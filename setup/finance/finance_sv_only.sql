-- =====================================================================================
-- Keystone Financial (fictional) - Step 2: rolling-date views (the semantic view's sources)
-- The pack's data is frozen at the week of 2026-09-14. These views move every row forward by
-- whole weeks so the newest week is always the LAST FULL WEEK (Mon-Sun) before today. Weekly
-- shapes and the planted stories ("last 15 / 18 / 22 weeks") are unchanged.
-- Columns are prefixed C_ because Snowflake resolves bare names in semantic expressions to
-- semantic objects first (a column named like a metric would create a cycle).
-- Each week is dated by its WEEK ENDING (Sunday): a week counts as complete as soon as it is in
-- the data, and it belongs to the month it ends in.
-- =====================================================================================
USE ROLE WBR_OWNER;
USE WAREHOUSE POWERHOUSE;
USE SCHEMA WBR_DB.FINANCE_DEMO;

CREATE OR REPLACE VIEW V_WEEK_SHIFT
  COMMENT = 'Whole weeks added to the pack dates so the newest week is the last full Mon-Sun week'
AS
SELECT GREATEST(0, FLOOR(DATEDIFF('day',
         (SELECT MAX(WEEK_START_DATE) FROM WBR_DB.FINANCE_DEMO.FINANCE_FACT_PORTFOLIO_WEEK),
         DATEADD('day', -(DAYOFWEEKISO(CURRENT_DATE()) - 1) - 7, CURRENT_DATE())) / 7))::INT AS SHIFT_WEEKS;

CREATE OR REPLACE VIEW SV_SRC_WEEKS COMMENT = 'Calendar of the weekly data (rolling)' AS
WITH w AS (
  SELECT DISTINCT DATEADD('day', 7 * s.SHIFT_WEEKS + 6, f.WEEK_START_DATE) AS WE
  FROM WBR_DB.FINANCE_DEMO.FINANCE_FACT_PORTFOLIO_WEEK f CROSS JOIN WBR_DB.FINANCE_DEMO.V_WEEK_SHIFT s)
SELECT WE AS C_WEEK_ENDING,
       DATEADD('day', -6, WE) AS C_WEEK_START,
       DATE_TRUNC('month', WE) AS C_MONTH_START,
       TO_CHAR(WE, 'Mon YYYY') AS C_MONTH_NAME,
       YEAR(WE) || '-Q' || QUARTER(WE) AS C_QUARTER,
       YEAR(WE) AS C_YEAR,
       WEEKISO(DATEADD('day', -6, WE)) AS C_WEEK_OF_YEAR
FROM w;

CREATE OR REPLACE VIEW SV_SRC_PRODUCT AS
SELECT PRODUCT_ID AS C_PRODUCT_ID, PRODUCT_NAME AS C_PRODUCT_NAME, PRODUCT_TYPE AS C_PRODUCT_TYPE, TIER AS C_TIER,
       AVG_APR_PCT / 100 AS C_LIST_APR
FROM WBR_DB.FINANCE_DEMO.FINANCE_DIM_PRODUCT;

CREATE OR REPLACE VIEW SV_SRC_SEGMENT AS
SELECT SEGMENT_ID AS C_SEGMENT_ID, SEGMENT_NAME AS C_SEGMENT_NAME, DESCRIPTION AS C_SEGMENT_DESCRIPTION,
       CASE WHEN AVG_FICO >= 740 THEN 'Prime (740+)' WHEN AVG_FICO >= 660 THEN 'Near-prime (660-739)'
            ELSE 'Subprime (<660)' END AS C_CREDIT_TIER
FROM WBR_DB.FINANCE_DEMO.FINANCE_DIM_SEGMENT;

-- Portfolio: every product (cards and deposits) x segment x week. Balances are stocks.
CREATE OR REPLACE VIEW SV_SRC_PORTFOLIO AS
SELECT DATEADD('day', 7 * s.SHIFT_WEEKS + 6, f.WEEK_START_DATE) AS C_WEEK_ENDING,
       f.PRODUCT_ID AS C_PRODUCT_ID, f.SEGMENT_ID AS C_SEGMENT_ID,
       f.ENDING_BALANCE AS C_ENDING_BALANCE,
       IFF(p.PRODUCT_TYPE = 'Credit Card', f.ENDING_BALANCE, 0) AS C_CARD_BALANCE,
       f.ENDING_BALANCE * f.REVOLVE_RATE_PCT / 100 AS C_REVOLVING_BALANCE,
       f.NEW_ACCOUNTS AS C_NEW_ACCOUNTS, f.CLOSED_ACCOUNTS AS C_CLOSED_ACCOUNTS, f.ACTIVE_ACCOUNTS AS C_ACTIVE_ACCOUNTS,
       f.PURCHASE_VOLUME AS C_PURCHASE_VOLUME, f.INTERCHANGE_REVENUE AS C_INTERCHANGE_REVENUE,
       f.REWARDS_EXPENSE AS C_REWARDS_EXPENSE, f.NET_INTEREST_INCOME AS C_NET_INTEREST_INCOME,
       f.COST_OF_FUNDS_DOLLARS AS C_COST_OF_FUNDS
FROM WBR_DB.FINANCE_DEMO.FINANCE_FACT_PORTFOLIO_WEEK f
JOIN WBR_DB.FINANCE_DEMO.FINANCE_DIM_PRODUCT p ON p.PRODUCT_ID = f.PRODUCT_ID
CROSS JOIN WBR_DB.FINANCE_DEMO.V_WEEK_SHIFT s;

-- Credit: card products only. The card balance of the same product x segment x week is carried
-- in, so delinquency and loss rates divide by CARD balances only (never deposits).
CREATE OR REPLACE VIEW SV_SRC_CREDIT AS
SELECT DATEADD('day', 7 * s.SHIFT_WEEKS + 6, c.WEEK_START_DATE) AS C_WEEK_ENDING,
       c.PRODUCT_ID AS C_PRODUCT_ID, c.SEGMENT_ID AS C_SEGMENT_ID,
       c.DPD_30_BALANCE AS C_DPD_30_BALANCE, c.DPD_60_BALANCE AS C_DPD_60_BALANCE, c.DPD_90_BALANCE AS C_DPD_90_BALANCE,
       c.GROSS_CHARGEOFF_DOLLARS AS C_GROSS_CHARGEOFFS, c.RECOVERY_DOLLARS AS C_RECOVERIES,
       c.NET_CHARGEOFF_DOLLARS AS C_NET_CHARGEOFFS,
       f.ENDING_BALANCE AS C_CARD_BALANCE,
       c.AVG_FICO * f.ENDING_BALANCE AS C_FICO_X_BALANCE,
       f.NET_INTEREST_INCOME + f.INTERCHANGE_REVENUE - f.REWARDS_EXPENSE AS C_CARD_REVENUE
FROM WBR_DB.FINANCE_DEMO.FINANCE_FACT_CREDIT_WEEK c
JOIN WBR_DB.FINANCE_DEMO.FINANCE_FACT_PORTFOLIO_WEEK f
  ON f.WEEK_START_DATE = c.WEEK_START_DATE AND f.PRODUCT_ID = c.PRODUCT_ID AND f.SEGMENT_ID = c.SEGMENT_ID
CROSS JOIN WBR_DB.FINANCE_DEMO.V_WEEK_SHIFT s;

-- Deposits: deposit products only. Rates become fractions; balance-weighted helpers so rates
-- are never plain-averaged. rate gap = competitor rate - rate paid (POSITIVE = we pay less).
CREATE OR REPLACE VIEW SV_SRC_DEPOSITS AS
SELECT DATEADD('day', 7 * s.SHIFT_WEEKS + 6, d.WEEK_START_DATE) AS C_WEEK_ENDING,
       d.PRODUCT_ID AS C_PRODUCT_ID, d.SEGMENT_ID AS C_SEGMENT_ID,
       d.DEPOSIT_BALANCE AS C_DEPOSIT_BALANCE, d.RUNOFF_DOLLARS AS C_RUNOFF, d.MATURING_DOLLARS AS C_MATURING,
       d.NEW_MONEY_DOLLARS AS C_NEW_MONEY,
       d.RATE_PAID_PCT / 100 * d.DEPOSIT_BALANCE AS C_RATE_PAID_X_BALANCE,
       d.COMPETITOR_RATE_PCT / 100 * d.DEPOSIT_BALANCE AS C_COMPETITOR_RATE_X_BALANCE,
       d.RATE_GAP_PCT / 100 * d.DEPOSIT_BALANCE AS C_RATE_GAP_X_BALANCE
FROM WBR_DB.FINANCE_DEMO.FINANCE_FACT_DEPOSITS_WEEK d
CROSS JOIN WBR_DB.FINANCE_DEMO.V_WEEK_SHIFT s;

-- Acquisition: product x marketing channel x week.
CREATE OR REPLACE VIEW SV_SRC_ACQUISITION AS
SELECT DATEADD('day', 7 * s.SHIFT_WEEKS + 6, a.WEEK_START_DATE) AS C_WEEK_ENDING,
       a.PRODUCT_ID AS C_PRODUCT_ID, a.CHANNEL AS C_CHANNEL,
       a.MARKETING_SPEND AS C_MARKETING_SPEND, a.APPLICATIONS AS C_APPLICATIONS, a.APPROVALS AS C_APPROVALS,
       a.BOOKINGS AS C_BOOKINGS, a.AVG_INITIAL_CREDIT_LINE * a.BOOKINGS AS C_CREDIT_LINE_X_BOOKINGS
FROM WBR_DB.FINANCE_DEMO.FINANCE_FACT_ACQUISITION_WEEK a
CROSS JOIN WBR_DB.FINANCE_DEMO.V_WEEK_SHIFT s;

SELECT SHIFT_WEEKS, (SELECT MIN(C_WEEK_ENDING) FROM SV_SRC_WEEKS) AS FIRST_WEEK_ENDING,
       (SELECT MAX(C_WEEK_ENDING) FROM SV_SRC_WEEKS) AS LAST_WEEK_ENDING, CURRENT_DATE() AS TODAY
FROM V_WEEK_SHIFT;
-- =====================================================================================
-- Keystone Financial (fictional) - Step 3: FINANCE_ANALYTICS_SV (generated by build_finance_sv.py)
-- Created from the richest definition this account supports: 1) end-of-week stocks + AI instructions,
-- 2) end-of-week stocks without AI instructions, 3) without the end-of-week stock metrics.
-- =====================================================================================
USE ROLE WBR_OWNER;
USE WAREHOUSE POWERHOUSE;
USE SCHEMA WBR_DB.FINANCE_DEMO;
CREATE OR REPLACE TABLE SV_DDL (ATTEMPT NUMBER, NAME VARCHAR, DDL VARCHAR);
INSERT INTO SV_DDL VALUES (1, 'full: end-of-week stocks + AI instructions', $$CREATE OR REPLACE SEMANTIC VIEW WBR_DB.FINANCE_DEMO.FINANCE_ANALYTICS_SV
  TABLES (
    weeks AS WBR_DB.FINANCE_DEMO.SV_SRC_WEEKS PRIMARY KEY (C_WEEK_ENDING)
      WITH SYNONYMS ('calendar', 'week') COMMENT = 'Weekly calendar. Every row covers Monday to Sunday and is dated by the Sunday the week ends; a week belongs to the month it ends in.',
    products AS WBR_DB.FINANCE_DEMO.SV_SRC_PRODUCT PRIMARY KEY (C_PRODUCT_ID)
      WITH SYNONYMS ('product', 'card', 'account type') COMMENT = 'Six products: four credit cards (Cash Rewards, Travel Signature, Secured, Small Business) and two deposit products (High-Yield Savings, 12-Month CD).',
    segments AS WBR_DB.FINANCE_DEMO.SV_SRC_SEGMENT PRIMARY KEY (C_SEGMENT_ID)
      WITH SYNONYMS ('customer segment', 'behavioural segment') COMMENT = 'Six behavioural segments crossing credit quality and product usage.',
    portfolio AS WBR_DB.FINANCE_DEMO.SV_SRC_PORTFOLIO PRIMARY KEY (C_WEEK_ENDING, C_PRODUCT_ID, C_SEGMENT_ID)
      WITH SYNONYMS ('book', 'balances', 'portfolio performance')
      COMMENT = 'Weekly balances, accounts, card spend and economics for every product (cards and deposits) and segment.',
    credit AS WBR_DB.FINANCE_DEMO.SV_SRC_CREDIT PRIMARY KEY (C_WEEK_ENDING, C_PRODUCT_ID, C_SEGMENT_ID)
      WITH SYNONYMS ('credit risk', 'delinquency', 'losses')
      COMMENT = 'Weekly credit performance of CREDIT CARD products only: past-due balances, charge-offs, recoveries, FICO.',
    deposits AS WBR_DB.FINANCE_DEMO.SV_SRC_DEPOSITS PRIMARY KEY (C_WEEK_ENDING, C_PRODUCT_ID, C_SEGMENT_ID)
      WITH SYNONYMS ('savings', 'CDs', 'deposit book')
      COMMENT = 'Weekly retail deposit balances, flows and pricing for DEPOSIT products only.',
    acquisition AS WBR_DB.FINANCE_DEMO.SV_SRC_ACQUISITION PRIMARY KEY (C_WEEK_ENDING, C_PRODUCT_ID, C_CHANNEL)
      WITH SYNONYMS ('marketing', 'new account acquisition', 'funnel')
      COMMENT = 'Weekly acquisition funnel by product and marketing channel: spend, applications, approvals, bookings.'
  )
  RELATIONSHIPS (
    portfolio_to_weeks AS portfolio (C_WEEK_ENDING) REFERENCES weeks,
    portfolio_to_products AS portfolio (C_PRODUCT_ID) REFERENCES products,
    portfolio_to_segments AS portfolio (C_SEGMENT_ID) REFERENCES segments,
    credit_to_weeks AS credit (C_WEEK_ENDING) REFERENCES weeks,
    credit_to_products AS credit (C_PRODUCT_ID) REFERENCES products,
    credit_to_segments AS credit (C_SEGMENT_ID) REFERENCES segments,
    deposits_to_weeks AS deposits (C_WEEK_ENDING) REFERENCES weeks,
    deposits_to_products AS deposits (C_PRODUCT_ID) REFERENCES products,
    deposits_to_segments AS deposits (C_SEGMENT_ID) REFERENCES segments,
    acquisition_to_weeks AS acquisition (C_WEEK_ENDING) REFERENCES weeks,
    acquisition_to_products AS acquisition (C_PRODUCT_ID) REFERENCES products
  )
  FACTS (
    portfolio.f_week AS C_WEEK_ENDING,
    portfolio.f_ending_balance AS C_ENDING_BALANCE,
    portfolio.f_card_balance AS C_CARD_BALANCE,
    portfolio.f_revolving_balance AS C_REVOLVING_BALANCE,
    portfolio.f_new_accounts AS C_NEW_ACCOUNTS,
    portfolio.f_closed_accounts AS C_CLOSED_ACCOUNTS,
    portfolio.f_active_accounts AS C_ACTIVE_ACCOUNTS,
    portfolio.f_purchase_volume AS C_PURCHASE_VOLUME,
    portfolio.f_interchange_revenue AS C_INTERCHANGE_REVENUE,
    portfolio.f_rewards_expense AS C_REWARDS_EXPENSE,
    portfolio.f_net_interest_income AS C_NET_INTEREST_INCOME,
    portfolio.f_cost_of_funds AS C_COST_OF_FUNDS,
    credit.f_dpd_30_balance AS C_DPD_30_BALANCE,
    credit.f_dpd_60_balance AS C_DPD_60_BALANCE,
    credit.f_dpd_90_balance AS C_DPD_90_BALANCE,
    credit.f_gross_chargeoffs AS C_GROSS_CHARGEOFFS,
    credit.f_recoveries AS C_RECOVERIES,
    credit.f_net_chargeoffs AS C_NET_CHARGEOFFS,
    credit.f_card_balance AS C_CARD_BALANCE,
    credit.f_fico_x_balance AS C_FICO_X_BALANCE,
    credit.f_card_revenue AS C_CARD_REVENUE,
    deposits.f_deposit_balance AS C_DEPOSIT_BALANCE,
    deposits.f_runoff AS C_RUNOFF,
    deposits.f_maturing AS C_MATURING,
    deposits.f_new_money AS C_NEW_MONEY,
    deposits.f_rate_paid_x_balance AS C_RATE_PAID_X_BALANCE,
    deposits.f_competitor_rate_x_balance AS C_COMPETITOR_RATE_X_BALANCE,
    deposits.f_rate_gap_x_balance AS C_RATE_GAP_X_BALANCE,
    acquisition.f_marketing_spend AS C_MARKETING_SPEND,
    acquisition.f_applications AS C_APPLICATIONS,
    acquisition.f_approvals AS C_APPROVALS,
    acquisition.f_bookings AS C_BOOKINGS,
    acquisition.f_credit_line_x_bookings AS C_CREDIT_LINE_X_BOOKINGS
  )
  DIMENSIONS (
    weeks.week_ending AS C_WEEK_ENDING WITH SYNONYMS = ('week', 'week ending', 'date')
      COMMENT = 'Sunday that ends the week. Use for all time filtering; the newest week is the last full week.',
    weeks.week_start AS C_WEEK_START COMMENT = 'Monday that starts the week.',
    weeks.month_start AS C_MONTH_START WITH SYNONYMS = ('month') COMMENT = 'First day of the month the week ends in.',
    weeks.month_name AS C_MONTH_NAME COMMENT = 'Month label, e.g. Oct 2026.',
    weeks.calendar_quarter AS C_QUARTER WITH SYNONYMS = ('fiscal quarter') COMMENT = 'Calendar quarter, e.g. 2026-Q3.',
    weeks.calendar_year AS C_YEAR WITH SYNONYMS = ('fiscal year') COMMENT = 'Calendar (= fiscal) year.',
    weeks.week_of_year AS C_WEEK_OF_YEAR COMMENT = 'ISO week number.',
    products.product_name AS C_PRODUCT_NAME WITH SYNONYMS = ('product', 'card product', 'deposit product')
      COMMENT = 'Product name, e.g. Keystone Travel Signature Card.',
    products.product_type AS C_PRODUCT_TYPE WITH SYNONYMS = ('business line', 'line of business')
      COMMENT = 'Credit Card or Deposit.',
    products.tier AS C_TIER WITH SYNONYMS = ('product tier') COMMENT = 'Mainstream, Premium, Subprime or Business.',
    segments.segment_name AS C_SEGMENT_NAME WITH SYNONYMS = ('segment', 'customer segment')
      COMMENT = 'Behavioural segment, e.g. Near-Prime Revolver, Mass Affluent Saver.',
    segments.credit_tier AS C_CREDIT_TIER WITH SYNONYMS = ('FICO band', 'credit band')
      COMMENT = 'Prime (740+), Near-prime (660-739) or Subprime (<660), from the segment average FICO.',
    segments.segment_description AS C_SEGMENT_DESCRIPTION COMMENT = 'What characterises the segment.',
    acquisition.channel AS C_CHANNEL WITH SYNONYMS = ('marketing channel', 'acquisition channel')
      COMMENT = 'Acquisition channel, e.g. Direct Mail, Digital Paid, Branch.'
  )
  METRICS (
    portfolio.ending_balance NON ADDITIVE BY (weeks.week_ending) AS SUM(portfolio.f_ending_balance) WITH SYNONYMS = ('balance', 'balances', 'managed balances', 'outstandings')
      COMMENT = 'Balance at the end of the latest week in the period (cards + deposits unless filtered). A stock: never summed across weeks.',
    portfolio.active_accounts NON ADDITIVE BY (weeks.week_ending) AS SUM(portfolio.f_active_accounts) WITH SYNONYMS = ('accounts', 'open accounts')
      COMMENT = 'Active accounts at the end of the latest week in the period.',
    portfolio.helper_weeks AS COUNT(DISTINCT portfolio.f_week) COMMENT = 'Helper: weeks in the period.',
    portfolio.helper_balance_weeks AS SUM(portfolio.f_ending_balance) COMMENT = 'Helper: weekly balances summed over weeks.',
    portfolio.helper_card_balance_weeks AS SUM(portfolio.f_card_balance) COMMENT = 'Helper: weekly card balances summed over weeks.',
    portfolio.helper_active_weeks AS SUM(portfolio.f_active_accounts) COMMENT = 'Helper: weekly active accounts summed over weeks.',
    portfolio.average_balance AS DIV0(portfolio.helper_balance_weeks, portfolio.helper_weeks) WITH SYNONYMS = ('average balances')
      COMMENT = 'Average weekly ending balance over the period.',
    portfolio.new_accounts AS SUM(portfolio.f_new_accounts) WITH SYNONYMS = ('new accounts opened', 'account openings')
      COMMENT = 'Accounts opened in the period.',
    portfolio.closed_accounts AS SUM(portfolio.f_closed_accounts) COMMENT = 'Accounts closed in the period.',
    portfolio.attrition_rate AS DIV0(portfolio.closed_accounts * 52, portfolio.helper_active_weeks) WITH SYNONYMS = ('attrition', 'churn rate')
      COMMENT = 'Annualised account attrition: closed accounts / active accounts, x 52 weeks.',
    portfolio.purchase_volume AS SUM(portfolio.f_purchase_volume) WITH SYNONYMS = ('card spend', 'spend volume', 'purchases')
      COMMENT = 'Card purchase volume (USD).',
    portfolio.interchange_revenue AS SUM(portfolio.f_interchange_revenue) WITH SYNONYMS = ('interchange')
      COMMENT = 'Interchange fees earned on card spend (USD).',
    portfolio.rewards_expense AS SUM(portfolio.f_rewards_expense) WITH SYNONYMS = ('rewards cost', 'rewards')
      COMMENT = 'Cost of card rewards (USD).',
    portfolio.rewards_to_interchange_ratio AS DIV0(portfolio.rewards_expense, portfolio.interchange_revenue)
      WITH SYNONYMS = ('rewards to interchange', 'rewards ratio')
      COMMENT = 'Rewards expense / interchange revenue. Healthy below 0.80; above 0.85 is a profitability breach.',
    portfolio.net_interest_income AS SUM(portfolio.f_net_interest_income) WITH SYNONYMS = ('NII', 'interest income')
      COMMENT = 'Net interest income (USD).',
    portfolio.cost_of_funds AS SUM(portfolio.f_cost_of_funds) WITH SYNONYMS = ('funding cost')
      COMMENT = 'Cost of funds (USD).',
    portfolio.net_interest_margin_pct AS DIV0((portfolio.net_interest_income - portfolio.cost_of_funds) * 52, portfolio.helper_balance_weeks)
      WITH SYNONYMS = ('NIM', 'net interest margin')
      COMMENT = 'Annualised (net interest income - cost of funds) / average balance.',
    portfolio.cost_of_funds_rate AS DIV0(portfolio.cost_of_funds * 52, portfolio.helper_balance_weeks)
      COMMENT = 'Annualised cost of funds / average balance.',
    portfolio.helper_revolving_weeks AS SUM(portfolio.f_revolving_balance) COMMENT = 'Helper: weekly revolving balances summed over weeks.',
    portfolio.revolve_rate AS DIV0(portfolio.helper_revolving_weeks, portfolio.helper_balance_weeks)
      WITH SYNONYMS = ('revolving share') COMMENT = 'Share of balance carrying interest (balance-weighted).',
    credit.dpd_30_balance NON ADDITIVE BY (weeks.week_ending) AS SUM(credit.f_dpd_30_balance) WITH SYNONYMS = ('30 days past due', '30+ DPD balance')
      COMMENT = 'Card balance 30+ days past due at the end of the latest week in the period.',
    credit.dpd_60_balance NON ADDITIVE BY (weeks.week_ending) AS SUM(credit.f_dpd_60_balance) WITH SYNONYMS = ('60 days past due')
      COMMENT = 'Card balance 60+ days past due at the end of the latest week in the period.',
    credit.dpd_90_balance NON ADDITIVE BY (weeks.week_ending) AS SUM(credit.f_dpd_90_balance) WITH SYNONYMS = ('90 days past due')
      COMMENT = 'Card balance 90+ days past due at the end of the latest week in the period.',
    credit.helper_dpd_30_weeks AS SUM(credit.f_dpd_30_balance) COMMENT = 'Helper: weekly 30+ DPD balances summed over weeks.',
    credit.helper_credit_card_balance_weeks AS SUM(credit.f_card_balance) COMMENT = 'Helper: weekly card balances summed over weeks.',
    credit.delinquency_rate AS DIV0(credit.helper_dpd_30_weeks, credit.helper_credit_card_balance_weeks)
      WITH SYNONYMS = ('delinquency', '30+ delinquency rate', 'past due rate')
      COMMENT = '30+ days past due balance / card balance (cards only; average over the weeks in the period).',
    credit.gross_chargeoffs AS SUM(credit.f_gross_chargeoffs) WITH SYNONYMS = ('gross charge-offs', 'gross losses')
      COMMENT = 'Gross charge-offs (USD).',
    credit.recoveries AS SUM(credit.f_recoveries) COMMENT = 'Recoveries on charged-off accounts (USD).',
    credit.net_chargeoffs AS SUM(credit.f_net_chargeoffs) WITH SYNONYMS = ('net charge-offs', 'NCO', 'net losses')
      COMMENT = 'Gross charge-offs minus recoveries (USD).',
    credit.annualized_loss_rate AS DIV0(credit.net_chargeoffs * 52, credit.helper_credit_card_balance_weeks)
      WITH SYNONYMS = ('loss rate', 'net charge-off rate', 'NCO rate')
      COMMENT = 'Annualised net charge-offs / average card balance.',
    credit.recovery_rate AS DIV0(credit.recoveries, credit.gross_chargeoffs) COMMENT = 'Recoveries / gross charge-offs.',
    credit.card_revenue AS SUM(credit.f_card_revenue) WITH SYNONYMS = ('card revenue')
      COMMENT = 'Card net interest income + interchange - rewards (USD), before funding cost and losses.',
    credit.risk_adjusted_yield AS DIV0((credit.card_revenue - credit.net_chargeoffs) * 52, credit.helper_credit_card_balance_weeks)
      WITH SYNONYMS = ('risk adjusted yield', 'risk-adjusted margin', 'yield after losses')
      COMMENT = 'Annualised (card revenue - net charge-offs) / average card balance. Below zero the segment loses money after losses.',
    credit.helper_fico_x_balance AS SUM(credit.f_fico_x_balance) COMMENT = 'Helper: FICO x card balance summed.',
    credit.average_fico AS DIV0(credit.helper_fico_x_balance, credit.helper_credit_card_balance_weeks)
      WITH SYNONYMS = ('FICO', 'credit score') COMMENT = 'Balance-weighted average FICO score of card customers.',
    deposits.deposit_balance NON ADDITIVE BY (weeks.week_ending) AS SUM(deposits.f_deposit_balance) WITH SYNONYMS = ('deposits', 'deposit balances', 'savings balance')
      COMMENT = 'Deposit balance at the end of the latest week in the period.',
    deposits.helper_deposit_balance_weeks AS SUM(deposits.f_deposit_balance) COMMENT = 'Helper: weekly deposit balances summed over weeks.',
    deposits.runoff AS SUM(deposits.f_runoff) WITH SYNONYMS = ('deposit runoff', 'outflows', 'withdrawals')
      COMMENT = 'Deposit balances that left the bank (USD).',
    deposits.new_money AS SUM(deposits.f_new_money) WITH SYNONYMS = ('inflows', 'new deposits') COMMENT = 'New deposit money (USD).',
    deposits.net_new_money AS deposits.new_money - deposits.runoff WITH SYNONYMS = ('net flows', 'net deposit flows')
      COMMENT = 'New money minus runoff (USD).',
    deposits.maturing_dollars AS SUM(deposits.f_maturing) WITH SYNONYMS = ('CD maturities', 'maturing balances')
      COMMENT = 'CD balances reaching maturity (USD).',
    deposits.runoff_rate AS DIV0(deposits.runoff * 52, deposits.helper_deposit_balance_weeks)
      WITH SYNONYMS = ('deposit runoff rate', 'attrition of deposits') COMMENT = 'Annualised runoff / average deposit balance.',
    deposits.maturity_concentration AS DIV0(deposits.maturing_dollars, deposits.helper_deposit_balance_weeks)
      COMMENT = 'Maturing dollars / deposit balance (average week in the period).',
    deposits.helper_rate_paid_x_balance AS SUM(deposits.f_rate_paid_x_balance) COMMENT = 'Helper: rate paid x balance summed.',
    deposits.helper_competitor_x_balance AS SUM(deposits.f_competitor_rate_x_balance) COMMENT = 'Helper: competitor rate x balance summed.',
    deposits.helper_rate_gap_x_balance AS SUM(deposits.f_rate_gap_x_balance) COMMENT = 'Helper: rate gap x balance summed.',
    deposits.rate_paid AS DIV0(deposits.helper_rate_paid_x_balance, deposits.helper_deposit_balance_weeks)
      WITH SYNONYMS = ('APY', 'deposit rate') COMMENT = 'Balance-weighted rate (APY) paid to depositors.',
    deposits.competitor_rate AS DIV0(deposits.helper_competitor_x_balance, deposits.helper_deposit_balance_weeks)
      WITH SYNONYMS = ('market rate') COMMENT = 'Balance-weighted competitor rate for the same products.',
    deposits.rate_gap AS DIV0(deposits.helper_rate_gap_x_balance, deposits.helper_deposit_balance_weeks)
      WITH SYNONYMS = ('rate gap to competitors', 'pricing gap')
      COMMENT = 'Competitor rate minus rate paid (balance-weighted). POSITIVE means competitors pay more than Keystone: balances are at risk.',
    acquisition.marketing_spend AS SUM(acquisition.f_marketing_spend) WITH SYNONYMS = ('acquisition spend', 'marketing cost')
      COMMENT = 'Acquisition marketing spend (USD).',
    acquisition.applications AS SUM(acquisition.f_applications) WITH SYNONYMS = ('apps') COMMENT = 'Applications received.',
    acquisition.approvals AS SUM(acquisition.f_approvals) COMMENT = 'Applications approved.',
    acquisition.bookings AS SUM(acquisition.f_bookings) WITH SYNONYMS = ('booked accounts') COMMENT = 'Approved applications that opened an account.',
    acquisition.approval_rate AS DIV0(acquisition.approvals, acquisition.applications) COMMENT = 'Approvals / applications.',
    acquisition.booking_rate AS DIV0(acquisition.bookings, acquisition.approvals) COMMENT = 'Bookings / approvals.',
    acquisition.cost_per_booking AS DIV0(acquisition.marketing_spend, acquisition.bookings) WITH SYNONYMS = ('CAC', 'customer acquisition cost')
      COMMENT = 'Marketing spend / bookings (USD).',
    acquisition.helper_credit_line_x_bookings AS SUM(acquisition.f_credit_line_x_bookings) COMMENT = 'Helper: initial line x bookings summed.',
    acquisition.average_initial_credit_line AS DIV0(acquisition.helper_credit_line_x_bookings, acquisition.bookings)
      WITH SYNONYMS = ('initial line') COMMENT = 'Booking-weighted average initial credit line (USD).'
  )
  COMMENT = 'Keystone Financial (fictional US consumer bank): card and deposit portfolio, credit risk, deposit pricing and acquisition. Weekly, rolling to the last full week.'
  AI_SQL_GENERATION 'Keystone Financial is a fictional consumer bank. Data is weekly; weeks run Monday to Sunday and are dated by week_ending; filter time on weeks.week_ending. Credit metrics (delinquency, charge-offs, loss rate, FICO) apply to credit card products only; deposit metrics to deposit products only; never add them together. Balances, active accounts and past-due balances are end-of-week stocks: never sum them across weeks. Rates are fractions and already weighted; never average a rate. Annualise weekly flows with x 52. rate_gap = competitor rate - rate paid: a POSITIVE gap means competitors pay more and deposits are at risk. Portfolio-level loss rates can hide one segment deteriorating: check segment detail.'$$);
INSERT INTO SV_DDL VALUES (2, 'end-of-week stocks, no AI instructions', $$CREATE OR REPLACE SEMANTIC VIEW WBR_DB.FINANCE_DEMO.FINANCE_ANALYTICS_SV
  TABLES (
    weeks AS WBR_DB.FINANCE_DEMO.SV_SRC_WEEKS PRIMARY KEY (C_WEEK_ENDING)
      WITH SYNONYMS ('calendar', 'week') COMMENT = 'Weekly calendar. Every row covers Monday to Sunday and is dated by the Sunday the week ends; a week belongs to the month it ends in.',
    products AS WBR_DB.FINANCE_DEMO.SV_SRC_PRODUCT PRIMARY KEY (C_PRODUCT_ID)
      WITH SYNONYMS ('product', 'card', 'account type') COMMENT = 'Six products: four credit cards (Cash Rewards, Travel Signature, Secured, Small Business) and two deposit products (High-Yield Savings, 12-Month CD).',
    segments AS WBR_DB.FINANCE_DEMO.SV_SRC_SEGMENT PRIMARY KEY (C_SEGMENT_ID)
      WITH SYNONYMS ('customer segment', 'behavioural segment') COMMENT = 'Six behavioural segments crossing credit quality and product usage.',
    portfolio AS WBR_DB.FINANCE_DEMO.SV_SRC_PORTFOLIO PRIMARY KEY (C_WEEK_ENDING, C_PRODUCT_ID, C_SEGMENT_ID)
      WITH SYNONYMS ('book', 'balances', 'portfolio performance')
      COMMENT = 'Weekly balances, accounts, card spend and economics for every product (cards and deposits) and segment.',
    credit AS WBR_DB.FINANCE_DEMO.SV_SRC_CREDIT PRIMARY KEY (C_WEEK_ENDING, C_PRODUCT_ID, C_SEGMENT_ID)
      WITH SYNONYMS ('credit risk', 'delinquency', 'losses')
      COMMENT = 'Weekly credit performance of CREDIT CARD products only: past-due balances, charge-offs, recoveries, FICO.',
    deposits AS WBR_DB.FINANCE_DEMO.SV_SRC_DEPOSITS PRIMARY KEY (C_WEEK_ENDING, C_PRODUCT_ID, C_SEGMENT_ID)
      WITH SYNONYMS ('savings', 'CDs', 'deposit book')
      COMMENT = 'Weekly retail deposit balances, flows and pricing for DEPOSIT products only.',
    acquisition AS WBR_DB.FINANCE_DEMO.SV_SRC_ACQUISITION PRIMARY KEY (C_WEEK_ENDING, C_PRODUCT_ID, C_CHANNEL)
      WITH SYNONYMS ('marketing', 'new account acquisition', 'funnel')
      COMMENT = 'Weekly acquisition funnel by product and marketing channel: spend, applications, approvals, bookings.'
  )
  RELATIONSHIPS (
    portfolio_to_weeks AS portfolio (C_WEEK_ENDING) REFERENCES weeks,
    portfolio_to_products AS portfolio (C_PRODUCT_ID) REFERENCES products,
    portfolio_to_segments AS portfolio (C_SEGMENT_ID) REFERENCES segments,
    credit_to_weeks AS credit (C_WEEK_ENDING) REFERENCES weeks,
    credit_to_products AS credit (C_PRODUCT_ID) REFERENCES products,
    credit_to_segments AS credit (C_SEGMENT_ID) REFERENCES segments,
    deposits_to_weeks AS deposits (C_WEEK_ENDING) REFERENCES weeks,
    deposits_to_products AS deposits (C_PRODUCT_ID) REFERENCES products,
    deposits_to_segments AS deposits (C_SEGMENT_ID) REFERENCES segments,
    acquisition_to_weeks AS acquisition (C_WEEK_ENDING) REFERENCES weeks,
    acquisition_to_products AS acquisition (C_PRODUCT_ID) REFERENCES products
  )
  FACTS (
    portfolio.f_week AS C_WEEK_ENDING,
    portfolio.f_ending_balance AS C_ENDING_BALANCE,
    portfolio.f_card_balance AS C_CARD_BALANCE,
    portfolio.f_revolving_balance AS C_REVOLVING_BALANCE,
    portfolio.f_new_accounts AS C_NEW_ACCOUNTS,
    portfolio.f_closed_accounts AS C_CLOSED_ACCOUNTS,
    portfolio.f_active_accounts AS C_ACTIVE_ACCOUNTS,
    portfolio.f_purchase_volume AS C_PURCHASE_VOLUME,
    portfolio.f_interchange_revenue AS C_INTERCHANGE_REVENUE,
    portfolio.f_rewards_expense AS C_REWARDS_EXPENSE,
    portfolio.f_net_interest_income AS C_NET_INTEREST_INCOME,
    portfolio.f_cost_of_funds AS C_COST_OF_FUNDS,
    credit.f_dpd_30_balance AS C_DPD_30_BALANCE,
    credit.f_dpd_60_balance AS C_DPD_60_BALANCE,
    credit.f_dpd_90_balance AS C_DPD_90_BALANCE,
    credit.f_gross_chargeoffs AS C_GROSS_CHARGEOFFS,
    credit.f_recoveries AS C_RECOVERIES,
    credit.f_net_chargeoffs AS C_NET_CHARGEOFFS,
    credit.f_card_balance AS C_CARD_BALANCE,
    credit.f_fico_x_balance AS C_FICO_X_BALANCE,
    credit.f_card_revenue AS C_CARD_REVENUE,
    deposits.f_deposit_balance AS C_DEPOSIT_BALANCE,
    deposits.f_runoff AS C_RUNOFF,
    deposits.f_maturing AS C_MATURING,
    deposits.f_new_money AS C_NEW_MONEY,
    deposits.f_rate_paid_x_balance AS C_RATE_PAID_X_BALANCE,
    deposits.f_competitor_rate_x_balance AS C_COMPETITOR_RATE_X_BALANCE,
    deposits.f_rate_gap_x_balance AS C_RATE_GAP_X_BALANCE,
    acquisition.f_marketing_spend AS C_MARKETING_SPEND,
    acquisition.f_applications AS C_APPLICATIONS,
    acquisition.f_approvals AS C_APPROVALS,
    acquisition.f_bookings AS C_BOOKINGS,
    acquisition.f_credit_line_x_bookings AS C_CREDIT_LINE_X_BOOKINGS
  )
  DIMENSIONS (
    weeks.week_ending AS C_WEEK_ENDING WITH SYNONYMS = ('week', 'week ending', 'date')
      COMMENT = 'Sunday that ends the week. Use for all time filtering; the newest week is the last full week.',
    weeks.week_start AS C_WEEK_START COMMENT = 'Monday that starts the week.',
    weeks.month_start AS C_MONTH_START WITH SYNONYMS = ('month') COMMENT = 'First day of the month the week ends in.',
    weeks.month_name AS C_MONTH_NAME COMMENT = 'Month label, e.g. Oct 2026.',
    weeks.calendar_quarter AS C_QUARTER WITH SYNONYMS = ('fiscal quarter') COMMENT = 'Calendar quarter, e.g. 2026-Q3.',
    weeks.calendar_year AS C_YEAR WITH SYNONYMS = ('fiscal year') COMMENT = 'Calendar (= fiscal) year.',
    weeks.week_of_year AS C_WEEK_OF_YEAR COMMENT = 'ISO week number.',
    products.product_name AS C_PRODUCT_NAME WITH SYNONYMS = ('product', 'card product', 'deposit product')
      COMMENT = 'Product name, e.g. Keystone Travel Signature Card.',
    products.product_type AS C_PRODUCT_TYPE WITH SYNONYMS = ('business line', 'line of business')
      COMMENT = 'Credit Card or Deposit.',
    products.tier AS C_TIER WITH SYNONYMS = ('product tier') COMMENT = 'Mainstream, Premium, Subprime or Business.',
    segments.segment_name AS C_SEGMENT_NAME WITH SYNONYMS = ('segment', 'customer segment')
      COMMENT = 'Behavioural segment, e.g. Near-Prime Revolver, Mass Affluent Saver.',
    segments.credit_tier AS C_CREDIT_TIER WITH SYNONYMS = ('FICO band', 'credit band')
      COMMENT = 'Prime (740+), Near-prime (660-739) or Subprime (<660), from the segment average FICO.',
    segments.segment_description AS C_SEGMENT_DESCRIPTION COMMENT = 'What characterises the segment.',
    acquisition.channel AS C_CHANNEL WITH SYNONYMS = ('marketing channel', 'acquisition channel')
      COMMENT = 'Acquisition channel, e.g. Direct Mail, Digital Paid, Branch.'
  )
  METRICS (
    portfolio.ending_balance NON ADDITIVE BY (weeks.week_ending) AS SUM(portfolio.f_ending_balance) WITH SYNONYMS = ('balance', 'balances', 'managed balances', 'outstandings')
      COMMENT = 'Balance at the end of the latest week in the period (cards + deposits unless filtered). A stock: never summed across weeks.',
    portfolio.active_accounts NON ADDITIVE BY (weeks.week_ending) AS SUM(portfolio.f_active_accounts) WITH SYNONYMS = ('accounts', 'open accounts')
      COMMENT = 'Active accounts at the end of the latest week in the period.',
    portfolio.helper_weeks AS COUNT(DISTINCT portfolio.f_week) COMMENT = 'Helper: weeks in the period.',
    portfolio.helper_balance_weeks AS SUM(portfolio.f_ending_balance) COMMENT = 'Helper: weekly balances summed over weeks.',
    portfolio.helper_card_balance_weeks AS SUM(portfolio.f_card_balance) COMMENT = 'Helper: weekly card balances summed over weeks.',
    portfolio.helper_active_weeks AS SUM(portfolio.f_active_accounts) COMMENT = 'Helper: weekly active accounts summed over weeks.',
    portfolio.average_balance AS DIV0(portfolio.helper_balance_weeks, portfolio.helper_weeks) WITH SYNONYMS = ('average balances')
      COMMENT = 'Average weekly ending balance over the period.',
    portfolio.new_accounts AS SUM(portfolio.f_new_accounts) WITH SYNONYMS = ('new accounts opened', 'account openings')
      COMMENT = 'Accounts opened in the period.',
    portfolio.closed_accounts AS SUM(portfolio.f_closed_accounts) COMMENT = 'Accounts closed in the period.',
    portfolio.attrition_rate AS DIV0(portfolio.closed_accounts * 52, portfolio.helper_active_weeks) WITH SYNONYMS = ('attrition', 'churn rate')
      COMMENT = 'Annualised account attrition: closed accounts / active accounts, x 52 weeks.',
    portfolio.purchase_volume AS SUM(portfolio.f_purchase_volume) WITH SYNONYMS = ('card spend', 'spend volume', 'purchases')
      COMMENT = 'Card purchase volume (USD).',
    portfolio.interchange_revenue AS SUM(portfolio.f_interchange_revenue) WITH SYNONYMS = ('interchange')
      COMMENT = 'Interchange fees earned on card spend (USD).',
    portfolio.rewards_expense AS SUM(portfolio.f_rewards_expense) WITH SYNONYMS = ('rewards cost', 'rewards')
      COMMENT = 'Cost of card rewards (USD).',
    portfolio.rewards_to_interchange_ratio AS DIV0(portfolio.rewards_expense, portfolio.interchange_revenue)
      WITH SYNONYMS = ('rewards to interchange', 'rewards ratio')
      COMMENT = 'Rewards expense / interchange revenue. Healthy below 0.80; above 0.85 is a profitability breach.',
    portfolio.net_interest_income AS SUM(portfolio.f_net_interest_income) WITH SYNONYMS = ('NII', 'interest income')
      COMMENT = 'Net interest income (USD).',
    portfolio.cost_of_funds AS SUM(portfolio.f_cost_of_funds) WITH SYNONYMS = ('funding cost')
      COMMENT = 'Cost of funds (USD).',
    portfolio.net_interest_margin_pct AS DIV0((portfolio.net_interest_income - portfolio.cost_of_funds) * 52, portfolio.helper_balance_weeks)
      WITH SYNONYMS = ('NIM', 'net interest margin')
      COMMENT = 'Annualised (net interest income - cost of funds) / average balance.',
    portfolio.cost_of_funds_rate AS DIV0(portfolio.cost_of_funds * 52, portfolio.helper_balance_weeks)
      COMMENT = 'Annualised cost of funds / average balance.',
    portfolio.helper_revolving_weeks AS SUM(portfolio.f_revolving_balance) COMMENT = 'Helper: weekly revolving balances summed over weeks.',
    portfolio.revolve_rate AS DIV0(portfolio.helper_revolving_weeks, portfolio.helper_balance_weeks)
      WITH SYNONYMS = ('revolving share') COMMENT = 'Share of balance carrying interest (balance-weighted).',
    credit.dpd_30_balance NON ADDITIVE BY (weeks.week_ending) AS SUM(credit.f_dpd_30_balance) WITH SYNONYMS = ('30 days past due', '30+ DPD balance')
      COMMENT = 'Card balance 30+ days past due at the end of the latest week in the period.',
    credit.dpd_60_balance NON ADDITIVE BY (weeks.week_ending) AS SUM(credit.f_dpd_60_balance) WITH SYNONYMS = ('60 days past due')
      COMMENT = 'Card balance 60+ days past due at the end of the latest week in the period.',
    credit.dpd_90_balance NON ADDITIVE BY (weeks.week_ending) AS SUM(credit.f_dpd_90_balance) WITH SYNONYMS = ('90 days past due')
      COMMENT = 'Card balance 90+ days past due at the end of the latest week in the period.',
    credit.helper_dpd_30_weeks AS SUM(credit.f_dpd_30_balance) COMMENT = 'Helper: weekly 30+ DPD balances summed over weeks.',
    credit.helper_credit_card_balance_weeks AS SUM(credit.f_card_balance) COMMENT = 'Helper: weekly card balances summed over weeks.',
    credit.delinquency_rate AS DIV0(credit.helper_dpd_30_weeks, credit.helper_credit_card_balance_weeks)
      WITH SYNONYMS = ('delinquency', '30+ delinquency rate', 'past due rate')
      COMMENT = '30+ days past due balance / card balance (cards only; average over the weeks in the period).',
    credit.gross_chargeoffs AS SUM(credit.f_gross_chargeoffs) WITH SYNONYMS = ('gross charge-offs', 'gross losses')
      COMMENT = 'Gross charge-offs (USD).',
    credit.recoveries AS SUM(credit.f_recoveries) COMMENT = 'Recoveries on charged-off accounts (USD).',
    credit.net_chargeoffs AS SUM(credit.f_net_chargeoffs) WITH SYNONYMS = ('net charge-offs', 'NCO', 'net losses')
      COMMENT = 'Gross charge-offs minus recoveries (USD).',
    credit.annualized_loss_rate AS DIV0(credit.net_chargeoffs * 52, credit.helper_credit_card_balance_weeks)
      WITH SYNONYMS = ('loss rate', 'net charge-off rate', 'NCO rate')
      COMMENT = 'Annualised net charge-offs / average card balance.',
    credit.recovery_rate AS DIV0(credit.recoveries, credit.gross_chargeoffs) COMMENT = 'Recoveries / gross charge-offs.',
    credit.card_revenue AS SUM(credit.f_card_revenue) WITH SYNONYMS = ('card revenue')
      COMMENT = 'Card net interest income + interchange - rewards (USD), before funding cost and losses.',
    credit.risk_adjusted_yield AS DIV0((credit.card_revenue - credit.net_chargeoffs) * 52, credit.helper_credit_card_balance_weeks)
      WITH SYNONYMS = ('risk adjusted yield', 'risk-adjusted margin', 'yield after losses')
      COMMENT = 'Annualised (card revenue - net charge-offs) / average card balance. Below zero the segment loses money after losses.',
    credit.helper_fico_x_balance AS SUM(credit.f_fico_x_balance) COMMENT = 'Helper: FICO x card balance summed.',
    credit.average_fico AS DIV0(credit.helper_fico_x_balance, credit.helper_credit_card_balance_weeks)
      WITH SYNONYMS = ('FICO', 'credit score') COMMENT = 'Balance-weighted average FICO score of card customers.',
    deposits.deposit_balance NON ADDITIVE BY (weeks.week_ending) AS SUM(deposits.f_deposit_balance) WITH SYNONYMS = ('deposits', 'deposit balances', 'savings balance')
      COMMENT = 'Deposit balance at the end of the latest week in the period.',
    deposits.helper_deposit_balance_weeks AS SUM(deposits.f_deposit_balance) COMMENT = 'Helper: weekly deposit balances summed over weeks.',
    deposits.runoff AS SUM(deposits.f_runoff) WITH SYNONYMS = ('deposit runoff', 'outflows', 'withdrawals')
      COMMENT = 'Deposit balances that left the bank (USD).',
    deposits.new_money AS SUM(deposits.f_new_money) WITH SYNONYMS = ('inflows', 'new deposits') COMMENT = 'New deposit money (USD).',
    deposits.net_new_money AS deposits.new_money - deposits.runoff WITH SYNONYMS = ('net flows', 'net deposit flows')
      COMMENT = 'New money minus runoff (USD).',
    deposits.maturing_dollars AS SUM(deposits.f_maturing) WITH SYNONYMS = ('CD maturities', 'maturing balances')
      COMMENT = 'CD balances reaching maturity (USD).',
    deposits.runoff_rate AS DIV0(deposits.runoff * 52, deposits.helper_deposit_balance_weeks)
      WITH SYNONYMS = ('deposit runoff rate', 'attrition of deposits') COMMENT = 'Annualised runoff / average deposit balance.',
    deposits.maturity_concentration AS DIV0(deposits.maturing_dollars, deposits.helper_deposit_balance_weeks)
      COMMENT = 'Maturing dollars / deposit balance (average week in the period).',
    deposits.helper_rate_paid_x_balance AS SUM(deposits.f_rate_paid_x_balance) COMMENT = 'Helper: rate paid x balance summed.',
    deposits.helper_competitor_x_balance AS SUM(deposits.f_competitor_rate_x_balance) COMMENT = 'Helper: competitor rate x balance summed.',
    deposits.helper_rate_gap_x_balance AS SUM(deposits.f_rate_gap_x_balance) COMMENT = 'Helper: rate gap x balance summed.',
    deposits.rate_paid AS DIV0(deposits.helper_rate_paid_x_balance, deposits.helper_deposit_balance_weeks)
      WITH SYNONYMS = ('APY', 'deposit rate') COMMENT = 'Balance-weighted rate (APY) paid to depositors.',
    deposits.competitor_rate AS DIV0(deposits.helper_competitor_x_balance, deposits.helper_deposit_balance_weeks)
      WITH SYNONYMS = ('market rate') COMMENT = 'Balance-weighted competitor rate for the same products.',
    deposits.rate_gap AS DIV0(deposits.helper_rate_gap_x_balance, deposits.helper_deposit_balance_weeks)
      WITH SYNONYMS = ('rate gap to competitors', 'pricing gap')
      COMMENT = 'Competitor rate minus rate paid (balance-weighted). POSITIVE means competitors pay more than Keystone: balances are at risk.',
    acquisition.marketing_spend AS SUM(acquisition.f_marketing_spend) WITH SYNONYMS = ('acquisition spend', 'marketing cost')
      COMMENT = 'Acquisition marketing spend (USD).',
    acquisition.applications AS SUM(acquisition.f_applications) WITH SYNONYMS = ('apps') COMMENT = 'Applications received.',
    acquisition.approvals AS SUM(acquisition.f_approvals) COMMENT = 'Applications approved.',
    acquisition.bookings AS SUM(acquisition.f_bookings) WITH SYNONYMS = ('booked accounts') COMMENT = 'Approved applications that opened an account.',
    acquisition.approval_rate AS DIV0(acquisition.approvals, acquisition.applications) COMMENT = 'Approvals / applications.',
    acquisition.booking_rate AS DIV0(acquisition.bookings, acquisition.approvals) COMMENT = 'Bookings / approvals.',
    acquisition.cost_per_booking AS DIV0(acquisition.marketing_spend, acquisition.bookings) WITH SYNONYMS = ('CAC', 'customer acquisition cost')
      COMMENT = 'Marketing spend / bookings (USD).',
    acquisition.helper_credit_line_x_bookings AS SUM(acquisition.f_credit_line_x_bookings) COMMENT = 'Helper: initial line x bookings summed.',
    acquisition.average_initial_credit_line AS DIV0(acquisition.helper_credit_line_x_bookings, acquisition.bookings)
      WITH SYNONYMS = ('initial line') COMMENT = 'Booking-weighted average initial credit line (USD).'
  )
  COMMENT = 'Keystone Financial (fictional US consumer bank): card and deposit portfolio, credit risk, deposit pricing and acquisition. Weekly, rolling to the last full week.'$$);
INSERT INTO SV_DDL VALUES (3, 'no end-of-week stock metrics', $$CREATE OR REPLACE SEMANTIC VIEW WBR_DB.FINANCE_DEMO.FINANCE_ANALYTICS_SV
  TABLES (
    weeks AS WBR_DB.FINANCE_DEMO.SV_SRC_WEEKS PRIMARY KEY (C_WEEK_ENDING)
      WITH SYNONYMS ('calendar', 'week') COMMENT = 'Weekly calendar. Every row covers Monday to Sunday and is dated by the Sunday the week ends; a week belongs to the month it ends in.',
    products AS WBR_DB.FINANCE_DEMO.SV_SRC_PRODUCT PRIMARY KEY (C_PRODUCT_ID)
      WITH SYNONYMS ('product', 'card', 'account type') COMMENT = 'Six products: four credit cards (Cash Rewards, Travel Signature, Secured, Small Business) and two deposit products (High-Yield Savings, 12-Month CD).',
    segments AS WBR_DB.FINANCE_DEMO.SV_SRC_SEGMENT PRIMARY KEY (C_SEGMENT_ID)
      WITH SYNONYMS ('customer segment', 'behavioural segment') COMMENT = 'Six behavioural segments crossing credit quality and product usage.',
    portfolio AS WBR_DB.FINANCE_DEMO.SV_SRC_PORTFOLIO PRIMARY KEY (C_WEEK_ENDING, C_PRODUCT_ID, C_SEGMENT_ID)
      WITH SYNONYMS ('book', 'balances', 'portfolio performance')
      COMMENT = 'Weekly balances, accounts, card spend and economics for every product (cards and deposits) and segment.',
    credit AS WBR_DB.FINANCE_DEMO.SV_SRC_CREDIT PRIMARY KEY (C_WEEK_ENDING, C_PRODUCT_ID, C_SEGMENT_ID)
      WITH SYNONYMS ('credit risk', 'delinquency', 'losses')
      COMMENT = 'Weekly credit performance of CREDIT CARD products only: past-due balances, charge-offs, recoveries, FICO.',
    deposits AS WBR_DB.FINANCE_DEMO.SV_SRC_DEPOSITS PRIMARY KEY (C_WEEK_ENDING, C_PRODUCT_ID, C_SEGMENT_ID)
      WITH SYNONYMS ('savings', 'CDs', 'deposit book')
      COMMENT = 'Weekly retail deposit balances, flows and pricing for DEPOSIT products only.',
    acquisition AS WBR_DB.FINANCE_DEMO.SV_SRC_ACQUISITION PRIMARY KEY (C_WEEK_ENDING, C_PRODUCT_ID, C_CHANNEL)
      WITH SYNONYMS ('marketing', 'new account acquisition', 'funnel')
      COMMENT = 'Weekly acquisition funnel by product and marketing channel: spend, applications, approvals, bookings.'
  )
  RELATIONSHIPS (
    portfolio_to_weeks AS portfolio (C_WEEK_ENDING) REFERENCES weeks,
    portfolio_to_products AS portfolio (C_PRODUCT_ID) REFERENCES products,
    portfolio_to_segments AS portfolio (C_SEGMENT_ID) REFERENCES segments,
    credit_to_weeks AS credit (C_WEEK_ENDING) REFERENCES weeks,
    credit_to_products AS credit (C_PRODUCT_ID) REFERENCES products,
    credit_to_segments AS credit (C_SEGMENT_ID) REFERENCES segments,
    deposits_to_weeks AS deposits (C_WEEK_ENDING) REFERENCES weeks,
    deposits_to_products AS deposits (C_PRODUCT_ID) REFERENCES products,
    deposits_to_segments AS deposits (C_SEGMENT_ID) REFERENCES segments,
    acquisition_to_weeks AS acquisition (C_WEEK_ENDING) REFERENCES weeks,
    acquisition_to_products AS acquisition (C_PRODUCT_ID) REFERENCES products
  )
  FACTS (
    portfolio.f_week AS C_WEEK_ENDING,
    portfolio.f_ending_balance AS C_ENDING_BALANCE,
    portfolio.f_card_balance AS C_CARD_BALANCE,
    portfolio.f_revolving_balance AS C_REVOLVING_BALANCE,
    portfolio.f_new_accounts AS C_NEW_ACCOUNTS,
    portfolio.f_closed_accounts AS C_CLOSED_ACCOUNTS,
    portfolio.f_active_accounts AS C_ACTIVE_ACCOUNTS,
    portfolio.f_purchase_volume AS C_PURCHASE_VOLUME,
    portfolio.f_interchange_revenue AS C_INTERCHANGE_REVENUE,
    portfolio.f_rewards_expense AS C_REWARDS_EXPENSE,
    portfolio.f_net_interest_income AS C_NET_INTEREST_INCOME,
    portfolio.f_cost_of_funds AS C_COST_OF_FUNDS,
    credit.f_dpd_30_balance AS C_DPD_30_BALANCE,
    credit.f_dpd_60_balance AS C_DPD_60_BALANCE,
    credit.f_dpd_90_balance AS C_DPD_90_BALANCE,
    credit.f_gross_chargeoffs AS C_GROSS_CHARGEOFFS,
    credit.f_recoveries AS C_RECOVERIES,
    credit.f_net_chargeoffs AS C_NET_CHARGEOFFS,
    credit.f_card_balance AS C_CARD_BALANCE,
    credit.f_fico_x_balance AS C_FICO_X_BALANCE,
    credit.f_card_revenue AS C_CARD_REVENUE,
    deposits.f_deposit_balance AS C_DEPOSIT_BALANCE,
    deposits.f_runoff AS C_RUNOFF,
    deposits.f_maturing AS C_MATURING,
    deposits.f_new_money AS C_NEW_MONEY,
    deposits.f_rate_paid_x_balance AS C_RATE_PAID_X_BALANCE,
    deposits.f_competitor_rate_x_balance AS C_COMPETITOR_RATE_X_BALANCE,
    deposits.f_rate_gap_x_balance AS C_RATE_GAP_X_BALANCE,
    acquisition.f_marketing_spend AS C_MARKETING_SPEND,
    acquisition.f_applications AS C_APPLICATIONS,
    acquisition.f_approvals AS C_APPROVALS,
    acquisition.f_bookings AS C_BOOKINGS,
    acquisition.f_credit_line_x_bookings AS C_CREDIT_LINE_X_BOOKINGS
  )
  DIMENSIONS (
    weeks.week_ending AS C_WEEK_ENDING WITH SYNONYMS = ('week', 'week ending', 'date')
      COMMENT = 'Sunday that ends the week. Use for all time filtering; the newest week is the last full week.',
    weeks.week_start AS C_WEEK_START COMMENT = 'Monday that starts the week.',
    weeks.month_start AS C_MONTH_START WITH SYNONYMS = ('month') COMMENT = 'First day of the month the week ends in.',
    weeks.month_name AS C_MONTH_NAME COMMENT = 'Month label, e.g. Oct 2026.',
    weeks.calendar_quarter AS C_QUARTER WITH SYNONYMS = ('fiscal quarter') COMMENT = 'Calendar quarter, e.g. 2026-Q3.',
    weeks.calendar_year AS C_YEAR WITH SYNONYMS = ('fiscal year') COMMENT = 'Calendar (= fiscal) year.',
    weeks.week_of_year AS C_WEEK_OF_YEAR COMMENT = 'ISO week number.',
    products.product_name AS C_PRODUCT_NAME WITH SYNONYMS = ('product', 'card product', 'deposit product')
      COMMENT = 'Product name, e.g. Keystone Travel Signature Card.',
    products.product_type AS C_PRODUCT_TYPE WITH SYNONYMS = ('business line', 'line of business')
      COMMENT = 'Credit Card or Deposit.',
    products.tier AS C_TIER WITH SYNONYMS = ('product tier') COMMENT = 'Mainstream, Premium, Subprime or Business.',
    segments.segment_name AS C_SEGMENT_NAME WITH SYNONYMS = ('segment', 'customer segment')
      COMMENT = 'Behavioural segment, e.g. Near-Prime Revolver, Mass Affluent Saver.',
    segments.credit_tier AS C_CREDIT_TIER WITH SYNONYMS = ('FICO band', 'credit band')
      COMMENT = 'Prime (740+), Near-prime (660-739) or Subprime (<660), from the segment average FICO.',
    segments.segment_description AS C_SEGMENT_DESCRIPTION COMMENT = 'What characterises the segment.',
    acquisition.channel AS C_CHANNEL WITH SYNONYMS = ('marketing channel', 'acquisition channel')
      COMMENT = 'Acquisition channel, e.g. Direct Mail, Digital Paid, Branch.'
  )
  METRICS (
    portfolio.helper_weeks AS COUNT(DISTINCT portfolio.f_week) COMMENT = 'Helper: weeks in the period.',
    portfolio.helper_balance_weeks AS SUM(portfolio.f_ending_balance) COMMENT = 'Helper: weekly balances summed over weeks.',
    portfolio.helper_card_balance_weeks AS SUM(portfolio.f_card_balance) COMMENT = 'Helper: weekly card balances summed over weeks.',
    portfolio.helper_active_weeks AS SUM(portfolio.f_active_accounts) COMMENT = 'Helper: weekly active accounts summed over weeks.',
    portfolio.average_balance AS DIV0(portfolio.helper_balance_weeks, portfolio.helper_weeks) WITH SYNONYMS = ('average balances')
      COMMENT = 'Average weekly ending balance over the period.',
    portfolio.new_accounts AS SUM(portfolio.f_new_accounts) WITH SYNONYMS = ('new accounts opened', 'account openings')
      COMMENT = 'Accounts opened in the period.',
    portfolio.closed_accounts AS SUM(portfolio.f_closed_accounts) COMMENT = 'Accounts closed in the period.',
    portfolio.attrition_rate AS DIV0(portfolio.closed_accounts * 52, portfolio.helper_active_weeks) WITH SYNONYMS = ('attrition', 'churn rate')
      COMMENT = 'Annualised account attrition: closed accounts / active accounts, x 52 weeks.',
    portfolio.purchase_volume AS SUM(portfolio.f_purchase_volume) WITH SYNONYMS = ('card spend', 'spend volume', 'purchases')
      COMMENT = 'Card purchase volume (USD).',
    portfolio.interchange_revenue AS SUM(portfolio.f_interchange_revenue) WITH SYNONYMS = ('interchange')
      COMMENT = 'Interchange fees earned on card spend (USD).',
    portfolio.rewards_expense AS SUM(portfolio.f_rewards_expense) WITH SYNONYMS = ('rewards cost', 'rewards')
      COMMENT = 'Cost of card rewards (USD).',
    portfolio.rewards_to_interchange_ratio AS DIV0(portfolio.rewards_expense, portfolio.interchange_revenue)
      WITH SYNONYMS = ('rewards to interchange', 'rewards ratio')
      COMMENT = 'Rewards expense / interchange revenue. Healthy below 0.80; above 0.85 is a profitability breach.',
    portfolio.net_interest_income AS SUM(portfolio.f_net_interest_income) WITH SYNONYMS = ('NII', 'interest income')
      COMMENT = 'Net interest income (USD).',
    portfolio.cost_of_funds AS SUM(portfolio.f_cost_of_funds) WITH SYNONYMS = ('funding cost')
      COMMENT = 'Cost of funds (USD).',
    portfolio.net_interest_margin_pct AS DIV0((portfolio.net_interest_income - portfolio.cost_of_funds) * 52, portfolio.helper_balance_weeks)
      WITH SYNONYMS = ('NIM', 'net interest margin')
      COMMENT = 'Annualised (net interest income - cost of funds) / average balance.',
    portfolio.cost_of_funds_rate AS DIV0(portfolio.cost_of_funds * 52, portfolio.helper_balance_weeks)
      COMMENT = 'Annualised cost of funds / average balance.',
    portfolio.helper_revolving_weeks AS SUM(portfolio.f_revolving_balance) COMMENT = 'Helper: weekly revolving balances summed over weeks.',
    portfolio.revolve_rate AS DIV0(portfolio.helper_revolving_weeks, portfolio.helper_balance_weeks)
      WITH SYNONYMS = ('revolving share') COMMENT = 'Share of balance carrying interest (balance-weighted).',
    credit.helper_dpd_30_weeks AS SUM(credit.f_dpd_30_balance) COMMENT = 'Helper: weekly 30+ DPD balances summed over weeks.',
    credit.helper_credit_card_balance_weeks AS SUM(credit.f_card_balance) COMMENT = 'Helper: weekly card balances summed over weeks.',
    credit.delinquency_rate AS DIV0(credit.helper_dpd_30_weeks, credit.helper_credit_card_balance_weeks)
      WITH SYNONYMS = ('delinquency', '30+ delinquency rate', 'past due rate')
      COMMENT = '30+ days past due balance / card balance (cards only; average over the weeks in the period).',
    credit.gross_chargeoffs AS SUM(credit.f_gross_chargeoffs) WITH SYNONYMS = ('gross charge-offs', 'gross losses')
      COMMENT = 'Gross charge-offs (USD).',
    credit.recoveries AS SUM(credit.f_recoveries) COMMENT = 'Recoveries on charged-off accounts (USD).',
    credit.net_chargeoffs AS SUM(credit.f_net_chargeoffs) WITH SYNONYMS = ('net charge-offs', 'NCO', 'net losses')
      COMMENT = 'Gross charge-offs minus recoveries (USD).',
    credit.annualized_loss_rate AS DIV0(credit.net_chargeoffs * 52, credit.helper_credit_card_balance_weeks)
      WITH SYNONYMS = ('loss rate', 'net charge-off rate', 'NCO rate')
      COMMENT = 'Annualised net charge-offs / average card balance.',
    credit.recovery_rate AS DIV0(credit.recoveries, credit.gross_chargeoffs) COMMENT = 'Recoveries / gross charge-offs.',
    credit.card_revenue AS SUM(credit.f_card_revenue) WITH SYNONYMS = ('card revenue')
      COMMENT = 'Card net interest income + interchange - rewards (USD), before funding cost and losses.',
    credit.risk_adjusted_yield AS DIV0((credit.card_revenue - credit.net_chargeoffs) * 52, credit.helper_credit_card_balance_weeks)
      WITH SYNONYMS = ('risk adjusted yield', 'risk-adjusted margin', 'yield after losses')
      COMMENT = 'Annualised (card revenue - net charge-offs) / average card balance. Below zero the segment loses money after losses.',
    credit.helper_fico_x_balance AS SUM(credit.f_fico_x_balance) COMMENT = 'Helper: FICO x card balance summed.',
    credit.average_fico AS DIV0(credit.helper_fico_x_balance, credit.helper_credit_card_balance_weeks)
      WITH SYNONYMS = ('FICO', 'credit score') COMMENT = 'Balance-weighted average FICO score of card customers.',
    deposits.helper_deposit_balance_weeks AS SUM(deposits.f_deposit_balance) COMMENT = 'Helper: weekly deposit balances summed over weeks.',
    deposits.runoff AS SUM(deposits.f_runoff) WITH SYNONYMS = ('deposit runoff', 'outflows', 'withdrawals')
      COMMENT = 'Deposit balances that left the bank (USD).',
    deposits.new_money AS SUM(deposits.f_new_money) WITH SYNONYMS = ('inflows', 'new deposits') COMMENT = 'New deposit money (USD).',
    deposits.net_new_money AS deposits.new_money - deposits.runoff WITH SYNONYMS = ('net flows', 'net deposit flows')
      COMMENT = 'New money minus runoff (USD).',
    deposits.maturing_dollars AS SUM(deposits.f_maturing) WITH SYNONYMS = ('CD maturities', 'maturing balances')
      COMMENT = 'CD balances reaching maturity (USD).',
    deposits.runoff_rate AS DIV0(deposits.runoff * 52, deposits.helper_deposit_balance_weeks)
      WITH SYNONYMS = ('deposit runoff rate', 'attrition of deposits') COMMENT = 'Annualised runoff / average deposit balance.',
    deposits.maturity_concentration AS DIV0(deposits.maturing_dollars, deposits.helper_deposit_balance_weeks)
      COMMENT = 'Maturing dollars / deposit balance (average week in the period).',
    deposits.helper_rate_paid_x_balance AS SUM(deposits.f_rate_paid_x_balance) COMMENT = 'Helper: rate paid x balance summed.',
    deposits.helper_competitor_x_balance AS SUM(deposits.f_competitor_rate_x_balance) COMMENT = 'Helper: competitor rate x balance summed.',
    deposits.helper_rate_gap_x_balance AS SUM(deposits.f_rate_gap_x_balance) COMMENT = 'Helper: rate gap x balance summed.',
    deposits.rate_paid AS DIV0(deposits.helper_rate_paid_x_balance, deposits.helper_deposit_balance_weeks)
      WITH SYNONYMS = ('APY', 'deposit rate') COMMENT = 'Balance-weighted rate (APY) paid to depositors.',
    deposits.competitor_rate AS DIV0(deposits.helper_competitor_x_balance, deposits.helper_deposit_balance_weeks)
      WITH SYNONYMS = ('market rate') COMMENT = 'Balance-weighted competitor rate for the same products.',
    deposits.rate_gap AS DIV0(deposits.helper_rate_gap_x_balance, deposits.helper_deposit_balance_weeks)
      WITH SYNONYMS = ('rate gap to competitors', 'pricing gap')
      COMMENT = 'Competitor rate minus rate paid (balance-weighted). POSITIVE means competitors pay more than Keystone: balances are at risk.',
    acquisition.marketing_spend AS SUM(acquisition.f_marketing_spend) WITH SYNONYMS = ('acquisition spend', 'marketing cost')
      COMMENT = 'Acquisition marketing spend (USD).',
    acquisition.applications AS SUM(acquisition.f_applications) WITH SYNONYMS = ('apps') COMMENT = 'Applications received.',
    acquisition.approvals AS SUM(acquisition.f_approvals) COMMENT = 'Applications approved.',
    acquisition.bookings AS SUM(acquisition.f_bookings) WITH SYNONYMS = ('booked accounts') COMMENT = 'Approved applications that opened an account.',
    acquisition.approval_rate AS DIV0(acquisition.approvals, acquisition.applications) COMMENT = 'Approvals / applications.',
    acquisition.booking_rate AS DIV0(acquisition.bookings, acquisition.approvals) COMMENT = 'Bookings / approvals.',
    acquisition.cost_per_booking AS DIV0(acquisition.marketing_spend, acquisition.bookings) WITH SYNONYMS = ('CAC', 'customer acquisition cost')
      COMMENT = 'Marketing spend / bookings (USD).',
    acquisition.helper_credit_line_x_bookings AS SUM(acquisition.f_credit_line_x_bookings) COMMENT = 'Helper: initial line x bookings summed.',
    acquisition.average_initial_credit_line AS DIV0(acquisition.helper_credit_line_x_bookings, acquisition.bookings)
      WITH SYNONYMS = ('initial line') COMMENT = 'Booking-weighted average initial credit line (USD).'
  )
  COMMENT = 'Keystone Financial (fictional US consumer bank): card and deposit portfolio, credit risk, deposit pricing and acquisition. Weekly, rolling to the last full week.'$$);

EXECUTE IMMEDIATE $$
DECLARE
  c CURSOR FOR SELECT ATTEMPT, NAME, DDL FROM WBR_DB.FINANCE_DEMO.SV_DDL ORDER BY ATTEMPT;
  errs VARCHAR DEFAULT '';
  stmt VARCHAR;
BEGIN
  FOR r IN c DO
    stmt := r.DDL;
    BEGIN
      EXECUTE IMMEDIATE :stmt;
      RETURN 'FINANCE_ANALYTICS_SV created (' || r.NAME || ')' || IFF(errs = '', '', ' | earlier attempts: ' || errs);
    EXCEPTION
      WHEN OTHER THEN
        errs := errs || '[' || r.ATTEMPT || '] ' || LEFT(SQLERRM, 300) || ' ';
    END;
  END FOR;
  RETURN 'FAILED: ' || errs;
END;
$$;

DESCRIBE SEMANTIC VIEW WBR_DB.FINANCE_DEMO.FINANCE_ANALYTICS_SV;
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
