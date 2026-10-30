import sys; sys.path.insert(0, "/home/claude/rnd")
from boards_helpers import *
rows = [
("Finance","F1 Accounts roll-forward","Drop","'Other movement' is unexplained; a real roll-forward needs payments and purchases the pack lacks"),
("Finance","F2 Delinquency by segment","Keep","Standard CCO view; add roll rates and age buckets beside it"),
("Finance","F3 Risk-return bubble","Change","Bubbles are hard to read; use risk-adjusted yield bars (revenue − losses)"),
("Finance","F4 Rate vs competitor lines","Change","Gap is tiny on a rate axis; diverging rate-gap bars + balance change"),
("Finance","F5 Rewards ratio vs breach","Keep","Governed limit drawn on the chart"),
("Finance","F6 Acquisition funnel","Low value","Channels nearly identical; keep only cost-per-booking ranking"),
("CPG","C1 Sell-in vs sell-through gap","Change","Weekly gap is noisy; cumulative channel-inventory build is what planners use"),
("CPG","C2 Weeks of supply band","Keep","Target band 6–12 weeks"),
("CPG","C3 Gross-to-net waterfall","Keep","Standard RGM view"),
("CPG","C4 Promo ROI by tactic","Change","Averages hid 38 losing events; plot every event vs break-even"),
("CPG","C5 Distribution vs velocity scatter","Change","Decomposition bars answer 'why did sales change' directly"),
("CPG","C6 Channel mix area","Change","Share drift is slow; sell-through heatmap account × product finds the problem cell"),
("Retail","R1 Traffic × conversion × basket","Keep","Core comp-sales decomposition"),
("Retail","R2 Region × category heatmap","Keep","Finds the one bad cell"),
("Retail","R3 Quadrant scatter","Change","Margin change diverging bars are easier to act on"),
("Retail","R4 Inventory index","Change","Sales vs on-hand indexed for the problem cell; weeks of supply vs last year"),
("Retail","R5 Margin leakage","Drop","Pack has no markdown/shrink split; replaced by growth trend by region"),
("Retail","R6 Fulfilment mix","Drop","No fulfilment data in the pack"),
]
col = {"Keep": GOOD, "Change": "#c27c00", "Drop": CRIT, "Low value": GRAY}
fig, ax = plt.subplots(figsize=(15, 8.6)); ax.axis("off")
fig.suptitle("Self-audit: were the v1 charts useful for analysis?", x=.04, y=.975, ha="left", fontsize=17, fontweight="bold")
fig.text(.04, .935, "6 keep · 8 change · 4 drop or low value. Test used: does the chart answer the persona's real question, with data the pack actually has?", fontsize=10.5, color=INK2)
y = .97; dom = None
for d, c, v, why in rows:
    if d != dom:
        ax.text(.0, y, d, fontsize=12, fontweight="bold", transform=ax.transAxes); y -= .045; dom = d
    ax.text(.02, y, c, fontsize=10, transform=ax.transAxes)
    ax.text(.31, y, v, fontsize=10, fontweight="bold", color=col[v], transform=ax.transAxes)
    ax.text(.40, y, why, fontsize=9.5, color=INK2, transform=ax.transAxes)
    y -= .042
fig.savefig(OUT + "RD2_audit.png", dpi=110, bbox_inches="tight", facecolor="#f9f9f7")
