# Analytics Accelerator – Enterprise

A Snowflake-native dashboard builder: business users describe what they need in plain English, Cortex designs the dashboard from governed data, every number is checked automatically against the source tables, and the result is published to viewers in a read-only portal. Everything runs inside Snowflake: no data leaves the account, and no external BI tool is involved.

Owner: Sharath (Blend360) · Built with Claude · README updated 27 Oct 2026 · "Analytics Accelerator" is a working name.

---

## 1. What it does

| Step | What the user does | What happens inside Snowflake |
|---|---|---|
| **Ask** | Types a goal on Home ("Board pack on revenue and margin vs last year, by region") and picks a persona of the workspace (e.g. Chief Credit Officer, Revenue Growth Manager, Category Manager) or Leadership | Cortex `AI_COMPLETE` routes the request to the right semantic view and proposes dashboard ideas for that persona |
| **Review** | Approves the recommended metrics (definition and formula shown from the semantic view) and an editable outline of pages and tiles | Cortex only proposes. A validator accepts only real fields, valid metric × dimension pairs and known chart types |
| **Build** | Gets a multi-page dashboard: KPIs, trends, breakdowns, forecasts, drivers, exceptions, a live operations view | Every number comes from a `SEMANTIC_VIEW()` query. Forecasts, drivers and anomalies come from Snowflake ML functions |
| **Validate** | Opens the Validation tab and runs the check on demand; every tile gets Verified, Review, Mismatch or Not checked, with evidence. Business reviewers sign off in the app | Each number is re-derived independently from the base tables and compared (section 4) |
| **Style** | Dashboards use the company theme (Classic until one is set) | Brand colours from a form, a design-token file or the logo, checked for WCAG contrast before saving (`themes.py`) |
| **Refine** | Edits tiles, pages and filters directly or in plain English; asks questions per tile | Edits go through the same validator. Questions go to a Cortex Agent (Cortex Analyst + Cortex Search) |
| **Alert** | Asks in plain English for an email when a metric crosses a line | A task runs the saved check on schedule and emails through a notification integration |
| **Publish** | Publishes a version to Snowflake roles or named users (needs a fresh validation) | Viewers get the **Analytics Accelerator Portal**: read-only, no builder controls, the same governed data |

**No semantic view yet?** The app can create one. A user describes a business question, Cortex picks candidate tables from metadata only, and the app drafts a single- or multi-table semantic view (2–8 tables) for the user to review. Join keys are checked for uniqueness and totals are reconciled before `CREATE SEMANTIC VIEW`.

**Custom metrics.** Users define metrics as a formula over governed metrics, or in plain English. The grammar is strict, the SQL is built from a parsed tree, and Cortex output is never executed as written.

## 2. Architecture

Full component view and connections: `ARCHITECTURE.md` and the slide `Downloads\Analytics Accelerator Partner Demo\Analytics_Accelerator_Architecture.pptx`.

```
Snowsight
 ├─ ANALYTICS_ACCELERATOR_ENTERPRISE   builder app  (Streamlit in Snowflake, container runtime)
 └─ ANALYTICS_ACCELERATOR_PORTAL       viewer app   (same code, portal mode: viewing actions only)
        │
        │  React UI (Streamlit Components v2) proposes actions; it never runs SQL.
        ▼
 Python (app/streamlit) owns every query, Cortex call, validation and write
   ├─ semantic_catalog / semantic_query   DESCRIBE + SEMANTIC_VIEW() queries (allowlisted fields, bound values)
   ├─ composer / layout_catalog / persona_layouts   Cortex designs layouts; validator certifies them
   ├─ engine / persona_tiles               computes every tile from governed queries + Snowflake ML
   ├─ chart_tiles / headlines              bars + line, treemap, gauge, P&L table; rule-written tile headlines
   ├─ validation                           automatic QA of every tile against base tables
   ├─ themes                               company themes: brand inputs -> checked colour tokens
   ├─ domains / domain_packs / domain_tiles  workspaces (Retail, Finance, CPG), personas, layout packs, analysis tiles
   ├─ home                                 catalog, ideas per persona, prompt routing
   ├─ uat / alerts / alerts_core           business sign-off; data alerts (task + procedure + email)
   ├─ ai_services / agent_service          AI_COMPLETE, AI_AGG, ML functions, Cortex Agents
   └─ store                                app tables in WBR_DB.ANALYTICS_ENTERPRISE
```

**Design rules**
- The browser is an untrusted proposer. The only channel to Python is an action event, and Python validates every payload.
- Every number comes from a semantic view under the app's role. Field names are matched against `DESCRIBE SEMANTIC VIEW` output, and filter values are checked against values read from the view.
- Cortex output is treated as a suggestion. Layouts, metric mappings, custom metrics and semantic view drafts are all validated before use, and every Cortex decision is logged.
- A failed query shows an explicit error on the tile. The app never substitutes sample values.

## 3. Snowflake features used

| Area | Features |
|---|---|
| Semantic layer | Semantic views (FACTS, metrics on metrics, synonyms), `SEMANTIC_VIEW()`, `DESCRIBE SEMANTIC VIEW`, `SHOW SEMANTIC DIMENSIONS … FOR METRIC`, `CREATE SEMANTIC VIEW` (drafted, then reviewed) |
| Cortex AI | `AI_COMPLETE` (constrained and validated), `AI_AGG` (page summaries from governed facts), `AI_PARSE_DOCUMENT` and chunking for documents |
| Cortex Agents | Cortex Analyst on the same semantic view, Cortex Search over policy documents, a custom stored-procedure tool that logs decisions, agents auto-created per view |
| Snowflake ML | `FORECAST`, `TOP_INSIGHTS` (key drivers), `ANOMALY_DETECTION` (exceptions) |
| Platform | Streamlit in Snowflake (container runtime), tasks + stored procedures (alerts), `SYSTEM$SEND_EMAIL` with a notification integration, query tags per feature for cost attribution, `ACCOUNT_USAGE` for the Cortex usage panel |

The full map, including deliberate non-uses, is in `CAPABILITY_MAP.md` (updated 23 Oct).

## 4. Trust: automatic validation (QA)

Validation runs on demand from the Validation tab (since 21 Oct). Nothing is checked while building. Publishing requires a fresh validation (after the last change, same data-through date, every page); mismatches do not block but need a sign-off reason.

| Check | What it proves |
|---|---|
| **QA-01 Source recompute** | Each query behind the tile is rebuilt as independent SQL straight against the **base tables**. The joins, column expressions and filters come from the semantic view's own definition. The results are compared row by row (relative tolerance 1e-6) |
| QA-02 Display arithmetic | % changes, shares, totals, Pareto and bridge steps on the tile are recalculated from the queried values |
| QA-03 Reconciles to total | For additive metrics, the segments add up to the headline total |
| QA-04 Join integrity | Lookup keys are unique (no double counting) and fact rows find their lookup row |
| QA-05 Period logic | Current, prior and year-ago periods are complete and correctly bounded, and the data coverage matches the base tables |
| QA-06 Data health | Freshness, gaps in the series, blank categories, negative values where they are impossible |
| QA-07 Filters applied | Active filters reach the tile and the independent query |
| QA-08 Narrative grounded | Every figure in the Cortex summary matches a computed fact |

- **Evidence.** Every check shows expected vs actual, the difference, and both SQL statements. Each run is stored in `AA_VALIDATION_RUNS`. A check that cannot run honestly says "Not checked" with the reason; it never passes by default.
- **What viewers see.** Portal viewers see "Numbers verified against the source tables", with the date checked, stored with the published version.
- **Cost limits.** At most 30 independent queries per run, 6 in parallel. Only changed tiles are re-checked. A refresh with no change to the page's tiles or view re-checks at most every 10 minutes.

## 5. Governance and cost

- **AI ledger.** `AA_AI_RUNS` records every Cortex call: feature, input, output, provenance, status, latency, and the signed-in person (from `st.user`, not the app's service user). The Governance & AI quality panel shows it together with Cortex usage and recent SQL.
- **Cost guardrails.** Per-person daily limits on AI and agent calls (`config.AI_DAILY_LIMIT`, `AGENT_DAILY_LIMIT`). Viewing is never limited. Admin budget and prompt-injection guardrail SQL is prepared in `setup/admin_ai_guardrails.sql` for an ACCOUNTADMIN to run.
- **Access today.**
  - The apps run with owner's rights, so every viewer sees the same governed data.
  - The builder and the portal are separate objects, granted separately.
  - Dashboards are shared to roles, or limited to named users.
- **Access, next on the roadmap.** Per-dashboard access by group, and row rules applied by the app.

## 6. Folder layout

| Path | Contents |
|---|---|
| `app\streamlit\` | The app: Python modules, `app_bundle.js` (the React UI; the deployed bundle is the source of truth), `app_styles.css`, `snowflake.yml` (both apps), `config.py` (schemas, models, limits) |
| `app\tests\` | Unit tests against `fake_snowflake.py`, an in-memory stand-in for Snowflake. No account needed |
| `setup\` | Schema creation, the agent tool, agent evaluation, cost snapshot, admin guardrails, alert email integration, and demo data: Harborline retail (`setup\retail\`), Keystone Financial (`setup\finance\`), Apex Athletic (`setup\cpg\`) |
| `gateway_probe\` | Test-only app that checks whether Streamlit in Snowflake can call the Cortex AI Gateway |
| `deploy_enterprise.cmd`, `deploy_portal.cmd` | Run the tests, then deploy each app with the Snowflake CLI (connection `wbr`) |
| `ENTERPRISE_TRACKER.md` | Roadmap (section R) and change log. Updated with every change |
| `ENTERPRISE_PLAN.md`, `CAPABILITY_MAP.md`, `DEMO_SCRIPT.md` | Original plan, feature map and demo script (written for the October demo) |
| `MULTI_DOMAIN_PLAN.md` | Multi-domain plan: Retail, Finance, CPG workspaces, personas, analysis tiles, persona ideas v2 plan (current priority) |
| `ARCHITECTURE.md` | Component architecture and connections (23 Oct) |
| `NEW_SESSION_PROMPT.md` | Prompt to start a new Claude session on this project |
| `DEMO_FAQ.md` | Answers to demo questions: how ideas are generated, training, agents per domain |
| `VISUALS_PLAN.md` | Visuals program: design system v3 and Cortex Design Studio (agreed 16 Oct, parked 21 Oct) |
| `SCENARIO_18_*.md`, `SCENARIO_19_*.md` | Test steps for the live account |

An install package for other Snowflake accounts, driven by `settings.ini`, is kept separately in `Downloads\Analytics_Accelerator_Install`.

## 7. Deploy and test

First time only (creates the schema and app tables):
```
cd /d "C:\Users\SharathKumarKammari\Downloads\snowflake-react-app-runtime\Analytics_Accelerator_Enterprise_Claude" && snow sql -c wbr -f setup\00_create_schema.sql
```
Deploy the builder and the portal (each script runs the unit tests first):
```
cd /d "C:\Users\SharathKumarKammari\Downloads\snowflake-react-app-runtime\Analytics_Accelerator_Enterprise_Claude" && deploy_enterprise.cmd
cd /d "C:\Users\SharathKumarKammari\Downloads\snowflake-react-app-runtime\Analytics_Accelerator_Enterprise_Claude" && deploy_portal.cmd
```
Run the tests only:
```
cd /d "C:\Users\SharathKumarKammari\Downloads\snowflake-react-app-runtime\Analytics_Accelerator_Enterprise_Claude\app" && python -m unittest discover -s tests -p "test_*.py"
```
Latest result: 289 tests pass (27 Oct), in the project and the install package.

**Required privileges for the app role:**
- USAGE on the allowlisted schemas and their semantic views.
- SELECT on the base tables behind them, needed for validation QA-01.
- Cortex AI functions, and the Snowflake ML functions used.

## 8. Status and known limits

**Status.**
- Demoed live to stakeholders in early October.
- Built since the demo:
  - Cost guardrails.
  - Custom metrics.
  - Layout variety.
  - Multi-table semantic views and the table picker.
  - UI restyle with visible progress.
  - Automatic validation, with a Validation tab, diagnosis and resolutions.
  - Insight headlines, company themes and four new chart types (15–16 Oct).
  - In-app business sign-off, validation on demand + publish gate, data alerts by email (16–21 Oct; first live email 21 Oct).
  - Workspaces: Retail, Finance, CPG with live data, domain layout packs, suggested alerts, analysis tiles, domain personas and persona ideas on Home (21–22 Oct).
  - Persona ideas v2: Cortex writes ideas at run time from the persona, its guidance and what moved in the data ("Why this idea"); '+ Your role' drafts a persona for any role; navigation keeps your work (continue card, back to Review, unsaved prompt) (23–27 Oct). All deployed 27 Oct.
- Most post-demo work has been verified locally only, with fake Snowflake and browser tests. The live test steps are Scenarios 13–21; the 22 Oct domain work still needs a deploy and walkthrough.

**Known limits.**
- Validation shows "Not checked" for derived metrics that mix tables at different grains, and for window-function metrics.
- The property names `DESCRIBE SEMANTIC VIEW` uses for relationships still need a check on the live account.
- The Cortex Agent does not yet know custom metrics.
- Composite join keys are not detected automatically.
- Per-viewer row filtering is not built yet. The apps run with owner's rights.

## 9. Roadmap (priority order, 27 Oct, after the Clarity meeting)

Built 27 Oct: anomaly alerts, click a value to ask, data-first agent, Review "+ Add or remove metrics" on every layout.

1. **Set me up + weekly digest:** an interview ("who are you, what do you do") that builds a persona workspace, 3–5 dashboards and alerts, then emails what changed and why. Adds "Build it for me" (Review stays).
2. **Trust:** certified metrics, tie-out against a reference number (e.g. finance's figure), semantic view change detection.
3. **"What else is going on":** drivers of a change + outside context from Marketplace data, in the digest (scope first).
4. **One-month starter offer:** install with configurable domains + pilot playbook.
5. **Cross-source matching** of campaign / customer IDs (when a Marketing domain is approved; scope first).
6. Access control (admin-free, BI-tool style; PRIORITY, plan in `ACCESS_CONTROL_PLAN.md`), dev / test / prod, audit trail + publish approval, security review, monitoring, load test.
7. Domain polish (DEV version): validation checks from the ontology gotchas, agent evaluations for Finance and CPG.
8. Later: Cortex AI Gateway, Snowflake Intelligence agent, Native App / Marketplace. **Parked:** visuals program (`VISUALS_PLAN.md`).

Demo questions (how ideas are made, training, agents): `DEMO_FAQ.md`. Full status: `ENTERPRISE_TRACKER.md`, section R.
