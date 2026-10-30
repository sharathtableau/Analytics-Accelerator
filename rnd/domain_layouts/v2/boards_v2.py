"""R&D v2: research-backed domain views, drawn from the INFERA pack data. Reuses helpers from boards.py."""
import sys; sys.path.insert(0, "/home/claude/rnd")
from boards_helpers import *  # noqa

# ============================================================================================ FINANCE v2
pf = pd.read_csv(D + "finance_fact_portfolio_week.csv", parse_dates=["week_start_date"])
cr = pd.read_csv(D + "finance_fact_credit_week.csv", parse_dates=["week_start_date"])
dp = pd.read_csv(D + "finance_fact_deposits_week.csv", parse_dates=["week_start_date"])
fprod = pd.read_csv(D + "finance_dim_product.csv"); fseg = pd.read_csv(D + "finance_dim_segment.csv")
for x in (pf, cr, dp):
    x["we"] = x.week_start_date + SHIFT
W = sorted(pf.we.unique())
seg = dict(zip(fseg.segment_id, fseg.segment_name)); prod = dict(zip(fprod.product_id, fprod.product_name.str.replace("Keystone ", "")))
cards = fprod[fprod.product_type == "Credit Card"].product_id.tolist()
cc = cr.merge(pf[["we", "product_id", "segment_id", "ending_balance"]], on=["we", "product_id", "segment_id"])

fig, A = board("Finance · Keystone Financial: research-backed views (v2)",
               "Credit-risk views follow what card risk teams and the OCC expect (delinquency by segment, roll rates, ageing, losses); deposits follow pricing practice.")
fig.subplots_adjust(left=.12, wspace=.36)
# 1 delinquency trend (kept)
ax = A[0]; ax.set_title("30+ delinquency rate by segment, last 52 weeks", pad=22)
sub(ax, "CCO · is any segment deteriorating? Portfolio averages hide it, so show every segment, highlight the outlier")
g = cc[cc.we >= W[-52]].groupby(["we", "segment_id"])[["dpd_30_balance", "ending_balance"]].sum()
rate = (g.dpd_30_balance / g.ending_balance).unstack() * 100
for s in rate.columns:
    hl = s == "SEG-03"; ax.plot(rate.index, rate[s], color=ORANGE if hl else GRAY, lw=2.4 if hl else 1.2, zorder=3 if hl else 2)
end_labels(ax, rate.index[-1] + timedelta(days=5), [(rate[s].iloc[-1], seg[s] + (f"  {rate[s].iloc[-1]:.1f}%" if s == "SEG-03" else ""), s == "SEG-03") for s in rate.columns], .62)
ax.set_xlim(rate.index[0], rate.index[-1] + timedelta(days=110)); ax.yaxis.set_major_formatter(lambda v, p: f"{v:.0f}%")
ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b %y")); clip_dates(ax, rate.index[-1])

# 2 roll (flow) rates
ax = A[1]; ax.set_title("Roll rates by segment: now vs a year ago", pad=22)
sub(ax, "CCO · are past-due balances rolling deeper? share of a bucket that rolls to the next one 4 weeks later")
gb = cr.groupby(["we", "segment_id"])[["dpd_30_balance", "dpd_60_balance", "dpd_90_balance"]].sum().unstack()
r1 = gb["dpd_60_balance"] / gb["dpd_30_balance"].shift(4); r2 = gb["dpd_90_balance"] / gb["dpd_60_balance"].shift(4)
now1, ly1 = r1.iloc[-8:].mean(), r1.iloc[-60:-52].mean(); now2, ly2 = r2.iloc[-8:].mean(), r2.iloc[-60:-52].mean()
order = list((now2 - ly2).sort_values().index); yy = np.arange(len(order))
for k, (now, ly, off, lab) in enumerate([(now1, ly1, -.17, "30→60"), (now2, ly2, .17, "60→90")]):
    for i, s in enumerate(order):
        ax.plot([ly[s] * 100, now[s] * 100], [i + off] * 2, color=GRID, lw=3, zorder=1)
        worse = now[s] - ly[s] > .03
        ax.scatter(ly[s] * 100, i + off, color=GRAY, s=36, zorder=2)
        ax.scatter(now[s] * 100, i + off, color=(CRIT if worse else (BLUE if k == 0 else VIOLET)), s=52, zorder=3, marker="o" if k == 0 else "D")
ax.set_yticks(yy, [seg[s] for s in order]); ax.grid(axis="y", visible=False); ax.xaxis.set_major_formatter(lambda v, p: f"{v:.0f}%")
ax.legend(handles=[plt.Line2D([], [], marker="o", ls="", color=BLUE, label="30→60 now"), plt.Line2D([], [], marker="D", ls="", color=VIOLET, label="60→90 now"),
                   plt.Line2D([], [], marker="o", ls="", color=GRAY, label="a year ago"), plt.Line2D([], [], marker="o", ls="", color=CRIT, label="worse by > 3 pts")],
          loc="lower center", bbox_to_anchor=(.45, -.24), ncol=4, fontsize=8.3)

# 3 ageing of past-due balances (stacked bars, 4-week periods), Near-Prime
ax = A[2]; ax.set_title("Near-Prime Revolver: past-due balances by age bucket", pad=22)
sub(ax, "CCO · is the problem early-stage (30) or already deep (90+)? End-of-period balances, every 4 weeks")
n3 = cr[(cr.segment_id == "SEG-03") & (cr.we >= W[-52])].groupby("we")[["dpd_30_balance", "dpd_60_balance", "dpd_90_balance"]].sum()
n3 = n3.iloc[::-4][::-1]
bot = np.zeros(len(n3)); xs = np.arange(len(n3))
for c, lab, col in [("dpd_30_balance", "30–59 days", "#86b6ef"), ("dpd_60_balance", "60–89 days", BLUE), ("dpd_90_balance", "90+ days", "#0d366b")]:
    ax.bar(xs, n3[c] / 1e6, bottom=bot, color=col, width=.7, label=lab, edgecolor=SURF, lw=1.2); bot += n3[c] / 1e6
ax.set_xticks(xs, [d.strftime("%d %b") for d in n3.index], fontsize=8, rotation=0); ax.yaxis.set_major_formatter(lambda v, p: f"${v:.0f}M")
ax.legend(loc="upper left", fontsize=8.5); ax.grid(axis="x", visible=False)
ax.text(.0, -.17, "30/60/90 are the pack's past-due balance columns; buckets as provided", transform=ax.transAxes, fontsize=8, color=INK2)

# 4 risk-adjusted margin
ax = A[3]; ax.set_title("Risk-adjusted yield by segment (cards), last 13 weeks", pad=22)
sub(ax, "Leadership · which segments earn their risk? (net interest + interchange − rewards − net losses) ÷ balance, annualised")
r13 = cc[cc.we > W[-14]].groupby("segment_id")[["net_chargeoff_dollars", "ending_balance"]].sum()
loss = r13.net_chargeoff_dollars * 52 / r13.ending_balance * 100
p13 = pf[(pf.we > W[-14]) & pf.product_id.isin(cards)].groupby("segment_id")[["net_interest_income", "interchange_revenue", "rewards_expense", "ending_balance"]].sum()
nim = (p13.net_interest_income + p13.interchange_revenue - p13.rewards_expense) * 52 / p13.ending_balance * 100
ram = (nim - loss).sort_values(); yy = np.arange(len(ram))
ax.barh(yy, ram, color=[CRIT if v < 0 else BLUE for v in ram], height=.6)
for i, s in enumerate(ram.index):
    ax.text(max(ram.max(), 0) + 1, i, f"{ram[s]:+.1f}%  = revenue {nim[s]:.1f}% − losses {loss[s]:.1f}%", va="center",
            ha="left", fontsize=8.6, color=CRIT if ram[s] < 0 else INK)
ax.set_yticks(yy, [seg[s] for s in ram.index]); ax.axvline(0, color=INK2, lw=1); ax.grid(axis="y", visible=False)
ax.set_xlim(min(ram.min(), 0) - 2, max(ram.max(), 0) + 30); ax.xaxis.set_major_formatter(lambda v, p: f"{v:.0f}%")

# 5 rewards ratio vs breach (kept)
ax = A[4]; ax.set_title("Rewards-to-interchange by card vs the 0.85 breach line", pad=22)
sub(ax, "Card P&L owner · the governed limit drawn on the chart; 4-week rolling")
p4 = pf[pf.product_id.isin(cards) & (pf.we >= W[-30])].groupby(["we", "product_id"])[["rewards_expense", "interchange_revenue"]].sum()
rr = (p4.rewards_expense / p4.interchange_revenue).unstack().rolling(4).mean().dropna()
ax.axhspan(.85, 1.2, color=CRIT, alpha=.07); ax.axhline(.85, color=CRIT, lw=1.2, ls="--"); ax.text(rr.index[0], .86, "breach (> 0.85)", color=CRIT, fontsize=8.5)
for p in rr.columns:
    ax.plot(rr.index, rr[p], color=ORANGE if p == "PRD-02" else GRAY, lw=2.4 if p == "PRD-02" else 1.2)
end_labels(ax, rr.index[-1] + timedelta(days=4), [(rr[p].iloc[-1], prod[p].replace(" Card", "") + (f"  {rr[p].iloc[-1]:.2f}" if p == "PRD-02" else ""), p == "PRD-02") for p in rr.columns], .022)
ax.set_ylim(.6, 1.12); ax.set_xlim(rr.index[0], rr.index[-1] + timedelta(days=70)); clip_dates(ax, rr.index[-1])
ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b %y"))

# 6 deposits: rate gap + 15-week balance change, one row per segment
ax = A[5]; ax.set_title("Deposits by segment: price position and what it costs", pad=22)
sub(ax, "Head of Deposits · rate gap (bars; > 0 = competitors pay more) and balance change over 15 weeks")
dp["gx"] = dp.rate_gap_pct * dp.deposit_balance
l4 = dp[dp.we > W[-5]].groupby("segment_id")[["gx", "deposit_balance"]].sum(); gap = l4.gx / l4.deposit_balance
bal = dp.groupby(["we", "segment_id"]).deposit_balance.sum().unstack(); chg = (bal.iloc[-1] / bal.iloc[-16] - 1) * 100
gap = gap.sort_values(); yy = np.arange(len(gap))
ax.barh(yy, gap * 100, color=[CRIT if v > 0 else BLUE for v in gap], height=.55)
for i, s in enumerate(gap.index):
    ax.text(gap.max() * 100 + 5, i, f"balance {chg[s]:+.1f}%", va="center", fontsize=9, color=CRIT if chg[s] < -5 else INK)
ax.set_yticks(yy, [seg[s] for s in gap.index]); ax.axvline(0, color=INK2, lw=1); ax.grid(axis="y", visible=False)
ax.set_xlim(gap.min() * 100 - 4, gap.max() * 100 + 30); ax.set_xlabel("rate gap, basis points")
fig.savefig(OUT + "RD2_finance.png", dpi=110); plt.close(fig)

# ============================================================================================ CPG v2
si = pd.read_csv(D + "cpg_fact_sellin_week.csv", parse_dates=["week_start_date"])
st = pd.read_csv(D + "cpg_fact_sellthrough_week.csv", parse_dates=["week_start_date"])
pr = pd.read_csv(D + "cpg_fact_trade_promo.csv", parse_dates=["week_start_date"])
cu = pd.read_csv(D + "cpg_dim_customer.csv"); cp = pd.read_csv(D + "cpg_dim_product.csv")
for x in (si, st, pr):
    x["we"] = x.week_start_date + SHIFT
y_ = si.merge(st, on=["we", "week_start_date", "customer_id", "product_id"]).merge(cu, on="customer_id").merge(cp, on="product_id")
WC = sorted(y_.we.unique())
fig, A = board("CPG · Apex Athletic: research-backed views (v2)",
               "Follows how CPG / syndicated-data analysts work: sales change = distribution × velocity, sell-in vs sell-out builds channel inventory, promotions judged event by event.")
fig.subplots_adjust(left=.12, wspace=.36)
# 1 distribution vs velocity decomposition
ax = A[0]; ax.set_title("Why consumer sales changed: distribution vs velocity", pad=22)
sub(ax, "Brand Director · POS \$ vs same 13 weeks last year = distribution (ACV) + velocity (\$ per ACV point)")
z = y_[y_.channel == "Wholesale"].copy(); z["acvx"] = z.acv_distribution_pct * z.pos_dollars
def agg(ws):
    q = z[z.we.isin(ws)].groupby("product_name").agg(pos=("pos_dollars", "sum"), acvx=("acvx", "sum")); q["acv"] = q.acvx / q.pos; q["vel"] = q.pos / q.acv; return q
a, b = agg(WC[-13:]), agg(WC[-65:-52])
de, ve = (a.acv - b.acv) * b.vel / 1e6, (a.vel - b.vel) * a.acv / 1e6
o = (de + ve).sort_values().index; yy = np.arange(len(o))
for i, n in enumerate(o):
    for v, col, start in [(de[n], AQUA, 0), (ve[n], BLUE, de[n] if np.sign(de[n]) == np.sign(ve[n]) else 0)]:
        ax.barh(i, v, left=start, color=col, height=.6)
    tot = de[n] + ve[n]; ax.text(max(tot, 0) + .3 if tot >= 0 else min(tot, 0) - .3, i, f"{(a.pos[n] / b.pos[n] - 1) * 100:+.0f}%", va="center",
                                  ha="left" if tot >= 0 else "right", fontsize=8.6, color=CRIT if tot < 0 else INK)
ax.set_yticks(yy, list(o), fontsize=8.3); ax.axvline(0, color=INK2, lw=1); ax.grid(axis="y", visible=False); ax.xaxis.set_major_formatter(lambda v, p: ("−" if v < 0 else "") + f"${abs(v):.0f}M")
ax.set_xlim(min((de + ve).min(), 0) - 3, (de + ve).max() + 2.5)
ax.legend(handles=[Patch(color=AQUA, label="distribution effect"), Patch(color=BLUE, label="velocity effect")], loc="lower right", fontsize=8.5)

# 2 channel inventory build
ax = A[1]; ax.set_title("Running Shoes: channel inventory build, last 26 weeks", pad=22)
sub(ax, "Account Manager · cumulative shipped − consumer units per account; rising = stock piling up")
rs = y_[(y_.product_id == "SKU-107") & (y_.channel == "Wholesale") & (y_.we >= WC[-26])].copy(); rs["d"] = rs.shipped_units - rs.pos_units
cum = rs.groupby(["we", "customer_name"]).d.sum().unstack().cumsum() / 1e3
for c in cum.columns:
    ax.plot(cum.index, cum[c], color=GRAY, lw=1.2)
tot = cum.sum(axis=1); ax.plot(tot.index, tot, color=ORANGE, lw=2.6)
top3 = cum.iloc[-1].sort_values().index[-3:]
end_labels(ax, cum.index[-1] + timedelta(days=4), [(tot.iloc[-1], f"All wholesale  +{tot.iloc[-1]:.0f}K units", True)] + [(cum[c].iloc[-1], f"{c} +{cum[c].iloc[-1]:.0f}K", False) for c in top3], max(tot.iloc[-1], 1) * .05)
ax.axhline(0, color=INK2, lw=1); ax.set_xlim(cum.index[0], cum.index[-1] + timedelta(days=80)); clip_dates(ax, cum.index[-1])
ax.yaxis.set_major_formatter(lambda v, p: f"{v:.0f}K"); ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b %y"))

# 3 sell-through ratio heatmap account x product (diverging around 1.0)
ax = A[2]; ax.set_title("Sell-through ratio: account × product line, last 13 weeks", pad=22)
sub(ax, "Planner · consumer units ÷ shipped units vs the typical ratio; red = shipping ahead of demand")
q = y_[(y_.we > WC[-14]) & (y_.channel == "Wholesale")].groupby(["customer_name", "product_name"])[["pos_units", "shipped_units"]].sum()
hm = (q.pos_units / q.shipped_units).unstack()
hm = hm[hm.mean().sort_values().index]
med = float(np.nanmedian(hm.values))
im = ax.imshow(hm.values, cmap=matplotlib.colors.LinearSegmentedColormap.from_list("d", [CRIT, "#f0efec", BLUE]), vmin=med - .2, vmax=med + .2, aspect="auto")
ax.text(0, -.42, f"typical ratio {med:.2f} (shipments include returns and pipeline fill)", transform=ax.transAxes, fontsize=8, color=INK2)
ax.set_xticks(range(hm.shape[1]), hm.columns, rotation=40, ha="right", fontsize=7.6); ax.set_yticks(range(hm.shape[0]), hm.index, fontsize=8); ax.grid(False)
for i in range(hm.shape[0]):
    for j in range(hm.shape[1]):
        ax.text(j, i, f"{hm.values[i, j]:.2f}", ha="center", va="center", fontsize=6.8, color=INK)

# 4 promo events scatter
ax = A[3]; ax.set_title("Every promotion event: spend vs ROI", pad=22)
sub(ax, "RGM · judged event by event, not averaged by tactic: below the line the event lost money")
neg = pr.promo_roi_pct < 0
tcol = {t: c for t, c in zip(sorted(pr.promo_type.unique()), [BLUE, ORANGE, AQUA, YELLOW, MAG, VIOLET])}
for t, gg in pr.groupby("promo_type"):
    ax.scatter(gg.trade_spend / 1e3, gg.promo_roi_pct, s=34, color=tcol[t], alpha=.85, edgecolor=SURF, lw=.8, label=t)
ax.axhline(0, color=CRIT, lw=1.2); ax.axhspan(pr.promo_roi_pct.min() - 3, 0, color=CRIT, alpha=.05)
ax.text(.99, .04, f"{neg.sum()} of {len(pr)} events lost money (\${pr[neg].trade_spend.sum() / 1e6:.1f}M of trade)", transform=ax.transAxes, ha="right", fontsize=9.5, color=CRIT, fontweight="bold")
ax.set_xlabel("trade spend per event (\$K)"); ax.yaxis.set_major_formatter(lambda v, p: f"{v:.0f}%"); ax.legend(fontsize=8, ncol=6, loc="upper center", bbox_to_anchor=(.5, -.17), handletextpad=.2, columnspacing=.8)

# 5 gross-to-net (kept)
ax = A[4]; ax.set_title("Gross-to-net, last 13 weeks", pad=22)
sub(ax, "RGM / Finance · what trade and returns take out of gross sales")
g13 = y_[y_.we > WC[-14]]; gs, ts, rd = g13.gross_sales.sum(), g13.trade_spend.sum(), g13.return_dollars.sum()
waterfall(ax, [("Gross sales", gs, "start"), ("Trade spend", -ts, "down"), ("Returns", -rd, "down"), ("Net of returns", gs - ts - rd, "end")], lambda v: money(v))
ax.set_ylim(0, gs * 1.08); ax.yaxis.set_major_formatter(lambda v, p: money(v, 0))

# 6 off-price: share and margin, aligned small multiples (no dual axis)
ax = A[5]
op = y_[y_.we >= WC[-52]].copy(); op["off"] = op.customer_name.str.contains("Off-Price"); op["gm"] = op.net_sales * op.gross_margin_pct / 100
t_ = op.groupby("we").agg(ns=("net_sales", "sum")).rolling(4).sum()
o_ = op[op.off].groupby("we").agg(ns=("net_sales", "sum"), gm=("gm", "sum")).rolling(4).sum()
share = (o_.ns / t_.ns * 100).dropna(); marg = (o_.gm / o_.ns * 100).dropna()
sp = ax.get_subplotspec(); ax.remove(); gs = sp.subgridspec(2, 1, hspace=.12, height_ratios=[1.3, 1])
ax = fig.add_subplot(gs[0]); ins = fig.add_subplot(gs[1], sharex=ax)
ax.set_title("Off-price channel: share of net sales and its margin", pad=22)
sub(ax, "Brand Director · rising share at a falling margin = excess stock being cleared (4-week rolling)")
ax.plot(share.index, share, color=ORANGE, lw=2.2); ax.set_ylabel("share of net sales", color=INK2, fontsize=8.5)
ax.yaxis.set_major_formatter(lambda v, p: f"{v:.0f}%"); ax.tick_params(labelbottom=False)
ins.plot(marg.index, marg, color=INK2, lw=1.8); ins.set_ylabel("gross margin", color=INK2, fontsize=8.5)
ins.yaxis.set_major_formatter(lambda v, p: f"{v:.0f}%"); ins.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b %y"))
ax.text(share.index[-1], share.iloc[-1], f"  {share.iloc[-1]:.1f}%", fontsize=9, fontweight="bold", va="center")
ins.text(marg.index[-1], marg.iloc[-1], f"  {marg.iloc[-1]:.1f}%", fontsize=9, fontweight="bold", va="center")
ax.set_xlim(share.index[0], share.index[-1] + timedelta(days=40))
fig.savefig(OUT + "RD2_cpg.png", dpi=110); plt.close(fig)

# ============================================================================================ RETAIL v2 (sample)
rf = pd.read_csv(D + "retail_fact_store_category_week.csv", parse_dates=["week_start_date"])
rs_ = pd.read_csv(D + "retail_dim_store.csv"); rc = pd.read_csv(D + "retail_dim_category.csv")
rf = rf.merge(rs_, on="store_id").merge(rc, on="category_id")
WR = sorted(rf.week_start_date.unique()); cur, ly = WR[-13:], WR[-65:-52]
fig, A = board("Retail: research-backed views (v2, pack retail sample)",
               "Follows merchandising practice: comp sales split into traffic × conversion × basket, sales vs stock (weeks of supply, stock-to-sales), margin by category.")
fig.subplots_adjust(left=.12, wspace=.36)
# 1 drivers (kept)
ax = A[0]; ax.set_title("Comp sales vs last year: traffic × conversion × basket", pad=22)
sub(ax, "Ops Director · is it demand or basket? last 13 weeks vs same weeks last year")
def agg(ws): z = rf[rf.week_start_date.isin(ws)]; return z.net_sales.sum(), z.customer_traffic.sum(), z.transactions.sum()
s1, t1, x1 = agg(cur); s0, t0, x0 = agg(ly)
parts = [("Traffic", t1 / t0 - 1), ("Conversion", (x1 / t1) / (x0 / t0) - 1), ("Basket", (s1 / x1) / (s0 / x0) - 1), ("Sales", s1 / s0 - 1)]
yy = np.arange(len(parts))[::-1]
for (lab, v), yv in zip(parts, yy):
    ax.barh(yv, v * 100, color=BLUE if lab == "Sales" else (GRAY if abs(v) < .001 else GOOD if v >= 0 else CRIT), height=.55)
    ax.text(v * 100 + .1, yv, f"{v * 100:+.1f}%", va="center", fontsize=9.5)
ax.set_yticks(yy, [p[0] for p in parts]); ax.axvline(0, color=INK2, lw=1); ax.grid(axis="y", visible=False); ax.xaxis.set_major_formatter(lambda v, p: f"{v:.0f}%")
# 2 heatmap (kept)
ax = A[1]; ax.set_title("Sales growth vs last year: region × category", pad=22)
sub(ax, "Category Manager · one cell lights up: Southwest Apparel")
a = rf[rf.week_start_date.isin(cur)].groupby(["region", "category_name"]).net_sales.sum(); b = rf[rf.week_start_date.isin(ly)].groupby(["region", "category_name"]).net_sales.sum()
gm = ((a / b - 1) * 100).unstack(); lim = max(abs(gm.min().min()), abs(gm.max().max()))
ax.imshow(gm.values, cmap=matplotlib.colors.LinearSegmentedColormap.from_list("d", [CRIT, "#f0efec", BLUE]), vmin=-lim, vmax=lim, aspect="auto")
ax.set_xticks(range(gm.shape[1]), [c.replace(" & ", "/") for c in gm.columns], rotation=35, ha="right", fontsize=8); ax.set_yticks(range(gm.shape[0]), gm.index); ax.grid(False)
for i in range(gm.shape[0]):
    for j in range(gm.shape[1]):
        ax.text(j, i, f"{gm.values[i, j]:+.0f}", ha="center", va="center", fontsize=7.5)
# 3 SW apparel: sales vs on-hand indexed
ax = A[2]; ax.set_title("Southwest Apparel: sales vs stock on hand (indexed)", pad=22)
sub(ax, "Category Manager · demand fell and stock kept rising = markdown exposure (index 100 = 26 weeks ago)")
sw = rf[(rf.region == "Southwest") & (rf.category_name == "Apparel") & (rf.week_start_date >= WR[-26])].groupby("week_start_date")[["net_sales", "on_hand_units"]].sum().rolling(4).mean().dropna()
ix = sw / sw.iloc[0] * 100
ax.plot(ix.index, ix.net_sales, color=BLUE, lw=2.2); ax.plot(ix.index, ix.on_hand_units, color=ORANGE, lw=2.2)
end_labels(ax, ix.index[-1] + timedelta(days=3), [(ix.net_sales.iloc[-1], f"Sales {ix.net_sales.iloc[-1]:.0f}", True), (ix.on_hand_units.iloc[-1], f"On hand {ix.on_hand_units.iloc[-1]:.0f}", True)], 6)
ax.axhline(100, color=INK2, lw=.8); ax.set_xlim(ix.index[0], ix.index[-1] + timedelta(days=40)); clip_dates(ax, ix.index[-1]); ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b %y"))
# 4 weeks of supply by category now vs LY
ax = A[3]; ax.set_title("Weeks of supply by category: now vs a year ago", pad=22)
sub(ax, "Inventory Planner · on-hand ÷ average weekly units; where is cover building?")
def wos(ws):
    z = rf[rf.week_start_date.isin(ws)]; last = z[z.week_start_date == max(ws)].groupby("category_name").on_hand_units.sum()
    return last / (z.groupby("category_name").units_sold.sum() / len(ws))
wn, wl = wos(WR[-4:]), wos(WR[-56:-52]); o = (wn - wl).sort_values().index; yy = np.arange(len(o))
ax.hlines(yy, wl[o], wn[o], color=GRID, lw=3); ax.scatter(wl[o], yy, color=GRAY, s=40, label="a year ago")
ax.scatter(wn[o], yy, color=[CRIT if wn[n] - wl[n] > .5 else BLUE for n in o], s=58, zorder=3, label="now")
ax.set_yticks(yy, list(o), fontsize=8.3); ax.grid(axis="y", visible=False); ax.legend(loc="lower right", fontsize=8.5); ax.set_xlabel("weeks of supply")
# 5 margin change by category
ax = A[4]; ax.set_title("Gross margin change by category vs last year", pad=22)
sub(ax, "Category Manager · margin rate in points, sales-weighted; last 13 weeks")
z1 = rf[rf.week_start_date.isin(cur)].copy(); z0 = rf[rf.week_start_date.isin(ly)].copy()
for zz in (z1, z0):
    zz["gx"] = zz.gross_margin_pct * zz.net_sales
m1 = z1.groupby("category_name").gx.sum() / z1.groupby("category_name").net_sales.sum(); m0 = z0.groupby("category_name").gx.sum() / z0.groupby("category_name").net_sales.sum()
dm = (m1 - m0).sort_values(); yy = np.arange(len(dm))
ax.barh(yy, dm, color=[CRIT if v < -1 else (BLUE if v >= 0 else GRAY) for v in dm], height=.6)
for i, (n, v) in enumerate(dm.items()):
    ax.text(v + (.05 if v >= 0 else -.05), i, f"{v:+.1f} pts", va="center", ha="left" if v >= 0 else "right", fontsize=8.5)
ax.set_yticks(yy, list(dm.index), fontsize=8.3); ax.axvline(0, color=INK2, lw=1); ax.grid(axis="y", visible=False); ax.set_xlim(dm.min() - 1, dm.max() + 1)
# 6 comp sales trend by region
ax = A[5]; ax.set_title("Weekly sales growth vs last year by region", pad=22)
sub(ax, "Ops Director · 4-week rolling, same weeks last year; highlight the outlier")
rw = rf.groupby(["week_start_date", "region"]).net_sales.sum().unstack().rolling(4).sum()
gr = ((rw / rw.shift(52) - 1) * 100).dropna().iloc[-30:]
for r in gr.columns:
    ax.plot(gr.index, gr[r], color=ORANGE if r == "Southwest" else GRAY, lw=2.4 if r == "Southwest" else 1.2)
end_labels(ax, gr.index[-1] + timedelta(days=3), [(gr[r].iloc[-1], r + (f"  {gr[r].iloc[-1]:+.1f}%" if r == "Southwest" else ""), r == "Southwest") for r in gr.columns], .45)
ax.axhline(0, color=INK2, lw=.8); ax.set_xlim(gr.index[0], gr.index[-1] + timedelta(days=45)); clip_dates(ax, gr.index[-1])
ax.yaxis.set_major_formatter(lambda v, p: f"{v:+.0f}%"); ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b %y"))
fig.savefig(OUT + "RD2_retail.png", dpi=110); plt.close(fig)
print("ok")
