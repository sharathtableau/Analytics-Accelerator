-- =====================================================================================
-- Harborline Outfitters (FICTIONAL US apparel / footwear / accessories retailer)
-- Step 1: reference data (calendar, regions, categories, subcategories, products,
--         stores, customers, promotion calendar, carriers).
-- All data is synthetic, generated inside Snowflake. Nothing here is real company data.
-- =====================================================================================
USE ROLE WBR_OWNER;
USE WAREHOUSE POWERHOUSE;
CREATE SCHEMA IF NOT EXISTS WBR_DB.RETAIL_DEMO
  COMMENT = 'Harborline Outfitters: fictional US omnichannel retailer, synthetic data generated in Snowflake for demos';
USE SCHEMA WBR_DB.RETAIL_DEMO;

-- History starts Oct 2023; rows are pre-generated to 31 Dec 2026 and revealed by the
-- live views only once their timestamp has passed (simulated real-time feed).
SET START_DATE = '2023-10-01'::DATE;
SET END_DATE   = '2026-12-31'::DATE;

-- ------------------------------------------------------------------ calendar
CREATE OR REPLACE TABLE DIM_DATE (DATE_KEY, CAL_YEAR, CAL_QUARTER, MONTH_START, MONTH_NAME, MONTH_NUM, WEEK_START, DAY_OF_WEEK, DOW_ISO, IS_WEEKEND, HOLIDAY_NAME, RETAIL_SEASON) AS
WITH d AS (
  SELECT DATEADD(day, SEQ4(), $START_DATE) AS DATE_KEY
  FROM TABLE(GENERATOR(ROWCOUNT => 1300))
), h AS (
  SELECT column1::DATE AS D, column2 AS NAME FROM VALUES
  ('2023-11-23','Thanksgiving'),('2023-11-24','Black Friday'),('2023-11-27','Cyber Monday'),('2023-12-25','Christmas Day'),
  ('2024-01-01','New Year''s Day'),('2024-05-27','Memorial Day'),('2024-07-04','Independence Day'),('2024-09-02','Labor Day'),
  ('2024-11-28','Thanksgiving'),('2024-11-29','Black Friday'),('2024-12-02','Cyber Monday'),('2024-12-25','Christmas Day'),
  ('2025-01-01','New Year''s Day'),('2025-05-26','Memorial Day'),('2025-07-04','Independence Day'),('2025-09-01','Labor Day'),
  ('2025-11-27','Thanksgiving'),('2025-11-28','Black Friday'),('2025-12-01','Cyber Monday'),('2025-12-25','Christmas Day'),
  ('2026-01-01','New Year''s Day'),('2026-05-25','Memorial Day'),('2026-07-04','Independence Day'),('2026-09-07','Labor Day'),
  ('2026-11-26','Thanksgiving'),('2026-11-27','Black Friday'),('2026-11-30','Cyber Monday'),('2026-12-25','Christmas Day')
)
SELECT d.DATE_KEY, YEAR(d.DATE_KEY), YEAR(d.DATE_KEY) || '-Q' || QUARTER(d.DATE_KEY),
       DATE_TRUNC('month', d.DATE_KEY), TO_CHAR(d.DATE_KEY, 'Mon YYYY'), MONTH(d.DATE_KEY),
       DATEADD(day, 1 - DAYOFWEEKISO(d.DATE_KEY), d.DATE_KEY), DAYNAME(d.DATE_KEY), DAYOFWEEKISO(d.DATE_KEY),
       DAYOFWEEKISO(d.DATE_KEY) >= 6, h.NAME,
       CASE WHEN MONTH(d.DATE_KEY) IN (11, 12) THEN 'Holiday'
            WHEN MONTH(d.DATE_KEY) IN (1, 2) THEN 'Winter clearance'
            WHEN MONTH(d.DATE_KEY) IN (3, 4, 5) THEN 'Spring'
            WHEN MONTH(d.DATE_KEY) IN (6, 7) THEN 'Summer'
            ELSE 'Back to school & fall' END
FROM d LEFT JOIN h ON h.D = d.DATE_KEY
WHERE d.DATE_KEY <= $END_DATE;

-- ------------------------------------------------------------------ regions / DCs (1 DC serves each region)
CREATE OR REPLACE TABLE DIM_REGION (REGION_ID, REGION_NAME, DC_NAME, DC_CITY, DC_STATE, DEMAND_SHARE, BASE_CLICK_TO_SHIP_HOURS, CLIMATE) AS
SELECT column1, column2, column3, column4, column5, column6, column7, column8 FROM VALUES
 (1, 'Northeast', 'Edison DC',   'Edison',   'NJ', 0.23, 18, 'north'),
 (2, 'Southeast', 'Atlanta DC',  'Atlanta',  'GA', 0.21, 20, 'south'),
 (3, 'Midwest',   'Columbus DC', 'Columbus', 'OH', 0.18, 16, 'north'),
 (4, 'Southwest', 'Dallas DC',   'Dallas',   'TX', 0.16, 19, 'south'),
 (5, 'West',      'Reno DC',     'Reno',     'NV', 0.22, 21, 'west');

CREATE OR REPLACE TABLE DIM_STATE (STATE_CODE, STATE_NAME, REGION_ID, WEIGHT) AS
SELECT column1, column2, column3, column4 FROM VALUES
 ('NY','New York',1,0.38),('NJ','New Jersey',1,0.18),('PA','Pennsylvania',1,0.24),('MA','Massachusetts',1,0.13),('CT','Connecticut',1,0.07),
 ('FL','Florida',2,0.36),('GA','Georgia',2,0.19),('NC','North Carolina',2,0.19),('VA','Virginia',2,0.15),('TN','Tennessee',2,0.11),
 ('IL','Illinois',3,0.31),('OH','Ohio',3,0.24),('MI','Michigan',3,0.20),('MN','Minnesota',3,0.13),('WI','Wisconsin',3,0.12),
 ('TX','Texas',4,0.60),('AZ','Arizona',4,0.15),('CO','Colorado',4,0.12),('OK','Oklahoma',4,0.08),('NM','New Mexico',4,0.05),
 ('CA','California',5,0.58),('WA','Washington',5,0.17),('OR','Oregon',5,0.09),('NV','Nevada',5,0.07),('UT','Utah',5,0.09);

-- ------------------------------------------------------------------ stores (12 per region)
CREATE OR REPLACE TABLE DIM_STORE (STORE_ID, STORE_NAME, STORE_CITY, STORE_STATE, STORE_FORMAT, REGION_ID, REGION_STORE_IDX, OPENED_YEAR) AS
WITH s AS (
  SELECT column1 AS CITY, column2 AS ST, column3 AS FMT, column4 AS REGION_ID FROM VALUES
  ('New York','NY','Flagship',1),('Brooklyn','NY','Street',1),('Long Island','NY','Mall',1),('Buffalo','NY','Mall',1),
  ('Newark','NJ','Mall',1),('Paramus','NJ','Outlet',1),('Philadelphia','PA','Flagship',1),('Pittsburgh','PA','Mall',1),
  ('King of Prussia','PA','Mall',1),('Boston','MA','Flagship',1),('Natick','MA','Mall',1),('Stamford','CT','Street',1),
  ('Miami','FL','Flagship',2),('Orlando','FL','Outlet',2),('Tampa','FL','Mall',2),('Jacksonville','FL','Mall',2),
  ('Atlanta','GA','Flagship',2),('Savannah','GA','Street',2),('Charlotte','NC','Mall',2),('Raleigh','NC','Mall',2),
  ('Arlington','VA','Mall',2),('Richmond','VA','Outlet',2),('Nashville','TN','Street',2),('Memphis','TN','Mall',2),
  ('Chicago','IL','Flagship',3),('Schaumburg','IL','Mall',3),('Oak Brook','IL','Mall',3),('Columbus','OH','Mall',3),
  ('Cleveland','OH','Mall',3),('Cincinnati','OH','Outlet',3),('Detroit','MI','Mall',3),('Grand Rapids','MI','Street',3),
  ('Minneapolis','MN','Flagship',3),('Bloomington','MN','Mall',3),('Milwaukee','WI','Mall',3),('Madison','WI','Street',3),
  ('Dallas','TX','Flagship',4),('Plano','TX','Mall',4),('Houston','TX','Flagship',4),('The Woodlands','TX','Mall',4),
  ('Austin','TX','Street',4),('San Antonio','TX','Outlet',4),('Phoenix','AZ','Mall',4),('Scottsdale','AZ','Street',4),
  ('Denver','CO','Flagship',4),('Boulder','CO','Street',4),('Oklahoma City','OK','Mall',4),('Albuquerque','NM','Mall',4),
  ('Los Angeles','CA','Flagship',5),('San Francisco','CA','Flagship',5),('San Diego','CA','Mall',5),('Irvine','CA','Mall',5),
  ('San Jose','CA','Mall',5),('Sacramento','CA','Outlet',5),('Seattle','WA','Flagship',5),('Bellevue','WA','Mall',5),
  ('Portland','OR','Street',5),('Las Vegas','NV','Outlet',5),('Salt Lake City','UT','Mall',5),('Reno','NV','Street',5)
)
SELECT ROW_NUMBER() OVER (ORDER BY REGION_ID, CITY), CITY || ' ' || FMT, CITY, ST, FMT, REGION_ID,
       ROW_NUMBER() OVER (PARTITION BY REGION_ID ORDER BY CITY),
       2008 + MOD(ABS(HASH(CITY)), 14)
FROM s;

-- ------------------------------------------------------------------ categories / subcategories / products
CREATE OR REPLACE TABLE DIM_CATEGORY (CATEGORY_ID, CATEGORY_NAME, SKU_PREFIX) AS
SELECT column1, column2, column3 FROM VALUES (1, 'Apparel', 'AP'), (2, 'Footwear', 'FW'), (3, 'Accessories', 'AC');

-- Behavioural parameters per subcategory (drive seasonality, regional mix, price, margin, returns).
CREATE OR REPLACE TABLE REF_SUBCATEGORY (SUBCATEGORY_ID, CATEGORY_ID, SUBCATEGORY, BASE_PRICE, MARGIN, DEMAND_SHARE, PEAK_MONTH, SEASON_AMP, NORTH_F, SOUTH_F, WEST_F, RETURN_ONLINE, RETURN_STORE, SKU_COUNT, NOUNS, SEASON_GROUP) AS
SELECT column1, column2, column3, column4, column5, column6, column7, column8, column9, column10, column11,
       column12, column13, column14, SPLIT(column15, '|'), column16 FROM VALUES
 (1, 1,'T-Shirts & Tops',     28, .62, .110,  7, .15, .95, 1.08, 1.00, .14, .05, 105, 'Crew Tee|V-Neck Tee|Tank|Long Sleeve Tee|Graphic Tee', 'core'),
 (2, 1,'Shirts & Blouses',    48, .58, .050,  4, .10,1.00, 1.00, 1.00, .16, .06,  65, 'Oxford Shirt|Flannel Shirt|Linen Shirt|Blouse|Poplin Shirt', 'core'),
 (3, 1,'Sweaters & Hoodies',  62, .60, .070, 12, .55,1.20,  .80, 1.00, .15, .05,  80, 'Crewneck Sweater|Hoodie|Cardigan|Quarter-Zip|Fleece Pullover', 'winter'),
 (4, 1,'Jackets & Outerwear',145, .55, .060, 12, .80,1.35,  .70, 1.05, .12, .04,  75, 'Puffer Jacket|Rain Shell|Parka|Denim Jacket|Softshell Jacket', 'winter'),
 (5, 1,'Pants & Jeans',       64, .57, .095, 10, .15,1.00, 1.00, 1.00, .20, .07,  95, 'Slim Jean|Chino|Jogger|Cargo Pant|Straight Jean', 'core'),
 (6, 1,'Shorts',              38, .60, .040,  7, .75, .80, 1.25, 1.05, .15, .05,  45, 'Chino Short|Running Short|Denim Short|Board Short', 'summer'),
 (7, 1,'Dresses & Skirts',    72, .60, .040,  5, .35, .95, 1.10, 1.05, .24, .08,  55, 'Wrap Dress|Midi Skirt|Sundress|Shirt Dress|Knit Dress', 'core'),
 (8, 1,'Activewear',          52, .63, .070,  1, .15,1.00, 1.00, 1.20, .13, .05,  75, 'Legging|Sports Bra|Training Tee|Track Jacket|Yoga Pant', 'core'),
 (9, 1,'Swimwear',            46, .62, .030,  6, .90, .70, 1.35, 1.10, .19, .06,  40, 'Swimsuit|Bikini Set|Swim Trunk|Rash Guard', 'summer'),
 (10,1,'Socks & Underwear',   16, .66, .065, 11, .10,1.00, 1.00, 1.00, .03, .01,  45, 'Crew Sock 3-Pack|Boxer Brief 3-Pack|Ankle Sock 6-Pack|Bralette', 'core'),
 (11,2,'Running Shoes',      118, .45, .048,  4, .20, .95, 1.00, 1.20, .21, .07,  60, 'Road Runner|Trail Runner|Tempo Trainer|Cushion Runner', 'core'),
 (12,2,'Sneakers',            92, .47, .052,  8, .20,1.00, 1.00, 1.05, .19, .06,  65, 'Court Sneaker|Canvas Low|Retro Runner|Slip-On Sneaker', 'core'),
 (13,2,'Boots',              148, .48, .030, 11, .75,1.35,  .70, 1.00, .17, .05,  45, 'Chelsea Boot|Hiking Boot|Winter Boot|Chukka Boot', 'winter'),
 (14,2,'Sandals & Slides',    42, .52, .025,  6, .85, .75, 1.30, 1.10, .12, .04,  40, 'Slide|Sport Sandal|Flip Flop|Strappy Sandal', 'summer'),
 (15,2,'Dress Shoes',        128, .46, .010,  4, .15,1.05,  .95,  .95, .18, .06,  25, 'Oxford|Loafer|Derby|Pump', 'core'),
 (16,2,'Slippers',            38, .55, .010, 12, .80,1.20,  .80, 1.00, .08, .03,  20, 'Moccasin Slipper|Scuff Slipper|Bootie Slipper', 'winter'),
 (17,3,'Bags & Backpacks',    78, .63, .040,  8, .30,1.00, 1.00, 1.00, .08, .03,  55, 'Daypack|Tote|Crossbody|Duffel|Laptop Backpack', 'core'),
 (18,3,'Hats & Beanies',      26, .68, .025, 12, .50,1.25,  .85, 1.00, .06, .02,  40, 'Beanie|Baseball Cap|Bucket Hat|Sun Hat', 'core'),
 (19,3,'Gloves & Scarves',    32, .68, .015, 12, .90,1.40,  .60,  .90, .05, .02,  35, 'Knit Glove|Touchscreen Glove|Wool Scarf|Infinity Scarf', 'winter'),
 (20,3,'Belts & Wallets',     44, .66, .020,  5, .10,1.00, 1.00, 1.00, .06, .03,  35, 'Leather Belt|Bifold Wallet|Card Case|Reversible Belt', 'core'),
 (21,3,'Sunglasses',          58, .70, .020,  6, .60, .85, 1.20, 1.15, .09, .03,  35, 'Aviator|Wayfarer|Sport Shield|Round Frame', 'summer'),
 (22,3,'Watches',            165, .55, .010, 12, .30,1.00, 1.00, 1.00, .07, .03,  20, 'Field Watch|Chronograph|Minimal Watch|Smart Band', 'core'),
 (23,3,'Jewelry',             48, .72, .015,  2, .25,1.00, 1.00, 1.00, .07, .03,  35, 'Pendant Necklace|Stud Earrings|Bangle|Chain Bracelet', 'core');

CREATE OR REPLACE TABLE DIM_PRODUCT (SKU, PRODUCT_NAME, CATEGORY_ID, SUBCATEGORY_ID, SUBCATEGORY, BRAND, GENDER, PRICE_TIER, COLOR_FAMILY, LIST_PRICE, UNIT_COST, POPULARITY) AS
WITH n AS (SELECT SEQ4() AS I FROM TABLE(GENERATOR(ROWCOUNT => 200))),
base AS (
  SELECT s.*, n.I, s.SUBCATEGORY_ID * 1000 + n.I AS PID,
         MOD(ABS(HASH(s.SUBCATEGORY_ID, n.I, 'u1')), 1000000) / 1e6 AS U1,
         MOD(ABS(HASH(s.SUBCATEGORY_ID, n.I, 'u2')), 1000000) / 1e6 AS U2,
         MOD(ABS(HASH(s.SUBCATEGORY_ID, n.I, 'u3')), 1000000) / 1e6 AS U3,
         MOD(ABS(HASH(s.SUBCATEGORY_ID, n.I, 'u4')), 1000000) / 1e6 AS U4
  FROM REF_SUBCATEGORY s JOIN n ON n.I < s.SKU_COUNT
), attrs AS (
  SELECT b.*,
    CASE WHEN U1 < .30 THEN 'Value' WHEN U1 < .80 THEN 'Core' ELSE 'Premium' END AS TIER,
    GET(ARRAY_CONSTRUCT('Harbor & Pine','Ridgewell','Kestrel Athletic','Maple Row','Summit Loom','Tidewater','Oakhaven','Bramble & Co'),
        MOD(ABS(HASH(SUBCATEGORY_ID, I, 'brand')), 8))::VARCHAR AS BRAND,
    GET(ARRAY_CONSTRUCT('Classic','Everyday','Trail','Urban','Performance','Heritage','Lightweight','Essential','Relaxed',
                        'Tech','Coastal','Alpine','Studio','Weekend','Signature'),
        MOD(ABS(HASH(SUBCATEGORY_ID, I, 'adj')), 15))::VARCHAR AS ADJ,
    GET(NOUNS, MOD(ABS(HASH(SUBCATEGORY_ID, I, 'noun')), ARRAY_SIZE(NOUNS)))::VARCHAR AS NOUN,
    GET(ARRAY_CONSTRUCT('Black','Navy','Grey','White','Olive','Tan','Red','Blue','Green','Brown'),
        MOD(ABS(HASH(SUBCATEGORY_ID, I, 'color')), 10))::VARCHAR AS COLOR
  FROM base b
), gendered AS (
  SELECT a.*,
    CASE WHEN SUBCATEGORY_ID = 7 OR NOUN IN ('Blouse', 'Sports Bra', 'Legging', 'Yoga Pant', 'Swimsuit', 'Bikini Set', 'Bralette',
                                               'Pump', 'Strappy Sandal', 'Stud Earrings', 'Pendant Necklace', 'Bangle', 'Crossbody', 'Tote')
              THEN IFF(U2 < .88, 'Women', 'Kids')
         WHEN NOUN IN ('Swim Trunk', 'Boxer Brief 3-Pack', 'Board Short', 'Derby') THEN IFF(U2 < .88, 'Men', 'Kids')
         WHEN NOUN IN ('Watch', 'Field Watch', 'Chronograph', 'Minimal Watch', 'Smart Band', 'Aviator', 'Wayfarer', 'Sport Shield',
                       'Round Frame', 'Daypack', 'Duffel', 'Laptop Backpack', 'Beanie', 'Baseball Cap', 'Bucket Hat', 'Wool Scarf',
                       'Infinity Scarf', 'Card Case', 'Crew Sock 3-Pack', 'Ankle Sock 6-Pack', 'Slide', 'Flip Flop')
              THEN CASE WHEN U2 < .40 THEN 'Unisex' WHEN U2 < .72 THEN 'Women' WHEN U2 < .95 THEN 'Men' ELSE 'Kids' END
         ELSE CASE WHEN U2 < .48 THEN 'Women' WHEN U2 < .88 THEN 'Men' ELSE 'Kids' END END AS GENDER
  FROM attrs a
), priced AS (
  SELECT a.*, IFF(GENDER = 'Kids', 0.7, 1.0) AS KIDS_F, ROUND(BASE_PRICE * DECODE(TIER, 'Value', .72, 'Core', 1.0, 1.6) * (0.85 + U3 * 0.3) * IFF(GENDER = 'Kids', 0.7, 1.0)) - 0.01 AS LP
  FROM gendered a
)
SELECT c.SKU_PREFIX || '-' || LPAD(TO_VARCHAR(PID), 5, '0'),
       BRAND || ' ' || ADJ || ' ' || NOUN, p.CATEGORY_ID, SUBCATEGORY_ID, SUBCATEGORY, BRAND, GENDER, TIER, COLOR,
       GREATEST(LP, 4.99), ROUND(GREATEST(LP, 4.99) * (1 - MARGIN + (U4 - 0.5) * 0.08), 2),
       1 / POWER(1 + ROW_NUMBER() OVER (PARTITION BY SUBCATEGORY_ID ORDER BY U4 DESC), 0.75)
FROM priced p JOIN DIM_CATEGORY c ON c.CATEGORY_ID = p.CATEGORY_ID;

-- ------------------------------------------------------------------ customers (loyalty programme)
CREATE OR REPLACE TABLE DIM_CUSTOMER (CUSTOMER_ID, REGION_ID, REGION_CUST_IDX, STATE_CODE, LOYALTY_TIER, AGE_BAND, JOINED_DATE) AS
WITH g AS (
  SELECT SEQ4() + 1 AS CUSTOMER_ID, UNIFORM(0::FLOAT, 1::FLOAT, RANDOM()) AS U_REGION,
         UNIFORM(0::FLOAT, 1::FLOAT, RANDOM()) AS U_TIER, UNIFORM(0::FLOAT, 1::FLOAT, RANDOM()) AS U_AGE,
         UNIFORM(0::FLOAT, 1::FLOAT, RANDOM()) AS U_STATE
  FROM TABLE(GENERATOR(ROWCOUNT => 600000))
), r AS (
  SELECT g.*, CASE WHEN U_REGION < .23 THEN 1 WHEN U_REGION < .44 THEN 2 WHEN U_REGION < .62 THEN 3
                   WHEN U_REGION < .78 THEN 4 ELSE 5 END AS REGION_ID
  FROM g
), st AS (
  SELECT STATE_CODE, REGION_ID,
         SUM(WEIGHT) OVER (PARTITION BY REGION_ID ORDER BY STATE_CODE) - WEIGHT AS LO
  FROM DIM_STATE
)
SELECT r.CUSTOMER_ID, r.REGION_ID, ROW_NUMBER() OVER (PARTITION BY r.REGION_ID ORDER BY r.CUSTOMER_ID),
       st.STATE_CODE,
       CASE WHEN U_TIER < .40 THEN 'Member' WHEN U_TIER < .72 THEN 'Silver' WHEN U_TIER < .92 THEN 'Gold' ELSE 'Platinum' END,
       CASE WHEN U_AGE < .12 THEN '18-24' WHEN U_AGE < .38 THEN '25-34' WHEN U_AGE < .62 THEN '35-44'
            WHEN U_AGE < .82 THEN '45-54' ELSE '55+' END,
       DATEADD(day, -UNIFORM(0, 2500, RANDOM()), '2026-09-30'::DATE)
FROM r ASOF JOIN st MATCH_CONDITION (r.U_STATE >= st.LO) ON r.REGION_ID = st.REGION_ID;

-- ------------------------------------------------------------------ promotions & events
-- Demand multipliers per channel group, discounts, free-shipping periods. SCOPE: ALL or a
-- '|'-delimited list of subcategory names.
CREATE OR REPLACE TABLE REF_EVENT (EVENT_NAME, START_DATE, END_DATE, STORE_MULT, ONLINE_MULT, DISCOUNT, SCOPE, FREE_SHIP) AS
WITH y AS (SELECT column1 AS Y, column2::DATE AS TG FROM VALUES (2023,'2023-11-23'),(2024,'2024-11-28'),(2025,'2025-11-27'),(2026,'2026-11-26'))
SELECT 'Thanksgiving', TG, TG, 0.0, 1.6, 0.20, 'ALL', FALSE FROM y UNION ALL
SELECT 'Black Friday', DATEADD(day,1,TG), DATEADD(day,1,TG), 2.6, 3.0, 0.30, 'ALL', TRUE FROM y UNION ALL
SELECT 'Black Friday weekend', DATEADD(day,2,TG), DATEADD(day,3,TG), 1.8, 1.7, 0.25, 'ALL', TRUE FROM y UNION ALL
SELECT 'Cyber Monday', DATEADD(day,4,TG), DATEADD(day,4,TG), 1.1, 3.4, 0.30, 'ALL', TRUE FROM y UNION ALL
SELECT 'Holiday gifting', DATEADD(day,5,TG), DATE_FROM_PARTS(Y,12,22), 1.40, 1.45, 0.15, 'ALL', FALSE FROM y UNION ALL
SELECT 'Holiday free shipping', DATE_FROM_PARTS(Y,12,1), DATE_FROM_PARTS(Y,12,15), 1.0, 1.0, 0.0, 'ALL', TRUE FROM y UNION ALL
SELECT 'Christmas Eve', DATE_FROM_PARTS(Y,12,24), DATE_FROM_PARTS(Y,12,24), 1.3, 0.7, 0.0, 'ALL', FALSE FROM y UNION ALL
SELECT 'Christmas Day', DATE_FROM_PARTS(Y,12,25), DATE_FROM_PARTS(Y,12,25), 0.0, 0.45, 0.0, 'ALL', FALSE FROM y UNION ALL
SELECT 'After-Christmas sale', DATE_FROM_PARTS(Y,12,26), DATE_FROM_PARTS(Y,12,31), 1.35, 1.3, 0.25, 'ALL', FALSE FROM y UNION ALL
SELECT 'Winter clearance', DATE_FROM_PARTS(Y+1,1,2), DATE_FROM_PARTS(Y+1,2,15), 0.85, 0.85, 0.35,
       'Jackets & Outerwear|Boots|Sweaters & Hoodies|Gloves & Scarves|Slippers', FALSE FROM y WHERE Y < 2026 UNION ALL
SELECT 'Memorial Day sale', column1::DATE - 2, column1::DATE, 1.3, 1.35, 0.20, 'ALL', FALSE
  FROM VALUES ('2024-05-27'),('2025-05-26'),('2026-05-25') UNION ALL
SELECT 'Summer sale', column1::DATE, column1::DATE + 2, 1.2, 1.9, 0.25, 'ALL', TRUE
  FROM VALUES ('2024-07-16'),('2025-07-15'),('2026-07-14') UNION ALL
SELECT 'Back to school', column1::DATE, column1::DATE + 30, 1.2, 1.2, 0.15,
       'Bags & Backpacks|Sneakers|Running Shoes|T-Shirts & Tops|Pants & Jeans|Activewear', FALSE
  FROM VALUES ('2024-08-01'),('2025-08-01'),('2026-08-01') UNION ALL
SELECT 'End-of-summer clearance', column1::DATE, column1::DATE + 20, 1.0, 1.05, 0.35,
       'Swimwear|Sandals & Slides|Shorts|Sunglasses', FALSE
  FROM VALUES ('2024-08-20'),('2025-08-20'),('2026-08-20') UNION ALL
SELECT 'Labor Day sale', column1::DATE - 2, column1::DATE, 1.25, 1.3, 0.20, 'ALL', FALSE
  FROM VALUES ('2024-09-02'),('2025-09-01'),('2026-09-07');

-- ------------------------------------------------------------------ carriers & shipping service levels
CREATE OR REPLACE TABLE REF_CARRIER (CARRIER, SHIP_METHOD, BASE_TRANSIT_DAYS, SLA_DAYS) AS
SELECT column1, column2, column3, column4 FROM VALUES
 ('USPS','Standard',4.2,6),('UPS','Standard',3.7,6),('FedEx','Standard',3.8,6),('OnTrac','Standard',3.1,6),
 ('UPS','Expedited',1.9,3),('FedEx','Expedited',2.0,3),('UPS','Next Day',0.9,2),('FedEx','Next Day',0.9,2);

SELECT 'reference data ready' AS STATUS,
       (SELECT COUNT(*) FROM DIM_PRODUCT) AS PRODUCTS, (SELECT COUNT(*) FROM DIM_STORE) AS STORES,
       (SELECT COUNT(*) FROM DIM_CUSTOMER) AS CUSTOMERS, (SELECT COUNT(*) FROM DIM_DATE) AS DAYS;
-- =====================================================================================
-- Harborline Outfitters (fictional) - Step 2: facts
--   ORDER_LINES      ~19M rows  (order line grain, Oct 2023 -> Dec 2026, revealed live by V_SALES)
--   INVENTORY_DAILY  ~7M rows   (SKU x regional DC x day)
--   PLAN_DAILY       ~18K rows  (region x category x day, phased from a monthly plan)
-- Behaviour: seasonality, weekday/hour patterns, holiday events & promotions, channel growth,
-- free-shipping threshold ($99 -> $119 from 1 Mar 2026), carrier transit & peak-season delays,
-- replenishment cycles with stockouts and lost sales, returns by category/channel.
-- Planted stories (for the AI to find):
--   * West-region footwear stockouts Aug-Oct 2026 (low replenishment) -> lost sales, low in-stock
--   * Southeast USPS standard deliveries slow down from Aug 2026 -> on-time % drops
--   * Southwest demand softens through 2026 against an aggressive plan -> plan miss
--   * Free-shipping threshold raised from $99 to $119 in Mar 2026 -> free-ship % down, AOV up
-- =====================================================================================
USE ROLE WBR_OWNER;
USE WAREHOUSE POWERHOUSE;
USE SCHEMA WBR_DB.RETAIL_DEMO;
SET START_DATE = '2023-10-01'::DATE;

-- ------------------------------------------------------------------ daily event factors
CREATE OR REPLACE TABLE WRK_DAY_FACTOR AS
SELECT d.DATE_KEY,
       IFF(MIN(COALESCE(e.STORE_MULT, 1)) = 0, 0, EXP(SUM(LN(NULLIF(COALESCE(e.STORE_MULT, 1), 0))))) AS STORE_EVENT,
       EXP(SUM(LN(COALESCE(e.ONLINE_MULT, 1)))) AS ONLINE_EVENT,
       BOOLOR_AGG(COALESCE(e.FREE_SHIP, FALSE)) AS FREE_SHIP_DAY
FROM DIM_DATE d
LEFT JOIN REF_EVENT e ON d.DATE_KEY BETWEEN e.START_DATE AND e.END_DATE AND e.SCOPE = 'ALL'
   OR (d.DATE_KEY BETWEEN e.START_DATE AND e.END_DATE AND e.EVENT_NAME IN ('Winter clearance', 'Back to school'))
GROUP BY d.DATE_KEY;

-- promotional discount per day x subcategory (largest applicable event discount)
CREATE OR REPLACE TABLE WRK_PROMO AS
SELECT d.DATE_KEY, s.SUBCATEGORY_ID,
       MAX(e.DISCOUNT) AS PROMO_DISCOUNT,
       MAX_BY(e.EVENT_NAME, e.DISCOUNT) AS PROMO_NAME
FROM DIM_DATE d
JOIN REF_EVENT e ON d.DATE_KEY BETWEEN e.START_DATE AND e.END_DATE AND e.DISCOUNT > 0
JOIN REF_SUBCATEGORY s ON e.SCOPE = 'ALL' OR ARRAY_CONTAINS(s.SUBCATEGORY::VARIANT, SPLIT(e.SCOPE, '|'))
GROUP BY 1, 2;

-- ------------------------------------------------------------------ expected orders: day x region x channel
CREATE OR REPLACE TABLE WRK_DEMAND AS
WITH ch AS (
  SELECT column1 AS CHANNEL, column2 AS SHARE0, column3 AS GROWTH, column4 AS IS_ONLINE FROM VALUES
  ('Store', 0.55, 0.01, FALSE), ('Web', 0.26, 0.06, TRUE), ('App', 0.12, 0.22, TRUE), ('Marketplace', 0.07, 0.10, TRUE)
), mf AS (
  SELECT column1 AS M, column2 AS F FROM VALUES
  (1,.80),(2,.78),(3,.92),(4,.96),(5,1.0),(6,.97),(7,.95),(8,1.02),(9,.92),(10,.97),(11,1.05),(12,1.10)
), base AS (
  SELECT d.DATE_KEY, d.MONTH_NUM, d.DOW_ISO, r.REGION_ID, r.DEMAND_SHARE, ch.*,
         DATEDIFF(day, $START_DATE, d.DATE_KEY) / 365.0 AS YRS,
         f.STORE_EVENT, f.ONLINE_EVENT, mf.F AS MONTH_F
  FROM DIM_DATE d
  CROSS JOIN DIM_REGION r CROSS JOIN ch
  JOIN WRK_DAY_FACTOR f ON f.DATE_KEY = d.DATE_KEY
  JOIN mf ON mf.M = d.MONTH_NUM
)
SELECT DATE_KEY, REGION_ID, CHANNEL, IS_ONLINE,
  7200 * DEMAND_SHARE * SHARE0 * POWER(1 + GROWTH, YRS) * MONTH_F
  * IFF(IS_ONLINE, DECODE(DOW_ISO, 1, 1.08, 2, 1.03, 3, 1.00, 4, .98, 5, .92, 6, .95, 1.06),
                   DECODE(DOW_ISO, 1, .82, 2, .84, 3, .88, 4, .95, 5, 1.12, 6, 1.40, 1.15))
  * IFF(IS_ONLINE, ONLINE_EVENT, STORE_EVENT)
  -- regional stories: Southwest softens through 2026, West keeps outgrowing
  * CASE WHEN REGION_ID = 4 AND DATE_KEY >= '2026-01-01' THEN 0.95 - 0.08 * LEAST(1, DATEDIFF(day, '2026-01-01', DATE_KEY) / 270.0)
         WHEN REGION_ID = 5 AND DATE_KEY >= '2025-06-01' THEN 1.04 ELSE 1 END AS EXPECTED_ORDERS
FROM base;

CREATE OR REPLACE TABLE WRK_DEMAND_N AS
SELECT w.*, GREATEST(0, ROUND(EXPECTED_ORDERS * EXP(NORMAL(0, 0.07, RANDOM()))))::INT AS ORDERS_COUNT
FROM WRK_DEMAND w;

-- ------------------------------------------------------------------ orders
CREATE OR REPLACE TABLE WRK_ORDERS AS
WITH n AS (SELECT SEQ4() AS K FROM TABLE(GENERATOR(ROWCOUNT => 12000))),
o AS (
  SELECT w.DATE_KEY, w.REGION_ID, w.CHANNEL, w.IS_ONLINE, n.K,
         UNIFORM(0::FLOAT, 1::FLOAT, RANDOM()) AS U1, UNIFORM(0::FLOAT, 1::FLOAT, RANDOM()) AS U2,
         UNIFORM(0::FLOAT, 1::FLOAT, RANDOM()) AS U3, UNIFORM(0::FLOAT, 1::FLOAT, RANDOM()) AS U4,
         UNIFORM(0::FLOAT, 1::FLOAT, RANDOM()) AS U5, UNIFORM(0::FLOAT, 1::FLOAT, RANDOM()) AS U6,
         UNIFORM(0::FLOAT, 1::FLOAT, RANDOM()) AS U7, NORMAL(0, 1, RANDOM()) AS Z1
  FROM WRK_DEMAND_N w JOIN n ON n.K < w.ORDERS_COUNT
), cust_n AS (SELECT REGION_ID, COUNT(*) AS N FROM DIM_CUSTOMER GROUP BY 1),
t AS (
  SELECT o.*,
    DATEADD(second,
      IFF(IS_ONLINE, MOD(72000 + ROUND(Z1 * 14400)::INT + 172800, 86400),
                     36000 + ROUND((U1 + U2) / 2 * 39600)::INT),
      DATE_KEY::TIMESTAMP_NTZ) AS ORDER_TS,
    IFF(CHANNEL = 'Store', 1 + FLOOR(U3 * 12), NULL) AS STORE_IDX,
    IFF(CHANNEL = 'Store' AND U4 < 0.45, NULL, 1 + FLOOR(U5 * c.N)) AS CUST_IDX
  FROM o JOIN cust_n c ON c.REGION_ID = o.REGION_ID
)
SELECT ROW_NUMBER() OVER (ORDER BY t.ORDER_TS, t.REGION_ID, t.CHANNEL, t.K) AS ORDER_NUM,
       t.DATE_KEY AS ORDER_DATE, t.ORDER_TS, t.REGION_ID, t.CHANNEL, t.IS_ONLINE,
       s.STORE_ID, cu.CUSTOMER_ID, COALESCE(cu.LOYALTY_TIER, 'Guest') AS LOYALTY_TIER,
       COALESCE(cu.AGE_BAND, 'Unknown') AS AGE_BAND, COALESCE(cu.STATE_CODE, s.STORE_STATE) AS CUSTOMER_STATE,
       CASE WHEN t.U6 < .52 THEN 1 WHEN t.U6 < .79 THEN 2 WHEN t.U6 < .91 THEN 3 WHEN t.U6 < .97 THEN 4 ELSE 5 END AS LINE_COUNT,
       IFF(t.IS_ONLINE, CASE WHEN t.U7 < .78 THEN 'Standard' WHEN t.U7 < .94 THEN 'Expedited' ELSE 'Next Day' END, NULL) AS SHIP_METHOD,
       t.U1 AS U_CARRIER, t.U4 AS U_FEE
FROM t
LEFT JOIN DIM_STORE s ON s.REGION_ID = t.REGION_ID AND s.REGION_STORE_IDX = t.STORE_IDX
LEFT JOIN DIM_CUSTOMER cu ON cu.REGION_ID = t.REGION_ID AND cu.REGION_CUST_IDX = t.CUST_IDX;

-- ------------------------------------------------------------------ product mix
-- subcategory mix by month x region (seasonality and climate), then SKU by popularity
CREATE OR REPLACE TABLE WRK_SUBCAT_CUM AS
WITH m AS (SELECT SEQ4() + 1 AS MONTH_NUM FROM TABLE(GENERATOR(ROWCOUNT => 12))),
w AS (
  SELECT m.MONTH_NUM, r.REGION_ID, s.SUBCATEGORY_ID,
         s.DEMAND_SHARE * (1 + s.SEASON_AMP * COS(2 * PI() * (m.MONTH_NUM - s.PEAK_MONTH) / 12))
         * DECODE(r.CLIMATE, 'north', s.NORTH_F, 'south', s.SOUTH_F, s.WEST_F) AS W
  FROM m CROSS JOIN DIM_REGION r CROSS JOIN REF_SUBCATEGORY s
)
SELECT MONTH_NUM, REGION_ID, SUBCATEGORY_ID,
       (SUM(W) OVER (PARTITION BY MONTH_NUM, REGION_ID ORDER BY SUBCATEGORY_ID) - W)
       / SUM(W) OVER (PARTITION BY MONTH_NUM, REGION_ID) AS LO
FROM w;

CREATE OR REPLACE TABLE WRK_PRODUCT_CUM AS
SELECT SUBCATEGORY_ID, SKU,
       (SUM(POPULARITY) OVER (PARTITION BY SUBCATEGORY_ID ORDER BY SKU) - POPULARITY)
       / SUM(POPULARITY) OVER (PARTITION BY SUBCATEGORY_ID) AS LO
FROM DIM_PRODUCT;

CREATE OR REPLACE TABLE WRK_LINES_A AS
WITH k AS (SELECT SEQ4() + 1 AS LINE_NUMBER FROM TABLE(GENERATOR(ROWCOUNT => 5))),
l AS (
  SELECT o.*, k.LINE_NUMBER, MONTH(o.ORDER_DATE) AS MONTH_NUM,
         UNIFORM(0::FLOAT, 1::FLOAT, RANDOM()) AS U_SUB
  FROM WRK_ORDERS o JOIN k ON k.LINE_NUMBER <= o.LINE_COUNT
)
SELECT l.*, sc.SUBCATEGORY_ID, UNIFORM(0::FLOAT, 1::FLOAT, RANDOM()) AS U_PROD
FROM l ASOF JOIN WRK_SUBCAT_CUM sc
  MATCH_CONDITION (l.U_SUB >= sc.LO)
  ON l.MONTH_NUM = sc.MONTH_NUM AND l.REGION_ID = sc.REGION_ID;

CREATE OR REPLACE TABLE WRK_LINES AS
WITH p AS (
  SELECT a.*, pc.SKU
  FROM WRK_LINES_A a ASOF JOIN WRK_PRODUCT_CUM pc
    MATCH_CONDITION (a.U_PROD >= pc.LO)
    ON a.SUBCATEGORY_ID = pc.SUBCATEGORY_ID
), q AS (
  SELECT p.*, pr.CATEGORY_ID, pr.LIST_PRICE, pr.UNIT_COST,
         UNIFORM(0::FLOAT, 1::FLOAT, RANDOM()) AS U_QTY, UNIFORM(0::FLOAT, 1::FLOAT, RANDOM()) AS U_DISC,
         UNIFORM(0::FLOAT, 1::FLOAT, RANDOM()) AS U_RET, UNIFORM(0::FLOAT, 1::FLOAT, RANDOM()) AS U_RET2,
         pm.PROMO_DISCOUNT, pm.PROMO_NAME
  FROM p JOIN DIM_PRODUCT pr ON pr.SKU = p.SKU
  LEFT JOIN WRK_PROMO pm ON pm.DATE_KEY = p.ORDER_DATE AND pm.SUBCATEGORY_ID = p.SUBCATEGORY_ID
), d AS (
  SELECT q.*,
    IFF(SUBCATEGORY_ID = 10, 1 + FLOOR(U_QTY * 3), CASE WHEN U_QTY < .86 THEN 1 WHEN U_QTY < .97 THEN 2 ELSE 3 END) AS QTY,
    LEAST(0.60,
      COALESCE(PROMO_DISCOUNT, IFF(U_DISC < 0.08, 0.10 + U_DISC * 1.25, 0))              -- event promo, else 8% markdowns
      + IFF(LOYALTY_TIER = 'Platinum' AND U_DISC > 0.70, 0.05, 0)                          -- member coupon
      + IFF(CHANNEL = 'Marketplace', 0.03, 0)) AS DISCOUNT_PCT,                            -- marketplace price match
    COALESCE(PROMO_NAME, IFF(U_DISC < 0.08, 'Markdown', NULL)) AS PROMO
  FROM q
)
SELECT ORDER_NUM, LINE_NUMBER, ORDER_DATE, ORDER_TS, REGION_ID, CHANNEL, IS_ONLINE, STORE_ID, CUSTOMER_ID, LOYALTY_TIER,
       AGE_BAND, CUSTOMER_STATE, SHIP_METHOD, U_CARRIER, U_FEE, SKU, CATEGORY_ID, SUBCATEGORY_ID, QTY, LIST_PRICE,
       DISCOUNT_PCT, PROMO, UNIT_COST, U_RET, U_RET2,
       ROUND(QTY * LIST_PRICE, 2) AS GROSS_SALES,
       ROUND(QTY * LIST_PRICE * DISCOUNT_PCT, 2) AS DISCOUNT_AMOUNT,
       ROUND(QTY * LIST_PRICE, 2) - ROUND(QTY * LIST_PRICE * DISCOUNT_PCT, 2) AS NET_SALES,
       ROUND(QTY * UNIT_COST, 2) AS COGS
FROM d;

-- ------------------------------------------------------------------ inventory (replenish-up-to cycles) & lost sales
CREATE OR REPLACE TABLE WRK_DEMAND_DAY AS
SELECT ORDER_DATE AS DATE_KEY, SKU, REGION_ID, SUM(QTY) AS DEMAND_UNITS
FROM WRK_LINES GROUP BY 1, 2, 3;

CREATE OR REPLACE TABLE WRK_INV AS
WITH sc AS (
  SELECT d.DATE_KEY, p.SKU, p.CATEGORY_ID, p.SUBCATEGORY_ID, p.UNIT_COST, r.REGION_ID,
         DATEDIFF(day, $START_DATE, d.DATE_KEY) + MOD(ABS(HASH(p.SKU, r.REGION_ID)), 14) AS SHIFTED_IDX
  FROM DIM_DATE d CROSS JOIN DIM_PRODUCT p CROSS JOIN DIM_REGION r
), c AS (
  SELECT sc.*, FLOOR(SHIFTED_IDX / 14) AS CYCLE_ID, MOD(SHIFTED_IDX, 14) AS DAY_IN_CYCLE,
         COALESCE(dd.DEMAND_UNITS, 0) AS DEMAND_UNITS
  FROM sc LEFT JOIN WRK_DEMAND_DAY dd
    ON dd.DATE_KEY = sc.DATE_KEY AND dd.SKU = sc.SKU AND dd.REGION_ID = sc.REGION_ID
), cyc AS (
  SELECT c.*,
    SUM(DEMAND_UNITS) OVER (PARTITION BY SKU, REGION_ID, CYCLE_ID) AS CYCLE_DEMAND,
    COALESCE(SUM(DEMAND_UNITS) OVER (PARTITION BY SKU, REGION_ID, CYCLE_ID ORDER BY DATE_KEY
                                     ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING), 0) AS CUM_BEFORE,
    MIN(DATE_KEY) OVER (PARTITION BY SKU, REGION_ID, CYCLE_ID) AS CYCLE_START,
    MOD(ABS(HASH(SKU, REGION_ID, CYCLE_ID)), 1000000) / 1e6 AS UC
  FROM c
), s AS (
  SELECT cyc.*,
    -- days of cover the replenishment brings the DC up to
    CASE WHEN REGION_ID = 5 AND CATEGORY_ID = 2 AND CYCLE_START BETWEEN '2026-07-25' AND '2026-10-20'
              THEN 5 + UC * 7                                   -- planted: West footwear under-replenished
         WHEN UC < 0.12 THEN 6 + UC * 50                        -- ~12% of cycles run short (6-12 days)
         ELSE 35 + UC * 45 END AS COVER_DAYS                    -- healthy: 5-11 weeks of cover
  FROM cyc
), st AS (
  SELECT s.*, CEIL(GREATEST(CYCLE_DEMAND, 1) / 14.0 * COVER_DAYS) + 2 AS ORDER_UP_TO
  FROM s
)
SELECT DATE_KEY, SKU, REGION_ID, CATEGORY_ID, SUBCATEGORY_ID, UNIT_COST, DAY_IN_CYCLE, DEMAND_UNITS,
       GREATEST(0, ORDER_UP_TO - CUM_BEFORE) AS ON_HAND_START,
       GREATEST(0, ORDER_UP_TO - CUM_BEFORE - DEMAND_UNITS) AS ON_HAND_END,
       ORDER_UP_TO
FROM st;

-- lines that could not be fulfilled because the DC ran out are lost sales (not recorded as sales)
CREATE OR REPLACE TABLE WRK_LINES_OK AS
SELECT l.*
FROM WRK_LINES l
JOIN WRK_INV i ON i.DATE_KEY = l.ORDER_DATE AND i.SKU = l.SKU AND i.REGION_ID = l.REGION_ID
QUALIFY SUM(l.QTY) OVER (PARTITION BY l.ORDER_DATE, l.SKU, l.REGION_ID ORDER BY l.ORDER_TS, l.ORDER_NUM, l.LINE_NUMBER
                         ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) <= i.ON_HAND_START;

-- ------------------------------------------------------------------ ORDER_LINES (final)
CREATE OR REPLACE TABLE ORDER_LINES AS
WITH ord AS (
  SELECT ORDER_NUM, SUM(NET_SALES) AS SUBTOTAL, COUNT(*) AS N_LINES FROM WRK_LINES_OK GROUP BY 1
), bf AS (
  SELECT YEAR(START_DATE) AS Y, MIN(START_DATE) AS BF_DATE FROM REF_EVENT WHERE EVENT_NAME = 'Black Friday' GROUP BY 1
), f AS (
  SELECT l.*, o.SUBTOTAL, df.FREE_SHIP_DAY, r.BASE_CLICK_TO_SHIP_HOURS, d.DOW_ISO, bf.BF_DATE,
         IFF(l.ORDER_DATE >= '2026-03-01', 119, 99) AS FREE_SHIP_THRESHOLD,
         CASE WHEN NOT l.IS_ONLINE THEN NULL
              WHEN l.SHIP_METHOD = 'Standard' THEN
                   CASE WHEN l.REGION_ID = 5 AND l.U_CARRIER < .35 THEN 'USPS' WHEN l.REGION_ID = 5 AND l.U_CARRIER < .65 THEN 'UPS'
                        WHEN l.REGION_ID = 5 AND l.U_CARRIER < .85 THEN 'FedEx' WHEN l.REGION_ID = 5 THEN 'OnTrac'
                        WHEN l.U_CARRIER < .38 THEN 'USPS' WHEN l.U_CARRIER < .78 THEN 'UPS' ELSE 'FedEx' END
              ELSE IFF(l.U_CARRIER < .55, 'UPS', 'FedEx') END AS CARRIER,
         -- one fulfilment draw per order (all lines ship together)
         MOD(ABS(HASH(l.ORDER_NUM, 'c2s')), 1000000) / 1e6 AS U_C2S,
         MOD(ABS(HASH(l.ORDER_NUM, 'tr')), 1000000) / 1e6 AS U_TR,
         MOD(ABS(HASH(l.ORDER_NUM, 'tr2')), 1000000) / 1e6 AS U_TR2
  FROM WRK_LINES_OK l
  JOIN ord o ON o.ORDER_NUM = l.ORDER_NUM
  JOIN WRK_DAY_FACTOR df ON df.DATE_KEY = l.ORDER_DATE
  JOIN DIM_REGION r ON r.REGION_ID = l.REGION_ID
  JOIN DIM_DATE d ON d.DATE_KEY = l.ORDER_DATE
  LEFT JOIN bf ON bf.Y = YEAR(l.ORDER_DATE)
), fee AS (
  SELECT f.*, c.BASE_TRANSIT_DAYS, c.SLA_DAYS,
    CASE WHEN NOT IS_ONLINE THEN NULL
         WHEN CHANNEL = 'Marketplace' THEN IFF(U_FEE < 0.80, 0, 5.99)
         WHEN f.SHIP_METHOD = 'Standard' THEN IFF(SUBTOTAL >= FREE_SHIP_THRESHOLD OR LOYALTY_TIER IN ('Gold', 'Platinum') OR FREE_SHIP_DAY, 0, 6.95)
         WHEN f.SHIP_METHOD = 'Expedited' THEN IFF(LOYALTY_TIER = 'Platinum', 0, 14.95)
         ELSE 24.95 END AS ORDER_SHIPPING_FEE,
    -- hours from order to carrier hand-off (lognormal around the DC's norm; peak & weekend slower)
    BASE_CLICK_TO_SHIP_HOURS
      * DECODE(f.SHIP_METHOD, 'Standard', 1.0, 'Expedited', 0.6, 0.35)
      * CASE WHEN ORDER_DATE BETWEEN DATEADD(day, -1, BF_DATE) AND DATEADD(day, 4, BF_DATE) THEN 2.0
             WHEN MONTH(ORDER_DATE) = 12 AND DAY(ORDER_DATE) <= 22 THEN 1.55 ELSE 1.0 END
      * IFF(DOW_ISO >= 6, 1.35, 1.0)
      * EXP(0.35 * SQRT(-2 * LN(GREATEST(U_C2S, 1e-6))) * COS(2 * PI() * U_TR2)) AS C2S_HOURS,
    GREATEST(IFF(f.SHIP_METHOD = 'Next Day', 0.6, 0.9),
      c.BASE_TRANSIT_DAYS
      + IFF(f.SHIP_METHOD = 'Standard', 0.9, 0.25) * SQRT(-2 * LN(GREATEST(U_TR, 1e-6))) * SIN(2 * PI() * U_TR2)
      + IFF(f.SHIP_METHOD = 'Standard' AND MONTH(ORDER_DATE) = 12 AND DAY(ORDER_DATE) BETWEEN 8 AND 24, 1.1, 0)
      -- planted: Southeast USPS network slowdown from Aug 2026
      + IFF(REGION_ID = 2 AND f.CARRIER = 'USPS' AND ORDER_DATE >= '2026-08-01', 1.6, 0)) AS TRANSIT_D
  FROM f LEFT JOIN REF_CARRIER c ON c.CARRIER = f.CARRIER AND c.SHIP_METHOD = f.SHIP_METHOD
), t AS (
  SELECT fee.*,
    IFF(IS_ONLINE, DATEADD(minute, ROUND(C2S_HOURS * 60)::INT, ORDER_TS), NULL) AS SHIP_TS,
    IFF(IS_ONLINE, DATEADD(minute, ROUND((C2S_HOURS + TRANSIT_D * 24) * 60)::INT, ORDER_TS), NULL) AS DELIVERED_TS,
    IFF(IS_ONLINE, DATEADD(day, SLA_DAYS, ORDER_DATE), NULL) AS PROMISED_DATE,
    -- returns: category x channel propensity; Marketplace slightly higher
    U_RET < IFF(IS_ONLINE, sc.RETURN_ONLINE * IFF(CHANNEL = 'Marketplace', 1.2, 1.0), sc.RETURN_STORE) AS RETURN_FLAG
  FROM fee JOIN REF_SUBCATEGORY sc ON sc.SUBCATEGORY_ID = fee.SUBCATEGORY_ID
)
SELECT
  'HL-' || LPAD(TO_VARCHAR(ORDER_NUM), 9, '0') || '-' || LINE_NUMBER AS LINE_ID,
  'HL-' || LPAD(TO_VARCHAR(ORDER_NUM), 9, '0') AS ORDER_ID,
  LINE_NUMBER, ORDER_DATE, ORDER_TS, REGION_ID, CATEGORY_ID, SUBCATEGORY_ID, SKU, CHANNEL, IS_ONLINE, STORE_ID,
  CUSTOMER_ID, LOYALTY_TIER, AGE_BAND, CUSTOMER_STATE, PROMO AS PROMO_NAME,
  QTY, LIST_PRICE, ROUND(DISCOUNT_PCT, 4) AS DISCOUNT_PCT, GROSS_SALES, DISCOUNT_AMOUNT, NET_SALES, COGS,
  IS_ONLINE AS IS_SHIPPED_ORDER, SHIP_METHOD, CARRIER, FREE_SHIP_THRESHOLD, ORDER_SHIPPING_FEE,
  ROUND(ORDER_SHIPPING_FEE * NET_SALES / NULLIF(SUBTOTAL, 0), 2) AS LINE_SHIPPING_FEE,
  IFF(IS_ONLINE, ORDER_SHIPPING_FEE = 0, NULL) AS FREE_SHIPPING_FLAG,
  SHIP_TS, DELIVERED_TS, PROMISED_DATE,
  ROUND(DATEDIFF(minute, ORDER_TS, SHIP_TS) / 60.0, 1) AS CLICK_TO_SHIP_HOURS,
  ROUND(DATEDIFF(minute, SHIP_TS, DELIVERED_TS) / 1440.0, 2) AS TRANSIT_DAYS,
  ROUND(DATEDIFF(minute, ORDER_TS, DELIVERED_TS) / 1440.0, 2) AS DELIVERY_DAYS,
  IFF(IS_ONLINE, DELIVERED_TS::DATE <= PROMISED_DATE, NULL) AS ON_TIME_FLAG,
  RETURN_FLAG,
  IFF(RETURN_FLAG, DATEADD(hour, ROUND((3 + U_RET2 * 25) * 24)::INT, COALESCE(DELIVERED_TS, ORDER_TS)), NULL) AS RETURN_TS,
  IFF(RETURN_FLAG,
      CASE WHEN CATEGORY_ID = 2 AND U_RET2 < .58 THEN 'Size or fit'
           WHEN CATEGORY_ID = 1 AND U_RET2 < .45 THEN 'Size or fit'
           WHEN U_RET2 < .70 THEN 'Changed mind'
           WHEN U_RET2 < .85 THEN 'Not as described'
           ELSE 'Damaged or defective' END, NULL) AS RETURN_REASON
FROM t
ORDER BY ORDER_DATE, REGION_ID;

-- ------------------------------------------------------------------ INVENTORY_DAILY (final)
CREATE OR REPLACE TABLE INVENTORY_DAILY AS
WITH sold AS (
  SELECT ORDER_DATE AS DATE_KEY, SKU, REGION_ID, SUM(QTY) AS UNITS_SOLD FROM ORDER_LINES GROUP BY 1, 2, 3
)
SELECT i.DATE_KEY AS SNAPSHOT_DATE, i.SKU, i.REGION_ID, i.CATEGORY_ID, i.SUBCATEGORY_ID, i.UNIT_COST,
       i.ON_HAND_START AS UNITS_ON_HAND_START,
       i.ON_HAND_END AS UNITS_ON_HAND,
       IFF(i.DAY_IN_CYCLE >= 9, GREATEST(0, i.ORDER_UP_TO - i.ON_HAND_END), 0) AS UNITS_ON_ORDER,
       COALESCE(s.UNITS_SOLD, 0) AS UNITS_SOLD,
       i.DEMAND_UNITS,
       GREATEST(0, i.DEMAND_UNITS - COALESCE(s.UNITS_SOLD, 0)) AS LOST_UNITS,
       ROUND(i.ON_HAND_END * i.UNIT_COST, 2) AS INVENTORY_VALUE,
       i.ON_HAND_END = 0 AS STOCKOUT_FLAG
FROM WRK_INV i
LEFT JOIN sold s ON s.DATE_KEY = i.DATE_KEY AND s.SKU = i.SKU AND s.REGION_ID = i.REGION_ID
ORDER BY SNAPSHOT_DATE, REGION_ID;

-- ------------------------------------------------------------------ PLAN_DAILY (monthly plan phased to days)
CREATE OR REPLACE TABLE PLAN_DAILY AS
WITH act AS (
  SELECT DATE_TRUNC('month', ORDER_DATE) AS MONTH_START, REGION_ID, CATEGORY_ID,
         SUM(NET_SALES) AS NET_SALES, SUM(QTY) AS UNITS, SUM(NET_SALES - COGS) AS MARGIN
  FROM ORDER_LINES GROUP BY 1, 2, 3
), plan_m AS (
  SELECT a.MONTH_START, a.REGION_ID, a.CATEGORY_ID,
         -- plan = last year's actual x growth target (Southwest set aggressively); first year: actual +/- a few %
         IFF(py.NET_SALES IS NULL, 0.97 + 0.07 * MOD(ABS(HASH(a.MONTH_START, a.REGION_ID, a.CATEGORY_ID)), 1000) / 1000,
             DECODE(a.REGION_ID, 1, 1.06, 2, 1.07, 3, 1.05, 4, 1.10, 1.08)
             * (0.98 + 0.04 * MOD(ABS(HASH(a.MONTH_START, a.REGION_ID, a.CATEGORY_ID)), 1000) / 1000)) AS F,
         COALESCE(py.NET_SALES, a.NET_SALES) AS NS_BASE, COALESCE(py.UNITS, a.UNITS) AS U_BASE,
         COALESCE(py.MARGIN, a.MARGIN) AS M_BASE
  FROM act a
  LEFT JOIN act py ON py.MONTH_START = DATEADD(year, -1, a.MONTH_START)
                  AND py.REGION_ID = a.REGION_ID AND py.CATEGORY_ID = a.CATEGORY_ID
), phase AS (
  SELECT DATE_KEY, REGION_ID, SUM(EXPECTED_ORDERS) AS W,
         SUM(SUM(EXPECTED_ORDERS)) OVER (PARTITION BY REGION_ID, DATE_TRUNC('month', DATE_KEY)) AS W_MONTH
  FROM WRK_DEMAND GROUP BY 1, 2
)
SELECT ph.DATE_KEY, p.REGION_ID, p.CATEGORY_ID,
       ROUND(p.NS_BASE * p.F * ph.W / ph.W_MONTH, 2) AS PLAN_NET_SALES,
       ROUND(p.U_BASE * p.F * ph.W / ph.W_MONTH, 1) AS PLAN_UNITS,
       ROUND(p.M_BASE * p.F * ph.W / ph.W_MONTH, 2) AS PLAN_GROSS_MARGIN
FROM plan_m p
JOIN phase ph ON ph.REGION_ID = p.REGION_ID AND DATE_TRUNC('month', ph.DATE_KEY) = p.MONTH_START;

-- ------------------------------------------------------------------ tidy up work tables
DROP TABLE IF EXISTS WRK_LINES_A;
DROP TABLE IF EXISTS WRK_LINES;
DROP TABLE IF EXISTS WRK_LINES_OK;
DROP TABLE IF EXISTS WRK_ORDERS;
DROP TABLE IF EXISTS WRK_INV;
DROP TABLE IF EXISTS WRK_DEMAND_DAY;

SELECT 'facts ready' AS STATUS,
       (SELECT COUNT(*) FROM ORDER_LINES) AS ORDER_LINES,
       (SELECT COUNT(DISTINCT ORDER_ID) FROM ORDER_LINES) AS ORDERS,
       (SELECT COUNT(*) FROM INVENTORY_DAILY) AS INVENTORY_ROWS,
       (SELECT COUNT(*) FROM PLAN_DAILY) AS PLAN_ROWS;
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

-- The semantic view is created from the richest definition this account supports:
-- 1) with semi-additive ending stock + cross-table plan metrics + Cortex Analyst instructions,
-- 2) without the semi-additive metric, 3) core metrics only. The result says which one won.
CREATE OR REPLACE TABLE SV_DDL (ATTEMPT NUMBER, NAME VARCHAR, DDL VARCHAR);

INSERT INTO SV_DDL VALUES (1, 'full: ending stock + plan attainment + AI instructions', $$CREATE OR REPLACE SEMANTIC VIEW WBR_DB.RETAIL_DEMO.RETAIL_ANALYTICS_SV
  TABLES (
    dates AS WBR_DB.RETAIL_DEMO.DIM_DATE PRIMARY KEY (DATE_KEY)
      WITH SYNONYMS ('calendar', 'day') COMMENT = 'Calendar day. Weeks start Monday; fiscal year equals calendar year.',
    regions AS WBR_DB.RETAIL_DEMO.DIM_REGION PRIMARY KEY (REGION_ID)
      WITH SYNONYMS ('territory', 'market') COMMENT = 'Five US sales regions, each served by one distribution center.',
    categories AS WBR_DB.RETAIL_DEMO.DIM_CATEGORY PRIMARY KEY (CATEGORY_ID)
      WITH SYNONYMS ('department', 'merchandise category') COMMENT = 'Apparel, Footwear, Accessories.',
    products AS WBR_DB.RETAIL_DEMO.DIM_PRODUCT PRIMARY KEY (SKU)
      WITH SYNONYMS ('items', 'SKUs', 'styles') COMMENT = 'Product master at SKU level (fictional house brands).',
    stores AS WBR_DB.RETAIL_DEMO.DIM_STORE PRIMARY KEY (STORE_ID)
      WITH SYNONYMS ('shops', 'doors') COMMENT = 'Physical stores (60).',
    sales AS WBR_DB.RETAIL_DEMO.V_SALES PRIMARY KEY (LINE_ID)
      WITH SYNONYMS ('orders', 'transactions', 'order lines')
      COMMENT = 'Live order lines across Store, Web, App and Marketplace. Rows appear as orders are placed; shipment, delivery and return fields update as those events happen.',
    inventory AS WBR_DB.RETAIL_DEMO.V_INVENTORY PRIMARY KEY (SNAPSHOT_DATE, SKU, REGION_ID)
      WITH SYNONYMS ('stock', 'on hand')
      COMMENT = 'End-of-day inventory per SKU per regional distribution center. Today reflects stock as of now.',
    plan AS WBR_DB.RETAIL_DEMO.PLAN_DAILY PRIMARY KEY (DATE_KEY, REGION_ID, CATEGORY_ID)
      WITH SYNONYMS ('target', 'budget', 'forecast plan')
      COMMENT = 'Approved financial plan by day, region and category (monthly plan phased to days).'
  )
  RELATIONSHIPS (
    sales_to_dates AS sales (ORDER_DATE) REFERENCES dates,
    sales_to_regions AS sales (REGION_ID) REFERENCES regions,
    sales_to_categories AS sales (CATEGORY_ID) REFERENCES categories,
    sales_to_products AS sales (SKU) REFERENCES products,
    sales_to_stores AS sales (STORE_ID) REFERENCES stores,
    inventory_to_dates AS inventory (SNAPSHOT_DATE) REFERENCES dates,
    inventory_to_regions AS inventory (REGION_ID) REFERENCES regions,
    inventory_to_categories AS inventory (CATEGORY_ID) REFERENCES categories,
    inventory_to_products AS inventory (SKU) REFERENCES products,
    plan_to_dates AS plan (DATE_KEY) REFERENCES dates,
    plan_to_regions AS plan (REGION_ID) REFERENCES regions,
    plan_to_categories AS plan (CATEGORY_ID) REFERENCES categories
  )
  DIMENSIONS (
    dates.calendar_date AS DATE_KEY WITH SYNONYMS = ('date', 'order date', 'day')
      COMMENT = 'Calendar day: order date for sales, snapshot date for inventory, plan date for targets.',
    dates.week_start AS WEEK_START WITH SYNONYMS = ('week') COMMENT = 'Monday that starts the week.',
    dates.month_start AS MONTH_START WITH SYNONYMS = ('month') COMMENT = 'First day of the month.',
    dates.month_name AS MONTH_NAME COMMENT = 'Month label, e.g. Sep 2026.',
    dates.cal_quarter AS CAL_QUARTER WITH SYNONYMS = ('quarter') COMMENT = 'Calendar quarter, e.g. 2026-Q3.',
    dates.cal_year AS CAL_YEAR WITH SYNONYMS = ('year', 'fiscal year') COMMENT = 'Calendar (= fiscal) year.',
    dates.day_of_week AS DAY_OF_WEEK COMMENT = 'Day name (Mon-Sun).',
    dates.is_weekend AS IS_WEEKEND COMMENT = 'Saturday or Sunday.',
    dates.holiday AS COALESCE(HOLIDAY_NAME, 'No holiday') COMMENT = 'US retail holiday on this date, if any.',
    dates.retail_season AS RETAIL_SEASON COMMENT = 'Holiday, Winter clearance, Spring, Summer, Back to school & fall.',
    regions.region AS REGION_NAME WITH SYNONYMS = ('sales region', 'territory', 'area')
      COMMENT = 'US sales region (Northeast, Southeast, Midwest, Southwest, West). Online orders use the ship-to region.',
    regions.distribution_center AS DC_NAME WITH SYNONYMS = ('DC', 'warehouse', 'fulfillment center')
      COMMENT = 'Distribution center serving the region.',
    categories.category AS CATEGORY_NAME WITH SYNONYMS = ('product category', 'department')
      COMMENT = 'Merchandise category: Apparel, Footwear or Accessories.',
    products.subcategory AS SUBCATEGORY WITH SYNONYMS = ('product type', 'class') COMMENT = 'Merchandise subcategory, e.g. Running Shoes.',
    products.brand AS BRAND COMMENT = 'House brand.',
    products.product_name AS PRODUCT_NAME WITH SYNONYMS = ('product', 'style', 'item') COMMENT = 'Product (SKU) name.',
    products.sku_code AS SKU WITH SYNONYMS = ('SKU', 'item number') COMMENT = 'Stock keeping unit code.',
    products.gender AS GENDER COMMENT = 'Target customer: Women, Men, Kids, Unisex.',
    products.price_tier AS PRICE_TIER COMMENT = 'Value, Core or Premium price tier.',
    products.color_family AS COLOR_FAMILY COMMENT = 'Primary color family.',
    stores.store AS STORE_NAME WITH SYNONYMS = ('store name', 'location') COMMENT = 'Store name (store channel only).',
    stores.store_format AS STORE_FORMAT COMMENT = 'Flagship, Mall, Outlet or Street.',
    stores.store_state AS STORE_STATE COMMENT = 'State where the store is located.',
    sales.channel AS CHANNEL WITH SYNONYMS = ('sales channel') COMMENT = 'Store, Web, App or Marketplace.',
    sales.ship_method AS COALESCE(SHIP_METHOD, 'In-store') WITH SYNONYMS = ('shipping method', 'delivery speed')
      COMMENT = 'Standard, Expedited, Next Day; In-store for store purchases.',
    sales.carrier AS COALESCE(CARRIER, 'In-store') WITH SYNONYMS = ('shipping carrier') COMMENT = 'Parcel carrier for shipped orders.',
    sales.loyalty_tier AS LOYALTY_TIER WITH SYNONYMS = ('membership tier', 'customer tier')
      COMMENT = 'Guest, Member, Silver, Gold or Platinum at time of order.',
    sales.age_band AS AGE_BAND COMMENT = 'Customer age band (Unknown for guests).',
    sales.customer_state AS CUSTOMER_STATE WITH SYNONYMS = ('state', 'ship-to state') COMMENT = 'Ship-to state (store state for store purchases).',
    sales.fulfillment_status AS FULFILLMENT_STATUS COMMENT = 'Processing, In transit, Delivered, or In-store purchase - as of now.',
    sales.promotion AS COALESCE(PROMO_NAME, 'Full price') WITH SYNONYMS = ('promo', 'campaign', 'event')
      COMMENT = 'Promotion or markdown applied to the line; Full price when none.',
    sales.return_reason AS COALESCE(RETURN_REASON, 'Not returned') COMMENT = 'Reason given for the return.',
    sales.order_hour AS ORDER_HOUR COMMENT = 'Hour of day the order was placed (US Eastern).'
  )
  METRICS (
    sales.net_sales AS SUM(NET_SALES) WITH SYNONYMS = ('revenue', 'sales', 'net revenue')
      COMMENT = 'Net merchandise sales (USD): list price x units minus discounts. Excludes tax, shipping fees and returns.',
    sales.gross_sales AS SUM(GROSS_SALES) WITH SYNONYMS = ('gross revenue')
      COMMENT = 'Sales at list price before discounts (USD).',
    sales.discount_amount AS SUM(DISCOUNT_AMOUNT) WITH SYNONYMS = ('markdowns', 'promotional discount')
      COMMENT = 'Value of promotional discounts, markdowns and member coupons (USD).',
    sales.discount_rate AS SUM(DISCOUNT_AMOUNT) / NULLIF(SUM(GROSS_SALES), 0)
      COMMENT = 'Discount amount / gross sales.',
    sales.cost_of_goods_sold AS SUM(COGS) WITH SYNONYMS = ('COGS', 'product cost') COMMENT = 'Landed unit cost x units (USD).',
    sales.gross_margin AS SUM(NET_SALES - COGS) WITH SYNONYMS = ('gross profit', 'margin dollars')
      COMMENT = 'Net sales minus cost of goods sold (USD).',
    sales.gross_margin_pct AS SUM(NET_SALES - COGS) / NULLIF(SUM(NET_SALES), 0) WITH SYNONYMS = ('margin rate', 'GM%')
      COMMENT = 'Gross margin / net sales.',
    sales.units_sold AS SUM(QTY) WITH SYNONYMS = ('units', 'quantity sold') COMMENT = 'Units sold (fulfilled).',
    sales.order_count AS COUNT(DISTINCT ORDER_ID) WITH SYNONYMS = ('orders', 'transactions', 'number of orders')
      COMMENT = 'Distinct orders. With a product breakdown it counts orders containing that product.',
    sales.average_order_value AS SUM(NET_SALES) / NULLIF(COUNT(DISTINCT ORDER_ID), 0) WITH SYNONYMS = ('AOV', 'basket size')
      COMMENT = 'Net sales / orders.',
    sales.units_per_transaction AS SUM(QTY) / NULLIF(COUNT(DISTINCT ORDER_ID), 0) WITH SYNONYMS = ('UPT', 'units per order')
      COMMENT = 'Units / orders.',
    sales.active_customers AS COUNT(DISTINCT CUSTOMER_ID) WITH SYNONYMS = ('customers', 'buyers')
      COMMENT = 'Distinct identified customers who ordered (guests excluded).',
    sales.online_sales_share AS SUM(IFF(IS_ONLINE, NET_SALES, 0)) / NULLIF(SUM(NET_SALES), 0) WITH SYNONYMS = ('digital share', 'ecommerce penetration')
      COMMENT = 'Share of net sales from Web, App and Marketplace.',
    sales.shipped_orders AS COUNT(DISTINCT IFF(IS_SHIPPED_ORDER, ORDER_ID, NULL))
      COMMENT = 'Orders shipped to customers (Web, App, Marketplace).',
    sales.free_shipping_order_pct AS COUNT(DISTINCT IFF(FREE_SHIPPING_FLAG, ORDER_ID, NULL)) / NULLIF(COUNT(DISTINCT IFF(IS_SHIPPED_ORDER, ORDER_ID, NULL)), 0)
      WITH SYNONYMS = ('free shipping %', 'free shipping rate')
      COMMENT = 'Shipped orders with a 0 USD shipping fee / all shipped orders. Free when subtotal meets the threshold (99 USD, 119 USD from Mar 2026), for Gold and Platinum members, on free-shipping promotion days, or by marketplace policy.',
    sales.shipping_fee_revenue AS SUM(LINE_SHIPPING_FEE) COMMENT = 'Shipping fees charged to customers (USD).',
    sales.avg_click_to_ship_hours AS AVG(CLICK_TO_SHIP_HOURS) WITH SYNONYMS = ('fulfillment time', 'order to ship time', 'processing time')
      COMMENT = 'Average hours from order placed to carrier hand-off, over shipped order lines.',
    sales.avg_transit_days AS AVG(TRANSIT_DAYS) WITH SYNONYMS = ('carrier transit time')
      COMMENT = 'Average days from carrier hand-off to delivery, over delivered order lines.',
    sales.avg_delivery_days AS AVG(DELIVERY_DAYS) WITH SYNONYMS = ('shipping time', 'avg shipping time', 'delivery time', 'click to door')
      COMMENT = 'Average days from order placed to delivery, over delivered order lines.',
    sales.on_time_delivery_pct AS AVG(CASE WHEN ON_TIME_FLAG THEN 1 WHEN NOT ON_TIME_FLAG THEN 0 END)
      WITH SYNONYMS = ('OTD', 'on-time rate')
      COMMENT = 'Delivered lines that arrived on or before the promised date (Standard 6 days, Expedited 3, Next Day 2) / all delivered lines.',
    sales.returned_sales AS SUM(RETURNED_SALES) COMMENT = 'Net sales value of items returned so far (USD).',
    sales.returned_units AS SUM(RETURNED_UNITS) COMMENT = 'Units returned so far.',
    sales.return_rate AS SUM(RETURNED_SALES) / NULLIF(SUM(NET_SALES), 0) WITH SYNONYMS = ('returns %')
      COMMENT = 'Returned sales / net sales for orders placed in the period. Recent periods rise as returns arrive.',
    sales.net_sales_after_returns AS SUM(NET_SALES - RETURNED_SALES) COMMENT = 'Net sales less returns (USD).',
    inventory.avg_units_on_hand AS SUM(UNITS_ON_HAND) / NULLIF(COUNT(DISTINCT SNAPSHOT_DATE), 0)
      WITH SYNONYMS = ('units on hand', 'inventory units', 'stock on hand')
      COMMENT = 'Average daily end-of-day units on hand: stock is summed across the selected SKUs and DCs, then averaged over days (stock is never added up across days).',
    inventory.avg_inventory_value AS SUM(INVENTORY_VALUE) / NULLIF(COUNT(DISTINCT SNAPSHOT_DATE), 0)
      WITH SYNONYMS = ('inventory value', 'stock value') COMMENT = 'Average daily inventory value at cost (USD).',
    inventory.avg_units_on_order AS SUM(UNITS_ON_ORDER) / NULLIF(COUNT(DISTINCT SNAPSHOT_DATE), 0)
      WITH SYNONYMS = ('on order', 'open PO units') COMMENT = 'Average daily units on open replenishment orders.',
    inventory.units_sold_from_stock AS SUM(UNITS_SOLD) COMMENT = 'Units fulfilled from DC stock (equals units sold for the same slice).',
    inventory.lost_sales_units AS SUM(LOST_UNITS) WITH SYNONYMS = ('lost sales', 'unmet demand')
      COMMENT = 'Units customers wanted that could not be fulfilled because the DC was out of stock.',
    inventory.stockout_rate AS AVG(IFF(STOCKOUT_FLAG, 1, 0)) WITH SYNONYMS = ('out of stock %', 'OOS rate')
      COMMENT = 'Share of SKU x DC x day records ending with zero units on hand.',
    inventory.in_stock_rate AS 1 - AVG(IFF(STOCKOUT_FLAG, 1, 0)) WITH SYNONYMS = ('in-stock %', 'availability')
      COMMENT = 'Share of SKU x DC x day records ending with stock available.',
    inventory.weeks_of_supply AS SUM(UNITS_ON_HAND) / NULLIF(7 * SUM(UNITS_SOLD), 0) WITH SYNONYMS = ('WOS', 'weeks of cover')
      COMMENT = 'Average units on hand / average weekly units sold.',
    inventory.sell_through_pct AS SUM(UNITS_SOLD) / NULLIF(SUM(UNITS_SOLD) + SUM(UNITS_ON_HAND) / NULLIF(COUNT(DISTINCT SNAPSHOT_DATE), 0), 0)
      WITH SYNONYMS = ('sell-through', 'sell thru')
      COMMENT = 'Units sold / (units sold + average daily units on hand) for the period.',
    inventory.ending_units_on_hand NON ADDITIVE BY (dates.calendar_date) AS SUM(UNITS_ON_HAND)
      WITH SYNONYMS = ('closing stock', 'current units on hand')
      COMMENT = 'Units on hand on the last day of the period (semi-additive: summed across SKUs and DCs, never across days).',
    plan.plan_net_sales AS SUM(PLAN_NET_SALES) WITH SYNONYMS = ('sales plan', 'sales target', 'budget')
      COMMENT = 'Planned net sales (USD).',
    plan.plan_units AS SUM(PLAN_UNITS) WITH SYNONYMS = ('unit plan') COMMENT = 'Planned units.',
    plan.plan_gross_margin AS SUM(PLAN_GROSS_MARGIN) WITH SYNONYMS = ('margin plan') COMMENT = 'Planned gross margin (USD).',
    plan_attainment_pct AS sales.net_sales / NULLIF(plan.plan_net_sales, 0)
      WITH SYNONYMS = ('sales vs plan %', 'attainment', 'percent to plan')
      COMMENT = 'Net sales / planned net sales.',
    net_sales_vs_plan AS sales.net_sales - plan.plan_net_sales
      WITH SYNONYMS = ('sales gap to plan', 'variance to plan') COMMENT = 'Net sales minus planned net sales (USD).'
  )
  COMMENT = 'Harborline Outfitters (fictional US retailer): live sales, fulfillment, inventory and plan. Synthetic data generated in Snowflake.'
  AI_SQL_GENERATION 'Fiscal year equals calendar year; weeks start Monday. Net sales excludes tax, shipping and returns. Inventory measures are end-of-day stock and must never be summed across days. Use calendar_date for all time filtering. Current period metrics are live: today is incomplete.'$$);
INSERT INTO SV_DDL VALUES (2, 'no semi-additive ending stock', $$CREATE OR REPLACE SEMANTIC VIEW WBR_DB.RETAIL_DEMO.RETAIL_ANALYTICS_SV
  TABLES (
    dates AS WBR_DB.RETAIL_DEMO.DIM_DATE PRIMARY KEY (DATE_KEY)
      WITH SYNONYMS ('calendar', 'day') COMMENT = 'Calendar day. Weeks start Monday; fiscal year equals calendar year.',
    regions AS WBR_DB.RETAIL_DEMO.DIM_REGION PRIMARY KEY (REGION_ID)
      WITH SYNONYMS ('territory', 'market') COMMENT = 'Five US sales regions, each served by one distribution center.',
    categories AS WBR_DB.RETAIL_DEMO.DIM_CATEGORY PRIMARY KEY (CATEGORY_ID)
      WITH SYNONYMS ('department', 'merchandise category') COMMENT = 'Apparel, Footwear, Accessories.',
    products AS WBR_DB.RETAIL_DEMO.DIM_PRODUCT PRIMARY KEY (SKU)
      WITH SYNONYMS ('items', 'SKUs', 'styles') COMMENT = 'Product master at SKU level (fictional house brands).',
    stores AS WBR_DB.RETAIL_DEMO.DIM_STORE PRIMARY KEY (STORE_ID)
      WITH SYNONYMS ('shops', 'doors') COMMENT = 'Physical stores (60).',
    sales AS WBR_DB.RETAIL_DEMO.V_SALES PRIMARY KEY (LINE_ID)
      WITH SYNONYMS ('orders', 'transactions', 'order lines')
      COMMENT = 'Live order lines across Store, Web, App and Marketplace. Rows appear as orders are placed; shipment, delivery and return fields update as those events happen.',
    inventory AS WBR_DB.RETAIL_DEMO.V_INVENTORY PRIMARY KEY (SNAPSHOT_DATE, SKU, REGION_ID)
      WITH SYNONYMS ('stock', 'on hand')
      COMMENT = 'End-of-day inventory per SKU per regional distribution center. Today reflects stock as of now.',
    plan AS WBR_DB.RETAIL_DEMO.PLAN_DAILY PRIMARY KEY (DATE_KEY, REGION_ID, CATEGORY_ID)
      WITH SYNONYMS ('target', 'budget', 'forecast plan')
      COMMENT = 'Approved financial plan by day, region and category (monthly plan phased to days).'
  )
  RELATIONSHIPS (
    sales_to_dates AS sales (ORDER_DATE) REFERENCES dates,
    sales_to_regions AS sales (REGION_ID) REFERENCES regions,
    sales_to_categories AS sales (CATEGORY_ID) REFERENCES categories,
    sales_to_products AS sales (SKU) REFERENCES products,
    sales_to_stores AS sales (STORE_ID) REFERENCES stores,
    inventory_to_dates AS inventory (SNAPSHOT_DATE) REFERENCES dates,
    inventory_to_regions AS inventory (REGION_ID) REFERENCES regions,
    inventory_to_categories AS inventory (CATEGORY_ID) REFERENCES categories,
    inventory_to_products AS inventory (SKU) REFERENCES products,
    plan_to_dates AS plan (DATE_KEY) REFERENCES dates,
    plan_to_regions AS plan (REGION_ID) REFERENCES regions,
    plan_to_categories AS plan (CATEGORY_ID) REFERENCES categories
  )
  DIMENSIONS (
    dates.calendar_date AS DATE_KEY WITH SYNONYMS = ('date', 'order date', 'day')
      COMMENT = 'Calendar day: order date for sales, snapshot date for inventory, plan date for targets.',
    dates.week_start AS WEEK_START WITH SYNONYMS = ('week') COMMENT = 'Monday that starts the week.',
    dates.month_start AS MONTH_START WITH SYNONYMS = ('month') COMMENT = 'First day of the month.',
    dates.month_name AS MONTH_NAME COMMENT = 'Month label, e.g. Sep 2026.',
    dates.cal_quarter AS CAL_QUARTER WITH SYNONYMS = ('quarter') COMMENT = 'Calendar quarter, e.g. 2026-Q3.',
    dates.cal_year AS CAL_YEAR WITH SYNONYMS = ('year', 'fiscal year') COMMENT = 'Calendar (= fiscal) year.',
    dates.day_of_week AS DAY_OF_WEEK COMMENT = 'Day name (Mon-Sun).',
    dates.is_weekend AS IS_WEEKEND COMMENT = 'Saturday or Sunday.',
    dates.holiday AS COALESCE(HOLIDAY_NAME, 'No holiday') COMMENT = 'US retail holiday on this date, if any.',
    dates.retail_season AS RETAIL_SEASON COMMENT = 'Holiday, Winter clearance, Spring, Summer, Back to school & fall.',
    regions.region AS REGION_NAME WITH SYNONYMS = ('sales region', 'territory', 'area')
      COMMENT = 'US sales region (Northeast, Southeast, Midwest, Southwest, West). Online orders use the ship-to region.',
    regions.distribution_center AS DC_NAME WITH SYNONYMS = ('DC', 'warehouse', 'fulfillment center')
      COMMENT = 'Distribution center serving the region.',
    categories.category AS CATEGORY_NAME WITH SYNONYMS = ('product category', 'department')
      COMMENT = 'Merchandise category: Apparel, Footwear or Accessories.',
    products.subcategory AS SUBCATEGORY WITH SYNONYMS = ('product type', 'class') COMMENT = 'Merchandise subcategory, e.g. Running Shoes.',
    products.brand AS BRAND COMMENT = 'House brand.',
    products.product_name AS PRODUCT_NAME WITH SYNONYMS = ('product', 'style', 'item') COMMENT = 'Product (SKU) name.',
    products.sku_code AS SKU WITH SYNONYMS = ('SKU', 'item number') COMMENT = 'Stock keeping unit code.',
    products.gender AS GENDER COMMENT = 'Target customer: Women, Men, Kids, Unisex.',
    products.price_tier AS PRICE_TIER COMMENT = 'Value, Core or Premium price tier.',
    products.color_family AS COLOR_FAMILY COMMENT = 'Primary color family.',
    stores.store AS STORE_NAME WITH SYNONYMS = ('store name', 'location') COMMENT = 'Store name (store channel only).',
    stores.store_format AS STORE_FORMAT COMMENT = 'Flagship, Mall, Outlet or Street.',
    stores.store_state AS STORE_STATE COMMENT = 'State where the store is located.',
    sales.channel AS CHANNEL WITH SYNONYMS = ('sales channel') COMMENT = 'Store, Web, App or Marketplace.',
    sales.ship_method AS COALESCE(SHIP_METHOD, 'In-store') WITH SYNONYMS = ('shipping method', 'delivery speed')
      COMMENT = 'Standard, Expedited, Next Day; In-store for store purchases.',
    sales.carrier AS COALESCE(CARRIER, 'In-store') WITH SYNONYMS = ('shipping carrier') COMMENT = 'Parcel carrier for shipped orders.',
    sales.loyalty_tier AS LOYALTY_TIER WITH SYNONYMS = ('membership tier', 'customer tier')
      COMMENT = 'Guest, Member, Silver, Gold or Platinum at time of order.',
    sales.age_band AS AGE_BAND COMMENT = 'Customer age band (Unknown for guests).',
    sales.customer_state AS CUSTOMER_STATE WITH SYNONYMS = ('state', 'ship-to state') COMMENT = 'Ship-to state (store state for store purchases).',
    sales.fulfillment_status AS FULFILLMENT_STATUS COMMENT = 'Processing, In transit, Delivered, or In-store purchase - as of now.',
    sales.promotion AS COALESCE(PROMO_NAME, 'Full price') WITH SYNONYMS = ('promo', 'campaign', 'event')
      COMMENT = 'Promotion or markdown applied to the line; Full price when none.',
    sales.return_reason AS COALESCE(RETURN_REASON, 'Not returned') COMMENT = 'Reason given for the return.',
    sales.order_hour AS ORDER_HOUR COMMENT = 'Hour of day the order was placed (US Eastern).'
  )
  METRICS (
    sales.net_sales AS SUM(NET_SALES) WITH SYNONYMS = ('revenue', 'sales', 'net revenue')
      COMMENT = 'Net merchandise sales (USD): list price x units minus discounts. Excludes tax, shipping fees and returns.',
    sales.gross_sales AS SUM(GROSS_SALES) WITH SYNONYMS = ('gross revenue')
      COMMENT = 'Sales at list price before discounts (USD).',
    sales.discount_amount AS SUM(DISCOUNT_AMOUNT) WITH SYNONYMS = ('markdowns', 'promotional discount')
      COMMENT = 'Value of promotional discounts, markdowns and member coupons (USD).',
    sales.discount_rate AS SUM(DISCOUNT_AMOUNT) / NULLIF(SUM(GROSS_SALES), 0)
      COMMENT = 'Discount amount / gross sales.',
    sales.cost_of_goods_sold AS SUM(COGS) WITH SYNONYMS = ('COGS', 'product cost') COMMENT = 'Landed unit cost x units (USD).',
    sales.gross_margin AS SUM(NET_SALES - COGS) WITH SYNONYMS = ('gross profit', 'margin dollars')
      COMMENT = 'Net sales minus cost of goods sold (USD).',
    sales.gross_margin_pct AS SUM(NET_SALES - COGS) / NULLIF(SUM(NET_SALES), 0) WITH SYNONYMS = ('margin rate', 'GM%')
      COMMENT = 'Gross margin / net sales.',
    sales.units_sold AS SUM(QTY) WITH SYNONYMS = ('units', 'quantity sold') COMMENT = 'Units sold (fulfilled).',
    sales.order_count AS COUNT(DISTINCT ORDER_ID) WITH SYNONYMS = ('orders', 'transactions', 'number of orders')
      COMMENT = 'Distinct orders. With a product breakdown it counts orders containing that product.',
    sales.average_order_value AS SUM(NET_SALES) / NULLIF(COUNT(DISTINCT ORDER_ID), 0) WITH SYNONYMS = ('AOV', 'basket size')
      COMMENT = 'Net sales / orders.',
    sales.units_per_transaction AS SUM(QTY) / NULLIF(COUNT(DISTINCT ORDER_ID), 0) WITH SYNONYMS = ('UPT', 'units per order')
      COMMENT = 'Units / orders.',
    sales.active_customers AS COUNT(DISTINCT CUSTOMER_ID) WITH SYNONYMS = ('customers', 'buyers')
      COMMENT = 'Distinct identified customers who ordered (guests excluded).',
    sales.online_sales_share AS SUM(IFF(IS_ONLINE, NET_SALES, 0)) / NULLIF(SUM(NET_SALES), 0) WITH SYNONYMS = ('digital share', 'ecommerce penetration')
      COMMENT = 'Share of net sales from Web, App and Marketplace.',
    sales.shipped_orders AS COUNT(DISTINCT IFF(IS_SHIPPED_ORDER, ORDER_ID, NULL))
      COMMENT = 'Orders shipped to customers (Web, App, Marketplace).',
    sales.free_shipping_order_pct AS COUNT(DISTINCT IFF(FREE_SHIPPING_FLAG, ORDER_ID, NULL)) / NULLIF(COUNT(DISTINCT IFF(IS_SHIPPED_ORDER, ORDER_ID, NULL)), 0)
      WITH SYNONYMS = ('free shipping %', 'free shipping rate')
      COMMENT = 'Shipped orders with a 0 USD shipping fee / all shipped orders. Free when subtotal meets the threshold (99 USD, 119 USD from Mar 2026), for Gold and Platinum members, on free-shipping promotion days, or by marketplace policy.',
    sales.shipping_fee_revenue AS SUM(LINE_SHIPPING_FEE) COMMENT = 'Shipping fees charged to customers (USD).',
    sales.avg_click_to_ship_hours AS AVG(CLICK_TO_SHIP_HOURS) WITH SYNONYMS = ('fulfillment time', 'order to ship time', 'processing time')
      COMMENT = 'Average hours from order placed to carrier hand-off, over shipped order lines.',
    sales.avg_transit_days AS AVG(TRANSIT_DAYS) WITH SYNONYMS = ('carrier transit time')
      COMMENT = 'Average days from carrier hand-off to delivery, over delivered order lines.',
    sales.avg_delivery_days AS AVG(DELIVERY_DAYS) WITH SYNONYMS = ('shipping time', 'avg shipping time', 'delivery time', 'click to door')
      COMMENT = 'Average days from order placed to delivery, over delivered order lines.',
    sales.on_time_delivery_pct AS AVG(CASE WHEN ON_TIME_FLAG THEN 1 WHEN NOT ON_TIME_FLAG THEN 0 END)
      WITH SYNONYMS = ('OTD', 'on-time rate')
      COMMENT = 'Delivered lines that arrived on or before the promised date (Standard 6 days, Expedited 3, Next Day 2) / all delivered lines.',
    sales.returned_sales AS SUM(RETURNED_SALES) COMMENT = 'Net sales value of items returned so far (USD).',
    sales.returned_units AS SUM(RETURNED_UNITS) COMMENT = 'Units returned so far.',
    sales.return_rate AS SUM(RETURNED_SALES) / NULLIF(SUM(NET_SALES), 0) WITH SYNONYMS = ('returns %')
      COMMENT = 'Returned sales / net sales for orders placed in the period. Recent periods rise as returns arrive.',
    sales.net_sales_after_returns AS SUM(NET_SALES - RETURNED_SALES) COMMENT = 'Net sales less returns (USD).',
    inventory.avg_units_on_hand AS SUM(UNITS_ON_HAND) / NULLIF(COUNT(DISTINCT SNAPSHOT_DATE), 0)
      WITH SYNONYMS = ('units on hand', 'inventory units', 'stock on hand')
      COMMENT = 'Average daily end-of-day units on hand: stock is summed across the selected SKUs and DCs, then averaged over days (stock is never added up across days).',
    inventory.avg_inventory_value AS SUM(INVENTORY_VALUE) / NULLIF(COUNT(DISTINCT SNAPSHOT_DATE), 0)
      WITH SYNONYMS = ('inventory value', 'stock value') COMMENT = 'Average daily inventory value at cost (USD).',
    inventory.avg_units_on_order AS SUM(UNITS_ON_ORDER) / NULLIF(COUNT(DISTINCT SNAPSHOT_DATE), 0)
      WITH SYNONYMS = ('on order', 'open PO units') COMMENT = 'Average daily units on open replenishment orders.',
    inventory.units_sold_from_stock AS SUM(UNITS_SOLD) COMMENT = 'Units fulfilled from DC stock (equals units sold for the same slice).',
    inventory.lost_sales_units AS SUM(LOST_UNITS) WITH SYNONYMS = ('lost sales', 'unmet demand')
      COMMENT = 'Units customers wanted that could not be fulfilled because the DC was out of stock.',
    inventory.stockout_rate AS AVG(IFF(STOCKOUT_FLAG, 1, 0)) WITH SYNONYMS = ('out of stock %', 'OOS rate')
      COMMENT = 'Share of SKU x DC x day records ending with zero units on hand.',
    inventory.in_stock_rate AS 1 - AVG(IFF(STOCKOUT_FLAG, 1, 0)) WITH SYNONYMS = ('in-stock %', 'availability')
      COMMENT = 'Share of SKU x DC x day records ending with stock available.',
    inventory.weeks_of_supply AS SUM(UNITS_ON_HAND) / NULLIF(7 * SUM(UNITS_SOLD), 0) WITH SYNONYMS = ('WOS', 'weeks of cover')
      COMMENT = 'Average units on hand / average weekly units sold.',
    inventory.sell_through_pct AS SUM(UNITS_SOLD) / NULLIF(SUM(UNITS_SOLD) + SUM(UNITS_ON_HAND) / NULLIF(COUNT(DISTINCT SNAPSHOT_DATE), 0), 0)
      WITH SYNONYMS = ('sell-through', 'sell thru')
      COMMENT = 'Units sold / (units sold + average daily units on hand) for the period.',
    plan.plan_net_sales AS SUM(PLAN_NET_SALES) WITH SYNONYMS = ('sales plan', 'sales target', 'budget')
      COMMENT = 'Planned net sales (USD).',
    plan.plan_units AS SUM(PLAN_UNITS) WITH SYNONYMS = ('unit plan') COMMENT = 'Planned units.',
    plan.plan_gross_margin AS SUM(PLAN_GROSS_MARGIN) WITH SYNONYMS = ('margin plan') COMMENT = 'Planned gross margin (USD).',
    plan_attainment_pct AS sales.net_sales / NULLIF(plan.plan_net_sales, 0)
      WITH SYNONYMS = ('sales vs plan %', 'attainment', 'percent to plan')
      COMMENT = 'Net sales / planned net sales.',
    net_sales_vs_plan AS sales.net_sales - plan.plan_net_sales
      WITH SYNONYMS = ('sales gap to plan', 'variance to plan') COMMENT = 'Net sales minus planned net sales (USD).'
  )
  COMMENT = 'Harborline Outfitters (fictional US retailer): live sales, fulfillment, inventory and plan. Synthetic data generated in Snowflake.'
  AI_SQL_GENERATION 'Fiscal year equals calendar year; weeks start Monday. Net sales excludes tax, shipping and returns. Inventory measures are end-of-day stock and must never be summed across days. Use calendar_date for all time filtering. Current period metrics are live: today is incomplete.'$$);
INSERT INTO SV_DDL VALUES (3, 'no derived metrics', $$CREATE OR REPLACE SEMANTIC VIEW WBR_DB.RETAIL_DEMO.RETAIL_ANALYTICS_SV
  TABLES (
    dates AS WBR_DB.RETAIL_DEMO.DIM_DATE PRIMARY KEY (DATE_KEY)
      WITH SYNONYMS ('calendar', 'day') COMMENT = 'Calendar day. Weeks start Monday; fiscal year equals calendar year.',
    regions AS WBR_DB.RETAIL_DEMO.DIM_REGION PRIMARY KEY (REGION_ID)
      WITH SYNONYMS ('territory', 'market') COMMENT = 'Five US sales regions, each served by one distribution center.',
    categories AS WBR_DB.RETAIL_DEMO.DIM_CATEGORY PRIMARY KEY (CATEGORY_ID)
      WITH SYNONYMS ('department', 'merchandise category') COMMENT = 'Apparel, Footwear, Accessories.',
    products AS WBR_DB.RETAIL_DEMO.DIM_PRODUCT PRIMARY KEY (SKU)
      WITH SYNONYMS ('items', 'SKUs', 'styles') COMMENT = 'Product master at SKU level (fictional house brands).',
    stores AS WBR_DB.RETAIL_DEMO.DIM_STORE PRIMARY KEY (STORE_ID)
      WITH SYNONYMS ('shops', 'doors') COMMENT = 'Physical stores (60).',
    sales AS WBR_DB.RETAIL_DEMO.V_SALES PRIMARY KEY (LINE_ID)
      WITH SYNONYMS ('orders', 'transactions', 'order lines')
      COMMENT = 'Live order lines across Store, Web, App and Marketplace. Rows appear as orders are placed; shipment, delivery and return fields update as those events happen.',
    inventory AS WBR_DB.RETAIL_DEMO.V_INVENTORY PRIMARY KEY (SNAPSHOT_DATE, SKU, REGION_ID)
      WITH SYNONYMS ('stock', 'on hand')
      COMMENT = 'End-of-day inventory per SKU per regional distribution center. Today reflects stock as of now.',
    plan AS WBR_DB.RETAIL_DEMO.PLAN_DAILY PRIMARY KEY (DATE_KEY, REGION_ID, CATEGORY_ID)
      WITH SYNONYMS ('target', 'budget', 'forecast plan')
      COMMENT = 'Approved financial plan by day, region and category (monthly plan phased to days).'
  )
  RELATIONSHIPS (
    sales_to_dates AS sales (ORDER_DATE) REFERENCES dates,
    sales_to_regions AS sales (REGION_ID) REFERENCES regions,
    sales_to_categories AS sales (CATEGORY_ID) REFERENCES categories,
    sales_to_products AS sales (SKU) REFERENCES products,
    sales_to_stores AS sales (STORE_ID) REFERENCES stores,
    inventory_to_dates AS inventory (SNAPSHOT_DATE) REFERENCES dates,
    inventory_to_regions AS inventory (REGION_ID) REFERENCES regions,
    inventory_to_categories AS inventory (CATEGORY_ID) REFERENCES categories,
    inventory_to_products AS inventory (SKU) REFERENCES products,
    plan_to_dates AS plan (DATE_KEY) REFERENCES dates,
    plan_to_regions AS plan (REGION_ID) REFERENCES regions,
    plan_to_categories AS plan (CATEGORY_ID) REFERENCES categories
  )
  DIMENSIONS (
    dates.calendar_date AS DATE_KEY WITH SYNONYMS = ('date', 'order date', 'day')
      COMMENT = 'Calendar day: order date for sales, snapshot date for inventory, plan date for targets.',
    dates.week_start AS WEEK_START WITH SYNONYMS = ('week') COMMENT = 'Monday that starts the week.',
    dates.month_start AS MONTH_START WITH SYNONYMS = ('month') COMMENT = 'First day of the month.',
    dates.month_name AS MONTH_NAME COMMENT = 'Month label, e.g. Sep 2026.',
    dates.cal_quarter AS CAL_QUARTER WITH SYNONYMS = ('quarter') COMMENT = 'Calendar quarter, e.g. 2026-Q3.',
    dates.cal_year AS CAL_YEAR WITH SYNONYMS = ('year', 'fiscal year') COMMENT = 'Calendar (= fiscal) year.',
    dates.day_of_week AS DAY_OF_WEEK COMMENT = 'Day name (Mon-Sun).',
    dates.is_weekend AS IS_WEEKEND COMMENT = 'Saturday or Sunday.',
    dates.holiday AS COALESCE(HOLIDAY_NAME, 'No holiday') COMMENT = 'US retail holiday on this date, if any.',
    dates.retail_season AS RETAIL_SEASON COMMENT = 'Holiday, Winter clearance, Spring, Summer, Back to school & fall.',
    regions.region AS REGION_NAME WITH SYNONYMS = ('sales region', 'territory', 'area')
      COMMENT = 'US sales region (Northeast, Southeast, Midwest, Southwest, West). Online orders use the ship-to region.',
    regions.distribution_center AS DC_NAME WITH SYNONYMS = ('DC', 'warehouse', 'fulfillment center')
      COMMENT = 'Distribution center serving the region.',
    categories.category AS CATEGORY_NAME WITH SYNONYMS = ('product category', 'department')
      COMMENT = 'Merchandise category: Apparel, Footwear or Accessories.',
    products.subcategory AS SUBCATEGORY WITH SYNONYMS = ('product type', 'class') COMMENT = 'Merchandise subcategory, e.g. Running Shoes.',
    products.brand AS BRAND COMMENT = 'House brand.',
    products.product_name AS PRODUCT_NAME WITH SYNONYMS = ('product', 'style', 'item') COMMENT = 'Product (SKU) name.',
    products.sku_code AS SKU WITH SYNONYMS = ('SKU', 'item number') COMMENT = 'Stock keeping unit code.',
    products.gender AS GENDER COMMENT = 'Target customer: Women, Men, Kids, Unisex.',
    products.price_tier AS PRICE_TIER COMMENT = 'Value, Core or Premium price tier.',
    products.color_family AS COLOR_FAMILY COMMENT = 'Primary color family.',
    stores.store AS STORE_NAME WITH SYNONYMS = ('store name', 'location') COMMENT = 'Store name (store channel only).',
    stores.store_format AS STORE_FORMAT COMMENT = 'Flagship, Mall, Outlet or Street.',
    stores.store_state AS STORE_STATE COMMENT = 'State where the store is located.',
    sales.channel AS CHANNEL WITH SYNONYMS = ('sales channel') COMMENT = 'Store, Web, App or Marketplace.',
    sales.ship_method AS COALESCE(SHIP_METHOD, 'In-store') WITH SYNONYMS = ('shipping method', 'delivery speed')
      COMMENT = 'Standard, Expedited, Next Day; In-store for store purchases.',
    sales.carrier AS COALESCE(CARRIER, 'In-store') WITH SYNONYMS = ('shipping carrier') COMMENT = 'Parcel carrier for shipped orders.',
    sales.loyalty_tier AS LOYALTY_TIER WITH SYNONYMS = ('membership tier', 'customer tier')
      COMMENT = 'Guest, Member, Silver, Gold or Platinum at time of order.',
    sales.age_band AS AGE_BAND COMMENT = 'Customer age band (Unknown for guests).',
    sales.customer_state AS CUSTOMER_STATE WITH SYNONYMS = ('state', 'ship-to state') COMMENT = 'Ship-to state (store state for store purchases).',
    sales.fulfillment_status AS FULFILLMENT_STATUS COMMENT = 'Processing, In transit, Delivered, or In-store purchase - as of now.',
    sales.promotion AS COALESCE(PROMO_NAME, 'Full price') WITH SYNONYMS = ('promo', 'campaign', 'event')
      COMMENT = 'Promotion or markdown applied to the line; Full price when none.',
    sales.return_reason AS COALESCE(RETURN_REASON, 'Not returned') COMMENT = 'Reason given for the return.',
    sales.order_hour AS ORDER_HOUR COMMENT = 'Hour of day the order was placed (US Eastern).'
  )
  METRICS (
    sales.net_sales AS SUM(NET_SALES) WITH SYNONYMS = ('revenue', 'sales', 'net revenue')
      COMMENT = 'Net merchandise sales (USD): list price x units minus discounts. Excludes tax, shipping fees and returns.',
    sales.gross_sales AS SUM(GROSS_SALES) WITH SYNONYMS = ('gross revenue')
      COMMENT = 'Sales at list price before discounts (USD).',
    sales.discount_amount AS SUM(DISCOUNT_AMOUNT) WITH SYNONYMS = ('markdowns', 'promotional discount')
      COMMENT = 'Value of promotional discounts, markdowns and member coupons (USD).',
    sales.discount_rate AS SUM(DISCOUNT_AMOUNT) / NULLIF(SUM(GROSS_SALES), 0)
      COMMENT = 'Discount amount / gross sales.',
    sales.cost_of_goods_sold AS SUM(COGS) WITH SYNONYMS = ('COGS', 'product cost') COMMENT = 'Landed unit cost x units (USD).',
    sales.gross_margin AS SUM(NET_SALES - COGS) WITH SYNONYMS = ('gross profit', 'margin dollars')
      COMMENT = 'Net sales minus cost of goods sold (USD).',
    sales.gross_margin_pct AS SUM(NET_SALES - COGS) / NULLIF(SUM(NET_SALES), 0) WITH SYNONYMS = ('margin rate', 'GM%')
      COMMENT = 'Gross margin / net sales.',
    sales.units_sold AS SUM(QTY) WITH SYNONYMS = ('units', 'quantity sold') COMMENT = 'Units sold (fulfilled).',
    sales.order_count AS COUNT(DISTINCT ORDER_ID) WITH SYNONYMS = ('orders', 'transactions', 'number of orders')
      COMMENT = 'Distinct orders. With a product breakdown it counts orders containing that product.',
    sales.average_order_value AS SUM(NET_SALES) / NULLIF(COUNT(DISTINCT ORDER_ID), 0) WITH SYNONYMS = ('AOV', 'basket size')
      COMMENT = 'Net sales / orders.',
    sales.units_per_transaction AS SUM(QTY) / NULLIF(COUNT(DISTINCT ORDER_ID), 0) WITH SYNONYMS = ('UPT', 'units per order')
      COMMENT = 'Units / orders.',
    sales.active_customers AS COUNT(DISTINCT CUSTOMER_ID) WITH SYNONYMS = ('customers', 'buyers')
      COMMENT = 'Distinct identified customers who ordered (guests excluded).',
    sales.online_sales_share AS SUM(IFF(IS_ONLINE, NET_SALES, 0)) / NULLIF(SUM(NET_SALES), 0) WITH SYNONYMS = ('digital share', 'ecommerce penetration')
      COMMENT = 'Share of net sales from Web, App and Marketplace.',
    sales.shipped_orders AS COUNT(DISTINCT IFF(IS_SHIPPED_ORDER, ORDER_ID, NULL))
      COMMENT = 'Orders shipped to customers (Web, App, Marketplace).',
    sales.free_shipping_order_pct AS COUNT(DISTINCT IFF(FREE_SHIPPING_FLAG, ORDER_ID, NULL)) / NULLIF(COUNT(DISTINCT IFF(IS_SHIPPED_ORDER, ORDER_ID, NULL)), 0)
      WITH SYNONYMS = ('free shipping %', 'free shipping rate')
      COMMENT = 'Shipped orders with a 0 USD shipping fee / all shipped orders. Free when subtotal meets the threshold (99 USD, 119 USD from Mar 2026), for Gold and Platinum members, on free-shipping promotion days, or by marketplace policy.',
    sales.shipping_fee_revenue AS SUM(LINE_SHIPPING_FEE) COMMENT = 'Shipping fees charged to customers (USD).',
    sales.avg_click_to_ship_hours AS AVG(CLICK_TO_SHIP_HOURS) WITH SYNONYMS = ('fulfillment time', 'order to ship time', 'processing time')
      COMMENT = 'Average hours from order placed to carrier hand-off, over shipped order lines.',
    sales.avg_transit_days AS AVG(TRANSIT_DAYS) WITH SYNONYMS = ('carrier transit time')
      COMMENT = 'Average days from carrier hand-off to delivery, over delivered order lines.',
    sales.avg_delivery_days AS AVG(DELIVERY_DAYS) WITH SYNONYMS = ('shipping time', 'avg shipping time', 'delivery time', 'click to door')
      COMMENT = 'Average days from order placed to delivery, over delivered order lines.',
    sales.on_time_delivery_pct AS AVG(CASE WHEN ON_TIME_FLAG THEN 1 WHEN NOT ON_TIME_FLAG THEN 0 END)
      WITH SYNONYMS = ('OTD', 'on-time rate')
      COMMENT = 'Delivered lines that arrived on or before the promised date (Standard 6 days, Expedited 3, Next Day 2) / all delivered lines.',
    sales.returned_sales AS SUM(RETURNED_SALES) COMMENT = 'Net sales value of items returned so far (USD).',
    sales.returned_units AS SUM(RETURNED_UNITS) COMMENT = 'Units returned so far.',
    sales.return_rate AS SUM(RETURNED_SALES) / NULLIF(SUM(NET_SALES), 0) WITH SYNONYMS = ('returns %')
      COMMENT = 'Returned sales / net sales for orders placed in the period. Recent periods rise as returns arrive.',
    sales.net_sales_after_returns AS SUM(NET_SALES - RETURNED_SALES) COMMENT = 'Net sales less returns (USD).',
    inventory.avg_units_on_hand AS SUM(UNITS_ON_HAND) / NULLIF(COUNT(DISTINCT SNAPSHOT_DATE), 0)
      WITH SYNONYMS = ('units on hand', 'inventory units', 'stock on hand')
      COMMENT = 'Average daily end-of-day units on hand: stock is summed across the selected SKUs and DCs, then averaged over days (stock is never added up across days).',
    inventory.avg_inventory_value AS SUM(INVENTORY_VALUE) / NULLIF(COUNT(DISTINCT SNAPSHOT_DATE), 0)
      WITH SYNONYMS = ('inventory value', 'stock value') COMMENT = 'Average daily inventory value at cost (USD).',
    inventory.avg_units_on_order AS SUM(UNITS_ON_ORDER) / NULLIF(COUNT(DISTINCT SNAPSHOT_DATE), 0)
      WITH SYNONYMS = ('on order', 'open PO units') COMMENT = 'Average daily units on open replenishment orders.',
    inventory.units_sold_from_stock AS SUM(UNITS_SOLD) COMMENT = 'Units fulfilled from DC stock (equals units sold for the same slice).',
    inventory.lost_sales_units AS SUM(LOST_UNITS) WITH SYNONYMS = ('lost sales', 'unmet demand')
      COMMENT = 'Units customers wanted that could not be fulfilled because the DC was out of stock.',
    inventory.stockout_rate AS AVG(IFF(STOCKOUT_FLAG, 1, 0)) WITH SYNONYMS = ('out of stock %', 'OOS rate')
      COMMENT = 'Share of SKU x DC x day records ending with zero units on hand.',
    inventory.in_stock_rate AS 1 - AVG(IFF(STOCKOUT_FLAG, 1, 0)) WITH SYNONYMS = ('in-stock %', 'availability')
      COMMENT = 'Share of SKU x DC x day records ending with stock available.',
    inventory.weeks_of_supply AS SUM(UNITS_ON_HAND) / NULLIF(7 * SUM(UNITS_SOLD), 0) WITH SYNONYMS = ('WOS', 'weeks of cover')
      COMMENT = 'Average units on hand / average weekly units sold.',
    inventory.sell_through_pct AS SUM(UNITS_SOLD) / NULLIF(SUM(UNITS_SOLD) + SUM(UNITS_ON_HAND) / NULLIF(COUNT(DISTINCT SNAPSHOT_DATE), 0), 0)
      WITH SYNONYMS = ('sell-through', 'sell thru')
      COMMENT = 'Units sold / (units sold + average daily units on hand) for the period.',
    plan.plan_net_sales AS SUM(PLAN_NET_SALES) WITH SYNONYMS = ('sales plan', 'sales target', 'budget')
      COMMENT = 'Planned net sales (USD).',
    plan.plan_units AS SUM(PLAN_UNITS) WITH SYNONYMS = ('unit plan') COMMENT = 'Planned units.',
    plan.plan_gross_margin AS SUM(PLAN_GROSS_MARGIN) WITH SYNONYMS = ('margin plan') COMMENT = 'Planned gross margin (USD).'
  )
  COMMENT = 'Harborline Outfitters (fictional US retailer): live sales, fulfillment, inventory and plan. Synthetic data generated in Snowflake.'
  AI_SQL_GENERATION 'Fiscal year equals calendar year; weeks start Monday. Net sales excludes tax, shipping and returns. Inventory measures are end-of-day stock and must never be summed across days. Use calendar_date for all time filtering. Current period metrics are live: today is incomplete.'$$);
INSERT INTO SV_DDL VALUES (4, 'core (no AI instructions)', $$CREATE OR REPLACE SEMANTIC VIEW WBR_DB.RETAIL_DEMO.RETAIL_ANALYTICS_SV
  TABLES (
    dates AS WBR_DB.RETAIL_DEMO.DIM_DATE PRIMARY KEY (DATE_KEY)
      WITH SYNONYMS ('calendar', 'day') COMMENT = 'Calendar day. Weeks start Monday; fiscal year equals calendar year.',
    regions AS WBR_DB.RETAIL_DEMO.DIM_REGION PRIMARY KEY (REGION_ID)
      WITH SYNONYMS ('territory', 'market') COMMENT = 'Five US sales regions, each served by one distribution center.',
    categories AS WBR_DB.RETAIL_DEMO.DIM_CATEGORY PRIMARY KEY (CATEGORY_ID)
      WITH SYNONYMS ('department', 'merchandise category') COMMENT = 'Apparel, Footwear, Accessories.',
    products AS WBR_DB.RETAIL_DEMO.DIM_PRODUCT PRIMARY KEY (SKU)
      WITH SYNONYMS ('items', 'SKUs', 'styles') COMMENT = 'Product master at SKU level (fictional house brands).',
    stores AS WBR_DB.RETAIL_DEMO.DIM_STORE PRIMARY KEY (STORE_ID)
      WITH SYNONYMS ('shops', 'doors') COMMENT = 'Physical stores (60).',
    sales AS WBR_DB.RETAIL_DEMO.V_SALES PRIMARY KEY (LINE_ID)
      WITH SYNONYMS ('orders', 'transactions', 'order lines')
      COMMENT = 'Live order lines across Store, Web, App and Marketplace. Rows appear as orders are placed; shipment, delivery and return fields update as those events happen.',
    inventory AS WBR_DB.RETAIL_DEMO.V_INVENTORY PRIMARY KEY (SNAPSHOT_DATE, SKU, REGION_ID)
      WITH SYNONYMS ('stock', 'on hand')
      COMMENT = 'End-of-day inventory per SKU per regional distribution center. Today reflects stock as of now.',
    plan AS WBR_DB.RETAIL_DEMO.PLAN_DAILY PRIMARY KEY (DATE_KEY, REGION_ID, CATEGORY_ID)
      WITH SYNONYMS ('target', 'budget', 'forecast plan')
      COMMENT = 'Approved financial plan by day, region and category (monthly plan phased to days).'
  )
  RELATIONSHIPS (
    sales_to_dates AS sales (ORDER_DATE) REFERENCES dates,
    sales_to_regions AS sales (REGION_ID) REFERENCES regions,
    sales_to_categories AS sales (CATEGORY_ID) REFERENCES categories,
    sales_to_products AS sales (SKU) REFERENCES products,
    sales_to_stores AS sales (STORE_ID) REFERENCES stores,
    inventory_to_dates AS inventory (SNAPSHOT_DATE) REFERENCES dates,
    inventory_to_regions AS inventory (REGION_ID) REFERENCES regions,
    inventory_to_categories AS inventory (CATEGORY_ID) REFERENCES categories,
    inventory_to_products AS inventory (SKU) REFERENCES products,
    plan_to_dates AS plan (DATE_KEY) REFERENCES dates,
    plan_to_regions AS plan (REGION_ID) REFERENCES regions,
    plan_to_categories AS plan (CATEGORY_ID) REFERENCES categories
  )
  DIMENSIONS (
    dates.calendar_date AS DATE_KEY WITH SYNONYMS = ('date', 'order date', 'day')
      COMMENT = 'Calendar day: order date for sales, snapshot date for inventory, plan date for targets.',
    dates.week_start AS WEEK_START WITH SYNONYMS = ('week') COMMENT = 'Monday that starts the week.',
    dates.month_start AS MONTH_START WITH SYNONYMS = ('month') COMMENT = 'First day of the month.',
    dates.month_name AS MONTH_NAME COMMENT = 'Month label, e.g. Sep 2026.',
    dates.cal_quarter AS CAL_QUARTER WITH SYNONYMS = ('quarter') COMMENT = 'Calendar quarter, e.g. 2026-Q3.',
    dates.cal_year AS CAL_YEAR WITH SYNONYMS = ('year', 'fiscal year') COMMENT = 'Calendar (= fiscal) year.',
    dates.day_of_week AS DAY_OF_WEEK COMMENT = 'Day name (Mon-Sun).',
    dates.is_weekend AS IS_WEEKEND COMMENT = 'Saturday or Sunday.',
    dates.holiday AS COALESCE(HOLIDAY_NAME, 'No holiday') COMMENT = 'US retail holiday on this date, if any.',
    dates.retail_season AS RETAIL_SEASON COMMENT = 'Holiday, Winter clearance, Spring, Summer, Back to school & fall.',
    regions.region AS REGION_NAME WITH SYNONYMS = ('sales region', 'territory', 'area')
      COMMENT = 'US sales region (Northeast, Southeast, Midwest, Southwest, West). Online orders use the ship-to region.',
    regions.distribution_center AS DC_NAME WITH SYNONYMS = ('DC', 'warehouse', 'fulfillment center')
      COMMENT = 'Distribution center serving the region.',
    categories.category AS CATEGORY_NAME WITH SYNONYMS = ('product category', 'department')
      COMMENT = 'Merchandise category: Apparel, Footwear or Accessories.',
    products.subcategory AS SUBCATEGORY WITH SYNONYMS = ('product type', 'class') COMMENT = 'Merchandise subcategory, e.g. Running Shoes.',
    products.brand AS BRAND COMMENT = 'House brand.',
    products.product_name AS PRODUCT_NAME WITH SYNONYMS = ('product', 'style', 'item') COMMENT = 'Product (SKU) name.',
    products.sku_code AS SKU WITH SYNONYMS = ('SKU', 'item number') COMMENT = 'Stock keeping unit code.',
    products.gender AS GENDER COMMENT = 'Target customer: Women, Men, Kids, Unisex.',
    products.price_tier AS PRICE_TIER COMMENT = 'Value, Core or Premium price tier.',
    products.color_family AS COLOR_FAMILY COMMENT = 'Primary color family.',
    stores.store AS STORE_NAME WITH SYNONYMS = ('store name', 'location') COMMENT = 'Store name (store channel only).',
    stores.store_format AS STORE_FORMAT COMMENT = 'Flagship, Mall, Outlet or Street.',
    stores.store_state AS STORE_STATE COMMENT = 'State where the store is located.',
    sales.channel AS CHANNEL WITH SYNONYMS = ('sales channel') COMMENT = 'Store, Web, App or Marketplace.',
    sales.ship_method AS COALESCE(SHIP_METHOD, 'In-store') WITH SYNONYMS = ('shipping method', 'delivery speed')
      COMMENT = 'Standard, Expedited, Next Day; In-store for store purchases.',
    sales.carrier AS COALESCE(CARRIER, 'In-store') WITH SYNONYMS = ('shipping carrier') COMMENT = 'Parcel carrier for shipped orders.',
    sales.loyalty_tier AS LOYALTY_TIER WITH SYNONYMS = ('membership tier', 'customer tier')
      COMMENT = 'Guest, Member, Silver, Gold or Platinum at time of order.',
    sales.age_band AS AGE_BAND COMMENT = 'Customer age band (Unknown for guests).',
    sales.customer_state AS CUSTOMER_STATE WITH SYNONYMS = ('state', 'ship-to state') COMMENT = 'Ship-to state (store state for store purchases).',
    sales.fulfillment_status AS FULFILLMENT_STATUS COMMENT = 'Processing, In transit, Delivered, or In-store purchase - as of now.',
    sales.promotion AS COALESCE(PROMO_NAME, 'Full price') WITH SYNONYMS = ('promo', 'campaign', 'event')
      COMMENT = 'Promotion or markdown applied to the line; Full price when none.',
    sales.return_reason AS COALESCE(RETURN_REASON, 'Not returned') COMMENT = 'Reason given for the return.',
    sales.order_hour AS ORDER_HOUR COMMENT = 'Hour of day the order was placed (US Eastern).'
  )
  METRICS (
    sales.net_sales AS SUM(NET_SALES) WITH SYNONYMS = ('revenue', 'sales', 'net revenue')
      COMMENT = 'Net merchandise sales (USD): list price x units minus discounts. Excludes tax, shipping fees and returns.',
    sales.gross_sales AS SUM(GROSS_SALES) WITH SYNONYMS = ('gross revenue')
      COMMENT = 'Sales at list price before discounts (USD).',
    sales.discount_amount AS SUM(DISCOUNT_AMOUNT) WITH SYNONYMS = ('markdowns', 'promotional discount')
      COMMENT = 'Value of promotional discounts, markdowns and member coupons (USD).',
    sales.discount_rate AS SUM(DISCOUNT_AMOUNT) / NULLIF(SUM(GROSS_SALES), 0)
      COMMENT = 'Discount amount / gross sales.',
    sales.cost_of_goods_sold AS SUM(COGS) WITH SYNONYMS = ('COGS', 'product cost') COMMENT = 'Landed unit cost x units (USD).',
    sales.gross_margin AS SUM(NET_SALES - COGS) WITH SYNONYMS = ('gross profit', 'margin dollars')
      COMMENT = 'Net sales minus cost of goods sold (USD).',
    sales.gross_margin_pct AS SUM(NET_SALES - COGS) / NULLIF(SUM(NET_SALES), 0) WITH SYNONYMS = ('margin rate', 'GM%')
      COMMENT = 'Gross margin / net sales.',
    sales.units_sold AS SUM(QTY) WITH SYNONYMS = ('units', 'quantity sold') COMMENT = 'Units sold (fulfilled).',
    sales.order_count AS COUNT(DISTINCT ORDER_ID) WITH SYNONYMS = ('orders', 'transactions', 'number of orders')
      COMMENT = 'Distinct orders. With a product breakdown it counts orders containing that product.',
    sales.average_order_value AS SUM(NET_SALES) / NULLIF(COUNT(DISTINCT ORDER_ID), 0) WITH SYNONYMS = ('AOV', 'basket size')
      COMMENT = 'Net sales / orders.',
    sales.units_per_transaction AS SUM(QTY) / NULLIF(COUNT(DISTINCT ORDER_ID), 0) WITH SYNONYMS = ('UPT', 'units per order')
      COMMENT = 'Units / orders.',
    sales.active_customers AS COUNT(DISTINCT CUSTOMER_ID) WITH SYNONYMS = ('customers', 'buyers')
      COMMENT = 'Distinct identified customers who ordered (guests excluded).',
    sales.online_sales_share AS SUM(IFF(IS_ONLINE, NET_SALES, 0)) / NULLIF(SUM(NET_SALES), 0) WITH SYNONYMS = ('digital share', 'ecommerce penetration')
      COMMENT = 'Share of net sales from Web, App and Marketplace.',
    sales.shipped_orders AS COUNT(DISTINCT IFF(IS_SHIPPED_ORDER, ORDER_ID, NULL))
      COMMENT = 'Orders shipped to customers (Web, App, Marketplace).',
    sales.free_shipping_order_pct AS COUNT(DISTINCT IFF(FREE_SHIPPING_FLAG, ORDER_ID, NULL)) / NULLIF(COUNT(DISTINCT IFF(IS_SHIPPED_ORDER, ORDER_ID, NULL)), 0)
      WITH SYNONYMS = ('free shipping %', 'free shipping rate')
      COMMENT = 'Shipped orders with a 0 USD shipping fee / all shipped orders. Free when subtotal meets the threshold (99 USD, 119 USD from Mar 2026), for Gold and Platinum members, on free-shipping promotion days, or by marketplace policy.',
    sales.shipping_fee_revenue AS SUM(LINE_SHIPPING_FEE) COMMENT = 'Shipping fees charged to customers (USD).',
    sales.avg_click_to_ship_hours AS AVG(CLICK_TO_SHIP_HOURS) WITH SYNONYMS = ('fulfillment time', 'order to ship time', 'processing time')
      COMMENT = 'Average hours from order placed to carrier hand-off, over shipped order lines.',
    sales.avg_transit_days AS AVG(TRANSIT_DAYS) WITH SYNONYMS = ('carrier transit time')
      COMMENT = 'Average days from carrier hand-off to delivery, over delivered order lines.',
    sales.avg_delivery_days AS AVG(DELIVERY_DAYS) WITH SYNONYMS = ('shipping time', 'avg shipping time', 'delivery time', 'click to door')
      COMMENT = 'Average days from order placed to delivery, over delivered order lines.',
    sales.on_time_delivery_pct AS AVG(CASE WHEN ON_TIME_FLAG THEN 1 WHEN NOT ON_TIME_FLAG THEN 0 END)
      WITH SYNONYMS = ('OTD', 'on-time rate')
      COMMENT = 'Delivered lines that arrived on or before the promised date (Standard 6 days, Expedited 3, Next Day 2) / all delivered lines.',
    sales.returned_sales AS SUM(RETURNED_SALES) COMMENT = 'Net sales value of items returned so far (USD).',
    sales.returned_units AS SUM(RETURNED_UNITS) COMMENT = 'Units returned so far.',
    sales.return_rate AS SUM(RETURNED_SALES) / NULLIF(SUM(NET_SALES), 0) WITH SYNONYMS = ('returns %')
      COMMENT = 'Returned sales / net sales for orders placed in the period. Recent periods rise as returns arrive.',
    sales.net_sales_after_returns AS SUM(NET_SALES - RETURNED_SALES) COMMENT = 'Net sales less returns (USD).',
    inventory.avg_units_on_hand AS SUM(UNITS_ON_HAND) / NULLIF(COUNT(DISTINCT SNAPSHOT_DATE), 0)
      WITH SYNONYMS = ('units on hand', 'inventory units', 'stock on hand')
      COMMENT = 'Average daily end-of-day units on hand: stock is summed across the selected SKUs and DCs, then averaged over days (stock is never added up across days).',
    inventory.avg_inventory_value AS SUM(INVENTORY_VALUE) / NULLIF(COUNT(DISTINCT SNAPSHOT_DATE), 0)
      WITH SYNONYMS = ('inventory value', 'stock value') COMMENT = 'Average daily inventory value at cost (USD).',
    inventory.avg_units_on_order AS SUM(UNITS_ON_ORDER) / NULLIF(COUNT(DISTINCT SNAPSHOT_DATE), 0)
      WITH SYNONYMS = ('on order', 'open PO units') COMMENT = 'Average daily units on open replenishment orders.',
    inventory.units_sold_from_stock AS SUM(UNITS_SOLD) COMMENT = 'Units fulfilled from DC stock (equals units sold for the same slice).',
    inventory.lost_sales_units AS SUM(LOST_UNITS) WITH SYNONYMS = ('lost sales', 'unmet demand')
      COMMENT = 'Units customers wanted that could not be fulfilled because the DC was out of stock.',
    inventory.stockout_rate AS AVG(IFF(STOCKOUT_FLAG, 1, 0)) WITH SYNONYMS = ('out of stock %', 'OOS rate')
      COMMENT = 'Share of SKU x DC x day records ending with zero units on hand.',
    inventory.in_stock_rate AS 1 - AVG(IFF(STOCKOUT_FLAG, 1, 0)) WITH SYNONYMS = ('in-stock %', 'availability')
      COMMENT = 'Share of SKU x DC x day records ending with stock available.',
    inventory.weeks_of_supply AS SUM(UNITS_ON_HAND) / NULLIF(7 * SUM(UNITS_SOLD), 0) WITH SYNONYMS = ('WOS', 'weeks of cover')
      COMMENT = 'Average units on hand / average weekly units sold.',
    inventory.sell_through_pct AS SUM(UNITS_SOLD) / NULLIF(SUM(UNITS_SOLD) + SUM(UNITS_ON_HAND) / NULLIF(COUNT(DISTINCT SNAPSHOT_DATE), 0), 0)
      WITH SYNONYMS = ('sell-through', 'sell thru')
      COMMENT = 'Units sold / (units sold + average daily units on hand) for the period.',
    plan.plan_net_sales AS SUM(PLAN_NET_SALES) WITH SYNONYMS = ('sales plan', 'sales target', 'budget')
      COMMENT = 'Planned net sales (USD).',
    plan.plan_units AS SUM(PLAN_UNITS) WITH SYNONYMS = ('unit plan') COMMENT = 'Planned units.',
    plan.plan_gross_margin AS SUM(PLAN_GROSS_MARGIN) WITH SYNONYMS = ('margin plan') COMMENT = 'Planned gross margin (USD).'
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
