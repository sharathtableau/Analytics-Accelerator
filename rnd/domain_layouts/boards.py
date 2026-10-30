"""R&D: domain-native dashboard boards drawn from the INFERA pack data (real numbers, not mock values)."""
import pandas as pd, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from datetime import timedelta

D = "/mnt/user-data/uploads/files (9)/infera_vertical_packs/infera_vertical_packs/data/"
OUT = "/mnt/user-data/outputs/"
BLUE, ORANGE, AQUA, YELLOW, MAG, GREEN, VIOLET, RED = "#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"
GRAY, INK, INK2, SURF, GRID = "#b9b8b2", "#0b0b0b", "#52514e", "#fcfcfb", "#e6e5e0"
CRIT, GOOD, WARN = "#d03b3b", "#0ca30c", "#fab219"
SHIFT = timedelta(weeks=5, days=6)   # pack week start 2026-09-14 -> live week ending 2026-10-18

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9.5, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
                     "xtick.color": INK2, "ytick.color": INK2, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.grid": True, "grid.color": GRID, "grid.linewidth": .7, "axes.axisbelow": True,
                     "axes.titlesize": 11, "axes.titleweight": "bold", "axes.titlelocation": "left",
                     "axes.titlecolor": INK, "figure.facecolor": "#f9f9f7", "axes.facecolor": SURF, "legend.frameon": False})


def sub(ax, text):
    ax.text(0, 1.02, text, transform=ax.transAxes, fontsize=8.6, color=INK2, va="bottom")


def money(v, d=1):
    a = abs(v)
    return (f"${v/1e9:.{d}f}B" if a >= 1e9 else f"${v/1e6:.{d}f}M" if a >= 1e6 else f"${v/1e3:.0f}K" if a >= 1e3 else f"${v:.0f}")


def spread(vals, gap):
    """Nudge label y-positions apart (keeps order), so end-of-line / scatter labels never overlap."""
    order = sorted(range(len(vals)), key=lambda i: vals[i])
    out = list(vals)
    for k in range(1, len(order)):
        i, j = order[k], order[k - 1]
        if out[i] - out[j] < gap:
            out[i] = out[j] + gap
    return out


def end_labels(ax, x, items, gap):
    """items: [(y, text, highlight)] drawn at x with de-overlapped y."""
    ys = spread([y for y, _, _ in items], gap)
    for (y, t, hl), yy in zip(items, ys):
        ax.text(x, yy, t, fontsize=8.3, va="center", color=INK if hl else INK2, fontweight="bold" if hl else "normal")


def clip_dates(ax, last):
    ax.set_xticks([t for t in ax.get_xticks() if t <= matplotlib.dates.date2num(last)])


def board(title, subtitle, n=6):
    fig, axes = plt.subplots(3, 2, figsize=(15, 15.5))
    fig.suptitle(title, x=.04, y=.985, ha="left", fontsize=17, fontweight="bold", color=INK)
    fig.text(.04, .962, subtitle, fontsize=10.5, color=INK2)
    fig.subplots_adjust(left=.07, right=.97, top=.915, bottom=.065, hspace=.62, wspace=.27)
    return fig, axes.flatten()


def waterfall(ax, steps, fmt, colors=None):
    """steps: [(label, value, kind)] kind in start/up/down/end"""
    run, xs = 0, []
    for i, (lab, v, kind) in enumerate(steps):
        if kind in ("start", "end"):
            ax.bar(i, v, color=BLUE, width=.6); run = v; top = v
            ax.text(i, v, fmt(v), ha="center", va="bottom", fontsize=9, color=INK, fontweight="bold")
        else:
            base = run if v >= 0 else run + v
            ax.bar(i, abs(v), bottom=base, color=GOOD if v >= 0 else CRIT, width=.6)
            ax.text(i, base + abs(v), ("+" if v >= 0 else "−") + fmt(abs(v)), ha="center", va="bottom", fontsize=9, color=INK)
            run += v
        xs.append(lab)
    ax.set_xticks(range(len(xs)), xs)


# ============================================================================================ FINANCE
pf = pd.read_csv(D + "finance_fact_portfolio_week.csv", parse_dates=["week_start_date"])
cr = pd.read_csv(D + "finance_fact_credit_week.csv", parse_dates=["week_start_date"])
dp = pd.read_csv(D + "finance_fact_deposits_week.csv", parse_dates=["week_start_date"])
aq = pd.read_csv(D + "finance_fact_acquisition_week.csv", parse_dates=["week_start_date"])
fprod = pd.read_csv(D + "finance_dim_product.csv"); fseg = pd.read_csv(D + "finance_dim_segment.csv")
for x in (pf, cr, dp, aq):
    x["we"] = x.week_start_date + SHIFT
W = sorted(pf.we.unique())
seg_name = dict(zip(fseg.segment_id, fseg.segment_name)); prod_name = dict(zip(fprod.product_id, fprod.product_name.str.replace("Keystone ", "")))
cards = fprod[fprod.product_type == "Credit Card"].product_id.tolist()

fig, A = board("Finance · Keystone Financial: domain-native layout (R&D)",
               "Drawn from the real pack data (rolling dates, newest week ending 18 Oct 2026). Each chart answers one owner's weekly question.")
# F1 accounts roll-forward (cards, last 13 weeks)
c = pf[pf.product_id.isin(cards)]
w0, w1 = W[-14], W[-1]
open_ = c[c.we == w0].active_accounts.sum(); close = c[c.we == w1].active_accounts.sum()
win = c[(c.we > w0) & (c.we <= w1)]
new, closed = win.new_accounts.sum(), win.closed_accounts.sum()
other = close - open_ - new + closed
ax = A[0]; ax.set_title("Card accounts roll-forward, last 13 weeks", pad=22)
sub(ax, "Head of Card Portfolio: where did the book grow or shrink? (opening + new − closed ± other = closing)")
f = lambda v: f"{v/1e6:.2f}M" if v >= 1e6 else f"{v/1e3:.0f}K"
steps = [("New accounts", new), ("Closed", -closed), ("Other movement", other), ("Net change", close - open_)]
run = 0
for i, (lab, v) in enumerate(steps):
    if lab == "Net change":
        ax.bar(i, v, color=BLUE, width=.6); top = v
    else:
        base = run if v >= 0 else run + v
        ax.bar(i, abs(v), bottom=base, color=GOOD if v >= 0 else CRIT, width=.6); run += v; top = base + abs(v)
    ax.text(i, top, ("+" if v >= 0 else "−") + f(abs(v)), ha="center", va="bottom", fontsize=9.5, color=INK, fontweight="bold" if lab == "Net change" else "normal")
ax.set_xticks(range(len(steps)), [x[0] for x in steps]); ax.axhline(0, color=INK2, lw=1)
ax.yaxis.set_major_formatter(lambda v, p: f"{v/1e3:.0f}K")
ax.set_xlabel(f"Opening {open_/1e6:.2f}M → closing {close/1e6:.2f}M active card accounts", fontsize=9); ax.set_ylim(0, (new) * 1.15)

# F2 delinquency by segment, highlight one
ax = A[1]; ax.set_title("Delinquency rate by segment, last 52 weeks", pad=22)
sub(ax, "Chief Credit Officer: one segment is turning: highlight it, mute the rest")
cc = cr.merge(pf[["we", "product_id", "segment_id", "ending_balance"]], on=["we", "product_id", "segment_id"])
g = cc[cc.we >= W[-52]].groupby(["we", "segment_id"])[["dpd_30_balance", "ending_balance"]].sum()
rate = (g.dpd_30_balance / g.ending_balance).unstack()
for s in rate.columns:
    hl = s == "SEG-03"
    ax.plot(rate.index, rate[s] * 100, color=ORANGE if hl else GRAY, lw=2.4 if hl else 1.2, zorder=3 if hl else 2)
end_labels(ax, rate.index[-1] + timedelta(days=5), [(rate[s].iloc[-1] * 100, seg_name[s] + (f"  {rate[s].iloc[-1]*100:.1f}%" if s == "SEG-03" else ""), s == "SEG-03") for s in rate.columns], .62)
ax.set_xlim(rate.index[0], rate.index[-1] + timedelta(days=110)); ax.yaxis.set_major_formatter(lambda v, p: f"{v:.0f}%")
ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b %y")); clip_dates(ax, rate.index[-1])

# F3 risk vs return quadrant
ax = A[2]; ax.set_title("Risk vs return by segment, last 13 weeks", pad=22)
sub(ax, "Leadership: who earns their risk? x = annualised loss rate, y = net interest margin, bubble = card balance")
r13 = cc[cc.we > W[-14]].groupby("segment_id")[["net_chargeoff_dollars", "ending_balance"]].sum()
loss = r13.net_chargeoff_dollars * 52 / r13.ending_balance
p13 = pf[(pf.we > W[-14]) & pf.product_id.isin(cards)].groupby("segment_id")[["net_interest_income", "cost_of_funds_dollars", "ending_balance"]].sum()
nim = (p13.net_interest_income - p13.cost_of_funds_dollars) * 52 / p13.ending_balance
bal = cc[cc.we == W[-1]].groupby("segment_id").ending_balance.sum()
ly_ = spread([nim[s] * 100 for s in loss.index], 1.3)
for s, yl in zip(loss.index, ly_):
    ax.scatter(loss[s] * 100, nim[s] * 100, s=bal[s] / bal.max() * 1600, color=ORANGE if s == "SEG-03" else BLUE, alpha=.75, edgecolor=SURF, lw=2)
    ax.text(loss[s] * 100 + 1.2, yl + .6, seg_name[s], fontsize=8.5, color=INK)
ax.axvline(np.median(loss) * 100, color=GRAY, ls="--", lw=1); ax.axhline(np.median(nim) * 100, color=GRAY, ls="--", lw=1)
ax.set_xlabel("Annualised loss rate"); ax.set_ylabel("Net interest margin")
ax.xaxis.set_major_formatter(lambda v, p: f"{v:.0f}%"); ax.yaxis.set_major_formatter(lambda v, p: f"{v:.0f}%")

# F4 rate paid vs competitor, gap shading
ax = A[3]; ax.set_title("Mass Affluent Saver: our rate vs competitors, last 26 weeks", pad=22)
sub(ax, "Head of Retail Deposits: red = competitors pay more (positive rate gap), and balances run off")
d5 = dp[(dp.segment_id == "SEG-05") & (dp.we >= W[-26])].copy()
d5["rp"] = d5.rate_paid_pct * d5.deposit_balance; d5["cp"] = d5.competitor_rate_pct * d5.deposit_balance
g5 = d5.groupby("we")[["rp", "cp", "deposit_balance"]].sum()
ours, comp = g5.rp / g5.deposit_balance, g5.cp / g5.deposit_balance
ax.plot(ours.index, ours, color=BLUE, lw=2, label="Rate we pay")
ax.plot(comp.index, comp, color=INK2, lw=1.6, ls="--", label="Competitor rate")
ax.fill_between(ours.index, ours, comp, where=comp > ours, color=CRIT, alpha=.18, interpolate=True)
ax.legend(loc="lower left", fontsize=8.5); ax.yaxis.set_major_formatter(lambda v, p: f"{v:.2f}%")
ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b %y"))
chg = (g5.deposit_balance.iloc[-1] / g5.deposit_balance.iloc[-16] - 1) * 100
ax.text(.99, .95, f"Balance {chg:+.1f}% in 15 weeks", transform=ax.transAxes, ha="right", va="top", fontsize=9.5, color=CRIT, fontweight="bold")

# F5 rewards ratio vs threshold band
ax = A[4]; ax.set_title("Rewards-to-interchange by card, breach line 0.85", pad=22)
sub(ax, "Head of Card Portfolio: the governed rule is drawn on the chart, not just in an alert")
p4 = pf[pf.product_id.isin(cards) & (pf.we >= W[-30])].groupby(["we", "product_id"])[["rewards_expense", "interchange_revenue"]].sum()
rr = (p4.rewards_expense / p4.interchange_revenue).unstack().rolling(4).mean().dropna()
ax.axhspan(.85, 1.2, color=CRIT, alpha=.07); ax.axhline(.85, color=CRIT, lw=1.2, ls="--")
ax.text(rr.index[0], .86, "breach (> 0.85)", color=CRIT, fontsize=8.5, va="bottom")
for p in rr.columns:
    hl = p == "PRD-02"
    ax.plot(rr.index, rr[p], color=ORANGE if hl else GRAY, lw=2.4 if hl else 1.2)
end_labels(ax, rr.index[-1] + timedelta(days=4), [(rr[p].iloc[-1], prod_name[p].replace(" Card", "") + (f"  {rr[p].iloc[-1]:.2f}" if p == "PRD-02" else ""), p == "PRD-02") for p in rr.columns], .022)
ax.set_ylim(.6, 1.12); ax.set_xlim(rr.index[0], rr.index[-1] + timedelta(days=70)); clip_dates(ax, rr.index[-1])
ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b %y")); ax.text(.0, -.17, "4-week rolling ratio", transform=ax.transAxes, fontsize=8, color=INK2)

# F6 acquisition funnel by channel
ax = A[5]; ax.set_title("Acquisition funnel by channel, last 13 weeks", pad=22)
sub(ax, "Head of Acquisition: share of applications approved and booked; cost per booking on the right")
a13 = aq[aq.we > W[-14]].groupby("channel")[["applications", "approvals", "bookings", "marketing_spend"]].sum()
a13["cac"] = a13.marketing_spend / a13.bookings; a13 = a13.sort_values("cac")
y = np.arange(len(a13))
ax.barh(y, 100, color="#e8eef8", height=.62, label="Applications (100%)")
ax.barh(y, a13.approvals / a13.applications * 100, color="#86b6ef", height=.62, label="Approved")
ax.barh(y, a13.bookings / a13.applications * 100, color=BLUE, height=.62, label="Booked")
for i, (ch, r) in enumerate(a13.iterrows()):
    ax.text(102, i, f"CAC ${r.cac:,.0f}", va="center", fontsize=9, color=INK)
ax.set_yticks(y, a13.index); ax.set_xlim(0, 125); ax.xaxis.set_major_formatter(lambda v, p: f"{v:.0f}%" if v <= 100 else "")
ax.legend(loc="lower center", bbox_to_anchor=(.45, -.22), ncol=3, fontsize=8.3); ax.grid(axis="y", visible=False)
fig.savefig(OUT + "RD_finance_board.png", dpi=110); plt.close(fig)

# ============================================================================================ CPG
si = pd.read_csv(D + "cpg_fact_sellin_week.csv", parse_dates=["week_start_date"])
st = pd.read_csv(D + "cpg_fact_sellthrough_week.csv", parse_dates=["week_start_date"])
pr = pd.read_csv(D + "cpg_fact_trade_promo.csv", parse_dates=["week_start_date"])
cu = pd.read_csv(D + "cpg_dim_customer.csv"); cp = pd.read_csv(D + "cpg_dim_product.csv")
for x in (si, st, pr):
    x["we"] = x.week_start_date + SHIFT
y_ = si.merge(st, on=["we", "week_start_date", "customer_id", "product_id"]).merge(cu, on="customer_id").merge(cp, on="product_id")
WC = sorted(y_.we.unique())
fig, A = board("CPG · Apex Athletic: domain-native layout (R&D)",
               "Drawn from the real pack data (rolling dates). Sell-in (shipments) vs sell-through (consumer purchases) is the core of every view.")
# C1 sell-in vs sell-through gap
ax = A[0]; ax.set_title("Running Shoes, wholesale: shipped vs bought by consumers", pad=22)
sub(ax, "National Account Manager: shaded = we shipped more than consumers bought (stock building at retail)")
rs = y_[(y_.product_id == "SKU-107") & (y_.channel == "Wholesale") & (y_.we >= WC[-36])].groupby("we")[["shipped_units", "pos_units"]].sum().rolling(4).mean().dropna()
ax.plot(rs.index, rs.shipped_units / 1e3, color=BLUE, lw=2, label="Shipped (sell-in)")
ax.plot(rs.index, rs.pos_units / 1e3, color=INK2, lw=1.6, ls="--", label="Bought (sell-through)")
ax.fill_between(rs.index, rs.shipped_units / 1e3, rs.pos_units / 1e3, where=rs.shipped_units > rs.pos_units, color=CRIT, alpha=.16, interpolate=True)
ax.legend(loc="upper left", fontsize=8.5); ax.yaxis.set_major_formatter(lambda v, p: f"{v:.0f}K"); ax.text(.0, -.17, "units, 4-week rolling", transform=ax.transAxes, fontsize=8, color=INK2)
ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b %y")); clip_dates(ax, rs.index[-1])

# C2 weeks of supply vs band (dot plot)
ax = A[1]; ax.set_title("Weeks of supply by account vs healthy band (6–12)", pad=22)
sub(ax, "Planner: dots outside the band need action. Running Shoes vs all products, last 4 weeks, wholesale only")
l4 = y_[(y_.we > WC[-5]) & (y_.channel == "Wholesale")]
allw = l4.groupby("customer_name").apply(lambda z: z.retailer_on_hand_units.sum() / z.pos_units.sum())
shoe = l4[l4.product_id == "SKU-107"].groupby("customer_name").apply(lambda z: z.retailer_on_hand_units.sum() / z.pos_units.sum())
order = shoe.sort_values().index; yy = np.arange(len(order))
ax.axvspan(6, 12, color=GOOD, alpha=.09); ax.axvline(14, color=CRIT, ls="--", lw=1); ax.text(14.2, -.45, "bloat > 14", color=CRIT, fontsize=8.3, va="center")
ax.hlines(yy, allw[order], shoe[order], color=GRID, lw=2)
ax.scatter(allw[order], yy, color=GRAY, s=60, zorder=3, label="All products"); ax.scatter(shoe[order], yy, color=ORANGE, s=70, zorder=3, label="Running Shoes")
ax.set_yticks(yy, order); ax.legend(loc="lower right", fontsize=8.5); ax.grid(axis="y", visible=False); ax.set_xlabel("weeks of supply")

# C3 gross-to-net waterfall
ax = A[2]; ax.set_title("Gross-to-net, last 13 weeks", pad=22)
sub(ax, "Revenue Growth Manager: what trade and returns take out of gross sales")
g13 = y_[y_.we > WC[-14]]
gs, ts, rd = g13.gross_sales.sum(), g13.trade_spend.sum(), g13.return_dollars.sum()
waterfall(ax, [("Gross sales", gs, "start"), ("Trade spend", -ts, "down"), ("Returns", -rd, "down"), ("Net of returns", gs - ts - rd, "end")], lambda v: money(v))
ax.set_ylim(0, gs * 1.08); ax.yaxis.set_major_formatter(lambda v, p: money(v, 0))

# C4 promo ROI bubbles by tactic
ax = A[3]; ax.set_title("Promotion ROI by tactic", pad=22)
sub(ax, "RGM: x = trade spend, y = spend-weighted ROI, bubble = incremental revenue; below 0 loses money")
pr["rx"] = pr.promo_roi_pct * pr.trade_spend
pt = pr.groupby("promo_type").agg(spend=("trade_spend", "sum"), rx=("rx", "sum"), inc=("incremental_revenue", "sum"), n=("promo_id", "count"))
pt["roi"] = pt.rx / pt.spend
for t, r in pt.iterrows():
    ax.scatter(r.spend / 1e6, r.roi, s=r.inc / pt.inc.max() * 1800, color=BLUE, alpha=.7, edgecolor=SURF, lw=2)
    ax.annotate(f"{t} ({r.n:.0f})", (r.spend / 1e6, r.roi), xytext=(9, 6), textcoords="offset points", fontsize=8.5)
ax.axhline(0, color=CRIT, lw=1); ax.set_ylim(-1, pt.roi.max() + 4); ax.set_xlabel("trade spend ($M)"); ax.yaxis.set_major_formatter(lambda v, p: f"{v:.0f}%")

# C5 distribution vs velocity
ax = A[4]; ax.set_title("Distribution vs velocity by product line, last 13 weeks", pad=22)
sub(ax, "Brand Director: low velocity at high distribution = a selling problem, not a listing problem")
d13 = y_[y_.we > WC[-14]].copy(); d13["acvx"] = d13.acv_distribution_pct * d13.pos_dollars
dv = d13.groupby("product_name").agg(acvx=("acvx", "sum"), pos=("pos_dollars", "sum"))
dv["acv"] = dv.acvx / dv.pos; dv["vel"] = dv.pos / 13 / dv.acv
ax.scatter(dv.acv, dv.vel / 1e3, s=90, color=BLUE, edgecolor=SURF, lw=2, zorder=3)
yl = spread(list(dv.vel / 1e3), 2.2)
for (n, r), yy in zip(dv.iterrows(), yl):
    ax.text(r.acv + .12, yy, n, fontsize=8, va="center", color=INK)
ax.axvline(dv.acv.median(), color=GRAY, ls="--", lw=1); ax.axhline(dv.vel.median() / 1e3, color=GRAY, ls="--", lw=1)
ax.set_xlabel("ACV distribution (POS-weighted %)"); ax.set_ylabel("weekly POS $ per ACV point ($K)")

# C6 channel mix stacked share
ax = A[5]; ax.set_title("Net sales mix by channel, last 52 weeks", pad=22)
sub(ax, "Brand Director: off-price growing is a warning (excess stock cleared at lower margin)")
y_["ctype"] = np.where(y_.channel == "DTC", "DTC", np.where(y_.customer_name.str.contains("Off-Price"), "Off-price", "Wholesale partners"))
mx = y_[y_.we >= WC[-52]].groupby(["we", "ctype"]).net_sales.sum().unstack().rolling(4).mean().dropna()
sh = mx.div(mx.sum(axis=1), axis=0) * 100
cols = ["Wholesale partners", "DTC", "Off-price"]; colr = [BLUE, AQUA, ORANGE]
ax.stackplot(sh.index, [sh[c] for c in cols], colors=colr, labels=cols, edgecolor=SURF, lw=1.5)
ax.set_ylim(0, 100); ax.yaxis.set_major_formatter(lambda v, p: f"{v:.0f}%"); ax.legend(loc="lower left", fontsize=8.5, ncol=3)
ax.text(sh.index[-1], 100 - sh["Off-price"].iloc[-1] / 2, f" Off-price {sh['Off-price'].iloc[-1]:.1f}%", fontsize=9, color=INK, va="center", fontweight="bold")
ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b %y")); ax.set_xlim(sh.index[0], sh.index[-1] + timedelta(days=70)); clip_dates(ax, sh.index[-1])
fig.savefig(OUT + "RD_cpg_board.png", dpi=110); plt.close(fig)

# ============================================================================================ RETAIL (sample)
rf = pd.read_csv(D + "retail_fact_store_category_week.csv", parse_dates=["week_start_date"])
rdg = pd.read_csv(D + "retail_fact_digital_week.csv", parse_dates=["week_start_date"])
rs_ = pd.read_csv(D + "retail_dim_store.csv"); rc = pd.read_csv(D + "retail_dim_category.csv")
rf = rf.merge(rs_, on="store_id").merge(rc, on="category_id"); rdg = rdg.merge(rc, on="category_id")
WR = sorted(rf.week_start_date.unique())
cur, ly = WR[-13:], [w - np.timedelta64(364, "D") for w in WR[-13:]]
fig, A = board("Retail: domain-native layout (R&D, sample retail data from the pack)",
               "Harborline's real data lives in Snowflake; this board uses the pack's retail sample to show the retail visual language.")
# R1 sales driver tree (YoY % by driver)
ax = A[0]; ax.set_title("What moved sales vs last year: traffic × conversion × basket", pad=22)
sub(ax, "Regional Ops Director: sales = traffic × conversion × average basket; last 13 weeks vs same weeks last year")
def agg(ws): z = rf[rf.week_start_date.isin(ws)]; return z.net_sales.sum(), z.customer_traffic.sum(), z.transactions.sum()
s1, t1, x1 = agg(cur); s0, t0, x0 = agg(ly)
parts = [("Traffic", t1 / t0 - 1), ("Conversion", (x1 / t1) / (x0 / t0) - 1), ("Basket", (s1 / x1) / (s0 / x0) - 1), ("Net sales", s1 / s0 - 1)]
yy = np.arange(len(parts))[::-1]
for (lab, v), yv in zip(parts, yy):
    ax.barh(yv, v * 100, color=(BLUE if lab == "Net sales" else (GOOD if v >= 0 else CRIT)), height=.55)
    ax.text(v * 100 + (.15 if v >= 0 else -.15), yv, f"{v*100:+.1f}%", va="center", ha="left" if v >= 0 else "right", fontsize=9.5, color=INK)
ax.set_yticks(yy, [p[0] for p in parts]); ax.axvline(0, color=INK2, lw=1); ax.grid(axis="y", visible=False)
ax.xaxis.set_major_formatter(lambda v, p: f"{v:.0f}%")
# R2 region x category growth heatmap (diverging)
ax = A[1]; ax.set_title("Sales growth vs last year: region × category", pad=22)
sub(ax, "Category Manager: one cell lights up (Southwest Apparel) - a map, not a list")
a = rf[rf.week_start_date.isin(cur)].groupby(["region", "category_name"]).net_sales.sum()
b = rf[rf.week_start_date.isin(ly)].groupby(["region", "category_name"]).net_sales.sum()
gm = ((a / b - 1) * 100).unstack()
lim = max(abs(gm.min().min()), abs(gm.max().max()))
im = ax.imshow(gm.values, cmap=matplotlib.colors.LinearSegmentedColormap.from_list("d", [CRIT, "#f0efec", BLUE]), vmin=-lim, vmax=lim, aspect="auto")
ax.set_xticks(range(len(gm.columns)), [c.replace(" & ", "/") for c in gm.columns], rotation=35, ha="right", fontsize=8)
ax.set_yticks(range(len(gm.index)), gm.index); ax.grid(False)
for i in range(gm.shape[0]):
    for j in range(gm.shape[1]):
        ax.text(j, i, f"{gm.values[i,j]:+.0f}", ha="center", va="center", fontsize=7.5, color=INK)
# R3 margin vs growth quadrant by category
ax = A[2]; ax.set_title("Category margin vs growth", pad=22)
sub(ax, "Category Manager: growing at the expense of margin? (bubble = sales, last 13 weeks)")
z1 = rf[rf.week_start_date.isin(cur)].copy(); z1["gmx"] = z1.gross_margin_pct * z1.net_sales
z0 = rf[rf.week_start_date.isin(ly)].copy(); z0["gmx"] = z0.gross_margin_pct * z0.net_sales
c1 = z1.groupby("category_name")[["net_sales", "gmx"]].sum(); c0 = z0.groupby("category_name")[["net_sales", "gmx"]].sum()
gro = (c1.net_sales / c0.net_sales - 1) * 100; mar = c1.gmx / c1.net_sales; dmar = mar - c0.gmx / c0.net_sales
for n in c1.index:
    odd = dmar[n] < -1 or gro[n] < 4.5
    ax.scatter(gro[n], dmar[n], s=c1.net_sales[n] / c1.net_sales.max() * 1500, color=ORANGE if dmar[n] < -2 else (BLUE if odd else GRAY), alpha=.72, edgecolor=SURF, lw=2)
    if odd:
        ax.annotate(f"{n}  ({gro[n]:+.1f}%, {dmar[n]:+.1f} pts)", (gro[n], dmar[n]), xytext=(-10, -22 if dmar[n] > -1 else 14), textcoords="offset points", fontsize=8.5, ha="right" if gro[n] > 5 else "left", color=INK)
ax.text(.98, .8, "8 other categories: +5% to +7%, margin flat", transform=ax.transAxes, ha="right", fontsize=8.5, color=INK2)
ax.axhline(0, color=GRAY, ls="--", lw=1); ax.axvline(0, color=GRAY, ls="--", lw=1)
ax.set_xlabel("sales growth vs last year"); ax.set_ylabel("margin change (pts)"); ax.xaxis.set_major_formatter(lambda v, p: f"{v:.0f}%")
# R4 inventory build by region (highlight)
ax = A[3]; ax.set_title("Toys & Seasonal on-hand units by region, indexed", pad=22)
sub(ax, "Inventory Planner: Midwest is over-bought; index = 100 at the start of the window")
ts_ = rf[(rf.category_name.str.contains("Toys")) & (rf.week_start_date >= WR[-26])].groupby(["week_start_date", "region"]).on_hand_units.sum().unstack()
ix = ts_ / ts_.iloc[0] * 100
for r in ix.columns:
    hl = r == "Midwest"
    ax.plot(ix.index, ix[r], color=ORANGE if hl else GRAY, lw=2.4 if hl else 1.2)
end_labels(ax, ix.index[-1] + timedelta(days=3), [(ix[r].iloc[-1], r, r == "Midwest") for r in ix.columns], 4.5)
ax.axhline(100, color=INK2, lw=.8); ax.set_xlim(ix.index[0], ix.index[-1] + timedelta(days=32)); clip_dates(ax, ix.index[-1])
ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b %y"))
# R5 markdown & shrink as % of sales by region
ax = A[4]; ax.set_title("Margin leakage by region, last 13 weeks", pad=22)
sub(ax, "Ops Director: markdowns and shrink as % of sales, stacked")
l = rf[rf.week_start_date.isin(cur)].groupby("region")[["markdown_dollars", "shrink_dollars", "net_sales"]].sum()
l["md"] = l.markdown_dollars / l.net_sales * 100; l["sh"] = l.shrink_dollars / l.net_sales * 100; l = l.sort_values("md")
yy = np.arange(len(l))
ax.barh(yy, l.md, color=BLUE, height=.55, label="Markdowns"); ax.barh(yy, l.sh, left=l.md, color=YELLOW, height=.55, label="Shrink")
for i, (_, r) in enumerate(l.iterrows()):
    ax.text(r.md + r.sh + .05, i, f"{r.md + r.sh:.1f}%", va="center", fontsize=9)
ax.set_yticks(yy, l.index); ax.set_xlim(0, (l.md + l.sh).max() * 1.15); ax.legend(loc="lower center", bbox_to_anchor=(.45, -.22), ncol=2, fontsize=8.5); ax.grid(axis="y", visible=False); ax.xaxis.set_major_formatter(lambda v, p: f"{v:.0f}%")
# R6 fulfilment mix
ax = A[5]; ax.set_title("Digital fulfilment mix by category, last 13 weeks", pad=22)
sub(ax, "VP Omnichannel: how orders reach customers (share of digital orders)")
dg = rdg[rdg.week_start_date.isin(cur)].copy()
for c in ("pct_ship_to_home", "pct_buy_online_pickup_store", "pct_same_day_delivery"):
    dg[c + "_n"] = dg[c] * dg.digital_orders
fm = dg.groupby("category_name")[["pct_ship_to_home_n", "pct_buy_online_pickup_store_n", "pct_same_day_delivery_n", "digital_orders"]].sum()
fm = fm.div(fm.digital_orders, axis=0).drop(columns="digital_orders").sort_values("pct_same_day_delivery_n")
yy = np.arange(len(fm)); left = np.zeros(len(fm))
for c, lab, col in zip(fm.columns, ["Ship to home", "Pick up in store", "Same day"], [BLUE, AQUA, ORANGE]):
    ax.barh(yy, fm[c], left=left, color=col, height=.6, label=lab, edgecolor=SURF, lw=1.5); left += fm[c]
ax.set_yticks(yy, fm.index, fontsize=8); ax.set_xlim(0, 100); ax.xaxis.set_major_formatter(lambda v, p: f"{v:.0f}%")
ax.legend(loc="lower center", bbox_to_anchor=(.45, -.22), ncol=3, fontsize=8.3); ax.grid(axis="y", visible=False)
fig.savefig(OUT + "RD_retail_board.png", dpi=110); plt.close(fig)
print("ok")
