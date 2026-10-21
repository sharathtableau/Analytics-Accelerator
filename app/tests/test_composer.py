import json
import datetime as dt
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "streamlit"))
sys.path.insert(0, str(HERE))

from fake_snowflake import FakeSession, SV  # noqa: E402
from ai_services import Cortex  # noqa: E402
from composer import (DataContext, Governance, Validator, compose, compose_page, compose_tile,  # noqa: E402
                      compose_prompt, revalidate_tile)
from engine import Engine  # noqa: E402
from inventory import build_profile, infer_bindings  # noqa: E402
from semantic_catalog import describe_semantic_view  # noqa: E402
from semantic_query import SemanticQuery  # noqa: E402

APP = "WBR_DB.ANALYTICS_ENTERPRISE"
TODAY = dt.date(2025, 1, 2)
FEATURES = {"forecast": True, "top_insights": True, "complete": True}


class ComposerTests(unittest.TestCase):
    def setUp(self):
        self.s = FakeSession(fail_top_insights=False)
        self.model = describe_semantic_view(self.s, SV)
        self.b = infer_bindings(self.model)
        self.prof = build_profile(self.s, self.model, self.b, "executives", FEATURES, today=TODAY)
        distinct = SemanticQuery(self.s, self.model).distinct_counts([d.id for d in self.model.categorical_dimensions])
        self.ctx = DataContext(self.model, self.b, self.prof, distinct, "executives")
        self.cortex = Cortex(self.s, APP)
        self.cortex.model_in_use = "claude-sonnet-4-5"

    def test_prompt_describes_real_data(self):
        p = compose_prompt(self.ctx, "margin problems by region for the CFO")
        self.assertIn("ORDERS.PROFIT_RATIO", p)
        self.assertIn("NOT additive", p)
        self.assertIn("ORDERS.REGION | Region | 4 distinct values", p)
        self.assertIn("margin problems by region", p)
        self.assertIn("forecast_band", p)

    def test_compose_validates_repairs_and_drops(self):
        spec = compose(self.cortex, self.ctx, "margin health")
        gov = {e["tile"]: e for e in spec["governance"]}
        types = [c["type"] for p in spec["pages"] for c in p["components"]]
        self.assertEqual(spec["origin"], "cortex")
        self.assertIn("share_donut", types)
        self.assertIn("scatter", types)
        self.assertIn("heatmap", types)
        self.assertEqual(gov["Flow"]["action"], "dropped")                       # unknown tile type
        self.assertEqual(gov["Sales outlook"]["action"], "kept")                 # alias 'forecast' → forecast_band
        pareto = gov["Profit ratio concentration"]
        self.assertEqual(pareto["action"], "repaired")                           # ratio metric can't be pareto
        self.assertIn("not additive", pareto["reason"])
        kpis = spec["pages"][0]["components"][0]
        self.assertEqual(kpis["metrics"], ["ORDERS.SALES", "ORDERS.PROFIT", "ORDERS.PROFIT_RATIO"])  # resolved names
        detail = next(c for p in spec["pages"] for c in p["components"] if c["type"] == "detail_table")
        self.assertEqual(detail["metrics"], ["ORDERS.SALES"])                    # made-up metric removed
        ranked = gov["Sales ranking"]
        self.assertEqual(ranked["action"], "repaired")                           # unknown metric+dimension fixed
        self.assertEqual(gov["Unusual regions"]["action"], "dropped")            # page capped at MAX_TILES
        self.assertIn("kept it focused", gov["Unusual regions"]["reason"])
        all_ids = {m.id for m in self.model.metrics} | {d.id for d in self.model.dimensions}
        for p in spec["pages"]:
            for c in p["components"]:
                for k in ("metric_id", "metric2_id", "dimension", "dimension2"):
                    if c.get(k):
                        self.assertIn(c[k], all_ids)

    def test_every_composed_tile_renders(self):
        spec = compose(self.cortex, self.ctx, "margin health")
        results, facts = Engine(self.s, self.model, self.b, self.prof, self.cortex, None).build(spec)
        errors = {k: v for k, v in results.items() if v["status"] == "error"}
        self.assertEqual(errors, {})
        self.assertTrue(all(facts.values()))
        by_type = {c["type"]: results[f"{p['page_id']}/{c['component_id']}"]["data"]
                   for p in spec["pages"] for c in p["components"]}
        self.assertAlmostEqual(sum(s["share"] for s in by_type["share_donut"]["slices"]), 1.0, places=6)
        self.assertEqual(len(by_type["heatmap"]["rows"]), 3)
        self.assertTrue(by_type["scatter"]["points"])
        self.assertEqual(len(by_type["period_compare"]["labels"]), 3)

    def test_capability_gates(self):
        prof = build_profile(self.s, self.model, self.b, "executives", {"forecast": False}, today=TODAY)
        ctx = DataContext(self.model, self.b, prof, self.ctx.distinct, "executives")
        gov = Governance()
        tile = Validator(ctx, gov).tile({"type": "forecast_band", "title": "Outlook", "metric": "ORDERS.SALES"},
                                        "p", set())
        self.assertEqual(tile["type"], "trend_chart")
        self.assertIn("forecast not proven", gov.entries[0]["reason"])
        gov = Governance()
        tile = Validator(self.ctx, gov).tile({"type": "share_donut", "title": "x", "metric": "ORDERS.SALES",
                                              "dimension": "ORDERS.ORDER_DATE"}, "p", set())
        self.assertNotEqual(tile["dimension"], "ORDERS.ORDER_DATE")   # time dim is not categorical

    def test_add_tile_and_regenerate_page(self):
        spec = compose(self.cortex, self.ctx, "margin health")
        out = compose_tile(self.cortex, self.ctx, spec, "p1", "profit ratio share by category")
        self.assertEqual(out["tile"]["type"], "ranked_bar")          # ratio can't be a share donut
        self.assertNotIn(out["tile"]["component_id"],
                         [c["component_id"] for p in spec["pages"] for c in p["components"]])
        page = compose_page(self.cortex, self.ctx, spec, "p2", "focus on mix")["page"]
        self.assertEqual(page["page_id"], "p2")
        self.assertEqual([c["type"] for c in page["components"]], ["share_donut", "period_compare"])

    def test_user_edit_is_revalidated(self):
        spec = compose(self.cortex, self.ctx, "margin health")
        donut = next(c for c in spec["pages"][0]["components"] if c["type"] == "share_donut")
        new, gov = revalidate_tile(self.ctx, spec, "p1", donut, {"metric_id": "ORDERS.PROFIT"})
        self.assertEqual(new["metric_id"], "ORDERS.PROFIT")
        self.assertEqual(new["title"], "Profit share by region")
        with self.assertRaises(ValueError):
            revalidate_tile(self.ctx, spec, "p1", donut, {"type": "not_a_chart"})


if __name__ == "__main__":
    unittest.main()


class DeployManifestTests(unittest.TestCase):
    def test_every_local_module_is_deployed(self):
        import re
        root = HERE.parent / "streamlit"
        yml = (root / "snowflake.yml").read_text()
        for f in root.glob("*.py"):
            for mod in re.findall(r"^(?:from|import) (\w+)", f.read_text(), re.M):
                if (root / f"{mod}.py").exists():
                    self.assertIn(f"- {mod}.py", yml, f"{mod}.py missing from snowflake.yml artifacts")


class BreakdownValidationTests(unittest.TestCase):
    """Semantic views over several tables: a metric may only be split by related dimensions."""

    def setUp(self):
        self.s = FakeSession(fail_top_insights=False)
        self.model = describe_semantic_view(self.s, SV)
        # pretend PROFIT_RATIO lives in a table related only to date and region
        self.model.metric_dims = {"ORDERS.PROFIT_RATIO": {"ORDERS.ORDER_DATE", "ORDERS.REGION"}}
        self.b = infer_bindings(self.model)
        prof = build_profile(self.s, self.model, self.b, "executives", FEATURES, today=TODAY)
        distinct = SemanticQuery(self.s, self.model).distinct_counts([d.id for d in self.model.categorical_dimensions])
        self.ctx = DataContext(self.model, self.b, prof, distinct, "executives")

    def test_unrelated_dimension_is_repaired(self):
        gov = Governance()
        tile = Validator(self.ctx, gov).tile({"type": "ranked_bar", "title": "Ratio by category",
                                              "metric": "ORDERS.PROFIT_RATIO", "dimension": "ORDERS.CATEGORY"}, "p", set())
        self.assertEqual(tile["dimension"], "ORDERS.REGION")
        self.assertIn("not related", gov.entries[0]["reason"])

    def test_prompt_lists_valid_breakdowns(self):
        self.assertIn("Valid breakdowns", compose_prompt(self.ctx, "x"))

    def test_detail_table_drops_unsplittable_metric(self):
        gov = Governance()
        tile = Validator(self.ctx, gov).tile({"type": "detail_table", "title": "Detail",
                                              "metrics": ["ORDERS.SALES", "ORDERS.PROFIT_RATIO"],
                                              "dimensions": ["ORDERS.CATEGORY"]}, "p", set())
        self.assertEqual(tile["metrics"], ["ORDERS.SALES"])


class BuilderFeatureTests(unittest.TestCase):
    def setUp(self):
        self.s = FakeSession(fail_top_insights=False)
        self.model = describe_semantic_view(self.s, SV)
        self.b = infer_bindings(self.model)
        self.prof = build_profile(self.s, self.model, self.b, "executives", FEATURES, today=TODAY)
        distinct = SemanticQuery(self.s, self.model).distinct_counts([d.id for d in self.model.categorical_dimensions])
        self.ctx = DataContext(self.model, self.b, self.prof, distinct, "executives")
        self.cortex = Cortex(self.s, APP)
        self.cortex.model_in_use = "claude-sonnet-4-5"

    def test_filters_change_numbers(self):
        spec = compose(self.cortex, self.ctx, "x")
        allr, _ = Engine(self.s, self.model, self.b, self.prof, None, None).build(spec)
        west, _ = Engine(self.s, self.model, self.b, self.prof, None, None,
                         opts={"filters": {"ORDERS.REGION": ["West"]}}).build(spec)
        k_all = allr["p1/t1"]["data"]["items"][0]["current"]
        k_west = west["p1/t1"]["data"]["items"][0]["current"]
        self.assertLess(k_west, k_all)
        self.assertTrue(any("REGION IN ('West')" in q for q, _ in self.s.sqls))

    def test_compare_modes(self):
        comp = {"metrics": ["ORDERS.SALES"]}
        yoy = Engine(self.s, self.model, self.b, self.prof, opts={"compare": "yoy"}).kpi_grid(comp)["items"][0]
        self.assertEqual(yoy["delta"], yoy["yoy_change"])
        self.assertIn("Nov 2023", yoy["delta_label"])
        plan = Engine(self.s, self.model, self.b, self.prof, opts={"compare": "plan"}).kpi_grid(comp)["items"][0]
        self.assertEqual(plan["delta_label"], "vs plan")          # PLAN_SALES pairs with SALES
        self.assertIsNotNone(plan["base"])
        plan2 = Engine(self.s, self.model, self.b, self.prof, opts={"compare": "plan"}).kpi_grid(
            {"metrics": ["ORDERS.PROFIT"]})["items"][0]
        self.assertIn("no plan", plan2["delta_label"])

    def test_review_applies_choices(self):
        from composer import apply_review, metric_cards
        spec = compose(self.cortex, self.ctx, "x")
        cards = metric_cards(self.ctx, spec)
        self.assertTrue(any(c["recommended"] for c in cards))
        outline = [{"page_id": "p1", "label": "Headline", "tiles": ["t1", "t2"]}]
        out, gov = apply_review(self.ctx, spec, ["ORDERS.SALES", "ORDERS.QUANTITY"], outline)
        self.assertEqual([p["label"] for p in out["pages"]], ["Headline"])
        self.assertIn("ORDERS.QUANTITY", out["pages"][0]["components"][0]["metrics"])
        self.assertNotIn("ORDERS.PROFIT", out["pages"][0]["components"][0]["metrics"])

    def test_new_page_and_tile_edit(self):
        from composer import compose_new_page, edit_tile_nl
        spec = compose(self.cortex, self.ctx, "x")
        page = compose_new_page(self.cortex, self.ctx, spec, "customers")["page"]
        self.assertEqual(page["page_id"], "p3")
        tile = spec["pages"][0]["components"][2]
        out = edit_tile_nl(self.cortex, self.ctx, spec, "p1", tile, "make this a line chart")
        self.assertEqual(out["tile"]["type"], "trend_chart")
        self.assertEqual(out["tile"]["component_id"], tile["component_id"])


class AnomalyDetectionTests(unittest.TestCase):
    """C3: exceptions come from SNOWFLAKE.ML.ANOMALY_DETECTION (phase 2), z-score only as phase 1 / fallback."""
    COMP = {"type": "exception_table", "component_id": "x1", "title": "Unusual regions",
            "metric_id": "ORDERS.SALES", "dimension": "ORDERS.REGION", "state": "ready"}

    def setUp(self):
        self.s = FakeSession(fail_top_insights=False)
        self.model = describe_semantic_view(self.s, SV)
        self.b = infer_bindings(self.model)
        self.prof = build_profile(self.s, self.model, self.b, "executives", FEATURES, today=TODAY)
        self.cortex = Cortex(self.s, APP)
        self.cortex.model_in_use = "claude-sonnet-4-5"
        self.cortex.features = {"anomaly": True}

    def test_phase1_is_zscore_and_asks_for_ml(self):
        out = Engine(self.s, self.model, self.b, self.prof, self.cortex, None, {}, defer_ml=True)._exceptions(self.COMP)
        self.assertTrue(out["insights_pending"])
        self.assertFalse(out["ml"])
        self.assertIn("training", out["method"])

    def test_phase2_uses_snowflake_ml(self):
        cache = {}
        out = Engine(self.s, self.model, self.b, self.prof, self.cortex, None, cache, defer_ml=False)._exceptions(self.COMP)
        self.assertTrue(out["ml"])
        self.assertIn("95% prediction interval", out["method"])
        self.assertIn("ANOMALY_DETECTION", out["provenance"])
        self.assertTrue(all("lower" in r and "upper" in r for r in out["rows"]))
        sqls = " ".join(q for q, _ in self.s.sqls)
        self.assertIn("CREATE SNOWFLAKE.ML.ANOMALY_DETECTION IF NOT EXISTS", sqls)
        self.assertIn("SERIES_COLNAME => 'SEG'", sqls)
        self.assertIn("!DETECT_ANOMALIES", sqls)
        n = len(self.s.sqls)                                     # cached: no retraining on the next render
        Engine(self.s, self.model, self.b, self.prof, self.cortex, None, cache, defer_ml=False)._exceptions(self.COMP)
        self.assertFalse(any("DETECT_ANOMALIES" in q for q, _ in self.s.sqls[n:]))

    def test_falls_back_to_zscore_when_ml_unavailable(self):
        self.s.fail_anomaly = True
        out = Engine(self.s, self.model, self.b, self.prof, self.cortex, None, {}, defer_ml=False)._exceptions(self.COMP)
        self.assertFalse(out["ml"])
        self.assertIn("unavailable", out["method"])
        self.assertTrue(out["rows"])

    def test_feature_off_skips_ml(self):
        self.cortex.features = {"anomaly": False}
        out = Engine(self.s, self.model, self.b, self.prof, self.cortex, None, {}, defer_ml=True)._exceptions(self.COMP)
        self.assertFalse(out["insights_pending"])


class NarrativeTests(unittest.TestCase):
    """C4: page summaries come from Cortex AI_AGG over the page's governed fact rows; AI_COMPLETE is the fallback."""

    def setUp(self):
        self.s = FakeSession(fail_top_insights=False)
        self.cortex = Cortex(self.s, APP)
        self.cortex.model_in_use = "claude-sonnet-4-5"
        self.facts = ["Sales Nov 2024 $212K (+34.6% vs Nov 2023)", "West is 27% of sales", "Central below its norm"]

    def test_ai_agg_is_primary(self):
        out = self.cortex.narrative("Overview", "Are we growing?", self.facts, "executives")
        self.assertIn("AI_AGG", out["provenance"])
        self.assertIn("3 governed facts", out["text"])
        q, params = next((q, p) for q, p in self.s.sqls if "AI_AGG(" in q)
        self.assertIn("FLATTEN(INPUT => PARSE_JSON(?))", q)
        self.assertEqual(json.loads(params[0]), self.facts)

    def test_falls_back_to_ai_complete(self):
        self.s.fail_ai_agg = True
        out = self.cortex.narrative("Overview", "Are we growing?", self.facts, "executives")
        self.assertIn("AI_COMPLETE", out["provenance"])
        self.assertIn("AI_AGG unavailable", out["provenance"])


class KpiTrendToggleTests(unittest.TestCase):
    def setUp(self):
        self.s = FakeSession(fail_top_insights=False)
        self.model = describe_semantic_view(self.s, SV)
        self.b = infer_bindings(self.model)
        prof = build_profile(self.s, self.model, self.b, "executives", FEATURES, today=TODAY)
        distinct = SemanticQuery(self.s, self.model).distinct_counts([d.id for d in self.model.categorical_dimensions])
        self.ctx = DataContext(self.model, self.b, prof, distinct, "executives")

    def test_show_trend_defaults_on_and_can_be_turned_off(self):
        from composer import revalidate_tile
        tile = Validator(self.ctx, Governance()).tile({"type": "kpi_grid", "title": "KPIs",
                                                      "metrics": ["ORDERS.SALES", "ORDERS.PROFIT"]}, "p", set())
        self.assertTrue(tile["show_trend"])
        spec = {"pages": [{"page_id": "p1", "label": "P", "components": [tile]}]}
        new, _ = revalidate_tile(self.ctx, spec, "p1", tile, {"show_trend": False})
        self.assertFalse(new["show_trend"])
        self.assertEqual(new["metrics"], tile["metrics"])

    def test_toggle_phrase_detection(self):
        import re
        pat = re.compile(r"\b(remove|hide|drop|delete|no|without|turn off|show|add|bring back|turn on)\b[^.]{0,40}?"
                         r"\b(trends?|sparklines?|lines?|mini ?charts?)\b", re.I)
        self.assertEqual(pat.search("Remove the trend from bottom of all kpis").group(1).lower(), "remove")
        self.assertEqual(pat.search("bring back the sparklines").group(1).lower(), "bring back")
        self.assertIsNone(pat.search("make this a bar chart by region"))
