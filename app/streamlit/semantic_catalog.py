"""Read Snowflake semantic views: discovery, metadata and safe identifiers.

Everything the app queries is addressed through a semantic view that the
current role can see. Names coming from the browser are only ever matched
against names returned here; they are never concatenated into SQL unchecked.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from typing import Any, Iterable, Optional

IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*$")
FQN = re.compile(r"^[A-Za-z_][A-Za-z0-9_$]*\.[A-Za-z_][A-Za-z0-9_$]*\.[A-Za-z_][A-Za-z0-9_$]*$")
TIME_TYPES = ("DATE", "TIMESTAMP", "DATETIME")
TIME_NAME = re.compile(r"(DATE|_DT$|^DT_|TIME|_DAY$|^DAY$|PERIOD|MONTH|WEEK)", re.I)


def quote_ident(name: str) -> str:
    """Return a SQL identifier; quote anything that is not a plain identifier."""
    if IDENT.match(name) and name.upper() == name:
        return name
    return '"' + name.replace('"', '""') + '"'


def quote_fqn(fqn: str) -> str:
    return ".".join(quote_ident(part) for part in split_fqn(fqn))


def split_fqn(fqn: str) -> list[str]:
    parts = [p.strip().strip('"') for p in fqn.split(".")]
    if len(parts) != 3 or not all(parts):
        raise ValueError(f"Not a three-part name: {fqn}")
    return parts


def row_dict(row: Any) -> dict[str, Any]:
    """Snowpark Row / dict -> dict with lower-case keys."""
    if isinstance(row, dict):
        data = row
    elif hasattr(row, "as_dict"):
        data = row.as_dict()
    elif hasattr(row, "asDict"):
        data = row.asDict()
    else:
        data = dict(row)
    return {str(k).strip('"').lower(): v for k, v in data.items()}


@dataclass
class Field:
    entity: str
    name: str
    kind: str                     # dimension | metric | fact
    data_type: str = ""
    expression: str = ""
    synonyms: list[str] = field(default_factory=list)
    comment: str = ""

    @property
    def id(self) -> str:
        # derived metrics (defined across tables) have no logical table
        return f"{self.entity}.{self.name}" if self.entity else self.name

    @property
    def ref(self) -> str:
        return f"{quote_ident(self.entity)}.{quote_ident(self.name)}" if self.entity else quote_ident(self.name)

    @property
    def is_time(self) -> bool:
        if self.kind != "dimension":
            return False
        dtype = self.data_type.upper()
        if dtype:
            return dtype.startswith(TIME_TYPES)
        return bool(TIME_NAME.search(self.name))

    @property
    def additive(self) -> bool:
        """SUM/COUNT metrics reconcile across segments; ratios and distinct counts do not."""
        fixed = getattr(self, "fixed_additive", None)        # custom metrics: decided from their formula
        if fixed is not None:
            return fixed
        expr = re.sub(r"\s+", " ", self.expression.upper()).strip()
        if not expr:
            return False
        if "DISTINCT" in expr or "/" in expr or "AVG(" in expr:
            return False
        return bool(re.match(r"^(SUM|COUNT)\s*\(", expr))

    @property
    def label(self) -> str:
        return getattr(self, "custom_label", None) or self.name.replace("_", " ").title()


@dataclass
class SemanticModel:
    fqn: str
    comment: str
    tables: list[str]
    dimensions: list[Field]
    metrics: list[Field]
    facts: list[Field]
    scope: str = ""                   # logical table this model is limited to ("" = whole view)
    facts_mode: bool = False          # no metrics defined: ad-hoc metrics over facts (standard SQL)
    virtual: dict = field(default_factory=dict)   # metric ref -> ("SUM", fact_ref) | ("RATIO", num_ref, den_ref)
    metric_info: dict = field(default_factory=dict)   # metric id -> {"origin", "why", "theme"} for drafted metrics

    @property
    def source_id(self) -> str:
        """What the app stores and caches by: the view, or VIEW#TABLE for one table of a facts-only view."""
        return f"{self.fqn}#{self.scope}" if self.scope else self.fqn

    def field(self, field_id: str, kinds: Iterable[str] = ("dimension", "metric", "fact")) -> Field:
        wanted = set(kinds)
        for item in self.dimensions + self.metrics + self.facts:
            if item.id.upper() == str(field_id).upper() and item.kind in wanted:
                return item
        raise ValueError(f"{field_id} is not a {'/'.join(sorted(wanted))} of {self.fqn}")

    @property
    def time_dimensions(self) -> list[Field]:
        return [d for d in self.dimensions if d.is_time]

    @property
    def categorical_dimensions(self) -> list[Field]:
        return [d for d in self.dimensions if not d.is_time]

    def summary(self) -> dict[str, Any]:
        def pack(items):
            return [{**asdict(i), "id": i.id, "label": i.label, "is_time": i.is_time,
                     "additive": i.additive} for i in items]
        return {"fqn": self.fqn, "comment": self.comment, "tables": self.tables,
                "dimensions": pack(self.dimensions), "metrics": pack(self.metrics),
                "facts": pack(self.facts)}


def list_semantic_views(session, schemas: Iterable[str], schema_errors: Optional[dict] = None) -> list[dict[str, Any]]:
    """Semantic views visible to the current role in the allowlisted schemas.
    schema_errors (optional) collects {schema: error} for schemas the role couldn't list."""
    found: list[dict[str, Any]] = []
    errors: list[str] = []
    for schema in schemas:
        db, sch = schema.split(".")
        try:
            rows = session.sql(f"SHOW SEMANTIC VIEWS IN SCHEMA {quote_ident(db)}.{quote_ident(sch)}").collect()
        except Exception as exc:  # role may lack USAGE on a schema
            errors.append(f"{schema}: {exc}")
            if schema_errors is not None:
                schema_errors[schema.upper()] = str(exc)[:200]
            continue
        for row in rows:
            d = row_dict(row)
            name = str(d.get("name", ""))
            if not name:
                continue
            found.append({
                "fqn": f"{d.get('database_name', db)}.{d.get('schema_name', sch)}.{name}".upper(),
                "name": name,
                "schema": f"{d.get('database_name', db)}.{d.get('schema_name', sch)}".upper(),
                "comment": d.get("comment") or "",
                "created_on": str(d.get("created_on") or ""),
            })
    found.sort(key=lambda item: item["fqn"])
    return found if not errors or found else [{"error": "; ".join(errors)}]


def split_scope(source_id: str) -> tuple[str, str]:
    """'DB.SCH.VIEW#TABLE' -> ('DB.SCH.VIEW', 'TABLE'); plain FQN -> (FQN, '')."""
    base, _, scope = str(source_id).partition("#")
    return base.strip(), scope.strip()


NUMERIC = re.compile(r"NUMBER|DECIMAL|NUMERIC|INT|FLOAT|DOUBLE|REAL", re.I)
ID_LIKE = re.compile(r"(_ID|_KEY|_CODE|_NO|_NUMBER)$|^ID$", re.I)
AVG_LIKE = re.compile(r"RATE|PCT|PERCENT|RATIO|AVG|AVERAGE|SCORE|AGE$|_AGE_|PRICE|DAYS|HOURS|LENGTH_OF_STAY|LOS$", re.I)


def adhoc_aggregate(f: Field) -> Optional[str]:
    """How the app aggregates a fact when the view defines no metrics (None = not a measure)."""
    if ID_LIKE.search(f.name):
        return "COUNT_DISTINCT"
    if f.data_type and not NUMERIC.search(f.data_type):
        return None
    return "AVG" if AVG_LIKE.search(f.name) else "SUM"


def with_adhoc_metrics(model: "SemanticModel") -> "SemanticModel":
    """A view with facts but no metrics: expose each fact as an ad-hoc metric (SUM / AVG / COUNT DISTINCT).
    Queries then use the semantic view's standard-SQL interface, e.g. SELECT region, SUM(sales) FROM sv."""
    if model.metrics or not model.facts:
        return model
    made = []
    for f in model.facts:
        agg = adhoc_aggregate(f)
        if not agg:
            continue
        name = (f"{f.name}_COUNT" if agg == "COUNT_DISTINCT" else f"AVG_{f.name}" if agg == "AVG" else f.name)
        expr = (f"COUNT(DISTINCT {f.entity}.{f.name})" if agg == "COUNT_DISTINCT" else f"{agg}({f.entity}.{f.name})")
        m = Field(entity=f.entity, name=name, kind="metric", data_type=f.data_type, expression=expr,
                  synonyms=list(f.synonyms),
                  comment=(f.comment + " " if f.comment else "") + f"(ad-hoc {agg.replace('_', ' ')} of fact {f.name}; "
                          "the semantic view defines no metrics)")
        made.append(m)
        model.virtual[m.ref] = (agg, f.ref)
    model.metrics = made
    model.facts_mode = bool(made)
    return model


AGGS = ("SUM", "AVG", "MIN", "MAX", "COUNT", "COUNT_DISTINCT")
NAME_OK = re.compile(r"^[A-Z][A-Z0-9_]{1,62}$")


def apply_metric_draft(model: "SemanticModel", draft: dict) -> "SemanticModel":
    """Replace rule-based ad-hoc metrics with a reviewed draft (Cortex or rules), per logical table.
    draft = {"tables": {TABLE: {"metrics": [{name, agg, fact, comment, why, synonyms, theme}],
                                "ratios": [{name, numerator, denominator, comment, why, theme}]}}, "origin": ...}"""
    if not model.facts_mode or not draft or not draft.get("tables"):
        return model
    facts = {(f.entity.upper(), f.name.upper()): f for f in model.facts}
    made, virtual, info = [], {}, {}
    for table, spec in draft["tables"].items():
        table = table.upper()
        if model.scope and table != model.scope:
            continue
        by_name: dict[str, Field] = {}
        for m in spec.get("metrics") or []:
            f = facts.get((table, str(m.get("fact", "")).upper()))
            name, agg = str(m.get("name", "")).upper(), str(m.get("agg", "")).upper()
            if not f or not NAME_OK.match(name) or agg not in AGGS or name in by_name:
                continue
            expr = f"COUNT(DISTINCT {f.entity}.{f.name})" if agg == "COUNT_DISTINCT" else f"{agg}({f.entity}.{f.name})"
            fld = Field(entity=f.entity, name=name, kind="metric", data_type=f.data_type, expression=expr,
                        synonyms=[str(x) for x in (m.get("synonyms") or [])][:6], comment=str(m.get("comment") or "")[:300])
            by_name[name] = fld
            virtual[fld.ref] = (agg, f.ref)
            info[fld.id] = {"origin": draft.get("origin", "rules"), "why": str(m.get("why") or "")[:240],
                            "theme": str(m.get("theme") or "")[:30]}
        for r in spec.get("ratios") or []:
            name = str(r.get("name", "")).upper()
            num, den = by_name.get(str(r.get("numerator", "")).upper()), by_name.get(str(r.get("denominator", "")).upper())
            if not NAME_OK.match(name) or name in by_name or not num or not den or num is den:
                continue
            fld = Field(entity=num.entity, name=name, kind="metric", data_type="FLOAT",
                        expression=f"DIV0({num.name}, {den.name})", comment=str(r.get("comment") or "")[:300])
            by_name[name] = fld
            virtual[fld.ref] = ("RATIO", num.ref, den.ref)
            info[fld.id] = {"origin": draft.get("origin", "rules"), "why": str(r.get("why") or "")[:240],
                            "theme": str(r.get("theme") or "")[:30]}
        made += list(by_name.values())
    if made:
        model.metrics, model.virtual, model.metric_info = made, virtual, info
    return model


def metrics_ddl(model: "SemanticModel") -> str:
    """The METRICS clause the view owner can add to make the drafted metrics governed."""
    lines = []
    for m in model.metrics:
        spec = model.virtual.get(m.ref)
        if not spec:
            continue
        if spec[0] == "RATIO":
            num = next(x for x in model.metrics if x.ref == spec[1])
            den = next(x for x in model.metrics if x.ref == spec[2])
            expr = f"DIV0({num.entity}.{num.name}, {den.entity}.{den.name})"
        else:
            expr = m.expression
        cmt = (m.comment or "").replace("'", "''")
        lines.append(f"    {m.entity}.{m.name} AS {expr}" + (f"\n      COMMENT = '{cmt}'" if cmt else ""))
    return "METRICS (\n" + ",\n".join(lines) + "\n  )"


def scope_model(model: "SemanticModel", table: str) -> "SemanticModel":
    keep = lambda items: [x for x in items if (x.entity or "").upper() == table.upper()]
    sm = SemanticModel(fqn=model.fqn, comment=model.comment, tables=[t for t in model.tables if t.upper() == table.upper()],
                       dimensions=keep(model.dimensions), metrics=keep(model.metrics), facts=keep(model.facts),
                       scope=table.upper())
    if model.facts_mode:
        sm.facts_mode = True
        sm.virtual = {k: v for k, v in model.virtual.items() if any(x.ref == k for x in sm.metrics)}
        sm.metric_info = {k: v for k, v in model.metric_info.items() if any(x.id == k for x in sm.metrics)}
    if hasattr(model, "draft_meta"):
        sm.draft_meta = model.draft_meta
    return sm


def fact_tables(model: "SemanticModel") -> list[str]:
    """Tables to list separately on Home: only for facts-only views that span several unrelated tables."""
    if model.metrics:
        return []
    tabs = sorted({f.entity for f in model.facts if f.entity})
    return tabs if len(tabs) > 1 else []


def describe_semantic_view(session, fqn: str) -> SemanticModel:
    """Parse DESCRIBE SEMANTIC VIEW (object_kind/object_name/parent_entity/property/property_value).
    Accepts 'DB.SCH.VIEW#TABLE' to limit the model to one logical table."""
    fqn, scope = split_scope(fqn)
    if not FQN.match(fqn):
        raise ValueError("Semantic view must be a three-part name")
    rows = [row_dict(r) for r in session.sql(f"DESCRIBE SEMANTIC VIEW {quote_fqn(fqn)}").collect()]
    fields: dict[tuple[str, str, str], Field] = {}
    tables: list[str] = []
    comment = ""
    for r in rows:
        kind = str(r.get("object_kind") or "").upper()
        name = str(r.get("object_name") or "")
        parent = str(r.get("parent_entity") or "")
        prop = str(r.get("property") or "").upper()
        value = r.get("property_value")
        value = "" if value is None else str(value)
        if kind == "TABLE":
            if name and name not in tables:
                tables.append(name)
            continue
        if kind in ("", "SEMANTIC_VIEW", "SEMANTIC VIEW"):
            if prop == "COMMENT":
                comment = value
            continue
        mapped = {"DIMENSION": "dimension", "TIME_DIMENSION": "dimension", "TIME DIMENSION": "dimension",
                  "METRIC": "metric", "FACT": "fact",
                  "DERIVED_METRIC": "metric", "DERIVED METRIC": "metric"}.get(kind)
        if not mapped or not name:
            continue
        if mapped == "metric" and name.upper().startswith("HELPER_"):
            continue            # building blocks for other metrics, not shown to users
        entity = parent or ("" if mapped == "metric" else (tables[0] if tables else ""))
        key = (mapped, entity.upper(), name.upper())
        item = fields.setdefault(key, Field(entity=entity, name=name, kind=mapped))
        if prop == "DATA_TYPE":
            item.data_type = value
        elif prop == "EXPRESSION":
            item.expression = value
        elif prop == "COMMENT":
            item.comment = value
        elif prop == "SYNONYMS":
            item.synonyms = [s.strip(" '\"") for s in value.strip("[]()").split(",") if s.strip(" '\"")]
        elif prop == "TABLE" and not item.entity:
            item.entity = value
    ordered = sorted(fields.values(), key=lambda f: (f.kind, f.entity, f.name))
    model = SemanticModel(
        fqn=fqn.upper(), comment=comment, tables=tables,
        dimensions=[f for f in ordered if f.kind == "dimension"],
        metrics=[f for f in ordered if f.kind == "metric"],
        facts=[f for f in ordered if f.kind == "fact"],
    )
    if scope:
        model = scope_model(model, scope)
    return with_adhoc_metrics(model)


def metric_dimension_map(session, model: "SemanticModel") -> dict[str, set[str]]:
    """Which dimensions each metric can be broken down by (SHOW SEMANTIC DIMENSIONS ... FOR METRIC).

    In a semantic view over several tables, a dimension must be related to the metric's table.
    Returns {} when the account does not support the command (then every pair is allowed).
    """
    from concurrent.futures import ThreadPoolExecutor
    if model.facts_mode:     # ad-hoc metrics: a fact can be split by the dimensions of its own table
        dims = {}
        for m in model.metrics:
            dims[m.id.upper()] = {d.id.upper() for d in model.dimensions if d.entity.upper() == m.entity.upper()}
        return dims

    def one(m: Field):
        rows = session.sql(f"SHOW SEMANTIC DIMENSIONS IN {quote_fqn(model.fqn)} FOR METRIC {quote_ident(m.name)}").collect()
        dims = set()
        for r in rows:
            d = row_dict(r)
            table, name = str(d.get("table_name") or ""), str(d.get("name") or "")
            if name:
                dims.add(f"{table}.{name}".upper() if table else name.upper())
        return m.id.upper(), dims
    try:
        first = one(model.metrics[0]) if model.metrics else None
    except Exception:
        return {}
    out = dict([first]) if first else {}
    try:
        with ThreadPoolExecutor(max_workers=8) as pool:
            for mid, dims in pool.map(one, model.metrics[1:]):
                out[mid] = dims
    except Exception:
        return {}
    return out
