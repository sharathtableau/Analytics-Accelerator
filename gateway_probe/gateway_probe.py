"""AI Gateway probe: can a Streamlit-in-Snowflake app (container runtime) call the Cortex AI Gateway?

Deployed as its own small app (AA_GATEWAY_PROBE) so the Analytics Accelerator is never touched.
Click "Run all tests". Each test says PASS / FAIL / SKIP with the detail needed to decide the next step.
No token is ever shown: only its length. Each model call is one short prompt (a few hundred tokens).
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

import streamlit as st

st.set_page_config(page_title="AI Gateway probe", layout="wide")
st.title("AI Gateway probe")
st.caption("Can this Streamlit app call the Cortex AI Gateway? Run once, then copy the results block at the bottom.")

PROMPT = "Reply with exactly: GATEWAY OK"
TOKEN_FILE = "/snowflake/session/token"
model = st.text_input("Claude model for the Messages tests", "claude-sonnet-4-5")
other_model = st.text_input("Non-Claude model for the Chat Completions test", "llama3.3-70b")


def session():
    return st.connection("snowflake").session()


def sql(q: str):
    return session().sql(q).collect()


def session_token() -> str:
    with open(TOKEN_FILE, "r") as f:            # re-read every call: the file is refreshed every few minutes
        return f.read().strip()


def post(url: str, body: dict, headers: dict, timeout: int = 60) -> dict:
    """POST JSON with the standard library (no extra packages). Returns status, latency, body, request id."""
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST",
                                 headers={"Content-Type": "application/json", "Accept": "application/json", **headers})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read().decode("utf-8", "replace")
            status, hdrs = r.status, dict(r.headers)
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", "replace")
        status, hdrs = e.code, dict(e.headers or {})
    except Exception as e:                        # DNS, connection refused, timeout, TLS ...
        return {"status": None, "latency_s": round(time.time() - t0, 2), "error": f"{type(e).__name__}: {e}"}
    try:
        payload = json.loads(raw)
    except Exception:
        payload = raw[:1500]
    rid = next((v for k, v in hdrs.items() if k.lower() in ("x-snowflake-request-id", "x-request-id", "request-id")), "")
    return {"status": status, "latency_s": round(time.time() - t0, 2), "request_id": rid, "body": payload}


def reply_text(body) -> str:
    """Pull the model's text out of a Messages or Chat Completions response."""
    if not isinstance(body, dict):
        return ""
    if isinstance(body.get("content"), list):                      # Messages API
        return " ".join(c.get("text", "") for c in body["content"] if isinstance(c, dict)).strip()
    ch = body.get("choices")
    if isinstance(ch, list) and ch:                                # Chat Completions / Cortex inference
        m = ch[0].get("message") or ch[0].get("delta") or {}
        return str(m.get("content") or ch[0].get("text") or "").strip()
    return ""


def oauth_headers() -> dict:
    return {"Authorization": f"Bearer {session_token()}", "X-Snowflake-Authorization-Token-Type": "OAUTH",
            "snow-agent-name": "aa-gateway-probe"}


def messages_body(m: str) -> dict:
    return {"model": m, "max_tokens": 20, "messages": [{"role": "user", "content": PROMPT}]}


def result(rid, name, status, detail, data=None):
    return {"id": rid, "test": name, "result": status, "detail": detail, "data": data}


# ------------------------------------------------------------------------------------------------- tests
def t1_environment():
    host = os.getenv("SNOWFLAKE_HOST", "")
    has_token = os.path.exists(TOKEN_FILE)
    who = {}
    try:
        r = sql("SELECT CURRENT_USER() AS U, CURRENT_ROLE() AS R, CURRENT_ACCOUNT() AS A, CURRENT_REGION() AS G")[0]
        who = {"current_user": r[0], "current_role": r[1], "account": r[2], "region": r[3]}
    except Exception as e:
        who = {"sql_error": str(e)[:300]}
    try:
        u = st.user
        who["st_user"] = u.get("user_name") or u.get("email") or ""
    except Exception:
        who["st_user"] = ""
    data = {"SNOWFLAKE_HOST": host, "SNOWFLAKE_ACCOUNT": os.getenv("SNOWFLAKE_ACCOUNT", ""),
            "token_file": has_token, "token_length": len(session_token()) if has_token else 0, **who}
    ok = bool(host) and has_token
    return result("G1", "Container runtime: session token and host", "PASS" if ok else "FAIL",
                  "Session token and SNOWFLAKE_HOST present." if ok else
                  "No session token or host: not on the container runtime, so the REST tests below cannot run.", data)


def t2_sql_baseline():
    t0 = time.time()
    try:
        r = sql(f"SELECT AI_COMPLETE('{model}', '{PROMPT}') AS R")[0][0]
        return result("G2", f"Baseline: AI_COMPLETE in SQL ({model})", "PASS",
                      f"{round(time.time() - t0, 2)} s: {str(r)[:80]}")
    except Exception as e:
        return result("G2", f"Baseline: AI_COMPLETE in SQL ({model})", "FAIL", str(e)[:400])


def t3_gateway_object():
    data = {}
    try:
        rows = sql("SHOW AI GATEWAYS")
        data["gateways"] = [{k: str(v) for k, v in r.as_dict().items()} for r in rows][:5]
    except Exception as e:
        data["show_error"] = str(e)[:300]
    try:
        rows = sql("DESCRIBE AI GATEWAY SNOWFLAKE")
        data["describe"] = [{k: str(v)[:300] for k, v in r.as_dict().items()} for r in rows][:20]
    except Exception as e:
        data["describe_error"] = str(e)[:300]
    found = bool(data.get("gateways")) or bool(data.get("describe"))
    return result("G3", "Gateway visible to this role (SHOW / DESCRIBE AI GATEWAY)", "PASS" if found else "FAIL",
                  "The SNOWFLAKE gateway is visible; its endpoint is in the data below." if found else
                  "Not visible: the account may not have the gateway yet, or the role lacks USAGE.", data)


def t4_cortex_rest_control():
    """Control: the plain Cortex REST endpoint with the same token. Separates 'REST from SiS fails' from 'gateway fails'."""
    if not os.path.exists(TOKEN_FILE):
        return result("G4", "Control: Cortex REST (inference:complete) with the session token", "SKIP", "No token.")
    url = f"https://{os.getenv('SNOWFLAKE_HOST')}/api/v2/cortex/inference:complete"
    r = post(url, {"model": model, "messages": [{"role": "user", "content": PROMPT}], "max_tokens": 20,
                   "stream": False}, oauth_headers())
    txt = reply_text(r.get("body"))
    ok = r.get("status") == 200
    return result("G4", "Control: Cortex REST (inference:complete) with the session token", "PASS" if ok else "FAIL",
                  f"HTTP {r.get('status')} in {r.get('latency_s')} s. {txt[:80] or r.get('error', '')}", r)


def t5_gateway_messages_internal():
    if not os.path.exists(TOKEN_FILE):
        return result("G5", "Gateway Messages API via SNOWFLAKE_HOST + session token", "SKIP", "No token.")
    url = f"https://{os.getenv('SNOWFLAKE_HOST')}/api/v2/aigateways/SNOWFLAKE/v1/messages"
    r = post(url, messages_body(model), oauth_headers())
    txt = reply_text(r.get("body"))
    ok = r.get("status") == 200 and bool(txt)
    return result("G5", "Gateway Messages API via SNOWFLAKE_HOST + session token", "PASS" if ok else "FAIL",
                  f"HTTP {r.get('status')} in {r.get('latency_s')} s. {txt[:80] or r.get('error', '')}", r)


def t6_gateway_chat_internal():
    if not os.path.exists(TOKEN_FILE):
        return result("G6", "Gateway Chat Completions (non-Claude) via SNOWFLAKE_HOST", "SKIP", "No token.")
    url = f"https://{os.getenv('SNOWFLAKE_HOST')}/api/v2/aigateways/SNOWFLAKE/v1/chat/completions"
    r = post(url, {"model": other_model, "max_tokens": 20, "messages": [{"role": "user", "content": PROMPT}]},
             oauth_headers())
    txt = reply_text(r.get("body"))
    ok = r.get("status") == 200 and bool(txt)
    return result("G6", f"Gateway Chat Completions ({other_model}) via SNOWFLAKE_HOST", "PASS" if ok else "FAIL",
                  f"HTTP {r.get('status')} in {r.get('latency_s')} s. {txt[:80] or r.get('error', '')}", r)


def t7_gateway_public_pat():
    """Fallback path: the public account address with a PAT stored in a Snowflake secret (needs setup/gateway_probe_fallback.sql)."""
    try:
        pat = st.secrets["aa_gateway_pat"]
    except Exception:
        pat = os.environ.get("aa_gateway_pat", "")
    host = st.session_state.get("public_host", "")
    if not pat or not host:
        return result("G7", "Fallback: public endpoint + PAT secret", "SKIP",
                      "Only needed if G5 fails. Needs the secret and integration from setup/gateway_probe_fallback.sql, "
                      "and the account host typed in the box below.")
    url = f"https://{host}/api/v2/aigateways/SNOWFLAKE/v1/messages"
    r = post(url, messages_body(model), {"Authorization": f"Bearer {pat}",
                                        "X-Snowflake-Authorization-Token-Type": "PROGRAMMATIC_ACCESS_TOKEN",
                                        "snow-agent-name": "aa-gateway-probe"})
    txt = reply_text(r.get("body"))
    ok = r.get("status") == 200 and bool(txt)
    return result("G7", "Fallback: public endpoint + PAT secret", "PASS" if ok else "FAIL",
                  f"HTTP {r.get('status')} in {r.get('latency_s')} s. {txt[:80] or r.get('error', '')}", r)


def t8_traces():
    try:
        rows = sql("SELECT COUNT(*) AS N FROM TABLE(AGENT_TRACE_TABLE('SNOWFLAKE')) "
                   "WHERE TIMESTAMP >= DATEADD('hour', -1, CURRENT_TIMESTAMP())")
        n = int(rows[0][0])
        return result("G8", "Traces: gateway calls in the last hour (AGENT_TRACE_TABLE)", "PASS" if n else "INFO",
                      f"{n} trace rows in the last hour." + ("" if n else " Traces can lag a few minutes; run again."))
    except Exception as e:
        return result("G8", "Traces: gateway calls in the last hour (AGENT_TRACE_TABLE)", "INFO",
                      "Not readable by this role (needs MONITOR on the gateway). Check with an admin: " + str(e)[:200])


TESTS = [t1_environment, t2_sql_baseline, t3_gateway_object, t4_cortex_rest_control, t5_gateway_messages_internal,
         t6_gateway_chat_internal, t7_gateway_public_pat, t8_traces]

st.text_input("Only for test G7: account host, e.g. myorg-myaccount.snowflakecomputing.com", key="public_host")

if st.button("Run all tests", type="primary"):
    out = []
    bar = st.progress(0.0)
    for i, t in enumerate(TESTS):
        try:
            out.append(t())
        except Exception as e:
            out.append(result(t.__name__[:2].upper().replace("T", "G"), t.__name__, "FAIL", f"Probe error: {e}"))
        bar.progress((i + 1) / len(TESTS))
    st.session_state["results"] = out

res = st.session_state.get("results")
if res:
    icon = {"PASS": "✅", "FAIL": "❌", "SKIP": "⏭️", "INFO": "ℹ️"}
    for r in res:
        with st.expander(f"{icon.get(r['result'], '')} {r['id']}  {r['test']}: {r['result']}", expanded=r["result"] == "FAIL"):
            st.write(r["detail"])
            if r.get("data") is not None:
                st.json(r["data"], expanded=False)
    g5 = next((r for r in res if r["id"] == "G5"), {})
    g7 = next((r for r in res if r["id"] == "G7"), {})
    if g5.get("result") == "PASS":
        st.success("Verdict: the app CAN call the AI Gateway with its own session token. No integration or secret needed.")
    elif g7.get("result") == "PASS":
        st.warning("Verdict: the gateway works only through the public address with a PAT (fallback path).")
    else:
        st.error("Verdict: not reachable yet. Copy the results below and send them back.")
    st.subheader("Results to copy")
    st.code(json.dumps([{k: v for k, v in r.items() if k != "data"} | {"data": r.get("data")} for r in res],
                       indent=1, default=str)[:20000], language="json")
