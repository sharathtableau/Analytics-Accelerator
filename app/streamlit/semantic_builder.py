"""B1: draft a semantic view from a raw table — profile -> Cortex AI_COMPLETE draft -> validate -> human approves -> create.

Reuses the patterns proven on the retail view (and the Tableau accelerator's cortex_semantic.py):
  * real column names come from INFORMATION_SCHEMA, identifiers are quoted when needed;
  * the semantic view reads a source view whose columns are prefixed C_ so semantic names never collide with
    column names (the "cyclic reference" error);
  * metrics aggregate FACTS (SUM(t.f_x)), ratios are DIV0(metric, metric) — no raw columns inside metrics.
Cortex only proposes; every name, column and aggregation is checked here before any DDL is written.
"""
from __future__ import annotations

import json
import re
from typing import Any, Iterable, Optional

from semantic_catalog import FQN, quote_ident, row_dict, split_fqn

NUMERIC = ("NUMBER", "DECIMAL", "NUMERIC", "INT", "INTEGER", "BIGINT", "SMALLINT", "TINYINT", "BYTEINT",
           "FLOAT", "FLOAT4", "FLOAT8", "DOUBLE", "DOUBLE PRECISION", "REAL")
TIME = ("DATE", "DATETIME", "TIMESTAMP", "TIMESTAMP_NTZ", "TIMESTAMP_LTZ", "TIMESTAMP_TZ")
AGGS = {"SUM", "AVG", "MIN", "MAX", "COUNT", "COUNT_DISTINCT"}
NAME = re.compile(r"^[a-z][a-z0-9_]{0,59}$")
SKIP_PREFIX = ("AA_", "SV_SRC_", "WRK_", "SV_DDL")


def kind_of(data_type: str) -> str:
    t = (data_type or "").upper().split("(")[0].strip()
    if t in NUMERIC:
        return "number"
    if t in TIME:
        return "time"
    if t == "BOOLEAN":
        return "boolean"
    return "text"


def snake(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", str(text).lower()).strip("_")
    if not s or not s[0].isalpha():
        s = "x_" + s
    return s[:60]


def sq(text: Any) -> str:
    return "'" + str(text).replace("\\", "\\\\").replace("'", "''") + "'"


# ------------------------------------------------------------------------------------------- discovery
def list_tables(session, schemas: Iterable[str]) -> list[dict[str, Any]]:
    out = []
    for schema in schemas:
        db, sch = schema.split(".")
        try:
            rows = session.sql(
                f"SELECT TABLE_NAME, TABLE_TYPE, ROW_COUNT, TO_VARCHAR(LAST_ALTERED, 'YYYY-MM-DD') AS LAST_ALTERED, "
                f"COMMENT FROM {quote_ident(db)}.INFORMATION_SCHEMA.TABLES "
                "WHERE TABLE_SCHEMA = ? AND TABLE_TYPE IN ('BASE TABLE', 'VIEW') ORDER BY TABLE_NAME",
                params=[sch.upper()]).collect()
        except Exception:
            continue
        for r in rows:
            d = row_dict(r)
            name = str(d.get("table_name") or "")
            if not name or name.upper().startswith(SKIP_PREFIX):
                continue
            out.append({"fqn": f"{db}.{sch}.{name}".upper() if re.fullmatch(r"[A-Za-z0-9_$]+", name)
                        else f'{db}.{sch}."{name}"', "name": name, "schema": f"{db}.{sch}",
                        "type": d.get("table_type"), "rows": d.get("row_count"),
                        "altered": d.get("last_altered"), "comment": (d.get("comment") or "")[:200]})
    return out


def profile_table(session, fqn: str, max_cols: int = 60) -> dict[str, Any]:
    """Columns + row count + distinct counts, null share, samples (text) and ranges (number/time)."""
    db, sch, tbl = split_fqn(fqn)
    cols = [row_dict(r) for r in session.sql(
        f"SELECT COLUMN_NAME, DATA_TYPE, COMMENT FROM {quote_ident(db)}.INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? ORDER BY ORDINAL_POSITION",
        params=[sch.replace('"', ""), tbl.replace('"', "")]).collect()][:max_cols]
    if not cols:
        raise ValueError(f"No readable columns in {fqn}")
    exprs = ["COUNT(*) AS N__ROWS"]
    for i, c in enumerate(cols):
        q = quote_ident(c["column_name"])
        k = kind_of(c["data_type"])
        exprs.append(f"APPROX_COUNT_DISTINCT({q}) AS D{i}")
        exprs.append(f"COUNT_IF({q} IS NULL) AS N{i}")
        if k in ("number", "time"):
            exprs.append(f"TO_VARCHAR(MIN({q})) AS LO{i}")
            exprs.append(f"TO_VARCHAR(MAX({q})) AS HI{i}")
        else:
            exprs.append(f"ARRAY_SLICE(ARRAY_AGG(DISTINCT TO_VARCHAR({q})) WITHIN GROUP (ORDER BY TO_VARCHAR({q})), 0, 6) AS S{i}")
    sample = f"(SELECT * FROM {fqn} LIMIT 200000)"
    stats = row_dict(session.sql(f"SELECT {', '.join(exprs)} FROM {sample}").collect()[0])
    n = int(stats.get("n__rows") or 0)
    out = []
    for i, c in enumerate(cols):
        samples = stats.get(f"s{i}")
        if isinstance(samples, str):
            try:
                samples = json.loads(samples)
            except Exception:
                samples = [samples]
        out.append({"column": c["column_name"], "type": c["data_type"], "kind": kind_of(c["data_type"]),
                    "distinct": int(stats.get(f"d{i}") or 0), "nulls": int(stats.get(f"n{i}") or 0),
                    "min": stats.get(f"lo{i}"), "max": stats.get(f"hi{i}"), "samples": (samples or [])[:6],
                    "comment": c.get("comment") or ""})
    return {"fqn": fqn, "table": tbl.replace('"', ""), "rows_profiled": n, "columns": out}


# ------------------------------------------------------------------------------------------- Cortex draft
def draft_prompt(profile: dict[str, Any]) -> str:
    lines = []
    for c in profile["columns"]:
        extra = (f"range {c['min']} .. {c['max']}" if c["kind"] in ("number", "time")
                 else f"e.g. {', '.join(str(x) for x in c['samples'][:4])}")
        lines.append(f"- {c['column']} | {c['kind']} | {c['distinct']} distinct | {c['nulls']} nulls | {extra}"
                     + (f" | comment: {c['comment']}" if c["comment"] else ""))
    return (
        "You design a Snowflake semantic view for business users from one table. Use ONLY the columns listed.\n"
        f"Table: {profile['fqn']} ({profile['rows_profiled']} rows profiled)\nColumns (name | kind | distinct | nulls | values):\n"
        + "\n".join(lines) + "\n"
        "Rules: dimensions are columns people group or filter by (text, boolean, dates, low-cardinality codes); "
        "the main business date is the time dimension; metrics aggregate numeric columns (SUM for amounts and "
        "quantities, AVG for rates/durations/scores, COUNT_DISTINCT for ids); add a 'row_count' metric with agg "
        "COUNT and column null; ratios divide two of your metrics. Names are lower_snake_case business terms, "
        "never the raw column name with prefixes. Every item gets a one-sentence business definition and 1-3 "
        "synonyms. Propose 3-6 verified questions a manager would ask.\n"
        'Respond with JSON only: {"view_name": "", "description": "", "time_dimension": "<column>", '
        '"dimensions": [{"column": "", "name": "", "synonyms": [], "comment": ""}], '
        '"metrics": [{"name": "", "agg": "SUM|AVG|MIN|MAX|COUNT|COUNT_DISTINCT", "column": "<column or null>", '
        '"synonyms": [], "comment": ""}], "ratios": [{"name": "", "numerator": "<metric name>", '
        '"denominator": "<metric name>", "comment": ""}], "questions": [""]}')


def fallback_draft(profile: dict[str, Any]) -> dict[str, Any]:
    """Deterministic draft when Cortex is unavailable: text/bool/time -> dimensions, numbers -> SUM metrics."""
    dims, mets, time_col = [], [{"name": "row_count", "agg": "COUNT", "column": None, "synonyms": ["records"],
                                 "comment": "Number of rows."}], None
    for c in profile["columns"]:
        if c["kind"] == "time" and not time_col:
            time_col = c["column"]
        if c["kind"] in ("text", "boolean", "time") or (c["kind"] == "number" and c["distinct"] <= 12):
            dims.append({"column": c["column"], "name": snake(c["column"]), "synonyms": [],
                         "comment": c["comment"] or f"{c['column']} from {profile['table']}."})
        elif c["kind"] == "number":
            looks_id = bool(re.search(r"(^|_)(id|key|code)$", c["column"].lower()))
            mets.append({"name": snake(c["column"]) + ("_count" if looks_id else "_total"),
                         "agg": "COUNT_DISTINCT" if looks_id else "SUM", "column": c["column"], "synonyms": [],
                         "comment": c["comment"] or f"{'Distinct' if looks_id else 'Total'} {c['column']}."})
    return {"view_name": snake(profile["table"]), "description": f"Business view of {profile['fqn']}.",
            "time_dimension": time_col, "dimensions": dims, "metrics": mets, "ratios": [], "questions": []}


def validate_draft(draft: dict[str, Any], profile: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    """Keep only what is real and well-formed; every change is logged for the reviewer."""
    cols = {c["column"].upper(): c for c in profile["columns"]}
    notes: list[dict[str, str]] = []
    used: set[str] = set()

    renamed: dict[str, str] = {}

    def name_ok(raw: str, what: str) -> Optional[str]:
        # Source columns are exposed as C_<col> and facts as f_<col>, so only those prefixes and duplicates clash.
        n = snake(raw or "")
        if n.startswith(("c_", "f_")) or n in used:
            n2 = (n[2:] if n.startswith(("c_", "f_")) else n) + ("_dim" if what == "dimension" else "_value")
            notes.append({"item": raw, "action": "renamed", "why": f"'{n}' clashes with an internal or existing name -> '{n2}'"})
            if n not in used:                 # prefix clash: references to the old name follow the rename
                renamed[n] = n2
            n = n2
        if not NAME.match(n) or n in used:
            notes.append({"item": raw, "action": "dropped", "why": "invalid or duplicate name"})
            return None
        used.add(n)
        return n

    dims = []
    for d in draft.get("dimensions") or []:
        c = cols.get(str(d.get("column") or "").upper())
        if not c:
            notes.append({"item": str(d.get("name")), "action": "dropped", "why": f"column {d.get('column')!r} does not exist"})
            continue
        n = name_ok(d.get("name") or c["column"], "dimension")
        if n:
            dims.append({"column": c["column"], "name": n, "kind": c["kind"],
                         "synonyms": [str(x)[:40] for x in (d.get("synonyms") or [])][:3],
                         "comment": str(d.get("comment") or "")[:300], "include": True})
    mets = []
    for m in draft.get("metrics") or []:
        agg = str(m.get("agg") or "").upper().replace(" ", "_")
        col = m.get("column")
        c = cols.get(str(col or "").upper()) if col else None
        if agg not in AGGS:
            notes.append({"item": str(m.get("name")), "action": "dropped", "why": f"unknown aggregation {agg!r}"})
            continue
        if agg != "COUNT" and not c:
            notes.append({"item": str(m.get("name")), "action": "dropped", "why": f"column {col!r} does not exist"})
            continue
        if agg in ("SUM", "AVG") and c and c["kind"] != "number":
            notes.append({"item": str(m.get("name")), "action": "repaired", "why": f"{agg} on a {c['kind']} column -> COUNT_DISTINCT"})
            agg = "COUNT_DISTINCT"
        n = name_ok(m.get("name") or (c["column"] if c else "row_count"), "metric")
        if n:
            mets.append({"name": n, "agg": agg, "column": c["column"] if c else None,
                         "synonyms": [str(x)[:40] for x in (m.get("synonyms") or [])][:3],
                         "comment": str(m.get("comment") or "")[:300], "include": True})
    if not mets:
        mets.append({"name": "row_count", "agg": "COUNT", "column": None, "synonyms": ["records"],
                     "comment": "Number of rows.", "include": True})
    names = {m["name"] for m in mets}
    ratios = []
    for r in draft.get("ratios") or []:
        num, den = snake(r.get("numerator") or ""), snake(r.get("denominator") or "")
        num, den = renamed.get(num, num), renamed.get(den, den)
        if num not in names or den not in names or num == den:
            notes.append({"item": str(r.get("name")), "action": "dropped", "why": "ratio must divide two of the view's metrics"})
            continue
        n = name_ok(r.get("name") or f"{num}_per_{den}", "metric")
        if n:
            ratios.append({"name": n, "numerator": num, "denominator": den,
                           "comment": str(r.get("comment") or f"{num} / {den}")[:300], "include": True})
    tcol = cols.get(str(draft.get("time_dimension") or "").upper())
    if tcol and tcol["kind"] != "time":
        notes.append({"item": tcol["column"], "action": "repaired", "why": "time dimension must be a date/timestamp"})
        tcol = None
    if not tcol:
        tcol = next((c for c in profile["columns"] if c["kind"] == "time"), None)
    if tcol and not any(d["column"] == tcol["column"] for d in dims):
        dims.insert(0, {"column": tcol["column"], "name": name_ok(tcol["column"], "dimension") or "event_date",
                        "kind": "time", "synonyms": ["date"], "comment": "Main business date.", "include": True})
    view = snake(draft.get("view_name") or profile["table"])
    return ({"view_name": view, "description": str(draft.get("description") or "")[:400],
             "time_dimension": tcol["column"] if tcol else None, "dimensions": dims, "metrics": mets,
             "ratios": ratios, "questions": [str(q)[:200] for q in (draft.get("questions") or [])][:6]}, notes)


def draft(cortex, profile: dict[str, Any]) -> dict[str, Any]:
    from ai_services import _json_from_text
    origin = "cortex"
    try:
        text, _ = cortex.complete(draft_prompt(profile))
        raw = _json_from_text(text)
        if not raw.get("dimensions") and not raw.get("metrics"):
            raise ValueError("empty draft")
    except Exception:
        raw, origin = fallback_draft(profile), "profile-fallback"
    clean, notes = validate_draft(raw, profile)
    return {**clean, "origin": origin, "notes": notes}


# ------------------------------------------------------------------------------------------- DDL
def build_ddl(spec: dict[str, Any], profile: dict[str, Any], target_schema: str) -> dict[str, str]:
    """Source view with C_-prefixed columns + CREATE SEMANTIC VIEW over it. spec = validated (and reviewed) draft."""
    if not re.fullmatch(r"[A-Za-z0-9_$]+\.[A-Za-z0-9_$]+", target_schema):
        raise ValueError("target schema")
    base = re.sub(r"[^A-Z0-9_]", "_", spec["view_name"].upper())[:50] or "SOURCE"
    src = f"{target_schema}.AA_SRC_{base}".upper()
    sv = f"{target_schema}.AA_{base}_SV".upper()
    alias = "t"
    cols = {c["column"]: c for c in profile["columns"]}
    used_cols = set()
    dims = [d for d in spec["dimensions"] if d.get("include", True) and d["column"] in cols]
    mets = [m for m in spec["metrics"] if m.get("include", True) and (m["column"] in cols or m["agg"] == "COUNT")]
    keep = {m["name"] for m in mets}
    ratios = [r for r in spec.get("ratios", []) if r.get("include", True) and r["numerator"] in keep and r["denominator"] in keep]
    if not mets:
        raise ValueError("Select at least one metric")
    for d in dims:
        used_cols.add(d["column"])
    for m in mets:
        if m["column"]:
            used_cols.add(m["column"])
    c_name = {c: "C_" + re.sub(r"[^A-Z0-9_]", "_", c.upper()) for c in used_cols}
    view_sql = (f"CREATE OR REPLACE VIEW {src} COMMENT = {sq('Analytics Accelerator source view for ' + profile['fqn'])} AS SELECT "
                + ", ".join(f"{quote_ident(c)} AS {c_name[c]}" for c in sorted(used_cols)) + ", 1 AS C__ROW"
                + f" FROM {profile['fqn']}")

    def syn(items):
        items = [s for s in items if s]
        return f" WITH SYNONYMS = ({', '.join(sq(s) for s in items)})" if items else ""

    facts, metric_lines = [f"    {alias}.f__row AS C__ROW"], []
    fact_for = {}
    for m in mets:
        if m["column"] and m["column"] not in fact_for:
            f = "f_" + snake(m["column"])[:55]
            fact_for[m["column"]] = f
            facts.append(f"    {alias}.{f} AS {c_name[m['column']]}")
    for m in mets:
        f = fact_for.get(m["column"])
        expr = {"SUM": f"SUM({alias}.{f})", "AVG": f"AVG({alias}.{f})", "MIN": f"MIN({alias}.{f})",
                "MAX": f"MAX({alias}.{f})", "COUNT_DISTINCT": f"COUNT(DISTINCT {alias}.{f})",
                "COUNT": f"SUM({alias}.f__row)" if not f else f"COUNT({alias}.{f})"}[m["agg"]]
        metric_lines.append(f"    {alias}.{m['name']} AS {expr}{syn(m['synonyms'])}"
                            + (f"\n      COMMENT = {sq(m['comment'])}" if m["comment"] else ""))
    for r in ratios:
        metric_lines.append(f"    {alias}.{r['name']} AS DIV0({alias}.{r['numerator']}, {alias}.{r['denominator']})"
                            + (f"\n      COMMENT = {sq(r['comment'])}" if r["comment"] else ""))
    dim_lines = [f"    {alias}.{d['name']} AS {c_name[d['column']]}{syn(d['synonyms'])}"
                 + (f"\n      COMMENT = {sq(d['comment'])}" if d["comment"] else "") for d in dims]
    parts = [f"CREATE OR REPLACE SEMANTIC VIEW {sv}",
             f"  TABLES (\n    {alias} AS {src}\n      COMMENT = {sq(spec.get('description') or 'Source rows')}\n  )",
             "  FACTS (\n" + ",\n".join(facts) + "\n  )"]
    if dim_lines:
        parts.append("  DIMENSIONS (\n" + ",\n".join(dim_lines) + "\n  )")
    parts.append("  METRICS (\n" + ",\n".join(metric_lines) + "\n  )")
    parts.append(f"  COMMENT = {sq((spec.get('description') or '') + ' (drafted by Cortex, approved in Analytics Accelerator)')}")
    test_metric = mets[0]["name"]
    test_dim = dims[0]["name"] if dims else None
    test_sql = (f"SELECT * FROM SEMANTIC_VIEW({sv} METRICS {alias}.{test_metric}"
                + (f" DIMENSIONS {alias}.{test_dim}" if test_dim else "") + ") LIMIT 5")
    return {"source_view": src, "semantic_view": sv, "view_sql": view_sql, "sv_sql": "\n".join(parts),
            "test_sql": test_sql}


def create(session, ddl: dict[str, str]) -> dict[str, Any]:
    session.sql(ddl["view_sql"]).collect()
    session.sql(ddl["sv_sql"]).collect()
    rows = [row_dict(r) for r in session.sql(ddl["test_sql"]).collect()]
    return {"semantic_view": ddl["semantic_view"], "test_rows": rows[:5]}
