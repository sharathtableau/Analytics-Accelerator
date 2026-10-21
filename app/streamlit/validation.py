"""Automatic QA validation of every dashboard tile.

Every number on a tile comes from governed SEMANTIC_VIEW queries (semantic_query records them). This module
re-derives the same numbers a second, independent way and compares:

  QA-01 Source recompute     same question asked straight of the base tables (joins, expressions and filters
                             rebuilt from the semantic view's definition), compared row by row
  QA-02 Display arithmetic   changes, shares and totals on the tile recomputed from the queried values
  QA-03 Reconciles to total  additive metrics: the segments add up to the headline total
  QA-04 Join integrity       lookup keys unique (no double counting), fact rows find their lookup row
  QA-05 Period logic         current / prior / year-ago periods complete and correctly bounded; coverage matches
  QA-06 Data health          freshness, gaps in the series, blank categories, impossible negatives
  QA-07 Filters applied      active filters reach the tile and the independent query
  QA-08 Narrative grounded   every number in the AI summary matches a computed fact

Results are warnings only: nothing is blocked. A check that cannot be run honestly says "not checkable" with the
reason - it never passes by default.
"""
from __future__ import annotations

import datetime as dt
import decimal
import hashlib
import json
import math
import re
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Callable, Optional

from semantic_catalog import FQN, SemanticModel, quote_fqn, quote_ident, row_dict, split_scope
from semantic_query import period_start, periods_per_year, shift

CHECKS = {
    "QA-01": ("Source recompute",
              "Each number is re-derived with independent SQL written directly against the base tables (not through "
              "the semantic view): joins, column expressions and filters are rebuilt from the view's definition, then "
              "compared row by row."),
    "QA-02": ("Display arithmetic",
              "Changes, shares and totals shown on the tile are recalculated from the queried values."),
    "QA-03": ("Reconciles to total",
              "For additive metrics (sums and counts) the segments must add up to the headline total for the same "
              "period and filters."),
    "QA-04": ("Join integrity",
              "Every lookup key is unique (otherwise rows are double counted) and fact rows find their lookup row "
              "(otherwise they show as blank)."),
    "QA-05": ("Period logic",
              "Current, prior and year-ago periods are complete and correctly bounded, and the data coverage matches "
              "the base tables."),
    "QA-06": ("Data health",
              "Freshness of the data, gaps in the time series, blank categories and negative values where they are "
              "impossible."),
    "QA-07": ("Filters applied",
              "Active dashboard filters are applied to the tile and to the independent query."),
    "QA-08": ("Narrative grounded",
              "Every number in the AI summary matches a fact computed from governed data."),
}
RANK = {"mismatch": 3, "review": 2, "pass": 1, "na": 0}
LABEL = {"mismatch": "Mismatch", "review": "Review", "pass": "Verified", "na": "Not checked"}
MAX_DIAGNOSES = 3         # mismatched tiles diagnosed automatically per run (a few extra queries each)
REL_TOL = 1e-6
ABS_TOL = 1e-6
MAX_QUERIES = 30            # independent queries per run (cost guardrail); the rest are reported as not checked
WORKERS = 6
BLANK_REVIEW_SHARE = 0.02
STALE_DAYS = {"day": 2, "week": 10, "month": 40, "quarter": 100}
POSITIVE_ONLY = re.compile(r"COUNT|QUANTITY|UNITS|ORDERS|CUSTOMERS|SALES|REVENUE|GMV|VISITS|SESSIONS|SHIPMENTS", re.I)
SIGNED = re.compile(r"PROFIT|MARGIN|VARIANCE|CHANGE|DELTA|NET|DIFF|GROWTH|BALANCE|RETURN", re.I)

KEYWORDS = {
    "AND", "OR", "NOT", "CASE", "WHEN", "THEN", "ELSE", "END", "NULL", "IS", "IN", "AS", "DISTINCT", "TRUE", "FALSE",
    "BETWEEN", "LIKE", "ILIKE", "RLIKE", "INTERVAL", "ESCAPE", "OVER", "PARTITION", "BY", "ORDER", "ASC", "DESC",
    "NULLS", "FIRST", "LAST", "WITHIN", "GROUP", "FILTER", "IGNORE", "RESPECT", "ROWS", "RANGE", "UNBOUNDED",
    "PRECEDING", "FOLLOWING", "CURRENT", "ROW", "ANY", "ALL", "SOME", "EXISTS",
    # types (CAST(x AS ...), x::TYPE)
    "NUMBER", "NUMERIC", "DECIMAL", "INT", "INTEGER", "BIGINT", "SMALLINT", "FLOAT", "DOUBLE", "REAL", "PRECISION",
    "VARCHAR", "STRING", "TEXT", "CHAR", "BOOLEAN", "DATE", "TIME", "TIMESTAMP", "TIMESTAMP_NTZ", "TIMESTAMP_LTZ",
    "TIMESTAMP_TZ", "DATETIME", "VARIANT", "OBJECT", "ARRAY", "BINARY",
    # date parts used unquoted (DATEADD(day, ...), EXTRACT(year FROM ...))
    "YEAR", "YEARS", "QUARTER", "MONTH", "MONTHS", "WEEK", "WEEKS", "DAY", "DAYS", "HOUR", "HOURS", "MINUTE",
    "MINUTES", "SECOND", "SECONDS", "DAYOFWEEK", "DAYOFYEAR", "WEEKOFYEAR", "YEAROFWEEK", "DOW", "DOY", "EPOCH",
    "FROM", "MILLISECOND", "NANOSECOND",
}
_IDENT = r'(?:"(?:[^"]|"")+"|[A-Za-z_][A-Za-z0-9_$]*)'
TOKEN = re.compile(rf'(?<![\w$."])({_IDENT})(?:\s*\.\s*({_IDENT}))?(\s*\()?')


class Unchecked(Exception):
    """The independent query cannot be built honestly - reported as 'not checkable', never as a pass."""


def _unq(tok: str) -> str:
    return tok[1:-1].replace('""', '"') if tok.startswith('"') else tok


def _segments(sql: str) -> list[tuple[bool, str]]:
    """Split SQL into (is_string_literal, text) parts so rewriting never touches quoted values."""
    out, i, n, buf = [], 0, len(sql), ""
    while i < n:
        ch = sql[i]
        if ch == "'":
            if buf:
                out.append((False, buf))
                buf = ""
            j = i + 1
            while j < n:
                if sql[j] == "'" and j + 1 < n and sql[j + 1] == "'":
                    j += 2
                    continue
                if sql[j] == "'":
                    break
                j += 1
            out.append((True, sql[i:j + 1]))
            i = j + 1
            continue
        buf += ch
        i += 1
    if buf:
        out.append((False, buf))
    return out


def _cols(value: Any) -> list[str]:
    """'["A","B"]' / '(A, B)' / 'A' -> ['A', 'B']."""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(v).strip().strip('"') for v in value if str(v).strip()]
    text = str(value).strip()
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return [str(v).strip().strip('"') for v in parsed if str(v).strip()]
    except ValueError:
        pass
    return [c.strip().strip('"\'') for c in text.strip("[]()").split(",") if c.strip().strip('"\'')]


NON_ADD_IN_EXPR = re.compile(r"\s*NON\s+ADDITIVE\s+BY\s*\(([^)]*)\)\s*(?:AS\s+)?", re.I)


def _non_additive(text: str) -> list[tuple[str, str, bool]]:
    """'(dates.calendar_date DESC)' / '["DATES.CALENDAR_DATE"]' -> [(ENTITY, NAME, descending)]"""
    out = []
    for part in re.split(r",", str(text).strip("[]() ")):
        part = part.strip().strip('"\'')
        if not part:
            continue
        m = re.match(rf"({_IDENT})(?:\s*\.\s*({_IDENT}))?(\s+(?:ASC|DESC))?", part, re.I)
        if not m:
            continue
        ent, name = (m.group(1), m.group(2)) if m.group(2) else ("", m.group(1))
        out.append((_unq(ent).upper(), _unq(name).upper(), bool(m.group(3) and "DESC" in m.group(3).upper())))
    return out


# ------------------------------------------------------------------------------------------------------------------
# Physical model: what DESCRIBE SEMANTIC VIEW says about base tables, keys, relationships and expressions
# ------------------------------------------------------------------------------------------------------------------
class Physical:
    def __init__(self, fqn: str, tables: dict, rels: list, fields: dict):
        self.fqn = fqn
        self.tables = tables          # LOGICAL -> {"fqn": DB.SCH.T, "pk": [...]}
        self.rels = rels              # [{"name", "left", "left_cols", "right", "right_cols"}]
        self.fields = fields          # (ENTITY, NAME) -> {"kind", "expr", "entity"}
        self.ddl = ""
        self.nonadd_from_ddl: set = set()

    @staticmethod
    def describe(session, fqn: str) -> "Physical":
        fqn, _ = split_scope(fqn)
        if not FQN.match(fqn):
            raise Unchecked("Not a three-part semantic view name")
        rows = [row_dict(r) for r in session.sql(f"DESCRIBE SEMANTIC VIEW {quote_fqn(fqn)}").collect()]
        phys = Physical.parse(fqn, rows)
        try:                                       # NON ADDITIVE BY is read from the DDL when DESCRIBE does not show it
            ddl = str(list(row_dict(session.sql(f"SELECT GET_DDL('SEMANTIC_VIEW', '{fqn}') AS D").collect()[0]).values())[0] or "")
        except Exception:
            ddl = ""
        phys.ddl = ddl
        for m in re.finditer(rf"({_IDENT})\s*\.\s*({_IDENT})\s+NON\s+ADDITIVE\s+BY\s*\(([^)]*)\)", ddl, re.I):
            key = (_unq(m.group(1)).upper(), _unq(m.group(2)).upper())
            f = phys.fields.get(key)
            if f is not None and not f.get("non_additive"):
                f["non_additive"] = _non_additive(m.group(3))
                phys.nonadd_from_ddl.add(key)
        return phys

    @staticmethod
    def parse(fqn: str, rows: list[dict]) -> "Physical":
        tprops: dict[str, dict[str, Any]] = {}
        rprops: dict[str, dict[str, Any]] = {}
        fields: dict[tuple[str, str], dict[str, Any]] = {}
        for r in rows:
            kind = str(r.get("object_kind") or "").upper().replace(" ", "_")
            name = str(r.get("object_name") or "")
            parent = str(r.get("parent_entity") or "")
            prop = str(r.get("property") or "").upper()
            value = r.get("property_value")
            if kind == "TABLE" and name:
                tprops.setdefault(name.upper(), {})[prop] = value
            elif kind == "RELATIONSHIP" and name:
                rp = rprops.setdefault(name.upper(), {})
                rp[prop] = value
                if parent:
                    rp.setdefault("_PARENT", parent)
            elif kind in ("DIMENSION", "TIME_DIMENSION", "FACT", "METRIC", "DERIVED_METRIC") and name:
                fk = "metric" if "METRIC" in kind else "fact" if kind == "FACT" else "dimension"
                item = fields.setdefault((parent.upper(), name.upper()), {"kind": fk, "expr": "", "entity": parent})
                if prop == "EXPRESSION":
                    text = "" if value is None else str(value)
                    m = NON_ADD_IN_EXPR.match(text)
                    if m:                                   # "NON ADDITIVE BY (d.x) AS SUM(...)" kept in the expression
                        item["non_additive"] = _non_additive(m.group(1))
                        text = text[m.end():]
                    item["expr"] = text
                elif "NON_ADDITIVE" in prop.replace(" ", "_") and value not in (None, "", "[]"):
                    item["non_additive"] = _non_additive(str(value))
                elif prop == "TABLE" and not item["entity"]:
                    item["entity"] = str(value or "")
        tables = {}
        for logical, p in tprops.items():
            base = p.get("BASE_TABLE_NAME")
            if not base:
                continue
            db, sch = p.get("BASE_TABLE_DATABASE_NAME"), p.get("BASE_TABLE_SCHEMA_NAME")
            if not (db and sch):
                vdb, vsch, _ = fqn.split(".")
                db, sch = db or vdb, sch or vsch
            tables[logical] = {"fqn": f"{db}.{sch}.{base}", "pk": _cols(p.get("PRIMARY_KEY"))}
        rels = []
        for name, p in rprops.items():
            left = str(p.get("TABLE") or p.get("_PARENT") or "").upper()
            right = str(p.get("REF_TABLE") or "").upper()
            lc, rc = _cols(p.get("FOREIGN_KEY")), _cols(p.get("REF_KEY"))
            if left and right:
                rels.append({"name": name, "left": left, "left_cols": lc,
                             "right": right, "right_cols": rc or list((tables.get(right) or {}).get("pk") or [])})
        # fields whose entity came from a TABLE property are re-keyed so (ENTITY, NAME) lookups work
        fixed = {}
        for (ent, name), f in fields.items():
            fixed[((f["entity"] or ent).upper(), name)] = f
        return Physical(fqn.upper(), tables, rels, fixed)


# ------------------------------------------------------------------------------------------------------------------
# Translator: a governed request (dimensions, metrics, WHERE over logical names) -> plain SQL over base tables
# ------------------------------------------------------------------------------------------------------------------
class Translator:
    def __init__(self, phys: Physical, model: SemanticModel):
        self.p = phys
        self.model = model
        self._used: set = set()
        self._stack: set = set()
        self._nonadd = None
        self.join_type = "LEFT"                  # diagnosis variant: INNER
        self.force_nonadd: dict = {}             # diagnosis variant: metric ref -> [(entity, dim, desc)]
        if not phys.tables:
            raise Unchecked("The semantic view's base tables are not described (DESCRIBE returned no BASE_TABLE_NAME)")

    # -- expressions ----------------------------------------------------------------------------------------------
    def _place(self, entity: str) -> str:
        if entity.upper() not in self.p.tables:
            raise Unchecked(f"Logical table {entity} has no base table in the semantic view description")
        self._used.add(entity.upper())
        return f"\x01{entity.upper()}\x01"

    def expr(self, text: str, owner: str, depth: int = 0) -> str:
        """Rewrite one expression: ENTITY.FIELD -> its definition, bare identifiers -> columns of `owner`."""
        if depth > 8:
            raise Unchecked("Expression nesting too deep to rebuild")
        out = []
        for literal, part in _segments(text):
            if literal:
                out.append(part)
                continue
            out.append(TOKEN.sub(lambda m: self._token(m, owner, depth), part))
        return "".join(out)

    def _token(self, m: re.Match, owner: str, depth: int) -> str:
        first, second, call = m.group(1), m.group(2), m.group(3) or ""
        if second is not None:
            ent, name = _unq(first).upper(), _unq(second)
            if ent not in self.p.tables and ent not in {k[0] for k in self.p.fields}:
                raise Unchecked(f"Unknown reference {first}.{second}")
            if (ent, name.upper()) in self._stack:      # a field defined as its own column (orders.region)
                return f"{self._place(ent)}.{second}" + call
            return self.field(ent, name, depth) + call
        if call:                                         # function name
            return m.group(0)
        word = _unq(first)
        if not first.startswith('"') and word.upper() in KEYWORDS:
            return m.group(0)
        if not owner:
            raise Unchecked(f"Bare column {word} in an expression with no table")
        col = first if first.startswith('"') else word
        return f"{self._place(owner)}.{col}"

    def field(self, entity: str, name: str, depth: int = 0) -> str:
        f = self.p.fields.get((entity.upper(), name.upper()))
        if f is not None and f.get("non_additive") and depth and f["kind"] == "metric":
            raise Unchecked(f"{name} is semi-additive (NON ADDITIVE BY) inside another formula - not rebuilt yet")
        if f is None:
            if entity.upper() in self.p.tables:          # a column of a logical table addressed directly
                return f"{self._place(entity)}.{quote_ident(name) if not re.match(r'^[A-Za-z_][A-Za-z0-9_$]*$', name) else name}"
            raise Unchecked(f"{entity}.{name} is not defined in the semantic view")
        if not f["expr"]:
            raise Unchecked(f"{entity}.{name} has no expression in the semantic view description")
        key = (entity.upper(), name.upper())
        self._stack.add(key)
        try:
            return "(" + self.expr(f["expr"], f["entity"] or entity, depth + 1) + ")"
        finally:
            self._stack.discard(key)

    def _ref_parts(self, ref: str) -> tuple[str, str]:
        m = re.fullmatch(rf"\s*({_IDENT})\s*\.\s*({_IDENT})\s*", ref)
        if m:
            return _unq(m.group(1)), _unq(m.group(2))
        m = re.fullmatch(rf"\s*({_IDENT})\s*", ref)
        if m:
            return "", _unq(m.group(1))
        raise Unchecked(f"Cannot read metric reference {ref}")

    def metric(self, ref: str, depth: int = 0) -> tuple[str, str]:
        """(SQL, home table) for a metric reference as the app writes it (governed, ad-hoc or custom)."""
        if depth > 6:
            raise Unchecked("Metric nesting too deep")
        spec = self.model.virtual.get(ref.strip())
        if spec:
            kind = spec[0]
            if kind == "FORMULA":
                from custom_metrics import render
                homes = set()

                def part(i, refs=spec[2]):
                    sql, home = self.metric(refs[i], depth + 1)
                    homes.add(home)
                    return f"({sql})"
                sql = render(spec[1], part)
                return sql, self._one_home(homes)
            if kind == "RATIO":
                n, hn = self.metric(spec[1], depth + 1)
                d, hd = self.metric(spec[2], depth + 1)
                return f"DIV0(({n}), ({d}))", self._one_home({hn, hd})
            ent, name = self._ref_parts(spec[1])
            inner = self.field(ent, name, depth)
            agg = "COUNT(DISTINCT " + inner + ")" if kind == "COUNT_DISTINCT" else f"{kind}({inner})"
            return agg, ent.upper()
        ent, name = self._ref_parts(ref)
        f = self.p.fields.get((ent.upper(), name.upper()))
        if f is None or f["kind"] != "metric":
            raise Unchecked(f"Metric {ref} is not in the semantic view description")
        if f.get("non_additive"):
            if depth:
                raise Unchecked(f"{name} is semi-additive (NON ADDITIVE BY) inside another formula - not rebuilt yet")
            self._nonadd = f["non_additive"]
        home = (f["entity"] or ent).upper()
        before = set(self._used)
        sql = self.field(ent, name, depth)
        if not home:                                     # derived metric: home is the single table it reads
            home = self._one_home(self._used - before or set(self._used))
        return sql, home

    @staticmethod
    def _one_home(homes: set) -> str:
        homes = {h for h in homes if h}
        if len(homes) != 1:
            raise Unchecked("The metric combines tables at different grains - independent rebuild not supported yet")
        return next(iter(homes))

    # -- joins -----------------------------------------------------------------------------------------------------
    def join_path(self, home: str, needed: set) -> list[dict]:
        """Many-to-one joins from the metric's table to every table the dimensions / filters need."""
        path, have, frontier = [], {home}, [home]
        while frontier and not needed <= have:
            nxt = []
            for t in frontier:
                for r in self.p.rels:
                    if r["left"] == t and r["right"] not in have:
                        if not r["left_cols"] or len(r["left_cols"]) != len(r["right_cols"]):
                            raise Unchecked(f"Relationship {r['name']} has no usable key columns in the description")
                        path.append(r)
                        have.add(r["right"])
                        nxt.append(r["right"])
            frontier = nxt
        missing = needed - have
        if missing:
            raise Unchecked(f"No many-to-one path from {home} to {', '.join(sorted(missing))}")
        # keep only relationships on the way to a needed table
        keep, want = [], set(needed)
        for r in reversed(path):
            if r["right"] in want:
                keep.append(r)
                want.add(r["left"])
        return list(reversed(keep))

    # -- whole request -----------------------------------------------------------------------------------------------
    def derived(self, req: dict) -> tuple[str, list[dict]]:
        """(SELECT dims, metrics FROM base tables ... GROUP BY dims) with the same column names the app reads.

        Metrics from different tables are aggregated separately at their own grain and merged by the dimension
        columns (UNION ALL with every part listing ALL columns in the same order, then MAX per column).
        Semi-additive metrics (NON ADDITIVE BY a date) use only the rows at the latest date within each group."""
        dims = [d.rsplit(" AS ", 1) for d in req.get("dims") or []]
        mets = [m.rsplit(" AS ", 1) for m in req.get("metrics") or []]
        if not mets:
            raise Unchecked("Query has no metrics")
        mcols = [a.strip() for _, a in mets]
        groups: dict[tuple, dict] = {}
        for ref, alias in mets:
            self._used, self._nonadd = set(), None
            sql, home = self.metric(ref.strip())
            if ref.strip().upper() in self.force_nonadd:
                self._nonadd = self.force_nonadd[ref.strip().upper()]
            key = (home, tuple(self._nonadd or ()))
            g = groups.setdefault(key, {"home": home, "nonadd": self._nonadd, "items": {}, "used": set()})
            g["items"][alias.strip()] = sql
            g["used"].update(self._used)
        parts, rels_used = [], []
        for g in groups.values():
            home = g["home"]
            self._used = {home} | g["used"]
            dsql = [(self.expr(e, "", 0), a.strip()) for e, a in dims]
            where = self.expr(req.get("where") or "", "", 0)
            na_sql = []
            for ent, name, desc in g["nonadd"] or []:
                if not ent:
                    ent = next((k[0] for k, f in self.p.fields.items() if k[1] == name and f["kind"] == "dimension"), "")
                if not ent:
                    raise Unchecked(f"Cannot find the NON ADDITIVE BY dimension {name}")
                na_sql.append((self.field(ent, name), desc))
            needed = set(self._used)
            joins = self.join_path(home, needed - {home})
            rels_used += joins
            alias = {home: "T0"}
            for i, r in enumerate(joins, 1):
                alias.setdefault(r["right"], f"T{i}")

            def sub(x, al=alias):
                return re.sub("\x01([^\x01]+)\x01", lambda m: al[m.group(1)], x)

            def frm(al=alias, js=joins):
                out = f"\nFROM {quote_fqn(self.p.tables[home]['fqn'])} T0"
                for r in js:
                    on = " AND ".join(f"{al[r['left']]}.{quote_ident(lc)} = {al[r['right']]}.{quote_ident(rc)}"
                                      for lc, rc in zip(r["left_cols"], r["right_cols"]))
                    out += f"\n{self.join_type} JOIN {quote_fqn(self.p.tables[r['right']]['fqn'])} {al[r['right']]} ON {on}"
                return out
            conds = [sub(where)] if where.strip() else []
            for expr, desc in na_sql:
                # latest (or earliest for DESC) value of the non-additive dimension inside each output group
                pick = "MIN" if desc else "MAX"
                keys = [sub(e) for e, _ in dsql]
                inner = ("SELECT " + ", ".join(keys + [f"{pick}({sub(expr)})"]) + frm()
                         + ("\nWHERE " + sub(where) if where.strip() else "")
                         + ("\nGROUP BY " + ", ".join(str(i + 1) for i in range(len(keys))) if keys else ""))
                lhs = "(" + ", ".join(keys + [sub(expr)]) + ")" if keys else sub(expr)
                conds.append(f"{lhs} IN ({inner})")
            cols = [f"{sub(e)} AS {a}" for e, a in dsql] + \
                   [f"{sub(g['items'][a])} AS {a}" if a in g["items"] else f"NULL AS {a}" for a in mcols]
            sql = "SELECT " + ", ".join(cols) + frm()
            if conds:
                sql += "\nWHERE " + " AND ".join(f"({c})" for c in conds)
            if dsql:
                sql += "\nGROUP BY " + ", ".join(str(i + 1) for i in range(len(dsql)))
            parts.append(sql)
        if len(parts) == 1:
            return "(" + parts[0] + ")", rels_used
        dcols = [a.strip() for _, a in dims]
        merged = ("SELECT " + ", ".join(dcols + [f"MAX({a}) AS {a}" for a in mcols]) + " FROM (\n"
                  + "\nUNION ALL\n".join(parts) + "\n)" + (" GROUP BY " + ", ".join(dcols) if dcols else ""))
        return "(" + merged + ")", rels_used


# ------------------------------------------------------------------------------------------------------------------
# Comparison helpers
# ------------------------------------------------------------------------------------------------------------------
def _num(v: Any) -> Optional[float]:
    if v is None:
        return None
    if isinstance(v, (int, float, decimal.Decimal)):
        f = float(v)
        return None if math.isnan(f) else f
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def close(a: Any, b: Any) -> bool:
    x, y = _num(a), _num(b)
    if x is None and y is None:
        return True
    if x is None or y is None:
        return (x or 0.0) == 0.0 and (y or 0.0) == 0.0        # "no value" and 0 are the same number on screen
    return abs(x - y) <= max(ABS_TOL, REL_TOL * max(abs(x), abs(y)))


def _key(v: Any) -> str:
    if v is None:
        return "∅"
    if isinstance(v, dt.datetime):
        return v.date().isoformat() if v.time() == dt.time(0) else v.isoformat()
    if isinstance(v, dt.date):
        return v.isoformat()
    if isinstance(v, (int, float, decimal.Decimal)):
        f = float(v)
        return str(int(f)) if f.is_integer() else repr(round(f, 9))
    s = str(v).strip()
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}( 00:00:00(\.0+)?)?", s):
        return s[:10]
    return s


def _show(v: Any) -> Any:
    f = _num(v)
    if f is None:
        return None if v is None else str(v)
    return round(f, 6)


def _chg(kind: Optional[str], cur: Any, base: Any) -> Optional[float]:
    """Change as the tiles show it: points for a percent metric, relative change otherwise."""
    c, b = _num(cur), _num(base)
    if c is None or b is None:
        return None
    if kind == "percent":
        return c - b
    return None if b == 0 else (c - b) / abs(b)


def compare_rows(app: list[dict], ind: list[dict], dkeys: list[str], mkeys: list[str], limit: Optional[int]) -> dict:
    """Row-by-row comparison keyed on the dimension columns."""
    def k(r):
        return tuple(_key(r.get(d)) for d in dkeys)
    ind_by = {}
    for r in ind:
        ind_by.setdefault(k(r), r)
    diffs, missing, compared, worst = [], [], 0, 0.0
    for r in app:
        other = ind_by.get(k(r))
        label = " · ".join(_key(r.get(d)) for d in dkeys) or "Total"
        if other is None:
            missing.append(label)
            continue
        for m in mkeys:
            compared += 1
            a, b = r.get(m), other.get(m)
            if not close(a, b):
                x, y = _num(a), _num(b)
                rel = abs((x or 0) - (y or 0)) / max(abs(y or 0), 1e-12) if (x is not None or y is not None) else 0
                worst = max(worst, rel)
                diffs.append({"label": label, "column": m, "dashboard": _show(a), "independent": _show(b),
                              "diff": (f"{(x - y) / abs(y) * 100:+.3f}%" if x is not None and y not in (None, 0)
                                       else "missing value")})
    app_keys = {k(r) for r in app}
    extra = [r for kk, r in ind_by.items() if kk not in app_keys]
    if limit is not None and len(app) >= limit and mkeys:
        floor = min((_num(r.get(mkeys[0])) for r in app if _num(r.get(mkeys[0])) is not None), default=None)
        extra = [r for r in extra if floor is not None and (_num(r.get(mkeys[0])) or -math.inf) > floor
                 and not close(r.get(mkeys[0]), floor)]
    extra_labels = [" · ".join(_key(r.get(d)) for d in dkeys) or "Total" for r in extra]
    ok = not diffs and not missing and not extra_labels
    return {"ok": ok, "compared": compared, "rows": len(app), "diffs": diffs[:8], "n_diffs": len(diffs),
            "missing": missing[:8], "extra": extra_labels[:8], "worst_rel": worst}


def check(cid: str, status: str, summary: str, detail: str = "", rows: Optional[list] = None,
          sql: Optional[dict] = None) -> dict:
    name, method = CHECKS[cid]
    out = {"id": cid, "name": name, "status": status, "label": LABEL[status], "summary": summary, "method": method}
    if detail:
        out["detail"] = detail
    if rows:
        out["rows"] = rows[:12]
    if sql:
        out["sql"] = sql
    return out


def worst(statuses) -> str:
    statuses = [s for s in statuses if s]
    real = [s for s in statuses if s != "na"]
    if not real:
        return "na"
    return max(real, key=lambda s: RANK[s])


def signature(result: dict, filters: dict) -> str:
    body = json.dumps({"r": result.get("data"), "s": result.get("status"), "f": filters}, sort_keys=True, default=str)
    return hashlib.sha1(body.encode()).hexdigest()[:16]


# ------------------------------------------------------------------------------------------------------------------
# Narrative grounding helpers
# ------------------------------------------------------------------------------------------------------------------
NUMBER = re.compile(r"(?<![\w.])([-+−]?)(\$)?(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)\s*(%|pt|pp|percentage points?|million|billion|thousand|[KMB]\b)?",
                    re.I)


def numbers_in(text: str) -> list[tuple[str, float, str]]:
    """[(as written, value, unit)] - unit in {'%', 'pt', ''}; K/M/B scaled."""
    out = []
    for m in NUMBER.finditer(text or ""):
        sign, cur, digits, unit = m.group(1), m.group(2), m.group(3), (m.group(4) or "")
        try:
            v = float(digits.replace(",", ""))
        except ValueError:
            continue
        u = unit.upper()
        scale = {"K": 1e3, "M": 1e6, "B": 1e9, "THOUSAND": 1e3, "MILLION": 1e6, "BILLION": 1e9}
        if u in scale:
            v *= scale[u]
            u = ""
        elif u.startswith("PERCENTAGE") or u in ("PT", "PP"):
            u = "pt"
        if sign in ("-", "−"):
            v = -v
        out.append((m.group(0).strip(), v, u))
    return out


def grounded(narrative: str, facts: list[str]) -> tuple[list[str], list[str]]:
    """(matched, unmatched) figures of the narrative against the facts. Rounding-tolerant: percentages within
    half a point, amounts within 5%. Small whole numbers (\"3 regions\") and years are not figures."""
    pool = [(v, u) for f in facts for _, v, u in numbers_in(f)]
    matched, unmatched = [], []
    for raw, v, u in numbers_in(narrative):
        if not u and float(v).is_integer() and (abs(v) < 10 or 1900 <= abs(v) <= 2100):
            continue
        pctish = u in ("%", "pt")
        hit = False
        for pv, pu in pool:
            if pctish != (pu in ("%", "pt")):
                continue
            gap = abs(abs(v) - abs(pv))
            if (pctish and gap <= 0.51) or (not pctish and gap <= max(0.051 * abs(pv), 0.01)):
                hit = True
                break
        (matched if hit else unmatched).append(raw)
    return matched, unmatched


# ------------------------------------------------------------------------------------------------------------------
# The validator
# ------------------------------------------------------------------------------------------------------------------
NON_DATA = {"action_table"}            # lists app records (decisions), not governed numbers
SEGMENT_TYPES = {"ranked_bar", "target_bar", "capacity_chart", "period_compare", "share_donut", "driver_bridge"}
PERIOD_TYPES = {"kpi_grid", "kpi_card", "trend_chart", "forecast_band"}


class Validator:
    def __init__(self, session, engine, physical: Optional[Physical], phys_error: str = ""):
        self.session = session
        self.e = engine
        self.p = physical
        self.phys_error = phys_error
        self.q_results: dict[str, dict] = {}
        self.rels_used: dict[str, dict] = {}
        self.queries_run = 0
        self.total_queries = 0
        self.cancelled = False
        self.join_info: list[dict] = []
        self.tables_used: set = set()
        self.diagnosed = 0

    # -- QA-01 ---------------------------------------------------------------------------------------------------------
    def _independent(self, cap: dict) -> dict:
        key = cap["sql"]
        if key in self.q_results:
            return self.q_results[key]
        res: dict[str, Any] = {"app_sql": cap["sql"]}
        try:
            if self.p is None:
                raise Unchecked(self.phys_error or "Semantic view description unavailable")
            tr = Translator(self.p, self.e.model)
            derived, rels = tr.derived(cap["req"])
            for r in rels:
                self.rels_used[r["name"]] = r
            outer = cap["sql"].replace(cap["sv"], derived, 1)
            self.tables_used.update(re.findall(r"(?:FROM|JOIN)\s+([A-Za-z0-9_$.\"]+)\s+T\d+", derived))
            m = re.search(r"\s+LIMIT\s+(\d+)\s*$", outer)
            limit = int(m.group(1)) if m else None
            outer = re.sub(r"\s+LIMIT\s+\d+\s*$", "", outer)
            res.update({"sql": outer, "limit": limit})
        except Unchecked as exc:
            res.update({"status": "na", "reason": str(exc)})
        self.q_results[key] = res
        return res

    def _run_independent(self, on_done: Optional[Callable[[], None]] = None) -> None:
        todo = [r for r in self.q_results.values() if "sql" in r and "rows" not in r and "status" not in r]
        over = todo[MAX_QUERIES:]
        for r in over:
            r.update({"status": "na", "reason": f"Skipped: more than {MAX_QUERIES} independent queries in one run "
                                                "(cost limit). Re-run validation on this page to check it."})
        todo = todo[:MAX_QUERIES]
        self.total_queries = len(todo)

        def go(r):
            if self.cancelled:
                return r, None, "Validation was superseded by a newer run."
            try:
                return r, [row_dict(x) for x in self.session.sql(r["sql"]).collect()], ""
            except Exception as exc:
                return r, None, str(exc)[:300]
        if not todo:
            if on_done:
                on_done()
            return
        with ThreadPoolExecutor(max_workers=min(WORKERS, len(todo))) as pool:
            futures = [pool.submit(go, r) for r in todo]
            for f in as_completed(futures):
                r, rows, err = f.result()
                self.queries_run += 1
                if err:
                    r.update({"status": "na", "reason": "Independent query failed: " + err})
                else:
                    r["rows"] = rows
                if on_done:
                    on_done()

    def qa01(self, caps: list[dict]) -> dict:
        if not caps:
            return check("QA-01", "na", "No governed query recorded for this tile (rebuilt from cache).",
                         "Refresh the page to record its queries, then validation re-runs.")
        total, compared, diffs, missing, extra, reasons, sqls, rows_out = 0, 0, [], [], [], [], [], []
        n_diffs = 0
        statuses = []
        bad = []
        for cap in caps:
            r = self._independent(cap)
            if r.get("status") == "na":
                statuses.append("na")
                reasons.append(r["reason"])
                continue
            req = cap["req"]
            dkeys = [d.rsplit(" AS ", 1)[1].strip().lower() for d in req.get("dims") or []]
            mkeys = [m.rsplit(" AS ", 1)[1].strip().lower() for m in req.get("metrics") or []]
            head = cap["sql"].upper().split("FROM", 1)[0]
            if "SELECT *" not in head:                   # an aggregate over the governed query (e.g. MIN/MAX)
                dkeys, mkeys = [], [k for k in (r.get("rows") or [{}])[0].keys()] if r.get("rows") else []
            cmp = compare_rows(cap["rows"], r.get("rows") or [], dkeys, mkeys, r.get("limit"))
            if not cmp["ok"]:
                bad.append((cap, r, dkeys, mkeys, cmp))
            total += cmp["rows"]
            compared += cmp["compared"]
            diffs += cmp["diffs"]
            n_diffs += cmp["n_diffs"]
            missing += cmp["missing"]
            extra += cmp["extra"]
            statuses.append("pass" if cmp["ok"] else "mismatch")
            sqls.append({"dashboard": cap["sql"], "independent": r["sql"]})
            names = self._labels(req)
            sample = cap["rows"][-4:] if "period" in dkeys else cap["rows"][:4]
            for row in sample:
                lbl = " · ".join(_key(row.get(d)) for d in dkeys) or "Total"
                for mk in mkeys[:2]:
                    other = next((o for o in (r.get("rows") or []) if all(_key(o.get(d)) == _key(row.get(d)) for d in dkeys)), {})
                    rows_out.append({"label": lbl, "column": names.get(mk, mk), "dashboard": _show(row.get(mk)),
                                     "independent": _show(other.get(mk)), "ok": close(row.get(mk), other.get(mk))})
        st = worst(statuses)
        if st == "mismatch":
            summ = (f"{n_diffs} of {compared} value(s) differ from the base tables" if diffs else "") + \
                   (f"{'; ' if diffs else ''}{len(missing)} row(s) not in base tables" if missing else "") + \
                   (f"{'; ' if diffs or missing else ''}{len(extra)} row(s) missing from tile" if extra else "")
            names = {}
            for cap in caps:
                names.update(self._labels(cap["req"]))
            detail_rows = [{**d, "column": names.get(d["column"], d["column"]), "ok": False} for d in diffs] + \
                          [{"label": x, "column": "row", "dashboard": "present", "independent": "absent", "ok": False} for x in missing] + \
                          [{"label": x, "column": "row", "dashboard": "absent", "independent": "present", "ok": False} for x in extra]
            out = check("QA-01", "mismatch", summ, "; ".join(reasons), detail_rows, sqls[0] if sqls else None)
            out["compared"] = compared
            if bad and self.diagnosed < MAX_DIAGNOSES and not self.cancelled:
                self.diagnosed += 1
                try:
                    out["diagnosis"] = self.diagnose(*bad[0][:4])
                except Exception as exc:
                    out["diagnosis"] = {"cause": "error", "proven": False, "title": "Diagnosis could not run",
                                        "explain": str(exc)[:200], "where": "", "fix": "", "action": "app",
                                        "ruled_out": []}
            return out
        if st == "pass":
            part = f" ({len(reasons)} query not checkable: {reasons[0]})" if reasons else ""
            out = check("QA-01", "pass" if not reasons else "review",
                        f"{compared} value(s) in {total} row(s) match the base tables{part}",
                        f"Tolerance: {REL_TOL:g} relative.", rows_out, sqls[0] if sqls else None)
            out["compared"] = compared
            return out
        return check("QA-01", "na", "Not checkable: " + (reasons[0] if reasons else "unknown"), "; ".join(dict.fromkeys(reasons)))

    # -- diagnosis of a QA-01 mismatch -----------------------------------------------------------------------------------
    def _variant_rows(self, cap: dict, tr: "Translator") -> tuple[list[dict], str]:
        derived, _ = tr.derived(cap["req"])
        sql = re.sub(r"\s+LIMIT\s+\d+\s*$", "", cap["sql"].replace(cap["sv"], derived, 1))
        rows = [row_dict(x) for x in self.session.sql(sql).collect()]
        self.queries_run += 1
        return rows, sql

    def diagnose(self, cap: dict, r: dict, dkeys: list, mkeys: list) -> dict:
        """Find the cause of a mismatch by testing variants of the rebuild. A cause is reported only when that
        variant reproduces the dashboard numbers EXACTLY (the whole gap explained); otherwise 'Cause not found'."""
        names = self._labels(cap["req"])
        limit = r.get("limit")
        tested = []

        def same(rows_a, rows_b):
            return compare_rows(rows_a, rows_b, dkeys, mkeys, limit)["ok"]

        # 1. the data moved between the dashboard query and the check (live feeds)
        try:
            now = [row_dict(x) for x in self.session.sql(cap["sql"]).collect()]
            self.queries_run += 1
            if same(now, r.get("rows") or []) and not same(cap["rows"], now):
                return {"cause": "live", "proven": True, "title": "The data changed during the check",
                        "explain": "Running the dashboard's own query again now gives exactly the base-table numbers. "
                                   "The source tables were updated between the dashboard query and the check.",
                        "where": "Nothing to fix: the dashboard showed the data as it was when it loaded.",
                        "fix": "Refresh the dashboard. Validation re-runs and this finding closes.",
                        "action": "refresh", "ruled_out": [], "sql": cap["sql"]}
            tested.append("the data changing during the check")
        except Exception as exc:
            tested.append(f"the data changing (could not re-run: {str(exc)[:80]})")
        # 2. rows with no matching lookup key: the view drops them, the rebuild kept them
        rels = []
        try:
            tr = Translator(self.p, self.e.model)
            _, rels = tr.derived(cap["req"])
        except Unchecked:
            pass
        if rels:
            try:
                tr = Translator(self.p, self.e.model)
                tr.join_type = "INNER"
                rows, sql = self._variant_rows(cap, tr)
                if same(cap["rows"], rows):
                    orph = []
                    for rel in rels:
                        info = next((j for j in self.join_info if j["name"] == rel["name"]), None) or self._join_check(rel)
                        if info and info.get("orphans"):
                            orph.append(info)
                    o = orph[0] if orph else {"left": rels[0]["left"], "right": rels[0]["right"], "orphans": "some",
                                              "fk": rels[0]["left_cols"], "right_table": self.p.tables[rels[0]["right"]]["fqn"],
                                              "left_table": self.p.tables[rels[0]["left"]]["fqn"]}
                    return {"cause": "orphans", "proven": True,
                            "title": f"{o['left']} rows with no matching {o['right']} are left out",
                            "explain": f"The dashboard numbers equal the base tables exactly when {o['left']} rows whose "
                                       f"{', '.join(o['fk'])} has no match in {o['right']} are excluded "
                                       f"({o['orphans']} such rows). The semantic view drops them; a plain left join keeps them.",
                            "where": f"Source data: {o['right_table']} is missing keys used by {o['left_table']}.",
                            "fix": f"Add the missing {o['right']} rows (or correct {o['left']}.{', '.join(o['fk'])}), then "
                                   "re-run. Raise a data issue to give it an owner.",
                            "action": "issue", "ruled_out": tested, "sql": sql}
                tested.append("rows dropped for unmatched keys")
            except Unchecked:
                pass
            except Exception as exc:
                tested.append(f"unmatched keys (query failed: {str(exc)[:80]})")
        # 3. end-of-period balance (NON ADDITIVE BY a date) the check did not apply
        time_ref = None
        for d in cap["req"].get("dims") or []:
            for ent, name in re.findall(rf"({_IDENT})\s*\.\s*({_IDENT})", d):
                try:
                    if self.e.model.field(f"{_unq(ent)}.{_unq(name)}", ("dimension",)).is_time:
                        time_ref = (_unq(ent).upper(), _unq(name).upper())
                except Exception:
                    continue
        bad_refs = []
        for m in cap["req"].get("metrics") or []:
            ref, alias = (x.strip() for x in m.rsplit(" AS ", 1))
            if alias.lower() in mkeys:
                bad_refs.append(ref)
        if time_ref is None:
            time_ref = next(((f.entity.upper(), f.name.upper()) for f in self.e.model.time_dimensions), None)
        if time_ref and bad_refs:
            for desc in (False, True):
                try:
                    tr = Translator(self.p, self.e.model)
                    tr.force_nonadd = {ref.upper(): [(time_ref[0], time_ref[1], desc)] for ref in bad_refs}
                    rows, sql = self._variant_rows(cap, tr)
                    if same(cap["rows"], rows):
                        label = ", ".join(names.get(k, k) for k in mkeys)
                        return {"cause": "semi_additive", "proven": True,
                                "title": f"{label} is an end-of-period balance",
                                "explain": f"The dashboard numbers equal the base tables exactly when only the "
                                           f"{'first' if desc else 'latest'} {time_ref[1].lower().replace('_', ' ')} in each "
                                           "period is used (NON ADDITIVE BY). The check summed every day instead because it "
                                           "did not read that rule from the semantic view.",
                                "where": "App (the validation reader), not your data. The dashboard numbers are correct.",
                                "fix": "App update: read the NON ADDITIVE rule for this metric. Send this finding to the app team.",
                                "action": "app", "ruled_out": tested, "sql": sql}
                except Unchecked:
                    break
                except Exception as exc:
                    tested.append(f"end-of-period rule (query failed: {str(exc)[:80]})")
                    break
            else:
                tested.append("an end-of-period (NON ADDITIVE BY) rule")
        return {"cause": "unknown", "proven": False, "title": "Cause not found",
                "explain": "The difference is not explained by: " + "; ".join(tested or ["(no tests could run)"]) + ".",
                "where": "Needs investigation: compare the semantic view definition (GET_DDL) with the rebuilt SQL.",
                "fix": "Send this finding to the app team with its evidence. Until then, accept it with a reason or "
                       "raise a data issue.",
                "action": "app", "ruled_out": tested}

    def _join_check(self, rel: dict) -> Optional[dict]:
        try:
            ref, fact = self.p.tables[rel["right"]]["fqn"], self.p.tables[rel["left"]]["fqn"]
            on = " AND ".join(f"L.{quote_ident(a)} = R.{quote_ident(b)}" for a, b in zip(rel["left_cols"], rel["right_cols"]))
            notnull = " AND ".join(f"L.{quote_ident(a)} IS NOT NULL" for a in rel["left_cols"])
            o = row_dict(self.session.sql(
                f"SELECT COUNT(*) AS N, COUNT_IF(R.{quote_ident(rel['right_cols'][0])} IS NULL) AS ORPHANS "
                f"FROM {quote_fqn(fact)} L LEFT JOIN {quote_fqn(ref)} R ON {on} WHERE {notnull}").collect()[0])
            self.queries_run += 1
            return {"left": rel["left"], "right": rel["right"], "fk": rel["left_cols"], "orphans": int(o.get("orphans") or 0),
                    "left_table": fact, "right_table": ref}
        except Exception:
            return None

    def _labels(self, req: dict) -> dict:
        """column alias (m0) -> metric label (Sales) for readable evidence."""
        out = {}
        for m in req.get("metrics") or []:
            ref, alias = (x.strip() for x in m.rsplit(" AS ", 1))
            label = next((f.label for f in self.e.model.metrics if f.ref == ref), None)
            if label:
                out[alias.lower()] = label
        return out

    # -- QA-02 / QA-03 --------------------------------------------------------------------------------------------------
    def qa02(self, comp: dict, data: dict) -> Optional[dict]:
        from engine import pct
        t = comp["type"]
        bad, n = [], 0

        def chk(label, shown, expect):
            nonlocal n
            n += 1
            if not close(shown, expect):
                bad.append({"label": label, "column": "value", "dashboard": _show(shown), "independent": _show(expect),
                            "ok": False})
        if t in ("kpi_grid", "kpi_card"):
            for it in data.get("items") or []:
                chk(f"{it['label']} change vs prior", it.get("change"), pct(it.get("current"), it.get("prior")))
                chk(f"{it['label']} change vs year ago", it.get("yoy_change"), pct(it.get("current"), it.get("yoy")))
                chk(f"{it['label']} headline delta", it.get("delta"), pct(it.get("current"), it.get("base")))
                if it.get("delta_pt") is not None:
                    chk(f"{it['label']} change in points", it["delta_pt"], (it.get("current") or 0) - (it.get("base") or 0))
        elif t in ("ranked_bar", "target_bar", "capacity_chart", "period_compare"):
            rows = data.get("rows") or []
            for r in rows:
                chk(f"{r['segment']} change vs prior", r.get("change"), pct(r.get("current"), r.get("prior")))
                chk(f"{r['segment']} change vs year ago", r.get("yoy_change"), pct(r.get("current"), r.get("yoy")))
        elif t == "share_donut":
            sl = data.get("slices") or []
            total = data.get("total")
            chk("Total = sum of slices", total, sum(_num(s.get("value")) or 0 for s in sl))
            for s in sl:
                if total:
                    chk(f"{s['label']} share", s.get("share"), (_num(s.get("value")) or 0) / total)
            if sl and total:
                chk("Shares add to 100%", sum(_num(s.get("share")) or 0 for s in sl), 1.0)
        elif t == "pareto":
            rows = data.get("rows") or []
            prev = 0.0
            for r in rows:
                c = _num(r.get("cum_share")) or 0
                n += 1
                if c + 1e-9 < prev or c > 1 + 1e-9:
                    bad.append({"label": r.get("label"), "column": "cumulative share", "dashboard": _show(c),
                                "independent": "non-decreasing, ≤ 100%", "ok": False})
                prev = c
        elif t == "driver_bridge":
            steps = data.get("steps") or []
            chk("Start + changes = end", (data.get("start") or 0) + sum(_num(s.get("delta")) or 0 for s in steps), data.get("end"))
        elif t == "treemap":
            groups = data.get("groups") or []
            shown = data.get("shown")
            chk("Boxes add up to the value shown", sum(_num(g.get("value")) or 0 for g in groups), shown)
            for g in groups:
                if shown:
                    chk(f"{g['label']} share", g.get("share"), (_num(g.get("value")) or 0) / shown)
                chk(f"{g['label']} change vs prior", g.get("change"), pct(g.get("value"), g.get("prior")))
                kids = g.get("children") or []
                if kids:
                    chk(f"{g['label']} = sum of its boxes", g.get("value"), sum(_num(c.get("value")) or 0 for c in kids))
                    for c in kids:
                        chk(f"{g['label']} / {c['label']} change vs prior", c.get("change"),
                            pct(c.get("value"), c.get("prior")))
            if groups and shown:
                chk("Shares add to 100%", sum(_num(g.get("share")) or 0 for g in groups), 1.0)
        elif t == "gauge":
            a, tg, ex = data.get("actual"), data.get("target"), data.get("expected")
            if a is not None and tg:
                chk("Progress = year to date / full-year target", data.get("progress"), a / tg)
            if a is not None and ex:
                chk("Pace = year to date / target by now", data.get("pace"), a / ex)
                if tg is not None:
                    chk("Projected finish = target × pace", data.get("projected"), tg * (a / ex))
            if ex is not None and tg:
                chk("Expected position = target by now / full-year target", data.get("expected_share"), ex / tg)
        elif t == "pnl_table":
            for r in data.get("rows") or []:
                kind = r.get("kind")
                ch = (lambda v, b: None if v is None or b is None else
                      (v - b if kind == "percent" else pct(v, b)))
                for col, c in zip(data.get("columns") or [], r.get("cells") or []):
                    chk(f"{r['label']} / {col} change", c.get("change"), ch(c.get("value"), c.get("base")))
                tot = r.get("total") or {}
                chk(f"{r['label']} total change", tot.get("change"), ch(tot.get("value"), tot.get("base")))
        elif t == "kpi_plan":
            for it in data.get("items") or []:
                k = it.get("kind")
                chk(f"{it['label']} vs {it.get('target_label') or 'target'}", it.get("delta"),
                    _chg(k, it.get("value"), it.get("target")))
                chk(f"{it['label']} vs last year", it.get("delta_py"), _chg(k, it.get("value"), it.get("py")))
                if it.get("month_target") is not None:
                    chk(f"{it['label']} latest month vs plan", it.get("month_delta"),
                        _chg(k, it.get("month"), it.get("month_target")))
        elif t == "scorecard":
            cols = data.get("columns") or []
            for r in (data.get("rows") or []) + ([data["total"]] if data.get("total") else []):
                for col, c in zip(cols, r.get("cells") or []):
                    chk(f"{r['segment']} / {col['label']} vs {col.get('compare', 'base')}", c.get("delta"),
                        _chg(col.get("kind"), c.get("value"), c.get("base")))
        elif t == "status_tiles":
            for it in data.get("items") or []:
                chk(f"{it['label']} vs {data.get('compare_label') or 'last week'}", it.get("delta"),
                    _chg(it.get("kind"), it.get("current"), it.get("base")))
        elif t in ("pace_chart", "ytd_trajectory"):
            ser = {x["key"]: x.get("values") or [] for x in data.get("series") or []}
            now = data.get("now_index")
            main = ser.get("today") or ser.get("actual") or []
            if now is not None and main:
                n += 1
                late = [v for v in main[now + 1:] if v is not None]
                if late:
                    bad.append({"label": "Line stops at the latest data", "column": "points after now",
                                "dashboard": len(late), "independent": 0, "ok": False})
            if t == "pace_chart" and data.get("mode") == "hour" and now is not None and ser.get("last"):
                cur, last = main[now], ser["last"][now]
                chk("Pace = today so far / last week by the same hour", data.get("pace"), pct(cur, last))
                if data.get("pace") is not None:
                    chk("Projected close = last week's close × pace", data.get("projected"),
                        ser["last"][-1] * (1 + data["pace"]))
            fc = ser.get("forecast")
            if t == "ytd_trajectory" and fc and now is not None:
                chk("Forecast starts where the actual line ends", fc[now], main[now])
        elif t == "worklist":
            rows = data.get("rows") or []
            for r in rows:
                lab = f"{r.get('metric_label')} · {r.get('segment')}"
                chk(f"{lab} deviation vs a normal day", r.get("deviation"),
                    _chg(r.get("kind"), r.get("current"), r.get("normal")))
                z = _num(r.get("z")) or 0
                n += 1
                if bool(r.get("worse")) != (z > 0 if r.get("inverse") else z < 0):
                    bad.append({"label": f"{lab} direction", "column": "worse", "dashboard": r.get("worse"),
                                "independent": not r.get("worse"), "ok": False})
                n += 1
                sev = "High" if abs(z) >= 3 else "Medium" if abs(z) >= 1.5 else "Watch"
                if r.get("severity") != sev:
                    bad.append({"label": f"{lab} severity", "column": "z", "dashboard": r.get("severity"),
                                "independent": sev, "ok": False})
            sc = [_num(r.get("score")) or 0 for r in rows]
            if len(sc) > 1:
                n += 1
                if any(a + 1e-9 < b for a, b in zip(sc, sc[1:])):
                    bad.append({"label": "Worst first", "column": "order", "dashboard": "not sorted",
                                "independent": "sorted by score", "ok": False})
        elif t in ("exception_table", "exception_queue", "risk_table"):
            rows = data.get("rows") or []
            for r in rows:
                seg = r.get("segment")
                chk(f"{seg} % vs expected", r.get("deviation"), pct(r.get("current"), r.get("expected")))
                z = _num(r.get("z")) or 0
                n += 1
                if z and r.get("direction") != ("above" if z > 0 else "below"):
                    bad.append({"label": f"{seg} direction", "column": "z", "dashboard": r.get("direction"),
                                "independent": "above" if z > 0 else "below", "ok": False})
                if not data.get("ml") and r.get("severity") != "Watch":
                    n += 1
                    if bool(r.get("is_anomaly")) != (abs(z) >= 2):
                        bad.append({"label": f"{seg} flagged", "column": "|z| ≥ 2", "dashboard": r.get("is_anomaly"),
                                    "independent": abs(z) >= 2, "ok": False})
            zs = [abs(_num(r.get("z")) or 0) for r in rows]
            if len(zs) > 1:
                n += 1
                if any(a + 1e-9 < b for a, b in zip(zs, zs[1:])):
                    bad.append({"label": "Largest deviation first", "column": "order", "dashboard": "not sorted",
                                "independent": "sorted by |z|", "ok": False})
        elif t == "combo_chart":
            pts = data.get("points") or []
            per = [p.get("period") for p in pts]
            n += 1
            if per != sorted(per) or len(set(per)) != len(per):
                bad.append({"label": "Periods in order, each once", "column": "period", "dashboard": "out of order",
                            "independent": "ascending", "ok": False})
        elif t == "small_multiples":
            for pn in data.get("panels") or []:
                per = [p.get("period") for p in pn.get("points") or []]
                n += 1
                if per != sorted(per):
                    bad.append({"label": f"{pn.get('segment')} periods in order", "column": "period",
                                "dashboard": "out of order", "independent": "ascending", "ok": False})
        elif t in ("heatmap", "segment_matrix"):
            rws, cls, vals = data.get("rows") or [], data.get("cols") or [], data.get("values") or []
            n += 1
            if len(vals) != len(rws) or any(len(v) != len(cls) for v in vals):
                bad.append({"label": "Every cell sits under its row and column", "column": "shape",
                            "dashboard": f"{len(vals)} rows", "independent": f"{len(rws)} × {len(cls)}", "ok": False})
        else:
            return None
        if not n:
            return None
        if bad:
            return check("QA-02", "mismatch", f"{len(bad)} of {n} displayed calculation(s) disagree", rows=bad)
        return check("QA-02", "pass", f"{n} displayed calculation(s) recomputed and match")

    def qa03(self, comp: dict, data: dict) -> Optional[dict]:
        t = comp["type"]
        e = self.e
        if t == "treemap":
            return self._qa03_treemap(comp, data)
        if t == "pnl_table":
            return self._qa03_pnl(data)
        extra = {"kpi_plan": self._qa03_kpi_plan, "ytd_trajectory": self._qa03_ytd, "scorecard": self._qa03_scorecard,
                 "small_multiples": self._qa03_latest_by_segment, "exception_table": self._qa03_latest_by_segment,
                 "exception_queue": self._qa03_latest_by_segment, "risk_table": self._qa03_latest_by_segment,
                 "scatter": self._qa03_scatter, "combo_chart": self._qa03_combo}.get(t)
        if extra:
            return extra(comp, data)
        if t not in SEGMENT_TYPES | {"segment_matrix", "heatmap"}:
            return None
        try:
            m = e._metric_for(comp)
            field = e.model.field(m, ("metric",))
        except Exception:
            return None
        if not field.additive:
            return check("QA-03", "na", f"{field.label} is not additive (ratio, average or distinct count), so its "
                                        "segments are not expected to add up to the total.")
        try:
            total = e.value_at(e.metric_series(m), m, e.cal.current_start)
            if t in ("segment_matrix", "heatmap"):
                vals = [v for row in data.get("values") or [] for v in row]
                parts = sum(_num(v) or 0 for v in vals)
                note = "Matrix cells shown"
                if len(data.get("rows") or []) >= 15 or len(data.get("cols") or []) >= 12:
                    return check("QA-03", "na", "Matrix is truncated to the largest rows/columns, so cells cannot add "
                                                "up to the total by design.")
            else:
                dim = e._segment_dim(comp) if t != "driver_bridge" else (comp.get("dimension") or e.b.segment_dimension)
                snap = e._snapshot(m, dim)
                parts = sum((r["current"] or 0) for r in snap)
                note = f"All {len(snap)} {e.dlabel(dim)} values"
        except Exception as exc:
            return check("QA-03", "na", "Could not reconcile: " + str(exc)[:160])
        rows = [{"label": f"{note} ({e.cal.label(e.cal.current_start)})", "column": field.label,
                 "dashboard": _show(parts), "independent": _show(total), "ok": close(parts, total)}]
        if close(parts, total):
            return check("QA-03", "pass", f"Segments add up to the {field.label} total", rows=rows)
        return check("QA-03", "mismatch", f"Segments add up to {_show(parts)}, total is {_show(total)}",
                     "Rows with no value for the breakdown, or a breakdown not related to the metric, can cause this.",
                     rows=rows)

    def _qa03_treemap(self, comp: dict, data: dict) -> Optional[dict]:
        e = self.e
        try:
            field = e.model.field(e._metric_for(comp), ("metric",))
        except Exception:
            return None
        if not field.additive:
            return check("QA-03", "na", f"{field.label} is not additive, so its boxes are not expected to add up.")
        parts = (_num(data.get("shown")) or 0) + (_num(data.get("excluded")) or 0)
        total = data.get("total")
        note = "All boxes" + (f" plus {data.get('excluded_count')} zero/negative value(s) not drawn"
                              if data.get("excluded_count") else "")
        rows = [{"label": f"{note} ({data.get('period_label', '')})", "column": field.label,
                 "dashboard": _show(parts), "independent": _show(total), "ok": close(parts, total)}]
        if close(parts, total):
            return check("QA-03", "pass", f"Boxes add up to the {field.label} total", rows=rows)
        return check("QA-03", "mismatch", f"Boxes add up to {_show(parts)}, total is {_show(total)}",
                     "Rows with no value for the breakdown can cause this.", rows=rows)

    def _qa03_pnl(self, data: dict) -> Optional[dict]:
        if data.get("truncated"):
            return check("QA-03", "na", "Only the largest columns are shown, so they cannot add up to the total.")
        rows, n_add = [], 0
        for r in data.get("rows") or []:
            if not r.get("additive"):
                continue
            n_add += 1
            parts = sum(_num(c.get("value")) or 0 for c in r.get("cells") or [])
            total = (r.get("total") or {}).get("value")
            rows.append({"label": f"{r['label']}: columns vs total", "column": r["label"], "dashboard": _show(parts),
                         "independent": _show(total), "ok": close(parts, total)})
        if not n_add:
            return check("QA-03", "na", "No additive metric in this table (ratios and averages do not add up).")
        bad = [x for x in rows if not x["ok"]]
        if bad:
            return check("QA-03", "mismatch", f"{len(bad)} of {n_add} additive row(s) do not add up to their total",
                         "Rows with no value for the column dimension can cause this.", rows=rows)
        return check("QA-03", "pass", f"{n_add} additive row(s) add up to their total", rows=rows)

    # -- QA-03 for the persona tiles and the newer charts: each figure against a separate governed query ------------
    def _additive(self, m: str) -> bool:
        try:
            return bool(self.e.model.field(m, ("metric",)).additive)
        except Exception:
            return False

    def _verdict(self, rows: list[dict], ok_text: str, bad_text: str, why: str = "") -> dict:
        bad = [x for x in rows if not x["ok"]]
        if bad:
            return check("QA-03", "mismatch", f"{len(bad)} of {len(rows)} {bad_text}", why, rows=rows)
        return check("QA-03", "pass", ok_text, rows=rows)

    def _qa03_kpi_plan(self, comp: dict, data: dict) -> Optional[dict]:
        rows, skipped = [], []
        for it in data.get("items") or []:
            m = it.get("metric")
            if not self._additive(m):
                skipped.append(it["label"])
                continue
            spark = [_num(v) for v in it.get("spark") or []]
            if spark and it.get("value") is not None:
                parts = sum(v or 0 for v in spark)
                rows.append({"label": f"{it['label']}: months add up to year to date", "column": it["label"],
                             "dashboard": _show(it["value"]), "independent": _show(parts),
                             "ok": close(it["value"], parts)})
            tsp = [_num(v) for v in it.get("target_spark") or []]
            if tsp and it.get("target_label") == "plan" and it.get("target") is not None:
                parts = sum(v or 0 for v in tsp)
                rows.append({"label": f"{it['label']}: plan months add up to plan to date", "column": "Plan",
                             "dashboard": _show(it["target"]), "independent": _show(parts),
                             "ok": close(it["target"], parts)})
        if not rows:
            return check("QA-03", "na", "No additive metric on this tile (ratios and averages do not add up)."
                         if skipped else "Nothing to reconcile.")
        note = f" {', '.join(skipped)} not additive, not reconciled." if skipped else ""
        return self._verdict(rows, f"Year-to-date values equal the sum of their months.{note}",
                             "year-to-date value(s) differ from the sum of their months",
                             "The monthly trend and the year-to-date total come from two separate queries.")

    def _qa03_ytd(self, comp: dict, data: dict) -> Optional[dict]:
        e = self.e
        m = e._metric_for(comp)
        if not self._additive(m):
            return check("QA-03", "na", f"{e.mlabel(m)} is not additive, so a running total is not meaningful to "
                                        "reconcile.")
        ser = {x["key"]: x.get("values") or [] for x in data.get("series") or []}
        now = data.get("now_index")
        if now is None or not ser.get("actual"):
            return None
        start, end, py_start, py_end = e._ytd_bounds()
        rows = []
        tot = e._totals([m], start, end).get(m)
        rows.append({"label": f"Running total at {data['labels'][now]} vs year-to-date total", "column": e.mlabel(m),
                     "dashboard": _show(ser["actual"][now]), "independent": _show(tot),
                     "ok": close(ser["actual"][now], tot)})
        if ser.get("py"):
            mo = now + 1                      # the reference line holds whole months of last year
            py_to = dt.date(py_start.year + (mo == 12), 1 if mo == 12 else mo + 1, 1)
            ptot = e._totals([m], py_start, py_to).get(m)
            rows.append({"label": f"Last year's line at {data['labels'][now]} vs last year to the end of "
                                  f"{data['labels'][now]}",
                         "column": e.mlabel(m), "dashboard": _show(ser["py"][now]), "independent": _show(ptot),
                         "ok": close(ser["py"][now], ptot)})
        plan = e.plan_metric(m)
        if ser.get("plan") and plan:
            y = start.year
            ftot = e._totals([plan], dt.date(y, 1, 1), dt.date(y + 1, 1, 1)).get(plan)
            rows.append({"label": "Plan line at December vs full-year plan", "column": e.mlabel(plan),
                         "dashboard": _show(ser["plan"][-1]), "independent": _show(ftot),
                         "ok": close(ser["plan"][-1], ftot)})
        return self._verdict(rows, "Running totals match separate year-to-date queries",
                             "running total(s) differ from the year-to-date query",
                             "Months with no data, or a time filter on the tile, can cause this.")

    def _qa03_scorecard(self, comp: dict, data: dict) -> Optional[dict]:
        rows_in = data.get("rows") or []
        if len(rows_in) >= 15:
            return check("QA-03", "na", "Only the 15 largest rows are shown, so they cannot add up to the total.")
        total = (data.get("total") or {}).get("cells") or []
        rows, skipped = [], []
        for i, col in enumerate(data.get("columns") or []):
            if not self._additive(col["metric"]):
                skipped.append(col["label"])
                continue
            parts = sum(_num((r.get("cells") or [{}] * (i + 1))[i].get("value")) or 0 for r in rows_in)
            tv = total[i].get("value") if i < len(total) else None
            rows.append({"label": f"{col['label']}: rows vs Total row", "column": col["label"],
                         "dashboard": _show(parts), "independent": _show(tv), "ok": close(parts, tv)})
        if not rows:
            return check("QA-03", "na", "No additive column (ratios and averages do not add up).")
        note = f" {', '.join(skipped)} not additive." if skipped else ""
        return self._verdict(rows, f"Rows add up to the Total row.{note}", "column(s) do not add up to the Total row",
                             "Rows with no value for the breakdown can cause this.")

    def _segment_values(self, m: str, dim: str) -> dict[str, Optional[float]]:
        e = self.e
        got = e._rows([m], [dim], e.cal.current_start, e.cal.end_exclusive)
        return {str(r[dim]): r.get(m) for r in got}

    def _qa03_latest_by_segment(self, comp: dict, data: dict) -> Optional[dict]:
        """Latest value per segment on the tile (from the period series) vs a separate query for that period."""
        e = self.e
        m, dim = e._metric_for(comp), e._segment_dim(comp)
        ref = self._segment_values(m, dim)
        cur = e.cal.current_start.isoformat()
        rows = []
        if comp["type"] == "small_multiples":
            for pn in data.get("panels") or []:
                v = next((p.get("value") for p in pn.get("points") or [] if str(p.get("period"))[:10] == cur), None)
                if v is None:
                    continue
                rows.append({"label": f"{pn['segment']} ({e.cal.label(e.cal.current_start)})", "column": e.mlabel(m),
                             "dashboard": _show(v), "independent": _show(ref.get(str(pn["segment"]))),
                             "ok": close(v, ref.get(str(pn["segment"])))})
        else:
            for r in data.get("rows") or []:
                rows.append({"label": f"{r['segment']} ({e.cal.label(e.cal.current_start)})", "column": e.mlabel(m),
                             "dashboard": _show(r.get("current")), "independent": _show(ref.get(str(r["segment"]))),
                             "ok": close(r.get("current"), ref.get(str(r["segment"])))})
        if not rows:
            return check("QA-03", "na", "No value in the latest period to reconcile.")
        return self._verdict(rows, "Latest values match a separate query for the period",
                             "latest value(s) differ from a separate query for the period",
                             "The tile reads a period series; the check queries the period directly.")

    def _qa03_scatter(self, comp: dict, data: dict) -> Optional[dict]:
        e = self.e
        m, m2 = e._metric_for(comp), comp.get("metric2_id")
        pts = data.get("points") or []
        if len(pts) >= 150:
            return check("QA-03", "na", "Only the first 150 points are drawn, so they cannot add up to the total.")
        start = max(e.cal.window_start, shift(e.cal.current_start, e.cal.grain, -11))
        rows, skipped = [], []
        for key, met in (("x", m), ("y", m2)):
            if not met or not self._additive(met):
                skipped.append(e.mlabel(met) if met else key)
                continue
            parts = sum(_num(p.get(key)) or 0 for p in pts)
            tot = e._totals([met], start, e.cal.end_exclusive).get(met)
            rows.append({"label": f"All points vs the {data.get('period_label', 'window')} total", "column": e.mlabel(met),
                         "dashboard": _show(parts), "independent": _show(tot), "ok": close(parts, tot)})
        if not rows:
            return check("QA-03", "na", "Neither metric is additive (ratios and averages do not add up).")
        note = f" {', '.join(skipped)} not additive." if skipped else ""
        return self._verdict(rows, f"Points add up to the total for the window.{note}",
                             "metric(s) do not add up to the window total",
                             "Points with a missing value for either metric are not drawn and can cause this.")

    def _qa03_combo(self, comp: dict, data: dict) -> Optional[dict]:
        e = self.e
        pts = data.get("points") or []
        cur = e.cal.current_start.isoformat()
        last = pts[-1] if pts else None
        if not last or str(last.get("period"))[:10] != cur:
            return check("QA-03", "na", "The latest period is not on the chart, nothing to reconcile.")
        m, m2 = data.get("metric") or e._metric_for(comp), data.get("metric2") or comp.get("metric2_id")
        tot = e._totals([x for x in (m, m2) if x], e.cal.current_start, e.cal.end_exclusive)
        rows = [{"label": f"Bar for {last['label']} vs the period total", "column": e.mlabel(m),
                 "dashboard": _show(last.get("bar")), "independent": _show(tot.get(m)), "ok": close(last.get("bar"), tot.get(m))}]
        if m2:
            rows.append({"label": f"Line for {last['label']} vs the period value", "column": e.mlabel(m2),
                         "dashboard": _show(last.get("line")), "independent": _show(tot.get(m2)),
                         "ok": close(last.get("line"), tot.get(m2))})
        return self._verdict(rows, "Latest bar and line match a separate query for the period",
                             "value(s) differ from a separate query for the period")

    # -- QA-06 (tile) ---------------------------------------------------------------------------------------------------
    def qa06(self, comp: dict, data: dict) -> Optional[dict]:
        e, t = self.e, comp["type"]
        notes, status = [], "pass"
        try:
            m = e._metric_for(comp)
            name = e.model.field(m, ("metric",)).name
        except Exception:
            m, name = None, ""
        # gaps in the time series
        if t in ("trend_chart", "forecast_band", "kpi_grid", "kpi_card"):
            if t in ("kpi_grid", "kpi_card"):
                ms = [x for x in (comp.get("metrics") or []) if x in {f.id for f in e.model.metrics}]
                series = e.multi_series(ms) if ms else e.kpi_series()
            else:
                series = e.metric_series(m)
            have = {r["period"] for r in series}
            p, gaps = e.cal.window_start, []
            while p <= e.cal.current_start:
                if p.isoformat() not in have:
                    gaps.append(e.cal.label(p))
                p = shift(p, e.cal.grain, 1)
            if gaps:
                status = "review"
                notes.append(f"{len(gaps)} {e.cal.grain}(s) with no data in the window: {', '.join(gaps[:6])}"
                             + ("…" if len(gaps) > 6 else ""))
            else:
                notes.append(f"No gaps: every {e.cal.grain} from {e.cal.label(e.cal.window_start)} to "
                             f"{e.cal.label(e.cal.current_start)} has data")
        # blank categories
        rows = data.get("rows") if isinstance(data.get("rows"), list) else []
        if t in SEGMENT_TYPES and rows:
            cur = [r for r in rows if isinstance(r, dict) and "segment" in r]
            tot = sum(abs(_num(r.get("current")) or 0) for r in cur)
            blank = sum(abs(_num(r.get("current")) or 0) for r in cur if r.get("segment") == "(blank)")
            if tot and blank:
                share = blank / tot
                if share > BLANK_REVIEW_SHARE:
                    status = "review"
                notes.append(f"{share * 100:.1f}% of the value has a blank category")
        if t == "share_donut":
            blank = next((s for s in data.get("slices") or [] if s.get("label") == "(blank)"), None)
            if blank and (blank.get("share") or 0) > BLANK_REVIEW_SHARE:
                status = "review"
                notes.append(f"{blank['share'] * 100:.1f}% of the value has a blank category")
        # impossible negatives
        if name and POSITIVE_ONLY.search(name) and not SIGNED.search(name):
            neg = []
            for r in rows or []:
                if isinstance(r, dict) and (_num(r.get("current")) or 0) < 0:
                    neg.append(str(r.get("segment")))
            for p in data.get("points") or []:
                if (_num(p.get("value")) or 0) < 0:
                    neg.append(str(p.get("label")))
            for it in data.get("items") or []:
                if (_num(it.get("current")) or 0) < 0:
                    neg.append(str(it.get("label")))
            if neg:
                status = "review"
                notes.append(f"Negative values where they are unexpected: {', '.join(neg[:5])}")
        if not notes:
            return None
        return check("QA-06", status, notes[0] if len(notes) == 1 else f"{len(notes)} data health notes",
                     "\n".join(notes))

    def qa07(self, cid: str, result: dict) -> Optional[dict]:
        e = self.e
        if not e.filters:
            return None
        text = "; ".join(f"{e.dlabel(d)} = {', '.join(map(str, v))}" for d, v in e.filters.items())
        skipped = result.get("skipped_filters") or []
        if skipped:
            return check("QA-07", "review", f"Filter not applied to this tile: {', '.join(skipped)}",
                         "The semantic view cannot split this metric by that field, so the tile shows the unfiltered "
                         "value. Viewers see a note on the tile.")
        return check("QA-07", "pass", f"Filters applied: {text}",
                     "The same filter is in the tile's governed query and in the independent base-table query.")

    # -- dashboard-level checks -----------------------------------------------------------------------------------------
    def qa04(self) -> dict:
        if self.p is None:
            return check("QA-04", "na", "Not checkable: " + (self.phys_error or "semantic view description unavailable"))
        if not self.rels_used:
            if len(self.p.tables) <= 1:
                return check("QA-04", "pass", "Single base table: no joins, so no double counting is possible.")
            return check("QA-04", "pass", "The tiles on this page read one base table each: no joins were needed.")
        rows, statuses, sqls = [], [], []
        for r in self.rels_used.values():
            ref = self.p.tables[r["right"]]["fqn"]
            fact = self.p.tables[r["left"]]["fqn"]
            keys = ", ".join(quote_ident(c) for c in r["right_cols"])
            u_sql = f"SELECT COUNT(*) AS N, COUNT(DISTINCT {keys}) AS D FROM {quote_fqn(ref)}"
            on = " AND ".join(f"L.{quote_ident(a)} = R.{quote_ident(b)}" for a, b in zip(r["left_cols"], r["right_cols"]))
            notnull = " AND ".join(f"L.{quote_ident(a)} IS NOT NULL" for a in r["left_cols"])
            o_sql = (f"SELECT COUNT(*) AS N, COUNT_IF(R.{quote_ident(r['right_cols'][0])} IS NULL) AS ORPHANS "
                     f"FROM {quote_fqn(fact)} L LEFT JOIN {quote_fqn(ref)} R ON {on} WHERE {notnull}")
            sqls.append({"dashboard": f"Relationship {r['name']}", "independent": u_sql + ";\n" + o_sql})
            try:
                u = row_dict(self.session.sql(u_sql).collect()[0])
                o = row_dict(self.session.sql(o_sql).collect()[0])
                self.queries_run += 2
            except Exception as exc:
                statuses.append("na")
                rows.append({"label": r["name"], "column": "check", "dashboard": "error", "independent": str(exc)[:120],
                             "ok": False})
                continue
            n, d = int(u.get("n") or 0), int(u.get("d") or 0)
            fn, orph = int(o.get("n") or 0), int(o.get("orphans") or 0)
            self.join_info.append({"name": r["name"], "left": r["left"], "right": r["right"],
                                   "left_table": fact, "right_table": ref, "keys": r["right_cols"],
                                   "fk": r["left_cols"], "lookup_rows": n, "distinct_keys": d,
                                   "fact_rows": fn, "orphans": orph, "unique": n == d})
            dup_ok, orph_ok = n == d, orph == 0
            statuses.append("pass" if dup_ok and orph_ok else "mismatch" if not dup_ok else "review")
            rows.append({"label": f"{r['right']} key ({', '.join(r['right_cols'])})", "column": "unique keys",
                         "dashboard": d, "independent": n, "ok": dup_ok})
            rows.append({"label": f"{r['left']} rows with no {r['right']} match", "column": "orphans",
                         "dashboard": orph, "independent": f"of {fn}", "ok": orph_ok})
        st = worst(statuses)
        summ = {"pass": f"{len(self.rels_used)} join(s): keys unique and every fact row finds its lookup row",
                "review": "Some fact rows have no lookup row; they show as (blank)",
                "mismatch": "A lookup key is not unique: joined rows are double counted",
                "na": "Join checks could not run"}[st]
        return check("QA-04", st, summ, rows=rows, sql=sqls[0] if sqls else None)

    def qa05(self) -> dict:
        e, cal = self.e, self.e.cal
        g = cal.grain
        rows, status, notes = [], "pass", []
        nxt = shift(cal.current_start, g, 1)
        complete = (cal.max_date + dt.timedelta(days=1)) >= nxt
        exp_prior, exp_yoy = shift(cal.current_start, g, -1), shift(cal.current_start, g, -periods_per_year(g))
        for label, shown, expect in (("Current period starts", cal.current_start, period_start(cal.current_start, g)),
                                     ("Prior period starts", cal.prior_start, exp_prior),
                                     ("Year-ago period starts", cal.yoy_start, exp_yoy)):
            ok = shown == expect
            rows.append({"label": label, "column": g, "dashboard": shown.isoformat(), "independent": expect.isoformat(),
                         "ok": ok})
            if not ok:
                status = "mismatch"
        rows.append({"label": "Current period complete", "column": "data through", "dashboard": cal.max_date.isoformat(),
                     "independent": f"needs ≥ {(nxt - dt.timedelta(days=1)).isoformat()}", "ok": complete})
        if not complete:
            status = "mismatch"
        latest_partial = period_start(cal.max_date, g)
        if latest_partial != cal.current_start and latest_partial > cal.current_start:
            notes.append(f"{cal.label(latest_partial)} is still in progress (data through {cal.max_date.isoformat()}), "
                         f"so the dashboard compares the last complete {g}: {cal.label(cal.current_start)}.")
        if g == "week":
            notes.append("Year-ago for weeks is 52 weeks earlier (same weekday).")
        # coverage from the base tables
        sqls = None
        try:
            if self.p is None:
                raise Unchecked(self.phys_error or "semantic view description unavailable")
            tr = Translator(self.p, e.model)
            time = e.q.dim(e.b.time_dimension)
            req = {"dims": [e.q.trunc(time, "day", "D")], "metrics": [f"{e.q.metric(e.b.primary_metric).ref} AS V"],
                   "where": ""}
            derived, _ = tr.derived(req)
            sql = f"SELECT MIN(D) AS MIN_D, MAX(D) AS MAX_D FROM {derived}"
            r = row_dict(self.session.sql(sql).collect()[0])
            self.queries_run += 1
            lo, hi = _key(r.get("min_d")), _key(r.get("max_d"))
            ok = lo == cal.min_date.isoformat() and hi == cal.max_date.isoformat()
            rows.append({"label": "Data coverage (first – last date)", "column": "dates",
                         "dashboard": f"{cal.min_date.isoformat()} – {cal.max_date.isoformat()}",
                         "independent": f"{lo} – {hi}", "ok": ok})
            if not ok:
                status = "mismatch"
            sqls = {"dashboard": "Calendar from the semantic view", "independent": sql}
        except Unchecked as exc:
            notes.append("Coverage not re-derived: " + str(exc))
        except Exception as exc:
            notes.append("Coverage query failed: " + str(exc)[:160])
        summ = (f"Current {cal.label(cal.current_start)} (complete) vs prior {cal.label(cal.prior_start)} and year-ago "
                f"{cal.label(cal.yoy_start)}" if status == "pass" else "Period boundaries need attention")
        return check("QA-05", status, summ, "\n".join(notes), rows, sqls)

    def freshness(self) -> dict:
        cal = self.e.cal
        lag = (dt.date.today() - cal.max_date).days
        limit = STALE_DAYS.get(cal.grain, 40)
        st = "pass" if lag <= limit else "review"
        return check("QA-06", st, f"Data through {cal.max_date.isoformat()} ({lag} day(s) ago)",
                     f"Expected within {limit} days for a {cal.grain}ly dashboard." if st == "review" else "")

    # -- orchestration ---------------------------------------------------------------------------------------------------
    def _tile(self, page: dict, comp: dict, cid: str, res: dict, caps: list[dict]) -> dict:
        data = res.get("data") or {}
        checks = [self.qa01(caps)]
        for fn in (lambda: self.qa02(comp, data), lambda: self.qa03(comp, data), lambda: self.qa06(comp, data),
                   lambda: self.qa07(cid, res)):
            try:
                c = fn()
            except Exception as exc:
                c = check("QA-02", "na", "Check failed to run: " + str(exc)[:160])
            if c:
                checks.append(c)
        return {"status": worst(c["status"] for c in checks), "checks": checks,
                "sig": signature(res, self.e.filters), "title": comp.get("title") or comp["type"],
                "page_id": page["page_id"]}

    def run(self, spec: dict, page_ids: list[str], results: dict, tile_q: dict, cache: dict,
            only: Optional[set] = None, progress: Optional[Callable[[str, Any], None]] = None) -> dict:
        """Validate the given pages. `only` limits tile checks to those component ids (incremental re-runs).
        `progress(event, data)` is called with ("query", (done, total)) after each independent query and with
        ("tile", (cid, result)) as soon as all of a tile's queries are back, so results can be shown tile by tile."""
        tiles = []
        for page in spec["pages"]:
            if page["page_id"] not in page_ids:
                continue
            for comp in page["components"]:
                cid = f"{page['page_id']}/{comp['component_id']}"
                res = results.get(cid) or {}
                if res.get("status") != "ready" or comp.get("state") == "omitted" or comp["type"] in NON_DATA:
                    continue
                if only is not None and cid not in only:
                    continue
                caps = []
                for k in tile_q.get(cid) or []:
                    caps += cache.get("__q__" + k) or []
                tiles.append((page, comp, cid, res, caps))
                for cap in caps:
                    self._independent(cap)
        out_tiles: dict[str, dict] = {}

        def ready(caps):
            return all("rows" in self.q_results[c["sql"]] or "status" in self.q_results[c["sql"]] for c in caps)

        def emit():
            if progress:
                progress("query", (self.queries_run, self.total_queries))
            for page, comp, cid, res, caps in tiles:
                if cid not in out_tiles and not self.cancelled and ready(caps):
                    out_tiles[cid] = self._tile(page, comp, cid, res, caps)
                    if progress:
                        progress("tile", (cid, out_tiles[cid]))
        self._run_independent(emit)
        for page, comp, cid, res, caps in tiles:            # anything not emitted yet (e.g. no queries at all)
            if cid not in out_tiles and not self.cancelled:
                out_tiles[cid] = self._tile(page, comp, cid, res, caps)
                if progress:
                    progress("tile", (cid, out_tiles[cid]))
        dash = [] if self.cancelled else [self.qa04(), self.qa05(), self.freshness()]
        lineage = {"view": self.p.fqn if self.p else "", "tables": sorted(t.replace('"', "") for t in self.tables_used),
                   "joins": self.join_info, "nonadd_from_ddl": sorted(".".join(k) for k in (self.p.nonadd_from_ddl if self.p else ()))}
        return {"tiles": out_tiles, "dashboard": dash, "queries": self.queries_run, "lineage": lineage,
                "at": dt.datetime.now().strftime("%Y-%m-%d %H:%M"), "run_id": uuid.uuid4().hex[:12]}


def eff(t: dict) -> str:
    """Status after resolutions: an accepted / owned finding shows as 'accepted' (never as verified)."""
    return t.get("status_eff") or t.get("status") or "na"


LABEL["accepted"] = "Accepted"
RANK["accepted"] = 1.5


def page_summary(report: dict, page_id: str) -> dict:
    """Counts and overall status for one page from the merged report."""
    tiles = [t for cid, t in (report.get("tiles") or {}).items() if t.get("page_id") == page_id]
    counts = {"pass": 0, "accepted": 0, "review": 0, "mismatch": 0, "na": 0}
    for t in tiles:
        counts[eff(t)] = counts.get(eff(t), 0) + 1
    page_checks = list(report.get("dashboard") or []) + list((report.get("pages") or {}).get(page_id, {}).get("checks") or [])
    status = worst([eff(t) for t in tiles] + [c.get("status_eff") or c["status"] for c in page_checks])
    notes = [(RANK[c["status"]], f"{c['name']}: {c['summary']}") for c in page_checks
             if (c.get("status_eff") or c["status"]) in ("mismatch", "review")]
    notes += [(RANK[eff(t)], f"{t.get('title')}: {next((c['summary'] for c in t['checks'] if c['status'] == t['status']), '')}")
              for t in tiles if eff(t) in ("mismatch", "review")]
    notes = [n for _, n in sorted(notes, key=lambda x: -x[0])]
    return {"status": status, "label": LABEL[status], "counts": counts, "tiles": len(tiles), "notes": notes[:6]}


def narrative_check(narrative_text: str, facts: list[str]) -> dict:
    matched, unmatched = grounded(narrative_text, facts)
    if not matched and not unmatched:
        return check("QA-08", "pass", "The summary quotes no figures that need grounding.")
    rows = [{"label": u, "column": "number in summary", "dashboard": u, "independent": "not in the computed facts",
             "ok": False} for u in unmatched] + \
           [{"label": m, "column": "number in summary", "dashboard": m, "independent": "matches a fact", "ok": True}
            for m in matched[:6]]
    if unmatched:
        return check("QA-08", "review", f"{len(unmatched)} of {len(matched) + len(unmatched)} figure(s) in the summary "
                                        "do not match a computed fact", "Regenerate the summary or check the wording.",
                     rows)
    return check("QA-08", "pass", f"All {len(matched)} figure(s) in the summary match computed facts", rows=rows)
