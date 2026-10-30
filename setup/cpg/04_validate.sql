-- =====================================================================================
-- Apex Athletic (fictional) - Step 4: checks (read-only)
-- Expected values were computed from the CSV files with the same formulas (22 Oct 2026).
-- =====================================================================================
USE ROLE WBR_OWNER;
USE WAREHOUSE POWERHOUSE;
USE SCHEMA WBR_DB.CPG_DEMO;

-- 1) rolling calendar: the newest week must end on the last Sunday before today
SELECT MIN(C_WEEK_ENDING) AS FIRST_WEEK_ENDING, MAX(C_WEEK_ENDING) AS LAST_WEEK_ENDING, COUNT(*) AS WEEKS,
       DATEADD('day', -DAYOFWEEKISO(CURRENT_DATE()), CURRENT_DATE()) AS LAST_SUNDAY,
       IFF(MAX(C_WEEK_ENDING) = DATEADD('day', -DAYOFWEEKISO(CURRENT_DATE()), CURRENT_DATE()), 'OK', 'CHECK') AS RESULT
FROM SV_SRC_WEEKS;

-- 2) sell-in and sell-through matched 1:1 (12,480 rows) and semantic view = base tables
SELECT COUNT(*) AS MATCHED_ROWS, IFF(COUNT(*) = 12480, 'OK', 'CHECK: sell-in / sell-through not 1:1') AS RESULT
FROM SV_SRC_ACCOUNT_WEEK;
WITH sv AS (
  SELECT * FROM SEMANTIC_VIEW(WBR_DB.CPG_DEMO.CPG_ANALYTICS_SV
    METRICS trade.net_sales, trade.shipped_units, trade.pos_units, trade.trade_spend, promotions.promo_spend)
), raw AS (
  SELECT (SELECT SUM(NET_SALES) FROM CPG_FACT_SELLIN_WEEK) AS NS, (SELECT SUM(SHIPPED_UNITS) FROM CPG_FACT_SELLIN_WEEK) AS SU,
         (SELECT SUM(POS_UNITS) FROM CPG_FACT_SELLTHROUGH_WEEK) AS PU, (SELECT SUM(TRADE_SPEND) FROM CPG_FACT_SELLIN_WEEK) AS TS,
         (SELECT SUM(TRADE_SPEND) FROM CPG_FACT_TRADE_PROMO) AS PS
)
SELECT IFF(ABS(sv.NET_SALES - raw.NS) < 1 AND sv.SHIPPED_UNITS = raw.SU AND sv.POS_UNITS = raw.PU
           AND ABS(sv.TRADE_SPEND - raw.TS) < 1 AND ABS(sv.PROMO_SPEND - raw.PS) < 1,
           'OK: semantic view totals = base tables', 'CHECK: totals differ') AS RECONCILE, sv.*, raw.*
FROM sv, raw;

-- 2b) end-of-week stock: on-hand for the whole history must equal the LAST week only (not a sum)
SELECT IFF(ABS(sv.RETAILER_ON_HAND_UNITS - last_week.U) < 1, 'OK: on-hand is the latest week', 'CHECK: on-hand summed across weeks') AS STOCK_CHECK,
       sv.RETAILER_ON_HAND_UNITS, last_week.U AS LATEST_WEEK_ON_HAND
FROM SEMANTIC_VIEW(WBR_DB.CPG_DEMO.CPG_ANALYTICS_SV METRICS trade.retailer_on_hand_units) sv,
     (SELECT SUM(RETAILER_ON_HAND_UNITS) AS U FROM CPG_FACT_SELLTHROUGH_WEEK
      WHERE WEEK_START_DATE = (SELECT MAX(WEEK_START_DATE) FROM CPG_FACT_SELLTHROUGH_WEEK)) last_week;

SET LAST_WE = (SELECT MAX(C_WEEK_ENDING) FROM WBR_DB.CPG_DEMO.SV_SRC_WEEKS);
SET W16 = (SELECT DATEADD('week', -16, $LAST_WE));
SET W18 = (SELECT DATEADD('week', -18, $LAST_WE));
SET W20 = (SELECT DATEADD('week', -20, $LAST_WE));
SET W36 = (SELECT DATEADD('week', -36, $LAST_WE));

-- 3) planted stories (see DEMO_GUIDE in the INFERA pack; not loaded into document search)
-- C2 Running Shoes, wholesale: sell-in +10% while sell-through -11% (last 18 weeks vs the 18 before);
--    weeks of supply ~12 -> ~20 (all wholesale products ~11)
SELECT * FROM SEMANTIC_VIEW(WBR_DB.CPG_DEMO.CPG_ANALYTICS_SV
  METRICS trade.shipped_units, trade.pos_units, trade.sell_through_ratio, trade.weeks_of_supply
  WHERE products.product_name = 'Running Shoes' AND accounts.channel = 'Wholesale'
    AND weeks.week_ending > $W18);
SELECT * FROM SEMANTIC_VIEW(WBR_DB.CPG_DEMO.CPG_ANALYTICS_SV
  METRICS trade.shipped_units, trade.pos_units, trade.sell_through_ratio, trade.weeks_of_supply
  WHERE products.product_name = 'Running Shoes' AND accounts.channel = 'Wholesale'
    AND weeks.week_ending > $W36 AND weeks.week_ending <= $W18);
-- C1 Off-Price Channel net sales up ~60% (last 16 weeks vs the 16 before; others +4% to +9%), margin ~47% -> ~41%
SELECT * FROM SEMANTIC_VIEW(WBR_DB.CPG_DEMO.CPG_ANALYTICS_SV
  DIMENSIONS accounts.customer_name
  METRICS trade.net_sales, trade.gross_margin_pct
  WHERE weeks.week_ending > $W16
) ORDER BY 2 DESC;
-- C3 Womens Leggings: DTC net sales up ~30% while wholesale ~+5% (last 20 weeks vs the 20 before)
SELECT * FROM SEMANTIC_VIEW(WBR_DB.CPG_DEMO.CPG_ANALYTICS_SV
  DIMENSIONS accounts.channel
  METRICS trade.net_sales
  WHERE products.product_name = 'Womens Leggings' AND weeks.week_ending > $W20
);
-- Promotion events (one row per event, last 52 weeks): about a quarter lose money (ROI below 0)
SELECT COUNT(*) AS EVENTS, COUNT_IF(PROMO_ROI < 0) AS LOSING_EVENTS FROM SEMANTIC_VIEW(WBR_DB.CPG_DEMO.CPG_ANALYTICS_SV
  DIMENSIONS promotions.promo_id
  METRICS promotions.promo_spend, promotions.promo_roi
  WHERE weeks.week_ending > DATEADD('week', -52, (SELECT MAX(C_WEEK_ENDING) FROM WBR_DB.CPG_DEMO.SV_SRC_WEEKS))
);
