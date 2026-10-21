"""In-memory stand-in for a Snowpark session, for local tests only.

It understands exactly the SQL shapes the app emits (SEMANTIC_VIEW queries,
SHOW/DESCRIBE, AI_COMPLETE, ML FORECAST, DATA_AGENT_RUN, app tables) over a
synthetic Superstore-like dataset. It is NOT used in Snowflake.
"""
from __future__ import annotations

import os
import time
import datetime as dt
import json
import random
import re
from collections import defaultdict

SV = "WBR_DB.PUBLIC.SUPERSTORE_DEMO_SV"
ENTITY = "ORDERS"


def _gen_rows():
    rnd = random.Random(7)
    regions = ["West", "East", "Central", "South"]
    segments = ["Consumer", "Corporate", "Home Office"]
    cats = ["Technology", "Furniture", "Office Supplies"]
    rows = []
    day = dt.date(2021, 1, 4)
    oid = 0
    while day <= dt.date(2024, 12, 29):
        growth = 1 + (day - dt.date(2021, 1, 1)).days / 1461 * 0.45
        season = 1.35 if day.month in (11, 12) else (0.8 if day.month in (1, 2) else 1.0)
        for _ in range(rnd.randint(3, 9)):
            oid += 1
            region = rnd.choice(regions)
            seg = rnd.choices(segments, [5, 3, 2])[0]
            cat = rnd.choice(cats)
            sales = rnd.uniform(20, 900) * growth * season * (1.6 if cat == "Technology" else 1.0)
            if region == "Central" and day >= dt.date(2024, 12, 1):
                sales *= 0.45   # planted exception for the demo month
            profit = sales * rnd.uniform(-0.1, 0.3)
            rows.append({"ORDER_DATE": day, "REGION": region, "SEGMENT": seg, "CATEGORY": cat,
                         "SALES": sales, "PROFIT": profit, "QUANTITY": rnd.randint(1, 9), "ORDER_ID": oid})
        day += dt.timedelta(days=1)
    # order hour (separate RNG so the original stream - and existing test numbers - are unchanged);
    # the last day is "live": only orders up to 14:00 exist yet.
    hr = random.Random(11)
    weights = [0, 0, 0, 0, 0, 0, 1, 2, 4, 6, 7, 8, 9, 9, 8, 8, 8, 9, 10, 10, 8, 6, 3, 1]
    last = rows[-1]["ORDER_DATE"]
    out = []
    for r in rows:
        r["ORDER_HOUR"] = hr.choices(range(24), weights)[0]
        if r["ORDER_DATE"] == last and r["ORDER_HOUR"] > 14:
            continue
        out.append(r)
    return out


ROWS = _gen_rows()
DIMS = {"ORDER_DATE": "DATE", "REGION": "VARCHAR", "SEGMENT": "VARCHAR", "CATEGORY": "VARCHAR",
        "ORDER_HOUR": "NUMBER"}
METRICS = {
    "SALES": ("SUM(SALES)", lambda rs: sum(r["SALES"] for r in rs)),
    "PROFIT": ("SUM(PROFIT)", lambda rs: sum(r["PROFIT"] for r in rs)),
    "QUANTITY": ("SUM(QUANTITY)", lambda rs: sum(r["QUANTITY"] for r in rs)),
    "ORDER_COUNT": ("COUNT(DISTINCT ORDER_ID)", lambda rs: len({r["ORDER_ID"] for r in rs})),
    # plan phased from a smooth trend (no noise), so actuals land either side of it
    "PLAN_SALES": ("SUM(PLAN_SALES)", lambda rs: sum(r["SALES"] for r in rs) * 0.97 + 40 * len({r["ORDER_DATE"] for r in rs})),
    "PROFIT_RATIO": ("ORDERS.PROFIT / ORDERS.SALES", lambda rs: (sum(r["PROFIT"] for r in rs) / sum(r["SALES"] for r in rs))
                     if rs else None),
}


class Row(dict):
    def as_dict(self):
        return dict(self)


def trunc(d: dt.date, g: str) -> dt.date:
    if g == "day":
        return d
    if g == "week":
        return d - dt.timedelta(days=d.weekday())
    if g == "month":
        return d.replace(day=1)
    if g == "quarter":
        return d.replace(month=3 * ((d.month - 1) // 3) + 1, day=1)
    raise ValueError(g)


class Result:
    def __init__(self, rows):
        self.rows = [Row(r) for r in rows]

    def collect(self):
        return self.rows


class FakeSession:
    def __init__(self, *, fail_top_insights=True, fail_forecast=False, agents=None):
        self.sqls = []
        self.tables = defaultdict(list)
        self.fail_top_insights = fail_top_insights
        self.fail_forecast = fail_forecast
        self.agents = agents if agents is not None else {}
        self.forecast_models = {}

    def sql(self, text, params=None):
        if os.environ.get("AA_FAKE_DELAY"):                    # local demos only: makes slow actions visible
            time.sleep(float(os.environ["AA_FAKE_DELAY"]))
        self.sqls.append((text, params))
        return Result(self._run(text.strip(), params or []))

    # ------------------------------------------------------------------------------------
    def _run(self, s, params):
        up = s.upper()
        if up.startswith("SELECT CURRENT_ROLE"):
            return [{"R": "WBR_OWNER"}]
        # ---- B1 semantic view builder ----
        if "INFORMATION_SCHEMA.TABLES" in up:
            return ([{"TABLE_NAME": "SHIPMENTS", "TABLE_TYPE": "BASE TABLE", "ROW_COUNT": 1000},
                     {"TABLE_NAME": "CARRIERS", "TABLE_TYPE": "BASE TABLE", "ROW_COUNT": 4},
                     {"TABLE_NAME": "CALLS", "TABLE_TYPE": "BASE TABLE", "ROW_COUNT": 0},
                     {"TABLE_NAME": "APP_SETTINGS", "TABLE_TYPE": "BASE TABLE", "ROW_COUNT": 3},
                     {"TABLE_NAME": "AI_BI_STUDIO_EVENTS", "TABLE_TYPE": "BASE TABLE", "ROW_COUNT": 500},
                     {"TABLE_NAME": "SHIPMENT_FACTS_V", "TABLE_TYPE": "VIEW", "ROW_COUNT": None}]
                    if params and params[0] == "PUBLIC" else [])
        if "SELECT TABLE_NAME, COLUMN_NAME FROM" in up and "INFORMATION_SCHEMA.COLUMNS" in up:
            if not params or params[0] != "PUBLIC":
                return []
            ship = ["SHIP_DATE", "CARRIER", "Region Name", "SHIPMENT_ID", "FREIGHT_COST", "TRANSIT_DAYS"]
            return ([{"TABLE_NAME": "SHIPMENTS", "COLUMN_NAME": c} for c in ship]
                    + [{"TABLE_NAME": "CARRIERS", "COLUMN_NAME": c} for c in ("CARRIER", "CARRIER_TYPE", "SLA_DAYS")])
        # ---- B6 multi-table: CARRIERS is the lookup SHIPMENTS.CARRIER points to ----
        if "INFORMATION_SCHEMA.COLUMNS" in up and len(params) > 1 and params[1] == "CARRIERS":
            return [{"COLUMN_NAME": c, "DATA_TYPE": t, "COMMENT": None} for c, t in
                    (("CARRIER", "TEXT"), ("CARRIER_TYPE", "TEXT"), ("SLA_DAYS", "NUMBER"))]
        if up.startswith("SELECT COUNT(*) AS N__ROWS") and ".CARRIERS " in up + " ":
            return [{"N__ROWS": 4, "D0": 4, "N0": 0, "S0": '["FedEx","OnTrac","UPS","USPS"]',
                     "D1": 2, "N1": 0, "S1": '["Ground","Express"]', "D2": 3, "N2": 0, "LO2": "1", "HI2": "5"}]
        if up.startswith("SHOW PRIMARY KEYS"):
            raise RuntimeError("SHOW PRIMARY KEYS not supported (fake)")
        if up.startswith("SELECT COUNT(*) AS N, COUNT(DISTINCT"):
            col = re.search(r"COUNT\(DISTINCT (.+?)\)", s).group(1).strip('"').upper()
            uniq = {("SHIPMENTS", "SHIPMENT_ID"): (1000, 1000), ("CARRIERS", "CARRIER"): (4, 4),
                    ("CARRIERS", "CARRIER_TYPE"): (4, 2), ("CARRIERS", "SLA_DAYS"): (4, 3)}
            tbl = "CARRIERS" if "CARRIERS" in up else "SHIPMENTS"
            n, d = uniq.get((tbl, col), (1000, 10))
            return [{"N": n, "D": d, "Z": 0}]
        if "COUNT_IF(S.V IS NOT NULL) AS N" in up:
            return [{"N": 1000, "MISS": int(getattr(self, "fake_miss", 0))}]
        if up.startswith("SELECT SUM(") and "WBR_DB.PUBLIC.SHIPMENTS" in up:
            return [{"V": 123456.78}]
        if "SEMANTIC_VIEW(WBR_DB.ANALYTICS_ENTERPRISE.AA_" in up and " AS V)" in up:
            return [{"V": getattr(self, "fake_sv_total", 123456.78)}]
        if "INFORMATION_SCHEMA.COLUMNS" in up:
            return [{"COLUMN_NAME": c, "DATA_TYPE": t, "COMMENT": None} for c, t in
                    (("SHIP_DATE", "DATE"), ("CARRIER", "TEXT"), ("Region Name", "TEXT"), ("SHIPMENT_ID", "NUMBER"),
                     ("FREIGHT_COST", "NUMBER"), ("TRANSIT_DAYS", "FLOAT"))]
        if up.startswith("SELECT COUNT(*) AS N__ROWS"):
            row = {"N__ROWS": 1000}
            for i, (d, lo, hi, smp) in enumerate(((400, "2025-01-01", "2026-09-30", None), (4, None, None, '["FedEx","OnTrac","UPS","USPS"]'),
                                                   (5, None, None, '["Midwest","Northeast","West"]'), (1000, "1", "1000", None),
                                                   (900, "1.2", "88", None), (40, "1", "9", None))):
                row.update({f"D{i}": d, f"N{i}": 0})
                if smp: row[f"S{i}"] = smp
                else: row.update({f"LO{i}": lo, f"HI{i}": hi})
            return [row]
        if up.startswith("CREATE OR REPLACE VIEW WBR_DB.ANALYTICS_ENTERPRISE.AA_SRC_"):
            self.created_views = getattr(self, "created_views", []) + [s]
            return []
        if up.startswith("CREATE OR REPLACE SEMANTIC VIEW"):
            self.created_svs = getattr(self, "created_svs", []) + [s]
            return []
        if "SEMANTIC_VIEW(WBR_DB.ANALYTICS_ENTERPRISE.AA_" in up:
            return [{"CARRIER": "UPS", "FREIGHT_COST": 1234.5}, {"CARRIER": "USPS", "FREIGHT_COST": 987.0}]
        if up.startswith("SHOW SEMANTIC DIMENSIONS") and " FOR METRIC " in up:
            import os
            if os.environ.get("AA_FAKE_RESTRICT") != "1":
                raise RuntimeError("unsupported (fake)")         # default: every pair allowed, as before
            metric = up.rsplit(" FOR METRIC ", 1)[1].strip().strip('"')
            allowed = ["ORDER_DATE", "REGION"] if metric == "PROFIT_RATIO" else list(DIMS)
            return [{"table_name": ENTITY, "name": d} for d in allowed]
        if up.startswith("SHOW SEMANTIC VIEWS IN SCHEMA"):
            if "WBR_DB.PUBLIC" in up:
                return [{"name": "SUPERSTORE_DEMO_SV", "database_name": "WBR_DB", "schema_name": "PUBLIC",
                         "comment": "Superstore orders (demo)", "created_on": "2026-07-24"}]
            return []
        if up.startswith("DESCRIBE SEMANTIC VIEW"):
            out = [{"object_kind": "TABLE", "object_name": ENTITY, "parent_entity": None,
                    "property": "BASE_TABLE_NAME", "property_value": "ORDERS_SAMPLE_SUPERSTORE"}]
            for d, t in DIMS.items():
                out.append({"object_kind": "DIMENSION", "object_name": d, "parent_entity": ENTITY,
                            "property": "DATA_TYPE", "property_value": t})
                out.append({"object_kind": "DIMENSION", "object_name": d, "parent_entity": ENTITY,
                            "property": "EXPRESSION", "property_value": d})
            for m, (expr, _) in METRICS.items():
                out.append({"object_kind": "METRIC", "object_name": m, "parent_entity": ENTITY,
                            "property": "EXPRESSION", "property_value": expr})
                out.append({"object_kind": "METRIC", "object_name": m, "parent_entity": ENTITY,
                            "property": "DATA_TYPE", "property_value": "NUMBER(38,2)"})
            return out
        if up.startswith("SHOW AGENTS IN SCHEMA"):
            schema = s.split("IN SCHEMA", 1)[1].strip().upper()
            return [{"name": fqn.split(".")[2], "database_name": fqn.split(".")[0],
                     "schema_name": fqn.split(".")[1], "owner": "WBR_OWNER",
                     "profile": json.dumps({"display_name": "Superstore agent"})}
                    for fqn in self.agents if fqn.startswith(schema + ".")]
        if up.startswith("DESCRIBE AGENT"):
            fqn = s.split("AGENT", 1)[1].strip().replace('"', "").upper()
            return [{"agent_spec": json.dumps(self.agents.get(fqn, {}))}]
        if up.startswith("CREATE AGENT") or up.startswith("CREATE OR REPLACE AGENT"):
            name = re.search(r"CREATE (?:OR REPLACE )?AGENT (?:IF NOT EXISTS )?(\S+)", s).group(1).upper()
            spec = json.loads(s.split("$$")[1])
            self.agents[name] = spec
            return [{"status": "created"}]
        if "DATA_AGENT_RUN" in up:
            body = json.loads(params[1])
            q = body["messages"][0]["content"][0]["text"]
            return [{"R": json.dumps(json.dumps({"role": "assistant", "content": [
                {"type": "tool_use", "tool_use": {"name": "analyst"}},
                {"type": "tool_result", "tool_result": {"content": [{"json": {
                    "sql": "SELECT REGION, SUM(SALES) FROM ORDERS GROUP BY 1",
                    "result_set": {"data": [["West", "1200"], ["East", "900"]],
                                   "resultSetMetaData": {"rowType": [{"name": "REGION"}, {"name": "SALES"}]}}}}]}},
                {"type": "text", "text": f"(fake agent) Answer to: {q}. West leads sales."}],
                "metadata": {"run_id": "run-123", "thread_id": 42, "assistant_message_id": 7}}))}]
        if "AI_COMPLETE" in up or "CORTEX.COMPLETE" in up:
            prompt = params[1] if params else s
            import os
            import time as _t
            if os.environ.get("AA_FAKE_DELAY") and "single word OK" not in prompt:
                _t.sleep(float(os.environ["AA_FAKE_DELAY"]))
            if "Reply with the single word OK" in prompt:
                return [{"R": "OK"}]
            if "Pick the tables (1 to 6)" in prompt:
                return [{"R": json.dumps({"tables": [{"fqn": "WBR_DB.PUBLIC.SHIPMENTS", "why": "freight cost per shipment"},
                                                     {"fqn": "WBR_DB.PUBLIC.CARRIERS", "why": "carrier type and SLA"},
                                                     {"fqn": "WBR_DB.PUBLIC.NOT_LISTED", "why": "invented"}],
                                          "note": "No customer table found."})}]
            if "You turn a business user's alert request" in prompt:
                req = prompt.split("User request:", 1)[1].split("\n", 1)[0]
                emails = re.findall(r"[\w.+-]+@[\w.-]+\.[a-z]{2,}", req)
                out = {"metric": "ORDERS.PROFIT_RATIO", "filters": {"ORDERS.REGION": ["West"]} if "west" in req.lower() else {},
                       "grain": "day", "rule": "threshold", "op": "below", "value": 12,
                       "schedule": {"freq": "daily", "hour": 9}, "recipients": emails,
                       "missing_people": ["Priya"] if "priya" in req.lower() else [], "question": ""}
                if "margin" in req.lower() and "ratio" not in req.lower():
                    out["question"] = "Did you mean Profit Ratio (a %) or Profit (an amount)?"
                return [{"R": json.dumps(out)}]
            if "You turn a business user's description of a metric" in prompt:
                req = prompt.split("User request:", 1)[1].split("\n", 1)[0].lower()
                if "only" in req or "region" in req:
                    return [{"R": json.dumps({"error": "It needs a filter on region, which a formula cannot apply."})}]
                if "drop" in req:
                    return [{"R": json.dumps({"name": "EVIL", "formula": "ORDERS.SALES; DROP TABLE X"})}]
                return [{"R": json.dumps({"name": "PROFIT_PER_ORDER", "label": "Profit per Order",
                                          "formula": "ORDERS.PROFIT / ORDERS.ORDER_COUNT",
                                          "description": "Average profit earned on each order.", "theme": "Profitability"})}]
            if "dashboards for EACH audience" in prompt:
                sv = "WBR_DB.PUBLIC.SUPERSTORE_DEMO_SV"
                items = []
                for aud, t, ms in (
                        ("executives", "Revenue and margin vs last year", ["Sales", "Profit", "Made Up"]),
                        ("executives", "Profitability outlook and drivers", ["Profit Ratio", "Profit"]),
                        ("executives", "Volume trend to year end", ["Order Count", "Quantity"]),
                        ("managers", "Region sales scorecard", ["Sales", "Profit Ratio"]),
                        ("managers", "Category profitability ranking", ["Profit", "Profit Ratio"]),
                        ("managers", "Segment volume exceptions", ["Quantity", "Order Count"]),
                        ("daily_operations", "Live sales today", ["Sales"]),
                        ("daily_operations", "Order pace by hour", ["Order Count", "Quantity"]),
                        ("daily_operations", "Margin leaks today", ["Profit Ratio", "Profit"])):
                    items.append({"audience": aud, "title": t, "detail": f"{', '.join(ms)} for this audience",
                                  "metrics": ms, "semantic_view": sv, "domain": "Superstore", "goal": t})
                items.append({"audience": "ceo", "title": "bad", "semantic_view": sv})
                items.append({"audience": "executives", "title": "bad view", "semantic_view": "X.Y.Z"})
                return [{"R": json.dumps({"suggestions": items})}]
            if "Route a business user's request" in prompt:
                return [{"R": json.dumps({"semantic_view": "WBR_DB.PUBLIC.SUPERSTORE_DEMO_SV", "audience": "managers",
                                          "goal": "Manager view of profit by region", "primary_metric": "Profit",
                                          "reason": "Superstore has profit by region."})}]
            if "User request for this tile" in prompt:
                return [{"R": json.dumps({"tile": {"type": "trend_chart", "title": "Sales trend",
                                                   "metric": "ORDERS.SALES", "width": 8}})}]
            if "Design ONE new page" in prompt:
                return [{"R": json.dumps({"pages": [{"label": "Customers", "question": "Who buys?", "tiles": [
                    {"type": "share_donut", "title": "Sales by segment", "metric": "ORDERS.SALES",
                     "dimension": "ORDERS.SEGMENT", "width": 4},
                    {"type": "ranked_bar", "title": "Orders by region", "metric": "ORDERS.ORDER_COUNT",
                     "dimension": "ORDERS.REGION", "width": 8}]}]})}]
            if "Return ONE new tile" in prompt:
                return [{"R": json.dumps({"tile": {"type": "share_donut", "title": "Profit ratio share by category",
                                                   "question": "q", "metric": "ORDERS.PROFIT_RATIO",
                                                   "dimension": "ORDERS.CATEGORY", "width": 4}})}]
            if "Redesign ONE page only" in prompt:
                return [{"R": "```json\n" + json.dumps({"pages": [{"label": "Mix", "question": "What is the mix?",
                    "tiles": [{"type": "share_donut", "title": "Sales mix by segment", "metric": "ORDERS.SALES",
                               "dimension": "ORDERS.SEGMENT", "width": 4},
                              {"type": "period_compare", "title": "Sales by category vs last year",
                               "metric": "ORDERS.SALES", "dimension": "ORDERS.CATEGORY", "width": 8}]}]}) + "\n```"}]
            if "Design the layout as JSON" in prompt:
                return [{"R": json.dumps({"title": "Margin health", "summary": "Where profit leaks.", "pages": [
                    {"label": "Overview", "question": "Are we growing profitably?", "tiles": [
                        {"type": "kpi_grid", "title": "Headline KPIs", "metrics": ["ORDERS.SALES", "PROFIT", "Profit Ratio"], "width": 12},
                        {"type": "forecast", "title": "Sales outlook", "metric": "ORDERS.SALES", "width": 8},
                        {"type": "share_donut", "title": "Sales share by region", "metric": "ORDERS.SALES",
                         "dimension": "ORDERS.REGION", "width": 4},
                        {"type": "scatter", "title": "Sales vs profit by region", "metric": "ORDERS.SALES",
                         "metric2": "ORDERS.PROFIT", "dimension": "ORDERS.REGION", "width": 6},
                        {"type": "sankey", "title": "Flow", "metric": "ORDERS.SALES"},
                        {"type": "exception_table", "title": "Regions needing attention", "metric": "ORDERS.SALES",
                         "dimension": "ORDERS.REGION", "width": 6}]},
                    {"label": "Margin", "question": "Where is margin weakest?", "tiles": [
                        {"type": "heatmap", "title": "Profit by segment and region", "metric": "ORDERS.PROFIT",
                         "dimension": "ORDERS.SEGMENT", "dimension2": "ORDERS.REGION", "width": 12},
                        {"type": "pareto", "title": "Profit ratio concentration", "metric": "ORDERS.PROFIT_RATIO",
                         "dimension": "ORDERS.CATEGORY", "width": 6},
                        {"type": "period_compare", "title": "Profit by category", "metric": "ORDERS.PROFIT",
                         "dimension": "ORDERS.CATEGORY", "width": 6},
                        {"type": "driver_bridge", "title": "What moved sales", "metric": "ORDERS.SALES",
                         "dimension": "ORDERS.CATEGORY", "width": 7},
                        {"type": "detail_table", "title": "Detail", "metrics": ["ORDERS.SALES", "ORDERS.MADE_UP"],
                         "dimensions": ["ORDERS.REGION", "ORDERS.CATEGORY"], "width": 12},
                        {"type": "ranked_bar", "title": "Sales ranking", "metric": "ORDERS.NOPE",
                         "dimension": "ORDERS.STATE", "width": 5},
                        {"type": "exception_table", "title": "Unusual regions", "metric": "ORDERS.SALES",
                         "dimension": "ORDERS.REGION", "width": 5}]}]})}]
            if "You design a Snowflake semantic view" in prompt:
                return [{"R": json.dumps({"view_name": "shipments", "description": "Parcel shipments by carrier and region",
                    "time_dimension": "SHIP_DATE",
                    "dimensions": [{"column": "CARRIER", "name": "carrier", "synonyms": ["shipper"], "comment": "Parcel carrier."},
                                   {"column": "Region Name", "name": "region", "synonyms": ["territory"], "comment": "Sales region."},
                                   {"column": "WAREHOUSE", "name": "warehouse", "synonyms": [], "comment": "made up"}],
                    "metrics": [{"name": "freight_cost", "agg": "SUM", "column": "FREIGHT_COST", "synonyms": ["shipping cost"], "comment": "Total freight cost (USD)."},
                                {"name": "shipments", "agg": "COUNT_DISTINCT", "column": "SHIPMENT_ID", "synonyms": ["parcels"], "comment": "Number of shipments."},
                                {"name": "avg_transit_days", "agg": "AVG", "column": "TRANSIT_DAYS", "synonyms": [], "comment": "Average days in transit."}],
                    "ratios": [{"name": "cost_per_shipment", "numerator": "freight_cost", "denominator": "shipments", "comment": "Freight cost per shipment (USD)."}],
                    "questions": ["Which carrier costs most per shipment?", "Is transit time rising?"]})}]
            if "Allowed layouts" in prompt:
                ids = re.findall(r"^- ([a-z0-9_]+):", prompt, re.M)
                return [{"R": json.dumps({"template_id": ids[-1] if ids else None,
                                          "reason": "Matches the stated intent (fake Cortex)."})}]
            if "Map semantic-view fields" in prompt:
                return [{"R": json.dumps({"primary_metric": "ORDERS.SALES",
                                          "supporting_metrics": ["ORDERS.PROFIT", "ORDERS.NOT_A_METRIC"],
                                          "time_dimension": "ORDERS.ORDER_DATE",
                                          "segment_dimension": "ORDERS.SEGMENT",
                                          "region_dimension": "ORDERS.REGION", "reason": "fake"})}]
            return [{"R": "- Sales grew vs last year (fake summary).\n- Central is below its norm.\n"
                          "- Technology leads.\nSuggested action: review Central region pricing."}]
        if up.startswith("SHOW SNOWFLAKE.ML.FORECAST") or up.startswith("SHOW SNOWFLAKE.ML.TOP_INSIGHTS"):
            return []
        if up.startswith("CREATE OR REPLACE TABLE") or up.startswith("INSERT INTO WBR_DB.ANALYTICS_ENTERPRISE.AA_FC_IN"):
            if self.fail_forecast:
                raise RuntimeError("Insufficient privileges to create FORECAST (fake)")
            if up.startswith("INSERT"):
                table = s.split()[2].upper()
                vals = re.findall(r"\('([0-9-]+)'::TIMESTAMP_NTZ, ([-0-9.e]+)\)", s)
                self.tables[table] = [(a, float(b)) for a, b in vals]
            return []
        if "EXECUTE_AI_EVALUATION" in up:
            if "'START'" in up:
                self.eval_started = getattr(self, "eval_started", []) + [params[0]]
                return [{"STATUS": "STARTED"}]
            return [{"STATUS": "COMPLETED", "DETAIL": f"run {params[0]}"}]
        if "AA_EVAL_RUNS" in up:
            runs = self.tables.setdefault("EVAL_RUNS", [])
            if up.startswith("INSERT"):
                runs.append({"RUN_NAME": params[0], "AGENT": params[1], "STARTED_BY": "SHARATH",
                             "STARTED_AT": f"2026-10-01 12:{len(runs):02d}"})
            if up.startswith("SELECT"):
                return [r for r in runs if r["AGENT"] == params[0]][::-1]
            return []
        if "GET_AI_EVALUATION_DATA" in up:
            if "GROUP BY" in up:
                return [{"METRIC_NAME": "answer_correctness", "SCORE": 0.81, "N": 8},
                        {"METRIC_NAME": "cites_sources", "SCORE": 0.62, "N": 8},
                        {"METRIC_NAME": "logical_consistency", "SCORE": 0.9, "N": 8}]
            return [{"INPUT": "Why did free shipping % drop this year?", "METRIC_NAME": "answer_correctness",
                     "SCORE": 0.9, "OUTPUT": "Threshold raised to 119 USD (HLO-POL-014)", "DURATION_MS": 8200}]
        if up.startswith("ALTER SESSION SET QUERY_TAG"):
            self.query_tag = s.split("=", 1)[1].strip().strip("'")
            return []
        if "SNOWFLAKE.ACCOUNT_USAGE.QUERY_HISTORY" in up:
            if "QUERY_ATTRIBUTION_HISTORY" in up:
                raise RuntimeError("Object 'QUERY_ATTRIBUTION_HISTORY' does not exist or not authorized (fake)")
            return [{"FEATURE": "set_view", "QUERIES": 42, "ELAPSED_S": 31.5, "CORTEX_CREDITS": None, "TOKENS": None},
                    {"FEATURE": "ask", "QUERIES": 6, "ELAPSED_S": 18.2, "CORTEX_CREDITS": 0.012, "TOKENS": 9100}]
        if "AI_AGG(" in up:
            if getattr(self, "fail_ai_agg", False):
                raise RuntimeError("AI_AGG not available (fake)")
            n = len(json.loads(params[0])) if params else 0
            return [{"R": f"- {n} governed facts summarised (fake AI_AGG).\n- West leads.\n- Central lags.\n"
                          "Suggested action: review Central pricing."}]
        if up.startswith("SHOW SNOWFLAKE.ML.ANOMALY_DETECTION"):
            if getattr(self, "fail_anomaly", False):
                raise RuntimeError("ANOMALY_DETECTION not enabled (fake)")
            return []
        if up.startswith("INSERT INTO WBR_DB.ANALYTICS_ENTERPRISE.AA_AD_"):
            table = s.split()[2].upper()
            self.tables[table] = [(a, b, float(c)) for a, b, c in
                                  re.findall(r"\('((?:[^']|'')*)', '([0-9-]+)'::TIMESTAMP_NTZ, ([-0-9.e]+)\)", s)]
            return []
        if up.startswith("CREATE SNOWFLAKE.ML.ANOMALY_DETECTION"):
            if getattr(self, "fail_anomaly", False):
                raise RuntimeError("ANOMALY_DETECTION not enabled (fake)")
            name = re.search(r"IF NOT EXISTS (\S+)\(", s).group(1).upper()
            table = re.search(r"SYSTEM\$REFERENCE\('TABLE', '([^']+)'\)", s).group(1).upper()
            self.forecast_models[name] = self.tables[table]
            return []
        if up.startswith("CALL") and "!DETECT_ANOMALIES" in up:
            name = re.search(r"CALL (\S+)!DETECT_ANOMALIES", s).group(1).upper()
            table = re.search(r"SYSTEM\$REFERENCE\('TABLE', '([^']+)'\)", s).group(1).upper()
            train = self.forecast_models[name]
            out = []
            for seg, ts, y in self.tables[table]:
                hist = [v for sg, _, v in train if sg == seg][-12:]
                mean = sum(hist) / len(hist)
                band = max(abs(mean) * 0.08, 1e-9)
                out.append({"SERIES": json.dumps(seg), "TS": ts + " 00:00:00", "Y": y, "FORECAST": mean,
                            "LOWER_BOUND": mean - band, "UPPER_BOUND": mean + band,
                            "IS_ANOMALY": abs(y - mean) > band, "PERCENTILE": 0.99 if y > mean else 0.01,
                            "DISTANCE": abs(y - mean) / band})
            return out
        if up.startswith("CREATE SNOWFLAKE.ML.FORECAST"):
            name = re.search(r"IF NOT EXISTS (\S+)\(", s).group(1).upper()
            table = re.search(r"SYSTEM\$REFERENCE\('TABLE', '([^']+)'\)", s).group(1).upper()
            self.forecast_models[name] = self.tables[table]
            return []
        if up.startswith("CALL") and "!FORECAST" in up:
            name = re.search(r"CALL (\S+)!FORECAST", s).group(1).upper()
            n = int(re.search(r"FORECASTING_PERIODS => (\d+)", s).group(1))
            data = self.forecast_models[name]
            last = dt.date.fromisoformat(data[-1][0])
            step = (last - dt.date.fromisoformat(data[-2][0])).days
            base = sum(v for _, v in data[-3:]) / 3
            out = []
            for i in range(1, n + 1):
                d = last + dt.timedelta(days=step * i)
                if step >= 28:
                    d = (last.replace(day=1) + dt.timedelta(days=32 * i)).replace(day=1)
                out.append({"TS": d.isoformat() + " 00:00:00", "FORECAST": base * (1 + 0.01 * i),
                            "LOWER_BOUND": base * 0.85, "UPPER_BOUND": base * 1.15})
            return out
        if up.startswith("CREATE OR REPLACE TRANSIENT TABLE"):
            return []
        if up.startswith("CREATE SNOWFLAKE.ML.TOP_INSIGHTS") or "GET_DRIVERS" in up:
            if self.fail_top_insights:
                raise RuntimeError("TOP_INSIGHTS not enabled (fake)")
            return [{"CONTRIBUTOR": json.dumps(["D1 = Central"]), "METRIC_CONTROL": 100.0, "METRIC_TEST": 40.0,
                     "CONTRIBUTION": -60.0, "RELATIVE_CONTRIBUTION": -0.5, "GROWTH_RATE": -0.6}]
        if up.startswith("CREATE TABLE IF NOT EXISTS"):
            return []
        if up.startswith("INSERT INTO") and "AA_DECISIONS" in up:
            keys = ["DECISION_ID", "SEMANTIC_VIEW", "TEMPLATE_ID", "TITLE", "DETAIL", "OWNER", "DUE_DATE", "EVIDENCE"]
            row = dict(zip(keys, params))
            row.update({"STATUS": "Open", "CREATED_BY": "SHARATH", "CREATED_AT": "2026-09-30 12:00"})
            self.tables["DECISIONS"].append(row)
            return []
        if up.startswith("UPDATE") and "AA_DECISIONS" in up:
            for r in self.tables["DECISIONS"]:
                if r["DECISION_ID"] == params[1]:
                    r["STATUS"] = params[0]
            return []
        if "FROM WBR_DB.ANALYTICS_ENTERPRISE.AA_DECISIONS" in up:
            return [dict(r) for r in self.tables["DECISIONS"] if r["SEMANTIC_VIEW"] == params[0]][::-1]
        if "AA_CUSTOM_METRICS" in up:
            cms = self.tables["CUSTOM_METRICS"]
            if up.startswith("INSERT"):
                keys = ["SEMANTIC_VIEW", "NAME", "LABEL", "FORMULA", "DESCRIPTION", "THEME", "ORIGIN", "CREATED_BY"]
                cms.append({**dict(zip(keys, params)), "ACTIVE": True, "CREATED_AT": "2026-10-10"})
                return []
            return [{k: v for k, v in r.items() if k != "SEMANTIC_VIEW"} for r in cms
                    if r["SEMANTIC_VIEW"] == params[0] and r["ACTIVE"]]
        if "AA_IDEAS" in up:
            ideas = self.tables.setdefault("IDEAS", [])
            if up.startswith("INSERT"):
                ideas.append({"ROLE_NAME": params[0], "CATALOG_SIG": params[1], "IDEAS": params[2],
                              "CREATED_AT": f"2026-10-01 12:{len(ideas):02d}"})
                return []
            if up.startswith("SELECT"):
                mine = [r for r in ideas if r["ROLE_NAME"] == params[0]]
                import re as _re
                n = int((_re.search(r"LIMIT (\d+)", up) or [0, 1])[1])
                return mine[::-1][:n]                  # newest first
            return []
        if "AA_PUBLISHED" in up:
            pub = self.tables.setdefault("PUB", [])
            if up.startswith("SELECT COALESCE"):
                return [{"V": max([r["VERSION"] for r in pub if r["DASHBOARD_ID"] == params[0]] or [0])}]
            if up.startswith("INSERT"):
                keys = ["DASHBOARD_ID", "VERSION", "NAME", "SEMANTIC_VIEW", "AUDIENCE", "BINDINGS", "LAYOUT_SPEC",
                        "VIEW_SETTINGS", "SHARED_ROLES", "SHARED_USERS", "NOTE", "PUBLISHED_BY"]
                pub.append({**dict(zip(keys, params)), "PUBLISHED_AT": "2026-10-01 12:00"})
                return []
            latest = {}
            for r in pub:
                if r["DASHBOARD_ID"] not in latest or r["VERSION"] > latest[r["DASHBOARD_ID"]]["VERSION"]:
                    latest[r["DASHBOARD_ID"]] = r
            return list(latest.values())
        if up.startswith("GRANT USAGE ON STREAMLIT"):
            self.grants = getattr(self, "grants", []) + [s]
            return [{"status": "granted"}]
        if up.startswith("SHOW ROLES"):
            return [{"name": n} for n in ("WBR_OWNER", "REGION_MANAGER_WEST", "EXEC_VIEWER", "PUBLIC")]
        if "AA_VALIDATION_RUNS" in up:
            runs = self.tables.setdefault("VALIDATION", [])
            if up.startswith("INSERT"):
                keys = ["RUN_ID", "DASHBOARD_ID", "SEMANTIC_VIEW", "PAGE_ID", "STATUS", "TILES", "VERIFIED", "REVIEW",
                        "MISMATCH", "NOT_CHECKED", "QUERIES", "REPORT", "RUN_BY"]
                runs.append({**dict(zip(keys, params)), "RUN_AT": f"2026-10-15 10:{len(runs):02d}"})
                return []
            return list(runs)[::-1]
        if "AA_THEMES" in up:
            th = self.tables.setdefault("THEMES", [])
            if up.startswith("CREATE"):
                return []
            if up.startswith("INSERT"):
                keys = ["THEME_ID", "NAME", "SOURCE", "INPUTS", "TOKENS", "CHECKS", "STATUS", "ACTIVE", "CREATED_BY"]
                th.append({**dict(zip(keys, params)), "CREATED_AT": f"2026-10-15 11:{len(th):02d}"})
                return []
            latest = {}
            for r in th:
                latest[r["THEME_ID"]] = r
            return list(latest.values())
        # ---- data alerts ----
        if up.startswith("CREATE OR REPLACE PROCEDURE") or up.startswith("CREATE OR REPLACE TASK") \
                or up.startswith("ALTER TASK"):
            self.tables["DDL"].append(s[:120])
            return [{"status": "ok"}]
        if "SYSTEM$SEND_EMAIL" in up:
            import os
            if os.environ.get("AA_FAKE_NO_EMAIL"):
                raise RuntimeError("Integration 'AA_EMAIL_INT' does not exist or not authorized.")
            self.tables["EMAILS"].append({"integration": params[0], "to": params[1], "subject": params[2],
                                          "body": params[3]})
            return [{"R": True}]
        if up.startswith("SHOW NOTIFICATION INTEGRATIONS"):
            import os
            return [{"name": "AA_EMAIL_INT", "type": "EMAIL", "enabled": "true"}] if not os.environ.get("AA_FAKE_NO_EMAIL") else []
        if up.startswith("SHOW TASKS"):
            return [{"name": "AA_ALERTS_TASK", "state": "started"}] if any("TASK" in d for d in self.tables["DDL"]) else []
        if "AA_ALERT_RUNS" in up:
            runs = self.tables["ALERT_RUNS"]
            if up.startswith("CREATE"):
                return []
            if up.startswith("INSERT"):
                keys = ["RUN_ID", "ALERT_ID", "CHECKED_AT", "TRIGGER_KIND", "STATUS", "PERIOD_LABEL", "VALUE",
                        "COMPARE_VALUE", "FIRED", "EMAILED", "MESSAGE"]
                runs.append(dict(zip(keys, params)))
                return []
            return [r for r in runs if r["ALERT_ID"] == params[0]][::-1]
        if "AA_ALERTS" in up:
            al = self.tables["ALERTS"]
            if up.startswith("CREATE"):
                return []
            if up.startswith("INSERT"):
                keys = ["ALERT_ID", "NAME", "SEMANTIC_VIEW", "DASHBOARD_ID", "DASHBOARD_NAME", "SPEC", "CHECK_SQL",
                        "OWNER"]
                row = dict(zip(keys, params))
                row.update(ACTIVE=True, DELETED=False, OWNER=row["OWNER"] or "SHARATH", CREATED_AT=f"2026-10-21 10:{len(al):02d}",
                           LAST_CHECK_AT=None, LAST_STATUS=None, LAST_VALUE=None, LAST_MESSAGE=None,
                           LAST_FIRED_KEY="", LAST_FIRED_AT=None)
                al.append(row)
                return []
            if up.startswith("UPDATE"):
                aid = params[-1]
                for r in al:
                    if r["ALERT_ID"] != aid:
                        continue
                    if "SET DELETED = TRUE" in up:
                        r.update(DELETED=True, ACTIVE=False)
                    elif "SET ACTIVE = ?" in up:
                        r["ACTIVE"] = params[0]
                    elif "SET NAME = ?" in up:
                        r.update(NAME=params[0], SPEC=params[1], CHECK_SQL=params[2], LAST_FIRED_KEY="")
                    elif "SET LAST_CHECK_AT" in up:
                        r.update(LAST_CHECK_AT=params[0], LAST_STATUS=params[1], LAST_VALUE=params[2],
                                 LAST_MESSAGE=params[3], LAST_FIRED_KEY=params[4])
                        if params[5]:
                            r["LAST_FIRED_AT"] = params[6]
                return []
            live = [r for r in al if not r["DELETED"]]
            if "ALERT_ID = ?" in up:
                live = [r for r in live if r["ALERT_ID"] == params[0]]
            return [dict(r) for r in live][::-1]
        if "AA_UAT_SIGNOFFS" in up:
            ut = self.tables.setdefault("UAT", [])
            if up.startswith("CREATE"):
                return []
            if up.startswith("INSERT"):
                keys = ["ENTRY_ID", "DASHBOARD_ID", "SEMANTIC_VIEW", "PAGE_ID", "TILE_KEY", "KIND", "DECISION", "COMMENT",
                        "TILE_SIG", "PAGE_SIG", "RUN_AT", "VALIDATION_STATUS", "CREATED_BY", "DASHBOARD_NAME",
                        "PAGE_LABEL", "TILE_TITLE"]
                ut.append({**dict(zip(keys, params)), "CREATED_AT": f"2026-10-16 09:{len(ut):02d}"})
                ut[-1]["CREATED_BY"] = ut[-1]["CREATED_BY"] or "SHARATH"
                return []
            if up.startswith("ALTER"):
                return []
            if up.startswith("UPDATE"):
                for r in ut:
                    if r["SEMANTIC_VIEW"] == params[2] and not r["DASHBOARD_ID"]:
                        r["DASHBOARD_ID"], r["DASHBOARD_NAME"] = params[0], params[1]
                return []
            if "COUNT_IF(DECISION" in up:
                keys = {(r["DASHBOARD_ID"], r["TILE_KEY"]) for r in ut if r["DECISION"] == "rejected"}
                return [r for r in ut if r["KIND"] == "tile" and r["DASHBOARD_ID"]
                        and (r["DASHBOARD_ID"], r["TILE_KEY"]) in keys][::-1]
            if "SEMANTIC_VIEW = ?" in up:
                hit = [r for r in ut if r["SEMANTIC_VIEW"] == params[0] and not r["DASHBOARD_ID"]]
            else:
                hit = [r for r in ut if r["DASHBOARD_ID"] == params[0]]
            return hit[::-1]
        if "AA_APP_SETTINGS" in up:
            st = self.tables.setdefault("SETTINGS", [])
            if up.startswith("CREATE"):
                return []
            if up.startswith("INSERT"):
                st.append({"SETTING_KEY": params[0], "SETTING_VALUE": params[1], "SET_BY": params[2] or "SHARATH",
                           "SET_AT": f"2026-10-15 11:{len(st):02d}"})
                return []
            if "STARTSWITH" in up:
                last = {}
                for r in st:
                    if r["SETTING_KEY"].startswith(params[0]):
                        last[r["SETTING_KEY"]] = r
                return list(last.values())
            hit = [r for r in st if r["SETTING_KEY"] == params[0]]
            return hit[-1:]
        if "AA_VALIDATION_RESOLUTIONS" in up:
            res = self.tables.setdefault("RESOLUTIONS", [])
            if up.startswith("INSERT"):
                keys = ["RES_ID", "DASHBOARD_ID", "SEMANTIC_VIEW", "TILE_KEY", "TILE_TITLE", "CHECK_ID", "ACTION", "REASON",
                        "OWNER", "DUE_DATE", "EXPIRES_AT", "TILE_SIG", "DECISION_ID", "CREATED_BY"]
                res.append({**dict(zip(keys, params)), "ACTIVE": True, "CREATED_AT": "2026-10-15 10:00"})
                return []
            if params and len(params) == 1 and "DASHBOARD_ID = ?" in up and "SEMANTIC_VIEW = ?" not in up:
                return [r for r in res if r["DASHBOARD_ID"] == params[0]][::-1]
            return [r for r in res if r["SEMANTIC_VIEW"] == params[0] and not r["DASHBOARD_ID"]][::-1]
        if "AA_DASHBOARDS" in up:
            if up.startswith("SELECT COALESCE"):
                return [{"V": max([r["VERSION"] for r in self.tables["DASH"] if r["DASHBOARD_ID"] == params[0]] or [0])}]
            if up.startswith("ALTER TABLE"):
                return []
            if up.startswith("INSERT"):
                keys = ["DASHBOARD_ID", "NAME", "SEMANTIC_VIEW", "AUDIENCE", "TEMPLATE_ID", "TEMPLATE_VERSION",
                        "BINDINGS", "VERSION", "LAYOUT_SPEC"]
                keys = ["DASHBOARD_ID", "NAME", "SEMANTIC_VIEW", "AUDIENCE", "TEMPLATE_ID", "TEMPLATE_VERSION",
                        "BINDINGS", "VERSION", "CREATED_BY", "LAYOUT_SPEC"]
                row = dict(zip(keys, params))
                row["CREATED_BY"] = row.get("CREATED_BY") or "SHARATH"
                self.tables["DASH"].append({**row, "CREATED_AT": "2026-09-30 12:00"})
                return []
            first = {}
            for r in self.tables["DASH"]:
                first.setdefault(r["DASHBOARD_ID"], r["CREATED_BY"])
            return [{**r, "OWNER": first[r["DASHBOARD_ID"]]} for r in self.tables["DASH"]]
        if "AA_AI_RUNS" in up:
            if up.startswith("INSERT"):
                self.tables["AI"].append({"FEATURE": params[1], "PROVENANCE": params[5], "STATUS": params[6],
                                          "LATENCY_S": params[7], "INPUT": params[3][:200], "OUTPUT": params[4][:300],
                                          "SEMANTIC_VIEW": params[2],
                                          "CREATED_BY": (params[8] if len(params) > 8 and params[8] else "SHARATH"),
                                          "CREATED_AT": "2026-09-30 12:00"})
                return []
            if "COUNT_IF" in up:
                mine = [r for r in self.tables["AI"] if r["CREATED_BY"] == params[0]]
                return [{"N_ALL": sum(r["FEATURE"] != "page_summary" for r in mine),
                         "N_AGENT": sum(r["FEATURE"] == "agent_question" for r in mine)}]
            return list(self.tables["AI"])[::-1]
        if "CORTEX_FUNCTIONS_USAGE_HISTORY" in up:
            return [{"FUNCTION_NAME": "AI_COMPLETE", "MODEL_NAME": "claude-sonnet-4-5", "CREDITS": 1.23, "TOKENS": 45000}]
        if "ORDERS_SAMPLE_SUPERSTORE" in up and "SEMANTIC_VIEW(" not in up:
            return self._base(s)
        if "SEMANTIC_VIEW(" in up:
            return self._semantic(s)
        raise RuntimeError(f"FakeSession does not understand: {s[:120]}")

    # ------------------------------------------------------------------------------------
    def _semantic(self, s):
        if "UNION ALL" in s.upper():
            out = []
            for part in re.split(r"\s+UNION ALL\s+", s, flags=re.I):
                ix = int(re.match(r"SELECT (\d+) AS IX", part.strip()).group(1))
                rows = self._eval_sv(part)
                out.append({"IX": ix, "N": len(rows)})
            return out
        rows = self._eval_sv(s)
        if "EXCLUDE (AA_B" in s:                      # custom metrics: formula computed over the base metrics
            rows = self._formulas(s, rows)
        head = s.upper().split("FROM", 1)[0]
        if "MIN(D)" in head:
            ds = [r["D"] for r in rows]
            return [{"MIN_D": min(ds), "MAX_D": max(ds)}]
        order = re.search(r"\)\s*ORDER BY (.+?)(?: LIMIT (\d+))?\s*$", s, re.S | re.I)
        if order:
            spec = order.group(1)
            if "M0 DESC" in spec.upper():
                rows.sort(key=lambda r: (r["M0"] is None, -(r["M0"] or 0)))
            else:
                keys = [k.strip() for k in spec.split(",")]
                rows.sort(key=lambda r: tuple(str(r.get(k)) for k in keys))
            if order.group(2):
                rows = rows[: int(order.group(2))]
        return rows

    @staticmethod
    def _formulas(s, rows):
        m = re.search(r"EXCLUDE \(([^)]*)\), (.+?) FROM SEMANTIC_VIEW\(", s, re.S)
        hidden = [h.strip() for h in m.group(1).split(",")]
        parts, depth, cur = [], 0, ""
        for ch in m.group(2):
            if ch == "," and depth == 0:
                parts.append(cur); cur = ""
                continue
            depth += ch == "("
            depth -= ch == ")"
            cur += ch
        parts.append(cur)
        exprs = [p.strip().rsplit(" AS ", 1) for p in parts]
        div0 = lambda a, b: 0.0 if not b else a / b
        out = []
        for r in rows:
            env = {k: (r.get(k) or 0.0) for k in hidden}
            item = {k: v for k, v in r.items() if k not in hidden}
            for expr, alias in exprs:
                if not re.fullmatch(r"[A-Z0-9_ .()+*/,-]+", expr):
                    raise RuntimeError("unexpected formula SQL: " + expr)
                item[alias] = eval(expr.replace("DIV0", "div0"), {"__builtins__": {}}, {**env, "div0": div0})
            out.append(item)
        return out

    def _eval_sv(self, s):
        inner = s[s.upper().index("SEMANTIC_VIEW(") + len("SEMANTIC_VIEW("):]
        dims_txt = re.search(r"DIMENSIONS (.+?)(?:\n\s*METRICS|\n\s*WHERE|\n\))", inner, re.S)
        mets_txt = re.search(r"METRICS (.+?)(?:\n\s*WHERE|\n\))", inner, re.S)
        where = re.search(r"WHERE (.+?)\n\)", inner, re.S)
        dims = []
        if dims_txt:
            for part in re.split(r",\s*(?![^()]*\))", dims_txt.group(1)):
                part = part.strip()
                m = re.match(r"DATE_TRUNC\('(\w+)', \w+\.(\w+)\) AS (\w+)", part)
                if m:
                    dims.append((m.group(3), m.group(2), m.group(1)))
                else:
                    m = re.match(r"\w+\.(\w+) AS (\w+)", part)
                    dims.append((m.group(2), m.group(1), None))
        mets = []
        if mets_txt:
            for part in mets_txt.group(1).split(","):
                m = re.match(r"\s*\w+\.(\w+) AS (\w+)", part)
                if m.group(1) not in METRICS:
                    raise RuntimeError(f"invalid metric {m.group(1)}")
                mets.append((m.group(2), m.group(1)))
        data = ROWS
        if where:
            lo, hi = re.findall(r"TO_DATE\('([0-9-]+)'\)", where.group(1))[:2]
            lo, hi = dt.date.fromisoformat(lo), dt.date.fromisoformat(hi)
            data = [r for r in data if lo <= r["ORDER_DATE"] < hi]
            for col, op, num in re.findall(r"\w+\.(\w+) (<=|>=|=) (\d+)", where.group(1)):
                n = int(num)
                data = [r for r in data if (r[col] <= n if op == "<=" else r[col] >= n if op == ">=" else r[col] == n)]
            for col, vals in re.findall(r"\w+\.(\w+) IN \(([^)]*)\)", where.group(1)):
                allowed = {v.strip().strip("'").replace("''", "'") for v in vals.split(",")}
                data = [r for r in data if str(r[col]) in allowed]
        groups = defaultdict(list)
        for r in data:
            key = tuple(trunc(r[col], g) if g else r[col] for _, col, g in dims)
            groups[key].append(r)
        out = []
        skew = getattr(self, "sv_skew", {})             # tests: the governed (dashboard) numbers drift, e.g. live data
        for key, rs in groups.items():
            row = {alias: key[i] for i, (alias, _, _) in enumerate(dims)}
            for alias, metric in mets:
                v = METRICS[metric][1](rs)
                row[alias] = v * skew[metric] if metric in skew and v is not None else v
            out.append(row)
        return out


# ---- independent base-table queries (validation QA-01/QA-05) ------------------------------------------------------
def _split_top(text, sep=","):
    parts, depth, cur, q = [], 0, "", False
    for ch in text:
        if ch == "'":
            q = not q
        if not q:
            depth += ch == "("
            depth -= ch == ")"
            if ch == sep and depth == 0:
                parts.append(cur)
                cur = ""
                continue
        cur += ch
    parts.append(cur)
    return [p.strip() for p in parts]


def _matching(text, i):
    """index of the ')' matching '(' at i"""
    depth = 0
    for j in range(i, len(text)):
        depth += text[j] == "("
        depth -= text[j] == ")"
        if depth == 0:
            return j
    raise ValueError("unbalanced")


def _pyexpr(e):
    e = re.sub(r"T0\.\"?(\w+)\"?", lambda m: f"r[{m.group(1)!r}]", e)
    e = re.sub(r"DATE_TRUNC\('(\w+)',", lambda m: f"_tr({m.group(1)!r},", e)
    e = re.sub(r"TO_DATE\('([0-9-]+)'\)", lambda m: f"_d({m.group(1)!r})", e)
    e = re.sub(r"(\S+|\([^()]*\)) IN \(([^)]*)\)", lambda m: f"_in({m.group(1)}, ({m.group(2)},))", e)
    e = re.sub(r"(?<![<>!=])=(?!=)", "==", e).replace("<>", "!=")
    e = re.sub(r"\bAND\b", "and", e)
    e = re.sub(r"\bOR\b", "or", e)
    e = e.replace("DIV0", "_div0")
    return e


_ENV = {"_tr": lambda g, d: trunc(d, g), "_d": lambda x: dt.date.fromisoformat(x),
        "_in": lambda v, vals: str(v) in {str(x) for x in vals}, "_div0": lambda a, b: 0.0 if not b else a / b,
        "__builtins__": {}}


def _agg_eval(expr, rows, skew):
    """Evaluate an aggregate expression over a group: replace SUM(...)/COUNT(DISTINCT ...)/AVG/MIN/MAX by values."""
    out, i = "", 0
    while i < len(expr):
        m = re.match(r"(SUM|AVG|MIN|MAX|COUNT)\(", expr[i:])
        if m and (i == 0 or not (expr[i - 1].isalnum() or expr[i - 1] == "_")):
            start = i + len(m.group(0)) - 1
            end = _matching(expr, start)
            inner = expr[start + 1:end].strip()
            fn = m.group(1)
            distinct = inner.upper().startswith("DISTINCT ")
            if distinct:
                inner = inner[9:]
            col = re.fullmatch(r"\(?T0\.(\w+)\)?", inner)
            if fn == "SUM" and col and col.group(1) == "PLAN_SALES":
                v = METRICS["PLAN_SALES"][1](rows)
            else:
                py = _pyexpr(inner)
                vals = [eval(py, _ENV, {"r": r}) for r in rows]
                vals = [v for v in vals if v is not None]
                if fn == "COUNT":
                    v = len(set(vals)) if distinct else len(vals)
                elif not vals:
                    v = None
                else:
                    v = {"SUM": sum, "MIN": min, "MAX": max, "AVG": lambda xs: sum(xs) / len(xs)}[fn](vals)
                if fn == "SUM" and col and col.group(1) in skew:
                    v = v * skew[col.group(1)]
            out += repr(v)
            i = end + 1
            continue
        out += expr[i]
        i += 1
    py = _pyexpr(out)
    return eval(py.replace("None", "0.0") if "/" in py else py, _ENV, {})


def _base(self, s):
    """SELECT <outer> FROM (SELECT items FROM ...ORDERS_SAMPLE_SUPERSTORE T0 [WHERE ..] [GROUP BY ..]) [ORDER BY ..]"""
    self.base_sqls = getattr(self, "base_sqls", []) + [s]
    if os.environ.get("AA_FAKE_BASE_DELAY"):            # local demos: slow base-table scans (validation)
        time.sleep(float(os.environ["AA_FAKE_BASE_DELAY"]))
    if getattr(self, "fail_base", False):
        raise RuntimeError("SQL access control error: insufficient privileges on ORDERS_SAMPLE_SUPERSTORE (fake)")
    skew = getattr(self, "base_skew", None) or json.loads(os.environ.get("AA_FAKE_SKEW", "{}"))   # plant an error
    open_ix = s.index("(SELECT ")
    close_ix = _matching(s, open_ix)
    outer_sel = s[len("SELECT "):s.upper().index(" FROM ")].strip()
    order = s[close_ix + 1:].strip()
    inner = s[open_ix + 1:close_ix]
    m = re.match(r"SELECT (.+?)\nFROM \S+ T0(?:\nWHERE (.+?))?(?:\nGROUP BY (.+))?$", inner, re.S)
    items = [x.rsplit(" AS ", 1) for x in _split_top(m.group(1))]
    data = ROWS
    if m.group(2):
        cond = _pyexpr(m.group(2))
        data = [r for r in data if eval(cond, _ENV, {"r": r})]
    aggs = re.compile(r"(?<![\w])(SUM|AVG|MIN|MAX|COUNT)\(")
    dim_items = [(e, a) for e, a in items if not aggs.search(e)]
    met_items = [(e, a) for e, a in items if aggs.search(e)]
    groups = defaultdict(list)
    for r in data:
        key = tuple(eval(_pyexpr(e), _ENV, {"r": r}) for e, _ in dim_items)
        groups[key].append(r)
    if not dim_items and not groups:
        groups[()] = []
    rows = []
    for key, rs in groups.items():
        row = {a: key[i] for i, (_, a) in enumerate(dim_items)}
        for e, a in met_items:
            row[a] = _agg_eval(e, rs, skew)
        rows.append(row)
    if outer_sel != "*":
        out = {}
        for e, a in (x.rsplit(" AS ", 1) for x in _split_top(outer_sel)):
            fn, col = re.match(r"(MIN|MAX)\((\w+)\)", e).groups()
            vals = [r[col] for r in rows if r[col] is not None]
            out[a] = (min if fn == "MIN" else max)(vals) if vals else None
        return [out]
    om = re.match(r"ORDER BY (.+)", order, re.S)
    if om:
        spec = om.group(1)
        if "M0 DESC" in spec.upper():
            rows.sort(key=lambda r: (r["M0"] is None, -(r["M0"] or 0)))
        else:
            keys = [k.strip() for k in spec.split(",")]
            rows.sort(key=lambda r: tuple(str(r.get(k)) for k in keys))
    return rows


FakeSession._base = _base
