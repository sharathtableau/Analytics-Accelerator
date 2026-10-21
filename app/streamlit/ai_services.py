"""Snowflake Cortex AI + ML services used by the app.

Every model output is treated as a *suggestion*: it is parsed, validated
against allowlists (catalog template IDs, semantic-view field IDs) and shown
with its provenance. Numbers shown to users always come from governed queries.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from typing import Any, Optional, Sequence

from semantic_catalog import quote_fqn, quote_ident, row_dict

DEFAULT_MODELS = ("claude-sonnet-4-5", "llama3.3-70b", "mistral-large2")
_DETAILS = {"ok": True}      # set to False once AI_COMPLETE(show_details => TRUE) is rejected on this account


def _json_from_text(text: str) -> Any:
    text = (text or "").strip()
    if text.startswith('"') and text.endswith('"'):
        try:
            text = json.loads(text)
        except Exception:
            pass
    match = re.search(r"\{.*\}", text, re.S)
    if not match:
        raise ValueError("Model did not return JSON")
    return json.loads(match.group(0))


class Cortex:
    def __init__(self, session, app_schema: str, models: Sequence[str] = DEFAULT_MODELS,
                 log: Optional[list] = None, usage: Optional[list] = None):
        self.session = session
        # token ledger: one entry per AI_COMPLETE call with usage reported by Snowflake (show_details)
        self.usage = usage if usage is not None else []
        self.last_usage: Optional[dict] = None
        self.app_schema = app_schema
        self.models = list(models)
        self.model_in_use: Optional[str] = None
        self.log = log if log is not None else []
        self.features: dict[str, Any] = {}

    # -- feature detection ---------------------------------------------------------------
    def detect_features(self) -> dict[str, Any]:
        feats: dict[str, Any] = {"complete": False, "model": None, "forecast": False,
                                 "top_insights": False, "anomaly": False, "agents": False, "errors": {}}
        for model in self.models:
            try:
                self._complete_raw(model, "Reply with the single word OK.")
                feats["complete"], feats["model"] = True, model
                self.model_in_use = model
                break
            except Exception as exc:
                feats["errors"][f"AI_COMPLETE {model}"] = str(exc)[:200]
        for key, stmt in (("forecast", "SHOW SNOWFLAKE.ML.FORECAST IN SCHEMA " + self.app_schema),
                          ("top_insights", "SHOW SNOWFLAKE.ML.TOP_INSIGHTS IN SCHEMA " + self.app_schema),
                          ("anomaly", "SHOW SNOWFLAKE.ML.ANOMALY_DETECTION IN SCHEMA " + self.app_schema),
                          ("agents", "SHOW AGENTS IN SCHEMA " + self.app_schema)):
            try:
                self.session.sql(stmt).collect()
                feats[key] = True
            except Exception as exc:
                feats["errors"][key] = str(exc)[:200]
        self.features = feats
        return feats

    # -- completion ------------------------------------------------------------------------
    def _complete_raw(self, model: str, prompt: str) -> str:
        sql = "SELECT AI_COMPLETE(?, ?) AS R"
        self.log.append(f"AI_COMPLETE('{model}', <prompt {len(prompt)} chars>)")
        if not re.fullmatch(r"[a-z0-9._-]+", model):
            raise ValueError("model name")
        self.last_usage = None
        detail_sql = "SELECT AI_COMPLETE(model => ?, prompt => ?, show_details => TRUE) AS R"
        def detailed():
            if not _DETAILS["ok"]:
                raise RuntimeError("show_details unavailable")
            return self.session.sql(detail_sql, params=[model, prompt]).collect()[0]
        attempts = [
            detailed,
            lambda: self.session.sql(sql, params=[model, prompt]).collect()[0],
            lambda: self.session.sql("SELECT SNOWFLAKE.CORTEX.COMPLETE(?, ?) AS R",
                                     params=[model, prompt]).collect()[0],
        ]
        if "$$" not in prompt:
            attempts.append(lambda: self.session.sql(
                f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{model}', $${prompt}$$) AS R").collect()[0])
        row, last, used = None, None, -1
        for i, attempt in enumerate(attempts):
            try:
                row = attempt()
                used = i
                break
            except Exception as exc:
                last = exc
        if row is None:
            raise last
        if used >= 1 and _DETAILS["ok"]:      # the plain call worked where show_details did not: stop trying it
            _DETAILS["ok"] = False
        value = row_dict(row).get("r")
        if used == 0:                       # show_details: {"choices": [{"messages": ...}], "usage": {...}}
            text = self._from_details(value, model)
            if text is not None:
                return text
        if isinstance(value, str):
            try:
                parsed = json.loads(value)
                if isinstance(parsed, str):
                    return parsed
            except Exception:
                pass
        return "" if value is None else str(value)

    def _from_details(self, value: Any, model: str) -> Optional[str]:
        """Text and token usage from an AI_COMPLETE show_details result; None if the value is not that shape."""
        d = value
        if isinstance(d, str):
            try:
                d = json.loads(d)
            except Exception:
                return None
        if not isinstance(d, dict) or "choices" not in d:
            return None
        try:
            u = d.get("usage") or {}
            if not u:
                raise ValueError("no usage")
            self.last_usage = {"t": time.time(), "model": model, "in": int(u.get("prompt_tokens") or 0),
                               "out": int(u.get("completion_tokens") or 0), "kind": "AI_COMPLETE"}
            self.usage.append(self.last_usage)
            del self.usage[:-200]
        except Exception:
            self.last_usage = None
        choices = d.get("choices") or [{}]
        msg = choices[0].get("messages") if isinstance(choices[0], dict) else None
        if msg is None and isinstance(choices[0], dict):
            msg = choices[0].get("message") or choices[0].get("text")
        if isinstance(msg, (dict, list)):
            msg = json.dumps(msg)
        return "" if msg is None else str(msg)

    def complete(self, prompt: str) -> tuple[str, str]:
        model = self.model_in_use or self.models[0]
        started = time.time()
        text = self._complete_raw(model, prompt)
        u = self.last_usage
        tokens = f" · {u['in']:,} in / {u['out']:,} out tokens" if u else ""
        return text.strip(), f"{model} · {time.time() - started:.1f}s{tokens}"

    # -- layout recommendation (constrained) --------------------------------------------------------
    def recommend_layout(self, audience: str, intent: str, candidates: list[dict[str, Any]]) -> dict[str, Any]:
        allowed = [c for c in candidates if c.get("selectable")]
        if not allowed:
            return {"template_id": None, "reason": "No compatible saved layout.", "provenance": "catalog"}
        if len(allowed) == 1:
            return {"template_id": allowed[0]["template_id"], "reason": "Only compatible saved layout.",
                    "provenance": "catalog"}
        menu = "\n".join(f"- {c['template_id']}: {c['display_name']} — {c.get('description','')} "
                         f"(pages: {', '.join(p['label'] for p in c['page_map'])}; fit {c['fit_score']}%)"
                         for c in allowed)
        prompt = (
            "You select a saved dashboard layout for a Snowflake BI application.\n"
            f"Audience: {audience}\nUser intent: {intent or 'not stated'}\n"
            f"Allowed layouts (choose exactly one id from this list, or null):\n{menu}\n"
            "Do not invent ids, pages, metrics or SQL. "
            'Respond with JSON only: {"template_id": "<id or null>", "reason": "<one sentence>"}')
        text, prov = self.complete(prompt)
        data = _json_from_text(text)
        return {"template_id": data.get("template_id"), "reason": str(data.get("reason", ""))[:300],
                "provenance": f"Cortex AI_COMPLETE ({prov})"}

    # -- field role suggestion (constrained) ----------------------------------------------------------
    def suggest_bindings(self, model_summary: dict[str, Any], intent: str) -> dict[str, Any]:
        def lst(items):
            return "\n".join(f"- {i['id']} ({i.get('data_type') or i['kind']}) {i.get('comment','')}"[:160]
                             for i in items)
        prompt = (
            "Map semantic-view fields to dashboard roles for a business performance dashboard.\n"
            f"Business intent: {intent or 'general performance review'}\n"
            f"Metrics:\n{lst(model_summary['metrics'])}\n"
            f"Dimensions:\n{lst(model_summary['dimensions'])}\n"
            "Choose ONLY ids from the lists. primary_metric = the headline outcome; supporting_metrics = up to 3 "
            "other metrics; time_dimension = a date dimension; segment_dimension = the main business breakdown; "
            "region_dimension = a geographic breakdown or empty string.\n"
            'Respond with JSON only: {"primary_metric": "", "supporting_metrics": [], "time_dimension": "", '
            '"segment_dimension": "", "region_dimension": "", "reason": ""}')
        text, prov = self.complete(prompt)
        data = _json_from_text(text)
        data["provenance"] = f"Cortex AI_COMPLETE ({prov})"
        return data

    # -- narrative ------------------------------------------------------------------------------------
    def narrative(self, page_label: str, purpose: str, facts: list[str], audience: str) -> dict[str, Any]:
        """Page summary. Primary: Cortex AI_AGG aggregates the page's governed facts (one row per fact) into a
        summary inside Snowflake. Fallback: AI_COMPLETE over the same facts."""
        if not facts:
            return {"text": "", "provenance": "no governed facts"}
        task = (f"You write the executive summary for the '{page_label}' page of a {audience.replace('_', ' ')} "
                f"dashboard. Page question: {purpose}. Each row is one governed fact computed from a Snowflake "
                "semantic view. Use only these facts and do not add numbers that are not in them. Answer with ONE "
                "headline sentence (at most 30 words) that states the main change with its numbers, then 2 or 3 "
                "short bullet points (each line starting with '- '), then one line starting with 'Suggested action:'.")
        if "$$" not in task:
            sql = (f"SELECT AI_AGG(F, $${task}$$) AS R FROM "
                   "(SELECT VALUE::STRING AS F FROM TABLE(FLATTEN(INPUT => PARSE_JSON(?))))")
            self.log.append(f"AI_AGG(<{len(facts[:40])} governed fact rows>, <task>)")
            try:
                row = self.session.sql(sql, params=[json.dumps(facts[:40])]).collect()[0]
                text = str(row_dict(row).get("r") or "").strip()
                if text:
                    return {"text": text, "provenance": f"Cortex AI_AGG over {len(facts[:40])} governed fact rows"}
            except Exception as exc:
                self.features.setdefault("errors", {})["ai_agg"] = str(exc)[:200]
        prompt = (task + "\nFacts:\n" + "\n".join(f"- {f}" for f in facts[:40]))
        text, prov = self.complete(prompt)
        return {"text": text, "provenance": f"Cortex AI_COMPLETE ({prov}) over {len(facts)} governed facts "
                                            "(AI_AGG unavailable)"}

    # -- Snowflake ML FORECAST -------------------------------------------------------------------------
    def forecast(self, series: list[tuple[str, float]], horizon: int, grain: str) -> dict[str, Any]:
        """Train SNOWFLAKE.ML.FORECAST on the governed series and forecast `horizon` periods."""
        clean = [(p, v) for p, v in series if v is not None]
        if len(clean) < 12:
            raise ValueError("Forecast needs at least 12 periods")
        digest = hashlib.sha1(json.dumps(clean).encode()).hexdigest()[:10].upper()
        table = f"{self.app_schema}.AA_FC_IN_{digest}"
        model = f"{self.app_schema}.AA_FC_{digest}"
        values = ", ".join(f"('{p}'::TIMESTAMP_NTZ, {float(v)!r})" for p, v in clean)
        started = time.time()
        stmts = [
            f"CREATE OR REPLACE TABLE {table} (TS TIMESTAMP_NTZ, Y FLOAT)",
            f"INSERT INTO {table} VALUES {values}",
            f"CREATE SNOWFLAKE.ML.FORECAST IF NOT EXISTS {model}("
            f"INPUT_DATA => SYSTEM$REFERENCE('TABLE', '{table}'), "
            "TIMESTAMP_COLNAME => 'TS', TARGET_COLNAME => 'Y')",
        ]
        for s in stmts:
            self.log.append(s[:300])
            self.session.sql(s).collect()
        call = f"CALL {model}!FORECAST(FORECASTING_PERIODS => {int(horizon)})"
        self.log.append(call)
        rows = [row_dict(r) for r in self.session.sql(call).collect()]
        nonneg = all(v >= 0 for _, v in clean)
        points = []
        for r in rows:
            ts = r.get("ts")
            lo = float(r.get("lower_bound"))
            fc = float(r.get("forecast"))
            points.append({"period": str(ts)[:10], "forecast": max(fc, 0.0) if nonneg else fc,
                           "lower": max(lo, 0.0) if nonneg else lo, "upper": float(r.get("upper_bound"))})
        return {"points": points, "model": model,
                "provenance": f"Snowflake ML FORECAST {model.split('.')[-1]} · {time.time() - started:.1f}s"}

    # -- Snowflake ML ANOMALY_DETECTION ------------------------------------------------------------------
    def anomalies(self, by_segment: dict[str, list[tuple[str, float]]], current: str,
                  interval: float = 0.95) -> dict[str, Any]:
        """One multi-series SNOWFLAKE.ML.ANOMALY_DETECTION model per (tile, period): trained on each segment's
        history before `current`, then DETECT_ANOMALIES on the `current` period. Returns per-segment
        {y, forecast, lower, upper, is_anomaly, percentile}."""
        train, test = [], []
        for seg, pts in by_segment.items():
            hist = [(p, v) for p, v in pts if v is not None and p < current]
            cur = [(p, v) for p, v in pts if v is not None and p == current]
            if len(hist) >= 12 and cur:            # the model needs enough history per series
                train += [(seg, p, v) for p, v in hist]
                test += [(seg, p, v) for p, v in cur]
        if not test:
            raise ValueError("Anomaly detection needs at least 12 prior periods per segment")
        q = lambda x: str(x).replace("'", "''")
        digest = hashlib.sha1(json.dumps([train, test, interval]).encode()).hexdigest()[:10].upper()
        t_in, t_ev, model = (f"{self.app_schema}.AA_AD_IN_{digest}", f"{self.app_schema}.AA_AD_EV_{digest}",
                             f"{self.app_schema}.AA_AD_{digest}")
        rows = lambda data: ", ".join(f"('{q(sg)}', '{p}'::TIMESTAMP_NTZ, {float(v)!r})" for sg, p, v in data)
        started = time.time()
        stmts = [
            f"CREATE OR REPLACE TABLE {t_in} (SEG VARCHAR, TS TIMESTAMP_NTZ, Y FLOAT)",
            f"INSERT INTO {t_in} VALUES {rows(train)}",
            f"CREATE OR REPLACE TABLE {t_ev} (SEG VARCHAR, TS TIMESTAMP_NTZ, Y FLOAT)",
            f"INSERT INTO {t_ev} VALUES {rows(test)}",
            f"CREATE SNOWFLAKE.ML.ANOMALY_DETECTION IF NOT EXISTS {model}("
            f"INPUT_DATA => SYSTEM$REFERENCE('TABLE', '{t_in}'), SERIES_COLNAME => 'SEG', "
            "TIMESTAMP_COLNAME => 'TS', TARGET_COLNAME => 'Y', LABEL_COLNAME => '')",
        ]
        for st_ in stmts:
            self.log.append(st_[:300])
            self.session.sql(st_).collect()
        call = (f"CALL {model}!DETECT_ANOMALIES(INPUT_DATA => SYSTEM$REFERENCE('TABLE', '{t_ev}'), "
                "SERIES_COLNAME => 'SEG', TIMESTAMP_COLNAME => 'TS', TARGET_COLNAME => 'Y', "
                f"CONFIG_OBJECT => {{'prediction_interval': {float(interval)}}})")
        self.log.append(call)
        out: dict[str, Any] = {}
        for r in [row_dict(x) for x in self.session.sql(call).collect()]:
            seg = r.get("series")
            if isinstance(seg, str) and seg.startswith('"'):
                try:
                    seg = json.loads(seg)
                except Exception:
                    pass
            out[str(seg)] = {"y": float(r.get("y")), "forecast": float(r.get("forecast")),
                             "lower": float(r.get("lower_bound")), "upper": float(r.get("upper_bound")),
                             "is_anomaly": str(r.get("is_anomaly")).upper() in ("TRUE", "1"),
                             "percentile": float(r.get("percentile") or 0.5)}
        return {"segments": out, "model": model, "trained_series": len({s for s, _, _ in train}),
                "provenance": f"Snowflake ML ANOMALY_DETECTION {model.split('.')[-1]} · "
                              f"{len(out)} segments · {int(interval * 100)}% interval · {time.time() - started:.1f}s"}

    # -- Snowflake ML TOP_INSIGHTS ------------------------------------------------------------------------
    def top_insights(self, sv_select_sql: str, key: str) -> list[dict[str, Any]]:
        """sv_select_sql returns <categorical dims...>, METRIC (float), LABEL (TRUE = current period).

        Uses the documented form: CALL <instance>!GET_DRIVERS(INPUT_DATA => TABLE(t),
        LABEL_COLNAME => 'LABEL', METRIC_COLNAME => 'METRIC'). Dimensions are inferred by type.
        """
        instance = f"{self.app_schema}.AA_TOP_INSIGHTS"
        table = f"{self.app_schema}.AA_TI_IN_{hashlib.sha1(key.encode()).hexdigest()[:10].upper()}"
        stmts = [f"CREATE SNOWFLAKE.ML.TOP_INSIGHTS IF NOT EXISTS {instance}()",
                 f"CREATE OR REPLACE TRANSIENT TABLE {table} AS {sv_select_sql}"]
        for st_ in stmts:
            self.log.append(st_[:400])
            self.session.sql(st_).collect()
        call = (f"CALL {instance}!GET_DRIVERS(INPUT_DATA => TABLE({table}), "
                "LABEL_COLNAME => 'LABEL', METRIC_COLNAME => 'METRIC')")
        self.log.append(call)
        rows = [row_dict(r) for r in self.session.sql(call).collect()]
        out = []
        for r in rows:
            contributor = r.get("contributor")
            if isinstance(contributor, str):
                try:
                    contributor = json.loads(contributor)
                except Exception:
                    contributor = [contributor]
            out.append({
                "contributor": [str(c) for c in (contributor or [])],
                "control": _num(r.get("metric_control")),
                "test": _num(r.get("metric_test")),
                "contribution": _num(r.get("contribution")),
                "relative_contribution": _num(r.get("relative_contribution")),
                "growth_rate": _num(r.get("growth_rate")),
            })
        out = [o for o in out if o["contributor"]]
        out.sort(key=lambda x: abs(x["contribution"] or 0), reverse=True)
        return out


def _num(v):
    try:
        return None if v is None else float(v)
    except (TypeError, ValueError):
        return None
