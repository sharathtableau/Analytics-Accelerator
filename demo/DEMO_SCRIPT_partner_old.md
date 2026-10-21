# Demo script: Snowflake partner session, Tuesday 6 October 2026

**Audience:** Snowflake partners (SIs and consultancies). They want to know what they can deploy at their clients, how fast, and which Snowflake features it uses.
**Pitch line:** a dashboard product that lives entirely inside the client's Snowflake account, where every step is carried by a named Snowflake AI feature.
**Format, about 30 minutes:** slides 1–4 (4 min) → live demo (15 min) → slides 5–10 (6 min) → questions (5 min).
**Deck:** `Analytics_Accelerator_Partner_Deck.html` (Blend format; opens in any browser, works offline). Arrow keys or Space to move; End jumps to the last slide.
**Data:** Harborline Outfitters (fictional US retailer), `WBR_DB.RETAIL_DEMO.RETAIL_ANALYTICS_SV`, with planted stories (see the end of this script).

> This script follows the slimmer Home and dashboard header (starter buttons, one "Your data" line, one-line dashboard header). If that version is not deployed, the same steps work: use the "Try asking" list instead of the starter buttons.

---

## Monday: get ready (about 1 hour)

1. Deploy the latest build from a Command Prompt:
   ```
   cd /d "C:\Users\SharathKumarKammari\Downloads\snowflake-react-app-runtime\Analytics_Accelerator_Enterprise_Claude" && deploy_enterprise.cmd
   ```
   Expect "Ran … tests … OK", then the app URL.
2. Run the playbook's test round (R1–R21) and fix or drop anything that fails. Anything still failing comes out of the demo path below.
3. Rehearse the full flow once with a timer, then record it (backup video).
4. Pick the dashboard you'll open in the demo and **Save draft** it once, so you can reopen it if a build is slow.

## Tuesday: 30 minutes before

- [ ] Open Snowsight with role **WBR_OWNER** and warehouse **POWERHOUSE**; make sure the warehouse is running.
- [ ] Open the app: Snowsight → Projects → Streamlit → **ANALYTICS_ACCELERATOR_ENTERPRISE** (or the URL from the deploy).
- [ ] Warm the caches: build the Executive brief, the Manager scorecard and Live operations once each.
- [ ] Ask the agent one question, so the shared agent exists with its tools: "Why is stockout rate for Boots above normal?"
- [ ] Open the deck in a second browser tab, full screen (F11).
- [ ] Browser zoom 90–100%; close other tabs; notifications off.
- [ ] Backup video ready on the desktop.

---

## The session

### 0:00 · Slides 1–3 (3 min)

- **Slide 1, cover:** "Thanks for the time. In the next half hour we'll show a dashboard product that runs entirely inside the client's Snowflake account, where every step you see is a Snowflake AI feature doing the work."
- **Slide 2, what we see at clients:** "You see this at every client: the data is in Snowflake, but dashboards, metric logic and AI live in other tools. Snowflake now has everything to bring that layer in: semantic views, Cortex, Snowflake ML and Cortex Agents."
- **Slide 3, the accelerator:** walk the four boxes left to right: reads semantic views, Cortex designs, Snowflake computes, the agent explains and acts. "Nothing leaves the account; the client's roles decide what each person sees."

### 0:03 · Slide 4, "Live demo" → switch to the app (1 min)

- "Harborline is a fictional retailer: one semantic view, live data."

### 0:04 · Home: ask (2 min) · *Cortex AI_COMPLETE + semantic views*

1. Point at the box: "A business user starts here, in plain English."
2. Open **Harborline Retail · metrics · live ▾**: "Cortex read every semantic view this role can see. This is the governed data it can answer from." Close it.
3. Point at the ideas: "Ideas per audience, each on a different metric theme. ↻ New ideas brings themes that aren't on screen yet."
4. Click the **Live operations** starter. The request appears in the box. Edit one word live, then press send.
   Say: "Nothing is built until I send. Cortex AI_COMPLETE picks the governed data and the audience, and the metrics I named lead the dashboard."

### 0:06 · Review and Live operations (3 min) · *SEMANTIC_VIEW() on live data*

1. **Review:** "A reviewed layout for operations; Cortex filled the slots, and a validator certified every tile. I can add or remove metrics and redesign." Click **Build dashboard**.
2. **Live strip:** "Today so far, compared with the same weekday last week at the same hour; it refreshes every 5 minutes."
3. **Today's pace by hour:** the "now" line and where the day is heading.
4. **Worklist:** "What is off today against a normal day, worst first." Click **Ask agent** on the top row.

### 0:09 · Why? (3 min) · *Cortex Agent = Cortex Analyst + Cortex Search*

1. Agent question: "Why is stockout rate for Boots above normal?"
2. Point at the answer: numbers from **Cortex Analyst** (SQL shown) and the cause from **Cortex Search**, citing **HLO-INV-008** (Pacific Stride allocation cut, Reno DC transfer).
3. Follow-up in the same thread: "When is it expected to recover?" → the 20 October cycle, from the document.
4. Say: "The policy PDFs were parsed in Snowflake with AI_PARSE_DOCUMENT, chunked, and indexed by Cortex Search."

### 0:12 · Decide (1 min) · *agent tool log_decision → Snowflake table*

1. Ask the agent: "Log a decision: expedite the Reno DC transfer, owner Maria, due Friday."
2. Show the "Logged in Snowflake by the agent" card and the Decisions count. "The decision and its evidence sit in a Snowflake table next to the data."
   (Fallback: use **Log decision** on the worklist row.)

### 0:13 · Executive brief (3 min) · *Snowflake ML FORECAST + AI_AGG*

1. Home → **Executive brief** starter → send → Build.
2. Header: "One line tells you the data, the period and that the layout is validated."
3. **What changed and why** wrote itself: "Cortex AI_AGG over this page's governed facts; open 'show the governed facts' to see exactly what it read."
4. **Year to date vs plan:** switch **Bars → Arrows → Table** in the tile header. "Same numbers, three views; nothing is re-queried."
5. **Trajectory:** the purple dashed line is **Snowflake ML FORECAST** to year end.
6. Optional, if time: Manager scorecard → click the red Southwest row to drill (plan miss, HLO-FIN-003).

### 0:16 · Share and govern (2 min) · *RBAC, AI Observability, ACCOUNT_USAGE*

1. **Publish** to a viewer role → open the viewer link: read-only, same governed numbers.
2. **Governance & AI quality:** every Cortex call logged; agent evaluations (answer correctness, tool choice, citations); cost by app feature.

### 0:18 · Back to the deck, slides 5–10 (6 min)

- **Slide 5, the stages:** recap what they just saw, stage by stage, naming the Snowflake feature each time.
- **Slide 6, three audiences:** "One governed source, three dashboards with their own question and time grain."
- **Slide 7, the agent:** one agent per dataset, three tools, asked from anywhere; next, Snowflake Intelligence.
- **Slide 8, trust:** one metric definition, validator, roles, AI log, agent evaluations, cost by feature.
- **Slide 9, for partners:** deploy with one script, start from their semantic views (or draft one from a table), configure without code, and every step runs on Cortex, Snowflake ML and Cortex Agents in the client's account.
- **Slide 10, today and roadmap:** be precise. Anything you didn't show live today, say "built and being verified".

### 0:24 · Slide 11, questions (5 min)

---

## Questions partners are likely to ask

| Question | Answer |
|---|---|
| What does a client need? | A Snowflake account with Cortex and Snowflake ML available in its region, Streamlit in Snowflake (container runtime), a warehouse, and a role with access to their semantic views. |
| What if they have no semantic views? | Connect a table: Cortex drafts the semantic view from a profile of the columns, a person reviews it, and the app creates it. Views with facts but no metrics also work; Cortex drafts the metrics. |
| How is it deployed? | Snowflake CLI and one deploy script into the client's account; the tests run first. Nothing is hosted outside Snowflake. |
| Which models? | Cortex AI_COMPLETE with the first available of claude-sonnet-4-5, llama3.3-70b, mistral-large2 (set in one config file). |
| Can AI change the numbers? | No. Every number comes from SEMANTIC_VIEW() on the governed model; Cortex only chooses fields and layouts, and a validator checks every choice. |
| Security? | Runs under Snowflake roles; dashboards are published read-only to roles. Row-level security per viewer role is on the roadmap. |
| Cost? | Every query carries a query tag; Governance shows credits by feature from ACCOUNT_USAGE. |
| Native App or Marketplace? | On the roadmap. Today it deploys as a Streamlit app in the client's account. |
| Can it run in Snowflake Intelligence? | The agent is a standard Cortex Agent, so it can be added there; that step is next on the roadmap. |

## If something fails live

- **Build is slow:** open the draft you saved on Monday from "Continue where you left off".
- **Agent slow or unavailable:** use the ✦ answer already in the tile's panel, or play the backup video for that part.
- **Search not answering:** the agent still gives the numbers (Analyst); tell the document part from the table below.
- **Anything else:** switch to the deck and continue from slide 5.

## Stories in the data

| Story | What the data shows | Document |
|---|---|---|
| West footwear stockouts (Aug–Oct 2026) | Reno DC in-stock and lost sales for Boots, Sneakers, Running Shoes | HLO-INV-008 §5, WBR 10 Aug / 14 Sep / 28 Sep |
| Southeast USPS slowdown (from Aug 2026) | On-time % down, delivery days up for USPS in the Southeast | HLO-OPS-022 §6, WBR 10 Aug / 24 Aug |
| Southwest plan miss (2026) | Plan attainment about 0.87–0.88 | HLO-FIN-003 §3, WBR 14 Sep |
| Free-shipping threshold 99 → 119 USD (1 Mar 2026) | Free shipping % down about 9 pts, AOV up | HLO-POL-014, WBR 24 Aug |
