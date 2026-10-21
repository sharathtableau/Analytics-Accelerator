"""Deployment configuration (edit here, not in code)."""
import os
APP_SCHEMA = "WBR_DB.ANALYTICS_ENTERPRISE"
# Schemas whose semantic views and agents the app may use (current role still needs grants).
DISCOVERY_SCHEMAS = ["WBR_DB.RETAIL_DEMO", "WBR_DB.PUBLIC", "WBR_DB.PIPELINE_DEMO", "SANDBOX.BI", APP_SCHEMA]
AGENT_SCHEMAS = ["WBR_DB.RETAIL_DEMO", "WBR_DB.PUBLIC", "WBR_DB.PIPELINE_DEMO", "SANDBOX.BI", APP_SCHEMA]
# Cortex models tried in order; the first that works for this account is used.
MODELS = ["claude-sonnet-4-5", "llama3.3-70b", "mistral-large2"]
APP_TITLE = "Analytics Accelerator"

# Cost guardrails: Cortex calls per person per day (0 = no limit). Page summaries shown while viewing are not counted.
AI_DAILY_LIMIT = int(_v) if (_v := os.environ.get("AA_AI_DAILY_LIMIT", "200").strip()).isdigit() else 200
AGENT_DAILY_LIMIT = int(_v) if (_v := os.environ.get("AA_AGENT_DAILY_LIMIT", "40").strip()).isdigit() else 40
# Dashboard Portal (viewer-only app). PORTAL_URL opens its catalog from the builder's left bar.
# PORTAL_APP_URL (optional): the portal's direct app address printed by deploy_portal.cmd; when set, the
# publish dialog's share link opens that one dashboard in the portal (?view=<id>) instead of the builder.
PORTAL_URL = os.environ.get("AA_PORTAL_URL", "https://app.snowflake.com/wb19670/c2gpartners/#/streamlit-apps/"
                            "WBR_DB.ANALYTICS_ENTERPRISE.ANALYTICS_ACCELERATOR_PORTAL")
PORTAL_APP_URL = os.environ.get("AA_PORTAL_APP_URL", "")

# Warehouse the Cortex Agent analyst tool runs SQL on (falls back to the session warehouse).
AGENT_WAREHOUSE = "POWERHOUSE"

# Featured semantic views: shown first on Home, most Cortex ideas come from them, and prompts that could
# fit several datasets are routed to them. Leave empty to treat every view equally.
FEATURED_VIEWS = [v for v in os.environ.get(
    "AA_FEATURED", "WBR_DB.RETAIL_DEMO.RETAIL_ANALYTICS_SV,SANDBOX.BI.INFERA_SEMANTIC_VIEW#VW_RETAIL_MASTER").split(",") if v]
FEATURED_LABELS = {"WBR_DB.RETAIL_DEMO.RETAIL_ANALYTICS_SV": "Harborline Retail (live)",
                   "SANDBOX.BI.INFERA_SEMANTIC_VIEW#VW_RETAIL_MASTER": "Infera Retail",
                   "WBR_DB.PUBLIC.SUPERSTORE_DEMO_SV": "Demo Retail (live)"}

# Cortex Search services the domain agent gets as a second tool (documents: policies, standards, WBR notes,
# metric glossary). Format for the env override: "SV_FQN=SERVICE_FQN,SV2=SERVICE2".
_search_env = os.environ.get("AA_SEARCH", "")
SEARCH_SERVICES = dict(x.split("=", 1) for x in _search_env.split(",") if "=" in x) or {
    "WBR_DB.RETAIL_DEMO.RETAIL_ANALYTICS_SV": "WBR_DB.RETAIL_DEMO.RETAIL_DOCS_SEARCH"}

# Custom agent tool (stored procedure) that lets the agent log a decision. Created by setup/06_agent_tools.sql.
# Set AA_DECISION_TOOL="" to leave the tool out of agent definitions.
DECISION_TOOL = os.environ.get("AA_DECISION_TOOL", f"{APP_SCHEMA}.AA_CREATE_DECISION")

# D1: Snowflake-native Cortex Agent evaluations (AI Observability). agent FQN -> evaluation YAML on a stage.
# Created by setup/run_agent_eval.cmd. Gate = minimum average score per metric to "promote" the agent.
EVAL_CONFIGS = {f"{APP_SCHEMA}.AA_RETAIL_ANALYTICS_SV_AGENT": f"@{APP_SCHEMA}.AA_EVAL_CONFIG/aa_agent_eval.yaml"}
EVAL_GATE = {"answer_correctness": 0.70, "logical_consistency": 0.80, "tool_selection_accuracy": 0.75,
             "cites_sources": 0.70}
