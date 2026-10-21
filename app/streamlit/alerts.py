"""Data alerts (app side): turn a tile, a form or a plain-English sentence into a governed alert.

- normalize(): checks every part of an alert against the semantic view (metric, filter values, rule, schedule,
  recipients) and fills the labels; the same function validates Cortex's reading of a sentence and the form.
- check_sql(): the query the alert runs, built from the semantic view by the app's own query builder.
- parse_text(): Cortex AI_COMPLETE reads the sentence into the alert fields (never SQL); a small rule-based reader
  is the fallback when Cortex is not available.
- proc_ddl() / task_ddl(): the stored procedure (its body is alerts_core.py) and the hourly task.
"""
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path
from typing import Any, Optional

import alerts_core as core
from engine import fmt_kind
from semantic_query import SemanticQuery

RULES = ("threshold", "change", "plan", "freshness")
GRAINS = ("day", "week", "month")
FREQS = ("hourly", "daily", "weekly")
EMAIL = re.compile(r"^[A-Za-z0-9._%+'-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$")
PLAN_RE = re.compile(r"(^|_)(PLAN|TARGET|BUDGET|FORECAST)(_|$)", re.I)


def plan_for(model, metric_id: str) -> Optional[str]:
    """The plan metric paired with a metric, same naming rules as the dashboard (PLAN_<NAME>, ...)."""
    names = {x.name.upper(): x.id for x in model.metrics}
    try:
        n = model.field(metric_id, ("metric",)).name.upper()
    except Exception:
        return None
    for cand in (f"PLAN_{n}", "PLAN_" + n.replace("_SOLD", ""), "PLAN_" + n.split("_")[0], f"{n}_PLAN", f"TARGET_{n}"):
        if cand in names and names[cand] != metric_id:
            return names[cand]
    return None


def options(model, distinct_values: dict[str, list[str]], kinds: Optional[dict] = None) -> dict[str, Any]:
    """What the form offers: metrics (not plan columns) and the filterable dimensions with their values.
    kinds = metric id -> percent/currency/number measured on the data (a name like GROSS_MARGIN can be an amount)."""
    kinds = kinds or {}
    mets = [{"id": m.id, "label": m.label, "kind": kinds.get(m.id) or fmt_kind(m.name), "plan": bool(plan_for(model, m.id))}
            for m in model.metrics if not PLAN_RE.search(m.name)]
    dims = [{"id": d.id, "label": d.label, "values": distinct_values.get(d.id) or []}
            for d in model.categorical_dimensions if distinct_values.get(d.id)]
    return {"metrics": mets, "dims": dims}


def _match_value(val: str, allowed: list[str]) -> Optional[str]:
    low = {a.lower(): a for a in allowed}
    return low.get(str(val).strip().lower())


def normalize(model, raw: dict[str, Any], distinct_values: dict[str, list[str]],
              time_dim: str, defaults: Optional[dict] = None, kinds: Optional[dict] = None) -> tuple[dict[str, Any], list[str]]:
    """Validated alert spec + the list of problems a person must fix before saving (empty = ready)."""
    d = {**(defaults or {}), **{k: v for k, v in (raw or {}).items() if v not in (None, "")}}
    issues: list[str] = []
    mets = {m.id: m for m in model.metrics}
    by_label = {m.label.lower(): m.id for m in model.metrics}
    mid = d.get("metric")
    if mid not in mets and str(mid or "").lower() in by_label:
        mid = by_label[str(mid).lower()]
    if mid not in mets:
        issues.append("Choose the metric to watch." if not mid else f"'{mid}' is not a metric in this semantic view.")
        mid = None
    m = mets.get(mid)
    kind = ((kinds or {}).get(mid) or fmt_kind(m.name)) if m else "number"
    spec: dict[str, Any] = {"metric": mid, "metric_label": m.label if m else "", "kind": kind,
                            "sv": model.fqn, "time_dim": time_dim}
    # filters: only real dimensions and real values
    flt, labels = {}, {}
    dims = {x.id: x for x in model.categorical_dimensions}
    dlabel = {x.label.lower(): x.id for x in model.categorical_dimensions}
    for k, vals in (d.get("filters") or {}).items():
        did = k if k in dims else dlabel.get(str(k).lower())
        if not did:
            issues.append(f"'{k}' is not a dimension in this semantic view.")
            continue
        allowed = distinct_values.get(did) or []
        keep = []
        for v in (vals if isinstance(vals, list) else [vals]):
            hit = _match_value(v, allowed) if allowed else str(v)
            if hit is None:
                issues.append(f"'{v}' is not a value of {dims[did].label}.")
            else:
                keep.append(hit)
        if keep:
            flt[did], labels[dims[did].label] = keep, keep
    spec["filters"], spec["filter_labels"] = flt, labels
    rule = d.get("rule") if d.get("rule") in RULES else "threshold"
    spec["rule"] = rule
    spec["grain"] = d.get("grain") if d.get("grain") in GRAINS else "day"
    if rule == "threshold":
        spec["op"] = "above" if d.get("op") == "above" else "below"
        v = core._num(d.get("value_input") if d.get("value_input") not in (None, "") else d.get("value"))
        if v is None:
            issues.append("Give the value to compare with.")
        else:
            # percentages are typed as people read them (50 = 50%); stored in the metric's own unit (0.5)
            spec["value"] = v / 100.0 if kind == "percent" else v
            spec["value_input"] = v
    elif rule in ("change", "plan"):
        p = core._num(d.get("pct"))
        if p is None or p <= 0:
            issues.append("Give the size of the change in % (for example 10).")
        else:
            spec["pct"] = round(p, 3)
        if rule == "change":
            spec["compare"] = "year" if d.get("compare") == "year" else "prior"
            spec["direction"] = d.get("direction") if d.get("direction") in ("down", "up", "either") else "down"
        else:
            spec["plan_dir"] = "above" if d.get("plan_dir") == "above" else "below"
            spec["plan_metric"] = plan_for(model, mid) if mid else None
            if mid and not spec["plan_metric"]:
                issues.append(f"{spec['metric_label']} has no plan in this semantic view; use another rule.")
    else:
        n = core._num(d.get("days"))
        spec["days"] = int(n) if n and n >= 1 else 1
        spec["grain"] = "day"
    s = d.get("schedule") or {}
    freq = s.get("freq") if s.get("freq") in FREQS else "daily"
    hour = int(core._num(s.get("hour")) or 8) % 24
    spec["schedule"] = {"freq": freq, "hour": hour, "weekday": int(core._num(s.get("weekday")) or 0) % 7,
                        "tz": str(s.get("tz") or "UTC")[:60]}
    rec, bad = [], []
    for e in d.get("recipients") or []:
        e = str(e).strip().strip(",;")
        if not e:
            continue
        (rec if EMAIL.match(e) else bad).append(e)
    spec["recipients"] = list(dict.fromkeys(x.lower() for x in rec))[:20]
    if bad:
        issues.append("Not an email address: " + ", ".join(bad[:5]) + ". Use full addresses (name@company.com).")
    if not spec["recipients"]:
        issues.append("Add at least one email address.")
    for k in ("dashboard_id", "dashboard_name", "name"):
        if d.get(k):
            spec[k] = str(d[k])[:200]
    spec["name"] = spec.get("name") or (core.describe(spec) if mid else "")[:200]
    return spec, issues


def check_sql(model, spec: dict[str, Any]) -> str:
    """The governed query the alert runs: the metric (and its plan) per period, with the alert's filters."""
    q = SemanticQuery(None, model)
    time = q.dim(spec["time_dim"])
    mets = [f"{q.metric(spec['metric']).ref} AS M0"]
    if spec.get("rule") == "plan" and spec.get("plan_metric"):
        mets.append(f"{q.metric(spec['plan_metric']).ref} AS M1")
    # about 3 years back from when the alert is saved (enough for "same period last year"), no upper limit
    start = dt.date.today() - dt.timedelta(days=1100)
    parts = [q.range_where(time, start, dt.date(2100, 1, 1))]
    for did, vals in (spec.get("filters") or {}).items():
        lits = ", ".join("'" + str(v).replace("'", "''") + "'" for v in vals)
        parts.append(f"{q.dim(did).ref} IN ({lits})")
    return ("SELECT * FROM " + q._sv([q.trunc(time, spec.get("grain", "day"))], mets, " AND ".join(parts))
            + " ORDER BY PERIOD")


# ------------------------------------------------------------------------------------------------ plain English
def prompt(opts: dict[str, Any], text: str, defaults: dict[str, Any]) -> str:
    mets = "\n".join(f"- {m['id']}: {m['label']} ({m['kind']}{', has plan' if m['plan'] else ''})"
                     for m in opts["metrics"])
    dims = "\n".join(f"- {d['id']}: {d['label']} = {', '.join(d['values'][:25])}" for d in opts["dims"])
    return (
        "You turn a business user's alert request into alert settings for a Snowflake dashboard app.\n"
        f"User request: {text}\n"
        f"Current tile metric (use it when the request does not name one): {defaults.get('metric') or 'none'}\n"
        f"Metrics (use the id):\n{mets}\nFilter dimensions and their values (use exact values):\n{dims}\n"
        "Rules: threshold (value is above/below a number), change (moves by X% vs the previous period or the same "
        "period last year), plan (X% below/above plan; only metrics that have a plan), freshness (no new data for N days).\n"
        "Percent metrics: give numbers as shown to people (50 means 50%). Periods (grain): day, week, month.\n"
        "Schedule: hourly, daily (hour 0-23), weekly (weekday 0=Monday, hour). Default daily at 8.\n"
        "Recipients: only email addresses written in the request; put names without an address in missing_people.\n"
        "Never write SQL. If the request is ambiguous (e.g. two metrics could match), set question to a short "
        "question and still fill what you can. If it describes two separate alerts, describe the first and set "
        "question to say the second needs its own alert.\n"
        'Respond with JSON only: {"metric": "<id>", "filters": {"<dimension id>": ["<value>"]}, "grain": "day", '
        '"rule": "threshold|change|plan|freshness", "op": "below|above", "value": 0, "pct": 0, '
        '"compare": "prior|year", "direction": "down|up|either", "plan_dir": "below|above", "days": 1, '
        '"schedule": {"freq": "daily", "hour": 8, "weekday": 0}, "recipients": [], "missing_people": [], '
        '"question": ""}')


def _json(text: str) -> dict[str, Any]:
    t = (text or "").strip()
    if "```" in t:
        t = t.split("```", 2)[1].removeprefix("json").strip()
    a, b = t.find("{"), t.rfind("}")
    try:
        return json.loads(t[a:b + 1]) if a >= 0 and b > a else {}
    except ValueError:
        return {}


def fallback_read(opts: dict[str, Any], text: str, defaults: dict[str, Any]) -> dict[str, Any]:
    """Rule-based reading when Cortex is unavailable: good enough for 'X below 50% for West daily'."""
    low = " " + text.lower() + " "
    out: dict[str, Any] = {}
    best = sorted(opts["metrics"], key=lambda m: -len(m["label"]))
    for m in best:
        if m["label"].lower() in low:
            out["metric"] = m["id"]
            break
    out.setdefault("metric", defaults.get("metric"))
    flt = {}
    for d in opts["dims"]:
        for v in d["values"]:
            if re.fullmatch(r"[\d.\s]+", v):        # numbers in the sentence are amounts, not values like hour 9
                continue
            if re.search(r"(?<![a-z0-9])" + re.escape(v.lower()) + r"(?![a-z0-9])", low):
                flt.setdefault(d["id"], []).append(v)
    out["filters"] = flt
    amounts = re.sub(r"[A-Za-z0-9._%+'-]+@[A-Za-z0-9.-]+\.[a-z]{2,}", " ", low)          # not digits in emails
    amounts = re.sub(r"\b(at|by) \d{1,2}(:\d\d)?\s*(am|pm)?\b(?!\s*%)", " ", amounts)          # nor clock times
    num = re.search(r"(-?\d+(?:\.\d+)?)\s*(%|percent|pt|points|k|m)?", amounts)
    n = float(num.group(1)) if num else None
    if num and num.group(2) in ("k",):
        n = n * 1e3
    if num and num.group(2) in ("m",):
        n = n * 1e6
    if re.search(r"no (new )?data|not loaded|stale|missing data", low):
        out.update(rule="freshness", days=int(n or 1))
    elif "plan" in low or "target" in low or "budget" in low:
        out.update(rule="plan", pct=n, plan_dir="above" if re.search(r"\b(above|over|ahead)\b", low) else "below")
    elif re.search(r"\b(drops?|falls?|rises?|grows?|jumps?|changes?|moves?) (by|more than)\b|\bvs (last|prior|previous)\b", low):
        out.update(rule="change", pct=n, compare="year" if "last year" in low or "year ago" in low else "prior",
                   direction="up" if re.search(r"\b(rise|rises|grow|grows|jump|jumps|up)\b", low) else
                   "either" if re.search(r"\b(change|changes|moves?)\b", low) else "down")
    else:
        out.update(rule="threshold", value=n,
                   op="above" if re.search(r"\b(above|over|more than|exceeds?|higher than|greater than)\b", low) else "below")
    out["grain"] = "week" if "week" in low and "weekly" not in low else "month" if re.search(r"\bmonth\b", low) else "day"
    sch = {"freq": "daily", "hour": 8}
    if "every hour" in low or "hourly" in low:
        sch = {"freq": "hourly"}
    elif "weekly" in low or "every monday" in low or "each monday" in low:
        sch = {"freq": "weekly", "weekday": 0, "hour": 8}
    hm = re.search(r"\bat (\d{1,2})(?::00)?\s*(am|pm)?\b", low)
    if hm and sch.get("freq") != "hourly":
        h = int(hm.group(1)) % 12 + (12 if hm.group(2) == "pm" else 0) if hm.group(2) else int(hm.group(1))
        sch["hour"] = h
    out["schedule"] = sch
    out["recipients"] = re.findall(r"[A-Za-z0-9._%+'-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", text)
    return out


def parse_text(cortex, opts: dict[str, Any], text: str, defaults: dict[str, Any]) -> tuple[dict[str, Any], str, str]:
    """(fields, question, provenance). Cortex reads the sentence; the result is validated by normalize()."""
    text = (text or "").strip()[:600]
    if not text:
        return {}, "", ""
    if cortex is not None:
        try:
            raw, prov = cortex.complete(prompt(opts, text, defaults))
            data = _json(raw)
            if data:
                q = str(data.pop("question", "") or "")[:300]
                given = " ".join(str(r).lower() for r in data.get("recipients") or [])
                missing = [str(x) for x in data.pop("missing_people", []) or []
                           if str(x).strip() and str(x).strip().lower().split()[0] not in given][:10]
                if missing:
                    q = (q + " " if q else "") + "Add the email address for: " + ", ".join(missing) + "."
                return data, q, f"Cortex AI_COMPLETE ({prov})"
        except Exception:
            pass
    return fallback_read(opts, text, defaults), "", "rule-based reader (Cortex unavailable)"


# ------------------------------------------------------------------------------------------------ Snowflake objects
def proc_ddl(schema: str, app_url: str = "") -> str:
    body = Path(core.__file__).read_text(encoding="utf-8")
    body += f"\n\nSCHEMA = {schema!r}\nAPP_URL = {app_url!r}\n"
    if "$$" in body:
        raise ValueError("procedure body must not contain $$")
    return (f"CREATE OR REPLACE PROCEDURE {schema}.AA_RUN_ALERTS(ALERT_ID VARCHAR, FORCE BOOLEAN, TRIGGER_KIND VARCHAR)\n"
            "RETURNS VARIANT LANGUAGE PYTHON RUNTIME_VERSION = '3.11' PACKAGES = ('snowflake-snowpark-python', 'pytz')\n"
            f"HANDLER = 'main' EXECUTE AS OWNER\nCOMMENT = '{core.CORE_VERSION}: Analytics Accelerator data alerts'\n"
            f"AS $$\n{body}\n$$")


def task_ddl(schema: str, warehouse: str) -> list[str]:
    return [f"CREATE OR REPLACE TASK {schema}.AA_ALERTS_TASK WAREHOUSE = {warehouse} "
            f"SCHEDULE = 'USING CRON 0 * * * * UTC' "
            f"COMMENT = 'Analytics Accelerator: checks data alerts every hour' "
            f"AS CALL {schema}.AA_RUN_ALERTS(NULL, FALSE, 'schedule')",
            f"ALTER TASK {schema}.AA_ALERTS_TASK RESUME"]
