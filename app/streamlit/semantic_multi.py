"""B6: one semantic view over several tables - profile, find the joins, Cortex drafts, checks, one approval, create.

Automatic except the approval click:
  1. Profile every table (semantic_builder.profile_table).
  2. Keys: declared primary keys (SHOW PRIMARY KEYS) or columns that look unique in the profile; a key is only
     used after an EXACT check in Snowflake (COUNT(*) = COUNT(DISTINCT key), no NULLs).
  3. Joins: a column of table A that matches the key of table B by name (CUSTOMER_ID -> CUSTOMERS.CUSTOMER_ID,
     CUSTOMERS.ID). Each join is checked: key unique on B (otherwise rows multiply and totals double count:
     the join is dropped) and coverage (share of A's values found in B: a warning below 95%).
  4. Cortex AI_COMPLETE drafts dimensions, metrics, synonyms and definitions per table; it can drop a proposed
     join but never invent one. The single-table validator checks every item; names are made unique.
  5. A person approves. The app creates one source view per table and the semantic view (TABLES with PRIMARY
     KEY, RELATIONSHIPS ... REFERENCES - the syntax of the retail view), test-queries a join through
     SEMANTIC_VIEW() and reconciles every SUM metric with the base table.
"""
from __future__ import annotations

import json
import re
from typing import Any, Optional

import semantic_builder as sb
from semantic_catalog import quote_ident, row_dict, split_fqn

MAX_TABLES = 8
COVERAGE_WARN = 0.95
KEYLIKE = re.compile(r"(^|_)(ID|KEY|CODE|SKU|NO|NUMBER)$", re.I)


# ------------------------------------------------------------------------------------------- keys
def _singular(name: str) -> str:
    n = name.upper()
    for suf, rep in (("IES", "Y"), ("SES", "S"), ("S", "")):
        if n.endswith(suf) and len(n) > len(suf) + 1:
            return n[: -len(suf)] + rep
    return n


def declared_keys(session, fqn: str) -> list[str]:
    try:
        rows = [row_dict(r) for r in session.sql(f"SHOW PRIMARY KEYS IN TABLE {fqn}").collect()]
        return [str(r.get("column_name")) for r in sorted(rows, key=lambda r: int(r.get("key_sequence") or 0))]
    except Exception:
        return []


def key_candidates(profile: dict[str, Any]) -> list[str]:
    """Single columns that look unique and complete in the (approximate) profile, id-like names first."""
    n = profile["rows_profiled"] or 0
    cands = [c for c in profile["columns"] if n and c["nulls"] == 0 and c["kind"] in ("number", "text")
             and c["distinct"] >= 0.97 * n]
    cands.sort(key=lambda c: (not KEYLIKE.search(c["column"]), c["kind"] != "number", c["column"]))
    return [c["column"] for c in cands]


def exact_unique(session, fqn: str, col: str) -> dict[str, Any]:
    q = quote_ident(col)
    r = row_dict(session.sql(f"SELECT COUNT(*) AS N, COUNT(DISTINCT {q}) AS D, COUNT_IF({q} IS NULL) AS Z "
                             f"FROM {fqn}").collect()[0])
    n, d, z = int(r.get("n") or 0), int(r.get("d") or 0), int(r.get("z") or 0)
    return {"unique": n > 0 and n == d and z == 0, "rows": n, "distinct": d, "nulls": z}


def coverage(session, a_fqn: str, a_col: str, b_fqn: str, b_col: str) -> float:
    """Share of A's non-null join values that exist in B (up to 1M rows of A)."""
    a, b = quote_ident(a_col), quote_ident(b_col)
    r = row_dict(session.sql(
        f"SELECT COUNT_IF(s.v IS NOT NULL) AS N, COUNT_IF(s.v IS NOT NULL AND k.v IS NULL) AS MISS "
        f"FROM (SELECT {a} AS v FROM {a_fqn} LIMIT 1000000) s "
        f"LEFT JOIN (SELECT DISTINCT {b} AS v FROM {b_fqn}) k ON s.v = k.v").collect()[0])
    n, miss = int(r.get("n") or 0), int(r.get("miss") or 0)
    return 1.0 if n == 0 else round(1 - miss / n, 4)


def aliases(profiles: list[dict[str, Any]]) -> list[str]:
    out = []
    for p in profiles:
        a = sb.snake(p["table"])[:28]
        base, i = a, 2
        while a in out:
            a, i = f"{base}_{i}", i + 1
        out.append(a)
    return out


def _match(a_col: str, b_table: str, b_key: str) -> Optional[int]:
    """How strongly column a_col of A looks like a reference to B's key (lower = stronger); None = no match."""
    ac, bk, single = a_col.upper(), b_key.upper(), _singular(b_table)
    if ac == bk and bk not in ("ID", "KEY", "CODE"):
        return 0
    if bk in ("ID", "KEY", "CODE") and ac in (f"{single}_{bk}", f"{b_table.upper()}_{bk}"):
        return 1
    if ac == f"{single}_{bk}" or ac.endswith("_" + bk) and ac.startswith(single):
        return 2
    return None


def find_relationships(session, profiles: list[dict[str, Any]], als: list[str]) -> tuple[list[dict], dict, list[dict]]:
    """Proposed joins (each checked), the key of every referenced table, and the checks for the reviewer."""
    keys: dict[str, Optional[str]] = {}
    checks: list[dict[str, str]] = []
    for p, a in zip(profiles, als):
        cands = declared_keys(session, p["fqn"])[:1] or key_candidates(p)[:3]
        keys[a] = None
        for c in cands:
            u = exact_unique(session, p["fqn"], c)
            if u["unique"]:
                keys[a] = c
                checks.append({"check": f"{a}: key {c}", "status": "ok",
                               "detail": f"{u['rows']:,} rows, {u['distinct']:,} distinct, no blanks"})
                break
        if keys[a] is None:
            checks.append({"check": f"{a}: key", "status": "info",
                           "detail": "no single unique column: this table can only point to others, not be joined to"})
    rels: list[dict[str, Any]] = []
    for pa, a in zip(profiles, als):
        kinds = {c["column"]: c["kind"] for c in pa["columns"]}
        for pb, b in zip(profiles, als):
            if a == b or not keys[b]:
                continue
            bkind = next((c["kind"] for c in pb["columns"] if c["column"] == keys[b]), None)
            best = None
            for col, kind in kinds.items():
                if col == keys[a] and keys[a].upper() == keys[b].upper():
                    continue                                   # its own key with the same name: 1:1 twin, skip
                score = _match(col, pb["table"], keys[b])
                if score is not None and kind == bkind and (best is None or score < best[0]):
                    best = (score, col)
            if not best:
                continue
            if any(r["from"] == b and r["to"] == a for r in rels):
                continue                                       # one direction only
            cov = coverage(session, pa["fqn"], best[1], pb["fqn"], keys[b])
            rel = {"name": f"{a}_to_{b}"[:60], "from": a, "from_col": best[1], "to": b, "to_col": keys[b],
                   "coverage": cov, "include": True}
            rels.append(rel)
            checks.append({"check": f"join {a}.{best[1]} → {b}.{keys[b]}",
                           "status": "ok" if cov >= COVERAGE_WARN else "warn",
                           "detail": (f"{b}.{keys[b]} is unique, so totals of {a} are not multiplied; "
                                      f"{cov:.1%} of {a} values found in {b}")
                           + ("" if cov >= COVERAGE_WARN else " (rows without a match drop out when grouped by "
                              f"{b} columns)")})
    return rels, keys, checks


# ------------------------------------------------------------------------------------------- Cortex draft
def draft_prompt(profiles: list[dict[str, Any]], als: list[str], rels: list[dict[str, Any]],
                 keys: dict[str, Optional[str]]) -> str:
    blocks = []
    for p, a in zip(profiles, als):
        lines = [f"Table {a} = {p['fqn']} ({p['rows_profiled']} rows; key: {keys.get(a) or 'none'})"]
        for c in p["columns"]:
            extra = (f"range {c['min']} .. {c['max']}" if c["kind"] in ("number", "time")
                     else f"e.g. {', '.join(str(x) for x in c['samples'][:3])}")
            lines.append(f"  - {c['column']} | {c['kind']} | {c['distinct']} distinct | {extra}"
                         + (f" | {c['comment']}" if c["comment"] else ""))
        blocks.append("\n".join(lines))
    joins = "\n".join(f"- {r['name']}: {r['from']}.{r['from_col']} -> {r['to']}.{r['to_col']} "
                      f"({r['coverage']:.0%} matched)" for r in rels) or "- none"
    return (
        "You design ONE Snowflake semantic view for business users over these related tables. Use ONLY the "
        "columns listed, each item belongs to the table it comes from.\n\n" + "\n\n".join(blocks) +
        f"\n\nJoins already checked in Snowflake (you may drop one that makes no business sense, never add one):\n{joins}\n\n"
        "Rules: dimensions are columns people group or filter by (text, boolean, dates, low-cardinality codes), "
        "usually on the lookup tables; metrics aggregate numeric columns of the tables with the facts (SUM for "
        "amounts and quantities, AVG for rates/durations/scores, COUNT_DISTINCT for ids); never put a metric on a "
        "key or join column except COUNT_DISTINCT; ratios divide two metrics of the SAME table. Names are "
        "lower_snake_case business terms, unique across the whole view. Every item gets a one-sentence "
        "business definition and 1-3 synonyms. Propose 3-6 questions a manager would ask.\n"
        'Respond with JSON only: {"view_name": "", "description": "", "drop_joins": ["<join name>"], '
        '"tables": {"<table alias>": {"time_dimension": "<column or null>", '
        '"dimensions": [{"column": "", "name": "", "synonyms": [], "comment": ""}], '
        '"metrics": [{"name": "", "agg": "SUM|AVG|MIN|MAX|COUNT|COUNT_DISTINCT", "column": "<column or null>", '
        '"synonyms": [], "comment": ""}], "ratios": [{"name": "", "numerator": "", "denominator": "", '
        '"comment": ""}]}}, "questions": [""]}')


def _fallback(profiles, als, keys, rels) -> dict[str, Any]:
    tables = {}
    referenced = {r["to"] for r in rels}
    for p, a in zip(profiles, als):
        fb = sb.fallback_draft(p)
        join_cols = {r["from_col"] for r in rels if r["from"] == a} | ({keys[a]} if keys.get(a) else set())
        fb["dimensions"] = [d for d in fb["dimensions"] if d["column"] not in join_cols or a in referenced]
        fb["metrics"] = [m for m in fb["metrics"] if m["column"] not in join_cols]
        if a in referenced and not any(r["from"] == a for r in rels):
            fb["metrics"] = []                                   # lookup table: dimensions only
        tables[a] = fb
    return {"view_name": "_".join(als)[:40], "description": "Business view over " + ", ".join(p["table"] for p in profiles),
            "tables": tables, "questions": []}


def validate(raw: dict[str, Any], profiles, als, rels, keys) -> tuple[dict[str, Any], list[dict[str, str]]]:
    by_alias = dict(zip(als, profiles))
    notes: list[dict[str, str]] = []
    drop = {str(x) for x in (raw.get("drop_joins") or [])}
    keep_rels = []
    for r in rels:
        r = dict(r)
        if r["name"] in drop:
            r["include"] = False
            notes.append({"item": r["name"], "action": "repaired", "why": "Cortex suggested leaving this join out"})
        keep_rels.append(r)
    referenced = {r["to"] for r in keep_rels if r.get("include", True)}
    tables, used = {}, set()
    for a in als:
        t = (raw.get("tables") or {}).get(a) or {}
        clean, tnotes = sb.validate_draft({**t, "view_name": a}, by_alias[a])
        notes += [{**n, "item": f"{a}.{n['item']}"} for n in tnotes]
        if a in referenced and not t.get("metrics"):
            clean["metrics"] = [m for m in clean["metrics"] if m["name"] != "row_count"]   # lookup: no row count
        for k in ("dimensions", "metrics", "ratios"):
            for item in clean[k]:
                item["table"] = a
                if item["name"] in used:                       # names unique across the whole view
                    old, item["name"] = item["name"], f"{a}_{item['name']}"[:60]
                    notes.append({"item": f"{a}.{old}", "action": "renamed", "why": f"name used by another table -> {item['name']}"})
                    if k == "metrics":
                        for r2 in clean.get("ratios", []):
                            r2["numerator"] = item["name"] if r2["numerator"] == old else r2["numerator"]
                            r2["denominator"] = item["name"] if r2["denominator"] == old else r2["denominator"]
                used.add(item["name"])
        tables[a] = clean
    if not any(t["metrics"] for t in tables.values()):
        raise ValueError("No table has a numeric column to measure. Add the table with the facts (amounts, quantities).")
    spec = {"view_name": sb.snake(raw.get("view_name") or "_".join(als))[:40],
            "description": str(raw.get("description") or "")[:400],
            "tables": [{"alias": a, "fqn": by_alias[a]["fqn"], "table": by_alias[a]["table"], "key": keys.get(a),
                        "time_dimension": tables[a]["time_dimension"]} for a in als],
            "relationships": keep_rels,
            "dimensions": [d for a in als for d in tables[a]["dimensions"]],
            "metrics": [m for a in als for m in tables[a]["metrics"]],
            "ratios": [r for a in als for r in tables[a]["ratios"]],
            "questions": [str(q)[:200] for q in (raw.get("questions") or [])][:6]}
    return spec, notes


def draft(cortex, session, fqns: list[str]) -> dict[str, Any]:
    if not 2 <= len(fqns) <= MAX_TABLES:
        raise ValueError(f"Pick 2 to {MAX_TABLES} tables.")
    profiles = [sb.profile_table(session, f) for f in fqns]
    als = aliases(profiles)
    rels, keys, checks = find_relationships(session, profiles, als)
    if not rels:
        raise ValueError("No join found between these tables (no column matches another table's unique key). "
                         "Pick tables that share an id, or build them one by one.")
    origin = "cortex"
    try:
        from ai_services import _json_from_text
        text, _ = cortex.complete(draft_prompt(profiles, als, rels, keys))
        raw = _json_from_text(text)
        if not isinstance(raw, dict) or not raw.get("tables"):
            raise ValueError("empty draft")
    except Exception:
        raw, origin = _fallback(profiles, als, keys, rels), "profile-fallback"
    spec, notes = validate(raw, profiles, als, rels, keys)
    return {"spec": spec, "profiles": profiles, "checks": checks, "notes": notes, "origin": origin}


def revalidate(edited: dict[str, Any], profiles: list[dict[str, Any]]) -> tuple[dict[str, Any], list[dict]]:
    """The reviewer's edits, checked again. Joins and keys come from the checked draft; only `include` changes."""
    als = [t["alias"] for t in edited["tables"]]
    keys = {t["alias"]: t.get("key") for t in edited["tables"]}
    rels = edited.get("relationships") or []
    raw = {"view_name": edited.get("view_name"), "description": edited.get("description"),
           "questions": edited.get("questions"),
           "drop_joins": [r["name"] for r in rels if r.get("include") is False], "tables": {}}
    for a in als:
        pick = lambda k: [{kk: vv for kk, vv in x.items() if kk != "table"} for x in (edited.get(k) or [])
                          if x.get("table") == a and x.get("include", True)]
        t = next(t for t in edited["tables"] if t["alias"] == a)
        raw["tables"][a] = {"time_dimension": t.get("time_dimension"), "dimensions": pick("dimensions"),
                            "metrics": pick("metrics"), "ratios": pick("ratios")}
    fresh = [{k: r[k] for k in ("name", "from", "from_col", "to", "to_col", "coverage")} | {"include": True}
             for r in rels]
    spec, notes = validate(raw, profiles, als, fresh, keys)
    return spec, [n for n in notes if "Cortex suggested" not in n["why"]]


# ------------------------------------------------------------------------------------------- DDL
def build_ddl(spec: dict[str, Any], profiles: list[dict[str, Any]], target_schema: str) -> dict[str, Any]:
    if not re.fullmatch(r"[A-Za-z0-9_$]+\.[A-Za-z0-9_$]+", target_schema):
        raise ValueError("target schema")
    base = re.sub(r"[^A-Z0-9_]", "_", spec["view_name"].upper())[:40] or "MULTI"
    sv = f"{target_schema}.AA_{base}_SV".upper()
    by_alias = {t["alias"]: t for t in spec["tables"]}
    prof = {p["fqn"]: p for p in profiles}
    rels = [r for r in spec["relationships"] if r.get("include", True)]
    dims = [d for d in spec["dimensions"] if d.get("include", True)]
    mets = [m for m in spec["metrics"] if m.get("include", True)]
    keepm = {m["name"] for m in mets}
    ratios = [r for r in spec.get("ratios", []) if r.get("include", True) and r["numerator"] in keepm
              and r["denominator"] in keepm]
    if not mets:
        raise ValueError("Select at least one metric")
    referenced = {r["to"] for r in rels}
    joined = referenced | {r["from"] for r in rels}
    if len(joined) < len(by_alias):
        lonely = sorted(set(by_alias) - joined)
        raise ValueError(f"Table(s) {', '.join(lonely)} would not be joined to anything. Remove them or keep a join.")
    cname = lambda c: "C_" + re.sub(r"[^A-Z0-9_]", "_", c.upper())
    used: dict[str, set] = {a: set() for a in by_alias}
    for d in dims:
        used[d["table"]].add(d["column"])
    for m in mets:
        if m["column"]:
            used[m["table"]].add(m["column"])
    for r in rels:
        used[r["from"]].add(r["from_col"])
        used[r["to"]].add(r["to_col"])
    view_sqls, table_lines = [], []
    src = {}
    for a, t in by_alias.items():
        if t["fqn"] not in prof:
            raise ValueError(f"No profile for {t['fqn']}")
        cols = {c["column"] for c in prof[t["fqn"]]["columns"]}
        if t.get("key"):
            used[a].add(t["key"])
        bad = used[a] - cols
        if bad:
            raise ValueError(f"Unknown column(s) {', '.join(sorted(bad))} in {a}")
        src[a] = f"{target_schema}.AA_SRC_{base}_{a}".upper()[:250]
        view_sqls.append(f"CREATE OR REPLACE VIEW {src[a]} COMMENT = {sb.sq('Analytics Accelerator source view for ' + t['fqn'])} AS SELECT "
                         + ", ".join(f"{quote_ident(c)} AS {cname(c)}" for c in sorted(used[a])) + ", 1 AS C__ROW"
                         + f" FROM {t['fqn']}")
        pk = f" PRIMARY KEY ({cname(t['key'])})" if t.get("key") and a in referenced else ""
        table_lines.append(f"    {a} AS {src[a]}{pk}")

    def syn(items):
        items = [s for s in items or [] if s]
        return f" WITH SYNONYMS = ({', '.join(sb.sq(s) for s in items)})" if items else ""

    rel_lines = [f"    {r['name']} AS {r['from']} ({cname(r['from_col'])}) REFERENCES {r['to']}" for r in rels]
    facts, fact_for = [], {}
    for a in by_alias:
        if any(m["table"] == a for m in mets):
            facts.append(f"    {a}.f__row AS C__ROW")
    for m in mets:
        if m["column"] and (m["table"], m["column"]) not in fact_for:
            f = "f_" + sb.snake(m["column"])[:55]
            fact_for[(m["table"], m["column"])] = f
            facts.append(f"    {m['table']}.{f} AS {cname(m['column'])}")
    metric_lines = []
    for m in mets:
        a, f = m["table"], fact_for.get((m["table"], m["column"]))
        expr = {"SUM": f"SUM({a}.{f})", "AVG": f"AVG({a}.{f})", "MIN": f"MIN({a}.{f})", "MAX": f"MAX({a}.{f})",
                "COUNT_DISTINCT": f"COUNT(DISTINCT {a}.{f})",
                "COUNT": f"SUM({a}.f__row)" if not f else f"COUNT({a}.{f})"}[m["agg"]]
        metric_lines.append(f"    {a}.{m['name']} AS {expr}{syn(m.get('synonyms'))}"
                            + (f"\n      COMMENT = {sb.sq(m['comment'])}" if m.get("comment") else ""))
    for r in ratios:
        a = r["table"]
        metric_lines.append(f"    {a}.{r['name']} AS DIV0({a}.{r['numerator']}, {a}.{r['denominator']})"
                            + (f"\n      COMMENT = {sb.sq(r['comment'])}" if r.get("comment") else ""))
    dim_lines = [f"    {d['table']}.{d['name']} AS {cname(d['column'])}{syn(d.get('synonyms'))}"
                 + (f"\n      COMMENT = {sb.sq(d['comment'])}" if d.get("comment") else "") for d in dims]
    parts = [f"CREATE OR REPLACE SEMANTIC VIEW {sv}", "  TABLES (\n" + ",\n".join(table_lines) + "\n  )",
             "  RELATIONSHIPS (\n" + ",\n".join(rel_lines) + "\n  )", "  FACTS (\n" + ",\n".join(facts) + "\n  )"]
    if dim_lines:
        parts.append("  DIMENSIONS (\n" + ",\n".join(dim_lines) + "\n  )")
    parts.append("  METRICS (\n" + ",\n".join(metric_lines) + "\n  )")
    parts.append(f"  COMMENT = {sb.sq((spec.get('description') or '') + ' (drafted by Cortex over ' + str(len(by_alias)) + ' tables, approved in Analytics Accelerator)')}")
    # test query that goes through a join: a metric of a fact table by a dimension of a table it references
    tm = mets[0]
    via = next((d for d in dims for r in rels if r["from"] == tm["table"] and d["table"] == r["to"]), None)
    test_sql = (f"SELECT * FROM SEMANTIC_VIEW({sv} METRICS {tm['table']}.{tm['name']}"
                + (f" DIMENSIONS {via['table']}.{via['name']}" if via else "") + ") LIMIT 5")
    sums = [{"metric": f"{m['table']}.{m['name']}", "fqn": by_alias[m["table"]]["fqn"], "column": m["column"]}
            for m in mets if m["agg"] == "SUM" and m["column"]][:6]
    return {"semantic_view": sv, "source_views": list(src.values()), "view_sql": ";\n".join(view_sqls),
            "view_sqls": view_sqls, "sv_sql": "\n".join(parts), "test_sql": test_sql, "reconcile": sums}


def create(session, ddl: dict[str, Any]) -> dict[str, Any]:
    for s in ddl["view_sqls"]:
        session.sql(s).collect()
    session.sql(ddl["sv_sql"]).collect()
    rows = [row_dict(r) for r in session.sql(ddl["test_sql"]).collect()]
    checks = []
    for r in ddl["reconcile"]:                       # every SUM metric equals the base table's total
        try:
            base = row_dict(session.sql(f"SELECT SUM({quote_ident(r['column'])}) AS V FROM {r['fqn']}").collect()[0]).get("v")
            via = row_dict(session.sql(f"SELECT * FROM SEMANTIC_VIEW({ddl['semantic_view']} METRICS {r['metric']} AS V)")
                           .collect()[0]).get("v")
            b, v = float(base or 0), float(via or 0)
            ok = abs(b - v) <= max(0.01, abs(b) * 1e-6)
            checks.append({"check": f"total of {r['metric']}", "status": "ok" if ok else "fail",
                           "detail": f"base table {b:,.2f} · semantic view {v:,.2f}"
                                     + ("" if ok else " - totals differ: review the joins before using this view")})
        except Exception as exc:
            checks.append({"check": f"total of {r['metric']}", "status": "warn", "detail": f"not checked: {str(exc)[:160]}"})
    return {"semantic_view": ddl["semantic_view"], "test_rows": rows[:5], "checks": checks}
