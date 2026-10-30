-- =====================================================================================
-- Keystone Financial (fictional) - Step 4: checks (read-only)
-- Expected values were computed from the CSV files with the same formulas (21 Oct 2026).
-- =====================================================================================
USE ROLE WBR_OWNER;
USE WAREHOUSE POWERHOUSE;
USE SCHEMA WBR_DB.FINANCE_DEMO;

-- 1) rolling calendar: the newest week must end on the last Sunday before today
SELECT MIN(C_WEEK_ENDING) AS FIRST_WEEK_ENDING, MAX(C_WEEK_ENDING) AS LAST_WEEK_ENDING, COUNT(*) AS WEEKS,
       DATEADD('day', -DAYOFWEEKISO(CURRENT_DATE()), CURRENT_DATE()) AS LAST_SUNDAY,
       IFF(MAX(C_WEEK_ENDING) = DATEADD('day', -DAYOFWEEKISO(CURRENT_DATE()), CURRENT_DATE()), 'OK', 'CHECK') AS RESULT
FROM SV_SRC_WEEKS;

-- 2) semantic view = base tables (latest week ending balance; whole-history flows)
WITH sv AS (
  SELECT * FROM SEMANTIC_VIEW(WBR_DB.FINANCE_DEMO.FINANCE_ANALYTICS_SV
    METRICS portfolio.purchase_volume, portfolio.interchange_revenue, credit.net_chargeoffs, deposits.runoff,
            acquisition.bookings)
), raw AS (
  SELECT (SELECT SUM(PURCHASE_VOLUME) FROM FINANCE_FACT_PORTFOLIO_WEEK) AS PV,
         (SELECT SUM(INTERCHANGE_REVENUE) FROM FINANCE_FACT_PORTFOLIO_WEEK) AS IC,
         (SELECT SUM(NET_CHARGEOFF_DOLLARS) FROM FINANCE_FACT_CREDIT_WEEK) AS NCO,
         (SELECT SUM(RUNOFF_DOLLARS) FROM FINANCE_FACT_DEPOSITS_WEEK) AS RO,
         (SELECT SUM(BOOKINGS) FROM FINANCE_FACT_ACQUISITION_WEEK) AS BK
)
SELECT IFF(ABS(sv.PURCHASE_VOLUME - raw.PV) < 1 AND ABS(sv.INTERCHANGE_REVENUE - raw.IC) < 1
           AND ABS(sv.NET_CHARGEOFFS - raw.NCO) < 1 AND ABS(sv.RUNOFF - raw.RO) < 1 AND sv.BOOKINGS = raw.BK,
           'OK: semantic view totals = base tables', 'CHECK: totals differ') AS RECONCILE, sv.*, raw.*
FROM sv, raw;

-- 2b) end-of-week stock: ending balance for the whole history must equal the LAST week only (not a sum)
SELECT IFF(ABS(sv.ENDING_BALANCE - last_week.B) < 1, 'OK: ending balance is the latest week', 'CHECK: balance summed across weeks') AS STOCK_CHECK,
       sv.ENDING_BALANCE, last_week.B AS LATEST_WEEK_BALANCE
FROM SEMANTIC_VIEW(WBR_DB.FINANCE_DEMO.FINANCE_ANALYTICS_SV METRICS portfolio.ending_balance) sv,
     (SELECT SUM(ENDING_BALANCE) AS B FROM FINANCE_FACT_PORTFOLIO_WEEK
      WHERE WEEK_START_DATE = (SELECT MAX(WEEK_START_DATE) FROM FINANCE_FACT_PORTFOLIO_WEEK)) last_week;

SET RECENT_START = (SELECT DATEADD('week', -4, MAX(C_WEEK_ENDING)) FROM WBR_DB.FINANCE_DEMO.SV_SRC_WEEKS);

-- 3) planted stories (see DEMO_GUIDE in the INFERA pack; not loaded into document search)
-- F2 Near-Prime Revolver delinquency rises (~5.6% -> ~8.7% over the last 22 weeks); other segments flat
SELECT * FROM SEMANTIC_VIEW(WBR_DB.FINANCE_DEMO.FINANCE_ANALYTICS_SV
  DIMENSIONS segments.segment_name
  METRICS credit.delinquency_rate, credit.annualized_loss_rate, credit.average_fico
  WHERE weeks.week_ending > $RECENT_START
) ORDER BY 2 DESC;
-- F1 Mass Affluent Saver: the only positive rate gap (~ +0.0007 = +0.07 pts); deposit balance down ~13% in 15 weeks
SELECT * FROM SEMANTIC_VIEW(WBR_DB.FINANCE_DEMO.FINANCE_ANALYTICS_SV
  DIMENSIONS segments.segment_name
  METRICS deposits.rate_gap, deposits.rate_paid, deposits.competitor_rate, deposits.runoff_rate, deposits.net_new_money
  WHERE weeks.week_ending > $RECENT_START
) ORDER BY 2 DESC;
-- F3 Travel Signature rewards-to-interchange above the 0.85 breach line (~1.04 latest 4 weeks; others ~0.71)
SELECT * FROM SEMANTIC_VIEW(WBR_DB.FINANCE_DEMO.FINANCE_ANALYTICS_SV
  DIMENSIONS products.product_name
  METRICS portfolio.rewards_to_interchange_ratio, portfolio.interchange_revenue, portfolio.rewards_expense
  WHERE products.product_type = 'Credit Card'
    AND weeks.week_ending > $RECENT_START
) ORDER BY 2 DESC;
-- Risk-adjusted yield by segment, last 13 weeks (expect Near-Prime Revolver about -7% and Subprime Builder about -11%:
-- they lose money after losses; Prime Revolver about +11%)
SET Q_START = (SELECT DATEADD('week', -13, MAX(C_WEEK_ENDING)) FROM WBR_DB.FINANCE_DEMO.SV_SRC_WEEKS);
SELECT * FROM SEMANTIC_VIEW(WBR_DB.FINANCE_DEMO.FINANCE_ANALYTICS_SV
  DIMENSIONS segments.segment_name
  METRICS credit.risk_adjusted_yield, credit.card_revenue, credit.net_chargeoffs
  WHERE weeks.week_ending > $Q_START
) ORDER BY 2;
