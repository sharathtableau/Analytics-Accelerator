import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
INK, INK2, GRID, BLUE, ORANGE, GREEN = "#0b0b0b", "#52514e", "#e6e5e0", "#2a78d6", "#eb6834", "#0ca30c"
rows = [
 ("Bridge / waterfall", "Parts that add up to a total", "Sales vs plan bridge", "Accounts or balance roll-forward", "Gross-to-net"),
 ("Focus lines", "One series highlighted, the rest muted, labels at line ends", "Over-bought region (inventory index)", "The segment going bad (delinquency)", "The account or SKU drifting"),
 ("Threshold band", "Governed limit drawn on the chart", "In-stock target", "Rewards ratio > 0.85", "Weeks of supply 6–12, bloat > 14"),
 ("Gap lines", "Two same-unit series, gap shaded", "Sales vs plan", "Our rate vs competitor rate", "Sell-in vs sell-through"),
 ("Quadrant bubble", "x, y, size, median lines and direct labels", "Category margin vs growth", "Risk vs return by segment", "Promo ROI; distribution vs velocity"),
 ("Band dot plot", "Each entity vs its target band (dumbbell)", "Stores vs labour target", "Segments vs loss-rate plan", "Accounts vs weeks-of-supply band"),
 ("Funnel", "Stage-to-stage conversion plus unit cost", "Traffic → conversion → basket", "Applications → approvals → bookings", "Distribution → velocity → sales"),
 ("Share over time", "100% stacked area: mix shift", "Online share; fulfilment mix", "Product mix of balances", "Wholesale / off-price / DTC mix"),
 ("Driver tree", "Total = A × B × C; which factor moved", "Traffic × conversion × basket", "Balance × yield − losses", "Units × price × distribution"),
 ("Diverging heatmap", "Change vs last year, neutral midpoint", "Region × category growth", "Segment × product delinquency change", "Account × product sell-through"),
]
fig = plt.figure(figsize=(15, 10.2)); fig.patch.set_facecolor("#f9f9f7")
fig.text(.03, .955, "R&D finding: today the three workspaces differ in metrics, not in how the data is shown", fontsize=16.5, fontweight="bold", color=INK)
fig.text(.03, .925, "Finance and CPG packs use the same generic tile types (KPI grid, ranked bar, small multiples, heatmap, scatter, period compare, treemap, combo, tables).\n"
         "Domain experts read their business through different shapes. Proposal: 10 new tile types, each validated like today's tiles, used by the domain packs.",
         fontsize=10.5, color=INK2, va="top", linespacing=1.5)
cols = ["New tile type", "What it shows", "Retail", "Finance", "CPG"]
xs = [.03, .19, .45, .63, .81]; y0 = .80
for x, c in zip(xs, cols):
    fig.text(x, y0, c.upper(), fontsize=9, fontweight="bold", color=INK2)
for i, r in enumerate(rows):
    y = y0 - .052 - i * .067
    fig.add_artist(plt.Line2D([.03, .98], [y + .04, y + .04], color=GRID, lw=1, transform=fig.transFigure))
    fig.text(xs[0], y, r[0], fontsize=11, fontweight="bold", color=INK, va="center")
    fig.text(xs[1], y, r[1], fontsize=9.3, color=INK2, va="center", wrap=True)
    for j, k in enumerate((2, 3, 4)):
        fig.text(xs[2 + j], y, r[k], fontsize=9.3, color=INK, va="center")
yb = y0 - .052 - len(rows) * .067 + .005
fig.add_artist(plt.Line2D([.03, .98], [yb + .035, yb + .035], color=GRID, lw=1, transform=fig.transFigure))
fig.text(.03, yb - .01, "Retire: the dual-axis combo chart (two y-scales mislead). Use gap lines when the unit is the same, or two aligned charts when it is not.",
         fontsize=10, color="#d03b3b", fontweight="bold", va="center")
fig.savefig("/mnt/user-data/outputs/RD_summary.png", dpi=110)
print("ok")
