# Demo guide — planted signals

> **Internal. Do not load into Knowledge Hub and do not share with clients.**
> Every signal below was deliberately engineered into the synthetic data so a
> demo has something real to find. Verified present and isolated to a single
> segment or region in each case.

## Why this matters

A demo fails when the agent answers correctly and the answer is boring. Each
dataset therefore contains two or three genuine anomalies with a traceable cause,
so the agent can go from *detection* → *root cause* → *recommended action* on
live data rather than a scripted path.

## Retail — MeridianMart

| ID | Signal | Where | Window | Verified |
|---|---|---|---|---|
| R1 | Apparel sales collapse | Southwest region only | Last 14 weeks | −11.7% vs prior 13 wks; all other regions +4.7% to +7.1% |
| R2 | Electronics margin erosion | Company-wide | Last 20 weeks | 17.8% → 14.8% (−3.0 pts) |
| R3 | Toys & Seasonal over-buy | Midwest region only | Last 18 weeks | On-hand units +54.4%; other regions +4.8% to +12.6% |

**R1 has a deliberate second layer:** Southwest apparel inventory also rises 55%
over the same window. So the correct read is *not* "demand fell" alone — it is
"demand fell and we kept shipping", which is a markdown exposure problem. A good
agent answer separates the two.

### Category Manager demo script
1. *"Where is gross margin eroding fastest over the last 13 weeks?"* → finds R2
2. *"Which regions are underperforming in Apparel?"* → finds R1
3. *"Is that demand or inventory?"* → surfaces the inventory build
4. *"What's my markdown exposure in Southwest Apparel?"* → quantifies it
5. Investigate → scenario: markdown depth vs margin impact

## CPG — Apex Athletic

| ID | Signal | Where | Window | Verified |
|---|---|---|---|---|
| C1 | Off-price channel surge | Off-Price Channel (CUS-05) | Last 16 weeks | Net sales +79.8% vs +13.5%/+15.3% for other majors; margin −9 pts |
| C2 | **Channel stuffing** | Running Shoes (SKU-107), wholesale | Last 18 weeks | Sell-in units +17.5% while sell-through −7.5%; weeks of supply 10.6 → 15.2 |
| C3 | DTC demand shift | Womens Leggings (SKU-104) | Last 20 weeks | DTC net sales +42% while wholesale flat |

**C2 is the strongest demo moment in the whole dataset.** It is the exact failure
mode no dashboard catches, because sell-in looks healthy in isolation — revenue is
up. Only the divergence reveals the problem, and the consequence (C1, excess
inventory diverted to off-price at a 9-point margin hit) is visible in the same
data. The two signals connect causally.

### National Account Manager demo script
1. *"Which accounts have sell-in growing while sell-through declines?"* → C2
2. *"Show me weeks of supply for Running Shoes by account"* → confirms the build
3. *"What happened to off-price volume over the same period?"* → C1
4. *"What's the margin impact?"* → −9 pts quantified
5. Investigate → scenario: hold shipments vs markdown support

## Finance — Keystone Financial

| ID | Signal | Where | Window | Verified |
|---|---|---|---|---|
| F1 | Deposit runoff | Mass Affluent Saver (SEG-05) | Last 15 weeks | Balance −6.4% vs +0.8% to +1.6% all other segments |
| F2 | Credit deterioration | Near-Prime Revolver (SEG-03) | Last 22 weeks | Delinquency 5.84% → 7.93%; all other segments flat |
| F3 | Rewards cost breach | Travel Signature Card (PRD-02) | Last 18 weeks | Rewards/interchange 0.749 → 0.943 vs 0.720 → 0.723 for Cash Rewards |

**F1 carries its own cause in the data.** SEG-05 is the only segment with a
*positive* rate gap (+0.07) — meaning competitors pay more than Keystone does.
Every other segment sits at −0.15. So the agent can answer "why" without
speculation, and the recommended action (a rate exception) has a costable size.

**F3 crosses a documented threshold.** The alert library sets the rewards-to-
interchange breach at 0.85; PRD-02 is at 0.943. That lets the demo show an alert
firing against a governed business rule rather than an arbitrary number.

### Head of Retail Deposits demo script
1. *"Which segments are losing balances fastest?"* → F1
2. *"What's the rate gap for that segment?"* → +0.07, the only positive one
3. *"How much would a 25bp exception cost annually?"* → sizes the fix
4. Investigate → scenario: exception cost vs balance retained

### Chief Credit Officer demo script
1. *"Which segments show deteriorating delinquency?"* → F2
2. *"Show roll rates from 30 to 60 DPD for that segment"*
3. *"Is average FICO drifting?"*
4. *"What's the annualised loss rate versus the rest of the book?"*

## Running the demo well

- **Lead with the question, not the screen.** Open on the chat, type the persona's
  real Monday question, let the portfolio assemble itself.
- **Always do the second question.** Detection is unimpressive; root cause is the
  product. The signals above are built so question two has a real answer.
- **End on the action.** Each script finishes at a decision with a number attached.
  That is the part a buyer remembers.
- **Don't demo all three domains.** Pick the one matching the client's industry.
  Breadth reads as generic, which is the feedback that started this work.
