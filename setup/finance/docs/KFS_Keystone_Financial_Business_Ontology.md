# Keystone Financial — Consumer Banking Domain Ontology

> Context document for INFERA on Snowflake. Load into Knowledge Hub (Cortex Search)
> and use as the business-definition source for the Cortex Analyst semantic view.
> **All data is synthetic.** Keystone Financial is a fictional consumer bank.
> Nothing here is financial advice or a real institution's results.

## 1. Company context

Keystone Financial is a consumer-focused bank with roughly **$26B in managed
balances** across two businesses:

- **Credit cards** — four products: Cash Rewards, Travel Signature (premium),
  Secured (credit building), Small Business
- **Retail deposits** — High-Yield Savings and 12-Month CDs

Customers are grouped into six behavioural segments crossing credit quality and
product usage. The economics of the two businesses pull in opposite directions
when rates move: **falling benchmark rates compress deposit spread but reduce
funding cost for the card book.** Managing that tension is the core of the weekly
and monthly rhythm.

**Cadences.** Weekly portfolio watchlist. Monthly pricing committee (deposit rates
and card rate exceptions). Monthly credit review. Quarterly reserve setting.

## 2. Personas

### 2.1 Head of Retail Deposits
**Owns:** deposit balances, deposit pricing and cost of funds.
**Core decision:** which segments get a rate exception or retention offer, and at
what cost.
**Cadence:** weekly runoff watchlist, monthly pricing committee.
**Triggers:** balance runoff accelerating, rate gap to competitors turning
unfavourable, CD maturity concentration approaching.
**Primary metrics:** deposit balance, runoff rate, net new money, rate paid, rate
gap to competition, cost of funds, maturity concentration, attrition rate.
**Typical actions:** approve a rate exception for a segment, launch a retention
campaign, re-price a CD tenor, escalate to ALCO.

### 2.2 Head of Card Portfolio (P&L owner)
**Owns:** card revenue, rewards cost and portfolio profitability.
**Core decision:** where to push spend, where to tighten rewards, which products
are earning their keep.
**Cadence:** weekly performance review, monthly P&L.
**Triggers:** rewards cost outrunning interchange, revolve rate shifting, purchase
volume softening, NIM compression.
**Primary metrics:** ending balance, purchase volume, interchange revenue, rewards
expense, rewards-to-interchange ratio, net interest income, net interest margin,
revolve rate, cost of funds, active accounts.
**Typical actions:** adjust a rewards structure, change spend-category bonuses,
reprice, shift marketing emphasis between products.

### 2.3 Chief Credit Officer
**Owns:** credit quality and loss performance.
**Core decision:** where to tighten underwriting or line assignment, and what to
reserve.
**Cadence:** weekly delinquency watch, monthly credit review, quarterly reserves.
**Triggers:** delinquency rate rising in a segment, roll rates deteriorating, loss
rate above plan, FICO mix drifting.
**Primary metrics:** delinquency rate, 30/60/90 DPD balances, roll rate, gross and
net charge-off dollars, annualised loss rate, recovery rate, average FICO,
provision expense.
**Typical actions:** tighten a segment's credit box, reduce line assignments,
increase provision, pause a marketing channel feeding poor credit.

### 2.4 Head of Acquisition Marketing
**Owns:** new account growth and acquisition efficiency.
**Core decision:** where to spend next month's acquisition budget.
**Cadence:** weekly channel performance, monthly budget allocation.
**Triggers:** cost per booking rising, approval rate falling, a channel delivering
poor downstream credit.
**Primary metrics:** marketing spend, applications, approval rate, booking rate,
cost per booking (CAC), new accounts, average initial credit line, spend by
channel.
**Typical actions:** shift budget between channels, pause a channel, adjust
targeting, revise offer terms.

## 3. Metric dictionary

| # | Metric | Definition / formula | Grain | Good direction |
|---|---|---|---|---|
| 1 | Ending balance | `SUM(ending_balance)` | product × segment × week | Up |
| 2 | Active accounts | `SUM(active_accounts)` | product × segment × week | Up |
| 3 | New accounts | `SUM(new_accounts)` | product × segment × week | Up |
| 4 | Attrition rate % | `closed_accounts / active_accounts × 100` annualised | product × segment | Down |
| 5 | Purchase volume | `SUM(purchase_volume)` — card spend | product × segment × week | Up |
| 6 | Interchange revenue | `SUM(interchange_revenue)` | product × segment × week | Up |
| 7 | Rewards expense | `SUM(rewards_expense)` | product × segment × week | Down |
| 8 | **Rewards-to-interchange ratio** | `rewards_expense / interchange_revenue` | product | Band: < 0.80 |
| 9 | Net interest income | `SUM(net_interest_income)` | product × segment × week | Up |
| 10 | Cost of funds % | `cost_of_funds_dollars × 52 / ending_balance × 100` | product | Down |
| 11 | Net interest margin % | `(NII − cost of funds) × 52 / ending_balance × 100` | product | Up |
| 12 | Revolve rate % | `revolve_rate_pct` — share of balance carrying interest | product × segment | Band |
| 13 | Delinquency rate % | `dpd_30_balance / ending_balance × 100` | product × segment | Down |
| 14 | 30/60/90 DPD balance | `dpd_30_balance`, `dpd_60_balance`, `dpd_90_balance` | product × segment | Down |
| 15 | Roll rate % | `dpd_60_balance / prior-period dpd_30_balance × 100` | product × segment | Down |
| 16 | Net charge-offs | `gross_chargeoff_dollars − recovery_dollars` | product × segment | Down |
| 17 | Annualised loss rate % | `net_chargeoff_dollars × 52 / ending_balance × 100` | product × segment | Down |
| 18 | Recovery rate % | `recovery_dollars / gross_chargeoff_dollars × 100` | product × segment | Up |
| 19 | Average FICO | `avg_fico`, weight by balance | segment | Up |
| 20 | Deposit runoff rate % | `runoff_dollars / deposit_balance × 100` annualised | product × segment | Down |
| 21 | Net new money | `new_money_dollars − runoff_dollars` | product × segment | Up |
| 22 | Rate paid % | `rate_paid_pct` — APY paid to depositors | product × segment | Band |
| 23 | **Rate gap %** | `competitor_rate_pct − rate_paid_pct`. **Positive means competitors pay more than we do — an attrition risk** | product × segment | Negative |
| 24 | Maturity concentration | `maturing_dollars / deposit_balance × 100` | product × week | Down |
| 25 | Cost per booking (CAC) | `marketing_spend / bookings` | product × channel | Down |
| 26 | Approval rate % | `approvals / applications × 100` | product × channel | Band |
| 27 | Booking rate % | `bookings / approvals × 100` | product × channel | Up |

**Aggregation rules.** Rates and ratios must always be recomputed from summed
numerators and denominators, never averaged. Annualisation from weekly data uses
× 52. Loss and delinquency rates apply to credit card products only — deposits
have no credit risk.

## 4. Table dictionary

### `FINANCE_FACT_PORTFOLIO_WEEK`
Grain: product × segment × week. 3,744 rows.
`week_start_date`, `fiscal_year`, `fiscal_week`, `product_id`, `segment_id`,
`ending_balance`, `new_accounts`, `closed_accounts`, `active_accounts`,
`purchase_volume`, `interchange_revenue`, `rewards_expense`,
`net_interest_income`, `cost_of_funds_dollars`, `revolve_rate_pct`, `apr_pct`.

### `FINANCE_FACT_CREDIT_WEEK`
Grain: card product × segment × week. 2,496 rows. **Credit cards only.**
`week_start_date`, `product_id`, `segment_id`, `dpd_30_balance`,
`dpd_60_balance`, `dpd_90_balance`, `gross_chargeoff_dollars`,
`recovery_dollars`, `net_chargeoff_dollars`, `delinquency_rate_pct`,
`annualized_loss_rate_pct`, `avg_fico`.

### `FINANCE_FACT_DEPOSITS_WEEK`
Grain: deposit product × segment × week. 1,248 rows. **Deposits only.**
`week_start_date`, `product_id`, `segment_id`, `deposit_balance`,
`runoff_dollars`, `maturing_dollars`, `new_money_dollars`, `rate_paid_pct`,
`competitor_rate_pct`, `rate_gap_pct`.

### `FINANCE_FACT_ACQUISITION_WEEK`
Grain: product × channel × week. 3,120 rows.
`week_start_date`, `product_id`, `channel`, `marketing_spend`, `applications`,
`approvals`, `bookings`, `cost_per_booking`, `avg_initial_credit_line`.

### `FINANCE_DIM_PRODUCT`
6 rows. `product_id`, `product_name`, `product_type` (Credit Card / Deposit),
`tier`, `portfolio_mix_pct`, `avg_apr_pct`.

### `FINANCE_DIM_SEGMENT`
6 rows. `segment_id`, `segment_name`, `avg_fico`, `portfolio_mix_pct`,
`description`.

**Joins.** All facts join to `dim_product` on `product_id` and `dim_segment` on
`segment_id`. Credit and deposit facts are mutually exclusive by product type —
never union them.

## 5. Suggested questions by persona

**Head of Retail Deposits**
- Which segments are losing balances fastest, and what is their rate gap?
- Where do competitors pay more than we do?
- What is my CD maturity exposure over the next 13 weeks?
- What would a 25bp rate exception for Mass Affluent Savers cost annually?

**Head of Card Portfolio**
- What is the rewards-to-interchange ratio by product and how is it trending?
- Which products are compressing on net interest margin?
- Where is purchase volume softening relative to balance?
- Which segments drive the most interchange per active account?

**Chief Credit Officer**
- Which segments show deteriorating delinquency over the last 13 weeks?
- Show roll rates from 30 to 60 DPD by segment.
- What is the annualised loss rate versus plan by product?
- Is average FICO drifting in any segment?

**Head of Acquisition Marketing**
- Rank channels by cost per booking.
- Which channels have falling approval rates?
- Where is spend rising without booking growth?

## 6. Alert library

| Alert | Rule | Severity | Owner |
|---|---|---|---|
| Deposit runoff acceleration | Runoff rate up > 50% vs 13-week average | Critical | Head of Deposits |
| Unfavourable rate gap | Rate gap positive (competitors higher) 2 weeks running | Critical | Head of Deposits |
| Maturity concentration | Maturing dollars > 4% of balance in one week | Warning | Head of Deposits |
| Delinquency deterioration | Delinquency rate up > 25% vs 13-week average | Critical | Chief Credit Officer |
| Loss rate breach | Annualised loss rate above segment plan | Critical | Chief Credit Officer |
| Roll rate spike | 30→60 roll rate up > 20% | Warning | Chief Credit Officer |
| Rewards cost breach | Rewards-to-interchange ratio > 0.85 | Critical | Card Portfolio Head |
| NIM compression | Net interest margin down > 30bp over 8 weeks | Warning | Card Portfolio Head |
| CAC breach | Cost per booking up > 25% over 8 weeks | Warning | Acquisition Head |
| Approval rate drop | Approval rate down > 10pts vs channel average | Warning | Acquisition Head |

## 7. Business rules and gotchas

- **Rate gap sign convention.** `rate_gap_pct = competitor_rate − rate_paid`. A
  **positive** gap means we are underpaying the market and balances are at risk.
  This is the most commonly misread field in the model.
- **Credit metrics are card-only.** Deposits carry no credit risk; any delinquency
  or loss figure on a deposit product is a data error.
- **Weekly to annual.** All flow metrics in these tables are weekly. Annualise
  with × 52, not × 12.
- **Revolve rate drives NII.** Transactor segments (SEG-02) generate almost no
  interest income regardless of balance — their value is interchange. Comparing
  NII across segments without accounting for revolve rate is misleading.
- **Balance is a stock, flows are weekly.** `ending_balance` is a point-in-time
  snapshot; do not sum it across weeks. Sum flows, average or take latest for
  stocks.
- **Segment mix changes conclusions.** Portfolio-level loss rates can look stable
  while a segment deteriorates badly. Always check segment detail before declaring
  credit stable.
