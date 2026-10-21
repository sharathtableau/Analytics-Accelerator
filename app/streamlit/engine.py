"""Compute data for every ready component of a bound layout.

All values come from SEMANTIC_VIEW queries (semantic_query) or Snowflake ML on
those governed results. A failed query yields an explicit error state for that
component; the app never substitutes sample values.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import re
import statistics
import time
from typing import Any, Callable, Optional

from inventory import Bindings, Profile, SOURCE_BASELINE
from headlines import headline as tile_headline
from chart_tiles import ChartTiles
from persona_tiles import PersonaTiles
from semantic_catalog import SemanticModel
from semantic_query import SemanticQuery, capturing, shift

CURRENCY = re.compile(r"SALES|REVENUE|PROFIT|AMOUNT|COST|PRICE|SPEND|GMV|VALUE|MARGIN|USD", re.I)   # a ratio MARGIN is caught by PERCENT first
PERCENT = re.compile(r"RATIO|RATE|PCT|PERCENT|MARGIN$|SHARE|DISCOUNT", re.I)
HORIZON = {"day": 14, "week": 8, "month": 6, "quarter": 4}


COUNTS = re.compile(r"UNITS|_COUNT$|^COUNT|ORDERS$|CUSTOMERS$|HOURS|DAYS|WEEKS|QUANTITY", re.I)


def fmt_kind(metric_name: str, sample: Optional[float] = None) -> str:
    if PERCENT.search(metric_name) and (sample is None or abs(sample) <= 1.5):
        return "percent"
    if COUNTS.search(metric_name):
        return "number"
    if CURRENCY.search(metric_name):
        return "currency"
    return "number"


def fmt(v: Optional[float], kind: str = "number") -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "n/a"
    if kind == "percent":
        return f"{v * 100:.1f}%"
    a = abs(v)
    for div, suf in ((1e9, "B"), (1e6, "M"), (1e3, "K")):
        if a >= div:
            s = f"{v / div:.1f}{suf}"
            break
    else:
        s = f"{v:,.0f}" if a >= 100 or float(v).is_integer() else f"{v:,.2f}"
    return ("$" + s) if kind == "currency" else s


def pct(cur: Optional[float], base: Optional[float]) -> Optional[float]:
    if cur is None or base in (None, 0):
        return None
    return (cur - base) / abs(base)


class Deferred(Exception):
    """Component waits for a slower Snowflake ML step (filled in by a second pass)."""


class Engine(ChartTiles, PersonaTiles):
    def __init__(self, session, model: SemanticModel, b: Bindings, profile: Profile,
                 cortex=None, store=None, cache: Optional[dict] = None, log: Optional[list] = None,
                 defer_ml: bool = False, opts: Optional[dict] = None):
        self.defer_ml = defer_ml
        self.opts = opts or {}
        self.filters = {k: list(v) for k, v in (self.opts.get("filters") or {}).items() if v}
        self.compare = self.opts.get("compare") or "prior"
        self.fsig = json.dumps(self.filters, sort_keys=True) if self.filters else ""
        self.q = SemanticQuery(session, model, log)
        self.model = model
        self.b = b
        self.p = profile
        self.cal = profile.calendar
        self.cortex = cortex
        self.store = store
        self.cache = cache if cache is not None else {}
        self.log = log if log is not None else []
        self._memo: dict[str, Any] = {}
        self._tile: Optional[str] = None                    # component being built (links its queries for validation)
        self.tile_keys: dict[str, list[str]] = {}

    # -- shared datasets -----------------------------------------------------------
    def _memo_get(self, key: str, fn: Callable[[], Any]) -> Any:
        """Governed query results are shared across actions (cleared by Refresh)."""
        full = (f"q:{self.model.fqn}:{self.b.time_dimension}:{self.cal.grain}:{self.cal.window_start}:"
                f"{self.cal.current_start}:{self.fsig}:{key}")
        if full not in self.cache:
            with capturing() as got:
                value = fn()
            self.cache["__q__" + full] = got          # the governed queries behind it, for validation
            self.cache[full] = value
        if self._tile:
            keys = self.tile_keys.setdefault(self._tile, [])
            if full not in keys:
                keys.append(full)
        return self.cache[full]

    # -- filters ----------------------------------------------------------------------
    def allowed(self, metric: str, dim: str) -> bool:
        valid = getattr(self.model, "metric_dims", {}).get(str(metric).upper())
        return not valid or dim.upper() in valid

    def _flt(self, metrics) -> str:
        """WHERE clause for the global filters every given metric can be split by."""
        parts = []
        for dim, vals in self.filters.items():
            if not all(self.allowed(m, dim) for m in metrics):
                continue
            lits = ", ".join("'" + str(v).replace("'", "''") + "'" for v in vals)
            parts.append(f"{self.q.dim(dim).ref} IN ({lits})")
        return " AND ".join(parts)

    def skipped_filters(self, metrics) -> list[str]:
        return [self.dlabel(d) for d in self.filters if not all(self.allowed(m, d) for m in metrics)]

    def _series(self, metrics: list[str], dim: Optional[str] = None) -> list[dict[str, Any]]:
        """One query per group of metrics that share the same applicable filters; rows merged by period."""
        groups: dict[str, list[str]] = {}
        for m in metrics:
            groups.setdefault(self._flt([m]), []).append(m)
        if len(groups) <= 1:
            where, ms = next(iter(groups.items())) if groups else ("", metrics)
            return self.q.series(self.b.time_dimension, ms, self.cal, dim, where)
        merged: dict[tuple, dict[str, Any]] = {}
        for where, ms in groups.items():
            for r in self.q.series(self.b.time_dimension, ms, self.cal, dim, where):
                key = (r["period"], r.get("segment"))
                merged.setdefault(key, {k: v for k, v in r.items() if k in ("period", "segment")}).update(r)
        return [merged[k] for k in sorted(merged, key=lambda k: (k[0], str(k[1])))]

    def _by_dim(self, metrics: list[str], dims: list[str], start, end, limit: int = 200) -> list[dict[str, Any]]:
        return self.q.by_dim(self.b.time_dimension, metrics, dims, start, end, limit=limit, extra=self._flt(metrics))

    @property
    def kpis(self) -> list[str]:
        return [self.b.primary_metric] + [m for m in self.b.supporting_metrics if m != self.b.primary_metric]

    def kpi_series(self) -> list[dict[str, Any]]:
        return self._memo_get("kpi:" + ",".join(self.kpis),
                              lambda: self._series(self.kpis))

    def metric_series(self, metric: str) -> list[dict[str, Any]]:
        if metric in self.kpis:
            return self.kpi_series()
        return self._memo_get(f"m:{metric}", lambda: self._series([metric]))

    def multi_series(self, metrics: list[str]) -> list[dict[str, Any]]:
        if all(m in self.kpis for m in metrics):
            return self.kpi_series()
        return self._memo_get("multi:" + ",".join(metrics),
                              lambda: self._series(metrics))

    def window_by_dim(self, metrics: list[str], dims: list[str], periods: int = 12) -> list[dict[str, Any]]:
        start = max(self.cal.window_start, shift(self.cal.current_start, self.cal.grain, -(periods - 1)))
        return self._memo_get(f"win:{periods}:{','.join(metrics)}:{','.join(dims)}",
                              lambda: self._by_dim(metrics, dims, start, self.cal.end_exclusive, limit=500))

    def window_label(self, periods: int = 12) -> str:
        start = max(self.cal.window_start, shift(self.cal.current_start, self.cal.grain, -(periods - 1)))
        return f"{self.cal.label(start)} – {self.cal.label(self.cal.current_start)}"

    def seg_series(self, metric: str, dim: str) -> list[dict[str, Any]]:
        return self._memo_get(f"seg:{metric}:{dim}",
                              lambda: self._series([metric], dim))

    def label(self, period_iso: str) -> str:
        return self.cal.label(dt.date.fromisoformat(period_iso))

    def mlabel(self, metric_id: str) -> str:
        return self.model.field(metric_id, ("metric",)).label

    def dlabel(self, dim_id: str) -> str:
        return self.model.field(dim_id, ("dimension",)).label

    def value_at(self, series: list[dict], metric: str, start: dt.date) -> Optional[float]:
        iso = start.isoformat()
        for row in series:
            if row["period"] == iso:
                return row.get(metric)
        return None

    def kind_of(self, metric: str) -> str:
        key = f"kind:{metric}"
        if key in self._memo:
            return self._memo[key]
        name = self.model.field(metric, ("metric",)).name
        if not PERCENT.search(name):          # the sample only matters for ratio-looking names
            self._memo[key] = fmt_kind(name)
            return self._memo[key]
        series = next((v for k, v in self.cache.items()
                       if isinstance(v, list) and v and isinstance(v[0], dict) and metric in v[0]), None)
        if series is None:
            try:
                series = self.metric_series(metric)
            except Exception:
                series = []
        sample = next((r.get(metric) for r in reversed(series) if r.get(metric) is not None), None)
        self._memo[key] = fmt_kind(self.model.field(metric, ("metric",)).name, sample)
        return self._memo[key]

    # -- component builders ---------------------------------------------------------------
    def plan_metric(self, metric: str) -> Optional[str]:
        """The plan/target metric that pairs with a metric (PLAN_NET_SALES for NET_SALES, ...)."""
        names = {x.name.upper(): x.id for x in self.model.metrics}
        n = self.model.field(metric, ("metric",)).name.upper()
        for cand in (f"PLAN_{n}", "PLAN_" + n.replace("_SOLD", ""), "PLAN_" + n.split("_")[0]):
            if cand in names and names[cand] != metric:
                return names[cand]
        return None

    def kpi_grid(self, comp) -> dict[str, Any]:
        metrics = [m for m in (comp.get("metrics") or []) if m in {x.id for x in self.model.metrics}] or self.kpis
        s = self.multi_series(metrics)
        cur, prior, yoy = self.cal.current_start, self.cal.prior_start, self.cal.yoy_start
        spark_rows = s[-13:]
        spark_labels = [self.label(r["period"]) for r in spark_rows]
        items, facts = [], []
        for m in metrics:
            kind = self.kind_of(m)
            c, p, y = self.value_at(s, m, cur), self.value_at(s, m, prior), self.value_at(s, m, yoy)
            base, base_label, plan_id = p, self.cal.label(prior), None
            if self.compare == "yoy":
                base, base_label = y, self.cal.label(yoy)
            elif self.compare == "plan":
                plan_id = self.plan_metric(m)
                if plan_id:
                    base, base_label = self.value_at(self.metric_series(plan_id), plan_id, cur), "plan"
                else:
                    base_label = self.cal.label(prior) + " (no plan)"
            items.append({"metric": m, "label": self.mlabel(m), "kind": kind, "current": c, "prior": p,
                          "yoy": y, "change": pct(c, p), "yoy_change": pct(c, y),
                          "base": base, "delta": pct(c, base), "delta_label": "vs " + base_label,
                          "delta_pt": (c - base) if kind == "percent" and c is not None and base is not None else None,
                          "spark": [r.get(m) for r in spark_rows]})
            facts.append(f"{self.mlabel(m)} {self.cal.label(cur)} = {fmt(c, kind)}"
                         + ((f" ({(c - base) * 100:+.1f} percentage points vs {base_label}, {fmt(base, kind)})" if kind == "percent"
                             else f" ({pct(c, base) * 100:+.1f}% vs {base_label}, {fmt(base, kind)})") if pct(c, base) is not None else "")
                         + ((f" ({(c - y) * 100:+.1f} percentage points vs {self.cal.label(yoy)})" if kind == "percent"
                             else f" ({pct(c, y) * 100:+.1f}% vs {self.cal.label(yoy)})")
                            if pct(c, y) is not None and self.compare != "yoy" else ""))
        return {"items": items, "current_label": self.cal.label(cur), "prior_label": self.cal.label(prior),
                "yoy_label": self.cal.label(yoy), "compare": self.compare, "grain": self.cal.grain,
                "spark_labels": spark_labels,
                "spark_caption": f"Last {len(spark_rows)} {self.cal.grain}s", "_facts": facts}

    def kpi_card(self, comp) -> dict[str, Any]:
        data = self.kpi_grid(comp)
        metric = comp.get("metric_id") or self.b.primary_metric
        data["items"] = [i for i in data["items"] if i["metric"] == metric] or data["items"][:1]
        return data

    def _metric_for(self, comp) -> str:
        mid = comp.get("metric_id") or ""
        if mid and ":" not in mid and mid in {m.id for m in self.model.metrics}:
            return mid
        for role in ("strategic_kpi", "manager_kpi", "wbr_kpi"):
            if role in comp.get("role_bindings", {}):
                return comp["role_bindings"][role]
        return self.b.primary_metric

    def trend_chart(self, comp) -> dict[str, Any]:
        m = self._metric_for(comp)
        s = self.metric_series(m)
        with_baseline = comp.get("role_bindings", {}).get("target") == SOURCE_BASELINE
        per_year = {"day": 364, "week": 52, "month": 12, "quarter": 4}[self.cal.grain]
        points = []
        by_iso = {r["period"]: r.get(m) for r in s}
        show = s[-(per_year + 1):] if with_baseline else s
        for r in show:
            start = dt.date.fromisoformat(r["period"])
            base = by_iso.get(shift(start, self.cal.grain, -per_year).isoformat()) if with_baseline else None
            points.append({"period": r["period"], "label": self.label(r["period"]), "value": r.get(m),
                           "baseline": base})
        kind = self.kind_of(m)
        facts = []
        if points:
            last = points[-1]
            facts.append(f"{self.mlabel(m)} trend over {len(points)} {self.cal.grain}s; latest {last['label']} "
                         f"= {fmt(last['value'], kind)}"
                         + (f", prior-year baseline {fmt(last['baseline'], kind)}" if last.get("baseline") is not None else ""))
            vals = [p["value"] for p in points if p["value"] is not None]
            if vals:
                hi = max(points, key=lambda p: p["value"] or -1e30)
                facts.append(f"Peak {self.mlabel(m)} in window: {hi['label']} ({fmt(hi['value'], kind)})")
        return {"metric": m, "metric_label": self.mlabel(m), "kind": kind, "points": points,
                "baseline_label": "Prior-year baseline" if with_baseline else None, "_facts": facts}

    def forecast_band(self, comp) -> dict[str, Any]:
        m = self._metric_for(comp)
        key0 = f"fc:{self.model.fqn}:{m}:{self.cal.grain}:{self.cal.current_start}:{self.fsig}"
        if self.defer_ml and key0 not in self.cache:
            raise Deferred("Training Snowflake ML FORECAST…")
        s = self.metric_series(m)
        history = [(r["period"], r.get(m)) for r in s]
        key = f"fc:{self.model.fqn}:{m}:{self.cal.grain}:{self.cal.current_start}:{self.fsig}"
        if key not in self.cache:
            if not self.cortex:
                raise RuntimeError("Snowflake ML FORECAST is not available")
            self.cache[key] = self.cortex.forecast(history, HORIZON[self.cal.grain], self.cal.grain)
        fc = self.cache[key]
        kind = self.kind_of(m)
        hist = [{"period": p, "label": self.label(p), "value": v} for p, v in history][-24:]
        pts = [{**pt, "label": self.cal.label(dt.date.fromisoformat(pt["period"][:10]))} for pt in fc["points"]]
        facts = []
        if pts:
            total = sum(p["forecast"] for p in pts)
            facts.append(f"Snowflake ML forecast for {self.mlabel(m)} next {len(pts)} {self.cal.grain}s totals "
                         f"{fmt(total, kind)} (first: {pts[0]['label']} {fmt(pts[0]['forecast'], kind)}, "
                         f"range {fmt(pts[0]['lower'], kind)}–{fmt(pts[0]['upper'], kind)})")
        return {"metric": m, "metric_label": self.mlabel(m), "kind": kind, "history": hist, "forecast": pts,
                "provenance": fc.get("provenance"), "_facts": facts}

    def _snapshot(self, metric: str, dim: str) -> list[dict[str, Any]]:
        s = self.seg_series(metric, dim)
        cur, prior, yoy = (self.cal.current_start.isoformat(), self.cal.prior_start.isoformat(),
                           self.cal.yoy_start.isoformat())
        rows: dict[str, dict[str, Any]] = {}
        for r in s:
            seg = r["segment"]
            row = rows.setdefault(seg, {"segment": seg, "current": None, "prior": None, "yoy": None})
            if r["period"] == cur:
                row["current"] = r.get(metric)
            elif r["period"] == prior:
                row["prior"] = r.get(metric)
            elif r["period"] == yoy:
                row["yoy"] = r.get(metric)
        out = [r for r in rows.values() if r["current"] is not None or r["prior"] is not None]
        total = sum((r["current"] or 0) for r in out) or None
        for r in out:
            r["change"] = pct(r["current"], r["prior"])
            r["yoy_change"] = pct(r["current"], r["yoy"])
            r["share"] = (r["current"] or 0) / total if total else None
        out.sort(key=lambda r: r["current"] or 0, reverse=True)
        return out

    def _segment_dim(self, comp) -> str:
        if comp.get("dimension"):
            return comp["dimension"]
        rb = comp.get("role_bindings", {})
        return rb.get("segment") or rb.get("team_or_segment") or rb.get("region") or self.b.segment_dimension

    def ranked_bar(self, comp) -> dict[str, Any]:
        m, dim = self._metric_for(comp), self._segment_dim(comp)
        rows = self._snapshot(m, dim)[:15]
        kind = self.kind_of(m)
        facts = [f"{self.dlabel(dim)} ranking for {self.mlabel(m)} in {self.cal.label(self.cal.current_start)}: "
                 + "; ".join(f"{r['segment']} {fmt(r['current'], kind)}"
                             + (f" ({r['change'] * 100:+.1f}% vs prior)" if r['change'] is not None else "")
                             for r in rows[:6])]
        return {"metric": m, "metric_label": self.mlabel(m), "dimension_label": self.dlabel(dim), "kind": kind,
                "rows": rows, "current_label": self.cal.label(self.cal.current_start),
                "prior_label": self.cal.label(self.cal.prior_start), "_facts": facts}

    target_bar = ranked_bar
    capacity_chart = ranked_bar

    def small_multiples(self, comp) -> dict[str, Any]:
        m, dim = self._metric_for(comp), self._segment_dim(comp)
        s = self.seg_series(m, dim)
        top = [r["segment"] for r in self._snapshot(m, dim)[:6]]
        periods = sorted({r["period"] for r in s})[-(26 if self.cal.grain == "week" else 13):]
        panels = []
        for seg in top:
            by = {r["period"]: r.get(m) for r in s if r["segment"] == seg}
            panels.append({"segment": seg, "points": [{"period": p, "label": self.label(p), "value": by.get(p)}
                                                     for p in periods]})
        facts = []
        for panel in panels:
            vals = [pt["value"] for pt in panel["points"] if pt["value"] is not None]
            if len(vals) >= 2:
                facts.append(f"{panel['segment']}: {fmt(vals[0], self.kind_of(m))} → {fmt(vals[-1], self.kind_of(m))} "
                             f"over {len(vals)} {self.cal.grain}s")
        return {"metric": m, "metric_label": self.mlabel(m), "dimension_label": self.dlabel(dim),
                "kind": self.kind_of(m), "panels": panels, "_facts": facts}

    def driver_bridge(self, comp) -> dict[str, Any]:
        m, dim = self._metric_for(comp), comp.get("dimension") or self.b.segment_dimension
        rows = self._snapshot(m, dim)
        kind = self.kind_of(m)
        start = sum((r["prior"] or 0) for r in rows)
        end = sum((r["current"] or 0) for r in rows)
        deltas = sorted(({"segment": r["segment"], "delta": (r["current"] or 0) - (r["prior"] or 0)} for r in rows),
                        key=lambda d: abs(d["delta"]), reverse=True)
        top, rest = deltas[:7], deltas[7:]
        if rest:
            top.append({"segment": f"Other ({len(rest)})", "delta": sum(d["delta"] for d in rest)})
        reconciled = abs(start + sum(d["delta"] for d in top) - end) < 1e-6 * max(1.0, abs(end))
        facts = [f"{self.mlabel(m)} moved from {fmt(start, kind)} ({self.cal.label(self.cal.prior_start)}) to "
                 f"{fmt(end, kind)} ({self.cal.label(self.cal.current_start)}); biggest contributors: "
                 + "; ".join(f"{d['segment']} {'+' if d['delta'] >= 0 else '−'}{fmt(abs(d['delta']), kind)}"
                             for d in top[:4])]
        insights, insight_note = [], ""
        pending = False
        if self.cortex and self.b.use_drivers:
            key = f"ti:{self.model.fqn}:{m}:{dim}:{self.cal.grain}:{self.cal.current_start}:{self.fsig}"
            if key not in self.cache and self.defer_ml:
                pending = True
            elif key not in self.cache:
                try:
                    self.cache[key] = {"rows": self._top_insights(m, dim), "error": ""}
                except Exception as exc:
                    self.cache[key] = {"rows": [], "error": str(exc)[:240]}
            if not pending:
                insights = self.cache[key]["rows"][:6]
                insight_note = self.cache[key]["error"]
            for ins in insights[:3]:
                facts.append("Snowflake ML Top Insights driver: " + " & ".join(ins["contributor"])
                             + f" contributed {fmt(ins['contribution'], kind)}")
        return {"metric": m, "metric_label": self.mlabel(m), "dimension_label": self.dlabel(dim), "kind": kind,
                "start": start, "end": end, "steps": top, "reconciled": reconciled,
                "start_label": self.cal.label(self.cal.prior_start), "end_label": self.cal.label(self.cal.current_start),
                "insights": insights, "insights_error": insight_note, "insights_pending": pending,
                "_facts": facts}

    def _top_insights(self, metric: str, first_dim: str = "") -> list[dict[str, Any]]:
        valid = getattr(self.model, "metric_dims", {}).get(metric.upper())
        ok = (lambda d: valid is None or not valid or d.upper() in valid)
        cats = list(dict.fromkeys(d for d in (first_dim, self.b.segment_dimension, self.b.region_dimension) if d and ok(d)))
        extra = [d.id for d in self.model.categorical_dimensions if d.id not in cats and ok(d.id)]
        cats += extra[: max(0, 4 - len(cats))]
        time = self.q.dim(self.b.time_dimension)
        dims = [self.q.trunc(time, self.cal.grain)] + [f"{self.q.dim(d).ref} AS D{i}" for i, d in enumerate(cats)]
        where = self.q.range_where(time, self.cal.prior_start, shift(self.cal.current_start, self.cal.grain, 1))
        if self._flt([metric]):
            where += " AND " + self._flt([metric])
        inner = self.q.sv(dims, [f"{self.q.metric(metric).ref} AS M0"], where)
        names = {f"D{i}": self.dlabel(d) for i, d in enumerate(cats)}
        cols = ", ".join(f"COALESCE(TO_VARCHAR(D{i}), '(blank)') AS \"{names[f'D{i}']}\"" for i in range(len(cats)))
        select = (f"SELECT {cols}, M0::FLOAT AS METRIC, (PERIOD = TO_DATE('{self.cal.current_start.isoformat()}')) "
                  f"AS LABEL FROM {inner}")
        key = f"{self.model.fqn}:{metric}:{self.cal.grain}:{self.cal.current_start}:{','.join(cats)}:{self.fsig}"
        return self.cortex.top_insights(select, key)

    def _exceptions(self, comp) -> dict[str, Any]:
        """Segments whose latest period is abnormal vs their own history.
        Primary: Snowflake ML ANOMALY_DETECTION (multi-series, 95% prediction interval), trained in phase 2.
        Phase 1 / fallback: z-score vs each segment's trailing 12-period mean."""
        m, dim = self._metric_for(comp), self._segment_dim(comp)
        s = self.seg_series(m, dim)
        kind = self.kind_of(m)
        cur_iso = self.cal.current_start.isoformat()
        by_seg: dict[str, list[tuple[str, float]]] = {}
        for r in s:
            if r.get(m) is not None:
                by_seg.setdefault(r["segment"], []).append((r["period"], r[m]))
        key = f"ad:{self.model.fqn}:{m}:{dim}:{self.cal.grain}:{cur_iso}:{self.fsig}"
        ml, ml_note, pending = None, "", False
        if key in self.cache:
            ml = self.cache[key]
        elif self.cortex and (self.cortex.features or {}).get("anomaly", True):
            if self.defer_ml:
                pending = True
            else:
                try:
                    ml = self.cache[key] = self.cortex.anomalies(by_seg, cur_iso)
                except Exception as exc:
                    ml = self.cache[key] = {"error": str(exc)[:300]}
        if ml and ml.get("error"):
            ml_note, ml = ml["error"], None

        rows = []
        for seg, pts in by_seg.items():
            hist = [v for p, v in pts if p < cur_iso][-12:]
            cur = next((v for p, v in pts if p == cur_iso), None)
            if cur is None or len(hist) < 4:
                continue
            a = (ml or {}).get("segments", {}).get(str(seg)) if ml else None
            if a:
                half = max((a["upper"] - a["lower"]) / 2, 1e-12)
                z = (cur - a["forecast"]) / (half / 1.96)          # standardised distance from the ML forecast
                sev = ("High" if a["is_anomaly"] and abs(z) >= 3 else "Medium" if a["is_anomaly"] else "Watch")
                rows.append({"segment": seg, "current": cur, "expected": a["forecast"], "lower": a["lower"],
                             "upper": a["upper"], "deviation": pct(cur, a["forecast"]), "z": z,
                             "is_anomaly": a["is_anomaly"], "direction": "above" if z > 0 else "below",
                             "severity": sev})
                continue
            mean = statistics.fmean(hist)
            sd = statistics.pstdev(hist)
            z = (cur - mean) / sd if sd > 0 else 0.0
            rows.append({"segment": seg, "current": cur, "expected": mean, "deviation": pct(cur, mean), "z": z,
                         "is_anomaly": abs(z) >= 2, "direction": "above" if z > 0 else "below",
                         "severity": "High" if abs(z) >= 3 else "Medium" if abs(z) >= 2 else "Low"})
        rows.sort(key=lambda r: abs(r["z"]), reverse=True)
        flagged = [r for r in rows if r["is_anomaly"]]
        none_flagged = not flagged
        if none_flagged:          # nothing is abnormal: show the closest movers, clearly labelled as "Watch"
            flagged = [{**r, "severity": "Watch"} for r in rows[:3]]
        facts = [f"{r['segment']} {self.mlabel(m)} {fmt(r['current'], kind)} is {abs(r['deviation'] or 0) * 100:.0f}% "
                 f"{r['direction']} its expected level ({fmt(r['expected'], kind)})"
                 + (" — flagged by Snowflake ML ANOMALY_DETECTION" if ml else f", z={r['z']:+.1f}")
                 for r in flagged[:4]]
        if ml:
            method = (f"One model across {ml.get('trained_series', len(rows))} "
                      f"{self.dlabel(dim).lower()} series, trained on prior {self.cal.grain}s; latest "
                      f"{self.cal.grain} outside the 95% prediction interval is flagged.")
        else:
            method = (f"Latest {self.cal.grain} vs each segment's trailing 12-{self.cal.grain} mean; |z| ≥ 2 flagged."
                      + (" Snowflake ML anomaly model is training…" if pending else "")
                      + (f" (ML anomaly detection unavailable: {ml_note[:120]})" if ml_note else ""))
        return {"metric": m, "metric_label": self.mlabel(m), "dimension_label": self.dlabel(dim), "kind": kind,
                "rows": flagged[:10], "none_flagged": none_flagged, "method": method,
                "ml": bool(ml), "provenance": (ml or {}).get("provenance"), "insights_pending": pending,
                "_facts": facts}

    exception_table = _exceptions
    exception_queue = _exceptions
    risk_table = _exceptions

    def action_table(self, comp) -> dict[str, Any]:
        rows = self.store.list_decisions(self.model.fqn) if self.store else []
        open_n = sum(1 for r in rows if r.get("status") != "Done")
        return {"rows": rows, "_facts": [f"{len(rows)} decisions logged, {open_n} open"] if rows else []}

    def evidence_table(self, comp) -> dict[str, Any]:
        dims = comp.get("dimensions") or [d for d in (self._segment_dim(comp), self.b.region_dimension) if d]
        dims = list(dict.fromkeys(dims))
        metrics = comp.get("metrics") or self.kpis
        rows = self._memo_get(f"detail:{','.join(metrics)}:{','.join(dims)}", lambda: self._by_dim(
            metrics, dims, self.cal.current_start, shift(self.cal.current_start, self.cal.grain, 1), limit=50))
        cols = [{"id": d, "label": self.dlabel(d), "type": "dim"} for d in dims] + \
               [{"id": m, "label": self.mlabel(m), "type": "metric", "kind": self.kind_of(m)} for m in metrics]
        return {"columns": cols, "rows": rows, "period_label": self.cal.label(self.cal.current_start), "_facts": []}

    def segment_matrix(self, comp) -> dict[str, Any]:
        m = self._metric_for(comp)
        d1 = comp.get("dimension") or self.b.segment_dimension
        d2 = comp.get("dimension2") or self.b.region_dimension
        if not d2:
            raise RuntimeError("Needs a second dimension")
        rows = self._memo_get(f"matrix:{m}:{d1}:{d2}", lambda: self._by_dim(
            [m], [d1, d2], self.cal.current_start, shift(self.cal.current_start, self.cal.grain, 1), limit=900))
        kind = self.kind_of(m)
        cols = sorted({r[d2] for r in rows})[:12]
        rws = sorted({r[d1] for r in rows})[:15]
        cells = {(r[d1], r[d2]): r[m] for r in rows}
        best = max(rows, key=lambda r: r[m] or -1e30) if rows else None
        facts = [f"Largest {self.dlabel(d1)} x {self.dlabel(d2)} cell: {best[d1]} / {best[d2]} "
                 f"{fmt(best[m], kind)}"] if best else []
        return {"metric_label": self.mlabel(m), "kind": kind, "row_label": self.dlabel(d1), "col_label": self.dlabel(d2),
                "rows": rws, "cols": cols, "values": [[cells.get((r, c)) for c in cols] for r in rws], "_facts": facts}

    detail_table = evidence_table
    heatmap = segment_matrix

    def period_compare(self, comp) -> dict[str, Any]:
        m, dim = self._metric_for(comp), self._segment_dim(comp)
        rows = self._snapshot(m, dim)[:15]
        kind = self.kind_of(m)
        facts = [f"{self.mlabel(m)} by {self.dlabel(dim)}, {self.cal.label(self.cal.current_start)} vs "
                 f"{self.cal.label(self.cal.prior_start)} vs {self.cal.label(self.cal.yoy_start)}: "
                 + "; ".join(f"{r['segment']} {fmt(r['current'], kind)}"
                             + (f" ({r['yoy_change'] * 100:+.1f}% YoY)" if r['yoy_change'] is not None else "")
                             for r in rows[:6])]
        return {"metric_label": self.mlabel(m), "dimension_label": self.dlabel(dim), "kind": kind, "rows": rows,
                "labels": [self.cal.label(self.cal.current_start), self.cal.label(self.cal.prior_start),
                           self.cal.label(self.cal.yoy_start)], "_facts": facts}

    def share_donut(self, comp) -> dict[str, Any]:
        m, dim = self._metric_for(comp), self._segment_dim(comp)
        rows = [r for r in self._snapshot(m, dim) if (r["current"] or 0) > 0]
        kind = self.kind_of(m)
        total = sum(r["current"] for r in rows)
        slices = [{"label": r["segment"], "value": r["current"], "share": r["current"] / total if total else None,
                   "prior_share": None} for r in rows[:8]]
        if len(rows) > 8:
            rest = sum(r["current"] for r in rows[8:])
            slices.append({"label": f"Other ({len(rows) - 8})", "value": rest, "share": rest / total if total else None})
        facts = [f"Share of {self.mlabel(m)} by {self.dlabel(dim)} in {self.cal.label(self.cal.current_start)}: "
                 + "; ".join(f"{x['label']} {x['share'] * 100:.0f}%" for x in slices[:6] if x["share"] is not None)]
        return {"metric_label": self.mlabel(m), "dimension_label": self.dlabel(dim), "kind": kind,
                "total": total, "slices": slices, "period_label": self.cal.label(self.cal.current_start),
                "_facts": facts}

    def pareto(self, comp) -> dict[str, Any]:
        m, dim = self._metric_for(comp), self._segment_dim(comp)
        rows = [r for r in self.window_by_dim([m], [dim]) if r.get(m) is not None]
        rows.sort(key=lambda r: r[m], reverse=True)
        kind = self.kind_of(m)
        total = sum(max(0.0, r[m]) for r in rows) or None
        run, out, n80 = 0.0, [], None
        for i, r in enumerate(rows[:30]):
            run += max(0.0, r[m])
            cum = run / total if total else None
            out.append({"label": r[dim], "value": r[m], "cum_share": cum})
            if n80 is None and cum is not None and cum >= 0.8:
                n80 = i + 1
        facts = [f"{n80} of {len(rows)} {self.dlabel(dim)} values make up 80% of {self.mlabel(m)} "
                 f"({self.window_label()})"] if n80 else []
        return {"metric_label": self.mlabel(m), "dimension_label": self.dlabel(dim), "kind": kind, "rows": out,
                "total_count": len(rows), "n80": n80, "period_label": self.window_label(), "_facts": facts}

    def scatter(self, comp) -> dict[str, Any]:
        m, dim = self._metric_for(comp), self._segment_dim(comp)
        m2 = comp.get("metric2_id")
        if not m2:
            raise RuntimeError("Scatter needs a second metric")
        rows = [r for r in self.window_by_dim([m, m2], [dim]) if r.get(m) is not None and r.get(m2) is not None]
        pts = [{"label": r[dim], "x": r[m], "y": r[m2]} for r in rows[:150]]
        kx, ky = self.kind_of(m), self.kind_of(m2)
        facts = []
        if len(pts) >= 3:
            low = min(pts, key=lambda p: p["y"])
            facts.append(f"Across {len(pts)} {self.dlabel(dim)} values ({self.window_label()}), lowest "
                         f"{self.mlabel(m2)} is {low['label']} ({fmt(low['y'], ky)}) at "
                         f"{self.mlabel(m)} {fmt(low['x'], kx)}")
        return {"x_label": self.mlabel(m), "y_label": self.mlabel(m2), "x_kind": kx, "y_kind": ky,
                "dimension_label": self.dlabel(dim), "points": pts, "period_label": self.window_label(),
                "_facts": facts}

    # -- orchestration ---------------------------------------------------------------------
    def prefetch(self, spec: dict[str, Any]) -> None:
        """Run the shared governed queries concurrently (Snowpark sessions are thread-safe)."""
        jobs: dict[str, Callable[[], Any]] = {"kpi_series": self.kpi_series}
        seg_kinds = {"ranked_bar", "target_bar", "capacity_chart", "small_multiples", "driver_bridge",
                     "exception_table", "exception_queue", "risk_table", "period_compare", "share_donut"}
        for p in spec["pages"]:
            for c in p["components"]:
                if c["state"] != "ready":
                    continue
                try:
                    m = self._metric_for(c)
                    if c["type"] in seg_kinds:
                        d = self._segment_dim(c) if c["type"] != "driver_bridge" else (
                            c.get("dimension") or self.b.segment_dimension)
                        if d:
                            jobs[f"seg:{m}:{d}"] = (lambda m=m, d=d: self.seg_series(m, d))
                    elif c["type"] in ("trend_chart", "forecast_band"):
                        jobs[f"m:{m}"] = (lambda m=m: self.metric_series(m))
                    elif c["type"] in ("kpi_grid", "kpi_card") and c.get("metrics"):
                        jobs["multi:" + ",".join(c["metrics"])] = (lambda ms=c["metrics"]: self.multi_series(ms))
                    elif c["type"] == "pareto":
                        d = self._segment_dim(c)
                        jobs[f"win:{m}:{d}"] = (lambda m=m, d=d: self.window_by_dim([m], [d]))
                    elif c["type"] == "scatter" and c.get("metric2_id"):
                        d, m2 = self._segment_dim(c), c["metric2_id"]
                        jobs[f"win:{m}:{m2}:{d}"] = (lambda m=m, m2=m2, d=d: self.window_by_dim([m, m2], [d]))
                except Exception:
                    continue
        try:
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor(max_workers=min(8, len(jobs))) as pool:
                for f in [pool.submit(fn) for fn in jobs.values()]:
                    f.result()
        except Exception:
            pass   # fall back to sequential, lazily inside each builder

    def build(self, spec: dict[str, Any]) -> tuple[dict[str, Any], dict[str, list[str]]]:
        self.prefetch(spec)
        results: dict[str, Any] = {}
        facts: dict[str, list[str]] = {}
        for page in spec["pages"]:
            page_facts: list[str] = []
            for comp in page["components"]:
                cid = f"{page['page_id']}/{comp['component_id']}"
                if comp["state"] != "ready":
                    results[cid] = {"status": comp["state"], "missing": comp.get("missing_requirements", [])}
                    continue
                fn = getattr(self, comp["type"], None)
                started = time.time()
                self._tile = cid
                if fn is None:
                    results[cid] = {"status": "error", "error": f"No renderer for {comp['type']}"}
                    continue
                try:
                    data = fn(comp)
                    page_facts += data.pop("_facts", [])
                    data["headline"] = tile_headline(comp["type"], data, fmt)
                    results[cid] = {"status": "ready", "data": data, "ms": int((time.time() - started) * 1000)}
                    used = [x for x in [comp.get("metric_id") if ":" not in str(comp.get("metric_id") or ":") else None,
                                        comp.get("metric2_id"), *(comp.get("metrics") or [])] if x]
                    skipped = self.skipped_filters(used or [self._metric_for(comp)]) if self.filters else []
                    if skipped:
                        results[cid]["skipped_filters"] = skipped
                except Deferred as wait:
                    results[cid] = {"status": "pending", "message": str(wait)}
                except Exception as exc:
                    results[cid] = {"status": "error", "error": str(exc)[:600]}
            facts[page["page_id"]] = page_facts
        self._tile = None
        return results, facts
