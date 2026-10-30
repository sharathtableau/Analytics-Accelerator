# Domain chart research, v2 (22 Oct 2026)

The question: are the v1 R&D charts useful for analysis? Answer: 6 of 18 were. They were rebuilt using how analysts in each industry actually work, and checked against the pack data (the INFERA CSVs). The numbers in the v2 boards are real values from that data.

## Self-audit of v1 (see RD2_audit.png)

| Chart | Verdict | Why |
|---|---|---|
| F1 Accounts roll-forward | Drop | "Other movement" is unexplained; a real roll-forward needs payments and purchases, which the pack does not have |
| F2 Delinquency by segment | Keep | Standard CCO view; add roll rates and age buckets |
| F3 Risk-return bubble | Change | Risk-adjusted yield bars: (net interest + interchange − rewards − net losses) ÷ balance |
| F4 Rate vs competitor lines | Change | The gap is invisible on a rate axis; diverging rate-gap bars plus balance change |
| F5 Rewards ratio vs breach | Keep | |
| F6 Acquisition funnel | Low value | Channels are nearly identical; keep cost per booking only |
| C1 Sell-in vs sell-through gap | Change | Cumulative channel-inventory build |
| C2 Weeks of supply band | Keep | |
| C3 Gross-to-net | Keep | |
| C4 Promo ROI by tactic | Change | Plot every event against the break-even line (averages hid 38 losing events) |
| C5 Distribution vs velocity scatter | Change | Bars splitting the sales change into a distribution effect and a velocity effect |
| C6 Channel mix area | Change | Sell-through ratio heatmap, account × product |
| R1 Traffic × conversion × basket | Keep | |
| R2 Region × category heatmap | Keep | |
| R3 Quadrant | Change | Margin change diverging bars |
| R4 Inventory index | Change | Sales vs on-hand (indexed) for the problem cell; weeks of supply vs last year |
| R5 Margin leakage | Drop | No markdown or shrink split in the data |
| R6 Fulfilment mix | Drop | No fulfilment data |

## What the data showed (checked)

- **Finance**
  - Near-Prime Revolver: 30→60 roll rate 46.5% → 51.8%, 60→90 roll rate 61.6% → 68.6%. Other segments are flat.
  - Risk-adjusted yield is negative for Near-Prime Revolver (−6.8%) and Subprime Builder (−11.0%).
  - Deposit rate gaps do not vary over time within a segment, so a deposit elasticity chart cannot be built from this data.
- **CPG**
  - Running Shoes consumer sales (POS) are down 17%, almost entirely from velocity (−$8.0M) rather than distribution (−$0.4M). All other lines grow 9–19%.
  - Running Shoes channel inventory has grown by +332K units in 26 weeks; its sell-through ratio is 0.68–0.75 at every account, against a typical 0.93.
  - 38 of 140 promotions lost money ($12.2M of trade spend). Lift and ROI barely move together (correlation −0.09).
  - Off-price share went from 7% to 13% of net sales while its gross margin fell from 47% to 38.5%.
- **Retail (pack sample)**
  - Southwest Apparel: sales index 71, on-hand index 101.
  - Toys & Seasonal weeks of supply went from 14 to 18.
  - Electronics margin is down 3.7 points.

## Industry practice behind the choices

- **Card risk:** delinquency by segment, roll (flow) rates, 30/60/90 ageing, loss rates, risk-adjusted yield (OCC Credit Card Lending handbook; Preditta).
- **CPG:** sales change = distribution (%ACV, TDP) × velocity; sell-through = sell-out ÷ sell-in; channel inventory = cumulative sell-in − sell-out (CPG Data Insights; Vxceed).
- **Trade promotion:** judge each event against break-even, not averages by tactic (Scout; Revology).
- **Deposits:** deposit beta needs a benchmark rate series (NY Fed; Teradata).
- **Retail:** comp-sales drivers, weeks of supply, stock-to-sales, GMROI (ERS Retail Math; 7thonline; SPS Commerce).

## Data gaps (do not promise these in a demo)

- Vintage curves and an account-level roll matrix need account-level data.
- Promo incrementality needs a modelled baseline.
- TDP needs item counts by store.
- Deposit beta needs a benchmark rate series (e.g. the Fed funds rate).
- Retail markdown, shrink and fulfilment splits are not in the data.

## Proposed new tile types for the app (smallest useful set)

1. **Driver decomposition bars:** split the change into its drivers (traffic × conversion × basket; distribution vs velocity).
2. **Diverging bars vs a reference:** margin change, rate gap, risk-adjusted yield.
3. **Dumbbell, now vs a year ago:** roll rates, weeks of supply.
4. **Diverging heatmap:** region × category growth; sell-through ratio by account × product.
5. **Event scatter with a break-even line:** promotions.
6. **Cumulative build line:** channel inventory.

These reuse existing building blocks (bar, line, heatmap, scatter) with new settings, so no new chart library is needed.
