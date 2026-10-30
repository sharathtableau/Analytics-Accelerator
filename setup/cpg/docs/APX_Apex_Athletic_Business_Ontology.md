# Apex Athletic — CPG / Branded Manufacturer Domain Ontology

> Context document for INFERA on Snowflake. Load into Knowledge Hub (Cortex Search)
> and use as the business-definition source for the Cortex Analyst semantic view.
> **All data is synthetic.** Apex Athletic is a fictional athletic apparel brand.

## 1. Company context

Apex Athletic designs and sells athletic apparel, footwear and accessories. Annual
net revenue is approximately $1.1B. It sells through **two routes to market**:

- **Wholesale** — eight retail partners (national sporting chains, mass retail,
  department stores, specialty, off-price, team dealers, pure-play ecommerce,
  international distribution)
- **DTC** — Apex.com and owned retail stores

**The central analytical tension in this business is sell-in versus sell-through.**
Sell-in is what Apex ships to a retail partner and books as revenue. Sell-through
is what the consumer actually buys off that partner's shelf. When sell-in runs
ahead of sell-through, inventory accumulates in the channel. That inventory
eventually comes back as markdown pressure, off-price diversion, cancelled future
orders, or returns. **A quarter can look excellent on sell-in and be
simultaneously destroying next quarter.** Detecting that divergence early is the
single most valuable thing this domain does.

## 2. Personas

### 2.1 National Account Manager
**Owns:** the commercial relationship with one or more retail partners.
**Core decision:** what to ship, what to hold, and what to negotiate with the
account this week.
**Cadence:** weekly account review; monthly joint business planning.
**Triggers:** sell-through falling while sell-in holds, retailer weeks-of-supply
rising, fill rate complaints, off-price diversion.
**Primary metrics:** sell-in net sales, sell-through POS dollars and units,
sell-through ratio, retailer weeks of supply, ACV distribution, fill rate, OTIF,
trade spend as % of sales, returns rate.
**Typical actions:** hold or re-phase a shipment, negotiate markdown support,
escalate a fill rate problem, propose a joint promotion.

### 2.2 Revenue Growth Manager (Trade Marketing)
**Owns:** trade promotion spend and its return.
**Core decision:** which promotions to repeat, resize or kill next cycle.
**Cadence:** post-event review weekly; cycle planning monthly or quarterly.
**Triggers:** promo ROI below threshold, volume lift below breakeven, trade spend
rate drifting up without revenue response.
**Primary metrics:** promo ROI %, volume lift %, incremental revenue, trade spend
rate, baseline vs incremental volume, average selling price, price gap to
competition.
**Typical actions:** cut a promotion, shift spend between accounts or mechanics,
renegotiate promotional calendar.

### 2.3 Brand / Category Director
**Owns:** a product line's revenue and margin.
**Core decision:** where to invest, what to discontinue, how to price.
**Cadence:** monthly, with quarterly range reviews.
**Triggers:** gross margin decline, DTC/wholesale mix shift, ASP erosion,
category losing distribution.
**Primary metrics:** net revenue by product, gross margin %, DTC mix %, ASP,
revenue mix, ACV distribution, sell-through velocity, returns rate.
**Typical actions:** reprice, reallocate marketing, discontinue a style, shift
channel emphasis.

### 2.4 Demand & Supply Planner
**Owns:** forecast accuracy and service level.
**Core decision:** what to produce and where to position it.
**Cadence:** weekly S&OP cycle.
**Triggers:** fill rate below target, OTIF slipping, channel inventory out of
band, forecast error rising.
**Primary metrics:** fill rate %, OTIF %, weeks of supply in channel, shipped
units, forecast error, returns units, order cycle variability.
**Typical actions:** expedite, re-phase production, rebalance across accounts.

## 3. Metric dictionary

| # | Metric | Definition / formula | Grain | Good direction |
|---|---|---|---|---|
| 1 | Gross sales | `SUM(gross_sales)` before trade | customer × product × week | Up |
| 2 | Trade spend | `SUM(trade_spend)` | customer × product × week | Band |
| 3 | Net sales (sell-in) | `gross_sales − trade_spend` | customer × product × week | Up |
| 4 | Trade spend rate % | `trade_spend / gross_sales × 100` | any | Down |
| 5 | Shipped units | `SUM(shipped_units)` | customer × product × week | Up |
| 6 | Gross margin % | `gross_margin_pct`, weight by net sales | any | Up |
| 7 | Average selling price | `gross_sales / shipped_units` (wholesale price) | customer × product | Band |
| 8 | Returns rate % | `return_dollars / gross_sales × 100` | any | Down |
| 9 | Fill rate % | Units shipped ÷ units ordered | customer × week | Up |
| 10 | OTIF % | On time and in full delivery rate | customer × week | Up |
| 11 | POS dollars (sell-through) | `SUM(pos_dollars)` at retail | customer × product × week | Up |
| 12 | POS units (sell-through) | `SUM(pos_units)` | customer × product × week | Up |
| 13 | **Sell-through ratio** | `pos_units / shipped_units` over matched period | customer × product | Band: 0.9–1.1 |
| 14 | Retailer weeks of supply | `retailer_on_hand_units / 4-wk avg pos_units` | customer × product | Band: 6–12 |
| 15 | ACV distribution % | % of all-commodity-volume carrying the item | product × customer | Up |
| 16 | Average retail price | `pos_dollars / pos_units` | customer × product | Band |
| 17 | Retail price gap % | Our retail price vs category average | product | Band |
| 18 | DTC mix % | DTC net sales ÷ total net sales | product / total | Up |
| 19 | Promo ROI % | `(incremental_revenue − trade_spend) / trade_spend × 100` | promo event | Up |
| 20 | Volume lift % | Promo volume vs non-promo baseline | promo event | Up |
| 21 | Channel inventory value | `retailer_on_hand_units × ASP` | customer | Band |
| 22 | Off-price mix % | Off-price channel net sales ÷ total | total | Down |

**Aggregation rules.** Sell-through ratio must be computed on summed units over a
matched window, never averaged across weekly ratios. Margin % weights by net sales.
Weeks of supply uses a 4-week trailing average of POS units as denominator.

## 4. Table dictionary

### `CPG_FACT_SELLIN_WEEK`
Grain: customer × product × week. 12,480 rows. What Apex ships and books.

`week_start_date`, `fiscal_year`, `fiscal_week`, `customer_id`, `product_id`,
`shipped_units`, `gross_sales`, `trade_spend`, `net_sales`, `gross_margin_pct`,
`return_units`, `return_dollars`, `avg_selling_price`, `fill_rate_pct`,
`otif_pct`, `promo_flag`.

### `CPG_FACT_SELLTHROUGH_WEEK`
Grain: customer × product × week. 12,480 rows. What consumers buy at retail.

`week_start_date`, `customer_id`, `product_id`, `pos_units`, `pos_dollars`,
`retailer_on_hand_units`, `weeks_of_supply`, `acv_distribution_pct`,
`avg_retail_price`, `retail_promo_flag`.

### `CPG_FACT_TRADE_PROMO`
Grain: one row per promotion event. 140 rows.
`promo_id`, `week_start_date`, `duration_weeks`, `customer_id`, `product_id`,
`promo_type`, `trade_spend`, `incremental_revenue`, `volume_lift_pct`,
`promo_roi_pct`.

### `CPG_DIM_PRODUCT`
12 rows. `product_id`, `product_name`, `product_category`, `gender_segment`,
`revenue_mix_pct`, `target_gross_margin_pct`, `seasonality_index`, `msrp_usd`.

### `CPG_DIM_CUSTOMER`
10 rows. `customer_id`, `customer_name`, `channel` (Wholesale / DTC),
`region_scope`, `revenue_mix_pct`, `payment_terms_days`.

**Joins.** Sell-in and sell-through join on
`customer_id + product_id + week_start_date`. Both join to the two dimensions.

## 5. Suggested questions by persona

**National Account Manager**
- Which accounts have sell-in growing while sell-through declines?
- Show retailer weeks of supply by account and product, flag anything above 12.
- What is my fill rate by account over the last 13 weeks?
- How much trade spend am I giving each account as a percent of gross sales?

**Revenue Growth Manager**
- Rank promotions by ROI over the last two quarters.
- Which promo types underperform, and with which accounts?
- Where is trade spend rate rising without a revenue response?

**Brand / Category Director**
- Which product lines are losing gross margin and why?
- How is the DTC versus wholesale mix shifting by product?
- Which products are losing ACV distribution?

**Demand & Supply Planner**
- Where is fill rate below 95% and what is the revenue at risk?
- Which account and product combinations have channel inventory out of band?
- Show order cycle variability by account.

## 6. Alert library

| Alert | Rule | Severity | Owner |
|---|---|---|---|
| Sell-in / sell-through divergence | Sell-in up > 10% while sell-through down > 5% over 13 weeks | Critical | Account Manager |
| Channel inventory bloat | Retailer weeks of supply > 14 for 3 consecutive weeks | Critical | Account Manager |
| Off-price diversion | Off-price mix up > 30% over 13 weeks | Critical | Brand Director |
| Fill rate breach | Fill rate < 95% for 2 consecutive weeks | Warning | Planner |
| OTIF breach | OTIF < 90% for 2 consecutive weeks | Warning | Planner |
| Promo ROI failure | Promo ROI < 0% on spend above $100k | Warning | RGM |
| Trade spend drift | Trade spend rate up > 2pts over 8 weeks | Warning | RGM |
| Margin erosion | Gross margin % down > 3pts over 13 weeks | Critical | Brand Director |
| Distribution loss | ACV distribution down > 5pts | Warning | Brand Director |
| Returns spike | Returns rate > 6% of gross sales | Warning | Account Manager |

## 7. Business rules and gotchas

- **Revenue means sell-in.** When a finance user says "revenue", they mean
  `net_sales` from the sell-in table. When a commercial user says "how are we
  selling", they usually mean sell-through POS. Clarify which is meant.
- **Sell-in is lumpy, sell-through is smooth.** Wholesale ships on order cycles
  roughly every four weeks. Never read a single week of sell-in as a trend; use a
  4-week or 13-week window.
- **DTC has no divergence.** For DTC customers sell-in and sell-through are the
  same event, so sell-through ratio is ~1.0 by construction. Exclude DTC when
  analysing channel inventory health.
- **Trade spend is already deducted** from net sales. Do not subtract it again.
- **Off-price is a symptom, not a channel strategy.** Rising off-price volume
  usually indicates excess inventory being cleared, and it carries materially
  lower margin. Treat growth there as a warning, not a win.
- **ACV is a distribution measure, not a sales measure.** It can rise while sales
  fall, which indicates a velocity problem rather than a listing problem.
