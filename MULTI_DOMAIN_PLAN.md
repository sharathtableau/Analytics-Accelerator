# Multi-domain plan: Retail, Finance, CPG (agreed 21 Oct 2026, revised the same day)

**Status (27 Oct)**
- Phase 1 (workspaces): built and deployed.
- Phase 2 (Finance): data live in Snowflake (21 Oct); layout pack and suggested alerts built (22 Oct, synced).
- Phase 3 (CPG): setup scripts, layout pack and suggested alerts built (22 Oct). Sharath runs `setup\cpg\run_cpg_setup.cmd`.
- Phase 3b (22 Oct): analysis tiles and rebuilt Finance / CPG layouts, plus 3 extra Retail layouts. Deployed 27 Oct.
- Phase 3c (22 Oct): domain personas on Home. Each workspace shows the ontology's 4 personas plus Leadership and Weekly watchlist; each persona has its own layout, starter questions, alerts and a "not in this data" note. Retail uses Harborline with 2 new layouts (Regional performance, Omnichannel & fulfilment). Deployed 27 Oct.
- Phase 3d (22 Oct): persona ideas on Home. Deployed.
- Phase 3e (27 Oct): persona ideas v2, runtime and data-aware: built and deployed (see section below; decisions: guidance seeded from research and stored as data, refresh per data week, '+ Your role' now, stay-in-lane = most metrics the persona's own + one supporting). Set me up parked (first priority after anomaly alerts + click a value to ask).
- Phase 4 (polish): to do.

## Persona ideas v2: runtime, data-aware (planned 23 Oct; BUILT and deployed 27 Oct)

**Problem (Sharath, 23 Oct):** persona ideas feel pre-filled. If the ideas are fixed, Cortex adds nothing. Cortex must suggest at run time, based on the persona and the data.

**Why today's ideas feel fixed (Phase 3d):**
1. The ontology questions go into the prompt word for word, so Cortex mostly rewrites them.
2. The first set is saved and shown again until someone clicks New ideas.
3. Cortex sees metric names only, never the numbers, so ideas do not react to what is moving.

**Plan**

| Part | What | Notes |
|---|---|---|
| A. Persona lens | Industry KPIs per persona (research below), given to Cortex as guidance, not as finished ideas. Cortex reasons: what this role usually watches → which of those this data has → which are missing. | Decide: lens kept in code per persona, or drafted by Cortex once and kept for review. |
| B. Data-aware ideas (main change) | When a persona is picked, a cheap pass computes the persona's metrics, last 13 weeks vs last year, by the main dimension: top 5 movers. Cortex gets the movers, so ideas point at the real story (e.g. "Near-Prime delinquency +5 pts"). New data week → new movers → new ideas. | Reuses `domain_tiles.py` mover logic; no new query engine. |
| C. Prompt redesign | Ontology questions become a tone example only; Cortex must not restate them. Ask for a mix: 2 monitoring, 2 diagnose-a-mover, 1 decision / what-if, 1 data gap ("you would need X"). | |
| D. Freshness | A saved set expires when the latest data week changes (or after 7 days), not never. New ideas button stays. | Decide: data-week change vs 7 days. |
| E. Any persona, typed in | User types "I'm a pricing analyst"; Cortex builds the persona brief at run time. | Overlaps with "Set me up" from the 22 Oct meeting. Decide: now or with Set me up. |
| F. Fallback | Without Cortex: ideas from the movers plus the lens, not the questions word for word. Clearly labelled. | |
| G. Quality check | Research KPI lists = expected coverage. A test fails if a persona's ideas cover fewer than 2 of its core KPIs, or repeat the ontology questions word for word. | |

**Build order:** B + C first (biggest effect), then D, F, G, then E.
**Cost:** about 1 movers query + 1 AI_COMPLETE per persona per data week.

**Persona lens: what each role usually watches (research, 23 Oct)**

| Domain | Persona | Usually watches |
|---|---|---|
| Finance | Chief Credit Officer | Delinquency by bucket, roll rates, net charge-off rate, vintage curves, risk-adjusted yield, FICO mix, approval rate vs loss |
| Finance | Head of Retail Deposits | Balance growth / runoff, rate paid vs competitors, deposit beta, cost of funds, CD maturity wall, attrition |
| Finance | Head of Card Portfolio | Purchase volume, active rate, interchange, rewards-to-interchange, revolve rate, NIM |
| Finance | Head of Acquisition Marketing | Applications, approval rate, cost per booked account, channel mix, early delinquency of new accounts |
| CPG | Revenue Growth Manager | Price / pack / mix, trade spend rate, promo ROI per event, gross-to-net, elasticity, baseline vs incremental |
| CPG | Key Account (NAM) | Sell-in vs sell-through, retailer weeks of supply, fill rate, trade per account, share at the account |
| CPG | Brand / Category | Consumer sales (POS), distribution (%ACV) vs velocity, share, price gap |
| CPG | Supply & service | Fill rate / OTIF, forecast accuracy, inventory days, stock-outs |
| Retail | Category Manager | Comp sales, margin %, GMROI, sell-through, weeks of supply, markdown %, assortment productivity |
| Retail | Regional | Comp by store / region, traffic × conversion × basket, labour %, shrink |
| Retail | Inventory | Weeks of supply, in-stock %, aged stock, open-to-buy |
| Retail | Omnichannel | Digital penetration, on-time delivery, fulfilment mix, returns |

Gaps in our data (never promise): vintage curves and roll rates (no account-level data), deposit beta (no benchmark rate), elasticity and baseline (no model), retail markdown / shrink / labour.

Sources: Javelin (card metrics), dotData (roll rates), Deloitte and Vividly (RGM), Leafio and Cleverence (category and inventory KPIs), Curinos and S&P Global (deposits).

## Analysis tiles (22 Oct)

Each tile answers one question and writes its own one-line finding from its own numbers. Comparisons are the last 13 weeks against the same weeks last year.

| Tile | Shows | Used for |
|---|---|---|
| outlier_lines | every member on one chart; the mover, or the one past a reference line, highlighted | delinquency by segment, rewards ratio vs 0.85, weeks of supply vs the 6–12 band, deposit index |
| change_bars | change vs last year as diverging bars (worst first); `dots` = now vs a year ago; `level` = value around a line | net charge-offs, margin by line, fill rate vs 95%, rate gap vs 0 with the balance change |
| driver_split | outcome = product of drivers, % change each | retail net sales = orders × order value |
| velocity_split | sales change = distribution effect + velocity effect | CPG product lines (wholesale) |
| stacked_trend | past-due balances by age (30–59, 60–89, 90+) for the worst segment | credit risk |
| metric_waterfall | gross sales − trade − returns, reconciled to the view | CPG gross-to-net |
| scatter (+ options) | every promotion event against break-even, coloured by tactic | trade & promotions |
| heatmap (+ options) | 13-week window, change vs last year, or coloured against a healthy band / the typical cell | sell-through, weeks of supply, delinquency change |

**Dropped after checking the data:**
- Roll rates: the DPD columns are cumulative (30+, 60+, 90+), and the v2 "roll" rise was an artefact of growth.
- Cumulative shipped-minus-sold: seasonality makes every line build up.

**Snowflake changes:**
- Finance: new `RISK_ADJUSTED_YIELD` and `CARD_REVENUE` metrics (re-run `run_finance_sv.cmd`, which now includes `02_views.sql`).
- CPG: new `PROMO_ID` dimension (included in `run_cpg_setup.cmd`).

**Revision (21 Oct):** the Finance and CPG data now come from the **INFERA vertical packs**: synthetic, seeded data with a business ontology and planted demo stories. Sharath compared them with our own plan and chose them because they are better.
- The pack is in `Downloads\files (9)\infera_vertical_packs`.
- It replaces our own planned "Meridian Card Services" and "Northpeak Brands".

## Why

Today the accelerator is a retail demo (Harborline Outfitters). Workspaces show that it works for any industry.

**Snowflake's feedback** (pack README): "breadth reads as generic".
- So we never demo all three workspaces at once.
- In a client meeting, open only that client's industry and go deep: question → root cause → action → alert → validated dashboard.
- We build one domain to full depth first. That is Finance.

## Decisions (Sharath, 21 Oct)

| Topic | Decision |
|---|---|
| Approach | One app with a domain layer. Not three apps, and no copies of Home. |
| Picker | Shown on the first visit, then remembered. A switcher under the brand in the left menu. |
| Retail | **Harborline Outfitters** (existing, validated, live feed). The pack's MeridianMart is parked. |
| Finance | **Keystone Financial**: consumer bank with cards and deposits (Capital One-type). Data from the INFERA pack. |
| CPG | **Apex Athletic**: athletic apparel and footwear brand selling through retailers (Under Armour-type). Data from the INFERA pack. |
| Names | Fictional companies only. Real companies were only examples of the business type. |
| Dashboards | Each dashboard belongs to one workspace, through its semantic view. Existing dashboards are Retail. |
| Layouts | Each domain gets its own layout pack, built from the pack's personas. |
| Portal | Gets the picker too. |
| Access | Open to everyone for now. |
| Agents | One Cortex Agent per domain: its semantic view, its document search (the pack's ontology) and its persona sample questions. |
| Dates | The pack's data is frozen at the week of 2026-09-14. Rolling views move it forward by whole weeks so the newest week is always the last full week. |
| Build order | Finance to full depth first, then CPG. |

## What we take from the INFERA pack, and what we fixed

**Taken from the pack:**
- the data: 104 weeks, weekly, seeded;
- the planted stories (internal guide, never loaded into search);
- the ontology: personas, metric dictionary, column dictionary, sample questions per persona, alert library, business rules and gotchas.

**Fixed in our build** (the pack's Cortex Analyst YAML would give wrong numbers):
1. **Delinquency and loss rates** now divide by **card** balances of the same product × segment × week. The pack divided across tables, with deposit balances included.
2. **Balances, active accounts and past-due balances** are end-of-week stocks: `NON ADDITIVE BY week`. The pack summed them across weeks.
3. **Rates** (rate paid, competitor rate, rate gap, revolve rate, FICO) are balance-weighted. The pack averaged them.
4. **Rolling dates.** The pack's "last 13 weeks from today" queries were going stale.
5. **Weeks are dated by week ending (Sunday).** A week counts as complete as soon as it is loaded, and it belongs to the month it ends in.

## Finance: Keystone Financial (`WBR_DB.FINANCE_DEMO`), build ready

**Scripts:** `setup\finance\`, mirroring `setup\retail\`. Run them with:

`cd /d "C:\Users\SharathKumarKammari\Downloads\snowflake-react-app-runtime\Analytics_Accelerator_Enterprise_Claude\setup\finance" && run_finance_setup.cmd`

One sign-in runs:
1. `01a_load_tables.sql`: schema, stage, raw tables with the pack's names.
2. A PUT of `data\*.csv`.
3. `01b_copy.sql`: COPY plus row-count check. Expected rows: 6, 6, 3744, 2496, 1248, 3120.
4. `02_views.sql`: `V_WEEK_SHIFT` and the rolling `SV_SRC_*` views (C_-prefixed columns, as in retail).
5. `03_semantic_view.sql`: `FINANCE_ANALYTICS_SV`, generated by `build_finance_sv.py`. It tries three definitions and keeps the richest one the account accepts: full, then without AI instructions, then without the stock metrics.
6. `04_validate.sql`: checks that
   - the rolling calendar ends last Sunday;
   - the semantic view totals equal the base tables;
   - ending balance equals the latest week (not a sum);
   - the three planted stories show up.
7. `05a`/`05b`: the ontology loaded into document search as `FINANCE_DOCS_SEARCH`, plus a metric glossary from the semantic view.

The log is saved to `finance_setup_log.txt`. `99_teardown.sql` drops the schema.

**Semantic view**

| Part | Contents |
|---|---|
| Tables | `weeks`, `products`, `segments`, `portfolio`, `credit` (cards only), `deposits` (deposits only), `acquisition` |
| Portfolio metrics | ending balance\*, active accounts\*, average balance, new / closed accounts, attrition rate, purchase volume, interchange revenue, rewards expense, rewards-to-interchange ratio, net interest income, cost of funds, NIM, cost-of-funds rate, revolve rate |
| Credit metrics | 30 / 60 / 90 days-past-due balances\*, delinquency rate, gross / net charge-offs, recoveries, annualised loss rate, recovery rate, average FICO |
| Deposit metrics | deposit balance\*, runoff, new money, net new money, maturing dollars, runoff rate, maturity concentration, rate paid, competitor rate, rate gap |
| Acquisition metrics | marketing spend, applications, approvals, bookings, approval rate, booking rate, cost per booking, average initial credit line |
| Dimensions | week ending (time), week start, month, quarter, year, ISO week, product, product type, tier, segment, credit tier, channel |

\* End-of-week stock (`NON ADDITIVE BY week`).

**Planted stories** (checked against the CSVs, latest 4 weeks)
- **F2:** Near-Prime Revolver delinquency rises from 5.6% to 8.7%; other segments are flat.
- **F1:** Mass Affluent Saver is the only segment with a positive rate gap (+0.07 pts). Its deposits are down 12.9% over 15 weeks, against −1% to +4% for the others.
- **F3:** Travel Signature rewards-to-interchange is 1.04, above the 0.85 breach line; the other cards are about 0.71.

**App support (done):**
- workspace renamed to Keystone Financial, with its featured view and its document search;
- agent sample questions come from the ontology personas;
- a weekly dataset is detected automatically, so the daily operations view shows weekly points;
- the "week ending" time dimension is recognised;
- money formatting covers balance, volume, income, expense, charge-offs, runoff and similar names, in dashboards and alert emails.

**Finance status:**
1. Setup run on 21 Oct: all checks OK. The semantic view was first created without AI instructions; fixed, re-run with `run_finance_sv.cmd`.
2. **Layout pack (done, `domain_packs.py`):**
   - Executives: Portfolio brief (default), Risk & return.
   - Managers: Credit risk watch, Deposits & pricing, Card economics, Acquisition funnel (the 4 ontology personas).
   - Operations: Weekly watchlist.
   - The question picks the layout by keywords ("delinquency" → Credit risk watch); Cortex chooses among the pack; generic layouts stay as alternatives.
3. **Suggested alerts (done):** 5 from the alert library in My alerts, one click to a pre-filled form. Where the library uses a 13-week average, the template says which comparison it uses instead.
4. **Done:** lead metric is ending balance (not bookings); tidy metric labels; weekly data offers week/month alerts only.
5. **Later:** validation checks from the gotchas (credit metrics only on card products); 30→60 roll rate (needs the prior week).

## CPG: Apex Athletic (`WBR_DB.CPG_DEMO`), built 22 Oct

**Run:** `cd /d "C:\Users\SharathKumarKammari\Downloads\snowflake-react-app-runtime\Analytics_Accelerator_Enterprise_Claude\setup\cpg" && run_cpg_setup.cmd` (log `cpg_setup_log.txt`; view only: `run_cpg_sv.cmd`).

- Sell-in and sell-through have the same grain (week × account × product, 1:1), so they are **one source**: sell-through ratio (POS units / shipped units) and weeks of supply (average on-hand / average weekly POS units) are exact.
- Fixes to the pack YAML: on-hand units NON ADDITIVE BY week; gross margin %, fill rate, OTIF, ACV distribution and promo ROI weighted (the pack averaged them).
- Metrics: net / gross sales, trade spend and rate, margin $ and %, ASP, returns and rate, fill rate, OTIF, DTC mix, off-price mix, POS units / dollars, sell-through ratio, on-hand, weeks of supply, ACV distribution, retail price, promotions (count, spend, incremental revenue, ROI, lift).
- Checks: rolling calendar, 1:1 match, totals = base tables, on-hand = latest week, and stories C1 (off-price +60%, margin 47% → 41%), C2 (Running Shoes sell-in +10% vs sell-through −11%, weeks of supply 12 → 20), C3 (Womens Leggings DTC +30% vs wholesale +5%), checked against the CSVs.
- Layout pack: Commercial brief, Sell-in vs sell-through (executives); Account health, Trade & promotions, Brand & category, Supply & service (managers = the 4 ontology personas); Weekly watchlist.
- Suggested alerts: inventory bloat (weeks of supply > 14), off-price diversion, margin erosion, fill rate < 95%, OTIF < 90%, returns > 6%.
- **Data:**
  - Sell-in by week × account × product: shipped units, gross / net sales, trade spend, margin, returns, fill rate and on-time-in-full (OTIF).
  - Sell-through by the same keys: store sales (POS), retailer on-hand units, weeks of supply, distribution (ACV %).
  - Trade promotions, plus product and customer dimensions.
- **Planted stories:**
  - C1: off-price channel surge;
  - C2: channel stuffing on Running Shoes (sell-in up while sell-through falls);
  - C3: direct-to-consumer (DTC) shift in Womens Leggings.
- **Check the CPG YAML for the same kinds of errors.** Weeks of supply and on-hand units are stocks, and rates are weighted.

## Open questions and risks

- **Privileges:** WBR_OWNER must be able to `CREATE SCHEMA` in WBR_DB (it did for RETAIL_DEMO), create Cortex Search services, and PUT to an internal stage.
- **Unverified DDL:** the semantic view DDL follows the retail syntax that worked live, but this exact definition has not run yet. The fallback attempts and the log cover that.
- **Install package:** domain schemas are hard-coded in domains.py. Template them for other accounts later.
