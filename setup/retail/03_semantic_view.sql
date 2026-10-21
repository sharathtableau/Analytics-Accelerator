-- =====================================================================================
-- Harborline Outfitters (fictional) - Step 3: live views + semantic view
-- Rows are pre-generated to 31 Dec 2026; the views only expose what has "happened" by now
-- (US Eastern time): new orders appear minute by minute, shipments move to In transit /
-- Delivered, returns arrive, and today's inventory is drawn down by today's sales.
-- =====================================================================================
USE ROLE WBR_OWNER;
USE WAREHOUSE POWERHOUSE;
USE SCHEMA WBR_DB.RETAIL_DEMO;

CREATE OR REPLACE VIEW V_SALES
  COMMENT = 'Live order lines: only orders placed up to now; fulfillment and returns as of now'
AS
WITH n AS (SELECT CONVERT_TIMEZONE('America/New_York', CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS NOW)
SELECT l.LINE_ID, l.ORDER_ID, l.LINE_NUMBER, l.ORDER_DATE, l.ORDER_TS, HOUR(l.ORDER_TS) AS ORDER_HOUR,
       l.REGION_ID, l.CATEGORY_ID, l.SUBCATEGORY_ID, l.SKU, l.CHANNEL, l.IS_ONLINE, l.STORE_ID, l.CUSTOMER_ID,
       l.LOYALTY_TIER, l.AGE_BAND, l.CUSTOMER_STATE, l.PROMO_NAME, l.QTY, l.LIST_PRICE, l.DISCOUNT_PCT,
       l.GROSS_SALES, l.DISCOUNT_AMOUNT, l.NET_SALES, l.COGS, l.IS_SHIPPED_ORDER, l.SHIP_METHOD, l.CARRIER,
       l.FREE_SHIP_THRESHOLD, l.ORDER_SHIPPING_FEE, l.LINE_SHIPPING_FEE, l.FREE_SHIPPING_FLAG, l.PROMISED_DATE,
       IFF(l.SHIP_TS <= n.NOW, l.SHIP_TS, NULL) AS SHIP_TS,
       IFF(l.SHIP_TS <= n.NOW, l.CLICK_TO_SHIP_HOURS, NULL) AS CLICK_TO_SHIP_HOURS,
       IFF(l.DELIVERED_TS <= n.NOW, l.DELIVERED_TS, NULL) AS DELIVERED_TS,
       IFF(l.DELIVERED_TS <= n.NOW, l.TRANSIT_DAYS, NULL) AS TRANSIT_DAYS,
       IFF(l.DELIVERED_TS <= n.NOW, l.DELIVERY_DAYS, NULL) AS DELIVERY_DAYS,
       IFF(l.DELIVERED_TS <= n.NOW, l.ON_TIME_FLAG, NULL) AS ON_TIME_FLAG,
       CASE WHEN NOT l.IS_SHIPPED_ORDER THEN 'In-store purchase'
            WHEN l.DELIVERED_TS <= n.NOW THEN 'Delivered'
            WHEN l.SHIP_TS <= n.NOW THEN 'In transit' ELSE 'Processing' END AS FULFILLMENT_STATUS,
       COALESCE(l.RETURN_FLAG AND l.RETURN_TS <= n.NOW, FALSE) AS IS_RETURNED,
       IFF(l.RETURN_FLAG AND l.RETURN_TS <= n.NOW, l.NET_SALES, 0) AS RETURNED_SALES,
       IFF(l.RETURN_FLAG AND l.RETURN_TS <= n.NOW, l.QTY, 0) AS RETURNED_UNITS,
       IFF(l.RETURN_FLAG AND l.RETURN_TS <= n.NOW, l.RETURN_REASON, NULL) AS RETURN_REASON
FROM ORDER_LINES l, n
WHERE l.ORDER_TS <= n.NOW;

CREATE OR REPLACE VIEW V_INVENTORY
  COMMENT = 'Live DC inventory: closed days as recorded; today = start-of-day stock minus units sold so far'
AS
WITH n AS (SELECT CONVERT_TIMEZONE('America/New_York', CURRENT_TIMESTAMP())::TIMESTAMP_NTZ AS NOW),
today_sold AS (
  SELECT l.SKU, l.REGION_ID, SUM(l.QTY) AS UNITS
  FROM ORDER_LINES l, n
  WHERE l.ORDER_DATE = n.NOW::DATE AND l.ORDER_TS <= n.NOW
  GROUP BY 1, 2
)
SELECT i.SNAPSHOT_DATE, i.SKU, i.REGION_ID, i.CATEGORY_ID, i.SUBCATEGORY_ID, i.UNIT_COST, i.UNITS_ON_HAND,
       i.UNITS_ON_ORDER, i.UNITS_SOLD, i.LOST_UNITS, i.INVENTORY_VALUE, i.STOCKOUT_FLAG
FROM INVENTORY_DAILY i, n
WHERE i.SNAPSHOT_DATE < n.NOW::DATE
UNION ALL
SELECT i.SNAPSHOT_DATE, i.SKU, i.REGION_ID, i.CATEGORY_ID, i.SUBCATEGORY_ID, i.UNIT_COST,
       GREATEST(0, i.UNITS_ON_HAND_START - COALESCE(t.UNITS, 0)) AS UNITS_ON_HAND,
       i.UNITS_ON_ORDER, COALESCE(t.UNITS, 0) AS UNITS_SOLD, 0 AS LOST_UNITS,
       ROUND(GREATEST(0, i.UNITS_ON_HAND_START - COALESCE(t.UNITS, 0)) * i.UNIT_COST, 2) AS INVENTORY_VALUE,
       GREATEST(0, i.UNITS_ON_HAND_START - COALESCE(t.UNITS, 0)) = 0 AS STOCKOUT_FLAG
FROM INVENTORY_DAILY i
JOIN n ON i.SNAPSHOT_DATE = n.NOW::DATE
LEFT JOIN today_sold t ON t.SKU = i.SKU AND t.REGION_ID = i.REGION_ID;

-- source views with C_-prefixed columns (see note in build_sv.py)
CREATE OR REPLACE VIEW WBR_DB.RETAIL_DEMO.SV_SRC_DATE AS SELECT DATE_KEY AS C_DATE_KEY, CAL_YEAR AS C_CAL_YEAR, CAL_QUARTER AS C_CAL_QUARTER, MONTH_START AS C_MONTH_START, MONTH_NAME AS C_MONTH_NAME, MONTH_NUM AS C_MONTH_NUM, WEEK_START AS C_WEEK_START, DAY_OF_WEEK AS C_DAY_OF_WEEK, DOW_ISO AS C_DOW_ISO, IS_WEEKEND AS C_IS_WEEKEND, HOLIDAY_NAME AS C_HOLIDAY_NAME, RETAIL_SEASON AS C_RETAIL_SEASON FROM WBR_DB.RETAIL_DEMO.DIM_DATE;
CREATE OR REPLACE VIEW WBR_DB.RETAIL_DEMO.SV_SRC_REGION AS SELECT REGION_ID AS C_REGION_ID, REGION_NAME AS C_REGION_NAME, DC_NAME AS C_DC_NAME, DC_CITY AS C_DC_CITY, DC_STATE AS C_DC_STATE FROM WBR_DB.RETAIL_DEMO.DIM_REGION;
CREATE OR REPLACE VIEW WBR_DB.RETAIL_DEMO.SV_SRC_CATEGORY AS SELECT CATEGORY_ID AS C_CATEGORY_ID, CATEGORY_NAME AS C_CATEGORY_NAME FROM WBR_DB.RETAIL_DEMO.DIM_CATEGORY;
CREATE OR REPLACE VIEW WBR_DB.RETAIL_DEMO.SV_SRC_PRODUCT AS SELECT SKU AS C_SKU, PRODUCT_NAME AS C_PRODUCT_NAME, CATEGORY_ID AS C_CATEGORY_ID, SUBCATEGORY_ID AS C_SUBCATEGORY_ID, SUBCATEGORY AS C_SUBCATEGORY, BRAND AS C_BRAND, GENDER AS C_GENDER, PRICE_TIER AS C_PRICE_TIER, COLOR_FAMILY AS C_COLOR_FAMILY, LIST_PRICE AS C_LIST_PRICE, UNIT_COST AS C_UNIT_COST FROM WBR_DB.RETAIL_DEMO.DIM_PRODUCT;
CREATE OR REPLACE VIEW WBR_DB.RETAIL_DEMO.SV_SRC_STORE AS SELECT STORE_ID AS C_STORE_ID, STORE_NAME AS C_STORE_NAME, STORE_CITY AS C_STORE_CITY, STORE_STATE AS C_STORE_STATE, STORE_FORMAT AS C_STORE_FORMAT, REGION_ID AS C_REGION_ID FROM WBR_DB.RETAIL_DEMO.DIM_STORE;
CREATE OR REPLACE VIEW WBR_DB.RETAIL_DEMO.SV_SRC_SALES AS SELECT LINE_ID AS C_LINE_ID, ORDER_ID AS C_ORDER_ID, LINE_NUMBER AS C_LINE_NUMBER, ORDER_DATE AS C_ORDER_DATE, ORDER_TS AS C_ORDER_TS, ORDER_HOUR AS C_ORDER_HOUR, REGION_ID AS C_REGION_ID, CATEGORY_ID AS C_CATEGORY_ID, SUBCATEGORY_ID AS C_SUBCATEGORY_ID, SKU AS C_SKU, CHANNEL AS C_CHANNEL, IS_ONLINE AS C_IS_ONLINE, STORE_ID AS C_STORE_ID, CUSTOMER_ID AS C_CUSTOMER_ID, LOYALTY_TIER AS C_LOYALTY_TIER, AGE_BAND AS C_AGE_BAND, CUSTOMER_STATE AS C_CUSTOMER_STATE, PROMO_NAME AS C_PROMO_NAME, QTY AS C_QTY, LIST_PRICE AS C_LIST_PRICE, DISCOUNT_PCT AS C_DISCOUNT_PCT, GROSS_SALES AS C_GROSS_SALES, DISCOUNT_AMOUNT AS C_DISCOUNT_AMOUNT, NET_SALES AS C_NET_SALES, COGS AS C_COGS, IS_SHIPPED_ORDER AS C_IS_SHIPPED_ORDER, SHIP_METHOD AS C_SHIP_METHOD, CARRIER AS C_CARRIER, FREE_SHIP_THRESHOLD AS C_FREE_SHIP_THRESHOLD, ORDER_SHIPPING_FEE AS C_ORDER_SHIPPING_FEE, LINE_SHIPPING_FEE AS C_LINE_SHIPPING_FEE, FREE_SHIPPING_FLAG AS C_FREE_SHIPPING_FLAG, PROMISED_DATE AS C_PROMISED_DATE, SHIP_TS AS C_SHIP_TS, CLICK_TO_SHIP_HOURS AS C_CLICK_TO_SHIP_HOURS, DELIVERED_TS AS C_DELIVERED_TS, TRANSIT_DAYS AS C_TRANSIT_DAYS, DELIVERY_DAYS AS C_DELIVERY_DAYS, ON_TIME_FLAG AS C_ON_TIME_FLAG, FULFILLMENT_STATUS AS C_FULFILLMENT_STATUS, IS_RETURNED AS C_IS_RETURNED, RETURNED_SALES AS C_RETURNED_SALES, RETURNED_UNITS AS C_RETURNED_UNITS, RETURN_REASON AS C_RETURN_REASON FROM WBR_DB.RETAIL_DEMO.V_SALES;
CREATE OR REPLACE VIEW WBR_DB.RETAIL_DEMO.SV_SRC_INVENTORY AS SELECT SNAPSHOT_DATE AS C_SNAPSHOT_DATE, SKU AS C_SKU, REGION_ID AS C_REGION_ID, CATEGORY_ID AS C_CATEGORY_ID, SUBCATEGORY_ID AS C_SUBCATEGORY_ID, UNIT_COST AS C_UNIT_COST, UNITS_ON_HAND AS C_UNITS_ON_HAND, UNITS_ON_ORDER AS C_UNITS_ON_ORDER, UNITS_SOLD AS C_UNITS_SOLD, LOST_UNITS AS C_LOST_UNITS, INVENTORY_VALUE AS C_INVENTORY_VALUE, STOCKOUT_FLAG AS C_STOCKOUT_FLAG FROM WBR_DB.RETAIL_DEMO.V_INVENTORY;
CREATE OR REPLACE VIEW WBR_DB.RETAIL_DEMO.SV_SRC_PLAN AS SELECT DATE_KEY AS C_DATE_KEY, REGION_ID AS C_REGION_ID, CATEGORY_ID AS C_CATEGORY_ID, PLAN_NET_SALES AS C_PLAN_NET_SALES, PLAN_UNITS AS C_PLAN_UNITS, PLAN_GROSS_MARGIN AS C_PLAN_GROSS_MARGIN FROM WBR_DB.RETAIL_DEMO.PLAN_DAILY;

-- The semantic view is created from the richest definition this account supports:
-- 1) with semi-additive ending stock + cross-table plan metrics + Cortex Analyst instructions,
-- 2) without the semi-additive metric, 3) core metrics only. The result says which one won.
CREATE OR REPLACE TABLE SV_DDL (ATTEMPT NUMBER, NAME VARCHAR, DDL VARCHAR);

INSERT INTO SV_DDL VALUES (1, 'full: ending stock + plan attainment + AI instructions', $$CREATE OR REPLACE SEMANTIC VIEW WBR_DB.RETAIL_DEMO.RETAIL_ANALYTICS_SV
  TABLES (
    dates AS WBR_DB.RETAIL_DEMO.SV_SRC_DATE PRIMARY KEY (C_DATE_KEY)
      WITH SYNONYMS ('calendar', 'day') COMMENT = 'Calendar day. Weeks start Monday; fiscal year equals calendar year.',
    regions AS WBR_DB.RETAIL_DEMO.SV_SRC_REGION PRIMARY KEY (C_REGION_ID)
      WITH SYNONYMS ('territory', 'market') COMMENT = 'Five US sales regions, each served by one distribution center.',
    categories AS WBR_DB.RETAIL_DEMO.SV_SRC_CATEGORY PRIMARY KEY (C_CATEGORY_ID)
      WITH SYNONYMS ('department', 'merchandise category') COMMENT = 'Apparel, Footwear, Accessories.',
    products AS WBR_DB.RETAIL_DEMO.SV_SRC_PRODUCT PRIMARY KEY (C_SKU)
      WITH SYNONYMS ('items', 'SKUs', 'styles') COMMENT = 'Product master at SKU level (fictional house brands).',
    stores AS WBR_DB.RETAIL_DEMO.SV_SRC_STORE PRIMARY KEY (C_STORE_ID)
      WITH SYNONYMS ('shops', 'doors') COMMENT = 'Physical stores (60).',
    sales AS WBR_DB.RETAIL_DEMO.SV_SRC_SALES PRIMARY KEY (C_LINE_ID)
      WITH SYNONYMS ('orders', 'transactions', 'order lines')
      COMMENT = 'Live order lines across Store, Web, App and Marketplace. Rows appear as orders are placed; shipment, delivery and return fields update as those events happen.',
    inventory AS WBR_DB.RETAIL_DEMO.SV_SRC_INVENTORY PRIMARY KEY (C_SNAPSHOT_DATE, C_SKU, C_REGION_ID)
      WITH SYNONYMS ('stock', 'on hand')
      COMMENT = 'End-of-day inventory per SKU per regional distribution center. Today reflects stock as of now.',
    plan AS WBR_DB.RETAIL_DEMO.SV_SRC_PLAN PRIMARY KEY (C_DATE_KEY, C_REGION_ID, C_CATEGORY_ID)
      WITH SYNONYMS ('target', 'budget', 'forecast plan')
      COMMENT = 'Approved financial plan by day, region and category (monthly plan phased to days).'
  )
  RELATIONSHIPS (
    sales_to_dates AS sales (C_ORDER_DATE) REFERENCES dates,
    sales_to_regions AS sales (C_REGION_ID) REFERENCES regions,
    sales_to_categories AS sales (C_CATEGORY_ID) REFERENCES categories,
    sales_to_products AS sales (C_SKU) REFERENCES products,
    sales_to_stores AS sales (C_STORE_ID) REFERENCES stores,
    inventory_to_dates AS inventory (C_SNAPSHOT_DATE) REFERENCES dates,
    inventory_to_regions AS inventory (C_REGION_ID) REFERENCES regions,
    inventory_to_categories AS inventory (C_CATEGORY_ID) REFERENCES categories,
    inventory_to_products AS inventory (C_SKU) REFERENCES products,
    plan_to_dates AS plan (C_DATE_KEY) REFERENCES dates,
    plan_to_regions AS plan (C_REGION_ID) REFERENCES regions,
    plan_to_categories AS plan (C_CATEGORY_ID) REFERENCES categories
  )
  FACTS (
    sales.f_order_id AS C_ORDER_ID,
    sales.f_customer_id AS C_CUSTOMER_ID,
    sales.f_qty AS C_QTY,
    sales.f_gross_sales AS C_GROSS_SALES,
    sales.f_discount_amount AS C_DISCOUNT_AMOUNT,
    sales.f_net_sales AS C_NET_SALES,
    sales.f_cogs AS C_COGS,
    sales.f_gross_margin AS C_NET_SALES - C_COGS,
    sales.f_online_net_sales AS IFF(C_IS_ONLINE, C_NET_SALES, 0),
    sales.f_shipped_order_id AS IFF(C_IS_SHIPPED_ORDER, C_ORDER_ID, NULL),
    sales.f_free_ship_order_id AS IFF(C_FREE_SHIPPING_FLAG, C_ORDER_ID, NULL),
    sales.f_line_shipping_fee AS C_LINE_SHIPPING_FEE,
    sales.f_click_to_ship_hours AS C_CLICK_TO_SHIP_HOURS,
    sales.f_transit_days AS C_TRANSIT_DAYS,
    sales.f_delivery_days AS C_DELIVERY_DAYS,
    sales.f_on_time AS CASE WHEN C_ON_TIME_FLAG THEN 1 WHEN NOT C_ON_TIME_FLAG THEN 0 END,
    sales.f_returned_sales AS C_RETURNED_SALES,
    sales.f_returned_units AS C_RETURNED_UNITS,
    inventory.f_snapshot_date AS C_SNAPSHOT_DATE,
    inventory.f_units_on_hand AS C_UNITS_ON_HAND,
    inventory.f_inventory_value AS C_INVENTORY_VALUE,
    inventory.f_units_on_order AS C_UNITS_ON_ORDER,
    inventory.f_units_sold AS C_UNITS_SOLD,
    inventory.f_lost_units AS C_LOST_UNITS,
    inventory.f_stockout AS IFF(C_STOCKOUT_FLAG, 1, 0),
    plan.f_plan_net_sales AS C_PLAN_NET_SALES,
    plan.f_plan_units AS C_PLAN_UNITS,
    plan.f_plan_gross_margin AS C_PLAN_GROSS_MARGIN
  )
  DIMENSIONS (
    dates.calendar_date AS C_DATE_KEY WITH SYNONYMS = ('date', 'order date', 'day')
      COMMENT = 'Calendar day: order date for sales, snapshot date for inventory, plan date for targets.',
    dates.week_start AS C_WEEK_START WITH SYNONYMS = ('week') COMMENT = 'Monday that starts the week.',
    dates.month_start AS C_MONTH_START WITH SYNONYMS = ('month') COMMENT = 'First day of the month.',
    dates.month_name AS C_MONTH_NAME COMMENT = 'Month label, e.g. Sep 2026.',
    dates.cal_quarter AS C_CAL_QUARTER WITH SYNONYMS = ('quarter') COMMENT = 'Calendar quarter, e.g. 2026-Q3.',
    dates.cal_year AS C_CAL_YEAR WITH SYNONYMS = ('year', 'fiscal year') COMMENT = 'Calendar (= fiscal) year.',
    dates.day_of_week AS C_DAY_OF_WEEK COMMENT = 'Day name (Mon-Sun).',
    dates.is_weekend AS C_IS_WEEKEND COMMENT = 'Saturday or Sunday.',
    dates.holiday AS COALESCE(C_HOLIDAY_NAME, 'No holiday') COMMENT = 'US retail holiday on this date, if any.',
    dates.retail_season AS C_RETAIL_SEASON COMMENT = 'Holiday, Winter clearance, Spring, Summer, Back to school & fall.',
    regions.region AS C_REGION_NAME WITH SYNONYMS = ('sales region', 'territory', 'area')
      COMMENT = 'US sales region (Northeast, Southeast, Midwest, Southwest, West). Online orders use the ship-to region.',
    regions.distribution_center AS C_DC_NAME WITH SYNONYMS = ('DC', 'warehouse', 'fulfillment center')
      COMMENT = 'Distribution center serving the region.',
    categories.category AS C_CATEGORY_NAME WITH SYNONYMS = ('product category', 'department')
      COMMENT = 'Merchandise category: Apparel, Footwear or Accessories.',
    products.subcategory AS C_SUBCATEGORY WITH SYNONYMS = ('product type', 'class') COMMENT = 'Merchandise subcategory, e.g. Running Shoes.',
    products.brand AS C_BRAND COMMENT = 'House brand.',
    products.product_name AS C_PRODUCT_NAME WITH SYNONYMS = ('product', 'style', 'item') COMMENT = 'Product (SKU) name.',
    products.sku_code AS C_SKU WITH SYNONYMS = ('SKU', 'item number') COMMENT = 'Stock keeping unit code.',
    products.gender AS C_GENDER COMMENT = 'Target customer: Women, Men, Kids, Unisex.',
    products.price_tier AS C_PRICE_TIER COMMENT = 'Value, Core or Premium price tier.',
    products.color_family AS C_COLOR_FAMILY COMMENT = 'Primary color family.',
    stores.store AS C_STORE_NAME WITH SYNONYMS = ('store name', 'location') COMMENT = 'Store name (store channel only).',
    stores.store_format AS C_STORE_FORMAT COMMENT = 'Flagship, Mall, Outlet or Street.',
    stores.store_state AS C_STORE_STATE COMMENT = 'State where the store is located.',
    sales.channel AS C_CHANNEL WITH SYNONYMS = ('sales channel') COMMENT = 'Store, Web, App or Marketplace.',
    sales.ship_method AS COALESCE(C_SHIP_METHOD, 'In-store') WITH SYNONYMS = ('shipping method', 'delivery speed')
      COMMENT = 'Standard, Expedited, Next Day; In-store for store purchases.',
    sales.carrier AS COALESCE(C_CARRIER, 'In-store') WITH SYNONYMS = ('shipping carrier') COMMENT = 'Parcel carrier for shipped orders.',
    sales.loyalty_tier AS C_LOYALTY_TIER WITH SYNONYMS = ('membership tier', 'customer tier')
      COMMENT = 'Guest, Member, Silver, Gold or Platinum at time of order.',
    sales.age_band AS C_AGE_BAND COMMENT = 'Customer age band (Unknown for guests).',
    sales.customer_state AS C_CUSTOMER_STATE WITH SYNONYMS = ('state', 'ship-to state') COMMENT = 'Ship-to state (store state for store purchases).',
    sales.fulfillment_status AS C_FULFILLMENT_STATUS COMMENT = 'Processing, In transit, Delivered, or In-store purchase - as of now.',
    sales.promotion AS COALESCE(C_PROMO_NAME, 'Full price') WITH SYNONYMS = ('promo', 'campaign', 'event')
      COMMENT = 'Promotion or markdown applied to the line; Full price when none.',
    sales.return_reason AS COALESCE(C_RETURN_REASON, 'Not returned') COMMENT = 'Reason given for the return.',
    sales.order_hour AS C_ORDER_HOUR COMMENT = 'Hour of day the order was placed (US Eastern).'
  )
  METRICS (
    sales.net_sales AS SUM(sales.f_net_sales) WITH SYNONYMS = ('revenue', 'sales', 'net revenue')
      COMMENT = 'Net merchandise sales (USD): list price x units minus discounts. Excludes tax, shipping fees and returns.',
    sales.gross_sales AS SUM(sales.f_gross_sales) WITH SYNONYMS = ('gross revenue')
      COMMENT = 'Sales at list price before discounts (USD).',
    sales.discount_amount AS SUM(sales.f_discount_amount) WITH SYNONYMS = ('markdowns', 'promotional discount')
      COMMENT = 'Value of promotional discounts, markdowns and member coupons (USD).',
    sales.discount_rate AS DIV0(sales.discount_amount, sales.gross_sales)
      COMMENT = 'Discount amount / gross sales.',
    sales.cost_of_goods_sold AS SUM(sales.f_cogs) WITH SYNONYMS = ('COGS', 'product cost') COMMENT = 'Landed unit cost x units (USD).',
    sales.gross_margin AS SUM(sales.f_gross_margin) WITH SYNONYMS = ('gross profit', 'margin dollars')
      COMMENT = 'Net sales minus cost of goods sold (USD).',
    sales.gross_margin_pct AS DIV0(sales.gross_margin, sales.net_sales) WITH SYNONYMS = ('margin rate', 'GM%')
      COMMENT = 'Gross margin / net sales.',
    sales.units_sold AS SUM(sales.f_qty) WITH SYNONYMS = ('units', 'quantity sold') COMMENT = 'Units sold (fulfilled).',
    sales.order_count AS COUNT(DISTINCT sales.f_order_id) WITH SYNONYMS = ('orders', 'transactions', 'number of orders')
      COMMENT = 'Distinct orders. With a product breakdown it counts orders containing that product.',
    sales.average_order_value AS DIV0(sales.net_sales, sales.order_count) WITH SYNONYMS = ('AOV', 'basket size')
      COMMENT = 'Net sales / orders.',
    sales.units_per_transaction AS DIV0(sales.units_sold, sales.order_count) WITH SYNONYMS = ('UPT', 'units per order')
      COMMENT = 'Units / orders.',
    sales.active_customers AS COUNT(DISTINCT sales.f_customer_id) WITH SYNONYMS = ('customers', 'buyers')
      COMMENT = 'Distinct identified customers who ordered (guests excluded).',
    sales.online_net_sales AS SUM(sales.f_online_net_sales) WITH SYNONYMS = ('digital sales', 'ecommerce sales')
      COMMENT = 'Net sales from Web, App and Marketplace (USD).',
    sales.online_sales_share AS DIV0(sales.online_net_sales, sales.net_sales) WITH SYNONYMS = ('digital share', 'ecommerce penetration')
      COMMENT = 'Share of net sales from Web, App and Marketplace.',
    sales.shipped_orders AS COUNT(DISTINCT sales.f_shipped_order_id)
      COMMENT = 'Orders shipped to customers (Web, App, Marketplace).',
    sales.free_shipping_orders AS COUNT(DISTINCT sales.f_free_ship_order_id)
      COMMENT = 'Shipped orders with a 0 USD shipping fee.',
    sales.free_shipping_order_pct AS DIV0(sales.free_shipping_orders, sales.shipped_orders)
      WITH SYNONYMS = ('free shipping %', 'free shipping rate')
      COMMENT = 'Shipped orders with a 0 USD shipping fee / all shipped orders. Free when subtotal meets the threshold (99 USD, 119 USD from Mar 2026), for Gold and Platinum members, on free-shipping promotion days, or by marketplace policy.',
    sales.shipping_fee_revenue AS SUM(sales.f_line_shipping_fee) COMMENT = 'Shipping fees charged to customers (USD).',
    sales.avg_click_to_ship_hours AS AVG(sales.f_click_to_ship_hours) WITH SYNONYMS = ('fulfillment time', 'order to ship time', 'processing time')
      COMMENT = 'Average hours from order placed to carrier hand-off, over shipped order lines.',
    sales.avg_transit_days AS AVG(sales.f_transit_days) WITH SYNONYMS = ('carrier transit time')
      COMMENT = 'Average days from carrier hand-off to delivery, over delivered order lines.',
    sales.avg_delivery_days AS AVG(sales.f_delivery_days) WITH SYNONYMS = ('shipping time', 'avg shipping time', 'delivery time', 'click to door')
      COMMENT = 'Average days from order placed to delivery, over delivered order lines.',
    sales.on_time_delivery_pct AS AVG(sales.f_on_time) WITH SYNONYMS = ('OTD', 'on-time rate')
      COMMENT = 'Delivered lines that arrived on or before the promised date (Standard 6 days, Expedited 3, Next Day 2) / all delivered lines.',
    sales.returned_sales AS SUM(sales.f_returned_sales) COMMENT = 'Net sales value of items returned so far (USD).',
    sales.returned_units AS SUM(sales.f_returned_units) COMMENT = 'Units returned so far.',
    sales.return_rate AS DIV0(sales.returned_sales, sales.net_sales) WITH SYNONYMS = ('returns %')
      COMMENT = 'Returned sales / net sales for orders placed in the period. Recent periods rise as returns arrive.',
    sales.net_sales_after_returns AS sales.net_sales - sales.returned_sales COMMENT = 'Net sales less returns (USD).',
    inventory.helper_inventory_days AS COUNT(DISTINCT inventory.f_snapshot_date)
      COMMENT = 'Helper: number of days with inventory snapshots in the selection.',
    inventory.helper_unit_days AS SUM(inventory.f_units_on_hand) COMMENT = 'Helper: end-of-day units summed over days.',
    inventory.helper_value_days AS SUM(inventory.f_inventory_value) COMMENT = 'Helper: end-of-day inventory value summed over days.',
    inventory.helper_on_order_days AS SUM(inventory.f_units_on_order) COMMENT = 'Helper: open order units summed over days.',
    inventory.avg_units_on_hand AS DIV0(inventory.helper_unit_days, inventory.helper_inventory_days)
      WITH SYNONYMS = ('units on hand', 'inventory units', 'stock on hand')
      COMMENT = 'Average daily end-of-day units on hand: stock is summed across the selected SKUs and DCs, then averaged over days (stock is never added up across days).',
    inventory.avg_inventory_value AS DIV0(inventory.helper_value_days, inventory.helper_inventory_days)
      WITH SYNONYMS = ('inventory value', 'stock value') COMMENT = 'Average daily inventory value at cost (USD).',
    inventory.avg_units_on_order AS DIV0(inventory.helper_on_order_days, inventory.helper_inventory_days)
      WITH SYNONYMS = ('on order', 'open PO units') COMMENT = 'Average daily units on open replenishment orders.',
    inventory.units_sold_from_stock AS SUM(inventory.f_units_sold) COMMENT = 'Units fulfilled from DC stock (equals units sold for the same slice).',
    inventory.lost_sales_units AS SUM(inventory.f_lost_units) WITH SYNONYMS = ('lost sales', 'unmet demand')
      COMMENT = 'Units customers wanted that could not be fulfilled because the DC was out of stock.',
    inventory.stockout_rate AS AVG(inventory.f_stockout) WITH SYNONYMS = ('out of stock %', 'OOS rate')
      COMMENT = 'Share of SKU x DC x day records ending with zero units on hand.',
    inventory.in_stock_rate AS 1 - inventory.stockout_rate WITH SYNONYMS = ('in-stock %', 'availability')
      COMMENT = 'Share of SKU x DC x day records ending with stock available.',
    inventory.weeks_of_supply AS DIV0(inventory.helper_unit_days, 7 * inventory.units_sold_from_stock) WITH SYNONYMS = ('WOS', 'weeks of cover')
      COMMENT = 'Average units on hand / average weekly units sold.',
    inventory.sell_through_pct AS DIV0(inventory.units_sold_from_stock, inventory.units_sold_from_stock + inventory.avg_units_on_hand)
      WITH SYNONYMS = ('sell-through', 'sell thru')
      COMMENT = 'Units sold / (units sold + average daily units on hand) for the period.',
    inventory.ending_units_on_hand NON ADDITIVE BY (dates.calendar_date) AS SUM(inventory.f_units_on_hand)
      WITH SYNONYMS = ('closing stock', 'current units on hand')
      COMMENT = 'Units on hand on the last day of the period (semi-additive: summed across SKUs and DCs, never across days).',
    plan.plan_net_sales AS SUM(plan.f_plan_net_sales) WITH SYNONYMS = ('sales plan', 'sales target', 'budget')
      COMMENT = 'Planned net sales (USD).',
    plan.plan_units AS SUM(plan.f_plan_units) WITH SYNONYMS = ('unit plan') COMMENT = 'Planned units.',
    plan.plan_gross_margin AS SUM(plan.f_plan_gross_margin) WITH SYNONYMS = ('margin plan') COMMENT = 'Planned gross margin (USD).',
    plan_attainment_pct AS DIV0(sales.net_sales, plan.plan_net_sales)
      WITH SYNONYMS = ('sales vs plan %', 'attainment', 'percent to plan')
      COMMENT = 'Net sales / planned net sales.',
    net_sales_vs_plan AS sales.net_sales - plan.plan_net_sales
      WITH SYNONYMS = ('sales gap to plan', 'variance to plan') COMMENT = 'Net sales minus planned net sales (USD).'
  )
  COMMENT = 'Harborline Outfitters (fictional US retailer): live sales, fulfillment, inventory and plan. Synthetic data generated in Snowflake.'
  AI_SQL_GENERATION 'Fiscal year equals calendar year; weeks start Monday. Net sales excludes tax, shipping and returns. Inventory measures are end-of-day stock and must never be summed across days. Use calendar_date for all time filtering. Current period metrics are live: today is incomplete.'$$);
INSERT INTO SV_DDL VALUES (2, 'no semi-additive ending stock', $$CREATE OR REPLACE SEMANTIC VIEW WBR_DB.RETAIL_DEMO.RETAIL_ANALYTICS_SV
  TABLES (
    dates AS WBR_DB.RETAIL_DEMO.SV_SRC_DATE PRIMARY KEY (C_DATE_KEY)
      WITH SYNONYMS ('calendar', 'day') COMMENT = 'Calendar day. Weeks start Monday; fiscal year equals calendar year.',
    regions AS WBR_DB.RETAIL_DEMO.SV_SRC_REGION PRIMARY KEY (C_REGION_ID)
      WITH SYNONYMS ('territory', 'market') COMMENT = 'Five US sales regions, each served by one distribution center.',
    categories AS WBR_DB.RETAIL_DEMO.SV_SRC_CATEGORY PRIMARY KEY (C_CATEGORY_ID)
      WITH SYNONYMS ('department', 'merchandise category') COMMENT = 'Apparel, Footwear, Accessories.',
    products AS WBR_DB.RETAIL_DEMO.SV_SRC_PRODUCT PRIMARY KEY (C_SKU)
      WITH SYNONYMS ('items', 'SKUs', 'styles') COMMENT = 'Product master at SKU level (fictional house brands).',
    stores AS WBR_DB.RETAIL_DEMO.SV_SRC_STORE PRIMARY KEY (C_STORE_ID)
      WITH SYNONYMS ('shops', 'doors') COMMENT = 'Physical stores (60).',
    sales AS WBR_DB.RETAIL_DEMO.SV_SRC_SALES PRIMARY KEY (C_LINE_ID)
      WITH SYNONYMS ('orders', 'transactions', 'order lines')
      COMMENT = 'Live order lines across Store, Web, App and Marketplace. Rows appear as orders are placed; shipment, delivery and return fields update as those events happen.',
    inventory AS WBR_DB.RETAIL_DEMO.SV_SRC_INVENTORY PRIMARY KEY (C_SNAPSHOT_DATE, C_SKU, C_REGION_ID)
      WITH SYNONYMS ('stock', 'on hand')
      COMMENT = 'End-of-day inventory per SKU per regional distribution center. Today reflects stock as of now.',
    plan AS WBR_DB.RETAIL_DEMO.SV_SRC_PLAN PRIMARY KEY (C_DATE_KEY, C_REGION_ID, C_CATEGORY_ID)
      WITH SYNONYMS ('target', 'budget', 'forecast plan')
      COMMENT = 'Approved financial plan by day, region and category (monthly plan phased to days).'
  )
  RELATIONSHIPS (
    sales_to_dates AS sales (C_ORDER_DATE) REFERENCES dates,
    sales_to_regions AS sales (C_REGION_ID) REFERENCES regions,
    sales_to_categories AS sales (C_CATEGORY_ID) REFERENCES categories,
    sales_to_products AS sales (C_SKU) REFERENCES products,
    sales_to_stores AS sales (C_STORE_ID) REFERENCES stores,
    inventory_to_dates AS inventory (C_SNAPSHOT_DATE) REFERENCES dates,
    inventory_to_regions AS inventory (C_REGION_ID) REFERENCES regions,
    inventory_to_categories AS inventory (C_CATEGORY_ID) REFERENCES categories,
    inventory_to_products AS inventory (C_SKU) REFERENCES products,
    plan_to_dates AS plan (C_DATE_KEY) REFERENCES dates,
    plan_to_regions AS plan (C_REGION_ID) REFERENCES regions,
    plan_to_categories AS plan (C_CATEGORY_ID) REFERENCES categories
  )
  FACTS (
    sales.f_order_id AS C_ORDER_ID,
    sales.f_customer_id AS C_CUSTOMER_ID,
    sales.f_qty AS C_QTY,
    sales.f_gross_sales AS C_GROSS_SALES,
    sales.f_discount_amount AS C_DISCOUNT_AMOUNT,
    sales.f_net_sales AS C_NET_SALES,
    sales.f_cogs AS C_COGS,
    sales.f_gross_margin AS C_NET_SALES - C_COGS,
    sales.f_online_net_sales AS IFF(C_IS_ONLINE, C_NET_SALES, 0),
    sales.f_shipped_order_id AS IFF(C_IS_SHIPPED_ORDER, C_ORDER_ID, NULL),
    sales.f_free_ship_order_id AS IFF(C_FREE_SHIPPING_FLAG, C_ORDER_ID, NULL),
    sales.f_line_shipping_fee AS C_LINE_SHIPPING_FEE,
    sales.f_click_to_ship_hours AS C_CLICK_TO_SHIP_HOURS,
    sales.f_transit_days AS C_TRANSIT_DAYS,
    sales.f_delivery_days AS C_DELIVERY_DAYS,
    sales.f_on_time AS CASE WHEN C_ON_TIME_FLAG THEN 1 WHEN NOT C_ON_TIME_FLAG THEN 0 END,
    sales.f_returned_sales AS C_RETURNED_SALES,
    sales.f_returned_units AS C_RETURNED_UNITS,
    inventory.f_snapshot_date AS C_SNAPSHOT_DATE,
    inventory.f_units_on_hand AS C_UNITS_ON_HAND,
    inventory.f_inventory_value AS C_INVENTORY_VALUE,
    inventory.f_units_on_order AS C_UNITS_ON_ORDER,
    inventory.f_units_sold AS C_UNITS_SOLD,
    inventory.f_lost_units AS C_LOST_UNITS,
    inventory.f_stockout AS IFF(C_STOCKOUT_FLAG, 1, 0),
    plan.f_plan_net_sales AS C_PLAN_NET_SALES,
    plan.f_plan_units AS C_PLAN_UNITS,
    plan.f_plan_gross_margin AS C_PLAN_GROSS_MARGIN
  )
  DIMENSIONS (
    dates.calendar_date AS C_DATE_KEY WITH SYNONYMS = ('date', 'order date', 'day')
      COMMENT = 'Calendar day: order date for sales, snapshot date for inventory, plan date for targets.',
    dates.week_start AS C_WEEK_START WITH SYNONYMS = ('week') COMMENT = 'Monday that starts the week.',
    dates.month_start AS C_MONTH_START WITH SYNONYMS = ('month') COMMENT = 'First day of the month.',
    dates.month_name AS C_MONTH_NAME COMMENT = 'Month label, e.g. Sep 2026.',
    dates.cal_quarter AS C_CAL_QUARTER WITH SYNONYMS = ('quarter') COMMENT = 'Calendar quarter, e.g. 2026-Q3.',
    dates.cal_year AS C_CAL_YEAR WITH SYNONYMS = ('year', 'fiscal year') COMMENT = 'Calendar (= fiscal) year.',
    dates.day_of_week AS C_DAY_OF_WEEK COMMENT = 'Day name (Mon-Sun).',
    dates.is_weekend AS C_IS_WEEKEND COMMENT = 'Saturday or Sunday.',
    dates.holiday AS COALESCE(C_HOLIDAY_NAME, 'No holiday') COMMENT = 'US retail holiday on this date, if any.',
    dates.retail_season AS C_RETAIL_SEASON COMMENT = 'Holiday, Winter clearance, Spring, Summer, Back to school & fall.',
    regions.region AS C_REGION_NAME WITH SYNONYMS = ('sales region', 'territory', 'area')
      COMMENT = 'US sales region (Northeast, Southeast, Midwest, Southwest, West). Online orders use the ship-to region.',
    regions.distribution_center AS C_DC_NAME WITH SYNONYMS = ('DC', 'warehouse', 'fulfillment center')
      COMMENT = 'Distribution center serving the region.',
    categories.category AS C_CATEGORY_NAME WITH SYNONYMS = ('product category', 'department')
      COMMENT = 'Merchandise category: Apparel, Footwear or Accessories.',
    products.subcategory AS C_SUBCATEGORY WITH SYNONYMS = ('product type', 'class') COMMENT = 'Merchandise subcategory, e.g. Running Shoes.',
    products.brand AS C_BRAND COMMENT = 'House brand.',
    products.product_name AS C_PRODUCT_NAME WITH SYNONYMS = ('product', 'style', 'item') COMMENT = 'Product (SKU) name.',
    products.sku_code AS C_SKU WITH SYNONYMS = ('SKU', 'item number') COMMENT = 'Stock keeping unit code.',
    products.gender AS C_GENDER COMMENT = 'Target customer: Women, Men, Kids, Unisex.',
    products.price_tier AS C_PRICE_TIER COMMENT = 'Value, Core or Premium price tier.',
    products.color_family AS C_COLOR_FAMILY COMMENT = 'Primary color family.',
    stores.store AS C_STORE_NAME WITH SYNONYMS = ('store name', 'location') COMMENT = 'Store name (store channel only).',
    stores.store_format AS C_STORE_FORMAT COMMENT = 'Flagship, Mall, Outlet or Street.',
    stores.store_state AS C_STORE_STATE COMMENT = 'State where the store is located.',
    sales.channel AS C_CHANNEL WITH SYNONYMS = ('sales channel') COMMENT = 'Store, Web, App or Marketplace.',
    sales.ship_method AS COALESCE(C_SHIP_METHOD, 'In-store') WITH SYNONYMS = ('shipping method', 'delivery speed')
      COMMENT = 'Standard, Expedited, Next Day; In-store for store purchases.',
    sales.carrier AS COALESCE(C_CARRIER, 'In-store') WITH SYNONYMS = ('shipping carrier') COMMENT = 'Parcel carrier for shipped orders.',
    sales.loyalty_tier AS C_LOYALTY_TIER WITH SYNONYMS = ('membership tier', 'customer tier')
      COMMENT = 'Guest, Member, Silver, Gold or Platinum at time of order.',
    sales.age_band AS C_AGE_BAND COMMENT = 'Customer age band (Unknown for guests).',
    sales.customer_state AS C_CUSTOMER_STATE WITH SYNONYMS = ('state', 'ship-to state') COMMENT = 'Ship-to state (store state for store purchases).',
    sales.fulfillment_status AS C_FULFILLMENT_STATUS COMMENT = 'Processing, In transit, Delivered, or In-store purchase - as of now.',
    sales.promotion AS COALESCE(C_PROMO_NAME, 'Full price') WITH SYNONYMS = ('promo', 'campaign', 'event')
      COMMENT = 'Promotion or markdown applied to the line; Full price when none.',
    sales.return_reason AS COALESCE(C_RETURN_REASON, 'Not returned') COMMENT = 'Reason given for the return.',
    sales.order_hour AS C_ORDER_HOUR COMMENT = 'Hour of day the order was placed (US Eastern).'
  )
  METRICS (
    sales.net_sales AS SUM(sales.f_net_sales) WITH SYNONYMS = ('revenue', 'sales', 'net revenue')
      COMMENT = 'Net merchandise sales (USD): list price x units minus discounts. Excludes tax, shipping fees and returns.',
    sales.gross_sales AS SUM(sales.f_gross_sales) WITH SYNONYMS = ('gross revenue')
      COMMENT = 'Sales at list price before discounts (USD).',
    sales.discount_amount AS SUM(sales.f_discount_amount) WITH SYNONYMS = ('markdowns', 'promotional discount')
      COMMENT = 'Value of promotional discounts, markdowns and member coupons (USD).',
    sales.discount_rate AS DIV0(sales.discount_amount, sales.gross_sales)
      COMMENT = 'Discount amount / gross sales.',
    sales.cost_of_goods_sold AS SUM(sales.f_cogs) WITH SYNONYMS = ('COGS', 'product cost') COMMENT = 'Landed unit cost x units (USD).',
    sales.gross_margin AS SUM(sales.f_gross_margin) WITH SYNONYMS = ('gross profit', 'margin dollars')
      COMMENT = 'Net sales minus cost of goods sold (USD).',
    sales.gross_margin_pct AS DIV0(sales.gross_margin, sales.net_sales) WITH SYNONYMS = ('margin rate', 'GM%')
      COMMENT = 'Gross margin / net sales.',
    sales.units_sold AS SUM(sales.f_qty) WITH SYNONYMS = ('units', 'quantity sold') COMMENT = 'Units sold (fulfilled).',
    sales.order_count AS COUNT(DISTINCT sales.f_order_id) WITH SYNONYMS = ('orders', 'transactions', 'number of orders')
      COMMENT = 'Distinct orders. With a product breakdown it counts orders containing that product.',
    sales.average_order_value AS DIV0(sales.net_sales, sales.order_count) WITH SYNONYMS = ('AOV', 'basket size')
      COMMENT = 'Net sales / orders.',
    sales.units_per_transaction AS DIV0(sales.units_sold, sales.order_count) WITH SYNONYMS = ('UPT', 'units per order')
      COMMENT = 'Units / orders.',
    sales.active_customers AS COUNT(DISTINCT sales.f_customer_id) WITH SYNONYMS = ('customers', 'buyers')
      COMMENT = 'Distinct identified customers who ordered (guests excluded).',
    sales.online_net_sales AS SUM(sales.f_online_net_sales) WITH SYNONYMS = ('digital sales', 'ecommerce sales')
      COMMENT = 'Net sales from Web, App and Marketplace (USD).',
    sales.online_sales_share AS DIV0(sales.online_net_sales, sales.net_sales) WITH SYNONYMS = ('digital share', 'ecommerce penetration')
      COMMENT = 'Share of net sales from Web, App and Marketplace.',
    sales.shipped_orders AS COUNT(DISTINCT sales.f_shipped_order_id)
      COMMENT = 'Orders shipped to customers (Web, App, Marketplace).',
    sales.free_shipping_orders AS COUNT(DISTINCT sales.f_free_ship_order_id)
      COMMENT = 'Shipped orders with a 0 USD shipping fee.',
    sales.free_shipping_order_pct AS DIV0(sales.free_shipping_orders, sales.shipped_orders)
      WITH SYNONYMS = ('free shipping %', 'free shipping rate')
      COMMENT = 'Shipped orders with a 0 USD shipping fee / all shipped orders. Free when subtotal meets the threshold (99 USD, 119 USD from Mar 2026), for Gold and Platinum members, on free-shipping promotion days, or by marketplace policy.',
    sales.shipping_fee_revenue AS SUM(sales.f_line_shipping_fee) COMMENT = 'Shipping fees charged to customers (USD).',
    sales.avg_click_to_ship_hours AS AVG(sales.f_click_to_ship_hours) WITH SYNONYMS = ('fulfillment time', 'order to ship time', 'processing time')
      COMMENT = 'Average hours from order placed to carrier hand-off, over shipped order lines.',
    sales.avg_transit_days AS AVG(sales.f_transit_days) WITH SYNONYMS = ('carrier transit time')
      COMMENT = 'Average days from carrier hand-off to delivery, over delivered order lines.',
    sales.avg_delivery_days AS AVG(sales.f_delivery_days) WITH SYNONYMS = ('shipping time', 'avg shipping time', 'delivery time', 'click to door')
      COMMENT = 'Average days from order placed to delivery, over delivered order lines.',
    sales.on_time_delivery_pct AS AVG(sales.f_on_time) WITH SYNONYMS = ('OTD', 'on-time rate')
      COMMENT = 'Delivered lines that arrived on or before the promised date (Standard 6 days, Expedited 3, Next Day 2) / all delivered lines.',
    sales.returned_sales AS SUM(sales.f_returned_sales) COMMENT = 'Net sales value of items returned so far (USD).',
    sales.returned_units AS SUM(sales.f_returned_units) COMMENT = 'Units returned so far.',
    sales.return_rate AS DIV0(sales.returned_sales, sales.net_sales) WITH SYNONYMS = ('returns %')
      COMMENT = 'Returned sales / net sales for orders placed in the period. Recent periods rise as returns arrive.',
    sales.net_sales_after_returns AS sales.net_sales - sales.returned_sales COMMENT = 'Net sales less returns (USD).',
    inventory.helper_inventory_days AS COUNT(DISTINCT inventory.f_snapshot_date)
      COMMENT = 'Helper: number of days with inventory snapshots in the selection.',
    inventory.helper_unit_days AS SUM(inventory.f_units_on_hand) COMMENT = 'Helper: end-of-day units summed over days.',
    inventory.helper_value_days AS SUM(inventory.f_inventory_value) COMMENT = 'Helper: end-of-day inventory value summed over days.',
    inventory.helper_on_order_days AS SUM(inventory.f_units_on_order) COMMENT = 'Helper: open order units summed over days.',
    inventory.avg_units_on_hand AS DIV0(inventory.helper_unit_days, inventory.helper_inventory_days)
      WITH SYNONYMS = ('units on hand', 'inventory units', 'stock on hand')
      COMMENT = 'Average daily end-of-day units on hand: stock is summed across the selected SKUs and DCs, then averaged over days (stock is never added up across days).',
    inventory.avg_inventory_value AS DIV0(inventory.helper_value_days, inventory.helper_inventory_days)
      WITH SYNONYMS = ('inventory value', 'stock value') COMMENT = 'Average daily inventory value at cost (USD).',
    inventory.avg_units_on_order AS DIV0(inventory.helper_on_order_days, inventory.helper_inventory_days)
      WITH SYNONYMS = ('on order', 'open PO units') COMMENT = 'Average daily units on open replenishment orders.',
    inventory.units_sold_from_stock AS SUM(inventory.f_units_sold) COMMENT = 'Units fulfilled from DC stock (equals units sold for the same slice).',
    inventory.lost_sales_units AS SUM(inventory.f_lost_units) WITH SYNONYMS = ('lost sales', 'unmet demand')
      COMMENT = 'Units customers wanted that could not be fulfilled because the DC was out of stock.',
    inventory.stockout_rate AS AVG(inventory.f_stockout) WITH SYNONYMS = ('out of stock %', 'OOS rate')
      COMMENT = 'Share of SKU x DC x day records ending with zero units on hand.',
    inventory.in_stock_rate AS 1 - inventory.stockout_rate WITH SYNONYMS = ('in-stock %', 'availability')
      COMMENT = 'Share of SKU x DC x day records ending with stock available.',
    inventory.weeks_of_supply AS DIV0(inventory.helper_unit_days, 7 * inventory.units_sold_from_stock) WITH SYNONYMS = ('WOS', 'weeks of cover')
      COMMENT = 'Average units on hand / average weekly units sold.',
    inventory.sell_through_pct AS DIV0(inventory.units_sold_from_stock, inventory.units_sold_from_stock + inventory.avg_units_on_hand)
      WITH SYNONYMS = ('sell-through', 'sell thru')
      COMMENT = 'Units sold / (units sold + average daily units on hand) for the period.',
    plan.plan_net_sales AS SUM(plan.f_plan_net_sales) WITH SYNONYMS = ('sales plan', 'sales target', 'budget')
      COMMENT = 'Planned net sales (USD).',
    plan.plan_units AS SUM(plan.f_plan_units) WITH SYNONYMS = ('unit plan') COMMENT = 'Planned units.',
    plan.plan_gross_margin AS SUM(plan.f_plan_gross_margin) WITH SYNONYMS = ('margin plan') COMMENT = 'Planned gross margin (USD).',
    plan_attainment_pct AS DIV0(sales.net_sales, plan.plan_net_sales)
      WITH SYNONYMS = ('sales vs plan %', 'attainment', 'percent to plan')
      COMMENT = 'Net sales / planned net sales.',
    net_sales_vs_plan AS sales.net_sales - plan.plan_net_sales
      WITH SYNONYMS = ('sales gap to plan', 'variance to plan') COMMENT = 'Net sales minus planned net sales (USD).'
  )
  COMMENT = 'Harborline Outfitters (fictional US retailer): live sales, fulfillment, inventory and plan. Synthetic data generated in Snowflake.'
  AI_SQL_GENERATION 'Fiscal year equals calendar year; weeks start Monday. Net sales excludes tax, shipping and returns. Inventory measures are end-of-day stock and must never be summed across days. Use calendar_date for all time filtering. Current period metrics are live: today is incomplete.'$$);
INSERT INTO SV_DDL VALUES (3, 'no derived metrics', $$CREATE OR REPLACE SEMANTIC VIEW WBR_DB.RETAIL_DEMO.RETAIL_ANALYTICS_SV
  TABLES (
    dates AS WBR_DB.RETAIL_DEMO.SV_SRC_DATE PRIMARY KEY (C_DATE_KEY)
      WITH SYNONYMS ('calendar', 'day') COMMENT = 'Calendar day. Weeks start Monday; fiscal year equals calendar year.',
    regions AS WBR_DB.RETAIL_DEMO.SV_SRC_REGION PRIMARY KEY (C_REGION_ID)
      WITH SYNONYMS ('territory', 'market') COMMENT = 'Five US sales regions, each served by one distribution center.',
    categories AS WBR_DB.RETAIL_DEMO.SV_SRC_CATEGORY PRIMARY KEY (C_CATEGORY_ID)
      WITH SYNONYMS ('department', 'merchandise category') COMMENT = 'Apparel, Footwear, Accessories.',
    products AS WBR_DB.RETAIL_DEMO.SV_SRC_PRODUCT PRIMARY KEY (C_SKU)
      WITH SYNONYMS ('items', 'SKUs', 'styles') COMMENT = 'Product master at SKU level (fictional house brands).',
    stores AS WBR_DB.RETAIL_DEMO.SV_SRC_STORE PRIMARY KEY (C_STORE_ID)
      WITH SYNONYMS ('shops', 'doors') COMMENT = 'Physical stores (60).',
    sales AS WBR_DB.RETAIL_DEMO.SV_SRC_SALES PRIMARY KEY (C_LINE_ID)
      WITH SYNONYMS ('orders', 'transactions', 'order lines')
      COMMENT = 'Live order lines across Store, Web, App and Marketplace. Rows appear as orders are placed; shipment, delivery and return fields update as those events happen.',
    inventory AS WBR_DB.RETAIL_DEMO.SV_SRC_INVENTORY PRIMARY KEY (C_SNAPSHOT_DATE, C_SKU, C_REGION_ID)
      WITH SYNONYMS ('stock', 'on hand')
      COMMENT = 'End-of-day inventory per SKU per regional distribution center. Today reflects stock as of now.',
    plan AS WBR_DB.RETAIL_DEMO.SV_SRC_PLAN PRIMARY KEY (C_DATE_KEY, C_REGION_ID, C_CATEGORY_ID)
      WITH SYNONYMS ('target', 'budget', 'forecast plan')
      COMMENT = 'Approved financial plan by day, region and category (monthly plan phased to days).'
  )
  RELATIONSHIPS (
    sales_to_dates AS sales (C_ORDER_DATE) REFERENCES dates,
    sales_to_regions AS sales (C_REGION_ID) REFERENCES regions,
    sales_to_categories AS sales (C_CATEGORY_ID) REFERENCES categories,
    sales_to_products AS sales (C_SKU) REFERENCES products,
    sales_to_stores AS sales (C_STORE_ID) REFERENCES stores,
    inventory_to_dates AS inventory (C_SNAPSHOT_DATE) REFERENCES dates,
    inventory_to_regions AS inventory (C_REGION_ID) REFERENCES regions,
    inventory_to_categories AS inventory (C_CATEGORY_ID) REFERENCES categories,
    inventory_to_products AS inventory (C_SKU) REFERENCES products,
    plan_to_dates AS plan (C_DATE_KEY) REFERENCES dates,
    plan_to_regions AS plan (C_REGION_ID) REFERENCES regions,
    plan_to_categories AS plan (C_CATEGORY_ID) REFERENCES categories
  )
  FACTS (
    sales.f_order_id AS C_ORDER_ID,
    sales.f_customer_id AS C_CUSTOMER_ID,
    sales.f_qty AS C_QTY,
    sales.f_gross_sales AS C_GROSS_SALES,
    sales.f_discount_amount AS C_DISCOUNT_AMOUNT,
    sales.f_net_sales AS C_NET_SALES,
    sales.f_cogs AS C_COGS,
    sales.f_gross_margin AS C_NET_SALES - C_COGS,
    sales.f_online_net_sales AS IFF(C_IS_ONLINE, C_NET_SALES, 0),
    sales.f_shipped_order_id AS IFF(C_IS_SHIPPED_ORDER, C_ORDER_ID, NULL),
    sales.f_free_ship_order_id AS IFF(C_FREE_SHIPPING_FLAG, C_ORDER_ID, NULL),
    sales.f_line_shipping_fee AS C_LINE_SHIPPING_FEE,
    sales.f_click_to_ship_hours AS C_CLICK_TO_SHIP_HOURS,
    sales.f_transit_days AS C_TRANSIT_DAYS,
    sales.f_delivery_days AS C_DELIVERY_DAYS,
    sales.f_on_time AS CASE WHEN C_ON_TIME_FLAG THEN 1 WHEN NOT C_ON_TIME_FLAG THEN 0 END,
    sales.f_returned_sales AS C_RETURNED_SALES,
    sales.f_returned_units AS C_RETURNED_UNITS,
    inventory.f_snapshot_date AS C_SNAPSHOT_DATE,
    inventory.f_units_on_hand AS C_UNITS_ON_HAND,
    inventory.f_inventory_value AS C_INVENTORY_VALUE,
    inventory.f_units_on_order AS C_UNITS_ON_ORDER,
    inventory.f_units_sold AS C_UNITS_SOLD,
    inventory.f_lost_units AS C_LOST_UNITS,
    inventory.f_stockout AS IFF(C_STOCKOUT_FLAG, 1, 0),
    plan.f_plan_net_sales AS C_PLAN_NET_SALES,
    plan.f_plan_units AS C_PLAN_UNITS,
    plan.f_plan_gross_margin AS C_PLAN_GROSS_MARGIN
  )
  DIMENSIONS (
    dates.calendar_date AS C_DATE_KEY WITH SYNONYMS = ('date', 'order date', 'day')
      COMMENT = 'Calendar day: order date for sales, snapshot date for inventory, plan date for targets.',
    dates.week_start AS C_WEEK_START WITH SYNONYMS = ('week') COMMENT = 'Monday that starts the week.',
    dates.month_start AS C_MONTH_START WITH SYNONYMS = ('month') COMMENT = 'First day of the month.',
    dates.month_name AS C_MONTH_NAME COMMENT = 'Month label, e.g. Sep 2026.',
    dates.cal_quarter AS C_CAL_QUARTER WITH SYNONYMS = ('quarter') COMMENT = 'Calendar quarter, e.g. 2026-Q3.',
    dates.cal_year AS C_CAL_YEAR WITH SYNONYMS = ('year', 'fiscal year') COMMENT = 'Calendar (= fiscal) year.',
    dates.day_of_week AS C_DAY_OF_WEEK COMMENT = 'Day name (Mon-Sun).',
    dates.is_weekend AS C_IS_WEEKEND COMMENT = 'Saturday or Sunday.',
    dates.holiday AS COALESCE(C_HOLIDAY_NAME, 'No holiday') COMMENT = 'US retail holiday on this date, if any.',
    dates.retail_season AS C_RETAIL_SEASON COMMENT = 'Holiday, Winter clearance, Spring, Summer, Back to school & fall.',
    regions.region AS C_REGION_NAME WITH SYNONYMS = ('sales region', 'territory', 'area')
      COMMENT = 'US sales region (Northeast, Southeast, Midwest, Southwest, West). Online orders use the ship-to region.',
    regions.distribution_center AS C_DC_NAME WITH SYNONYMS = ('DC', 'warehouse', 'fulfillment center')
      COMMENT = 'Distribution center serving the region.',
    categories.category AS C_CATEGORY_NAME WITH SYNONYMS = ('product category', 'department')
      COMMENT = 'Merchandise category: Apparel, Footwear or Accessories.',
    products.subcategory AS C_SUBCATEGORY WITH SYNONYMS = ('product type', 'class') COMMENT = 'Merchandise subcategory, e.g. Running Shoes.',
    products.brand AS C_BRAND COMMENT = 'House brand.',
    products.product_name AS C_PRODUCT_NAME WITH SYNONYMS = ('product', 'style', 'item') COMMENT = 'Product (SKU) name.',
    products.sku_code AS C_SKU WITH SYNONYMS = ('SKU', 'item number') COMMENT = 'Stock keeping unit code.',
    products.gender AS C_GENDER COMMENT = 'Target customer: Women, Men, Kids, Unisex.',
    products.price_tier AS C_PRICE_TIER COMMENT = 'Value, Core or Premium price tier.',
    products.color_family AS C_COLOR_FAMILY COMMENT = 'Primary color family.',
    stores.store AS C_STORE_NAME WITH SYNONYMS = ('store name', 'location') COMMENT = 'Store name (store channel only).',
    stores.store_format AS C_STORE_FORMAT COMMENT = 'Flagship, Mall, Outlet or Street.',
    stores.store_state AS C_STORE_STATE COMMENT = 'State where the store is located.',
    sales.channel AS C_CHANNEL WITH SYNONYMS = ('sales channel') COMMENT = 'Store, Web, App or Marketplace.',
    sales.ship_method AS COALESCE(C_SHIP_METHOD, 'In-store') WITH SYNONYMS = ('shipping method', 'delivery speed')
      COMMENT = 'Standard, Expedited, Next Day; In-store for store purchases.',
    sales.carrier AS COALESCE(C_CARRIER, 'In-store') WITH SYNONYMS = ('shipping carrier') COMMENT = 'Parcel carrier for shipped orders.',
    sales.loyalty_tier AS C_LOYALTY_TIER WITH SYNONYMS = ('membership tier', 'customer tier')
      COMMENT = 'Guest, Member, Silver, Gold or Platinum at time of order.',
    sales.age_band AS C_AGE_BAND COMMENT = 'Customer age band (Unknown for guests).',
    sales.customer_state AS C_CUSTOMER_STATE WITH SYNONYMS = ('state', 'ship-to state') COMMENT = 'Ship-to state (store state for store purchases).',
    sales.fulfillment_status AS C_FULFILLMENT_STATUS COMMENT = 'Processing, In transit, Delivered, or In-store purchase - as of now.',
    sales.promotion AS COALESCE(C_PROMO_NAME, 'Full price') WITH SYNONYMS = ('promo', 'campaign', 'event')
      COMMENT = 'Promotion or markdown applied to the line; Full price when none.',
    sales.return_reason AS COALESCE(C_RETURN_REASON, 'Not returned') COMMENT = 'Reason given for the return.',
    sales.order_hour AS C_ORDER_HOUR COMMENT = 'Hour of day the order was placed (US Eastern).'
  )
  METRICS (
    sales.net_sales AS SUM(sales.f_net_sales) WITH SYNONYMS = ('revenue', 'sales', 'net revenue')
      COMMENT = 'Net merchandise sales (USD): list price x units minus discounts. Excludes tax, shipping fees and returns.',
    sales.gross_sales AS SUM(sales.f_gross_sales) WITH SYNONYMS = ('gross revenue')
      COMMENT = 'Sales at list price before discounts (USD).',
    sales.discount_amount AS SUM(sales.f_discount_amount) WITH SYNONYMS = ('markdowns', 'promotional discount')
      COMMENT = 'Value of promotional discounts, markdowns and member coupons (USD).',
    sales.discount_rate AS DIV0(sales.discount_amount, sales.gross_sales)
      COMMENT = 'Discount amount / gross sales.',
    sales.cost_of_goods_sold AS SUM(sales.f_cogs) WITH SYNONYMS = ('COGS', 'product cost') COMMENT = 'Landed unit cost x units (USD).',
    sales.gross_margin AS SUM(sales.f_gross_margin) WITH SYNONYMS = ('gross profit', 'margin dollars')
      COMMENT = 'Net sales minus cost of goods sold (USD).',
    sales.gross_margin_pct AS DIV0(sales.gross_margin, sales.net_sales) WITH SYNONYMS = ('margin rate', 'GM%')
      COMMENT = 'Gross margin / net sales.',
    sales.units_sold AS SUM(sales.f_qty) WITH SYNONYMS = ('units', 'quantity sold') COMMENT = 'Units sold (fulfilled).',
    sales.order_count AS COUNT(DISTINCT sales.f_order_id) WITH SYNONYMS = ('orders', 'transactions', 'number of orders')
      COMMENT = 'Distinct orders. With a product breakdown it counts orders containing that product.',
    sales.average_order_value AS DIV0(sales.net_sales, sales.order_count) WITH SYNONYMS = ('AOV', 'basket size')
      COMMENT = 'Net sales / orders.',
    sales.units_per_transaction AS DIV0(sales.units_sold, sales.order_count) WITH SYNONYMS = ('UPT', 'units per order')
      COMMENT = 'Units / orders.',
    sales.active_customers AS COUNT(DISTINCT sales.f_customer_id) WITH SYNONYMS = ('customers', 'buyers')
      COMMENT = 'Distinct identified customers who ordered (guests excluded).',
    sales.online_net_sales AS SUM(sales.f_online_net_sales) WITH SYNONYMS = ('digital sales', 'ecommerce sales')
      COMMENT = 'Net sales from Web, App and Marketplace (USD).',
    sales.online_sales_share AS DIV0(sales.online_net_sales, sales.net_sales) WITH SYNONYMS = ('digital share', 'ecommerce penetration')
      COMMENT = 'Share of net sales from Web, App and Marketplace.',
    sales.shipped_orders AS COUNT(DISTINCT sales.f_shipped_order_id)
      COMMENT = 'Orders shipped to customers (Web, App, Marketplace).',
    sales.free_shipping_orders AS COUNT(DISTINCT sales.f_free_ship_order_id)
      COMMENT = 'Shipped orders with a 0 USD shipping fee.',
    sales.free_shipping_order_pct AS DIV0(sales.free_shipping_orders, sales.shipped_orders)
      WITH SYNONYMS = ('free shipping %', 'free shipping rate')
      COMMENT = 'Shipped orders with a 0 USD shipping fee / all shipped orders. Free when subtotal meets the threshold (99 USD, 119 USD from Mar 2026), for Gold and Platinum members, on free-shipping promotion days, or by marketplace policy.',
    sales.shipping_fee_revenue AS SUM(sales.f_line_shipping_fee) COMMENT = 'Shipping fees charged to customers (USD).',
    sales.avg_click_to_ship_hours AS AVG(sales.f_click_to_ship_hours) WITH SYNONYMS = ('fulfillment time', 'order to ship time', 'processing time')
      COMMENT = 'Average hours from order placed to carrier hand-off, over shipped order lines.',
    sales.avg_transit_days AS AVG(sales.f_transit_days) WITH SYNONYMS = ('carrier transit time')
      COMMENT = 'Average days from carrier hand-off to delivery, over delivered order lines.',
    sales.avg_delivery_days AS AVG(sales.f_delivery_days) WITH SYNONYMS = ('shipping time', 'avg shipping time', 'delivery time', 'click to door')
      COMMENT = 'Average days from order placed to delivery, over delivered order lines.',
    sales.on_time_delivery_pct AS AVG(sales.f_on_time) WITH SYNONYMS = ('OTD', 'on-time rate')
      COMMENT = 'Delivered lines that arrived on or before the promised date (Standard 6 days, Expedited 3, Next Day 2) / all delivered lines.',
    sales.returned_sales AS SUM(sales.f_returned_sales) COMMENT = 'Net sales value of items returned so far (USD).',
    sales.returned_units AS SUM(sales.f_returned_units) COMMENT = 'Units returned so far.',
    sales.return_rate AS DIV0(sales.returned_sales, sales.net_sales) WITH SYNONYMS = ('returns %')
      COMMENT = 'Returned sales / net sales for orders placed in the period. Recent periods rise as returns arrive.',
    sales.net_sales_after_returns AS sales.net_sales - sales.returned_sales COMMENT = 'Net sales less returns (USD).',
    inventory.helper_inventory_days AS COUNT(DISTINCT inventory.f_snapshot_date)
      COMMENT = 'Helper: number of days with inventory snapshots in the selection.',
    inventory.helper_unit_days AS SUM(inventory.f_units_on_hand) COMMENT = 'Helper: end-of-day units summed over days.',
    inventory.helper_value_days AS SUM(inventory.f_inventory_value) COMMENT = 'Helper: end-of-day inventory value summed over days.',
    inventory.helper_on_order_days AS SUM(inventory.f_units_on_order) COMMENT = 'Helper: open order units summed over days.',
    inventory.avg_units_on_hand AS DIV0(inventory.helper_unit_days, inventory.helper_inventory_days)
      WITH SYNONYMS = ('units on hand', 'inventory units', 'stock on hand')
      COMMENT = 'Average daily end-of-day units on hand: stock is summed across the selected SKUs and DCs, then averaged over days (stock is never added up across days).',
    inventory.avg_inventory_value AS DIV0(inventory.helper_value_days, inventory.helper_inventory_days)
      WITH SYNONYMS = ('inventory value', 'stock value') COMMENT = 'Average daily inventory value at cost (USD).',
    inventory.avg_units_on_order AS DIV0(inventory.helper_on_order_days, inventory.helper_inventory_days)
      WITH SYNONYMS = ('on order', 'open PO units') COMMENT = 'Average daily units on open replenishment orders.',
    inventory.units_sold_from_stock AS SUM(inventory.f_units_sold) COMMENT = 'Units fulfilled from DC stock (equals units sold for the same slice).',
    inventory.lost_sales_units AS SUM(inventory.f_lost_units) WITH SYNONYMS = ('lost sales', 'unmet demand')
      COMMENT = 'Units customers wanted that could not be fulfilled because the DC was out of stock.',
    inventory.stockout_rate AS AVG(inventory.f_stockout) WITH SYNONYMS = ('out of stock %', 'OOS rate')
      COMMENT = 'Share of SKU x DC x day records ending with zero units on hand.',
    inventory.in_stock_rate AS 1 - inventory.stockout_rate WITH SYNONYMS = ('in-stock %', 'availability')
      COMMENT = 'Share of SKU x DC x day records ending with stock available.',
    inventory.weeks_of_supply AS DIV0(inventory.helper_unit_days, 7 * inventory.units_sold_from_stock) WITH SYNONYMS = ('WOS', 'weeks of cover')
      COMMENT = 'Average units on hand / average weekly units sold.',
    inventory.sell_through_pct AS DIV0(inventory.units_sold_from_stock, inventory.units_sold_from_stock + inventory.avg_units_on_hand)
      WITH SYNONYMS = ('sell-through', 'sell thru')
      COMMENT = 'Units sold / (units sold + average daily units on hand) for the period.',
    plan.plan_net_sales AS SUM(plan.f_plan_net_sales) WITH SYNONYMS = ('sales plan', 'sales target', 'budget')
      COMMENT = 'Planned net sales (USD).',
    plan.plan_units AS SUM(plan.f_plan_units) WITH SYNONYMS = ('unit plan') COMMENT = 'Planned units.',
    plan.plan_gross_margin AS SUM(plan.f_plan_gross_margin) WITH SYNONYMS = ('margin plan') COMMENT = 'Planned gross margin (USD).'
  )
  COMMENT = 'Harborline Outfitters (fictional US retailer): live sales, fulfillment, inventory and plan. Synthetic data generated in Snowflake.'
  AI_SQL_GENERATION 'Fiscal year equals calendar year; weeks start Monday. Net sales excludes tax, shipping and returns. Inventory measures are end-of-day stock and must never be summed across days. Use calendar_date for all time filtering. Current period metrics are live: today is incomplete.'$$);
INSERT INTO SV_DDL VALUES (4, 'core (no AI instructions)', $$CREATE OR REPLACE SEMANTIC VIEW WBR_DB.RETAIL_DEMO.RETAIL_ANALYTICS_SV
  TABLES (
    dates AS WBR_DB.RETAIL_DEMO.SV_SRC_DATE PRIMARY KEY (C_DATE_KEY)
      WITH SYNONYMS ('calendar', 'day') COMMENT = 'Calendar day. Weeks start Monday; fiscal year equals calendar year.',
    regions AS WBR_DB.RETAIL_DEMO.SV_SRC_REGION PRIMARY KEY (C_REGION_ID)
      WITH SYNONYMS ('territory', 'market') COMMENT = 'Five US sales regions, each served by one distribution center.',
    categories AS WBR_DB.RETAIL_DEMO.SV_SRC_CATEGORY PRIMARY KEY (C_CATEGORY_ID)
      WITH SYNONYMS ('department', 'merchandise category') COMMENT = 'Apparel, Footwear, Accessories.',
    products AS WBR_DB.RETAIL_DEMO.SV_SRC_PRODUCT PRIMARY KEY (C_SKU)
      WITH SYNONYMS ('items', 'SKUs', 'styles') COMMENT = 'Product master at SKU level (fictional house brands).',
    stores AS WBR_DB.RETAIL_DEMO.SV_SRC_STORE PRIMARY KEY (C_STORE_ID)
      WITH SYNONYMS ('shops', 'doors') COMMENT = 'Physical stores (60).',
    sales AS WBR_DB.RETAIL_DEMO.SV_SRC_SALES PRIMARY KEY (C_LINE_ID)
      WITH SYNONYMS ('orders', 'transactions', 'order lines')
      COMMENT = 'Live order lines across Store, Web, App and Marketplace. Rows appear as orders are placed; shipment, delivery and return fields update as those events happen.',
    inventory AS WBR_DB.RETAIL_DEMO.SV_SRC_INVENTORY PRIMARY KEY (C_SNAPSHOT_DATE, C_SKU, C_REGION_ID)
      WITH SYNONYMS ('stock', 'on hand')
      COMMENT = 'End-of-day inventory per SKU per regional distribution center. Today reflects stock as of now.',
    plan AS WBR_DB.RETAIL_DEMO.SV_SRC_PLAN PRIMARY KEY (C_DATE_KEY, C_REGION_ID, C_CATEGORY_ID)
      WITH SYNONYMS ('target', 'budget', 'forecast plan')
      COMMENT = 'Approved financial plan by day, region and category (monthly plan phased to days).'
  )
  RELATIONSHIPS (
    sales_to_dates AS sales (C_ORDER_DATE) REFERENCES dates,
    sales_to_regions AS sales (C_REGION_ID) REFERENCES regions,
    sales_to_categories AS sales (C_CATEGORY_ID) REFERENCES categories,
    sales_to_products AS sales (C_SKU) REFERENCES products,
    sales_to_stores AS sales (C_STORE_ID) REFERENCES stores,
    inventory_to_dates AS inventory (C_SNAPSHOT_DATE) REFERENCES dates,
    inventory_to_regions AS inventory (C_REGION_ID) REFERENCES regions,
    inventory_to_categories AS inventory (C_CATEGORY_ID) REFERENCES categories,
    inventory_to_products AS inventory (C_SKU) REFERENCES products,
    plan_to_dates AS plan (C_DATE_KEY) REFERENCES dates,
    plan_to_regions AS plan (C_REGION_ID) REFERENCES regions,
    plan_to_categories AS plan (C_CATEGORY_ID) REFERENCES categories
  )
  FACTS (
    sales.f_order_id AS C_ORDER_ID,
    sales.f_customer_id AS C_CUSTOMER_ID,
    sales.f_qty AS C_QTY,
    sales.f_gross_sales AS C_GROSS_SALES,
    sales.f_discount_amount AS C_DISCOUNT_AMOUNT,
    sales.f_net_sales AS C_NET_SALES,
    sales.f_cogs AS C_COGS,
    sales.f_gross_margin AS C_NET_SALES - C_COGS,
    sales.f_online_net_sales AS IFF(C_IS_ONLINE, C_NET_SALES, 0),
    sales.f_shipped_order_id AS IFF(C_IS_SHIPPED_ORDER, C_ORDER_ID, NULL),
    sales.f_free_ship_order_id AS IFF(C_FREE_SHIPPING_FLAG, C_ORDER_ID, NULL),
    sales.f_line_shipping_fee AS C_LINE_SHIPPING_FEE,
    sales.f_click_to_ship_hours AS C_CLICK_TO_SHIP_HOURS,
    sales.f_transit_days AS C_TRANSIT_DAYS,
    sales.f_delivery_days AS C_DELIVERY_DAYS,
    sales.f_on_time AS CASE WHEN C_ON_TIME_FLAG THEN 1 WHEN NOT C_ON_TIME_FLAG THEN 0 END,
    sales.f_returned_sales AS C_RETURNED_SALES,
    sales.f_returned_units AS C_RETURNED_UNITS,
    inventory.f_snapshot_date AS C_SNAPSHOT_DATE,
    inventory.f_units_on_hand AS C_UNITS_ON_HAND,
    inventory.f_inventory_value AS C_INVENTORY_VALUE,
    inventory.f_units_on_order AS C_UNITS_ON_ORDER,
    inventory.f_units_sold AS C_UNITS_SOLD,
    inventory.f_lost_units AS C_LOST_UNITS,
    inventory.f_stockout AS IFF(C_STOCKOUT_FLAG, 1, 0),
    plan.f_plan_net_sales AS C_PLAN_NET_SALES,
    plan.f_plan_units AS C_PLAN_UNITS,
    plan.f_plan_gross_margin AS C_PLAN_GROSS_MARGIN
  )
  DIMENSIONS (
    dates.calendar_date AS C_DATE_KEY WITH SYNONYMS = ('date', 'order date', 'day')
      COMMENT = 'Calendar day: order date for sales, snapshot date for inventory, plan date for targets.',
    dates.week_start AS C_WEEK_START WITH SYNONYMS = ('week') COMMENT = 'Monday that starts the week.',
    dates.month_start AS C_MONTH_START WITH SYNONYMS = ('month') COMMENT = 'First day of the month.',
    dates.month_name AS C_MONTH_NAME COMMENT = 'Month label, e.g. Sep 2026.',
    dates.cal_quarter AS C_CAL_QUARTER WITH SYNONYMS = ('quarter') COMMENT = 'Calendar quarter, e.g. 2026-Q3.',
    dates.cal_year AS C_CAL_YEAR WITH SYNONYMS = ('year', 'fiscal year') COMMENT = 'Calendar (= fiscal) year.',
    dates.day_of_week AS C_DAY_OF_WEEK COMMENT = 'Day name (Mon-Sun).',
    dates.is_weekend AS C_IS_WEEKEND COMMENT = 'Saturday or Sunday.',
    dates.holiday AS COALESCE(C_HOLIDAY_NAME, 'No holiday') COMMENT = 'US retail holiday on this date, if any.',
    dates.retail_season AS C_RETAIL_SEASON COMMENT = 'Holiday, Winter clearance, Spring, Summer, Back to school & fall.',
    regions.region AS C_REGION_NAME WITH SYNONYMS = ('sales region', 'territory', 'area')
      COMMENT = 'US sales region (Northeast, Southeast, Midwest, Southwest, West). Online orders use the ship-to region.',
    regions.distribution_center AS C_DC_NAME WITH SYNONYMS = ('DC', 'warehouse', 'fulfillment center')
      COMMENT = 'Distribution center serving the region.',
    categories.category AS C_CATEGORY_NAME WITH SYNONYMS = ('product category', 'department')
      COMMENT = 'Merchandise category: Apparel, Footwear or Accessories.',
    products.subcategory AS C_SUBCATEGORY WITH SYNONYMS = ('product type', 'class') COMMENT = 'Merchandise subcategory, e.g. Running Shoes.',
    products.brand AS C_BRAND COMMENT = 'House brand.',
    products.product_name AS C_PRODUCT_NAME WITH SYNONYMS = ('product', 'style', 'item') COMMENT = 'Product (SKU) name.',
    products.sku_code AS C_SKU WITH SYNONYMS = ('SKU', 'item number') COMMENT = 'Stock keeping unit code.',
    products.gender AS C_GENDER COMMENT = 'Target customer: Women, Men, Kids, Unisex.',
    products.price_tier AS C_PRICE_TIER COMMENT = 'Value, Core or Premium price tier.',
    products.color_family AS C_COLOR_FAMILY COMMENT = 'Primary color family.',
    stores.store AS C_STORE_NAME WITH SYNONYMS = ('store name', 'location') COMMENT = 'Store name (store channel only).',
    stores.store_format AS C_STORE_FORMAT COMMENT = 'Flagship, Mall, Outlet or Street.',
    stores.store_state AS C_STORE_STATE COMMENT = 'State where the store is located.',
    sales.channel AS C_CHANNEL WITH SYNONYMS = ('sales channel') COMMENT = 'Store, Web, App or Marketplace.',
    sales.ship_method AS COALESCE(C_SHIP_METHOD, 'In-store') WITH SYNONYMS = ('shipping method', 'delivery speed')
      COMMENT = 'Standard, Expedited, Next Day; In-store for store purchases.',
    sales.carrier AS COALESCE(C_CARRIER, 'In-store') WITH SYNONYMS = ('shipping carrier') COMMENT = 'Parcel carrier for shipped orders.',
    sales.loyalty_tier AS C_LOYALTY_TIER WITH SYNONYMS = ('membership tier', 'customer tier')
      COMMENT = 'Guest, Member, Silver, Gold or Platinum at time of order.',
    sales.age_band AS C_AGE_BAND COMMENT = 'Customer age band (Unknown for guests).',
    sales.customer_state AS C_CUSTOMER_STATE WITH SYNONYMS = ('state', 'ship-to state') COMMENT = 'Ship-to state (store state for store purchases).',
    sales.fulfillment_status AS C_FULFILLMENT_STATUS COMMENT = 'Processing, In transit, Delivered, or In-store purchase - as of now.',
    sales.promotion AS COALESCE(C_PROMO_NAME, 'Full price') WITH SYNONYMS = ('promo', 'campaign', 'event')
      COMMENT = 'Promotion or markdown applied to the line; Full price when none.',
    sales.return_reason AS COALESCE(C_RETURN_REASON, 'Not returned') COMMENT = 'Reason given for the return.',
    sales.order_hour AS C_ORDER_HOUR COMMENT = 'Hour of day the order was placed (US Eastern).'
  )
  METRICS (
    sales.net_sales AS SUM(sales.f_net_sales) WITH SYNONYMS = ('revenue', 'sales', 'net revenue')
      COMMENT = 'Net merchandise sales (USD): list price x units minus discounts. Excludes tax, shipping fees and returns.',
    sales.gross_sales AS SUM(sales.f_gross_sales) WITH SYNONYMS = ('gross revenue')
      COMMENT = 'Sales at list price before discounts (USD).',
    sales.discount_amount AS SUM(sales.f_discount_amount) WITH SYNONYMS = ('markdowns', 'promotional discount')
      COMMENT = 'Value of promotional discounts, markdowns and member coupons (USD).',
    sales.discount_rate AS DIV0(sales.discount_amount, sales.gross_sales)
      COMMENT = 'Discount amount / gross sales.',
    sales.cost_of_goods_sold AS SUM(sales.f_cogs) WITH SYNONYMS = ('COGS', 'product cost') COMMENT = 'Landed unit cost x units (USD).',
    sales.gross_margin AS SUM(sales.f_gross_margin) WITH SYNONYMS = ('gross profit', 'margin dollars')
      COMMENT = 'Net sales minus cost of goods sold (USD).',
    sales.gross_margin_pct AS DIV0(sales.gross_margin, sales.net_sales) WITH SYNONYMS = ('margin rate', 'GM%')
      COMMENT = 'Gross margin / net sales.',
    sales.units_sold AS SUM(sales.f_qty) WITH SYNONYMS = ('units', 'quantity sold') COMMENT = 'Units sold (fulfilled).',
    sales.order_count AS COUNT(DISTINCT sales.f_order_id) WITH SYNONYMS = ('orders', 'transactions', 'number of orders')
      COMMENT = 'Distinct orders. With a product breakdown it counts orders containing that product.',
    sales.average_order_value AS DIV0(sales.net_sales, sales.order_count) WITH SYNONYMS = ('AOV', 'basket size')
      COMMENT = 'Net sales / orders.',
    sales.units_per_transaction AS DIV0(sales.units_sold, sales.order_count) WITH SYNONYMS = ('UPT', 'units per order')
      COMMENT = 'Units / orders.',
    sales.active_customers AS COUNT(DISTINCT sales.f_customer_id) WITH SYNONYMS = ('customers', 'buyers')
      COMMENT = 'Distinct identified customers who ordered (guests excluded).',
    sales.online_net_sales AS SUM(sales.f_online_net_sales) WITH SYNONYMS = ('digital sales', 'ecommerce sales')
      COMMENT = 'Net sales from Web, App and Marketplace (USD).',
    sales.online_sales_share AS DIV0(sales.online_net_sales, sales.net_sales) WITH SYNONYMS = ('digital share', 'ecommerce penetration')
      COMMENT = 'Share of net sales from Web, App and Marketplace.',
    sales.shipped_orders AS COUNT(DISTINCT sales.f_shipped_order_id)
      COMMENT = 'Orders shipped to customers (Web, App, Marketplace).',
    sales.free_shipping_orders AS COUNT(DISTINCT sales.f_free_ship_order_id)
      COMMENT = 'Shipped orders with a 0 USD shipping fee.',
    sales.free_shipping_order_pct AS DIV0(sales.free_shipping_orders, sales.shipped_orders)
      WITH SYNONYMS = ('free shipping %', 'free shipping rate')
      COMMENT = 'Shipped orders with a 0 USD shipping fee / all shipped orders. Free when subtotal meets the threshold (99 USD, 119 USD from Mar 2026), for Gold and Platinum members, on free-shipping promotion days, or by marketplace policy.',
    sales.shipping_fee_revenue AS SUM(sales.f_line_shipping_fee) COMMENT = 'Shipping fees charged to customers (USD).',
    sales.avg_click_to_ship_hours AS AVG(sales.f_click_to_ship_hours) WITH SYNONYMS = ('fulfillment time', 'order to ship time', 'processing time')
      COMMENT = 'Average hours from order placed to carrier hand-off, over shipped order lines.',
    sales.avg_transit_days AS AVG(sales.f_transit_days) WITH SYNONYMS = ('carrier transit time')
      COMMENT = 'Average days from carrier hand-off to delivery, over delivered order lines.',
    sales.avg_delivery_days AS AVG(sales.f_delivery_days) WITH SYNONYMS = ('shipping time', 'avg shipping time', 'delivery time', 'click to door')
      COMMENT = 'Average days from order placed to delivery, over delivered order lines.',
    sales.on_time_delivery_pct AS AVG(sales.f_on_time) WITH SYNONYMS = ('OTD', 'on-time rate')
      COMMENT = 'Delivered lines that arrived on or before the promised date (Standard 6 days, Expedited 3, Next Day 2) / all delivered lines.',
    sales.returned_sales AS SUM(sales.f_returned_sales) COMMENT = 'Net sales value of items returned so far (USD).',
    sales.returned_units AS SUM(sales.f_returned_units) COMMENT = 'Units returned so far.',
    sales.return_rate AS DIV0(sales.returned_sales, sales.net_sales) WITH SYNONYMS = ('returns %')
      COMMENT = 'Returned sales / net sales for orders placed in the period. Recent periods rise as returns arrive.',
    sales.net_sales_after_returns AS sales.net_sales - sales.returned_sales COMMENT = 'Net sales less returns (USD).',
    inventory.helper_inventory_days AS COUNT(DISTINCT inventory.f_snapshot_date)
      COMMENT = 'Helper: number of days with inventory snapshots in the selection.',
    inventory.helper_unit_days AS SUM(inventory.f_units_on_hand) COMMENT = 'Helper: end-of-day units summed over days.',
    inventory.helper_value_days AS SUM(inventory.f_inventory_value) COMMENT = 'Helper: end-of-day inventory value summed over days.',
    inventory.helper_on_order_days AS SUM(inventory.f_units_on_order) COMMENT = 'Helper: open order units summed over days.',
    inventory.avg_units_on_hand AS DIV0(inventory.helper_unit_days, inventory.helper_inventory_days)
      WITH SYNONYMS = ('units on hand', 'inventory units', 'stock on hand')
      COMMENT = 'Average daily end-of-day units on hand: stock is summed across the selected SKUs and DCs, then averaged over days (stock is never added up across days).',
    inventory.avg_inventory_value AS DIV0(inventory.helper_value_days, inventory.helper_inventory_days)
      WITH SYNONYMS = ('inventory value', 'stock value') COMMENT = 'Average daily inventory value at cost (USD).',
    inventory.avg_units_on_order AS DIV0(inventory.helper_on_order_days, inventory.helper_inventory_days)
      WITH SYNONYMS = ('on order', 'open PO units') COMMENT = 'Average daily units on open replenishment orders.',
    inventory.units_sold_from_stock AS SUM(inventory.f_units_sold) COMMENT = 'Units fulfilled from DC stock (equals units sold for the same slice).',
    inventory.lost_sales_units AS SUM(inventory.f_lost_units) WITH SYNONYMS = ('lost sales', 'unmet demand')
      COMMENT = 'Units customers wanted that could not be fulfilled because the DC was out of stock.',
    inventory.stockout_rate AS AVG(inventory.f_stockout) WITH SYNONYMS = ('out of stock %', 'OOS rate')
      COMMENT = 'Share of SKU x DC x day records ending with zero units on hand.',
    inventory.in_stock_rate AS 1 - inventory.stockout_rate WITH SYNONYMS = ('in-stock %', 'availability')
      COMMENT = 'Share of SKU x DC x day records ending with stock available.',
    inventory.weeks_of_supply AS DIV0(inventory.helper_unit_days, 7 * inventory.units_sold_from_stock) WITH SYNONYMS = ('WOS', 'weeks of cover')
      COMMENT = 'Average units on hand / average weekly units sold.',
    inventory.sell_through_pct AS DIV0(inventory.units_sold_from_stock, inventory.units_sold_from_stock + inventory.avg_units_on_hand)
      WITH SYNONYMS = ('sell-through', 'sell thru')
      COMMENT = 'Units sold / (units sold + average daily units on hand) for the period.',
    plan.plan_net_sales AS SUM(plan.f_plan_net_sales) WITH SYNONYMS = ('sales plan', 'sales target', 'budget')
      COMMENT = 'Planned net sales (USD).',
    plan.plan_units AS SUM(plan.f_plan_units) WITH SYNONYMS = ('unit plan') COMMENT = 'Planned units.',
    plan.plan_gross_margin AS SUM(plan.f_plan_gross_margin) WITH SYNONYMS = ('margin plan') COMMENT = 'Planned gross margin (USD).'
  )
  COMMENT = 'Harborline Outfitters (fictional US retailer): live sales, fulfillment, inventory and plan.'$$);

EXECUTE IMMEDIATE $$
DECLARE
  c CURSOR FOR SELECT ATTEMPT, NAME, DDL FROM WBR_DB.RETAIL_DEMO.SV_DDL ORDER BY ATTEMPT;
  errs VARCHAR DEFAULT '';
  stmt VARCHAR;
BEGIN
  FOR r IN c DO
    stmt := r.DDL;
    BEGIN
      EXECUTE IMMEDIATE :stmt;
      RETURN 'RETAIL_ANALYTICS_SV created (' || r.NAME || ')' || IFF(errs = '', '', ' | earlier attempts: ' || errs);
    EXCEPTION
      WHEN OTHER THEN
        errs := errs || '[' || r.ATTEMPT || '] ' || LEFT(SQLERRM, 300) || ' ';
    END;
  END FOR;
  RETURN 'FAILED: ' || errs;
END;
$$;

DESCRIBE SEMANTIC VIEW WBR_DB.RETAIL_DEMO.RETAIL_ANALYTICS_SV;
