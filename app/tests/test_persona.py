"""Persona layouts (L1-L3): grain per audience, reviewed skeletons, Cortex slot fill, new tiles."""
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "streamlit"))
sys.path.insert(0, str(HERE))

from fake_snowflake import FakeSession, SV  # noqa: E402
from ai_services import Cortex  # noqa: E402
from composer import DataContext, apply_review  # noqa: E402
from engine import Engine  # noqa: E402
from inventory import build_profile, infer_bindings  # noqa: E402
from persona_layouts import compose_persona, fill_slots, slot_options  # noqa: E402
from semantic_catalog import describe_semantic_view  # noqa: E402
from semantic_query import SemanticQuery  # noqa: E402
from test_composer import APP, FEATURES, TODAY  # noqa: E402


class StubCortex:
    def __init__(self, payload):
        self.payload = payload

    def complete(self, prompt):
        self.prompt = prompt
        return json.dumps(self.payload), "stub"


class PersonaTests(unittest.TestCase):
    def setUp(self):
        self.s = FakeSession(fail_top_insights=False)
        self.model = describe_semantic_view(self.s, SV)
        self.b = infer_bindings(self.model)
        self.distinct = SemanticQuery(self.s, self.model).distinct_counts(
            [d.id for d in self.model.categorical_dimensions])

    def ctx(self, aud):
        prof = build_profile(self.s, self.model, self.b, aud, FEATURES, today=TODAY)
        return DataContext(self.model, self.b, prof, self.distinct, aud), prof

    def build(self, aud, spec, defer=False):
        ctx, prof = self.ctx(aud)
        return Engine(self.s, self.model, self.b, prof, Cortex(self.s, APP), None, {}, [], defer_ml=defer).build(spec)

    def test_grain_per_persona(self):
        grains = {a: self.ctx(a)[1].calendar.grain for a in ("executives", "managers", "daily_operations")}
        self.assertEqual(grains, {"executives": "month", "managers": "week", "daily_operations": "day"})

    def test_three_personas_have_different_skeletons(self):
        types = {}
        for aud in ("executives", "managers", "daily_operations"):
            spec = compose_persona(None, self.ctx(aud)[0], "")
            types[aud] = [c["type"] for p in spec["pages"] for c in p["components"]]
            self.assertEqual(spec["origin"], "persona")
            self.assertEqual(spec["slot_origin"], "defaults")
        self.assertEqual(types["executives"], ["kpi_plan", "ytd_trajectory", "gauge", "driver_bridge", "action_table"])
        self.assertEqual(types["daily_operations"], ["status_tiles", "pace_chart", "hour_heatmap", "worklist"])
        self.assertEqual(types["managers"][0], "scorecard")
        # no tile type is shared by all three
        self.assertFalse(set(types["executives"]) & set(types["managers"]) & set(types["daily_operations"]))

    def test_cortex_fills_slots_and_bad_ids_are_ignored(self):
        ctx = self.ctx("managers")[0]
        cx = StubCortex({"title": "Regional scorecard", "summary": "s",
                         "slots": {"scorecard_dimension": ["ORDERS.CATEGORY"],
                                   "scorecard_kpis": ["ORDERS.PROFIT", "ORDERS.NOPE"]}})
        spec = compose_persona(cx, ctx, "category managers")
        sc = spec["pages"][0]["components"][0]
        self.assertEqual(sc["dimension"], "ORDERS.CATEGORY")
        self.assertEqual(sc["metrics"][0], "ORDERS.PROFIT")
        self.assertEqual(spec["display_name"], "Regional scorecard")
        self.assertTrue(any("ORDERS.NOPE" in e["reason"] for e in spec["governance"]))
        self.assertIn("Options:", cx.prompt)

    def test_operations_tiles_compute(self):
        ctx, _ = self.ctx("daily_operations")
        spec = compose_persona(None, ctx, "")
        res, facts = self.build("daily_operations", spec)
        for cid, r in res.items():
            self.assertEqual(r["status"], "ready", (cid, r))
        st = res["p1/t1"]["data"]
        self.assertEqual(st["hour"], 14)                       # live day stops at 14:00 in the fake
        self.assertIn("same time", st["compare_label"])
        pace = res["p1/t2"]["data"]
        today = next(s for s in pace["series"] if s["key"] == "today")["values"]
        self.assertIsNone(today[-1])                           # future hours are empty
        self.assertIsNotNone(today[pace["now_index"]])
        wl = res["p1/t4"]["data"]
        self.assertIn("rows", wl)
        self.assertTrue(any("Worklist" in f or "today" in f for f in facts["p1"]))

    def test_hour_filter_is_applied_to_comparisons(self):
        ctx, _ = self.ctx("daily_operations")
        spec = compose_persona(None, ctx, "")
        self.s.sqls.clear()
        self.build("daily_operations", spec)
        self.assertTrue(any("ORDER_HOUR <= 14" in q for q, _ in self.s.sqls))

    def test_executive_tiles_and_forecast_phase(self):
        ctx, _ = self.ctx("executives")
        spec = compose_persona(None, ctx, "")
        res, _ = self.build("executives", spec, defer=True)
        kp = res["p1/t1"]["data"]
        self.assertTrue(kp["has_plan"])
        sales = next(i for i in kp["items"] if i["metric"] == "ORDERS.SALES")
        self.assertEqual(sales["target_label"], "plan")
        traj = res["p1/t2"]["data"]
        self.assertTrue(traj.get("insights_pending"))           # ML forecast deferred to phase 2
        res2, _ = self.build("executives", spec, defer=False)
        traj2 = res2["p1/t2"]["data"]
        self.assertTrue(traj2.get("ml"), traj2.get("forecast_error"))
        fc = next(s for s in traj2["series"] if s["key"] == "forecast")["values"]
        self.assertIsNotNone(fc[-1])

    def test_manager_scorecard(self):
        ctx, _ = self.ctx("managers")
        spec = compose_persona(None, ctx, "")
        res, _ = self.build("managers", spec)
        sc = res["p1/t1"]["data"]
        self.assertEqual(sc["total"]["segment"], "Total")
        self.assertEqual(sc["columns"][0]["compare"], "plan")
        self.assertTrue(all(c["status"] in ("good", "ok", "warn", "bad") for r in sc["rows"] for c in r["cells"]))
        self.assertTrue(sc["period_label"].startswith("Wk of"))

    def test_ratio_cannot_be_cumulated(self):
        ctx, _ = self.ctx("executives")
        cx = StubCortex({"slots": {"trajectory_metric": ["ORDERS.PROFIT_RATIO"]}})
        chosen, info, notes = fill_slots(cx, ctx, "executives", "")
        self.assertNotIn("ORDERS.PROFIT_RATIO", chosen["trajectory_metric"])   # not an option for the slot
        self.assertNotIn("ORDERS.PROFIT_RATIO", slot_options(ctx, "executives")["trajectory_metric"]["options"])

    def test_review_keeps_persona_kpi_tile(self):
        ctx, _ = self.ctx("executives")
        spec = compose_persona(None, ctx, "")
        out, gov = apply_review(ctx, spec, ["ORDERS.SALES", "ORDERS.QUANTITY"], [])
        self.assertEqual(out["pages"][0]["components"][0]["type"], "kpi_plan")


if __name__ == "__main__":
    unittest.main()
