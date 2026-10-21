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
from agent_service import SPEC_VERSION, ask_agent, create_agent, find_agents, is_missing_warehouse
from ai_services import Cortex
from composer import (TILES, DataContext, apply_review, compose, compose_new_page, compose_page, compose_tile,
                      edit_tile_nl, manual_tile, metric_cards, normalise_template_spec, revalidate_tile)
from engine import Engine, fmt as engine_fmt
from headlines import headline as tile_headline
import home
from inventory import SOURCE_BASELINE, Bindings, build_profile, infer_bindings, validate_bindings
from layout_catalog import (AUDIENCES, bind_template, get_template, picker_options, select_template,
                            validate_cortex_output)
from semantic_catalog import (describe_semantic_view, list_semantic_views, metric_dimension_map, metrics_ddl, row_dict,
                              scope_model)
import semantic_builder as sb
import semantic_multi
import table_finder
from persona_layouts import PERSONAS, compose_persona
import metric_drafter
import custom_metrics
from semantic_query import AUDIENCE_GRAIN, SemanticQuery, distinct_values
from store import Store
import validation
import themes
import uat
import uat_export
import alerts
import alerts_core
import base64
import threading

HERE = Path(__file__).parent
PORTAL = os.environ.get("AA_PORTAL") == "1"      # viewer-only Analytics Accelerator Portal app (portal.py)
st.set_page_config(page_title="Analytics Accelerator Portal" if PORTAL else config.APP_TITLE, layout="wide",
                   initial_sidebar_state="collapsed")
st.markdown("<style>.block-container{padding:0.5rem 0.75rem 0 0.75rem!important;max-width:100%!important}"
            "header[data-testid='stHeader']{display:none}"
            # Streamlit greys out ("stale") elements while a rerun is in flight; the React UI shows its own
            # progress indicator, so keep the dashboard fully visible instead of flashing dull/blank.
            "[data-stale='true'],.stale-element{opacity:1!important;transition:none!important;filter:none!important}"
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
    "features": None, "sources": [], "dashboards": [], "source": None, "model": None, "metric_draft": None,
    "bindings": None, "binding_errors": [], "binding_suggestion": None, "audience": "executives",
    "profile": None, "options": [], "recommendation": None, "spec": None, "results": {},
    "narratives": {}, "agents": [], "agent": None, "chat": [], "thread": None, "decisions": [],
    "dashboard": None, "quality": None, "sql_log": [], "cache": {},
})
for _k, _v in {"view": {"grain": None, "compare": "prior", "filters": {}}, "filter_dims": [],
               "filter_options": {}, "draft": None, "tile_chat": {}, "viewer_mode": False, "published": [],
               "roles": [], "share": None, "featured": [], "data_brief": [], "prompts": [], "themes": [],
               "theme_default": {}, "theme_draft": None, "uat_entries": [], "download": None, "uat_inbox": None,
               "alert_draft": None, "alerts": None, "open_drawer": None,
               "uat_focus": None}.items():
    S.setdefault(_k, _v)
store = Store(session, config.APP_SCHEMA)
if PORTAL:
    store.ready = True          # portal only reads existing tables: skip the CREATE TABLE IF NOT EXISTS round on every run
APP_FQN = f"{config.APP_SCHEMA}.ANALYTICS_ACCELERATOR_ENTERPRISE"
PORTAL_FQN = f"{config.APP_SCHEMA}.ANALYTICS_ACCELERATOR_PORTAL"     # viewers get this app, never the builder


def cortex() -> Cortex:
    c = Cortex(session, config.APP_SCHEMA, config.MODELS, S["sql_log"], S.setdefault("ai_tokens", []))
    if S["features"]:
        c.model_in_use = S["features"].get("model")
        c.features = S["features"]
    return c


@st.cache_resource(show_spinner=False)
def _shared_cache() -> dict:
    return {}


def shared(key: str, fn, ttl: int = 600):
    """Portal only: set-up results shared by every viewer session for `ttl` seconds, so only the first viewer
    pays for them. Holds metadata (model description, profile, feature check), never dashboard numbers."""
    c = _shared_cache()
    hit = c.get(key)
    if hit and time.time() - hit[0] < ttl:
        return hit[1]
    value = fn()
    c[key] = (time.time(), value)
    return value


ENGINE_SHARE_SECONDS = 900


def qcache() -> dict:
    """Query and Snowflake ML results for the dashboard engine. Builder: this session only. Portal: shared by every
    viewer for 15 minutes, because every viewer sees the same governed data (the app runs with owner's rights), so
    only the first viewer of a page pays for its queries and ML training. Refresh still forces fresh numbers."""
    if not PORTAL:
        return S["cache"]
    bucket = int(time.time() // ENGINE_SHARE_SECONDS)
    c = _shared_cache()
    for k in [k for k in c if k.startswith("engine:") and k != f"engine:{bucket}"]:
        c.pop(k, None)                                   # drop older windows
    return shared(f"engine:{bucket}", dict, ttl=ENGINE_SHARE_SECONDS)


def sv_fqn() -> str:
    """The real semantic view (a Home dataset may be one table of it: 'DB.SCH.VIEW#TABLE')."""
    return (S["source"] or {}).get("fqn", "").split("#")[0]


def full_model(base: str, draft_now: bool = True):
    """The whole semantic view. A view with facts but no metrics gets metrics drafted from its facts:
    profiled in Snowflake, drafted by Cortex, validated, stored in AA_METRIC_DRAFTS and reused by everyone."""
    models = st.session_state.setdefault("_full", {})
    if base in models and (models[base].draft_meta is not None or not draft_now):
        return models[base]
    m = describe_semantic_view(session, base)
    m.draft_meta = None
    if m.facts_mode:
        sig = metric_drafter.signature(m)
        d = store.load_metric_draft(base, sig)
        if d is None and draft_now:
            started = time.time()
            d = metric_drafter.draft(cortex(), session, m, S["sql_log"])
            try:
                store.save_metric_draft(base, sig, d, viewer_name() or S["role"])
            except Exception:
                pass
            log_ai("metric_draft", base, json.dumps({k: d.get(k) for k in ("tables", "notes")})[:4000],
                   d.get("provenance", ""), d.get("origin", ""), started)
        if d:
            metric_drafter.apply(m, d)
            m.draft_meta = {k: d.get(k) for k in ("origin", "provenance", "notes", "profiled_facts", "error",
                                                  "saved_at", "saved_by")}
    models[base] = m
    return m


def model_obj():
    """Semantic view metadata, described once per session (one table of it for 'VIEW#TABLE' sources)."""
    if not S["source"]:
        return None
    models = st.session_state.setdefault("_models", {})
    fqn = S["source"]["fqn"]
    if PORTAL and (fqn not in models or not hasattr(models[fqn], "metric_dims")):
        def make():
            base, _, table = fqn.partition("#")
            full = full_model(base, draft_now=False)          # viewers reuse the stored metric draft, never draft
            m = scope_model(full, table) if table else full
            custom_metrics.apply(m, [])
            m.base_metric_dims = metric_dimension_map(session, m)
            return with_custom(m, base)
        models[fqn] = shared("model:" + fqn, make)
    if fqn not in models or not hasattr(models[fqn], "metric_dims"):
        base, _, table = fqn.partition("#")
        full = full_model(base)
        m = scope_model(full, table) if table else full
        custom_metrics.apply(m, [])                        # the dimension map is for the view's own metrics
        m.base_metric_dims = metric_dimension_map(session, m)   # valid metric x dimension pairs
        models[fqn] = with_custom(m, base)
    return models[fqn]


def with_custom(m, base: str):
    """Add the builders' custom metrics (AA_CUSTOM_METRICS) to the model; they split by the dimensions all
    their base metrics allow."""
    custom_metrics.apply(m, store.load_custom_metrics(base))
    m.metric_dims = custom_metrics.dims_for(m, getattr(m, "base_metric_dims", {}) or {})
    return m


def forget_model(fqn: str) -> None:
    """Drop cached models and profiles of a view so the next use reloads them (after a custom metric is saved)."""
    base = fqn.partition("#")[0]
    for k in list(st.session_state.get("_models", {})):
        if k.partition("#")[0] == base:
            st.session_state["_models"].pop(k, None)
    st.session_state.pop("_profiles", None)
    c = _shared_cache()
    for k in [k for k in c if k.startswith("model:" + base) or k.startswith("profile:")]:
        c.pop(k, None)


def redraft_metrics(_p=None):
    """Metrics page: ask Cortex for a fresh draft of the metrics (facts-only views)."""
    if not S["source"]:
        return
    base = sv_fqn()
    m = describe_semantic_view(session, base)
    if not m.facts_mode:
        raise ValueError("This semantic view already defines its own metrics.")
    started = time.time()
    d = metric_drafter.draft(cortex(), session, m, S["sql_log"])
    store.save_metric_draft(base, metric_drafter.signature(m), d, viewer_name() or S["role"])
    log_ai("metric_draft", base, json.dumps({k: d.get(k) for k in ("tables", "notes")})[:4000],
           d.get("provenance", ""), d.get("origin", ""), started)
    for k in ("_full", "_models", "_profiles", "_distinct", "_catalog"):
        st.session_state.pop(k, None)
    home.cache_put(S["role"], catalog=None)
    m = model_obj()
    S["model"] = m.summary()
    S["model"]["metric_dims"] = {k: sorted(v) for k, v in (getattr(m, "metric_dims", None) or {}).items()}
    S["metric_draft"] = metric_draft_payload(m)
    S["bindings"] = infer_bindings(m).as_dict()          # metric ids changed with the new draft
    if S.get("draft"):
        compose_layout({"goal": S["draft"].get("goal") or ""})   # re-fill the layout with the new metrics
    S["notice"] = f"Cortex re-drafted {len(m.metrics)} metrics from the facts. Review them on this page."


def metric_draft_payload(m):
    meta = getattr(m, "draft_meta", None)
    if not m or not m.facts_mode or not meta:
        return None
    return {**meta, "count": len(m.metrics), "facts": len(m.facts), "ddl": metrics_ddl(m),
            "view": m.fqn, "table": m.scope}


def profile_for(m, b: Bindings, audience: str):
    """Capability profile, computed once per (view, bindings, audience)."""
    cache = st.session_state.setdefault("_profiles", {})
    grain = (S.get("view") or {}).get("grain")
    key = (m.source_id, json.dumps(b.as_dict(), sort_keys=True), audience, grain)
    if key not in cache:
        make = lambda: build_profile(session, m, b, audience, S["features"] or {}, log=S["sql_log"], grain=grain)
        cache[key] = shared("profile:" + repr(key), make) if PORTAL else make()
    return cache[key]


def distinct_for(m) -> dict[str, int]:
    """Cardinality of every categorical dimension (one UNION query per source, cached)."""
    cache = st.session_state.setdefault("_distinct", {})
    if m.source_id not in cache:
        dims = [d.id for d in m.categorical_dimensions][:30]
        try:
            make = lambda: SemanticQuery(session, m, S["sql_log"]).distinct_counts(dims)
            cache[m.source_id] = shared("distinct:" + m.source_id, make) if PORTAL else make()
        except Exception:
            cache[m.source_id] = {}
    return cache[m.source_id]


def data_ctx() -> DataContext:
    m, b, prof = _profile_obj()
    return DataContext(m, b, prof, {**distinct_for(m), **(prof.distinct or {})}, S["audience"])


def with_tokens(prov, started):
    """Append the tokens Snowflake reported for the AI calls made since `started` (AI_COMPLETE show_details,
    agent response usage), so AA_AI_RUNS shows real tokens per feature without ACCOUNT_USAGE access."""
    try:
        led = [u for u in S.get("ai_tokens", []) if u.get("t", 0) >= started - 0.5]
        if not led:
            return prov
        tin, tout = sum(u.get("in", 0) for u in led), sum(u.get("out", 0) for u in led)
        cache = sum(u.get("cache_read", 0) for u in led)
        cw = sum(u.get("cache_write", 0) for u in led)
        extra = (f" · tokens {tin} in / {tout} out" + (f" / {cache} cache_read" if cache else "")
                 + (f" / {cw} cache_write" if cw else ""))
        return f"{(prov or '')[:300]}{extra}"
    except Exception:
        return prov


def note_agent_tokens(ans):
    t = (ans or {}).get("tokens")
    if t:
        S.setdefault("ai_tokens", []).append({"t": time.time(), "kind": "agent", **t})
        del S["ai_tokens"][:-200]


def log_ai(feature, inp, out, prov, status, started):
    prov = with_tokens(prov, started)
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


def portal_source(did) -> None:
    """Portal: discover only the schema of the dashboard being opened (shared across viewers)."""
    d = next((x for x in S["published"] if x["dashboard_id"] == did), None)
    if not d:
        return
    base = str(d.get("semantic_view") or "").upper().partition("#")[0]
    if base in {s.get("fqn") for s in S["sources"]}:
        return
    schema = base.rsplit(".", 1)[0]
    found = shared("sources:" + schema, lambda: list_semantic_views(session, [schema], {}))
    S["sources"] = list({s["fqn"]: s for s in (S["sources"] or []) + list(found)}.values())


def portal_boot():
    """Portal start-up: only what viewing needs. No table DDL, no draft list, one schema, shared feature check."""
    S["features"] = shared("features", lambda: cortex().detect_features(), ttl=3600)
    S["schema_errors"] = {}
    store.ready = True                       # tables already exist; the portal only reads them
    S["dashboards"] = []
    if not S.get("published"):
        S["published"] = store.list_published()
    wanted = st.query_params.get("view")
    if wanted:
        portal_source(wanted)
        open_published({"dashboard_id": wanted})


def boot():
    if PORTAL:
        S["viewer"] = S.get("viewer") or viewer_name()
        return portal_boot()
    S["viewer"] = viewer_name()
    try:
        S["role"] = str(session.sql("SELECT CURRENT_ROLE() AS R").collect()[0][0])
    except Exception:
        S["role"] = ""
    S["features"] = cortex().detect_features()
    S["schema_errors"] = {}
    S["sources"] = list_semantic_views(session, config.DISCOVERY_SCHEMAS, S["schema_errors"])
    store.ensure()
    S["dashboards"] = store.list_dashboards()
    S["published"] = store.list_published()
    load_themes()
    if not PORTAL:
        uat_inbox_refresh()                     # badges on Change requests / Waiting for my sign-off
        try:
            alerts_open()                       # badge on My alerts (alerts that fired)
        except Exception:
            S["alerts"] = None
    try:
        wanted = st.query_params.get("view")
    except Exception:
        wanted = None
    if wanted:
        open_published({"dashboard_id": wanted})


def _describe_cached(fqn):
    """Home catalog: uses a stored metric draft if there is one, never drafts (that happens on open)."""
    return full_model(fqn, draft_now=False)


def catalog():
    if "_catalog" not in st.session_state:
        hit = home.cache_get(S["role"])
        if hit and hit.get("catalog") is not None:
            st.session_state["_catalog"] = hit["catalog"]
            S["catalog_skipped"] = hit.get("skipped") or []
        else:
            skipped: list = []
            featured = {f: config.FEATURED_LABELS.get(f, "") for f in config.FEATURED_VIEWS}
            st.session_state["_catalog"] = home.build_catalog(S["sources"], _describe_cached, featured, skipped)
            # a featured view that is missing from Home always says why (no access, wrong name, no table)
            home.featured_gaps(st.session_state["_catalog"], featured, S["sources"], skipped,
                               S.get("schema_errors") or {})
            S["catalog_skipped"] = skipped
        home.cache_put(S["role"], catalog=st.session_state["_catalog"], skipped=S.get("catalog_skipped") or [])
    return st.session_state["_catalog"]


def _idea_sets() -> list:
    try:
        return store.idea_history(S["role"])
    except Exception:
        return []


def _show_ideas(sets: list, cat: list) -> bool:
    """Saved Cortex ideas (newest set first, earlier sets kept below), checked against today's catalog."""
    ideas = home.ensure_featured(home.merge_ideas(sets, cat), cat) if sets else []
    if not ideas:
        return False
    S["suggestions"], S["suggestions_by"], S["suggestions_at"] = ideas, "cortex", sets[0].get("created_at", "")
    home.cache_put(S["role"], suggestions=ideas, ideas_at=S["suggestions_at"])
    return True


def _featured_summary(cat):
    S["catalog_size"] = len(cat)
    S["data_brief"] = home.data_brief(cat)          # two lines under the prompt bar: what can I ask about?
    S["prompts"] = home.starter_prompts(cat)        # ready-to-edit requests per audience
    S["featured"] = [{"fqn": c["fqn"], "label": c["label"], "metrics": len(c["metrics"]), "adhoc": c.get("adhoc", False),
                      "dimensions": len(c["dimensions"])} for c in cat if c.get("featured")]


def home_suggestions(_p=None):
    """Phase 1: saved Cortex ideas (kept across deploys and catalog changes); otherwise instant catalog ideas."""
    hit = home.cache_get(S["role"])
    cat = catalog()
    _featured_summary(cat)
    if hit and hit.get("suggestions"):
        S["suggestions"], S["suggestions_by"], S["suggestions_at"] = hit["suggestions"], "cortex", hit.get("ideas_at", "")
        return
    if _show_ideas(_idea_sets(), cat):
        return
    S["suggestions"], S["suggestions_by"] = home.fallback_suggestions(cat), "catalog"


def home_suggestions_ai(p=None):
    """Phase 2: Cortex proposes executive / manager / operations dashboards. A new set is ADDED on top of the
    earlier ones (AA_IDEAS is append-only); nothing the user saw before disappears."""
    if not (S["features"] or {}).get("complete"):
        S["suggestions_by"] = "catalog-final"
        return
    started = time.time()
    on_screen = list(S.get("suggestions") or [])
    if (p or {}).get("fresh"):
        # "New ideas" also re-scans the semantic views, so a view added or changed since shows up
        S["schema_errors"] = {}
        S["sources"] = list_semantic_views(session, config.DISCOVERY_SCHEMAS, S["schema_errors"])
        for k in ("_catalog", "_full", "_models"):
            st.session_state.pop(k, None)
        home.cache_put(S["role"], catalog=None, skipped=None)
        _featured_summary(catalog())
    try:
        # 'New ideas' = the next themes per audience, never the ones already on screen
        avoid = home.shown_themes(on_screen, catalog()) if (p or {}).get("fresh") else {}
        sug = home.ai_suggestions(cortex(), catalog(), avoid)
        try:
            store.save_ideas(S["role"], home.catalog_signature(catalog()), sug, S["role"])
        except Exception:
            pass
        sets = _idea_sets()
        if not sets or sets[0].get("ideas") != sug:      # not saved (no store): still show new + earlier
            sets = [{"ideas": sug, "created_at": time.strftime("%Y-%m-%d %H:%M")}] + sets
        _show_ideas(sets, catalog())
        S["suggestions_at"] = time.strftime("%Y-%m-%d %H:%M")
        store.log_ai("home_suggestions", "", f"{len(catalog())} views", json.dumps(sug)[:4000],
                       with_tokens("Cortex AI_COMPLETE", started), "valid", time.time() - started)
    except Exception as exc:
        store.log_ai("home_suggestions", "", "", str(exc)[:400], "Cortex AI_COMPLETE", "fallback",
                       time.time() - started)
        if (p or {}).get("fresh"):
            # keep what the user had, re-checked against the re-scanned catalog (featured views included)
            if not _show_ideas(_idea_sets(), catalog()):
                S["suggestions"] = home.ensure_featured(S.get("suggestions") or home.fallback_suggestions(catalog()), catalog())
            raise ValueError("Cortex couldn't suggest new ideas right now; your current ideas are kept.")
        S["suggestions_by"] = "catalog-final"


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
    by_label = {x.label.lower(): x.id for x in m.metrics}
    from persona_layouts import SKIP as _NOT_HEADLINE        # plan targets / variance metrics never lead
    idea_ids = [by_label[str(x).lower()] for x in ((sug or {}).get("metrics") or []) if str(x).lower() in by_label
                and not _NOT_HEADLINE.search(by_label[str(x).lower()].split(".")[-1])]
    if idea_ids:
        # an idea = an audience looking at a metric theme: its metrics lead the dashboard (KPIs, scorecard, worklist)
        b.supporting_metrics = list(dict.fromkeys(idea_ids[1:] + [b.primary_metric] + b.supporting_metrics))
        b.supporting_metrics = [x for x in b.supporting_metrics if x and x != idea_ids[0]][:5]
        b.primary_metric = idea_ids[0]
        b.source = "idea"
    elif len(named := [x for x in home.mentioned_metrics(m, p.get("prompt") or prompt)
                       if not _NOT_HEADLINE.search(x.split(".")[-1])]) >= 2:
        # a typed request that names several metrics: they lead the dashboard, like an idea's
        b.supporting_metrics = [x for x in dict.fromkeys(named[1:] + [b.primary_metric] + b.supporting_metrics)
                                if x and x != named[0]][:5]
        b.primary_metric = named[0]
        b.source = "idea"
    else:
        primary = home.pick_primary(m, r.get("primary_metric", ""), prompt)
        if primary and primary != b.primary_metric:
            b.supporting_metrics = [x for x in [b.primary_metric] + b.supporting_metrics if x != primary]
            b.primary_metric = primary
        b.source = "prompt"
    # the designer sees every metric; the focus list stays short so headline queries stay fast
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
    store.log_ai(feature, "", inp, out, with_tokens(prov, started), status, time.time() - started)


def select_source(p):
    fqn = str(p.get("fqn", "")).upper()
    base, _, table = fqn.partition("#")          # VIEW#TABLE = one table of a facts-only view
    if base not in {s.get("fqn") for s in S["sources"]}:
        raise ValueError("Choose one of the discovered semantic views.")
    src = next(s for s in S["sources"] if s.get("fqn") == base)
    S["source"] = {**src, "fqn": fqn, "name": f"{src['name']} {table}".strip()} if table else src
    m = model_obj()
    S["model"] = m.summary()
    S["metric_draft"] = metric_draft_payload(m)
    # valid metric x dimension pairs (from SHOW SEMANTIC DIMENSIONS ... FOR METRIC) so menus only offer what works
    S["model"]["metric_dims"] = {k: sorted(v) for k, v in (getattr(m, "metric_dims", None) or {}).items()}
    S["bindings"] = infer_bindings(m).as_dict()
    S["binding_errors"] = validate_bindings(m, Bindings.from_dict(S["bindings"]))
    S["binding_suggestion"] = None
    S["agents"] = (shared("agents:" + base, lambda: find_agents(session, base, config.AGENT_SCHEMAS)) if PORTAL
                   else find_agents(session, base, config.AGENT_SCHEMAS))
    S["agent"] = pick_agent(S["agents"])
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


def apply_spec(spec, page_id=None):
    """Phase 1: governed queries for the page on screen only (fast). Other pages load when their tab is
    opened ("load_page"); Snowflake ML runs in phase 2 ("enrich")."""
    m, b, prof = _profile_obj()
    ids = [p["page_id"] for p in spec["pages"]]
    first = page_id if page_id in ids else (ids[0] if ids else None)
    eng = Engine(session, m, b, prof, cortex(), store, qcache(), S["sql_log"], defer_ml=True, opts=S["view"])
    results, facts = eng.build({"pages": [p for p in spec["pages"] if p["page_id"] == first]})
    S.update(spec=spec, results=results, facts=facts, narratives={}, step="workspace",
             profile=prof.as_dict(), tile_q=dict(eng.tile_keys), validation=None)
    S["focus_page"] = None
    S["decisions"] = store.list_decisions(m.fqn)
    setup_filters()


def rebuild_pages(page_ids):
    m, b, prof = _profile_obj()
    pages = [p for p in S["spec"]["pages"] if p["page_id"] in page_ids]
    eng = Engine(session, m, b, prof, cortex(), store, qcache(), S["sql_log"], defer_ml=True, opts=S["view"])
    results, facts = eng.build({"pages": pages})
    tq = S.setdefault("tile_q", {})
    for k in [k for k in tq if k.split("/")[0] in page_ids]:
        del tq[k]
    tq.update(eng.tile_keys)
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
        if S["audience"] in PERSONAS and not seed_id:
            asked = str((S.get("building") or {}).get("prompt") or "").strip()[:400]   # the person's own words
            spec = compose_persona(cortex(), ctx, goal, asked=asked)
            log_ai("persona_slots", goal, json.dumps({"slots": spec["slots"], "governance": spec["governance"]})[:4000],
                   spec["provenance"], spec["slot_origin"], started)
            # the Review page says it already (origin pill): no second banner
            spec["goal"] = goal
            S["building"] = None
            S["draft"] = {"spec": spec, "cards": metric_cards(ctx, spec), "goal": goal}
            S["step"] = "review"
            return
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
def _custom_value(m, cand: dict) -> dict:
    """Run the candidate once: its value (and its base metrics') for the latest full period."""
    from engine import fmt, fmt_kind
    base = (S["source"] or {}).get("fqn", "").partition("#")[0]
    rows = store.load_custom_metrics(base)
    try:
        custom_metrics.apply(m, rows + [{**cand, "created_by": "preview"}])
        q = SemanticQuery(session, m, S["sql_log"])
        b = Bindings.from_dict(S["bindings"])
        grain = (S.get("view") or {}).get("grain") or AUDIENCE_GRAIN.get(S["audience"], "month")
        ids = [cand["name"]] + custom_metrics.bases(cand["tree"])
        cal = q.calendar(b.time_dimension, ids[1], grain)
        time_f = q.dim(b.time_dimension)
        mets = [f"{q.metric(x).ref} AS M{i}" for i, x in enumerate(ids)]
        r = q.run("SELECT * FROM " + q.sv([], mets, q.range_where(time_f, cal.current_start, cal.end_exclusive)))
        r = r[0] if r else {}
        vals = [None if r.get(f"m{i}") is None else float(r.get(f"m{i}")) for i in range(len(ids))]
        lab = lambda x: m.field(x, ("metric",)).label
        return {"period": cal.label(cal.current_start),
                "value": fmt(vals[0], fmt_kind(cand["name"], vals[0])),
                "bases": [{"label": lab(x), "value": fmt(v, fmt_kind(x.split(".")[-1], v))}
                          for x, v in zip(ids[1:], vals[1:])]}
    finally:
        custom_metrics.apply(m, rows)


def metric_define(p):
    """Review > metric picker > Define a metric: English or a formula -> checked, test-run preview (not saved)."""
    if not S.get("draft"):
        raise ValueError("Define custom metrics while reviewing a draft dashboard.")
    started = time.time()
    m = model_obj()
    text, name = str(p.get("text") or "")[:600], str(p.get("name") or "")[:60]
    S["draft"]["selected"] = [x for x in (p.get("selected") or []) if isinstance(x, str)]
    try:
        cand = custom_metrics.define(cortex(), m, text, name)
        test = _custom_value(m, cand)
    except custom_metrics.FormulaError as exc:
        S["draft"]["metric_preview"] = {"error": str(exc), "text": text, "name": name}
        log_ai("metric_custom", text, str(exc), "custom metric", "rejected", started)
        return
    lab = lambda x: m.field(x, ("metric",)).label
    preview = {k: cand[k] for k in ("name", "label", "formula", "description", "theme", "origin", "provenance")}
    preview.update({"text": text, "display": custom_metrics.show(cand["tree"], lab), **test})
    custom_metrics.apply(m, store.load_custom_metrics(S["source"]["fqn"].partition("#")[0]) + [cand])
    preview["governed"] = custom_metrics.governed_snippet(m, m.field(cand["name"], ("metric",)))
    with_custom(m, S["source"]["fqn"].partition("#")[0])
    S["draft"]["metric_preview"] = preview
    if cand["origin"] == "cortex":
        log_ai("metric_custom", text, json.dumps({k: preview[k] for k in ("name", "formula", "value")}),
               cand["provenance"], "valid", started)


def metric_save(p):
    """Save the previewed custom metric for this semantic view and put it on the draft."""
    pv = (S.get("draft") or {}).get("metric_preview") or {}
    if not pv or pv.get("error"):
        raise ValueError("Nothing to save: check a metric first.")
    m = model_obj()
    base = S["source"]["fqn"].partition("#")[0]
    tree = custom_metrics.parse(pv["formula"], m)                    # re-validated, never trusted from the UI
    if pv["name"] in {f.name.upper() for f in m.metrics + m.dimensions + m.facts}:
        raise ValueError(f"{pv['name']} already exists in this view.")
    store.save_custom_metric(base, {**pv, "formula": custom_metrics._canon(tree)}, viewer_key() or viewer_name())
    forget_model(S["source"]["fqn"])
    m = model_obj()
    new_id = m.field(pv["name"], ("metric",)).id
    S["draft"]["cards"] = metric_cards(data_ctx(), S["draft"]["spec"])
    S["draft"]["selected"] = list(dict.fromkeys([x for x in (p.get("selected") or []) if isinstance(x, str)] + [new_id]))
    S["draft"]["metric_preview"] = None
    S["notice"] = (f"{pv['label']} saved as a custom metric for this semantic view and added to the dashboard. "
                   "It shows a 'custom' tag until the data owner makes it governed.")


def switch_layout(p):
    """Review: another reviewed layout for the same audience, filled with the same metrics (no AI call)."""
    d = S.get("draft")
    if not d or d["spec"].get("origin") != "persona":
        raise ValueError("Layouts can be switched on a reviewed audience layout.")
    ctx = data_ctx()
    spec = compose_persona(None, ctx, d["spec"].get("goal") or d.get("goal") or "", variant=str(p.get("variant") or ""),
                           reuse=d["spec"])
    spec["goal"] = d["spec"].get("goal") or d.get("goal") or ""
    sel = [x for x in (p.get("metrics") or []) if isinstance(x, str)]
    S["draft"] = {**d, "spec": spec, "cards": metric_cards(ctx, spec), "selected": sel or d.get("selected"),
                  "preview": None, "metric_preview": None}
    S["notice"] = f"Layout switched to {spec['display_name']}. Same metrics; review, then build."


def preview_draft(p):
    """Review: run one page of the draft with real data so the preview shows real tiles (ML deferred)."""
    import copy
    d = S.get("draft")
    if not d:
        raise ValueError("Nothing to preview.")
    ctx = data_ctx()
    spec, _gov = apply_review(ctx, copy.deepcopy(d["spec"]), p.get("metrics") or [], p.get("outline") or [])
    pid = str(p.get("page_id") or spec["pages"][0]["page_id"])
    page = next((x for x in spec["pages"] if x["page_id"] == pid), spec["pages"][0])
    m, b, prof = _profile_obj()
    results, _facts = Engine(session, m, b, prof, cortex(), store, qcache(), S["sql_log"],
                             defer_ml=True, opts=S["view"]).build({"pages": [page]})
    S["draft"]["preview"] = {"page_id": page["page_id"], "results": results,
                             "comps": {c["component_id"]: {**c, "span": c.get("span") or c.get("width") or 6}
                                       for c in page["components"]}}


def metric_cancel(_p=None):
    if S.get("draft"):
        S["draft"]["metric_preview"] = None


def build_draft(p):
    """User approved the review: chosen metrics + edited outline -> build the dashboard."""
    if not S["draft"]:
        raise ValueError("Nothing to build - design a dashboard first.")
    spec, _gov = apply_review(data_ctx(), S["draft"]["spec"], p.get("metrics") or [], p.get("outline") or [])
    S["draft"] = None
    apply_spec(spec)
    S["notice"] = f"Built {len(spec['pages'])} page{'s' if len(spec['pages']) != 1 else ''} from your review."


def redraft(p):
    """Redesign around the metrics the user picked in review: metrics they added lead every metric slot
    (headline KPIs, scorecard columns, status tiles, worklist), the rest of their selection follows, and the
    selection is kept on the new draft instead of resetting to the recommended metrics."""
    m = model_obj()
    valid = {y.id for y in m.metrics}
    picked = [x for x in (p.get("metrics") or []) if x in valid]
    added = [x for x in (p.get("added") or []) if x in picked]
    ordered = list(dict.fromkeys(added + picked))
    goal = (S["draft"] or {}).get("goal") or ""
    goal = re.sub(r"\s*Focus on these metrics:.*$", "", goal)          # don't stack focus lists on re-designs
    if ordered:
        b = Bindings.from_dict(S["bindings"])
        b.primary_metric, b.supporting_metrics, b.source = ordered[0], ordered[1:9], "idea"
        S["bindings"] = b.as_dict()
        st.session_state.pop("_profiles", None)
    labels = [m.field(x, ("metric",)).label for x in ordered]
    compose_layout({"goal": goal + (" Focus on these metrics: " + ", ".join(labels) if labels else "")})
    if S.get("draft") and picked:
        S["draft"]["selected"] = picked                      # the review keeps the user's selection
        S["draft"]["goal"] = goal


AUDIENCE_NAMES = {"executives": "executive", "managers": "manager", "daily_operations": "operations",
                  "weekly_business_review": "weekly review"}
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
        key = (m.source_id, d)
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


THEMES = tuple(themes.BUILT_IN)          # classic (default), editorial, command; company themes are "t:<id>"


# ------------------------------------------------------------------------------ company themes
def load_themes():
    S["themes"] = store.list_themes()
    S["theme_default"] = store.get_setting("default_theme") or {}


def _theme_known(tid: str) -> bool:
    return tid in THEMES or (tid.startswith("t:") and any(t["theme_id"] == tid[2:] for t in S.get("themes") or []))


def resolved_theme() -> dict:
    """The theme the dashboard on screen uses: a published snapshot, else its own choice, else the company default,
    else Classic. Company themes reach the page as CSS colour variables only."""
    snap = (S.get("view") or {}).get("theme_snapshot")
    if S.get("viewer_mode") and snap:
        return snap
    tid = ((S.get("view") or {}).get("theme") or (S.get("spec") or {}).get("theme")
           or (S.get("theme_default") or {}).get("setting_value") or "classic")
    if tid.startswith("t:"):
        t = next((x for x in S.get("themes") or [] if x["theme_id"] == tid[2:]), None)
        if t and t.get("tokens"):
            return {"id": tid, "name": t["name"], "kind": "custom", "vars": themes.css_vars(t["tokens"]),
                    "dark": themes.is_dark(t["tokens"].get("bg", "#ffffff"))}
        tid = "classic"
    if tid not in THEMES:
        tid = "classic"
    return {"id": tid, "name": themes.BUILT_IN[tid]["name"], "kind": "builtin", "vars": {}, "dark": tid == "command"}


def theme_preview(p):
    """Form values, a token file or a logo -> brand colours -> full theme + checks. Nothing is saved."""
    src = p.get("source") or "form"
    if src in ("tokens", "logo"):
        f = p.get("file") or {}
        inputs = themes.parse_upload(src, str(f.get("name") or ""), str(f.get("b64") or ""))
        if not inputs.get("primary"):
            raise ValueError("No brand colours found in that file. Try the form, or a file with hex colours.")
        inputs = {**themes.clean_inputs(p.get("inputs") or {}), **{k: v for k, v in inputs.items() if v}}
    else:
        inputs = themes.clean_inputs(p.get("inputs") or {})
    out = themes.build(inputs)
    S["theme_draft"] = {"source": src, "name": str(p.get("name") or (p.get("file") or {}).get("name") or "")[:80],
                        "theme_id": str(p.get("theme_id") or ""), **out}


def theme_save(p):
    name = str(p.get("name") or "").strip()[:80]
    if not name:
        raise ValueError("Give the theme a name, e.g. the company or brand.")
    out = themes.build(p.get("inputs") or {})            # recomputed here: the browser never supplies tokens
    tid = str(p.get("theme_id") or "")
    if tid and not any(t["theme_id"] == tid for t in S.get("themes") or []):
        tid = ""
    tid = store.save_theme(tid, name, str(p.get("source") or "form"), out["inputs"], out["tokens"], out["checks"],
                           out["status"])
    if p.get("make_default"):
        store.set_setting("default_theme", "t:" + tid)
    load_themes()
    S["theme_draft"] = None
    S["notice"] = f"Saved theme '{name}'" + (" and made it the company default." if p.get("make_default") else ".")


def theme_default(p):
    tid = str(p.get("theme_id") or "classic")
    if not _theme_known(tid):
        raise ValueError("Unknown theme.")
    store.set_setting("default_theme", tid)
    load_themes()
    S["notice"] = "Company default theme set. Dashboards without their own theme use it; published versions keep theirs."


def theme_apply(p):
    """This dashboard only (kept when it is published). '' = follow the company default."""
    tid = str(p.get("theme_id") or "")
    if tid and not _theme_known(tid):
        raise ValueError("Unknown theme.")
    v = dict(S["view"])
    v.pop("theme_snapshot", None)
    if tid:
        v["theme"] = tid
    else:
        v.pop("theme", None)
    S["view"] = v
    if S.get("spec"):                       # saved with the dashboard layout, so it survives save / open
        if tid:
            S["spec"]["theme"] = tid
        else:
            S["spec"].pop("theme", None)
        S["spec"]["edited"] = True
    name = next((t["name"] for t in S.get("themes") or [] if "t:" + t["theme_id"] == tid), None) or \
        (themes.BUILT_IN.get(tid) or {}).get("name") or "the company default"
    S["notice"] = f"This dashboard now uses {name}."


def theme_delete(p):
    t = next((x for x in S.get("themes") or [] if x["theme_id"] == p.get("theme_id")), None)
    if not t:
        raise ValueError("Unknown theme.")
    store.save_theme(t["theme_id"], t["name"], t.get("source") or "", t.get("inputs") or {}, t.get("tokens") or {},
                     t.get("checks") or [], t.get("status") or "", active=False)
    if (S.get("theme_default") or {}).get("setting_value") == "t:" + t["theme_id"]:
        store.set_setting("default_theme", "classic")
    if (S["view"] or {}).get("theme") == "t:" + t["theme_id"]:
        S["view"] = {k: v for k, v in S["view"].items() if k != "theme"}
    load_themes()
    S["notice"] = f"Removed theme '{t['name']}'. Published dashboards that used it keep their colours."


def set_view(p):
    """Time bar and filters: period grain, compare-to, filter values. Rebuilds every page.
    A theme change only restyles (no queries)."""
    v = dict(S["view"])
    if set(p) == {"theme"}:
        if _theme_known(str(p["theme"])):
            v["theme"] = p["theme"]
            v.pop("theme_snapshot", None)
            S["view"] = v
        return
    if "grain" in p:
        v["grain"] = p["grain"] if p["grain"] in ("day", "week", "month", "quarter") else None
    if "compare" in p and p["compare"] in ("prior", "yoy", "plan"):
        v["compare"] = p["compare"]
    if "filters" in p:
        clean = {}
        cats = {d.id for d in model_obj().categorical_dimensions}
        for dim, vals in (p.get("filters") or {}).items():
            if dim not in S["filter_options"] and dim in cats:      # drill from a scorecard row
                S["filter_options"][dim] = distinct_values(SemanticQuery(session, model_obj()), dim, 300)
            allowed = set(S["filter_options"].get(dim) or [])
            keep = [x for x in (vals or []) if x in allowed]     # only values read from the semantic view
            if keep:
                clean[dim] = keep
        v["filters"] = clean
    S["view"] = v
    if S["spec"]:
        # Only the page on screen is re-queried; the others reload (cached by filter signature) when opened.
        m, b, prof = _profile_obj()
        S["profile"] = prof.as_dict()
        S["results"], S["narratives"] = {}, {}
        ids = [x["page_id"] for x in S["spec"]["pages"]]
        rebuild_pages([p.get("page_id") if p.get("page_id") in ids else ids[0]])


def load_page(p):
    """A page tab was opened whose tiles have not been queried yet under the current view."""
    pid = p.get("page_id")
    if S["spec"] and any(x["page_id"] == pid for x in S["spec"]["pages"]):
        if not any(k.startswith(pid + "/") for k in S["results"]):
            rebuild_pages([pid])


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
TREND_TOGGLE = re.compile(r"\b(remove|hide|drop|delete|no|without|turn off|show|add|include|bring back|turn on)\b[^.]{0,40}?"
                          r"\b(trends?|sparklines?|lines?|mini ?charts?)\b", re.I)
from composer import KPI_DISPLAYS, display_from_text as _display_from_text  # noqa: E402


TITLE_EDIT = re.compile(r"^\s*(?:please\s+)?(?:change|rename|set|update|call|make)\s+(?:the\s+)?(?:this\s+)?"
                        r"(?:tile'?s?\s+)?(?:title|name|heading|tile)\s*(?:of\s+this\s+tile\s*)?(?:to|as|:)\s*"
                        r"[\"'\u201c\u2018]?(?P<t>.+?)[\"'\u201d\u2019]?\s*\.?\s*$", re.I)
ASK_BUT_EDIT = re.compile(r"^\s*(?:please\s+)?(change|make|switch|convert|rename|show (it|this) as|split|break|"
                          r"resize|swap|replace|remove|add|turn)\b", re.I)
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
    if S.get("viewer_mode"):                         # published dashboards: questions only, never edits
        if TITLE_EDIT.match(text) or ASK_BUT_EDIT.match(text) or p.get("mode") == "edit":
            chat.append({"role": "agent", "kind": "answer", "text": "This is a published dashboard, so it can't be "
                         "changed here. Ask me a question about it, or open it in the builder to change it.",
                         "provenance": "Tile assistant"})
            return
        p = {**p, "mode": "ask"}
    title = TITLE_EDIT.match(text)
    if title and title.group("t").strip():          # deterministic, any mode: a new title is never a question
        comp["title"] = title.group("t").strip()[:80]
        comp["title_locked"] = True
        S["spec"]["edited"] = True
        chat.append({"role": "agent", "kind": "edit", "text": f"Renamed the tile to '{comp['title']}'.",
                     "provenance": "Tile setting (no query change)"})
        return
    if p.get("mode") == "ask" and ASK_BUT_EDIT.match(text):
        p = {**p, "mode": "edit"}                    # a change request typed in Ask mode: treat it as a change
        chat.append({"role": "agent", "kind": "edit", "text": "That's a change, not a question, so I'm changing "
                     "the tile instead of asking the agent.", "provenance": "Tile assistant"})
    disp = _display_from_text(text) if comp.get("type") == "kpi_plan" and p.get("mode") != "ask" else None
    if disp:                                      # deterministic: switch how the KPI comparison is drawn
        comp["display"] = disp
        S["spec"]["edited"] = True
        chat.append({"role": "agent", "kind": "edit", "text": f"Showing these KPIs as {KPI_DISPLAYS[disp]}.",
                     "provenance": "Tile setting (no query change)"})
        return
    toggle = TREND_TOGGLE.search(text) if comp.get("type") in ("kpi_grid", "kpi_plan") and p.get("mode") != "ask" else None
    if toggle:                                    # deterministic: no need to ask Cortex to hide/show sparklines
        show = not re.match(r"(remove|hide|drop|delete|no|without|turn off)", toggle.group(1), re.I)
        new, gov = revalidate_tile(data_ctx(), S["spec"], page["page_id"], comp, {"show_trend": show})
        page["components"][page["components"].index(comp)] = new
        _edited(gov)
        rebuild_pages([page["page_id"]])
        chat.append({"role": "agent", "kind": "edit", "text": ("Showing" if show else "Removed") +
                     " the monthly trend line under every KPI card.", "provenance": "Tile setting (layout validator)"})
        return
    if p.get("mode") == "edit" or (p.get("mode") != "ask" and EDIT_WORDS.match(text)):
        try:
            out = edit_tile_nl(cortex(), data_ctx(), S["spec"], page["page_id"], comp, text)
            keys = ("type", "metric_id", "metric2_id", "metrics", "dimension", "dimension2", "dimensions", "width",
                    "show_trend", "title")
            if all(out["tile"].get(k) == comp.get(k) for k in keys):
                chat.append({"role": "agent", "kind": "edit", "text":
                             "No change made: that isn't something this tile can do. A tile can change its chart type, "
                             "metric(s), breakdown, width, title" + (", and show or hide the KPI trend lines"
                                                                     if comp.get("type") in ("kpi_grid", "kpi_plan") else "") + ".",
                             "provenance": f"Cortex AI_COMPLETE ({out['provenance']}) + layout validator"})
                return
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
    ensure_agent()
    question = f"Context: {tile_context(page, comp)}.\nQuestion: {text}"
    try:
        try:
            ans = ask_agent(session, S["agent"]["fqn"], question, None)
        except Exception as first:
            owned = S["agent"]["fqn"].upper().startswith(config.APP_SCHEMA.upper() + ".")
            if not (is_missing_warehouse(first) and owned):
                raise
            create_agent(session, config.APP_SCHEMA, sv_fqn(), S["source"]["name"].replace("_", " ").title(),
                         agent_questions(), warehouse=agent_warehouse(), replace=True,
                         search_service=search_service_for(sv_fqn()),
                         decision_proc=config.DECISION_TOOL or "")
            ans = ask_agent(session, S["agent"]["fqn"], question, None)
        chat.append({"role": "agent", "kind": "answer", **ans, "agent": S["agent"]["fqn"]})
        note_agent_tokens(ans)
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


def grant_portal(role: str) -> None:
    """A viewer role needs USAGE on the app's database and schema as well as on the portal app itself."""
    db = config.APP_SCHEMA.split(".")[0]
    for stmt in (f"GRANT USAGE ON DATABASE {db} TO ROLE {role}",
                 f"GRANT USAGE ON SCHEMA {config.APP_SCHEMA} TO ROLE {role}"):
        try:
            session.sql(stmt).collect()
        except Exception:
            pass                                     # already granted, or managed by an admin: the app grant decides
    session.sql(f"GRANT USAGE ON STREAMLIT {PORTAL_FQN} TO ROLE {role}").collect()


def publish(p):
    """Freeze a version for viewers, give the chosen roles the Analytics Accelerator Portal, record who it is shared with."""
    spec = S["spec"]
    if not spec:
        raise ValueError("Nothing to publish.")
    name = str(p.get("name") or spec.get("display_name") or "Dashboard")[:200]
    roles = [r for r in (p.get("roles") or []) if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_$]*", str(r))][:20]
    users = [u.strip() for u in (p.get("users") or []) if str(u).strip()][:50]
    if not S["dashboard"]:
        save_dashboard({"name": name})
    did = S["dashboard"]["dashboard_id"]
    view = {**S["view"], "validation": validation_brief(), "theme_snapshot": resolved_theme()}
    out = store.publish(did, name, S["source"]["fqn"], S["audience"], S["bindings"], spec, view, roles, users,
                        str(p.get("note") or ""), S.get("viewer") or "")
    granted, failed = [], []
    for r in roles:
        try:
            grant_portal(r.upper())
            granted.append(r.upper())
        except Exception as exc:
            failed.append(f"{r}: {str(exc)[:100]}")
    S["published"] = store.list_published()
    direct = bool(getattr(config, "PORTAL_APP_URL", ""))
    S["share"] = {"dashboard_id": did, "version": out["version"], "name": name, "granted": granted, "failed": failed,
                  "link": app_link(did) if direct else getattr(config, "PORTAL_URL", "") or app_link(did),
                  "link_note": ("This link opens the dashboard in the Analytics Accelerator Portal. It is also in the portal "
                                "catalog for everyone it is shared with." if direct else
                                f"This opens the Analytics Accelerator Portal. '{name}' is in its catalog for everyone it is "
                                "shared with. In the portal, Share on the tile gives a link straight to it.")}
    S["notice"] = (f"Published '{name}' v{out['version']}."
                   + (f" Analytics Accelerator Portal access granted to {', '.join(granted)}." if granted else "")
                   + (f" Could not grant: {'; '.join(failed)}" if failed else ""))


def own_base_url() -> str:
    try:
        return (st.context.url or "").split("?")[0]
    except Exception:
        return ""


def app_link(did: str) -> str:
    if not PORTAL and getattr(config, "PORTAL_APP_URL", ""):      # share links open the portal, not the builder
        return config.PORTAL_APP_URL.split("?")[0].rstrip("/") + f"?view={did}"
    try:
        base = st.context.url
    except Exception:
        base = ""
    return (base.split("?")[0] + f"?view={did}") if base else f"?view={did}"


def viewer_ids() -> set:
    """Every name the signed-in viewer may be listed under: user name, email, first name (computed once)."""
    if S.get("viewer_ids") is None:
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
        ids = set()
        for c in cands:
            c = str(c or "").strip().lower()
            if not c or re.search(r"streamlit|stplat|service|system", c):
                continue
            ids.update({c, re.split(r"[.@_\s]", c)[0]})
        if S.get("viewer"):
            ids.add(S["viewer"].lower())
        S["viewer_ids"] = sorted(ids)
    return set(S["viewer_ids"])


def viewer_key() -> str:
    """The signed-in person's Snowflake user name (or email), never the app's service user. Computed once."""
    if S.get("viewer_key") is None:
        key = ""
        try:
            u = st.user
            for c in (u.get("user_name"), u.get("email")):
                c = str(c or "").strip()
                if c and not re.search(r"streamlit|stplat|service|system", c, re.I):
                    key = c.upper()
                    break
        except Exception:
            pass
        S["viewer_key"] = key
    return S["viewer_key"]


# Actions that call Cortex on request. Viewing (load_page, narrative, enrich) is never limited.
AI_ACTIONS = {"route_prompt", "compose_layout", "recommend_layout", "suggest_bindings", "home_suggestions_ai",
              "tile_add", "tile_ask", "ask", "sb_draft", "metrics_redraft", "redraft", "build_draft",
              "page_regenerate", "page_add", "metric_define", "sb_suggest"}


def ai_limit_message(kind: str, payload: dict) -> str:
    """Empty when the action may run; otherwise the friendly message shown instead (per-person daily limit)."""
    if kind not in AI_ACTIONS or not (config.AI_DAILY_LIMIT or config.AGENT_DAILY_LIMIT):
        return ""
    who = viewer_key()
    if not who:
        return ""                                     # cannot tell people apart: the Snowflake budget still applies
    if kind == "tile_ask" and TITLE_EDIT.match(str(payload.get("text") or "")):
        return ""                                     # a rename uses no AI
    try:
        used = store.ai_usage_today(who)
    except Exception:
        return ""                                     # never block work because the count failed
    if kind == "ask" and config.AGENT_DAILY_LIMIT and used["agent"] >= config.AGENT_DAILY_LIMIT:
        return (f"You've reached today's limit of {config.AGENT_DAILY_LIMIT} agent questions. "
                "It resets tomorrow; ask your admin if you need more.")
    if config.AI_DAILY_LIMIT and used["all"] >= config.AI_DAILY_LIMIT:
        return (f"You've reached today's limit of {config.AI_DAILY_LIMIT} AI requests. Dashboards still open and "
                "refresh as usual; building with AI resets tomorrow. Ask your admin if you need more.")
    return ""


def can_share(d) -> bool:
    """Only the person who published a dashboard changes who it is shared with."""
    return bool((d.get("published_by") or "").lower() in viewer_ids())


def visible_published():
    ids = viewer_ids()
    out = []
    for d in S["published"]:
        users = {u.strip().lower() for u in (d.get("shared_users") or [])}
        if not users or not ids or users & ids or can_share(d):
            out.append(d)
    return out


def portal_roles() -> list:
    def load():
        rows = session.sql("SHOW ROLES").collect()
        names = {str(row_dict(r).get("name")) for r in rows if row_dict(r).get("name")}
        return sorted(n for n in names if n not in ("ACCOUNTADMIN", "ORGADMIN", "SECURITYADMIN", "USERADMIN", "SYSADMIN"))[:200]
    try:
        return shared("roles", load)
    except Exception:
        return []


def save_sharing(did: str) -> None:
    """Portal Share panel: grant the chosen roles the portal and record who this dashboard is shared with."""
    d = next((x for x in S["published"] if x["dashboard_id"] == did), None)
    if not d or not can_share(d):
        S["portal_flash"] = "Only the person who published this dashboard can change who it is shared with."
        return
    roles = [str(r).upper() for r in (st.session_state.get(f"pt_roles_{did}") or [])
             if re.fullmatch(r"[A-Za-z_][A-Za-z0-9_$]*", str(r))][:20]
    users = [u.strip() for u in str(st.session_state.get(f"pt_users_{did}") or "").split(",") if u.strip()][:50]
    granted, failed = [], []
    for r in roles:
        try:
            grant_portal(r)
            granted.append(r)
        except Exception as exc:
            failed.append(f"{r}: {str(exc)[:100]}")
    try:
        store.update_sharing(did, d["version"], roles, users)
    except Exception as exc:
        S["portal_flash"] = f"Could not save sharing: {str(exc)[:160]}"
        return
    S["published"] = store.list_published()
    S["_pub_at"] = time.time()
    S["portal_flash"] = (f"Sharing saved for '{d.get('name')}'."
                         + (f" Analytics Accelerator Portal access granted to {', '.join(granted)}." if granted else "")
                         + (f" Only these users see it: {', '.join(users)}." if users else "")
                         + (f" Could not grant: {'; '.join(failed)}" if failed else ""))


def open_published(p):
    d = next((x for x in S["published"] if x["dashboard_id"] == p.get("dashboard_id")), None)
    if not d:
        S["published"] = store.list_published()
        d = next((x for x in S["published"] if x["dashboard_id"] == p.get("dashboard_id")), None)
    if not d:
        raise ValueError("That dashboard is not published (or was removed).")
    select_source({"fqn": d["semantic_view"]})
    used = {str(x).upper() for x in re.findall(r'"(?:metric_id|metric2_id)":\s*"([^"]+)"', json.dumps(d["layout_spec"]))}
    known = {x.id.upper() for x in (model_obj().metrics if model_obj() else [])}
    if used - known:                                   # e.g. a custom metric saved after the model was cached
        forget_model(d["semantic_view"])
    S["bindings"] = Bindings.from_dict(d["bindings"]).as_dict()
    vs = dict(d.get("view_settings") or {})
    published_check = vs.pop("validation", None) or {}
    S["view"] = {**{"grain": None, "compare": "prior", "filters": {}}, **vs}
    set_audience({"audience": d["audience"]})
    apply_spec(d["layout_spec"])
    S["viewer_mode"] = True
    S["dashboard"] = {"dashboard_id": d["dashboard_id"], "version": d["version"], "name": d["name"],
                      "published": True, "published_at": d.get("published_at"), "published_by": d.get("published_by"),
                      "validation": published_check}


def exit_viewer(_p=None):
    S["viewer_mode"] = False
    S["step"] = "home"
    if PORTAL:                                   # back to the catalog, never to the builder Home
        S["dashboard"] = None
        try:
            st.query_params.clear()
        except Exception:
            pass


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
    changed = [e for e in entries if e.get("action") in ("repaired", "dropped")]
    if changed:     # never silently override the user: say what the validator changed and why
        S["notice"] = "Validator adjusted your change — " + "; ".join(e["reason"] for e in changed)[:400]


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
             if k in ("metric_id", "metric2_id", "dimension", "dimension2", "type", "width", "title", "metrics",
                      "show_trend", "display")}
    if "display" in patch:                        # visual only: bullet bars / variance with arrows / table
        if patch["display"] not in KPI_DISPLAYS:
            raise ValueError("Choose bullet bars, variance with arrows, or a variance table.")
        comp["display"] = patch.pop("display")
        S["spec"]["edited"] = True
        if not patch:
            return
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
    eng = Engine(session, m, b, prof, cortex(), store, qcache(), S["sql_log"], defer_ml=False, opts=S["view"])
    for page in S["spec"]["pages"]:
        for comp in page["components"]:
            cid = f"{page['page_id']}/{comp['component_id']}"
            res = S["results"].get(cid) or {}
            waiting = res.get("status") == "pending" or (res.get("data") or {}).get("insights_pending")
            if not waiting:
                continue
            started = time.time()
            eng._tile = cid
            try:
                data = getattr(eng, comp["type"])(comp)
                S.setdefault("tile_q", {})[cid] = list(dict.fromkeys((S["tile_q"].get(cid) or []) + eng.tile_keys.get(cid, [])))
                S.setdefault("facts", {}).setdefault(page["page_id"], []).extend(data.pop("_facts", []))
                data["headline"] = tile_headline(comp["type"], data, engine_fmt)
                S["results"][cid] = {"status": "ready", "data": data, "ms": int((time.time() - started) * 1000)}
            except Exception as exc:
                S["results"][cid] = {"status": "error", "error": str(exc)[:600]}


def refresh_workspace(_p=None):
    if S["spec"]:
        st.session_state.pop("_profiles", None)
        st.session_state.pop("_distinct", None)
        qcache().clear()
        apply_spec(S["spec"], (_p or {}).get("page_id"))


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
    V = S.get("validation")
    if V and page_id in (V.get("pages") or {}):        # QA-08 needs no queries: re-check the new summary at once
        V["pages"][page_id]["checks"] = [validation.narrative_check(out.get("text") or "", facts)]
        V["pages"][page_id].update(validation.page_summary(V, page_id))


# ------------------------------------------------------------------------------ validation (QA)
def _physical():
    """DESCRIBE SEMANTIC VIEW read for base tables, keys, relationships (once per view per session)."""
    fqn = sv_fqn()
    cache = st.session_state.setdefault("_physical", {})
    if fqn not in cache:
        try:
            cache[fqn] = (validation.Physical.describe(session, fqn), "")
        except Exception as exc:
            cache[fqn] = (None, f"Could not read the semantic view definition: {str(exc)[:200]}")
    return cache[fqn]


def _data_tiles(page):
    for comp in page["components"]:
        cid = f"{page['page_id']}/{comp['component_id']}"
        res = S["results"].get(cid) or {}
        if res.get("status") == "ready" and comp.get("state") != "omitted" and comp["type"] not in validation.NON_DATA:
            yield cid, res


VALIDATE_REFRESH_SECONDS = 600     # a data refresh alone (auto-refresh on live pages) re-validates at most this often


def _page_struct(page) -> str:
    """What the page shows, not the numbers: tiles, fields, filters, grain, compare."""
    body = json.dumps({"c": page["components"], "v": S["view"]}, sort_keys=True, default=str)
    return validation.hashlib.sha1(body.encode()).hexdigest()[:16]


def validation_stale(page) -> list:
    """Tiles on a page whose shown numbers have not been validated yet (new, edited, re-filtered or refreshed).
    A refresh that changes only the numbers re-validates at most every VALIDATE_REFRESH_SECONDS (cost guardrail)."""
    V = S.get("validation") or {}
    tiles = V.get("tiles") or {}
    filters = S["view"].get("filters") or {}
    stale = [cid for cid, res in _data_tiles(page)
             if (tiles.get(cid) or {}).get("sig") != validation.signature(res, filters)]
    pv = (V.get("pages") or {}).get(page["page_id"]) or {}
    if (stale and pv.get("struct") == _page_struct(page) and time.time() - pv.get("ts", 0) < VALIDATE_REFRESH_SECONDS
            and all(cid in tiles for cid in stale)):
        return []
    return stale


def validation_prune() -> None:
    """Drop results for tiles that no longer exist and refresh page counts (no queries)."""
    V = S.get("validation")
    if not V or not S.get("spec"):
        return
    live = {f"{p['page_id']}/{c['component_id']}" for p in S["spec"]["pages"] for c in p["components"]}
    for cid in [c for c in V.get("tiles", {}) if c not in live]:
        del V["tiles"][cid]
    pages = {p["page_id"] for p in S["spec"]["pages"]}
    for pid in list(V.get("pages", {})):
        if pid not in pages:
            del V["pages"][pid]
        else:
            V["pages"][pid].update(validation.page_summary(V, pid))


def _val_job():
    return st.session_state.get("_val_job")


def validation_needed() -> list:
    """Pages with tiles still to validate and no background run already covering them."""
    if not S.get("spec") or S.get("viewer_mode") or PORTAL:
        return []
    job = _val_job()
    busy = set(job["cids"]) - job["merged"] if job and job["running"] else set()
    return [p["page_id"] for p in S["spec"]["pages"] if set(validation_stale(p)) - busy]


def validate(p):
    """QA for the page on screen (or given tiles), in the BACKGROUND: the action returns at once."""
    page_id = p.get("page_id")
    page = next((x for x in (S["spec"] or {}).get("pages", []) if x["page_id"] == page_id), None)
    if not page:
        return
    if p.get("cids"):
        stale = {c for c in p["cids"] if c in dict(_data_tiles(page))}
    elif p.get("all"):
        stale = {cid for cid, _ in _data_tiles(page)}
    else:
        stale = set(validation_stale(page))
    _start_validation([page_id], stale, force=bool(p.get("all") or p.get("cids")))


def validate_all(p=None):
    """'Validate all pages': query pages never opened, then check every tile of every page in the background.
    force=True re-checks every tile even if its numbers did not change."""
    if not S.get("spec"):
        return
    for pg in S["spec"]["pages"]:
        if not any(k.startswith(pg["page_id"] + "/") for k in S["results"]):
            rebuild_pages([pg["page_id"]])
    force = bool((p or {}).get("force"))
    stale = set()
    for pg in S["spec"]["pages"]:
        stale |= {cid for cid, _ in _data_tiles(pg)} if force else set(validation_stale(pg))
    _start_validation([pg["page_id"] for pg in S["spec"]["pages"]], stale, force=force, all_pages=True)


def _start_validation(page_ids, stale, force=False, all_pages=False):
    job = _val_job()
    if job and job["running"]:
        if not force and set(page_ids) <= set(job["page_ids"]) and stale <= set(job["cids"]):
            return                                   # already being checked
        job["validator"].cancelled = True            # superseded: its results are dropped
    if not stale:
        return
    S["validation"] = S.get("validation") or {"tiles": {}, "pages": {}, "dashboard": []}
    m, b, prof = _profile_obj()
    eng = Engine(session, m, b, prof, None, store, dict(qcache()), [], defer_ml=True, opts=S["view"])
    phys, err = _physical()
    results = {cid: S["results"][cid] for cid in stale if cid in S["results"]}
    spec_copy = json.loads(json.dumps(S["spec"], default=str))
    tile_q = dict(S.get("tile_q") or {})
    cache = qcache()
    v = validation.Validator(session, eng, phys, err)
    pids = [pid for pid in page_ids if any(c.split("/")[0] == pid for c in stale)] or list(page_ids)
    job = {"id": validation.uuid.uuid4().hex[:12], "page_id": pids[0], "page_ids": pids, "all_pages": all_pages,
           "cids": sorted(stale), "running": True, "done": 0, "total": 0, "tiles": {}, "merged": set(), "rep": None,
           "error": "", "started": time.time(), "validator": v, "finalized": False}

    def progress(kind, data):
        if kind == "query":
            job["done"], job["total"] = data
        else:
            job["tiles"][data[0]] = data[1]

    def work():
        try:
            job["rep"] = v.run(spec_copy, pids, results, tile_q, cache, only=set(stale), progress=progress)
        except Exception as exc:                     # never leave tiles "checking" forever: record the failure
            job["error"] = f"Validation could not run: {str(exc)[:240]}"
        finally:
            job["running"] = False
    st.session_state["_val_job"] = job
    S["validation_job"] = {"page_id": pids[0], "page_ids": pids, "running": True, "done": 0, "total": 0,
                           "tiles_done": 0, "tiles_total": len(stale)}
    threading.Thread(target=work, name=f"aa-validate-{job['id']}", daemon=True).start()


def validation_merge(_p=None):
    """Bring finished tiles of the background run into the dashboard; finish the pages when the run is done."""
    job = _val_job()
    if not job or job["finalized"]:
        S["validation_job"] = None
        return
    V = S["validation"] = S.get("validation") or {"tiles": {}, "pages": {}, "dashboard": []}
    for cid, t in list(job["tiles"].items()):
        if cid not in job["merged"]:
            V["tiles"][cid] = t
            job["merged"].add(cid)
    S["validation_job"] = {"page_id": job["page_id"], "page_ids": job["page_ids"], "running": job["running"],
                           "done": job["done"], "total": job["total"], "tiles_done": len(job["merged"]),
                           "tiles_total": len(job["cids"])}
    if job["running"]:
        return
    job["finalized"] = True
    S["validation_job"] = None
    if job["validator"].cancelled:
        return
    rep = job["rep"] or {"dashboard": V.get("dashboard") or [], "queries": 0, "run_id": "",
                         "at": dt.datetime.now().strftime("%Y-%m-%d %H:%M")}
    filters = S["view"].get("filters") or {}
    for cid in job["cids"]:                          # a tile the run could not finish still gets an honest entry
        if cid not in job["merged"]:
            res = S["results"].get(cid) or {}
            V["tiles"][cid] = {"status": "na", "sig": validation.signature(res, filters), "page_id": cid.split("/")[0],
                               "title": cid, "checks": [validation.check("QA-01", "na", job["error"] or "Tile has no data to check.")]}
    if rep.get("dashboard"):
        V["dashboard"] = rep["dashboard"]
    if rep.get("lineage"):
        old = V.get("lineage") or {}
        joins = {j["name"]: j for j in (old.get("joins") or []) + (rep["lineage"].get("joins") or [])}
        V["lineage"] = {"view": rep["lineage"].get("view") or old.get("view"),
                        "tables": sorted(set(old.get("tables") or []) | set(rep["lineage"].get("tables") or [])),
                        "joins": list(joins.values()), "nonadd_from_ddl": rep["lineage"].get("nonadd_from_ddl") or []}
    V["at"], V["queries"] = rep["at"], rep.get("queries", 0)
    V["seconds"] = round(time.time() - job["started"], 1)
    apply_resolutions()
    for page_id in job["page_ids"]:
        page = next((x for x in (S.get("spec") or {}).get("pages", []) if x["page_id"] == page_id), None)
        if not page:
            continue
        nar = (S.get("narratives") or {}).get(page_id)
        V.setdefault("pages", {})[page_id] = {"checks": [validation.narrative_check(nar.get("text") or "", nar.get("facts") or [])]
                                              if nar else []}
        V["pages"][page_id].update(validation.page_summary(V, page_id), at=rep["at"], ts=time.time(),
                                   struct=_page_struct(page), seconds=V["seconds"])
        page_tiles = {k: v for k, v in V["tiles"].items() if v.get("page_id") == page_id}
        store.save_validation(rep.get("run_id") or job["id"], (S.get("dashboard") or {}).get("dashboard_id") or "", sv_fqn(),
                              page_id, V["pages"][page_id], rep.get("queries", 0),
                              {"page": page["label"], "tiles": page_tiles, "dashboard": V["dashboard"],
                               "page_checks": V["pages"][page_id]["checks"], "filters": filters,
                               "lineage": V.get("lineage"), "seconds": V["seconds"],
                               "calendar": (S.get("profile") or {}).get("calendar")})
    S["validation_history"] = store.validation_history(sv_fqn(), (S.get("dashboard") or {}).get("dashboard_id") or "")


# -- resolutions: every finding ends fixed, accepted (with a reason) or owned ------------------------------------------
def apply_resolutions() -> None:
    """Mark tiles whose open findings are all accepted / owned (same numbers, not expired) as 'accepted'."""
    V = S.get("validation")
    if not V:
        return
    today = dt.date.today().isoformat()
    by_tile = {}
    for r in S.get("val_resolutions") or []:
        by_tile.setdefault(r["tile_key"], []).append(r)
    for cid, t in V.get("tiles", {}).items():
        t.pop("status_eff", None)
        t.pop("resolution", None)
        if t.get("status") not in ("mismatch", "review"):
            continue
        live = [r for r in by_tile.get(cid, []) if (r.get("tile_sig") or "") == t.get("sig")
                and (not r.get("expires_at") or str(r["expires_at"]) >= today)]
        if live:
            t["status_eff"] = "accepted"
            t["resolution"] = live[0]
    for pid in list((V.get("pages") or {})):
        V["pages"][pid].update(validation.page_summary(V, pid))


def validation_open(_p=None):
    """Validation tab opened: run history and resolutions (two small reads)."""
    did = (S.get("dashboard") or {}).get("dashboard_id") or ""
    S["validation_history"] = store.validation_history(sv_fqn(), did)
    S["val_resolutions"] = store.list_resolutions(sv_fqn(), did)
    S["uat_entries"] = store.list_uat(sv_fqn(), did)
    apply_resolutions()
    uat_inbox_refresh()


# ------------------------------------------------------------------------------ UAT (acceptance + sign-off)
def _is_data_tile(page, comp) -> bool:
    return comp.get("state") != "omitted" and comp["type"] not in validation.NON_DATA


def uat_overview() -> dict:
    V = S.get("validation") or {}
    tiles = {cid: {**t, "status_eff": validation.eff(t)} for cid, t in (V.get("tiles") or {}).items()}
    return uat.status(S.get("spec") or {}, tiles, S.get("uat_entries") or [], _is_data_tile)


def _uat_names(cid: str = "", page_id: str = "") -> dict:
    """Dashboard, page and tile names stored with each sign-off row, so the cross-dashboard lists can show them."""
    spec = S.get("spec") or {}
    pid = page_id or cid.split("/")[0]
    pg = next((x for x in spec.get("pages") or [] if x["page_id"] == pid), {}) or {}
    comp = next((c for c in pg.get("components") or [] if f"{pid}/{c['component_id']}" == cid), {}) if cid else {}
    return {"dashboard_name": (S.get("dashboard") or {}).get("name") or spec.get("display_name") or "",
            "page_label": pg.get("label") or "", "tile_title": (comp or {}).get("title") or ""}


def _uat_save(**e):
    did = (S.get("dashboard") or {}).get("dashboard_id") or ""
    store.save_uat({"dashboard_id": did, "sv": sv_fqn(), "run_at": (S.get("validation") or {}).get("at"),
                    **_uat_names(e.get("tile_key") or "", e.get("page_id") or ""), **e})
    S["uat_entries"] = store.list_uat(sv_fqn(), did)
    uat_inbox_refresh()


def uat_load_entries():
    """Sign-off rows of the dashboard on screen (tile notes, Validation tab)."""
    try:
        S["uat_entries"] = store.list_uat(sv_fqn(), (S.get("dashboard") or {}).get("dashboard_id") or "")
    except Exception:
        S["uat_entries"] = []


def uat_inbox_refresh(_p=None):
    """Change requests and fixes waiting for re-check on every saved dashboard (one small read)."""
    try:
        owners_set = store.list_settings("owner:")
        owners = {d["dashboard_id"]: {"name": d.get("name") or "",
                                      "owner": owners_set.get(f"owner:{d['dashboard_id']}") or d.get("owner")
                                      or d.get("created_by") or ""}
                  for d in S.get("dashboards") or []}
        S["uat_inbox"] = {**uat.inbox(store.list_uat_tiles(), owners, viewer_key()), "me": viewer_key(),
                          "owners": {k: v["owner"] for k, v in owners.items()}}
    except Exception as exc:
        S["uat_inbox"] = {"rows": [], "closed_30d": 0, "badge_requests": 0, "badge_recheck": 0, "error": str(exc)}


def uat_owner(p):
    """Hand a dashboard's change requests to another builder (the owner is its creator until handed over)."""
    did = str(p.get("dashboard_id") or "")
    owner = str(p.get("owner") or "").strip().upper()[:200]
    if not did or not owner:
        raise ValueError("Choose the dashboard and type the new owner's Snowflake user name.")
    store.set_setting(f"owner:{did}", owner)
    uat_inbox_refresh()
    S["notice"] = f"Change requests for this dashboard now go to {owner}."


def uat_open(p):
    """Open tile ->: open the dashboard (if another one is on screen), go to the page and point at the tile."""
    did, cid = str(p.get("dashboard_id") or ""), str(p.get("cid") or "")
    if (S.get("dashboard") or {}).get("dashboard_id") != did:
        open_dashboard({"dashboard_id": did})
    S["step"] = "workspace"
    pid = cid.split("/")[0]
    if not any(pg["page_id"] == pid for pg in (S.get("spec") or {}).get("pages") or []):
        raise ValueError("That tile is no longer on the dashboard (the page was removed).")
    S["focus_page"] = pid
    S["uat_focus"] = {"cid": cid, "id": f"{time.time():.3f}"}
    uat_load_entries()


def _uat_row(cid: str):
    return next((r for pg in uat_overview()["pages"] for r in pg["tiles"] if r["cid"] == cid), None)


def uat_builder(p):
    """The builder answers a change request: Mark as fixed (note optional) or Reply (text required)."""
    cid = str(p.get("cid") or "")
    row = _uat_row(cid)
    if not row:
        raise ValueError("Unknown tile.")
    comment = str(p.get("comment") or "").strip()[:2000]
    decision = uat.check_builder(str(p.get("decision") or ""), comment, row["state"])
    t = ((S.get("validation") or {}).get("tiles") or {}).get(cid) or {}
    _uat_save(kind="tile", page_id=cid.split("/")[0], tile_key=cid, decision=decision, comment=comment,
              tile_sig=t.get("sig") or "", validation_status=validation.eff(t) if t else "none")
    S["notice"] = ("Marked as fixed. The reviewer sees it in Waiting for my sign-off."
                   if decision == "fixed" else "Reply sent to the reviewer.")


def uat_tile(p):
    """Reviewer accepts or rejects a tile: does it answer its business question? Tied to the numbers they saw."""
    cid = str(p.get("cid") or "")
    t = ((S.get("validation") or {}).get("tiles") or {}).get(cid)
    if not t:
        raise ValueError("Validate this tile first, then accept it.")
    comment = str(p.get("comment") or "").strip()[:2000]
    vstat = validation.eff(t)
    decision = uat.check_tile(str(p.get("decision") or ""), comment, vstat)
    _uat_save(kind="tile", page_id=cid.split("/")[0], tile_key=cid, decision=decision, comment=comment,
              tile_sig=t.get("sig") or "", validation_status=vstat)
    S["notice"] = ("Marked as looks right. It re-opens if the numbers change." if decision == "accepted" else
                   "Change requested. The builder sees it in Change requests.")


def uat_page(p):
    """Page sign-off. Never blocked: with open findings or tiles not accepted it needs a reason (Approved with notes)."""
    ov = uat_overview()
    pg = next((x for x in ov["pages"] if x["page_id"] == p.get("page_id")), None)
    if not pg:
        raise ValueError("Unknown page.")
    comment = str(p.get("comment") or "").strip()[:2000]
    decision = uat.check_page(str(p.get("decision") or ""), comment, pg)
    _uat_save(kind="page", page_id=pg["page_id"], decision=decision, comment=comment, page_sig=pg["sig"],
              validation_status=f"{pg['open_findings']} open finding(s); {pg['accepted']}/{pg['total']} tiles accepted")
    S["notice"] = f"Page '{pg['label']}': {uat.PAGE_LABEL[decision]}."


def uat_requirement(p):
    """Optional requirement / BRD reference per tile, kept with the dashboard layout."""
    cid = str(p.get("cid") or "")
    if not S.get("spec") or "/" not in cid:
        raise ValueError("Unknown tile.")
    req = S["spec"].setdefault("requirements", {})
    text = str(p.get("text") or "").strip()[:300]
    if text:
        req[cid] = text
    else:
        req.pop(cid, None)
    S["spec"]["edited"] = True


def uat_download(p):
    """The UAT pack in the corporate workbook format, filled from the validation run and the in-app sign-offs."""
    V = S.get("validation") or {}
    if not V.get("tiles"):
        raise ValueError("Validate the dashboard first (Validate all pages).")
    spec = S.get("spec") or {}
    ov = uat_overview()
    cal = (S.get("profile") or {}).get("calendar") or {}
    dates = sorted(str(e.get("created_at") or "")[:10] for e in S.get("uat_entries") or [] if e.get("created_at"))
    today = dt.date.today()
    started = dt.date.fromisoformat(dates[0]) if dates else today
    name = (S.get("dashboard") or {}).get("name") or spec.get("display_name") or "Dashboard"
    did = (S.get("dashboard") or {}).get("dashboard_id") or ""
    flt = "; ".join(f"{k.split('.')[-1]} = {', '.join(map(str, v))}" for k, v in (S["view"].get("filters") or {}).items())
    meta = {"title": f"{name} – Dashboard UAT",
            "reference": str(p.get("reference") or "").strip()[:60] or (f"{did} v{(S.get('dashboard') or {}).get('version', '')}" if did else "draft"),
            "testers": str(p.get("testers") or "").strip()[:200] or (S.get("viewer") or ""),
            "recipients": str(p.get("recipients") or "").strip()[:300] or "—",
            "environment": f"Snowflake – {config.APP_SCHEMA.split('.')[0]} (Analytics Accelerator)",
            "semantic_view": sv_fqn(), "base_tables": (V.get("lineage") or {}).get("tables") or [],
            "period": cal.get("current_label") or "", "filters": flt or "No filters",
            "description": "Automatic validation of every tile against the base tables (QA-01 to QA-08) and in-app "
                           "acceptance by the reviewer, exported from the Analytics Accelerator.",
            "started": started, "completed": today, "goal": spec.get("goal") or spec.get("summary") or "",
            "reviewer": ", ".join(sorted({x["signed_by"] for x in ov["pages"] if x.get("signed_by")})) or "",
            "history": S.get("uat_entries") or []}
    report = {"tiles": V.get("tiles") or {}, "dashboard": V.get("dashboard") or [], "lineage": V.get("lineage") or {}}
    data = uat_export.build(spec, report, meta, uat_status=ov)
    safe = re.sub(r"[^A-Za-z0-9_-]+", "_", name)[:60]
    S["download"] = {"name": f"{safe}_UAT_{today:%Y%m%d}.xlsx",
                     "mime": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                     "b64": base64.b64encode(data).decode(), "id": f"{time.time():.3f}"}
    S["notice"] = "UAT pack ready: the download starts in your browser."


# ------------------------------------------------------------------------------ data alerts (email)
def _alert_model(sv: str):
    """The semantic view an alert watches: the one on screen, or described once for an alert of another view."""
    if S.get("source") and S["source"]["fqn"] == sv:
        return model_obj()
    cache = st.session_state.setdefault("_alert_models", {})
    if sv not in cache:
        base, _, table = sv.partition("#")
        m = describe_semantic_view(session, base)
        cache[sv] = scope_model(m, table) if table else m
    return cache[sv]


def _alert_values(m) -> dict:
    """Values of each filterable dimension (for the form and to check Cortex's reading); cached per view."""
    cache = st.session_state.setdefault("_alert_values", {})
    if m.fqn not in cache:
        q = SemanticQuery(session, m, S["sql_log"])
        out = {}
        for d in list(m.categorical_dimensions)[:20]:
            try:
                out[d.id] = distinct_values(q, d.id, 60)
            except Exception:
                continue
        cache[m.fqn] = out
    return cache[m.fqn]


def _alert_kinds(m) -> dict:
    """percent / currency / number per metric, measured once on the data: a ratio-looking name (GROSS_MARGIN)
    is only a percentage when its value is a fraction."""
    cache = st.session_state.setdefault("_alert_kinds", {})
    if m.fqn not in cache:
        from engine import PERCENT, fmt_kind
        q = SemanticQuery(session, m, S["sql_log"])
        out = {}
        for f in m.metrics:
            if not PERCENT.search(f.name):
                out[f.id] = fmt_kind(f.name)
                continue
            try:
                r = q.run("SELECT * FROM " + q.sv([], [f"{f.ref} AS V"]))
                v = r[0].get("v") if r else None
                out[f.id] = fmt_kind(f.name, None if v is None else float(v))
            except Exception:
                out[f.id] = fmt_kind(f.name)
        cache[m.fqn] = out
    return cache[m.fqn]


def _alert_time(m) -> str:
    if S.get("source") and S["source"]["fqn"] == m.fqn and (S.get("bindings") or {}).get("time_dimension"):
        return S["bindings"]["time_dimension"]
    return infer_bindings(m).time_dimension


def _viewer_email() -> str:
    try:
        e = str(st.user.get("email") or "")
        return e if alerts.EMAIL.match(e) else ""
    except Exception:
        return ""


def _alert_draft(spec_in: dict, editing: str = "", text: str = "", question: str = "", provenance: str = "",
                 preview=None, sv: str = ""):
    sv = sv or spec_in.get("sv") or (S.get("source") or {}).get("fqn") or ""
    if not sv:
        raise ValueError("Open a dashboard first: alerts watch the semantic view behind it.")
    m = _alert_model(sv)
    vals = _alert_values(m)
    kinds = _alert_kinds(m)
    spec, issues = alerts.normalize(m, spec_in, vals, _alert_time(m), kinds=kinds)
    S["alert_draft"] = {"spec": spec, "issues": issues, "sentence": alerts_core.describe(spec) if spec.get("metric") else "",
                        "schedule_text": alerts_core.schedule_text(spec.get("schedule")),
                        "options": alerts.options(m, vals, kinds), "editing": editing, "text": text, "question": question,
                        "provenance": provenance, "preview": preview}
    return m, spec, issues


def _open_drawer(name: str):
    S["open_drawer"] = {"name": name, "id": f"{time.time():.3f}"}


def alert_new(p):
    """Alert me… on a tile: the tile's metric and the dashboard's filters, the signed-in person's email."""
    seed = {"filters": {k: list(v) for k, v in ((S.get("view") or {}).get("filters") or {}).items() if v},
            "recipients": [e for e in [_viewer_email()] if e],
            "schedule": {"freq": "daily", "hour": 8, "tz": str(p.get("tz") or "UTC")[:60]},
            "dashboard_id": (S.get("dashboard") or {}).get("dashboard_id") or "",
            "dashboard_name": (S.get("dashboard") or {}).get("name") or (S.get("spec") or {}).get("display_name") or ""}
    comp = None
    if p.get("page_id") and p.get("component_id"):
        try:
            comp = _find(p["page_id"], p["component_id"])[1]
        except Exception:
            comp = None
    if comp:
        seed["metric"] = comp.get("metric_id") or (comp.get("metrics") or [None])[0]
    else:
        seed["metric"] = (S.get("bindings") or {}).get("primary_metric")
    _alert_draft(seed)
    _open_drawer("alert")


def alert_update(p):
    d = S.get("alert_draft") or {}
    _alert_draft(p.get("spec") or {}, d.get("editing", ""), d.get("text", ""), "", d.get("provenance", ""))


def alert_parse(p):
    """Plain English -> alert fields (Cortex reads, normalize() checks every part against the semantic view)."""
    d = S.get("alert_draft") or {}
    cur = dict(p.get("spec") or d.get("spec") or {})
    text = str(p.get("text") or "").strip()[:600]
    if not text:
        raise ValueError("Type what you want to be alerted about.")
    started = time.time()
    m = _alert_model(cur.get("sv") or (S.get("source") or {}).get("fqn") or "")
    opts = alerts.options(m, _alert_values(m), _alert_kinds(m))
    try:
        cx = cortex()
    except Exception:
        cx = None
    fields, question, prov = alerts.parse_text(cx, opts, text, {"metric": cur.get("metric")})
    merged = {**cur, **{k: v for k, v in fields.items() if v not in (None, "", [], {})}}
    merged["recipients"] = list(dict.fromkeys((cur.get("recipients") or []) + (fields.get("recipients") or [])))
    if fields.get("schedule"):
        merged["schedule"] = {**(cur.get("schedule") or {}), **fields["schedule"]}
    if "filters" in fields:
        merged["filters"] = fields.get("filters") or {}
    _alert_draft(merged, d.get("editing", ""), text, question, prov)
    log_ai("alert_parse", text, json.dumps(fields)[:3900], prov, "valid" if not S["alert_draft"]["issues"] else "partial",
           started)


def _alert_check(spec_in: dict):
    d = S.get("alert_draft") or {}
    m, spec, issues = _alert_draft(spec_in, d.get("editing", ""), d.get("text", ""), d.get("question", ""),
                                   d.get("provenance", ""))
    blocking = [i for i in issues if "email" not in i.lower()]
    if not spec.get("metric") or blocking:
        raise ValueError("Before testing: " + " ".join(blocking or issues or ["Choose the metric to watch."]))
    sql = alerts.check_sql(m, spec)
    rows = SemanticQuery(session, m, S["sql_log"]).run(sql)
    res = alerts_core.evaluate(spec, rows)
    S["alert_draft"]["preview"] = {**res, "value_text": alerts_core.fmt(res.get("value"), spec.get("kind"))}
    return m, spec, issues, sql, res


def alert_preview(p):
    _alert_check(p.get("spec") or (S.get("alert_draft") or {}).get("spec") or {})


def alert_test(p):
    m, spec, issues, sql, res = _alert_check(p.get("spec") or (S.get("alert_draft") or {}).get("spec") or {})
    if not spec.get("recipients"):
        raise ValueError("Add at least one email address.")
    subj, body = alerts_core.email(spec, res, test=True, app_url=getattr(config, "PORTAL_URL", ""))
    try:
        integ = alerts_core.send_email(session, config.APP_SCHEMA, spec["recipients"], subj, body)
    except Exception as exc:
        raise ValueError(f"Snowflake could not send the email: {str(exc)[:300]} — email needs the admin setup "
                         "(setup\\admin_alerts_email.sql): the notification integration, and each recipient's email "
                         "verified on their Snowflake user.")
    S["notice"] = f"Test email sent to {', '.join(spec['recipients'])} through {integ}."


def alert_save(p):
    d = S.get("alert_draft") or {}
    m, spec, issues = _alert_draft(p.get("spec") or d.get("spec") or {}, d.get("editing", ""), d.get("text", ""),
                                   d.get("question", ""), d.get("provenance", ""), d.get("preview"))
    if issues:
        raise ValueError("Fix before saving: " + " ".join(issues))
    aid = store.save_alert(spec, alerts.check_sql(m, spec), d.get("editing", ""))
    S["alert_draft"] = None
    alerts_open()
    _open_drawer("alerts")
    S["notice"] = (f"Alert {'updated' if d.get('editing') else 'created'}: {alerts_core.describe(spec)}. "
                   f"{alerts_core.schedule_text(spec['schedule'])}." + ("" if (S["alerts"]["setup"] or {}).get("task_on")
                   else " Scheduled checks start once the hourly schedule is on (My alerts)."))
    return aid


def alert_edit(p):
    a = next((x for x in store.list_alerts() if x["alert_id"] == p.get("alert_id")), None)
    if not a:
        raise ValueError("Alert not found.")
    _alert_draft(a["spec"], a["alert_id"])
    _open_drawer("alert")


def _alert_setup() -> dict:
    out = {"integration": alerts_core.integration_name(session, config.APP_SCHEMA), "integration_found": None,
           "task_on": False, "task_state": ""}
    try:
        names = [str(row_dict(r).get("name") or "").upper() for r in session.sql("SHOW NOTIFICATION INTEGRATIONS").collect()]
        out["integration_found"] = out["integration"].upper() in names
        out["integrations"] = names[:20]
    except Exception as exc:
        out["integration_error"] = str(exc)[:200]
    try:
        rows = session.sql(f"SHOW TASKS LIKE 'AA_ALERTS_TASK' IN SCHEMA {config.APP_SCHEMA}").collect()
        st_ = str(row_dict(rows[0]).get("state") or "") if rows else ""
        out["task_state"], out["task_on"] = st_, st_.lower() == "started"
    except Exception:
        pass
    if rows_task_exists(out):                     # keep the scheduled checker on the same code as this app version
        try:
            if ((store.get_setting("alert_proc_version") or {}).get("setting_value") or "") != alerts_core.CORE_VERSION:
                session.sql(alerts.proc_ddl(config.APP_SCHEMA, getattr(config, "PORTAL_URL", ""))).collect()
                store.set_setting("alert_proc_version", alerts_core.CORE_VERSION)
        except Exception as exc:
            out["proc_error"] = str(exc)[:200]
    return out


def rows_task_exists(setup: dict) -> bool:
    return bool(setup.get("task_state"))


def alerts_open(_p=None):
    items = store.list_alerts()
    for a in items:
        sp = a.get("spec") or {}
        a["sentence"] = alerts_core.describe(sp) if sp.get("metric") else a.get("name")
        a["schedule_text"] = alerts_core.schedule_text(sp.get("schedule"))
        a["value_text"] = alerts_core.fmt(a.get("last_value"), sp.get("kind")) if a.get("last_value") is not None else ""
        a["recipients"] = sp.get("recipients") or []
    S["alerts"] = {"items": items, "setup": _alert_setup(), "runs": (S.get("alerts") or {}).get("runs") or {},
                   "firing": sum(1 for a in items if a.get("active") and a.get("last_status") == "fired")}


def alert_runs(p):
    aid = str(p.get("alert_id") or "")
    if S.get("alerts") is None:
        alerts_open()
    S["alerts"]["runs"][aid] = store.alert_runs(aid)


def alert_toggle(p):
    store.set_alert(str(p.get("alert_id") or ""), active=bool(p.get("active")))
    alerts_open()


def alert_delete(p):
    store.set_alert(str(p.get("alert_id") or ""), deleted=True)
    alerts_open()
    S["notice"] = "Alert deleted."


def alert_run(p):
    """Check now: one alert or all of them, right away (emails the ones that fire, once per period)."""
    aid = str(p.get("alert_id") or "") or None
    out = alerts_core.run_alerts(session, config.APP_SCHEMA, only_id=aid, force=True, trigger="manual",
                                 app_url=getattr(config, "PORTAL_URL", ""))
    alerts_open()
    if aid:
        S["alerts"]["runs"][aid] = store.alert_runs(aid)
    fired = [x for x in out if x["fired"]]
    mailed = [x for x in out if x["emailed"]]
    notes = [x["note"] for x in out if x.get("note") and "Already" not in x["note"]]
    S["notice"] = (f"Checked {len(out)} alert(s): {len(fired)} fired, {len(mailed)} emailed."
                   + (f" {notes[0]}" if notes else ""))


def alert_schedule(_p=None):
    """Install the checker procedure and the hourly task (needs CREATE PROCEDURE/TASK; EXECUTE TASK to resume)."""
    try:
        session.sql(alerts.proc_ddl(config.APP_SCHEMA, getattr(config, "PORTAL_URL", ""))).collect()
        for q in alerts.task_ddl(config.APP_SCHEMA, config.AGENT_WAREHOUSE):
            session.sql(q).collect()
        store.set_setting("alert_proc_version", alerts_core.CORE_VERSION)
    except Exception as exc:
        alerts_open()
        raise ValueError(f"The hourly schedule could not be turned on: {str(exc)[:240]}. This needs the EXECUTE TASK "
                         "privilege for the app's role; an admin can grant it with setup\\admin_alerts_email.sql.")
    alerts_open()
    S["notice"] = "Hourly schedule is on: Snowflake task AA_ALERTS_TASK checks every alert when it is due."


def alert_integration(p):
    name = re.sub(r"[^A-Za-z0-9_$.]", "", str(p.get("name") or ""))[:120]
    if not name:
        raise ValueError("Type the notification integration's name.")
    store.set_setting("alert_email_integration", name)
    alerts_open()


def val_resolve(p):
    """Accept a finding with a reason (expires; re-opens if the numbers change) or hand it to an owner as a data issue."""
    cid, action = str(p.get("cid") or ""), p.get("action")
    V = S.get("validation") or {}
    t = (V.get("tiles") or {}).get(cid)
    if not t or action not in ("accept", "issue"):
        raise ValueError("Pick a finding to resolve.")
    reason = str(p.get("reason") or "").strip()
    if not reason:
        raise ValueError("A reason is required.")
    bad = next((c for c in t["checks"] if c["status"] == t["status"]), {})
    did = (S.get("dashboard") or {}).get("dashboard_id") or ""
    decision_id = ""
    if action == "issue":
        diag = bad.get("diagnosis") or {}
        decision_id = store.add_decision(sv_fqn(), "validation", f"Data issue: {t.get('title')}"[:300],
                                         (reason + "\n\n" + (diag.get("explain") or bad.get("summary") or ""))[:4000],
                                         str(p.get("owner") or "")[:120], str(p.get("due") or "") or None,
                                         {"tile": cid, "check": bad.get("id"), "summary": bad.get("summary"),
                                          "diagnosis": diag, "sql": bad.get("sql")})
        S["decisions"] = store.list_decisions(sv_fqn())
    days = int(p.get("days") or 30) if action == "accept" else 0
    expires = (dt.date.today() + dt.timedelta(days=days)).isoformat() if days else ""
    store.save_resolution({"dashboard_id": did, "sv": sv_fqn(), "tile_key": cid, "title": t.get("title"),
                           "check_id": bad.get("id"), "action": "accepted" if action == "accept" else "data_issue",
                           "reason": reason, "owner": p.get("owner"), "due": p.get("due"), "expires": expires,
                           "sig": t.get("sig"), "decision_id": decision_id})
    S["val_resolutions"] = store.list_resolutions(sv_fqn(), did)
    apply_resolutions()
    S["notice"] = ("Finding accepted with your reason. It re-opens if the numbers change"
                   + (f" or after {days} days." if days else ".")) if action == "accept" else \
                  "Data issue logged in Decisions with an owner. The finding stays visible until it is fixed."


def validation_overview() -> dict:
    """Dashboard-level picture for the Validation tab (no queries)."""
    V = S.get("validation") or {}
    spec = S.get("spec") or {}
    pages, issues, counts, compared = [], [], {"pass": 0, "accepted": 0, "review": 0, "mismatch": 0, "na": 0}, 0
    for pg in spec.get("pages") or []:
        pv = (V.get("pages") or {}).get(pg["page_id"])
        data_cids = [f"{pg['page_id']}/{c['component_id']}" for c in pg["components"]
                     if c.get("state") != "omitted" and c["type"] not in validation.NON_DATA]
        rows = []
        for c in pg["components"]:
            cid = f"{pg['page_id']}/{c['component_id']}"
            t = (V.get("tiles") or {}).get(cid)
            if cid not in data_cids:
                continue
            st_ = validation.eff(t) if t else "none"
            if t:
                counts[st_] = counts.get(st_, 0) + 1
                compared += sum(int(x.get("compared") or 0) for x in t["checks"] if x["id"] == "QA-01")
            cells = {x["id"]: x.get("status") for x in (t or {}).get("checks", [])}
            if t:                                    # joins and periods are checked once per dashboard
                for x in V.get("dashboard") or []:
                    if x["id"] in ("QA-04", "QA-05"):
                        cells.setdefault(x["id"], x["status"])
            rows.append({"cid": cid, "title": c.get("title") or c["type"], "status": st_, "cells": cells})
            if t and t["status"] in ("mismatch", "review"):
                bad = next((x for x in t["checks"] if x["status"] == t["status"]), {})
                issues.append({"cid": cid, "page_id": pg["page_id"], "page": pg["label"], "title": c.get("title"),
                               "status": st_, "raw_status": t["status"], "check": bad.get("id"), "check_name": bad.get("name"),
                               "summary": bad.get("summary"), "diagnosis": bad.get("diagnosis"),
                               "resolution": t.get("resolution")})
        for x in (pv or {}).get("checks") or []:
            if x["status"] in ("mismatch", "review"):
                issues.append({"cid": "", "page_id": pg["page_id"], "page": pg["label"], "title": "AI summary",
                               "status": x["status"], "raw_status": x["status"], "check": x["id"], "check_name": x["name"],
                               "summary": x["summary"], "diagnosis": None, "resolution": None})
        pages.append({"page_id": pg["page_id"], "label": pg["label"], "checked": bool(pv), "status": (pv or {}).get("status"),
                      "tiles": rows})
    for x in V.get("dashboard") or []:
        if x["status"] in ("mismatch", "review"):
            issues.append({"cid": "", "page_id": "", "page": "Data", "title": x["name"], "status": x["status"],
                           "raw_status": x["status"], "check": x["id"], "check_name": x["name"], "summary": x["summary"],
                           "diagnosis": None, "resolution": None})
    issues.sort(key=lambda i: -validation.RANK.get(i["status"], 0))
    statuses = [p["status"] for p in pages if p["status"]]
    checked = sum(1 for p in pages if p["checked"])
    status = validation.worst(statuses) if statuses else "none"
    return {"status": status, "label": validation.LABEL.get(status, "Not validated"), "counts": counts,
            "pages_checked": checked, "pages_total": len(pages), "pages": pages, "issues": issues,
            "values_compared": compared, "queries": V.get("queries"), "at": V.get("at"), "seconds": V.get("seconds"),
            "lineage": V.get("lineage") or {}, "dashboard_checks": V.get("dashboard") or [],
            "checks": [{"id": k, "name": n} for k, (n, _) in validation.CHECKS.items() if k != "QA-08"]}


def validation_brief() -> dict:
    """What publish stores with the version, so viewers see 'Verified' without re-running anything."""
    V = S.get("validation") or {}
    pages = V.get("pages") or {}
    if not pages:
        return {}
    statuses = [x.get("status") for x in pages.values()]
    counts = {k: sum((x.get("counts") or {}).get(k, 0) for x in pages.values())
              for k in ("pass", "accepted", "review", "mismatch", "na")}
    status = validation.worst(statuses)
    return {"status": status, "label": validation.LABEL[status], "counts": counts, "at": V.get("at"),
            "pages_checked": len(pages), "pages_total": len((S.get("spec") or {}).get("pages") or [])}


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


def pick_agent(agents):
    """Prefer the app-owned domain agent, then any agent that already has a document-search tool."""
    if not agents:
        return None
    owned = [a for a in agents if a["fqn"].upper().startswith(config.APP_SCHEMA.upper() + ".")]
    return (owned or sorted(agents, key=lambda a: not a.get("has_search")))[0]


def search_service_for(fqn: str) -> str:
    return config.SEARCH_SERVICES.get((fqn or "").upper(), "")


def create_agent_action(_p):
    title = S["source"]["name"].replace("_", " ").title()
    args = dict(warehouse=agent_warehouse(), replace=True, search_service=search_service_for(sv_fqn()),
                decision_proc=config.DECISION_TOOL or "")
    try:
        made = create_agent(session, config.APP_SCHEMA, sv_fqn(), title, agent_questions(), **args)
    except Exception:
        if not args["decision_proc"]:
            raise
        # e.g. setup/06_agent_tools.sql not run yet: keep analyst + search, drop the action tool
        args["decision_proc"] = ""
        made = create_agent(session, config.APP_SCHEMA, sv_fqn(), title, agent_questions(), **args)
    S["agents"] = find_agents(session, sv_fqn(), config.AGENT_SCHEMAS) or [made]
    S["agent"] = dict(next((a for a in S["agents"] if a["fqn"] == made["fqn"]), made))
    # SHOW AGENTS may not echo the comment/tools: trust what we just created so we don't rebuild every question
    S["agent"].update(comment=made["comment"], has_search=made["has_search"], has_actions=made["has_actions"])
    S["notice"] = f"Created Cortex Agent {made['fqn']} over {S['source']['fqn']}."


def ensure_agent():
    """One shared domain agent per semantic view, created on first use and upgraded when its definition is
    out of date (e.g. a document-search tool became available)."""
    if not S["agent"]:
        create_agent_action({})
        S["notice"] = f"Set up the shared Cortex Agent for this data ({S['agent']['fqn']}); every dashboard reuses it."
        return
    owned = S["agent"]["fqn"].upper().startswith(config.APP_SCHEMA.upper() + ".")
    stale = SPEC_VERSION not in (S["agent"].get("comment") or "")
    wants_search = bool(search_service_for(sv_fqn())) and not S["agent"].get("has_search")
    if owned and (stale or wants_search):
        try:
            create_agent_action({})
            tools = ["analyst"] + (["document search"] if S["agent"].get("has_search") else []) + \
                (["log_decision"] if S["agent"].get("has_actions") else [])
            S["notice"] = f"Updated the shared Cortex Agent {S['agent']['fqn']} ({' + '.join(tools)})."
        except Exception as exc:        # e.g. the search service has not been created yet: keep the old agent
            S["notice"] = f"Kept the existing agent; could not upgrade it: {str(exc)[:160]}"
            S["agent"]["comment"] = SPEC_VERSION   # don't retry on every question this session


def ask(p):
    ensure_agent()
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
            create_agent(session, config.APP_SCHEMA, sv_fqn(), title, agent_questions(),
                         warehouse=agent_warehouse(), replace=True,
                         search_service=search_service_for(sv_fqn()),
                         decision_proc=config.DECISION_TOOL or "")
            S["notice"] = f"Updated {S['agent']['fqn']} to run its analyst tool on {agent_warehouse()}."
            ans = ask_agent(session, S["agent"]["fqn"], question, S["thread"])
        S["thread"] = ans.get("thread") if ans.get("thread", {}).get("thread_id") else S["thread"]
        S["chat"].append({"role": "agent", **ans, "agent": S["agent"]["fqn"], "at": dt.datetime.now().strftime("%H:%M")})
        if ans.get("actions"):
            S["decisions"] = store.list_decisions(S["source"]["fqn"])
            _refresh_action_tables()
            S["notice"] = f"The agent logged decision {ans['actions'][0]['id']} in Snowflake."
        note_agent_tokens(ans)
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
    first = not (S.get("dashboard") or {}).get("dashboard_id")
    S["dashboard"] = {**saved, "name": name}
    S["dashboards"] = store.list_dashboards()
    if first:                                  # sign-offs made on the unsaved draft move to the saved dashboard
        store.adopt_uat(sv_fqn(), saved["dashboard_id"], name)
    uat_load_entries()
    uat_inbox_refresh()
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
        uat_load_entries()
        return
    tpl = get_template(d["template_id"])
    if not tpl or tpl.version != int(d["template_version"]):
        raise ValueError("Saved layout version is no longer in the catalog; choose a current layout.")
    select_layout({"template_id": d["template_id"]})
    S["dashboard"] = {"dashboard_id": d["dashboard_id"], "version": d["version"], "name": d["name"]}
    uat_load_entries()


# ------------------------------------------------------------------------------ B1: semantic view builder
def sb_tables(_p=None):
    """Tables/views the role can read in the allowlisted schemas (not the app's own objects), with their columns,
    the semantic views that already use them, and which tables join (metadata only)."""
    schemas = [x for x in config.DISCOVERY_SCHEMAS if x.upper() != config.APP_SCHEMA.upper()]
    tables = sb.list_tables(session, schemas)
    cat = table_finder.catalog(session, tables, schemas, S.get("sources") or [], config.APP_SCHEMA)
    S["sb"] = {"step": "pick", "tables": cat["tables"], "related": cat["related"], "suggest": None}


def sb_suggest(p):
    """Connect a table: Cortex picks the tables for a business question (from names, comments, columns)."""
    sbs = S.get("sb") or {}
    if not sbs.get("tables"):
        sb_tables()
        sbs = S["sb"]
    started = time.time()
    text = str(p.get("text") or "")[:400]
    out = table_finder.suggest(cortex(), sbs["tables"], text)
    S["sb"] = {**sbs, "suggest": out}
    log_ai("table_suggest", text, json.dumps(out["tables"])[:3900], f"Cortex AI_COMPLETE ({out['provenance']})",
           "valid" if out["tables"] else "empty", started)


def sb_draft(p):
    listed = {t["fqn"] for t in (S.get("sb") or {}).get("tables", [])}
    fqns = [str(x) for x in (p.get("fqns") or []) if x]
    if len(fqns) > 1:                                   # B6: one semantic view over several tables
        if any(f not in listed for f in fqns):
            raise ValueError("Pick tables from the list.")
        started = time.time()
        out = semantic_multi.draft(cortex(), session, fqns)
        ddl = semantic_multi.build_ddl(out["spec"], out["profiles"], config.APP_SCHEMA)
        S["sb"] = {**S["sb"], "step": "review", "multi": True, "fqns": fqns, "profiles": out["profiles"],
                   "spec": out["spec"], "ddl": ddl, "checks": out["checks"], "notes": out["notes"],
                   "origin": out["origin"]}
        log_ai("semantic_view_draft", ", ".join(fqns), json.dumps(out["spec"])[:3900],
               f"Cortex AI_COMPLETE ({out['origin']}), {len(fqns)} tables", "valid", started)
        return
    fqn = str(p.get("fqn") or (fqns[0] if fqns else ""))
    if fqn not in listed:
        raise ValueError("Pick one of the listed tables.")
    started = time.time()
    profile = sb.profile_table(session, fqn)
    spec = sb.draft(cortex(), profile)
    ddl = sb.build_ddl(spec, profile, config.APP_SCHEMA)
    S["sb"] = {**S["sb"], "step": "review", "multi": False, "fqn": fqn, "profile": profile, "spec": spec, "ddl": ddl,
               "notes": spec.pop("notes", []), "origin": spec.pop("origin", "")}
    log_ai("semantic_view_draft", fqn, json.dumps(spec)[:3900], f"Cortex AI_COMPLETE ({S['sb']['origin']})",
           "valid", started)


def _sb_reviewed(p):
    sbs = S.get("sb") or {}
    if not sbs.get("profile"):
        raise ValueError("Draft a semantic view first.")
    edited = p.get("spec") or sbs["spec"]
    keep = {k: [x for x in (edited.get(k) or []) if x.get("include", True)] for k in ("dimensions", "metrics", "ratios")}
    clean, notes = sb.validate_draft({**edited, **keep}, sbs["profile"])
    return sbs, clean, notes


def _sb_multi_reviewed(p):
    sbs = S.get("sb") or {}
    if not sbs.get("profiles"):
        raise ValueError("Draft a semantic view first.")
    clean, notes = semantic_multi.revalidate(p.get("spec") or sbs["spec"], sbs["profiles"])
    return sbs, clean, notes, semantic_multi.build_ddl(clean, sbs["profiles"], config.APP_SCHEMA)


def sb_preview(p):
    if (S.get("sb") or {}).get("multi"):
        sbs, clean, notes, ddl = _sb_multi_reviewed(p)
        S["sb"] = {**sbs, "spec": clean, "notes": notes, "ddl": ddl}
        return
    sbs, clean, notes = _sb_reviewed(p)
    S["sb"] = {**sbs, "spec": clean, "notes": notes, "ddl": sb.build_ddl(clean, sbs["profile"], config.APP_SCHEMA)}


def sb_create(p):
    if (S.get("sb") or {}).get("multi"):
        sbs, clean, notes, ddl = _sb_multi_reviewed(p)
        started = time.time()
        out = semantic_multi.create(session, ddl)
        log_ai("semantic_view_create", ", ".join(sbs["fqns"]), ddl["sv_sql"][:3900],
               f"CREATE SEMANTIC VIEW over {len(sbs['fqns'])} tables (approved by {viewer_key() or viewer_name()})",
               "ok" if all(c["status"] != "fail" for c in out["checks"]) else "check_failed", started)
        S["sources"] = list_semantic_views(session, config.DISCOVERY_SCHEMAS)
        st.session_state.pop("_catalog", None)
        home.cache_clear()
        S["sb"] = {**sbs, "spec": clean, "notes": notes, "ddl": ddl, "step": "done", "created": out}
        bad = [c for c in out["checks"] if c["status"] == "fail"]
        S["notice"] = (f"Created semantic view {out['semantic_view']} over {len(sbs['fqns'])} tables"
                       + (f" - but {len(bad)} total check(s) failed: review the joins before using it." if bad
                          else " - totals reconcile with the base tables. It is now available for dashboards and the agent."))
        return
    sbs, clean, notes = _sb_reviewed(p)
    ddl = sb.build_ddl(clean, sbs["profile"], config.APP_SCHEMA)
    started = time.time()
    out = sb.create(session, ddl)
    log_ai("semantic_view_create", sbs["fqn"], ddl["sv_sql"][:3900], "CREATE SEMANTIC VIEW (approved draft)", "ok", started)
    # make the new view a first-class source everywhere (Home ideas, routing, agent)
    S["sources"] = list_semantic_views(session, config.DISCOVERY_SCHEMAS)
    st.session_state.pop("_catalog", None)
    home.cache_clear()
    S["sb"] = {**sbs, "spec": clean, "notes": notes, "ddl": ddl, "step": "done", "created": out}
    S["notice"] = f"Created semantic view {out['semantic_view']} — it is now available for dashboards and the agent."


def sb_use(_p=None):
    fqn = ((S.get("sb") or {}).get("created") or {}).get("semantic_view")
    if fqn:
        select_source({"fqn": fqn})


def _eval_target():
    agent = (S.get("agent") or {}).get("fqn", "").upper()
    return agent, config.EVAL_CONFIGS.get(agent, "")


def eval_load(p=None):
    """Governance -> Agent evaluations: runs, per-metric averages vs the promotion gate, per-question scores."""
    agent, cfg = _eval_target()
    if not cfg:
        S["evals"] = {"agent": agent, "configured": False, "runs": []}
        return
    runs = store.eval_runs(agent)
    run = (p or {}).get("run") or (runs[0]["run_name"] if runs else "")
    res = store.eval_results(agent, run) if run else {"summary": [], "records": [], "error": ""}
    gate = []
    for r in res["summary"]:
        need = config.EVAL_GATE.get(str(r.get("metric_name")).lower())
        score = float(r.get("score") or 0)
        gate.append({**r, "score": round(score, 3), "threshold": need,
                     "pass": None if need is None else score >= need})
    decided = [g["pass"] for g in gate if g["pass"] is not None]
    S["evals"] = {"agent": agent, "configured": True, "runs": runs, "run": run,
                  "status": store.eval_status(cfg, run) if run else "", "summary": gate,
                  "records": res["records"], "error": res["error"],
                  "gate": None if not decided else all(decided)}


def eval_start(_p=None):
    agent, cfg = _eval_target()
    if not cfg:
        raise ValueError("No evaluation config for this agent (run setup\\run_agent_eval.cmd).")
    started = time.time()
    name = "aa_run_" + dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    store.eval_start(agent, cfg, name)
    log_ai("agent_evaluation", name, f"EXECUTE_AI_EVALUATION START {cfg}", "Snowflake AI Observability", "started", started)
    S["notice"] = f"Started Snowflake evaluation {name} (3-5 minutes). Refresh to see scores."
    eval_load({"run": name})


def quality(_p):
    S["quality"] = {"ledger": store.ai_ledger(), "usage": store.cortex_usage(),
                    "by_feature": store.usage_by_feature(QUERY_TAG_APP)}
    try:
        eval_load({})
    except Exception as exc:
        S["evals"] = {"configured": False, "error": str(exc)[:200], "runs": []}


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
    "exit_viewer": exit_viewer, "list_roles": list_roles, "load_page": load_page,
    "eval_load": eval_load, "eval_start": eval_start, "sb_tables": sb_tables, "sb_draft": sb_draft,
    "sb_preview": sb_preview, "sb_create": sb_create, "sb_use": sb_use, "metrics_redraft": redraft_metrics,
    "metric_define": metric_define, "metric_save": metric_save, "metric_cancel": metric_cancel,
    "switch_layout": switch_layout, "preview_draft": preview_draft, "sb_suggest": sb_suggest,
    "validate": validate, "validate_poll": validation_merge, "validate_all": validate_all,
    "validation_open": validation_open, "val_resolve": val_resolve,
    "theme_preview": theme_preview, "theme_save": theme_save, "theme_default": theme_default,
    "theme_apply": theme_apply, "theme_delete": theme_delete, "theme_cancel": lambda p: S.update(theme_draft=None),
    "uat_tile": uat_tile, "uat_page": uat_page, "uat_builder": uat_builder, "uat_open": uat_open,
    "uat_owner": uat_owner, "uat_inbox": uat_inbox_refresh,
    "alert_new": alert_new, "alert_update": alert_update, "alert_parse": alert_parse, "alert_preview": alert_preview,
    "alert_test": alert_test, "alert_save": alert_save, "alert_edit": alert_edit, "alerts_open": alerts_open,
    "alert_runs": alert_runs, "alert_toggle": alert_toggle, "alert_delete": alert_delete, "alert_run": alert_run,
    "alert_schedule": alert_schedule, "alert_integration": alert_integration, "uat_requirement": uat_requirement, "uat_download": uat_download,
    "download_done": lambda p: S.update(download=None),
}
VIEWER_ACTIONS = {"set_view", "load_page", "refresh", "enrich", "narrative", "tile_ask", "ask", "go", "exit_viewer", "open_published",
                  "add_decision", "decision_status", "quality", "boot", "home_suggestions", "home_suggestions_ai"}


PORTAL_ACTIONS = VIEWER_ACTIONS - {"boot", "home_suggestions", "home_suggestions_ai"}     # nothing that builds or suggests

QUERY_TAG_APP = "aa-enterprise"


def tag_queries(feature: str) -> None:
    """Tag every query an action runs (QUERY_TAG JSON) so cost can be attributed per feature and dashboard."""
    sv = ((S.get("source") or {}).get("fqn") or "").split(".")[-1]
    tag = json.dumps({"app": QUERY_TAG_APP, "feature": re.sub(r"[^a-z_]", "", feature or "other")[:40],
                      "semantic_view": re.sub(r"[^A-Z0-9_]", "", sv.upper())[:80],
                      "dashboard": re.sub(r"[^A-Za-z0-9_-]", "", str((S.get("dashboard") or {}).get("dashboard_id") or ""))[:40]},
                     separators=(",", ":"))
    if st.session_state.get("_query_tag") == tag:
        return
    try:
        session.sql(f"ALTER SESSION SET QUERY_TAG = '{tag}'").collect()
        st.session_state["_query_tag"] = tag
    except Exception:
        pass


def handle(event):
    if not isinstance(event, dict) or event.get("id") == S["last_request"]:
        return False
    store.actor = viewer_key()                 # AA_AI_RUNS records the person, not the app's service user
    S["last_request"] = event.get("id")
    if event.get("type") != "validate_poll":     # polls run no queries of their own
        tag_queries(str(event.get("type") or ""))
    if event.get("type") not in ("enrich", "validate", "validate_poll", "validation_open"):   # keep background messages
        S["error"] = S["notice"] = ""
    fn = ACTIONS.get(event.get("type"))
    if PORTAL and event.get("type") == "go" and (event.get("payload") or {}).get("step") != "workspace":
        exit_viewer()                            # any navigation away from the dashboard means back to the catalog
        S["revision"] += 1
        return True
    if PORTAL and event.get("type") not in PORTAL_ACTIONS:
        S["error"] = "This is the Analytics Accelerator Portal, for viewing. Building happens in the Analytics Accelerator app."
        S["revision"] += 1
        return True
    if S.get("viewer_mode") and event.get("type") not in VIEWER_ACTIONS:
        S["error"] = "This is a published, read-only dashboard. Open it in the builder to make changes."
        S["revision"] += 1
        return True
    if not fn:
        S["error"] = "Unknown action"
        return True
    over = ai_limit_message(event.get("type"), event.get("payload") or {})
    if over:
        S["error"] = over
        S["building"] = None
        S["revision"] += 1
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


def portal_gate():
    """Portal mode: no ?view= shows the catalog of dashboards this viewer may open; ?view= opens one, read-only."""
    import portal_view
    if not S.get("viewer"):
        S["viewer"] = viewer_name()
    if not S.get("published") or time.time() - S.get("_pub_at", 0) > 60:
        try:
            S["published"] = store.list_published()
            S["_pub_at"] = time.time()
        except Exception as exc:
            S["published"] = []
            S["error"] = f"Could not load dashboards: {exc}"
    mine = visible_published()
    wanted = st.query_params.get("view")
    flash = ""
    if wanted and wanted not in {d["dashboard_id"] for d in mine}:
        flash = "That dashboard is not available to you, or it is no longer published."
        try:
            st.query_params.clear()
        except Exception:
            pass
        wanted = None
    if not wanted:
        S["viewer_mode"] = False
        flash = flash or S.pop("portal_flash", "") or S.get("error") or ""
        portal_view.render(mine, S.get("viewer") or "", flash, own_base_url(),
                           getattr(config, "PORTAL_URL", ""),
                           {"can_share": can_share, "roles": portal_roles, "on_save": save_sharing})
        st.stop()
    global PORTAL_LOADER
    if S["features"] is None or (S.get("dashboard") or {}).get("dashboard_id") != wanted:
        name = next((d.get("name") for d in mine if d["dashboard_id"] == wanted), "")
        PORTAL_LOADER = st.empty()                   # drawn first, so the click gets an immediate response
        PORTAL_LOADER.markdown(portal_view.loader_html(name), unsafe_allow_html=True)
    if S["features"] is not None and (S.get("dashboard") or {}).get("dashboard_id") != wanted:
        try:
            portal_source(wanted)
            open_published({"dashboard_id": wanted})
        except Exception as exc:
            S["error"] = f"{exc}"


store.actor = viewer_key()                     # every AI run logged this rerun is attributed to the person
PORTAL_LOADER = None
if PORTAL:
    portal_gate()

if S["features"] is None:
    try:
        tag_queries("boot")
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

try:
    validation_merge()                       # background validation results that arrived since the last rerun
except Exception:
    pass
payload = {k: v for k, v in S.items() if k not in ("cache", "published", "tile_q")}
payload["catalog_audiences"] = list(AUDIENCES)
payload["app_schema"] = config.APP_SCHEMA
if S["source"] and S["step"] in ("layout", "workspace"):
    try:
        payload["distinct"] = distinct_for(model_obj())
    except Exception:
        payload["distinct"] = {}
payload["published"] = visible_published()
payload["portal_url"] = "" if PORTAL else getattr(config, "PORTAL_URL", "")   # left menu link to the portal
payload["is_portal"] = bool(PORTAL)
try:
    payload["uat"] = uat_overview() if S.get("spec") and not PORTAL and not S.get("viewer_mode") else None
except Exception:
    payload["uat"] = None
payload["theme"] = resolved_theme()
payload["theme_builtin"] = [{"id": k, "name": v["name"]} for k, v in themes.BUILT_IN.items()]
payload["tile_types"] = {k: {"label": v["label"], "fields": v["fields"], "use": v["use"],
                             "dim_range": v.get("dim_range"), "dim2_range": v.get("dim2_range"),
                             "additive": bool(v.get("additive"))} for k, v in TILES.items()}
payload["sql_log"] = S["sql_log"][-25:]
try:
    validation_prune()
    apply_resolutions()
    _stale = ([] if not S.get("spec") or S.get("viewer_mode") or PORTAL
              else [c for _pg in S["spec"]["pages"] for c in validation_stale(_pg)])
    _job = _val_job()
    if _job and _job["running"]:                     # tiles still being checked keep their "Checking" pill
        _stale = list(dict.fromkeys(_stale + [c for c in _job["cids"] if c not in _job["merged"]]))
    payload["validation_stale"] = _stale
    payload["validation_needed"] = validation_needed()
    payload["validation_overview"] = validation_overview() if S.get("spec") and not PORTAL else None
    payload["validation_brief"] = validation_brief()
except Exception:
    payload["validation_stale"], payload["validation_needed"] = [], []
def _on_action():
    """Runs BEFORE the script on the rerun a click triggers, so the click is applied and rendered in ONE
    script run (previously: render stale data, apply the click, st.rerun, render again)."""
    try:
        handle(getattr(st.session_state.get("aa_ui"), "action", None))
    except Exception as exc:            # never let a callback error blank the page
        S["error"] = f"{exc}"


if PORTAL_LOADER is not None:
    PORTAL_LOADER.empty()                            # the dashboard is about to be drawn

result = COMPONENT(key="aa_ui", data=json.loads(json.dumps(payload, default=str)), on_action_change=_on_action)

if handle(getattr(result, "action", None)):   # fallback if the callback path is unavailable
    st.rerun()
