import datetime as dt
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "streamlit"))
sys.path.insert(0, str(HERE))

from fake_snowflake import FakeSession, SV  # noqa: E402
from ai_services import Cortex  # noqa: E402
from agent_service import ask_agent, create_agent, find_agents  # noqa: E402
from engine import Engine  # noqa: E402
from inventory import Bindings, build_profile, infer_bindings, validate_bindings  # noqa: E402
from layout_catalog import bind_template, picker_options, select_template  # noqa: E402
from semantic_catalog import describe_semantic_view, list_semantic_views  # noqa: E402
from store import Store  # noqa: E402

APP = "WBR_DB.ANALYTICS_ENTERPRISE"
TODAY = dt.date(2025, 1, 2)
FEATURES = {"forecast": True, "top_insights": True, "complete": True}


class BackendTests(unittest.TestCase):
    def setUp(self):
        self.s = FakeSession()
        self.model = describe_semantic_view(self.s, SV)
        self.b = infer_bindings(self.model)

    def test_discovery_and_describe(self):
        views = list_semantic_views(self.s, ["WBR_DB.PUBLIC", "WBR_DB.PIPELINE_DEMO"])
        self.assertEqual(views[0]["fqn"], SV)
        self.assertEqual([d.name for d in self.model.time_dimensions], ["ORDER_DATE"])
        self.assertTrue(self.model.field("ORDERS.SALES").additive)
        self.assertFalse(self.model.field("ORDERS.PROFIT_RATIO").additive)
        self.assertFalse(self.model.field("ORDERS.ORDER_COUNT").additive)

    def test_inferred_bindings_are_valid(self):
        self.assertEqual(self.b.primary_metric, "ORDERS.SALES")
        self.assertEqual(self.b.segment_dimension, "ORDERS.SEGMENT")
        self.assertEqual(self.b.region_dimension, "ORDERS.REGION")
        self.assertEqual(validate_bindings(self.model, self.b), [])
        bad = Bindings.from_dict({**self.b.as_dict(), "primary_metric": "ORDERS.DROP_TABLE"})
        self.assertTrue(validate_bindings(self.model, bad))

    def test_profile_capabilities_are_explained(self):
        prof = build_profile(self.s, self.model, self.b, "executives", FEATURES, today=TODAY)
        caps = prof.capabilities
        self.assertTrue(caps["comparable_time_series"].granted)
        self.assertTrue(caps["stable_segment_hierarchy"].granted)
        self.assertTrue(caps["reconciled_driver_bridge"].granted)
        self.assertFalse(caps["plan_versioned"].granted)
        self.assertEqual(prof.calendar.current_start, dt.date(2024, 11, 1))  # Dec incomplete (data to 29 Dec)
        self.assertIn("reason", prof.as_dict()["capabilities"]["target"])

    def test_ops_layouts_blocked_for_stale_data(self):
        prof = build_profile(self.s, self.model, self.b, "daily_operations", FEATURES,
                             today=dt.date(2026, 9, 30))
        opts = picker_options("daily_operations", prof.inventory())
        self.assertFalse(any(o["selectable"] for o in opts))

    def test_every_new_layout_renders_all_components(self):
        cortex = Cortex(self.s, APP)
        cortex.model_in_use = "claude-sonnet-4-5"
        store = Store(self.s, APP)
        for audience, tid in (("executives", "exec_growth_baseline"), ("managers", "manager_segment_scorecard"),
                              ("weekly_business_review", "wbr_weekly_performance")):
            prof = build_profile(self.s, self.model, self.b, audience, FEATURES, today=TODAY)
            sel = select_template(audience, prof.inventory(), user_selected_template_id=tid)
            self.assertEqual(sel.status, "ready", (audience, sel.message))
            spec = bind_template(sel.template, prof.inventory())
            results, facts = Engine(self.s, self.model, self.b, prof, cortex, store).build(spec)
            errors = {k: v for k, v in results.items() if v["status"] == "error"}
            self.assertEqual(errors, {}, audience)
            self.assertTrue(any(facts.values()))

    def test_all_ready_catalog_layouts_render(self):
        from layout_catalog import AUDIENCES, list_templates
        cortex = Cortex(self.s, APP)
        cortex.model_in_use = "claude-sonnet-4-5"
        rendered = 0
        for audience in AUDIENCES:
            prof = build_profile(self.s, self.model, self.b, audience, FEATURES, today=TODAY)
            for tpl in list_templates(audience):
                sel = select_template(audience, prof.inventory(), user_selected_template_id=tpl.template_id)
                if sel.status != "ready":
                    continue
                spec = bind_template(sel.template, prof.inventory())
                results, _ = Engine(self.s, self.model, self.b, prof, cortex, Store(self.s, APP)).build(spec)
                errors = {k: v for k, v in results.items() if v["status"] == "error"}
                self.assertEqual(errors, {}, tpl.template_id)
                rendered += 1
        self.assertGreaterEqual(rendered, 5)

    def test_unlimited_supporting_metrics(self):
        b = Bindings.from_dict({**self.b.as_dict(), "supporting_metrics": [m.id for m in self.model.metrics]})
        self.assertEqual(len(b.supporting_metrics), len(self.model.metrics) - 1)
        prof = build_profile(self.s, self.model, b, "executives", FEATURES, today=TODAY)
        data = Engine(self.s, self.model, b, prof).kpi_grid({})
        self.assertEqual(len(data["items"]), len(self.model.metrics))

    def test_ml_is_deferred_then_enriched(self):
        from engine import Deferred
        prof = build_profile(self.s, self.model, self.b, "executives", FEATURES, today=TODAY)
        cortex = Cortex(self.s, APP)
        cache = {}
        fast = Engine(self.s, self.model, self.b, prof, cortex, None, cache, defer_ml=True)
        with self.assertRaises(Deferred):
            fast.forecast_band({"role_bindings": {"strategic_kpi": "ORDERS.SALES"}})
        bridge = fast.driver_bridge({"role_bindings": {"strategic_kpi": "ORDERS.SALES"}})
        self.assertTrue(bridge["insights_pending"] and bridge["reconciled"])
        slow = Engine(self.s, self.model, self.b, prof, cortex, None, cache, defer_ml=False)
        self.assertEqual(len(slow.forecast_band({"role_bindings": {"strategic_kpi": "ORDERS.SALES"}})["forecast"]), 6)

    def test_top_insights_success_path(self):
        s = FakeSession(fail_top_insights=False)
        prof = build_profile(s, self.model, self.b, "executives", FEATURES, today=TODAY)
        data = Engine(s, self.model, self.b, prof, Cortex(s, APP)).driver_bridge({"role_bindings": {}})
        self.assertTrue(data["insights"])
        self.assertTrue(any("CALL WBR_DB.ANALYTICS_ENTERPRISE.AA_TOP_INSIGHTS!GET_DRIVERS" in q for q, _ in s.sqls))

    def test_driver_bridge_reconciles_and_falls_back(self):
        prof = build_profile(self.s, self.model, self.b, "executives", FEATURES, today=TODAY)
        eng = Engine(self.s, self.model, self.b, prof, Cortex(self.s, APP), Store(self.s, APP))
        data = eng.driver_bridge({"metric_id": "ML:TOP_INSIGHTS", "role_bindings": {"strategic_kpi": "ORDERS.SALES"}})
        self.assertTrue(data["reconciled"])
        self.assertIn("not enabled", data["insights_error"])

    def test_exceptions_find_planted_anomaly(self):
        b = Bindings.from_dict({**self.b.as_dict(), "segment_dimension": "ORDERS.REGION",
                                "region_dimension": "ORDERS.SEGMENT"})
        prof = build_profile(self.s, self.model, b, "executives", FEATURES, today=dt.date(2025, 1, 2))
        # move current period to December by pretending data ends on 31 Dec
        eng = Engine(self.s, self.model, b, prof, None, None)
        data = eng._exceptions({"role_bindings": {"strategic_kpi": "ORDERS.SALES", "segment": "ORDERS.REGION"}})
        self.assertTrue(data["rows"])

    def test_cortex_layout_recommendation_is_validated(self):
        cortex = Cortex(self.s, APP)
        cortex.model_in_use = "claude-sonnet-4-5"
        prof = build_profile(self.s, self.model, self.b, "executives", FEATURES, today=TODAY)
        opts = picker_options("executives", prof.inventory())
        rec = cortex.recommend_layout("executives", "board pack", opts)
        allowed = {o["template_id"] for o in opts if o["selectable"]}
        self.assertTrue(rec["template_id"] in allowed or rec["template_id"] is None)

    def test_forecast_and_narrative(self):
        cortex = Cortex(self.s, APP)
        cortex.model_in_use = "claude-sonnet-4-5"
        series = [((dt.date(2023, 1, 1) + dt.timedelta(days=31 * i)).replace(day=1).isoformat(), 100.0 + i)
                  for i in range(20)]
        fc = cortex.forecast(series, 6, "month")
        self.assertEqual(len(fc["points"]), 6)
        text = cortex.narrative("Overview", "How are we doing?", ["Sales = $1M"], "executives")
        self.assertIn("Suggested action", text["text"])

    def test_agent_discovery_creation_and_ask(self):
        self.assertEqual(find_agents(self.s, SV, [APP]), [])
        made = create_agent(self.s, APP, SV, "Superstore", ["What were sales by region?"])
        found = find_agents(self.s, SV, [APP])
        self.assertEqual(found[0]["fqn"], made["fqn"])
        ans = ask_agent(self.s, made["fqn"], "Sales by region?")
        self.assertIn("West", ans["text"])
        self.assertTrue(ans["sql"])
        self.assertEqual(ans["thread"]["thread_id"], 42)

    def test_agent_spec_carries_warehouse(self):
        from agent_service import agent_spec, is_missing_warehouse
        spec = agent_spec(SV, "Superstore", [], "powerhouse")
        self.assertEqual(spec["tool_resources"]["analyst"]["execution_environment"],
                         {"type": "warehouse", "warehouse": "POWERHOUSE"})
        made = create_agent(self.s, APP, SV, "Superstore", [], warehouse="POWERHOUSE", replace=True)
        self.assertTrue(made["sql"].startswith("CREATE OR REPLACE AGENT"))
        self.assertTrue(is_missing_warehouse(RuntimeError("391920: The Analyst tool analyst is missing an execution environment")))

    def test_decisions_roundtrip(self):
        store = Store(self.s, APP)
        did = store.add_decision(SV, "exec_growth_baseline", "Fix Central", "detail", "Ana", "2026-10-15", {"z": -3})
        rows = store.list_decisions(SV)
        self.assertEqual(rows[0]["decision_id"], did)
        store.set_decision_status(did, "Done")
        self.assertEqual(store.list_decisions(SV)[0]["status"], "Done")


if __name__ == "__main__":
    unittest.main()


class CostAttributionTests(unittest.TestCase):
    """D4: every app query is tagged; Governance attributes queries, time and Cortex credits per feature."""

    def test_usage_by_feature_falls_back_gracefully(self):
        from store import Store
        from fake_snowflake import FakeSession
        out = Store(FakeSession(), "WBR_DB.ANALYTICS_ENTERPRISE").usage_by_feature("aa-enterprise")
        self.assertEqual(out["detail"], "no warehouse attribution")      # attribution view missing -> variant 2
        self.assertEqual(out["rows"][0]["feature"], "set_view")
        self.assertEqual(out["error"], "")
