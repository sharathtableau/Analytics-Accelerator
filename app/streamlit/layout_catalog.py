"""Saved multi-page BI layout catalog and audience-aware selector.

The catalog is reviewed application code. Cortex may suggest an allow-listed
saved template ID, but this module enforces audience and data-readiness gates.
MetricInventory MUST be assembled by trusted server-side code after Snowflake
semantic, freshness, quality, and permission checks.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Mapping, Optional


@dataclass(frozen=True)
class ComponentSpec:
    component_id: str
    kind: str
    title: str
    metric_role: Optional[str] = None
    required_roles: tuple[str, ...] = ()
    required_capabilities: tuple[str, ...] = ()
    optional: bool = False


@dataclass(frozen=True)
class PageSpec:
    page_id: str
    label: str
    purpose: str
    components: tuple[ComponentSpec, ...]


@dataclass(frozen=True)
class LayoutTemplate:
    template_id: str
    version: int
    audience_id: str
    display_name: str
    description: str
    required_roles: tuple[str, ...]
    required_capabilities: tuple[str, ...]
    optional_roles: tuple[str, ...]
    optional_capabilities: tuple[str, ...]
    pages: tuple[PageSpec, ...]
    priority: int = 100


@dataclass(frozen=True)
class MetricInventory:
    """Validated business metric bindings and capabilities from the app server."""
    role_to_metric_id: Mapping[str, str]
    validated_capabilities: frozenset[str]


@dataclass(frozen=True)
class TemplateCandidate:
    template_id: str
    audience_id: str
    display_name: str
    version: int
    compatible: bool
    fit_score: int
    missing_roles: tuple[str, ...]
    missing_capabilities: tuple[str, ...]
    missing_optional_roles: tuple[str, ...]
    missing_optional_capabilities: tuple[str, ...]


@dataclass(frozen=True)
class Selection:
    template: Optional[LayoutTemplate]
    status: str                   # ready | blocked | unavailable
    selected_by: str              # user | cortex | catalog_rules | none
    message: str
    rejected_cortex_suggestion: Optional[str]
    candidates: tuple[TemplateCandidate, ...]


def C(kind: str, component_id: str, title: str, *, role: str | None = None,
      roles: tuple[str, ...] = (), caps: tuple[str, ...] = (),
      optional: bool = False) -> ComponentSpec:
    return ComponentSpec(component_id, kind, title, role, roles, caps, optional)


def P(page_id: str, label: str, purpose: str, *components: ComponentSpec) -> PageSpec:
    return PageSpec(page_id, label, purpose, tuple(components))


# Edit this tuple to add or version reviewed presets. IDs and page IDs are
# stable API keys; display names and descriptions are safe to change separately.
CATALOG: tuple[LayoutTemplate, ...] = (
    LayoutTemplate(
        "exec_enterprise_performance", 1, "executives", "Enterprise Performance",
        "Strategic outcomes, trajectory, segments, and leadership follow-up.",
        ("strategic_kpi", "target"), ("comparable_time_series", "enterprise_scope_authorized"),
        ("forecast", "segment", "driver", "exception", "action_owner"),
        ("forecast_versioned", "stable_segment_hierarchy", "reconciled_driver_bridge", "action_tracking"),
        (
            P("executive_overview", "Overview", "Are enterprise outcomes on plan?",
              C("kpi_grid", "headline", "Strategic KPIs", roles=("strategic_kpi", "target")),
              C("trend_chart", "trajectory", "Performance trajectory", roles=("strategic_kpi",), caps=("comparable_time_series",)),
              C("exception_table", "attention", "Leadership attention", roles=("exception", "action_owner"), optional=True)),
            P("executive_trend", "Trend & outlook", "How is trajectory changing against plan?",
              C("trend_chart", "actual_plan", "Actual vs plan", roles=("strategic_kpi", "target"), caps=("comparable_time_series",)),
              C("forecast_band", "forecast", "Forecast outlook", role="forecast", caps=("forecast_versioned",), optional=True)),
            P("executive_portfolio", "Portfolio", "Which segments contribute to the result?",
              C("ranked_bar", "segments", "Segment comparison", roles=("segment", "strategic_kpi"), caps=("stable_segment_hierarchy",), optional=True),
              C("driver_bridge", "drivers", "Reconciled drivers", role="driver", caps=("reconciled_driver_bridge",), optional=True)),
            P("executive_actions", "Exceptions & actions", "What requires follow-up?",
              C("action_table", "followup", "Exceptions and owners", roles=("exception", "action_owner"), caps=("action_tracking",), optional=True)),
        ), 10,
    ),
    LayoutTemplate(
        "exec_portfolio_review", 1, "executives", "Portfolio & Market Review",
        "Compare authorized regions, business units, or markets.",
        ("strategic_kpi", "target", "segment"), ("stable_segment_hierarchy", "enterprise_scope_authorized"),
        ("driver", "forecast", "exception", "action_owner"),
        ("comparable_time_series", "reconciled_driver_bridge", "forecast_versioned", "action_tracking"),
        (
            P("portfolio_overview", "Portfolio overview", "Where is performance concentrated?",
              C("kpi_grid", "portfolio_kpis", "Portfolio KPIs", roles=("strategic_kpi", "target")),
              C("ranked_bar", "ranking", "Segment ranking", roles=("segment", "strategic_kpi"), caps=("stable_segment_hierarchy",))),
            P("portfolio_trends", "Market trends", "Are segment differences persistent?",
              C("small_multiples", "segment_trends", "Segment trends", roles=("segment", "strategic_kpi"), caps=("comparable_time_series", "stable_segment_hierarchy"))),
            P("portfolio_followup", "Drivers & follow-up", "What evidence and owners explain variance?",
              C("driver_bridge", "driver", "Driver analysis", role="driver", caps=("reconciled_driver_bridge",), optional=True),
              C("action_table", "actions", "Follow-up", roles=("exception", "action_owner"), caps=("action_tracking",), optional=True)),
        ), 20,
    ),
    LayoutTemplate(
        "manager_team_scorecard", 1, "managers", "Team Performance & Exceptions",
        "Track targets, team variance, and accountable follow-up.",
        ("manager_kpi", "target", "team_or_segment"),
        ("manager_scope_authorized", "comparable_time_series", "stable_segment_hierarchy"),
        ("driver", "exception", "action_owner"), ("reconciled_driver_bridge", "action_tracking"),
        (
            P("manager_overview", "Overview", "What needs my attention?",
              C("kpi_grid", "team_kpis", "Team KPIs", roles=("manager_kpi", "target")),
              C("trend_chart", "team_trend", "Trend vs target", role="manager_kpi", caps=("comparable_time_series",))),
            P("manager_segments", "Teams & segments", "Where is variance concentrated?",
              C("ranked_bar", "team_compare", "Team comparison", roles=("team_or_segment", "manager_kpi"), caps=("stable_segment_hierarchy",)),
              C("driver_bridge", "variance_drivers", "Variance drivers", role="driver", caps=("reconciled_driver_bridge",), optional=True)),
            P("manager_exceptions", "Exceptions", "Who owns follow-up?",
              C("exception_queue", "priority_queue", "Priority follow-up", roles=("exception", "action_owner"), caps=("action_tracking",), optional=True)),
        ), 10,
    ),
    LayoutTemplate(
        "manager_regional_scorecard", 1, "managers", "Regional Scorecard",
        "Compare regions and drill into authorized teams as needed.",
        ("manager_kpi", "target", "region"), ("manager_scope_authorized", "stable_segment_hierarchy"),
        ("team_or_segment", "driver", "exception", "action_owner"),
        ("comparable_time_series", "reconciled_driver_bridge", "action_tracking"),
        (
            P("regional_overview", "Regional overview", "How are regions performing?",
              C("kpi_grid", "regional_kpis", "Regional KPIs", roles=("manager_kpi", "target")),
              C("ranked_bar", "regional_ranking", "Target attainment", roles=("region", "manager_kpi"))),
            P("regional_trends", "Trend & comparison", "Which regions are changing?",
              C("small_multiples", "regional_trend", "Regional trends", roles=("region", "manager_kpi"), caps=("comparable_time_series",))),
            P("regional_followup", "Team detail & follow-up", "Which teams need action?",
              C("evidence_table", "team_detail", "Authorized team detail", role="team_or_segment", optional=True),
              C("exception_queue", "exceptions", "Regional exceptions", roles=("exception", "action_owner"), caps=("action_tracking",), optional=True)),
        ), 20,
    ),
    LayoutTemplate(
        "ops_queue_sla_triage", 1, "daily_operations", "Queue & SLA Triage",
        "Monitor current backlog and SLA risk, then move from queue to exception detail.",
        ("backlog", "sla_attainment", "queue"),
        ("fresh_data", "event_time", "operating_scope_authorized", "target"),
        ("exception", "action_owner", "throughput", "capacity"), ("action_tracking", "comparable_intraday_series"),
        (
            P("shift_control", "Shift control", "Are we safe now, and what needs action?",
              C("kpi_card", "backlog", "Open backlog", role="backlog", caps=("fresh_data",)),
              C("kpi_card", "sla", "SLA attainment", role="sla_attainment", caps=("target",)),
              C("risk_table", "queue_risk", "Queue risk", role="queue")),
            P("queue_sla", "Queue & SLA", "Which queue is at risk, and by how much?",
              C("trend_chart", "sla_trend", "Queue-level SLA trend", role="sla_attainment", roles=("queue",), caps=("comparable_intraday_series",)),
              C("exception_table", "breaches", "Breach follow-up", roles=("exception", "action_owner"), caps=("action_tracking",), optional=True)),
            P("ops_detail", "Detail & drivers", "What evidence explains the selected risk?",
              C("evidence_table", "event_detail", "Authorized event detail", role="queue", caps=("event_time",)),
              C("capacity_chart", "capacity", "Capacity context", role="capacity", optional=True)),
        ), 10,
    ),
    LayoutTemplate(
        "ops_capacity_flow", 1, "daily_operations", "Capacity & Flow",
        "Balance demand, throughput, backlog, and current capacity.",
        ("arrival_count", "throughput", "capacity"),
        ("fresh_data", "event_time", "operating_scope_authorized", "comparable_intraday_series"),
        ("queue", "backlog", "staffing", "exception"), ("target", "action_tracking"),
        (
            P("flow_overview", "Flow overview", "Is demand exceeding throughput or capacity?",
              C("trend_chart", "arrivals", "Arrivals", role="arrival_count", caps=("comparable_intraday_series",)),
              C("trend_chart", "throughput", "Completions", role="throughput", caps=("comparable_intraday_series",)),
              C("target_bar", "capacity", "Available capacity", role="capacity")),
            P("flow_queues", "Queue comparison", "Where is capacity pressure concentrated?",
              C("ranked_bar", "queue_pressure", "Pressure by queue", role="queue", optional=True),
              C("kpi_card", "backlog", "Backlog and age", role="backlog", optional=True)),
            P("flow_followup", "Exceptions & detail", "Which events need follow-up?",
              C("exception_queue", "exceptions", "Operational exceptions", role="exception", optional=True),
              C("evidence_table", "staffing", "Staffing detail", role="staffing", optional=True)),
        ), 20,
    ),
    LayoutTemplate(
        "wbr_plan_actual", 1, "weekly_business_review", "Plan vs Actual Review",
        "Review the finalized week, movement, segments, reconciled drivers, and actions.",
        ("wbr_kpi", "plan", "segment"), ("period_complete", "comparable_time_series", "plan_versioned"),
        ("driver", "leading_indicator", "risk", "action_owner"), ("reconciled_driver_bridge", "action_tracking"),
        (
            P("wbr_overview", "Overview", "What needs discussion this week?",
              C("kpi_grid", "outcomes", "Finalized outcomes vs plan", roles=("wbr_kpi", "plan"), caps=("period_complete",)),
              C("trend_chart", "movement", "Recent movement", role="wbr_kpi", caps=("comparable_time_series",))),
            P("wbr_segments", "Segments", "Where did the gap originate?",
              C("ranked_bar", "contribution", "Segment contribution", roles=("segment", "wbr_kpi"))),
            P("wbr_drivers", "Drivers & actions", "Can we reconcile the explanation and assign follow-up?",
              C("driver_bridge", "bridge", "Reconciled bridge", role="driver", caps=("reconciled_driver_bridge",), optional=True),
              C("action_table", "actions", "Actions and owners", role="action_owner", caps=("action_tracking",), optional=True)),
        ), 10,
    ),
    LayoutTemplate(
        "wbr_leading_indicators", 1, "weekly_business_review", "Leading Indicators & Risks",
        "Review leading signals and mitigations alongside governed outcomes.",
        ("wbr_kpi", "leading_indicator", "risk"), ("period_complete", "plan_versioned", "risk_metadata_current"),
        ("plan", "segment", "action_owner"), ("comparable_time_series", "action_tracking"),
        (
            P("risk_overview", "Risk overview", "Which signals may derail the plan?",
              C("kpi_grid", "indicators", "Outcomes and indicators", roles=("wbr_kpi", "leading_indicator")),
              C("risk_table", "risk_register", "Prioritized risks", role="risk", caps=("risk_metadata_current",))),
            P("indicator_trends", "Indicator trends", "Which leading signals are moving?",
              C("trend_chart", "indicator_trends", "Indicator trends", role="leading_indicator", caps=("comparable_time_series",), optional=True),
              C("segment_matrix", "risk_segments", "Risk by segment", roles=("segment", "risk"), optional=True)),
            P("risk_actions", "Mitigations & actions", "Who owns the next step?",
              C("action_table", "mitigations", "Mitigation owners and due dates", role="action_owner", caps=("action_tracking",), optional=True)),
        ), 20,
    ),
    # ---- Enterprise baseline presets (v1) -------------------------------------
    # For governed sources that have no versioned plan/target. They require only
    # what a Snowflake semantic view can prove (KPI, segment, time series) and
    # light up optional sections from Snowflake ML/Cortex (forecast, drivers)
    # and the app's decision log (actions). Target, when present, is an explicit
    # prior-year baseline, never an invented plan.
    LayoutTemplate(
        "exec_growth_baseline", 1, "executives", "Executive Growth Review",
        "Enterprise KPIs, trajectory vs last year, AI forecast, drivers and leadership actions.",
        ("strategic_kpi", "segment"),
        ("comparable_time_series", "enterprise_scope_authorized", "stable_segment_hierarchy"),
        ("target", "region", "forecast", "driver", "exception", "action_owner"),
        ("forecast_versioned", "reconciled_driver_bridge", "action_tracking"),
        (
            P("growth_overview", "Overview", "Is the business growing, and where should leaders look?",
              C("kpi_grid", "headline", "Headline KPIs", roles=("strategic_kpi",)),
              C("trend_chart", "trajectory", "Trajectory", role="strategic_kpi", caps=("comparable_time_series",)),
              C("exception_table", "attention", "Needs attention", roles=("exception", "segment"), optional=True)),
            P("growth_outlook", "Trend & outlook", "Are we ahead of last year, and where are we heading?",
              C("trend_chart", "vs_baseline", "Actual vs prior-year baseline", roles=("strategic_kpi", "target"), caps=("comparable_time_series",), optional=True),
              C("forecast_band", "forecast", "Snowflake ML forecast", role="forecast", roles=("strategic_kpi",), caps=("forecast_versioned",), optional=True)),
            P("growth_portfolio", "Segments & drivers", "Which segments explain the change?",
              C("ranked_bar", "segments", "Segment ranking", roles=("segment", "strategic_kpi"), caps=("stable_segment_hierarchy",)),
              C("driver_bridge", "drivers", "What drove the change", role="driver", roles=("strategic_kpi",), caps=("reconciled_driver_bridge",), optional=True),
              C("segment_matrix", "matrix", "Segment x region", roles=("segment", "region", "strategic_kpi"), optional=True)),
            P("growth_actions", "Decisions", "Who owns the follow-up?",
              C("action_table", "actions", "Decisions and owners", role="action_owner", caps=("action_tracking",), optional=True),
              C("evidence_table", "evidence", "Supporting detail", roles=("segment", "strategic_kpi"))),
        ), 15,
    ),
    LayoutTemplate(
        "manager_segment_scorecard", 1, "managers", "Segment Scorecard",
        "Compare segments, spot movers and exceptions, and assign follow-up.",
        ("manager_kpi", "team_or_segment"),
        ("manager_scope_authorized", "comparable_time_series", "stable_segment_hierarchy"),
        ("target", "region", "driver", "exception", "action_owner"),
        ("reconciled_driver_bridge", "action_tracking"),
        (
            P("scorecard_overview", "Scorecard", "How is each segment performing?",
              C("kpi_grid", "kpis", "Scorecard KPIs", roles=("manager_kpi",)),
              C("ranked_bar", "segment_rank", "Segment performance", roles=("team_or_segment", "manager_kpi"), caps=("stable_segment_hierarchy",))),
            P("scorecard_trends", "Trends", "Which segments are moving?",
              C("small_multiples", "segment_trends", "Segment trends", roles=("team_or_segment", "manager_kpi"), caps=("comparable_time_series",)),
              C("driver_bridge", "movers", "Period-over-period movers", role="driver", roles=("manager_kpi",), caps=("reconciled_driver_bridge",), optional=True)),
            P("scorecard_followup", "Exceptions & actions", "What needs follow-up and who owns it?",
              C("exception_queue", "exceptions", "Exception queue", roles=("exception", "team_or_segment"), optional=True),
              C("action_table", "actions", "Decisions and owners", role="action_owner", caps=("action_tracking",), optional=True),
              C("evidence_table", "detail", "Segment detail", roles=("team_or_segment", "manager_kpi"))),
        ), 15,
    ),
    LayoutTemplate(
        "wbr_weekly_performance", 1, "weekly_business_review", "Weekly Performance Review",
        "Finalized week vs prior week and last year, segment contribution, drivers, exceptions and actions.",
        ("wbr_kpi", "segment"), ("period_complete", "comparable_time_series"),
        ("target", "region", "forecast", "driver", "exception", "action_owner"),
        ("forecast_versioned", "reconciled_driver_bridge", "action_tracking"),
        (
            P("wbr_week", "This week", "What happened in the finalized week?",
              C("kpi_grid", "week_kpis", "Finalized week", roles=("wbr_kpi",), caps=("period_complete",)),
              C("trend_chart", "weekly_trend", "Weekly trend", role="wbr_kpi", caps=("comparable_time_series",))),
            P("wbr_contribution", "Contribution", "Where did the change come from?",
              C("ranked_bar", "segment_contribution", "Segment contribution", roles=("segment", "wbr_kpi")),
              C("driver_bridge", "wow_bridge", "Week-over-week bridge", role="driver", roles=("wbr_kpi",), caps=("reconciled_driver_bridge",), optional=True)),
            P("wbr_outlook", "Outlook & exceptions", "What should we watch next week?",
              C("forecast_band", "next_weeks", "Next weeks (Snowflake ML forecast)", role="forecast", roles=("wbr_kpi",), caps=("forecast_versioned",), optional=True),
              C("exception_table", "watchlist", "Watch list", roles=("exception", "segment"), optional=True)),
            P("wbr_actions", "Actions", "Who owns the next step?",
              C("action_table", "wbr_actions", "Actions and owners", role="action_owner", caps=("action_tracking",), optional=True)),
        ), 15,
    ),
)

AUDIENCES: tuple[str, ...] = (
    "executives", "managers", "daily_operations", "weekly_business_review"
)
CATALOG_BY_ID = {template.template_id: template for template in CATALOG}


def validate_catalog() -> tuple[str, ...]:
    errors: list[str] = []
    seen_templates: set[str] = set()
    for template in CATALOG:
        if template.template_id in seen_templates:
            errors.append(f"duplicate template ID: {template.template_id}")
        seen_templates.add(template.template_id)
        if template.audience_id not in AUDIENCES:
            errors.append(f"unknown audience: {template.audience_id}")
        page_ids = [page.page_id for page in template.pages]
        if not page_ids or len(page_ids) != len(set(page_ids)):
            errors.append(f"missing or duplicate page IDs: {template.template_id}")
        for page in template.pages:
            if not page.components:
                errors.append(f"page has no components: {page.page_id}")
            component_ids = [component.component_id for component in page.components]
            if len(component_ids) != len(set(component_ids)):
                errors.append(f"duplicate component IDs: {page.page_id}")
    for audience in AUDIENCES:
        if not any(template.audience_id == audience for template in CATALOG):
            errors.append(f"no template for audience: {audience}")
    return tuple(errors)


def list_templates(audience_id: Optional[str] = None) -> tuple[LayoutTemplate, ...]:
    items = CATALOG if audience_id is None else tuple(
        item for item in CATALOG if item.audience_id == audience_id
    )
    return tuple(sorted(items, key=lambda item: (item.priority, item.display_name)))


def get_template(template_id: str) -> Optional[LayoutTemplate]:
    return CATALOG_BY_ID.get(template_id)


def _candidate(template: LayoutTemplate, inventory: MetricInventory) -> TemplateCandidate:
    roles = set(inventory.role_to_metric_id)
    capabilities = set(inventory.validated_capabilities)
    missing_roles = tuple(sorted(set(template.required_roles) - roles))
    missing_caps = tuple(sorted(set(template.required_capabilities) - capabilities))
    missing_optional_roles = tuple(sorted(set(template.optional_roles) - roles))
    missing_optional_caps = tuple(sorted(set(template.optional_capabilities) - capabilities))
    optional_total = len(template.optional_roles) + len(template.optional_capabilities)
    optional_matched = optional_total - len(missing_optional_roles) - len(missing_optional_caps)
    fit = 100 if optional_total == 0 else round(100 * optional_matched / optional_total)
    return TemplateCandidate(
        template.template_id, template.audience_id, template.display_name, template.version,
        not missing_roles and not missing_caps, fit, missing_roles, missing_caps,
        missing_optional_roles, missing_optional_caps,
    )


def rank_templates(audience_id: str, inventory: MetricInventory) -> tuple[TemplateCandidate, ...]:
    """Rank only saved templates for the selected audience; explain hard-gate gaps."""
    candidates = [_candidate(item, inventory) for item in list_templates(audience_id)]
    priority = {item.template_id: item.priority for item in CATALOG}
    return tuple(sorted(candidates, key=lambda c: (
        not c.compatible, -c.fit_score, priority[c.template_id], c.template_id
    )))


def select_template(
    audience_id: str,
    inventory: MetricInventory,
    *,
    user_selected_template_id: Optional[str] = None,
    cortex_suggested_template_id: Optional[str] = None,
) -> Selection:
    """Accept a user choice, or validate an optional Cortex hint; never invent a template."""
    candidates = rank_templates(audience_id, inventory)
    by_id = {candidate.template_id: candidate for candidate in candidates}
    compatible = [candidate for candidate in candidates if candidate.compatible]

    if user_selected_template_id is not None:
        candidate = by_id.get(user_selected_template_id)
        if candidate is None:
            return Selection(None, "blocked", "user",
                             "That saved template does not belong to the selected audience.", None, candidates)
        if not candidate.compatible:
            missing = candidate.missing_roles + candidate.missing_capabilities
            return Selection(get_template(candidate.template_id), "blocked", "user",
                             "Template is missing validated requirements: " + ", ".join(missing),
                             None, candidates)
        return Selection(get_template(candidate.template_id), "ready", "user",
                         "Using the saved template selected by the user.", None, candidates)

    rejected: Optional[str] = None
    if cortex_suggested_template_id:
        candidate = by_id.get(cortex_suggested_template_id)
        if candidate is None:
            rejected = "Cortex suggestion was not a saved template for this audience; ignored."
        elif not candidate.compatible:
            missing = candidate.missing_roles + candidate.missing_capabilities
            rejected = "Cortex suggestion failed required data gates (" + ", ".join(missing) + "); ignored."
        else:
            return Selection(get_template(candidate.template_id), "ready", "cortex",
                             "Cortex suggested a saved template; application audience and data checks passed.",
                             None, candidates)

    if compatible:
        best = compatible[0]
        message = "Selected the highest-ranked compatible saved template by catalog rules."
        if rejected:
            message = rejected + " " + message
        return Selection(get_template(best.template_id), "ready", "catalog_rules", message, rejected, candidates)
    return Selection(None, "unavailable", "none",
                     "No saved template has all required validated data. Show missing requirements instead of inventing a layout.",
                     rejected, candidates)


def bind_template(template: LayoutTemplate, inventory: MetricInventory) -> dict[str, Any]:
    """Bind validated metric IDs to a JSON-safe page/component render spec."""
    global_candidate = _candidate(template, inventory)
    if not global_candidate.compatible:
        missing = global_candidate.missing_roles + global_candidate.missing_capabilities
        raise ValueError("Template does not pass hard gates: " + ", ".join(missing))

    role_map = dict(inventory.role_to_metric_id)
    capabilities = set(inventory.validated_capabilities)
    rendered_pages: list[dict[str, Any]] = []
    for page in template.pages:
        rendered_components = []
        for component in page.components:
            missing = set(component.required_roles) - set(role_map)
            if component.metric_role and component.metric_role not in role_map:
                missing.add(component.metric_role)
            missing.update(set(component.required_capabilities) - capabilities)
            missing_items = sorted(missing)
            state = "ready" if not missing_items else ("omitted" if component.optional else "blocked")
            rendered_components.append({
                "component_id": component.component_id,
                "type": component.kind,
                "title": component.title,
                "metric_id": role_map.get(component.metric_role) if component.metric_role else None,
                "role_bindings": {role: role_map[role] for role in component.required_roles if role in role_map},
                "state": state,
                "missing_requirements": missing_items,
            })
        rendered_pages.append({
            "page_id": page.page_id,
            "label": page.label,
            "purpose": page.purpose,
            "components": rendered_components,
        })
    return {
        "template_id": template.template_id,
        "template_version": template.version,
        "audience_id": template.audience_id,
        "display_name": template.display_name,
        "pages": rendered_pages,
    }


def picker_options(audience_id: str, inventory: MetricInventory) -> list[dict[str, Any]]:
    """UI cards: compatible options first, with reasons and page map."""
    result = []
    for candidate in rank_templates(audience_id, inventory):
        missing = list(candidate.missing_roles + candidate.missing_capabilities)
        optional_missing = list(candidate.missing_optional_roles + candidate.missing_optional_capabilities)
        result.append({
            **asdict(candidate),
            "selectable": candidate.compatible,
            "message": ("Ready" if candidate.compatible else "Missing: " + ", ".join(missing)),
            "optional_sections_hidden": optional_missing,
            "page_map": [
                {"page_id": page.page_id, "label": page.label, "purpose": page.purpose}
                for page in get_template(candidate.template_id).pages
            ],
        })
    return result


def cortex_allowlist(audience_id: str, inventory: MetricInventory) -> tuple[str, ...]:
    """Only compatible saved IDs for the already selected audience."""
    return tuple(candidate.template_id for candidate in rank_templates(audience_id, inventory)
                 if candidate.compatible)


def cortex_selection_prompt(audience_id: str, inventory: MetricInventory) -> str:
    allowed = cortex_allowlist(audience_id, inventory)
    if not allowed:
        return "No compatible saved templates. Return template_id=null."
    return (
        "Choose one existing dashboard template that best fits the user's stated need. "
        "Return JSON {template_id, reason}. You MUST choose from this allowlist or null. "
        "Do not invent IDs, pages, components, SQL, metrics, or permissions. "
        f"Audience={audience_id}; allowed template IDs={list(allowed)}."
    )


def validate_cortex_output(
    audience_id: str, inventory: MetricInventory, output: Any
) -> Selection:
    """Validate parsed Cortex JSON. Prose or unknown IDs never become templates."""
    suggestion: Optional[str] = None
    if isinstance(output, dict) and isinstance(output.get("template_id"), str):
        suggestion = output["template_id"]
    return select_template(audience_id, inventory, cortex_suggested_template_id=suggestion)


def template_to_dict(template: LayoutTemplate) -> dict[str, Any]:
    return asdict(template)


if errors := validate_catalog():
    raise ValueError("Invalid code-resident layout catalog: " + "; ".join(errors))

__all__ = [
    "AUDIENCES", "CATALOG", "ComponentSpec", "LayoutTemplate", "MetricInventory",
    "PageSpec", "Selection", "TemplateCandidate", "bind_template", "cortex_allowlist",
    "cortex_selection_prompt", "get_template", "list_templates", "picker_options",
    "rank_templates", "select_template", "template_to_dict", "validate_catalog",
    "validate_cortex_output",
]

if __name__ == "__main__":
    print(f"Loaded {len(CATALOG)} saved templates.")
    for audience in AUDIENCES:
        for template in list_templates(audience):
            print(f"{audience}: {template.template_id} v{template.version} — {template.display_name}")
            print("  " + " -> ".join(page.page_id for page in template.pages))
    print("Catalog validation:", "OK" if not validate_catalog() else validate_catalog())
