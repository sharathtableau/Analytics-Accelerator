"""Build the trusted MetricInventory for the layout catalog.

Roles come from reviewed bindings of semantic-view fields. Capabilities are
computed from evidence (queries against the semantic view, feature checks, app
tables); each capability carries a human-readable reason so the UI can show
*why* a layout is or is not available.
"""
from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field, asdict
from typing import Any, Optional

from layout_catalog import MetricInventory
from semantic_catalog import SemanticModel
from semantic_query import AUDIENCE_GRAIN, Calendar, SemanticQuery

KPI_ROLES = ("strategic_kpi", "manager_kpi", "wbr_kpi")
SEGMENT_ROLES = ("segment", "team_or_segment")
SOURCE_BASELINE = "BASELINE:PRIOR_YEAR"
SOURCE_FORECAST = "ML:FORECAST"
SOURCE_DRIVERS = "ML:TOP_INSIGHTS"
SOURCE_EXCEPTIONS = "APP:EXCEPTIONS"
SOURCE_DECISIONS = "APP:DECISIONS"

METRIC_HINTS = (r"SALES|REVENUE|BOOKING|GMV|AMOUNT", r"PROFIT|MARGIN|EBIT", r"ORDER|COUNT|QUANTITY|UNITS|VOLUME")
SEGMENT_HINTS = (r"SEGMENT", r"CATEGORY", r"CHANNEL|PRODUCT_LINE|LINE_OF_BUSINESS|BU\b", r"TYPE|CLASS")
REGION_HINTS = (r"REGION|TERRITORY|MARKET|COUNTRY|STATE|GEO",)


@dataclass
class Bindings:
    """Reviewed field choices. IDs are ENTITY.NAME from the semantic view."""
    primary_metric: str = ""
    supporting_metrics: list[str] = field(default_factory=list)
    time_dimension: str = ""
    segment_dimension: str = ""
    region_dimension: str = ""
    use_baseline: bool = True        # prior-year baseline as an explicit, labelled target
    use_forecast: bool = True        # Snowflake ML FORECAST
    use_drivers: bool = True         # Snowflake ML TOP_INSIGHTS / contribution bridge
    reviewed_by: str = ""
    source: str = "heuristic"        # heuristic | cortex | user

    @staticmethod
    def from_dict(data: dict[str, Any]) -> "Bindings":
        allowed = {f for f in Bindings.__dataclass_fields__}
        clean = {k: v for k, v in (data or {}).items() if k in allowed}
        b = Bindings(**clean)
        b.supporting_metrics = [m for m in (b.supporting_metrics or []) if m and m != b.primary_metric]
        b.supporting_metrics = list(dict.fromkeys(b.supporting_metrics))
        return b

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _first(pattern_list, items, used=()):
    for pattern in pattern_list:
        for item in items:
            if item.id not in used and re.search(pattern, item.name, re.I):
                return item.id
    return ""


def infer_bindings(model: SemanticModel) -> Bindings:
    """Deterministic first guess the user reviews (Cortex can improve it)."""
    metrics = model.metrics
    primary = (_first((r"^NET_(SALES|REVENUE)$", r"^(SALES|REVENUE)$"), metrics)
               or _first(METRIC_HINTS[:1], metrics) or (metrics[0].id if metrics else ""))
    support = []
    for hints in ((r"^GROSS_MARGIN$", r"^(GROSS_)?PROFIT$") + METRIC_HINTS[1:2],
                  (r"^(ORDER_COUNT|ORDERS|UNITS_SOLD)$",) + METRIC_HINTS[2:3]):
        pick = _first(hints, metrics, used=[primary] + support)
        if pick:
            support.append(pick)
    for m in metrics:
        if len(support) >= 3:
            break
        if m.id != primary and m.id not in support and m.additive:
            support.append(m.id)
    times = model.time_dimensions
    time = _first((r"^(CALENDAR_DATE|DATE_KEY|DATE)$", r"ORDER_DATE|TRANSACTION_DATE|EVENT_DATE"), times) or (times[0].id if times else "")
    cats = model.categorical_dimensions
    segment = _first(SEGMENT_HINTS, cats)
    region = _first(REGION_HINTS, cats, used=[segment])
    if not segment and cats:
        segment = next((c.id for c in cats if c.id != region), "")
    return Bindings(primary, support, time, segment, region)


def validate_bindings(model: SemanticModel, b: Bindings) -> list[str]:
    errors = []
    metric_ids = {m.id.upper() for m in model.metrics}
    time_ids = {d.id.upper() for d in model.time_dimensions}
    cat_ids = {d.id.upper() for d in model.categorical_dimensions}
    if b.primary_metric.upper() not in metric_ids:
        errors.append("Choose a primary metric from the semantic view.")
    for m in b.supporting_metrics:
        if m.upper() not in metric_ids:
            errors.append(f"{m} is not a metric in the semantic view.")
    if b.time_dimension.upper() not in time_ids:
        errors.append("Choose a date/time dimension.")
    for label, value in (("segment", b.segment_dimension), ("region", b.region_dimension)):
        if value and value.upper() not in cat_ids:
            errors.append(f"{value} is not a categorical dimension ({label}).")
    if b.segment_dimension and b.segment_dimension == b.region_dimension:
        errors.append("Segment and region must be different dimensions.")
    return errors


@dataclass
class Evidence:
    granted: bool
    reason: str


@dataclass
class Profile:
    """Everything proven about the source for one audience grain."""
    audience: str
    calendar: Optional[Calendar]
    distinct: dict[str, int]
    capabilities: dict[str, Evidence]
    roles: dict[str, str]
    role_reasons: dict[str, str]
    current_role: str = ""

    def inventory(self) -> MetricInventory:
        return MetricInventory(dict(self.roles),
                               frozenset(k for k, v in self.capabilities.items() if v.granted))

    def as_dict(self) -> dict[str, Any]:
        return {
            "audience": self.audience,
            "calendar": self.calendar.as_dict() if self.calendar else None,
            "distinct": self.distinct,
            "capabilities": {k: asdict(v) for k, v in sorted(self.capabilities.items())},
            "roles": self.roles,
            "role_reasons": self.role_reasons,
            "current_role": self.current_role,
        }


def build_profile(session, model: SemanticModel, b: Bindings, audience: str,
                  features: dict[str, bool], today: Optional[dt.date] = None,
                  log: Optional[list] = None, grain: Optional[str] = None) -> Profile:
    today = today or dt.date.today()
    q = SemanticQuery(session, model, log)
    grain = grain if grain in ("day", "week", "month", "quarter") else AUDIENCE_GRAIN[audience]
    caps: dict[str, Evidence] = {}
    roles: dict[str, str] = {}
    reasons: dict[str, str] = {}

    current_role = ""
    try:
        current_role = str(q.run("SELECT CURRENT_ROLE() AS R")[0].get("r") or "")
    except Exception:
        pass

    cal = None
    try:
        cal = q.calendar(b.time_dimension, b.primary_metric, grain)
        authorized = Evidence(True, f"Role {current_role or 'current role'} queried {model.fqn} "
                                    "successfully; Snowflake RBAC and row policies apply to every query.")
    except Exception as exc:
        authorized = Evidence(False, f"Query through {model.fqn} failed: {exc}")
    for cap in ("enterprise_scope_authorized", "manager_scope_authorized", "operating_scope_authorized"):
        caps[cap] = authorized

    distinct = {}
    cats = [d for d in (b.segment_dimension, b.region_dimension) if d]
    if cal and cats:
        try:
            distinct = q.distinct_counts(cats)
        except Exception:
            distinct = {}

    if cal:
        n_periods = 0
        start = cal.window_start
        from semantic_query import shift
        while start <= cal.current_start:
            n_periods += 1
            start = shift(start, grain, 1)
        caps["comparable_time_series"] = Evidence(
            n_periods >= 6,
            f"{n_periods} complete {grain}s available ({cal.label(cal.window_start)} – {cal.label(cal.current_start)}).")
        caps["period_complete"] = Evidence(
            True, f"Latest complete {grain} is {cal.label(cal.current_start)}; data ends {cal.max_date:%d %b %Y}.")
        age = (today - cal.max_date).days
        caps["fresh_data"] = Evidence(age <= 2, f"Latest data is {age} day(s) old (as of {cal.max_date:%d %b %Y}).")
        caps["event_time"] = Evidence(True, f"{b.time_dimension} is a date/time dimension.")
        caps["comparable_intraday_series"] = Evidence(False, "Source is at day grain; no intraday timestamps.")
        yoy_ok = cal.yoy_start >= cal.window_start
        if b.use_baseline:
            caps["target"] = Evidence(yoy_ok, "Target = prior-year baseline (" + cal.label(cal.yoy_start) + ")."
                                      if yoy_ok else "Not enough history for a prior-year baseline.")
        else:
            caps["target"] = Evidence(False, "No governed target; prior-year baseline switched off.")
        forecast_ok = features.get("forecast", False) and b.use_forecast and n_periods >= 12
        caps["forecast_versioned"] = Evidence(
            forecast_ok,
            "Snowflake ML FORECAST trained per run on the governed series; model name and run time are recorded."
            if forecast_ok else ("Snowflake ML FORECAST unavailable for this role." if not features.get("forecast")
                                 else "Forecast switched off or fewer than 12 periods."))
    else:
        for cap in ("comparable_time_series", "period_complete", "fresh_data", "event_time", "target",
                    "forecast_versioned", "comparable_intraday_series"):
            caps[cap] = Evidence(False, "No readable time series.")

    seg_n = distinct.get(b.segment_dimension, 0)
    caps["stable_segment_hierarchy"] = Evidence(
        2 <= seg_n <= 60,
        f"{b.segment_dimension or 'No segment'} has {seg_n} distinct values" + ("." if 2 <= seg_n <= 60 else " (needs 2–60)."))

    primary = model.field(b.primary_metric, ("metric",)) if b.primary_metric else None
    additive = bool(primary and primary.additive)
    caps["reconciled_driver_bridge"] = Evidence(
        bool(b.use_drivers and additive and b.segment_dimension and cal),
        "Segment contributions of an additive metric sum exactly to the total change."
        if additive else f"{b.primary_metric} is not additive (ratio/distinct), so a bridge would not reconcile.")
    caps["action_tracking"] = Evidence(True, "Decisions are stored in the app's Snowflake decision log with owner and due date.")
    caps["plan_versioned"] = Evidence(False, "No versioned plan object is registered.")
    caps["risk_metadata_current"] = Evidence(False, "No risk register is registered.")
    caps["stable_segment_hierarchy"]  # keep order readable

    # ---- roles ----------------------------------------------------------------
    if b.primary_metric:
        for r in KPI_ROLES:
            roles[r] = b.primary_metric
        reasons["kpi"] = f"Primary metric {b.primary_metric} from {model.fqn}."
    if b.segment_dimension:
        for r in SEGMENT_ROLES:
            roles[r] = b.segment_dimension
        reasons["segment"] = f"Segment dimension {b.segment_dimension}."
    if b.region_dimension:
        roles["region"] = b.region_dimension
        reasons["region"] = f"Region dimension {b.region_dimension}."
    if caps["target"].granted:
        roles["target"] = SOURCE_BASELINE
        reasons["target"] = caps["target"].reason
    if caps["forecast_versioned"].granted:
        roles["forecast"] = SOURCE_FORECAST
        reasons["forecast"] = "Snowflake ML FORECAST on the primary metric."
    if caps["reconciled_driver_bridge"].granted:
        roles["driver"] = SOURCE_DRIVERS
        reasons["driver"] = "Snowflake ML TOP_INSIGHTS, reconciled with a contribution bridge."
    if cal and b.segment_dimension and caps["comparable_time_series"].granted:
        roles["exception"] = SOURCE_EXCEPTIONS
        reasons["exception"] = "Segments whose latest period deviates ≥ 2σ from their own history."
    roles["action_owner"] = SOURCE_DECISIONS
    reasons["action_owner"] = "App decision log."

    return Profile(audience, cal, distinct, caps, roles, reasons, current_role)
