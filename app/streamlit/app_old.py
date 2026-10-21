"""Analytics Accelerator — Enterprise edition (Streamlit in Snowflake, container runtime).

A React workspace (Components v2) renders governed, audience-specific layouts from
a reviewed catalog. Python owns every Snowflake call: semantic-view discovery,
governed SEMANTIC_VIEW queries, Cortex AI_COMPLETE, Snowflake ML FORECAST /
TOP_INSIGHTS, Cortex Agents, and the decision/dashboard/AI-run tables.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import re
import time
import traceback
from pathlib import Path

import streamlit as st

import config
from agent_service import ask_agent, create_agent, find_agents, is_missing_warehouse
from ai_services import Cortex
from composer import (TILES, DataContext, apply_review, compose, compose_new_page, compose_page, compose_tile,
                      edit_tile_nl, manual_tile, metric_cards, normalise_template_spec, revalidate_tile)
from engine import Engine
import home
from inventory import SOURCE_BASELINE, Bindings, build_profile, infer_bindings, validate_bindings
from layout_catalog import (AUDIENCES, bind_template, get_template, picker_options, select_template,
                            validate_cortex_output)
from semantic_catalog import describe_semantic_view, list_semantic_views, metric_dimension_map, row_dict
from semantic_query import SemanticQuery, distinct_values
from store import Store

HERE = Path(__file__).parent
st.set_page_config(page_title=config.APP_TITLE, layout="wide", initial_sidebar_state="collapsed")
st.markdown("<style>.block-container{padding:0.5rem 0.75rem 0 0.75rem!important;max-width:100%!important}"
            "header[data-testid='stHeader']{display:none}"
            # Streamlit greys out ("stale") elements while a rerun is in flight; the React UI shows its own
            # progress indicator, so keep the dashboard fully visible instead of flashing dull/blank.
            ""
            "[data-testid='stStatusWidget']{visibility:hidden}</style>", unsafe_allow_html=True)


def get_session():
    if os.environ.get("AA_FAKE_SNOWFLAKE") == "1":           # local testing only
        import sys
        sys.path.insert(0, str(HERE.parent / "tests"))
        from fake_snowflake import FakeSession
        if "_fake" not in st.session_state:
            st.session_state._fake = FakeSession()
        return st.session_state._fake
    from snowflake.snowpark.context import get_active_session
    return get_active_session()


session = get_session()
S = st.session_state.setdefault("aa_state", {
    "step": "home", "revision": 0, "viewer": "", "suggestions": [], "suggestions_by": "", "suggestions_at": "", "building": None,
    "role": "", "revision_home": 0, "last_request": None, "error": "", "notice": "",
    "features": None, "sources": [], "dashboards": [], "source": None, "model": None,
    "bindings": None, "binding_errors": [], "binding_suggestion": None, "audience": "executives",
    "profile": None, "options": [], "recommendation": None, "spec": None, "results": {},
    "narratives": {}, "agents": [], "agent": None, "chat": [], "thread": None, "decisions": [],
    "dashboard": None, "quality": None, "sql_log": [], "cache": {},
})
for _k, _v in {"view": {"grain": None, "compare": "prior", "filters": {}}, "filter_dims": [],
               "filter_options": {}, "draft": None, "tile_chat": {}, "viewer_mode": False, "published": [],
               "roles": [], "share": None, "featured": []}.items():
    S.setdefault(_k, _v)
store = Store(session, config.APP_SCHEMA)
APP_FQN = f"{config.APP_SCHEMA}.ANALYTICS_ACCELERATOR_ENTERPRISE"


def cortex() -> Cortex:
    c = Cortex(session, config.APP_SCHEMA, config.MODELS, S["sql_log"])
    if S["features"]:
        c.model_in_use = S["features"].get("model")
        c.features = S["features"]
    return c


def model_obj():
    """Semantic view metadata, described once per session."""
    if not S["source"]:
        return None
    models = st.session_state.setdefault("_models", {})
    fqn = S["source"]["fqn"]
    if fqn not in models or not hasattr(models[fqn], "metric_dims"):
        m = models.get(fqn) or describe_semantic_view(session, fqn)
        m.metric_dims = metric_dimension_map(session, m)   # valid metric x dimension pairs
        models[fqn] = m
    return models[fqn]


def profile_for(m, b: Bindings, audience: str):
    """Capability profile, computed once per (view, bindings, audience)."""
    cache = st.session_state.setdefault("_profiles", {})
    grain = (S.get("view") or {}).get("grain")
    key = (m.fqn, json.dumps(b.as_dict(), sort_keys=True), audience, grain)
    if key not in cache:
        cache[key] = build_profile(session, m, b, audience, S["features"] or {}, log=S["sql_log"], grain=grain)
    return cache[key]


def distinct_for(m) -> dict[str, int]:
    """Cardinality of every categorical dimension (one UNION query per source, cached)."""
    cache = st.session_state.setdefault("_distinct", {})
    if m.fqn not in cache:
        dims = [d.id for d in m.categorical_dimensions][:30]
        try:
            cache[m.fqn] = SemanticQuery(session, m, S["sql_log"]).distinct_counts(dims)
        except Exception:
            cache[m.fqn] = {}
    return cache[m.fqn]


def data_ctx() -> DataContext:
    m, b, prof = _profile_obj()
    return DataContext(m, b, prof, {**distinct_for(m), **(prof.distinct or {})}, S["audience"])


def log_ai(feature, inp, out, prov, status, started):
    store.log_ai(feature, S["source"]["fqn"] if S["source"] else "", inp, out, prov, status,
                 time.time() - started)


# --------------------------------------------------------------------------------------- actions
def viewer_name() -> str:
    """First name of the signed-in viewer (never the app's service user)."""
    cands = []
    try:
        u = st.user
        cands += [u.get("user_name"), u.get("name"), u.get("email")]
    except Exception:
        pass
    try:
        cands.append(session.sql("SELECT CURRENT_USER() AS U").collect()[0][0])
    except Exception:
        pass
    for c in cands:
        c = str(c or "")
        if not c or re.search(r"STREAMLIT|STPLAT|SERVICE|SYSTEM", c, re.I):
            continue
        first = re.split(r"[.@_\s]", c)[0]
        if first.isalpha() and 2 <= len(first) <= 20:
            return first.capitalize()
    return ""


def boot():
    S["viewer"] = viewer_name()
    try:
        S["role"] = str(session.sql("SELECT CURRENT_ROLE() AS R").collect()[0][0])
    except Exception:
        S["role"] = ""
    S["features"] = cortex().detect_features()
    S["sources"] = list_semantic_views(session, config.DISCOVERY_SCHEMAS)
    store.ensure()
    S["dashboards"] = store.list_dashboards()
    S["published"] = store.list_published()
    try:
        wanted = st.query_params.get("view")
    except Exception:
        wanted = None
    if wanted:
        open_published({"dashboard_id": wanted})


def _describe_cached(fqn):
    models = st.session_state.setdefault("_models", {})
    if fqn not in models:
        models[fqn] = describe_semantic_view(session, fqn)
    return models[fqn]


def catalog():
    if "_catalog" not in st.session_state:
        hit = home.cache_get(S["role"])
        st.session_state["_catalog"] = hit["catalog"] if hit and hit.get("catalog") is not None else \
            home.build_catalog(S["sources"], _describe_cached,
                               {f: config.FEATURED_LABELS.get(f, "") for f in config.FEATURED_VIEWS})
        home.cache_put(S["role"], catalog=st.session_state["_catalog"])
    return st.session_state["_catalog"]


def home_suggestions(_p=None):
    """Phase 1: saved Cortex ideas if the data hasn't changed; otherwise instant ideas from the catalog."""
    hit = home.cache_get(S["role"])
    cat = catalog()
    S["catalog_size"] = len(cat)
    S["featured"] = [{"fqn": c["fqn"], "label": c["label"], "metrics": len(c["metrics"]),
                      "dimensions": len(c["dimensions"])} for c in cat if c.get("featured")]
    if hit and hit.get("suggestions"):
        S["suggestions"], S["suggestions_by"], S["suggestions_at"] = hit["suggestions"], "cortex", hit.get("ideas_at", "")
        return
    try:
        saved = store.load_ideas(S["role"])
    except Exception:
        saved = None
    if saved and saved.get("ideas") and saved.get("catalog_sig") == home.catalog_signature(cat):
        S["suggestions"], S["suggestions_by"], S["suggestions_at"] = saved["ideas"], "cortex", saved.get("created_at", "")
        home.cache_put(S["role"], suggestions=saved["ideas"], ideas_at=S["suggestions_at"])
        return
    S["suggestions"], S["suggestions_by"] = home.fallback_suggestions(cat), "catalog"


def home_suggestions_ai(p=None):
    """Phase 2: Cortex proposes executive / manager / operations dashboards; saved until the user asks again."""
    if not (S["features"] or {}).get("complete"):
        S["suggestions_by"] = "catalog-final"
        return
    started = time.time()
    try:
        sug = home.ai_suggestions(cortex(), catalog())
        S["suggestions"], S["suggestions_by"] = sug, "cortex"
        S["suggestions_at"] = time.strftime("%Y-%m-%d %H:%M")
        home.cache_put(S["role"], suggestions=sug, ideas_at=S["suggestions_at"])
        try:
            store.save_ideas(S["role"], home.catalog_signature(catalog()), sug, S["role"])
        except Exception:
            pass
        store.log_ai("home_suggestions", "", f"{len(catalog())} views", json.dumps(sug)[:4000],
                       "Cortex AI_COMPLETE", "valid", time.time() - started)
    except Exception as exc:
        if not (p or {}).get("fresh"):
            S["suggestions_by"] = "catalog-final"
        store.log_ai("home_suggestions", "", "", str(exc)[:400], "Cortex AI_COMPLETE", "fallback",
                       time.time() - started)
        if (p or {}).get("fresh"):
            raise ValueError("Cortex couldn't suggest new ideas right now; your current ideas are kept.")


def route_prompt(p):
    """Typed request or suggestion card -> dataset, metrics, audience. Designing happens next (compose)."""
    started = time.time()
    sug = p.get("suggestion") or None
    prompt = str((sug or {}).get("goal") or p.get("prompt") or "").strip()[:500]
    if not prompt:
        raise ValueError("Tell me what you want to see, or pick one of the ideas.")
    cat = catalog()
    if sug and sug.get("semantic_view") in {c["fqn"] for c in cat}:
        r = {"semantic_view": sug["semantic_view"], "audience": sug.get("audience") or "executives",
             "goal": prompt, "primary_metric": " ".join(sug.get("metrics") or [])[:80],
             "reason": "Suggested idea", "by": sug.get("by") or "catalog"}
    else:
        r = home.route(cortex(), cat, prompt)
        log_ai_raw("prompt_routing", prompt, json.dumps(r), r.get("by", ""), "valid", started)
    if p.get("audience") in home.AUDIENCES:
        r["audience"] = p["audience"]
    if not r.get("semantic_view"):
        raise ValueError("I couldn't find governed data for that request.")
    select_source({"fqn": r["semantic_view"]})
    m = model_obj()
    b = Bindings.from_dict(S["bindings"])
    primary = home.pick_primary(m, r.get("primary_metric", ""), prompt)
    if primary and primary != b.primary_metric:
        b.supporting_metrics = [x for x in [b.primary_metric] + b.supporting_metrics if x != primary]
        b.primary_metric = primary
    # the designer sees every metric; the focus list stays short so headline queries stay fast
    b.source = "prompt"
    errors = validate_bindings(m, b)
    if errors:
        raise ValueError("This data can't drive a dashboard yet: " + " ".join(errors))
    S["bindings"], S["binding_errors"] = b.as_dict(), []
    S["view"] = {"grain": None, "compare": AUDIENCE_COMPARE.get(r["audience"], "prior"), "filters": {}}
    set_audience({"audience": r["audience"]})
    view = next((c for c in cat if c["fqn"] == r["semantic_view"]), {})
    S["building"] = {"goal": r["goal"], "prompt": prompt, "audience": r["audience"], "domain": view.get("label", ""),
                     "reason": r.get("reason", ""), "by": r.get("by", ""), "metrics": len(m.metrics),
                     "dimensions": len(m.categorical_dimensions)}
    S["step"] = "home"


def log_ai_raw(feature, inp, out, prov, status, started):
    store.log_ai(feature, "", inp, out, prov, status, time.time() - started)


def select_source(p):
    fqn = str(p.get("fqn", "")).upper()
    if fqn not in {s.get("fqn") for s in S["sources"]}:
        raise ValueError("Choose one of the discovered semantic views.")
    S["source"] = next(s for s in S["sources"] if s.get("fqn") == fqn)
    m = model_obj()
    S["model"] = m.summary()
    S["bindings"] = infer_bindings(m).as_dict()
    S["binding_errors"] = validate_bindings(m, Bindings.from_dict(S["bindings"]))
    S["binding_suggestion"] = None
    S["agents"] = find_agents(session, fqn, config.AGENT_SCHEMAS)
    S["agent"] = S["agents"][0] if S["agents"] else None
    S.update(step="metrics", spec=None, results={}, narratives={}, chat=[], thread=None, profile=None,
             dashboard=None)
    S["decisions"] = store.list_decisions(fqn)


def suggest_bindings(p):
    started = time.time()
    m = model_obj()
    raw = cortex().suggest_bindings(S["model"], str(p.get("intent", ""))[:300])
    candidate = Bindings.from_dict({**S["bindings"], **{k: raw.get(k) for k in (
        "primary_metric", "time_dimension", "segment_dimension", "region_dimension") if raw.get(k) is not None},
        "supporting_metrics": raw.get("supporting_metrics") or []})
    metric_ids = {x.id for x in m.metrics}
    candidate.supporting_metrics = [x for x in candidate.supporting_metrics if x in metric_ids]
    errors = validate_bindings(m, candidate)
    rejected = [x for x in (raw.get("supporting_metrics") or []) if x not in metric_ids]
    S["binding_suggestion"] = {"bindings": candidate.as_dict(), "errors": errors, "reason": raw.get("reason", ""),
                               "rejected": rejected, "provenance": raw.get("provenance")}
    log_ai("field_mapping", p.get("intent", ""), json.dumps(raw), raw.get("provenance", ""),
           "valid" if not errors else "rejected", started)


def set_bindings(p):
    m = model_obj()
    b = Bindings.from_dict({**S["bindings"], **(p.get("bindings") or {})})
    b.source = str(p.get("source") or "user")
    errors = validate_bindings(m, b)
    S["bindings"], S["binding_errors"] = b.as_dict(), errors
    if not errors and p.get("advance"):
        set_audience({"audience": S["audience"]})


def set_audience(p):
    audience = p.get("audience")
    if audience not in AUDIENCES:
        raise ValueError("audience")
    S["audience"] = audience
    m = model_obj()
    b = Bindings.from_dict(S["bindings"])
    prof = profile_for(m, b, audience)
    S["profile"] = prof.as_dict()
    options = picker_options(audience, prof.inventory())
    for o in options:
        o["description"] = get_template(o["template_id"]).description
    S["options"] = options
    S["recommendation"] = None
    S["step"] = "layout"


def _profile_obj():
    m = model_obj()
    b = Bindings.from_dict(S["bindings"])
    return m, b, profile_for(m, b, S["audience"])


def recommend_layout(p):
    started = time.time()
    m, b, prof = _profile_obj()
    intent = str(p.get("intent", ""))[:400]
    raw = cortex().recommend_layout(S["audience"], intent, S["options"])
    sel = validate_cortex_output(S["audience"], prof.inventory(), raw)
    S["recommendation"] = {
        "suggested": raw.get("template_id"), "reason": raw.get("reason"), "provenance": raw.get("provenance"),
        "validated_template": sel.template.template_id if sel.template else None,
        "selected_by": sel.selected_by, "message": sel.message, "rejected": sel.rejected_cortex_suggestion}
    log_ai("layout_recommendation", intent, json.dumps(raw), raw.get("provenance", ""), sel.selected_by, started)


def select_layout(p):
    m, b, prof = _profile_obj()
    sel = select_template(S["audience"], prof.inventory(), user_selected_template_id=p.get("template_id"))
    if sel.status != "ready":
        raise ValueError(sel.message)
    spec = normalise_template_spec(bind_template(sel.template, prof.inventory()))
    spec["description"] = sel.template.description
    if prof.roles.get("target") == SOURCE_BASELINE:
        # Honest labelling: this account has no versioned plan; "target" is the prior-year baseline.
        def unplan(text):
            return re.sub(r"\bplan\b", "prior-year baseline", text, flags=re.I)
        for page in spec["pages"]:
            page["purpose"] = unplan(page["purpose"])
            page["label"] = unplan(page["label"])
            for comp in page["components"]:
                comp["title"] = unplan(comp["title"])
    apply_spec(spec)


def apply_spec(spec):
    """Phase 1: governed queries only (fast). Snowflake ML runs in phase 2 ("enrich")."""
    m, b, prof = _profile_obj()
    results, facts = Engine(session, m, b, prof, cortex(), store, S["cache"], S["sql_log"],
                            defer_ml=True, opts=S["view"]).build(spec)
    S.update(spec=spec, results=results, facts=facts, narratives={}, step="workspace",
             profile=prof.as_dict())
    S["focus_page"] = None
    S["decisions"] = store.list_decisions(m.fqn)
    setup_filters()


def rebuild_pages(page_ids):
    m, b, prof = _profile_obj()
    pages = [p for p in S["spec"]["pages"] if p["page_id"] in page_ids]
    results, facts = Engine(session, m, b, prof, cortex(), store, S["cache"], S["sql_log"],
                            defer_ml=True, opts=S["view"]).build({"pages": pages})
    for pid in page_ids:
        for k in [k for k in S["results"] if k.startswith(pid + "/")]:
            del S["results"][k]
        S["narratives"].pop(pid, None)
    S["results"].update(results)
    S.setdefault("facts", {}).update(facts)


def compose_layout(p):
    """Cortex designs the layout from the data profile + goal; the validator keeps it governed."""
    started = time.time()
    goal = str(p.get("goal", ""))[:400]
    seed = None
    ctx = data_ctx()
    seed_id = p.get("seed_template_id")
    if seed_id:
        sel = select_template(S["audience"], ctx.profile.inventory(), user_selected_template_id=seed_id)
        if sel.status == "ready":
            seed = bind_template(sel.template, ctx.profile.inventory())
    try:
        spec = compose(cortex(), ctx, goal, seed)
        log_ai("layout_compose", goal, json.dumps({"pages": spec["pages"], "governance": spec["governance"]})[:4000],
               spec["provenance"], "valid", started)
        kept = sum(1 for e in spec["governance"] if e["action"] != "dropped" and e["tile"] != "(page)")
        fixed = sum(1 for e in spec["governance"] if e["action"] == "repaired")
        dropped = sum(1 for e in spec["governance"] if e["action"] == "dropped")
        S["notice"] = (f"Cortex drafted {len(spec['pages'])} pages / {kept} tiles; the validator repaired {fixed} "
                       f"and dropped {dropped}. Review the metrics and outline, then build.")
    except Exception as exc:
        log_ai("layout_compose", goal, str(exc), "Cortex AI_COMPLETE", "fallback", started)
        sel = select_template(S["audience"], ctx.profile.inventory(), user_selected_template_id=seed_id)
        if sel.status != "ready":
            raise ValueError(f"Cortex could not design a layout ({exc}) and no catalog template is ready.")
        spec = normalise_template_spec(bind_template(sel.template, ctx.profile.inventory()))
        spec["description"] = sel.template.description
        spec["origin"] = "catalog-fallback"
        spec["governance"] = [{"page": "-", "tile": "(layout)", "action": "fallback",
                               "reason": f"Cortex design failed ({str(exc)[:200]}); used reviewed template "
                                         f"{sel.template.template_id}."}]
        S["notice"] = f"Cortex was unavailable, so the reviewed template '{sel.template.display_name}' was used."
    spec["goal"] = goal
    S["building"] = None
    S["draft"] = {"spec": spec, "cards": metric_cards(ctx, spec), "goal": goal}
    S["step"] = "review"


# ------------------------------------------------------------------------------ review, view settings, filters
def build_draft(p):
    """User approved the review: chosen metrics + edited outline -> build the dashboard."""
    if not S["draft"]:
        raise ValueError("Nothing to build - design a dashboard first.")
    spec, _gov = apply_review(data_ctx(), S["draft"]["spec"], p.get("metrics") or [], p.get("outline") or [])
    S["draft"] = None
    apply_spec(spec)
    S["notice"] = f"Built {len(spec['pages'])} pages from your review."


def redraft(p):
    """Ask Cortex for a fresh design focused on the metrics the user picked."""
    m = model_obj()
    labels = [m.field(x, ("metric",)).label for x in (p.get("metrics") or []) if x in {y.id for y in m.metrics}]
    goal = (S["draft"] or {}).get("goal") or ""
    compose_layout({"goal": goal + (" Focus on these metrics: " + ", ".join(labels) if labels else "")})


AUDIENCE_COMPARE = {"executives": "yoy", "managers": "prior", "weekly_business_review": "prior",
                    "daily_operations": "prior"}


def setup_filters():
    """Global filter choices: region, main breakdown, and a channel-like dimension if the view has one."""
    m = model_obj()
    b = Bindings.from_dict(S["bindings"])
    dims = [d for d in (b.region_dimension, b.segment_dimension) if d]
    dims += [d.id for d in m.categorical_dimensions if re.search(r"CHANNEL", d.name, re.I)]
    dims = list(dict.fromkeys(dims))[:3]
    cache = st.session_state.setdefault("_fvals", {})
    opts = {}
    for d in dims:
        key = (m.fqn, d)
        if key not in cache:
            try:
                cache[key] = distinct_values(SemanticQuery(session, m, S["sql_log"]), d)
            except Exception:
                cache[key] = []
        if cache[key]:
            opts[d] = cache[key]
    S["filter_dims"] = [{"id": d, "label": m.field(d, ("dimension",)).label} for d in opts]
    S["filter_options"] = opts
    S["view"]["filters"] = {k: v for k, v in (S["view"].get("filters") or {}).items() if k in opts}


def set_view(p):
    """Time bar and filters: period grain, compare-to, filter values. Rebuilds every page."""
    v = dict(S["view"])
    if "grain" in p:
        v["grain"] = p["grain"] if p["grain"] in ("day", "week", "month", "quarter") else None
    if "compare" in p and p["compare"] in ("prior", "yoy", "plan"):
        v["compare"] = p["compare"]
    if "filters" in p:
        clean = {}
        for dim, vals in (p.get("filters") or {}).items():
            allowed = set(S["filter_options"].get(dim) or [])
            keep = [x for x in (vals or []) if x in allowed]     # only values read from the semantic view
            if keep:
                clean[dim] = keep
        v["filters"] = clean
    S["view"] = v
    if S["spec"]:
        m, b, prof = _profile_obj()
        S["profile"] = prof.as_dict()
        apply_spec(S["spec"])


# ------------------------------------------------------------------------------ pages
def page_add(p):
    started = time.time()
    mode = p.get("mode") or "cortex"
    spec = S["spec"]
    if mode == "blank":
        n = 1 + max([int(x["page_id"][1:]) for x in spec["pages"] if x["page_id"][1:].isdigit()] or [0])
        page = {"page_id": f"p{n}", "label": str(p.get("label") or "New page")[:40],
                "purpose": str(p.get("label") or "New page")[:200], "components": []}
        spec["pages"].append(page)
        S["notice"] = "Blank page added - add tiles with the + Tile button or describe one to Cortex."
    else:
        instruction = str(p.get("instruction") or "").strip()[:300]
        out = compose_new_page(cortex(), data_ctx(), spec, instruction)
        spec["pages"].append(out["page"])
        _edited(out["governance"])
        log_ai("layout_new_page", instruction, json.dumps(out["page"])[:4000], f"Cortex AI_COMPLETE ({out['provenance']})",
               "valid", started)
        rebuild_pages([out["page"]["page_id"]])
        S["notice"] = f"Cortex added page '{out['page']['label']}'."
    S["focus_page"] = spec["pages"][-1]["page_id"]
    S["spec"]["edited"] = True


def page_rename(p):
    page, _ = _find(p.get("page_id"))
    label = str(p.get("label") or "").strip()[:40]
    if label:
        page["label"] = label
        S["spec"]["edited"] = True


def page_move(p):
    pages = S["spec"]["pages"]
    page, _ = _find(p.get("page_id"))
    i = pages.index(page)
    j = max(0, min(len(pages) - 1, i + (1 if int(p.get("dir", 1)) > 0 else -1)))
    pages[i], pages[j] = pages[j], pages[i]
    S["spec"]["edited"] = True


def page_remove(p):
    if len(S["spec"]["pages"]) <= 1:
        raise ValueError("A dashboard needs at least one page.")
    page, _ = _find(p.get("page_id"))
    S["spec"]["pages"].remove(page)
    _edited([{"page": page["label"], "tile": "(page)", "action": "removed", "reason": "Page removed by user."}])


def tile_add_manual(p):
    page, _ = _find(p.get("page_id"))
    raw = {k: p.get(k) for k in ("type", "title", "metric", "metric2", "dimension", "dimension2", "metrics", "dimensions")}
    if not raw.get("title"):
        m = model_obj()
        parts = [m.field(raw["metric"], ("metric",)).label if raw.get("metric") in {x.id for x in m.metrics} else ""]
        if raw.get("dimension") in {x.id for x in m.dimensions}:
            parts.append("by " + m.field(raw["dimension"], ("dimension",)).label)
        raw["title"] = " ".join(x for x in parts if x) or TILES.get(raw.get("type") or "", {}).get("label", "Tile")
    out = manual_tile(data_ctx(), S["spec"], page["page_id"], raw)
    page["components"].append(out["tile"])
    _edited(out["governance"])
    rebuild_pages([page["page_id"]])


# ------------------------------------------------------------------------------ per-tile AI
EDIT_WORDS = re.compile(r"^\s*(change|make|switch|convert|turn|show (it|this|me this) as|split|break|add|remove|use|"
                        r"sort|swap|resize|move|replace|group|compare|display as|plot)\b", re.I)


def tile_context(page, comp) -> str:
    m = model_obj()
    cal = (S["profile"] or {}).get("calendar") or {}
    parts = [f"Dashboard tile '{comp['title']}' ({comp['type'].replace('_', ' ')})"]
    for k, kind in (("metric_id", "metric"), ("metric2_id", "metric"), ("dimension", "dimension"), ("dimension2", "dimension")):
        if comp.get(k):
            try:
                parts.append(f"{kind}: {m.field(comp[k], (kind,)).label}")
            except Exception:
                pass
    if comp.get("metrics"):
        parts.append("metrics: " + ", ".join(m.field(x, ("metric",)).label for x in comp["metrics"]
                                            if x in {y.id for y in m.metrics}))
    if cal:
        parts.append(f"period: {cal.get('current_label')} ({cal.get('grain')} grain)")
    flt = S["view"].get("filters") or {}
    if flt:
        parts.append("filters: " + "; ".join(f"{m.field(d, ('dimension',)).label} = {', '.join(v)}" for d, v in flt.items()))
    facts = [f for f in (S.get("facts") or {}).get(page["page_id"], []) if comp["title"].split(" ")[0].lower() in f.lower()][:3]
    if facts:
        parts.append("values shown: " + " | ".join(facts))
    return "; ".join(parts)


def tile_ask(p):
    """Question -> Cortex Agent with the tile's context. Edit request -> Cortex + validator."""
    page, comp = _find(p.get("page_id"), p.get("component_id"))
    text = str(p.get("text") or "").strip()[:1000]
    if not text:
        raise ValueError("Type a question or a change for this tile.")
    cid = f"{page['page_id']}/{comp['component_id']}"
    chat = S["tile_chat"].setdefault(cid, [])
    chat.append({"role": "user", "text": text, "at": dt.datetime.now().strftime("%H:%M")})
    started = time.time()
    if p.get("mode") == "edit" or (p.get("mode") != "ask" and EDIT_WORDS.match(text)):
        try:
            out = edit_tile_nl(cortex(), data_ctx(), S["spec"], page["page_id"], comp, text)
            page["components"][page["components"].index(comp)] = out["tile"]
            _edited(out["governance"])
            rebuild_pages([page["page_id"]])
            notes = "; ".join(e["reason"] for e in out["governance"] if e["action"] != "kept")
            chat.append({"role": "agent", "kind": "edit", "text": f"Updated the tile: {out['tile']['title']} "
                         f"({out['tile']['type'].replace('_', ' ')})." + (f" Validator: {notes}" if notes else ""),
                         "provenance": f"Cortex AI_COMPLETE ({out['provenance']}) + layout validator"})
            S["tile_chat"][cid] = chat
            S["tile_chat"].setdefault(f"{page['page_id']}/{out['tile']['component_id']}", chat)
            log_ai("tile_edit", text, json.dumps(out["tile"]), out["provenance"], "valid", started)
        except Exception as exc:
            chat.append({"role": "agent", "kind": "edit", "error": str(exc)[:400], "text": ""})
        return
    if not S["agent"]:
        create_agent_action({})
    question = f"Context: {tile_context(page, comp)}.\nQuestion: {text}"
    try:
        try:
            ans = ask_agent(session, S["agent"]["fqn"], question, None)
        except Exception as first:
            owned = S["agent"]["fqn"].upper().startswith(config.APP_SCHEMA.upper() + ".")
            if not (is_missing_warehouse(first) and owned):
                raise
            create_agent(session, config.APP_SCHEMA, S["source"]["fqn"], S["source"]["name"].replace("_", " ").title(),
                         agent_questions(), warehouse=agent_warehouse(), replace=True)
            ans = ask_agent(session, S["agent"]["fqn"], question, None)
        chat.append({"role": "agent", "kind": "answer", **ans, "agent": S["agent"]["fqn"]})
        log_ai("tile_question", question, ans["text"], S["agent"]["fqn"], "ok", started)
    except Exception as exc:
        chat.append({"role": "agent", "kind": "answer", "error": str(exc)[:400], "text": ""})


# ------------------------------------------------------------------------------ publish (option A)
def list_roles(_p=None):
    try:
        rows = session.sql("SHOW ROLES").collect()
        S["roles"] = sorted({str(row_dict(r).get("name")) for r in rows if row_dict(r).get("name")})[:200]
    except Exception as exc:
        S["roles"] = []
        S["notice"] = f"Could not list roles ({str(exc)[:120]}); type role names instead."


def publish(p):
    """Freeze a version for viewers, grant app access to the chosen roles, record who it is shared with."""
    spec = S["spec"]
    if not spec:
        raise ValueError("Nothing to publish.")
    name = str(p.get("name") or spec.get("display_name") or "Dashboard")[:200]
    roles = [r for r in (p.get("roles") or []) if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_$]*", str(r))][:20]
    users = [u.strip() for u in (p.get("users") or []) if str(u).strip()][:50]
    if not S["dashboard"]:
        save_dashboard({"name": name})
    did = S["dashboard"]["dashboard_id"]
    out = store.publish(did, name, S["source"]["fqn"], S["audience"], S["bindings"], spec, S["view"], roles, users,
                        str(p.get("note") or ""), S.get("viewer") or "")
    granted, failed = [], []
    for r in roles:
        try:
            session.sql(f"GRANT USAGE ON STREAMLIT {APP_FQN} TO ROLE {r.upper()}").collect()
            granted.append(r.upper())
        except Exception as exc:
            failed.append(f"{r}: {str(exc)[:100]}")
    S["published"] = store.list_published()
    S["share"] = {"dashboard_id": did, "version": out["version"], "name": name, "granted": granted, "failed": failed,
                  "link": app_link(did)}
    S["notice"] = (f"Published '{name}' v{out['version']}."
                   + (f" App access granted to {', '.join(granted)}." if granted else "")
                   + (f" Could not grant: {'; '.join(failed)}" if failed else ""))


def app_link(did: str) -> str:
    try:
        base = st.context.url
    except Exception:
        base = ""
    return (base.split("?")[0] + f"?view={did}") if base else f"?view={did}"


def visible_published():
    me = (S.get("viewer") or "").lower()
    out = []
    for d in S["published"]:
        users = [u.lower() for u in (d.get("shared_users") or [])]
        if not users or not me or me in users or (d.get("published_by") or "").lower() == me:
            out.append(d)
    return out


def open_published(p):
    d = next((x for x in S["published"] if x["dashboard_id"] == p.get("dashboard_id")), None)
    if not d:
        S["published"] = store.list_published()
        d = next((x for x in S["published"] if x["dashboard_id"] == p.get("dashboard_id")), None)
    if not d:
        raise ValueError("That dashboard is not published (or was removed).")
    select_source({"fqn": d["semantic_view"]})
    S["bindings"] = Bindings.from_dict(d["bindings"]).as_dict()
    S["view"] = {**{"grain": None, "compare": "prior", "filters": {}}, **(d.get("view_settings") or {})}
    set_audience({"audience": d["audience"]})
    apply_spec(d["layout_spec"])
    S["viewer_mode"] = True
    S["dashboard"] = {"dashboard_id": d["dashboard_id"], "version": d["version"], "name": d["name"],
                      "published": True, "published_at": d.get("published_at"), "published_by": d.get("published_by")}


def exit_viewer(_p=None):
    S["viewer_mode"] = False
    S["step"] = "home"


def _find(page_id, component_id=None):
    page = next((p for p in S["spec"]["pages"] if p["page_id"] == page_id), None)
    if not page:
        raise ValueError("page")
    if component_id is None:
        return page, None
    comp = next((c for c in page["components"] if c["component_id"] == component_id), None)
    if not comp:
        raise ValueError("tile")
    return page, comp


def _edited(entries):
    S["spec"]["governance"] = (S["spec"].get("governance") or []) + entries
    S["spec"]["edited"] = True


def tile_remove(p):
    page, comp = _find(p.get("page_id"), p.get("component_id"))
    page["components"].remove(comp)
    S["results"].pop(f"{page['page_id']}/{comp['component_id']}", None)
    _edited([{"page": page["label"], "tile": comp["title"], "action": "removed", "reason": "Removed by user."}])


def tile_move(p):
    page, comp = _find(p.get("page_id"), p.get("component_id"))
    comps = page["components"]
    i = comps.index(comp)
    j = max(0, min(len(comps) - 1, i + (1 if int(p.get("dir", 1)) > 0 else -1)))
    comps[i], comps[j] = comps[j], comps[i]
    S["spec"]["edited"] = True


def tile_update(p):
    """Swap metric / dimension / chart type / width; the same validator as Cortex output applies."""
    page, comp = _find(p.get("page_id"), p.get("component_id"))
    patch = {k: v for k, v in (p.get("patch") or {}).items()
             if k in ("metric_id", "metric2_id", "dimension", "dimension2", "type", "width", "title", "metrics")}
    if set(patch) == {"width"}:
        comp["width"] = max(3, min(12, int(patch["width"])))
        S["spec"]["edited"] = True
        return
    new, entries = revalidate_tile(data_ctx(), S["spec"], page["page_id"], comp, patch)
    page["components"][page["components"].index(comp)] = new
    for e in entries:
        e["action"] = "edited" if e["action"] == "kept" else e["action"]
    _edited(entries)
    rebuild_pages([page["page_id"]])


def tile_add(p):
    started = time.time()
    page, _ = _find(p.get("page_id"))
    instruction = str(p.get("instruction", "")).strip()[:300]
    if not instruction:
        raise ValueError("Describe the tile to add, e.g. 'profit ratio by sub-category'.")
    out = compose_tile(cortex(), data_ctx(), S["spec"], page["page_id"], instruction)
    out["tile"]["origin"] = "cortex-edit"
    page["components"].append(out["tile"])
    for e in out["governance"]:
        e["reason"] = f"Added from request '{instruction}'. " + e["reason"]
    _edited(out["governance"])
    log_ai("layout_add_tile", instruction, json.dumps(out["tile"]), f"Cortex AI_COMPLETE ({out['provenance']})",
           "valid", started)
    rebuild_pages([page["page_id"]])
    S["notice"] = f"Cortex added '{out['tile']['title']}' ({out['tile']['type'].replace('_', ' ')})."


def page_regenerate(p):
    started = time.time()
    page, _ = _find(p.get("page_id"))
    instruction = str(p.get("instruction", "")).strip()[:300]
    out = compose_page(cortex(), data_ctx(), S["spec"], page["page_id"], instruction)
    S["spec"]["pages"][S["spec"]["pages"].index(page)] = out["page"]
    _edited(out["governance"])
    log_ai("layout_page", instruction or page["label"], json.dumps(out["page"])[:4000],
           f"Cortex AI_COMPLETE ({out['provenance']})", "valid", started)
    rebuild_pages([page["page_id"]])
    S["notice"] = f"Cortex redesigned page '{out['page']['label']}'."


def enrich(_p=None):
    """Phase 2: Snowflake ML FORECAST and TOP_INSIGHTS for components waiting on them."""
    if not S["spec"]:
        return
    m, b, prof = _profile_obj()
    eng = Engine(session, m, b, prof, cortex(), store, S["cache"], S["sql_log"], defer_ml=False, opts=S["view"])
    for page in S["spec"]["pages"]:
        for comp in page["components"]:
            cid = f"{page['page_id']}/{comp['component_id']}"
            res = S["results"].get(cid) or {}
            waiting = res.get("status") == "pending" or (res.get("data") or {}).get("insights_pending")
            if not waiting:
                continue
            started = time.time()
            try:
                data = getattr(eng, comp["type"])(comp)
                S.setdefault("facts", {}).setdefault(page["page_id"], []).extend(data.pop("_facts", []))
                S["results"][cid] = {"status": "ready", "data": data, "ms": int((time.time() - started) * 1000)}
            except Exception as exc:
                S["results"][cid] = {"status": "error", "error": str(exc)[:600]}


def refresh_workspace(_p=None):
    if S["spec"]:
        st.session_state.pop("_profiles", None)
        st.session_state.pop("_distinct", None)
        S["cache"].clear()
        apply_spec(S["spec"])


def narrative(p):
    page_id = p.get("page_id")
    page = next((x for x in S["spec"]["pages"] if x["page_id"] == page_id), None)
    if not page:
        raise ValueError("page")
    started = time.time()
    facts = S.get("facts", {}).get(page_id, [])
    out = cortex().narrative(page["label"], page["purpose"], facts, S["audience"])
    out["facts"] = facts
    S["narratives"][page_id] = out
    log_ai("page_summary", "\n".join(facts), out["text"], out["provenance"], "ok", started)


def agent_warehouse() -> str:
    try:
        wh = session.get_current_warehouse()
    except Exception:
        wh = None
    return (wh or config.AGENT_WAREHOUSE or "").replace('"', "")


def agent_questions():
    b = S["bindings"]
    return [f"What was {b['primary_metric'].split('.')[-1].lower().replace('_', ' ')} by "
            f"{(b.get('segment_dimension') or b['time_dimension']).split('.')[-1].lower().replace('_', ' ')} last month?",
            "Which segment grew fastest year over year?"]


def create_agent_action(_p):
    title = S["source"]["name"].replace("_", " ").title()
    made = create_agent(session, config.APP_SCHEMA, S["source"]["fqn"], title, agent_questions(),
                        warehouse=agent_warehouse(), replace=True)
    S["agents"] = find_agents(session, S["source"]["fqn"], config.AGENT_SCHEMAS) or [made]
    S["agent"] = next((a for a in S["agents"] if a["fqn"] == made["fqn"]), made)
    S["notice"] = f"Created Cortex Agent {made['fqn']} over {S['source']['fqn']}."


def ask(p):
    if not S["agent"]:
        raise ValueError("No Cortex Agent governs this semantic view yet. Create one first.")
    question = str(p.get("question", ""))
    started = time.time()
    S["chat"].append({"role": "user", "text": question, "at": dt.datetime.now().strftime("%H:%M")})
    try:
        try:
            ans = ask_agent(session, S["agent"]["fqn"], question, S["thread"])
        except Exception as first:
            # Agents created before the warehouse fix: rebuild app-owned ones once, then retry.
            owned = S["agent"]["fqn"].upper().startswith(config.APP_SCHEMA.upper() + ".")
            if not (is_missing_warehouse(first) and owned):
                raise
            title = S["source"]["name"].replace("_", " ").title()
            create_agent(session, config.APP_SCHEMA, S["source"]["fqn"], title, agent_questions(),
                         warehouse=agent_warehouse(), replace=True)
            S["notice"] = f"Updated {S['agent']['fqn']} to run its analyst tool on {agent_warehouse()}."
            ans = ask_agent(session, S["agent"]["fqn"], question, S["thread"])
        S["thread"] = ans.get("thread") if ans.get("thread", {}).get("thread_id") else S["thread"]
        S["chat"].append({"role": "agent", **ans, "agent": S["agent"]["fqn"], "at": dt.datetime.now().strftime("%H:%M")})
        log_ai("agent_question", question, ans["text"], f"{S['agent']['fqn']} run {ans.get('run_id')}", "ok", started)
    except Exception as exc:
        S["chat"].append({"role": "agent", "error": str(exc)[:400], "text": "", "agent": S["agent"]["fqn"]})
        log_ai("agent_question", question, str(exc), S["agent"]["fqn"], "error", started)


def add_decision(p):
    title = str(p.get("title", "")).strip()
    if not title:
        raise ValueError("A decision needs a title.")
    store.add_decision(S["source"]["fqn"], (S["spec"] or {}).get("template_id", ""), title,
                       str(p.get("detail", "")), str(p.get("owner", "")), p.get("due") or None,
                       p.get("evidence") or {})
    S["decisions"] = store.list_decisions(S["source"]["fqn"])
    _refresh_action_tables()
    S["notice"] = "Decision logged in Snowflake."


def decision_status(p):
    store.set_decision_status(str(p.get("decision_id")), str(p.get("status")))
    S["decisions"] = store.list_decisions(S["source"]["fqn"])
    _refresh_action_tables()


def _refresh_action_tables():
    for page in (S["spec"] or {}).get("pages", []):
        for comp in page["components"]:
            if comp["type"] == "action_table" and comp["state"] == "ready":
                S["results"][f"{page['page_id']}/{comp['component_id']}"] = {
                    "status": "ready", "data": {"rows": S["decisions"]}}


def save_dashboard(p):
    spec = S["spec"]
    name = str(p.get("name") or spec["display_name"])[:200]
    saved = store.save_dashboard(name, S["source"]["fqn"], S["audience"], spec["template_id"],
                                 spec["template_version"], S["bindings"],
                                 (S["dashboard"] or {}).get("dashboard_id"), layout=spec)
    S["dashboard"] = {**saved, "name": name}
    S["dashboards"] = store.list_dashboards()
    S["notice"] = f"Saved '{name}' as version {saved['version']} in Snowflake."


def open_dashboard(p):
    d = next((x for x in S["dashboards"] if x["dashboard_id"] == p.get("dashboard_id")), None)
    if not d:
        raise ValueError("dashboard")
    select_source({"fqn": d["semantic_view"]})
    S["bindings"] = Bindings.from_dict(d["bindings"]).as_dict()
    set_audience({"audience": d["audience"]})
    if d.get("layout"):
        apply_spec(d["layout"])
        S["dashboard"] = {"dashboard_id": d["dashboard_id"], "version": d["version"], "name": d["name"]}
        return
    tpl = get_template(d["template_id"])
    if not tpl or tpl.version != int(d["template_version"]):
        raise ValueError("Saved layout version is no longer in the catalog; choose a current layout.")
    select_layout({"template_id": d["template_id"]})
    S["dashboard"] = {"dashboard_id": d["dashboard_id"], "version": d["version"], "name": d["name"]}


def quality(_p):
    S["quality"] = {"ledger": store.ai_ledger(), "usage": store.cortex_usage()}


def go(p):
    step = p.get("step")
    if step in ("home", "source", "metrics", "layout", "workspace", "review"):
        S["step"] = step
        S["building"] = None
        if step == "source":
            S["dashboards"] = store.list_dashboards()
        if step == "home":
            S["published"] = store.list_published()


ACTIONS = {
    "boot": lambda p: boot(), "select_source": select_source, "suggest_bindings": suggest_bindings,
    "set_bindings": set_bindings, "set_audience": set_audience, "recommend_layout": recommend_layout,
    "select_layout": select_layout, "compose_layout": compose_layout, "home_suggestions": home_suggestions,
    "home_suggestions_ai": home_suggestions_ai, "route_prompt": route_prompt, "tile_remove": tile_remove,
    "tile_move": tile_move, "tile_update": tile_update, "tile_add": tile_add, "page_regenerate": page_regenerate,
    "refresh": refresh_workspace, "enrich": enrich, "narrative": narrative,
    "create_agent": create_agent_action, "ask": ask, "add_decision": add_decision,
    "decision_status": decision_status, "save_dashboard": save_dashboard, "open_dashboard": open_dashboard,
    "quality": quality, "go": go, "build_draft": build_draft, "redraft": redraft, "set_view": set_view,
    "page_add": page_add, "page_rename": page_rename, "page_move": page_move, "page_remove": page_remove,
    "tile_add_manual": tile_add_manual, "tile_ask": tile_ask, "publish": publish, "open_published": open_published,
    "exit_viewer": exit_viewer, "list_roles": list_roles,
}
VIEWER_ACTIONS = {"set_view", "enrich", "narrative", "tile_ask", "ask", "go", "exit_viewer", "open_published",
                  "add_decision", "decision_status", "quality", "boot", "home_suggestions", "home_suggestions_ai"}


def handle(event):
    if not isinstance(event, dict) or event.get("id") == S["last_request"]:
        return False
    S["last_request"] = event.get("id")
    if event.get("type") != "enrich":          # keep the previous action's message while ML fills in
        S["error"] = S["notice"] = ""
    fn = ACTIONS.get(event.get("type"))
    if S.get("viewer_mode") and event.get("type") not in VIEWER_ACTIONS:
        S["error"] = "This is a published, read-only dashboard. Open it in the builder to make changes."
        S["revision"] += 1
        return True
    if not fn:
        S["error"] = "Unknown action"
        return True
    try:
        fn(event.get("payload") or {})
    except Exception as exc:
        S["error"] = f"{exc}"
        S["debug"] = traceback.format_exc()[-1500:]
        if event.get("type") in ("compose_layout", "route_prompt", "redraft"):
            S["building"] = None
    S["revision"] += 1
    S["sql_log"][:] = S["sql_log"][-60:]
    return True


if S["features"] is None:
    try:
        boot()
    except Exception as exc:
        S["error"] = f"Startup: {exc}"
        S["features"] = {"complete": False, "errors": {"startup": str(exc)}}

if not hasattr(st.components, "v2"):
    st.error(f"This app needs Streamlit Components v2 (Streamlit ≥ 1.51); this runtime has {st.__version__}. "
             "Deploy on the container runtime (SYSTEM$ST_CONTAINER_RUNTIME_PY3_11).")
    st.stop()

COMPONENT = st.components.v2.component(
    "analytics_accelerator_enterprise",
    html="<div class='aa-root'></div>",
    # A comment line first: Streamlit treats single-line strings containing "/" as file paths.
    js="// Analytics Accelerator UI\n" + (HERE / "app_bundle.js").read_text(encoding="utf-8"),
    css="/* Analytics Accelerator UI */\n" + (HERE / "app_styles.css").read_text(encoding="utf-8"),
    isolate_styles=True,
)

payload = {k: v for k, v in S.items() if k not in ("cache", "published")}
payload["catalog_audiences"] = list(AUDIENCES)
payload["app_schema"] = config.APP_SCHEMA
if S["source"] and S["step"] in ("layout", "workspace"):
    try:
        payload["distinct"] = distinct_for(model_obj())
    except Exception:
        payload["distinct"] = {}
payload["published"] = visible_published()
payload["tile_types"] = {k: {"label": v["label"], "fields": v["fields"], "use": v["use"]} for k, v in TILES.items()}
payload["sql_log"] = S["sql_log"][-25:]
def _on_action():
    """Runs BEFORE the script on the rerun a click triggers, so the click is applied and rendered in ONE
    script run (previously: render stale data, apply the click, st.rerun, render again)."""
    try:
        handle(getattr(st.session_state.get("aa_ui"), "action", None))
    except Exception as exc:            # never let a callback error blank the page
        S["error"] = f"{exc}"


result = COMPONENT(key="aa_ui", data=json.loads(json.dumps(payload, default=str)), on_action_change=lambda: None)

if handle(getattr(result, "action", None)):   # fallback if the callback path is unavailable
    st.rerun()
