"""Finding the right tables in a big account (Connect a table): metadata only, nothing is scanned.

* catalog(): every readable table with rows, columns, last change, comment; which existing semantic views
  already use it ("covered" - leverage those instead of rebuilding); and which tables join with which
  (they share an id-like column, or A has <B>_ID and B has ID).
* suggest(): Cortex AI_COMPLETE reads names, comments and column names and picks the tables for a business
  question. Only listed tables can come back.
"""
from __future__ import annotations

import json
import re
from typing import Any, Iterable, Optional

from semantic_catalog import quote_fqn, quote_ident, row_dict

IDLIKE = re.compile(r"(^|_)(ID|KEY|CODE|SKU|NO|NUMBER)$", re.I)
TINY = 50
# Tables the app, other tools or ETL leave behind: hidden by default (shown by a toggle, or when searched for).
SYSTEMISH = re.compile(r"^(AA_|AI_BI_STUDIO_|AI_DECISION_FACTORY_|TMP_|TEMP_|TEST_)|(_CACHE|_LOGS?|_AUDIT|_BKP|_BACKUP|_TMP|_TEMP)$", re.I)
_STOP = {"the", "and", "for", "by", "of", "to", "in", "on", "with", "data", "table", "tables", "show", "me", "my", "all",
         "per", "from", "what", "how", "many", "much", "analyze", "analysis"}
MAX_SUGGEST = 6


def _singular(name: str) -> str:
    n = name.upper()
    for suf, rep in (("IES", "Y"), ("SES", "S"), ("S", "")):
        if n.endswith(suf) and len(n) > len(suf) + 1:
            return n[: -len(suf)] + rep
    return n


def columns_by_table(session, schemas: Iterable[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for schema in schemas:
        db, sch = schema.split(".")
        try:
            rows = session.sql(
                f"SELECT TABLE_NAME, COLUMN_NAME FROM {quote_ident(db)}.INFORMATION_SCHEMA.COLUMNS "
                "WHERE TABLE_SCHEMA = ? ORDER BY TABLE_NAME, ORDINAL_POSITION", params=[sch.upper()]).collect()
        except Exception:
            continue
        for r in rows:
            d = row_dict(r)
            t = str(d.get("table_name") or "")
            fqn = f"{db}.{sch}.{t}".upper() if re.fullmatch(r"[A-Za-z0-9_$]+", t) else f'{db}.{sch}."{t}"'
            out.setdefault(fqn, []).append(str(d.get("column_name") or ""))
    return out


def covered_by_views(session, sources: list[dict[str, Any]], app_schema: str) -> dict[str, list[str]]:
    """Base table -> semantic views already built on it. The app's own source views (AA_SRC_...) are mapped
    back to the table they read, from their comment."""
    src_of: dict[str, str] = {}
    try:
        db, sch = app_schema.split(".")
        for r in session.sql(f"SELECT TABLE_NAME, COMMENT FROM {quote_ident(db)}.INFORMATION_SCHEMA.VIEWS "
                             "WHERE TABLE_SCHEMA = ? AND TABLE_NAME LIKE 'AA_SRC_%'", params=[sch.upper()]).collect():
            d = row_dict(r)
            m = re.search(r"source view for (\S+)$", str(d.get("comment") or ""))
            if m:
                src_of[f"{app_schema}.{d.get('table_name')}".upper()] = m.group(1).upper()
    except Exception:
        pass
    out: dict[str, list[str]] = {}
    for s in (sources or [])[:30]:
        fqn = s.get("fqn") if isinstance(s, dict) else str(s)
        if not fqn or "#" in fqn:
            continue
        try:
            rows = [row_dict(r) for r in session.sql(f"DESCRIBE SEMANTIC VIEW {quote_fqn(fqn)}").collect()]
        except Exception:
            continue
        parts: dict[str, dict[str, str]] = {}
        for d in rows:
            if str(d.get("object_kind") or "").upper() != "TABLE":
                continue
            prop = str(d.get("property") or "").upper()
            if prop in ("BASE_TABLE_DATABASE_NAME", "BASE_TABLE_SCHEMA_NAME", "BASE_TABLE_NAME"):
                parts.setdefault(str(d.get("object_name")), {})[prop] = str(d.get("property_value") or "")
        label = fqn.split(".")[-1]
        for p in parts.values():
            if not p.get("BASE_TABLE_NAME"):
                continue
            base = ".".join(x for x in (p.get("BASE_TABLE_DATABASE_NAME"), p.get("BASE_TABLE_SCHEMA_NAME"),
                                         p["BASE_TABLE_NAME"]) if x).upper()
            for key in {base, src_of.get(base, base)}:
                if label not in out.setdefault(key, []):
                    out[key].append(label)
    return out


def related(tables: list[dict[str, Any]], limit: int = 8) -> dict[str, list[dict[str, str]]]:
    """Which tables can join: a shared id-like column (CUSTOMER_ID in both), or A.<B>_ID with B.ID."""
    info = []
    for t in tables:
        cols = {c.upper() for c in t.get("columns") or []}
        info.append((t["fqn"], t["name"].upper(), cols, {c for c in cols if IDLIKE.search(c)}))
    out: dict[str, list[dict[str, str]]] = {}
    for fa, na, ca, ida in info:
        hits = []
        for fb, nb, cb, idb in info:
            if fa == fb:
                continue
            via = sorted(c for c in ida & cb if c not in ("ID", "KEY", "CODE", "NO", "NUMBER"))
            for c in (_singular(nb), _singular(na)):                # CARRIER in SHIPMENTS and in CARRIERS
                if c in ca and c in cb and c not in via:
                    via.append(c)
            if not via:
                single = _singular(nb)
                via = [f"{c} = {nb}.{c.rsplit('_', 1)[-1]}" for c in ida
                       if c.startswith(single + "_") and c.rsplit("_", 1)[-1] in cb]
                via += [f"{na}.{c.rsplit('_', 1)[-1]} = {c}" for c in idb
                        if c.startswith(_singular(na) + "_") and c.rsplit("_", 1)[-1] in ca]
            if via:
                hits.append({"fqn": fb, "via": ", ".join(via[:2])})
        if hits:
            out[fa] = hits[:limit]
    return out


def catalog(session, tables: list[dict[str, Any]], schemas: Iterable[str], sources: list, app_schema: str) -> dict:
    schemas = list(schemas)
    cols = columns_by_table(session, schemas)
    covered = covered_by_views(session, sources, app_schema)
    for t in tables:
        c = cols.get(t["fqn"].upper()) or cols.get(t["fqn"]) or []
        t["columns"] = c[:400]
        t["cols"] = len(c)
        t["covered"] = covered.get(t["fqn"].upper(), [])
        rows = t.get("rows")
        t["tiny"] = rows is not None and int(rows or 0) < TINY
        t["empty"] = rows is not None and int(rows or 0) == 0
        t["system"] = bool(SYSTEMISH.search(t["name"]))
        t["view"] = str(t.get("type") or "").upper() == "VIEW"
    rel = related(tables)
    linked = set(rel) | {h["fqn"] for hits in rel.values() for h in hits}
    for t in tables:              # small lookup tables (regions, carriers) stay; small tables that join nothing hide
        t["tiny"] = t["tiny"] and t["fqn"] not in linked
    return {"tables": tables, "related": rel}


# ----------------------------------------------------------------------------------------- Cortex suggest
def suggest_prompt(tables: list[dict[str, Any]], question: str) -> str:
    lines, size = [], 0
    for t in sorted(tables, key=lambda x: (x.get("empty", False), x.get("tiny", False), x["fqn"])):
        if t.get("empty"):
            continue
        line = (f"- {t['fqn']} | {t.get('rows') if t.get('rows') is not None else '?'} rows"
                + (f" | {str(t.get('comment'))[:100]}" if t.get("comment") else "")
                + f" | columns: {', '.join((t.get('columns') or [])[:20])}")
        size += len(line)
        if size > 24000:
            break
        lines.append(line)
    return (
        "A business user wants to analyze something in Snowflake. Pick the tables (1 to 6) that together answer "
        "it: the table with the facts (transactions, events, amounts) plus the lookup tables it joins to (customers, "
        "products, stores, dates ...). Prefer tables that share id columns. Use ONLY tables from the list, exactly "
        "as written.\n"
        f"Question: {question[:400]}\n\nTables (fqn | rows | comment | columns):\n" + "\n".join(lines) + "\n\n"
        'Respond with JSON only: {"tables": [{"fqn": "", "why": "<one short reason>"}], '
        '"note": "<one sentence, e.g. what is missing>"}')


def nearest(tables: list[dict[str, Any]], question: str, limit: int = 4) -> list[dict[str, str]]:
    """Fallback when Cortex finds nothing: tables whose name, comment or columns share words with the question."""
    words = {w for w in re.findall(r"[a-z0-9]{3,}", question.lower()) if w not in _STOP}
    scored = []
    for t in tables:
        if t.get("empty") or t.get("system"):
            continue
        name = t["name"].lower()
        hay_c = f"{t.get('comment') or ''} {' '.join(t.get('columns') or [])}".lower()
        hits = [w for w in words if w in name]
        sc = 3 * len(hits) + sum(1 for w in words if w in hay_c and w not in hits)
        if sc:
            scored.append((-sc, t["fqn"], t["name"], hits or [w for w in words if w in hay_c][:2]))
    scored.sort()
    return [{"fqn": f, "why": "matches '" + "', '".join(h[:2]) + "'"} for _, f, _, h in scored[:limit]]


def suggest(cortex, tables: list[dict[str, Any]], question: str) -> dict[str, Any]:
    from ai_services import _json_from_text
    question = (question or "").strip()
    if not question:
        raise ValueError("Describe what you want to analyze, e.g. 'online orders by customer and product'.")
    text, prov = cortex.complete(suggest_prompt(tables, question))
    raw = _json_from_text(text) or {}
    listed = {t["fqn"].upper(): t["fqn"] for t in tables}
    picked, seen = [], set()
    for item in raw.get("tables") or []:
        if not isinstance(item, dict):
            continue
        f = listed.get(str(item.get("fqn") or "").upper())
        if f and f not in seen:
            seen.add(f)
            picked.append({"fqn": f, "why": str(item.get("why") or "")[:160]})
    near = [] if picked else nearest(tables, question)
    return {"question": question[:400], "tables": picked[:MAX_SUGGEST], "note": str(raw.get("note") or "")[:240],
            "nearest": near, "provenance": prov, "ignored": max(0, len(raw.get("tables") or []) - len(picked))}
