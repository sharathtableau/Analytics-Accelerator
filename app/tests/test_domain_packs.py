"""Domain layout packs: pack layouts come first in a domain workspace, resolve to real fields, and are validated."""
import re
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "streamlit"))
sys.path.insert(0, str(HERE))

import domain_packs  # noqa: E402
from composer import DataContext  # noqa: E402
from fake_snowflake import FakeSession, SV  # noqa: E402
from inventory import build_profile, infer_bindings  # noqa: E402
from persona_layouts import compose_persona, pick_variant, variant_ids  # noqa: E402
from semantic_catalog import describe_semantic_view  # noqa: E402
from semantic_query import SemanticQuery  # noqa: E402
from test_composer import FEATURES, TODAY  # noqa: E402

# a small pack over the fake (Superstore) view, to exercise the mechanics
TEST_PACK = {"managers": [
    {"id": "t_margin", "title": "Margin watch", "when": "profit, margin", "summary": "Profit by region.",
     "pages": [{"label": "Margin", "question": "Where is profit?", "tiles": [
         {"type": "kpi_grid", "title": "Profit KPIs", "metrics": ["PROFIT", "PROFIT_RATIO", "NOT_A_METRIC"], "width": 12},
         {"type": "ranked_bar", "title": "Profit by region", "metric": "PROFIT", "dimension": "REGION", "width": 6},
         {"type": "ranked_bar", "title": "Missing field", "metric": "NOT_A_METRIC", "dimension": "REGION", "width": 6},
     ]}]},
    {"id": "t_volume", "title": "Volume watch", "when": "orders, units", "summary": "Orders by segment.",
     "pages": [{"label": "Volume", "question": "Where are the orders?", "tiles": [
         {"type": "ranked_bar", "title": "Orders by segment", "metric": "ORDER_COUNT", "dimension": "SEGMENT", "width": 12},
     ]}]},
]}


class DomainPackTests(unittest.TestCase):
    def setUp(self):
        domain_packs.PACKS["test"] = TEST_PACK
        domain_packs.RULES["test"] = {"managers": [("t_volume", r"orders|units")]}
        self.s = FakeSession(fail_top_insights=False)
        self.model = describe_semantic_view(self.s, SV)
        self.b = infer_bindings(self.model)
        self.distinct = SemanticQuery(self.s, self.model).distinct_counts(
            [d.id for d in self.model.categorical_dimensions])

    def tearDown(self):
        domain_packs.PACKS.pop("test", None)
        domain_packs.RULES.pop("test", None)

    def ctx(self, aud, domain):
        prof = build_profile(self.s, self.model, self.b, aud, FEATURES, today=TODAY)
        return DataContext(self.model, self.b, prof, self.distinct, aud, domain)

    def test_pack_layouts_first_in_workspace_only(self):
        self.assertEqual(variant_ids("managers", self.ctx("managers", "test"))[:2], ["t_margin", "t_volume"])
        self.assertNotIn("t_margin", variant_ids("managers", self.ctx("managers", "")))

    def test_rule_then_pack_default(self):
        c = self.ctx("managers", "test")
        self.assertEqual(pick_variant("managers", "how many orders this week", c), "t_volume")
        self.assertEqual(pick_variant("managers", "weekly review", c), "t_margin")
        self.assertEqual(pick_variant("managers", "weekly review", self.ctx("managers", "")), "scorecard")

    def test_compose_uses_pack_and_drops_unknown_fields(self):
        spec = compose_persona(None, self.ctx("managers", "test"), "weekly review")
        self.assertEqual(spec["layout_variant"], "t_margin")
        self.assertEqual(spec["display_name"], "Margin watch")
        titles = [c["title"] for p in spec["pages"] for c in p["components"]]
        self.assertIn("Profit by region", titles)
        self.assertNotIn("Missing field", titles)
        kpi = next(c for p in spec["pages"] for c in p["components"] if c["title"] == "Profit KPIs")
        self.assertEqual(len(kpi["metrics"]), 2)
        self.assertIn("t_volume", [o["id"] for o in spec["layout_options"]])

    def test_switching_to_another_pack_layout(self):
        first = compose_persona(None, self.ctx("managers", "test"), "weekly review")
        again = compose_persona(None, self.ctx("managers", "test"), "weekly review", variant="t_volume", reuse=first)
        self.assertEqual(again["layout_variant"], "t_volume")

    def test_pack_layout_this_view_cannot_fill_is_not_offered(self):
        domain_packs.PACKS["test"]["executives"] = [{"id": "t_none", "title": "Nothing", "when": "x", "summary": "x",
            "pages": [{"label": "X", "question": "x", "tiles": [{"type": "ranked_bar", "title": "x",
                       "metric": "NOT_A_METRIC", "dimension": "REGION", "width": 12}]}]}]
        c = self.ctx("executives", "test")
        self.assertNotIn("t_none", variant_ids("executives", c))
        self.assertEqual(pick_variant("executives", "how is the year going", c), "plan")

    def test_weekly_alerts_never_use_days(self):
        import alerts
        spec, _ = alerts.normalize(self.model, {"metric": self.model.metrics[0].id, "grain": "day", "value_input": 5},
                                   {}, self.b.time_dimension, weekly=True)
        self.assertEqual(spec["grain"], "week")
        self.assertEqual(alerts.options(self.model, {}, weekly=True)["grains"], ["week", "month"])

    def _names(self, domain):
        sv = HERE.parents[1] / "setup" / domain / f"build_{domain}_sv.py"
        if not sv.exists():
            self.skipTest(f"{domain} setup not in this package")
        text = sv.read_text(encoding="utf-8")
        return ({m.upper() for m in re.findall(r"^\s+\w+\.(\w+) (?:\{NA\})?AS ", text, re.M)},
                {m.upper() for m in re.findall(r"^\s+\w+\.(\w+) AS C_", text, re.M)})

    def test_alert_templates_name_real_metrics(self):
        for dom in ("finance", "cpg"):
            metrics, _ = self._names(dom)
            for t in domain_packs.alert_templates(dom):
                self.assertIn(t["metric"], metrics, t["id"])
            for name in domain_packs.LEAD.get(dom, []):
                self.assertIn(name, metrics)

    def test_cpg_pack_names_exist_in_the_cpg_view(self):
        self._check_pack("cpg", domain_packs.CPG)

    def test_finance_pack_names_exist_in_the_finance_view(self):
        self._check_pack("finance", domain_packs.FINANCE)

    def _check_pack(self, dom, pack):
        metrics, dims = self._names(dom)
        for persona, vs in pack.items():
            for v in vs:
                for pg in v["pages"]:
                    for t in pg["tiles"]:
                        for k in ("metric", "metric2"):
                            if k in t:
                                self.assertIn(t[k], metrics, f"{v['id']}: {t[k]}")
                        for m in t.get("metrics", []):
                            self.assertIn(m, metrics, f"{v['id']}: {m}")
                        for k in ("dimension", "dimension2"):
                            if k in t:
                                self.assertIn(t[k], dims, f"{v['id']}: {t[k]}")
                        for d in t.get("dimensions", []):
                            self.assertIn(d, dims, f"{v['id']}: {d}")
                        for d in (t.get("opts") or {}).get("filter", {}):
                            self.assertIn(d, dims, f"{v['id']}: filter {d}")
                        for st in (t.get("opts") or {}).get("steps", []):
                            if st[0]:
                                self.assertIn(st[0], metrics, f"{v['id']}: step {st[0]}")

    def test_retail_pack_names_exist_in_the_retail_view(self):
        sv = HERE.parents[1] / "setup" / "retail" / "03_semantic_view.sql"
        if not sv.exists():
            self.skipTest("retail setup not in this package")
        text = sv.read_text(encoding="utf-8")
        names = {m.upper() for m in re.findall(r"^\s+\w+\.(\w+) (?:NON ADDITIVE BY \([^)]*\) )?AS ", text, re.M)}
        for persona, vs in domain_packs.RETAIL.items():
            for v in vs:
                for pg in v["pages"]:
                    for t in pg["tiles"]:
                        for x in [t.get("metric"), t.get("metric2"), t.get("dimension"), t.get("dimension2"),
                                  *t.get("metrics", []), *t.get("dimensions", [])]:
                            if x:
                                self.assertIn(x, names, f"{v['id']}: {x}")


if __name__ == "__main__":
    unittest.main()


class PersonaTests(unittest.TestCase):
    def test_every_domain_has_its_ontology_personas(self):
        want = {"finance": {"Head of Retail Deposits", "Head of Card Portfolio", "Chief Credit Officer",
                            "Head of Acquisition Marketing"},
                "cpg": {"National Account Manager", "Revenue Growth Manager", "Brand / Category Director",
                        "Demand & Supply Planner"},
                "retail": {"Category Manager", "Regional Operations Director", "Inventory & Allocation Planner",
                           "VP Omnichannel"}}
        for dom, names in want.items():
            labels = {p["label"] for p in domain_packs.personas(dom)}
            self.assertTrue(names <= labels, dom)
            self.assertIn("Leadership", labels)

    def test_personas_point_at_real_layouts_and_alerts(self):
        from home import AUDIENCES
        for dom in ("finance", "cpg", "retail"):
            ids = [p["id"] for p in domain_packs.personas(dom)]
            self.assertEqual(len(ids), len(set(ids)))
            alert_ids = {a["id"] for a in domain_packs.alert_templates(dom)}
            for p in domain_packs.personas(dom):
                self.assertIn(p["audience"], AUDIENCES, p["id"])
                if p["layout"]:
                    self.assertIsNotNone(domain_packs.get(dom, p["audience"], p["layout"]), p["id"])
                self.assertTrue(p["questions"], p["id"])
                for a in p["alerts"]:
                    self.assertIn(a, alert_ids, p["id"])
                self.assertEqual(len(p["alert_titles"]), len(p["alerts"]))
        self.assertIsNone(domain_packs.persona("finance", "nope"))
        self.assertEqual(domain_packs.personas("other"), [])
