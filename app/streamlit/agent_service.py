"""Cortex Agents: discover the agent governing a semantic view, create one, ask it.

The browser never names an agent. The server maps the selected semantic view to
agents whose Cortex Analyst tool points at that exact view, or creates a new
agent in the app schema with that view as its only analyst resource.
"""
from __future__ import annotations

import json
import re
import time
from typing import Any, Iterable, Optional

from semantic_catalog import FQN, quote_fqn, quote_ident, row_dict, split_fqn


def _walk(node: Any):
    if isinstance(node, dict):
        yield node
        for v in node.values():
            yield from _walk(v)
    elif isinstance(node, list):
        for v in node:
            yield from _walk(v)


def agent_semantic_views(spec: Any) -> list[str]:
    if isinstance(spec, str):
        try:
            spec = json.loads(spec)
        except Exception:
            return re.findall(r'semantic_view"?\s*[:=]\s*"?([A-Za-z0-9_$."]+)', spec)
    out = []
    for node in _walk(spec):
        sv = node.get("semantic_view")
        if isinstance(sv, str):
            out.append(sv.replace('"', "").upper())
    return out


def find_agents(session, semantic_view: str, schemas: Iterable[str]) -> list[dict[str, Any]]:
    target = semantic_view.upper()
    found = []
    for schema in schemas:
        db, sch = schema.split(".")
        try:
            rows = [row_dict(r) for r in session.sql(
                f"SHOW AGENTS IN SCHEMA {quote_ident(db)}.{quote_ident(sch)}").collect()]
        except Exception:
            continue
        for r in rows:
            name = str(r.get("name") or "")
            fqn = f"{r.get('database_name', db)}.{r.get('schema_name', sch)}.{name}".upper()
            try:
                desc = [row_dict(x) for x in session.sql(f"DESCRIBE AGENT {quote_fqn(fqn)}").collect()]
            except Exception:
                continue
            spec = desc[0].get("agent_spec") if desc else None
            if target in agent_semantic_views(spec):
                profile = r.get("profile") or "{}"
                try:
                    display = json.loads(profile).get("display_name") or name
                except Exception:
                    display = name
                found.append({"fqn": fqn, "display_name": display, "owner": r.get("owner", ""),
                              "comment": r.get("comment") or "",
                              "has_search": "cortex_search" in json.dumps(spec or ""),
                              "has_actions": "log_decision" in json.dumps(spec or "")})
    return found


SPEC_VERSION = "aa-spec-4"      # bump when the app-owned agent definition changes; old ones are rebuilt


def agent_spec(semantic_view: str, title: str, sample_questions: list[str],
               warehouse: str = "", search_service: str = "", decision_proc: str = "") -> dict[str, Any]:
    """One domain agent: Cortex Analyst over the semantic view, Cortex Search over the domain's documents, and a
    custom tool (stored procedure) that logs decisions — the agent acts, not only answers."""
    analyst: dict[str, Any] = {"semantic_view": semantic_view}
    if warehouse:
        # Without this the analyst tool fails with 391920 unless the caller has a default warehouse.
        analyst["execution_environment"] = {"type": "warehouse", "warehouse": warehouse.upper()}
    tools = [{"tool_spec": {"type": "cortex_analyst_text_to_sql", "name": "analyst",
                            "description": f"Governed metrics and dimensions from {semantic_view}. Use for every "
                                           "number: values, trends, comparisons, rankings."}}]
    resources: dict[str, Any] = {"analyst": analyst}
    orchestration = "Use the analyst tool for any number."
    if search_service:
        tools.append({"tool_spec": {"type": "cortex_search", "name": "documents",
                                    "description": "Company policies, operating standards, plan memos, weekly "
                                                   "business review notes and the metric glossary. Use for why "
                                                   "something happened, what a policy or target is, and what a "
                                                   "metric means."}})
        resources["documents"] = {"search_service": search_service, "max_results": 4,
                                  "id_column": "DOC_ID", "title_column": "TITLE"}
        orchestration = ("Use the analyst tool for numbers and the documents tool for reasons, policies, targets "
                         "and definitions. For 'why' questions, first quantify with the analyst tool, then look "
                         "for a documented cause with the documents tool, and say clearly which parts come from "
                         "data and which from documents. Cite document IDs such as HLO-POL-014.")
    if decision_proc:
        tools.append({"tool_spec": {
            "type": "generic", "name": "log_decision",
            "description": ("Record a business decision or follow-up action in Snowflake (table AA_DECISIONS) with an "
                            "owner, a due date and the evidence behind it. Use ONLY when the user explicitly asks to "
                            "log, record, assign or track a decision or action."),
            "input_schema": {"type": "object", "properties": {
                "p_title": {"type": "string", "description": "Short imperative title, e.g. 'Expedite Reno DC footwear transfer'"},
                "p_detail": {"type": "string", "description": "What should be done and why, in 1-3 sentences"},
                "p_owner": {"type": "string", "description": "Person or team accountable; ask the user if not given"},
                "p_due_date": {"type": "string", "description": "Due date as YYYY-MM-DD; ask the user if not given"},
                "p_evidence": {"type": "string", "description": "The numbers and document IDs that support it"},
                "p_semantic_view": {"type": "string", "description": f"Always exactly {semantic_view}"}},
                "required": ["p_title", "p_owner", "p_due_date", "p_semantic_view"]}}})
        proc: dict[str, Any] = {"type": "procedure", "identifier": decision_proc}
        if warehouse:
            proc["execution_environment"] = {"type": "warehouse", "warehouse": warehouse.upper()}
        resources["log_decision"] = proc
        orchestration += (" When the user asks to log, record or assign a decision or action, call log_decision with "
                          f"p_semantic_view = {semantic_view}; if the owner or due date is missing, ask for it first. "
                          "Never log a decision the user did not ask for. Report the decision ID the tool returns.")
    return {
        "models": {"orchestration": "auto"},
        "instructions": {
            "orchestration": orchestration,
            "response": (f"You are the governed analytics assistant for {title}. Be concise, name the metrics "
                         "you used, cite documents by ID, and say when neither the data nor the documents can "
                         "answer a question."),
            "sample_questions": [{"question": q} for q in sample_questions[:4]],
        },
        "tools": tools,
        "tool_resources": resources,
    }


def create_agent(session, app_schema: str, semantic_view: str, title: str,
                 sample_questions: list[str], warehouse: str = "", replace: bool = False,
                 search_service: str = "", decision_proc: str = "") -> dict[str, Any]:
    if not FQN.match(semantic_view):
        raise ValueError("semantic view")
    if warehouse and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_$]*", warehouse):
        raise ValueError("warehouse")
    short = re.sub(r"[^A-Z0-9_]", "_", split_fqn(semantic_view)[2].upper())[:60]
    fqn = f"{app_schema}.AA_{short}_AGENT".upper()
    if search_service and not FQN.match(search_service):
        raise ValueError("search service")
    if decision_proc and not FQN.match(decision_proc):
        raise ValueError("decision procedure")
    spec = json.dumps(agent_spec(semantic_view, title, sample_questions, warehouse, search_service, decision_proc),
                      indent=2)
    if "$$" in spec:
        raise ValueError("spec contains $$")
    profile = json.dumps({"display_name": f"{title} agent"}).replace("'", "''")
    verb = "CREATE OR REPLACE AGENT" if replace else "CREATE AGENT IF NOT EXISTS"
    sql = (f"{verb} {quote_fqn(fqn)} "
           f"COMMENT = 'Analytics Accelerator governed agent for {semantic_view} ({SPEC_VERSION})' "
           f"PROFILE = '{profile}' FROM SPECIFICATION $${spec}$$")
    session.sql(sql).collect()
    return {"fqn": fqn, "display_name": f"{title} agent", "created": True, "sql": sql,
            "has_search": bool(search_service), "has_actions": bool(decision_proc), "comment": SPEC_VERSION}


def is_missing_warehouse(exc: Exception) -> bool:
    msg = str(exc)
    return "391920" in msg or "missing an execution environment" in msg


def ask_agent(session, agent_fqn: str, question: str, thread: Optional[dict] = None) -> dict[str, Any]:
    question = (question or "").strip()
    if not 1 <= len(question) <= 2000:
        raise ValueError("Ask a question of up to 2,000 characters")
    if not FQN.match(agent_fqn):
        raise ValueError("agent")
    body: dict[str, Any] = {
        "messages": [{"role": "user", "content": [{"type": "text", "text": question}]}],
        "stream": False,
    }
    if thread and thread.get("thread_id") is not None:
        body["thread_id"] = int(thread["thread_id"])
        body["parent_message_id"] = int(thread.get("message_id") or 0)
    started = time.time()
    row = session.sql("SELECT SNOWFLAKE.CORTEX.DATA_AGENT_RUN(?, ?, TRUE) AS R",
                      params=[agent_fqn, json.dumps(body)]).collect()[0]
    raw = row_dict(row).get("r")
    payload: Any = raw
    for _ in range(3):                      # results can arrive double-encoded
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
                continue
            except Exception:
                break
        break
    if not isinstance(payload, dict):
        payload = {"content": [{"type": "text", "text": str(payload)}]} if payload else {}
    texts, sqls, tables = [], [], []
    for node in _walk(payload):
        if node.get("type") == "text" and isinstance(node.get("text"), str) and node["text"].strip():
            if node["text"] not in texts:
                texts.append(node["text"])
    error = ""
    for k in ("error", "message", "error_message"):
        if isinstance(payload.get(k), str) and not texts:
            error = payload[k]
    if payload.get("code") and not texts:
        error = f"{payload.get('code')}: {error or payload}"
    for node in _walk(payload):
        sql = node.get("sql")
        if isinstance(sql, str) and sql.strip() and sql not in sqls:
            sqls.append(sql.strip())
        rs = node.get("result_set") or node.get("resultSet")
        if isinstance(rs, dict) and rs.get("data"):
            meta = (rs.get("resultSetMetaData") or rs.get("result_set_meta_data") or {}).get("rowType") or []
            cols = [c.get("name") for c in meta if isinstance(c, dict)]
            tables.append({"columns": cols, "rows": rs.get("data")[:50]})
    cites = []
    for node in _walk(payload):
        for item in node.get("search_results") or []:
            if isinstance(item, dict):
                title = str(item.get("doc_title") or item.get("TITLE") or item.get("title") or "")
                doc = str(item.get("doc_id") or item.get("DOC_ID") or "")
                if not doc and not title:
                    doc = f"Source {item.get('source_id') or len(cites) + 1}"
                label = " · ".join(x for x in (doc, title) if x)[:120]
                if label and label not in [c["label"] for c in cites]:
                    cites.append({"label": label, "text": str(item.get("text") or item.get("CHUNK") or "")[:400]})
    blob = json.dumps(payload)
    actions = [{"kind": "decision", "id": m} for m in dict.fromkeys(re.findall(r"Logged decision ([0-9a-f]{12})", blob))]
    meta = payload.get("metadata") or {}
    tokens = {"in": 0, "cache_read": 0, "cache_write": 0, "out": 0}
    try:                                    # response.metadata.usage.tokens_consumed (per model)
        for t in ((meta.get("usage") or {}).get("tokens_consumed") or []):
            it = t.get("input_tokens") or {}
            tokens["in"] += int((it.get("total") if isinstance(it, dict) else it) or 0)
            tokens["cache_read"] += int((it.get("cache_read") if isinstance(it, dict) else 0) or 0)
            tokens["cache_write"] += int((it.get("cache_write") if isinstance(it, dict) else 0) or 0)
            ot = t.get("output_tokens") or {}
            tokens["out"] += int((ot.get("total") if isinstance(ot, dict) else ot) or 0)
    except Exception:
        pass
    if error and not texts:
        raise RuntimeError(f"Cortex Agent error: {error}"[:600])
    return {
        "raw_preview": "" if texts else json.dumps(payload)[:1500],
        "text": "\n\n".join(texts).strip() or "The agent returned no text answer.",
        "sql": sqls[:3],
        "tables": tables[:2],
        "citations": cites[:5],
        "actions": actions,
        "warnings": [str(w.get("message", w)) if isinstance(w, dict) else str(w)
                     for w in payload.get("warnings", []) or []],
        "run_id": str(meta.get("run_id") or ""),
        "thread": {"thread_id": payload.get("thread_id") or meta.get("thread_id"),
                   "message_id": payload.get("message_id") or meta.get("assistant_message_id")
                   or meta.get("message_id")},
        "latency": round(time.time() - started, 1),
        "tokens": tokens if tokens["in"] or tokens["out"] else None,
    }
