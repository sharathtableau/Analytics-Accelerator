"""Insight headlines for tiles: one plain sentence that says what the chart shows.

Written by rules from the tile's own computed data (never by AI), so every number in a headline is a number the
tile displays and validation already checks. A tile with nothing worth saying gets no headline.
"""
from __future__ import annotations

from typing import Any, Callable, Optional


def _pct(v: Optional[float]) -> str:
    return "" if v is None else f"{v * 100:+.0f}%"


def _move(v: Optional[float]) -> str:
    if v is None:
        return ""
    return "up" if v > 0.005 else "down" if v < -0.005 else "flat"


def headline(kind: str, data: dict[str, Any], fmt: Callable[[Any, str], str]) -> str:
    try:
        fn = RULES.get(kind)
        return (fn(data, fmt) or "").strip() if fn else ""
    except Exception:
        return ""


def _trend(d, fmt):
    pts = [p for p in d.get("points") or [] if p.get("value") is not None]
    if len(pts) < 3:
        return ""
    k, label, last = d.get("kind", "number"), d.get("metric_label", ""), pts[-1]
    peak = max(pts, key=lambda p: p["value"])
    base = last.get("baseline")
    if base:
        ch = (last["value"] - base) / abs(base)
        return f"{label} {fmt(last['value'], k)} in {last['label']}, {_pct(ch)} on a year earlier"
    if peak is last:
        return f"{label} hit {fmt(last['value'], k)} in {last['label']}, the highest in {len(pts)} periods"
    ch = (last["value"] - pts[0]["value"]) / abs(pts[0]["value"]) if pts[0]["value"] else None
    return (f"{label} {_move(ch)} {_pct(ch).lstrip('+-')} over {len(pts)} periods; peak {fmt(peak['value'], k)} in "
            f"{peak['label']}") if ch is not None else ""


def _forecast(d, fmt):
    pts = d.get("forecast") or []
    if not pts:
        return ""
    total = sum(p.get("forecast") or 0 for p in pts)
    return f"Snowflake ML expects {fmt(total, d.get('kind', 'number'))} of {d.get('metric_label', '')} over the next {len(pts)} periods"


def _ranked(d, fmt):
    rows = [r for r in d.get("rows") or [] if r.get("current") is not None]
    if len(rows) < 2:
        return ""
    k, top, low = d.get("kind", "number"), rows[0], rows[-1]
    tail = f", {_pct(top['change'])} on {d.get('prior_label', 'prior')}" if top.get("change") is not None else ""
    return f"{top['segment']} leads {d.get('metric_label', '')} at {fmt(top['current'], k)}{tail}; {low['segment']} trails at {fmt(low['current'], k)}"


def _compare(d, fmt):
    rows = [r for r in d.get("rows") or [] if r.get("yoy_change") is not None]
    if len(rows) < 2:
        return _ranked(d, fmt)
    best = max(rows, key=lambda r: r["yoy_change"])
    worst = min(rows, key=lambda r: r["yoy_change"])
    return (f"{best['segment']} grew fastest, {_pct(best['yoy_change'])} on last year; "
            f"{worst['segment']} {'slowest' if worst['yoy_change'] >= 0 else 'fell'} at {_pct(worst['yoy_change'])}")


def _donut(d, fmt):
    sl = [s for s in d.get("slices") or [] if s.get("share") is not None]
    if not sl:
        return ""
    top = sl[0]
    return f"{top['label']} is {top['share'] * 100:.0f}% of {d.get('metric_label', '')} in {d.get('period_label', 'the period')}"


def _pareto(d, fmt):
    if not d.get("n80"):
        return ""
    return f"{d['n80']} of {d.get('total_count')} {d.get('dimension_label', '').lower()} values make up 80% of {d.get('metric_label', '')}"


def _bridge(d, fmt):
    k, s, e = d.get("kind", "number"), d.get("start"), d.get("end")
    steps = [x for x in d.get("steps") or [] if not str(x.get("segment", "")).startswith("Other")]
    if s is None or e is None or not steps:
        return ""
    top = max(steps, key=lambda x: abs(x.get("delta") or 0))
    verb = "rose" if e >= s else "fell"
    sign = "+" if (top.get("delta") or 0) >= 0 else "−"
    return (f"{d.get('metric_label', '')} {verb} {fmt(abs(e - s), k)} vs {d.get('start_label', 'prior')}; "
            f"{top['segment']} moved it most ({sign}{fmt(abs(top['delta']), k)})")


def _matrix(d, fmt):
    vals = d.get("values") or []
    best, at = None, None
    for i, row in enumerate(vals):
        for j, v in enumerate(row):
            if v is not None and (best is None or v > best):
                best, at = v, (d["rows"][i], d["cols"][j])
    if at is None:
        return ""
    return f"Largest cell: {at[0]} × {at[1]} at {fmt(best, d.get('kind', 'number'))}"


def _exceptions(d, fmt):
    rows = d.get("rows") or []
    if not rows:
        return ""
    k, top = d.get("kind", "number"), rows[0]
    if d.get("none_flagged"):
        return f"Nothing outside its normal range; closest mover is {top['segment']} ({_pct(top.get('deviation'))})"
    n = sum(1 for r in rows if r.get("is_anomaly"))
    return (f"{n} {d.get('dimension_label', '').lower()} value{'s' if n != 1 else ''} outside normal; {top['segment']} "
            f"{fmt(top['current'], k)} is {_pct(top.get('deviation')).lstrip('+-')} {top.get('direction', '')} expected")


def _scatter(d, fmt):
    pts = d.get("points") or []
    if len(pts) < 3:
        return ""
    low = min(pts, key=lambda p: p["y"])
    return f"{low['label']} has the lowest {d.get('y_label', '')} ({fmt(low['y'], d.get('y_kind', 'number'))})"


def _chg_txt(v, kind):
    if v is None:
        return ""
    return f"{v * 100:+.1f} pt" if kind == "percent" else _pct(v)


def _combo(d, fmt):
    pts = [p for p in d.get("points") or [] if p.get("bar") is not None]
    if len(pts) < 2:
        return ""
    last, prev = pts[-1], pts[-2]
    kb, kl = d.get("bar_kind", "number"), d.get("line_kind", "number")
    bar_ch = (last["bar"] - prev["bar"]) / abs(prev["bar"]) if prev["bar"] else None
    out = f"{d.get('bar_label', '')} {fmt(last['bar'], kb)} in {last['label']}"
    if bar_ch is not None:
        out += f", {_pct(bar_ch)} on {prev['label']}"
    if last.get("line") is not None:
        out += f"; {d.get('line_label', '')} {fmt(last['line'], kl)}"
        if prev.get("line") is not None:
            ch = last["line"] - prev["line"] if kl == "percent" else (
                (last["line"] - prev["line"]) / abs(prev["line"]) if prev["line"] else None)
            if ch is not None:
                out += f" ({_chg_txt(ch, kl)})"
    return out


def _treemap(d, fmt):
    gs = [g for g in d.get("groups") or [] if not g.get("other")]
    if not gs or gs[0].get("share") is None:
        return ""
    top = gs[0]
    out = f"{top['label']} is {top['share'] * 100:.0f}% of {d.get('metric_label', '')}"
    movers = [g for g in gs if g.get("change") is not None]
    if len(movers) >= 2:
        mv = max(movers, key=lambda g: abs(g["change"]))
        if mv is top:
            out += f" and moved most ({_pct(mv['change'])} on {d.get('prior_label', 'prior')})"
        else:
            out += f"; {mv['label']} moved most ({_pct(mv['change'])} on {d.get('prior_label', 'prior')})"
    return out


def _gauge(d, fmt):
    if d.get("progress") is None:
        return ""
    k, lbl, t = d.get("kind", "number"), d.get("metric_label", ""), d.get("target_label", "target")
    full = "the full-year plan" if t == "plan" else "last year's full-year total"
    out = f"{lbl} at {d['progress'] * 100:.0f}% of {full}"
    if d.get("months_left"):
        out += f" with {d['months_left']} month{'s' if d['months_left'] != 1 else ''} left"
    if d.get("pace") is not None and d.get("projected") is not None:
        ahead = (d["pace"] >= 1) != bool(d.get("inverse"))
        out += (f"; {'ahead of' if ahead else 'behind'} pace, heading for {fmt(d['projected'], k)}")
    return out


def _pnl(d, fmt):
    rows = d.get("rows") or []
    if not rows:
        return ""
    r = rows[0]
    k, tot = r.get("kind", "number"), r.get("total") or {}
    if tot.get("value") is None:
        return ""
    out = f"{r['label']} {fmt(tot['value'], k)}"
    if tot.get("change") is not None:
        out += f", {_chg_txt(tot['change'], k)} vs {d.get('base_label', 'prior')}"
    cols = d.get("columns") or []
    cells = [(c, x["change"]) for c, x in zip(cols, r.get("cells") or []) if x.get("change") is not None]
    if len(cells) >= 2:
        sign = -1 if r.get("inverse") else 1
        best = max(cells, key=lambda c: sign * c[1])
        worst = min(cells, key=lambda c: sign * c[1])
        if sign * best[1] < 0:            # every column moved the wrong way
            out += f"; {best[0]} held up best ({_chg_txt(best[1], k)}), {worst[0]} worst ({_chg_txt(worst[1], k)})"
        elif sign * worst[1] > 0:         # every column moved the right way
            out += f"; {best[0]} led ({_chg_txt(best[1], k)}), {worst[0]} slowest ({_chg_txt(worst[1], k)})"
        else:
            out += f"; {best[0]} strongest ({_chg_txt(best[1], k)}), {worst[0]} weakest ({_chg_txt(worst[1], k)})"
    return out


RULES: dict[str, Callable] = {
    "trend_chart": _trend, "forecast_band": _forecast,
    "ranked_bar": _ranked, "target_bar": _ranked, "capacity_chart": _ranked,
    "period_compare": _compare, "share_donut": _donut, "pareto": _pareto, "driver_bridge": _bridge,
    "segment_matrix": _matrix, "heatmap": _matrix,
    "exception_table": _exceptions, "exception_queue": _exceptions, "risk_table": _exceptions,
    "scatter": _scatter,
    "combo_chart": _combo, "treemap": _treemap, "gauge": _gauge, "pnl_table": _pnl,
}
