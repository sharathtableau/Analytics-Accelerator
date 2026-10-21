"""App persistence in Snowflake: decisions, saved dashboards, AI run ledger."""
from __future__ import annotations

import json
import uuid
from typing import Any, Optional

from semantic_catalog import row_dict


class Store:
    def __init__(self, session, schema: str):
        self.session = session
        self.schema = schema
        self.ready = False
        self.error = ""
        self.actor = ""            # the signed-in person (st.user), set by the app; CURRENT_USER() is the app's service user

    @property
    def decisions(self) -> str:
        return f"{self.schema}.AA_DECISIONS"

    @property
    def dashboards(self) -> str:
        return f"{self.schema}.AA_DASHBOARDS"

    @property
    def published(self) -> str:
        return f"{self.schema}.AA_PUBLISHED"

    @property
    def ideas(self) -> str:
        return f"{self.schema}.AA_IDEAS"

    @property
    def metric_drafts(self) -> str:
        return f"{self.schema}.AA_METRIC_DRAFTS"

    @property
    def custom_metrics(self) -> str:
        return f"{self.schema}.AA_CUSTOM_METRICS"

    @property
    def ai_runs(self) -> str:
        return f"{self.schema}.AA_AI_RUNS"

    @property
    def validation_runs(self) -> str:
        return f"{self.schema}.AA_VALIDATION_RUNS"

    @property
    def validation_resolutions(self) -> str:
        return f"{self.schema}.AA_VALIDATION_RESOLUTIONS"

    @property
    def themes(self) -> str:
        return f"{self.schema}.AA_THEMES"

    @property
    def uat(self) -> str:
        return f"{self.schema}.AA_UAT_SIGNOFFS"

    @property
    def settings(self) -> str:
        return f"{self.schema}.AA_APP_SETTINGS"

    def ensure(self) -> bool:
        if self.ready:
            return True
        ddl = [
            f"""CREATE TABLE IF NOT EXISTS {self.decisions} (
                DECISION_ID VARCHAR, SEMANTIC_VIEW VARCHAR, TEMPLATE_ID VARCHAR, TITLE VARCHAR,
                DETAIL VARCHAR, OWNER VARCHAR, DUE_DATE DATE, STATUS VARCHAR, EVIDENCE VARIANT,
                CREATED_BY VARCHAR, CREATED_AT TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP(),
                UPDATED_AT TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP())""",
            f"""CREATE TABLE IF NOT EXISTS {self.dashboards} (
                DASHBOARD_ID VARCHAR, NAME VARCHAR, SEMANTIC_VIEW VARCHAR, AUDIENCE VARCHAR,
                TEMPLATE_ID VARCHAR, TEMPLATE_VERSION NUMBER, BINDINGS VARIANT, VERSION NUMBER,
                CREATED_BY VARCHAR, CREATED_AT TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP(), LAYOUT_SPEC VARIANT)""",
            f"ALTER TABLE {self.dashboards} ADD COLUMN IF NOT EXISTS LAYOUT_SPEC VARIANT",
            f"""CREATE TABLE IF NOT EXISTS {self.published} (
                DASHBOARD_ID VARCHAR, VERSION NUMBER, NAME VARCHAR, SEMANTIC_VIEW VARCHAR, AUDIENCE VARCHAR,
                BINDINGS VARIANT, LAYOUT_SPEC VARIANT, VIEW_SETTINGS VARIANT, SHARED_ROLES VARIANT,
                SHARED_USERS VARIANT, NOTE VARCHAR, PUBLISHED_BY VARCHAR,
                PUBLISHED_AT TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP())""",
            f"""CREATE TABLE IF NOT EXISTS {self.ideas} (
                ROLE_NAME VARCHAR, CATALOG_SIG VARCHAR, IDEAS VARIANT, CREATED_BY VARCHAR,
                CREATED_AT TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP())""",
            f"""CREATE TABLE IF NOT EXISTS {self.metric_drafts} (
                SEMANTIC_VIEW VARCHAR, SIGNATURE VARCHAR, DRAFT VARIANT, CREATED_BY VARCHAR,
                CREATED_AT TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP())""",
            f"""CREATE TABLE IF NOT EXISTS {self.custom_metrics} (
                SEMANTIC_VIEW VARCHAR, NAME VARCHAR, LABEL VARCHAR, FORMULA VARCHAR, DESCRIPTION VARCHAR,
                THEME VARCHAR, ORIGIN VARCHAR, ACTIVE BOOLEAN DEFAULT TRUE, CREATED_BY VARCHAR,
                CREATED_AT TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP())""",
            f"""CREATE TABLE IF NOT EXISTS {self.ai_runs} (
                RUN_ID VARCHAR, FEATURE VARCHAR, SEMANTIC_VIEW VARCHAR, INPUT VARCHAR, OUTPUT VARCHAR,
                PROVENANCE VARCHAR, STATUS VARCHAR, LATENCY_S FLOAT, CREATED_BY VARCHAR,
                CREATED_AT TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP())""",
            f"""CREATE TABLE IF NOT EXISTS {self.validation_runs} (
                RUN_ID VARCHAR, DASHBOARD_ID VARCHAR, SEMANTIC_VIEW VARCHAR, PAGE_ID VARCHAR, STATUS VARCHAR,
                TILES NUMBER, VERIFIED NUMBER, REVIEW NUMBER, MISMATCH NUMBER, NOT_CHECKED NUMBER, QUERIES NUMBER,
                REPORT VARIANT, RUN_BY VARCHAR, RUN_AT TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP())""",
            f"""CREATE TABLE IF NOT EXISTS {self.validation_resolutions} (
                RES_ID VARCHAR, DASHBOARD_ID VARCHAR, SEMANTIC_VIEW VARCHAR, TILE_KEY VARCHAR, TILE_TITLE VARCHAR,
                CHECK_ID VARCHAR, ACTION VARCHAR, REASON VARCHAR, OWNER VARCHAR, DUE_DATE DATE, EXPIRES_AT DATE,
                TILE_SIG VARCHAR, DECISION_ID VARCHAR, ACTIVE BOOLEAN DEFAULT TRUE, CREATED_BY VARCHAR,
                CREATED_AT TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP())""",
            f"""CREATE TABLE IF NOT EXISTS {self.themes} (
                THEME_ID VARCHAR, NAME VARCHAR, SOURCE VARCHAR, INPUTS VARIANT, TOKENS VARIANT, CHECKS VARIANT,
                STATUS VARCHAR, ACTIVE BOOLEAN DEFAULT TRUE, CREATED_BY VARCHAR,
                CREATED_AT TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP())""",
            f"""CREATE TABLE IF NOT EXISTS {self.uat} (
                ENTRY_ID VARCHAR, DASHBOARD_ID VARCHAR, SEMANTIC_VIEW VARCHAR, PAGE_ID VARCHAR, TILE_KEY VARCHAR,
                KIND VARCHAR, DECISION VARCHAR, COMMENT VARCHAR, TILE_SIG VARCHAR, PAGE_SIG VARCHAR, RUN_AT VARCHAR,
                VALIDATION_STATUS VARCHAR, CREATED_BY VARCHAR, CREATED_AT TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP(),
                DASHBOARD_NAME VARCHAR, PAGE_LABEL VARCHAR, TILE_TITLE VARCHAR)""",
            f"ALTER TABLE {self.uat} ADD COLUMN IF NOT EXISTS DASHBOARD_NAME VARCHAR",
            f"ALTER TABLE {self.uat} ADD COLUMN IF NOT EXISTS PAGE_LABEL VARCHAR",
            f"ALTER TABLE {self.uat} ADD COLUMN IF NOT EXISTS TILE_TITLE VARCHAR",
            f"""CREATE TABLE IF NOT EXISTS {self.schema}.AA_ALERTS (
                ALERT_ID VARCHAR, NAME VARCHAR, SEMANTIC_VIEW VARCHAR, DASHBOARD_ID VARCHAR, DASHBOARD_NAME VARCHAR,
                SPEC VARIANT, CHECK_SQL VARCHAR, ACTIVE BOOLEAN DEFAULT TRUE, DELETED BOOLEAN DEFAULT FALSE,
                OWNER VARCHAR, CREATED_AT TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP(), UPDATED_AT TIMESTAMP_LTZ,
                LAST_CHECK_AT VARCHAR, LAST_STATUS VARCHAR, LAST_VALUE FLOAT, LAST_MESSAGE VARCHAR,
                LAST_FIRED_KEY VARCHAR, LAST_FIRED_AT VARCHAR)""",
            f"""CREATE TABLE IF NOT EXISTS {self.schema}.AA_ALERT_RUNS (
                RUN_ID VARCHAR, ALERT_ID VARCHAR, CHECKED_AT VARCHAR, TRIGGER_KIND VARCHAR, STATUS VARCHAR,
                PERIOD_LABEL VARCHAR, VALUE FLOAT, COMPARE_VALUE FLOAT, FIRED BOOLEAN, EMAILED BOOLEAN, MESSAGE VARCHAR)""",
            f"""CREATE TABLE IF NOT EXISTS {self.settings} (
                SETTING_KEY VARCHAR, SETTING_VALUE VARCHAR, SET_BY VARCHAR,
                SET_AT TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP())""",
        ]
        try:
            for s in ddl:
                self.session.sql(s).collect()
            self.ready = True
        except Exception as exc:
            self.error = str(exc)
        return self.ready

    # -- decisions -------------------------------------------------------------------
    def add_decision(self, sv: str, template_id: str, title: str, detail: str, owner: str,
                     due: Optional[str], evidence: dict[str, Any]) -> str:
        self.ensure()
        did = uuid.uuid4().hex[:12]
        self.session.sql(
            f"INSERT INTO {self.decisions} (DECISION_ID, SEMANTIC_VIEW, TEMPLATE_ID, TITLE, DETAIL, OWNER, "
            "DUE_DATE, STATUS, EVIDENCE, CREATED_BY) SELECT ?, ?, ?, ?, ?, ?, TRY_TO_DATE(?), 'Open', "
            "PARSE_JSON(?), CURRENT_USER()",
            params=[did, sv, template_id, title[:300], detail[:4000], owner[:120], due or "",
                    json.dumps(evidence)[:15000]]).collect()
        return did

    def set_decision_status(self, decision_id: str, status: str) -> None:
        if status not in ("Open", "In progress", "Done"):
            raise ValueError("status")
        self.session.sql(f"UPDATE {self.decisions} SET STATUS = ?, UPDATED_AT = CURRENT_TIMESTAMP() "
                         "WHERE DECISION_ID = ?", params=[status, decision_id]).collect()

    def list_decisions(self, sv: str) -> list[dict[str, Any]]:
        if not self.ensure():
            return []
        rows = self.session.sql(
            f"SELECT DECISION_ID, TITLE, DETAIL, OWNER, TO_VARCHAR(DUE_DATE) AS DUE_DATE, STATUS, "
            f"TO_VARCHAR(EVIDENCE) AS EVIDENCE, CREATED_BY, TO_VARCHAR(CREATED_AT, 'YYYY-MM-DD HH24:MI') AS CREATED_AT "
            f"FROM {self.decisions} WHERE SEMANTIC_VIEW = ? ORDER BY CREATED_AT DESC LIMIT 100",
            params=[sv]).collect()
        out = []
        for r in rows:
            d = row_dict(r)
            try:
                d["evidence"] = json.loads(d.get("evidence") or "{}")
            except Exception:
                d["evidence"] = {}
            out.append(d)
        return out

    # -- dashboards --------------------------------------------------------------------
    def save_dashboard(self, name: str, sv: str, audience: str, template_id: str, template_version: int,
                       bindings: dict[str, Any], dashboard_id: Optional[str] = None,
                       layout: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        self.ensure()
        dashboard_id = dashboard_id or uuid.uuid4().hex[:12]
        rows = self.session.sql(f"SELECT COALESCE(MAX(VERSION), 0) AS V FROM {self.dashboards} "
                                "WHERE DASHBOARD_ID = ?", params=[dashboard_id]).collect()
        version = int(row_dict(rows[0]).get("v") or 0) + 1 if rows else 1
        self.session.sql(
            f"INSERT INTO {self.dashboards} (DASHBOARD_ID, NAME, SEMANTIC_VIEW, AUDIENCE, TEMPLATE_ID, "
            "TEMPLATE_VERSION, BINDINGS, VERSION, CREATED_BY, LAYOUT_SPEC) "
            "SELECT ?, ?, ?, ?, ?, ?, PARSE_JSON(?), ?, COALESCE(NULLIF(?, ''), CURRENT_USER()), PARSE_JSON(?)",
            params=[dashboard_id, name[:200], sv, audience, template_id, int(template_version),
                    json.dumps(bindings), version, self.actor or "", json.dumps(layout or {}, default=str)]).collect()
        return {"dashboard_id": dashboard_id, "version": version}

    def list_dashboards(self) -> list[dict[str, Any]]:
        if not self.ensure():
            return []
        rows = self.session.sql(
            f"SELECT DASHBOARD_ID, NAME, SEMANTIC_VIEW, AUDIENCE, TEMPLATE_ID, TEMPLATE_VERSION, "
            f"TO_VARCHAR(BINDINGS) AS BINDINGS, TO_VARCHAR(LAYOUT_SPEC) AS LAYOUT_SPEC, VERSION, CREATED_BY, "
            f"FIRST_VALUE(CREATED_BY) OVER (PARTITION BY DASHBOARD_ID ORDER BY VERSION) AS OWNER, "
            f"TO_VARCHAR(CREATED_AT, 'YYYY-MM-DD HH24:MI') AS CREATED_AT FROM {self.dashboards} "
            "QUALIFY ROW_NUMBER() OVER (PARTITION BY DASHBOARD_ID ORDER BY VERSION DESC) = 1 "
            "ORDER BY CREATED_AT DESC LIMIT 50").collect()
        out = []
        for r in rows:
            d = row_dict(r)
            try:
                d["bindings"] = json.loads(d.get("bindings") or "{}")
                d["layout"] = json.loads(d.pop("layout_spec", None) or "null") or None
            except Exception:
                d["bindings"] = {}
            out.append(d)
        return out

    # -- publishing -------------------------------------------------------------------
    def publish(self, dashboard_id: str, name: str, sv: str, audience: str, bindings: dict[str, Any],
                layout: dict[str, Any], view: dict[str, Any], roles: list[str], users: list[str],
                note: str, by: str) -> dict[str, Any]:
        self.ensure()
        rows = self.session.sql(f"SELECT COALESCE(MAX(VERSION), 0) AS V FROM {self.published} "
                                "WHERE DASHBOARD_ID = ?", params=[dashboard_id]).collect()
        version = int(row_dict(rows[0]).get("v") or 0) + 1 if rows else 1
        self.session.sql(
            f"INSERT INTO {self.published} (DASHBOARD_ID, VERSION, NAME, SEMANTIC_VIEW, AUDIENCE, BINDINGS, "
            "LAYOUT_SPEC, VIEW_SETTINGS, SHARED_ROLES, SHARED_USERS, NOTE, PUBLISHED_BY) "
            "SELECT ?, ?, ?, ?, ?, PARSE_JSON(?), PARSE_JSON(?), PARSE_JSON(?), PARSE_JSON(?), PARSE_JSON(?), ?, ?",
            params=[dashboard_id, version, name[:200], sv, audience, json.dumps(bindings),
                    json.dumps(layout, default=str), json.dumps(view), json.dumps(roles), json.dumps(users),
                    note[:1000], by[:200]]).collect()
        return {"dashboard_id": dashboard_id, "version": version}

    def update_sharing(self, dashboard_id: str, version: int, roles: list[str], users: list[str]) -> None:
        """Change who a published version is shared with (no new version: the layout is unchanged)."""
        self.session.sql(
            f"UPDATE {self.published} SET SHARED_ROLES = PARSE_JSON(?), SHARED_USERS = PARSE_JSON(?) "
            "WHERE DASHBOARD_ID = ? AND VERSION = ?",
            params=[json.dumps(roles), json.dumps(users), dashboard_id, int(version)]).collect()

    def list_published(self) -> list[dict[str, Any]]:
        if not self.ensure():
            return []
        rows = self.session.sql(
            f"SELECT DASHBOARD_ID, VERSION, NAME, SEMANTIC_VIEW, AUDIENCE, TO_VARCHAR(BINDINGS) AS BINDINGS, "
            f"TO_VARCHAR(LAYOUT_SPEC) AS LAYOUT_SPEC, TO_VARCHAR(VIEW_SETTINGS) AS VIEW_SETTINGS, "
            f"TO_VARCHAR(SHARED_ROLES) AS SHARED_ROLES, TO_VARCHAR(SHARED_USERS) AS SHARED_USERS, NOTE, PUBLISHED_BY, "
            f"TO_VARCHAR(PUBLISHED_AT, 'YYYY-MM-DD HH24:MI') AS PUBLISHED_AT FROM {self.published} "
            "QUALIFY ROW_NUMBER() OVER (PARTITION BY DASHBOARD_ID ORDER BY VERSION DESC) = 1 "
            "ORDER BY PUBLISHED_AT DESC LIMIT 50").collect()
        out = []
        for r in rows:
            d = row_dict(r)
            for k in ("bindings", "layout_spec", "view_settings", "shared_roles", "shared_users"):
                try:
                    d[k] = json.loads(d.get(k) or "null")
                except Exception:
                    d[k] = None
            out.append(d)
        return out

    # -- saved home ideas (so Cortex's suggestions stay put until the user asks for new ones) ----
    def save_ideas(self, role: str, sig: str, ideas: list[dict[str, Any]], by: str) -> None:
        if not self.ensure():
            return
        self.session.sql(f"INSERT INTO {self.ideas} (ROLE_NAME, CATALOG_SIG, IDEAS, CREATED_BY) "
                         "SELECT ?, ?, PARSE_JSON(?), ?", params=[role, sig, json.dumps(ideas), by[:200]]).collect()

    def load_ideas(self, role: str) -> Optional[dict[str, Any]]:
        if not self.ensure():
            return None
        rows = self.session.sql(
            f"SELECT CATALOG_SIG, TO_VARCHAR(IDEAS) AS IDEAS, TO_VARCHAR(CREATED_AT, 'YYYY-MM-DD HH24:MI') AS CREATED_AT "
            f"FROM {self.ideas} WHERE ROLE_NAME = ? ORDER BY CREATED_AT DESC LIMIT 1", params=[role]).collect()
        if not rows:
            return None
        d = row_dict(rows[0])
        try:
            d["ideas"] = json.loads(d.get("ideas") or "[]")
        except Exception:
            return None
        return d

    def idea_history(self, role: str, limit: int = 6) -> list[dict[str, Any]]:
        """The last few saved idea sets, newest first (AA_IDEAS is append-only, so nothing is ever lost)."""
        if not self.ensure():
            return []
        rows = self.session.sql(
            f"SELECT CATALOG_SIG, TO_VARCHAR(IDEAS) AS IDEAS, TO_VARCHAR(CREATED_AT, 'YYYY-MM-DD HH24:MI') AS CREATED_AT "
            f"FROM {self.ideas} WHERE ROLE_NAME = ? ORDER BY CREATED_AT DESC LIMIT {int(limit)}", params=[role]).collect()
        out = []
        for r in rows:
            d = row_dict(r)
            try:
                d["ideas"] = json.loads(d.get("ideas") or "[]")
            except Exception:
                continue
            out.append(d)
        return out

    # -- metric drafts for facts-only semantic views -------------------------------------------
    def save_metric_draft(self, sv: str, sig: str, draft: dict[str, Any], by: str) -> None:
        if not self.ensure():
            return
        self.session.sql(f"INSERT INTO {self.metric_drafts} (SEMANTIC_VIEW, SIGNATURE, DRAFT, CREATED_BY) "
                         "SELECT ?, ?, PARSE_JSON(?), ?", params=[sv, sig, json.dumps(draft), by[:200]]).collect()

    # -- custom metrics (formulas over a view's metrics, defined by builders) ---------------------------
    def load_custom_metrics(self, sv: str) -> list[dict[str, Any]]:
        """Active custom metrics of a semantic view, oldest first. [] if the table is not there yet."""
        try:
            rows = self.session.sql(
                f"SELECT NAME, LABEL, FORMULA, DESCRIPTION, THEME, ORIGIN, CREATED_BY, "
                f"TO_VARCHAR(CREATED_AT, 'YYYY-MM-DD') AS CREATED_AT FROM {self.custom_metrics} "
                "WHERE SEMANTIC_VIEW = ? AND ACTIVE ORDER BY CREATED_AT", params=[sv]).collect()
        except Exception:
            return []
        return [row_dict(r) for r in rows]

    def save_custom_metric(self, sv: str, m: dict[str, Any], by: str) -> None:
        if not self.ensure():
            raise RuntimeError(self.error or "App tables are not available.")
        self.session.sql(
            f"INSERT INTO {self.custom_metrics} (SEMANTIC_VIEW, NAME, LABEL, FORMULA, DESCRIPTION, THEME, ORIGIN, "
            "CREATED_BY) SELECT ?, ?, ?, ?, ?, ?, ?, ?",
            params=[sv, m["name"], m["label"][:80], m["formula"][:400], (m.get("description") or "")[:300],
                    (m.get("theme") or "")[:30], (m.get("origin") or "")[:20], (by or "")[:200]]).collect()

    def load_metric_draft(self, sv: str, sig: str) -> Optional[dict[str, Any]]:
        if not self.ensure():
            return None
        try:
            rows = self.session.sql(
                f"SELECT TO_VARCHAR(DRAFT) AS DRAFT, TO_VARCHAR(CREATED_AT, 'YYYY-MM-DD HH24:MI') AS CREATED_AT, "
                f"CREATED_BY FROM {self.metric_drafts} WHERE SEMANTIC_VIEW = ? AND SIGNATURE = ? "
                "ORDER BY CREATED_AT DESC LIMIT 1", params=[sv, sig]).collect()
        except Exception:
            return None
        if not rows:
            return None
        d = row_dict(rows[0])
        try:
            out = json.loads(d.get("draft") or "{}")
        except Exception:
            return None
        out["saved_at"], out["saved_by"] = d.get("created_at"), d.get("created_by")
        return out

    # -- AI ledger ------------------------------------------------------------------------
    def log_ai(self, feature: str, sv: str, input_text: str, output_text: str, provenance: str,
               status: str, latency: float) -> None:
        try:
            self.ensure()
            self.session.sql(
                f"INSERT INTO {self.ai_runs} (RUN_ID, FEATURE, SEMANTIC_VIEW, INPUT, OUTPUT, PROVENANCE, STATUS, "
                "LATENCY_S, CREATED_BY) SELECT ?, ?, ?, ?, ?, ?, ?, ?, COALESCE(NULLIF(?, ''), CURRENT_USER())",
                params=[uuid.uuid4().hex[:12], feature, sv, input_text[:4000], output_text[:8000],
                        provenance[:400], status, float(latency), self.actor or ""]).collect()
        except Exception:
            pass

    # -- validation ----------------------------------------------------------------------------
    def save_validation(self, run_id: str, dashboard_id: str, sv: str, page_id: str, summary: dict,
                        queries: int, report: dict) -> None:
        """One row per page validation: the evidence trail (every check, expected vs actual, both SQLs)."""
        try:
            self.ensure()
            c = summary.get("counts") or {}
            self.session.sql(
                f"INSERT INTO {self.validation_runs} (RUN_ID, DASHBOARD_ID, SEMANTIC_VIEW, PAGE_ID, STATUS, TILES, "
                "VERIFIED, REVIEW, MISMATCH, NOT_CHECKED, QUERIES, REPORT, RUN_BY) "
                "SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, PARSE_JSON(?), COALESCE(NULLIF(?, ''), CURRENT_USER())",
                params=[run_id, dashboard_id or "", sv, page_id, summary.get("status", ""), int(summary.get("tiles") or 0),
                        int(c.get("pass") or 0), int(c.get("review") or 0), int(c.get("mismatch") or 0),
                        int(c.get("na") or 0), int(queries or 0), json.dumps(report, default=str)[:15_000_000],
                        self.actor or ""]).collect()
        except Exception:
            pass

    def validation_history(self, sv: str, dashboard_id: str = "", limit: int = 12) -> list[dict[str, Any]]:
        """Latest validation runs for this dashboard (or semantic view when the dashboard is not saved yet)."""
        try:
            self.ensure()
            if dashboard_id:
                where, params = "DASHBOARD_ID = ?", [dashboard_id]
            else:
                where, params = "SEMANTIC_VIEW = ?", [sv]
            rows = self.session.sql(
                f"SELECT RUN_ID, PAGE_ID, STATUS, TILES, VERIFIED, REVIEW, MISMATCH, NOT_CHECKED, QUERIES, RUN_BY, "
                f"TO_VARCHAR(RUN_AT, 'YYYY-MM-DD HH24:MI') AS RUN_AT FROM {self.validation_runs} WHERE {where} "
                f"ORDER BY RUN_AT DESC LIMIT {int(limit)}", params=params).collect()
            return [{k.lower(): v for k, v in row_dict(r).items()} for r in rows]
        except Exception:
            return []

    def save_resolution(self, r: dict[str, Any]) -> str:
        """Accepted finding (with reason and expiry) or a data issue handed to an owner: the audit trail."""
        self.ensure()
        rid = uuid.uuid4().hex[:12]
        self.session.sql(
            f"INSERT INTO {self.validation_resolutions} (RES_ID, DASHBOARD_ID, SEMANTIC_VIEW, TILE_KEY, TILE_TITLE, "
            "CHECK_ID, ACTION, REASON, OWNER, DUE_DATE, EXPIRES_AT, TILE_SIG, DECISION_ID, CREATED_BY) "
            "SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?, TRY_TO_DATE(?), TRY_TO_DATE(?), ?, ?, COALESCE(NULLIF(?, ''), CURRENT_USER())",
            params=[rid, r.get("dashboard_id") or "", r.get("sv") or "", r["tile_key"], (r.get("title") or "")[:300],
                    r.get("check_id") or "", r["action"], (r.get("reason") or "")[:2000], (r.get("owner") or "")[:120],
                    r.get("due") or "", r.get("expires") or "", r.get("sig") or "", r.get("decision_id") or "",
                    self.actor or ""]).collect()
        return rid

    def list_resolutions(self, sv: str, dashboard_id: str = "") -> list[dict[str, Any]]:
        try:
            self.ensure()
            where, params = ("DASHBOARD_ID = ?", [dashboard_id]) if dashboard_id else ("SEMANTIC_VIEW = ? AND DASHBOARD_ID = ''", [sv])
            rows = self.session.sql(
                f"SELECT RES_ID, TILE_KEY, TILE_TITLE, CHECK_ID, ACTION, REASON, OWNER, TO_VARCHAR(DUE_DATE) AS DUE_DATE, "
                f"TO_VARCHAR(EXPIRES_AT) AS EXPIRES_AT, TILE_SIG, DECISION_ID, CREATED_BY, "
                f"TO_VARCHAR(CREATED_AT, 'YYYY-MM-DD HH24:MI') AS CREATED_AT FROM {self.validation_resolutions} "
                f"WHERE {where} AND ACTIVE ORDER BY CREATED_AT DESC", params=params).collect()
            return [{k.lower(): v for k, v in row_dict(r).items()} for r in rows]
        except Exception:
            return []

    # -- company themes (every save is a new row: the history is the audit trail) -----------------------------------
    def save_theme(self, theme_id: str, name: str, source: str, inputs: dict, tokens: dict, checks: list,
                   status: str, active: bool = True) -> str:
        self.ensure()
        theme_id = theme_id or uuid.uuid4().hex[:10]
        self.session.sql(
            f"INSERT INTO {self.themes} (THEME_ID, NAME, SOURCE, INPUTS, TOKENS, CHECKS, STATUS, ACTIVE, CREATED_BY) "
            "SELECT ?, ?, ?, PARSE_JSON(?), PARSE_JSON(?), PARSE_JSON(?), ?, ?, COALESCE(NULLIF(?, ''), CURRENT_USER())",
            params=[theme_id, name[:80], source[:40], json.dumps(inputs), json.dumps(tokens),
                    json.dumps(checks)[:15000], status, bool(active), self.actor or ""]).collect()
        return theme_id

    def list_themes(self) -> list[dict[str, Any]]:
        """Current version of every active theme."""
        try:
            self.ensure()
            rows = self.session.sql(
                f"SELECT THEME_ID, NAME, SOURCE, TO_VARCHAR(INPUTS) AS INPUTS, TO_VARCHAR(TOKENS) AS TOKENS, "
                f"TO_VARCHAR(CHECKS) AS CHECKS, STATUS, ACTIVE, CREATED_BY, "
                f"TO_VARCHAR(CREATED_AT, 'YYYY-MM-DD HH24:MI') AS CREATED_AT FROM {self.themes} "
                f"QUALIFY ROW_NUMBER() OVER (PARTITION BY THEME_ID ORDER BY CREATED_AT DESC) = 1").collect()
        except Exception:
            return []
        out = []
        for r in rows:
            d = {k.lower(): v for k, v in row_dict(r).items()}
            if not d.get("active"):
                continue
            for k in ("inputs", "tokens", "checks"):
                try:
                    d[k] = json.loads(d.get(k) or "null")
                except (TypeError, ValueError):
                    d[k] = None
            out.append(d)
        return sorted(out, key=lambda d: str(d.get("name") or "").lower())

    # -- UAT: tile acceptance and page sign-off (append-only; newest row per tile/page wins) -------------------------
    def save_uat(self, e: dict[str, Any]) -> str:
        self.ensure()
        eid = uuid.uuid4().hex[:12]
        self.session.sql(
            f"INSERT INTO {self.uat} (ENTRY_ID, DASHBOARD_ID, SEMANTIC_VIEW, PAGE_ID, TILE_KEY, KIND, DECISION, COMMENT, "
            "TILE_SIG, PAGE_SIG, RUN_AT, VALIDATION_STATUS, CREATED_BY, DASHBOARD_NAME, PAGE_LABEL, TILE_TITLE) "
            "SELECT ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE(NULLIF(?, ''), CURRENT_USER()), ?, ?, ?",
            params=[eid, e.get("dashboard_id") or "", e.get("sv") or "", e.get("page_id") or "", e.get("tile_key") or "",
                    e["kind"], e["decision"], (e.get("comment") or "")[:2000], e.get("tile_sig") or "",
                    e.get("page_sig") or "", str(e.get("run_at") or ""), e.get("validation_status") or "",
                    self.actor or "", (e.get("dashboard_name") or "")[:200], (e.get("page_label") or "")[:200],
                    (e.get("tile_title") or "")[:300]]).collect()
        return eid

    def adopt_uat(self, sv: str, dashboard_id: str, name: str) -> None:
        """First save of a draft: its sign-off rows (stored without a dashboard id) move to the saved dashboard."""
        try:
            self.session.sql(f"UPDATE {self.uat} SET DASHBOARD_ID = ?, DASHBOARD_NAME = ? "
                             "WHERE SEMANTIC_VIEW = ? AND DASHBOARD_ID = ''", params=[dashboard_id, name[:200], sv]).collect()
        except Exception:
            pass

    _UAT_COLS = ("ENTRY_ID, DASHBOARD_ID, PAGE_ID, TILE_KEY, KIND, DECISION, COMMENT, TILE_SIG, PAGE_SIG, RUN_AT, "
                 "VALIDATION_STATUS, CREATED_BY, TO_VARCHAR(CREATED_AT, 'YYYY-MM-DD HH24:MI') AS CREATED_AT, "
                 "DASHBOARD_NAME, PAGE_LABEL, TILE_TITLE")

    def list_uat(self, sv: str, dashboard_id: str = "") -> list[dict[str, Any]]:
        try:
            self.ensure()
            where, params = ("DASHBOARD_ID = ?", [dashboard_id]) if dashboard_id else \
                ("SEMANTIC_VIEW = ? AND DASHBOARD_ID = ''", [sv])
            rows = self.session.sql(
                f"SELECT {self._UAT_COLS} FROM {self.uat} WHERE {where} ORDER BY CREATED_AT DESC", params=params).collect()
            return [{k.lower(): v for k, v in row_dict(r).items()} for r in rows]
        except Exception:
            return []

    def list_uat_tiles(self, days: int = 180) -> list[dict[str, Any]]:
        """Tile reviews and change requests on every saved dashboard (newest first), for the Change requests and
        Waiting for my sign-off lists. Only tiles with a request in the window are returned."""
        try:
            self.ensure()
            rows = self.session.sql(
                f"SELECT {self._UAT_COLS} FROM {self.uat} WHERE KIND = 'tile' AND DASHBOARD_ID <> '' "
                "AND CREATED_AT >= DATEADD(day, -?, CURRENT_TIMESTAMP()) "
                "QUALIFY COUNT_IF(DECISION = 'rejected') OVER (PARTITION BY DASHBOARD_ID, TILE_KEY) > 0 "
                "ORDER BY CREATED_AT DESC LIMIT 5000", params=[int(days)]).collect()
            return [{k.lower(): v for k, v in row_dict(r).items()} for r in rows]
        except Exception:
            return []

    # -- data alerts -----------------------------------------------------------------------------------------------
    def save_alert(self, spec: dict[str, Any], sql: str, alert_id: str = "") -> str:
        self.ensure()
        if alert_id:
            self.session.sql(
                f"UPDATE {self.schema}.AA_ALERTS SET NAME = ?, SPEC = PARSE_JSON(?), CHECK_SQL = ?, "
                "UPDATED_AT = CURRENT_TIMESTAMP(), LAST_FIRED_KEY = '' WHERE ALERT_ID = ?",
                params=[spec.get("name", "")[:200], json.dumps(spec, default=str), sql, alert_id]).collect()
            return alert_id
        aid = uuid.uuid4().hex[:12]
        self.session.sql(
            f"INSERT INTO {self.schema}.AA_ALERTS (ALERT_ID, NAME, SEMANTIC_VIEW, DASHBOARD_ID, DASHBOARD_NAME, SPEC, "
            "CHECK_SQL, ACTIVE, DELETED, OWNER) SELECT ?, ?, ?, ?, ?, PARSE_JSON(?), ?, TRUE, FALSE, "
            "COALESCE(NULLIF(?, ''), CURRENT_USER())",
            params=[aid, spec.get("name", "")[:200], spec.get("sv", ""), spec.get("dashboard_id", ""),
                    spec.get("dashboard_name", ""), json.dumps(spec, default=str), sql, self.actor or ""]).collect()
        return aid

    def list_alerts(self) -> list[dict[str, Any]]:
        try:
            self.ensure()
            rows = self.session.sql(
                f"SELECT ALERT_ID, NAME, SEMANTIC_VIEW, DASHBOARD_ID, DASHBOARD_NAME, TO_VARCHAR(SPEC) AS SPEC, "
                "ACTIVE, OWNER, TO_VARCHAR(CREATED_AT, 'YYYY-MM-DD HH24:MI') AS CREATED_AT, LAST_CHECK_AT, LAST_STATUS, "
                f"LAST_VALUE, LAST_MESSAGE, LAST_FIRED_AT FROM {self.schema}.AA_ALERTS WHERE DELETED = FALSE "
                "ORDER BY CREATED_AT DESC").collect()
            out = []
            for r in rows:
                d = {k.lower(): v for k, v in row_dict(r).items()}
                try:
                    d["spec"] = json.loads(d.get("spec") or "{}")
                except ValueError:
                    d["spec"] = {}
                out.append(d)
            return out
        except Exception:
            return []

    def alert_runs(self, alert_id: str, limit: int = 20) -> list[dict[str, Any]]:
        try:
            rows = self.session.sql(
                f"SELECT CHECKED_AT, TRIGGER_KIND, STATUS, PERIOD_LABEL, VALUE, COMPARE_VALUE, FIRED, EMAILED, MESSAGE "
                f"FROM {self.schema}.AA_ALERT_RUNS WHERE ALERT_ID = ? ORDER BY CHECKED_AT DESC LIMIT {int(limit)}",
                params=[alert_id]).collect()
            return [{k.lower(): v for k, v in row_dict(r).items()} for r in rows]
        except Exception:
            return []

    def set_alert(self, alert_id: str, active: Optional[bool] = None, deleted: bool = False) -> None:
        self.ensure()
        if deleted:
            self.session.sql(f"UPDATE {self.schema}.AA_ALERTS SET DELETED = TRUE, ACTIVE = FALSE WHERE ALERT_ID = ?",
                             params=[alert_id]).collect()
        elif active is not None:
            self.session.sql(f"UPDATE {self.schema}.AA_ALERTS SET ACTIVE = ? WHERE ALERT_ID = ?",
                             params=[bool(active), alert_id]).collect()

    def set_setting(self, key: str, value: str) -> None:
        self.ensure()
        self.session.sql(f"INSERT INTO {self.settings} (SETTING_KEY, SETTING_VALUE, SET_BY) "
                         "SELECT ?, ?, COALESCE(NULLIF(?, ''), CURRENT_USER())",
                         params=[key, value, self.actor or ""]).collect()

    def get_setting(self, key: str) -> Optional[dict[str, Any]]:
        try:
            self.ensure()
            rows = self.session.sql(
                f"SELECT SETTING_VALUE, SET_BY, TO_VARCHAR(SET_AT, 'YYYY-MM-DD HH24:MI') AS SET_AT FROM {self.settings} "
                f"WHERE SETTING_KEY = ? ORDER BY SET_AT DESC LIMIT 1", params=[key]).collect()
            return {k.lower(): v for k, v in row_dict(rows[0]).items()} if rows else None
        except Exception:
            return None

    def list_settings(self, prefix: str) -> dict[str, str]:
        """Latest value of every setting whose key starts with prefix (e.g. 'owner:' -> dashboard owner hand-overs)."""
        try:
            self.ensure()
            rows = self.session.sql(
                f"SELECT SETTING_KEY, SETTING_VALUE FROM {self.settings} WHERE STARTSWITH(SETTING_KEY, ?) "
                "QUALIFY ROW_NUMBER() OVER (PARTITION BY SETTING_KEY ORDER BY SET_AT DESC) = 1",
                params=[prefix]).collect()
            return {str(d.get("setting_key")): str(d.get("setting_value") or "")
                    for d in ({k.lower(): v for k, v in row_dict(r).items()} for r in rows)}
        except Exception:
            return {}

    def ai_usage_today(self, actor: str) -> dict[str, int]:
        """Cortex calls this person made today. Page summaries are not counted: they run when a page is viewed."""
        rows = self.session.sql(
            f"SELECT COUNT_IF(FEATURE <> 'page_summary') AS N_ALL, COUNT_IF(FEATURE = 'agent_question') AS N_AGENT "
            f"FROM {self.ai_runs} WHERE CREATED_BY = ? AND CREATED_AT >= CURRENT_DATE()", params=[actor]).collect()
        r = row_dict(rows[0]) if rows else {}
        return {"all": int(r.get("n_all") or 0), "agent": int(r.get("n_agent") or 0)}

    def ai_ledger(self, limit: int = 50) -> list[dict[str, Any]]:
        if not self.ensure():
            return []
        rows = self.session.sql(
            f"SELECT FEATURE, SEMANTIC_VIEW, LEFT(INPUT, 200) AS INPUT, LEFT(OUTPUT, 300) AS OUTPUT, PROVENANCE, "
            f"STATUS, LATENCY_S, CREATED_BY, TO_VARCHAR(CREATED_AT, 'YYYY-MM-DD HH24:MI') AS CREATED_AT "
            f"FROM {self.ai_runs} ORDER BY CREATED_AT DESC LIMIT {int(limit)}").collect()
        return [row_dict(r) for r in rows]

    # -- Cortex Agent evaluations (Snowflake AI Observability) ----------------------------------------
    def eval_runs(self, agent_fqn: str) -> list[dict[str, Any]]:
        try:
            rows = self.session.sql(
                f"SELECT RUN_NAME, STARTED_BY, TO_VARCHAR(STARTED_AT, 'YYYY-MM-DD HH24:MI') AS STARTED_AT "
                f"FROM {self.schema}.AA_EVAL_RUNS WHERE AGENT = ? ORDER BY STARTED_AT DESC LIMIT 10",
                params=[agent_fqn]).collect()
            return [row_dict(r) for r in rows]
        except Exception:
            return []

    def eval_start(self, agent_fqn: str, config: str, run_name: str) -> str:
        self.session.sql("CALL EXECUTE_AI_EVALUATION('START', OBJECT_CONSTRUCT('run_name', ?), ?)",
                         params=[run_name, config]).collect()
        self.session.sql(f"CREATE TABLE IF NOT EXISTS {self.schema}.AA_EVAL_RUNS (RUN_NAME VARCHAR, AGENT VARCHAR, "
                         "CONFIG VARCHAR, STARTED_BY VARCHAR, STARTED_AT TIMESTAMP_LTZ DEFAULT CURRENT_TIMESTAMP())").collect()
        self.session.sql(f"INSERT INTO {self.schema}.AA_EVAL_RUNS (RUN_NAME, AGENT, CONFIG, STARTED_BY) "
                         "SELECT ?, ?, ?, CURRENT_USER()", params=[run_name, agent_fqn, config]).collect()
        return run_name

    def eval_status(self, config: str, run_name: str) -> str:
        try:
            rows = self.session.sql("CALL EXECUTE_AI_EVALUATION('STATUS', OBJECT_CONSTRUCT('run_name', ?), ?)",
                                    params=[run_name, config]).collect()
            return " ".join(str(v) for v in row_dict(rows[0]).values())[:300] if rows else ""
        except Exception as exc:
            return f"status unavailable: {str(exc)[:200]}"

    def eval_results(self, agent_fqn: str, run_name: str) -> dict[str, Any]:
        db, sch, name = agent_fqn.split(".")
        src = "TABLE(SNOWFLAKE.LOCAL.GET_AI_EVALUATION_DATA(?, ?, ?, 'CORTEX AGENT', ?))"
        args = [db, sch, name, run_name]
        try:
            summary = [row_dict(r) for r in self.session.sql(
                f"SELECT METRIC_NAME, AVG(EVAL_AGG_SCORE) AS SCORE, COUNT(*) AS N FROM {src} "
                "WHERE METRIC_NAME IS NOT NULL GROUP BY 1 ORDER BY 1", params=args).collect()]
            records = [row_dict(r) for r in self.session.sql(
                f"SELECT INPUT, METRIC_NAME, EVAL_AGG_SCORE AS SCORE, LEFT(TO_VARCHAR(OUTPUT), 600) AS OUTPUT, "
                f"DURATION_MS FROM {src} WHERE METRIC_NAME IS NOT NULL ORDER BY INPUT, METRIC_NAME LIMIT 200",
                params=args).collect()]
            return {"summary": summary, "records": records, "error": ""}
        except Exception as exc:
            return {"summary": [], "records": [], "error": str(exc)[:300]}

    def usage_by_feature(self, tag_app: str, days: int = 7) -> dict[str, Any]:
        """Cost per app feature from QUERY_TAG: queries + elapsed time (QUERY_HISTORY), Cortex token credits
        (CORTEX_FUNCTIONS_QUERY_USAGE_HISTORY) and warehouse credits (QUERY_ATTRIBUTION_HISTORY).
        Each enrichment is optional; ACCOUNT_USAGE lags by up to a few hours."""
        days = max(1, min(int(days), 90))
        q = ("SELECT QUERY_ID, COALESCE(TRY_PARSE_JSON(QUERY_TAG):feature::STRING, 'other') AS FEATURE, "
             "TOTAL_ELAPSED_TIME FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY "
             f"WHERE START_TIME >= DATEADD('day', -{days}, CURRENT_TIMESTAMP()) "
             f"AND TRY_PARSE_JSON(QUERY_TAG):app::STRING = '{tag_app}'")
        cortex = ("SELECT QUERY_ID, SUM(TOKEN_CREDITS) AS CR, SUM(TOKENS) AS TK "
                  "FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_FUNCTIONS_QUERY_USAGE_HISTORY GROUP BY 1")
        attrib = ("SELECT QUERY_ID, SUM(CREDITS_ATTRIBUTED_COMPUTE) AS WC "
                  "FROM SNOWFLAKE.ACCOUNT_USAGE.QUERY_ATTRIBUTION_HISTORY "
                  f"WHERE START_TIME >= DATEADD('day', -{days}, CURRENT_TIMESTAMP()) GROUP BY 1")
        variants = [
            (f"WITH q AS ({q}), c AS ({cortex}), a AS ({attrib}) SELECT q.FEATURE, COUNT(*) AS QUERIES, "
             "ROUND(SUM(q.TOTAL_ELAPSED_TIME) / 1000, 1) AS ELAPSED_S, SUM(c.CR) AS CORTEX_CREDITS, "
             "SUM(c.TK) AS TOKENS, SUM(a.WC) AS WAREHOUSE_CREDITS FROM q LEFT JOIN c ON c.QUERY_ID = q.QUERY_ID "
             "LEFT JOIN a ON a.QUERY_ID = q.QUERY_ID GROUP BY 1 ORDER BY ELAPSED_S DESC"),
            (f"WITH q AS ({q}), c AS ({cortex}) SELECT q.FEATURE, COUNT(*) AS QUERIES, "
             "ROUND(SUM(q.TOTAL_ELAPSED_TIME) / 1000, 1) AS ELAPSED_S, SUM(c.CR) AS CORTEX_CREDITS, "
             "SUM(c.TK) AS TOKENS FROM q LEFT JOIN c ON c.QUERY_ID = q.QUERY_ID GROUP BY 1 ORDER BY ELAPSED_S DESC"),
            (f"WITH q AS ({q}) SELECT FEATURE, COUNT(*) AS QUERIES, ROUND(SUM(TOTAL_ELAPSED_TIME) / 1000, 1) "
             "AS ELAPSED_S FROM q GROUP BY 1 ORDER BY ELAPSED_S DESC"),
        ]
        last = ""
        for i, sql in enumerate(variants):
            try:
                rows = [row_dict(r) for r in self.session.sql(sql).collect()]
                return {"rows": rows, "days": days, "error": "",
                        "detail": ["full", "no warehouse attribution", "queries and time only"][i]}
            except Exception as exc:
                last = str(exc)[:200]
        return {"rows": [], "days": days, "error": last, "detail": ""}

    def cortex_usage(self) -> dict[str, Any]:
        """Account-level Cortex credit usage (needs ACCOUNT_USAGE access; optional)."""
        try:
            rows = self.session.sql(
                "SELECT FUNCTION_NAME, MODEL_NAME, SUM(TOKEN_CREDITS) AS CREDITS, SUM(TOKENS) AS TOKENS "
                "FROM SNOWFLAKE.ACCOUNT_USAGE.CORTEX_FUNCTIONS_USAGE_HISTORY "
                "WHERE START_TIME >= DATEADD('day', -30, CURRENT_TIMESTAMP()) "
                "GROUP BY 1, 2 ORDER BY CREDITS DESC LIMIT 20").collect()
            return {"rows": [row_dict(r) for r in rows], "error": ""}
        except Exception as exc:
            return {"rows": [], "error": str(exc)[:200]}
