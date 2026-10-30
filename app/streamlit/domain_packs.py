"""Domain layout packs: reviewed dashboard layouts per business domain and persona.

The generic persona layouts (persona_layouts.py) work for any semantic view. A domain pack adds layouts written
for one line of business, built from that domain's business ontology (its personas, the decisions they own and the
metrics they watch). In a domain workspace these layouts come first and are what Cortex chooses from; the generic
ones stay available as alternatives.

A pack names metrics and breakdowns by their semantic-view NAME (e.g. DELINQUENCY_RATE, SEGMENT_NAME). Names that
do not exist in the view are skipped, and every tile still goes through the composer's validator, so a pack can
never produce a tile the governed data cannot answer.
"""
from __future__ import annotations

import re
from typing import Any, Optional

# Every tile answers one question a named owner asks, with the chart analysts in that industry use for it
# (rnd/domain_layouts/v2/CHART_RESEARCH_v2.md). Comparisons run over whole windows (13 weeks / 3 months vs the same
# weeks last year), never one noisy week. Tile options ("opts"): reference lines, healthy bands, fixed filters
# (e.g. wholesale accounts only, where sell-in and sell-through differ), and which direction is worse.
WHOLESALE = {"filter": {"CHANNEL": ["Wholesale"]}}
CARDS = {"filter": {"PRODUCT_TYPE": ["Credit Card"]}}

# --------------------------------------------------------------------------------------------- Finance (Keystone)
# Personas from the Keystone Financial ontology: Head of Retail Deposits, Head of Card Portfolio, Chief Credit
# Officer, Head of Acquisition Marketing (+ leadership). Data is weekly; there is no plan table, so comparisons are
# against last year.
FINANCE = {
    "executives": [
        {"id": "fin_brief", "title": "Portfolio brief",
         "when": "overall bank / portfolio performance, balances, income, risk at a glance (default for leadership)",
         "summary": "Balances, income, margin and credit quality against last year; which segment is going bad; and "
                    "which segments earn their risk after losses.",
         "pages": [{"label": "Brief", "question": "How is the bank performing, and where is it changing?", "tiles": [
             {"type": "kpi_grid", "title": "The book against last year", "width": 12,
              "metrics": ["ENDING_BALANCE", "NET_INTEREST_INCOME", "NET_INTEREST_MARGIN_PCT", "DELINQUENCY_RATE",
                          "ANNUALIZED_LOSS_RATE"],
              "question": "Balances, income, margin and credit quality vs last year."},
             {"type": "outlier_lines", "title": "Delinquency rate by segment", "metric": "DELINQUENCY_RATE",
              "dimension": "SEGMENT_NAME", "width": 7,
              "question": "A portfolio average hides one segment going bad: every segment, the mover highlighted."},
             {"type": "change_bars", "title": "Risk-adjusted yield by segment", "metric": "RISK_ADJUSTED_YIELD",
              "dimension": "SEGMENT_NAME", "width": 5, "opts": {"mode": "level", "reference": 0, "better": "up"},
              "question": "(Card revenue − net losses) ÷ card balances, annualised. Below zero, the segment loses "
                          "money after losses."},
             {"type": "trend_chart", "title": "Net interest income against last year", "metric": "NET_INTEREST_INCOME",
              "width": 7, "question": "Is income growing?"},
             {"type": "treemap", "title": "Where the balances sit, by product", "metric": "ENDING_BALANCE",
              "dimension": "PRODUCT_NAME", "width": 5, "question": "Which products make up the book?"},
         ]}]},
        {"id": "fin_risk_return", "title": "Risk & return",
         "when": "risk versus return, profitability versus losses, which segments earn their risk",
         "summary": "Risk-adjusted yield by segment, how loss rates moved against last year, and which segment's "
                    "losses are rising.",
         "pages": [{"label": "Risk & return", "question": "Which parts of the book earn their risk?", "tiles": [
             {"type": "kpi_grid", "title": "Return and risk", "width": 12,
              "metrics": ["RISK_ADJUSTED_YIELD", "NET_INTEREST_MARGIN_PCT", "ANNUALIZED_LOSS_RATE", "DELINQUENCY_RATE",
                          "AVERAGE_FICO"], "question": "Yield, margin and losses vs last year."},
             {"type": "change_bars", "title": "Risk-adjusted yield by segment", "metric": "RISK_ADJUSTED_YIELD",
              "dimension": "SEGMENT_NAME", "width": 6, "opts": {"mode": "level", "reference": 0, "better": "up"},
              "question": "Revenue after losses per dollar of balance: below zero loses money."},
             {"type": "change_bars", "title": "Loss rate: now vs a year ago", "metric": "ANNUALIZED_LOSS_RATE",
              "dimension": "SEGMENT_NAME", "width": 6, "opts": {"display": "dots"},
              "question": "Which segments' losses are rising?"},
             {"type": "outlier_lines", "title": "Annualised loss rate by segment", "metric": "ANNUALIZED_LOSS_RATE",
              "dimension": "SEGMENT_NAME", "width": 12, "question": "When did it start?"},
         ]}]},
    ],
    "managers": [
        {"id": "fin_credit", "title": "Credit risk watch",
         "when": "credit risk, delinquency, past due, charge-offs, losses, FICO (Chief Credit Officer)",
         "summary": "Which segment is deteriorating and since when, how much is past due by age for that segment, "
                    "where delinquency rose by segment and card, and the losses behind it.",
         "pages": [
             {"label": "Credit risk", "question": "Which segments are deteriorating, and how fast?", "tiles": [
                 {"type": "kpi_grid", "title": "Credit quality against last year", "width": 12,
                  "metrics": ["DELINQUENCY_RATE", "ANNUALIZED_LOSS_RATE", "NET_CHARGEOFFS", "DPD_30_BALANCE",
                              "AVERAGE_FICO"], "question": "Is credit quality getting better or worse?"},
                 {"type": "outlier_lines", "title": "30+ delinquency rate by segment", "metric": "DELINQUENCY_RATE",
                  "dimension": "SEGMENT_NAME", "width": 7,
                  "question": "Portfolio averages hide a single segment going bad: every segment on one chart."},
                 {"type": "stacked_trend", "title": "Past-due balances by age, worst segment",
                  "metrics": ["DPD_30_BALANCE", "DPD_60_BALANCE", "DPD_90_BALANCE"], "dimension": "SEGMENT_NAME",
                  "metric2": "DELINQUENCY_RATE", "width": 5, "opts": {"cumulative": True},
                  "question": "How many dollars are past due, and how much is already 90+ days late?"},
                 {"type": "heatmap", "title": "Delinquency change vs last year: segment × card", "metric": "DELINQUENCY_RATE",
                  "dimension": "SEGMENT_NAME", "dimension2": "PRODUCT_NAME", "width": 12, "opts": {"mode": "change"},
                  "question": "Exactly which segment and card combinations got worse?"},
             ]},
             {"label": "Losses", "question": "Where are the losses coming from?", "tiles": [
                 {"type": "change_bars", "title": "Net charge-offs by segment vs last year", "metric": "NET_CHARGEOFFS",
                  "dimension": "SEGMENT_NAME", "width": 6, "question": "Which segments are losing more than a year ago?"},
                 {"type": "change_bars", "title": "Loss rate: now vs a year ago", "metric": "ANNUALIZED_LOSS_RATE",
                  "dimension": "SEGMENT_NAME", "width": 6, "opts": {"display": "dots"},
                  "question": "Losses per dollar of balance, annualised."},
                 {"type": "detail_table", "title": "Credit detail by segment and product", "width": 12,
                  "dimensions": ["SEGMENT_NAME", "PRODUCT_NAME"],
                  "metrics": ["DELINQUENCY_RATE", "ANNUALIZED_LOSS_RATE", "NET_CHARGEOFFS", "AVERAGE_FICO"]},
             ]},
         ]},
        {"id": "fin_deposits", "title": "Deposits & pricing",
         "when": "deposits, savings, CDs, runoff, outflows, rate paid, rate gap, competitor rates, pricing (Head of Retail Deposits)",
         "summary": "Where competitors pay more than we do and what it costs in balances, which segments are running "
                    "off, and net flows by segment.",
         "pages": [{"label": "Deposits", "question": "Which segments are losing balances, and is it price?", "tiles": [
             {"type": "kpi_grid", "title": "Deposits against last year", "width": 12,
              "metrics": ["DEPOSIT_BALANCE", "NET_NEW_MONEY", "RUNOFF_RATE", "RATE_PAID", "RATE_GAP"],
              "question": "A positive rate gap means competitors pay more than we do."},
             {"type": "change_bars", "title": "Rate gap to competitors, and the balances it costs", "metric": "RATE_GAP",
              "metric2": "DEPOSIT_BALANCE", "dimension": "SEGMENT_NAME", "width": 6,
              "opts": {"mode": "level", "reference": 0, "better": "down"},
              "question": "Above zero, competitors pay more: the label shows that segment's balance change."},
             {"type": "outlier_lines", "title": "Deposit balances by segment (index)", "metric": "DEPOSIT_BALANCE",
              "dimension": "SEGMENT_NAME", "width": 6, "opts": {"index": True, "better": "up", "trail": 26},
              "question": "Indexed to 100 six months ago, so small and large segments compare."},
             {"type": "change_bars", "title": "Net new money by segment, last 13 weeks", "metric": "NET_NEW_MONEY",
              "dimension": "SEGMENT_NAME", "width": 12, "opts": {"mode": "level", "reference": 0, "better": "up"},
              "question": "New money minus runoff: below zero, money is leaving."},
         ]}]},
        {"id": "fin_card", "title": "Card economics",
         "when": "card spend, purchase volume, interchange, rewards cost, rewards ratio, revolve, card profitability (Head of Card Portfolio)",
         "summary": "The rewards-to-interchange ratio by card against its 0.85 breach line, spend against last year, "
                    "and the card P&L.",
         "pages": [{"label": "Card economics", "question": "Which card products are earning their keep?", "tiles": [
             {"type": "kpi_grid", "title": "Card economics against last year", "width": 12,
              "metrics": ["PURCHASE_VOLUME", "INTERCHANGE_REVENUE", "REWARDS_EXPENSE", "REWARDS_TO_INTERCHANGE_RATIO",
                          "REVOLVE_RATE"], "question": "Above 0.85 rewards-to-interchange is a profitability breach."},
             {"type": "outlier_lines", "title": "Rewards-to-interchange by card vs the breach line",
              "metric": "REWARDS_TO_INTERCHANGE_RATIO", "dimension": "PRODUCT_NAME", "width": 7,
              "opts": {"reference": 0.85, "reference_label": "breach", "better": "down", **CARDS},
              "question": "Which card is paying out more in rewards than it earns?"},
             {"type": "change_bars", "title": "Card spend by product vs last year", "metric": "PURCHASE_VOLUME",
              "dimension": "PRODUCT_NAME", "width": 5, "opts": {**CARDS, "better": "up"},
              "question": "Is spend growing where rewards cost is rising?"},
             {"type": "pnl_table", "title": "Card P&L by product: this week vs last", "dimension": "PRODUCT_NAME",
              "metrics": ["PURCHASE_VOLUME", "INTERCHANGE_REVENUE", "REWARDS_EXPENSE", "NET_INTEREST_INCOME"],
              "width": 12, "question": "Each line by product, shaded better or worse than the prior week."},
         ]}]},
        {"id": "fin_acq", "title": "Acquisition funnel",
         "when": "new accounts, acquisition, marketing channels, applications, approvals, bookings, cost per booking, CAC (Head of Acquisition Marketing)",
         "summary": "Cost per booking by channel now vs a year ago, bookings growth by channel, and the funnel detail.",
         "pages": [{"label": "Acquisition", "question": "Where should next month's acquisition budget go?", "tiles": [
             {"type": "kpi_grid", "title": "Acquisition against last year", "width": 12,
              "metrics": ["MARKETING_SPEND", "APPLICATIONS", "APPROVAL_RATE", "BOOKINGS", "COST_PER_BOOKING"],
              "question": "Is acquisition getting more or less efficient?"},
             {"type": "change_bars", "title": "Cost per booking by channel: now vs a year ago", "metric": "COST_PER_BOOKING",
              "dimension": "CHANNEL", "width": 6, "opts": {"display": "dots", "better": "down"},
              "question": "Which channels got more expensive per booked account?"},
             {"type": "change_bars", "title": "Bookings by channel vs last year", "metric": "BOOKINGS",
              "dimension": "CHANNEL", "width": 6, "opts": {"better": "up"},
              "question": "Where is spend rising without booking growth?"},
             {"type": "detail_table", "title": "Funnel by channel and product", "width": 12,
              "dimensions": ["CHANNEL", "PRODUCT_NAME"],
              "metrics": ["MARKETING_SPEND", "APPLICATIONS", "APPROVAL_RATE", "BOOKINGS", "COST_PER_BOOKING"]},
         ]}]},
    ],
    "daily_operations": [
        {"id": "fin_watch", "title": "Weekly watchlist",
         "when": "this week, what changed, watchlist, what needs action now (weekly data: no intraday)",
         "summary": "The newest week against the week before for the metrics each owner watches, what moved out of "
                    "its normal range, and a worklist by segment and product.",
         "pages": [{"label": "Watchlist", "question": "What moved this week, and who needs to act?", "tiles": [
             {"type": "kpi_grid", "title": "This week's watch metrics", "width": 12,
              "metrics": ["DEPOSIT_BALANCE", "RATE_GAP", "DELINQUENCY_RATE", "REWARDS_TO_INTERCHANGE_RATIO",
                          "COST_PER_BOOKING"], "question": "One watch metric per owner."},
             {"type": "exception_table", "title": "Segments outside their normal range", "metric": "DELINQUENCY_RATE",
              "dimension": "SEGMENT_NAME", "width": 6, "question": "Credit: which segments moved most?"},
             {"type": "exception_table", "title": "Deposit balances outside their normal range",
              "metric": "DEPOSIT_BALANCE", "dimension": "SEGMENT_NAME", "width": 6,
              "question": "Deposits: which segments are running off?"},
             {"type": "worklist", "title": "Worklist: act this week", "width": 12,
              "metrics": ["DELINQUENCY_RATE", "RATE_GAP", "REWARDS_TO_INTERCHANGE_RATIO", "RUNOFF_RATE"],
              "dimensions": ["SEGMENT_NAME", "PRODUCT_NAME"],
              "question": "What is off this week compared with a normal week, worst first?"},
         ]}]},
    ],
}


# --------------------------------------------------------------------------------------------- CPG (Apex Athletic)
# Personas from the Apex Athletic ontology: National Account Manager, Revenue Growth Manager, Brand / Category
# Director, Demand & Supply Planner (+ leadership). The core analysis is sell-in (shipments) vs sell-through (POS);
# for DTC accounts the two are the same, so channel-inventory views use wholesale accounts only.
GROSS_TO_NET = [["GROSS_SALES", "start"], ["TRADE_SPEND", "minus"], ["NET_SALES", "total"],
                ["RETURN_DOLLARS", "minus"], [None, "total", "Net of returns"]]
CPG = {
    "executives": [
        {"id": "apx_brief", "title": "Commercial brief",
         "when": "overall brand / commercial performance, revenue, margin, how we are selling (default for leadership)",
         "summary": "Sell-in, sell-through, margin and channel inventory against last year; why consumer sales "
                    "changed by product line; where stock is building; and gross-to-net.",
         "pages": [{"label": "Brief", "question": "How is the brand selling in, and selling through?", "tiles": [
             {"type": "kpi_grid", "title": "The business against last year", "width": 12,
              "metrics": ["NET_SALES", "POS_DOLLARS", "GROSS_MARGIN_PCT", "SELL_THROUGH_RATIO", "WEEKS_OF_SUPPLY"],
              "question": "Sell-in, sell-through, margin and channel inventory vs last year."},
             {"type": "velocity_split", "title": "Why consumer sales changed: distribution vs velocity",
              "metric": "POS_DOLLARS", "metric2": "ACV_DISTRIBUTION", "dimension": "PRODUCT_NAME", "width": 7,
              "opts": WHOLESALE,
              "question": "Fewer stores carrying it (distribution) or each store selling less (velocity)?"},
             {"type": "metric_waterfall", "title": "Gross-to-net", "width": 5, "opts": {"steps": GROSS_TO_NET},
              "question": "What trade spend and returns take out of gross sales."},
             {"type": "outlier_lines", "title": "Weeks of supply at retailers, by product line",
              "metric": "WEEKS_OF_SUPPLY", "dimension": "PRODUCT_NAME", "width": 7,
              "opts": {"band": [6, 12], "better": "down", "smooth": 4, **WHOLESALE},
              "question": "Healthy cover is 6–12 weeks (shaded). A line climbing out of it is stock piling up."},
             {"type": "change_bars", "title": "Net sales by account vs last year", "metric": "NET_SALES",
              "dimension": "CUSTOMER_NAME", "width": 5, "opts": {"better": "up"},
              "question": "Which accounts grew, and which fell?"},
         ]}]},
        {"id": "apx_channel", "title": "Sell-in vs sell-through",
         "when": "sell-in versus sell-through, channel inventory, divergence, stuffing, off-price",
         "summary": "Where shipments run ahead of consumer purchases, which account and product cells, and whether "
                    "the excess is leaking into off-price at a lower margin.",
         "pages": [{"label": "Channel health", "question": "Are we shipping more than consumers buy?", "tiles": [
             {"type": "kpi_grid", "title": "Channel health against last year", "width": 12,
              "metrics": ["SHIPPED_UNITS", "POS_UNITS", "SELL_THROUGH_RATIO", "WEEKS_OF_SUPPLY", "OFF_PRICE_MIX"],
              "question": "Sell-in looks healthy on its own: only the divergence shows the problem."},
             {"type": "outlier_lines", "title": "Weeks of supply at retailers, by product line",
              "metric": "WEEKS_OF_SUPPLY", "dimension": "PRODUCT_NAME", "width": 7,
              "opts": {"band": [6, 12], "better": "down", "smooth": 4, **WHOLESALE},
              "question": "Healthy cover is 6–12 weeks (shaded). A line climbing out of it is stock piling up."},
             {"type": "change_bars", "title": "Gross margin by account type vs last year", "metric": "GROSS_MARGIN_PCT",
              "dimension": "ACCOUNT_TYPE", "width": 5, "opts": {"better": "up"},
              "question": "Excess stock cleared through off-price shows up as margin lost there."},
             {"type": "heatmap", "title": "Sell-through ratio: account × product line", "metric": "SELL_THROUGH_RATIO",
              "dimension": "CUSTOMER_NAME", "dimension2": "PRODUCT_NAME", "width": 12,
              "opts": {"center": "median", "better": "up", **WHOLESALE},
              "question": "Consumer units ÷ shipped units, last 13 weeks; red cells ship well ahead of demand."},
             {"type": "trend_chart", "title": "Off-price share of net sales", "metric": "OFF_PRICE_MIX", "width": 12,
              "question": "Off-price growth is a warning, not a win."},
         ]}]},
    ],
    "managers": [
        {"id": "apx_accounts", "title": "Account health",
         "when": "accounts, retailers, sell-in vs sell-through, weeks of supply, divergence, stuffing (National Account Manager)",
         "summary": "Where weeks of supply are out of the 6–12 week band by account and product line, how cover moved "
                    "against a year ago, and sell-through by account.",
         "pages": [
             {"label": "Accounts", "question": "Which accounts are taking more than they sell?", "tiles": [
                 {"type": "kpi_grid", "title": "Account health against last year", "width": 12,
                  "metrics": ["NET_SALES", "SELL_THROUGH_RATIO", "WEEKS_OF_SUPPLY", "FILL_RATE", "TRADE_SPEND_RATE"],
                  "question": "Sell-in is lumpy: read it over 13 weeks, never one week."},
                 {"type": "heatmap", "title": "Weeks of supply: account × product line", "metric": "WEEKS_OF_SUPPLY",
                  "dimension": "CUSTOMER_NAME", "dimension2": "PRODUCT_NAME", "width": 12,
                  "opts": {"band": [6, 12], "better": "down", **WHOLESALE},
                  "question": "Healthy is 6–12 weeks: only cells outside the band are coloured."},
                 {"type": "change_bars", "title": "Weeks of supply by account: now vs a year ago",
                  "metric": "WEEKS_OF_SUPPLY", "dimension": "CUSTOMER_NAME", "width": 6,
                  "opts": {"display": "dots", "better": "down", **WHOLESALE},
                  "question": "Where is cover building?"},
                 {"type": "change_bars", "title": "Sell-through ratio by account vs last year",
                  "metric": "SELL_THROUGH_RATIO", "dimension": "CUSTOMER_NAME", "width": 6,
                  "opts": {"better": "up", **WHOLESALE}, "question": "Which accounts stopped selling through?"},
             ]},
             {"label": "Detail", "question": "Account by product line, ready to export.", "tiles": [
                 {"type": "detail_table", "title": "Sell-in vs sell-through by account and product line", "width": 12,
                  "dimensions": ["CUSTOMER_NAME", "PRODUCT_NAME"],
                  "metrics": ["SHIPPED_UNITS", "POS_UNITS", "SELL_THROUGH_RATIO", "WEEKS_OF_SUPPLY", "NET_SALES"]},
             ]},
         ]},
        {"id": "apx_rgm", "title": "Trade & promotions",
         "when": "trade spend, promotions, promo ROI, TPR, BOGO, display, deals (Revenue Growth Manager)",
         "summary": "Every promotion event against the break-even line, ROI by tactic, gross-to-net, and where the "
                    "trade rate is rising.",
         "pages": [{"label": "Trade", "question": "Which promotions pay back, and where is trade drifting?", "tiles": [
             {"type": "kpi_grid", "title": "Trade against last year", "width": 12,
              "metrics": ["TRADE_SPEND", "TRADE_SPEND_RATE", "PROMO_SPEND", "INCREMENTAL_REVENUE", "PROMO_ROI"],
              "question": "Trade spend is already deducted from net sales."},
             {"type": "scatter", "title": "Every promotion: spend vs ROI", "metric": "PROMO_SPEND", "metric2": "PROMO_ROI",
              "dimension": "PROMO_ID", "dimension2": "PROMO_TYPE", "width": 7,
              "opts": {"periods": 52, "reference_y": 0, "reference_label": "break-even", "noun": "promotions"},
              "question": "Judge promotions event by event: below the line the event lost money."},
             {"type": "metric_waterfall", "title": "Gross-to-net", "width": 5, "opts": {"steps": GROSS_TO_NET},
              "question": "What trade spend and returns take out of gross sales."},
             {"type": "change_bars", "title": "Promotion ROI by tactic, last 52 weeks", "metric": "PROMO_ROI",
              "dimension": "PROMO_TYPE", "width": 6, "opts": {"mode": "level", "reference": 0, "periods": 52},
              "question": "Spend-weighted, so a few big losers still pull a tactic down."},
             {"type": "change_bars", "title": "Trade spend rate by account vs last year", "metric": "TRADE_SPEND_RATE",
              "dimension": "CUSTOMER_NAME", "width": 6, "opts": {"better": "down"},
              "question": "Where is trade rising faster than sales?"},
         ]}]},
        {"id": "apx_brand", "title": "Brand & category",
         "when": "margin, brand, category, product lines, DTC mix, ACV distribution, off-price (Brand / Category Director)",
         "summary": "Why each product line's consumer sales changed (distribution or velocity), margin moves by line, "
                    "and which line is shifting to direct-to-consumer.",
         "pages": [{"label": "Brand", "question": "Which product lines are losing, and why?", "tiles": [
             {"type": "kpi_grid", "title": "Brand health against last year", "width": 12,
              "metrics": ["NET_SALES", "GROSS_MARGIN_PCT", "DTC_MIX", "ACV_DISTRIBUTION", "OFF_PRICE_MIX"],
              "question": "Off-price growth is a warning, not a win."},
             {"type": "velocity_split", "title": "Why consumer sales changed: distribution vs velocity",
              "metric": "POS_DOLLARS", "metric2": "ACV_DISTRIBUTION", "dimension": "PRODUCT_NAME", "width": 7,
              "opts": WHOLESALE,
              "question": "Fewer stores carrying it (distribution) or each store selling less (velocity)?"},
             {"type": "change_bars", "title": "Gross margin by product line vs last year", "metric": "GROSS_MARGIN_PCT",
              "dimension": "PRODUCT_NAME", "width": 5, "opts": {"better": "up"},
              "question": "Which lines are losing margin?"},
             {"type": "change_bars", "title": "DTC share of net sales by product line vs last year", "metric": "DTC_MIX",
              "dimension": "PRODUCT_NAME", "width": 7, "opts": {"better": "none"},
              "question": "Which line is moving to our own channels?"},
             {"type": "treemap", "title": "Net sales by account type", "metric": "NET_SALES", "dimension": "ACCOUNT_TYPE",
              "width": 5, "question": "Wholesale, off-price and DTC mix."},
         ]}]},
        {"id": "apx_supply", "title": "Supply & service",
         "when": "fill rate, OTIF, service levels, supply, on-hand inventory, planning (Demand & Supply Planner)",
         "summary": "Fill rate and on-time-in-full by account against their breach lines, and weeks of supply out of "
                    "band by product line and account.",
         "pages": [{"label": "Service", "question": "Where are we failing to ship, and where is stock out of band?", "tiles": [
             {"type": "kpi_grid", "title": "Service and inventory against last year", "width": 12,
              "metrics": ["FILL_RATE", "OTIF_RATE", "WEEKS_OF_SUPPLY", "RETAILER_ON_HAND_UNITS", "SHIPPED_UNITS"],
              "question": "Fill rate below 95% and OTIF below 90% are breaches."},
             {"type": "change_bars", "title": "Fill rate by account vs the 95% line", "metric": "FILL_RATE",
              "dimension": "CUSTOMER_NAME", "width": 6, "opts": {"mode": "level", "reference": 0.95, "better": "up"},
              "question": "Which accounts are we shorting?"},
             {"type": "change_bars", "title": "OTIF by account vs the 90% line", "metric": "OTIF_RATE",
              "dimension": "CUSTOMER_NAME", "width": 6, "opts": {"mode": "level", "reference": 0.90, "better": "up"},
              "question": "Is on-time-in-full slipping anywhere?"},
             {"type": "heatmap", "title": "Weeks of supply: product line × account", "metric": "WEEKS_OF_SUPPLY",
              "dimension": "PRODUCT_NAME", "dimension2": "CUSTOMER_NAME", "width": 12,
              "opts": {"band": [6, 12], "better": "down", **WHOLESALE},
              "question": "Healthy is 6–12 weeks: only cells outside the band are coloured."},
         ]}]},
    ],
    "daily_operations": [
        {"id": "apx_watch", "title": "Weekly watchlist",
         "when": "this week, what changed, watchlist, what needs action now (weekly data: no intraday)",
         "summary": "The newest week against the week before for the metrics each owner watches, what moved out of "
                    "its normal range, and a worklist by account and product line.",
         "pages": [{"label": "Watchlist", "question": "What moved this week, and who needs to act?", "tiles": [
             {"type": "kpi_grid", "title": "This week's watch metrics", "width": 12,
              "metrics": ["SELL_THROUGH_RATIO", "WEEKS_OF_SUPPLY", "FILL_RATE", "RETURNS_RATE", "OFF_PRICE_MIX"],
              "question": "One watch metric per owner."},
             {"type": "exception_table", "title": "Accounts outside their normal weeks of supply",
              "metric": "WEEKS_OF_SUPPLY", "dimension": "CUSTOMER_NAME", "width": 6,
              "question": "Accounts: where is inventory building?"},
             {"type": "exception_table", "title": "Product lines outside their normal sell-through",
              "metric": "SELL_THROUGH_RATIO", "dimension": "PRODUCT_NAME", "width": 6,
              "question": "Products: which lines stopped selling through?"},
             {"type": "worklist", "title": "Worklist: act this week", "width": 12,
              "metrics": ["WEEKS_OF_SUPPLY", "SELL_THROUGH_RATIO", "FILL_RATE", "RETURNS_RATE"],
              "dimensions": ["CUSTOMER_NAME", "PRODUCT_NAME"],
              "question": "What is off this week compared with a normal week, worst first?"},
         ]}]},
    ],
}


# --------------------------------------------------------------------------------------------- Retail (Harborline)
# Retail keeps its validated generic layouts first; these are extra layouts offered beside them (and chosen when the
# question asks for them). Net sales = orders x average order value exactly in the Harborline view.
RETAIL = {
    "executives": [
        {"id": "ret_drivers", "title": "Sales drivers",
         "when": "why sales changed, drivers, orders vs order value, basket, which regions and categories",
         "summary": "Net sales split into orders and order value against last year, where growth came from by "
                    "region and category, and margin moves by category.",
         "pages": [{"label": "Drivers", "question": "Why did sales change?", "tiles": [
             {"type": "kpi_grid", "title": "Trading against last year", "width": 12,
              "metrics": ["NET_SALES", "ORDER_COUNT", "AVERAGE_ORDER_VALUE", "GROSS_MARGIN_PCT", "RETURN_RATE"],
              "question": "Sales, orders, order value, margin and returns vs last year."},
             {"type": "driver_split", "title": "Net sales = orders × order value", "width": 5,
              "metrics": ["NET_SALES", "ORDER_COUNT", "AVERAGE_ORDER_VALUE"],
              "question": "More orders, or bigger orders?"},
             {"type": "heatmap", "title": "Sales growth vs last year: region × category", "metric": "NET_SALES",
              "dimension": "REGION", "dimension2": "CATEGORY", "width": 7, "opts": {"mode": "change", "better": "up"},
              "question": "One cell usually explains the miss."},
             {"type": "change_bars", "title": "Gross margin by category vs last year", "metric": "GROSS_MARGIN_PCT",
              "dimension": "CATEGORY", "width": 6, "opts": {"better": "up"}, "question": "Where did margin move?"},
             {"type": "outlier_lines", "title": "Net sales by region (index)", "metric": "NET_SALES",
              "dimension": "REGION", "width": 6, "opts": {"index": True, "better": "up", "trail": 26},
              "question": "Indexed to 100 six months ago, so regions of different size compare."},
         ]}]},
    ],
    "managers": [
        {"id": "ret_merch", "title": "Merchandise performance",
         "when": "category, merchandise, margin by category, discount, markdown, region by category, basket, order value",
         "summary": "Sales growth by region and category, the orders vs order value split, and margin and discount "
                    "moves by category.",
         "pages": [{"label": "Merchandise", "question": "Which categories are winning and losing, and why?", "tiles": [
             {"type": "kpi_grid", "title": "Merchandise against last year", "width": 12,
              "metrics": ["NET_SALES", "GROSS_MARGIN_PCT", "DISCOUNT_RATE", "RETURN_RATE", "UNITS_PER_TRANSACTION"],
              "question": "Sales, margin, discount, returns and basket size vs last year."},
             {"type": "heatmap", "title": "Sales growth vs last year: region × category", "metric": "NET_SALES",
              "dimension": "REGION", "dimension2": "CATEGORY", "width": 12, "opts": {"mode": "change", "better": "up"},
              "question": "Which region and category cell moved?"},
             {"type": "driver_split", "title": "Net sales = orders × order value", "width": 4,
              "metrics": ["NET_SALES", "ORDER_COUNT", "AVERAGE_ORDER_VALUE"], "question": "More orders, or bigger orders?"},
             {"type": "change_bars", "title": "Gross margin by category vs last year", "metric": "GROSS_MARGIN_PCT",
              "dimension": "CATEGORY", "width": 4, "opts": {"better": "up"}, "question": "Where did margin move?"},
             {"type": "change_bars", "title": "Discount rate by category vs last year", "metric": "DISCOUNT_RATE",
              "dimension": "CATEGORY", "width": 4, "opts": {"better": "down"},
              "question": "Is margin going into discounts?"},
         ]}]},
        {"id": "ret_regional", "title": "Regional performance",
         "when": "regions, stores, store performance, which stores are behind, in-stock and stockouts by region (Regional Operations Director)",
         "summary": "Sales growth by region and store against last year, where stock-outs cluster by region and "
                    "category, and which region is drifting.",
         "pages": [{"label": "Regions", "question": "Which regions and stores need my attention this week?", "tiles": [
             {"type": "kpi_grid", "title": "The region against last year", "width": 12,
              "metrics": ["NET_SALES", "ORDER_COUNT", "AVERAGE_ORDER_VALUE", "IN_STOCK_RATE", "STOCKOUT_RATE"],
              "question": "Sales, orders, basket and availability vs last year."},
             {"type": "change_bars", "title": "Net sales by region vs last year", "metric": "NET_SALES",
              "dimension": "REGION", "width": 5, "opts": {"better": "up"}, "question": "Which region is behind?"},
             {"type": "outlier_lines", "title": "Net sales by region (index)", "metric": "NET_SALES",
              "dimension": "REGION", "width": 7, "opts": {"index": True, "better": "up", "trail": 26},
              "question": "Indexed to 100 six months ago, so regions of different size compare."},
             {"type": "change_bars", "title": "Net sales by store vs last year", "metric": "NET_SALES",
              "dimension": "STORE", "width": 6, "opts": {"better": "up"}, "question": "Rank my stores by growth."},
             {"type": "heatmap", "title": "Stock-out rate: region × category", "metric": "STOCKOUT_RATE",
              "dimension": "REGION", "dimension2": "CATEGORY", "width": 6, "opts": {"center": "median", "better": "down"},
              "question": "Which region and category combinations run out most?"},
         ]}]},
        {"id": "ret_inventory", "title": "Inventory health",
         "when": "inventory, stock, weeks of supply, in stock, stockouts, sell-through, lost sales, overstock",
         "summary": "Weeks of supply by category against a year ago, in-stock moves, and where cover is out of line by "
                    "region and category.",
         "pages": [{"label": "Inventory", "question": "Where is stock too high or too low?", "tiles": [
             {"type": "kpi_grid", "title": "Inventory against last year", "width": 12,
              "metrics": ["WEEKS_OF_SUPPLY", "IN_STOCK_RATE", "SELL_THROUGH_PCT", "LOST_SALES_UNITS",
                          "ENDING_UNITS_ON_HAND"], "question": "Cover, availability and lost sales vs last year."},
             {"type": "change_bars", "title": "Weeks of supply by category: now vs a year ago", "metric": "WEEKS_OF_SUPPLY",
              "dimension": "CATEGORY", "width": 6, "opts": {"display": "dots", "better": "down"},
              "question": "Where is cover building?"},
             {"type": "change_bars", "title": "In-stock rate by category vs last year", "metric": "IN_STOCK_RATE",
              "dimension": "CATEGORY", "width": 6, "opts": {"better": "up"}, "question": "Where are we running out?"},
             {"type": "heatmap", "title": "Weeks of supply: region × category", "metric": "WEEKS_OF_SUPPLY",
              "dimension": "REGION", "dimension2": "CATEGORY", "width": 12, "opts": {"center": "median", "better": "down"},
              "question": "Coloured against the typical cell: red holds too much stock."},
         ]}]},
        {"id": "ret_omni", "title": "Omnichannel & fulfilment",
         "when": "digital, online, ecommerce, web, app, marketplace, delivery, shipping, on-time, fulfilment, click to ship (VP Omnichannel)",
         "summary": "Digital share by category against last year, on-time delivery by carrier, delivery speed by ship "
                    "method, and how each channel is growing.",
         "pages": [{"label": "Omnichannel", "question": "Where is digital growing, and is fulfilment keeping up?", "tiles": [
             {"type": "kpi_grid", "title": "Digital and fulfilment against last year", "width": 12,
              "metrics": ["ONLINE_NET_SALES", "ONLINE_SALES_SHARE", "ON_TIME_DELIVERY_PCT", "AVG_DELIVERY_DAYS",
                          "FREE_SHIPPING_ORDER_PCT"], "question": "Digital sales, penetration and delivery vs last year."},
             {"type": "change_bars", "title": "Digital share by category vs last year", "metric": "ONLINE_SALES_SHARE",
              "dimension": "CATEGORY", "width": 6, "opts": {"better": "none"},
              "question": "Where is digital penetration moving?"},
             {"type": "change_bars", "title": "Net sales by channel vs last year", "metric": "NET_SALES",
              "dimension": "CHANNEL", "width": 6, "opts": {"better": "up"}, "question": "Which channel is growing?"},
             {"type": "outlier_lines", "title": "On-time delivery by carrier", "metric": "ON_TIME_DELIVERY_PCT",
              "dimension": "CARRIER", "width": 7, "opts": {"better": "up"},
              "question": "Is any delivery partner slipping?"},
             {"type": "change_bars", "title": "Delivery days by ship method: now vs a year ago", "metric": "AVG_DELIVERY_DAYS",
              "dimension": "SHIP_METHOD", "width": 5, "opts": {"display": "dots", "better": "down"},
              "question": "Is delivery getting slower?"},
         ]}]},
    ],
    "daily_operations": [],
}
EXTRA = {"retail"}      # domains whose pack layouts are offered beside the generic ones, not instead of them

RULES = {
    "finance": {
        "executives": [("fin_risk_return", r"risk|loss|earn|return|profitab")],
        "managers": [("fin_deposits", r"deposit|saving|\bcds?\b|runoff|outflow|rate gap|rate paid|competitor|pricing|retention"),
                     ("fin_acq", r"acquisi|channel|booking|application|approval|\bcac\b|marketing|new account"),
                     ("fin_card", r"reward|interchange|card spend|purchase volume|\bspend\b|revolve|card econom|card profit"),
                     ("fin_credit", r"credit|delinquen|past due|\bdpd\b|charge.?off|loss|fico|roll rate")],
        "daily_operations": [],
    },
    "cpg": {
        "executives": [("apx_channel", r"sell.?in|sell.?through|channel inventor|stuff|divergen|off.?price|inventory")],
        "managers": [("apx_rgm", r"trade|promo|\broi\b|\btpr\b|bogo|display|deal"),
                     ("apx_supply", r"fill rate|\botif\b|service level|supply|planner|on.?hand"),
                     ("apx_brand", r"margin|brand|categor|\bdtc\b|direct to consumer|\bmix\b|\bacv\b|distribution|velocity|off.?price|product line"),
                     ("apx_accounts", r"account|retailer|sell.?in|sell.?through|weeks of supply|divergen|stuff|inventor")],
        "daily_operations": [],
    },
    "retail": {
        "executives": [("ret_drivers", r"driver|why .*(sales|revenue)|orders? vs|order value|\baov\b|basket")],
        "managers": [("ret_omni", r"digital|online|e-?commerce|\bweb\b|\bapp\b|marketplace|deliver|shipping|on.?time|fulfil|click to ship"),
                     ("ret_regional", r"region|stores?\b|store performance|stock.?out"),
                     ("ret_inventory", r"inventor|stock|weeks of supply|in.?stock|lost sales|overstock|sell.?through"),
                     ("ret_merch", r"merchandis|categor.*(margin|growth|perform)|discount|markdown|order value|\baov\b|basket")],
        "daily_operations": [],
    },
}

PACKS = {"finance": FINANCE, "cpg": CPG, "retail": RETAIL}

# The headline metric of a domain when the person did not name one (the generic default would pick the first
# metric that looks like revenue, which for a bank is bookings).
LEAD = {"finance": ["ENDING_BALANCE", "NET_INTEREST_INCOME", "PURCHASE_VOLUME"], "cpg": ["NET_SALES", "POS_DOLLARS"]}


def extra(domain: str) -> bool:
    """Pack layouts offered beside the generic ones (not first, not the only ones Cortex may pick)."""
    return (domain or "") in EXTRA


def variants(domain: str, persona: str) -> list[dict[str, Any]]:
    return list((PACKS.get(domain or "") or {}).get(persona) or [])


def rule(domain: str, persona: str, goal: str) -> Optional[str]:
    for vid, rx in (RULES.get(domain or "") or {}).get(persona, []):
        if re.search(rx, goal or "", re.I):
            return vid
    return None


def get(domain: str, persona: str, variant: str) -> Optional[dict[str, Any]]:
    return next((v for v in variants(domain, persona) if v["id"] == variant), None)


def resolve(ctx, variant: dict[str, Any]) -> dict[str, Any]:
    """The pack layout with metric / dimension NAMES replaced by this view's field ids; unknown names dropped,
    tiles that lose their required fields dropped (the validator then certifies the rest). Optional fields (a colour
    grouping, a focus breakdown, a filter) are dropped on their own without losing the tile."""
    mets = {m.name.upper(): m.id for m in ctx.model.metrics}
    dims = {d.name.upper(): d.id for d in ctx.model.categorical_dimensions}
    optional = {"scatter": ("dimension2",), "stacked_trend": ("dimension", "metric2"), "change_bars": ("metric2",)}
    pages = []
    for pg in variant["pages"]:
        tiles = []
        for t in pg["tiles"]:
            t2 = dict(t)
            ok = True
            opt = optional.get(t2.get("type"), ())
            for k in ("metric", "metric2"):
                if k in t2:
                    t2[k] = mets.get(str(t2[k]).upper())
                    if not t2[k] and k in opt:
                        t2.pop(k)
                        continue
                    ok = ok and bool(t2[k])
            for k in ("dimension", "dimension2"):
                if k in t2:
                    t2[k] = dims.get(str(t2[k]).upper())
                    if not t2[k] and k in opt:
                        t2.pop(k)
                        continue
                    ok = ok and bool(t2[k])
            if "metrics" in t2:
                asked = list(t2["metrics"])
                t2["metrics"] = [mets[x.upper()] for x in asked if x.upper() in mets]
                ok = ok and bool(t2["metrics"])
                if t2.get("type") in ("driver_split", "stacked_trend"):
                    ok = ok and len(t2["metrics"]) == len(asked)      # a missing driver or bucket breaks the story
            if "dimensions" in t2:
                t2["dimensions"] = [dims[x.upper()] for x in t2["dimensions"] if x.upper() in dims]
            if "opts" in t2:
                o = dict(t2["opts"])
                if "filter" in o:
                    o["filter"] = {dims[k.upper()]: v for k, v in o["filter"].items() if k.upper() in dims}
                    if not o["filter"]:
                        o.pop("filter")
                if "steps" in o:
                    steps = []
                    for st in o["steps"]:
                        if st[0] and st[0].upper() not in mets:
                            if st[1] in ("start", "minus", "plus"):
                                ok = False                    # a missing step would not add up
                            continue
                        steps.append([mets[st[0].upper()] if st[0] else None, *st[1:]])
                    o["steps"] = steps
                t2["opts"] = o
            if ok:
                tiles.append(t2)
        if tiles:
            pages.append({"label": pg["label"], "question": pg["question"], "tiles": tiles})
    return {"pages": pages}


# --------------------------------------------------------------------------------------------- alert templates
# From each domain's alert library (ontology section 6). Only rules the alert engine can check exactly are offered;
# where the library compares with a rolling average, the template says which comparison it uses instead.
ALERTS = {
    "finance": [
        {"id": "fin_rewards_breach", "title": "Rewards cost breach", "severity": "Critical", "owner": "Head of Card Portfolio",
         "metric": "REWARDS_TO_INTERCHANGE_RATIO", "rule": "threshold", "op": "above", "value_input": 85, "grain": "week",
         "note": "Rewards-to-interchange above 0.85 in the latest full week (the library's breach line)."},
        {"id": "fin_rate_gap", "title": "Unfavourable rate gap", "severity": "Critical", "owner": "Head of Retail Deposits",
         "metric": "RATE_GAP", "rule": "threshold", "op": "above", "value_input": 0, "grain": "week",
         "note": "Competitors pay more than we do (positive rate gap) in the latest full week."},
        {"id": "fin_delinquency_up", "title": "Delinquency deterioration", "severity": "Critical", "owner": "Chief Credit Officer",
         "metric": "DELINQUENCY_RATE", "rule": "unusual", "direction": "up", "by": "SEGMENT_NAME", "grain": "week",
         "note": "Delinquency rate above its normal range (last 13 weeks) for the total or any segment, as the library's 13-week rule."},
        {"id": "fin_runoff_accel", "title": "Deposit runoff acceleration", "severity": "Critical", "owner": "Head of Retail Deposits",
         "metric": "RUNOFF_RATE", "rule": "unusual", "direction": "up", "by": "SEGMENT_NAME", "grain": "week",
         "note": "Runoff rate above its normal range (last 13 weeks) for the total or any segment, as the library's 13-week rule."},
        {"id": "fin_cac_breach", "title": "Cost per booking breach", "severity": "Warning", "owner": "Head of Acquisition Marketing",
         "metric": "COST_PER_BOOKING", "rule": "change", "pct": 25, "direction": "up", "compare": "prior", "grain": "month",
         "note": "Cost per booking up more than 25% on the prior month (the library uses 8 weeks)."},
    ],
    "cpg": [
        {"id": "apx_inventory_bloat", "title": "Channel inventory bloat", "severity": "Critical", "owner": "National Account Manager",
         "metric": "WEEKS_OF_SUPPLY", "rule": "threshold", "op": "above", "value_input": 14, "grain": "week",
         "note": "Retailer weeks of supply above 14 in the latest full week (the library asks for 3 weeks running)."},
        {"id": "apx_offprice", "title": "Off-price diversion", "severity": "Critical", "owner": "Brand / Category Director",
         "metric": "OFF_PRICE_MIX", "rule": "unusual", "direction": "up", "grain": "week",
         "note": "Off-price share of net sales above its normal range over the last 13 weeks (the library's 13-week view)."},
        {"id": "apx_margin", "title": "Margin erosion", "severity": "Critical", "owner": "Brand / Category Director",
         "metric": "GROSS_MARGIN_PCT", "rule": "unusual", "direction": "down", "by": "PRODUCT_NAME", "grain": "week",
         "note": "Gross margin % below its normal range (last 13 weeks) for the total or any product line (the library uses 13 weeks)."},
        {"id": "apx_fill", "title": "Fill rate breach", "severity": "Warning", "owner": "Demand & Supply Planner",
         "metric": "FILL_RATE", "rule": "threshold", "op": "below", "value_input": 95, "grain": "week",
         "note": "Fill rate below 95% in the latest full week (the library asks for 2 weeks running)."},
        {"id": "apx_otif", "title": "OTIF breach", "severity": "Warning", "owner": "Demand & Supply Planner",
         "metric": "OTIF_RATE", "rule": "threshold", "op": "below", "value_input": 90, "grain": "week",
         "note": "On-time-in-full below 90% in the latest full week (the library asks for 2 weeks running)."},
        {"id": "apx_returns", "title": "Returns spike", "severity": "Warning", "owner": "National Account Manager",
         "metric": "RETURNS_RATE", "rule": "threshold", "op": "above", "value_input": 6, "grain": "week",
         "note": "Returns above 6% of gross sales in the latest full week."},
    ],
}


def alert_templates(domain: str) -> list[dict[str, Any]]:
    return list(ALERTS.get(domain or "") or [])


# --------------------------------------------------------------------------------------------- personas
# The people each domain is built for (ontology section 2): who they are, the decision they own, the layout made for
# them, the questions they ask (section 5), the alerts they own (section 6) and what this data cannot show them.
# A persona sits on one of the app's audience types (grain, comparisons, validation and publishing are unchanged).
# layout None = the app's reviewed generic layout for that audience.
PERSONAS = {
    "finance": [
        {"id": "fin_lead", "label": "Leadership", "audience": "executives", "layout": "fin_brief",
         "owns": "The whole book: balances, income, margin and credit quality",
         "decides": "Where the bank needs attention this month",
         "questions": ["How is the bank performing against last year?", "Which segments earn their risk after losses?",
                       "Where is credit quality changing?"],
         "alerts": [], "missing": []},
        {"id": "fin_deposits", "label": "Head of Retail Deposits", "audience": "managers", "layout": "fin_deposits",
         "owns": "Deposit balances, deposit pricing and cost of funds",
         "decides": "Which segments get a rate exception or retention offer, and at what cost",
         "questions": ["Which segments are losing balances fastest, and what is their rate gap?",
                       "Where do competitors pay more than we do?",
                       "What is my CD maturity exposure over the next 13 weeks?",
                       "What would a 25bp rate exception for Mass Affluent Savers cost annually?"],
         "alerts": ["fin_rate_gap", "fin_runoff_accel"],
         "missing": ["The cost of a rate exception is answered by the agent, not yet as a what-if tile"]},
        {"id": "fin_card", "label": "Head of Card Portfolio", "audience": "managers", "layout": "fin_card",
         "owns": "Card revenue, rewards cost and portfolio profitability",
         "decides": "Where to push spend, where to tighten rewards, which products earn their keep",
         "questions": ["What is the rewards-to-interchange ratio by product and how is it trending?",
                       "Which products are compressing on net interest margin?",
                       "Where is purchase volume softening relative to balance?",
                       "Which segments drive the most interchange per active account?"],
         "alerts": ["fin_rewards_breach"], "missing": []},
        {"id": "fin_credit", "label": "Chief Credit Officer", "audience": "managers", "layout": "fin_credit",
         "owns": "Credit quality and loss performance",
         "decides": "Where to tighten underwriting or line assignment, and what to reserve",
         "questions": ["Which segments show deteriorating delinquency over the last 13 weeks?",
                       "Which segments lose more than they earn after charge-offs?",
                       "Is average FICO drifting in any segment?"],
         "alerts": ["fin_delinquency_up"],
         "missing": ["Roll rates: the past-due balances are cumulative (30+, 60+, 90+), so 30→60 flows can't be derived",
                     "Provision expense and loss-rate plan are not in the data"]},
        {"id": "fin_acq", "label": "Head of Acquisition Marketing", "audience": "managers", "layout": "fin_acq",
         "owns": "New account growth and acquisition efficiency",
         "decides": "Where to spend next month's acquisition budget",
         "questions": ["Rank channels by cost per booking.", "Which channels have falling approval rates?",
                       "Where is spend rising without booking growth?"],
         "alerts": ["fin_cac_breach"],
         "missing": ["Downstream credit by channel: acquisition is not linked to the credit table"]},
        {"id": "fin_watch", "label": "Weekly watchlist", "audience": "daily_operations", "layout": "fin_watch",
         "owns": "The weekly portfolio watchlist",
         "decides": "Who needs to act this week",
         "questions": ["What moved this week, and who needs to act?"], "alerts": [], "missing": []},
    ],
    "cpg": [
        {"id": "apx_lead", "label": "Leadership", "audience": "executives", "layout": "apx_brief",
         "owns": "The brand's sell-in, sell-through, margin and channel inventory",
         "decides": "Where the business needs attention this month",
         "questions": ["How is the brand selling in and selling through?",
                       "Are we shipping more than consumers buy anywhere?", "Why did consumer sales change by product line?"],
         "alerts": [], "missing": []},
        {"id": "apx_nam", "label": "National Account Manager", "audience": "managers", "layout": "apx_accounts",
         "owns": "The commercial relationship with retail partners",
         "decides": "What to ship, what to hold, and what to negotiate with the account this week",
         "questions": ["Which accounts have sell-in growing while sell-through declines?",
                       "Show retailer weeks of supply by account and product, flag anything above 12.",
                       "What is my fill rate by account over the last 13 weeks?",
                       "How much trade spend am I giving each account as a percent of gross sales?"],
         "alerts": ["apx_inventory_bloat", "apx_returns"], "missing": []},
        {"id": "apx_rgm", "label": "Revenue Growth Manager", "audience": "managers", "layout": "apx_rgm",
         "owns": "Trade promotion spend and its return",
         "decides": "Which promotions to repeat, resize or kill next cycle",
         "questions": ["Rank promotions by ROI over the last two quarters.",
                       "Which promo types underperform, and with which accounts?",
                       "Where is trade spend rate rising without a revenue response?"],
         "alerts": [],
         "missing": ["Baseline vs incremental volume (no baseline model) and price gap to competition are not in the data"]},
        {"id": "apx_brand", "label": "Brand / Category Director", "audience": "managers", "layout": "apx_brand",
         "owns": "A product line's revenue and margin",
         "decides": "Where to invest, what to discontinue, how to price",
         "questions": ["Which product lines are losing gross margin and why?",
                       "How is the DTC versus wholesale mix shifting by product?",
                       "Which products are losing ACV distribution?"],
         "alerts": ["apx_offprice", "apx_margin"], "missing": []},
        {"id": "apx_supply", "label": "Demand & Supply Planner", "audience": "managers", "layout": "apx_supply",
         "owns": "Forecast accuracy and service level",
         "decides": "What to produce and where to position it",
         "questions": ["Where is fill rate below 95% and what is the revenue at risk?",
                       "Which account and product combinations have channel inventory out of band?"],
         "alerts": ["apx_fill", "apx_otif"],
         "missing": ["Forecast error and order cycle variability are not in the data"]},
        {"id": "apx_watch", "label": "Weekly watchlist", "audience": "daily_operations", "layout": "apx_watch",
         "owns": "The weekly S&OP and account watchlist", "decides": "Who needs to act this week",
         "questions": ["What moved this week, and who needs to act?"], "alerts": [], "missing": []},
    ],
    "retail": [
        {"id": "ret_lead", "label": "Leadership", "audience": "executives", "layout": None,
         "owns": "Sales and margin against plan and last year", "decides": "Where the business needs attention",
         "questions": ["How are we tracking against plan this year?", "Why did sales change: more orders or bigger orders?",
                       "Which regions and categories drove the change?"],
         "alerts": [], "missing": []},
        {"id": "ret_category", "label": "Category Manager", "audience": "managers", "layout": "ret_merch",
         "owns": "Assortment, pricing and markdown for categories",
         "decides": "Which categories get marked down this week, how deep, and in which regions",
         "questions": ["Where is gross margin eroding fastest over the last 13 weeks?",
                       "Which regions are underperforming in Apparel?",
                       "What is my discount rate by category versus the same period last year?"],
         "alerts": [],
         "missing": ["Markdown is shown as discount rate (no markdown split)", "GMROI, markdown liability and price gap "
                     "are not in this data"]},
        {"id": "ret_regional", "label": "Regional Operations Director", "audience": "managers", "layout": "ret_regional",
         "owns": "Store-level execution across a region", "decides": "Where to focus store operations this week",
         "questions": ["Rank my stores by sales growth over the last 13 weeks.",
                       "Which region and category combinations have the most stock-outs?",
                       "Which region is behind last year?"],
         "alerts": [],
         "missing": ["Comp-store flag, traffic, conversion, sales per sq ft and shrink are not in this data "
                     "(growth is all stores)"]},
        {"id": "ret_inventory", "label": "Inventory & Allocation Planner", "audience": "managers", "layout": "ret_inventory",
         "owns": "Stock position and flow across stores and DCs", "decides": "What to allocate where, and what to stop ordering",
         "questions": ["Show categories where weeks of supply rose while sell-through fell.",
                       "Where are we running out of stock?", "Which categories hold too much stock?"],
         "alerts": [], "missing": ["Inventory turns and GMROI are not in this data (weeks of supply is)"]},
        {"id": "ret_omni", "label": "VP Omnichannel", "audience": "managers", "layout": "ret_omni",
         "owns": "Digital sales and fulfilment", "decides": "Which fulfilment mix and categories to push digitally",
         "questions": ["What is digital penetration by category and how has it moved?",
                       "Is on-time delivery slipping for any carrier?", "Which channel is growing fastest?"],
         "alerts": [], "missing": ["Fulfilment cost per order is not in this data (shipping fee revenue is)"]},
        {"id": "ret_watch", "label": "Daily operations", "audience": "daily_operations", "layout": None,
         "owns": "Today's trading", "decides": "What needs fixing today",
         "questions": ["What is going wrong today, and where?"], "alerts": [], "missing": []},
    ],
}


def personas(domain: str) -> list[dict[str, Any]]:
    titles = {t["id"]: t["title"] for t in ALERTS.get(domain or "", [])}
    return [{**p, "alert_titles": [titles[a] for a in p["alerts"] if a in titles]} for p in PERSONAS.get(domain or "", [])]


def persona(domain: str, pid: str) -> Optional[dict[str, Any]]:
    return next((p for p in personas(domain) if p["id"] == pid), None)


def persona_tiles(domain: str, pid: str) -> list[dict[str, Any]]:
    """The tiles of the persona's own pack layout: [{'text': title + question, 'metrics': [names]}]."""
    p = persona(domain, pid)
    if not p or not p.get("layout"):
        return []
    v = get(domain, p["audience"], p["layout"])
    out = []
    for pg in (v or {}).get("pages") or []:
        for t in pg.get("tiles") or []:
            names = list(t.get("metrics") or []) + [t[k] for k in ("metric", "metric2") if t.get(k)]
            if names:
                out.append({"text": f"{t.get('title', '')} {t.get('question', '')}", "metrics": names})
    return out


# --------------------------------------------------------------------------------------------- persona guidance
# What each role watches in its industry (research 23 Oct: OCC card lending, Javelin, Curinos, S&P, Deloitte RGM,
# Vividly, Leafio, Cleverence, ERS retail math). This is only the SEED: the live guidance is data in AA_APP_SETTINGS
# (key lens:<domain>:<persona>), editable in the app without a code change. Cortex reads it to know what matters to
# the role; the persona's in-lane metrics come from its reviewed layout (persona_tiles) or, for a typed-in persona,
# from the metrics Cortex picked and the person confirmed.
LENS_SEED = {
    "finance": {
        "fin_lead": ["Balance growth vs last year", "Net interest income and margin", "Credit losses", "Risk-adjusted yield by segment"],
        "fin_deposits": ["Balance growth and runoff", "Rate paid vs competitors", "Deposit beta", "Cost of funds", "CD maturity wall", "Attrition"],
        "fin_card": ["Purchase volume", "Active rate", "Interchange revenue", "Rewards-to-interchange ratio", "Revolve rate", "Net interest margin"],
        "fin_credit": ["Delinquency by bucket", "Roll rates", "Net charge-off rate", "Risk-adjusted yield", "FICO mix", "Approval rate vs losses"],
        "fin_acq": ["Applications and approvals", "Approval rate", "Cost per booked account", "Channel mix", "Early delinquency of new accounts"],
        "fin_watch": ["Week-over-week breaks in balances, delinquency and rates"],
    },
    "cpg": {
        "apx_lead": ["Net sales vs last year", "Gross margin", "Channel mix", "Trade spend rate"],
        "apx_nam": ["Sell-in vs sell-through", "Retailer weeks of supply", "Fill rate", "Trade spend per account", "Share at the account"],
        "apx_rgm": ["Price / pack / mix", "Trade spend rate", "Promo ROI per event", "Gross-to-net", "Elasticity", "Baseline vs incremental"],
        "apx_brand": ["Consumer sales (POS)", "Distribution (%ACV) vs velocity", "Share", "Price gap"],
        "apx_supply": ["Fill rate and OTIF", "Forecast accuracy", "Inventory days", "Stock-outs"],
        "apx_watch": ["Week-over-week breaks in sales, fill rate and inventory"],
    },
    "retail": {
        "ret_lead": ["Comp sales vs last year and plan", "Gross margin", "Inventory health", "Digital share"],
        "ret_category": ["Comp sales", "Margin %", "GMROI", "Sell-through", "Weeks of supply", "Markdown %"],
        "ret_regional": ["Comp sales by store and region", "Traffic x conversion x basket", "Labour %", "Shrink"],
        "ret_inventory": ["Weeks of supply", "In-stock %", "Aged stock", "Open-to-buy"],
        "ret_omni": ["Digital penetration", "On-time delivery", "Fulfilment mix", "Returns"],
        "ret_watch": ["Today's breaks: stock-outs, late shipments, order pace"],
    },
}


def lens_seed(domain: str, pid: str) -> list[str]:
    return list((LENS_SEED.get(domain or "") or {}).get(pid) or [])


def lane_metrics(domain: str, pid: str) -> list[str]:
    """Metric NAMES that belong to a built-in persona: the metrics of its reviewed layout."""
    out: list[str] = []
    for t in persona_tiles(domain, pid):
        out += [x for x in t["metrics"] if x not in out]
    return out


def lane_dimensions(domain: str, pid: str) -> list[str]:
    """Dimension NAMES the persona's layout breaks its metrics by (first = the main one)."""
    p = persona(domain, pid)
    v = get(domain, p["audience"], p["layout"]) if p and p.get("layout") else None
    out: list[str] = []
    for pg in (v or {}).get("pages") or []:
        for t in pg.get("tiles") or []:
            for k in ("dimension", "dimension2"):
                if t.get(k) and t[k] not in out:
                    out.append(t[k])
    return out
