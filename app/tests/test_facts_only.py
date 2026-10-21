"""Facts-only semantic views (e.g. SANDBOX.BI.INFERA_SEMANTIC_VIEW: facts, no metrics, two unrelated tables)."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "streamlit"))
sys.path.insert(0, str(HERE))

import home  # noqa: E402
from semantic_catalog import describe_semantic_view, metric_dimension_map  # noqa: E402
from semantic_query import SemanticQuery  # noqa: E402

FQN = "SANDBOX.BI.INFERA_SEMANTIC_VIEW"


def rows():
    out = [{"object_kind": "TABLE", "object_name": t, "parent_entity": None, "property": "BASE_TABLE_NAME",
            "property_value": t} for t in ("VW_HEALTHCARE_MASTER", "VW_RETAIL_MASTER")]

    def add(kind, table, name, dtype):
        out.append({"object_kind": kind, "object_name": name, "parent_entity": table, "property": "DATA_TYPE",
                    "property_value": dtype})
        out.append({"object_kind": kind, "object_name": name, "parent_entity": table, "property": "EXPRESSION",
                    "property_value": name})
    add("DIMENSION", "VW_RETAIL_MASTER", "ORDER_DATE", "DATE")
    add("DIMENSION", "VW_RETAIL_MASTER", "REGION", "VARCHAR(50)")
    add("FACT", "VW_RETAIL_MASTER", "SALES_AMOUNT", "NUMBER(18,2)")
    add("FACT", "VW_RETAIL_MASTER", "ORDER_ID", "NUMBER(38,0)")
    add("FACT", "VW_RETAIL_MASTER", "DISCOUNT_PCT", "FLOAT")
    add("FACT", "VW_RETAIL_MASTER", "SHIP_MODE", "VARCHAR(20)")
    add("DIMENSION", "VW_HEALTHCARE_MASTER", "ADMIT_DATE", "DATE")
    add("DIMENSION", "VW_HEALTHCARE_MASTER", "DEPARTMENT", "VARCHAR(50)")
    add("FACT", "VW_HEALTHCARE_MASTER", "BILLING_AMOUNT", "NUMBER(18,2)")
    return out


class Row(dict):
    def as_dict(self):
        return dict(self)


class Stub:
    def __init__(self):
        self.sqls = []

    def sql(self, text, params=None):
        self.sqls.append(text)
        stub = self

        class R:
            def collect(self_inner):
                if text.upper().startswith("DESCRIBE SEMANTIC VIEW"):
                    return [Row(r) for r in rows()]
                if text.startswith("SELECT COUNT(") and "VW_RETAIL_MASTER.SALES_AMOUNT" in text:
                    # profile: facts in order DISCOUNT_PCT, ORDER_ID, SALES_AMOUNT, SHIP_MODE
                    return [Row({"N0": 100, "D0": 30, "L0": 0.0, "H0": 0.35, "A0": 0.08,
                                 "N1": 100, "D1": 100, "L1": 1, "H1": 100, "A1": 50.5,
                                 "N2": 100, "D2": 97, "L2": 5.0, "H2": 900.0, "A2": 120.0,
                                 "N3": 100, "D3": 3})]
                if "MIN(D)" in text:
                    return [Row({"MIN_D": "2025-01-01", "MAX_D": "2026-09-30"})]
                return []
        return R()


class FactsOnlyTests(unittest.TestCase):
    def setUp(self):
        self.s = Stub()

    def test_facts_become_adhoc_metrics(self):
        m = describe_semantic_view(self.s, FQN)
        self.assertTrue(m.facts_mode)
        names = {x.name: x.expression for x in m.metrics}
        self.assertEqual(names["SALES_AMOUNT"], "SUM(VW_RETAIL_MASTER.SALES_AMOUNT)")
        self.assertEqual(names["ORDER_ID_COUNT"], "COUNT(DISTINCT VW_RETAIL_MASTER.ORDER_ID)")
        self.assertEqual(names["AVG_DISCOUNT_PCT"], "AVG(VW_RETAIL_MASTER.DISCOUNT_PCT)")
        self.assertNotIn("SHIP_MODE", names)                       # text fact is not a measure
        self.assertTrue(m.field("VW_RETAIL_MASTER.SALES_AMOUNT", ("metric",)).additive)

    def test_scope_and_metric_dims(self):
        m = describe_semantic_view(self.s, FQN + "#VW_RETAIL_MASTER")
        self.assertEqual(m.fqn, FQN)                                # SQL still targets the real view
        self.assertEqual(m.source_id, FQN + "#VW_RETAIL_MASTER")
        self.assertEqual({x.entity for x in m.metrics}, {"VW_RETAIL_MASTER"})
        dims = metric_dimension_map(self.s, m)
        self.assertEqual(dims["VW_RETAIL_MASTER.SALES_AMOUNT"],
                         {"VW_RETAIL_MASTER.ORDER_DATE", "VW_RETAIL_MASTER.REGION"})

    def test_standard_sql_with_adhoc_metrics(self):
        m = describe_semantic_view(self.s, FQN + "#VW_RETAIL_MASTER")
        q = SemanticQuery(self.s, m)
        sql = q.sv([q.trunc(q.dim("VW_RETAIL_MASTER.ORDER_DATE"), "month"), "VW_RETAIL_MASTER.REGION AS SEG"],
                   ["VW_RETAIL_MASTER.SALES_AMOUNT AS M0", "VW_RETAIL_MASTER.ORDER_ID_COUNT AS M1"],
                   "VW_RETAIL_MASTER.REGION IN ('West')")
        self.assertEqual(sql, "(SELECT DATE_TRUNC('month', VW_RETAIL_MASTER.ORDER_DATE) AS PERIOD, "
                              "VW_RETAIL_MASTER.REGION AS SEG, SUM(VW_RETAIL_MASTER.SALES_AMOUNT) AS M0, "
                              "COUNT(DISTINCT VW_RETAIL_MASTER.ORDER_ID) AS M1 FROM SANDBOX.BI.INFERA_SEMANTIC_VIEW "
                              "WHERE VW_RETAIL_MASTER.REGION IN ('West') GROUP BY DATE_TRUNC('month', "
                              "VW_RETAIL_MASTER.ORDER_DATE), VW_RETAIL_MASTER.REGION)")
        self.assertNotIn("SEMANTIC_VIEW(", sql)
        cal = q.calendar("VW_RETAIL_MASTER.ORDER_DATE", "VW_RETAIL_MASTER.SALES_AMOUNT", "month")
        self.assertEqual(cal.grain, "month")

    def test_home_lists_one_dataset_per_table(self):
        cat = home.build_catalog([{"fqn": FQN, "name": "INFERA_SEMANTIC_VIEW"}],
                                 lambda f: describe_semantic_view(self.s, f),
                                 {FQN + "#VW_RETAIL_MASTER": "Infera Retail"}, [])
        by = {c["fqn"]: c for c in cat}
        self.assertEqual(set(by), {FQN + "#VW_HEALTHCARE_MASTER", FQN + "#VW_RETAIL_MASTER"})
        self.assertTrue(by[FQN + "#VW_RETAIL_MASTER"]["featured"])
        self.assertEqual(by[FQN + "#VW_RETAIL_MASTER"]["label"], "Infera Retail")
        self.assertEqual(by[FQN + "#VW_HEALTHCARE_MASTER"]["label"], "Infera · Healthcare Master")
        self.assertTrue(all(c["adhoc"] for c in cat))
        self.assertEqual(cat[0]["fqn"], FQN + "#VW_RETAIL_MASTER")   # featured first


class StubCortex:
    def __init__(self, payload=None, fail=False):
        self.payload, self.fail = payload, fail

    def complete(self, prompt):
        self.prompt = prompt
        if self.fail:
            raise RuntimeError("Cortex down")
        import json
        return json.dumps(self.payload), "stub-model"


class MetricDraftTests(unittest.TestCase):
    def setUp(self):
        self.s = Stub()

    def test_cortex_draft_is_profiled_validated_and_applied(self):
        import metric_drafter
        m = describe_semantic_view(self.s, FQN)
        cx = StubCortex({"tables": {"VW_RETAIL_MASTER": {
            "metrics": [{"name": "TOTAL_SALES", "agg": "SUM", "fact": "SALES_AMOUNT", "comment": "Net sales.",
                         "why": "amount, 5-900", "theme": "Sales"},
                        {"name": "ORDERS", "agg": "SUM", "fact": "ORDER_ID", "comment": "Orders."},
                        {"name": "AVG_DISCOUNT", "agg": "AVG", "fact": "DISCOUNT_PCT", "comment": "Avg discount."},
                        {"name": "BAD", "agg": "SUM", "fact": "SHIP_MODE"},
                        {"name": "GHOST", "agg": "SUM", "fact": "NOPE"}],
            "ratios": [{"name": "AVG_ORDER_VALUE", "numerator": "TOTAL_SALES", "denominator": "ORDERS",
                        "comment": "Sales per order."},
                       {"name": "BROKEN", "numerator": "TOTAL_SALES", "denominator": "MISSING"}]}}})
        d = metric_drafter.draft(cx, self.s, m)
        self.assertEqual(d["origin"], "cortex")
        self.assertEqual(d["profiled_facts"], 4)
        self.assertIn("looks_like", cx.prompt)                       # Cortex saw the data profile
        self.assertIn("identifier", cx.prompt)                       # ORDER_ID recognised from the data
        actions = {n["item"]: n["action"] for n in d["notes"]}
        self.assertEqual(actions["ORDERS"], "repaired")               # SUM of an id -> COUNT DISTINCT
        self.assertEqual(actions["BAD"], "dropped")
        self.assertEqual(actions["GHOST"], "dropped")
        self.assertEqual(actions["BROKEN"], "dropped")
        metric_drafter.apply(m, d)
        names = {x.name for x in m.metrics}
        self.assertEqual(names, {"TOTAL_SALES", "ORDERS", "AVG_DISCOUNT", "AVG_ORDER_VALUE"})
        q = SemanticQuery(self.s, m)
        sql = q.sv(["VW_RETAIL_MASTER.REGION AS D0"], ["VW_RETAIL_MASTER.AVG_ORDER_VALUE AS M0"])
        self.assertIn("DIV0(SUM(VW_RETAIL_MASTER.SALES_AMOUNT), COUNT(DISTINCT VW_RETAIL_MASTER.ORDER_ID)) AS M0", sql)
        self.assertFalse(m.field("VW_RETAIL_MASTER.AVG_ORDER_VALUE", ("metric",)).additive)
        self.assertEqual(m.metric_info["VW_RETAIL_MASTER.TOTAL_SALES"]["why"], "amount, 5-900")
        from semantic_catalog import metrics_ddl, scope_model
        ddl = metrics_ddl(m)
        self.assertIn("VW_RETAIL_MASTER.AVG_ORDER_VALUE AS DIV0(VW_RETAIL_MASTER.TOTAL_SALES, VW_RETAIL_MASTER.ORDERS)", ddl)
        sm = scope_model(m, "VW_RETAIL_MASTER")
        self.assertIn(("RATIO", "VW_RETAIL_MASTER.TOTAL_SALES", "VW_RETAIL_MASTER.ORDERS"), sm.virtual.values())

    def test_rules_when_cortex_is_down(self):
        import metric_drafter
        m = describe_semantic_view(self.s, FQN)
        d = metric_drafter.draft(StubCortex(fail=True), self.s, m)
        self.assertEqual(d["origin"], "rules")
        retail = {x["name"]: x["agg"] for x in d["tables"]["VW_RETAIL_MASTER"]["metrics"]}
        self.assertEqual(retail["ORDER_ID_COUNT"], "COUNT_DISTINCT")
        self.assertEqual(retail["AVG_DISCOUNT_PCT"], "AVG")          # profile says 0-1 fraction
        self.assertEqual(retail["SALES_AMOUNT"], "SUM")


if __name__ == "__main__":
    unittest.main()


class HomeFeaturedTests(unittest.TestCase):
    def test_every_featured_view_gets_ideas_and_time_dimensions_parse(self):
        import json
        s = Stub()
        orig = rows

        def rows_time():   # Snowflake may report dates as TIME_DIMENSION
            return [dict(r, object_kind="TIME_DIMENSION") if r["object_name"] == "ORDER_DATE" else r for r in orig()]
        globals()["rows"] = rows_time
        try:
            m = describe_semantic_view(s, FQN + "#VW_RETAIL_MASTER")
        finally:
            globals()["rows"] = orig
        self.assertEqual([d.name for d in m.time_dimensions], ["ORDER_DATE"])

        cat = [{"fqn": "A.B.HARBOR", "label": "Harborline", "featured": True, "test_like": False, "comment": "",
                "metrics": [{"id": "S.NET_SALES", "label": "Net Sales"}], "dimensions": [{"id": "S.REGION", "label": "Region"}]},
               {"fqn": FQN + "#VW_RETAIL_MASTER", "label": "Infera Retail", "featured": True, "test_like": False,
                "comment": "", "metrics": [{"id": "V.SALES_AMOUNT", "label": "Sales Amount"}],
                "dimensions": [{"id": "V.REGION", "label": "Region"}]}]

        class Cx:   # Cortex ignores the second featured view
            def complete(self, prompt):
                self.prompt = prompt
                return json.dumps({"suggestions": [{"audience": a, "title": f"Idea {a} {i}", "semantic_view": "A.B.HARBOR",
                                                    "metrics": ["Net Sales"]} for a in ("executives", "managers", "daily_operations")
                                                   for i in range(3)]}), "x"
        cx = Cx()
        ideas = home.ai_suggestions(cx, cat)
        self.assertIn("EVERY FEATURED view", cx.prompt)
        self.assertIn("6 dashboards for EACH audience", cx.prompt)
        for aud in ("executives", "managers", "daily_operations"):
            self.assertTrue(any(i["audience"] == aud and i["semantic_view"] == FQN + "#VW_RETAIL_MASTER" for i in ideas), aud)
