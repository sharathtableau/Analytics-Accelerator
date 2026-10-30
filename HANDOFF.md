# Analytics Accelerator – Enterprise: session handoff (updated 29 Oct 2026)

Read this fully, then wait for Sharath's go-ahead before building anything.

## How to work with Sharath

- **Plan before building.** Talk through the plan and the changes first; start only when he says yes. Never hide, remove or change anything he did not ask for (22 Oct: Cortex ideas were hidden without asking; he was rightly upset).
- **Deploy steps.** Always give the complete command (`cd /d "<project folder>" && <script>`), never just the script name.
- **UI changes.** Show a before/after image, screenshot or mockup. Keep the existing font (Inter in the app; Montserrat in the deck).
- **Be honest about testing.** Say what is verified locally (fake Snowflake + Playwright) and what is not yet run on Snowflake.
- **Quality bar.** The accelerator is going to Snowflake for approval: validation quality, evidence and readable visuals matter most. Slides must be readable (dark text, no small grey text).
- **No ACCOUNTADMIN.** Admin-free designs; when unavoidable, write complete, paste-ready SQL (no placeholders) for someone else to run.
- **Fictional companies only** in demo data and UI.
- **Main folder** on his computer always holds the latest code. He deploys himself.
- He often adds `/brain-dump` (wants the structured four-section analysis) and `/caveman` (short answers).

## The product

Snowflake-native BI builder: Streamlit in Snowflake (container runtime) + hand-patched React bundle `app/streamlit/app_bundle.js` (source of truth, never rebuilt), plus a viewer-only Portal running the same code. Architecture: `ARCHITECTURE.md` and the slide `Downloads\Analytics Accelerator Partner Demo\Analytics_Accelerator_Architecture.pptx`.

**Project root:** `C:\Users\SharathKumarKammari\Downloads\snowflake-react-app-runtime\Analytics_Accelerator_Enterprise_Claude` (connected as `~/mnt/Analytics_Accelerator_Enterprise_Claude`).

- `app\streamlit\`: app.py, store.py, config.py, engine.py (Engine = ChartTiles + PersonaTiles + DomainTiles), composer.py (TILES, Validator `_opts`), persona_layouts.py, persona_tiles.py, chart_tiles.py, **domain_tiles.py**, headlines.py, themes.py, custom_metrics.py, semantic_*.py, table_finder.py, home.py (catalog, ideas, **persona_ideas / persona_fallback**), validation.py, uat.py (`attention()`), uat_export.py, xlsx_lite.py, alerts.py, alerts_core.py, ai_services.py, agent_service.py, **domains.py**, **domain_packs.py** (FINANCE / CPG / RETAIL packs, RULES, ALERTS, PERSONAS, `persona_tiles()`), portal.py, portal_view.py, app_bundle.js, app_styles.css, snowflake.yml (every module listed for both apps; a test checks it).
- `app\tests\`: fake_snowflake.py, **fake_domains.py** (serves the real INFERA pack CSVs when `AA_FAKE_DOMAINS=1`, last week ending 2026-10-18), tests. Run: `cd app\tests`, `PYTHONPATH=..\streamlit;.`, `python -m unittest discover`. **Last result: 283 OK (22 Oct), project and package.**
- `setup\`: admin SQL; `retail\` (Harborline), `finance\` (Keystone Financial: `run_finance_setup.cmd`, view only `run_finance_sv.cmd`), `cpg\` (Apex Athletic: `run_cpg_setup.cmd`, view only `run_cpg_sv.cmd`). Logs are UTF-16 (convert with iconv).
- Root docs: **ENTERPRISE_TRACKER.md** (section R = priority order; change log; update with every change), **MULTI_DOMAIN_PLAN.md** (current priority), ARCHITECTURE.md, README.md, CAPABILITY_MAP.md, VISUALS_PLAN.md (parked), ENTERPRISE_PLAN.md + DEMO_SCRIPT.md (historical), SCENARIO_*.md, NEW_SESSION_PROMPT.md.
- R&D: `rnd\domain_layouts\v2\`, chart research `CHART_RESEARCH_v2.md` (project doc `claude/chart_research_v2.md`).

**Install package:** `C:\Users\SharathKumarKammari\Downloads\Analytics_Accelerator_Install` (+ .zip). `templates\app\streamlit\app.py`, `snowflake.yml` and `config.py` are templated: patch them in place with python/sed, never copy over. Tests from `templates\app` with `-s tests` and env AA_FAKE_SNOWFLAKE=1, AA_APP_SCHEMA=WBR_DB.ANALYTICS_ENTERPRISE, AA_DISCOVERY=WBR_DB.RETAIL_DEMO,WBR_DB.PUBLIC,WBR_DB.PIPELINE_DEMO, AA_FEATURED and AA_DEMO_SV=WBR_DB.RETAIL_DEMO.RETAIL_ANALYTICS_SV, AA_SEARCH=WBR_DB.RETAIL_DEMO.RETAIL_ANALYTICS_SV=WBR_DB.RETAIL_DEMO.RETAIL_DOCS_SEARCH, AA_AGENT_WAREHOUSE=POWERHOUSE. Then rebuild the zip with Python (`/tmp/aa_install.zip` → copy to Downloads).

**Deploy:**
- `cd /d "C:\Users\SharathKumarKammari\Downloads\snowflake-react-app-runtime\Analytics_Accelerator_Enterprise_Claude" && deploy_enterprise.cmd`
- `cd /d "C:\Users\SharathKumarKammari\Downloads\snowflake-react-app-runtime\Analytics_Accelerator_Enterprise_Claude" && deploy_portal.cmd`

**Working method:** edit in a cloud working copy → test with fake Snowflake + Playwright → compare device md5s with the last sync → commit files to the device → run device tests → sync the package (patch app.py in place) + rebuild zip → append to the tracker. Device deletes are not allowed: unwanted files go to `Downloads\_to_delete`.

**Bundle conventions:** Streamlit Components v2; onClick only (no form submit); `send(type, payload, label, quiet)`; patches use `/* @__PURE__ */ l.jsx` / `l.jsxs`; back up and `node --check` a .mjs copy; don't name locals `vr`. Home component `Cp`: persona state `pe`/`per`, persona ideas `PI`/`pI`. New S keys reach the frontend automatically (payload = S minus cache/published/tile_q).

**GitHub:** private repo https://github.com/sharathtableau/Analytics-Accelerator (tag `pre-visuals-2026-10-21`). A GitHub token was found in an unrelated folder's .git/config; he was told to revoke it. Never use or repeat it.

**Backups:** `..._backup_2026-10-16_pre_visuals` (project + install). A known-good backup after the live walkthrough is still to do.

## Update 29 Oct (read first)

- **Weekly digest email: NOT needed for now** (Sharath, 28 Oct). Set me up stays as deployed.
- **Access control PARKED as a top priority** (tracker row 4 / D3, plan in `ACCESS_CONTROL_PLAN.md`). Today the Portal does not know whether an executive or a manager is signed in: it knows the Snowflake user name only (owner's rights), Share "Roles" only grants Portal access, and only "Only these users" filters. Plan, BI-tool style: groups managed in the app (AA_GROUPS, group -> workspace + default persona) -> publish to groups -> Portal shows only what your groups may open -> row rules later. Open decisions: who manages groups; old dashboards visible to all until assigned (suggested); first drop without row rules (suggested). Picked up AFTER the changes Sharath lists next; plan + mockup with him before building.
- **Portal and domains (checked in code 28 Oct):** one Portal with a workspace picker (only domains with dashboards visible to the viewer; skipped when there is one; remembered per viewer; Switch workspace). Dashboards are assigned to a domain from the layout's domain or the semantic view; inside, grouped by audience. Personas, ideas, Set me up stay builder-only.
- **Multi-domain plan, still open:** Phase 4 polish (agent evals per domain + gotcha checks QA-09 = DEV developer; Finance/CPG playbook scenarios; demo script per domain); persona ideas quality check (plan step G) not built; domains hard-coded in domains.py (DEV Task 3); 30->60 roll rate effectively dropped (DPD columns cumulative).
- **Second developer re-scoped to testing (29 Oct):** see the tracker change log (Test round 29 Oct, Scenarios 23-33 in the Test & Demo Playbook).
- **Built 29 Oct, DEPLOYED 30 Oct by Sharath: Home layout Option A.** With a persona picked: ideas directly under the prompt box, persona card beside them as 'About this role' (nothing removed), data strip below the ideas; no persona = unchanged. Guard test test_home_layout.py; tests 325 OK project + package.
- **Next:** Sharath is about to list new changes; document them first, then plan, then build. After those: access control, then CL2 trust.

## Update 28 Oct (read first)

- **Built 27–28 Oct and deployed by Sharath (live check pending, see the test list below):**
  - Review "+ Add or remove metrics" restored on every layout;
  - Set me up: interview → proposal to tick → draft dashboards + alerts + Start here;
  - "+ Your role" merged into Set me up as "Just create my persona";
  - Home: Close on the Continue card; × delete on Your drafts (owner only, not published; hidden via `dash_hidden:<id>`, versions kept);
  - Meeting brief: Cortex over all pages' governed facts, every figure checked;
  - Share snapshot: all pages in one HTML file, Ctrl+P gives a PDF;
  - brief and snapshot are in the Portal too. Tests: 322 OK.
- **Live test list to run:** Review add metric → Set me up (Finance, "Head of collections") → Close/delete → Meeting brief (2+ pages) → Share snapshot → Portal brief/snapshot → click a value to ask, data-first agent, anomaly alert preview.
- **Next:** the weekly digest email (Set me up step 2; plan with Sharath first), then CL2 trust (certified metrics, tie-out, change detection), CL3 "what else is going on" (scope first), CL4 starter offer (after DEV Task 3), CL8 company-wide semantic layer (later).
- **Parked:** PowerPoint export (story deck), at Sharath's request. Cross-source matching waits for a Marketing domain.
- **Product name: OPEN.**
  - Sharath wants a professional name with a clear meaning (like VizLeap = viz + leap), not "Dash" names and not the VizLeap brand.
  - Rejected (taken or unsuitable): InsightPilot, DataPilot, InsightFlow, Clarity BI, Nexa BI, InsightIQ, LeapBI, Lodestar, MetricLens, the Dash* names, Icebreaker, Sixpoint, VizLeap Studio.
  - Latest shortlist: MetricMind (recommended), InsightCraft, DecisionCraft, Askwise, BoardReady.
  - A web check is not a trademark search: Blend legal to confirm.
  - When chosen, rename the UI text, Portal, slide and docs; Snowflake object names stay.
- **DEV version:** owned by DS_BASIC. Sharath deploys it with `set AA_DEV_CONN=wbr && deploy_dev.cmd` (always `--role DS_BASIC`). Developer tasks: Claude Doc "Analytics Accelerator DEV – Developer Tasks" + `DEV_TASKS.md`; code zip `Downloads\Analytics_Accelerator_Enterprise_DEV.zip`.
- **Rules (reconfirmed):** never hide, lock or remove an existing feature without Sharath's yes; list affected features before building; guard tests for existing features.

## Update 27 Oct (read first)

- **Roadmap after the Clarity meeting (agreed 27 Oct, tracker rows CL1–CL5):** 1) Set me up + weekly digest email (plan with Sharath first), 2) trust: certified metrics, tie-out check, semantic view change detection, 3) "what else is going on" with Marketplace context (scope), 4) one-month starter offer packaging (after DEV Task 3), 5) cross-source ID matching (only when a Marketing domain is approved). "Clarity" = Ryan / Harsh's strategic-analysis programme; this accelerator is its entry point.
- **27 Oct fix:** Review "+ Add or remove metrics" restored on every layout (it had been hidden on reviewed layout packs since 22 Oct without asking). Guard test `test_review_metrics.py`. Rule: never hide, lock or remove an existing feature without Sharath's yes; list affected features before building.
- **DEV version:** `Analytics_Accelerator_Enterprise_DEV`, app `WBR_DB.ANALYTICS_ENTERPRISE_DEV.ANALYTICS_ACCELERATOR_ENTERPRISE_DEV`, owned by DS_BASIC (deploy: `set AA_DEV_CONN=wbr && deploy_dev.cmd`, which always deploys with `--role DS_BASIC`). Developer tasks: Claude Doc "Analytics Accelerator DEV – Developer Tasks" + `DEV_TASKS.md`.

- **Deployed by Sharath 27 Oct:** everything below that was "deploy pending", plus navigation (Continue card, back to Review with edits kept, Save / Discard / Cancel when leaving unsaved work) and **persona ideas v2**: code computes what moved for the persona (governed change_bars, last 13 weeks vs last year) → Cortex AI_COMPLETE writes ~6 ideas → code checks real metrics + stay-in-lane (most metrics the persona's own, one supporting allowed); cards show "Why this idea" with the exact SQL finding; saved per role@domain#persona with the data week, so a new week = new ideas. Persona guidance ("Watches") is seeded from research (domain_packs.LENS_SEED) and stored as data in AA_APP_SETTINGS `lens:<domain>:<persona>` (Edit / Approve in the app). "+ Your role": Cortex drafts a personal persona (`mypersonas:<domain>:<viewer>`). Tests 289 OK.
- **Demo answers:** `DEMO_FAQ.md` (how ideas are made, no training, one agent per domain vs ideas).
- **Now (agreed 27 Oct, plan first):** anomaly alerts + click a value to ask. **Then Set me up** (parked, first priority after these). Then access control.
- Not wanted: in-app "How are these ideas made?" link.
- Open: Sharath to push to GitHub (commands given; this session has no GitHub access) and take a known-good backup.

## What is built (state 23 Oct)

Deployed and live: workspaces Phase 1, Finance + CPG data and semantic views (re-run 22 Oct with RISK_ADJUSTED_YIELD / PROMO_ID, checks OK), data alerts (first email 21 Oct), validation on demand + publish gate, in-app UAT.

Synced to the project folder and package, **deploy + walkthrough pending** (22 Oct):
1. **Analysis tiles** (domain_tiles.py + bundle "chart drop B"): outlier_lines, change_bars, driver_split, velocity_split, stacked_trend, metric_waterfall; scatter break-even/groups; heatmap window/change/band. Each writes its own finding.
2. **Rebuilt Finance / CPG layout packs**, 3 extra Retail layouts (offered beside the generic ones).
3. **Left menu:** Change requests and Waiting for my sign-off removed; replaced by the Home attention strip and "to fix / to re-check" pills.
4. **Domain personas on Home:** 4 ontology personas + Leadership + Weekly watchlist per workspace; persona card (owns, decides, questions, alerts, not in this data); dashboard built on the persona's layout, labelled "FOR <persona>".
5. **Persona ideas:** picking a persona shows "Ideas for the <persona>" from Cortex (saved per role@domain#persona, ↻ New ideas). Sharath's live check showed the same ideas for every persona = old build still deployed.

Built and deployed 27 Oct: **persona ideas v2** (was planned 23 Oct) (runtime, data-aware; plan A–G and the persona KPI research in MULTI_DOMAIN_PLAN.md). Open decisions: lens in code vs drafted by Cortex · freshness by data week vs 7 days · typed persona now or with Set me up.

Delivered 23 Oct: architecture slide (component view, numbered connections, readable text) + ARCHITECTURE.md; all docs updated.

## Meeting 22 Oct (team suggestions) – awaiting go-ahead

Recommended order: 1) **Set me up** (agentic interview → persona workspace + Start-here brief + alerts), 2) anomaly alerts, 3) click a value to ask, 4) outside context via Marketplace (scope first). Not now: harmonisation, export, Streamlit messaging. Open questions to Sharath: what is "Clarity"? Is a Marketing domain needed?

## Open items and known limits

- Sharath: deploy + walk through the 22 Oct work on all three workspaces; verify EXECUTE TASK for the hourly alert task; take a known-good backup; playbook Scenarios 13–21; AI Gateway probe; admin_ai_guardrails.sql.
- Unverified live: DESCRIBE SEMANTIC VIEW property names for relationships, multi-table CREATE SEMANTIC VIEW DDL, st.user values, NON ADDITIVE re-check.
- Data gaps (never promise): roll rates / vintages (no account-level data), deposit beta, promo baseline / elasticity, TDP, retail markdown / shrink / fulfilment.
- Validation: derived metrics across grains and window metrics show "Not checked". Agent doesn't know custom metrics. Composite join keys not detected.
- Install package: domain schemas hard-coded in domains.py (template later).

## Next steps (priority order)

1. Get Sharath's deploy result and walkthrough feedback; fix what he reports.
2. Persona ideas v2 after he answers the 3 decisions (build B + C first).
3. Meeting items in the order above, after go-ahead.
4. Phase 4 polish: agent evaluations per domain, validation checks from the ontology gotchas, playbook, demo script.
5. Access control (D3) is now a TOP priority (see Update 29 Oct). Later: install package fresh-account test + domain templating, AI Gateway, Snowflake Intelligence agent, what-if tile. Parked: visuals program.
