# Enterprise tracker — Analytics Accelerator (Snowflake partner demo Tue 6 Oct 2026)

**Read this first in every session.** Source: the 30 Sep brain-dump ("every step carried by a named
Snowflake AI feature") + what was built through 1 Oct. Update the Status column when anything changes.

Status: ✅ Done · 🔧 Built, needs your live run · ⏸ Paused / decision open · 🟡 Partial · ❌ Not started · ⏸ Decision open · ⛔ Obsolete
Priority: **P0** = before the demo · **P1** = demo if time · **P2** = after the demo (roadmap slide)

## R. Roadmap — agreed order (10 Oct 2026, after the demo; reordered same day: custom metrics and layouts first). Work goes in this order; update Status here.
No admin access today, so steps needing ACCOUNTADMIN are prepared as scripts and parked under "Needs an admin".
| Step | Item | Ref | Status |
|---|---|---|---|
| 0 | Cost guardrails: per-person AI limits, real names in the AI log, budget + guardrails scripts | D5, D2 | 🔧 built + deployed 10 Oct; test = playbook Scenario 13 |
| 0 | AI Gateway probe | D6 | 🔧 built + deployed 10 Oct; run = playbook Scenario 14 |
| 1 | Custom metrics | B5 | 🔧 built 10 Oct, test = Scenario 15 |
| 2 | Layout variety + UI polish pass | L6, L7 | 🔧 L6 built 10 Oct (Scenario 16) + fixes after live review (question tag only when asked, KPI sketch per metric); L7 waits on screenshots |
| 3 | Semantic layer both paths: leverage existing views, create multi-table views when missing | B6 | 🔧 built 10 Oct, test = Scenario 17; table picker restructured 11 Oct (find tables by question, joins, filters, in-view tags, tray), test = Scenario 18 |
| V1–V2 | Automatic QA validation: checks QA-01–08, background run, Validation tab, diagnosis, resolutions | — | 🔧 built 13–15 Oct; test = Scenario 19 |
| V3 | UAT drop 2: requirement trace, UAT Excel workbook, sign-off per page, test a view fix on a copy | — | ❌ **next** (Sharath 16 Oct: validation first, it completes the flow; then the visuals program) |
| VX | **Visuals program (agreed 16 Oct), full plan in `VISUALS_PLAN.md`** | — | — |
| VX-done | Insight headlines · Classic default + Company themes (brand colours / token file / logo, WCAG checks) · chart drop A (bars + line, treemap, gauge, P&L table) · Settings group | — | 🔧 built 15–16 Oct, pending deploy check |
| VX0 | Probe: Claude models + output limit in `AI_COMPLETE`, time/credits per page design, sandbox frame in Snowsight, Cortex image input | — | ❌ after V3 |
| VX1 | Design system v3: page compositions, annotation layer, emphasis rules, chart drop B, hover readout / motion / click-to-filter | — | ❌ mockup first, then build |
| VX2 | Cortex art director (JSON design spec) + Design QA score + critique loop | — | ❌ after VX0 |
| VX3 | Generated components: sandbox, code checks, QA-09 rendered numbers, approval, AA_DESIGNS library, Standard / Designed by Cortex | — | ❌ after VX0 + VX2 |
| VX4 | PDF / PowerPoint board pack, table alternative per chart, colour-blind palettes, laptop / projector / phone layouts | H2 | ❌ |
| 4 | Access control, admin-free (groups table, dashboard access, row rules, agent off when row-limited, cache per rule) | D3 | ❌ after L6/L7 (Sharath, 10 Oct) |
| 5 | Dev / test / prod schemas, deploy per environment, smoke check, rollback | H6 | ❌ |
| 6 | Audit trail + Governance view | H12 | ❌ |
| 7 | Monitoring health page + ML model clean-up | H5, H10 | ❌ |
| 8 | Security review of AI-generated SQL and prompts | H13 | ❌ |
| 9 | Publish approval (draft → review → publish, audited) | H3 | ❌ |
| 10 | Alerts / subscriptions (export to PDF / PowerPoint moved to VX4) | H1, H2 | ❌ |
| 11 | Load test + compute pool sizing | H14 | ❌ |
| 12 | Move AI calls to the AI Gateway (only if probe G5 passes) | D6 | ⏸ waits on Scenario 14 |
| 13 | No-code: agent in Snowflake Intelligence / CoWork; ask account team for Cortex Sense | A6, B3 | ❌ |
| 14 | Source control (Sharath 10 Oct: current code already = Nikunj's + Sharath's changes; git + rebuilt React source still open) | H11 | ❌ later |
| Later | Caller's rights + native row policies · Native App / Marketplace · MCP server · SPCS scale-out · weekly business review layout · AI_CLASSIFY / search bar · multi-country data | D7, E1, E2, A4, H7, H8, L5, C6, C7 | — |

**Needs an admin (park until one is available):** `setup/admin_ai_guardrails.sql` (budget, prompt-injection guardrails) · MONITOR on the AI gateway (traces) · gateway fallback integration (only if needed) · D7 caller's rights · IMPORTED PRIVILEGES on SNOWFLAKE for role sync and full cost panel.
**Pending tests (you):** playbook Scenarios 13 and 14 · install package in a fresh account · direct dashboard link.

## A. Multi-agent layer (the headline)
| # | Item | Status | Where it stands | Pri |
|---|---|---|---|---|
| A1 | One Cortex Agent per domain, tools = Cortex Analyst + Cortex Search | 🔧 | Agent spec v2: `analyst` + `documents` (Cortex Search) tools, cites doc IDs; app auto-upgrades the shared agent on first question. **Run `setup\retail\run_docs_search.cmd`, then deploy** | P0 |
| A2 | Action tools (stored procs): `create_decision`, `run_forecast`, `build_dashboard`, `approve_metric` | 🔧 | `AA_CREATE_DECISION` procedure (validated, p_-params) + agent tool `log_decision` (spec aa-spec-3); app shows "Logged in Snowflake by the agent" card and refreshes Decisions. **Run `setup\run_agent_tools.cmd`, then deploy.** `run_forecast` / `build_dashboard` / `approve_metric` still open (P2) | P1 |
| A3 | Coordinating layer routes each question to the right domain agent | 🟡 | Home prompt is routed to the right semantic view by Cortex (`home.route`); agent chat uses the current dashboard's agent only | P2 |
| A4 | MCP server so app capabilities work in Snowflake Intelligence / CoWork | ❌ | — | P2 |
| A5 | Decide: own router vs agent-to-agent (Native Apps) | ⏸ | — | P2 |
| A6 | Same agent answering in Snowflake Intelligence / CoWork | ❌ No code: add the retail agent in the SI / CoWork UI; write steps into the playbook | Roadmap step 11 |

## B. Semantic foundation that generates itself
| # | Item | Status | Where it stands | Pri |
|---|---|---|---|---|
| B1 | Auto-draft semantic view on source registration (profile → AI_COMPLETE drafts dims/metrics/synonyms/verified queries → approve → CREATE) | 🔧 | Home → "＋ Connect a Snowflake table": pick a table → profile (INFORMATION_SCHEMA + distinct/null/sample stats) → `AI_COMPLETE` draft → validator (real columns only, aggregation vs type, names, ratios) → editable review with SQL preview → `CREATE VIEW` (C_-prefixed source) + `CREATE SEMANTIC VIEW` in the app schema → test query → available on Home, routing and the agent. Verified queries are proposed but not yet written into the view | P1 |
| B2 | Reuse Tableau accelerator `cortex_semantic.py` | 🟡 | Reused its patterns (INFORMATION_SCHEMA introspection, identifier quoting); its generator is Tableau-IR driven, so raw tables use the new `semantic_builder.py` | P2 |
| B3 | Cortex Sense (runtime context over Horizon Context for CoWork / Cortex Code) | ⏸ Exists: private preview since 2 Jun 2026, no public API. Ask the account team (via Devang) for access | Roadmap step 11 | P2 |
| B4 | Decide: semantic view = single source of truth for metrics | ✅ | App reads metrics, definitions, formulas and valid metric×dimension pairs from the SV; no separate registry | — |
| B5 | User-defined (custom) metrics | 🔧 Built 10 Oct: Review → metric picker → "+ Define a metric" (English or formula) → Cortex AI_COMPLETE drafts a formula over the view's metrics → strict parser (metrics, numbers, + − × ÷ only; SQL generated from the parse tree, division = DIV0) → test-run value shown → Save stores it in AA_CUSTOM_METRICS (shared per view, tagged custom, "not governed" in its definition) → usable in every tile, portal included; "Make it governed" gives the owner the METRICS line. Base metrics come from SEMANTIC_VIEW(), formula computed on top. 15 new tests (140 total). Test: playbook Scenario 15. Limits: no filters/new columns, define only on Review, agent unaware, no edit/delete in app | ✅ built |
| B6 | Semantic layer, both paths: LEVERAGE existing semantic views (built by the client's data team, e.g. Snowflake Semantic View Autopilot, discovered automatically) and CREATE when missing: multi-table "Connect tables" — app profiles tables, detects joins (declared keys, name match, distinct counts, query history if readable), Cortex drafts dims/metrics/synonyms, automated checks (join key unique on one side = no double counting, totals reconcile to base tables, test queries), ONE approval click by an accountable owner (routes via H3 later), then CREATE SEMANTIC VIEW in a governed schema. Later: create from Tableau / Power BI files with our accelerators' parsers. Autopilot itself is UI-only (no API), so it is not our automated path | 🔧 Built 10 Oct: semantic_multi.py — tick 2-8 tables in Connect a table; keys exact-checked, joins by name match to a unique key (coverage %), Cortex drafts per table (can drop a join, never add), validator, one Approve click, source views + CREATE SEMANTIC VIEW (PRIMARY KEY + RELATIONSHIPS), join test query, SUM totals reconciled. 7 tests. Scenario 17. Limits: single-column keys, name-based join detection, ratios within a table | **P1 — roadmap step 3** |

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
| D2 | Guardrails — Cortex AI Guardrails (prompt injection), Cortex Guard, AI Gateway | 🔧 10 Oct: `setup/admin_ai_guardrails.sql` Part 2 (account-wide prompt-injection screening, needs ACCOUNTADMIN). Cortex Guard per call: not used (untested, extra cost). Gateway: see D6 | P1 |
| D3 | Access control: (a) who can open each published dashboard, (b) which rows each person sees | ❌ **Next build** (10 Oct decision, no admin): app-managed groups table (people → groups), dashboards shared to groups/people, row rules per group/person applied by the app to every query (tiles, filters, ML, summaries); agent off for row-limited people; portal cache split per rule. Admin-free; D7 is the end state | **P1 — roadmap step 1** |
| D4 | Cost panel — tokens/credits per agent and feature | 🔧 | Every app query carries a JSON `QUERY_TAG` (app, feature, semantic view, dashboard); Governance → "Cost by app feature": queries + elapsed (QUERY_HISTORY), Cortex credits/tokens (CORTEX_FUNCTIONS_QUERY_USAGE_HISTORY), warehouse credits (QUERY_ATTRIBUTION_HISTORY), each optional. Per-agent split still open (agent runs are tagged as feature `ask` / `tile_ask`) | P1 |
| D5 | Per-person AI limits + AI budget (was H4) | 🔧 10 Oct: AA_AI_RUNS logs the real person; 200 AI requests / 40 agent questions per person per day (config); budget + alerts in `setup/admin_ai_guardrails.sql` Part 1 (admin). Test: playbook Scenario 13 | ✅ built |
| D6 | Route the app's AI calls through the Cortex AI Gateway | 🔧 Probe built 10 Oct (`AA_GATEWAY_PROBE`, playbook Scenario 14), not yet run. If G5 passes: plan the switch (gateway behind a config flag, SQL as fallback) | Roadmap step 10 |
| D7 | Caller's rights for viewers + Snowflake row access / masking policies (native, replaces D3 app filters) | ❌ Needs an admin and a check that container-runtime Streamlit supports it | Later |

## E. Distribution
| # | Item | Status | Where it stands | Pri |
|---|---|---|---|---|
| E1 | Native App with Cortex Agents + MCP (GA 7 Aug 2026) | ⏸ | React↔Python link inside Native App Streamlit still unsolved | P2 |
| E2 | Marketplace / private listing | ❌ | — | P2 |
| E3 | Install package for other Snowflake accounts (`Downloads\Analytics_Accelerator_Install` + zip) | 🔧 10 Oct, not yet run in a fresh account | — |
| E4 | Analytics Accelerator Portal (viewer-only app, sharing to roles/people, shared cache) | ✅ 7–8 Oct | — |

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
| H4 | Cost guardrails (per-user Cortex quota, heavy-query warning) | 🔧 Moved to D5 (built 10 Oct). Heavy-query warning still open | — |
| H10 | Clean-up of ML model objects (`AA_FC_*`, `AA_AD_*`) created per period/filter | ❌ | P2 |
| H5 | Monitoring (error rate, slow tiles, failed AI calls) | 🟡 logged in ledger, no health view | P2 |
| H6 | Release process: dev/test/prod, CI tests, rollback | 🟡 tests run on every deploy; single environment | P2 |
| H7 | Accessibility audit, dark mode | ❌ | P2 |
| H8 | Scale: React on Snowpark Container Services with its own API | ❌ | P2 |
| H9 | Per-client config without code (schemas, featured data, limits) | ✅ 10 Oct: install package `settings.ini` → render.py generates config + SQL | — |
| H11 | One source of truth for the code: git repo; React source rebuilt from the deployed `app_bundle.js`; agreed path for Nikunj's Snowsight edits back into the repo | ❌ Biggest risk today (code in Downloads folders, Snowsight copy, stale `app/frontend/src`) | **P1 — roadmap step 2** |
| H12 | Audit trail: who opened which dashboard, who published / shared / changed what (one events table + Governance view) | ❌ | **P1 — roadmap step 4** |
| H13 | Security review: AI-written queries use only known fields, identifiers quoted, only intended data in prompts, injection tests | ❌ | **P1 — roadmap step 6** |
| H14 | Load test (20–50 concurrent viewers) and compute pool sizing | ❌ | P2 — roadmap step 9 |

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
| L6 | Layout variety | 🔧 Built 10 Oct: persona_layouts.VARIANTS — Exec: Year vs plan / Growth & mix / Answer first; Manager: Scorecard / Exceptions first / Compare segments; Ops: Live / Daily tracker. Cortex picks the layout in the same slot-fill call (validated), rules fallback; the person's own words (not the router's rewrite) drive the choice and the 'Your question' first tile. Switch on Review re-uses slots (no AI call). Review: chart sketches instead of icons, full-width pages, layout cards with thumbnails, 'Preview page 1 with data' (real tiles via Engine, ML deferred). 6 new tests (146 total). Test: playbook Scenario 16 | ✅ built |
| L7 | UI and visual polish pass: screenshot critique of each audience's dashboard + Home/Review/portal, then a fix list (hierarchy, density, chart variety, spacing). UI changes go into the React source (needs H11 first) | ❌ 10 Oct feedback | **P1 — proposed** |

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

## 2026-10-11 Connect a table picker for big accounts (Scenario 18)
- table_finder.py + new pick step: (1) 'What do you want to analyze?' - Cortex picks tables with a reason, metadata only (names, comments, columns; no data scanned), only listed tables can come back; (2) 'Joins with your selection' from shared id columns / A.<B>_ID; (3) compact one-line rows, schema filter, sort, search over names/comments/columns, empty and tiny tables hidden behind a toggle (small tables that others join to stay visible); (4) 'In <semantic view>' tag from DESCRIBE SEMANTIC VIEW, leverage before rebuild; (5) sticky tray with chips. semantic_builder.list_tables adds LAST_ALTERED + COMMENT. 4 tests; suite 159 OK. Install zip rebuilt (85 files).
- To verify live (VERIFY): LAST_ALTERED/COMMENT columns, DESCRIBE SEMANTIC VIEW property names, suggest quality on a real account.
- Limits: join hints are name-based; single-column keys.
- 11 Oct, after first live look: suggestion box keeps the question and shows one message plus 'Nearest by name, comment or column' when Cortex finds nothing; short schema (full on hover) and 'N schemas' tag for repeated names; default sort recently changed; app/log/temp-like tables (AA_, AI_BI_STUDIO_, *_CACHE, *_LOG ...) go last and hide behind 'Show N system-like tables' (shown when searched); rows show 'view' / 'n/a' instead of '?'. 161 tests OK.

## 2026-10-11 L7 UI polish after live review of the Executive screens
- Correctness: dashboard/layout names say 'plan' only when a PLAN_ metric exists (else 'vs last year'); tile subtitles are questions, never the person's instruction; a second trend chart is no longer added on top of a layout that has one (the existing one is tagged when it answers the question); margin shows as money; ratio changes show points (+1.6 pt) in cards and in the facts Cortex summarises.
- Look: Home status row centred, friendly source name (no 'Sv'), role pill gone, chart-type tags hidden for viewers, one origin pill instead of banner + pill, '1 page' grammar, equal layout cards (4-line summary), title looks like a heading until hovered, '+ Add tile' is a small right-aligned button.
- Not changed: 'Live - data through' wrapping and donut legend edge (screenshot crop, check live). Manager/Operations screens and the portal still to review. 164 tests OK.

## 2026-10-11 L7 visual restyle + visible progress
- Restyle (font unchanged, Inter): masthead with live eyebrow and large title, icon refresh, Cortex summary as a dark headline band (headline sentence, number highlights, point chips, suggested action; prompt now asks for headline + 2-3 bullets + action), pill filters, rounded cards with soft shadow, KPI cards with uppercase label, big number and delta chips.
- Progress: thin animated bar at the top for every action, clicked button shows a spinner, long actions (build, publish, layout, Cortex, semantic view, agent) show a centred status card with stages and a running timer, 'still working' notes after 25s and 90s. Stages are typical stages shown by elapsed time, not live server steps (that needs background jobs + polling: later).
- Not done: direct end labels on charts, per-chart 'so what' captions, Home layout, count-up motion.

## 2026-10-13 V1 Automatic QA validation (drop 1) - now first priority, ahead of access control
- Every data tile is validated automatically after build, edit, filter change or refresh. Warn only, nothing blocked. New module app/streamlit/validation.py.
- QA-01 Source recompute: each governed query behind a tile is rebuilt as independent SQL straight against the base tables (joins, column expressions, filters from DESCRIBE SEMANTIC VIEW) and compared row by row (relative tolerance 1e-6).
- QA-02 display arithmetic (deltas, shares, totals, Pareto, bridge); QA-03 segments add up to the KPI total (additive metrics; ratios n/a); QA-04 join integrity (unique lookup keys, orphan fact rows); QA-05 period logic + data coverage re-derived from base tables; QA-06 freshness, series gaps, blank share, impossible negatives; QA-07 filters applied / skipped; QA-08 every figure in the Cortex summary matches a computed fact.
- UI: pill per tile (Checking / Verified / Review / Mismatch / Not checked), page strip with counts and top note, Validation report modal (expected vs actual, difference, both SQLs, issues-only, re-run). Portal viewers see one "verified when published" line stored with the published version.
- Evidence: new table AA_VALIDATION_RUNS (one row per page run, full report as VARIANT).
- Guardrails: max 30 independent queries per run, 6 parallel, de-duplicated; only changed tiles re-checked; refresh-only changes re-checked at most every 10 minutes.
- Verified locally: 183 tests OK, Playwright on Executive / Manager / Operations dashboards; a planted 0.2% Profit error turned exactly the Profit tiles to Mismatch.
- Limits: derived metrics across tables at different grains and window-function metrics show Not checked; app role needs SELECT on base tables; DESCRIBE property names for relationships = VERIFY on the live account.
- Test steps: SCENARIO_19_validation.md. Next: drop 2 UAT (requirement trace, Excel UAT workbook, section sign-off).

## 2026-10-14 V1 fix after first live run (Harborline)
- Bug: QA-01 merged metrics from different tables (sales, plan, inventory) with UNION ALL but each part listed its columns in a different order, so values landed in the wrong column -> false Mismatch on 'Year to date vs plan', 'Gross Sales over time', 'where the year is heading'. Fixed: every part lists all metric columns in the same order. 'What drove the change' (one table) was already Verified.
- Semi-additive metrics (NON ADDITIVE BY dates.calendar_date, e.g. Ending Units On Hand) are now rebuilt with the same rule: only rows at the latest date inside each group. Read from DESCRIBE (NON_ADDITIVE property or 'NON ADDITIVE BY' in the expression) - VERIFY the property name on the live account. Semi-additive metrics used inside another formula show Not checked.
- 185 tests OK; synced to the package, zip rebuilt.
- Open: validation runs inside the action, so the app shows busy while it checks; proposal = run it in the background.

## 2026-10-14 V1 validation runs in the background
- The validate action now starts a background thread and returns at once, so the dashboard stays usable while the base-table checks run (they can take a while on 17M-row tables). Results arrive tile by tile; the strip shows "N of M checks · X of Y tiles done · you can keep working"; the UI polls every 2 s (validate_poll, no busy bar, no query tag). A newer run (filter change, tile edit) cancels the older one and its results are dropped. The finished run is written to AA_VALIDATION_RUNS with its duration.
- Safety: the background run works on a copy of the query cache and of the dashboard spec, never touches Streamlit state; a run that fails records "Not checked" with the reason instead of leaving tiles on "Checking".
- 186 tests OK; package synced, zip rebuilt.

## 2026-10-15 V2 Validation tab + diagnosis + resolutions
- New Validation tab next to the page tabs (also on single-page dashboards): overall status, pages checked, tiles verified, values compared, last run; "Validate all pages" (queries unopened pages, then checks everything in the background) and "Re-run everything"; check matrix (tile x QA check, click a row for inline evidence); Needs attention list; What was checked against (semantic view -> base tables, joins with unique keys and unmatched rows); run history from AA_VALIDATION_RUNS. Page strip "View report" opens the tab; tab icon follows the overall status.
- Diagnosis of every QA-01 mismatch (up to 3 per run): tests variants of the rebuild and reports a cause only when it reproduces the dashboard numbers exactly: (1) data changed during the check (re-run the dashboard query) -> Refresh; (2) rows with no matching lookup key dropped by the view -> source data, raise a data issue; (3) end-of-period (NON ADDITIVE BY) rule not applied -> app. Otherwise "Cause not found" with what was ruled out. NON ADDITIVE BY is now also read from GET_DDL when DESCRIBE does not show it.
- Resolutions: Accept with reason (re-opens after 7/30/90 days or when the numbers change; shown as Accepted, never Verified) or Raise data issue (owner + due, logged in Decisions with the evidence). Audit in new table AA_VALIDATION_RESOLUTIONS. Re-run tile, Refresh, Regenerate summary buttons per finding.
- Publish dialog shows pages validated / verified / open findings (warn only).
- Deferred to UAT drop 2: testing a semantic-view definition change on a copy (QA mismatches resolve to data, refresh or app causes; definition changes come from business expected values).
- 192 tests OK; package synced, zip rebuilt.

## 2026-10-15 Page tabs as a navigation bar
- Page tabs restyled: white bar with a PAGES label, numbered tabs, current page as a dark pill, page actions only on the current tab, Validation tab on the right with its status icon, dashed + Add page. CSS only (app_styles.css).

### 15 Oct 2026 — UI Phase 1: premium design system (themes + insight headlines)
- Three dashboard themes, switchable per dashboard with no query: **Editorial** (warm cream, default), **Command** (dark), **Classic** (previous look). Stored in view settings, published with the version.
- All chart colours now come from theme tokens (series palette, heat scale, area/line, heatmap empty cells), so one switch restyles every chart.
- **Insight headlines** (new headlines.py): each tile leads with one rule-written sentence from its own computed numbers ("South leads Profit at $1.8K, +131% on last week; Central trails at $596"). No AI, so every figure is one validation already checks. Tiles with nothing to say keep their question title.
- Period and Compare filters are now pill chips instead of dropdowns. Narrow tiles give the headline full width.
- Files: headlines.py (new, added to both snowflake.yml entities), engine.py, app.py, app_bundle.js, app_styles.css, tests/test_headlines.py. 195 tests pass (project folder and package). Package zip rebuilt (89 files).
- Verified locally only (fake Snowflake + Playwright, Executive / Manager / Operations, Editorial and Command). Next: Phase 2 chart engine.

### 15 Oct 2026 — Chart types, drop A + Classic default
- **Classic is the default theme again**; the Editorial/Command/Classic switch was removed from the dashboard header (Sharath: themes should follow the customer company, not be shown by default). Company themes (upload/brand colours) proposed as the next step.
- **Four new chart types** (new chart_tiles.py, added to both snowflake.yml entities):
  - **Bars + line** (combo_chart): a metric as bars plus a second metric, usually a rate, as a line on its own axis; latest values labelled.
  - **Treemap**: box size = value of an additive metric, share and change vs prior on each box, optional nesting by a second dimension; zero/negative values listed, not drawn.
  - **Progress gauge**: YTD vs full-year plan (else last year's total), tick at where the target is by now, pace and projected finish, time left.
  - **P&L table**: metrics as rows x dimension values + Total, each cell shaded better/worse vs prior period (or last year when Compare = Last year); lower-is-better aware.
- Cortex vocabulary + validator (repairs: ratio → no treemap/gauge, unknown nesting dropped), Add tile picker and tile edit menu, review-screen sketches, insight headlines.
- Reviewed layouts: Executive "Year vs plan" adds the gauge; Executive "Growth & mix" uses bars + line (when a rate exists) and the treemap; Manager Detail pages open with the P&L table.
- Validation: QA-01 recompute as for every tile; QA-02 recomputes treemap shares/changes/group sums, gauge progress/pace/projection, P&L changes; QA-03 reconciles treemap boxes and P&L additive rows to the total.
- Files: chart_tiles.py (new), composer.py, engine.py, headlines.py, validation.py, persona_layouts.py, app_bundle.js, app_styles.css, snowflake.yml, tests/test_chart_tiles.py (new, 8 tests), tests/test_persona.py. 203 tests pass (project and package). Zip rebuilt (91 files). Verified locally only.
- Next: company themes (if approved), then chart drop B (cash-flow river, daily pulse with annotations, cohort heatmap, new vs returning).

### 15 Oct 2026 — Company themes
- New **Company theme** screen (left menu, under the steps; builder only, never in the portal or viewer mode). Classic stays the built-in default until a company theme is set.
- Add a theme three ways: **brand colours** form (primary required; accent, background, cards, text, positive, negative, warning, up to 6 chart colours), **brand file** upload (JSON design tokens of any nesting incl. {value}/{$value}, or CSS custom properties), **logo** upload (PNG/JPG main colours quantised; SVG fill/stroke colours). Uploads are parsed for colour values only, max 1.5 MB.
- Everything else (lines, tints, heat scale, button text, summary band) is derived. Checks before saving (themes.py): T-01 text contrast >= 4.5:1, T-02 button text >= 4.5:1, T-03 chart colours >= 3:1 on cards (WCAG 1.4.11), T-04 chart colours distinct (delta E >= 15), T-05 positive vs negative different colour families. Failing colours are nudged (hue kept) and the report shows before → after; the person can change the input and re-check. Live preview of the result.
- **Company default** and **per-dashboard override** (kept in the layout spec, so save/open keeps it). Publishing freezes the theme with the version (theme_snapshot), so the portal shows it and later theme edits don't change published versions.
- Storage: AA_THEMES (every save is a new row = history; remove = inactive row), AA_APP_SETTINGS (default_theme, who/when). No admin rights needed. Font stays Inter.
- Files: themes.py (new, added to both snowflake.yml entities), store.py, app.py, app_bundle.js, app_styles.css, tests/test_themes.py (new, 11 tests), tests/fake_snowflake.py. 214 tests pass (project and package). Zip rebuilt (93 files). Verified locally only.
- Next: chart drop B (cash-flow river, daily pulse with annotations, cohort heatmap, new vs returning).
- 15 Oct (fix): Company theme and Governance & AI quality moved from the bottom of the left menu (pushed off-screen on long dashboards) into a **Settings** group under "For your viewers". Files: app_bundle.js, app_styles.css. Zip rebuilt.

### 16 Oct 2026 — Visuals program agreed
- Goal: dashboards at Claude-level design quality or better, keeping governed + validated numbers. Plan in `VISUALS_PLAN.md`; rows VX0–VX4 added to section R.
- Two layers: governed design system for every dashboard (compositions, annotations, emphasis, more chart types, export, accessibility) + Cortex Design Studio with Claude Opus at build time (art-director JSON spec, Design QA + critique loop, generated components in a sandbox with QA-09 rendered-number check, frozen and versioned, Layer 1 fallback).
- AI-written code is acceptable when it comes from Cortex, with controls replacing human review. Not doing: whole dashboards generated as code on every request.
- Success test: blind side-by-side of 5 reference dashboards, ours preferred or tied ≥ 70%.
- Next: VX0 probe and VX1 mockup (2–3 compositions on Harborline data, side by side with today) before building.
- 16 Oct: order confirmed by Sharath: validation drop 2 (V3) first, then the visuals program (VX0 onwards).
- 16 Oct: Test & Demo Playbook updated: Scenarios 18 (table picker), 19 Part A + B (validation, incl. recheck of the 14 Oct Harborline mismatches and Ending Units On Hand), 20 (look + company themes), 21 (new chart types); test round rows R22–R27 and results-log rows added.
- 16 Oct: V3 validation drop 2 built and synced: in-app Business sign-off (replaces the UAT workbook as the main flow). Validation tab: 4 steps (Numbers checked → Review tiles → Sign off pages → Ready to publish), one "Next step" line, per tile "Numbers check (automatic)" vs "Your decision" (Looks right / Needs change), quick reason chips when the numbers differ, "+ Link requirement", page sign-off never blocked (gaps → "Signed off with notes", reason required).
- 16 Oct: Fix loop: Needs change → builder sees a note on the tile (Mark as fixed / Reply) → reviewer re-checks (Looks right / Still needs change). New left-menu group "Review": Change requests (builders, all dashboards, badge) and Waiting for my sign-off (reviewers). Owner = dashboard creator, "Change owner" hands over. Publish dialog warns about open requests (does not block).
- 16 Oct: Storage: AA_UAT_SIGNOFFS (+ DASHBOARD_NAME, PAGE_LABEL, TILE_TITLE); owner hand-overs in AA_APP_SETTINGS (owner:<dashboard_id>); dashboard CREATED_BY now the signed-in user. UAT pack download (optional) gets a Review History tab. New files: uat.py, uat_export.py, xlsx_lite.py. 227 tests pass (project + package). Email alerts deferred (needs an admin-created Snowflake notification integration).
- 16 Oct: Validation coverage complete: QA-02 (displayed arithmetic) and QA-03 (reconciliation against a separate governed query) added for kpi_plan, ytd_trajectory, scorecard, status_tiles, pace_chart, worklist, small_multiples, scatter, heatmap (QA-02 shape; QA-03 existed), exception_table, combo_chart. Ratios/averages are marked "not additive" instead of forced to add up. New test_validation_tiles.py plants an error in every type and checks it is caught. 232 tests pass (project + package). Synced, not deployed.
- 16 Oct: Backup "pre visuals" taken before VX0/VX1: Downloads\snowflake-react-app-runtime\Analytics_Accelerator_Enterprise_Claude_backup_2026-10-16_pre_visuals (+ .zip, MANIFEST_md5.txt of 253 source files, RESTORE.md) and Downloads\Analytics_Accelerator_Install_backup_2026-10-16_pre_visuals (+ .zip). Not yet verified live; take a "known good" backup after the playbook passes. Optional Snowflake clone SQL is in RESTORE.md.
- 21 Oct: Source control: project pushed to GitHub, private repo https://github.com/sharathtableau/Analytics-Accelerator (branch main, tag pre-visuals-2026-10-21, 134 files; .gitignore excludes build output, caches, old snapshots, _codex_reference, Claude outputs, secrets). Install package not in the repo (kept as backup folder + zip).
- 21 Oct: Visuals program (VX0 probe, VX1 mockup) PARKED by Sharath for a new higher-priority requirement. Plan stays in VISUALS_PLAN.md; resume from VX0 when unparked. Baseline to return to: tag pre-visuals-2026-10-21.
- 21 Oct: Popup placement fixed (Sharath's request): Cortex Agent opens on the right, directly under the "Ask Cortex Agent" button (620 px wide, up to 640 px tall, shrinks to fit the screen); other popups (Decisions, Governance, Company theme, Change requests, Waiting for my sign-off) open centred on the part of the page on screen, found with IntersectionObserver strips since the app is one tall frame in Snowsight. Light shade, Esc closes. Bundle + CSS only. Synced, not deployed.
- 21 Oct: Data alerts by email (tracker row 10 / H1, data alerts first) built and synced, not deployed. Tile ⋯ → "Alert me…"; plain-English box read by Cortex AI_COMPLETE (fields only, never SQL; rule-based fallback), every part checked against the semantic view; rules: above/below, change vs previous period or last year (points for % metrics), behind/ahead of plan (metrics with PLAN_), no new data; latest day/week/month; hourly/daily/weekly in the person's time zone; several recipients. Test against data, Send test email, My alerts (status, history, Check now, Edit, Pause, Delete, badge). Each breach emailed once per period. New: alerts.py, alerts_core.py (also the body of procedure AA_RUN_ALERTS), tables AA_ALERTS + AA_ALERT_RUNS, task AA_ALERTS_TASK (hourly, created from the app). Email via SYSTEM$SEND_EMAIL + integration AA_EMAIL_INT (created by WBR_OWNER 21 Oct, no recipient list). Open: Sharath's Snowflake email not verified yet (IS_EMAIL_VERIFIED false) → no email can be sent until verified; EXECUTE TASK for WBR_OWNER not confirmed. 241 tests pass (project + package). setup/admin_alerts_email.sql added.
- 21 Oct (after first live test): alert fixes synced — alerts use finished periods only (today's partial day no longer compared with a full day last year); same day last year = same weekday 364 days back; a "%-looking" metric whose values are amounts (GROSS_MARGIN) is shown as $; redesigned email (subject says what happened, ALERT/NO ALERT label, value, comparison table, button to the dashboard); errors and results now show next to the form's buttons; incomplete alerts can no longer crash. First live test email received by Sharath 21 Oct.
