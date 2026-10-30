"""Analysis tiles that tell one story each: what moved, why, and by how much.

Built from how analysts in each industry read their numbers (see rnd/domain_layouts/v2/CHART_RESEARCH_v2.md):
  outlier_lines    every member of a dimension on one chart, the one that moved (or breached a line) highlighted
  change_bars      change vs the same weeks last year (or a level around a reference), diverging, worst first;
                   display="dots" draws it as now-vs-before dot pairs
  driver_split     an outcome and the drivers it multiplies out of (sales = orders x order value), % change each
  velocity_split   sales change split into a distribution effect and a velocity effect, per member
  stacked_trend    a few stock metrics stacked over time (past-due balances by age), optionally for the member
                   whose risk moved most
  metric_waterfall gross-to-net style steps from one metric to another, reconciled
Every number comes from governed SEMANTIC_VIEW queries; comparisons use whole windows (13 weeks / 3 months), never
one noisy week. Each tile writes its own one-line finding (the tile headline), from its own numbers.
"""
from __future__ import annotations

import json
import re
from dataclasses import replace
from statistics import median
from typing import Any, Optional

from semantic_query import shift

WIN = {"day": 28, "week": 13, "month": 3, "quarter": 1}
PER_YEAR = {"day": 364, "week": 52, "month": 12, "quarter": 4}
TRAIL = {"day": 91, "week": 52, "month": 13, "quarter": 8}
SMOOTH = {"day": 7, "week": 4, "month": 1, "quarter": 1}
UNIT = {"day": "days", "week": "weeks", "month": "months", "quarter": "quarters"}
WORSE_UP = re.compile(r"DELINQUEN|LOSS|CHARGE_?OFF|DPD|RATE_GAP|RUNOFF|ATTRITION|OFF_PRICE|REWARDS_TO|RETURN|"
                      r"STOCKOUT|COST|WEEKS_OF_SUPPLY|ON_HAND|DISCOUNT|LOST|DELIVERY_DAYS|TRANSIT", re.I)
MAX_SERIES = 8


def _f(fmt, v, kind):
    return fmt(v, kind)


def _chg_txt(delta: Optional[float], kind: str) -> str:
    if delta is None:
        return "n/a"
    if kind == "percent":
        return f"{delta * 100:+.2f} pts" if abs(delta) < 0.001 else f"{delta * 100:+.1f} pts"
    if kind == "index":
        return f"{delta:+.0f} pts"
    return f"{delta * 100:+.1f}%" if abs(delta) < 0.1 else f"{delta * 100:+.0f}%"


def _val(fmt, v, kind) -> str:
    """A value for a sentence: small rates keep two decimals (a 0.07% rate gap is not '0.1%'), indexes are whole."""
    if v is None:
        return "n/a"
    if kind == "index":
        return f"{v:.0f}"
    if kind == "percent" and abs(v) < 0.01 and v != 0:
        return f"{v * 100:.2f}%"
    if kind == "number" and abs(v) < 100 and not float(v).is_integer():
        return f"{v:.1f}"
    return fmt(v, kind)


class DomainTiles:
    # ------------------------------------------------------------------ shared helpers
    def _o(self, comp) -> dict[str, Any]:
        return comp.get("opts") or {}

    def _tile_where(self, comp, metrics) -> str:
        """Global filters the metrics allow, plus the tile's own fixed filter (e.g. wholesale accounts only)."""
        parts = [p for p in [self._flt(metrics)] if p]
        for dim, vals in (self._o(comp).get("filter") or {}).items():
            if not vals or not all(self.allowed(m, dim) for m in metrics):
                continue
            lits = ", ".join("'" + str(v).replace("'", "''") + "'" for v in vals)
            parts.append(f"{self.q.dim(dim).ref} IN ({lits})")
        return " AND ".join(parts)

    def _filter_note(self, comp) -> str:
        f = self._o(comp).get("filter") or {}
        return "; ".join(f"{self.dlabel(d)}: {', '.join(map(str, v))}" for d, v in f.items() if v)

    def _better_down(self, comp, metric) -> bool:
        b = self._o(comp).get("better")
        if b in ("up", "down"):
            return b == "down"
        return bool(WORSE_UP.search(self.model.field(metric, ("metric",)).name))

    def _windows(self, comp=None) -> dict[str, Any]:
        g = self.cal.grain
        n = int(self._o(comp or {}).get("periods") or WIN[g])
        end = shift(self.cal.current_start, g, 1)
        start = shift(self.cal.current_start, g, -(n - 1))
        py = PER_YEAR[g]
        return {"n": n, "cur": (start, end), "ly": (shift(start, g, -py), shift(end, g, -py)),
                "prior": (shift(start, g, -n), start),
                "label": f"last {n} {UNIT[g]}" if n > 1 else self.cal.label(self.cal.current_start)}

    def _win_rows(self, metrics, dims, rng, where) -> list[dict[str, Any]]:
        start, end = rng
        key = f"dt:{','.join(metrics)}:{','.join(dims)}:{start}:{end}:{where}"
        return self._memo_get(key, lambda: self.q.by_dim(self.b.time_dimension, metrics, dims, start, end,
                                                          limit=2000, extra=where))

    def _compare(self, comp, metrics, dims) -> tuple[dict, dict, str, str]:
        """{key: {metric: value}} for the current window and its comparison window (same weeks last year, else
        the window before), keyed by the dims' values (a tuple; () when no dims)."""
        w = self._windows(comp)
        where = self._tile_where(comp, metrics)
        cur = self._win_rows(metrics, dims, w["cur"], where)
        mode = self._o(comp).get("compare") or "yoy"
        base = self._win_rows(metrics, dims, w["ly"], where) if mode == "yoy" else []
        base_label = "same weeks last year" if self.cal.grain == "week" else "same period last year"
        if not any(r.get(metrics[0]) is not None for r in base):
            base, base_label = self._win_rows(metrics, dims, w["prior"], where), f"the {w['n']} {UNIT[self.cal.grain]} before"
        k = lambda r: tuple(r[d] for d in dims)
        return {k(r): r for r in cur}, {k(r): r for r in base}, w["label"], base_label

    def _series_by(self, comp, metrics, dim, back: int = 0) -> list[dict[str, Any]]:
        """Series per period (and member). back = periods before the current one the series must reach (the
        dashboard window can be shorter than a year plus a comparison window)."""
        where = self._tile_where(comp, metrics)
        cal = self.cal
        if back:
            start = shift(self.cal.current_start, self.cal.grain, -back)
            if start < self.cal.window_start:
                cal = replace(self.cal, window_start=start)
        key = f"ds:{','.join(metrics)}:{dim}:{where}:{cal.window_start}"
        return self._memo_get(key, lambda: self.q.series(self.b.time_dimension, metrics, cal, dim, where))

    @staticmethod
    def _delta(now, then, kind) -> Optional[float]:
        if now is None or then is None:
            return None
        if kind == "percent":
            return now - then
        return (now - then) / abs(then) if then else None

    def _ref(self, comp) -> Optional[dict[str, Any]]:
        r = self._o(comp).get("reference")
        if r is None:
            return None
        try:
            return {"value": float(r), "label": str(self._o(comp).get("reference_label") or "")[:40]}
        except (TypeError, ValueError):
            return None

    # ------------------------------------------------------------------ outlier_lines
    def outlier_lines(self, comp) -> dict[str, Any]:
        from engine import fmt
        m, dim = self._metric_for(comp), self._segment_dim(comp)
        o, g = self._o(comp), self.cal.grain
        kind = self.kind_of(m)
        trail = int(o.get("trail") or TRAIL[g])
        w0 = min(WIN[g], max(1, trail // 4))
        rows = self._series_by(comp, [m], dim, back=trail + PER_YEAR[g])
        allp = sorted({r["period"] for r in rows})
        periods = allp[-trail:]
        by: dict[str, dict[str, float]] = {}
        for r in rows:
            if r.get(m) is not None:
                by.setdefault(r["segment"], {})[r["period"]] = r[m]
        index = bool(o.get("index"))
        sm_n = int(o.get("smooth") or 1)
        w = w0
        py = PER_YEAR[g]
        yoy = len(allp) >= py + w and not index                      # same weeks last year are in the data
        then_p = allp[-(py + w):-py] if yoy else periods[:w]
        now_p = periods[-w:]
        cmp_label = (f"last {w} {UNIT[g]} vs a year earlier" if yoy else f"last {w} {UNIT[g]} vs the first {w} shown")
        down = self._better_down(comp, m)
        ref = self._ref(comp)

        def smooth(vals):
            if sm_n <= 1:
                return vals
            out = []
            for i in range(len(vals)):
                win = [v for v in vals[max(0, i - sm_n + 1):i + 1] if v is not None]
                out.append(sum(win) / len(win) if win else None)
            return out
        series = []
        for seg, pts in by.items():
            raw = [pts.get(p) for p in periods]
            base = next((v for v in raw if v), None)
            vals = smooth([None if v is None or not base else v / base * 100 for v in raw] if index else raw)
            known = [v for v in vals if v is not None]
            nowv = [pts[p] for p in now_p if pts.get(p) is not None]
            thenv = [pts[p] for p in then_p if pts.get(p) is not None]
            if len(known) < 2 or not nowv or not thenv:
                continue
            now, then = sum(nowv) / len(nowv), sum(thenv) / len(thenv)
            if index and base:
                now, then = now / base * 100, then / base * 100
            delta = (now - then) if (kind == "percent" or index) else self._delta(now, then, kind)
            series.append({"name": seg, "values": vals, "now": known[-1], "first": known[0], "delta": delta,
                           "avg_now": now, "avg_then": then})
        if not series:
            raise RuntimeError("No data for this breakdown")
        # what to highlight: members past the reference line on the wrong side, else the biggest mover
        hl: list[str] = []
        if ref:
            hl = [s["name"] for s in series if (s["now"] > ref["value"] if down else s["now"] < ref["value"])][:2]
        if not hl:
            score = lambda s: (s["delta"] or 0) * (1 if down else -1) if o.get("better") or WORSE_UP.search(m) \
                else abs(s["delta"] or 0)
            top = max(series, key=score)
            others = [s["delta"] or 0 for s in series if s is not top]
            if others:
                mid = median(others)
                mad = median(abs(x - mid) for x in others) or 1e-9
                spread = max(abs(x - mid) for x in others)
                gap = abs((top["delta"] or 0) - mid)
                if gap > 3 * mad and gap > 1.5 * spread and score(top) > 0:
                    hl = [top["name"]]
        series.sort(key=lambda s: -(s["now"] or 0))
        keep = [s for s in series if s["name"] in hl] + [s for s in series if s["name"] not in hl][:MAX_SERIES - len(hl)]
        keep.sort(key=lambda s: -(s["now"] or 0))
        ykind = "number" if index else kind
        labels = [self.label(p) for p in periods]
        out_series = [{"name": s["name"], "highlight": s["name"] in hl,
                       "points": [{"period": p, "label": lb, "value": v} for p, lb, v in zip(periods, labels, s["values"])],
                       "now": s["now"], "first": s["first"], "delta": s["delta"]} for s in keep]
        span = f"{len(periods)} {UNIT[g]}"
        what = "index (start = 100)" if index else self.mlabel(m)
        finding = ""
        vk = "index" if index else ykind
        dk = "index" if index else kind
        if hl:
            h = next(s for s in series if s["name"] == hl[0])
            rest = [s for s in series if s["name"] not in hl]
            lo, hi = (min(s["now"] for s in rest), max(s["now"] for s in rest)) if rest else (None, None)
            if ref and ((h["now"] > ref["value"]) if down else (h["now"] < ref["value"])):
                finding = (f"{h['name']} is {'above' if down else 'below'} the {_val(fmt, ref['value'], vk)} line at "
                           f"{_val(fmt, h['now'], vk)}" + (f"; the others are at {_val(fmt, lo, vk)}–{_val(fmt, hi, vk)}"
                                                           if rest else ""))
            else:
                ds = [s["delta"] for s in rest if s["delta"] is not None]
                verb = "up" if (h["delta"] or 0) > 0 else "down"
                when = "a year earlier" if yoy else "the start of the chart"
                if index:
                    rd = [x["now"] - 100 for x in rest]
                    finding = (f"{h['name']} {'up' if h['now'] > 100 else 'down'} {abs(h['now'] - 100):.0f}% in {span} "
                               f"(index {h['now']:.0f})" + (f"; the other {len(rd)} moved {min(rd):+.0f}% to {max(rd):+.0f}%"
                                                            if rd else ""))
                    rest = None
                unit = f" {self.mlabel(m).lower()}" if vk == "number" else ""
                finding = finding if rest is None else (f"{h['name']} averaged {_val(fmt, h['avg_now'], vk)}{unit} over the last {w} {UNIT[g]}, {verb} "
                           f"{_chg_txt(h['delta'], dk).lstrip('+-')} on {when}"
                           + (f"; the other {len(ds)} moved {_chg_txt(min(ds), dk)} to {_chg_txt(max(ds), dk)}" if ds else ""))
        elif series:
            ds = [x["delta"] for x in series if x["delta"] is not None]
            finding = (f"No {self.dlabel(dim).lower()} stands out: all moved {_chg_txt(min(ds), dk)} to "
                       f"{_chg_txt(max(ds), dk)}, {cmp_label}") if ds else ""
        facts = [f"{what} by {self.dlabel(dim)} over {span}: " + "; ".join(
            f"{s['name']} {fmt(s['first'], ykind)} → {fmt(s['now'], ykind)}" for s in keep[:6])]
        return {"metric_label": self.mlabel(m), "dimension_label": self.dlabel(dim), "kind": ykind,
                "index": index, "series": out_series, "reference": ref,
                "band": o.get("band"), "better": "down" if down else "up", "span_label": span,
                "smooth": sm_n if sm_n > 1 else None, "compare_label": cmp_label,
                "filter_note": self._filter_note(comp), "finding": finding, "_facts": facts}

    # ------------------------------------------------------------------ change_bars
    def change_bars(self, comp) -> dict[str, Any]:
        from engine import fmt
        m, dim = self._metric_for(comp), self._segment_dim(comp)
        o = self._o(comp)
        m2 = comp.get("metric2_id")
        kind = self.kind_of(m)
        down = self._better_down(comp, m)
        level = o.get("mode") == "level"
        metrics = [m] + ([m2] if m2 else [])
        cur, base, cur_label, base_label = self._compare(comp, metrics, [dim])
        if level and m2:      # the annotation compares with the window before (e.g. balances 13 weeks ago)
            w = self._windows(comp)
            prior = {(r[dim],): r for r in self._win_rows(metrics, [dim], w["prior"], self._tile_where(comp, metrics))}
        else:
            prior = base
        ref = self._ref(comp) or ({"value": 0.0, "label": ""} if level else None)
        rows = []
        for k, r in cur.items():
            now, then = r.get(m), (base.get(k) or {}).get(m)
            row = {"segment": k[0], "current": now, "base": then, "change": self._delta(now, then, kind)}
            if m2:
                k2 = self.kind_of(m2)
                row["m2_current"], row["m2_base"] = r.get(m2), (prior.get(k) or {}).get(m2)
                row["m2_change"] = self._delta(row["m2_current"], row["m2_base"], k2)
            if (row["current"] if level else row["change"]) is not None:
                rows.append(row)
        if not rows:
            raise RuntimeError("No comparable values for this breakdown")
        val = (lambda r: r["current"]) if level else (lambda r: r["change"])
        neutral = o.get("better") == "none"
        rows.sort(key=lambda r: -val(r) if neutral else val(r) * (-1 if down else 1))   # worst (or biggest) first
        rows = rows[:15]
        unit = "pts" if kind == "percent" else "%"
        worst = rows[0]
        if level:
            rv = ref["value"]
            bad = [r for r in rows if (r["current"] > rv if down else r["current"] < rv)]
            side = "above" if down else "below"
            if not bad:
                low = rows[0]
                finding = (f"All {len(rows)} {'below' if down else 'above'} {_val(fmt, rv, kind)}; "
                           f"{'highest' if down else 'lowest'} {low['segment']} at {_val(fmt, low['current'], kind)}")
            elif len(bad) == 1:
                finding = (f"Only {bad[0]['segment']} is {side} {_val(fmt, rv, kind)}, at {_val(fmt, bad[0]['current'], kind)}"
                           if len(rows) > 2 else f"{bad[0]['segment']} is {side} {_val(fmt, rv, kind)}, at "
                                                 f"{_val(fmt, bad[0]['current'], kind)}")
            else:
                finding = (f"{len(bad)} of {len(rows)} {side} {_val(fmt, rv, kind)}: " + ", ".join(
                    f"{r['segment']} {_val(fmt, r['current'], kind)}" for r in bad[:3]))
            if bad and m2 and bad[0].get("m2_change") is not None:
                finding += (f"; {self.mlabel(m2).lower()} {_chg_txt(bad[0]['m2_change'], self.kind_of(m2))} "
                            f"vs {self._windows(comp)['n']} {UNIT[self.cal.grain]} earlier")
        else:
            first, last = rows[0], rows[-1]
            ch = [r["change"] for r in rows]
            vs = f"vs {base_label}"
            if len(rows) < 2:
                finding = f"{first['segment']} {_chg_txt(first['change'], kind)} {vs}"
            elif neutral:
                finding = (f"{first['segment']} up most at {_chg_txt(first['change'], kind)} {vs}; "
                           f"{last['segment']} {_chg_txt(last['change'], kind)}")
            elif all(c < 0 for c in ch) or all(c > 0 for c in ch):
                word = "fell" if ch[0] < 0 else "rose"
                finding = (f"All {len(rows)} {word} {vs}: most {first['segment'] if (ch[0] < 0) == (not down) else last['segment']} "
                           f"{_chg_txt(first['change'] if (ch[0] < 0) == (not down) else last['change'], kind)}, least "
                           f"{last['segment'] if (ch[0] < 0) == (not down) else first['segment']} "
                           f"{_chg_txt(last['change'] if (ch[0] < 0) == (not down) else first['change'], kind)}")
            else:
                finding = (f"{first['segment']} worst at {_chg_txt(first['change'], kind)} {vs}; "
                           f"{last['segment']} best at {_chg_txt(last['change'], kind)}")
        facts = [f"{self.mlabel(m)} by {self.dlabel(dim)}, {cur_label} vs {base_label}: " + "; ".join(
            f"{r['segment']} {fmt(r['current'], kind)} ({_chg_txt(r['change'], kind)})" for r in rows[:6])]
        return {"metric_label": self.mlabel(m), "dimension_label": self.dlabel(dim), "kind": kind, "unit": unit,
                "mode": "level" if level else "change", "display": o.get("display") or "bars",
                "metric2_label": self.mlabel(m2) if m2 else None, "metric2_kind": self.kind_of(m2) if m2 else None,
                "rows": rows, "reference": ref, "better": "down" if down else "up",
                "neutral": neutral, "current_label": cur_label, "base_label": base_label if not (level and m2) else
                f"the {self._windows(comp)['n']} {UNIT[self.cal.grain]} before",
                "filter_note": self._filter_note(comp), "finding": finding, "_facts": facts}

    # ------------------------------------------------------------------ driver_split
    def driver_split(self, comp) -> dict[str, Any]:
        """metrics[0] = outcome, metrics[1:] = drivers whose product is the outcome (orders x order value)."""
        from engine import fmt
        ms = comp.get("metrics") or []
        if len(ms) < 3:
            raise RuntimeError("Needs an outcome and at least two drivers")
        cur, base, cur_label, base_label = self._compare(comp, ms, [])
        c, b = cur.get((), {}), base.get((), {})
        rows = []
        for i, m in enumerate(ms):
            kind = self.kind_of(m)
            rows.append({"segment": self.mlabel(m), "current": c.get(m), "base": b.get(m),
                         "change": self._delta(c.get(m), b.get(m), "number"), "total": i == 0, "kind": kind})
        prod = 1.0
        for r in rows[1:]:
            prod *= 1 + (r["change"] or 0)
        out_chg = rows[0]["change"]
        multiplies = out_chg is not None and abs((1 + out_chg) - prod) < 0.01
        drivers = sorted(rows[1:], key=lambda r: abs(r["change"] or 0), reverse=True)
        lead = drivers[0]
        finding = (f"{rows[0]['segment']} {_chg_txt(out_chg, 'number')} vs {base_label}: mostly "
                   f"{lead['segment'].lower()} ({_chg_txt(lead['change'], 'number')})"
                   + "".join(f", {d['segment'].lower()} {_chg_txt(d['change'], 'number')}" for d in drivers[1:]))
        facts = [finding]
        return {"rows": rows[1:] + rows[:1], "kind": "number", "unit": "%", "mode": "change", "display": "bars",
                "multiplies": multiplies, "metric_label": rows[0]["segment"], "dimension_label": "Driver",
                "current_label": cur_label, "base_label": base_label, "better": "up",
                "filter_note": self._filter_note(comp), "finding": finding, "_facts": facts}

    # ------------------------------------------------------------------ velocity_split
    def velocity_split(self, comp) -> dict[str, Any]:
        """Sales change = distribution effect + velocity effect (velocity = sales per point of distribution)."""
        from engine import fmt
        m, dim, m2 = self._metric_for(comp), self._segment_dim(comp), comp.get("metric2_id")
        if not m2:
            raise RuntimeError("Needs a distribution metric")
        cur, base, cur_label, base_label = self._compare(comp, [m, m2], [dim])
        kind = self.kind_of(m)
        rows = []
        for k, r in cur.items():
            s1, a1 = r.get(m), r.get(m2)
            s0, a0 = (base.get(k) or {}).get(m), (base.get(k) or {}).get(m2)
            if None in (s1, a1, s0, a0) or not a1 or not a0:
                continue
            v1, v0 = s1 / a1, s0 / a0
            dist, vel = (a1 - a0) * v0, (v1 - v0) * a1
            rows.append({"segment": k[0], "current": s1, "base": s0, "change": (s1 - s0) / abs(s0) if s0 else None,
                         "distribution_effect": dist, "velocity_effect": vel, "total_effect": s1 - s0,
                         "acv_now": a1, "acv_before": a0})
        if not rows:
            raise RuntimeError("No comparable values for this breakdown")
        rows.sort(key=lambda r: r["total_effect"], reverse=True)
        worst = min(rows, key=lambda r: r["total_effect"])
        driver = "velocity (sales per point of distribution)" if abs(worst["velocity_effect"]) >= abs(
            worst["distribution_effect"]) else "distribution (fewer stores carrying it)"
        if worst["total_effect"] < 0:
            finding = (f"{worst['segment']} {_chg_txt(worst['change'], 'number')} ({fmt(worst['total_effect'], kind)}): "
                       f"velocity {fmt(worst['velocity_effect'], kind)}, distribution "
                       f"{fmt(worst['distribution_effect'], kind)}")
            finding = finding.replace("distribution $", "distribution +$").replace("velocity $", "velocity +$")
        else:
            best = rows[0]
            finding = f"Every {self.dlabel(dim).lower()} grew; {best['segment']} most at {_chg_txt(best['change'], 'number')}"
        facts = [f"{self.mlabel(m)} change by {self.dlabel(dim)} ({cur_label} vs {base_label}) split into distribution "
                 "and velocity: " + "; ".join(f"{r['segment']} dist {fmt(r['distribution_effect'], kind)}, velocity "
                                              f"{fmt(r['velocity_effect'], kind)}" for r in rows[:6])]
        return {"metric_label": self.mlabel(m), "metric2_label": self.mlabel(m2), "dimension_label": self.dlabel(dim),
                "kind": kind, "rows": rows, "current_label": cur_label, "base_label": base_label,
                "filter_note": self._filter_note(comp), "finding": finding, "_facts": facts}

    # ------------------------------------------------------------------ stacked_trend
    def stacked_trend(self, comp) -> dict[str, Any]:
        """Stock metrics stacked over time. opts.cumulative: the metrics are '30+, 60+, 90+' style (each includes the
        next), so the stack shows the buckets between them. opts.focus_by: show the member of `dimension` whose
        focus_by metric worsened most (else the total)."""
        from engine import fmt
        ms = comp.get("metrics") or []
        if not ms:
            raise RuntimeError("Needs metrics to stack")
        o, g = self._o(comp), self.cal.grain
        dim = comp.get("dimension")
        focus = None
        if dim and comp.get("metric2_id"):
            fm = comp["metric2_id"]
            cur, base, _, _ = self._compare(comp, [fm], [dim])
            fk = self.kind_of(fm)
            down = self._better_down(comp, fm)
            cand = [(k[0], self._delta(r.get(fm), (base.get(k) or {}).get(fm), fk)) for k, r in cur.items()]
            cand = [c for c in cand if c[1] is not None]
            if cand:
                focus = max(cand, key=lambda c: c[1] * (1 if down else -1))[0]
        rows = self._series_by(comp, ms, dim) if focus else self._series_by(comp, ms, None)
        if focus:
            rows = [r for r in rows if r.get("segment") == focus]
        step = SMOOTH[g] if g in ("week", "day") else 1
        periods = sorted({r["period"] for r in rows})
        periods = periods[::-1][::step][::-1][-13:]
        byp = {r["period"]: r for r in rows}
        labels_m = [self.mlabel(m) for m in ms]
        cum = bool(o.get("cumulative"))
        names = o.get("labels") or (self._bucket_names(labels_m) if cum else labels_m)
        bars = []
        for p in periods:
            r = byp.get(p, {})
            vals = [r.get(m) or 0.0 for m in ms]
            if cum:
                vals = [max(0.0, vals[i] - (vals[i + 1] if i + 1 < len(vals) else 0.0)) for i in range(len(vals))]
            bars.append({"period": p, "label": self.label(p), "values": vals, "total": sum(vals)})
        if not bars:
            raise RuntimeError("No data")
        kind = self.kind_of(ms[0])
        first, last = bars[0], bars[-1]
        ch = (last["total"] - first["total"]) / first["total"] if first["total"] else None
        deep = names[-1]
        finding = ((f"{focus}: " if focus else "") + f"total {fmt(last['total'], kind)}, {_chg_txt(ch, 'number')} since "
                   f"{first['label']}; {deep} {fmt(last['values'][-1], kind)}")
        facts = [finding]
        return {"series_names": names, "kind": kind, "bars": bars, "focus": focus,
                "focus_label": (self.dlabel(dim) if focus else None),
                "focus_metric": (self.mlabel(comp["metric2_id"]) if focus else None), "metric_label": ", ".join(labels_m),
                "filter_note": self._filter_note(comp), "finding": finding, "_facts": facts}

    @staticmethod
    def _bucket_names(labels: list[str]) -> list[str]:
        nums = [re.search(r"(\d+)", x) for x in labels]
        if not all(nums):
            return labels
        n = [int(x.group(1)) for x in nums]
        out = [f"{a}–{b - 1} days" for a, b in zip(n, n[1:])] + [f"{n[-1]}+ days"]
        return out

    # ------------------------------------------------------------------ metric_waterfall
    def metric_waterfall(self, comp) -> dict[str, Any]:
        """opts.steps: [{"metric": id, "op": "start"|"minus"|"plus"|"total", "label"?}] over the current window.
        A 'total' step that is a governed metric is checked against the running sum."""
        from engine import fmt
        steps = self._o(comp).get("steps") or []
        ms = [s["metric"] for s in steps if s.get("metric")]
        if len(ms) < 2:
            raise RuntimeError("Needs at least two steps")
        w = self._windows(comp)
        r = (self._win_rows(ms, [], w["cur"], self._tile_where(comp, ms)) or [{}])[0]
        run, out, notes = 0.0, [], []
        kind = self.kind_of(ms[0])
        for s in steps:
            v = r.get(s.get("metric")) if s.get("metric") else None
            label = s.get("label") or (self.mlabel(s["metric"]) if s.get("metric") else "Total")
            op = s.get("op")
            if op == "start":
                run = v or 0.0
                out.append({"label": label, "value": run, "kind": "start"})
            elif op in ("minus", "plus"):
                d = (v or 0.0) * (-1 if op == "minus" else 1)
                out.append({"label": label, "value": d, "kind": "down" if d < 0 else "up", "base": run})
                run += d
            else:
                if v is not None and abs(v - run) > 0.005 * max(1.0, abs(run)):
                    notes.append(f"{label} in the semantic view is {fmt(v, kind)}; the steps add up to {fmt(run, kind)}")
                out.append({"label": label, "value": run, "kind": "end", "reconciled": not notes})
        start = out[0]["value"] if out else 0
        biggest = min((x for x in out if x["kind"] == "down"), key=lambda x: x["value"], default=None)
        finding = (f"{out[-1]['label']} {fmt(out[-1]['value'], kind)} from {out[0]['label'].lower()} "
                   f"{fmt(start, kind)} ({out[-1]['value'] / start * 100:.0f}%)" if start else "")
        if biggest and start:
            finding += f"; {biggest['label'].lower()} takes {abs(biggest['value']) / start * 100:.1f}%"
        return {"steps": out, "kind": kind, "period_label": w["label"], "notes": notes,
                "filter_note": self._filter_note(comp), "finding": finding, "_facts": [finding]}
