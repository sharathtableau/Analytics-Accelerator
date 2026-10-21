# Enterprise tracker — Analytics Accelerator (Snowflake partner demo Tue 6 Oct 2026)

**Read this first in every session.** Source: the 30 Sep brain-dump ("every step carried by a named
Snowflake AI feature") + what was built through 1 Oct. Update the Status column when anything changes.

Status: ✅ Done · 🔧 Built, needs your live run · ⏸ Paused / decision open · 🟡 Partial · ❌ Not started · ⏸ Decision open · ⛔ Obsolete
Priority: **P0** = before the demo · **P1** = demo if time · **P2** = after the demo (roadmap slide)

## A. Multi-agent layer (the headline)
| # | Item | Status | Where it stands | Pri |
|---|---|---|---|---|
| A1 | One Cortex Agent per domain, tools = Cortex Analyst + Cortex Search | 🔧 | Agent spec v2: `analyst` + `documents` (Cortex Search) tools, cites doc IDs; app auto-upgrades the shared agent on first question. **Run `setup\retail\run_docs_search.cmd`, then deploy** | P0 |
| A2 | Action tools (stored procs): `create_decision`, `run_forecast`, `build_dashboard`, `approve_metric` | 🔧 | `AA_CREATE_DECISION` procedure (validated, p_-params) + agent tool `log_decision` (spec aa-spec-3); app shows "Logged in Snowflake by the agent" card and refreshes Decisions. **Run `setup\run_agent_tools.cmd`, then deploy.** `run_forecast` / `build_dashboard` / `approve_metric` still open (P2) | P1 |
| A3 | Coordinating layer routes each question to the right domain agent | 🟡 | Home prompt is routed to the right semantic view by Cortex (`home.route`); agent chat uses the current dashboard's agent only | P2 |
| A4 | MCP server so app capabilities work in Snowflake Intelligence / CoWork | ❌ | — | P2 |
| A5 | Decide: own router vs agent-to-agent (Native Apps) | ⏸ | — | P2 |
| A6 | Same agent answering in Snowflake Intelligence | ❌ | Agent exists in schema; add it in the SI UI (no code) | **P0** |

## B. Semantic foundation that generates itself
| # | Item | Status | Where it stands | Pri |
|---|---|---|---|---|
| B1 | Auto-draft semantic view on source registration (profile → AI_COMPLETE drafts dims/metrics/synonyms/verified queries → approve → CREATE) | 🔧 | Home → "＋ Connect a Snowflake table": pick a table → profile (INFORMATION_SCHEMA + distinct/null/sample stats) → `AI_COMPLETE` draft → validator (real columns only, aggregation vs type, names, ratios) → editable review with SQL preview → `CREATE VIEW` (C_-prefixed source) + `CREATE SEMANTIC VIEW` in the app schema → test query → available on Home, routing and the agent. Verified queries are proposed but not yet written into the view | P1 |
| B2 | Reuse Tableau accelerator `cortex_semantic.py` | 🟡 | Reused its patterns (INFORMATION_SCHEMA introspection, identifier quoting); its generator is Tableau-IR driven, so raw tables use the new `semantic_builder.py` | P2 |
| B3 | Link to Horizon Context / Cortex Sense (names unverified) | ❌ | Verify these exist first | P2 |
| B4 | Decide: semantic view = single source of truth for metrics | ✅ | App reads metrics, definitions, formulas and valid metric×dimension pairs from the SV; no separate registry | — |

## C. AI in every screen
| # | Item | Status | Where it stands | Pri |
|---|---|---|---|---|
| C1 | Key drivers — `ML.TOP_INSIGHTS` | ✅ | "What moved" tiles, reconciled bridge fallback | — |
| C2 | Forecast — `ML.FORECAST` | ✅ | Forecast tiles, 80% band | — |
| C3 | Anomaly flags — `ML.ANOMALY_DETECTION` | 🔧 | Exception tiles: one multi-series model per tile (segments = series), trained on prior periods, latest period vs 95% prediction interval; runs in the background ML phase like FORECAST; z-score shown first and as fallback; "Snowflake ML · ANOMALY_DETECTION" badge + normal range per row. Deploy and test (no setup script) | P1 |
| C4 | Narrative cards — `AI_AGG` / `AI_SUMMARIZE_AGG` | 🔧 | "Generate with Cortex" page summary = `AI_AGG` over the page's governed fact rows (one row per fact, FLATTEN of a bound JSON array); `AI_COMPLETE` fallback; provenance shows which ran | P1 |
| C5 | Documents — `AI_PARSE_DOCUMENT` / `AI_EXTRACT` into Cortex Search | 🟡 ✅ live 1 Oct (parse + split + search verified; `AI_EXTRACT` open) | 5 Harborline PDFs (policy, carrier SLA, replenishment, plan memo, WBR notes) + metric glossary from the SV → stage → `AI_PARSE_DOCUMENT` → `SPLIT_TEXT_RECURSIVE_CHARACTER` → `RETAIL_DOCS_SEARCH` (fallbacks if a function is off). `AI_EXTRACT` still open | P0 |
| C6 | Text columns — `AI_CLASSIFY` / `AI_SENTIMENT` | ❌ | Retail data has no free-text column | P2 |
| C7 | Search bar via Cortex Search | ❌ | — | P2 |
| C8 | Agent drafts a decision (owner, due, evidence) | 🔧 via A2 — agent asks for owner/due if missing, then logs | "Log decision" pre-fills from exception evidence; not drafted by the agent | P1 (with A2) |
| C9 | Cortex designs the dashboard (`AI_COMPLETE`, governed validator) | ✅ | Home ideas, layout design, Review step, add page/tile in English, per-tile ✦ panel | — |

## D. Trust, governance, cost
| # | Item | Status | Where it stands | Pri |
|---|---|---|---|---|
| D1 | AI Quality on Snowflake **AI Observability** (evals, traces) | 🔧 | Native Cortex Agent evaluations: 8-question dataset with ground truth + expected tool calls (`AA_RETAIL_AGENT_EVALSET`), YAML config on `AA_EVAL_CONFIG` (answer_correctness, logical_consistency, tool_selection_accuracy + custom `cites_sources` judge), `EXECUTE_AI_EVALUATION`. Governance → Agent evaluations: runs, scores, promotion gate, "Run new evaluation"; traces in Snowsight. **Run `setup\run_agent_eval.cmd` after the agent exists.** Ledger `AA_AI_RUNS` kept for non-agent AI calls | P1 |
| D2 | Guardrails — Cortex Guard, prompt-injection, AI Gateway | ❌ | Validator constrains Cortex output to known fields/charts | P2 (slide) |
| D3 | Row access / masking end to end (two roles, different numbers) | ⏸ **Paused** (1 Oct, Sharath) | App runs with owner's rights; viewers see owner's data. To implement later: caller's-rights queries for viewers + a row access policy on region | Later |
| D4 | Cost panel — tokens/credits per agent and feature | 🔧 | Every app query carries a JSON `QUERY_TAG` (app, feature, semantic view, dashboard); Governance → "Cost by app feature": queries + elapsed (QUERY_HISTORY), Cortex credits/tokens (CORTEX_FUNCTIONS_QUERY_USAGE_HISTORY), warehouse credits (QUERY_ATTRIBUTION_HISTORY), each optional. Per-agent split still open (agent runs are tagged as feature `ask` / `tile_ask`) | P1 |

## E. Distribution
| # | Item | Status | Where it stands | Pri |
|---|---|---|---|---|
| E1 | Native App with Cortex Agents + MCP (GA 7 Aug 2026) | ⏸ | React↔Python link inside Native App Streamlit still unsolved | P2 |
| E2 | Marketplace / private listing | ❌ | — | P2 |

## F. Demo story
| # | Step | Status |
|---|---|---|
| F1 | Connect raw table → semantic view auto-drafted | 🔧 B1 built — playbook scenario 10 |
| F2 | Metrics approved | ✅ Review step |
| F3 | Dashboard generated | ✅ |
| F4 | "Why did it dip?" — drivers + forecast | ✅ |
| F5 | Decision logged | ✅ |
| F6 | Quality evidence + cost shown | 🟡 |
| F7 | Same agent in Snowflake Intelligence | ❌ (A6) |
| F8 | Decide dataset | ✅ Harborline retail (`WBR_DB.RETAIL_DEMO`, planted stories) |
| F9 | Decide audience in the room / demo surface | ⏸ |
| F10 | 15-min click-by-click demo script | ✅ `DEMO_SCRIPT.md` (draft — rehearse and adjust) |

## G. Build hygiene
| # | Item | Status | Note |
|---|---|---|---|
| G1 | Codex resetting deploy settings / `agent_preview.py` mix-up | ⛔ | Superseded: separate app `WBR_DB.ANALYTICS_ENTERPRISE.ANALYTICS_ACCELERATOR_ENTERPRISE`, `main_file: app.py`, `deploy_enterprise.cmd` (runs tests first) |
| G2 | Build parts with CoCo, mention in demo | ❌ | Optional talking point |

## Tasks from the brain-dump
| Task | Status |
|---|---|
| Fix live app (`agent_preview.py`) | ⛔ Superseded by the Enterprise app (live) |
| Validate one source end to end (tile → agent answer → follow-up) | 🟡 Tiles live on retail; agent auto-create fixed 1 Oct — re-test live |
| Feature availability check (models, AISQL, ML, Observability, Gateway) | 🟡 `setup/01_feature_check.sql` + app boot checks Cortex/Forecast/Top Insights/Agents; Observability/Gateway not checked |
| Cortex credit budget | ⏸ |
| Multi-tool agent (Analyst + Search), template `INFERA_KNOWLEDGE_HUB` | 🔧 built (A1) |
| Cortex Search over metric definitions + policies/WBR notes | ✅ live 1 Oct — `RETAIL_DOCS_SEARCH`, 3/3 test searches hit the right document |
| Snowflake capability map (every feature: used / planned / not used + why) | ✅ `CAPABILITY_MAP.md` — update with every change |
| Extend `snowflake-dashboard-builder-framework-revised.md` with agentic section | ❌ P1 |

## H. Enterprise gaps (added 1 Oct, not in the brain-dump)
| # | Item | Status | Pri |
|---|---|---|---|
| H1 | Alerts / subscriptions when an exception fires | ❌ | P2 |
| H2 | Export dashboard to PDF / PowerPoint | ❌ | P2 |
| H3 | Publish approval workflow (draft → review → publish, audited) | 🟡 versioned publish exists, no approval step | P2 |
| H4 | Cost guardrails (per-user Cortex quota, heavy-query warning) | ❌ | P2 |
| H10 | Clean-up of ML model objects (`AA_FC_*`, `AA_AD_*`) created per period/filter | ❌ | P2 |
| H5 | Monitoring (error rate, slow tiles, failed AI calls) | 🟡 logged in ledger, no health view | P2 |
| H6 | Release process: dev/test/prod, CI tests, rollback | 🟡 tests run on every deploy; single environment | P2 |
| H7 | Accessibility audit, dark mode | ❌ | P2 |
| H8 | Scale: React on Snowpark Container Services with its own API | ❌ | P2 |
| H9 | Per-client config without code (schemas, featured data) | 🟡 env vars / config.py | P2 |

## L. Persona layouts (added 1 Oct — Executive, Manager and Operations dashboards look alike)
Root cause (code): Executive and Manager both run at **month** grain; every persona gets the same focus metrics, the same 14 tile types and the same prompt rules ("open with KPI grid, 2–3 pages, 3–5 tiles, widths add to 12"); the persona is one sentence in the prompt; the reviewed persona templates in `layout_catalog.py` need queue/SLA/backlog roles retail does not have, so Cortex designs freely every time; the Validator falls back to the same region/segment dimensions. The "Operations" label on Home is actually the weekly business review persona, not daily operations.
Direction: a fixed skeleton per persona (reviewed, versioned); Cortex fills the slots (metrics, dimensions, titles, narrative); the Validator certifies the result. Wireframes: `persona_wireframes.png`.
| # | Item | Status | Pri |
|---|---|---|---|
| L1 | Grain per persona: Exec month + YTD, Manager week vs plan, Ops today / hourly | ✅ 1 Oct (`AUDIENCE_GRAIN`: managers → week) | **P0** |
| L2 | Persona skeletons replace free composition (Exec one page with no tabs; Manager scorecard + drill; Ops live control room) | ✅ 1 Oct (`persona_layouts.py`: reviewed skeleton, Cortex fills slots from valid options only, validator certifies) | **P0** |
| L3 | New tiles: KPI vs plan (bullet), scorecard matrix (RAG), today's pace (cumulative by hour vs last week), worklist (row actions) | ✅ 1 Oct (`persona_tiles.py`: kpi_plan, ytd_trajectory + ML forecast, scorecard, status_tiles, pace_chart, hour_heatmap, worklist) | **P0** |
| L4 | Persona chrome: Exec "data as of" strip with no tabs; Ops live strip + 5-minute auto-refresh; Manager filter bar + drill-through | ✅ 1 Oct (Exec summary writes itself; scorecard row click = drill filter) | P1 |
| L5 | Weekly business review: 6-week + 12-month paired charts per metric | ❌ | P2 |

## Built 1 Oct (UX, for reference)
Prompt-first Home with saved Cortex ideas (`AA_IDEAS`, "New ideas") · Review step (metric chips, picker, layout wireframe) ·
KPI cards with one delta + compare-to · tooltips on all charts · per-tile ✦ AI panel · page tabs with add/rename/move ·
global filters · Publish option A (`AA_PUBLISHED`, viewer mode) · Snowflake light theme (Inter, validated palette) ·
performance (one script run per click, lazy page queries) · exception fixes (lower-is-better colours, "Watch" state) ·
shared agent auto-created per semantic view.

## P0 before Thursday — in order
1. ✅ Capability map (`CAPABILITY_MAP.md`)
2. ✅ Demo script (`DEMO_SCRIPT.md`)
3. ✅ Cortex Search live (1 Oct) · 🔧 two-tool agent deployed — verify in app (agent upgrade notice, citations)
4. ❌ A6 — add the retail agent to Snowflake Intelligence (after step 3, so it has both tools)
5. ❌ Live end-to-end re-test on retail (agent answer + follow-up + citations)

## Change log
- 2 Oct (demo prep): demo moved to Tuesday 6 Oct, audience Snowflake partners. The partner deck (PowerPoint, built on the Blend360 template, 11 slides with speaker notes) and the partner demo script are kept OUTSIDE this project, in Downloads\Analytics Accelerator Partner Demo. DEMO_SCRIPT.md here is the original 8 Oct script. demo/ holds an older HTML version of the deck and partner script; it is no longer needed and can be deleted. The partner script follows the slimmer Home / dashboard header, which is built locally but not yet copied into this folder.
- 2 Oct (cost evidence): new setup\cost_snapshot.sql + cost_snapshot.py + run_cost_snapshot.cmd pull tokens and credits per app feature for the last 30 days (CORTEX_AI_FUNCTIONS_USAGE_HISTORY, CORTEX_AGENT_USAGE_HISTORY, QUERY_ATTRIBUTION_HISTORY, CORTEX_SEARCH_DAILY_USAGE_HISTORY, AA_AI_RUNS); output setup\cost_snapshot_log.txt. Not yet run live. The partner deck (v2, 15 slides) shows ESTIMATES from the app's prompt sizes at list rates (about $0.02 per dashboard design, $0.10-0.20 per agent question, 0 tokens to view); replace with actuals once the snapshot has run. Slim UI parked until after the demo (user decision).
- 2 Oct (measured tokens, no ACCOUNT_USAGE needed): WBR_OWNER cannot read SNOWFLAKE.ACCOUNT_USAGE and no ACCOUNTADMIN is available. The app now records the tokens Snowflake reports per call: AI_COMPLETE is called with show_details => TRUE (usage.prompt_tokens / completion_tokens; falls back to the plain call for the rest of the process if rejected) and the agent's response metadata.usage.tokens_consumed is summed. Tokens are appended to PROVENANCE in AA_AI_RUNS (' · tokens N in / M out [/ C cache_read]') and shown in AI provenance labels. AI_AGG reports no usage (not measured). cost_snapshot.sql queries 7-9 need no ACCOUNT_USAGE: 7 = agent tokens from AI Observability, 8 = AI_COUNT_TOKENS on logged outputs, 9 = measured tokens per feature priced at list rates. New test_token_usage.py (123 tests). Deployed and verified live 2 Oct.
- 2 Oct (measured cost, live): agent question about 200,000 input tokens (78% cache read, about 43,000 cache write) and 2,300 output, about 0.16 AI credits = $0.30 at list (AI Observability, 3 questions; app ledger agrees). Audience layout fill 2,297 in / 207 out = $0.01; new page 5,028 in / 594 out = $0.03. Deck slides 10-11 updated to measured numbers (100 users about $940/month AI, agent about 95%). Follow-up: agent_service now also records cache_write and query 9 prices it at 2.44 (LOCAL until next deploy). Latency: agent about 33 s, tile question 64 s.
- 1 Oct (Review, live feedback): Redesign ignored metrics added in review and reset to the recommended ones. Now Redesign makes the user's selection the dashboard's focus (metrics they added lead, then the rest of their selection) for every metric slot (executive headline up to 5 cards, manager scorecard columns, ops status tiles and worklist), and the new draft keeps the user's selection instead of resetting. Note: the page structure per audience is the reviewed skeleton by design; Redesign changes what fills it. 120 tests; checked locally (added Quantity -> Redesign -> headline, trajectory and driver bridge lead with Quantity; all 5 selected metrics kept).
- 1 Oct (Home, live feedback): (1) the box's grey placeholder rotated through the same requests listed under "Try asking", so a request looked doubled; the placeholder is generic again, and the second request per audience is worded differently ("How is ... tracking on ...", "Which regions ... are behind plan this week ...", "Show me what needs action this hour ..."). (2) Clicking an idea card built the dashboard straight away; now an idea card or a "Try asking" request only fills the box ("Editing: ..." line with Clear), sets the audience and keeps the idea's dataset; nothing builds until Send. If the text is edited, the metrics named in the text lead; unedited, the idea's metrics lead. 120 tests; checked locally (idea click no longer builds; edit + send builds).
- 1 Oct (deck): "Analytics Accelerator – AI at every stage" slides (Claude artifact, 6 slides): stage x Snowflake AI map (Connect, Discover, Design, Build, Explain, Decide, Govern), stage cards with guardrail and live/verifying status, the Cortex Agent and its three tools, live / verifying / next. Keep its status labels in step with this tracker.
- 1 Oct (KPI display, live feedback): "Show as" was only inside the tile menu and not found. The KPI-vs-plan tile header now has a visible Bars | Arrows | Table switch (builder only; viewers see the chosen look). Same backend as the menu option. Checked locally with a screenshot.
- 1 Oct (KPI display): the "Year to date vs plan" tile can be shown three ways, chosen in the tile menu (Show as) or by asking the tile ("show these as a table", "use arrows instead of bars"): bullet bars (default), variance cards with arrows (variance %, absolute variance, target), or a variance table (YTD, target, variance with arrow, variance %, latest month). Purely visual: no re-query; the choice is kept on the tile through edits, saves and publish. Arrows (up/down, coloured for lower-is-better) also added to KPI cards and operations status tiles. 120 tests; checked locally with screenshots, not yet live.
- 1 Oct (fix, live report): Executive "Year to date vs plan" showed Net Sales Vs Plan as a KPI; its value is negative, so the bullet bar ran out of the card across the next one, and "-129.9% vs last year" compared a variance with last year. Fixes: variance and plan metrics (NET_SALES_VS_PLAN, PLAN_*, *_VARIANCE, *_GAP, *_DELTA) are never headline KPIs, scorecard columns, status tiles or idea metrics (the tiles compute the variance themselves; existing dashboards drop them at render time); the bullet bar handles negative values (zero line, bar grows from zero) and is clamped to its track, and KPI cards clip their content. 118 tests; bar checked in a browser locally, not yet live.
- 1 Oct (ideas): "New ideas" rotates themes. The themes on screen per dataset x audience are passed to Cortex as "already shown"; Cortex is told exactly which next themes to use, the validator drops any idea on an on-screen theme, and catalog top-ups take the next unseen themes (wrapping round only when a dataset has run out). Within an audience every card has a different theme (per featured dataset; other datasets share one theme pool). 117 tests; verified locally only. Deploy command (always the full one): cd /d "C:\Users\SharathKumarKammari\Downloads\snowflake-react-app-runtime\Analytics_Accelerator_Enterprise_Claude" && deploy_enterprise.cmd
- 1 Oct (ideas, live feedback): Home showed 42 ideas with near-duplicates (three "sales pace" cards for Operations from earlier sets). Now one idea per audience x metric theme per dataset (the newest wins; an earlier card without a theme gets one from its metrics, plan metrics only count when nothing else is named), at most 3 per audience on a featured dataset and 2 per audience in total across all other datasets (one per dataset). Catalog ideas for non-featured data: 1 per audience. With Harborline + Infera featured that is 18 featured cards (6 per audience tab) plus up to 6 others. Operations "Try asking" worklist now names subcategory, distribution center and carrier (one breakdown per kind, no category + subcategory pair, no hour/date columns). AA_IDEAS rows are untouched. 115 tests; verified locally only.
- 1 Oct (prompt bar): under the prompt bar Home now shows "Your data" (one line per featured dataset: metric count, themes, whether plan exists, main breakdowns, live or not; plus "Also available: ...") and "Try asking" (ready-to-edit requests per audience written from the real metrics and dimensions, e.g. Manager: "Weekly scorecard by region for Harborline Retail: in stock rate, on time delivery % and return rate vs plan. Flag the regions in red and let me drill into what is driving them."). On Auto one request per audience; pick Executive / Manager / Operations to see two for that audience. Clicking puts the text in the box and sets the audience; nothing is sent until the user presses send. The rotating placeholder uses the same requests. A typed request that names 2+ metrics now makes them lead the dashboard (same as opening an idea); Cortex routing also maps a bare view name to its featured table. 114 tests; verified locally only.
- 1 Oct (ideas): Home ideas are now audience x metric theme, not the same 1-2 headline metrics on every card. Each metric is tagged with a theme (sales & growth, margin, channel mix, customers & basket, orders & units, inventory & availability, delivery & fulfilment, returns & discounts, patients for healthcare; plan metrics excluded). Each audience gets 3 ideas per featured dataset on 3 different themes picked for what it owns: executives = outcomes (sales, margin, channel), managers = levers by area (in-stock, on-time, returns), operations = what breaks today (stockouts, late shipments, order pace). Cortex sees ALL metrics grouped by theme (was the first 14 alphabetically, mostly inventory); the validator drops a second idea on the same theme or metric set for the same audience and tops up thin ideas from the same theme; earlier sets that repeat the same metrics collapse to one card. Cards show the theme. Opening an idea now carries ALL its metrics into the persona layout (exec headline KPIs, manager scorecard columns, ops status tiles and worklist), not just the first. 110 tests; verified locally only.
- 1 Oct (fix, live report): after the Infera deploy, old Home ideas were gone and Infera still missing. Causes: "New ideas" overwrote the shown set, and saved ideas were dropped whenever the catalog signature changed (it did with this deploy). AA_IDEAS is append-only, so nothing was deleted. Now Home merges the last 6 saved sets (newest first, earlier ones tagged "Earlier", duplicates and ideas on vanished views dropped); "New ideas" adds on top; no signature gate. Infera: featured matching is case/prefix tolerant (`#VW_RETAIL_MASTER` = `#retail_master`), Cortex ideas naming the bare view map to its featured table, and a featured view missing from Home is always listed under "found but not used" with the reason (schema not listable by WBR_OWNER, view not visible, or table name mismatch). 105 tests; verified locally only (fake Snowflake + screenshot).
- 1 Oct (fix): Infera missing from Home ideas. 'New ideas' now re-scans the semantic views (catalog was cached 30 min per role); every featured view gets an idea in every audience group (Cortex kept choosing Harborline only); TIME_DIMENSION rows from DESCRIBE are parsed as dates; featured tab says 'Featured data' when there are several. 97 tests.
- 1 Oct (B1+): metrics drafted from facts. When a semantic view has facts but no metrics, Snowflake profiles every fact through the view (count, distinct, min/max/avg, 0/1 and 0-1 detection), Cortex AI_COMPLETE drafts business metrics (SUM / AVG / COUNT DISTINCT per fact + ratios, definitions, why) and the validator checks them (real fact, allowed aggregation, no SUM of ids/text, ratios between drafted metrics). Draft stored once per view in AA_METRIC_DRAFTS and shared. Shown on the Review and fields pages with a banner, 'drafted' badges, the reason per metric, Re-draft with Cortex, and the METRICS clause the owner can paste to make them governed. Rules are the fallback. 96 tests; live run on INFERA pending.
- 1 Oct (data): facts-only semantic views supported. A view with facts but no metrics (SANDBOX.BI.INFERA_SEMANTIC_VIEW) is queried through Snowflake's standard-SQL semantic view interface with ad-hoc metrics (SUM of amounts, AVG of rates/prices, COUNT DISTINCT of ids); each unrelated logical table is its own dataset on Home (Infera Retail, Infera Healthcare). Infera Retail is featured next to Harborline Retail. No change to the semantic view. 94 tests; live SQL not yet verified.
- 1 Oct (data): SANDBOX.BI.INFERA_SEMANTIC_VIEW (healthcare + retail master views) is discovered but not on Home: it has facts but 0 metrics (and may not be granted to WBR_OWNER). Home now lists skipped views with the reason. Read-only check: `setup\infera\run_infera_check.cmd`; next step = add metrics (in place by DS_BASIC, or an app-owned copy) so it joins the ideas.
- 1 Oct (L1–L4): persona layouts. Executive = one-page brief (YTD vs plan bullets, cumulative trajectory + Snowflake ML forecast to year end, driver bridge, decisions; summary auto-written). Manager = weekly scorecard by region (red/amber/green vs plan or prior week, click a row to drill) + exceptions + trends, Drivers and Detail pages. Operations = live control room (status now vs same time last week, today's pace by hour, hour × day heatmap, worklist with Ask agent / Log decision, 5-minute auto-refresh). Home's Operations ideas now open the live operations persona (weekly review stays reachable). Hardening: hour filter only for metrics related to the hour dimension; one bad metric × breakdown pair no longer breaks a tile. 89 tests.
- 1 Oct (research): persona layouts look alike. Diagnosed the root causes and added roadmap section L with the per-persona skeleton design (wireframes in `persona_wireframes.png`).
- 1 Oct (fix): chart audit after the heatmap fix — line and waterfall axes now zoom to the data when a rate sits in a narrow band (e.g. in-stock 94–96%; was flat on a 0 baseline), marked with an axis-break symbol; removed the hidden 'max ≥ 1' floor on waterfall/pareto that squashed ratio metrics; donut folds the tail into one grey 'Other (n)' slice (max 6, tooltip lists members) instead of several identical grey slices; scatter labels placed without overlapping (right/left/above/below, white halo). Ranked/grouped bars, KPI sparklines and mini lines already OK. 80 tests.
- 1 Oct (fix): heatmap shading — 7-step sequential blue ramp (contrast-checked), equal-count shades for ordinary cells, outliers (> Q3+3·IQR) darkest with an orange outline, legend with value cut-offs; fixed scale bug that pinned max at 100%.
- 1 Oct (fix): tile menus only offer valid combinations (metric × dimension from the semantic view, chart value-count limits, additive metrics for donut/pareto); scatter y-axis and heatmap columns editable; KPI trend toggle; validator repairs now announced instead of silent.
- 1 Oct (fix): tile assistant — Enter sends; KPI trend lines can be hidden/shown ("remove the trend…"); unsupported change requests now say so instead of silently doing nothing.
- 1 Oct (fix): agent errors now shown inside the agent panel; agent no longer rebuilt per question; Sources chips show document IDs/titles (search tool id/title columns, spec aa-spec-4).
- 1 Oct (B1): semantic view builder (profile → Cortex draft → validate → review → create); fixed `06_agent_tools.sql` (COMMENT before EXECUTE AS); 78 tests.
- 1 Oct (D1): native Cortex Agent evaluations (AI Observability) + promotion gate in Governance; 68 tests.
- 1 Oct: D3 row-level security paused by decision; D1 and B1 started.
- 1 Oct (D4): QUERY_TAG on all app queries + cost by feature in Governance; 65 tests.
- 1 Oct (C4): page summaries on Cortex AI_AGG over governed fact rows, AI_COMPLETE fallback; 64 tests.
- 1 Oct (C3): exceptions on SNOWFLAKE.ML.ANOMALY_DETECTION (multi-series, 95% interval), z-score fallback; 62 tests.
- 1 Oct (A2): custom agent tool `log_decision` → `AA_CREATE_DECISION`; spec aa-spec-3 (analyst + search + action); 58 tests.
- 1 Oct (later): docs search run on account — AI_PARSE_DOCUMENT + SPLIT_TEXT_RECURSIVE_CHARACTER worked, no fallback; 41 glossary rows; search service created; app deployed.
- 1 Oct: tracker created; A1/C5 built (docs PDFs, search script, agent spec v2 with citations, 54 tests); capability map and demo script written.

## 2026-10-07 Dashboard Portal (viewer-only app) + merge of Nikunj's deployed changes
- Merged the deployed app (edited by Nikunj in Snowflake) into the local code: new Home UI (app_styles.css, app_bundle.js), KPI-plan trend lines (composer.py, persona_tiles.py, app.py). Originals saved in merge_backup_20261007/. Local keeps the cache_write token change.
- Frontend source (app/frontend/src) is OLDER than the deployed bundle. The bundle in app/streamlit is the source of truth until Nikunj shares his src. Do NOT run "deploy_enterprise.cmd build".
- New second app ANALYTICS_ACCELERATOR_PORTAL (portal.py runs app.py in portal mode, portal_view.py = catalog). Deploy: deploy_portal.cmd. Builder app is untouched.
- Portal: catalog of published dashboards grouped by audience, search, opens read-only viewer, Close/navigation returns to the catalog; all build/publish/suggestion actions blocked. Deep link to a dashboard the viewer is not shared on shows the catalog with a notice.
- Access today = SHARED_USERS soft filter. Role-based per-dashboard access, portal link in the publish dialog, and a second-role test are still to do.
- Portal tiles: each card has a layout thumbnail per audience; names aligned. Builder app now has a left bar with "Published dashboards" opening the portal (config.PORTAL_URL). Optional config.PORTAL_APP_URL (portal direct address) makes publish share links open the portal.
- Portal link moved into the builder's own left menu ("For your viewers" > Published dashboards, bundle patched + payload portal_url); the native Streamlit sidebar was removed. Give the same change to Nikunj for his frontend src (App.jsx rail, after the Advanced setup details).
- Portal speed: lean start-up (no table DDL, no draft list, one schema), shared 10-minute cache across viewers for model, profile, filter counts, agents and feature check. Opening a dashboard: 48 queries before, 34 for the first viewer, 17 after (no AI call). Builder unchanged.
- Sharing: publish dialog role box now grants the Dashboard Portal (PORTAL_FQN), not the builder; dialog wording updated. Portal tiles have a Share panel: direct link (?view=id on the portal's own address), Snowsight portal link, who it is shared with. Direct link not yet verified on the account.
- Portal Share panel: the publisher of a dashboard can pick roles (grants the portal) and limit to named users, saved on the published row without a new version (Store.update_sharing). Others see Shared with read-only. Viewer matched by user name, email or first name. Limit: a role cannot yet be restricted to only its own dashboards (owner's rights hide the viewer's roles); named-user limits do hide dashboards.
- Tile assistant: 'change/rename the title to X' works instantly in any mode (no AI); change requests typed in Ask mode are treated as changes; titles follow metric or breakdown changes unless renamed by hand (title_locked); published dashboards refuse edits in the tile assistant.
- Tile assistant panel: was position:fixed and centred, which landed off-screen inside Nikunj's animated (transformed) containers, and the chat auto-scroll pushed replies out of view. Now in page flow at the top of the dashboard, scrolls into view on open, chat scrolls to the newest question (bundle + CSS).
- Root cause of 'send does nothing': Snowsight's sandboxed frame blocks HTML form submission, so type=submit buttons never fire (Enter worked because it calls the handler directly). Tile assistant send arrow and the agent drawer Ask button + Enter now call the handlers directly. Verified in a sandboxed iframe: old bundle fails, new works. Rule for Nikunj: never rely on form submit in this UI.
- Portal renamed to 'Analytics Accelerator Portal' (Snowsight title, browser tab, header, all messages). Snowflake object name unchanged: ANALYTICS_ACCELERATOR_PORTAL.
- Portal: query and Snowflake ML results shared across viewers for 15 minutes (qcache, keys include view, period and filters). Page 2 for a later viewer: 11 queries + 3 ML trainings -> 2 small queries, 0 ML. First viewer of a page still pays once; Refresh clears.
- Portal: full-screen 'Opening dashboard' state (name + animated bar) drawn first when a dashboard is opened, removed once it renders (PORTAL_LOADER in app.py, loader_html in portal_view.py).
- 2026-10-10 Install package for other Snowflake accounts: Downloads\Analytics_Accelerator_Install (+ .zip). settings.ini drives everything (render.py -> build\); install.cmd = prereq check, schema/tables/decision tool (+ optional Harborline demo), deploy builder + portal. app.py: publishing/sharing to a role now also grants USAGE on the app database and schema (needed in a fresh account).

## 2026-10-10 Post-demo enterprise plan (agreed order)
1. Cost guardrails without the gateway — DONE in code (below). 2. Cortex AI Guardrails for the agent — admin SQL written, needs ACCOUNTADMIN. 3. Half-day test: can SiS call the Cortex AI Gateway (public preview 8 Oct; account AWS_US_EAST_1 eligible). 4. Cortex Sense (private preview) via the account team; add the agent to CoWork (A6). Then: per-dashboard roles + row-level security (D3), H6 dev/test/prod, H5 monitoring, H10 ML cleanup, H3 approval, H1 alerts, H2 export.
- Cost guardrails: AA_AI_RUNS.CREATED_BY now records the signed-in person (st.user user name/email), not the SiS service user (Store.actor, COALESCE fallback to CURRENT_USER()). Per-person daily limits checked before AI actions: config.AI_DAILY_LIMIT (200, env AA_AI_DAILY_LIMIT) and AGENT_DAILY_LIMIT (40). 0 = off. Viewing (load_page, narrative/AI_AGG summaries, enrich) and title renames are never limited; if the count query fails or the person is unknown, the action runs. Friendly message when over. Tests: tests/test_ai_limits.py (125 tests OK).
- setup/admin_ai_guardrails.sql (for an admin): monthly AI budget AA_AI_BUDGET on AI FUNCTION + CORTEX AGENT scoped by user tag AA_COST_CENTER (tag the app's service user + builders), threshold + email alerts; Cortex AI Guardrails (ALTER ACCOUNT SET AI_SETTINGS prompt injection). Lines marked VERIFY not yet run. Budget warns only, it does not stop spend.
- Install package synced: settings.ini [limits] ai_daily_limit / agent_daily_limit, render.py validates them, templates\sql\admin_ai_guardrails.sql, README. Zip rebuilt.
- AI Gateway test (plan item 2) built, not yet run: test-only app AA_GATEWAY_PROBE (gateway_probe\, deploy_gateway_probe.cmd) runs G1-G8: runtime/token, SQL baseline, SHOW/DESCRIBE AI GATEWAY, Cortex REST control, gateway Messages API with the container session token (the real test, no integration needed if it passes), Chat Completions, PAT fallback, traces. Read-only checks: setup\gateway_probe_checks.sql; fallback (admin + PAT, only if G5 fails): setup\gateway_probe_fallback.sql. Steps and decision rules: Test & Demo Playbook, Scenario 14. Scenario 13 = per-person AI limit tests.
