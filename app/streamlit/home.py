"""Prompt-first home: a catalog of what the data can answer, dashboard ideas, and prompt routing.

Users never pick a semantic view here. The app profiles every semantic view the role
can see (metrics, dimensions, time), Cortex proposes dashboard ideas per audience, and
a typed request is routed to the best view + audience. Every Cortex choice is checked
against the catalog; keyword matching is the fallback.
"""
from __future__ import annotations

import re
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Optional

AUDIENCES = ("executives", "managers", "weekly_business_review", "daily_operations")
AUDIENCE_GROUP = {"executives": "Executive", "managers": "Manager", "weekly_business_review": "Operations",
                  "daily_operations": "Operations"}
TTL = 1800
_CACHE: dict[str, dict[str, Any]] = {}          # process-wide: role -> {"at", "catalog", "suggestions"}
_LOCK = threading.Lock()
NOISE = re.compile(r"(_SEMANTIC_VIEW|_SEMANTIC|_SV|_MODEL|_VIEW)$", re.I)
TEST_LIKE = re.compile(r"\b(TEST|TMP|TEMP|SCRATCH|R\d+|V\d+|COPY|OLD|BACKUP)\b", re.I)


def friendly(name: str) -> str:
    base = NOISE.sub("", name or "")
    base = re.sub(r"_(\d+)_", " ", base)
    words = [w for w in base.replace("_", " ").split() if w]
    return " ".join(w.capitalize() if not w.isupper() or len(w) > 3 else w for w in words).strip() or name


def cache_get(role: str) -> Optional[dict[str, Any]]:
    with _LOCK:
        hit = _CACHE.get(role)
        return hit if hit and time.time() - hit["at"] < TTL else None


def cache_put(role: str, **values: Any) -> None:
    with _LOCK:
        entry = _CACHE.get(role)
        if not entry or time.time() - entry["at"] >= TTL:      # expired entries restart the clock
            entry = {"at": time.time()}
        entry.update(values)
        _CACHE[role] = entry


def cache_clear() -> None:
    with _LOCK:
        _CACHE.clear()


def catalog_signature(catalog: list[dict[str, Any]]) -> str:
    """Saved ideas stay valid while the set of views (and their metrics) is unchanged."""
    import hashlib
    key = "|".join(sorted(f"{c['fqn']}:{len(c.get('metrics') or [])}:{int(bool(c.get('featured')))}" for c in catalog))
    return hashlib.sha1(key.encode()).hexdigest()[:16]


def _table_key(t: str) -> str:
    """'VW_RETAIL_MASTER' / 'retail_master' / '"V_Retail_Master"' -> 'RETAIL_MASTER'."""
    return re.sub(r"^(VW|V|TBL|T)_", "", str(t or "").strip('"').upper())


def match_featured(fqn: str, featured: dict[str, str]) -> Optional[str]:
    """The featured key that names this catalog entry (case-insensitive; 'VIEW#TABLE' also matches with or
    without a VW_/V_ prefix on the table; a bare 'VIEW' key features every table of a facts-only view)."""
    base, _, table = str(fqn).upper().partition("#")
    for key in featured:
        kb, _, kt = str(key).upper().replace('"', "").partition("#")
        if kb != base:
            continue
        if not kt or (table and _table_key(kt) == _table_key(table)):
            return key
    return None


def featured_gaps(catalog: list[dict[str, Any]], featured: dict[str, str], sources: list[dict[str, Any]],
                  skipped: list[dict[str, Any]], schema_errors: Optional[dict] = None) -> list[dict[str, Any]]:
    """A featured view that is not on Home always gets a reason (adds to `skipped`, returns the new entries)."""
    added = []
    seen_base = {str(s.get("fqn") or "").upper() for s in sources}
    for key, label in (featured or {}).items():
        if any(match_featured(c["fqn"], {key: label}) for c in catalog):
            continue
        base, _, table = key.upper().partition("#")
        if any(str(x.get("fqn", "")).upper().partition("#")[0] == base for x in skipped):
            continue                                  # already explained (no access, no metrics, no date)
        schema = base.rsplit(".", 1)[0]
        err = (schema_errors or {}).get(schema)
        if base not in seen_base:
            why = (f"it is featured, but the app's role can't list semantic views in {schema} ({err[:120]}); grant USAGE "
                   "on the database and schema and SELECT on the semantic view" if err else
                   f"it is featured, but the app's role doesn't see it in {schema}: check the name, or grant USAGE on "
                   "the database and schema and SELECT on the semantic view")
        else:
            tabs = sorted({c["fqn"].partition("#")[2] for c in catalog if c["fqn"].partition("#")[0] == base} - {""})
            why = (f"it is featured as table {table}, but the view's tables are {', '.join(tabs)}" if tabs and table else
                   "it is featured, but it has no table with both measures and a date dimension")
        entry = {"fqn": key, "name": label or key.split(".")[-1], "reason": why, "featured": True}
        skipped.append(entry)
        added.append(entry)
    return added


def _idea_key(s: dict[str, Any]) -> tuple:
    return (str(s.get("semantic_view") or "").upper(), s.get("audience"), re.sub(r"\W+", " ", str(s.get("title") or "").lower()).strip())


def shown_themes(ideas: list[dict[str, Any]], catalog: list[dict[str, Any]]) -> dict[tuple, set]:
    """{(view, audience group): themes on screen now} - what 'New ideas' must not repeat."""
    by_fqn = {c["fqn"]: c for c in catalog}
    out: dict[tuple, set] = {}
    for s2 in ideas or []:
        c = by_fqn.get(s2.get("semantic_view"))
        if c and s2.get("audience") in AUDIENCES:
            out.setdefault((c["fqn"], AUDIENCE_GROUP[s2["audience"]]), set()).add(s2.get("theme") or idea_theme(s2, c))
    return out


def next_themes(c: dict[str, Any], aud: str, n: int, avoid: set) -> list[tuple[str, list]]:
    """The audience's next n themes for this dataset: unseen themes first (in the audience's order), then - only
    when the dataset has run out of new themes - the ones shown before, so the rotation wraps around."""
    allt = audience_themes(c, aud, 99)
    fresh = [x for x in allt if x[0] not in (avoid or set())]
    return (fresh + [x for x in allt if x not in fresh])[:n]


def ensure_featured(ideas: list[dict[str, Any]], catalog: list[dict[str, Any]], per: int = 3,
                    avoid: Optional[dict] = None) -> list[dict[str, Any]]:
    """Every featured view gets `per` ideas in every audience group, each on a different metric theme (catalog
    ideas fill what Cortex left out, skipping `avoid` themes - the ones on screen before 'New ideas');
    featured flags and domain labels follow the current catalog."""
    out = list(ideas)
    avoid = avoid or {}
    feat = [c for c in catalog if c.get("featured")]
    for c in reversed(feat):
        for aud in ("executives", "managers", "daily_operations"):
            mine = [s for s in out if AUDIENCE_GROUP[s["audience"]] == AUDIENCE_GROUP[aud]
                    and s["semantic_view"] == c["fqn"]]
            used = {s.get("theme") or idea_theme(s, c) for s in mine}
            need = per - len(mine)
            skip = avoid.get((c["fqn"], AUDIENCE_GROUP[aud]), set())
            extra = [theme_idea(c, aud, t, ms) for t, ms in next_themes(c, aud, 99, skip)
                     if t not in used][:max(0, need)]
            out[:0] = [{**x, "by": "catalog"} for x in extra]
    by_fqn = {c["fqn"]: c for c in catalog}
    for s2 in out:
        if s2.get("theme"):
            s2["theme_label"] = theme_label(s2["theme"])
        s2["featured"] = bool(by_fqn.get(s2["semantic_view"], {}).get("featured"))
        if s2["featured"]:
            s2["domain"] = by_fqn[s2["semantic_view"]]["label"]
    out.sort(key=lambda s2: (not s2["featured"], bool(s2.get("earlier"))))   # stable within each group
    return out


def idea_theme(s: dict[str, Any], c: dict[str, Any]) -> str:
    """The metric theme an idea is about: its own tag, else the most common theme of its metrics (plan metrics
    such as 'Net Sales vs Plan' only count when nothing else is named)."""
    if s.get("theme") and (s["theme"] in THEMES or s["theme"] == "other"):
        return s["theme"]
    by_label = {m["label"].lower(): (m.get("theme") or metric_theme(m["id"])) for m in c.get("metrics") or []}
    ts = [by_label.get(str(m).lower()) or metric_theme(str(m).upper().replace(" ", "_")) for m in s.get("metrics") or []]
    core = [t for t in ts if t not in ("plan", "other")] or ts
    return max(dict.fromkeys(core), key=core.count) if core else "other"


def merge_ideas(sets: list[dict[str, Any]], catalog: list[dict[str, Any]], limit: int = 48,
                per_featured: int = 3, per_other: int = 2) -> list[dict[str, Any]]:
    """Saved idea sets (newest first) -> one list: newest ideas first, earlier ones below (marked with the date
    they were saved). One idea per audience x metric theme per dataset (the newest wins), at most `per_featured`
    per audience on a featured dataset and `per_other` per audience across all other datasets (one per dataset);
    ideas on views that are gone are dropped.
    Nothing is deleted from AA_IDEAS."""
    by_fqn = {c["fqn"]: c for c in catalog}
    out, seen, count = [], set(), {}
    for i, st in enumerate(sets):
        for s in st.get("ideas") or []:
            if not isinstance(s, dict) or s.get("audience") not in AUDIENCES or not s.get("title"):
                continue
            fqn = str(s.get("semantic_view") or "").upper()
            if fqn not in by_fqn:
                fqn = _resolve_view(fqn, by_fqn) or ""
            if not fqn:
                continue
            group = AUDIENCE_GROUP[s["audience"]]
            theme = idea_theme(s, by_fqn[fqn])
            k = _idea_key({**s, "semantic_view": fqn})
            kt = (fqn if by_fqn[fqn].get("featured") else "*other*", group, theme)
            feat = bool(by_fqn[fqn].get("featured"))
            slot = (fqn, group) if feat else ("*other*", group)
            cap = per_featured if feat else per_other
            if k in seen or kt in seen or count.get(slot, 0) >= cap or (not feat and (fqn, group) in count):
                continue                              # same title, same audience x theme, or audience full
            seen.update({k, kt})
            count[slot] = count.get(slot, 0) + 1
            if not feat:
                count[(fqn, group)] = 1
            idea = {**s, "semantic_view": fqn, "theme": theme,
                    "metrics": _plain_metrics(s.get("metrics") or [], by_fqn[fqn]) or list(s.get("metrics") or [])}
            idea.pop("earlier", None)
            if i > 0:
                idea["earlier"] = st.get("created_at") or "earlier"
            out.append(idea)
    return out[:limit]


def _resolve_view(fqn: str, by_fqn: dict[str, Any]) -> Optional[str]:
    """A bare view name for a view split per table -> its featured (else first) table entry."""
    cands = [f for f in by_fqn if f.partition("#")[0] == fqn.partition("#")[0]
             and (not fqn.partition("#")[2] or _table_key(f.partition("#")[2]) == _table_key(fqn.partition("#")[2]))]
    cands.sort(key=lambda f: not by_fqn[f].get("featured"))
    return cands[0] if cands else None


# --------------------------------------------------------------------------- catalog
def build_catalog(sources: list[dict[str, Any]], describe: Callable[[str], Any],
                  featured: Optional[dict[str, str]] = None,
                  skipped: Optional[list] = None) -> list[dict[str, Any]]:
    """Describe every visible semantic view in parallel; keep the ones that can drive a dashboard."""
    views = [s for s in sources if s.get("fqn")]

    def one(src):
        try:
            m = describe(src["fqn"])
        except Exception as exc:
            return [{"fqn": src["fqn"], "error": str(exc)[:160]}]
        from semantic_catalog import scope_model
        tabs = sorted({x.entity for x in m.metrics if x.entity}) if getattr(m, "facts_mode", False) and not m.scope else []
        if len(tabs) > 1:
            # a facts-only view over several unrelated tables: one dataset per table on Home
            out = []
            for t in tabs:
                sm = scope_model(m, t)
                sm.facts_mode = True
                sm.virtual = {k: v for k, v in m.virtual.items() if any(x.ref == k for x in sm.metrics)}
                out.append(entry({**src, "fqn": f"{src['fqn']}#{t.upper()}", "name": f"{src['name']} {t}"}, sm,
                                 f"{friendly(src['name'])} · {friendly(re.sub(r'^(VW|V|TBL|T)_', '', t, flags=re.I))}"))
            return out
        return [entry(src, m, friendly(src["name"]))]

    def entry(src, m, label):
        return {
            "fqn": src["fqn"], "name": src["name"], "label": label,
            "adhoc": bool(getattr(m, "facts_mode", False)),
            "comment": (src.get("comment") or m.comment or "")[:160],
            "metrics": [{"id": x.id, "label": x.label, "additive": bool(x.additive), "theme": metric_theme(x.id)}
                        for x in m.metrics if not x.name.upper().startswith("HELPER_")][:60],
            "dimensions": [{"id": d.id, "label": d.label} for d in m.categorical_dimensions][:40],
            "time": [d.id for d in m.time_dimensions],
            "facts": len(m.facts),
            "test_like": bool(TEST_LIKE.search(src["name"].replace("_", " "))),
        }
    with ThreadPoolExecutor(max_workers=8) as pool:
        out = [e for lst in pool.map(one, views) for e in lst]
    usable = [c for c in out if not c.get("error") and c["metrics"] and c["time"]]
    if skipped is not None:          # say why a view is not on Home instead of hiding it silently
        for c in out:
            if c in usable:
                continue
            if c.get("error"):
                why = ("the app's role can't read it (grant USAGE on the database/schema and SELECT on the "
                       "semantic view and its tables)" if re.search(r"not exist|not authorized|privilege", c["error"], re.I)
                       else "it couldn't be described: " + c["error"][:100])
            elif not c["metrics"]:
                why = (f"it has {c.get('facts', 0)} facts but no metrics yet; dashboards need metrics such as "
                       "SUM(sales)") if c.get("facts") else "it has no metrics"
            else:
                why = "it has no date dimension to trend over"
            skipped.append({"fqn": c["fqn"], "name": c["fqn"].split(".")[-1], "reason": why})
    for c in usable:
        key = match_featured(c["fqn"], featured or {})
        c["featured"] = key is not None
        if key and (featured or {}).get(key):
            c["label"] = featured[key]
    usable.sort(key=lambda c: (not c["featured"], c["test_like"], -len(c["metrics"]), c["label"]))
    return usable


def _pick_views(catalog: list[dict[str, Any]], n: int) -> list[dict[str, Any]]:
    """Distinct business domains first (skip near-duplicate/test copies)."""
    picked, seen = [], set()
    for c in catalog:
        key = re.sub(r"\b(v\d+|r\d+|test|upload|sample|semantic|demo|data|using|\d+)\b", "", c["label"].lower())
        key = " ".join(sorted(set(key.split())))[:40]
        if key in seen:
            continue
        seen.add(key)
        picked.append(c)
        if len(picked) >= n:
            break
    return picked


def _pref(items: list[dict[str, Any]], patterns: tuple[str, ...]) -> list[dict[str, Any]]:
    """Order items by the first pattern their NAME (after the table prefix) matches."""
    scored = []
    for i, it in enumerate(items):
        rank = next((k for k, p in enumerate(patterns) if re.search(p, it["id"].split(".")[-1], re.I)), len(patterns))
        scored.append((rank, i, it))
    return [it for _, _, it in sorted(scored, key=lambda t: (t[0], t[1]))]


# --------------------------------------------------------------------------- audience x metric themes
# Ideas are an AUDIENCE looking at a METRIC THEME: each audience gets several ideas, each on a different theme
# chosen for what that audience owns (executives: outcomes; managers: the levers their areas control;
# operations: what breaks today). Order matters: the first matching theme wins (NET_SALES_AFTER_RETURNS -> returns).
THEMES = {
    "plan":       ("Plan", r"PLAN|BUDGET|TARGET|FORECAST", {}),
    "returns":    ("Returns & discounts", r"RETURN|DISCOUNT|MARKDOWN|REFUND",
                   {"executives": 1, "managers": 3, "daily_operations": 2}),
    "inventory":  ("Inventory & availability", r"STOCK|INVENTORY|ON_HAND|ON_ORDER|SUPPLY|SELL_THROUGH|LOST_SALES",
                   {"executives": 2, "managers": 3, "daily_operations": 3}),
    "fulfilment": ("Delivery & fulfilment", r"DELIVER|TRANSIT|SHIP|ON_TIME|CLICK_TO|FULFIL|CARRIER|LATE",
                   {"executives": 1, "managers": 3, "daily_operations": 3}),
    "margin":     ("Margin & profitability", r"MARGIN|PROFIT|COGS|COST_OF_GOODS|COST",
                   {"executives": 3, "managers": 2, "daily_operations": 0}),
    "channel":    ("Online & channel mix", r"ONLINE|DIGITAL|ECOM|CHANNEL|_SHARE",
                   {"executives": 2, "managers": 2, "daily_operations": 1}),
    "customer":   ("Customers & basket", r"CUSTOMER|ORDER_VALUE|AOV|BASKET|PER_TRANSACTION|CONVERSION|LOYAL",
                   {"executives": 2, "managers": 3, "daily_operations": 1}),
    "care":       ("Patients & utilisation", r"PATIENT|ADMI|BED|STAY|VISIT|CLAIM|BILLING|READMI|ENCOUNTER",
                   {"executives": 3, "managers": 3, "daily_operations": 3}),
    "volume":     ("Orders & units", r"ORDER|UNIT|QUANTITY|QTY|TRANSACTION|COUNT",
                   {"executives": 1, "managers": 2, "daily_operations": 3}),
    "revenue":    ("Sales & growth", r"SALES|REVENUE|AMOUNT|BOOKING|INCOME",
                   {"executives": 3, "managers": 2, "daily_operations": 2}),
}
OTHER = ("Other measures", "", {"executives": 1, "managers": 1, "daily_operations": 1})
RATE = re.compile(r"RATE|PCT|PERCENT|SHARE|RATIO|AVG|AVERAGE|DAYS|HOURS|PER_|_VALUE$", re.I)
HEADLINE = re.compile(r"^NET_(SALES|REVENUE)$|^(SALES|REVENUE)$|^GROSS_MARGIN_PCT$|^ORDER_COUNT$|^IN_STOCK_RATE$|"
                      r"^ON_TIME_DELIVERY_PCT$|^RETURN_RATE$|^AVERAGE_ORDER_VALUE$|^STOCKOUT_RATE$|^GROSS_MARGIN$|"
                      r"^UNITS_SOLD$|^ACTIVE_CUSTOMERS$|^LOST_SALES_UNITS$|^ONLINE_SALES_SHARE$|^ONLINE_NET_SALES$|"
                      r"^AVG_DELIVERY_DAYS$|^AVG_CLICK_TO_SHIP_HOURS$|^DISCOUNT_RATE$|^WEEKS_OF_SUPPLY$|^PROFIT|RATIO$", re.I)
# the metric a business user would name first within its theme (others follow the audience lens)
TOP = ("NET_SALES", "NET_REVENUE", "SALES", "REVENUE", "GROSS_MARGIN_PCT", "GROSS_MARGIN", "PROFIT_RATIO", "PROFIT",
       "ONLINE_SALES_SHARE", "ONLINE_NET_SALES", "IN_STOCK_RATE", "LOST_SALES_UNITS", "STOCKOUT_RATE",
       "ON_TIME_DELIVERY_PCT", "AVG_DELIVERY_DAYS", "AVG_CLICK_TO_SHIP_HOURS", "RETURN_RATE", "DISCOUNT_RATE",
       "AVERAGE_ORDER_VALUE", "ACTIVE_CUSTOMERS", "ORDER_COUNT", "UNITS_SOLD")


def _top_rank(metric_id: str) -> int:
    name = str(metric_id).split(".")[-1].upper()
    return TOP.index(name) if name in TOP else len(TOP)


# which themes each audience looks at first (themes with affinity 0 are never offered to that audience)
PREFER = {
    "executives": ("revenue", "margin", "channel", "inventory", "care", "customer", "fulfilment", "returns", "volume"),
    "managers": ("inventory", "fulfilment", "returns", "customer", "care", "margin", "revenue", "channel", "volume"),
    "daily_operations": ("inventory", "fulfilment", "volume", "care", "returns", "revenue", "customer", "channel"),
}
TITLES = {   # (executives, managers, operations) title per theme, in each audience's words
    "revenue": ("Sales vs plan and year-end outlook", "Sales vs plan by {dim}", "Today's sales pace vs last week"),
    "margin": ("Margin and profitability brief", "Margin scorecard by {dim}", "Margin leaks today"),
    "channel": ("Online and channel mix", "Channel mix by {dim}", "Online orders right now"),
    "inventory": ("Availability and lost sales", "In-stock scorecard by {dim}", "Stockouts to fix today"),
    "fulfilment": ("Delivery promise: are we on time?", "On-time delivery by {dim}", "Late shipments right now"),
    "returns": ("Returns and discount impact", "Returns and discounts by {dim}", "Return spikes today"),
    "customer": ("Customers and basket health", "Basket and customers by {dim}", "Basket size today"),
    "volume": ("Orders and units outlook", "Orders and units by {dim}", "Order pace by hour"),
    "care": ("Patients and utilisation brief", "Utilisation by {dim}", "Patient flow today"),
}
LENS = {
    "executives": {"title": "{theme}: year to date vs plan",
                   "detail": "{m} year to date vs plan, year-end outlook (Snowflake ML) and what drove it",
                   "goal": "One-page executive brief on {theme_l}: {m} year to date vs plan, outlook and key drivers"},
    "managers": {"title": "{theme} scorecard by {dim}",
                 "detail": "Weekly {m} by {dim_l} vs plan (red/amber/green), exceptions to act on",
                 "goal": "Weekly manager scorecard on {theme_l} by {dim}: {m} vs plan, with exceptions to act on"},
    "daily_operations": {"title": "{theme}: what's off today",
                         "detail": "Today's {m} by hour vs last week and a worklist of what is off now",
                         "goal": "Live operations control room on {theme_l} for today: {m} pace by hour and today's problems"},
}


def metric_theme(metric_id: str) -> str:
    name = str(metric_id).split(".")[-1]
    return next((k for k, (_, rx, _) in THEMES.items() if re.search(rx, name, re.I)), "other")


def theme_label(theme: str) -> str:
    return (THEMES.get(theme) or OTHER)[0]


def audience_themes(c: dict[str, Any], audience: str, n: int = 3) -> list[tuple[str, list[dict[str, Any]]]]:
    """The n metric themes this audience should see for one dataset (best fit first), each with its metrics
    ordered for the audience's lens (executives: amounts first; managers/operations: rates first)."""
    by_theme: dict[str, list] = {}
    for m in c.get("metrics") or []:
        t = m.get("theme") or metric_theme(m["id"])
        if t != "plan":
            by_theme.setdefault(t, []).append(m)
    ranked = []
    for t, ms in by_theme.items():
        aff = (THEMES.get(t) or OTHER)[2].get(audience, 1)
        if aff <= 0:
            continue
        lens_rate = audience != "executives"
        ms = sorted(ms, key=lambda m: (_top_rank(m["id"]), not HEADLINE.search(m["id"].split(".")[-1]),
                                       bool(RATE.search(m["id"].split(".")[-1])) != lens_rate))
        pref = PREFER.get(audience, ())
        ranked.append((pref.index(t) if t in pref else len(pref), -min(len(ms), 4), t, ms))
    ranked.sort()
    return [(t, ms) for *_, t, ms in ranked[:n]]


def _area_dim(c: dict[str, Any]) -> str:
    ds = _pref(c.get("dimensions") or [], (r"^REGION$|REGION|MARKET|COUNTRY|STORE|DEPARTMENT", r"CATEGORY|SEGMENT|CHANNEL"))
    return ds[0]["label"] if ds else "area"


def theme_idea(c: dict[str, Any], audience: str, theme: str, metrics: list[dict[str, Any]]) -> dict[str, Any]:
    ms = [m["label"] for m in metrics[:3]]
    lens, dim = LENS[audience], _area_dim(c)
    lbl = theme_label(theme)
    fmt = dict(theme=lbl, theme_l=lbl.lower(), m=", ".join(ms), dim=dim, dim_l=dim.lower())
    own = TITLES.get(theme)
    title = own[("executives", "managers", "daily_operations").index(audience)] if own else lens["title"]
    return {"audience": audience, "featured": c.get("featured", False), "theme": theme,
            "title": title.format(**fmt)[:70], "detail": lens["detail"].format(**fmt)[:140],
            "metrics": ms, "semantic_view": c["fqn"], "domain": c["label"], "goal": lens["goal"].format(**fmt)[:300]}


def fallback_suggestions(catalog: list[dict[str, Any]], per: int = 3) -> list[dict[str, Any]]:
    """Catalog ideas: for each dataset and audience, one idea per best-fitting metric theme."""
    out = []
    for c in _pick_views(catalog, 3):
        for aud in ("executives", "managers", "daily_operations"):
            out += [theme_idea(c, aud, t, ms) for t, ms in audience_themes(c, aud, per if c.get("featured") else 1)]
    return out


# --------------------------------------------------------------------------- prompt bar: data brief + starter prompts
def _domain(c: dict[str, Any]) -> str:
    return re.sub(r"\s*\((live|demo)\)\s*$", "", c["label"], flags=re.I).strip()


def _dims_like(c: dict[str, Any], patterns: tuple[str, ...], n: int) -> list[str]:
    """Business breakdowns only (no hour / date / id columns): one per pattern, in pattern order (so a worklist
    gets product line, DC and carrier, not category AND subcategory), then the rest to fill up."""
    dims = [d for d in c.get("dimensions") or [] if not re.search(r"HOUR|DATE|_ID$|_KEY$|YEAR|MONTH|WEEK|DAY", d["id"], re.I)]
    out = []
    for pat in patterns:
        hit = next((d for d in dims if d not in out and re.search(pat, d["id"].split(".")[-1], re.I)), None)
        if hit:
            out.append(hit)
    out += [d for d in dims if d not in out]
    return [d["label"] for d in out[:n]]


def data_brief(catalog: list[dict[str, Any]], limit: int = 2) -> list[str]:
    """Two lines under the prompt bar: what governed data this role can ask about."""
    feat = [c for c in catalog if c.get("featured")] or catalog[:1]
    lines = []
    for c in feat[:limit]:
        groups: dict[str, int] = {}
        for m in c["metrics"]:
            t = m.get("theme") or metric_theme(m["id"])
            if t not in ("plan", "other"):
                groups[t] = groups.get(t, 0) + 1
        themes = [theme_label(t).lower() for t, _ in sorted(groups.items(), key=lambda kv: -kv[1])[:5]]
        dims = _dims_like(c, (r"REGION|MARKET|COUNTRY", r"^CATEGORY$|CATEGORY", r"CHANNEL", r"STORE|DC|DEPARTMENT|CARRIER"), 4)
        kind = "measures drafted from facts" if c.get("adhoc") else "governed metrics"
        has_plan = any((m.get("theme") or metric_theme(m["id"])) == "plan" for m in c["metrics"])
        lines.append(f"{_domain(c)}: {len(c['metrics'])} {kind} on {', '.join(themes) or 'performance'}"
                     f"{' (with plan)' if has_plan else ''}, by {', '.join(d.lower() for d in dims) or 'segment'}"
                     f"{'; updating live' if 'live' in c['label'].lower() else ''}.")
    rest = [c for c in catalog if c not in feat[:limit]]
    if rest:
        names = list(dict.fromkeys(_domain(c) for c in rest))
        lines.append(f"Also available: {', '.join(names[:3])}{f' and {len(names) - 3} more' if len(names) > 3 else ''}.")
    return lines


PROMPTS = {
    "executives": "Build a one-page brief for leadership on {domain}: {mlist} year to date vs {base}, where we will "
                  "land by year end, and what drove the change.",
    "managers": "Weekly scorecard by {dim} for {domain}: {mlist} vs {base}. Flag the {dim}s in red and let me drill "
                "into what is driving them.",
    "daily_operations": "What is going wrong right now in {domain}? Today's {mlist} by hour vs the same day last "
                        "week, and a worklist by {wdims}.",
}
# the second request per audience is worded differently, so the two never read as the same sentence twice
PROMPTS_ALT = {
    "executives": "How is {domain} tracking on {mlist} this year against {base}, and what is driving the gap?",
    "managers": "Which {dim}s in {domain} are behind {base} this week on {mlist}, and why?",
    "daily_operations": "Show me what needs action this hour in {domain}: {mlist} by hour against a normal day, "
                        "worst first, by {wdims}.",
}
BASE = {"executives": ("plan", "last year"), "managers": ("plan", "last week"), "daily_operations": ("", "")}


def _say(labels: list[str]) -> str:
    """'Net Sales', 'Gross Margin Pct' -> 'net sales and gross margin %' (acronyms kept)."""
    words = [" ".join(w if w.isupper() and len(w) <= 4 else w.lower() for w in x.replace(" Pct", " %").split())
             for x in labels]
    return words[0] if len(words) == 1 else ", ".join(words[:-1]) + " and " + words[-1]


def starter_prompts(catalog: list[dict[str, Any]], per: int = 2) -> list[dict[str, Any]]:
    """Ready-to-edit requests per audience, written from the real metrics and dimensions of the featured data.
    Each names the headline metric of the audience's top themes (executives 2, managers 3, operations 2), so the
    request reads like that person would say it and the dashboard it builds leads with those metrics."""
    feat = [c for c in catalog if c.get("featured")] or catalog[:1]
    n_themes = {"executives": 2, "managers": 3, "daily_operations": 2}
    out = []
    for aud in ("executives", "managers", "daily_operations"):
        for k in range(per if feat else 0):
            c = feat[k % len(feat)]
            offset = (k // len(feat)) * n_themes[aud]          # same dataset again: its next themes
            th = audience_themes(c, aud, offset + n_themes[aud])[offset:]
            labels = list(dict.fromkeys(ms[0]["label"] for _, ms in th if ms))
            if not labels:
                continue
            has_plan = any((m.get("theme") or metric_theme(m["id"])) == "plan" for m in c["metrics"])
            dim = (_dims_like(c, (r"REGION|MARKET|COUNTRY|DEPARTMENT", r"STORE"), 1) or ["area"])[0].lower()
            wd = _dims_like(c, (r"SUBCATEGORY|PRODUCT_LINE", r"DISTRIBUTION|_DC$|^DC$|WAREHOUSE", r"CARRIER",
                                r"^CATEGORY$", r"CHANNEL|STORE|DEPARTMENT"), 3)
            text = (PROMPTS if k == 0 else PROMPTS_ALT)[aud].format(domain=_domain(c), mlist=_say(labels), dim=dim,
                                       base=BASE[aud][0 if has_plan else 1], wdims=_say(wd) if wd else dim)
            out.append({"audience": aud, "text": text, "semantic_view": c["fqn"], "metrics": labels,
                        "themes": [theme_label(t) for t, _ in th]})
    return out


def mentioned_metrics(model, text: str) -> list[str]:
    """Metric ids named in a typed request, in the order they are mentioned (longest names first, no overlaps:
    'online net sales' is not also 'net sales')."""
    low = " " + re.sub(r"[^a-z0-9%]+", " ", str(text or "").lower()) + " "
    cands = []
    for m in model.metrics:
        if m.name.upper().startswith(("HELPER_", "PLAN_")):
            continue
        for name in {m.label.lower(), m.name.lower().replace("_", " "), m.label.lower().replace(" pct", " %")}:
            name = re.sub(r"[^a-z0-9%]+", " ", name).strip()
            if len(name) > 2:
                cands.append((name, m.id))
    cands.sort(key=lambda t: -len(t[0]))
    taken, found = [False] * len(low), []
    for name, mid in cands:
        for hit in re.finditer(r"(?<= )" + re.escape(name) + r"(?= )", low):
            a, b = hit.span()
            if any(taken[a:b]):
                continue
            taken[a:b] = [True] * (b - a)
            found.append((a, mid))
    out = []
    for _, mid in sorted(found):
        if mid not in out:
            out.append(mid)
    return out


def _catalog_text(catalog: list[dict[str, Any]], limit: int = 25) -> str:
    """Each view with ALL its metrics grouped by theme, so Cortex can give each audience different themes."""
    lines = []
    for c in catalog[:limit]:
        groups: dict[str, list[str]] = {}
        for m in c["metrics"]:
            t = m.get("theme") or metric_theme(m["id"])
            if t != "plan":
                groups.setdefault(t, []).append(m["label"])
        themes = "\n".join(f"    {theme_label(t)}: {', '.join(ls[:8])}" for t, ls in groups.items())
        lines.append(f"- view: {c['fqn']} | domain: {c['label']}{' (test copy)' if c['test_like'] else ''}"
                     f"{' | FEATURED (live data)' if c.get('featured') else ''}"
                     f"{' | ' + c['comment'][:90] if c['comment'] else ''}\n"
                     f"  metric themes:\n{themes}\n"
                     f"  dimensions: {', '.join(d['label'] for d in c['dimensions'][:14])}")
    return "\n".join(lines)


AUDIENCE_BRIEF = (
    "Audiences and what each one owns:\n"
    "- executives: OUTCOMES - one-page brief, year to date vs plan, year-end outlook, what drove it "
    "(themes such as sales & growth, margin & profitability, channel mix, availability at a glance).\n"
    "- managers: the LEVERS their areas control - weekly scorecard by area vs plan, exceptions, drill-down "
    "(themes such as in-stock, on-time delivery, returns & discounts, basket and customers).\n"
    "- daily_operations: what BREAKS TODAY - live control room, pace by hour vs last week, worklist "
    "(themes such as stockouts and lost sales, late shipments, order pace, return spikes).\n")


VARIANCE = re.compile(r"^PLAN_|_VS_|VARIANCE|_GAP$|_DELTA$", re.I)


def _plain_metrics(labels: list[str], c: dict[str, Any]) -> list[str]:
    """Drop plan targets and variance metrics (e.g. 'Net Sales Vs Plan') from an idea: every tile already
    compares with plan or last year, so they would be compared twice."""
    ids = {m["label"].lower(): m["id"] for m in c.get("metrics") or []}
    return [x for x in labels if not VARIANCE.search(str(ids.get(str(x).lower(), str(x).upper().replace(" ", "_"))).split(".")[-1])]


def _top_up(idea: dict[str, Any], c: dict[str, Any]) -> dict[str, Any]:
    """An idea names 2-4 metrics of ONE theme: fill from the same theme when Cortex named fewer."""
    idea["metrics"] = _plain_metrics(idea["metrics"], c)
    ids = {m["label"]: m for m in c["metrics"]}
    themes = [ids[m].get("theme") or metric_theme(ids[m]["id"]) for m in idea["metrics"] if m in ids]
    theme = max(dict.fromkeys(themes), key=themes.count) if themes else (audience_themes(c, idea["audience"], 1) or [("other", [])])[0][0]
    if len(idea["metrics"]) < 2:
        pool = dict(audience_themes(c, idea["audience"], 12)).get(theme) or []
        idea["metrics"] = list(dict.fromkeys(idea["metrics"] + [m["label"] for m in pool]))[:3]
    idea["theme"] = theme
    return idea


def _rotation_text(catalog: list[dict[str, Any]], avoid: dict) -> str:
    """Per featured view and audience: the themes to use this time (not the ones already on screen)."""
    lines = []
    for c in [c for c in catalog if c.get("featured")]:
        for aud in ("executives", "managers", "daily_operations"):
            th = next_themes(c, aud, 3, avoid.get((c["fqn"], AUDIENCE_GROUP[aud]), set()))
            lines.append(f"- {c['fqn']} / {aud}: use themes {', '.join(theme_label(t) for t, _ in th)}")
    return "\n".join(lines)


def ai_suggestions(cortex, catalog: list[dict[str, Any]], avoid: Optional[dict] = None) -> list[dict[str, Any]]:
    """Cortex ideas: one audience x one metric theme each; themes never repeat within an audience on a dataset,
    and with `avoid` (themes on screen when the user clicks 'New ideas') the next themes in rotation are used."""
    from ai_services import _json_from_text
    avoid = avoid or {}
    feat_views = [c for c in catalog if c.get("featured")]
    per = min(8, 3 * max(1, len(feat_views)) + (1 if len(catalog) > len(feat_views) else 0))
    prompt = (
        "You are a BI lead proposing dashboards a business user can build from the Snowflake data below.\n"
        f"Available governed data (semantic views):\n{_catalog_text(catalog)}\n" + AUDIENCE_BRIEF
        + f"Propose {per} dashboards for EACH audience (audience ids: executives, managers, daily_operations). "
        "Every idea is one audience looking at one METRIC THEME: within an audience, each idea on the same view must "
        "use a DIFFERENT theme, picked for what that audience owns; do not reuse the same metrics across ideas of an "
        "audience. Each idea names 2-4 metrics from its theme. "
        + (f"EVERY FEATURED view ({', '.join(c['fqn'] for c in feat_views)}) must get 3 ideas (3 themes) for EACH "
           "audience; use other domains only for the rest. " if feat_views else
           "Spread them across DIFFERENT business domains where possible. ")
        + (("These themes are already on screen, so use exactly these themes this time (one idea each):\n"
            + _rotation_text(catalog, avoid) + "\n") if avoid and feat_views else "")
        + "Prefer non-test views, and use metric and dimension names exactly as listed.\n"
        "Each title is a short, specific promise in the audience's words (max 8 words, no view names). Detail names "
        "the metrics and what the user will learn (max 16 words). Goal is the instruction a dashboard designer would "
        "follow, naming the audience, the theme and the metrics.\n"
        'Respond with JSON only: {"suggestions": [{"audience": "executives", "theme": "<theme name>", "title": "", '
        '"detail": "", "metrics": ["<metric label>"], "semantic_view": "<view fqn from the list>", "domain": "<short '
        'domain name>", "goal": ""}]}')
    text, _ = cortex.complete(prompt)
    raw = _json_from_text(text).get("suggestions") or []
    by_fqn = {c["fqn"]: c for c in catalog}
    out, seen = [], set()
    for s in raw:
        if not isinstance(s, dict):
            continue
        fqn = str(s.get("semantic_view") or "").upper().replace('"', "")
        if fqn not in by_fqn:
            fqn = _resolve_view(fqn, by_fqn) or fqn       # Cortex wrote the view without its '#TABLE'
        aud = s.get("audience")
        if fqn not in by_fqn or aud not in AUDIENCES or not s.get("title"):
            continue                                  # validated: only real views and known audiences
        labels = {m["label"].lower(): m["label"] for m in by_fqn[fqn]["metrics"]}
        metrics = list(dict.fromkeys(labels[str(m).lower()] for m in (s.get("metrics") or [])
                                     if str(m).lower() in labels))[:4]
        idea = _top_up({"audience": aud, "title": str(s["title"])[:70], "detail": str(s.get("detail") or "")[:140],
                        "metrics": metrics, "semantic_view": fqn,
                        "domain": str(s.get("domain") or by_fqn[fqn]["label"])[:40],
                        "goal": str(s.get("goal") or s["title"])[:300], "by": "cortex"}, by_fqn[fqn])
        grp = AUDIENCE_GROUP[aud]
        key = fqn if by_fqn[fqn].get("featured") else "*other*"      # other datasets share one theme pool
        k = (key, grp, idea["theme"])
        skip = avoid.get((fqn, grp), set())
        if k in seen or (fqn, grp, frozenset(idea["metrics"])) in seen:
            continue                                  # same audience, same theme / metrics: one idea is enough
        if idea["theme"] in skip and len(skip) < len(audience_themes(by_fqn[fqn], aud, 99)):
            continue                                  # 'New ideas': this theme is already on screen
        seen.update({k, (fqn, grp, frozenset(idea["metrics"]))})
        out.append(idea)
    if len(out) < 3:
        raise ValueError("Cortex returned too few valid suggestions")
    return ensure_featured(out, catalog, avoid=avoid)


# --------------------------------------------------------------------------- routing
AUD_WORDS = (
    ("executives", r"\b(exec|executive|board|ceo|cfo|coo|leadership|c-suite|investor|company)\w*"),
    ("managers", r"\b(manager|team|scorecard|rep|territory|owner|department|regional manager)\w*"),
    ("weekly_business_review", r"\b(weekly|wbr|week over week|business review)\w*"),
    ("daily_operations", r"\b(ops|operation|operational|daily|today|yesterday|real.?time|live|hour)\w*"),
)


def keyword_route(catalog: list[dict[str, Any]], prompt: str) -> dict[str, Any]:
    words = set(re.findall(r"[a-z]{3,}", prompt.lower()))
    best, score = None, -1.0
    for c in catalog:
        vocab = " ".join([c["label"], c["comment"]] + [m["label"] for m in c["metrics"]]
                         + [d["label"] for d in c["dimensions"]]).lower()
        s = (sum(2.0 if w in c["label"].lower() else 1.0 for w in words if w in vocab) - (0.5 if c["test_like"] else 0)
             + (0.75 if c.get("featured") else 0))
        if s > score:
            best, score = c, s
    audience = next((a for a, p in AUD_WORDS if re.search(p, prompt, re.I)), "executives")
    return {"semantic_view": best["fqn"] if best else None, "audience": audience, "goal": prompt,
            "reason": "Matched your words to metric and dimension names.", "by": "keywords"}


def route(cortex, catalog: list[dict[str, Any]], prompt: str) -> dict[str, Any]:
    from ai_services import _json_from_text
    if not catalog:
        raise ValueError("No semantic view with metrics and a date dimension is visible to this role.")
    try:
        text, prov = cortex.complete(
            "Route a business user's request to the best governed dataset for a dashboard.\n"
            f"Request: {prompt}\nDatasets:\n{_catalog_text(catalog, 40)}\n"
            "Choose the ONE view whose metrics and dimensions best answer the request (prefer non-test views; when "
            "a FEATURED view can answer it, choose the featured view), "
            "and the audience: executives, managers, weekly_business_review or daily_operations. Rewrite the "
            "request as a clear goal for a dashboard designer, naming the relevant metrics and dimensions.\n"
            'Respond with JSON only: {"semantic_view": "<fqn>", "audience": "", "goal": "", '
            '"primary_metric": "<metric label>", "reason": "<one short sentence>"}')
        raw = _json_from_text(text)
        fqn = str(raw.get("semantic_view") or "").upper().replace('"', "")
        if fqn not in {c["fqn"] for c in catalog}:
            fqn = _resolve_view(fqn, {c["fqn"]: c for c in catalog}) or fqn
        if fqn not in {c["fqn"] for c in catalog}:
            raise ValueError("unknown view")
        aud = raw.get("audience") if raw.get("audience") in AUDIENCES else keyword_route(catalog, prompt)["audience"]
        return {"semantic_view": fqn, "audience": aud, "goal": str(raw.get("goal") or prompt)[:400],
                "primary_metric": str(raw.get("primary_metric") or ""), "reason": str(raw.get("reason") or "")[:200],
                "by": f"Cortex ({prov})"}
    except Exception:
        return keyword_route(catalog, prompt)


def pick_primary(model, hint: str, prompt: str) -> Optional[str]:
    """Metric the request is about (Cortex hint first, then words in the request)."""
    text = f"{hint} {prompt}".lower()
    best, best_len = None, 0
    for m in model.metrics:
        for cand in (m.label.lower(), m.name.lower().replace("_", " ")):
            if cand and cand in text and len(cand) > best_len:
                best, best_len = m.id, len(cand)
    return best
