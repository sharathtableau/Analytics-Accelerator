"""Generates 03_semantic_view.sql: CPG_ANALYTICS_SV over the rolling SV_SRC_* views (with fallbacks).

Fixes applied to the pack's semantic_model_cpg.yaml:
  1. sell-in and sell-through are one source (same grain, 1:1), so sell-through ratio = POS units / shipped units is
     exact (the pack had no such metric across its two tables);
  2. retailer on-hand units are an end-of-week stock: NON ADDITIVE BY week (the pack summed them across weeks);
  3. weeks of supply = average on-hand / average weekly POS units over the period (the pack averaged the weekly
     ratio column), gross margin %, fill rate, OTIF and ACV distribution are weighted (the pack averaged them);
  4. dates roll forward (02_views.sql) so "last 13 weeks" questions keep working.
Ratios/rates are fractions (0.123 = 12.3%) like the retail and finance views.
"""
S = "WBR_DB.CPG_DEMO"
WEEK = "weeks.week_ending"

TABLES = f"""
  TABLES (
    weeks AS {S}.SV_SRC_WEEKS PRIMARY KEY (C_WEEK_ENDING)
      WITH SYNONYMS ('calendar', 'week') COMMENT = 'Weekly calendar. Every row covers Monday to Sunday and is dated by the Sunday the week ends; a week belongs to the month it ends in.',
    accounts AS {S}.SV_SRC_CUSTOMER PRIMARY KEY (C_CUSTOMER_ID)
      WITH SYNONYMS ('customers', 'retailers', 'retail partners') COMMENT = 'Ten accounts: eight wholesale retail partners (one is the off-price channel) and two direct-to-consumer channels.',
    products AS {S}.SV_SRC_PRODUCT PRIMARY KEY (C_PRODUCT_ID)
      WITH SYNONYMS ('product lines', 'SKUs', 'styles') COMMENT = 'Twelve product lines across apparel, footwear and accessories.',
    trade AS {S}.SV_SRC_ACCOUNT_WEEK PRIMARY KEY (C_WEEK_ENDING, C_CUSTOMER_ID, C_PRODUCT_ID)
      WITH SYNONYMS ('sell-in', 'shipments', 'sell-through', 'POS')
      COMMENT = 'Weekly sell-in (what Apex ships and books as revenue) and sell-through (what consumers buy at the retailer) per account and product line.',
    promotions AS {S}.SV_SRC_PROMO PRIMARY KEY (C_PROMO_ID)
      WITH SYNONYMS ('trade promotions', 'promo events', 'deals')
      COMMENT = 'Trade promotion events: type, spend, incremental revenue, lift and ROI, dated by the week they start.'
  )"""

RELS = """
  RELATIONSHIPS (
    trade_to_weeks AS trade (C_WEEK_ENDING) REFERENCES weeks,
    trade_to_accounts AS trade (C_CUSTOMER_ID) REFERENCES accounts,
    trade_to_products AS trade (C_PRODUCT_ID) REFERENCES products,
    promotions_to_weeks AS promotions (C_WEEK_ENDING) REFERENCES weeks,
    promotions_to_accounts AS promotions (C_CUSTOMER_ID) REFERENCES accounts,
    promotions_to_products AS promotions (C_PRODUCT_ID) REFERENCES products
  )"""

FACTS = """
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
  )"""

DIMS = """
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
  )"""

STOCK = f"NON ADDITIVE BY ({WEEK}) "

METRICS = """
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
    trade.retailer_on_hand_units {NA}AS SUM(trade.f_on_hand_units) WITH SYNONYMS = ('retailer inventory', 'channel inventory', 'on hand')
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
  )"""

AI = ("  AI_SQL_GENERATION 'Apex Athletic is a fictional athletic apparel and footwear brand selling through retail "
      "accounts and its own DTC channels. Data is weekly; weeks run Monday to Sunday and are dated by week_ending; filter "
      "time on weeks.week_ending. Revenue means sell-in net_sales; how are we selling usually means sell-through (POS). "
      "Sell-in is lumpy (accounts order about every four weeks): never read one week of sell-in as a trend, use 4 or 13 "
      "weeks. For DTC accounts sell-in equals sell-through, so exclude DTC (accounts.channel = Wholesale) for channel "
      "inventory, weeks of supply and sell-through ratio. Trade spend is already deducted from net sales. Retailer on-hand "
      "units are end-of-week stocks: never sum them across weeks. Rates are fractions and already weighted; never average "
      "a rate. Off-price growth is a warning (excess inventory cleared at lower margin), not a win. ACV distribution can "
      "rise while sales fall: that is a velocity problem.'")

COMMENT = "  COMMENT = 'Apex Athletic (fictional athletic brand): sell-in vs sell-through, account inventory health, margin, service levels and trade promotions. Weekly, rolling to the last full week.'"


def ddl(stocks: bool, ai: bool) -> str:
    mets = METRICS.replace("{NA}", STOCK if stocks else "")
    if not stocks:
        keep, skip = [], False
        for line in mets.split("\n"):
            head = line.strip()
            if head.startswith("trade.retailer_on_hand_units "):
                skip = True
                continue
            if skip and not head.startswith(("trade.", "promotions.", ")")):
                continue
            skip = False
            keep.append(line)
        mets = "\n".join(keep)
    return (f"CREATE OR REPLACE SEMANTIC VIEW {S}.CPG_ANALYTICS_SV" + TABLES + RELS + FACTS + DIMS + mets
            + "\n" + COMMENT + ("\n" + AI if ai else ""))     # COMMENT must come before AI_SQL_GENERATION


HEAD = f"""-- =====================================================================================
-- Apex Athletic (fictional) - Step 3: CPG_ANALYTICS_SV (generated by build_cpg_sv.py)
-- Created from the richest definition this account supports: 1) end-of-week stock + AI instructions,
-- 2) end-of-week stock without AI instructions, 3) without the end-of-week stock metric.
-- =====================================================================================
USE ROLE WBR_OWNER;
USE WAREHOUSE POWERHOUSE;
USE SCHEMA {S};
CREATE OR REPLACE TABLE SV_DDL (ATTEMPT NUMBER, NAME VARCHAR, DDL VARCHAR);
"""

RUN = f"""
EXECUTE IMMEDIATE $$
DECLARE
  c CURSOR FOR SELECT ATTEMPT, NAME, DDL FROM {S}.SV_DDL ORDER BY ATTEMPT;
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

DESCRIBE SEMANTIC VIEW {S}.CPG_ANALYTICS_SV;
"""

if __name__ == "__main__":
    import pathlib
    out = [HEAD]
    for i, (name, st, ai) in enumerate([("full: end-of-week stock + AI instructions", True, True),
                                         ("end-of-week stock, no AI instructions", True, False),
                                         ("no end-of-week stock metric", False, False)], 1):
        out.append(f"INSERT INTO SV_DDL VALUES ({i}, '{name}', $${ddl(st, ai)}$$);\n")
    out.append(RUN)
    pathlib.Path(__file__).with_name("03_semantic_view.sql").write_text("".join(out), encoding="utf-8")
    print("wrote 03_semantic_view.sql")
