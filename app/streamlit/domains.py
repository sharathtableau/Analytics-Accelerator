"""Workspaces (business domains): Retail, Finance, CPG.

One app, one domain layer. A domain groups the semantic views (and so the dashboards, ideas, agent, alerts and
reviews) of one line of business. The defaults below are the demo companies (all fictional, synthetic data
generated in Snowflake). An account can override or add domains with rows in AA_DOMAINS (DOMAIN_ID, SPEC JSON),
or with config.DOMAINS, without code changes.

A semantic view belongs to:
  1. the domain it was created in (views built in the app are tagged: setting 'viewdomain:<FQN>'), else
  2. the domain whose `schemas` list holds its schema, else
  3. the default domain (Retail), so everything that existed before domains keeps working unchanged.
"""
from __future__ import annotations

import copy
import json
from typing import Any, Iterable, Optional

DEFAULT_ID = "retail"

DEFAULTS: list[dict[str, Any]] = [
    {"id": "retail", "name": "Retail", "company": "Harborline Outfitters", "tagline": "omnichannel apparel retailer",
     "blurb": "Sales, margin, inventory, stores and e-commerce, fulfilment and promotions.",
     "icon": "\U0001f6cd\ufe0f", "accent": "#0f3a5f", "soft": "#e6eefb", "sort": 1, "default": True,
     "schemas": [],                      # the default domain takes every view no other domain claims
     "featured": {}, "search": {},       # empty = config.FEATURED_VIEWS / FEATURED_LABELS / SEARCH_SERVICES
     "metrics": ["Net Sales", "Gross Margin", "Sell-through", "On-time delivery"],
     "agent_hint": "Why did gross margin drop last week?"},
    {"id": "finance", "name": "Finance", "company": "Keystone Financial", "tagline": "consumer bank: credit cards and deposits",
     "blurb": "Card and deposit balances, card economics, credit risk, deposit pricing and new-account acquisition.",
     "icon": "\U0001f4b3", "accent": "#0e6b52", "soft": "#e5f4ef", "sort": 2, "weekly": True,
     "schemas": ["WBR_DB.FINANCE_DEMO"],
     "featured": {"WBR_DB.FINANCE_DEMO.FINANCE_ANALYTICS_SV": "Keystone Financial (weekly)"},
     "search": {"WBR_DB.FINANCE_DEMO.FINANCE_ANALYTICS_SV": "WBR_DB.FINANCE_DEMO.FINANCE_DOCS_SEARCH"},
     "metrics": ["Ending Balance", "Delinquency Rate", "Rewards / Interchange", "Deposit Rate Gap"],
     "agent_hint": "Which segments are losing deposit balances fastest, and what is their rate gap?",
     "questions": ["Which segments are losing deposit balances fastest, and what is their rate gap?",
                   "Which segments show deteriorating delinquency over the last 13 weeks?",
                   "What is the rewards-to-interchange ratio by product and how is it trending?",
                   "Rank acquisition channels by cost per booking."]},
    {"id": "cpg", "name": "CPG", "company": "Apex Athletic", "tagline": "athletic apparel and footwear brand selling through retailers",
     "blurb": "Sell-in vs sell-through, account scorecards, trade promotion ROI, distribution and weeks of supply.",
     "icon": "\U0001f4e6", "accent": "#a65a0b", "soft": "#fbf0e3", "sort": 3, "weekly": True,
     "schemas": ["WBR_DB.CPG_DEMO"],
     "featured": {"WBR_DB.CPG_DEMO.CPG_ANALYTICS_SV": "Apex Athletic (weekly)"},
     "search": {"WBR_DB.CPG_DEMO.CPG_ANALYTICS_SV": "WBR_DB.CPG_DEMO.CPG_DOCS_SEARCH"},
     "metrics": ["Net Sales", "Sell-through", "Weeks of Supply", "Trade Spend %"],
     "agent_hint": "Which accounts have sell-in growing while sell-through declines?",
     "questions": ["Which accounts have sell-in growing while sell-through declines?",
                   "Show retailer weeks of supply by account and product, and flag anything above 12.",
                   "Rank promotion types by ROI over the last two quarters.",
                   "Which product lines are losing gross margin, and why?"]},
]

FIELDS = ("name", "company", "tagline", "blurb", "icon", "accent", "soft", "sort", "default", "schemas", "featured",
          "search", "metrics", "agent_hint", "questions", "weekly", "enabled")


def merge(rows: Iterable[dict[str, Any]] = (), extra: Optional[list] = None) -> list[dict[str, Any]]:
    """Code defaults, then config.DOMAINS (extra), then AA_DOMAINS rows ({domain_id, spec}); later wins per field."""
    out = {d["id"]: copy.deepcopy(d) for d in DEFAULTS}
    for d in list(extra or []) + [_row(r) for r in rows or []]:
        if not d or not d.get("id"):
            continue
        did = str(d["id"]).strip().lower()
        base = out.setdefault(did, {"id": did, "name": did.title(), "company": "", "tagline": "", "blurb": "",
                                    "icon": "\U0001f4ca", "accent": "#11567f", "soft": "#e8f1fd", "sort": 99, "schemas": [],
                                    "featured": {}, "search": {}, "metrics": [], "agent_hint": ""})
        for k in FIELDS:
            if k in d and d[k] is not None:
                base[k] = d[k]
    doms = [d for d in out.values() if d.get("enabled", True)]
    for d in doms:
        d["schemas"] = [str(s).upper() for s in d.get("schemas") or []]
        d["featured"] = {str(k).upper(): v for k, v in (d.get("featured") or {}).items()}
        d["search"] = {str(k).upper(): v for k, v in (d.get("search") or {}).items()}
    if not any(d.get("default") for d in doms) and doms:
        (next((d for d in doms if d["id"] == DEFAULT_ID), None) or doms[0])["default"] = True
    return sorted(doms, key=lambda d: (d.get("sort", 99), d["name"]))


def _row(r: dict[str, Any]) -> Optional[dict[str, Any]]:
    try:
        spec = r.get("spec")
        spec = json.loads(spec) if isinstance(spec, str) else dict(spec or {})
    except Exception:
        return None
    spec["id"] = r.get("domain_id") or spec.get("id")
    if r.get("active") is False:
        spec["enabled"] = False
    return spec


def default_id(doms: list[dict[str, Any]]) -> str:
    return next((d["id"] for d in doms if d.get("default")), doms[0]["id"] if doms else DEFAULT_ID)


def get(doms: list[dict[str, Any]], did: str) -> Optional[dict[str, Any]]:
    return next((d for d in doms if d["id"] == (did or "").lower()), None)


def discovery_schemas(base: Iterable[str], doms: list[dict[str, Any]]) -> list[str]:
    """The configured discovery list plus every domain's schemas (a schema that does not exist yet just stays empty)."""
    seen = [s.upper() for s in base]
    for d in doms:
        seen += [s for s in d.get("schemas") or [] if s not in seen]
    return list(dict.fromkeys(seen))


def of_view(fqn: str, doms: list[dict[str, Any]], tags: Optional[dict[str, str]] = None) -> str:
    """Domain id of a semantic view ('DB.SCHEMA.VIEW' or 'DB.SCHEMA.VIEW#TABLE')."""
    base = str(fqn or "").upper().partition("#")[0]
    ids = {d["id"] for d in doms}
    tagged = (tags or {}).get(base)
    if tagged in ids:
        return tagged
    schema = base.rsplit(".", 1)[0]
    for d in doms:
        if schema and schema in (d.get("schemas") or []):
            return d["id"]
    return default_id(doms)


def of_dashboard(d: dict[str, Any], doms: list[dict[str, Any]], tags: Optional[dict[str, str]] = None) -> str:
    lay = d.get("layout") or d.get("layout_spec") or {}
    did = (lay.get("domain") if isinstance(lay, dict) else None) or ""
    return did if get(doms, did) else of_view(d.get("semantic_view") or "", doms, tags)


def featured(dom: dict[str, Any], fallback_views: list[str], fallback_labels: dict[str, str]) -> dict[str, str]:
    """Featured views of a domain {fqn: label}; the default domain falls back to config.FEATURED_VIEWS."""
    if dom.get("featured"):
        return dict(dom["featured"])
    if dom.get("default"):
        return {f: fallback_labels.get(f, "") for f in fallback_views}
    return {}


def sources_in(sources: list[dict[str, Any]], did: str, doms: list[dict[str, Any]],
               tags: Optional[dict[str, str]] = None) -> list[dict[str, Any]]:
    return [s for s in sources or [] if s.get("fqn") and of_view(s["fqn"], doms, tags) == did]


def summary(doms: list[dict[str, Any]], sources: list[dict[str, Any]], dashboards: list[dict[str, Any]],
            tags: Optional[dict[str, str]] = None, inbox_rows: Optional[list] = None,
            alerts: Optional[list] = None, published: Optional[list] = None) -> list[dict[str, Any]]:
    """Cards for the picker: what each workspace holds and whether it is ready (has at least one semantic view)."""
    out = []
    for d in doms:
        src = sources_in(sources, d["id"], doms, tags)
        dash = [x for x in dashboards or [] if of_dashboard(x, doms, tags) == d["id"]]
        ids = {x.get("dashboard_id") for x in dash}
        out.append({k: d.get(k) for k in ("id", "name", "company", "tagline", "blurb", "icon", "accent", "soft",
                                           "metrics", "agent_hint", "default", "weekly")} | {
            "ready": bool(src),
            "datasets": [s.get("name") for s in src][:6],
            "n_datasets": len(src),
            "n_dashboards": len(dash),
            "n_published": sum(1 for p in published or [] if of_dashboard(p, doms, tags) == d["id"]),
            "n_reviews": sum(1 for r in inbox_rows or [] if r.get("dashboard_id") in ids),
            "n_alerts": sum(1 for a in alerts or [] if of_view(a.get("semantic_view") or "", doms, tags) == d["id"]),
        })
    return out
