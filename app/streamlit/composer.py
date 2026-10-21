"""Generative, governed layouts.

Cortex designs the dashboard (pages, tiles, chart types, metric/dimension choices,
titles, questions) from a profile of the actual data plus the user's goal. Every
tile is then checked against the tile vocabulary, the semantic view's real field
IDs, and proven data capabilities. Invalid tiles are repaired or dropped, and each
decision is recorded so the Governance panel can show *why*.

Cortex never writes SQL or chart code here: it chooses from a closed vocabulary,
and the engine computes every number through SEMANTIC_VIEW queries.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from typing import Any, Optional

from engine import fmt_kind
from inventory import Bindings, Profile
from semantic_catalog import SemanticModel

WIDTHS = (3, 4, 5, 6, 7, 8, 9, 12)
MAX_PAGES = 4
MAX_TILES = 6

# type -> requirements. dim_range = (min, max) distinct values for "dimension".
TILES: dict[str, dict[str, Any]] = {
    "kpi_grid": {"label": "KPI cards", "fields": ["metrics"], "width": 12,
                 "use": "Headline values for 1-8 metrics, change vs prior period and prior year, sparklines "
                        "(show_trend=false hides them)."},
    "trend_chart": {"label": "Trend line", "fields": ["metric"], "time": True, "width": 7,
                    "use": "One metric over time (with prior-year baseline when available)."},
    "forecast_band": {"label": "Forecast", "fields": ["metric"], "time": True, "caps": ["forecast_versioned"],
                      "width": 8, "use": "Snowflake ML FORECAST of one metric with 80% band."},
    "ranked_bar": {"label": "Ranked bars", "fields": ["metric", "dimension"], "dim_range": (2, 100000), "width": 5,
                   "use": "Rank dimension values by a metric (top 15) with prior-period marker."},
    "period_compare": {"label": "Period comparison", "fields": ["metric", "dimension"], "dim_range": (2, 15),
                       "width": 6, "use": "Current vs prior period vs prior year for each value of a small dimension."},
    "share_donut": {"label": "Share donut", "fields": ["metric", "dimension"], "dim_range": (2, 10),
                    "additive": True, "width": 4, "use": "Share of an additive metric across a small dimension."},
    "pareto": {"label": "Pareto", "fields": ["metric", "dimension"], "dim_range": (5, 100000), "additive": True,
               "width": 6, "use": "Concentration: sorted contribution with cumulative % line (80/20)."},
    "scatter": {"label": "Scatter", "fields": ["metric", "metric2", "dimension"], "dim_range": (4, 100000),
                "width": 6, "use": "Relationship between two metrics across dimension values (e.g. sales vs profit)."},
    "heatmap": {"label": "Heatmap", "fields": ["metric", "dimension", "dimension2"], "dim_range": (2, 30),
                "dim2_range": (2, 30), "width": 12, "use": "Metric across two dimensions (matrix)."},
    "small_multiples": {"label": "Small multiples", "fields": ["metric", "dimension"], "dim_range": (2, 60),
                        "time": True, "width": 12, "use": "Mini trend per top-6 dimension value."},
    "driver_bridge": {"label": "Driver bridge", "fields": ["metric", "dimension"], "dim_range": (2, 60),
                      "additive": True, "time": True, "width": 7,
                      "use": "Waterfall of what drove the change vs prior period + Snowflake ML Top Insights."},
    "exception_table": {"label": "Exceptions", "fields": ["metric", "dimension"], "dim_range": (2, 200),
                        "time": True, "width": 5,
                        "use": "Dimension values whose latest period deviates >= 2 sigma from their history."},
    "detail_table": {"label": "Detail table", "fields": ["dimensions", "metrics"], "width": 12,
                     "use": "Table of 1-3 dimensions x 1-6 metrics for the latest period."},
    "combo_chart": {"label": "Bars + line", "fields": ["metric", "metric2"], "time": True, "width": 7,
                    "use": "One metric as bars and a second metric (often a rate, e.g. margin %) as a line on its own "
                           "axis, over time: volume and rate together."},
    "treemap": {"label": "Treemap", "fields": ["metric", "dimension"], "dim_range": (3, 100000), "additive": True,
                "dim2_range": (2, 60), "width": 6,
                "use": "Where an additive, positive metric sits across a dimension (optionally nested by dimension2, "
                       "e.g. category > sub-category); box size = value, change vs prior on each box."},
    "gauge": {"label": "Progress gauge", "fields": ["metric"], "time": True, "cumulative": True, "width": 5,
              "use": "Year-to-date progress of one additive metric toward its full-year target (plan, else last "
                     "year's total), with where it should be by now and the projected finish."},
    "pnl_table": {"label": "P&L table", "fields": ["metrics", "dimension"], "dim_range": (2, 12), "width": 12,
                  "use": "Statement-style table: 2-8 metrics as rows, the values of a small dimension as columns plus "
                         "a total, each cell coloured by its change vs the comparison period."},
    "action_table": {"label": "Decision log", "fields": [], "width": 12,
                     "use": "Decisions with owner/due/status, stored in Snowflake."},
    # persona tiles (persona_tiles.py)
    "kpi_plan": {"label": "KPIs vs plan", "fields": ["metrics"], "time": True, "width": 12, "persona": "executives",
                 "use": "Executive headline: year-to-date value per metric vs plan (or last year when there is no "
                        "plan), with a bullet bar, latest month, and optional monthly trend lines "
                        "(show_trend=false hides them)."},
    "ytd_trajectory": {"label": "YTD trajectory", "fields": ["metric"], "time": True, "cumulative": True, "width": 7,
                       "persona": "executives",
                       "use": "Cumulative year-to-date vs plan vs last year, with a Snowflake ML forecast to year end."},
    "scorecard": {"label": "Scorecard", "fields": ["metrics", "dimension"], "dim_range": (2, 40), "time": True,
                  "width": 8, "persona": "managers",
                  "use": "Table of dimension values x KPIs with variance vs plan (or prior period), red/amber/green; "
                         "click a row to filter the dashboard to it."},
    "status_tiles": {"label": "Live status", "fields": ["metrics"], "time": True, "width": 12,
                     "persona": "daily_operations",
                     "use": "Today so far vs the same time on the same weekday last week, with status colours."},
    "pace_chart": {"label": "Today's pace", "fields": ["metric"], "time": True, "cumulative": True, "width": 7,
                   "persona": "daily_operations",
                   "use": "Cumulative value by hour today vs the same weekday last week (by day of month if the "
                          "view has no hour dimension)."},
    "hour_heatmap": {"label": "Hour x day heatmap", "fields": ["metric"], "time": True, "hour": True, "width": 5,
                     "persona": "daily_operations", "use": "Metric by hour of day for the last 7 days."},
    "worklist": {"label": "Worklist", "fields": ["metrics", "dimensions"], "time": True, "width": 12,
                 "persona": "daily_operations",
                 "use": "What deviates today (vs the same weekday in the last 4 weeks) across metrics x "
                        "breakdowns, worst first, with Ask agent / Log decision on each row."},
}
METRIC_LIST_TYPES = ("kpi_grid", "detail_table", "kpi_plan", "scorecard", "status_tiles", "worklist", "pnl_table")
FULL_WIDTH = ("kpi_grid", "heatmap", "small_multiples", "detail_table", "action_table", "kpi_plan",
              "status_tiles", "worklist", "pnl_table")
ALIASES = {
    "kpi": "kpi_grid", "kpis": "kpi_grid", "kpi_card": "kpi_grid", "cards": "kpi_grid", "line": "trend_chart",
    "trend": "trend_chart", "line_chart": "trend_chart", "forecast": "forecast_band", "bar": "ranked_bar",
    "bar_chart": "ranked_bar", "ranking": "ranked_bar", "target_bar": "ranked_bar", "capacity_chart": "ranked_bar",
    "donut": "share_donut", "pie": "share_donut", "share": "share_donut", "matrix": "heatmap",
    "segment_matrix": "heatmap", "table": "detail_table", "evidence_table": "detail_table",
    "waterfall": "driver_bridge", "bridge": "driver_bridge", "drivers": "driver_bridge",
    "exceptions": "exception_table", "anomalies": "exception_table", "exception_queue": "exception_table",
    "risk_table": "exception_table", "decisions": "action_table", "comparison": "period_compare",
    "grouped_bar": "period_compare", "combo": "combo_chart", "bar_line": "combo_chart", "dual_axis": "combo_chart",
    "tree_map": "treemap", "gauge_chart": "gauge", "progress": "gauge", "runway": "gauge", "pnl": "pnl_table",
    "p_and_l": "pnl_table", "statement": "pnl_table", "pivot": "pnl_table",
}
AUDIENCE_BRIEF = {
    "executives": "Executives: few headline KPIs, direction vs prior year, forecast, what drove change, decisions.",
    "managers": "Managers: segment/team performance, rankings, exceptions to act on, detail for follow-up.",
    "weekly_business_review": "Weekly business review: week-over-week movement, drivers, exceptions, actions.",
    "daily_operations": "Daily operations: latest day, anomalies, operational breakdowns.",
}


@dataclass
class DataContext:
    model: SemanticModel
    bindings: Bindings
    profile: Profile
    distinct: dict[str, int]
    audience: str

    def granted(self, cap: str) -> bool:
        ev = self.profile.capabilities.get(cap)
        return bool(ev and ev.granted)

    @property
    def has_time(self) -> bool:
        return self.granted("comparable_time_series")

    def metric_ids(self) -> list[str]:
        return [m.id for m in self.model.metrics]

    def dim_ids(self) -> list[str]:
        return [d.id for d in self.model.categorical_dimensions]

    def hour_dim(self, metric: Optional[str] = None) -> Optional[str]:
        for d in self.model.categorical_dimensions:
            if re.search(r"HOUR", d.name, re.I) and (metric is None or self.allowed(metric, d.id)):
                return d.id
        return None

    def cumulable(self, metric: str) -> bool:
        f = self.model.field(metric, ("metric",))
        return f.additive or bool(re.match(r"^COUNT\s*\(\s*DISTINCT", re.sub(r"\s+", " ", f.expression or "").strip(), re.I))

    def allowed(self, metric: Optional[str], dim: Optional[str]) -> bool:
        """Can this metric be broken down by this dimension in the semantic view?"""
        if not metric or not dim:
            return True
        valid = getattr(self.model, "metric_dims", {}).get(metric.upper())
        return not valid or dim.upper() in valid

    def breakdown_groups(self) -> list[tuple[list[str], list[str]]]:
        """Metrics grouped by the dimensions they support (for the Cortex prompt)."""
        dmap = getattr(self.model, "metric_dims", {}) or {}
        if not dmap:
            return []
        cats = {d.id.upper(): d.id for d in self.model.categorical_dimensions}
        groups: dict[tuple, list[str]] = {}
        for m in self.model.metrics:
            dims = tuple(sorted(cats[x] for x in dmap.get(m.id.upper(), set()) if x in cats))
            groups.setdefault(dims, []).append(m.id)
        return [(ms, list(ds)) for ds, ms in groups.items()]


@dataclass
class Governance:
    entries: list[dict[str, str]] = field(default_factory=list)

    def add(self, page: str, tile: str, action: str, reason: str) -> None:
        self.entries.append({"page": page, "tile": tile, "action": action, "reason": reason})


# --------------------------------------------------------------------------- data profile
def data_profile(ctx: DataContext) -> dict[str, Any]:
    cal = ctx.profile.calendar
    metrics = []
    for m in ctx.model.metrics:
        metrics.append({"id": m.id, "label": m.label, "format": fmt_kind(m.name),
                        "additive": bool(m.additive), "note": (m.comment or "")[:100]})
    dims = []
    for d in ctx.model.categorical_dimensions:
        dims.append({"id": d.id, "label": d.label, "distinct_values": ctx.distinct.get(d.id),
                     "note": (d.comment or "")[:80]})
    caps = {
        "time_series": ctx.has_time,
        "forecast": ctx.granted("forecast_versioned"),
        "prior_year_baseline": ctx.granted("target"),
        "top_insights": bool(ctx.bindings.use_drivers),
    }
    return {
        "semantic_view": ctx.model.fqn,
        "grain": cal.grain if cal else None,
        "latest_complete_period": cal.label(cal.current_start) if cal else None,
        "history": f"{cal.label(cal.window_start)} to {cal.label(cal.current_start)}" if cal else None,
        "primary_metric": ctx.bindings.primary_metric,
        "approved_metrics": [ctx.bindings.primary_metric] + list(ctx.bindings.supporting_metrics),
        "metrics": metrics, "dimensions": dims, "capabilities": caps,
    }


def _vocab_text(ctx: DataContext) -> str:
    lines = []
    for t, spec in TILES.items():
        if spec.get("caps") and not all(ctx.granted(c) for c in spec["caps"]):
            continue
        if spec.get("time") and not ctx.has_time:
            continue
        if spec.get("hour") and not ctx.hour_dim():
            continue
        req = ", ".join(spec["fields"]) or "none"
        extra = []
        if "dim_range" in spec:
            lo, hi = spec["dim_range"]
            extra.append(f"dimension with {lo}-{hi if hi < 1000 else 'any'} distinct values")
        if spec.get("additive"):
            extra.append("additive metric only")
        lines.append(f"- {t} (fields: {req}{'; ' + '; '.join(extra) if extra else ''}; default width "
                     f"{spec['width']}): {spec['use']}")
    return "\n".join(lines)


def _breakdown_text(ctx: DataContext) -> str:
    groups = ctx.breakdown_groups()
    if not groups or len(groups) == 1:
        return ""
    lines = ["Valid breakdowns (a metric can ONLY be split by the dimensions listed for it; the date works for all):"]
    for ms, ds in groups:
        lines.append(f"- metrics {', '.join(ms)} -> dimensions {', '.join(ds) if ds else '(date only)'}")
    return "\n".join(lines) + "\n"


TILE_SCHEMA = ('{"type": "<tile type>", "title": "<specific business title>", "question": "<the question it '
               'answers>", "metric": "<metric id>", "metric2": "<metric id, scatter/combo_chart only>", "metrics": ["<metric '
               'ids, kpi_grid/detail_table/pnl_table>"], "dimension": "<dimension id>", "dimension2": "<dimension id, heatmap '
               '(required) / treemap (optional nesting) only>", "dimensions": ["<dimension ids, detail_table>"], "width": <3-12>, "show_trend": <true|false, '
               'kpi_grid/kpi_plan only: sparkline under each card>}')


def compose_prompt(ctx: DataContext, goal: str, seed: Optional[dict[str, Any]] = None,
                   pages: tuple[int, int] = (2, 3), page_hint: str = "") -> str:
    prof = data_profile(ctx)
    metrics = "\n".join(f"- {m['id']} | {m['label']} | {m['format']} | "
                        f"{'additive' if m['additive'] else 'NOT additive (ratio/distinct)'}"
                        f"{' | ' + m['note'] if m['note'] else ''}" for m in prof["metrics"])
    dims = "\n".join(f"- {d['id']} | {d['label']} | {d['distinct_values'] if d['distinct_values'] is not None else '?'}"
                     f" distinct values{' | ' + d['note'] if d['note'] else ''}" for d in prof["dimensions"])
    seed_txt = ""
    if seed:
        seed_txt = ("\nStart from this reviewed template and ADAPT it to the goal and the data (you may rename, "
                    "reorder, swap charts and metrics, add or remove tiles):\n"
                    + "\n".join(f"  Page '{p['label']}' ({p['purpose']}): "
                                + ", ".join(f"{c['type']}[{c['title']}]" for c in p["components"])
                                for p in seed["pages"]) + "\n")
    return (
        "You are a senior BI designer building a dashboard inside Snowflake. Design the layout as JSON.\n"
        f"Audience: {AUDIENCE_BRIEF.get(ctx.audience, ctx.audience)}\n"
        f"Goal from the user: {goal.strip() or 'general performance review for this audience'}\n"
        f"{page_hint}"
        f"Data: semantic view {prof['semantic_view']}, {prof['grain']} grain, latest complete period "
        f"{prof['latest_complete_period']}, history {prof['history']}.\n"
        f"User-approved focus metrics (prefer these): {', '.join(prof['approved_metrics'])}\n"
        f"Metrics (id | label | format | additivity):\n{metrics}\n"
        f"Categorical dimensions (id | label | cardinality):\n{dims}\n"
        f"Capabilities: {json.dumps(prof['capabilities'])}\n"
        f"{_breakdown_text(ctx)}"
        f"Tile types you may use (ONLY these):\n{_vocab_text(ctx)}\n"
        f"{seed_txt}"
        "Rules:\n"
        f"- {pages[0]}-{pages[1]} pages, 3-5 tiles per page (quality over quantity; never repeat the same metric+view). Each page answers one business question.\n"
        "- Use ONLY the metric and dimension ids listed above, exactly as written. Never invent fields, SQL or numbers.\n"
        "- Pick the chart that fits the data: small dimensions (<=10 values) suit share_donut/period_compare; "
        "large ones suit ranked_bar/pareto; two related metrics suit scatter.\n"
        "- The first page should open with a kpi_grid. Do not repeat the same type+metric+dimension.\n"
        "- Widths in each row should add up to 12 (allowed: 3,4,5,6,7,8,9,12).\n"
        "- Titles must be specific (e.g. 'Profit ratio by sub-category'), not generic ('Chart 1').\n"
        "Respond with JSON only, no prose:\n"
        '{"title": "<dashboard title>", "summary": "<one sentence on what this dashboard is for>", '
        '"pages": [{"label": "<short tab label>", "question": "<business question for the page>", '
        f'"tiles": [{TILE_SCHEMA}]}}]}}'
    )


def tile_prompt(ctx: DataContext, instruction: str, page: dict[str, Any]) -> str:
    base = compose_prompt(ctx, instruction, pages=(1, 1))
    existing = ", ".join(f"{c['type']}[{c['title']}]" for c in page["components"])
    return (base.split("Rules:")[0]
            + f"The user is editing page '{page['label']}' which already has: {existing}.\n"
            f"User request: {instruction}\n"
            "Return ONE new tile that fulfils the request, using only the listed ids and tile types.\n"
            f"Respond with JSON only: {{\"tile\": {TILE_SCHEMA}}}")


# --------------------------------------------------------------------------- validation
def _resolver(ids: list[str], labels: dict[str, str]):
    by_upper = {i.upper(): i for i in ids}
    by_name = {}
    for i in ids:
        by_name.setdefault(i.split(".")[-1].upper(), i)
    by_label = {labels[i].upper(): i for i in ids}

    def resolve(value: Any) -> Optional[str]:
        if not isinstance(value, str) or not value.strip():
            return None
        v = value.strip().strip('"').upper()
        if v in by_upper:
            return by_upper[v]
        tail = v.split(".")[-1]
        return by_name.get(tail) or by_label.get(v) or by_label.get(tail.replace("_", " "))
    return resolve


class Validator:
    def __init__(self, ctx: DataContext, gov: Governance):
        self.ctx = ctx
        self.gov = gov
        m_labels = {m.id: m.label for m in ctx.model.metrics}
        d_labels = {d.id: d.label for d in ctx.model.categorical_dimensions}
        self.metric = _resolver(list(m_labels), m_labels)
        self.dim = _resolver(list(d_labels), d_labels)
        self.additive = {m.id: bool(m.additive) for m in ctx.model.metrics}
        self.seq = 0

    def _card(self, dim: str) -> Optional[int]:
        return self.ctx.distinct.get(dim)

    def _fits(self, dim: str, rng: tuple[int, int]) -> bool:
        n = self._card(dim)
        return n is None or rng[0] <= n <= rng[1]

    def _default_dim(self, rng: tuple[int, int], avoid: tuple[str, ...] = (),
                     metrics: tuple = ()) -> Optional[str]:
        b = self.ctx.bindings
        for d in [b.segment_dimension, b.region_dimension] + self.ctx.dim_ids():
            if d and d not in avoid and self._fits(d, rng) and all(self.ctx.allowed(m, d) for m in metrics if m):
                return d
        return None

    def tile(self, raw: Any, page_label: str, seen: set) -> Optional[dict[str, Any]]:
        if not isinstance(raw, dict):
            self.gov.add(page_label, "?", "dropped", "Tile was not a JSON object.")
            return None
        title = str(raw.get("title") or "").strip()[:90]
        t = str(raw.get("type") or "").strip().lower()
        t = ALIASES.get(t, t)
        name = title or t or "tile"
        if t not in TILES:
            self.gov.add(page_label, name, "dropped", f"'{raw.get('type')}' is not in the tile vocabulary.")
            return None
        spec = TILES[t]
        notes: list[str] = []
        b = self.ctx.bindings

        # time / capability gates (with downgrade where it keeps the intent)
        if spec.get("time") and not self.ctx.has_time:
            self.gov.add(page_label, name, "dropped", "Needs a comparable time series, which is not proven.")
            return None
        if t == "forecast_band" and not self.ctx.granted("forecast_versioned"):
            t, spec = "trend_chart", TILES["trend_chart"]
            notes.append("forecast not proven for this source → trend line")

        metric = self.metric(raw.get("metric"))
        if "metric" in spec["fields"] and not metric:
            if raw.get("metric"):
                notes.append(f"unknown metric '{raw.get('metric')}' → {b.primary_metric}")
            metric = b.primary_metric
        if spec.get("cumulative") and metric and not self.ctx.cumulable(metric):
            notes.append(f"{metric} is a ratio/average, so a running total is meaningless → trend line")
            t, spec = "trend_chart", TILES["trend_chart"]
        if spec.get("hour") and not self.ctx.hour_dim(metric):
            self.gov.add(page_label, name, "dropped", "Needs an hour-of-day dimension related to the metric.")
            return None
        if spec.get("additive") and metric and not self.additive.get(metric, False):
            notes.append(f"{metric} is not additive, so {t} would not reconcile → ranked bars")
            t, spec = "ranked_bar", TILES["ranked_bar"]

        dim = self.dim(raw.get("dimension"))
        if "dimension" in spec["fields"]:
            rng = spec.get("dim_range", (2, 100000))
            if dim and not self._fits(dim, rng):
                n = self._card(dim)
                if t == "share_donut":
                    t, spec = "ranked_bar", TILES["ranked_bar"]
                    notes.append(f"{dim} has {n} values, too many for a donut → ranked bars")
                elif t == "period_compare":
                    t, spec = "ranked_bar", TILES["ranked_bar"]
                    notes.append(f"{dim} has {n} values, too many to compare side by side → ranked bars")
                elif t == "pareto":
                    t, spec = "share_donut" if self._fits(dim, (2, 10)) else "ranked_bar", None
                    spec = TILES[t]
                    notes.append(f"{dim} has only {n} values, too few for a Pareto → {TILES[t]['label'].lower()}")
                elif t == "scatter":
                    t, spec = "ranked_bar", TILES["ranked_bar"]
                    notes.append(f"{dim} has only {n} values, too few points for a scatter → ranked bars")
                elif t == "treemap":
                    t, spec = "share_donut", TILES["share_donut"]
                    notes.append(f"{dim} has only {n} values, too few for a treemap → share donut")
                else:
                    alt = self._default_dim(rng, metrics=(metric,))
                    notes.append(f"{dim} has {n} values (needs {rng[0]}–{rng[1]}) → {alt}")
                    dim = alt
            if not dim:
                if raw.get("dimension"):
                    notes.append(f"unknown dimension '{raw.get('dimension')}'")
                dim = self._default_dim(spec.get("dim_range", (2, 100000)), metrics=(metric,))
                if dim:
                    notes.append(f"dimension set to {dim}")
            if dim and not self.ctx.allowed(metric, dim):
                alt = self._default_dim(spec.get("dim_range", (2, 100000)), metrics=(metric,))
                if not alt:
                    self.gov.add(page_label, name, "dropped",
                                 f"{metric} cannot be broken down by {dim}: their tables are not related in the semantic view.")
                    return None
                notes.append(f"{metric} cannot be broken down by {dim} (tables not related in the semantic view) → {alt}")
                dim = alt
            if not dim:
                self.gov.add(page_label, name, "dropped", "No categorical dimension fits this chart.")
                return None
        if (spec.get("time") or t in ("trend_chart", "forecast_band")) and not self.ctx.allowed(metric, b.time_dimension):
            self.gov.add(page_label, name, "dropped", f"{metric} has no relationship to {b.time_dimension}.")
            return None

        out: dict[str, Any] = {"type": t, "title": title or f"{TILES[t]['label']}",
                               "question": str(raw.get("question") or "").strip()[:200]}
        if "metric" in spec["fields"]:
            out["metric_id"] = metric
        if "dimension" in spec["fields"]:
            out["dimension"] = dim
        if t == "combo_chart":
            m2 = self.metric(raw.get("metric2"))
            tdim = b.time_dimension
            if not m2 or m2 == metric or not self.ctx.allowed(m2, tdim):
                pool = [*b.supporting_metrics, *self.ctx.metric_ids()]
                rate = [m for m in pool if m != metric and self.ctx.allowed(m, tdim)
                        and fmt_kind(self.ctx.model.field(m, ("metric",)).name) == "percent"]
                m2 = next(iter(rate), None) or next((m for m in pool if m != metric and self.ctx.allowed(m, tdim)), None)
                if not m2:
                    self.gov.add(page_label, name, "dropped", "Bars + line needs a second metric over time.")
                    return None
                notes.append(f"line metric set to {m2}")
            out["metric2_id"] = m2
        if t == "treemap" and raw.get("dimension2"):
            d2 = self.dim(raw.get("dimension2"))
            if d2 and d2 != dim and self._fits(d2, spec["dim2_range"]) and self.ctx.allowed(metric, d2):
                out["dimension2"] = d2
            else:
                notes.append(f"nesting by '{raw.get('dimension2')}' is not valid for this metric → one level")
        if t == "scatter":
            m2 = self.metric(raw.get("metric2"))
            if not m2 or m2 == metric or not self.ctx.allowed(m2, dim):
                m2 = next((m for m in [*b.supporting_metrics, *self.ctx.metric_ids()]
                           if m != metric and self.ctx.allowed(m, dim)), None)
                if not m2:
                    self.gov.add(page_label, name, "dropped", "Scatter needs a second metric.")
                    return None
                notes.append(f"second metric set to {m2}")
            out["metric2_id"] = m2
        if t == "heatmap":
            d2 = self.dim(raw.get("dimension2"))
            rng2 = spec["dim2_range"]
            if not d2 or d2 == dim or not self._fits(d2, rng2) or not self.ctx.allowed(metric, d2):
                d2 = self._default_dim(rng2, avoid=(dim,), metrics=(metric,))
                if not d2:
                    self.gov.add(page_label, name, "dropped", "Heatmap needs a second small dimension.")
                    return None
                notes.append(f"second dimension set to {d2}")
            out["dimension2"] = d2
        if t in METRIC_LIST_TYPES:
            asked = [v for v in (raw.get("metrics") or []) if v]
            ms = [x for x in (self.metric(v) for v in asked) if x]
            bad = [str(v) for v in asked if not self.metric(v)]
            if bad:
                notes.append("removed unknown metrics " + ", ".join(bad))
            if not ms and metric and self.metric(raw.get("metric")):
                ms = [metric]
            cap = {"kpi_grid": 8, "kpi_plan": 5, "scorecard": 5, "status_tiles": 6, "worklist": 4,
                   "pnl_table": 8}.get(t, 6)
            ms = list(dict.fromkeys(ms))[:cap]
            if not ms:
                ms = ([b.primary_metric] + list(b.supporting_metrics))[:cap]
                notes.append("metrics set to the approved focus metrics")
            if t in ("scorecard", "pnl_table") and dim:
                keep = [m for m in ms if self.ctx.allowed(m, dim)]
                if len(keep) < len(ms):
                    notes.append(f"removed metrics that cannot be split by {dim}")
                ms = keep or [b.primary_metric]
            if t in ("kpi_grid", "kpi_plan", "status_tiles", "pnl_table"):
                keep = [m for m in ms if self.ctx.allowed(m, b.time_dimension)]
                if len(keep) < len(ms):
                    notes.append("removed metrics without a date relationship")
                ms = keep or [b.primary_metric]
            out["metrics"] = ms
        if t == "worklist":
            asked_d = [v for v in (raw.get("dimensions") or []) if v]
            ds = [x for x in (self.dim(v) for v in asked_d) if x and x != self.ctx.hour_dim()]
            ds = [d for d in dict.fromkeys(ds) if self._fits(d, (2, 200))][:3] or \
                [d for d in (b.region_dimension, b.segment_dimension) if d][:2]
            pairs = [(m, d) for m in out["metrics"] for d in ds if self.ctx.allowed(m, d)]
            if not pairs:
                self.gov.add(page_label, name, "dropped", "No metric can be broken down by those dimensions.")
                return None
            out["dimensions"] = ds
        if t == "detail_table":
            asked_d = [v for v in (raw.get("dimensions") or []) if v]
            ds = [x for x in (self.dim(v) for v in asked_d) if x]
            if len(ds) < len(asked_d):
                notes.append("removed unknown dimensions " + ", ".join(str(v) for v in asked_d if not self.dim(v)))
            ds = list(dict.fromkeys(ds))[:3] or [d for d in (b.segment_dimension, b.region_dimension) if d][:2]
            if not ds:
                self.gov.add(page_label, name, "dropped", "Detail table needs a dimension.")
                return None
            ms2 = [m for m in out["metrics"] if all(self.ctx.allowed(m, d) for d in ds + [b.time_dimension])]
            if len(ms2) < len(out["metrics"]):
                notes.append("removed metrics that cannot be broken down by " + ", ".join(ds))
            if not ms2:
                self.gov.add(page_label, name, "dropped", "No metric can be broken down by those dimensions.")
                return None
            out["dimensions"], out["metrics"] = ds, ms2

        key = (t, out.get("metric_id"), out.get("dimension"), out.get("metric2_id"), out.get("dimension2"),
               tuple(out.get("metrics", ())), tuple(out.get("dimensions", ())))
        if key in seen:
            self.gov.add(page_label, name, "dropped", "Duplicate of another tile on this dashboard.")
            return None
        seen.add(key)

        try:
            width = int(raw.get("width") or TILES[t]["width"])
        except (TypeError, ValueError):
            width = TILES[t]["width"]
        width = min(WIDTHS, key=lambda w: abs(w - width))
        if t in FULL_WIDTH and width < 6:
            width = 12
        out["width"] = width
        if t in ("kpi_grid", "kpi_plan"):
            default_show = t == "kpi_grid"
            out["show_trend"] = raw.get("show_trend", default_show) is not False and str(raw.get("show_trend", default_show)).lower() != "false"
        self.seq += 1
        out.update({"component_id": f"t{self.seq}", "state": "ready", "role_bindings": {},
                    "missing_requirements": [], "origin": "cortex"})
        if out["type"] == "trend_chart" and self.ctx.granted("target"):
            out["role_bindings"] = {"target": "BASELINE:PRIOR_YEAR"}
        self.gov.add(page_label, out["title"], "repaired" if notes else "kept",
                     "; ".join(notes) if notes else "Valid tile type, fields exist in the semantic view, "
                                                    "requirements proven.")
        return out


def validate_layout(ctx: DataContext, raw: dict[str, Any], gov: Governance,
                    validator: Optional[Validator] = None, seen: Optional[set] = None) -> list[dict[str, Any]]:
    v = validator or Validator(ctx, gov)
    seen = seen if seen is not None else set()
    pages = []
    for i, p in enumerate((raw.get("pages") or [])[:MAX_PAGES]):
        if not isinstance(p, dict):
            continue
        label = str(p.get("label") or f"Page {i + 1}").strip()[:40]
        tiles = []
        for t in (p.get("tiles") or [])[:MAX_TILES * 2]:
            if len(tiles) >= MAX_TILES:
                gov.add(label, str(t.get("title", "?")) if isinstance(t, dict) else "?", "dropped",
                        f"Page already has {MAX_TILES} tiles; kept it focused.")
                continue
            tile = v.tile(t, label, seen)
            if tile:
                tiles.append(tile)
        if not tiles:
            gov.add(label, "(page)", "dropped", "No valid tiles on this page.")
            continue
        pages.append({"page_id": f"p{len(pages) + 1}", "label": label,
                      "purpose": str(p.get("question") or p.get("purpose") or "").strip()[:200] or label,
                      "components": tiles})
    for extra in (raw.get("pages") or [])[MAX_PAGES:]:
        gov.add(str((extra or {}).get("label", "?")), "(page)", "dropped", f"More than {MAX_PAGES} pages.")
    return pages


def next_ids(spec: dict[str, Any]) -> int:
    n = 0
    for p in spec["pages"]:
        for c in p["components"]:
            m = re.match(r"t(\d+)$", c["component_id"])
            if m:
                n = max(n, int(m.group(1)))
    return n


def compose(cortex, ctx: DataContext, goal: str, seed: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    """Cortex-designed, validated spec. Raises if Cortex fails or nothing survives validation."""
    from ai_services import _json_from_text
    prompt = compose_prompt(ctx, goal, seed)
    text, prov = cortex.complete(prompt)
    raw = _json_from_text(text)
    gov = Governance()
    pages = validate_layout(ctx, raw, gov)
    if not pages:
        raise ValueError("Cortex returned no valid tiles for this data.")
    digest = hashlib.sha1(json.dumps(pages, sort_keys=True).encode()).hexdigest()[:8]
    return {
        "template_id": f"cortex-{digest}", "template_version": 1, "origin": "cortex",
        "audience_id": ctx.audience, "display_name": str(raw.get("title") or "Cortex-designed dashboard")[:90],
        "description": str(raw.get("summary") or "")[:240], "goal": goal[:400],
        "seed_template": (seed or {}).get("template_id"), "provenance": f"Cortex AI_COMPLETE ({prov})",
        "pages": pages, "governance": gov.entries,
    }


def compose_page(cortex, ctx: DataContext, spec: dict[str, Any], page_id: str, instruction: str) -> dict[str, Any]:
    from ai_services import _json_from_text
    page = next(p for p in spec["pages"] if p["page_id"] == page_id)
    others = [f"'{p['label']}'" for p in spec["pages"] if p["page_id"] != page_id]
    hint = (f"Redesign ONE page only: '{page['label']}' ({page['purpose']}). "
            + (f"Other pages ({', '.join(others)}) already exist; do not duplicate them. " if others else "")
            + (f"Instruction: {instruction}\n" if instruction else "Try a fresh angle on the same question.\n"))
    text, prov = cortex.complete(compose_prompt(ctx, spec.get("goal") or "", None, (1, 1), hint))
    raw = _json_from_text(text)
    gov = Governance()
    v = Validator(ctx, gov)
    v.seq = next_ids(spec)
    new_pages = validate_layout(ctx, {"pages": (raw.get("pages") or [])[:1]}, gov, v)
    if not new_pages:
        raise ValueError("Cortex returned no valid tiles for this page.")
    new = new_pages[0]
    new["page_id"] = page_id
    for e in gov.entries:
        e["page"] = new["label"]
    return {"page": new, "governance": gov.entries, "provenance": prov}


def compose_tile(cortex, ctx: DataContext, spec: dict[str, Any], page_id: str, instruction: str) -> dict[str, Any]:
    from ai_services import _json_from_text
    page = next(p for p in spec["pages"] if p["page_id"] == page_id)
    text, prov = cortex.complete(tile_prompt(ctx, instruction, page))
    raw = _json_from_text(text)
    gov = Governance()
    v = Validator(ctx, gov)
    v.seq = next_ids(spec)
    tile = v.tile(raw.get("tile", raw), page["label"], set())
    if not tile:
        reason = gov.entries[-1]["reason"] if gov.entries else "invalid tile"
        raise ValueError(f"Cortex's tile was rejected by validation: {reason}")
    return {"tile": tile, "governance": gov.entries, "provenance": prov}


def revalidate_tile(ctx: DataContext, spec: dict[str, Any], page_id: str, tile: dict[str, Any],
                    patch: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """User edit (swap metric/dimension/type/width) goes through the same checks as Cortex output."""
    default_show_trend = True if tile.get("type") == "kpi_grid" else bool(tile.get("show_trend", False))
    raw = {"type": patch.get("type", tile["type"]), "title": patch.get("title", tile.get("title")),
           "question": tile.get("question", ""), "metric": patch.get("metric_id", tile.get("metric_id")),
           "metric2": patch.get("metric2_id", tile.get("metric2_id")),
           "metrics": patch.get("metrics", tile.get("metrics")),
           "dimension": patch.get("dimension", tile.get("dimension") or tile.get("role_bindings", {}).get("segment")),
           "dimension2": patch.get("dimension2", tile.get("dimension2")),
           "dimensions": patch.get("dimensions", tile.get("dimensions")),
           "width": patch.get("width", tile.get("width")),
           "show_trend": patch.get("show_trend", default_show_trend)}
    if "metric_id" in patch and not patch.get("title"):
        old = tile.get("metric_id")
        if old and raw["title"]:
            old_label = ctx.model.field(old, ("metric",)).label if old in ctx.metric_ids() else ""
            new_id = patch["metric_id"]
            new_label = ctx.model.field(new_id, ("metric",)).label if new_id in ctx.metric_ids() else ""
            if old_label and new_label and old_label.lower() in raw["title"].lower():
                raw["title"] = re.sub(re.escape(old_label), new_label, raw["title"], flags=re.I)
    gov = Governance()
    v = Validator(ctx, gov)
    page = next(p for p in spec["pages"] if p["page_id"] == page_id)
    new = v.tile(raw, page["label"], set())
    if not new:
        raise ValueError(gov.entries[-1]["reason"] if gov.entries else "Invalid edit")
    new["component_id"] = tile["component_id"]
    new["origin"] = "edited"
    if not patch.get("title"):
        retitle(ctx, tile, new)
    if tile.get("display") and new["type"] == tile["type"]:
        new["display"] = tile["display"]            # keep the chosen look (bullet / arrows / table) across edits
    if tile.get("role_bindings", {}).get("target") and new["type"] == "trend_chart":
        new["role_bindings"] = {"target": tile["role_bindings"]["target"]}
    return new, gov.entries


def _label(ctx: DataContext, field_id) -> str:
    try:
        return ctx.model.field(field_id).label if field_id else ""
    except Exception:
        return ""


def retitle(ctx: DataContext, old: dict[str, Any], new: dict[str, Any]) -> None:
    """Keep a tile's title honest after an edit: if the metric or breakdown changed but the title did not,
    swap the old field name for the new one (or write 'Metric by Breakdown' when the old name isn't in it)."""
    title = new.get("title") or ""
    if not title or title != (old.get("title") or ""):
        return                                           # the user (or Cortex) chose a new title: keep it
    if old.get("title_locked"):
        new["title_locked"] = True                       # renamed by hand earlier: never overwrite it
        return
    changed = False
    for key in ("metric_id", "dimension", "dimension2"):
        a, b = old.get(key), new.get(key)
        if a == b or not b:
            continue
        la, lb = _label(ctx, a), _label(ctx, b)
        if la and lb and la.lower() in title.lower():
            title = re.sub(re.escape(la), lb, title, flags=re.I)
            changed = True
        elif key == "dimension" and lb:
            m = _label(ctx, new.get("metric_id")) or title.split(" by ")[0]
            title = f"{m} by {lb}"
            changed = True
    if changed:
        new["title"] = title[:80]


def normalise_template_spec(spec: dict[str, Any]) -> dict[str, Any]:
    """Give catalog-template components the same editable shape as composed tiles."""
    spec.setdefault("origin", "catalog")
    spec.setdefault("governance", [])
    for page in spec["pages"]:
        for c in page["components"]:
            c.setdefault("question", "")
            c.setdefault("origin", "catalog")
    return spec


# --------------------------------------------------------------------------- page & tile helpers (builder)
def compose_new_page(cortex, ctx: DataContext, spec: dict[str, Any], instruction: str) -> dict[str, Any]:
    """Cortex designs one additional page from a sentence; validated like every other tile."""
    from ai_services import _json_from_text
    others = ", ".join(f"'{p['label']}'" for p in spec["pages"])
    hint = (f"Design ONE new page for an existing dashboard. Existing pages: {others}; do not duplicate them. "
            f"Page request: {instruction or 'a useful additional view'}\n")
    text, prov = cortex.complete(compose_prompt(ctx, spec.get("goal") or instruction, None, (1, 1), hint))
    raw = _json_from_text(text)
    gov = Governance()
    v = Validator(ctx, gov)
    v.seq = next_ids(spec)
    pages = validate_layout(ctx, {"pages": (raw.get("pages") or [])[:1]}, gov, v)
    if not pages:
        raise ValueError("Cortex returned no valid tiles for this page.")
    page = pages[0]
    page["page_id"] = f"p{1 + max([int(p['page_id'][1:]) for p in spec['pages'] if p['page_id'][1:].isdigit()] or [0])}"
    for e in gov.entries:
        e["page"] = page["label"]
    return {"page": page, "governance": gov.entries, "provenance": prov}


def edit_tile_nl(cortex, ctx: DataContext, spec: dict[str, Any], page_id: str, tile: dict[str, Any],
                 instruction: str) -> dict[str, Any]:
    """'make this a line chart', 'split by channel' -> updated tile, checked by the validator."""
    from ai_services import _json_from_text
    current = {k: tile.get(k) for k in ("type", "title", "question", "metric_id", "metric2_id", "metrics",
                                        "dimension", "dimension2", "dimensions", "width") if tile.get(k)}
    if tile.get("type") in ("kpi_grid", "kpi_plan"):
        current["show_trend"] = tile.get("show_trend", tile.get("type") == "kpi_grid")
    base = compose_prompt(ctx, instruction, pages=(1, 1)).split("Rules:")[0]
    prompt = (base + f"Current tile: {json.dumps(current)}\nUser request for this tile: {instruction}\n"
              "Return the UPDATED tile (keep what the user did not ask to change), using only the listed ids "
              f"and tile types. Respond with JSON only: {{\"tile\": {TILE_SCHEMA}}}")
    text, prov = cortex.complete(prompt)
    raw = _json_from_text(text)
    raw = raw.get("tile", raw)
    if isinstance(raw, dict):
        raw.setdefault("show_trend", tile.get("show_trend", tile.get("type") == "kpi_grid"))
        raw.setdefault("metric", raw.get("metric_id") or tile.get("metric_id"))
        raw.setdefault("dimension", tile.get("dimension"))
    gov = Governance()
    v = Validator(ctx, gov)
    page = next(p for p in spec["pages"] if p["page_id"] == page_id)
    new = v.tile(raw, page["label"], set())
    if not new:
        raise ValueError("The change was rejected by validation: " + (gov.entries[-1]["reason"] if gov.entries else "invalid"))
    new["component_id"] = tile["component_id"]
    new["origin"] = "cortex-edit"
    if tile.get("title_locked") and not re.search(r"\b(title|rename|name|heading|call it)\b", instruction, re.I):
        new["title"], new["title_locked"] = tile["title"], True    # a title the user set by hand survives other edits
    else:
        retitle(ctx, tile, new)
    return {"tile": new, "governance": gov.entries, "provenance": prov}


def manual_tile(ctx: DataContext, spec: dict[str, Any], page_id: str, raw: dict[str, Any]) -> dict[str, Any]:
    gov = Governance()
    v = Validator(ctx, gov)
    v.seq = next_ids(spec)
    page = next(p for p in spec["pages"] if p["page_id"] == page_id)
    tile = v.tile(raw, page["label"], set())
    if not tile:
        raise ValueError(gov.entries[-1]["reason"] if gov.entries else "Invalid tile")
    tile["origin"] = "user"
    return {"tile": tile, "governance": gov.entries}


THEMES = (
    ("Plan", r"^PLAN_|ATTAINMENT|VS_PLAN"),
    ("Inventory", r"ON_HAND|INVENTORY|STOCK|SUPPLY|SELL_THROUGH|LOST_SALES|ON_ORDER"),
    ("Fulfilment", r"SHIP|DELIVER|TRANSIT|CLICK_TO|ON_TIME"),
    ("Returns", r"RETURN"),
    ("Profitability", r"MARGIN|PROFIT|COGS|COST|DISCOUNT"),
    ("Customers", r"CUSTOMER|ORDER_VALUE|PER_TRANSACTION|ORDER_COUNT|^ORDERS$"),
)


def metric_cards(ctx: DataContext, spec: dict[str, Any]) -> list[dict[str, Any]]:
    """Cards for the review screen: every metric, grouped by theme, with its definition and formula."""
    used = set()
    for p in spec["pages"]:
        for c in p["components"]:
            for k in ("metric_id", "metric2_id"):
                if c.get(k):
                    used.add(c[k])
            used.update(c.get("metrics") or [])
    cards = []
    order = ["Sales", "Profitability", "Customers", "Fulfilment", "Returns", "Inventory", "Plan"]
    info = getattr(ctx.model, "metric_info", {}) or {}
    for m in ctx.model.metrics:
        theme = next((t for t, rx in THEMES if re.search(rx, m.name, re.I)), "Sales")
        mi = info.get(m.id) or {}
        alias = {"Operations": "Fulfilment", "Finance": "Profitability", "Volume": "Sales", "Quality": "Returns"}
        if mi.get("theme") in order or mi.get("theme") in alias:
            theme = alias.get(mi["theme"], mi["theme"])
        cards.append({"id": m.id, "label": m.label, "definition": m.comment, "formula": m.expression,
                      "theme": theme, "recommended": m.id in used, "table": m.entity or "derived",
                      "origin": mi.get("origin") or ("adhoc" if getattr(ctx.model, "facts_mode", False) else "view"),
                      "why": mi.get("why", "")})
    cards.sort(key=lambda c: (order.index(c["theme"]), not c["recommended"], c["label"]))
    return cards


def apply_review(ctx: DataContext, spec: dict[str, Any], selected: list[str],
                 outline: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """Apply the user's review: page names/order, removed tiles, chosen metrics."""
    gov: list[dict[str, str]] = []
    sel = set(selected or [])
    by_id = {p["page_id"]: p for p in spec["pages"]}
    pages = []
    for o in outline or [{"page_id": p["page_id"], "label": p["label"],
                          "tiles": [c["component_id"] for c in p["components"]]} for p in spec["pages"]]:
        page = by_id.get(o.get("page_id"))
        if not page:
            continue
        comps = {c["component_id"]: c for c in page["components"]}
        kept = []
        for tid in o.get("tiles") or []:
            c = comps.get(tid)
            if not c:
                continue
            if sel:
                if c.get("metrics"):
                    c["metrics"] = [m for m in c["metrics"] if m in sel] or None
                    if not c["metrics"]:
                        gov.append({"page": page["label"], "tile": c["title"], "action": "removed",
                                    "reason": "None of its metrics were selected in review."})
                        continue
                elif any(c.get(k) and c[k] not in sel for k in ("metric_id", "metric2_id")):
                    gov.append({"page": page["label"], "tile": c["title"], "action": "removed",
                                "reason": "Its metric was deselected in review."})
                    continue
            kept.append(c)
        for tid in set(comps) - set(o.get("tiles") or []):
            gov.append({"page": page["label"], "tile": comps[tid]["title"], "action": "removed",
                        "reason": "Removed in review."})
        label = str(o.get("label") or page["label"]).strip()[:40] or page["label"]
        if kept:
            pages.append({**page, "label": label, "components": kept})
    if not pages:
        raise ValueError("Keep at least one tile.")
    # newly selected metrics that no tile shows -> headline KPI cards on the first page
    used = {m for p in pages for c in p["components"] for m in [c.get("metric_id"), c.get("metric2_id"), *(c.get("metrics") or [])] if m}
    extra = [m for m in selected or [] if m not in used and ctx.allowed(m, ctx.bindings.time_dimension)]
    if extra:
        first = pages[0]
        kpi = next((c for c in first["components"] if c["type"] in ("kpi_grid", "kpi_card", "kpi_plan",
                                                                      "status_tiles")), None)
        if kpi is None:
            kpi = {"component_id": f"t{next_ids({'pages': pages}) + 1}", "type": "kpi_grid", "title": "Headline metrics",
                   "question": "", "metrics": [], "width": 12, "state": "ready", "role_bindings": {},
                   "missing_requirements": [], "origin": "review"}
            first["components"].insert(0, kpi)
        base = kpi.get("metrics") or [ctx.bindings.primary_metric]
        if kpi["type"] == "kpi_card":
            kpi["type"] = "kpi_grid"
        cap = {"kpi_plan": 5, "status_tiles": 6}.get(kpi["type"], 10)
        kpi["metrics"] = list(dict.fromkeys(base + extra))[:cap]
        gov.append({"page": first["label"], "tile": kpi["title"], "action": "edited",
                    "reason": "Added metrics selected in review: " + ", ".join(extra)})
    out = {**spec, "pages": pages}
    out["governance"] = (spec.get("governance") or []) + gov
    return out, gov


# KPI-vs-plan tile: how the comparison is drawn (purely visual, numbers unchanged)
KPI_DISPLAYS = {"bullet": "bullet bars", "variance": "variance with arrows", "table": "a variance table"}


def display_from_text(text: str) -> "str | None":
    """'show these as a table' / 'use arrows instead of bars' -> the KPI display; questions are left alone."""
    t = text.lower()
    if "?" in t or not re.search(r"\b(show|display|switch|change|make|use|turn|convert|as|instead)\b", t):
        return None
    if re.search(r"\btable|grid\b", t):
        return "table"
    if re.search(r"arrow|variance|delta|numbers?\b|conditional", t) and not re.search(r"\bbullet", t):
        return "variance"
    if re.search(r"\bbullet|\bbars?\b", t):
        return "bullet"
    return None
