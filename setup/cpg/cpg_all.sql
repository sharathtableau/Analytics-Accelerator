-- =====================================================================================
-- Apex Athletic (FICTIONAL athletic apparel / footwear brand selling through retailers)
-- Step 1: schema, stage and raw tables. Data = the INFERA vertical pack (synthetic, seeded,
-- 104 weeks ending 2026-09-14). CSVs are uploaded by run_cpg_setup.cmd (PUT), then copied in
-- by 01b_copy.sql. Nothing here is real company data.
-- =====================================================================================
USE ROLE WBR_OWNER;
USE WAREHOUSE POWERHOUSE;
CREATE SCHEMA IF NOT EXISTS WBR_DB.CPG_DEMO
  COMMENT = 'Apex Athletic: fictional athletic apparel brand (sell-in vs sell-through), synthetic weekly data for demos';
USE SCHEMA WBR_DB.CPG_DEMO;

CREATE OR REPLACE FILE FORMAT CPG_CSV
  TYPE = CSV FIELD_OPTIONALLY_ENCLOSED_BY = '"' SKIP_HEADER = 1 EMPTY_FIELD_AS_NULL = TRUE;
CREATE STAGE IF NOT EXISTS CPG_DATA_STAGE FILE_FORMAT = CPG_CSV COMMENT = 'Apex Athletic (fictional) CSV files';

CREATE OR REPLACE TABLE CPG_DIM_CUSTOMER (
  CUSTOMER_ID VARCHAR, CUSTOMER_NAME VARCHAR, CHANNEL VARCHAR, REGION_SCOPE VARCHAR,
  REVENUE_MIX_PCT NUMBER(9,3), PAYMENT_TERMS_DAYS NUMBER(5,0));
CREATE OR REPLACE TABLE CPG_DIM_PRODUCT (
  PRODUCT_ID VARCHAR, PRODUCT_NAME VARCHAR, PRODUCT_CATEGORY VARCHAR, GENDER_SEGMENT VARCHAR,
  REVENUE_MIX_PCT NUMBER(9,3), TARGET_GROSS_MARGIN_PCT NUMBER(9,3), SEASONALITY_INDEX NUMBER(9,3), MSRP_USD NUMBER(12,2));
CREATE OR REPLACE TABLE CPG_FACT_SELLIN_WEEK (
  WEEK_START_DATE DATE, FISCAL_YEAR NUMBER(4,0), FISCAL_WEEK NUMBER(2,0), CUSTOMER_ID VARCHAR, PRODUCT_ID VARCHAR,
  SHIPPED_UNITS NUMBER(12,0), GROSS_SALES NUMBER(18,2), TRADE_SPEND NUMBER(18,2), NET_SALES NUMBER(18,2),
  GROSS_MARGIN_PCT NUMBER(9,3), RETURN_UNITS NUMBER(12,0), RETURN_DOLLARS NUMBER(18,2), AVG_SELLING_PRICE NUMBER(12,2),
  FILL_RATE_PCT NUMBER(9,3), OTIF_PCT NUMBER(9,3), PROMO_FLAG NUMBER(1,0));
CREATE OR REPLACE TABLE CPG_FACT_SELLTHROUGH_WEEK (
  WEEK_START_DATE DATE, CUSTOMER_ID VARCHAR, PRODUCT_ID VARCHAR, POS_UNITS NUMBER(12,0), POS_DOLLARS NUMBER(18,2),
  RETAILER_ON_HAND_UNITS NUMBER(12,0), WEEKS_OF_SUPPLY NUMBER(9,3), ACV_DISTRIBUTION_PCT NUMBER(9,3),
  AVG_RETAIL_PRICE NUMBER(12,2), RETAIL_PROMO_FLAG NUMBER(1,0));
CREATE OR REPLACE TABLE CPG_FACT_TRADE_PROMO (
  PROMO_ID VARCHAR, WEEK_START_DATE DATE, DURATION_WEEKS NUMBER(3,0), CUSTOMER_ID VARCHAR, PRODUCT_ID VARCHAR,
  PROMO_TYPE VARCHAR, TRADE_SPEND NUMBER(18,2), INCREMENTAL_REVENUE NUMBER(18,2), VOLUME_LIFT_PCT NUMBER(9,3),
  PROMO_ROI_PCT NUMBER(9,3));
PUT 'file://C:/Users/SharathKumarKammari/Downloads/snowflake-react-app-runtime/Analytics_Accelerator_Enterprise_Claude/setup/cpg/data/*.csv' @WBR_DB.CPG_DEMO.CPG_DATA_STAGE OVERWRITE = TRUE;
-- Step 1b (runs after the PUT of data\*.csv): load the files, then check the row counts.
USE SCHEMA WBR_DB.CPG_DEMO;
COPY INTO CPG_DIM_CUSTOMER FROM @CPG_DATA_STAGE/cpg_dim_customer.csv ON_ERROR = ABORT_STATEMENT;
COPY INTO CPG_DIM_PRODUCT FROM @CPG_DATA_STAGE/cpg_dim_product.csv ON_ERROR = ABORT_STATEMENT;
COPY INTO CPG_FACT_SELLIN_WEEK FROM @CPG_DATA_STAGE/cpg_fact_sellin_week.csv ON_ERROR = ABORT_STATEMENT;
COPY INTO CPG_FACT_SELLTHROUGH_WEEK FROM @CPG_DATA_STAGE/cpg_fact_sellthrough_week.csv ON_ERROR = ABORT_STATEMENT;
COPY INTO CPG_FACT_TRADE_PROMO FROM @CPG_DATA_STAGE/cpg_fact_trade_promo.csv ON_ERROR = ABORT_STATEMENT;

-- expected: 10, 12, 12480, 12480, 140
SELECT 'CPG_DIM_CUSTOMER' AS TABLE_NAME, COUNT(*) AS ROWS_LOADED, 10 AS EXPECTED FROM CPG_DIM_CUSTOMER
UNION ALL SELECT 'CPG_DIM_PRODUCT', COUNT(*), 12 FROM CPG_DIM_PRODUCT
UNION ALL SELECT 'CPG_FACT_SELLIN_WEEK', COUNT(*), 12480 FROM CPG_FACT_SELLIN_WEEK
UNION ALL SELECT 'CPG_FACT_SELLTHROUGH_WEEK', COUNT(*), 12480 FROM CPG_FACT_SELLTHROUGH_WEEK
UNION ALL SELECT 'CPG_FACT_TRADE_PROMO', COUNT(*), 140 FROM CPG_FACT_TRADE_PROMO;
-- =====================================================================================
-- Apex Athletic (fictional) - Step 2: rolling-date views (the semantic view's sources)
-- Same approach as finance: every row moves forward by whole weeks so the newest week is always the LAST FULL
-- WEEK (Mon-Sun) before today; weeks are dated by their week ending (Sunday). Sell-in and sell-through have the
-- same grain (week x account x product, 12,480 rows each, 1:1), so they are one source: sell-through ratio and
-- weeks of supply are then exact within one table.
-- =====================================================================================
USE ROLE WBR_OWNER;
USE WAREHOUSE POWERHOUSE;
USE SCHEMA WBR_DB.CPG_DEMO;

CREATE OR REPLACE VIEW V_WEEK_SHIFT
  COMMENT = 'Whole weeks added to the pack dates so the newest week is the last full Mon-Sun week'
AS
SELECT GREATEST(0, FLOOR(DATEDIFF('day',
         (SELECT MAX(WEEK_START_DATE) FROM WBR_DB.CPG_DEMO.CPG_FACT_SELLIN_WEEK),
         DATEADD('day', -(DAYOFWEEKISO(CURRENT_DATE()) - 1) - 7, CURRENT_DATE())) / 7))::INT AS SHIFT_WEEKS;

CREATE OR REPLACE VIEW SV_SRC_WEEKS COMMENT = 'Calendar of the weekly data (rolling)' AS
WITH w AS (
  SELECT DISTINCT DATEADD('day', 7 * s.SHIFT_WEEKS + 6, f.WEEK_START_DATE) AS WE
  FROM WBR_DB.CPG_DEMO.CPG_FACT_SELLIN_WEEK f CROSS JOIN WBR_DB.CPG_DEMO.V_WEEK_SHIFT s)
SELECT WE AS C_WEEK_ENDING,
       DATEADD('day', -6, WE) AS C_WEEK_START,
       DATE_TRUNC('month', WE) AS C_MONTH_START,
       TO_CHAR(WE, 'Mon YYYY') AS C_MONTH_NAME,
       YEAR(WE) || '-Q' || QUARTER(WE) AS C_QUARTER,
       YEAR(WE) AS C_YEAR,
       WEEKISO(DATEADD('day', -6, WE)) AS C_WEEK_OF_YEAR
FROM w;

CREATE OR REPLACE VIEW SV_SRC_CUSTOMER AS
SELECT CUSTOMER_ID AS C_CUSTOMER_ID, CUSTOMER_NAME AS C_CUSTOMER_NAME, CHANNEL AS C_CHANNEL,
       REGION_SCOPE AS C_REGION_SCOPE,
       CASE WHEN CHANNEL = 'DTC' THEN 'Direct to consumer' WHEN CUSTOMER_NAME ILIKE '%off-price%' THEN 'Off-price'
            ELSE 'Wholesale partner' END AS C_ACCOUNT_TYPE
FROM WBR_DB.CPG_DEMO.CPG_DIM_CUSTOMER;

CREATE OR REPLACE VIEW SV_SRC_PRODUCT AS
SELECT PRODUCT_ID AS C_PRODUCT_ID, PRODUCT_NAME AS C_PRODUCT_NAME, PRODUCT_CATEGORY AS C_PRODUCT_CATEGORY,
       GENDER_SEGMENT AS C_GENDER_SEGMENT
FROM WBR_DB.CPG_DEMO.CPG_DIM_PRODUCT;

-- Sell-in (what Apex ships and books) + sell-through (what consumers buy at retail) per week x account x product.
-- Percent columns become weighted helpers so rates are never plain-averaged.
CREATE OR REPLACE VIEW SV_SRC_ACCOUNT_WEEK AS
SELECT DATEADD('day', 7 * s.SHIFT_WEEKS + 6, i.WEEK_START_DATE) AS C_WEEK_ENDING,
       i.CUSTOMER_ID AS C_CUSTOMER_ID, i.PRODUCT_ID AS C_PRODUCT_ID,
       i.SHIPPED_UNITS AS C_SHIPPED_UNITS, i.GROSS_SALES AS C_GROSS_SALES, i.TRADE_SPEND AS C_TRADE_SPEND,
       i.NET_SALES AS C_NET_SALES, i.NET_SALES * i.GROSS_MARGIN_PCT / 100 AS C_GROSS_MARGIN_DOLLARS,
       i.RETURN_UNITS AS C_RETURN_UNITS, i.RETURN_DOLLARS AS C_RETURN_DOLLARS,
       i.FILL_RATE_PCT / 100 * i.SHIPPED_UNITS AS C_FILL_X_UNITS, i.OTIF_PCT / 100 * i.SHIPPED_UNITS AS C_OTIF_X_UNITS,
       IFF(c.CHANNEL = 'DTC', i.NET_SALES, 0) AS C_DTC_NET_SALES,
       IFF(c.CUSTOMER_NAME ILIKE '%off-price%', i.NET_SALES, 0) AS C_OFF_PRICE_NET_SALES,
       i.PROMO_FLAG AS C_PROMO_FLAG,
       t.POS_UNITS AS C_POS_UNITS, t.POS_DOLLARS AS C_POS_DOLLARS, t.RETAILER_ON_HAND_UNITS AS C_ON_HAND_UNITS,
       t.ACV_DISTRIBUTION_PCT / 100 * t.POS_DOLLARS AS C_ACV_X_POS_DOLLARS
FROM WBR_DB.CPG_DEMO.CPG_FACT_SELLIN_WEEK i
JOIN WBR_DB.CPG_DEMO.CPG_FACT_SELLTHROUGH_WEEK t
  ON t.WEEK_START_DATE = i.WEEK_START_DATE AND t.CUSTOMER_ID = i.CUSTOMER_ID AND t.PRODUCT_ID = i.PRODUCT_ID
JOIN WBR_DB.CPG_DEMO.CPG_DIM_CUSTOMER c ON c.CUSTOMER_ID = i.CUSTOMER_ID
CROSS JOIN WBR_DB.CPG_DEMO.V_WEEK_SHIFT s;

-- Trade promotions: one row per event, dated by the week it starts.
CREATE OR REPLACE VIEW SV_SRC_PROMO AS
SELECT p.PROMO_ID AS C_PROMO_ID, DATEADD('day', 7 * s.SHIFT_WEEKS + 6, p.WEEK_START_DATE) AS C_WEEK_ENDING,
       p.CUSTOMER_ID AS C_CUSTOMER_ID, p.PRODUCT_ID AS C_PRODUCT_ID, p.PROMO_TYPE AS C_PROMO_TYPE,
       p.DURATION_WEEKS AS C_DURATION_WEEKS, p.TRADE_SPEND AS C_PROMO_SPEND, p.INCREMENTAL_REVENUE AS C_INCREMENTAL_REVENUE,
       p.PROMO_ROI_PCT / 100 * p.TRADE_SPEND AS C_ROI_X_SPEND, p.VOLUME_LIFT_PCT / 100 * p.TRADE_SPEND AS C_LIFT_X_SPEND
FROM WBR_DB.CPG_DEMO.CPG_FACT_TRADE_PROMO p
CROSS JOIN WBR_DB.CPG_DEMO.V_WEEK_SHIFT s;

SELECT SHIFT_WEEKS, (SELECT MIN(C_WEEK_ENDING) FROM SV_SRC_WEEKS) AS FIRST_WEEK_ENDING,
       (SELECT MAX(C_WEEK_ENDING) FROM SV_SRC_WEEKS) AS LAST_WEEK_ENDING, CURRENT_DATE() AS TODAY
FROM V_WEEK_SHIFT;
-- =====================================================================================
-- Apex Athletic (fictional) - Step 3: CPG_ANALYTICS_SV (generated by build_cpg_sv.py)
-- Created from the richest definition this account supports: 1) end-of-week stock + AI instructions,
-- 2) end-of-week stock without AI instructions, 3) without the end-of-week stock metric.
-- =====================================================================================
USE ROLE WBR_OWNER;
USE WAREHOUSE POWERHOUSE;
USE SCHEMA WBR_DB.CPG_DEMO;
CREATE OR REPLACE TABLE SV_DDL (ATTEMPT NUMBER, NAME VARCHAR, DDL VARCHAR);
INSERT INTO SV_DDL VALUES (1, 'full: end-of-week stock + AI instructions', $$CREATE OR REPLACE SEMANTIC VIEW WBR_DB.CPG_DEMO.CPG_ANALYTICS_SV
  TABLES (
    weeks AS WBR_DB.CPG_DEMO.SV_SRC_WEEKS PRIMARY KEY (C_WEEK_ENDING)
      WITH SYNONYMS ('calendar', 'week') COMMENT = 'Weekly calendar. Every row covers Monday to Sunday and is dated by the Sunday the week ends; a week belongs to the month it ends in.',
    accounts AS WBR_DB.CPG_DEMO.SV_SRC_CUSTOMER PRIMARY KEY (C_CUSTOMER_ID)
      WITH SYNONYMS ('customers', 'retailers', 'retail partners') COMMENT = 'Ten accounts: eight wholesale retail partners (one is the off-price channel) and two direct-to-consumer channels.',
    products AS WBR_DB.CPG_DEMO.SV_SRC_PRODUCT PRIMARY KEY (C_PRODUCT_ID)
      WITH SYNONYMS ('product lines', 'SKUs', 'styles') COMMENT = 'Twelve product lines across apparel, footwear and accessories.',
    trade AS WBR_DB.CPG_DEMO.SV_SRC_ACCOUNT_WEEK PRIMARY KEY (C_WEEK_ENDING, C_CUSTOMER_ID, C_PRODUCT_ID)
      WITH SYNONYMS ('sell-in', 'shipments', 'sell-through', 'POS')
      COMMENT = 'Weekly sell-in (what Apex ships and books as revenue) and sell-through (what consumers buy at the retailer) per account and product line.',
    promotions AS WBR_DB.CPG_DEMO.SV_SRC_PROMO PRIMARY KEY (C_PROMO_ID)
      WITH SYNONYMS ('trade promotions', 'promo events', 'deals')
      COMMENT = 'Trade promotion events: type, spend, incremental revenue, lift and ROI, dated by the week they start.'
  )
  RELATIONSHIPS (
    trade_to_weeks AS trade (C_WEEK_ENDING) REFERENCES weeks,
    trade_to_accounts AS trade (C_CUSTOMER_ID) REFERENCES accounts,
    trade_to_products AS trade (C_PRODUCT_ID) REFERENCES products,
    promotions_to_weeks AS promotions (C_WEEK_ENDING) REFERENCES weeks,
    promotions_to_accounts AS promotions (C_CUSTOMER_ID) REFERENCES accounts,
    promotions_to_products AS promotions (C_PRODUCT_ID) REFERENCES products
  )
  FACTS (
    trade.f_shipped_units AS C_SHIPPED_UNITS,
    trade.f_gross_sales AS C_GROSS_SALES,
    trade.f_trade_spend AS C_TRADE_SPEND,
    trade.f_net_sales AS C_NET_SALES,
    trade.f_gross_margin_dollars AS C_GROSS_MARGIN_DOLLARS,
    trade.f_return_units AS C_RETURN_UNITS,
    trade.f_return_dollars AS C_RETURN_DOLLARS,
    trade.f_fill_x_units AS C_FILL_X_UNITS,
    trade.f_otif_x_units AS C_OTIF_X_UNITS,
    trade.f_dtc_net_sales AS C_DTC_NET_SALES,
    trade.f_off_price_net_sales AS C_OFF_PRICE_NET_SALES,
    trade.f_pos_units AS C_POS_UNITS,
    trade.f_pos_dollars AS C_POS_DOLLARS,
    trade.f_on_hand_units AS C_ON_HAND_UNITS,
    trade.f_acv_x_pos_dollars AS C_ACV_X_POS_DOLLARS,
    promotions.f_promo_id AS C_PROMO_ID,
    promotions.f_promo_spend AS C_PROMO_SPEND,
    promotions.f_incremental_revenue AS C_INCREMENTAL_REVENUE,
    promotions.f_roi_x_spend AS C_ROI_X_SPEND,
    promotions.f_lift_x_spend AS C_LIFT_X_SPEND
  )
  DIMENSIONS (
    weeks.week_ending AS C_WEEK_ENDING WITH SYNONYMS = ('week', 'week ending', 'date')
      COMMENT = 'Sunday that ends the week. Use for all time filtering; the newest week is the last full week.',
    weeks.week_start AS C_WEEK_START COMMENT = 'Monday that starts the week.',
    weeks.month_start AS C_MONTH_START WITH SYNONYMS = ('month') COMMENT = 'First day of the month the week ends in.',
    weeks.month_name AS C_MONTH_NAME COMMENT = 'Month label, e.g. Oct 2026.',
    weeks.calendar_quarter AS C_QUARTER WITH SYNONYMS = ('quarter', 'fiscal quarter') COMMENT = 'Calendar quarter, e.g. 2026-Q3.',
    weeks.calendar_year AS C_YEAR WITH SYNONYMS = ('year', 'fiscal year') COMMENT = 'Calendar (= fiscal) year.',
    weeks.week_of_year AS C_WEEK_OF_YEAR COMMENT = 'ISO week number.',
    accounts.customer_name AS C_CUSTOMER_NAME WITH SYNONYMS = ('account', 'customer', 'retailer', 'retail partner')
      COMMENT = 'Account name, e.g. National Sporting Chain, Off-Price Channel, Apex.com DTC.',
    accounts.channel AS C_CHANNEL WITH SYNONYMS = ('sales channel', 'wholesale or DTC')
      COMMENT = 'Wholesale or DTC (direct to consumer). Exclude DTC when analysing channel inventory.',
    accounts.account_type AS C_ACCOUNT_TYPE COMMENT = 'Wholesale partner, Off-price or Direct to consumer.',
    accounts.region_scope AS C_REGION_SCOPE WITH SYNONYMS = ('coverage') COMMENT = 'National, Regional, Digital, Intl or Owned.',
    products.product_name AS C_PRODUCT_NAME WITH SYNONYMS = ('product', 'product line', 'style')
      COMMENT = 'Product line, e.g. Running Shoes, Womens Leggings.',
    products.product_category AS C_PRODUCT_CATEGORY WITH SYNONYMS = ('category') COMMENT = 'Apparel, Footwear or Accessories.',
    products.gender_segment AS C_GENDER_SEGMENT WITH SYNONYMS = ('gender', 'consumer segment') COMMENT = 'Mens, Womens, Unisex or Team.',
    promotions.promo_type AS C_PROMO_TYPE WITH SYNONYMS = ('promotion type', 'tactic')
      COMMENT = 'TPR, Feature, Display, Feature+Display, Endcap or BOGO.',
    promotions.promo_id AS C_PROMO_ID WITH SYNONYMS = ('promotion', 'promotion event', 'event')
      COMMENT = 'One promotion event (e.g. PROMO-3000). Use it to judge promotions event by event.'
  )
  METRICS (
    trade.gross_sales AS SUM(trade.f_gross_sales) WITH SYNONYMS = ('gross revenue', 'gross shipments')
      COMMENT = 'Sell-in gross sales before trade spend (USD).',
    trade.trade_spend AS SUM(trade.f_trade_spend) WITH SYNONYMS = ('trade', 'trade investment')
      COMMENT = 'Trade spend deducted from gross sales (USD).',
    trade.net_sales AS SUM(trade.f_net_sales) WITH SYNONYMS = ('revenue', 'sell-in revenue', 'net revenue')
      COMMENT = 'Sell-in net sales = gross sales - trade spend (USD). What finance calls revenue.',
    trade.trade_spend_rate AS DIV0(trade.trade_spend, trade.gross_sales) WITH SYNONYMS = ('trade rate', 'trade spend %')
      COMMENT = 'Trade spend / gross sales.',
    trade.shipped_units AS SUM(trade.f_shipped_units) WITH SYNONYMS = ('sell-in units', 'shipments')
      COMMENT = 'Units shipped to accounts (sell-in).',
    trade.gross_margin_dollars AS SUM(trade.f_gross_margin_dollars) WITH SYNONYMS = ('gross margin', 'gross profit')
      COMMENT = 'Gross margin on sell-in net sales (USD).',
    trade.gross_margin_pct AS DIV0(trade.gross_margin_dollars, trade.net_sales) WITH SYNONYMS = ('margin rate', 'GM%')
      COMMENT = 'Gross margin / net sales (weighted by net sales, never averaged).',
    trade.average_selling_price AS DIV0(trade.gross_sales, trade.shipped_units) WITH SYNONYMS = ('ASP', 'wholesale price')
      COMMENT = 'Gross sales / shipped units (USD).',
    trade.return_dollars AS SUM(trade.f_return_dollars) COMMENT = 'Returns (USD).',
    trade.returns_rate AS DIV0(trade.return_dollars, trade.gross_sales) WITH SYNONYMS = ('return rate', 'returns %')
      COMMENT = 'Returns / gross sales. Above 6% is a returns spike.',
    trade.helper_fill_x_units AS SUM(trade.f_fill_x_units) COMMENT = 'Helper: fill rate x shipped units.',
    trade.helper_otif_x_units AS SUM(trade.f_otif_x_units) COMMENT = 'Helper: OTIF x shipped units.',
    trade.fill_rate AS DIV0(trade.helper_fill_x_units, trade.shipped_units) WITH SYNONYMS = ('fill rate %', 'case fill')
      COMMENT = 'Share of ordered units shipped (weighted by shipped units). Below 95% is a breach.',
    trade.otif_rate AS DIV0(trade.helper_otif_x_units, trade.shipped_units) WITH SYNONYMS = ('OTIF', 'on time in full')
      COMMENT = 'On-time-in-full delivery rate (weighted by shipped units). Below 90% is a breach.',
    trade.dtc_net_sales AS SUM(trade.f_dtc_net_sales) WITH SYNONYMS = ('DTC sales', 'direct to consumer sales')
      COMMENT = 'Net sales through the direct-to-consumer accounts (USD).',
    trade.dtc_mix AS DIV0(trade.dtc_net_sales, trade.net_sales) WITH SYNONYMS = ('DTC share', 'DTC mix %')
      COMMENT = 'DTC net sales / total net sales.',
    trade.off_price_net_sales AS SUM(trade.f_off_price_net_sales) COMMENT = 'Net sales through the off-price channel (USD).',
    trade.off_price_mix AS DIV0(trade.off_price_net_sales, trade.net_sales) WITH SYNONYMS = ('off-price share', 'off-price mix %')
      COMMENT = 'Off-price net sales / total. Growth here is a warning: excess inventory being cleared at lower margin.',
    trade.pos_units AS SUM(trade.f_pos_units) WITH SYNONYMS = ('sell-through units', 'consumer units', 'POS units')
      COMMENT = 'Units consumers bought at the retailer (sell-through).',
    trade.pos_dollars AS SUM(trade.f_pos_dollars) WITH SYNONYMS = ('POS sales', 'consumer sales', 'retail sales')
      COMMENT = 'Consumer purchases at retail (USD).',
    trade.sell_through_ratio AS DIV0(trade.pos_units, trade.shipped_units) WITH SYNONYMS = ('sell-through rate', 'sell-thru')
      COMMENT = 'POS units / shipped units over the same weeks. Healthy 0.9 to 1.1; below means stock is building at the retailer.',
    trade.retailer_on_hand_units NON ADDITIVE BY (weeks.week_ending) AS SUM(trade.f_on_hand_units) WITH SYNONYMS = ('retailer inventory', 'channel inventory', 'on hand')
      COMMENT = 'Units on hand at the retailers at the end of the latest week in the period.',
    trade.helper_on_hand_weeks AS SUM(trade.f_on_hand_units) COMMENT = 'Helper: weekly on-hand units summed over weeks.',
    trade.weeks_of_supply AS DIV0(trade.helper_on_hand_weeks, trade.pos_units) WITH SYNONYMS = ('WOS', 'weeks of cover')
      COMMENT = 'Average retailer on-hand units / average weekly POS units. Healthy 6 to 12; above 14 is inventory bloat. Exclude DTC.',
    trade.helper_acv_x_pos AS SUM(trade.f_acv_x_pos_dollars) COMMENT = 'Helper: ACV x POS dollars.',
    trade.acv_distribution AS DIV0(trade.helper_acv_x_pos, trade.pos_dollars) WITH SYNONYMS = ('ACV', 'distribution', 'ACV %')
      COMMENT = 'Share of all-commodity volume carrying the item (weighted by POS dollars). A distribution measure, not a sales measure.',
    trade.average_retail_price AS DIV0(trade.pos_dollars, trade.pos_units) COMMENT = 'POS dollars / POS units (USD).',
    promotions.promo_count AS COUNT(DISTINCT promotions.f_promo_id) WITH SYNONYMS = ('promotions', 'events')
      COMMENT = 'Number of promotion events.',
    promotions.promo_spend AS SUM(promotions.f_promo_spend) WITH SYNONYMS = ('promotion spend', 'promo trade spend')
      COMMENT = 'Trade spend on promotion events (USD).',
    promotions.incremental_revenue AS SUM(promotions.f_incremental_revenue) WITH SYNONYMS = ('incremental sales', 'promo lift revenue')
      COMMENT = 'Revenue above the non-promoted baseline (USD).',
    promotions.helper_roi_x_spend AS SUM(promotions.f_roi_x_spend) COMMENT = 'Helper: promo ROI x spend.',
    promotions.helper_lift_x_spend AS SUM(promotions.f_lift_x_spend) COMMENT = 'Helper: volume lift x spend.',
    promotions.promo_roi AS DIV0(promotions.helper_roi_x_spend, promotions.promo_spend) WITH SYNONYMS = ('promotion ROI', 'ROI')
      COMMENT = 'Promotion ROI (spend-weighted). Below 0 means the promotion lost money.',
    promotions.volume_lift AS DIV0(promotions.helper_lift_x_spend, promotions.promo_spend) WITH SYNONYMS = ('lift', 'promo lift')
      COMMENT = 'Promotion volume lift vs the non-promoted baseline (spend-weighted).'
  )
  COMMENT = 'Apex Athletic (fictional athletic brand): sell-in vs sell-through, account inventory health, margin, service levels and trade promotions. Weekly, rolling to the last full week.'
  AI_SQL_GENERATION 'Apex Athletic is a fictional athletic apparel and footwear brand selling through retail accounts and its own DTC channels. Data is weekly; weeks run Monday to Sunday and are dated by week_ending; filter time on weeks.week_ending. Revenue means sell-in net_sales; how are we selling usually means sell-through (POS). Sell-in is lumpy (accounts order about every four weeks): never read one week of sell-in as a trend, use 4 or 13 weeks. For DTC accounts sell-in equals sell-through, so exclude DTC (accounts.channel = Wholesale) for channel inventory, weeks of supply and sell-through ratio. Trade spend is already deducted from net sales. Retailer on-hand units are end-of-week stocks: never sum them across weeks. Rates are fractions and already weighted; never average a rate. Off-price growth is a warning (excess inventory cleared at lower margin), not a win. ACV distribution can rise while sales fall: that is a velocity problem.'$$);
INSERT INTO SV_DDL VALUES (2, 'end-of-week stock, no AI instructions', $$CREATE OR REPLACE SEMANTIC VIEW WBR_DB.CPG_DEMO.CPG_ANALYTICS_SV
  TABLES (
    weeks AS WBR_DB.CPG_DEMO.SV_SRC_WEEKS PRIMARY KEY (C_WEEK_ENDING)
      WITH SYNONYMS ('calendar', 'week') COMMENT = 'Weekly calendar. Every row covers Monday to Sunday and is dated by the Sunday the week ends; a week belongs to the month it ends in.',
    accounts AS WBR_DB.CPG_DEMO.SV_SRC_CUSTOMER PRIMARY KEY (C_CUSTOMER_ID)
      WITH SYNONYMS ('customers', 'retailers', 'retail partners') COMMENT = 'Ten accounts: eight wholesale retail partners (one is the off-price channel) and two direct-to-consumer channels.',
    products AS WBR_DB.CPG_DEMO.SV_SRC_PRODUCT PRIMARY KEY (C_PRODUCT_ID)
      WITH SYNONYMS ('product lines', 'SKUs', 'styles') COMMENT = 'Twelve product lines across apparel, footwear and accessories.',
    trade AS WBR_DB.CPG_DEMO.SV_SRC_ACCOUNT_WEEK PRIMARY KEY (C_WEEK_ENDING, C_CUSTOMER_ID, C_PRODUCT_ID)
      WITH SYNONYMS ('sell-in', 'shipments', 'sell-through', 'POS')
      COMMENT = 'Weekly sell-in (what Apex ships and books as revenue) and sell-through (what consumers buy at the retailer) per account and product line.',
    promotions AS WBR_DB.CPG_DEMO.SV_SRC_PROMO PRIMARY KEY (C_PROMO_ID)
      WITH SYNONYMS ('trade promotions', 'promo events', 'deals')
      COMMENT = 'Trade promotion events: type, spend, incremental revenue, lift and ROI, dated by the week they start.'
  )
  RELATIONSHIPS (
    trade_to_weeks AS trade (C_WEEK_ENDING) REFERENCES weeks,
    trade_to_accounts AS trade (C_CUSTOMER_ID) REFERENCES accounts,
    trade_to_products AS trade (C_PRODUCT_ID) REFERENCES products,
    promotions_to_weeks AS promotions (C_WEEK_ENDING) REFERENCES weeks,
    promotions_to_accounts AS promotions (C_CUSTOMER_ID) REFERENCES accounts,
    promotions_to_products AS promotions (C_PRODUCT_ID) REFERENCES products
  )
  FACTS (
    trade.f_shipped_units AS C_SHIPPED_UNITS,
    trade.f_gross_sales AS C_GROSS_SALES,
    trade.f_trade_spend AS C_TRADE_SPEND,
    trade.f_net_sales AS C_NET_SALES,
    trade.f_gross_margin_dollars AS C_GROSS_MARGIN_DOLLARS,
    trade.f_return_units AS C_RETURN_UNITS,
    trade.f_return_dollars AS C_RETURN_DOLLARS,
    trade.f_fill_x_units AS C_FILL_X_UNITS,
    trade.f_otif_x_units AS C_OTIF_X_UNITS,
    trade.f_dtc_net_sales AS C_DTC_NET_SALES,
    trade.f_off_price_net_sales AS C_OFF_PRICE_NET_SALES,
    trade.f_pos_units AS C_POS_UNITS,
    trade.f_pos_dollars AS C_POS_DOLLARS,
    trade.f_on_hand_units AS C_ON_HAND_UNITS,
    trade.f_acv_x_pos_dollars AS C_ACV_X_POS_DOLLARS,
    promotions.f_promo_id AS C_PROMO_ID,
    promotions.f_promo_spend AS C_PROMO_SPEND,
    promotions.f_incremental_revenue AS C_INCREMENTAL_REVENUE,
    promotions.f_roi_x_spend AS C_ROI_X_SPEND,
    promotions.f_lift_x_spend AS C_LIFT_X_SPEND
  )
  DIMENSIONS (
    weeks.week_ending AS C_WEEK_ENDING WITH SYNONYMS = ('week', 'week ending', 'date')
      COMMENT = 'Sunday that ends the week. Use for all time filtering; the newest week is the last full week.',
    weeks.week_start AS C_WEEK_START COMMENT = 'Monday that starts the week.',
    weeks.month_start AS C_MONTH_START WITH SYNONYMS = ('month') COMMENT = 'First day of the month the week ends in.',
    weeks.month_name AS C_MONTH_NAME COMMENT = 'Month label, e.g. Oct 2026.',
    weeks.calendar_quarter AS C_QUARTER WITH SYNONYMS = ('quarter', 'fiscal quarter') COMMENT = 'Calendar quarter, e.g. 2026-Q3.',
    weeks.calendar_year AS C_YEAR WITH SYNONYMS = ('year', 'fiscal year') COMMENT = 'Calendar (= fiscal) year.',
    weeks.week_of_year AS C_WEEK_OF_YEAR COMMENT = 'ISO week number.',
    accounts.customer_name AS C_CUSTOMER_NAME WITH SYNONYMS = ('account', 'customer', 'retailer', 'retail partner')
      COMMENT = 'Account name, e.g. National Sporting Chain, Off-Price Channel, Apex.com DTC.',
    accounts.channel AS C_CHANNEL WITH SYNONYMS = ('sales channel', 'wholesale or DTC')
      COMMENT = 'Wholesale or DTC (direct to consumer). Exclude DTC when analysing channel inventory.',
    accounts.account_type AS C_ACCOUNT_TYPE COMMENT = 'Wholesale partner, Off-price or Direct to consumer.',
    accounts.region_scope AS C_REGION_SCOPE WITH SYNONYMS = ('coverage') COMMENT = 'National, Regional, Digital, Intl or Owned.',
    products.product_name AS C_PRODUCT_NAME WITH SYNONYMS = ('product', 'product line', 'style')
      COMMENT = 'Product line, e.g. Running Shoes, Womens Leggings.',
    products.product_category AS C_PRODUCT_CATEGORY WITH SYNONYMS = ('category') COMMENT = 'Apparel, Footwear or Accessories.',
    products.gender_segment AS C_GENDER_SEGMENT WITH SYNONYMS = ('gender', 'consumer segment') COMMENT = 'Mens, Womens, Unisex or Team.',
    promotions.promo_type AS C_PROMO_TYPE WITH SYNONYMS = ('promotion type', 'tactic')
      COMMENT = 'TPR, Feature, Display, Feature+Display, Endcap or BOGO.',
    promotions.promo_id AS C_PROMO_ID WITH SYNONYMS = ('promotion', 'promotion event', 'event')
      COMMENT = 'One promotion event (e.g. PROMO-3000). Use it to judge promotions event by event.'
  )
  METRICS (
    trade.gross_sales AS SUM(trade.f_gross_sales) WITH SYNONYMS = ('gross revenue', 'gross shipments')
      COMMENT = 'Sell-in gross sales before trade spend (USD).',
    trade.trade_spend AS SUM(trade.f_trade_spend) WITH SYNONYMS = ('trade', 'trade investment')
      COMMENT = 'Trade spend deducted from gross sales (USD).',
    trade.net_sales AS SUM(trade.f_net_sales) WITH SYNONYMS = ('revenue', 'sell-in revenue', 'net revenue')
      COMMENT = 'Sell-in net sales = gross sales - trade spend (USD). What finance calls revenue.',
    trade.trade_spend_rate AS DIV0(trade.trade_spend, trade.gross_sales) WITH SYNONYMS = ('trade rate', 'trade spend %')
      COMMENT = 'Trade spend / gross sales.',
    trade.shipped_units AS SUM(trade.f_shipped_units) WITH SYNONYMS = ('sell-in units', 'shipments')
      COMMENT = 'Units shipped to accounts (sell-in).',
    trade.gross_margin_dollars AS SUM(trade.f_gross_margin_dollars) WITH SYNONYMS = ('gross margin', 'gross profit')
      COMMENT = 'Gross margin on sell-in net sales (USD).',
    trade.gross_margin_pct AS DIV0(trade.gross_margin_dollars, trade.net_sales) WITH SYNONYMS = ('margin rate', 'GM%')
      COMMENT = 'Gross margin / net sales (weighted by net sales, never averaged).',
    trade.average_selling_price AS DIV0(trade.gross_sales, trade.shipped_units) WITH SYNONYMS = ('ASP', 'wholesale price')
      COMMENT = 'Gross sales / shipped units (USD).',
    trade.return_dollars AS SUM(trade.f_return_dollars) COMMENT = 'Returns (USD).',
    trade.returns_rate AS DIV0(trade.return_dollars, trade.gross_sales) WITH SYNONYMS = ('return rate', 'returns %')
      COMMENT = 'Returns / gross sales. Above 6% is a returns spike.',
    trade.helper_fill_x_units AS SUM(trade.f_fill_x_units) COMMENT = 'Helper: fill rate x shipped units.',
    trade.helper_otif_x_units AS SUM(trade.f_otif_x_units) COMMENT = 'Helper: OTIF x shipped units.',
    trade.fill_rate AS DIV0(trade.helper_fill_x_units, trade.shipped_units) WITH SYNONYMS = ('fill rate %', 'case fill')
      COMMENT = 'Share of ordered units shipped (weighted by shipped units). Below 95% is a breach.',
    trade.otif_rate AS DIV0(trade.helper_otif_x_units, trade.shipped_units) WITH SYNONYMS = ('OTIF', 'on time in full')
      COMMENT = 'On-time-in-full delivery rate (weighted by shipped units). Below 90% is a breach.',
    trade.dtc_net_sales AS SUM(trade.f_dtc_net_sales) WITH SYNONYMS = ('DTC sales', 'direct to consumer sales')
      COMMENT = 'Net sales through the direct-to-consumer accounts (USD).',
    trade.dtc_mix AS DIV0(trade.dtc_net_sales, trade.net_sales) WITH SYNONYMS = ('DTC share', 'DTC mix %')
      COMMENT = 'DTC net sales / total net sales.',
    trade.off_price_net_sales AS SUM(trade.f_off_price_net_sales) COMMENT = 'Net sales through the off-price channel (USD).',
    trade.off_price_mix AS DIV0(trade.off_price_net_sales, trade.net_sales) WITH SYNONYMS = ('off-price share', 'off-price mix %')
      COMMENT = 'Off-price net sales / total. Growth here is a warning: excess inventory being cleared at lower margin.',
    trade.pos_units AS SUM(trade.f_pos_units) WITH SYNONYMS = ('sell-through units', 'consumer units', 'POS units')
      COMMENT = 'Units consumers bought at the retailer (sell-through).',
    trade.pos_dollars AS SUM(trade.f_pos_dollars) WITH SYNONYMS = ('POS sales', 'consumer sales', 'retail sales')
      COMMENT = 'Consumer purchases at retail (USD).',
    trade.sell_through_ratio AS DIV0(trade.pos_units, trade.shipped_units) WITH SYNONYMS = ('sell-through rate', 'sell-thru')
      COMMENT = 'POS units / shipped units over the same weeks. Healthy 0.9 to 1.1; below means stock is building at the retailer.',
    trade.retailer_on_hand_units NON ADDITIVE BY (weeks.week_ending) AS SUM(trade.f_on_hand_units) WITH SYNONYMS = ('retailer inventory', 'channel inventory', 'on hand')
      COMMENT = 'Units on hand at the retailers at the end of the latest week in the period.',
    trade.helper_on_hand_weeks AS SUM(trade.f_on_hand_units) COMMENT = 'Helper: weekly on-hand units summed over weeks.',
    trade.weeks_of_supply AS DIV0(trade.helper_on_hand_weeks, trade.pos_units) WITH SYNONYMS = ('WOS', 'weeks of cover')
      COMMENT = 'Average retailer on-hand units / average weekly POS units. Healthy 6 to 12; above 14 is inventory bloat. Exclude DTC.',
    trade.helper_acv_x_pos AS SUM(trade.f_acv_x_pos_dollars) COMMENT = 'Helper: ACV x POS dollars.',
    trade.acv_distribution AS DIV0(trade.helper_acv_x_pos, trade.pos_dollars) WITH SYNONYMS = ('ACV', 'distribution', 'ACV %')
      COMMENT = 'Share of all-commodity volume carrying the item (weighted by POS dollars). A distribution measure, not a sales measure.',
    trade.average_retail_price AS DIV0(trade.pos_dollars, trade.pos_units) COMMENT = 'POS dollars / POS units (USD).',
    promotions.promo_count AS COUNT(DISTINCT promotions.f_promo_id) WITH SYNONYMS = ('promotions', 'events')
      COMMENT = 'Number of promotion events.',
    promotions.promo_spend AS SUM(promotions.f_promo_spend) WITH SYNONYMS = ('promotion spend', 'promo trade spend')
      COMMENT = 'Trade spend on promotion events (USD).',
    promotions.incremental_revenue AS SUM(promotions.f_incremental_revenue) WITH SYNONYMS = ('incremental sales', 'promo lift revenue')
      COMMENT = 'Revenue above the non-promoted baseline (USD).',
    promotions.helper_roi_x_spend AS SUM(promotions.f_roi_x_spend) COMMENT = 'Helper: promo ROI x spend.',
    promotions.helper_lift_x_spend AS SUM(promotions.f_lift_x_spend) COMMENT = 'Helper: volume lift x spend.',
    promotions.promo_roi AS DIV0(promotions.helper_roi_x_spend, promotions.promo_spend) WITH SYNONYMS = ('promotion ROI', 'ROI')
      COMMENT = 'Promotion ROI (spend-weighted). Below 0 means the promotion lost money.',
    promotions.volume_lift AS DIV0(promotions.helper_lift_x_spend, promotions.promo_spend) WITH SYNONYMS = ('lift', 'promo lift')
      COMMENT = 'Promotion volume lift vs the non-promoted baseline (spend-weighted).'
  )
  COMMENT = 'Apex Athletic (fictional athletic brand): sell-in vs sell-through, account inventory health, margin, service levels and trade promotions. Weekly, rolling to the last full week.'$$);
INSERT INTO SV_DDL VALUES (3, 'no end-of-week stock metric', $$CREATE OR REPLACE SEMANTIC VIEW WBR_DB.CPG_DEMO.CPG_ANALYTICS_SV
  TABLES (
    weeks AS WBR_DB.CPG_DEMO.SV_SRC_WEEKS PRIMARY KEY (C_WEEK_ENDING)
      WITH SYNONYMS ('calendar', 'week') COMMENT = 'Weekly calendar. Every row covers Monday to Sunday and is dated by the Sunday the week ends; a week belongs to the month it ends in.',
    accounts AS WBR_DB.CPG_DEMO.SV_SRC_CUSTOMER PRIMARY KEY (C_CUSTOMER_ID)
      WITH SYNONYMS ('customers', 'retailers', 'retail partners') COMMENT = 'Ten accounts: eight wholesale retail partners (one is the off-price channel) and two direct-to-consumer channels.',
    products AS WBR_DB.CPG_DEMO.SV_SRC_PRODUCT PRIMARY KEY (C_PRODUCT_ID)
      WITH SYNONYMS ('product lines', 'SKUs', 'styles') COMMENT = 'Twelve product lines across apparel, footwear and accessories.',
    trade AS WBR_DB.CPG_DEMO.SV_SRC_ACCOUNT_WEEK PRIMARY KEY (C_WEEK_ENDING, C_CUSTOMER_ID, C_PRODUCT_ID)
      WITH SYNONYMS ('sell-in', 'shipments', 'sell-through', 'POS')
      COMMENT = 'Weekly sell-in (what Apex ships and books as revenue) and sell-through (what consumers buy at the retailer) per account and product line.',
    promotions AS WBR_DB.CPG_DEMO.SV_SRC_PROMO PRIMARY KEY (C_PROMO_ID)
      WITH SYNONYMS ('trade promotions', 'promo events', 'deals')
      COMMENT = 'Trade promotion events: type, spend, incremental revenue, lift and ROI, dated by the week they start.'
  )
  RELATIONSHIPS (
    trade_to_weeks AS trade (C_WEEK_ENDING) REFERENCES weeks,
    trade_to_accounts AS trade (C_CUSTOMER_ID) REFERENCES accounts,
    trade_to_products AS trade (C_PRODUCT_ID) REFERENCES products,
    promotions_to_weeks AS promotions (C_WEEK_ENDING) REFERENCES weeks,
    promotions_to_accounts AS promotions (C_CUSTOMER_ID) REFERENCES accounts,
    promotions_to_products AS promotions (C_PRODUCT_ID) REFERENCES products
  )
  FACTS (
    trade.f_shipped_units AS C_SHIPPED_UNITS,
    trade.f_gross_sales AS C_GROSS_SALES,
    trade.f_trade_spend AS C_TRADE_SPEND,
    trade.f_net_sales AS C_NET_SALES,
    trade.f_gross_margin_dollars AS C_GROSS_MARGIN_DOLLARS,
    trade.f_return_units AS C_RETURN_UNITS,
    trade.f_return_dollars AS C_RETURN_DOLLARS,
    trade.f_fill_x_units AS C_FILL_X_UNITS,
    trade.f_otif_x_units AS C_OTIF_X_UNITS,
    trade.f_dtc_net_sales AS C_DTC_NET_SALES,
    trade.f_off_price_net_sales AS C_OFF_PRICE_NET_SALES,
    trade.f_pos_units AS C_POS_UNITS,
    trade.f_pos_dollars AS C_POS_DOLLARS,
    trade.f_on_hand_units AS C_ON_HAND_UNITS,
    trade.f_acv_x_pos_dollars AS C_ACV_X_POS_DOLLARS,
    promotions.f_promo_id AS C_PROMO_ID,
    promotions.f_promo_spend AS C_PROMO_SPEND,
    promotions.f_incremental_revenue AS C_INCREMENTAL_REVENUE,
    promotions.f_roi_x_spend AS C_ROI_X_SPEND,
    promotions.f_lift_x_spend AS C_LIFT_X_SPEND
  )
  DIMENSIONS (
    weeks.week_ending AS C_WEEK_ENDING WITH SYNONYMS = ('week', 'week ending', 'date')
      COMMENT = 'Sunday that ends the week. Use for all time filtering; the newest week is the last full week.',
    weeks.week_start AS C_WEEK_START COMMENT = 'Monday that starts the week.',
    weeks.month_start AS C_MONTH_START WITH SYNONYMS = ('month') COMMENT = 'First day of the month the week ends in.',
    weeks.month_name AS C_MONTH_NAME COMMENT = 'Month label, e.g. Oct 2026.',
    weeks.calendar_quarter AS C_QUARTER WITH SYNONYMS = ('quarter', 'fiscal quarter') COMMENT = 'Calendar quarter, e.g. 2026-Q3.',
    weeks.calendar_year AS C_YEAR WITH SYNONYMS = ('year', 'fiscal year') COMMENT = 'Calendar (= fiscal) year.',
    weeks.week_of_year AS C_WEEK_OF_YEAR COMMENT = 'ISO week number.',
    accounts.customer_name AS C_CUSTOMER_NAME WITH SYNONYMS = ('account', 'customer', 'retailer', 'retail partner')
      COMMENT = 'Account name, e.g. National Sporting Chain, Off-Price Channel, Apex.com DTC.',
    accounts.channel AS C_CHANNEL WITH SYNONYMS = ('sales channel', 'wholesale or DTC')
      COMMENT = 'Wholesale or DTC (direct to consumer). Exclude DTC when analysing channel inventory.',
    accounts.account_type AS C_ACCOUNT_TYPE COMMENT = 'Wholesale partner, Off-price or Direct to consumer.',
    accounts.region_scope AS C_REGION_SCOPE WITH SYNONYMS = ('coverage') COMMENT = 'National, Regional, Digital, Intl or Owned.',
    products.product_name AS C_PRODUCT_NAME WITH SYNONYMS = ('product', 'product line', 'style')
      COMMENT = 'Product line, e.g. Running Shoes, Womens Leggings.',
    products.product_category AS C_PRODUCT_CATEGORY WITH SYNONYMS = ('category') COMMENT = 'Apparel, Footwear or Accessories.',
    products.gender_segment AS C_GENDER_SEGMENT WITH SYNONYMS = ('gender', 'consumer segment') COMMENT = 'Mens, Womens, Unisex or Team.',
    promotions.promo_type AS C_PROMO_TYPE WITH SYNONYMS = ('promotion type', 'tactic')
      COMMENT = 'TPR, Feature, Display, Feature+Display, Endcap or BOGO.',
    promotions.promo_id AS C_PROMO_ID WITH SYNONYMS = ('promotion', 'promotion event', 'event')
      COMMENT = 'One promotion event (e.g. PROMO-3000). Use it to judge promotions event by event.'
  )
  METRICS (
    trade.gross_sales AS SUM(trade.f_gross_sales) WITH SYNONYMS = ('gross revenue', 'gross shipments')
      COMMENT = 'Sell-in gross sales before trade spend (USD).',
    trade.trade_spend AS SUM(trade.f_trade_spend) WITH SYNONYMS = ('trade', 'trade investment')
      COMMENT = 'Trade spend deducted from gross sales (USD).',
    trade.net_sales AS SUM(trade.f_net_sales) WITH SYNONYMS = ('revenue', 'sell-in revenue', 'net revenue')
      COMMENT = 'Sell-in net sales = gross sales - trade spend (USD). What finance calls revenue.',
    trade.trade_spend_rate AS DIV0(trade.trade_spend, trade.gross_sales) WITH SYNONYMS = ('trade rate', 'trade spend %')
      COMMENT = 'Trade spend / gross sales.',
    trade.shipped_units AS SUM(trade.f_shipped_units) WITH SYNONYMS = ('sell-in units', 'shipments')
      COMMENT = 'Units shipped to accounts (sell-in).',
    trade.gross_margin_dollars AS SUM(trade.f_gross_margin_dollars) WITH SYNONYMS = ('gross margin', 'gross profit')
      COMMENT = 'Gross margin on sell-in net sales (USD).',
    trade.gross_margin_pct AS DIV0(trade.gross_margin_dollars, trade.net_sales) WITH SYNONYMS = ('margin rate', 'GM%')
      COMMENT = 'Gross margin / net sales (weighted by net sales, never averaged).',
    trade.average_selling_price AS DIV0(trade.gross_sales, trade.shipped_units) WITH SYNONYMS = ('ASP', 'wholesale price')
      COMMENT = 'Gross sales / shipped units (USD).',
    trade.return_dollars AS SUM(trade.f_return_dollars) COMMENT = 'Returns (USD).',
    trade.returns_rate AS DIV0(trade.return_dollars, trade.gross_sales) WITH SYNONYMS = ('return rate', 'returns %')
      COMMENT = 'Returns / gross sales. Above 6% is a returns spike.',
    trade.helper_fill_x_units AS SUM(trade.f_fill_x_units) COMMENT = 'Helper: fill rate x shipped units.',
    trade.helper_otif_x_units AS SUM(trade.f_otif_x_units) COMMENT = 'Helper: OTIF x shipped units.',
    trade.fill_rate AS DIV0(trade.helper_fill_x_units, trade.shipped_units) WITH SYNONYMS = ('fill rate %', 'case fill')
      COMMENT = 'Share of ordered units shipped (weighted by shipped units). Below 95% is a breach.',
    trade.otif_rate AS DIV0(trade.helper_otif_x_units, trade.shipped_units) WITH SYNONYMS = ('OTIF', 'on time in full')
      COMMENT = 'On-time-in-full delivery rate (weighted by shipped units). Below 90% is a breach.',
    trade.dtc_net_sales AS SUM(trade.f_dtc_net_sales) WITH SYNONYMS = ('DTC sales', 'direct to consumer sales')
      COMMENT = 'Net sales through the direct-to-consumer accounts (USD).',
    trade.dtc_mix AS DIV0(trade.dtc_net_sales, trade.net_sales) WITH SYNONYMS = ('DTC share', 'DTC mix %')
      COMMENT = 'DTC net sales / total net sales.',
    trade.off_price_net_sales AS SUM(trade.f_off_price_net_sales) COMMENT = 'Net sales through the off-price channel (USD).',
    trade.off_price_mix AS DIV0(trade.off_price_net_sales, trade.net_sales) WITH SYNONYMS = ('off-price share', 'off-price mix %')
      COMMENT = 'Off-price net sales / total. Growth here is a warning: excess inventory being cleared at lower margin.',
    trade.pos_units AS SUM(trade.f_pos_units) WITH SYNONYMS = ('sell-through units', 'consumer units', 'POS units')
      COMMENT = 'Units consumers bought at the retailer (sell-through).',
    trade.pos_dollars AS SUM(trade.f_pos_dollars) WITH SYNONYMS = ('POS sales', 'consumer sales', 'retail sales')
      COMMENT = 'Consumer purchases at retail (USD).',
    trade.sell_through_ratio AS DIV0(trade.pos_units, trade.shipped_units) WITH SYNONYMS = ('sell-through rate', 'sell-thru')
      COMMENT = 'POS units / shipped units over the same weeks. Healthy 0.9 to 1.1; below means stock is building at the retailer.',
    trade.helper_on_hand_weeks AS SUM(trade.f_on_hand_units) COMMENT = 'Helper: weekly on-hand units summed over weeks.',
    trade.weeks_of_supply AS DIV0(trade.helper_on_hand_weeks, trade.pos_units) WITH SYNONYMS = ('WOS', 'weeks of cover')
      COMMENT = 'Average retailer on-hand units / average weekly POS units. Healthy 6 to 12; above 14 is inventory bloat. Exclude DTC.',
    trade.helper_acv_x_pos AS SUM(trade.f_acv_x_pos_dollars) COMMENT = 'Helper: ACV x POS dollars.',
    trade.acv_distribution AS DIV0(trade.helper_acv_x_pos, trade.pos_dollars) WITH SYNONYMS = ('ACV', 'distribution', 'ACV %')
      COMMENT = 'Share of all-commodity volume carrying the item (weighted by POS dollars). A distribution measure, not a sales measure.',
    trade.average_retail_price AS DIV0(trade.pos_dollars, trade.pos_units) COMMENT = 'POS dollars / POS units (USD).',
    promotions.promo_count AS COUNT(DISTINCT promotions.f_promo_id) WITH SYNONYMS = ('promotions', 'events')
      COMMENT = 'Number of promotion events.',
    promotions.promo_spend AS SUM(promotions.f_promo_spend) WITH SYNONYMS = ('promotion spend', 'promo trade spend')
      COMMENT = 'Trade spend on promotion events (USD).',
    promotions.incremental_revenue AS SUM(promotions.f_incremental_revenue) WITH SYNONYMS = ('incremental sales', 'promo lift revenue')
      COMMENT = 'Revenue above the non-promoted baseline (USD).',
    promotions.helper_roi_x_spend AS SUM(promotions.f_roi_x_spend) COMMENT = 'Helper: promo ROI x spend.',
    promotions.helper_lift_x_spend AS SUM(promotions.f_lift_x_spend) COMMENT = 'Helper: volume lift x spend.',
    promotions.promo_roi AS DIV0(promotions.helper_roi_x_spend, promotions.promo_spend) WITH SYNONYMS = ('promotion ROI', 'ROI')
      COMMENT = 'Promotion ROI (spend-weighted). Below 0 means the promotion lost money.',
    promotions.volume_lift AS DIV0(promotions.helper_lift_x_spend, promotions.promo_spend) WITH SYNONYMS = ('lift', 'promo lift')
      COMMENT = 'Promotion volume lift vs the non-promoted baseline (spend-weighted).'
  )
  COMMENT = 'Apex Athletic (fictional athletic brand): sell-in vs sell-through, account inventory health, margin, service levels and trade promotions. Weekly, rolling to the last full week.'$$);

EXECUTE IMMEDIATE $$
DECLARE
  c CURSOR FOR SELECT ATTEMPT, NAME, DDL FROM WBR_DB.CPG_DEMO.SV_DDL ORDER BY ATTEMPT;
  errs VARCHAR DEFAULT '';
  stmt VARCHAR;
BEGIN
  FOR r IN c DO
    stmt := r.DDL;
    BEGIN
      EXECUTE IMMEDIATE :stmt;
      RETURN 'CPG_ANALYTICS_SV created (' || r.NAME || ')' || IFF(errs = '', '', ' | earlier attempts: ' || errs);
    EXCEPTION
      WHEN OTHER THEN
        errs := errs || '[' || r.ATTEMPT || '] ' || LEFT(SQLERRM, 300) || ' ';
    END;
  END FOR;
  RETURN 'FAILED: ' || errs;
END;
$$;

DESCRIBE SEMANTIC VIEW WBR_DB.CPG_DEMO.CPG_ANALYTICS_SV;
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
-- Apex Athletic documents -> Cortex Search. Part 1: stage (the PUT of docs\*.md follows).
USE ROLE WBR_OWNER;
USE WAREHOUSE POWERHOUSE;
USE SCHEMA WBR_DB.CPG_DEMO;
CREATE STAGE IF NOT EXISTS CPG_DOCS_STAGE
  DIRECTORY = (ENABLE = TRUE) ENCRYPTION = (TYPE = 'SNOWFLAKE_SSE')
  COMMENT = 'Apex Athletic (fictional) business ontology: personas, metric dictionary, alert library, business rules';
PUT 'file://C:/Users/SharathKumarKammari/Downloads/snowflake-react-app-runtime/Analytics_Accelerator_Enterprise_Claude/setup/cpg/docs/*.md' @WBR_DB.CPG_DEMO.CPG_DOCS_STAGE AUTO_COMPRESS = FALSE OVERWRITE = TRUE;
-- Part 2 (after the PUT): markdown -> chunks (+ metric glossary from the semantic view) -> Cortex Search.
-- The INFERA pack's DEMO_GUIDE (planted signals) is deliberately NOT loaded: it would give the answers away.
USE SCHEMA WBR_DB.CPG_DEMO;
ALTER STAGE CPG_DOCS_STAGE REFRESH;
SELECT RELATIVE_PATH, SIZE FROM DIRECTORY(@CPG_DOCS_STAGE) ORDER BY 1;

CREATE OR REPLACE FILE FORMAT FF_LINES TYPE = CSV FIELD_DELIMITER = NONE RECORD_DELIMITER = '\n'
  SKIP_BLANK_LINES = FALSE FIELD_OPTIONALLY_ENCLOSED_BY = NONE ESCAPE_UNENCLOSED_FIELD = NONE;
CREATE OR REPLACE TABLE CPG_DOCS_PARSED AS
SELECT METADATA$FILENAME AS FILE_NAME,
       LISTAGG(COALESCE($1, ''), '\n') WITHIN GROUP (ORDER BY METADATA$FILE_ROW_NUMBER) AS CONTENT
FROM @CPG_DOCS_STAGE (FILE_FORMAT => 'WBR_DB.CPG_DEMO.FF_LINES', PATTERN => '.*[.]md')
GROUP BY METADATA$FILENAME;
SELECT FILE_NAME, LENGTH(CONTENT) AS CHARS FROM CPG_DOCS_PARSED ORDER BY 1;

-- Chunk with SPLIT_TEXT_RECURSIVE_CHARACTER (markdown-aware). Fallback: one chunk per section heading.
CREATE OR REPLACE TABLE CPG_DOCS (
  DOC_ID STRING, TITLE STRING, DOC_TYPE STRING, SOURCE STRING, CHUNK_NO INT, CHUNK STRING);
EXECUTE IMMEDIATE $$
BEGIN
  INSERT INTO WBR_DB.CPG_DEMO.CPG_DOCS
  SELECT 'APX-ONTOLOGY', 'Apex Athletic business ontology', 'business definitions', p.FILE_NAME, c.INDEX, c.VALUE::STRING
  FROM WBR_DB.CPG_DEMO.CPG_DOCS_PARSED p,
       LATERAL FLATTEN(SNOWFLAKE.CORTEX.SPLIT_TEXT_RECURSIVE_CHARACTER(p.CONTENT, 'markdown', 1200, 150)) c;
  RETURN 'Chunked with SPLIT_TEXT_RECURSIVE_CHARACTER';
EXCEPTION WHEN OTHER THEN
  INSERT INTO WBR_DB.CPG_DEMO.CPG_DOCS
  SELECT 'APX-ONTOLOGY', 'Apex Athletic business ontology', 'business definitions', p.FILE_NAME, s.INDEX,
         '## ' || s.VALUE::STRING
  FROM WBR_DB.CPG_DEMO.CPG_DOCS_PARSED p, LATERAL FLATTEN(SPLIT(p.CONTENT, '\n## ')) s;
  RETURN 'SPLIT_TEXT_RECURSIVE_CHARACTER unavailable - chunked by section heading';
END;
$$;

-- Metric glossary straight from the semantic view, so definitions in search = definitions in the dashboard.
DESCRIBE SEMANTIC VIEW WBR_DB.CPG_DEMO.CPG_ANALYTICS_SV;
INSERT INTO CPG_DOCS
SELECT 'GLOSSARY', 'Metric definition: ' || INITCAP(REPLACE("object_name", '_', ' ')), 'metric definition',
       'CPG_ANALYTICS_SV', 0,
       'Metric ' || INITCAP(REPLACE("object_name", '_', ' ')) || ' (' || "object_name" || '): ' || "property_value"
FROM TABLE(RESULT_SCAN(LAST_QUERY_ID()))
WHERE "object_kind" IN ('METRIC', 'DERIVED_METRIC') AND "property" = 'COMMENT'
  AND "object_name" NOT ILIKE 'HELPER%';
SELECT DOC_TYPE, COUNT(*) AS CHUNKS FROM CPG_DOCS GROUP BY 1 ORDER BY 1;

CREATE OR REPLACE CORTEX SEARCH SERVICE CPG_DOCS_SEARCH
  ON CHUNK
  ATTRIBUTES DOC_TYPE, TITLE, DOC_ID
  WAREHOUSE = POWERHOUSE
  TARGET_LAG = '1 day'
  COMMENT = 'Apex Athletic (fictional): personas, metric dictionary, alert library, business rules and metric glossary'
  AS SELECT CHUNK, TITLE, DOC_TYPE, DOC_ID, SOURCE, CHUNK_NO FROM CPG_DOCS;

-- Smoke tests: the definitions the demo relies on.
SELECT PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW('WBR_DB.CPG_DEMO.CPG_DOCS_SEARCH',
  '{"query": "why exclude DTC from channel inventory", "columns": ["DOC_ID", "TITLE", "CHUNK"], "limit": 2}'))['results'] AS DTC_RULE;
SELECT PARSE_JSON(SNOWFLAKE.CORTEX.SEARCH_PREVIEW('WBR_DB.CPG_DEMO.CPG_DOCS_SEARCH',
  '{"query": "weeks of supply healthy band and inventory bloat alert", "columns": ["DOC_ID", "TITLE", "CHUNK"], "limit": 2}'))['results'] AS WOS_RULE;
