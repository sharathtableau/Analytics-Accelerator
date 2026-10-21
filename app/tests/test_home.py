import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "streamlit"))
sys.path.insert(0, str(HERE))

from fake_snowflake import FakeSession, SV  # noqa: E402
from ai_services import Cortex  # noqa: E402
import home  # noqa: E402
from semantic_catalog import describe_semantic_view, list_semantic_views  # noqa: E402

APP = "WBR_DB.ANALYTICS_ENTERPRISE"


class HomeTests(unittest.TestCase):
    def setUp(self):
        self.s = FakeSession()
        sources = list_semantic_views(self.s, ["WBR_DB.PUBLIC"])
        self.cat = home.build_catalog(sources, lambda f: describe_semantic_view(self.s, f))
        self.cortex = Cortex(self.s, APP)
        self.cortex.model_in_use = "claude-sonnet-4-5"

    def test_catalog_and_fallback_ideas(self):
        self.assertEqual(self.cat[0]["fqn"], SV)
        ideas = home.fallback_suggestions(self.cat)
        self.assertEqual({i["audience"] for i in ideas}, {"executives", "managers", "daily_operations"})
        self.assertTrue(all(i["semantic_view"] == SV for i in ideas))

    def test_cortex_ideas_are_validated(self):
        ideas = home.ai_suggestions(self.cortex, self.cat)
        self.assertEqual(len(ideas), 9)                                  # bad audience + unknown view dropped
        self.assertEqual(ideas[0]["metrics"], ["Sales", "Profit"])       # invented metric removed

    def test_routing(self):
        r = home.route(self.cortex, self.cat, "profit by region for my team")
        self.assertEqual((r["semantic_view"], r["audience"]), (SV, "managers"))
        kw = home.keyword_route(self.cat, "weekly ops review of sales by region")
        self.assertEqual((kw["semantic_view"], kw["audience"]), (SV, "weekly_business_review"))
        m = describe_semantic_view(self.s, SV)
        self.assertEqual(home.pick_primary(m, "Profit Ratio", ""), "ORDERS.PROFIT_RATIO")

    def test_friendly_names(self):
        self.assertEqual(home.friendly("HUMAN_RESOURCE_DASHBOARD_SEMANTIC"), "Human Resource Dashboard")


if __name__ == "__main__":
    unittest.main()


class FeaturedTests(unittest.TestCase):
    def test_featured_view_leads(self):
        s = FakeSession()
        sources = list_semantic_views(s, ["WBR_DB.PUBLIC"])
        cat = home.build_catalog(sources, lambda f: describe_semantic_view(s, f), {SV: "Demo Retail (live)"})
        self.assertTrue(cat[0]["featured"])
        self.assertEqual(cat[0]["label"], "Demo Retail (live)")
        cx = Cortex(s, APP)
        cx.model_in_use = "claude-sonnet-4-5"
        ideas = home.ai_suggestions(cx, cat)
        self.assertTrue(ideas[0]["featured"])
        self.assertIn("FEATURED", home._catalog_text(cat))


class SavedIdeasTests(unittest.TestCase):
    """Cortex's ideas survive restarts/redeploys and only change when the user asks."""

    def test_ideas_round_trip_and_signature(self):
        from store import Store
        s = FakeSession()
        sources = list_semantic_views(s, ["WBR_DB.PUBLIC"])
        cat = home.build_catalog(sources, lambda f: describe_semantic_view(s, f), {SV: "Demo Retail (live)"})
        cx = Cortex(s, APP)
        cx.model_in_use = "claude-sonnet-4-5"
        ideas = home.ai_suggestions(cx, cat)
        st = Store(s, APP)
        st.save_ideas("WBR_OWNER", home.catalog_signature(cat), ideas, "WBR_OWNER")
        got = Store(s, APP).load_ideas("WBR_OWNER")            # fresh store = app restarted
        self.assertEqual([i["title"] for i in got["ideas"]], [i["title"] for i in ideas])
        self.assertEqual(got["catalog_sig"], home.catalog_signature(cat))
        self.assertIsNone(Store(s, APP).load_ideas("OTHER_ROLE"))
        changed = [dict(c, metrics=c["metrics"][:-1]) if i == 0 else c for i, c in enumerate(cat)]
        self.assertNotEqual(home.catalog_signature(changed), home.catalog_signature(cat))

    def test_expired_cache_restarts_clock(self):
        home.cache_clear()
        home.cache_put("R", suggestions=[1])
        home._CACHE["R"]["at"] -= home.TTL + 1
        self.assertIsNone(home.cache_get("R"))
        home.cache_put("R", suggestions=[2])
        self.assertEqual(home.cache_get("R")["suggestions"], [2])


class SkippedViewTests(unittest.TestCase):
    def test_views_without_metrics_or_access_are_explained(self):
        from types import SimpleNamespace as NS
        facts_only = NS(comment="", metrics=[], categorical_dimensions=[], facts=[1, 2, 3],
                        time_dimensions=[NS(id="T.D")])

        def describe(fqn):
            if fqn.endswith("LOCKED"):
                raise RuntimeError("Semantic view 'X' does not exist or not authorized.")
            return facts_only
        skipped = []
        cat = home.build_catalog([{"fqn": "SANDBOX.BI.INFERA_SEMANTIC_VIEW", "name": "INFERA_SEMANTIC_VIEW"},
                                  {"fqn": "SANDBOX.BI.LOCKED", "name": "LOCKED"}], describe, {}, skipped)
        self.assertEqual(cat, [])
        why = {s["name"]: s["reason"] for s in skipped}
        self.assertIn("3 facts but no metrics", why["INFERA_SEMANTIC_VIEW"])
        self.assertIn("can't read it", why["LOCKED"])
