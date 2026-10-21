# Demo script — 15 minutes · Snowflake, Thu 8 Oct 2026

Pitch: **every click is carried by a named Snowflake AI feature.** Say the feature name each time.
Data: Harborline Outfitters (fictional US retailer), `WBR_DB.RETAIL_DEMO`, one semantic view, live feed.
Status of each step is tracked in ENTERPRISE_TRACKER.md (F section).

## Before the room (T-30 min)
- [ ] Open the app once; open each page of the dashboard you will show (warms caches).
- [ ] Ask the agent one question so the shared agent exists (first run creates/upgrades it).
- [ ] Snowflake Intelligence tab open with the same agent.
- [ ] Backup video ready.

## 0:00 — Frame (1 min)
"A partner-built dashboard product that lives entirely inside Snowflake. No extract, no second BI tool.
Every step you'll see is a Snowflake AI feature doing the work."

## 1:00 — Home: same data, three audiences (1 min) · *Cortex AI_COMPLETE + semantic views*
1. Point at "Your data" under the prompt bar (what this role can ask about), then click the Manager line under
   "Try asking": the request lands in the box, edit a word live, and send. Say: "a typed request works the same way."
2. Point at the ideas: "Cortex read the semantic views this role can see and proposed dashboards per audience:
   Executive, Manager, Operations."
3. Say: "Each audience gets a reviewed layout — its own question, time grain and density. Cortex chooses which
   governed metrics fill each slot; the validator certifies every tile."

## 2:00 — Operations: live control room (2 min) · *SEMANTIC_VIEW() on live data*
1. Open **Operations · live operations today**. Review shows the fixed layout + Cortex's metric picks → Build.
2. Green Live strip: "today so far, compared with the same weekday last week at the same hour; refreshes every 5 minutes."
3. Today's pace by hour: the "now" line, the projection for the day.
4. Worklist: "what is off today vs a normal Thursday, worst first" → click **Ask agent** on the top row (carries into *Why?*).

## 4:00 — Executive: one-page brief (2 min) · *ML FORECAST + AI_AGG*
1. Home → **Executive brief**. No tabs, one page.
2. YTD vs plan cards with bullet bars ("tick = plan"); the "What changed and why" summary wrote itself (Cortex AI_AGG
   over the page's governed facts — open "show the governed facts").
3. Trajectory: cumulative year vs plan vs last year; the purple dashed line is **Snowflake ML FORECAST** to year end.

## 6:00 — Manager: scorecard & drill (1.5 min) · *semantic view relationships*
1. Home → **Manager scorecard**. Red/amber/green by region vs weekly plan.
2. Click the red row (Southwest) → the whole dashboard filters to it; Exceptions (Snowflake ML ANOMALY_DETECTION) → Drivers tab.
3. If time is short, skip this beat: the wireframes in `persona_wireframes.png` make the point.

## 7:30 — Why? (3 min) · *Cortex Agent = Cortex Analyst + Cortex Search*
1. On the exception tile click **Ask agent** on Boots (West): "Why is stockout rate for Boots above normal?"
2. Point at the answer: numbers from **Cortex Analyst** (SQL shown) + the cause from **Cortex Search** —
   cites **HLO-INV-008** (Pacific Stride allocation cut, Reno DC transfer).
3. Follow-up in the same thread: "When is it expected to recover?" → 20 Oct cycle (from the document).
4. Second story (optional): "Why did free shipping % drop this year?" → HLO-POL-014, threshold 99 → 119 USD, intended.
5. Say: "The PDFs were parsed in Snowflake with AI_PARSE_DOCUMENT, chunked, and indexed by Cortex Search."

## 10:30 — Decide (1.5 min) · *Snowflake tables*
1. **Log decision** from the answer: owner, due date, evidence pre-filled. Show Decisions count.
2. "The decision and its evidence live in a Snowflake table, next to the data."

## 12:00 — Share (1 min) · *Streamlit in Snowflake + RBAC*
1. Publish to role `EXEC_VIEWER` → open the viewer link: read-only, same governed numbers.

## 13:00 — Trust and cost (1 min) · *ACCOUNT_USAGE, AI ledger*
1. Governance drawer: every Cortex call logged with input, output, provenance, latency; Cortex usage from ACCOUNT_USAGE.
2. Layout decisions: what the validator kept, repaired or dropped from Cortex's design.

## 14:00 — Same agent everywhere (1 min) · *Snowflake Intelligence*
1. Switch to Snowflake Intelligence, ask the same agent: "Which region is furthest behind plan and why?"
   → Southwest ~88% (data) + three new stores, only Austin opened (HLO-FIN-003).
2. Close: roadmap slide — custom agent tools, auto-drafted semantic views, AI Observability, Native App.

## Stories in the data (for questions)
| Story | Data shows | Document |
|---|---|---|
| West footwear stockouts (Aug–Oct 2026) | Reno DC in-stock and lost sales for Boots, Sneakers, Running Shoes | HLO-INV-008 §5, WBR 10 Aug / 14 Sep / 28 Sep |
| Southeast USPS slowdown (from Aug 2026) | On-time % down, delivery days up for USPS in Southeast | HLO-OPS-022 §6, WBR 10 Aug / 24 Aug |
| Southwest plan miss (2026) | Plan attainment ~0.87–0.88 | HLO-FIN-003 §3, WBR 14 Sep |
| Free-shipping threshold 99 → 119 USD (1 Mar 2026) | Free shipping % down ~9 pts, AOV up | HLO-POL-014, WBR 24 Aug |

## If something fails live
- Agent slow/unavailable → use the ✦ tile panel answer already in the thread, or the backup video.
- Search not created yet → agent still answers numbers (Analyst only); tell the documents part from the table above.
