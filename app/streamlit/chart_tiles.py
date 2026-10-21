"""Chart tiles, drop A: bars + line combo, treemap, progress gauge, P&L table.

Every number is a SEMANTIC_VIEW query (through PersonaTiles._rows / _totals, or the shared period series), so
validation QA-01 re-derives each one from the base tables like any other tile. The display arithmetic each tile adds
(shares, changes, pace, projection) is recomputed by validation QA-02. Mixed into Engine (engine.py).
"""
from __future__ import annotations

import datetime as dt
from typing import Any, Optional

TREEMAP_GROUPS = 10         # top groups shown; the rest become "Other"
TREEMAP_CHILDREN = 8        # top children per group when nested


def _pct(cur, base):
    if cur is None or base in (None, 0):
        return None
    return (cur - base) / abs(base)


class ChartTiles:
    # ------------------------------------------------------------------ bars + line
    def combo_chart(self, comp) -> dict[str, Any]:
        m = self._metric_for(comp)
        m2 = comp.get("metric2_id")
        if not m2:
            raise RuntimeError("Bars + line needs a second metric")
        s = self.multi_series([m, m2])
        n = {"day": 30, "week": 26, "month": 13, "quarter": 8}.get(self.cal.grain, 13)
        rows = [r for r in s if r["period"] <= self.cal.current_start.isoformat()][-n:]
        kb, kl = self.kind_of(m), self.kind_of(m2)
        points = [{"period": r["period"], "label": self.label(r["period"]), "bar": r.get(m), "line": r.get(m2)}
                  for r in rows]
        facts = []
        if len(points) >= 2:
            last, prev = points[-1], points[-2]
            facts.append(f"{self.mlabel(m)} {last['label']} = {self._fmt(last['bar'], kb)}"
                         + (f" ({self._dtxt(_pct(last['bar'], prev['bar']), kb)} vs {prev['label']})"
                            if _pct(last['bar'], prev['bar']) is not None else "")
                         + f"; {self.mlabel(m2)} = {self._fmt(last['line'], kl)}"
                         + (f" ({self._dtxt(self._chg(last['line'], prev['line'], kl), kl)} vs {prev['label']})"
                            if self._chg(last['line'], prev['line'], kl) is not None else ""))
            bars = [p for p in points if p["bar"] is not None]
            if bars:
                hi = max(bars, key=lambda p: p["bar"])
                facts.append(f"Highest {self.mlabel(m)} in the window: {hi['label']} ({self._fmt(hi['bar'], kb)})")
        return {"metric": m, "metric2": m2, "bar_label": self.mlabel(m), "line_label": self.mlabel(m2),
                "bar_kind": kb, "line_kind": kl, "points": points, "grain": self.cal.grain, "_facts": facts}

    @staticmethod
    def _chg(cur, base, kind):
        """Change shown for a metric: points for a percent metric, relative change otherwise."""
        if cur is None or base is None:
            return None
        return cur - base if kind == "percent" else _pct(cur, base)

    # ------------------------------------------------------------------ treemap
    def treemap(self, comp) -> dict[str, Any]:
        m, d1 = self._metric_for(comp), self._segment_dim(comp)
        d2 = comp.get("dimension2")
        kind = self.kind_of(m)
        cur, end, prior = self.cal.current_start, self.cal.end_exclusive, self.cal.prior_start
        dims = [d1] + ([d2] if d2 else [])
        key = f"tm:{m}:{','.join(dims)}"
        cur_rows = self._cached(f"{key}:{cur}", lambda: self._rows([m], dims, cur, end))
        pri_rows = self._cached(f"{key}:{prior}", lambda: self._rows([m], dims, prior, cur))
        total = self._totals([m], cur, end).get(m)
        pri = {tuple(str(r[d]) for d in dims): r.get(m) for r in pri_rows}
        leaves, excluded = [], 0.0
        for r in cur_rows:
            v = r.get(m)
            if v is None:
                continue
            if v <= 0:                      # a box cannot have a negative or zero area
                excluded += v
                continue
            k = tuple(str(r[d]) for d in dims)
            leaves.append({"key": k, "value": v, "prior": pri.get(k)})
        shown = sum(x["value"] for x in leaves)
        groups: dict[str, dict[str, Any]] = {}
        for x in leaves:
            g = groups.setdefault(x["key"][0], {"label": x["key"][0], "value": 0.0, "prior": 0.0, "has_prior": False,
                                               "children": []})
            g["value"] += x["value"]
            if x["prior"] is not None:
                g["prior"] += x["prior"]
                g["has_prior"] = True
            if d2:
                g["children"].append({"label": x["key"][1], "value": x["value"], "prior": x["prior"]})
        order = sorted(groups.values(), key=lambda g: -g["value"])
        top, rest = order[:TREEMAP_GROUPS], order[TREEMAP_GROUPS:]
        if rest:
            top.append({"label": f"Other ({len(rest)})", "value": sum(g["value"] for g in rest),
                        "prior": sum(g["prior"] for g in rest), "has_prior": any(g["has_prior"] for g in rest),
                        "children": [], "other": True})
        out_groups = []
        for g in top:
            kids = sorted(g["children"], key=lambda c: -c["value"])
            k_top, k_rest = kids[:TREEMAP_CHILDREN], kids[TREEMAP_CHILDREN:]
            if k_rest:
                k_top.append({"label": f"Other ({len(k_rest)})", "value": sum(c["value"] for c in k_rest),
                              "prior": (sum(c["prior"] for c in k_rest if c["prior"] is not None)
                                        if any(c["prior"] is not None for c in k_rest) else None), "other": True})
            children = [{"label": c["label"], "value": c["value"], "prior": c["prior"],
                         "share": c["value"] / shown if shown else None,
                         "change": _pct(c["value"], c["prior"]), "other": bool(c.get("other"))} for c in k_top]
            prior_v = g["prior"] if g["has_prior"] else None
            out_groups.append({"label": g["label"], "value": g["value"], "prior": prior_v,
                               "share": g["value"] / shown if shown else None, "change": _pct(g["value"], prior_v),
                               "other": bool(g.get("other")), "children": children})
        facts = []
        if out_groups:
            lead = out_groups[0]
            facts.append(f"{self.mlabel(m)} by {self.dlabel(d1)} in {self.cal.label(cur)}: "
                         + "; ".join(f"{g['label']} {self._fmt(g['value'], kind)} ({(g['share'] or 0) * 100:.0f}%)"
                                     for g in out_groups[:6]))
            movers = [g for g in out_groups if g["change"] is not None and not g["other"]]
            if movers:
                mv = max(movers, key=lambda g: abs(g["change"]))
                facts.append(f"Biggest mover vs {self.cal.label(prior)}: {mv['label']} {self._dtxt(mv['change'], 'number')}")
            if d2 and lead["children"]:
                c = lead["children"][0]
                facts.append(f"Largest {self.dlabel(d2)} inside {lead['label']}: {c['label']} {self._fmt(c['value'], kind)}")
        return {"metric": m, "metric_label": self.mlabel(m), "dimension_label": self.dlabel(d1),
                "dimension2_label": self.dlabel(d2) if d2 else None, "kind": kind, "groups": out_groups,
                "total": total, "shown": shown, "excluded": excluded,
                "excluded_count": sum(1 for r in cur_rows if r.get(m) is not None and r[m] <= 0),
                "period_label": self.cal.label(cur), "prior_label": self.cal.label(prior), "_facts": facts}

    # ------------------------------------------------------------------ progress gauge
    def gauge(self, comp) -> dict[str, Any]:
        m = self._metric_for(comp)
        kind = self.kind_of(m)
        start, end, py_start, py_end = self._ytd_bounds()
        year = start.year
        y1 = dt.date(year + 1, 1, 1)
        plan = self.plan_metric(m)
        actual = self._totals([m], start, end).get(m)
        if plan:
            target = self._totals([plan], start, y1).get(plan)
            expected = self._totals([plan], start, end).get(plan)
            tlabel = "plan"
        else:
            target, expected, tlabel = None, None, "last year"
        if target is None:               # no plan rows for this year: last year's full year is the target
            plan, tlabel = None, "last year"
            target = self._totals([m], py_start, start).get(m)
            expected = self._totals([m], py_start, py_end).get(m)
        progress = actual / target if actual is not None and target else None
        pace = actual / expected if actual is not None and expected else None
        projected = target * pace if target is not None and pace is not None else None
        last_day = end - dt.timedelta(days=1)
        months_left = 12 - last_day.month if last_day.year == year else 0
        days_left = max(0, (y1 - end).days)
        expected_share = expected / target if expected is not None and target else None
        facts = []
        if progress is not None:
            facts.append(f"{self.mlabel(m)} {year} to date ({start:%b}–{last_day:%b}) = {self._fmt(actual, kind)}, "
                         f"{progress * 100:.0f}% of " + ("the full-year plan" if tlabel == "plan" else "last year's full-year total")
                         + f" ({self._fmt(target, kind)})")
        if pace is not None:
            facts.append(f"By this point {'the plan' if tlabel == 'plan' else 'last year'} reached {self._fmt(expected, kind)}: {self.mlabel(m)} is at "
                         f"{pace * 100:.0f}% of that pace; at this pace the year ends near {self._fmt(projected, kind)}")
        return {"metric": m, "metric_label": self.mlabel(m), "kind": kind, "year": year, "actual": actual,
                "target": target, "target_label": tlabel, "expected": expected, "progress": progress,
                "expected_share": expected_share, "pace": pace, "projected": projected,
                "months_left": months_left, "days_left": days_left, "inverse": self.lower_is_better(m),
                "period_label": f"{start:%b} – {last_day:%b %Y}", "_facts": facts}

    # ------------------------------------------------------------------ P&L table
    def pnl_table(self, comp) -> dict[str, Any]:
        d = comp.get("dimension") or self.b.region_dimension or self.b.segment_dimension
        metrics = [m for m in (comp.get("metrics") or []) if m in {x.id for x in self.model.metrics}
                   and self.allowed(m, d)][:8] or [self.b.primary_metric]
        cur, end = self.cal.current_start, self.cal.end_exclusive
        if self.compare == "yoy":
            b0, blabel = self.cal.yoy_start, self.cal.label(self.cal.yoy_start)
            b1 = self._shift_end(b0)
        else:
            b0, b1, blabel = self.cal.prior_start, cur, self.cal.label(self.cal.prior_start)
        key = f"pnl:{d}:{','.join(metrics)}"
        cur_rows = self._cached(f"{key}:{cur}", lambda: self._rows(metrics, [d], cur, end))
        base_rows = self._cached(f"{key}:{b0}", lambda: self._rows(metrics, [d], b0, b1))
        tot_c, tot_b = self._totals(metrics, cur, end), self._totals(metrics, b0, b1)
        C = {str(r[d]): r for r in cur_rows}
        B = {str(r[d]): r for r in base_rows}
        cols = sorted(C, key=lambda s: -(C[s].get(metrics[0]) or 0))[:8]
        rows, facts = [], []
        for m in metrics:
            kind = self.kind_of(m)
            inv = self.lower_is_better(m)

            def cell(v, base):
                ch = self._chg(v, base, kind)
                good = None if ch is None or abs(ch) < 5e-4 else ((ch > 0) != inv)
                return {"value": v, "base": base, "change": ch, "good": good}
            cells = [cell(C[c].get(m), (B.get(c) or {}).get(m)) for c in cols]
            total = cell(tot_c.get(m), tot_b.get(m))
            rows.append({"metric": m, "label": self.mlabel(m), "kind": kind, "inverse": inv,
                         "additive": bool(self.model.field(m, ("metric",)).additive), "cells": cells, "total": total})
            if total["value"] is not None:
                facts.append(f"{self.mlabel(m)} {self.cal.label(cur)} total {self._fmt(total['value'], kind)}"
                             + (f" ({self._dtxt(total['change'], kind)} vs {blabel})" if total["change"] is not None else ""))
        return {"dimension": d, "dimension_label": self.dlabel(d), "columns": cols, "rows": rows,
                "truncated": len(C) > len(cols), "period_label": self.cal.label(cur), "base_label": blabel,
                "compare": "yoy" if self.compare == "yoy" else "prior", "_facts": facts}

    def _shift_end(self, start: dt.date) -> dt.date:
        from semantic_query import shift
        return shift(start, self.cal.grain, 1)
