-- =====================================================================================
-- Harborline Outfitters (fictional) - Step 4: validation (read-only)
-- =====================================================================================
USE ROLE WBR_OWNER;
USE WAREHOUSE POWERHOUSE;
USE SCHEMA WBR_DB.RETAIL_DEMO;

-- 1) live feed: volumes, latest visible order vs now (US Eastern)
SELECT COUNT(*) AS LINES_VISIBLE, COUNT(DISTINCT ORDER_ID) AS ORDERS_VISIBLE, MIN(ORDER_DATE) AS FIRST_DAY,
       MAX(ORDER_TS) AS LATEST_ORDER_TS,
       CONVERT_TIMEZONE('America/New_York', CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS NOW_EASTERN
FROM V_SALES;

-- 2) yearly business shape (should look like a ~$300M omnichannel retailer)
SELECT YEAR(ORDER_DATE) AS YR, ROUND(SUM(NET_SALES) / 1e6, 1) AS NET_SALES_M,
       COUNT(DISTINCT ORDER_ID) AS ORDERS, ROUND(SUM(NET_SALES) / COUNT(DISTINCT ORDER_ID), 2) AS AOV,
       ROUND(SUM(QTY) / COUNT(DISTINCT ORDER_ID), 2) AS UPT,
       ROUND(SUM(NET_SALES - COGS) / SUM(NET_SALES), 3) AS GM_PCT,
       ROUND(SUM(DISCOUNT_AMOUNT) / SUM(GROSS_SALES), 3) AS DISC_RATE,
       ROUND(SUM(RETURNED_SALES) / SUM(NET_SALES), 3) AS RETURN_RATE,
       ROUND(SUM(IFF(IS_ONLINE, NET_SALES, 0)) / SUM(NET_SALES), 3) AS ONLINE_SHARE,
       ROUND(AVG(CASE WHEN ON_TIME_FLAG THEN 1 WHEN NOT ON_TIME_FLAG THEN 0 END), 3) AS ON_TIME,
       ROUND(AVG(DELIVERY_DAYS), 2) AS AVG_DELIVERY_DAYS
FROM V_SALES GROUP BY 1 ORDER BY 1;

-- 3) semantic view: sales + inventory + plan in ONE governed query, last complete month by region
SELECT * FROM SEMANTIC_VIEW(
  WBR_DB.RETAIL_DEMO.RETAIL_ANALYTICS_SV
  DIMENSIONS regions.region
  METRICS sales.net_sales, plan.plan_net_sales, sales.units_sold, inventory.avg_units_on_hand,
          inventory.weeks_of_supply, inventory.in_stock_rate, sales.free_shipping_order_pct,
          sales.avg_delivery_days, sales.on_time_delivery_pct, sales.gross_margin_pct
  WHERE dates.calendar_date >= DATEADD(month, -1, DATE_TRUNC('month', CURRENT_DATE()))
    AND dates.calendar_date < DATE_TRUNC('month', CURRENT_DATE())
) ORDER BY 1;

-- 4) planted stories
-- 4a West footwear in-stock rate by month (drops Aug-Oct 2026)
SELECT * FROM SEMANTIC_VIEW(
  WBR_DB.RETAIL_DEMO.RETAIL_ANALYTICS_SV
  DIMENSIONS dates.month_start, regions.region, categories.category
  METRICS inventory.in_stock_rate, inventory.lost_sales_units
  WHERE dates.calendar_date >= '2026-05-01' AND categories.category = 'Footwear'
) ORDER BY 1, 2;
-- 4b Southeast USPS on-time by month (drops from Aug 2026)
SELECT * FROM SEMANTIC_VIEW(
  WBR_DB.RETAIL_DEMO.RETAIL_ANALYTICS_SV
  DIMENSIONS dates.month_start, sales.carrier
  METRICS sales.on_time_delivery_pct, sales.avg_delivery_days
  WHERE dates.calendar_date >= '2026-05-01' AND regions.region = 'Southeast' AND sales.channel <> 'Store'
) ORDER BY 1, 2;
-- 4c plan attainment by region, 2026 YTD (Southwest misses)
SELECT r.REGION_NAME, ROUND(SUM(s.NET_SALES) / 1e6, 2) AS ACTUAL_M, ROUND(p.PLAN_M, 2) AS PLAN_M,
       ROUND(SUM(s.NET_SALES) / 1e6 / p.PLAN_M, 3) AS ATTAINMENT
FROM V_SALES s JOIN DIM_REGION r ON r.REGION_ID = s.REGION_ID
JOIN (SELECT REGION_ID, SUM(PLAN_NET_SALES) / 1e6 AS PLAN_M FROM PLAN_DAILY
      WHERE DATE_KEY BETWEEN '2026-01-01' AND CONVERT_TIMEZONE('America/New_York', CURRENT_TIMESTAMP())::DATE - 1 GROUP BY 1) p
  ON p.REGION_ID = s.REGION_ID
WHERE s.ORDER_DATE BETWEEN '2026-01-01' AND CONVERT_TIMEZONE('America/New_York', CURRENT_TIMESTAMP())::DATE - 1
GROUP BY r.REGION_NAME, p.PLAN_M ORDER BY 1;
-- 4d free-shipping % and AOV around the threshold change (1 Mar 2026)
SELECT DATE_TRUNC('month', ORDER_DATE) AS MONTH,
       ROUND(COUNT(DISTINCT IFF(FREE_SHIPPING_FLAG, ORDER_ID, NULL)) / NULLIF(COUNT(DISTINCT IFF(IS_SHIPPED_ORDER, ORDER_ID, NULL)), 0), 3) AS FREE_SHIP_PCT,
       ROUND(SUM(IFF(IS_ONLINE, NET_SALES, 0)) / NULLIF(COUNT(DISTINCT IFF(IS_ONLINE, ORDER_ID, NULL)), 0), 2) AS ONLINE_AOV
FROM V_SALES WHERE ORDER_DATE BETWEEN '2025-11-01' AND '2026-06-30' GROUP BY 1 ORDER BY 1;

-- 5) which dimensions are valid for an inventory metric (used by the app's validator)
SHOW SEMANTIC DIMENSIONS IN WBR_DB.RETAIL_DEMO.RETAIL_ANALYTICS_SV FOR METRIC avg_units_on_hand;
SELECT 'validation complete' AS STATUS;
