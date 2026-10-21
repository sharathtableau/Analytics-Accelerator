"""Custom metrics: strict formula parsing, SQL generation, model integration, storage, Cortex drafting."""
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "streamlit"))
sys.path.insert(0, str(HERE))

from fake_snowflake import FakeSession, SV  # noqa: E402
import custom_metrics as cm  # noqa: E402
from semantic_catalog import describe_semantic_view  # noqa: E402
from semantic_query import SemanticQuery  # noqa: E402
from store import Store  # noqa: E402


class FakeCortex:
    def __init__(self, reply):
        self.reply, self.prompts = reply, []

    def complete(self, prompt):
        self.prompts.append(prompt)
        return json.dumps(self.reply), "fake-model · 0.1s"


class ParseTests(unittest.TestCase):
    def setUp(self):
        self.m = describe_semantic_view(FakeSession(), SV)

    def test_valid_formulas(self):
        t = cm.parse("ORDERS.PROFIT / ORDERS.ORDER_COUNT", self.m)
        self.assertEqual(cm.bases(t), ["ORDERS.PROFIT", "ORDERS.ORDER_COUNT"])
        self.assertEqual(cm.render(t, lambda i: i), "DIV0(ORDERS.PROFIT, ORDERS.ORDER_COUNT)")
        t = cm.parse("(sales - profit) * 1.5 + -quantity", self.m)      # bare names, case-insensitive
        self.assertEqual(cm.render(t, lambda i: i.split(".")[1]),
                         "(((SALES - PROFIT) * 1.5) + (-QUANTITY))")
        self.assertEqual(cm.show(cm.parse("PROFIT ÷ SALES", self.m), lambda i: i.split(".")[1].title()),
                         "Profit ÷ Sales")

    def test_rejects_anything_but_metrics_numbers_and_operators(self):
        for bad in ["SALES; DROP TABLE X", "SUM(SALES)", "SALES -- x", "'1'", "SALES)", "(SALES", "SALES +",
                    "1 + 2", "ORDERS.REGION", "FOO / SALES", "SALES /* x */", "SALES || PROFIT", ""]:
            with self.assertRaises(cm.FormulaError, msg=bad):
                cm.parse(bad, self.m)

    def test_length_and_complexity_limits(self):
        with self.assertRaises(cm.FormulaError):
            cm.parse(" + ".join(["SALES"] * 60), self.m)

    def test_additivity(self):
        self.assertTrue(cm.additive(cm.parse("SALES - PROFIT", self.m), self.m))
        self.assertFalse(cm.additive(cm.parse("PROFIT / SALES", self.m), self.m))
        self.assertFalse(cm.additive(cm.parse("SALES + PROFIT_RATIO", self.m), self.m))


class ModelAndQueryTests(unittest.TestCase):
    def setUp(self):
        self.s = FakeSession()
        self.m = describe_semantic_view(self.s, SV)
        cm.apply(self.m, [{"name": "PROFIT_PER_ORDER", "formula": "ORDERS.PROFIT / ORDERS.ORDER_COUNT",
                           "label": "Profit per order", "created_by": "ANNA"},
                          {"name": "BROKEN", "formula": "ORDERS.GONE / ORDERS.SALES"},
                          {"name": "SALES", "formula": "ORDERS.PROFIT"}])          # clashes with a metric name

    def test_apply_adds_valid_metrics_and_reports_the_rest(self):
        f = self.m.field("PROFIT_PER_ORDER", ("metric",))
        self.assertEqual(f.label, "Profit per order")
        self.assertFalse(f.additive)
        self.assertIn("Custom metric (not governed)", f.comment)
        self.assertEqual(self.m.metric_info[f.id]["origin"], "custom")
        self.assertEqual(sorted(e["name"] for e in self.m.custom_errors), ["BROKEN", "SALES"])

    def test_apply_is_idempotent(self):
        rows = [{"name": "PROFIT_PER_ORDER", "formula": "ORDERS.PROFIT / ORDERS.ORDER_COUNT"}]
        cm.apply(self.m, rows)
        cm.apply(self.m, rows)
        self.assertEqual(sum(1 for x in self.m.metrics if x.name == "PROFIT_PER_ORDER"), 1)
        cm.apply(self.m, [])
        self.assertFalse(any(x.name == "PROFIT_PER_ORDER" for x in self.m.metrics))

    def test_query_computes_formula_over_semantic_view(self):
        q = SemanticQuery(self.s, self.m)
        ref = self.m.field("PROFIT_PER_ORDER", ("metric",)).ref
        sql = q.sv(["ORDERS.REGION AS D0"], [f"{ref} AS M0"])
        self.assertIn("SEMANTIC_VIEW(", sql)
        self.assertIn("DIV0(AA_B0, AA_B1) AS M0", sql)
        self.assertIn("EXCLUDE (AA_B0, AA_B1)", sql)
        t = self.m.time_dimensions[0].id
        cal = q.calendar(t, "PROFIT_PER_ORDER", "month")
        rows = q.by_dim(t, ["PROFIT_PER_ORDER", "ORDERS.PROFIT", "ORDERS.ORDER_COUNT"], ["ORDERS.REGION"],
                        cal.current_start, cal.end_exclusive)
        for r in rows:
            self.assertAlmostEqual(r["PROFIT_PER_ORDER"], r["ORDERS.PROFIT"] / r["ORDERS.ORDER_COUNT"])

    def test_dimensions_are_the_intersection_of_the_bases(self):
        dims = cm.dims_for(self.m, {"ORDERS.PROFIT": {"A", "B"}, "ORDERS.ORDER_COUNT": {"B", "C"}})
        self.assertEqual(dims["PROFIT_PER_ORDER"], {"B"})
        self.assertEqual(cm.dims_for(self.m, {}), {})              # no map = every pair allowed, as before

    def test_governed_snippet(self):
        snip = cm.governed_snippet(self.m, self.m.field("PROFIT_PER_ORDER", ("metric",)))
        self.assertIn("PROFIT_PER_ORDER AS DIV0(ORDERS.PROFIT, ORDERS.ORDER_COUNT)", snip)


class DefineTests(unittest.TestCase):
    def setUp(self):
        self.m = describe_semantic_view(FakeSession(), SV)

    def test_typed_formula_needs_no_ai(self):
        c = FakeCortex({})
        out = cm.define(c, self.m, "Profit per order = ORDERS.PROFIT / ORDERS.ORDER_COUNT")
        self.assertEqual((out["name"], out["label"], out["origin"]), ("PROFIT_PER_ORDER", "Profit per order", "formula"))
        self.assertEqual(c.prompts, [])

    def test_typed_formula_with_unknown_metric_gets_its_own_error(self):
        with self.assertRaisesRegex(cm.FormulaError, "FOO"):
            cm.define(FakeCortex({}), self.m, "ORDERS.SALES / FOO")

    def test_english_goes_through_cortex_and_is_validated(self):
        c = FakeCortex({"name": "profit per order", "label": "Profit per Order",
                        "formula": "ORDERS.PROFIT / ORDERS.ORDER_COUNT", "theme": "Profitability"})
        out = cm.define(c, self.m, "average profit on each order")
        self.assertEqual((out["name"], out["origin"], out["theme"]), ("PROFIT_PER_ORDER", "cortex", "Profitability"))
        self.assertIn("ORDERS.ORDER_COUNT", c.prompts[0])

    def test_cortex_output_is_never_trusted(self):
        with self.assertRaises(cm.FormulaError):
            cm.define(FakeCortex({"name": "X", "formula": "ORDERS.SALES); DROP TABLE T; --"}), self.m, "anything")
        with self.assertRaisesRegex(cm.FormulaError, "filter"):
            cm.define(FakeCortex({"error": "It needs a filter on region."}), self.m, "east sales only")

    def test_name_clash_is_refused(self):
        with self.assertRaisesRegex(cm.FormulaError, "already exists"):
            cm.define(FakeCortex({}), self.m, "SALES = ORDERS.PROFIT * 2")


class StoreTests(unittest.TestCase):
    def test_save_and_load_per_view(self):
        st = Store(FakeSession(), "WBR_DB.ANALYTICS_ENTERPRISE")
        st.ready = True
        st.save_custom_metric(SV, {"name": "PROFIT_PER_ORDER", "label": "Profit per order",
                                   "formula": "(ORDERS.PROFIT / ORDERS.ORDER_COUNT)", "origin": "cortex"}, "ANNA")
        rows = st.load_custom_metrics(SV)
        self.assertEqual([(r["name"], r["created_by"]) for r in rows], [("PROFIT_PER_ORDER", "ANNA")])
        self.assertEqual(st.load_custom_metrics("OTHER.DB.SV"), [])


if __name__ == "__main__":
    unittest.main()
