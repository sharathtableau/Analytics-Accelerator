# Analytics Accelerator – Enterprise: architecture (23 Oct 2026)

Slide version: `Downloads\Analytics Accelerator Partner Demo\Analytics_Accelerator_Architecture.pptx` (one slide, deck style, speaker notes).

Everything runs inside the client's Snowflake account. Data, prompts and answers never leave; the only outbound traffic is alert emails to the notification integration's recipients.

## Components

| Zone | Component | Snowflake object / feature | Role |
|---|---|---|---|
| Users (outside) | Builders | Snowflake sign-in, HTTPS | Analysts who design, validate and publish |
| | Viewers | USAGE on the Portal only | Business roles, read-only |
| | Alert recipients | Email | Receive alert emails |
| Streamlit in Snowflake | Builder app | `ANALYTICS_ACCELERATOR_ENTERPRISE` (container runtime, owner's rights) | React UI (`app_bundle.js`) + Python services: router, persona ideas, composer, validator, query engine, UAT, publish, alert builder |
| | Portal app | `ANALYTICS_ACCELERATOR_PORTAL` | Same code in portal mode: published dashboards, ask the agent, no building |
| | Domain workspaces | Code: `domains.py`, `domain_packs.py`, `domain_tiles.py` | Retail · Finance · CPG: personas, layout packs, alert library, analysis tiles |
| Cortex AI and Snowflake ML | LLM | `AI_COMPLETE` | Ideas, routing, layouts, alert wording. Returns JSON, checked by the validator |
| | Summary | `AI_AGG` | Page summary over governed rows |
| | Cortex Agent (one per domain) | `CREATE AGENT`, `DATA_AGENT_RUN` | Tools: Cortex Analyst (semantic view), Cortex Search (documents), `log_decision` → `AA_CREATE_DECISION` |
| | ML functions | `SNOWFLAKE.ML.FORECAST`, `TOP_INSIGHTS`, `ANOMALY_DETECTION` | Forecasts, drivers, exceptions on governed series |
| Data and state | Semantic views | `RETAIL_ANALYTICS_SV`, `FINANCE_ANALYTICS_SV`, `CPG_ANALYTICS_SV` | Every metric defined once; every number on screen is a `SEMANTIC_VIEW()` query |
| | Domain schemas | `WBR_DB.RETAIL_DEMO`, `FINANCE_DEMO`, `CPG_DEMO` (tables, rolling-date views) | Client data |
| | Cortex Search | `<DOMAIN>_DOCS_SEARCH` | Policies, ontology, metric glossary |
| | Document stage | `AI_PARSE_DOCUMENT` + chunking | Parsed documents for search |
| | Alert task | `AA_ALERTS_TASK` → procedure `AA_RUN_ALERTS` | Runs the check SQL saved with each alert |
| | App schema | `WBR_DB.ANALYTICS_ENTERPRISE.AA_*` | Dashboards, published versions, ideas, alerts, UAT sign-offs, validation runs, decisions, AI ledger (`AA_AI_RUNS`) |
| | Email | `SYSTEM$SEND_EMAIL` via `AA_EMAIL_INT` | Alert emails (only egress) |

## Connections (numbered as on the slide)

1. **prompt:** Builder app → `AI_COMPLETE`; JSON back; the validator checks every metric, dimension and chart against the semantic view and drops anything invalid.
2. **SQL query:** apps → semantic views with `SEMANTIC_VIEW()`; this is where every number comes from (plus Snowflake ML on the same governed series).
3. **question:** apps → Cortex Agent; the agent uses Analyst on the semantic view and Search on the documents, and can log a decision.
4. **app state:** apps read and write the `AA_*` tables (dashboards, ideas, sign-offs, the AI ledger).
5. **email:** alert task → `SYSTEM$SEND_EMAIL` → recipients.

## Across every component

- RBAC: the app sees only what its role can use; viewers get USAGE on the Portal only.
- Query tag `aa-enterprise` on every query; cost by feature from `ACCOUNT_USAGE`.
- AI ledger: every Cortex call with prompt, output and tokens, per signed-in person (`st.user`).
- Agent evaluations with `AI_EVALUATION`; optional AI budget (`setup/admin_ai_guardrails.sql`).
- Deployed with the Snowflake CLI (`snow streamlit deploy`) after the unit tests pass (283 on 22 Oct).

## Design rule

**AI proposes, code verifies.** Cortex output is a suggestion; it is validated before use and logged. Cortex never produces a number on a tile.
