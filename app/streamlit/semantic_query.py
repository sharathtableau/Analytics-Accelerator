"""Governed query builder: every number comes from SEMANTIC_VIEW(...).

Only fields that exist in the described semantic view can be referenced, grain
is an allowlisted keyword, and filter values are bound parameters.
"""
from __future__ import annotations

import datetime as dt
import threading
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Optional, Sequence

from semantic_catalog import Field, SemanticModel, quote_fqn, row_dict

GRAINS = ("day", "week", "month", "quarter")
AUDIENCE_GRAIN = {
    "executives": "month",
    "managers": "week",
    "weekly_business_review": "week",
    "daily_operations": "day",
}
WINDOW = {"day": 90, "week": 26, "month": 24, "quarter": 12}

# --- query capture for validation -------------------------------------------------------------
# Every governed query records its structured request (dimensions, metrics, WHERE) and the rows it returned,
# so the validation layer can re-derive the same numbers independently from the base tables.
_TL = threading.local()
MAX_CAPTURED_ROWS = 3000


@contextmanager
def capturing():
    """Collect the governed queries run (on this thread) inside the block: [{sql, sv, req, rows}]."""
    outer = getattr(_TL, "capture", None)
    _TL.capture = []
    try:
        yield _TL.capture
    finally:
        got = _TL.capture
        _TL.capture = outer
        if outer is not None:
            outer.extend(got)


def _date(value: Any) -> Optional[dt.date]:
    if value is None:
        return None
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    try:
        return dt.date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def period_start(day: dt.date, grain: str) -> dt.date:
    if grain == "day":
        return day
    if grain == "week":
        return day - dt.timedelta(days=day.weekday())
    if grain == "month":
        return day.replace(day=1)
    if grain == "quarter":
        return day.replace(month=3 * ((day.month - 1) // 3) + 1, day=1)
    raise ValueError(grain)


def shift(start: dt.date, grain: str, n: int) -> dt.date:
    if grain == "day":
        return start + dt.timedelta(days=n)
    if grain == "week":
        return start + dt.timedelta(weeks=n)
    months = {"month": 1, "quarter": 3}[grain] * n
    y, m = divmod(start.month - 1 + months, 12)
    return dt.date(start.year + y, m + 1, 1)


def periods_per_year(grain: str) -> int:
    return {"day": 364, "week": 52, "month": 12, "quarter": 4}[grain]


@dataclass
class Calendar:
    """Data coverage for the chosen time dimension and grain."""
    min_date: dt.date
    max_date: dt.date
    grain: str
    current_start: dt.date      # last COMPLETE period
    window_start: dt.date
    end_exclusive: dt.date      # start of the (incomplete) period after current

    @property
    def prior_start(self) -> dt.date:
        return shift(self.current_start, self.grain, -1)

    @property
    def yoy_start(self) -> dt.date:
        return shift(self.current_start, self.grain, -periods_per_year(self.grain))

    def label(self, start: dt.date) -> str:
        if self.grain == "month":
            return start.strftime("%b %Y")
        if self.grain == "quarter":
            return f"Q{(start.month - 1) // 3 + 1} {start.year}"
        if self.grain == "week":
            return "Wk of " + start.strftime("%d %b %Y")
        return start.strftime("%d %b %Y")

    def as_dict(self) -> dict[str, Any]:
        return {"min_date": self.min_date.isoformat(), "max_date": self.max_date.isoformat(),
                "grain": self.grain, "current_start": self.current_start.isoformat(),
                "current_label": self.label(self.current_start),
                "prior_label": self.label(self.prior_start),
                "yoy_label": self.label(self.yoy_start),
                "window_start": self.window_start.isoformat(),
                "end_exclusive": self.end_exclusive.isoformat()}


class SemanticQuery:
    def __init__(self, session, model: SemanticModel, log: Optional[list] = None):
        self.session = session
        self.model = model
        self.log = log if log is not None else []

    # -- low level -----------------------------------------------------------------
    def run(self, sql: str, params: Sequence[Any] = ()) -> list[dict[str, Any]]:
        self.log.append(sql)
        rows = self.session.sql(sql, params=list(params)).collect() if params else self.session.sql(sql).collect()
        out = [row_dict(r) for r in rows]
        cap = getattr(_TL, "capture", None)
        if cap is not None and not params:
            for text, req in reversed(getattr(_TL, "recent", [])):
                if text in sql and sql.count("SEMANTIC_VIEW(") == text.count("SEMANTIC_VIEW("):
                    cap.append({"sql": sql, "sv": text, "req": req, "rows": out[:MAX_CAPTURED_ROWS],
                                "truncated": len(out) > MAX_CAPTURED_ROWS})
                    break
        return out

    def sv(self, dims: Sequence[str] = (), metrics: Sequence[str] = (), where: str = "") -> str:
        text = self._sv(dims, metrics, where)
        recent = getattr(_TL, "recent", None)
        if recent is None:
            recent = _TL.recent = []
        recent.append((text, {"model": self.model.source_id, "dims": list(dims), "metrics": list(metrics),
                              "where": where}))
        del recent[:-8]
        return text

    def _sv(self, dims: Sequence[str] = (), metrics: Sequence[str] = (), where: str = "") -> str:
        if getattr(self.model, "facts_mode", False):
            return self._adhoc(dims, metrics, where)
        if any(self._formula(m.rsplit(" AS ", 1)[0].strip()) for m in metrics):
            return self._with_formulas(dims, metrics, where)
        parts = [quote_fqn(self.model.fqn)]
        if dims:
            parts.append("DIMENSIONS " + ", ".join(dims))
        if metrics:
            parts.append("METRICS " + ", ".join(metrics))
        if where:
            parts.append("WHERE " + where)
        return "SEMANTIC_VIEW(\n  " + "\n  ".join(parts) + "\n)"

    def _formula(self, ref: str):
        spec = self.model.virtual.get(ref)
        return spec if spec and spec[0] == "FORMULA" else None

    def _with_formulas(self, dims: Sequence[str], metrics: Sequence[str], where: str) -> str:
        """Custom metrics (formulas over governed metrics): the base metrics come from SEMANTIC_VIEW(...), the
        formula is computed on top. SQL is generated from the parsed formula, never from typed text."""
        from custom_metrics import render
        inner, outer, aliases = [], [], {}
        for m in metrics:
            ref, alias = (x.strip() for x in m.rsplit(" AS ", 1))
            spec = self._formula(ref)
            if not spec:
                inner.append(m)
                continue
            for base_id, base_ref in spec[2].items():
                if base_ref not in aliases:
                    aliases[base_ref] = f"AA_B{len(aliases)}"
                    inner.append(f"{base_ref} AS {aliases[base_ref]}")
            outer.append(f"{render(spec[1], lambda i, r=spec[2]: aliases[r[i]])} AS {alias}")
        parts = [quote_fqn(self.model.fqn)]
        if dims:
            parts.append("DIMENSIONS " + ", ".join(dims))
        parts.append("METRICS " + ", ".join(inner))
        if where:
            parts.append("WHERE " + where)
        base = "SEMANTIC_VIEW(\n  " + "\n  ".join(parts) + "\n)"
        hidden = ", ".join(aliases.values())
        return f"(SELECT * EXCLUDE ({hidden}), {', '.join(outer)} FROM {base})"

    def _adhoc_call(self, ref: str, depth: int = 0) -> str:
        spec = self.model.virtual.get(ref, ("SUM", ref))
        if spec[0] == "FORMULA" and depth < 3:
            from custom_metrics import render
            return render(spec[1], lambda i, r=spec[2]: self._adhoc_call(r[i], depth + 1))
        if spec[0] == "RATIO" and depth < 3:
            return f"DIV0({self._adhoc_call(spec[1], depth + 1)}, {self._adhoc_call(spec[2], depth + 1)})"
        agg, fact = spec[0], spec[1]
        return f"COUNT(DISTINCT {fact})" if agg == "COUNT_DISTINCT" else f"{agg}({fact})"

    def _adhoc(self, dims: Sequence[str], metrics: Sequence[str], where: str) -> str:
        """Facts-only semantic view: standard-SQL query with ad-hoc metrics, as a derived table
        (SELECT d, SUM(fact) FROM semantic_view WHERE ... GROUP BY d)."""
        sel, group = [], []
        for d in dims:
            expr, alias = d.rsplit(" AS ", 1)
            sel.append(f"{expr} AS {alias}")
            group.append(expr)
        for m in metrics:
            ref, alias = m.rsplit(" AS ", 1)
            sel.append(f"{self._adhoc_call(ref.strip())} AS {alias}")
        sql = "SELECT " + ", ".join(sel) + " FROM " + quote_fqn(self.model.fqn)
        if where:
            sql += " WHERE " + where
        if group:
            sql += " GROUP BY " + ", ".join(group)
        return "(" + sql + ")"

    def dim(self, field_id: str) -> Field:
        return self.model.field(field_id, ("dimension",))

    def metric(self, field_id: str) -> Field:
        return self.model.field(field_id, ("metric",))

    @staticmethod
    def trunc(time: Field, grain: str, alias: str = "PERIOD") -> str:
        if grain not in GRAINS:
            raise ValueError("grain")
        return f"DATE_TRUNC('{grain}', {time.ref}) AS {alias}"

    @staticmethod
    def range_where(time: Field, start: dt.date, end_excl: dt.date) -> str:
        # Dates are generated server-side from python date objects (never user text).
        return (f"{time.ref} >= TO_DATE('{start.isoformat()}') "
                f"AND {time.ref} < TO_DATE('{end_excl.isoformat()}')")

    # -- profiling -----------------------------------------------------------------
    def calendar(self, time_id: str, metric_id: str, grain: str) -> Calendar:
        time, metric = self.dim(time_id), self.metric(metric_id)
        sql = (f"SELECT MIN(D) AS MIN_D, MAX(D) AS MAX_D FROM "
               + self.sv([self.trunc(time, "day", "D")], [f"{metric.ref} AS V"]))
        row = self.run(sql)[0]
        lo, hi = _date(row.get("min_d")), _date(row.get("max_d"))
        if not lo or not hi:
            raise ValueError("The time dimension has no dates")
        start = period_start(hi, grain)
        next_start = shift(start, grain, 1)
        complete = (hi + dt.timedelta(days=1)) >= next_start
        current = start if complete else shift(start, grain, -1)
        end_excl = shift(current, grain, 1)
        span = WINDOW[grain] if grain == "day" else max(WINDOW[grain], periods_per_year(grain) + 1)
        window_start = max(period_start(lo, grain), shift(current, grain, -(span - 1)))
        return Calendar(lo, hi, grain, current, window_start, end_excl)

    def distinct_counts(self, dim_ids: Sequence[str]) -> dict[str, int]:
        if not dim_ids:
            return {}
        parts = []
        for i, fid in enumerate(dim_ids):
            d = self.dim(fid)
            parts.append(f"SELECT {i} AS IX, COUNT(*) AS N FROM " + self.sv([f"{d.ref} AS K"]))
        rows = self.run("\nUNION ALL\n".join(parts))
        by_ix = {int(r["ix"]): int(r["n"]) for r in rows}
        return {fid: by_ix.get(i, 0) for i, fid in enumerate(dim_ids)}

    # -- analytical queries -------------------------------------------------------------
    def series(self, time_id: str, metric_ids: Sequence[str], cal: Calendar,
               dim_id: Optional[str] = None, extra: str = "") -> list[dict[str, Any]]:
        time = self.dim(time_id)
        dims = [self.trunc(time, cal.grain)]
        if dim_id:
            dims.append(f"{self.dim(dim_id).ref} AS SEG")
        mets = [f"{self.metric(m).ref} AS M{i}" for i, m in enumerate(metric_ids)]
        where = self.range_where(time, cal.window_start, cal.end_exclusive) + (f" AND {extra}" if extra else "")
        sql = ("SELECT * FROM " + self.sv(dims, mets, where) + " ORDER BY PERIOD" + (", SEG" if dim_id else ""))
        rows = self.run(sql)
        out = []
        for r in rows:
            item = {"period": _date(r.get("period")).isoformat()}
            if dim_id:
                item["segment"] = "(blank)" if r.get("seg") is None else str(r.get("seg"))
            for i, m in enumerate(metric_ids):
                v = r.get(f"m{i}")
                item[m] = None if v is None else float(v)
            out.append(item)
        return out

    def by_dim(self, time_id: str, metric_ids: Sequence[str], dim_ids: Sequence[str],
               start: dt.date, end_excl: dt.date, limit: int = 200, extra: str = "") -> list[dict[str, Any]]:
        time = self.dim(time_id)
        dims = [f"{self.dim(d).ref} AS D{i}" for i, d in enumerate(dim_ids)]
        mets = [f"{self.metric(m).ref} AS M{i}" for i, m in enumerate(metric_ids)]
        where = self.range_where(time, start, end_excl) + (f" AND {extra}" if extra else "")
        sql = ("SELECT * FROM " + self.sv(dims, mets, where) + " ORDER BY M0 DESC NULLS LAST LIMIT " + str(int(limit)))
        rows = self.run(sql)
        out = []
        for r in rows:
            item = {}
            for i, d in enumerate(dim_ids):
                val = r.get(f"d{i}")
                item[d] = "(blank)" if val is None else str(val)
            for i, m in enumerate(metric_ids):
                v = r.get(f"m{i}")
                item[m] = None if v is None else float(v)
            out.append(item)
        return out


def distinct_values(q: "SemanticQuery", dim_id: str, limit: int = 60) -> list[str]:
    d = q.dim(dim_id)
    rows = q.run("SELECT * FROM " + q.sv([f"{d.ref} AS K"]) + f" ORDER BY K LIMIT {int(limit)}")
    return [str(r.get("k")) for r in rows if r.get("k") is not None]
