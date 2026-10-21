# Snowflake capability map — Analytics Accelerator (Enterprise)

Every relevant Snowflake capability, where it appears in the app, and a reason for anything not used.
Status: ✅ Used (live) · 🔧 Built, pending first live run · 🟡 Partial · 📅 Planned (see ENTERPRISE_TRACKER.md) · ⛔ Deliberately not used
Last updated: 1 Oct 2026

## Semantic layer and data
| Capability | Status | Where / why |
|---|---|---|
| Semantic views (`CREATE SEMANTIC VIEW`, FACTS, metrics on metrics, synonyms, comments) | ✅ | `RETAIL_ANALYTICS_SV` — single source of truth for every metric, definition and formula shown in the app |
| `SEMANTIC_VIEW()` queries | ✅ | Every number on every tile; filters applied inside the semantic query |
| `DESCRIBE SEMANTIC VIEW`, `SHOW SEMANTIC DIMENSIONS … FOR METRIC` | ✅ | Catalog + validator: Cortex may only use real fields and valid metric × dimension pairs |
| Horizon Catalog / governed context for metrics | 📅 | B3 — verify product names (Horizon Context / Cortex Sense) before claiming |
| Auto-drafted semantic views (profile → `AI_COMPLETE` → approve → create) | 🔧 | Home → Connect a Snowflake table: Cortex drafts dimensions, metrics, ratios, synonyms and definitions from a column profile; validator + human review; `CREATE SEMANTIC VIEW` |
| Metrics drafted for facts-only semantic views (profile through the view → `AI_COMPLETE` → validator → review) | 🔧 | Views without metrics (e.g. `SANDBOX.BI.INFERA_SEMANTIC_VIEW`) get metrics from their facts; queried as ad-hoc metrics with the semantic view's standard-SQL interface; owner can paste the generated METRICS clause |
| Dynamic tables / streams / tasks | ⛔ | Demo "live feed" is time-revealed views over pre-generated data; a real client would land data with Snowpipe/dynamic tables — nothing in the app depends on how data arrives |

## Cortex AI (AISQL)
| Capability | Status | Where / why |
|---|---|---|
| `AI_COMPLETE` | ✅ | Home ideas per audience × metric theme (validated: distinct themes and metrics per audience), prompt routing, dashboard layout design, add page / tile in English, per-tile edits — always constrained and validated (page-summary fallback) |
| `AI_AGG` | 🔧 | Page AI summary: aggregates the page's governed fact rows inside Snowflake; `AI_COMPLETE` fallback |
| `AI_SUMMARIZE_AGG` | ⛔ | `AI_AGG` takes a task instruction (audience, page question, output shape); `AI_SUMMARIZE_AGG` doesn't |
| `AI_PARSE_DOCUMENT` | ✅ | Harborline policy PDFs parsed on stage (`setup/retail/05b_docs_search.sql`) |
| `SPLIT_TEXT_RECURSIVE_CHARACTER` | ✅ | Markdown-aware chunking before indexing |
| `AI_EXTRACT` | 📅 | C5 — pull effective dates / owners / thresholds out of policies into a table |
| `AI_CLASSIFY`, `AI_SENTIMENT` | ⛔ (demo) | Retail demo data has no free-text column; planned for client data with reviews/tickets (C6) |
| `AI_FILTER`, `AI_EMBED`, `AI_TRANSLATE`, `AI_REDACT` | ⛔ | No use case in the product flow; Cortex Search manages its own embeddings; US-only data |

## Cortex Search, Analyst, Agents
| Capability | Status | Where / why |
|---|---|---|
| Cortex Analyst (text-to-SQL on the semantic view) | ✅ | Tool 1 of the domain agent; SQL shown with every answer |
| Cortex Search service | ✅ | `RETAIL_DOCS_SEARCH` over policies, standards, plan memo, WBR notes and the metric glossary |
| Cortex Agents (`CREATE AGENT`, `DATA_AGENT_RUN`, threads) | ✅ | One shared agent per semantic view, auto-created/upgraded by the app; "Ask agent" on exceptions and bars; ✦ panel on each tile |
| Agent with two tools (Analyst + Search) | 🔧 | Agent spec v2 (`aa-spec-2`) adds the `documents` tool; answers cite document IDs |
| Custom agent tools (stored procedures) | 🔧 | `log_decision` → `AA_CREATE_DECISION`: the agent writes a validated decision (owner, due, evidence) to Snowflake. Next: `run_forecast`, `build_dashboard` |
| Multi-agent routing / agent-to-agent | 📅 | A3/A5 — decision pending (own router vs Native App agent-to-agent) |
| Snowflake Intelligence | 📅 **P0** | A6 — same agent answering outside the app |
| MCP server | 📅 | A4 — expose app capabilities to Snowflake Intelligence / CoWork |

## Snowflake ML functions
| Capability | Status | Where / why |
|---|---|---|
| `SNOWFLAKE.ML.FORECAST` | ✅ | Forecast tiles with 80% band, trained on the governed series |
| `SNOWFLAKE.ML.TOP_INSIGHTS` | ✅ | "What drove the change" — contributors across dimensions |
| `SNOWFLAKE.ML.ANOMALY_DETECTION` | 🔧 | Exception tiles: multi-series model (one series per segment), 95% prediction interval; z-score only while training or as fallback |
| `SNOWFLAKE.ML.CLASSIFICATION` | ⛔ | No prediction use case in a dashboard builder |

## Persona layouts (1 Oct)
| Capability | Status | Where / why |
|---|---|---|
| Reviewed layout per audience, slots filled by `AI_COMPLETE` | 🔧 | `persona_layouts.py` — Executive brief, Manager scorecard, Operations control room; Cortex picks only from valid options per slot, validator certifies |
| Time grain per audience | 🔧 | Executive month + YTD, Manager week, Operations today by hour (`AUDIENCE_GRAIN`) |
| Live operations on `SEMANTIC_VIEW()` | 🔧 | Today to the current hour vs the same weekday last week (hour filter inside the semantic query); worklist vs 4 same weekdays |
| ML forecast to year end on the executive trajectory | 🔧 | `SNOWFLAKE.ML.FORECAST` on the monthly series, cumulated onto YTD actual |

## Trust, governance, cost
| Capability | Status | Where / why |
|---|---|---|
| RBAC (role-scoped discovery; app objects owned by a role) | ✅ | App only sees semantic views/agents the role can use |
| Owner's-rights Streamlit, `GRANT USAGE ON STREAMLIT` | ✅ | Publish (option A): read-only viewer link shared to roles |
| Row access / masking policies end to end | ⏸ | D3 paused — two roles, different numbers; needs caller's-rights queries for viewers |
| AI Observability — Cortex Agent evaluations (`SYSTEM$CREATE_EVALUATION_DATASET`, `EXECUTE_AI_EVALUATION`, `GET_AI_EVALUATION_DATA`) | 🔧 | Retail agent evaluated on 8 ground-truth questions: answer correctness, logical consistency, tool selection, custom citation judge; promotion gate in Governance; traces in Snowsight |
| Cortex Guard, prompt-injection defence, AI Gateway | 📅 | D2 — today the validator rejects anything outside known fields/charts |
| `ACCOUNT_USAGE` (QUERY_HISTORY, CORTEX_FUNCTIONS_QUERY_USAGE_HISTORY, QUERY_ATTRIBUTION_HISTORY) | 🔧 | Governance → cost by app feature (queries, time, Cortex and warehouse credits) |
| Query tags for cost attribution | 🔧 | JSON `QUERY_TAG` set per action: app, feature, semantic view, dashboard |

## Platform and distribution
| Capability | Status | Where / why |
|---|---|---|
| Streamlit in Snowflake, container runtime, Components v2 (React) | ✅ | The whole app; nothing leaves Snowflake |
| Snowflake CLI | ✅ | `deploy_enterprise.cmd` (tests run before every deploy) |
| Native App (with agents + MCP, GA 7 Aug 2026) | 📅 | E1 — decision pending on React↔Python bridge inside a Native App |
| Marketplace / private listing | 📅 | E2 |
| Cortex Code (CoCo) | 📅 | G2 — optional build talking point |
