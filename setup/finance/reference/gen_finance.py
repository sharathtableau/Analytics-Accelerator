"""Keystone Financial (consumer card issuer + retail deposits) — 104 weeks."""
import numpy as np, pandas as pd
from datetime import date, timedelta

RNG = np.random.default_rng(31337)
WEEKS = 104
END = date(2026, 9, 14)
START = END - timedelta(weeks=WEEKS - 1)
dates = [START + timedelta(weeks=i) for i in range(WEEKS)]
OUT = '/home/claude/infera_domains/data'

prods = [
    ('PRD-01','Keystone Cash Rewards Card','Credit Card','Mainstream', 0.22, 0.2290),
    ('PRD-02','Keystone Travel Signature Card','Credit Card','Premium', 0.17, 0.2090),
    ('PRD-03','Keystone Secured Card','Credit Card','Subprime',        0.06, 0.2890),
    ('PRD-04','Keystone Small Business Card','Credit Card','Business',  0.11, 0.2190),
    ('PRD-05','Keystone High-Yield Savings','Deposit','Mainstream',     0.28, 0.0000),
    ('PRD-06','Keystone 12-Month CD','Deposit','Mainstream',            0.16, 0.0000),
]
dim_product = pd.DataFrame([dict(
    product_id=p, product_name=n, product_type=t, tier=tier,
    portfolio_mix_pct=round(m*100,1), avg_apr_pct=round(a*100,2))
    for p,n,t,tier,m,a in prods])

segs = [
    ('SEG-01','Prime Revolver',      760, 0.24, 'High balance, carries balance, rate sensitive'),
    ('SEG-02','Prime Transactor',    780, 0.21, 'Pays in full, interchange-driven, rewards sensitive'),
    ('SEG-03','Near-Prime Revolver', 665, 0.17, 'Moderate balance, elevated loss rate'),
    ('SEG-04','Subprime Builder',    595, 0.09, 'Credit building, highest loss rate'),
    ('SEG-05','Mass Affluent Saver', 775, 0.18, 'Deposit heavy, highly rate sensitive'),
    ('SEG-06','Small Business Owner',720, 0.11, 'Mixed card and deposit, seasonal cash cycle'),
]
dim_segment = pd.DataFrame([dict(
    segment_id=s, segment_name=n, avg_fico=f, portfolio_mix_pct=round(m*100,1), description=d)
    for s,n,f,m,d in segs])

t = np.arange(WEEKS)
woy = np.array([d.isocalendar()[1] for d in dates])
TOTAL = 28_000_000_000

# benchmark rate drifts down then stabilises
fed = 5.25 - np.clip((t-20)*0.021, 0, 1.55)
comp_rate = fed - 0.7 + RNG.normal(0, 0.05, WEEKS)

port, credit, dep, acq = [], [], [], []
for _, p in dim_product.iterrows():
    for _, s in dim_segment.iterrows():
        base = TOTAL*(p.portfolio_mix_pct/100)*(s.portfolio_mix_pct/100)
        if p.product_type=='Deposit' and s.segment_id in ('SEG-03','SEG-04'): base *= 0.3
        if p.product_type=='Credit Card' and s.segment_id=='SEG-05': base *= 0.35

        holiday = 1 + 0.26*np.exp(-0.5*((woy-48)/3.0)**2)
        tax     = 1 + 0.11*np.exp(-0.5*((woy-14)/3.0)**2)
        drift = 1 + 0.0011*t
        bal = base*drift*RNG.normal(1, 0.012, WEEKS)

        # ---- planted signals ----
        # D) Mass Affluent Saver deposit runoff accelerating last 15 weeks
        if p.product_type=='Deposit' and s.segment_id=='SEG-05':
            bal[-15:] *= np.linspace(0.995, 0.86, 15)
        # E) Near-Prime delinquency deterioration last 22 weeks
        # F) Travel card rewards cost outrunning interchange last 18 weeks

        if p.product_type=='Credit Card':
            pv = bal*np.clip(RNG.normal(0.62, 0.05, WEEKS),0.3,1.2)*holiday*tax/4.3
            revolve = {'SEG-01':0.71,'SEG-02':0.08,'SEG-03':0.79,'SEG-04':0.86,
                       'SEG-05':0.12,'SEG-06':0.54}[s.segment_id]
            interchange = pv*RNG.normal(0.0168, 0.0006, WEEKS)
            rewards = pv*RNG.normal(0.0121, 0.0008, WEEKS)
            if p.product_id=='PRD-02':
                rewards[-18:] *= np.linspace(1.02, 1.48, 18)        # signal F
            nii = bal*revolve*(p.avg_apr_pct/100)/52
            cof = bal*(np.maximum(fed-0.45,0.3)/100)/52
        else:
            pv = np.zeros(WEEKS); interchange = np.zeros(WEEKS); rewards = np.zeros(WEEKS)
            revolve = 0.0
            paid = np.maximum(fed-0.55, 0.35)
            if s.segment_id=='SEG-05': paid = paid - 0.22        # underpricing vs market
            nii = bal*0.0088/52
            cof = bal*(paid/100)/52

        new_acct = np.clip(RNG.normal(bal/9.5e5, bal/4.5e6, WEEKS),0,None)
        closed = new_acct*np.clip(RNG.normal(0.62,0.12,WEEKS),0.2,1.6)
        if p.product_type=='Deposit' and s.segment_id=='SEG-05':
            closed[-15:] *= np.linspace(1.1, 2.4, 15)

        for i,d in enumerate(dates):
            port.append((d.isoformat(), d.isocalendar()[0], d.isocalendar()[1],
                         p.product_id, s.segment_id,
                         round(float(bal[i]),2), int(new_acct[i]), int(closed[i]),
                         int(bal[i]/RNG.uniform(2600,5200)),
                         round(float(pv[i]),2), round(float(interchange[i]),2),
                         round(float(rewards[i]),2), round(float(nii[i]),2),
                         round(float(cof[i]),2), round(revolve*100,1),
                         round(float(p.avg_apr_pct),2)))

        if p.product_type=='Credit Card':
            base_dq = {'SEG-01':0.021,'SEG-02':0.006,'SEG-03':0.052,
                       'SEG-04':0.094,'SEG-05':0.008,'SEG-06':0.034}[s.segment_id]
            dq = base_dq*RNG.normal(1,0.05,WEEKS)*(1+0.10*np.exp(-0.5*((woy-6)/4.0)**2))
            if s.segment_id=='SEG-03':
                dq[-22:] *= np.linspace(1.02, 1.72, 22)            # signal E
            d30 = bal*dq; d60 = d30*RNG.uniform(0.42,0.52,WEEKS); d90 = d60*RNG.uniform(0.55,0.68,WEEKS)
            nco = d90*RNG.uniform(0.22,0.31,WEEKS)
            rec = nco*RNG.uniform(0.09,0.17,WEEKS)
            for i,d in enumerate(dates):
                credit.append((d.isoformat(), p.product_id, s.segment_id,
                               round(float(d30[i]),2), round(float(d60[i]),2), round(float(d90[i]),2),
                               round(float(nco[i]),2), round(float(rec[i]),2),
                               round(float(nco[i]-rec[i]),2),
                               round(float(dq[i])*100,3),
                               round(float((nco[i]-rec[i])*52/bal[i])*100,3),
                               int(s.avg_fico + RNG.normal(0,6))))

        if p.product_type=='Deposit':
            mat = bal*np.where(p.product_id=='PRD-06', RNG.uniform(0.012,0.028,WEEKS), 0)
            runoff = bal*np.clip(RNG.normal(0.0075,0.002,WEEKS),0.001,None)
            if s.segment_id=='SEG-05': runoff[-15:] *= np.linspace(1.1,2.9,15)
            paid_r = np.maximum(fed-0.55,0.35) - (0.22 if s.segment_id=='SEG-05' else 0)
            for i,d in enumerate(dates):
                dep.append((d.isoformat(), p.product_id, s.segment_id,
                            round(float(bal[i]),2), round(float(runoff[i]),2),
                            round(float(mat[i]),2),
                            round(float(bal[i]*RNG.uniform(0.004,0.011)),2),
                            round(float(paid_r[i]),3), round(float(comp_rate[i]),3),
                            round(float(comp_rate[i]-paid_r[i]),3)))

chans = ['Direct Mail','Digital Paid','Branch','Partner Referral','Organic Search']
for _,p in dim_product.iterrows():
    for ch in chans:
        s0 = float(RNG.uniform(120_000, 880_000))
        for i,d in enumerate(dates):
            spend = s0*RNG.normal(1,0.17)*(1+0.2*np.exp(-0.5*((woy[i]-4)/5.0)**2))
            apps = spend/RNG.uniform(38,96)
            appr = apps*RNG.uniform(0.34,0.71)
            book = appr*RNG.uniform(0.62,0.85)
            acq.append((d.isoformat(), p.product_id, ch, round(spend,2),
                        int(apps), int(appr), int(book),
                        round(spend/max(book,1),2),
                        round(float(RNG.uniform(380, 1450)),2)))

pd.DataFrame(port, columns=['week_start_date','fiscal_year','fiscal_week','product_id','segment_id',
    'ending_balance','new_accounts','closed_accounts','active_accounts','purchase_volume',
    'interchange_revenue','rewards_expense','net_interest_income','cost_of_funds_dollars',
    'revolve_rate_pct','apr_pct']).to_csv(f'{OUT}/finance_fact_portfolio_week.csv', index=False)
pd.DataFrame(credit, columns=['week_start_date','product_id','segment_id','dpd_30_balance',
    'dpd_60_balance','dpd_90_balance','gross_chargeoff_dollars','recovery_dollars',
    'net_chargeoff_dollars','delinquency_rate_pct','annualized_loss_rate_pct','avg_fico'
    ]).to_csv(f'{OUT}/finance_fact_credit_week.csv', index=False)
pd.DataFrame(dep, columns=['week_start_date','product_id','segment_id','deposit_balance',
    'runoff_dollars','maturing_dollars','new_money_dollars','rate_paid_pct',
    'competitor_rate_pct','rate_gap_pct']).to_csv(f'{OUT}/finance_fact_deposits_week.csv', index=False)
pd.DataFrame(acq, columns=['week_start_date','product_id','channel','marketing_spend',
    'applications','approvals','bookings','cost_per_booking','avg_initial_credit_line'
    ]).to_csv(f'{OUT}/finance_fact_acquisition_week.csv', index=False)
dim_product.to_csv(f'{OUT}/finance_dim_product.csv', index=False)
dim_segment.to_csv(f'{OUT}/finance_dim_segment.csv', index=False)
print('portfolio',len(port),'credit',len(credit),'deposits',len(dep),'acq',len(acq))
