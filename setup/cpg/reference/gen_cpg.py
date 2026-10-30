"""Apex Athletic (branded athletic apparel / CPG) — 104 weeks.
Sell-in (what we ship to retail partners) vs sell-through (what consumers buy)."""
import numpy as np, pandas as pd
from datetime import date, timedelta

RNG = np.random.default_rng(777001)
WEEKS = 104
END = date(2026, 9, 14)
START = END - timedelta(weeks=WEEKS - 1)
dates = [START + timedelta(weeks=i) for i in range(WEEKS)]
OUT = '/home/claude/infera_domains/data'

# ---------- dimensions ----------
prods = [
    ('SKU-101','Performance Tees','Apparel','Mens',   0.11, 0.49, 2.2),
    ('SKU-102','Training Shorts','Apparel','Mens',    0.09, 0.47, 2.6),
    ('SKU-103','Compression Base Layer','Apparel','Mens', 0.07, 0.52, 1.6),
    ('SKU-104','Womens Leggings','Apparel','Womens',  0.12, 0.55, 2.0),
    ('SKU-105','Womens Sports Bra','Apparel','Womens',0.07, 0.56, 1.9),
    ('SKU-106','Fleece Hoodies','Apparel','Unisex',   0.10, 0.45, 3.4),
    ('SKU-107','Running Shoes','Footwear','Unisex',   0.13, 0.41, 1.8),
    ('SKU-108','Training Shoes','Footwear','Unisex',  0.08, 0.40, 1.7),
    ('SKU-109','Team Uniforms','Apparel','Team',      0.06, 0.38, 2.9),
    ('SKU-110','Backpacks & Bags','Accessories','Unisex',0.06, 0.44, 2.3),
    ('SKU-111','Caps & Headwear','Accessories','Unisex',0.05, 0.51, 1.5),
    ('SKU-112','Socks Multipack','Accessories','Unisex',0.06, 0.47, 1.2),
]
dim_product = pd.DataFrame([dict(
    product_id=p, product_name=n, product_category=c, gender_segment=g,
    revenue_mix_pct=round(m*100,1), target_gross_margin_pct=round(gm*100,1),
    seasonality_index=s, msrp_usd=round(float(RNG.uniform(22, 145)),2))
    for p,n,c,g,m,gm,s in prods])

custs = [
    ('CUS-01','National Sporting Chain','Wholesale','National',  0.19),
    ('CUS-02','Mass Retail Partner','Wholesale','National',      0.16),
    ('CUS-03','Department Store Group','Wholesale','National',   0.11),
    ('CUS-04','Specialty Run Network','Wholesale','Regional',    0.07),
    ('CUS-05','Off-Price Channel','Wholesale','National',        0.08),
    ('CUS-06','Team Dealer Network','Wholesale','Regional',      0.05),
    ('CUS-07','Pure-Play Ecommerce','Wholesale','Digital',       0.09),
    ('CUS-08','International Distributor','Wholesale','Intl',    0.06),
    ('CUS-09','Apex.com DTC','DTC','Digital',                    0.13),
    ('CUS-10','Apex Owned Retail','DTC','Owned',                 0.06),
]
dim_customer = pd.DataFrame([dict(
    customer_id=c, customer_name=n, channel=ch, region_scope=r,
    revenue_mix_pct=round(m*100,1),
    payment_terms_days=int(RNG.choice([30,45,60])) if ch=='Wholesale' else 0)
    for c,n,ch,r,m in custs])

woy = np.array([d.isocalendar()[1] for d in dates])
t = np.arange(WEEKS)
def season(strength):
    holiday = np.exp(-0.5*((woy-46)/3.5)**2)*0.8
    bts     = np.exp(-0.5*((woy-31)/3.0)**2)*0.55
    spring  = np.exp(-0.5*((woy-12)/4.0)**2)*0.35
    return 1 + strength*(holiday+bts+spring)

sellin, sellthru, promo_rows = [], [], []
for _, p in dim_product.iterrows():
    for _, c in dim_customer.iterrows():
        base = 23_000_000 * (p.revenue_mix_pct/100) * (c.revenue_mix_pct/100)
        seas = season(p.seasonality_index/3.0)
        trend = 1 + 0.0016*t
        promo = (RNG.random(WEEKS) < 0.14).astype(int)

        # sell-in is lumpy: wholesale ships on order cycles, DTC is smooth
        if c.channel == 'Wholesale':
            order_cycle = (np.sin(2*np.pi*t/4.0 + RNG.uniform(0,6.28)) > 0.1).astype(float)*0.9 + 0.35
        else:
            order_cycle = np.ones(WEEKS)
        ship_noise = RNG.normal(1, 0.11 if c.channel=='Wholesale' else 0.05, WEEKS)
        gross = base*seas*trend*order_cycle*ship_noise

        # ---- planted signals ----
        # A) Off-Price channel surge last 16 wks (brand-health risk: excess inventory dumped)
        if c.customer_id == 'CUS-05':
            gross[-16:] *= np.linspace(1.05, 2.1, 16)
        # B) Running Shoes sell-in holding up while sell-through falls (channel stuffing)
        # C) Womens Leggings DTC outperforming wholesale (shift in demand)
        if p.product_id == 'SKU-104' and c.channel == 'DTC':
            gross[-20:] *= np.linspace(1.02, 1.42, 20)

        trade = gross * np.clip(RNG.normal(0.115, 0.03, WEEKS) + promo*0.05, 0.02, None)
        if c.customer_id == 'CUS-05':
            trade[-16:] *= 1.35
        returns_u = np.clip(RNG.normal(0.038, 0.012, WEEKS), 0.004, None)
        net = gross - trade
        gm = p.target_gross_margin_pct/100 * RNG.normal(1, 0.022, WEEKS)
        if c.customer_id == 'CUS-05':
            gm[-16:] -= np.linspace(0.01, 0.09, 16)
        asp = p.msrp_usd * (0.52 if c.channel=='Wholesale' else 0.94) * RNG.normal(1, 0.03, WEEKS)
        ship_units = gross/asp
        fill = np.clip(RNG.normal(96.5, 2.6, WEEKS), 72, 100)
        otif = np.clip(fill - RNG.uniform(1.5, 5.0, WEEKS), 65, 100)

        # sell-through at the retailer (DTC: sell-in == sell-through)
        if c.channel == 'Wholesale':
            st_units = ship_units * np.clip(RNG.normal(0.93, 0.09, WEEKS), 0.5, 1.4)
            if p.product_id == 'SKU-107':
                st_units[-18:] *= np.linspace(0.98, 0.66, 18)      # signal B
        else:
            st_units = ship_units*RNG.normal(1, 0.02, WEEKS)
        retail_price = p.msrp_usd*np.clip(RNG.normal(0.93, 0.05, WEEKS) - promo*0.12, 0.45, 1.05)
        st_dollars = st_units*retail_price

        on_hand = np.zeros(WEEKS); inv = ship_units[0]*3.2
        for i in range(WEEKS):
            inv = max(inv + ship_units[i] - st_units[i], ship_units[i]*0.4)
            on_hand[i] = inv
        wos = on_hand/np.clip(pd.Series(st_units).rolling(4, min_periods=1).mean().values, 1, None)
        acv = np.clip(RNG.normal(78, 9, WEEKS) + (p.revenue_mix_pct-8)*1.2, 25, 99)

        for i, d in enumerate(dates):
            sellin.append((d.isoformat(), d.isocalendar()[0], d.isocalendar()[1],
                           c.customer_id, p.product_id,
                           int(ship_units[i]), round(float(gross[i]),2), round(float(trade[i]),2),
                           round(float(net[i]),2), round(float(gm[i])*100,2),
                           int(ship_units[i]*returns_u[i]), round(float(gross[i]*returns_u[i]),2),
                           round(float(asp[i]),2), round(float(fill[i]),1), round(float(otif[i]),1),
                           int(promo[i])))
            sellthru.append((d.isoformat(), c.customer_id, p.product_id,
                             int(st_units[i]), round(float(st_dollars[i]),2),
                             int(on_hand[i]), round(float(wos[i]),1),
                             round(float(acv[i]),1), round(float(retail_price[i]),2),
                             int(promo[i])))

df_sellin = pd.DataFrame(sellin, columns=[
    'week_start_date','fiscal_year','fiscal_week','customer_id','product_id',
    'shipped_units','gross_sales','trade_spend','net_sales','gross_margin_pct',
    'return_units','return_dollars','avg_selling_price','fill_rate_pct','otif_pct','promo_flag'])
df_sellthru = pd.DataFrame(sellthru, columns=[
    'week_start_date','customer_id','product_id','pos_units','pos_dollars',
    'retailer_on_hand_units','weeks_of_supply','acv_distribution_pct',
    'avg_retail_price','retail_promo_flag'])

# trade promotion events
ev = []
for k in range(140):
    c = dim_customer.sample(1, random_state=int(RNG.integers(1e6))).iloc[0]
    p = dim_product.sample(1, random_state=int(RNG.integers(1e6))).iloc[0]
    wk = dates[int(RNG.integers(0, WEEKS-4))]
    spend = float(RNG.uniform(45_000, 620_000))
    lift = float(RNG.uniform(-0.05, 0.62))
    ev.append((f'PROMO-{3000+k}', wk.isoformat(), int(RNG.choice([1,2,3,4])),
               c.customer_id, p.product_id,
               str(RNG.choice(['TPR','Feature','Display','Feature+Display','BOGO','Endcap'])),
               round(spend,2), round(spend*(1+lift)*RNG.uniform(1.4,3.1),2),
               round(lift*100,1), round(float(RNG.uniform(-18, 46)),1)))
df_promo = pd.DataFrame(ev, columns=[
    'promo_id','week_start_date','duration_weeks','customer_id','product_id','promo_type',
    'trade_spend','incremental_revenue','volume_lift_pct','promo_roi_pct'])

dim_product.to_csv(f'{OUT}/cpg_dim_product.csv', index=False)
dim_customer.to_csv(f'{OUT}/cpg_dim_customer.csv', index=False)
df_sellin.to_csv(f'{OUT}/cpg_fact_sellin_week.csv', index=False)
df_sellthru.to_csv(f'{OUT}/cpg_fact_sellthrough_week.csv', index=False)
df_promo.to_csv(f'{OUT}/cpg_fact_trade_promo.csv', index=False)
print('sellin',len(df_sellin),'sellthru',len(df_sellthru),'promo',len(df_promo))
print('annual net revenue $B', round(df_sellin.net_sales.sum()/2/1e9,2))
