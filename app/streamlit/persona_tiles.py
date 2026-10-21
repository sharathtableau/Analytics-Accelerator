"""Persona tiles: the building blocks that make Executive, Manager and Operations dashboards different.

Executive : kpi_plan (YTD vs plan / last year, bullet), ytd_trajectory (cumulative YTD vs plan vs last year
            + Snowflake ML forecast to year end)
Manager   : scorecard (dimension x KPIs, variance vs plan or prior period, red/amber/green)
Operations: status_tiles (right now vs same time last week), pace_chart (cumulative by hour today),
            hour_heatmap (hour x day, last 7 days), worklist (what deviates today, ranked, with actions)

Every number is a SEMANTIC_VIEW query. Dates and hours in WHERE clauses are generated server-side from
python dates/ints, never from user text. Mixed into Engine (engine.py).
"""
from __future__ import annotations

import datetime as dt
import re
import statistics
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Optional

HOUR = re.compile(r"HOUR", re.I)
LOWER_IS_BETTER = re.compile(r"RETURN|STOCKOUT|DELIVERY_DAYS|TRANSIT|CLICK_TO_SHIP|DISCOUNT|LOST|COST|COGS|"
                             r"WEEKS_OF_SUPPLY", re.I)
COUNT_DISTINCT = re.compile(r"^COUNT\s*\(\s*DISTINCT", re.I)
WEEKS_BACK = 4


def _pct(cur, base):
    if cur is None or base in (None, 0):
        return None
    return (cur - base) / abs(base)


class PersonaTiles:
    # ------------------------------------------------------------------ helpers
    def lower_is_better(self, metric: str) -> bool:
        return bool(LOWER_IS_BETTER.search(self.model.field(metric, ("metric",)).name))

    def cumulable(self, metric: str) -> bool:
        """Can values be summed across hours/days? (SUM/COUNT, or distinct counts of per-event ids)."""
        f = self.model.field(metric, ("metric",))
        return f.additive or bool(COUNT_DISTINCT.match(re.sub(r"\s+", " ", f.expression or "").strip()))

    def hour_dim(self, metric: Optional[str] = None) -> Optional[str]:
        known = bool(getattr(self.model, "metric_dims", None))
        for d in self.model.categorical_dimensions:
            if not HOUR.search(d.name):
                continue
            if metric is None:
                return d.id
            if known:
                if self.allowed(metric, d.id):
                    return d.id
            else:   # no relationship map: only trust a dimension on the metric's own table
                f = self.model.field(metric, ("metric",))
                if f.entity and f.entity.upper() == (d.entity or "").upper():
                    return d.id
        return None

    @property
    def today(self) -> dt.date:
        return self.cal.max_date

    def _rows(self, metrics: list[str], dims: list[str], start: dt.date, end_excl: dt.date,
              extra: str = "", by_day: bool = False, by_month: bool = False) -> list[dict[str, Any]]:
        """Generic governed query: optional day/month bucket + categorical dims, metrics M0..Mn."""
        time = self.q.dim(self.b.time_dimension)
        sel = []
        if by_day or by_month:
            sel.append(self.q.trunc(time, "month" if by_month else "day", "PERIOD"))
        sel += [f"{self.q.dim(d).ref} AS D{i}" for i, d in enumerate(dims)]
        mets = [f"{self.q.metric(m).ref} AS M{i}" for i, m in enumerate(metrics)]
        where = self.q.range_where(time, start, end_excl)
        flt = self._flt(metrics)
        for part in (flt, extra):
            if part:
                where += f" AND {part}"
        sql = "SELECT * FROM " + self.q.sv(sel, mets, where)
        out = []
        for r in self.q.run(sql):
            item: dict[str, Any] = {}
            if by_day or by_month:
                p = r.get("period")
                item["period"] = (p.date() if isinstance(p, dt.datetime) else
                                  p if isinstance(p, dt.date) else dt.date.fromisoformat(str(p)[:10]))
            for i, d in enumerate(dims):
                v = r.get(f"d{i}")
                item[d] = "(blank)" if v is None else v
            for i, m in enumerate(metrics):
                v = r.get(f"m{i}")
                item[m] = None if v is None else float(v)
            out.append(item)
        return out

    def _cached(self, key: str, fn):
        return self._memo_get("persona:" + key, fn)

    def live_hour(self) -> Optional[int]:
        """Latest hour with data today (None when the view has no hour dimension)."""
        m = self.b.primary_metric
        h = self.hour_dim(m)
        if not h:
            return None

        def run():
            rows = self._rows([m], [h], self.today, self.today + dt.timedelta(days=1))
            hours = [int(float(r[h])) for r in rows if r[m] is not None and str(r[h]).replace(".", "").isdigit()]
            return max(hours) if hours else None
        return self._cached(f"hour:{self.today}", run)

    def _hour_filter(self, metric: str, hour: Optional[int]) -> str:
        h = self.hour_dim(metric)
        if h is None or hour is None or hour >= 23:
            return ""
        return f"{self.q.dim(h).ref} <= {int(hour)}"

    def _same_weekdays(self) -> list[dt.date]:
        return [self.today - dt.timedelta(days=7 * k) for k in range(1, WEEKS_BACK + 1)]

    def _status(self, metric: str, kind: str, cur, base) -> tuple[Optional[float], str]:
        """(delta, status) with direction awareness: good / ok / warn / bad."""
        if cur is None or base is None:
            return None, "ok"
        if kind == "percent":
            delta, small, big = cur - base, 0.005, 0.02
        else:
            delta, small, big = _pct(cur, base), 0.03, 0.10
        if delta is None:
            return None, "ok"
        worse = (delta > 0) if self.lower_is_better(metric) else (delta < 0)
        size = abs(delta)
        if size < small:
            return delta, "ok"
        if not worse:
            return delta, "good"
        return delta, "bad" if size >= big else "warn"

    # ------------------------------------------------------------------ operations
    def status_tiles(self, comp) -> dict[str, Any]:
        metrics = [m for m in (comp.get("metrics") or []) if m in {x.id for x in self.model.metrics}][:6] \
            or [self.b.primary_metric]
        hour = self.live_hour()
        weeks = self._same_weekdays()
        start, end = weeks[-1], self.today + dt.timedelta(days=1)
        groups: dict[str, list[str]] = {}
        for m in metrics:
            groups.setdefault(self._hour_filter(m, hour), []).append(m)
        vals: dict[tuple, Optional[float]] = {}
        for extra, ms in groups.items():
            try:
                rows = self._cached(f"st:{','.join(ms)}:{extra}:{self.today}",
                                    lambda ms=ms, extra=extra: self._rows(ms, [], start, end, extra, by_day=True))
            except Exception:
                rows = []                       # one metric the view can't combine -> query each alone
                for m1 in ms:
                    try:
                        rows += self._cached(f"st:{m1}:{extra}:{self.today}",
                                             lambda m1=m1, extra=extra: self._rows([m1], [], start, end, extra, by_day=True))
                    except Exception:
                        continue
            for r in rows:
                for m in ms:
                    if m in r:
                        vals[(m, r["period"])] = r[m]
        items, facts = [], []
        wk = self.today.strftime("%a")
        for m in metrics:
            kind = self.kind_of(m)
            cur, last = vals.get((m, self.today)), vals.get((m, weeks[0]))
            hist = [vals.get((m, d)) for d in weeks if vals.get((m, d)) is not None]
            avg = sum(hist) / len(hist) if hist else None
            delta, status = self._status(m, kind, cur, last)
            timed = bool(self._hour_filter(m, hour))
            items.append({"metric": m, "label": self.mlabel(m), "kind": kind, "current": cur, "base": last,
                          "avg": avg, "delta": delta, "status": status, "timed": timed,
                          "inverse": self.lower_is_better(m)})
            facts.append(f"{self.mlabel(m)} today{' to ' + f'{hour:02d}:59' if timed else ''} = "
                         f"{self._fmt(cur, kind)} vs {self._fmt(last, kind)} last {wk} ({status})")
        return {"items": items, "today_label": self.today.strftime("%a %d %b %Y"),
                "hour": hour, "as_of": f"{hour:02d}:59" if hour is not None and hour < 23 else None,
                "compare_label": f"vs last {wk}" + (" at the same time" if hour is not None and hour < 23 else ""),
                "_facts": facts}

    def pace_chart(self, comp) -> dict[str, Any]:
        m = self._metric_for(comp)
        kind = self.kind_of(m)
        h = self.hour_dim(m)
        if h:
            return self._pace_by_hour(m, h, kind)
        return self._pace_month(m, kind)

    def _pace_by_hour(self, m: str, h: str, kind: str) -> dict[str, Any]:
        weeks = self._same_weekdays()
        rows = self._cached(f"pace:{m}:{self.today}", lambda: self._rows(
            [m], [h], weeks[-1], self.today + dt.timedelta(days=1), by_day=True))
        hour_now = self.live_hour()
        by: dict[dt.date, dict[int, float]] = {}
        hours = set()
        for r in rows:
            try:
                hr = int(float(r[h]))
            except (TypeError, ValueError):
                continue
            hours.add(hr)
            by.setdefault(r["period"], {})[hr] = r[m] or 0.0
        if not hours:
            return {"labels": [], "series": [], "kind": kind, "metric_label": self.mlabel(m), "_facts": []}
        hs = list(range(min(hours), max(hours) + 1))

        def cum(day: dt.date, upto: Optional[int] = None):
            out, run = [], 0.0
            for hr in hs:
                if upto is not None and hr > upto:
                    out.append(None)
                    continue
                run += by.get(day, {}).get(hr, 0.0)
                out.append(run)
            return out
        today = cum(self.today, hour_now)
        last = cum(weeks[0])
        avg_days = [d for d in weeks if d in by]
        avg = [sum(cum(d)[i] for d in avg_days) / len(avg_days) for i in range(len(hs))] if avg_days else []
        now_ix = hs.index(hour_now) if hour_now in hs else len(hs) - 1
        cur_v, last_v = today[now_ix], last[now_ix]
        wk = self.today.strftime("%a")
        facts = [f"{self.mlabel(m)} today to {hs[now_ix]:02d}:59 = {self._fmt(cur_v, kind)} vs "
                 f"{self._fmt(last_v, kind)} by the same hour last {wk} "
                 f"({(_pct(cur_v, last_v) or 0) * 100:+.1f}%); last {wk} closed at {self._fmt(last[-1], kind)}"]
        series = [{"key": "today", "label": "Today", "style": "actual", "values": today},
                  {"key": "last", "label": f"Last {wk}", "style": "plan", "values": last}]
        if avg:
            series.append({"key": "avg", "label": f"Average of last {len(avg_days)} {wk}s", "style": "ref", "values": avg})
        return {"labels": [f"{x:02d}:00" for x in hs], "series": series, "kind": kind, "now_index": now_ix,
                "metric_label": self.mlabel(m), "mode": "hour",
                "pace": _pct(cur_v, last_v), "projected": (last[-1] * (1 + (_pct(cur_v, last_v) or 0))) if last else None,
                "caption": f"Cumulative {self.mlabel(m).lower()} by hour · {self.today:%a %d %b}", "_facts": facts}

    def _pace_month(self, m: str, kind: str) -> dict[str, Any]:
        """No hour dimension: month-to-date pace by day vs last month (and plan when there is one)."""
        start = self.today.replace(day=1)
        prev = (start - dt.timedelta(days=1)).replace(day=1)
        plan = self.plan_metric(m)
        rows = self._cached(f"pacem:{m}:{self.today}", lambda: self._rows(
            [m], [], prev, self.today + dt.timedelta(days=1), by_day=True))
        vals = {r["period"]: r[m] or 0.0 for r in rows}
        days = list(range(1, 32))

        def cum(first: dt.date, upto: Optional[int]):
            out, run = [], 0.0
            for d in days:
                try:
                    day = first.replace(day=d)
                except ValueError:
                    out.append(None)
                    continue
                if upto is not None and d > upto:
                    out.append(None)
                    continue
                run += vals.get(day, 0.0)
                out.append(run)
            return out
        series = [{"key": "today", "label": "This month", "style": "actual", "values": cum(start, self.today.day)},
                  {"key": "last", "label": "Last month", "style": "plan", "values": cum(prev, None)}]
        if plan:
            prow = self._cached(f"pacep:{plan}:{self.today}", lambda: self._rows(
                [plan], [], start, (start + dt.timedelta(days=32)).replace(day=1), by_day=True))
            pv = {r["period"]: r[plan] or 0.0 for r in prow}
            run, out = 0.0, []
            for d in days:
                try:
                    run += pv.get(start.replace(day=d), 0.0)
                    out.append(run)
                except ValueError:
                    out.append(None)
            series[1] = {"key": "plan", "label": "Plan", "style": "plan", "values": out}
            series.append({"key": "last", "label": "Last month", "style": "ref", "values": cum(prev, None)})
        return {"labels": [str(d) for d in days], "series": series, "kind": kind, "now_index": self.today.day - 1,
                "metric_label": self.mlabel(m), "mode": "month",
                "caption": f"Cumulative {self.mlabel(m).lower()} by day of month", "_facts": []}

    def hour_heatmap(self, comp) -> dict[str, Any]:
        m = self._metric_for(comp)
        h = self.hour_dim(m)
        if not h:
            raise RuntimeError("This semantic view has no hour-of-day dimension for this metric.")
        start = self.today - dt.timedelta(days=6)
        rows = self._cached(f"hh:{m}:{self.today}", lambda: self._rows(
            [m], [h], start, self.today + dt.timedelta(days=1), by_day=True))
        cells, hours = {}, set()
        for r in rows:
            try:
                hr = int(float(r[h]))
            except (TypeError, ValueError):
                continue
            hours.add(hr)
            cells[(r["period"], hr)] = r[m]
        hs = sorted(hours)
        days = [self.today - dt.timedelta(days=k) for k in range(0, 7)]
        labels = ["Today" if d == self.today else d.strftime("%a %d") for d in days]
        kind = self.kind_of(m)
        busiest = max(cells.items(), key=lambda kv: kv[1] or -1e30) if cells else None
        facts = [f"Busiest hour in the last 7 days: {busiest[0][0]:%a %d %b} {busiest[0][1]:02d}:00 "
                 f"({self._fmt(busiest[1], kind)} {self.mlabel(m).lower()})"] if busiest else []
        return {"metric_label": self.mlabel(m), "kind": kind, "row_label": "Day", "col_label": "Hour",
                "rows": labels, "cols": [f"{x:02d}" for x in hs],
                "values": [[cells.get((d, x)) for x in hs] for d in days], "_facts": facts}

    def worklist(self, comp) -> dict[str, Any]:
        """Today vs the same weekday in the last 4 weeks, per metric x breakdown; worst first."""
        metrics = [m for m in (comp.get("metrics") or []) if m in {x.id for x in self.model.metrics}][:4] \
            or [self.b.primary_metric]
        dims = [d for d in (comp.get("dimensions") or [comp.get("dimension")]) if d][:3] \
            or [d for d in (self.b.region_dimension, self.b.segment_dimension) if d]
        hour = self.live_hour()
        weeks = self._same_weekdays()
        start, end = weeks[-1], self.today + dt.timedelta(days=1)
        pairs = [(m, d) for m in metrics for d in dims if self.allowed(m, d)]

        def fetch(pair):
            m, d = pair
            extra = self._hour_filter(m, hour)
            try:
                return pair, self._cached(f"wl:{m}:{d}:{extra}:{self.today}",
                                          lambda: self._rows([m], [d], start, end, extra, by_day=True))
            except Exception:
                return pair, []                 # an unrelated pair is skipped, not fatal
        try:
            with ThreadPoolExecutor(max_workers=min(6, len(pairs) or 1)) as pool:
                results = list(pool.map(fetch, pairs))
        except Exception:
            results = [fetch(p) for p in pairs]
        cands = []
        for (m, d), rows in results:
            kind = self.kind_of(m)
            inv = self.lower_is_better(m)
            series: dict[str, dict[dt.date, float]] = {}
            for r in rows:
                if r[m] is not None:
                    series.setdefault(str(r[d]), {})[r["period"]] = r[m]
            total_norm = 0.0
            stats = []
            for seg, s in series.items():
                hist = [s[x] for x in weeks if x in s]
                cur = s.get(self.today)
                if cur is None or len(hist) < 2:
                    continue
                mean = sum(hist) / len(hist)
                sd = statistics.pstdev(hist)
                total_norm += abs(mean)
                stats.append((seg, cur, mean, sd))
            for seg, cur, mean, sd in stats:
                floor = 0.004 if kind == "percent" else 0.05 * abs(mean)
                z = (cur - mean) / max(sd, floor, 1e-9)
                worse = z > 0 if inv else z < 0
                dev = (cur - mean) if kind == "percent" else _pct(cur, mean)
                if dev is None:
                    continue
                material = abs(dev) >= (0.005 if kind == "percent" else 0.05)
                share = abs(mean) / total_norm if (total_norm and self.model.field(m, ("metric",)).additive) else 0.3
                score = min(abs(z), 6) * (0.4 + share)
                cands.append({"metric": m, "metric_label": self.mlabel(m), "dimension": d,
                              "dimension_label": self.dlabel(d), "segment": seg, "kind": kind,
                              "current": cur, "normal": mean, "deviation": dev, "z": z, "worse": worse,
                              "material": material, "score": score, "inverse": inv})
        flagged = [c for c in cands if c["worse"] and c["material"] and abs(c["z"]) >= 1.5]
        calm = not flagged
        rows = sorted(flagged or [c for c in cands if c["worse"]], key=lambda c: -c["score"])[:10]
        for c in rows:
            c["severity"] = "High" if abs(c["z"]) >= 3 else "Medium" if abs(c["z"]) >= 1.5 else "Watch"
        wk = self.today.strftime("%a")
        facts = [f"Worklist today: {c['metric_label']} for {c['segment']} ({c['dimension_label']}) is "
                 f"{self._fmt(c['current'], c['kind'])} vs a normal {wk} of {self._fmt(c['normal'], c['kind'])}"
                 for c in rows[:5]]
        return {"rows": rows, "none_flagged": calm, "today_label": self.today.strftime("%a %d %b"),
                "as_of": f"{hour:02d}:59" if hour is not None and hour < 23 else None,
                "method": (f"Today{' to ' + f'{hour:02d}:59' if hour is not None and hour < 23 else ''} vs the same "
                           f"weekday in the previous {WEEKS_BACK} weeks (same hours); flagged when it moves the wrong "
                           f"way by |z| ≥ 1.5 and a material amount. {len(pairs)} metric × breakdown checks."),
                "_facts": facts}

    # ------------------------------------------------------------------ executive
    def _ytd_bounds(self) -> tuple[dt.date, dt.date, dt.date, dt.date]:
        end = self.cal.end_exclusive                     # end of the latest complete period
        start = dt.date(self.cal.current_start.year, 1, 1)
        py_start = dt.date(start.year - 1, 1, 1)
        try:
            py_end = end.replace(year=end.year - 1)
        except ValueError:
            py_end = end - dt.timedelta(days=365)
        return start, end, py_start, py_end

    def _totals(self, metrics: list[str], start: dt.date, end: dt.date) -> dict[str, Optional[float]]:
        if not metrics:
            return {}
        rows = self._cached(f"tot:{','.join(metrics)}:{start}:{end}",
                            lambda: self._rows(metrics, [], start, end))
        return rows[0] if rows else {}

    def kpi_plan(self, comp) -> dict[str, Any]:
        from persona_layouts import SKIP
        metrics = [m for m in (comp.get("metrics") or []) if m in {x.id for x in self.model.metrics}
                   and not SKIP.search(m.split(".")[-1])][:5] or [self.b.primary_metric]
        start, end, py_start, py_end = self._ytd_bounds()
        cur_start = self.cal.current_start
        plans = {m: self.plan_metric(m) for m in metrics}
        plan_ids = sorted({p for p in plans.values() if p})
        series_metrics = list(dict.fromkeys(metrics + plan_ids))
        series = self._cached(f"kplan_series:{','.join(series_metrics)}:{start}:{end}",
                              lambda: self._rows(series_metrics, [], start, end, by_month=True))
        spark_labels = [self.cal.label(r["period"]) for r in series]
        ytd, py = self._totals(metrics, start, end), self._totals(metrics, py_start, py_end)
        mon = self._totals(metrics, cur_start, end)
        ytd_p, mon_p = self._totals(plan_ids, start, end), self._totals(plan_ids, cur_start, end)
        items, facts = [], []
        for m in metrics:
            kind = self.kind_of(m)
            p = plans[m]
            a, t, y = ytd.get(m), (ytd_p.get(p) if p else None), py.get(m)
            ma, mt = mon.get(m), (mon_p.get(p) if p else None)
            target, tlabel = (t, "plan") if t is not None else (y, "last year")
            d_t, st = self._status(m, kind, a, target)
            d_y, _ = self._status(m, kind, a, y)
            items.append({"metric": m, "label": self.mlabel(m), "kind": kind, "value": a, "target": target,
                          "target_label": tlabel, "delta": d_t, "status": st, "py": y, "delta_py": d_y,
                          "month": ma, "month_target": mt, "month_delta": self._status(m, kind, ma, mt)[0] if mt else None,
                          "inverse": self.lower_is_better(m), "spark": [r.get(m) for r in series],
                          "target_spark": [r.get(p) for r in series] if p else []})
            facts.append(f"{self.mlabel(m)} YTD {start:%b}–{(end - dt.timedelta(days=1)):%b %Y} = {self._fmt(a, kind)}"
                         + (f", {self._dtxt(d_t, kind)} vs {tlabel} ({self._fmt(target, kind)})" if d_t is not None else "")
                         + (f", {self._dtxt(d_y, kind)} vs last year" if d_y is not None and tlabel != "last year" else ""))
        return {"items": items, "period_label": f"YTD {start:%b} – {(end - dt.timedelta(days=1)):%b %Y}",
                "month_label": self.cal.label(cur_start), "has_plan": bool(plan_ids), "spark_labels": spark_labels,
                "spark_caption": f"Monthly trend, {start:%Y}", "_facts": facts}

    def ytd_trajectory(self, comp) -> dict[str, Any]:
        m = self._metric_for(comp)
        kind = self.kind_of(m)
        year = self.cal.current_start.year
        y0, y1, py0 = dt.date(year, 1, 1), dt.date(year + 1, 1, 1), dt.date(year - 1, 1, 1)
        rows = self._cached(f"traj:{m}:{year}", lambda: self._rows([m], [], py0, min(y1, self.cal.end_exclusive),
                                                                  by_month=True))
        by = {(r["period"].year, r["period"].month): r[m] or 0.0 for r in rows}
        last_month = (self.cal.end_exclusive - dt.timedelta(days=1)).month if self.cal.end_exclusive.year == year else 12
        plan = self.plan_metric(m)
        pv = {}
        if plan:
            prow = self._cached(f"trajp:{plan}:{year}", lambda: self._rows([plan], [], y0, y1, by_month=True))
            pv = {r["period"].month: r[plan] or 0.0 for r in prow}

        def cum(get, upto=12):
            out, run = [], 0.0
            for mo in range(1, 13):
                if mo > upto:
                    out.append(None)
                    continue
                run += get(mo)
                out.append(run)
            return out
        actual = cum(lambda mo: by.get((year, mo), 0.0), last_month)
        series = [{"key": "actual", "label": f"{year} actual", "style": "actual", "values": actual}]
        if pv:
            series.append({"key": "plan", "label": "Plan", "style": "plan", "values": cum(lambda mo: pv.get(mo, 0.0))})
        series.append({"key": "py", "label": f"{year - 1}", "style": "ref",
                       "values": cum(lambda mo: by.get((year - 1, mo), 0.0))})
        out = {"labels": [dt.date(year, mo, 1).strftime("%b") for mo in range(1, 13)], "series": series,
               "kind": kind, "now_index": last_month - 1, "metric_label": self.mlabel(m), "mode": "ytd",
               "caption": f"Cumulative {self.mlabel(m).lower()}, {year}"}
        # Snowflake ML forecast to year end (phase 2), added on top of YTD actual
        if last_month < 12 and self.cal.grain == "month" and self.granted_forecast():
            key = f"fc:{self.model.fqn}:{m}:{self.cal.grain}:{self.cal.current_start}:{self.fsig}"
            if key not in self.cache and self.defer_ml:
                out["insights_pending"] = True
            else:
                try:
                    if key not in self.cache:
                        s = self.metric_series(m)
                        self.cache[key] = self.cortex.forecast([(r["period"], r.get(m)) for r in s], 6, "month")
                    fc = self.cache[key]
                    base = actual[last_month - 1] or 0.0
                    f, lo, hi = [None] * 12, [None] * 12, [None] * 12
                    f[last_month - 1] = lo[last_month - 1] = hi[last_month - 1] = base
                    run_f = run_l = run_h = base
                    for pt in fc["points"]:
                        d = dt.date.fromisoformat(str(pt["period"])[:10])
                        if d.year != year:
                            continue
                        run_f += pt["forecast"]
                        run_l += pt["lower"]
                        run_h += pt["upper"]
                        f[d.month - 1], lo[d.month - 1], hi[d.month - 1] = run_f, run_l, run_h
                    out["series"].append({"key": "forecast", "label": "Forecast (Snowflake ML)", "style": "forecast",
                                          "values": f})
                    out["band"] = {"lower": lo, "upper": hi}
                    out["provenance"] = fc.get("provenance")
                    out["ml"] = True
                except Exception as exc:     # forecast is optional on this tile
                    out["forecast_error"] = str(exc)[:200]
        p_now = next((s for s in series if s["key"] == "plan"), None)
        a_now = actual[last_month - 1]
        facts = [f"{self.mlabel(m)} cumulative {year} to {dt.date(year, last_month, 1):%b} = {self._fmt(a_now, kind)}"
                 + (f" vs plan {self._fmt(p_now['values'][last_month - 1], kind)}" if p_now else "")]
        if out.get("ml"):
            ye = next(s for s in out["series"] if s["key"] == "forecast")["values"][-1]
            facts.append(f"Snowflake ML projects {year} {self.mlabel(m).lower()} at {self._fmt(ye, kind)}"
                         + (f" vs full-year plan {self._fmt(p_now['values'][-1], kind)}" if p_now else ""))
        out["_facts"] = facts
        return out

    def granted_forecast(self) -> bool:
        ev = self.p.capabilities.get("forecast_versioned")
        return bool(ev and ev.granted and self.cortex)

    # ------------------------------------------------------------------ manager
    def scorecard(self, comp) -> dict[str, Any]:
        d = comp.get("dimension") or self.b.region_dimension or self.b.segment_dimension
        metrics = [m for m in (comp.get("metrics") or []) if m in {x.id for x in self.model.metrics}
                   and self.allowed(m, d)][:5] or [self.b.primary_metric]
        cur, end, prior = self.cal.current_start, self.cal.end_exclusive, self.cal.prior_start
        plans = {m: p for m in metrics if (p := self.plan_metric(m)) and self.allowed(p, d)}
        cur_rows = self._cached(f"sc:{d}:{','.join(metrics)}:{cur}", lambda: self._rows(metrics, [d], cur, end))
        pri_rows = self._cached(f"sc:{d}:{','.join(metrics)}:{prior}", lambda: self._rows(metrics, [d], prior, cur))
        plan_rows = self._cached(f"scp:{d}:{','.join(sorted(set(plans.values())))}:{cur}",
                                 lambda: self._rows(sorted(set(plans.values())), [d], cur, end)) if plans else []
        tot_cur = self._totals(metrics, cur, end)
        tot_pri = self._totals(metrics, prior, cur)
        tot_plan = self._totals(sorted(set(plans.values())), cur, end) if plans else {}
        idx = lambda rows: {str(r[d]): r for r in rows}
        C, P, T = idx(cur_rows), idx(pri_rows), idx(plan_rows)
        segs = sorted(C, key=lambda s: -(C[s].get(metrics[0]) or 0))[:15]
        cols = [{"metric": m, "label": self.mlabel(m), "kind": self.kind_of(m),
                 "compare": "plan" if m in plans else f"prior {self.cal.grain}", "inverse": self.lower_is_better(m)}
                for m in metrics]

        def cell(m, row_c, row_p, row_t):
            kind = self.kind_of(m)
            v = (row_c or {}).get(m)
            base = (row_t or {}).get(plans[m]) if m in plans else (row_p or {}).get(m)
            delta, status = self._status(m, kind, v, base)
            return {"value": v, "base": base, "delta": delta, "status": status}
        rows = [{"segment": s, "cells": [cell(m, C.get(s), P.get(s), T.get(s)) for m in metrics]} for s in segs]
        total = {"segment": "Total", "cells": [cell(m, tot_cur, tot_pri, tot_plan) for m in metrics]}
        bad = [(r["segment"], cols[i]["label"]) for r in rows for i, c in enumerate(r["cells"]) if c["status"] == "bad"]
        facts = [f"Scorecard {self.cal.label(cur)} by {self.dlabel(d)}: " + "; ".join(
            f"{r['segment']} {cols[0]['label']} {self._fmt(r['cells'][0]['value'], cols[0]['kind'])}"
            + (f" ({self._dtxt(r['cells'][0]['delta'], cols[0]['kind'])} vs {cols[0]['compare']})"
               if r['cells'][0]['delta'] is not None else "") for r in rows[:6])]
        if bad:
            facts.append("Red cells: " + ", ".join(f"{s} {lbl}" for s, lbl in bad[:8]))
        return {"dimension": d, "dimension_label": self.dlabel(d), "columns": cols, "rows": rows, "total": total,
                "period_label": self.cal.label(cur), "_facts": facts}

    # ------------------------------------------------------------------ formatting for facts
    @staticmethod
    def _fmt(v, kind):
        from engine import fmt
        return fmt(v, kind)

    @staticmethod
    def _dtxt(d, kind):
        if d is None:
            return "n/a"
        return f"{d * 100:+.1f} pt" if kind == "percent" else f"{d * 100:+.1f}%"
