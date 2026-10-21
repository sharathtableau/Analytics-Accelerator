"""Metrics for semantic views that define none (facts only).

1. Profile every fact in Snowflake through the semantic view's standard-SQL interface
   (COUNT, COUNT DISTINCT, MIN, MAX, AVG, share of 0/1 values) - no raw-table access.
2. Cortex AI_COMPLETE reads the profile plus names, types, comments and dimensions and drafts business
   metrics: aggregate per fact (SUM / AVG / COUNT DISTINCT ...) and ratios between them, each with a
   definition and the reason it chose that aggregation.
3. A validator keeps only valid drafts (real fact, allowed aggregation, numeric for SUM/AVG, unique names,
   ratios between drafted metrics). Rules fill in if Cortex is unavailable.
The user then reviews the metrics on the Review page; the owner can copy the METRICS clause to make them
governed in the semantic view itself.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Optional

from semantic_catalog import (AGGS, NAME_OK, NUMERIC, SemanticModel, adhoc_aggregate, apply_metric_draft,
                              quote_fqn)

THEMES = ("Sales", "Profitability", "Customers", "Operations", "Quality", "Volume", "Finance", "Other")


def signature(model: SemanticModel) -> str:
    """Drafts stay valid while the facts are unchanged."""
    key = "|".join(sorted(f"{f.entity}.{f.name}:{f.data_type}" for f in model.facts))
    return hashlib.sha1(key.encode()).hexdigest()[:16]


def profile(session, model: SemanticModel, log: Optional[list] = None) -> dict[str, dict[str, Any]]:
    """Per-fact statistics, one standard-SQL query per logical table (ad-hoc aggregates over facts)."""
    out: dict[str, dict[str, Any]] = {}
    tables = sorted({f.entity for f in model.facts if f.entity})
    for t in tables:
        facts = [f for f in model.facts if f.entity == t][:40]
        sel = []
        for i, f in enumerate(facts):
            sel += [f"COUNT({f.ref}) AS N{i}", f"COUNT(DISTINCT {f.ref}) AS D{i}"]
            if not f.data_type or NUMERIC.search(f.data_type):
                sel += [f"MIN({f.ref}) AS L{i}", f"MAX({f.ref}) AS H{i}", f"AVG({f.ref}) AS A{i}"]
        sql = f"SELECT {', '.join(sel)} FROM {quote_fqn(model.fqn)}"
        try:
            if log is not None:
                log.append(sql)
            rows = session.sql(sql).collect()
            r = {k.upper(): v for k, v in (rows[0].as_dict() if hasattr(rows[0], "as_dict") else dict(rows[0])).items()} if rows else {}
        except Exception as exc:
            out[t] = {"_error": str(exc)[:200]}
            continue
        for i, f in enumerate(facts):
            num = lambda k: (float(r[k]) if r.get(k) is not None else None)
            st = {"non_null": num(f"N{i}"), "distinct": num(f"D{i}"), "min": num(f"L{i}"), "max": num(f"H{i}"),
                  "avg": num(f"A{i}")}
            if st["min"] is not None and st["max"] is not None:
                st["looks_like"] = ("flag 0/1" if st["min"] >= 0 and st["max"] <= 1 and (st["distinct"] or 0) <= 2
                                    else "fraction 0-1" if st["min"] >= 0 and st["max"] <= 1
                                    else "percent 0-100" if st["min"] >= 0 and st["max"] <= 100 and re.search(r"PCT|PERCENT|RATE", f.name, re.I)
                                    else "identifier" if (re.search(r"(_ID|_KEY|_NO|_NUMBER)$|^ID$", f.name, re.I)
                                                          or (st["distinct"] and st["non_null"] and st["distinct"] >= 0.98 * st["non_null"]
                                                              and re.search(r"NUMBER\(\d+,\s*0\)|INT", f.data_type or "", re.I)))
                                    else "amount/count")
            if st["non_null"] is not None:
                out.setdefault(t, {})[f.name] = {k: v for k, v in st.items() if v is not None}
    return out


def draft_prompt(model: SemanticModel, prof: dict[str, Any]) -> str:
    lines = []
    for t in sorted({f.entity for f in model.facts if f.entity}):
        lines.append(f"Table {t}:")
        dims = [d for d in model.dimensions if d.entity == t]
        lines.append("  dimensions: " + ", ".join(f"{d.name}{' (date)' if d.is_time else ''}" for d in dims[:40]))
        for f in [f for f in model.facts if f.entity == t][:40]:
            st = (prof.get(t) or {}).get(f.name) or {}
            stats = ", ".join(f"{k}={round(v, 4) if isinstance(v, float) else v}" for k, v in st.items())
            lines.append(f"  fact {f.name} [{f.data_type or '?'}]{' - ' + f.comment[:80] if f.comment else ''}"
                         f"{' | ' + stats if stats else ''}")
    return (
        "You are a BI analyst defining business metrics for a Snowflake semantic view that has facts but no "
        "metrics. Use the data profile to choose the right aggregation for each fact.\n"
        f"Semantic view {model.fqn}. {model.comment or ''}\n" + "\n".join(lines) + "\n"
        "Rules:\n"
        "- Amounts, quantities, costs, counts per row -> SUM. Rates, percentages, scores, ages, prices, durations, "
        "0/1 flags -> AVG (an AVG of a 0/1 flag is a rate). Identifiers -> COUNT_DISTINCT (e.g. number of orders, "
        "patients). Never SUM an identifier or a rate.\n"
        f"- Allowed agg: {', '.join(AGGS)}. Skip text facts unless they are identifiers.\n"
        "- Add ratios that a business user expects (e.g. average order value = sales / orders, margin % = profit "
        "/ sales, cost per patient) using names of metrics you defined in the same table.\n"
        "- Names: UPPER_SNAKE_CASE business names (TOTAL_SALES, ORDER_COUNT, AVG_LENGTH_OF_STAY), max 15 metrics + "
        "6 ratios per table. Comment = one-sentence business definition. why = why this aggregation (cite the profile).\n"
        f"- theme: one of {', '.join(THEMES)}.\n"
        'Respond with JSON only: {"tables": {"<TABLE>": {"metrics": [{"name": "", "agg": "", "fact": "", '
        '"comment": "", "why": "", "synonyms": [""], "theme": ""}], "ratios": [{"name": "", "numerator": "", '
        '"denominator": "", "comment": "", "why": "", "theme": ""}]}}}'
    )


def rules_draft(model: SemanticModel, prof: Optional[dict] = None) -> dict[str, Any]:
    """Deterministic fallback, informed by the profile when available."""
    tables: dict[str, Any] = {}
    for f in model.facts:
        st = ((prof or {}).get(f.entity) or {}).get(f.name) or {}
        agg = adhoc_aggregate(f)
        if st.get("looks_like") == "identifier":
            agg = "COUNT_DISTINCT"
        elif st.get("looks_like") in ("flag 0/1", "fraction 0-1", "percent 0-100") and agg:
            agg = "AVG"
        if not agg:
            continue
        name = f"{f.name}_COUNT" if agg == "COUNT_DISTINCT" else f"AVG_{f.name}" if agg == "AVG" else f.name
        tables.setdefault(f.entity.upper(), {"metrics": [], "ratios": []})["metrics"].append(
            {"name": name.upper(), "agg": agg, "fact": f.name, "comment": f.comment or f"{agg.replace('_', ' ').title()} of {f.name.replace('_', ' ').lower()}.",
             "why": f"Rule: {st.get('looks_like', 'name/type')} -> {agg}"})
    return {"tables": tables, "origin": "rules"}


def validate(model: SemanticModel, raw: dict[str, Any]) -> tuple[dict[str, Any], list[dict[str, str]]]:
    notes: list[dict[str, str]] = []
    facts = {(f.entity.upper(), f.name.upper()): f for f in model.facts}
    out: dict[str, Any] = {}
    for t, spec in (raw.get("tables") or {}).items():
        t = str(t).upper()
        if not any(k[0] == t for k in facts):
            notes.append({"item": t, "action": "dropped", "why": "not a table of this semantic view"})
            continue
        ms, names = [], set()
        for m in (spec or {}).get("metrics") or []:
            name, agg = str(m.get("name", "")).upper(), str(m.get("agg", "")).upper().replace(" ", "_")
            f = facts.get((t, str(m.get("fact", "")).upper()))
            if not f:
                notes.append({"item": name, "action": "dropped", "why": f"fact {m.get('fact')} does not exist"})
                continue
            if agg not in AGGS:
                notes.append({"item": name, "action": "dropped", "why": f"aggregation {agg} not allowed"})
                continue
            if agg in ("SUM", "AVG") and f.data_type and not NUMERIC.search(f.data_type):
                notes.append({"item": name, "action": "dropped", "why": f"{agg} of a {f.data_type} column"})
                continue
            if agg == "SUM" and re.search(r"(_ID|_KEY)$", f.name, re.I):
                notes.append({"item": name, "action": "repaired", "why": "SUM of an identifier -> COUNT_DISTINCT"})
                agg = "COUNT_DISTINCT"
            if not NAME_OK.match(name):
                name = re.sub(r"[^A-Z0-9_]", "_", name)[:60].strip("_") or f.name.upper()
            if name in names:
                notes.append({"item": name, "action": "dropped", "why": "duplicate name"})
                continue
            names.add(name)
            ms.append({**m, "name": name, "agg": agg, "fact": f.name})
        rs = []
        for r in (spec or {}).get("ratios") or []:
            name = str(r.get("name", "")).upper()
            n, d = str(r.get("numerator", "")).upper(), str(r.get("denominator", "")).upper()
            if n not in names or d not in names or n == d or not NAME_OK.match(name) or name in names:
                notes.append({"item": name or "?", "action": "dropped", "why": "ratio must divide two drafted metrics"})
                continue
            names.add(name)
            rs.append({**r, "name": name, "numerator": n, "denominator": d})
        if ms:
            out[t] = {"metrics": ms[:15], "ratios": rs[:6]}
    return {"tables": out}, notes


def draft(cortex, session, model: SemanticModel, log: Optional[list] = None) -> dict[str, Any]:
    """Profile + Cortex draft + validation; rules when Cortex is unavailable or returns nothing usable."""
    prof = profile(session, model, log)
    profiled = sum(1 for t in prof.values() for k in t if not k.startswith("_"))
    result: dict[str, Any] = {}
    if cortex is not None:
        try:
            from ai_services import _json_from_text
            text, prov = cortex.complete(draft_prompt(model, prof))
            checked, notes = validate(model, _json_from_text(text))
            if sum(len(v["metrics"]) for v in checked["tables"].values()) >= 2:
                result = {**checked, "origin": "cortex", "provenance": f"Cortex AI_COMPLETE ({prov})", "notes": notes}
        except Exception as exc:
            result = {"error": str(exc)[:200]}
    if not result.get("tables"):
        fb = rules_draft(model, prof)
        result = {**fb, "provenance": "Rules over the data profile (Cortex unavailable)",
                  "notes": result.get("notes", []), "error": result.get("error")}
    result["profiled_facts"] = profiled
    result["profile_errors"] = {t: v["_error"] for t, v in prof.items() if "_error" in v}
    result["signature"] = signature(model)
    return result


def apply(model: SemanticModel, d: Optional[dict[str, Any]]) -> SemanticModel:
    """Apply a stored draft (drafted on the whole view); invalid entries are skipped by apply_metric_draft."""
    if d and d.get("tables"):
        apply_metric_draft(model, d)
        model.draft_meta = {k: d.get(k) for k in ("origin", "provenance", "notes", "profiled_facts", "error")}
    return model
