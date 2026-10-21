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
