"""Chart drop A: bars + line, treemap, progress gauge, P&L table (validator, compute, validation, headlines)."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "streamlit"))
sys.path.insert(0, str(HERE))

from fake_snowflake import FakeSession, SV  # noqa: E402
from composer import DataContext, Governance, validate_layout  # noqa: E402
from engine import Engine  # noqa: E402
from inventory import build_profile, infer_bindings  # noqa: E402
from semantic_catalog import describe_semantic_view  # noqa: E402
from semantic_query import SemanticQuery  # noqa: E402
from store import Store  # noqa: E402
from test_composer import APP, FEATURES, TODAY  # noqa: E402
import validation as V  # noqa: E402

RAW = {"pages": [{"label": "Charts", "tiles": [
    {"type": "combo_chart", "title": "Sales and margin", "metric": "ORDERS.SALES"},
    {"type": "treemap", "title": "Sales mix", "metric": "ORDERS.SALES", "dimension": "ORDERS.CATEGORY"},
    {"type": "gauge", "title": "Sales to the full year", "metric": "ORDERS.SALES"},
    {"type": "pnl_table", "title": "KPIs by region", "dimension": "ORDERS.REGION",
     "metrics": ["ORDERS.SALES", "ORDERS.PROFIT", "ORDERS.PROFIT_RATIO", "ORDERS.QUANTITY"]},
]}]}


class ChartTileTests(unittest.TestCase):
    def setUp(self):
        self.s = FakeSession()
        self.model = describe_semantic_view(self.s, SV)
        self.b = infer_bindings(self.model)
        self.distinct = SemanticQuery(self.s, self.model).distinct_counts(
            [d.id for d in self.model.categorical_dimensions])

    def layout(self, raw, aud="executives"):
        prof = build_profile(self.s, self.model, self.b, aud, FEATURES, today=TODAY)
        gov = Governance()
        pages = validate_layout(DataContext(self.model, self.b, prof, self.distinct, aud), raw, gov)
        return {"pages": pages}, gov, prof

    def run_all(self, aud="executives", **fake):
        for k, v in fake.items():
            setattr(self.s, k, v)
        spec, _, prof = self.layout(RAW, aud)
        cache = {}
        e = Engine(self.s, self.model, self.b, prof, None, Store(self.s, APP), cache)
        res, facts = e.build(spec)
        e2 = Engine(self.s, self.model, self.b, prof, None, Store(self.s, APP), cache)
        rep = V.Validator(self.s, e2, V.Physical.describe(self.s, SV)).run(
            spec, [p["page_id"] for p in spec["pages"]], res, e.tile_keys, cache)
        return spec, res, facts, rep

    def by_type(self, spec, res):
        return {c["type"]: res[f"p1/{c['component_id']}"] for c in spec["pages"][0]["components"]}

    # ---------------------------------------------------------------- validator
    def test_validator_keeps_and_repairs(self):
        spec, gov, _ = self.layout(RAW)
        comps = {c["type"]: c for c in spec["pages"][0]["components"]}
        self.assertEqual(set(comps), {"combo_chart", "treemap", "gauge", "pnl_table"})
        self.assertEqual(comps["combo_chart"]["metric2_id"], "ORDERS.PROFIT_RATIO")    # a rate is picked for the line
        self.assertEqual(comps["pnl_table"]["width"], 12)
        self.assertEqual(len(comps["pnl_table"]["metrics"]), 4)

    def test_validator_downgrades_what_does_not_fit(self):
        raw = {"pages": [{"label": "X", "tiles": [
            {"type": "treemap", "title": "a", "metric": "ORDERS.PROFIT_RATIO", "dimension": "ORDERS.CATEGORY"},
            {"type": "gauge", "title": "b", "metric": "ORDERS.PROFIT_RATIO"},
            {"type": "treemap", "title": "c", "metric": "ORDERS.SALES", "dimension": "ORDERS.REGION",
             "dimension2": "ORDERS.NOPE"},
            {"type": "pie_of_doom", "title": "d"},
        ]}]}
        spec, gov, _ = self.layout(raw)
        types = [c["type"] for c in spec["pages"][0]["components"]]
        self.assertEqual(types, ["ranked_bar", "trend_chart", "treemap"])     # ratio: no area, no running total
        self.assertNotIn("dimension2", spec["pages"][0]["components"][2])
        reasons = " ".join(e["reason"] for e in gov.entries)
        self.assertIn("not additive", reasons)
        self.assertIn("running total is meaningless", reasons)
        self.assertIn("one level", reasons)

    def test_aliases(self):
        raw = {"pages": [{"label": "X", "tiles": [{"type": "waterfall_nope"}, {"type": "pnl", "title": "p",
                                                                                "dimension": "ORDERS.REGION"},
                                                  {"type": "bar_line", "title": "c", "metric": "ORDERS.SALES",
                                                   "metric2": "ORDERS.PROFIT"}]}]}
        spec, _, _ = self.layout(raw)
        comps = spec["pages"][0]["components"]
        self.assertEqual([c["type"] for c in comps], ["pnl_table", "combo_chart"])
        self.assertEqual(comps[1]["metric2_id"], "ORDERS.PROFIT")             # an explicit valid choice is kept

    # ---------------------------------------------------------------- compute
    def test_tiles_compute(self):
        spec, res, facts, _ = self.run_all()
        t = self.by_type(spec, res)
        for k, r in t.items():
            self.assertEqual(r["status"], "ready", (k, r.get("error")))
            self.assertTrue(r["data"]["headline"], k)
        c = t["combo_chart"]["data"]
        self.assertEqual(len(c["points"]), 13)
        self.assertEqual(c["line_kind"], "percent")
        tm = t["treemap"]["data"]
        self.assertAlmostEqual(sum(g["share"] for g in tm["groups"]), 1.0)
        self.assertAlmostEqual(tm["shown"] + tm["excluded"], tm["total"], places=4)
        g = t["gauge"]["data"]
        self.assertEqual(g["target_label"], "plan")
        self.assertAlmostEqual(g["progress"], g["actual"] / g["target"])
        self.assertAlmostEqual(g["projected"], g["target"] * g["actual"] / g["expected"])
        p = t["pnl_table"]["data"]
        self.assertEqual([r["label"] for r in p["rows"]], ["Sales", "Profit", "Profit Ratio", "Quantity"])
        ratio = p["rows"][2]["total"]
        self.assertAlmostEqual(ratio["change"], ratio["value"] - ratio["base"])     # rates change in points
        self.assertTrue(any("full-year plan" in f for f in facts["p1"]))

    def test_pnl_compares_to_last_year_when_asked(self):
        spec, _, prof = self.layout(RAW)
        e = Engine(self.s, self.model, self.b, prof, None, None, {}, opts={"compare": "yoy"})
        comp = next(c for c in spec["pages"][0]["components"] if c["type"] == "pnl_table")
        d = e.pnl_table(comp)
        self.assertEqual(d["compare"], "yoy")
        self.assertEqual(d["base_label"], prof.calendar.label(prof.calendar.yoy_start))

    # ---------------------------------------------------------------- validation
    def test_every_new_tile_validates(self):
        spec, res, _, rep = self.run_all()
        for cid, tile in rep["tiles"].items():
            checks = {c["id"]: c for c in tile["checks"]}
            self.assertEqual(checks["QA-01"]["status"], "pass", (cid, checks["QA-01"]))
            self.assertNotEqual(tile["status"], "mismatch", (cid, tile))
        types = {c["component_id"]: c["type"] for c in spec["pages"][0]["components"]}
        qa = {types[cid.split("/")[1]]: {c["id"]: c for c in t["checks"]} for cid, t in rep["tiles"].items()}
        for t in ("treemap", "gauge", "pnl_table"):
            self.assertEqual(qa[t]["QA-02"]["status"], "pass", (t, qa[t]["QA-02"]))
        self.assertEqual(qa["treemap"]["QA-03"]["status"], "pass")
        self.assertEqual(qa["pnl_table"]["QA-03"]["status"], "pass")

    def test_planted_error_reaches_new_tiles(self):
        _, _, _, rep = self.run_all(base_skew={"SALES": 1.001})
        bad = [cid for cid, t in rep["tiles"].items() if t["status"] == "mismatch"]
        self.assertGreaterEqual(len(bad), 3)

    def test_display_arithmetic_tamper_is_caught(self):
        spec, res, _, _ = self.run_all()
        t = self.by_type(spec, res)
        e = Engine(self.s, self.model, self.b, self.layout(RAW)[2], None, None, {})
        v = V.Validator(self.s, e, None)
        g = dict(t["gauge"]["data"], projected=t["gauge"]["data"]["projected"] * 1.1)
        self.assertEqual(v.qa02({"type": "gauge"}, g)["status"], "mismatch")
        tm = t["treemap"]["data"]
        tm2 = dict(tm, groups=[dict(tm["groups"][0], share=0.99)] + tm["groups"][1:])
        self.assertEqual(v.qa02({"type": "treemap"}, tm2)["status"], "mismatch")


if __name__ == "__main__":
    unittest.main()
