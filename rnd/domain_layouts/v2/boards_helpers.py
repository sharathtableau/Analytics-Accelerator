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


