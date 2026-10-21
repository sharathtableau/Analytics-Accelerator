"""Custom metrics: a builder defines a metric the semantic view does not have, from the metrics it does have.

A custom metric is a formula over the view's existing (governed or drafted) metrics, e.g.
    RETURN_RATE = ORDERS.RETURNED_UNITS / ORDERS.UNITS_SOLD
    NET_SALES   = ORDERS.SALES - ORDERS.DISCOUNT_AMOUNT
The text a person types (plain English or a formula) is turned into a formula by Cortex AI_COMPLETE, or used
directly when it already is one. Nothing Cortex or the person writes reaches SQL as text: the formula is parsed
by a strict grammar (metric ids of this view, numbers, + - * / and brackets) and SQL is generated from the parse
tree, with every division as DIV0. Saved formulas are re-validated against the view each time it is loaded.
Queries: the base metrics come from SEMANTIC_VIEW(...) and the formula is computed on top (semantic_query.sv).
"""
from __future__ import annotations

import json
import re
from typing import Any, Callable, Optional

from semantic_catalog import Field, NAME_OK, SemanticModel, quote_ident

THEMES = ("Sales", "Profitability", "Customers", "Fulfilment", "Returns", "Inventory", "Plan")
MAX_LEN = 400
MAX_NODES = 40
TOKEN = re.compile(r"\s*(?:(?P<num>\d+(?:\.\d+)?)|(?P<id>[A-Za-z_][A-Za-z0-9_$]*(?:\.[A-Za-z_][A-Za-z0-9_$]*)?)"
                   r"|(?P<op>[-+*/()]))")


class FormulaError(ValueError):
    pass


# ----------------------------------------------------------------------------------------- parse
def _tokens(text: str) -> list[tuple[str, str]]:
    text = (text or "").replace("×", "*").replace("÷", "/").replace("−", "-").strip()
    if not text:
        raise FormulaError("The formula is empty.")
    if len(text) > MAX_LEN:
        raise FormulaError("The formula is too long.")
    out, pos = [], 0
    while pos < len(text):
        m = TOKEN.match(text, pos)
        if not m or m.end() == pos:
            bad = text[pos:].strip()[:20]
            raise FormulaError(f"Only metrics, numbers, + - * / and brackets are allowed (stopped at '{bad}').")
        kind = m.lastgroup
        out.append((kind, m.group(kind)))
        pos = m.end()
        while pos < len(text) and text[pos].isspace():
            pos += 1
    return out


def _resolver(model: SemanticModel) -> Callable[[str], Field]:
    by_id = {m.id.upper(): m for m in model.metrics if not is_custom(model, m)}
    by_name: dict[str, list[Field]] = {}
    for m in by_id.values():
        by_name.setdefault(m.name.upper(), []).append(m)

    def find(token: str) -> Field:
        t = token.upper()
        if t in by_id:
            return by_id[t]
        hits = by_name.get(t.split(".")[-1], [])
        if len(hits) == 1:
            return hits[0]
        if len(hits) > 1:
            raise FormulaError(f"'{token}' is ambiguous: use one of {', '.join(h.id for h in hits)}.")
        raise FormulaError(f"'{token}' is not a metric of this semantic view.")
    return find


def parse(text: str, model: SemanticModel) -> Any:
    """Formula text -> tree: ("num", 2.0) | ("m", metric_id) | ("neg", x) | (op, left, right)."""
    toks, find = _tokens(text), _resolver(model)
    pos, nodes = 0, 0

    def peek():
        return toks[pos] if pos < len(toks) else (None, None)

    def take():
        nonlocal pos
        t = peek()
        pos += 1
        return t

    def node(n):
        nonlocal nodes
        nodes += 1
        if nodes > MAX_NODES:
            raise FormulaError("The formula is too complex.")
        return n

    def expr():
        left = term()
        while peek()[1] in ("+", "-"):
            op = take()[1]
            left = node((op, left, term()))
        return left

    def term():
        left = factor()
        while peek()[1] in ("*", "/"):
            op = take()[1]
            left = node((op, left, factor()))
        return left

    def factor():
        kind, val = take()
        if kind == "num":
            return node(("num", float(val)))
        if kind == "id":
            return node(("m", find(val).id))
        if val == "-":
            return node(("neg", factor()))
        if val == "(":
            inner = expr()
            if take()[1] != ")":
                raise FormulaError("A bracket is not closed.")
            return inner
        raise FormulaError("The formula is incomplete." if kind is None else f"Unexpected '{val}'.")

    tree = expr()
    if pos != len(toks):
        raise FormulaError(f"Unexpected '{toks[pos][1]}'.")
    if not bases(tree):
        raise FormulaError("The formula must use at least one metric.")
    return tree


def bases(tree: Any) -> list[str]:
    if tree[0] == "m":
        return [tree[1]]
    if tree[0] == "num":
        return []
    return list(dict.fromkeys(x for child in tree[1:] for x in bases(child)))


def render(tree: Any, ref: Callable[[str], str]) -> str:
    """SQL from the tree. Division is DIV0 (0 instead of an error when the denominator is 0)."""
    k = tree[0]
    if k == "num":
        v = tree[1]
        return str(int(v)) if v == int(v) else repr(v)
    if k == "m":
        return ref(tree[1])
    if k == "neg":
        return f"(-{render(tree[1], ref)})"
    a, b = render(tree[1], ref), render(tree[2], ref)
    return f"DIV0({a}, {b})" if k == "/" else f"({a} {k} {b})"


def show(tree: Any, label: Callable[[str], str], top: bool = True) -> str:
    """Readable formula: Returned Units ÷ Units Sold."""
    k = tree[0]
    if k == "num":
        v = tree[1]
        return str(int(v)) if v == int(v) else str(v)
    if k == "m":
        return label(tree[1])
    if k == "neg":
        return "−" + show(tree[1], label, False)
    sym = {"+": "+", "-": "−", "*": "×", "/": "÷"}[k]
    s = f"{show(tree[1], label, False)} {sym} {show(tree[2], label, False)}"
    return s if top else f"({s})"


def _canon(tree: Any) -> str:
    k = tree[0]
    if k == "num":
        v = tree[1]
        return str(int(v)) if v == int(v) else repr(v)
    if k == "m":
        return tree[1]
    if k == "neg":
        return f"-({_canon(tree[1])})"
    return f"({_canon(tree[1])} {k} {_canon(tree[2])})"


def additive(tree: Any, model: SemanticModel) -> bool:
    """Sums and differences of additive metrics add up across segments; anything else does not."""
    k = tree[0]
    if k == "m":
        try:
            return model.field(tree[1], ("metric",)).additive
        except ValueError:
            return False
    if k == "neg":
        return additive(tree[1], model)
    if k in ("+", "-"):
        return additive(tree[1], model) and additive(tree[2], model)
    return False


# ----------------------------------------------------------------------------------------- model
def is_custom(model: SemanticModel, f: Field) -> bool:
    spec = model.virtual.get(f.ref)
    return bool(spec) and spec[0] == "FORMULA"


def apply(model: SemanticModel, rows: list[dict[str, Any]]) -> SemanticModel:
    """Add the saved custom metrics to the model (idempotent). A saved formula that no longer fits the view
    (a base metric was removed) is skipped and listed in model.custom_errors."""
    model.metrics = [m for m in model.metrics if not is_custom(model, m)]
    model.virtual = {k: v for k, v in model.virtual.items() if v[0] != "FORMULA"}
    model.metric_info = {k: v for k, v in (model.metric_info or {}).items() if v.get("origin") != "custom"}
    model.custom_errors = []
    taken = {f.name.upper() for f in model.metrics + model.dimensions + model.facts}
    for r in rows or []:
        name = str(r.get("name") or "").upper()
        try:
            if not NAME_OK.match(name) or name in taken:
                raise FormulaError("name clashes with a field of the view")
            tree = parse(str(r.get("formula") or ""), model)
        except FormulaError as exc:
            model.custom_errors.append({"name": name, "error": str(exc)})
            continue
        label = str(r.get("label") or name.replace("_", " ").title())[:80]
        shown = show(tree, lambda i: model.field(i, ("metric",)).label)
        fld = Field(entity="", name=name, kind="metric", data_type="FLOAT", expression=shown,
                    comment=(f"Custom metric (not governed) = {shown}. "
                             + str(r.get("description") or "")).strip()[:300])
        fld.fixed_additive = additive(tree, model)
        fld.custom_label = label
        model.metrics.append(fld)
        model.virtual[fld.ref] = ("FORMULA", tree, {b: model.field(b, ("metric",)).ref for b in bases(tree)})
        model.metric_info[fld.id] = {"origin": "custom", "theme": str(r.get("theme") or "")[:30],
                                     "why": f"Custom metric by {r.get('created_by') or 'a builder'} (not governed)",
                                     "formula": _canon(tree), "label": label}
        taken.add(name)
    return model


def dims_for(model: SemanticModel, metric_dims: dict[str, set[str]]) -> dict[str, set[str]]:
    """A custom metric can be split by the dimensions all its base metrics can be split by."""
    out = dict(metric_dims or {})
    if not out:
        return out
    for m in model.metrics:
        spec = model.virtual.get(m.ref)
        if spec and spec[0] == "FORMULA":
            sets = [out.get(b.upper()) for b in bases(spec[1])]
            if all(s is not None for s in sets):
                out[m.id.upper()] = set.intersection(*sets) if sets else set()
    return out


def governed_snippet(model: SemanticModel, f: Field) -> str:
    """What the view owner can add to the METRICS clause to make it governed (a derived metric)."""
    spec = model.virtual.get(f.ref)
    if not spec or spec[0] != "FORMULA":
        return ""
    expr = render(spec[1], lambda i: model.field(i, ("metric",)).ref)
    return (f"-- add to the METRICS clause of {model.fqn} (derived metric; check the syntax for your account)\n"
            f"{f.name} AS {expr}\n  COMMENT = '{(f.comment or '').replace(chr(39), chr(39) * 2)[:200]}'")


# ----------------------------------------------------------------------------------------- Cortex
def prompt(model: SemanticModel, text: str, name_hint: str = "") -> str:
    mets = [{"id": m.id, "label": m.label, "definition": (m.comment or "")[:160],
             "kind": "adds up" if m.additive else "ratio/average/distinct"}
            for m in model.metrics if not is_custom(model, m)][:120]
    return (
        "You turn a business user's description of a metric into a formula over EXISTING metrics of a Snowflake "
        "semantic view. Use only the metric ids listed below, numbers, + - * / and brackets. No functions, no "
        "columns, no filters. Ratios and rates stay as fractions (do not multiply by 100). If the request needs a "
        "filter (e.g. only one region), a column or a metric that is not listed, do not guess: return an error "
        "that says what is missing.\n\n"
        f"Metrics:\n{json.dumps(mets, separators=(',', ':'))}\n\n"
        f"User request: {text[:600]}\n"
        + (f"Preferred name: {name_hint[:60]}\n" if name_hint else "")
        + "\nReply with JSON only, either\n"
        '{"name": "UPPER_SNAKE_CASE (end ratios with _RATE or _PCT, amounts with _AMOUNT or a clear noun)", '
        '"label": "Title Case", "formula": "ENTITY.METRIC / ENTITY.METRIC", '
        '"description": "one sentence a business user understands", '
        f'"theme": "one of {list(THEMES)}"}}\n'
        'or {"error": "what is missing, in one sentence"}'
    )


def clean_name(raw: str) -> str:
    n = re.sub(r"[^A-Z0-9_]+", "_", str(raw or "").upper()).strip("_")
    if n and not n[0].isalpha():
        n = "M_" + n
    return n[:60]


def _looks_like_formula(text: str) -> bool:
    """Only formula tokens, with an operator or a TABLE.METRIC id: the person typed a formula, not a sentence."""
    try:
        toks = _tokens(text)
    except FormulaError:
        return False
    return any(k == "op" for k, _ in toks) or any(k == "id" and "." in v for k, v in toks)


def define(cortex, model: SemanticModel, text: str, name_hint: str = "") -> dict[str, Any]:
    """Text (English or formula) -> a checked candidate {name, label, formula, description, theme, tree, origin,
    provenance}. Raises FormulaError with a message for the person."""
    text = (text or "").strip()
    if not text:
        raise FormulaError("Describe the metric, e.g. 'return rate = returned units divided by units sold'.")
    left, sep, right = text.partition("=")
    direct, formula_error = None, None
    for cand in ([right] if sep else []) + [text]:
        try:
            direct = parse(cand, model)
            break
        except FormulaError as exc:
            if _looks_like_formula(cand) and formula_error is None:
                formula_error = exc                     # typed as a formula: report its error, don't guess
    if direct is None and formula_error is not None:
        raise formula_error
    if direct is not None:
        name = clean_name(name_hint or (left if sep else "")) or "CUSTOM_" + "_".join(
            model.field(b, ("metric",)).name for b in bases(direct))[:50]
        label = (left.strip() if sep and left.strip() else name.replace("_", " ").title())[:80]
        out = {"name": name, "label": label, "formula": _canon(direct),
               "description": text[:300], "theme": "", "tree": direct, "origin": "formula",
               "provenance": "Typed formula (no AI call)"}
    else:
        from ai_services import _json_from_text
        raw, prov = cortex.complete(prompt(model, text, name_hint))
        data = _json_from_text(raw) or {}
        if not isinstance(data, dict):
            raise FormulaError("Cortex did not return a metric. Try a formula, e.g. ORDERS.PROFIT / ORDERS.SALES.")
        if data.get("error"):
            raise FormulaError(f"Cortex could not build it: {str(data['error'])[:240]}")
        tree = parse(str(data.get("formula") or ""), model)
        name = clean_name(name_hint or data.get("name"))
        theme = data.get("theme") if data.get("theme") in THEMES else ""
        out = {"name": name, "label": str(data.get("label") or name.replace("_", " ").title())[:80],
               "formula": _canon(tree), "description": str(data.get("description") or text)[:300],
               "theme": theme, "tree": tree, "origin": "cortex", "provenance": f"Cortex AI_COMPLETE ({prov})"}
    if not NAME_OK.match(out["name"]):
        raise FormulaError("Give the metric a name of letters, digits and underscores, starting with a letter.")
    taken = {f.name.upper() for f in model.metrics + model.dimensions + model.facts}
    if out["name"] in taken:
        raise FormulaError(f"{out['name']} already exists in this view. Pick another name.")
    return out
