"""Persona layouts: a reviewed skeleton per audience, slots filled by Cortex, certified by the validator.

Why: when Cortex designed every layout from scratch, Executive, Manager and Operations dashboards
converged on the same shape (KPI row + the same charts). The audience now decides the skeleton
(question, time grain, density, interaction); Cortex only chooses which metrics and breakdowns fill
each slot, from options that are valid for that slot; the Validator certifies every tile.

  Executive  - one-page brief: KPIs vs plan (YTD) · cumulative trajectory + ML forecast · drivers · decisions
  Manager    - scorecard & drill: region x KPI scorecard · exceptions · trends · drivers · detail
  Operations - live control room: status now · today's pace by hour · hour x day heatmap · worklist
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Optional

from composer import DataContext, Governance, validate_layout
from engine import fmt_kind

PERSONAS = ("executives", "managers", "daily_operations")
# plan targets and helpers, and variance metrics such as NET_SALES_VS_PLAN (actual - plan): the tiles compute the
# variance themselves, so a variance as a headline KPI would be compared with plan/last year a second time
SKIP = re.compile(r"^PLAN_|^HELPER_|_VS_|VARIANCE|_GAP$|_DELTA$", re.I)

META = {
    "executives": {"title": "Executive brief", "question": "Are we on plan this year, why, and what are we doing about it?",
                   "summary": "One page for leadership: year to date against plan, where the year is heading, what "
                              "drove the change, and the decisions in flight."},
    "managers": {"title": "Performance scorecard", "question": "Which of my areas are off plan this week, and who is on it?",
                 "summary": "Weekly scorecard by area with red/amber/green against plan, the exceptions to act on, "
                            "and drill-down to the drivers and detail."},
    "daily_operations": {"title": "Live operations", "question": "Are we OK right now, and what needs action this hour?",
                         "summary": "Today so far against the same time last week, the pace by hour, and a worklist "
                                    "of what is going wrong right now."},
}


# Reviewed layouts per audience. The first one is the default; Cortex (or the rules below) picks the one that fits
# the question, and the builder can switch on Review. Every layout is filled from the same slots.
VARIANTS = {
    "executives": [
        {"id": "plan", "title": "Year vs plan brief", "when": "how the year is going against plan, overall performance",
         "summary": META["executives"]["summary"]},
        {"id": "growth_mix", "title": "Growth & mix",
         "when": "growth, trend, mix or share questions (where growth comes from, which segments gain share)",
         "summary": "Headline KPIs against last year, the trend of the lead metric, its mix across the main "
                    "breakdown, and how each segment moved."},
        {"id": "question", "title": "Answer first",
         "when": "a specific question about one metric by one breakdown (e.g. returns by channel)",
         "summary": "Opens with the answer to the question asked, then the headline KPIs and what drove the change."},
    ],
    "managers": [
        {"id": "scorecard", "title": "Performance scorecard", "when": "routine weekly review of areas vs plan",
         "summary": META["managers"]["summary"]},
        {"id": "exceptions", "title": "Exceptions first",
         "when": "problems, issues, anomalies, what is off track and needs action",
         "summary": "Opens with what is outside its normal range, where it is concentrated, and the trends behind it."},
        {"id": "compare", "title": "Compare segments",
         "when": "ranking or comparing areas, best and worst, one segment versus another",
         "summary": "Ranks the areas, compares them with the prior period and last year, and maps two breakdowns "
                    "and two metrics against each other."},
    ],
    "daily_operations": [
        {"id": "live", "title": "Live operations", "when": "right now, today, this hour",
         "summary": META["daily_operations"]["summary"]},
        {"id": "daily", "title": "Daily tracker", "when": "the last few days, yesterday, day-by-day trends and issues",
         "summary": "Status today, the daily trend with unusual days flagged, and a worklist of what to fix."},
    ],
}
VARIANT_RULES = {
    "executives": [("growth_mix", r"\bgrow|growth|\bmix\b|\bshare\b|trend|gaining|losing"),
                   ("question", r"\bby\s+\w+|which\s+\w+|per\s+\w+|each\s+\w+|every\s+\w+")],
    "managers": [("exceptions", r"exception|issue|problem|anomal|off[ -]?track|wrong|risk|alert"),
                 ("compare", r"compar|versus|\bvs\b|rank|best|worst|top\s+\d*|bottom")],
    "daily_operations": [("daily", r"yesterday|last\s+\d+\s+days|daily|this week|day by day|past week")],
}


def variant_ids(persona: str) -> list[str]:
    return [v["id"] for v in VARIANTS.get(persona, [])]


def rule_variant(persona: str, goal: str) -> str:
    for vid, rx in VARIANT_RULES.get(persona, []):
        if re.search(rx, goal or "", re.I):
            return vid
    return variant_ids(persona)[0]


def text_focus(ctx: DataContext, goal: str) -> dict[str, Optional[str]]:
    """Metric and breakdown the question names, matched on labels and names (longest first)."""
    g = " " + re.sub(r"[^a-z0-9]+", " ", (goal or "").lower()) + " "
    def hit(fields):
        best = None
        for f in fields:
            for name in {f.label.lower(), f.name.lower().replace("_", " ")}:
                if len(name) > 2 and f" {name} " in g and (best is None or len(name) > best[1]):
                    best = (f.id, len(name))
        return best[0] if best else None
    dim = None
    for f in ctx.model.categorical_dimensions:          # "by <dimension>" wins
        for name in {f.label.lower(), f.name.lower().replace("_", " ")}:
            forms = "|".join(re.escape(x) for x in {name, name + "s", name[:-1] + "ies" if name.endswith("y") else name})
            if re.search(rf"\b(by|per|across|which|each|every|compare|comparing)\s+({forms})\b", g):
                dim = f.id
    return {"metric": hit(_metrics(ctx)), "dimension": dim}           # a breakdown only when asked "by X"


# ----------------------------------------------------------------------------- slot options
def _metrics(ctx: DataContext) -> list:
    return [m for m in ctx.model.metrics if not SKIP.search(m.name)]


def _pick(ctx: DataContext, patterns: list[str], pool: list[str], n: int, start: Optional[list[str]] = None) -> list[str]:
    names = {m.id: m.name for m in ctx.model.metrics}
    out = [x for x in (start or []) if x in pool]
    for pat in patterns:
        if len(out) >= n:
            break
        hit = next((m for m in pool if m not in out and re.search(pat, names[m], re.I)), None)
        if hit:
            out.append(hit)
    for m in pool:                      # top up in catalogue order
        if len(out) >= n:
            break
        if m not in out:
            out.append(m)
    return out[:n]


def _dims(ctx: DataContext, patterns: list[str], n: int, lo: int = 2, hi: int = 80,
          start: Optional[list[str]] = None) -> list[str]:
    hour = ctx.hour_dim()
    pool = [d.id for d in ctx.model.categorical_dimensions if d.id != hour
            and (ctx.distinct.get(d.id) is None or lo <= ctx.distinct.get(d.id) <= hi)]
    names = {d.id: d.name for d in ctx.model.categorical_dimensions}
    out = [d for d in (start or []) if d in pool]
    for pat in patterns:
        if len(out) >= n:
            break
        hit = next((d for d in pool if d not in out and re.search(pat, names[d], re.I)), None)
        if hit:
            out.append(hit)
    for d in pool:
        if len(out) >= n:
            break
        if d not in out:
            out.append(d)
    return out[:n]


def slot_options(ctx: DataContext, persona: str) -> dict[str, dict[str, Any]]:
    """Each slot: allowed ids, how many to pick, and the default pick (used when Cortex is unavailable)."""
    b = ctx.bindings
    time_ok = [m.id for m in _metrics(ctx) if ctx.allowed(m.id, b.time_dimension)]
    cum = [m for m in time_ok if ctx.cumulable(m)]
    approved = [m for m in [b.primary_metric, *b.supporting_metrics] if m in time_ok]
    # opened from a Home idea: the idea's metrics (its theme) lead every metric slot
    lead = len(approved) if getattr(b, "source", "") == "idea" else 0
    region = b.region_dimension or b.segment_dimension
    segment = b.segment_dimension or b.region_dimension
    cats = [d.id for d in ctx.model.categorical_dimensions if d.id != ctx.hour_dim()]
    if persona == "executives":
        n_head = min(5, max(4, lead))           # up to 5 headline cards when the user picked more metrics
        head = _pick(ctx, [r"MARGIN_PCT|MARGIN_RATE|PROFIT_RATIO|GM", r"ONLINE.*SHARE|DIGITAL", r"IN_STOCK|AVAILAB",
                           r"ORDER_COUNT|^ORDERS$"], time_ok, n_head, approved[:max(2, lead)])
        traj = next((m for m in [b.primary_metric, *head] if m in cum), cum[0] if cum else b.primary_metric)
        mix = _dims(ctx, [r"CHANNEL", r"CATEGORY", r"SEGMENT"], 1, 2, 10, [segment])
        return {
            "headline_kpis": {"options": time_ok, "n": n_head, "default": head,
                              "what": f"{n_head} headline KPIs shown year-to-date against plan"},
            "trajectory_metric": {"options": cum, "n": 1, "default": [traj],
                                  "what": "the summable metric whose cumulative year is charted against plan"},
            "driver_dimension": {"options": cats, "n": 1, "kind": "dimension",
                                 "default": _dims(ctx, [], 1, 2, 60, [region]),
                                 "what": "breakdown that explains what drove the change"},
            "mix_dimension": {"options": cats, "n": 1, "kind": "dimension", "default": mix,
                              "what": "small breakdown (up to 10 values) for the mix / share view"},
        }
    if persona == "managers":
        score = _pick(ctx, [r"MARGIN_PCT|PROFIT_RATIO", r"ON_TIME", r"IN_STOCK|STOCKOUT", r"RETURN_RATE"],
                      time_ok, 5, approved[:max(1, lead)])
        return {
            "scorecard_dimension": {"options": cats, "n": 1, "kind": "dimension",
                                    "default": _dims(ctx, [], 1, 2, 40, [region]),
                                    "what": "the areas the manager is accountable for (rows of the scorecard)"},
            "scorecard_kpis": {"options": time_ok, "n": 5, "default": score,
                               "what": "KPIs in the scorecard columns, compared with plan or the prior week"},
            "exception_dimension": {"options": cats, "n": 1, "kind": "dimension",
                                    "default": _dims(ctx, [r"SUBCATEGORY|CLASS", r"CATEGORY"], 1, 4, 200, []),
                                    "what": "breakdown scanned for anomalies (Snowflake ML)"},
            "driver_dimension": {"options": cats, "n": 1, "kind": "dimension",
                                 "default": _dims(ctx, [r"CATEGORY", r"CHANNEL"], 1, 2, 60, [segment]),
                                 "what": "breakdown for the variance bridge"},
            "detail_dimension": {"options": cats, "n": 1, "kind": "dimension",
                                 "default": _dims(ctx, [r"SUBCATEGORY", r"PRODUCT|STORE"], 1, 5, 100000, []) or [],
                                 "what": "fine-grained breakdown for concentration (Pareto) and detail"},
        }
    # daily operations
    hour_ok = [m for m in cum if ctx.hour_dim(m)] or cum
    pace = _pick(ctx, [r"ORDER_COUNT|^ORDERS$"], hour_ok, 1, [])
    status = _pick(ctx, [r"ORDER_COUNT|^ORDERS$", r"ON_TIME", r"CLICK_TO_SHIP|FULFIL", r"STOCKOUT|IN_STOCK",
                         r"LOST"], time_ok, 4, approved[:lead] or [b.primary_metric])
    work = _pick(ctx, [r"LOST_SALES|STOCKOUT", r"ON_TIME|DELIVERY_DAYS", r"RETURN_RATE"], time_ok, 4,
                 approved[:lead] or [b.primary_metric])
    return {
        "status_kpis": {"options": time_ok, "n": 4, "default": status,
                        "what": "what the floor watches right now (today vs same time last week)"},
        "pace_metric": {"options": hour_ok, "n": 1, "default": pace or [b.primary_metric],
                        "what": "the volume metric whose running total by hour shows today's pace"},
        "worklist_kpis": {"options": time_ok, "n": 4, "default": work,
                          "what": "metrics scanned for today's problems"},
        "worklist_dimensions": {"options": cats, "n": 3, "kind": "dimension",
                                "default": _dims(ctx, [r"SUBCATEGORY", r"DISTRIBUTION|_DC$|WAREHOUSE", r"CARRIER",
                                                       r"CHANNEL"], 3, 2, 120, []),
                                "what": "where problems are located (e.g. product line, DC, carrier)"},
    }


# ----------------------------------------------------------------------------- Cortex slot fill
def slot_prompt(ctx: DataContext, persona: str, goal: str, slots: dict[str, dict[str, Any]], asked: str = "") -> str:
    m_lbl = {m.id: f"{m.id} ({m.label}{': ' + m.comment[:70] if m.comment else ''})" for m in ctx.model.metrics}
    d_lbl = {d.id: f"{d.id} ({d.label}, {ctx.distinct.get(d.id, '?')} values)" for d in ctx.model.categorical_dimensions}
    lines = []
    for name, sl in slots.items():
        lbl = d_lbl if sl.get("kind") == "dimension" else m_lbl
        lines.append(f"- {name}: pick {sl['n']} — {sl['what']}. Options: " + "; ".join(lbl[x] for x in sl["options"]))
    meta = META[persona]
    return (
        "You are filling a reviewed dashboard layout for one audience. The layout is fixed; you only choose "
        "which fields fill each slot, so the dashboard answers the audience's question for this user's goal.\n"
        f"Audience question: {meta['question']}\n"
        f"User goal: {goal.strip() or 'general performance for this audience'}\n"
        + (f"The person's own words: {asked[:300]}\n" if asked and asked.lower() not in goal.lower() else "") +
        f"Semantic view: {ctx.model.fqn}. {ctx.model.comment or ''}\n"
        "Slots (use ONLY ids from each slot's options, exactly as written):\n" + "\n".join(lines) + "\n"
        "Layouts for this audience (pick the one that fits the user goal best):\n"
        + "\n".join(f"- {v['id']}: {v['title']} - use for {v['when']}" for v in VARIANTS[persona]) + "\n"
        "Focus: only if the person's own words (or the goal, when no own words are given) name a specific metric "
        "and/or breakdown (e.g. 'returns by channel'), give their ids "
        "(metric from any metric slot's options, dimension from any dimension slot's options), else null.\n"
        'Respond with JSON only: {"title": "<dashboard title, max 6 words>", "summary": "<one sentence>", '
        '"layout": "<layout id>", "focus": {"metric": "<id or null>", "dimension": "<id or null>"}, '
        '"slots": {"<slot>": ["<id>", ...]}}'
    )


def fill_slots(cortex, ctx: DataContext, persona: str, goal: str,
               asked: str = "") -> tuple[dict[str, list[str]], dict[str, Any], list]:
    slots = slot_options(ctx, persona)
    chosen = {k: list(v["default"]) for k, v in slots.items()}
    info: dict[str, Any] = {"origin": "defaults", "title": None, "summary": None}
    notes = []
    if cortex is not None:
        try:
            from ai_services import _json_from_text
            text, prov = cortex.complete(slot_prompt(ctx, persona, goal, slots, asked))
            raw = _json_from_text(text)
            got = raw.get("slots") or {}
            for k, sl in slots.items():
                picks = [x for x in (got.get(k) or []) if isinstance(x, str)]
                ok = [x for x in picks if x in sl["options"]]
                bad = [x for x in picks if x not in sl["options"]]
                if bad:
                    notes.append({"page": "-", "tile": k, "action": "repaired",
                                  "reason": f"Cortex picked {', '.join(bad)}, not valid for this slot → ignored"})
                if ok:
                    chosen[k] = list(dict.fromkeys(ok))[: sl["n"]]
                    if len(chosen[k]) < sl["n"]:     # top up with defaults
                        chosen[k] += [x for x in sl["default"] if x not in chosen[k]][: sl["n"] - len(chosen[k])]
            info = {"origin": "cortex", "title": str(raw.get("title") or "")[:60] or None,
                    "summary": str(raw.get("summary") or "")[:240] or None, "provenance": prov}
            if raw.get("layout") in variant_ids(persona):
                info["layout"] = raw["layout"]
            fo = raw.get("focus") if isinstance(raw.get("focus"), dict) else {}
            metrics_ok = {m.id for m in ctx.model.metrics}
            dims_ok = {d.id for d in ctx.model.categorical_dimensions}
            info["focus"] = {"metric": fo.get("metric") if fo.get("metric") in metrics_ok else None,
                             "dimension": fo.get("dimension") if fo.get("dimension") in dims_ok else None}
        except Exception as exc:                       # Cortex optional: the reviewed defaults always work
            info["error"] = str(exc)[:200]
    return chosen, info, notes


# ----------------------------------------------------------------------------- skeletons
def skeleton(ctx: DataContext, persona: str, s: dict[str, list[str]]) -> dict[str, Any]:
    lab = lambda m: ctx.model.field(m, ("metric",)).label
    dlab = lambda d: ctx.model.field(d, ("dimension",)).label if d else "breakdown"
    one = lambda k: (s.get(k) or [None])[0]
    if persona == "executives":
        traj, drv = one("trajectory_metric"), one("driver_dimension")
        return {"pages": [{
            "label": "Brief", "question": META[persona]["question"], "tiles": [
                {"type": "kpi_plan", "title": "Year to date vs plan", "metrics": s["headline_kpis"],
                 "question": "Are we on plan for the year?", "width": 12},
                {"type": "ytd_trajectory", "title": f"{lab(traj)}: where the year is heading", "metric": traj,
                 "question": "Cumulative year vs plan and last year, with the Snowflake ML forecast to year end.",
                 "width": 7},
                {"type": "gauge", "title": f"{lab(traj)}: progress to the full year", "metric": traj,
                 "question": "How much of the year's target is done, and are we on pace?", "width": 5},
                {"type": "driver_bridge", "title": f"What drove the change, by {dlab(drv).lower()}", "metric": traj,
                 "dimension": drv, "question": "Which areas explain the movement vs the prior month?", "width": 12},
                {"type": "action_table", "title": "Decisions & asks", "width": 12,
                 "question": "What has leadership decided, who owns it, and when is it due?"},
            ]}]}
    if persona == "managers":
        dim, kpis = one("scorecard_dimension"), s["scorecard_kpis"]
        lead = kpis[0]
        exc, drv, det = one("exception_dimension"), one("driver_dimension"), one("detail_dimension")
        return {"pages": [
            {"label": "Scorecard", "question": META[persona]["question"], "tiles": [
                {"type": "scorecard", "title": f"Scorecard by {dlab(dim).lower()}", "metrics": kpis, "dimension": dim,
                 "question": "Red/amber/green vs plan (or the prior week). Click a row to drill in.", "width": 8},
                {"type": "exception_table", "title": "Exceptions to act on", "metric": lead, "dimension": exc,
                 "question": f"Which {dlab(exc).lower()} values are outside their normal range?", "width": 4},
                {"type": "small_multiples", "title": f"{lab(lead)} trend by {dlab(dim).lower()}", "metric": lead,
                 "dimension": dim, "question": "Is the gap new or persistent?", "width": 12},
            ]},
            {"label": "Drivers", "question": "What drove the gap, and where is it concentrated?", "tiles": [
                {"type": "driver_bridge", "title": f"{lab(lead)} bridge by {dlab(drv).lower()}", "metric": lead,
                 "dimension": drv, "question": "What moved vs the prior week?", "width": 7 if det else 12},
            ] + ([{"type": "pareto", "title": f"Where {lab(lead).lower()} is concentrated", "metric": lead,
                   "dimension": det, "question": f"Which {dlab(det).lower()} values carry most of the total?",
                   "width": 5}] if det else [])},
            {"label": "Detail", "question": "The numbers behind the scorecard, ready to export.", "tiles": [
                {"type": "pnl_table", "title": f"KPIs by {dlab(dim).lower()}: this week vs last", "metrics": kpis,
                 "dimension": dim, "question": "Each KPI by area, shaded better or worse than the prior week.",
                 "width": 12},
                {"type": "detail_table", "title": f"{dlab(dim)} × {dlab(drv).lower()} detail",
                 "dimensions": [d for d in dict.fromkeys([dim, drv]) if d], "metrics": kpis, "width": 12},
            ]},
        ]}
    pace = one("pace_metric")
    tiles = [
        {"type": "status_tiles", "title": "Right now vs same time last week", "metrics": s["status_kpis"],
         "question": "Are we on track today?", "width": 12},
        {"type": "pace_chart", "title": f"Today's pace: {lab(pace).lower()}", "metric": pace,
         "question": "Running total by hour vs the same weekday last week.", "width": 7 if ctx.hour_dim(pace) else 12},
    ]
    if ctx.hour_dim(pace):
        tiles.append({"type": "hour_heatmap", "title": f"{lab(pace)} by hour, last 7 days", "metric": pace,
                      "question": "When are the peaks?", "width": 5})
    tiles.append({"type": "worklist", "title": "Worklist: act now", "metrics": s["worklist_kpis"],
                  "dimensions": s["worklist_dimensions"],
                  "question": "What is off today compared with a normal day, worst first?", "width": 12})
    return {"pages": [{"label": "Live", "question": META[persona]["question"], "tiles": tiles}]}


def focus_tile(ctx: DataContext, focus: dict, goal: str, s: dict[str, list[str]]) -> Optional[dict[str, Any]]:
    """The question asked, answered first: metric by breakdown (ranked bars, or share when it asks about mix),
    or the metric over time when no breakdown is named."""
    m, d = (focus or {}).get("metric"), (focus or {}).get("dimension")
    if not m and d:
        m = next(iter(s.get("headline_kpis") or s.get("scorecard_kpis") or s.get("status_kpis") or []), None)
    if not m:
        return None
    lab = ctx.model.field(m, ("metric",)).label
    g = (goal or "").strip()
    # the subtitle is a question, never the person's instruction ("Show executives ... "): their own wording only
    # when it already is a short question, otherwise a plain one built from what the tile shows
    own = g if g.endswith("?") and len(g) <= 110 else ""
    q = own or (f"How is {lab} moving?" if not d else "")
    if d and ctx.allowed(m, d):
        dl = ctx.model.field(d, ("dimension",)).label
        share = re.search(r"\bshare|\bmix|split|breakdown of", goal or "", re.I) and ctx.distinct.get(d, 99) <= 10
        q = own or (f"What makes up {lab} by {dl.lower()}?" if share else f"Which {dl.lower()} lead on {lab}?")
        return {"type": "share_donut" if share else "ranked_bar", "title": f"{lab} by {dl.lower()}",
                "metric": m, "dimension": d, "question": q, "width": 12 if not share else 6, "focus": True}
    if re.search(r"trend|over time|month|week|daily|growth", goal or "", re.I):
        return {"type": "trend_chart", "title": f"{lab} over time", "metric": m, "question": q, "width": 12,
                "focus": True}
    return None


def variant_skeleton(ctx: DataContext, persona: str, s: dict[str, list[str]], variant: str,
                     focus: dict) -> dict[str, Any]:
    lab = lambda m: ctx.model.field(m, ("metric",)).label
    dlab = lambda d: ctx.model.field(d, ("dimension",)).label if d else "breakdown"
    one = lambda k: (s.get(k) or [None])[0]
    if persona == "executives" and variant == "growth_mix":
        lead = one("trajectory_metric") or (s.get("headline_kpis") or [None])[0]
        mix, drv = one("mix_dimension") or one("driver_dimension"), one("driver_dimension")
        rate = next((m for m in [*(s.get("headline_kpis") or []), *[x.id for x in _metrics(ctx)]]
                     if m != lead and ctx.allowed(m, ctx.bindings.time_dimension)
                     and fmt_kind(ctx.model.field(m, ("metric",)).name) == "percent"), None)
        return {"pages": [{"label": "Growth & mix", "question": "Where is growth coming from, and is the mix shifting?",
                           "tiles": [
            {"type": "kpi_grid", "title": "Headline vs last year", "metrics": s["headline_kpis"], "width": 12,
             "question": "How are the headline metrics moving against last year?"},
            ({"type": "combo_chart", "title": f"{lab(lead)} and {lab(rate).lower()}", "metric": lead, "metric2": rate,
              "width": 7, "question": "Is growth coming with better or worse rates?"} if rate else
             {"type": "trend_chart", "title": f"{lab(lead)} trend", "metric": lead, "width": 7,
              "question": "Is growth accelerating or slowing?"}),
            {"type": "treemap", "title": f"{lab(lead)} mix by {dlab(mix).lower()}", "metric": lead,
             "dimension": mix, "width": 5, "question": "Which segments make up the total, and which moved?"},
            {"type": "period_compare", "title": f"{lab(lead)} by {dlab(drv).lower()}: now vs before", "metric": lead,
             "dimension": drv, "width": 6, "question": "Which segments grew and which declined?"},
            {"type": "ranked_bar", "title": f"Top {dlab(drv).lower()} by {lab(lead).lower()}", "metric": lead,
             "dimension": drv, "width": 6, "question": "Which segments lead?"},
        ]}]}
    if persona == "executives" and variant == "question":
        m = (focus or {}).get("metric") or one("trajectory_metric") or (s.get("headline_kpis") or [None])[0]
        asked_d = (focus or {}).get("dimension")
        asked_d = asked_d if asked_d and ctx.allowed(m, asked_d) else None    # same check as every other layout
        d = asked_d or one("driver_dimension")
        return {"pages": [{"label": "Answer", "question": "The question asked, then the context around it.", "tiles": [
            {"type": "ranked_bar", "title": f"{lab(m)} by {dlab(d).lower()}", "metric": m, "dimension": d,
             "width": 12, "question": "The answer to the question asked." if asked_d else "The main breakdown.",
             "focus": bool(asked_d)},
            {"type": "kpi_grid", "title": "Headline KPIs", "metrics": s["headline_kpis"], "width": 12,
             "question": "The context: how the headline metrics stand."},
            {"type": "trend_chart", "title": f"{lab(m)} over time", "metric": m, "width": 7,
             "question": "Is this new or a trend?"},
            {"type": "driver_bridge", "title": f"What moved {lab(m).lower()}, by {dlab(d).lower()}", "metric": m,
             "dimension": d, "width": 5, "question": "Which values explain the change vs the prior period?"},
        ]}]}
    if persona == "managers" and variant == "exceptions":
        kpis = s["scorecard_kpis"]
        lead, exc, det, dim = kpis[0], one("exception_dimension"), one("detail_dimension"), one("scorecard_dimension")
        return {"pages": [
            {"label": "Exceptions", "question": "What is outside its normal range, and where?", "tiles": [
                {"type": "exception_table", "title": f"{lab(lead)}: unusual {dlab(exc).lower()} values", "metric": lead,
                 "dimension": exc, "width": 7, "question": "Which values are outside their normal range this week?"},
                {"type": "pareto", "title": f"Where {lab(lead).lower()} is concentrated", "metric": lead,
                 "dimension": det or exc, "width": 5, "question": "Is the problem concentrated in a few places?"},
                {"type": "small_multiples", "title": f"{lab(lead)} trend by {dlab(dim).lower()}", "metric": lead,
                 "dimension": dim, "width": 12, "question": "Is it new or persistent?"},
            ]},
            {"label": "Detail", "question": "The numbers behind the exceptions.", "tiles": [
                {"type": "detail_table", "title": f"{dlab(dim)} × {dlab(exc).lower()} detail",
                 "dimensions": [x for x in dict.fromkeys([dim, exc]) if x], "metrics": kpis, "width": 12},
            ]},
        ]}
    if persona == "managers" and variant == "compare":
        kpis = s["scorecard_kpis"]
        lead, m2 = kpis[0], (kpis[1] if len(kpis) > 1 else kpis[0])
        dim, drv, det = one("scorecard_dimension"), one("driver_dimension"), one("detail_dimension")
        return {"pages": [
            {"label": "Compare", "question": "How do the areas compare, and who is ahead?", "tiles": [
                {"type": "ranked_bar", "title": f"{lab(lead)} by {dlab(dim).lower()}", "metric": lead, "dimension": dim,
                 "width": 6, "question": "Who leads and who trails?"},
                {"type": "period_compare", "title": f"{dlab(dim)}: this week vs last week vs last year", "metric": lead,
                 "dimension": dim, "width": 6, "question": "Who improved and who slipped?"},
                {"type": "heatmap", "title": f"{lab(lead)}: {dlab(dim).lower()} × {dlab(drv).lower()}", "metric": lead,
                 "dimension": dim, "dimension2": drv, "width": 12, "question": "Where exactly is each area strong or weak?"},
                {"type": "scatter", "title": f"{lab(lead)} vs {lab(m2).lower()} by {dlab(det or drv).lower()}",
                 "metric": lead, "metric2": m2, "dimension": det or drv, "width": 12,
                 "question": "Do the two metrics move together, and which values stand out?"},
            ]},
            {"label": "Detail", "question": "The numbers behind the comparison.", "tiles": [
                {"type": "pnl_table", "title": f"KPIs by {dlab(dim).lower()}: this week vs last", "metrics": kpis,
                 "dimension": dim, "question": "Each KPI by area, shaded better or worse than the prior week.",
                 "width": 12},
                {"type": "detail_table", "title": f"{dlab(dim)} detail", "dimensions": [dim], "metrics": kpis,
                 "width": 12},
            ]},
        ]}
    if persona == "daily_operations" and variant == "daily":
        pace = one("pace_metric")
        tiles = [
            {"type": "status_tiles", "title": "Today vs same time last week", "metrics": s["status_kpis"], "width": 12,
             "question": "Are we on track today?"},
            {"type": "trend_chart", "title": f"{lab(pace)} by day", "metric": pace, "width": 7,
             "question": "How have the last days gone?"},
            {"type": "exception_table", "title": f"Unusual {dlab(one('worklist_dimensions')).lower()} values",
             "metric": pace, "dimension": one("worklist_dimensions"), "width": 5,
             "question": "Which values are off compared with a normal day?"},
            {"type": "worklist", "title": "Worklist: act now", "metrics": s["worklist_kpis"],
             "dimensions": s["worklist_dimensions"], "width": 12,
             "question": "What is off today compared with a normal day, worst first?"},
        ]
        return {"pages": [{"label": "Daily", "question": "How have the last days gone, and what needs fixing?",
                           "tiles": tiles}]}
    return skeleton(ctx, persona, s)


def build_layout(ctx: DataContext, persona: str, chosen: dict, variant: str, focus: dict, goal: str,
                 gov: Optional[Governance] = None) -> list[dict[str, Any]]:
    raw = variant_skeleton(ctx, persona, chosen, variant, focus)
    lead = focus_tile(ctx, focus, goal, chosen) if variant != "question" else None
    if lead and lead["type"] == "trend_chart":              # the layout already has a trend chart: no second one on top
        same = next((t for t in raw["pages"][0]["tiles"] if t.get("type") == "trend_chart"), None)
        if same:
            if same.get("metric") == lead["metric"]:
                same["focus"] = True                        # it answers the question asked: tag it
            lead = None
    if lead and raw["pages"]:
        raw["pages"][0]["tiles"] = [lead] + raw["pages"][0]["tiles"]
    first = raw["pages"][0]["tiles"][0] if variant == "question" and raw["pages"] and raw["pages"][0]["tiles"] else {}
    asked = (lead or (first if first.get("focus") else {})).get("title")     # tagged only when the person asked it
    pages = validate_layout(ctx, raw, gov or Governance())
    for p in pages:
        for c in p["components"]:
            c["origin"] = "persona"
    if asked and pages:                                    # the tile that answers the question asked
        hit = next((c for c in pages[0]["components"] if c.get("title") == asked), None)
        if hit:
            hit["focus"] = True
    return pages


def layout_options(ctx: DataContext, persona: str, chosen: dict, focus: dict, goal: str) -> list[dict[str, Any]]:
    """Every layout of this audience, filled with the same slots: for the switcher's thumbnails."""
    out = []
    for v in VARIANTS[persona]:
        try:
            pages = build_layout(ctx, persona, chosen, v["id"], focus, goal)
        except Exception:
            continue
        if not pages:
            continue
        out.append({"id": v["id"], "title": v["title"], "summary": v["summary"], "pages": len(pages),
                    "tiles": [{"type": c["type"], "span": c.get("span") or c.get("width") or 6,
                               "n": len(c.get("metrics") or [])}
                              for c in pages[0]["components"]][:8]})
    return out


def has_plan(ctx: DataContext, chosen: dict) -> bool:
    """True when at least one headline metric has a PLAN_<metric> target in the semantic view."""
    names = {m.name.upper() for m in ctx.model.metrics}
    for k in ("headline_kpis", "scorecard_kpis", "status_kpis", "trajectory_metric"):
        for mid in chosen.get(k) or []:
            n = ctx.model.field(mid, ("metric",)).name.upper()
            if any(c in names for c in (f"PLAN_{n}", "PLAN_" + n.replace("_SOLD", ""), "PLAN_" + n.split("_")[0])):
                return True
    return False


_PLAN_WORDS = ((r"\bvs\.? plan\b", "vs last year"), (r"\bagainst plan\b", "against last year"),
               (r"\bon plan\b", "on track"), (r"\boff plan\b", "off track"), (r"\bplan or\b", "last year or"))


def without_plan(text: str) -> str:
    """No plan targets in this semantic view: never promise a plan comparison the tiles do not make."""
    for rx, rep_ in _PLAN_WORDS:
        text = re.sub(rx, rep_, text or "", flags=re.I)
    return re.sub(r"\byear to date against last year\b", "year to date against last year", text, flags=re.I)


def _t(text: str, plan_ok: bool) -> str:
    return text if plan_ok else without_plan(text)


def compose_persona(cortex, ctx: DataContext, goal: str, variant: Optional[str] = None,
                    reuse: Optional[dict[str, Any]] = None, asked: str = "") -> dict[str, Any]:
    """Reviewed layout for the audience. `reuse` (a previous spec) switches layout without a new Cortex call.
    `asked` = the person's own words (the goal may be a rewritten version): layout rules and the question tile
    follow what the person asked, never a rewrite."""
    asked = (asked or "").strip()
    persona = ctx.audience
    if persona not in PERSONAS:
        raise ValueError(f"No persona skeleton for {persona}")
    gov = Governance()
    if reuse:
        chosen, focus = reuse["slots"], reuse.get("focus") or {}
        asked = asked or reuse.get("asked") or ""
        info = {"origin": reuse.get("slot_origin", "defaults"), "title": None, "summary": None,
                "provenance": "slots kept from the first draft"}
    else:
        chosen, info, notes = fill_slots(cortex, ctx, persona, goal, asked)
        gov.entries.extend(notes)
        tf = text_focus(ctx, asked or goal)
        focus = {k: (info.get("focus") or {}).get(k) or tf.get(k) for k in ("metric", "dimension")}
    if variant not in variant_ids(persona):
        variant = info.get("layout") or rule_variant(persona, asked or goal)
        if variant == "question" and not focus.get("dimension"):
            variant = variant_ids(persona)[0]          # nothing specific asked: the default layout
    pages = build_layout(ctx, persona, chosen, variant, focus, asked or goal, gov)
    if not pages:
        raise ValueError("No tile of the persona layout is valid for this semantic view.")
    vmeta = next(v for v in VARIANTS[persona] if v["id"] == variant)
    plan_ok = has_plan(ctx, chosen)
    digest = hashlib.sha1(json.dumps(pages, sort_keys=True).encode()).hexdigest()[:8]
    by_cortex = info["origin"] == "cortex"
    default = variant == variant_ids(persona)[0]
    return {
        "template_id": f"persona-{persona}-{variant}-{digest}", "template_version": 1, "origin": "persona",
        "persona": persona, "audience_id": persona, "layout_variant": variant,
        "display_name": _t(((info.get("title") if not reuse else None) or (META[persona]["title"] if default
                                                                           else vmeta["title"]))[:90], plan_ok),
        "description": _t((info.get("summary") if not reuse else None) or vmeta["summary"], plan_ok), "goal": goal[:400],
        "slots": chosen, "slot_origin": info["origin"], "focus": focus,
        "layout_options": [{**o, "title": _t(o["title"], plan_ok), "summary": _t(o["summary"], plan_ok)}
                           for o in layout_options(ctx, persona, chosen, focus, asked or goal)], "asked": asked,
        "provenance": (f"Reviewed {persona.replace('_', ' ')} layout '{vmeta['title']}' · slots filled by Cortex "
                       f"AI_COMPLETE ({info.get('provenance', '')})" if by_cortex
                       else f"Reviewed {persona.replace('_', ' ')} layout '{vmeta['title']}' · default slots"),
        "pages": pages, "governance": gov.entries,
    }
