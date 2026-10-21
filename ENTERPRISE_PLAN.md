# Analytics Accelerator — Enterprise Edition (Snowflake demo: Thu 8 Oct 2026)

Owner: Sharath · Built with Claude · status as of 1 Oct 2026

## What this is
A new, separate Streamlit-in-Snowflake app (container runtime) with a React workspace. It does not
touch the current app (`DECISION_STUDIO_REACT_POC.ANALYTICS_ACCELERATOR_UI`).

| | |
|---|---|
| App | `WBR_DB.ANALYTICS_ENTERPRISE.ANALYTICS_ACCELERATOR_ENTERPRISE` |
| App tables | `WBR_DB.ANALYTICS_ENTERPRISE.AA_DECISIONS`, `AA_DASHBOARDS`, `AA_AI_RUNS` (+ `AA_FC_*` forecast models) |
| Code | `app\streamlit` (Python + built UI), `app\frontend\src` (React source), `app\tests` |
| Deploy | `deploy_enterprise.cmd` (connection `wbr`) |
| Config | `app\streamlit\config.py` — schemas, models |
| Old code | `_codex_reference\` (Codex package, kept for reference only) |

## User journey (4 steps)
1. **Source** — pick a semantic view the current role can see (allowlisted schemas).
2. **Metrics** — map fields to roles (primary/supporting metrics, time, segment, region). Heuristic
   first guess → optional **Cortex AI_COMPLETE** suggestion (validated: unknown IDs rejected) → user approves.
3. **Layout** — choose audience; the **layout catalog** (your starter, extended) shows every preset with
   readiness, fit score, page map and *why* it is blocked. Capability evidence is computed from real
   queries (time coverage, segment cardinality, freshness, additivity, RBAC). **Cortex recommends** a
   preset from the allowlist only; the catalog validator re-checks it.
4. **Workspace** — multi-page dashboard rendered from the bound spec via a fixed component registry.

## Snowflake AI used (all live, all governed)
| Capability | Snowflake feature | Where |
|---|---|---|
| All numbers | `SEMANTIC_VIEW()` queries under the user's role | every tile |
| Field mapping, layout pick, page summaries | Cortex `AI_COMPLETE` (constrained + validated) | steps 2–4 |
| Forecast | `SNOWFLAKE.ML.FORECAST` trained on the governed series | "Snowflake ML forecast" tiles |
| Key drivers | `SNOWFLAKE.ML.TOP_INSIGHTS` + reconciled contribution bridge | "What drove the change" |
| Conversational Q&A | Cortex Agent (`DATA_AGENT_RUN`) with Cortex Analyst on the same semantic view; auto-discovers the agent or **creates one** | "Ask Cortex Agent" drawer, "Ask agent" on exceptions/bars |
| Exceptions | Per-segment z-score vs own 12-period history | "Needs attention" |
| Decisions | Snowflake table, owner/due/status/evidence; log from exceptions or agent answers | Decisions page/drawer |
| AI governance | AI run ledger table + Cortex usage (ACCOUNT_USAGE) + recent SQL | Governance drawer |
| Saved dashboards | Versioned in Snowflake, reopen from Source page | Save button |

## Layout catalog
11 presets: your 8 starter presets + 3 baseline presets (`exec_growth_baseline`,
`manager_segment_scorecard`, `wbr_weekly_performance`) for sources without a versioned plan.
Where the target is a prior-year baseline, component titles say "prior-year baseline", never "plan".
Daily-operations presets stay blocked on stale data (fresh_data) — shown with reasons, by design.

## Verified locally (fake Snowflake session)
24 unit tests + full browser click-through: source → Cortex mapping → layout (evidence + Cortex pick)
→ 4-page workspace → AI summary → agent created → question answered → decision logged → saved → governance.
**Not yet verified in the account** — first deploy is the real test.

## First deploy
```
cd /d "%USERPROFILE%\Downloads\snowflake-react-app-runtime\Analytics_Accelerator_Enterprise_Claude"
snow sql -c wbr -f setup\00_create_schema.sql
deploy_enterprise.cmd
```

## Built since 30 Sep
| Area | What changed |
|---|---|
| Layouts | Cortex designs pages/tiles from a data profile + goal; validator allows only known chart types, real fields, proven capabilities and valid metric x dimension pairs; every decision in Governance -> Layout decisions |
| Charts | + share donut, Pareto, scatter, period comparison, heatmap (any two dims), detail table |
| Editing | Edit layout: move / resize / remove tiles, swap chart type, metric, dimension; add KPI metrics; "add a tile" and "redesign this page" in plain English |
| Home | Prompt-first home ("What can I help you build today?"), Cortex dashboard ideas per audience from all semantic views, request routing to the right data |
| Agent | Warehouse set on the analyst tool (fixes error 391920); app-owned agents are rebuilt automatically |
| Retail data | `WBR_DB.RETAIL_DEMO` - Harborline Outfitters (fictional): 17M order lines, 9.6M orders, 7M inventory rows, daily plan; simulated live feed; planted stories (West footwear stockouts, Southeast USPS slowdown, Southwest plan miss, free-shipping threshold change) |
| Semantic view | `RETAIL_ANALYTICS_SV`: sales + inventory + plan, ~45 metrics with definitions and synonyms (semi-additive inventory, plan attainment); v2 uses FACTS + metric-on-metric ratios after the first attempt was rejected |

## Next build - UX review of 1 Oct (approved, Publish = option A) - BUILT 1 Oct, tested locally, pending deploy
| # | Change | Why |
|---|---|---|
| 1 | **Review screen before building**: recommended metric cards (grouped by theme, definition + formula from the semantic view, "Recommended by Cortex" badge, checkbox) + an editable outline of pages and tiles -> **Build dashboard** | Cortex proposes, the user approves |
| 2 | **KPI cards**: value, period label, **one** delta; dashboard-level time bar - Period (last complete month/week/day) and **Compare to** (previous period / same period last year / plan) | Two comparisons per card were noisy and unclear |
| 3 | **Sparklines**: labelled window ("last 13 months"), current point highlighted, hover shows period + value | Unlabelled lines without hover said nothing |
| 4 | **Hover tooltips on every chart** (line, bars, waterfall, heatmap, donut, scatter) | Missing today |
| 5 | **Per-tile AI panel** (sparkle button): tile context (metric, dimension, period, data) -> questions to the **Cortex Agent** (governed SQL); edit requests via Cortex AI_COMPLETE through the same validator; suggested prompts | Ask and edit at the widget |
| 6 | **Pages sidebar**: page list, **+ Add page** (Cortex from a sentence, or blank + tile picker), rename, reorder, remove | Multi-page dashboards like a BI tool |
| 7 | **Audience as a chip, not a step**: Executive / Manager / Operations set defaults (grain, density, comparison) | Less friction |
| 8 | **Global filters**: Region, Category, Channel (+ period) applied to every tile | Real dashboards have filters |
| 9 | **Publish (option A)**: versioned, read-only viewer link (no builder chrome), share to Snowflake roles (GRANT USAGE on the app), optional user list; edits go to a draft and republish as v2. Note: the app runs with owner's rights, so all viewers see the same governed data | Production-style sharing without one app per dashboard |

Stretch / later: per-viewer row filtering (caller's rights), option B "publish as standalone Streamlit app" (CREATE STREAMLIT per dashboard), Cortex Search tool, US + Canada/UK data.

## Plan to Thursday (revised)
| Day | Goal |
|---|---|
| Thu 1 Oct | Semantic view v2 live (done); all 9 UX items built + tested on simulated Snowflake (done) -> deploy |
| Fri 2 Oct | Live test on retail data; fix what the account rejects; tune Cortex prompts |
| Mon 5 Oct | Demo storyline on the planted stories; polish |
| Tue 6 Oct | Publish to a test role, viewer walkthrough; backup video |
| Wed 7 Oct | Freeze at noon, rehearse twice, backup video |

## Roadmap (not in this build)
> **Superseded 10 Oct 2026:** the agreed post-demo roadmap and its order is section **R** of `ENTERPRISE_TRACKER.md`. The list below is the original 1 Oct note.
> **16 Oct 2026:** the visuals program (Claude-level design quality, Cortex Design Studio) is planned in `VISUALS_PLAN.md`.

Option B standalone app publishing · Cortex Search document tool · Native App packaging with agents ·
MCP server / Snowflake Intelligence surfacing · Cortex AI Gateway policies · ML anomaly detection model ·
multi-country data (US + Canada/UK) · scheduled email snapshots.

> **Tracker:** status of every brain-dump item and enterprise gap is in `ENTERPRISE_TRACKER.md` — keep that file current.
