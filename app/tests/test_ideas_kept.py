"""Home ideas are never lost: new sets are added on top, deploys/catalog changes don't discard them, and a
featured view that is missing from Home always says why (1 Oct fix)."""
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
from store import Store  # noqa: E402

APP = "WBR_DB.ANALYTICS_ENTERPRISE"
INF = "SANDBOX.BI.INFERA_SEMANTIC_VIEW"


def idea(view, aud, title):
    return {"audience": aud, "title": title, "detail": "", "metrics": [], "semantic_view": view, "domain": "x", "goal": title}


def cat_entry(fqn, featured=False, label="L"):
    return {"fqn": fqn, "label": label, "featured": featured, "test_like": False, "comment": "",
            "metrics": [{"id": "T.SALES", "label": "Sales", "additive": True}],
            "dimensions": [{"id": "T.REGION", "label": "Region"}], "time": ["T.D"]}


class KeepIdeasTests(unittest.TestCase):
    def test_new_set_on_top_earlier_kept(self):
        cat = [cat_entry(SV, True, "Harborline"), cat_entry("A.B.OTHER")]
        cat[0]["metrics"] += [{"id": "T.IN_STOCK_RATE", "label": "In Stock Rate", "theme": "inventory"}]
        old = {"created_at": "2026-09-30 10:00", "ideas": [
            dict(idea(SV, "executives", "Old brief"), metrics=["Sales"]),
            dict(idea(SV, "executives", "Old availability"), metrics=["In Stock Rate"]),
            idea("A.B.OTHER", "managers", "Other scorecard"),
            idea("A.B.GONE", "managers", "View dropped")]}
        new = {"created_at": "2026-10-01 11:00", "ideas": [dict(idea(SV, "executives", "New brief"), metrics=["Sales"])]}
        got = home.merge_ideas([new, old], cat)
        titles = [s["title"] for s in got]
        self.assertEqual(titles[0], "New brief")
        self.assertNotIn("Old brief", titles)                        # same audience x theme: newest wins
        self.assertIn("Old availability", titles)                    # different theme: kept as earlier
        self.assertIn("Other scorecard", titles)
        self.assertNotIn("View dropped", titles)                    # its view is gone
        earlier = {s["title"]: s.get("earlier") for s in got}
        self.assertIsNone(earlier["New brief"])
        self.assertEqual(earlier["Old availability"], "2026-09-30 10:00")
        self.assertEqual({s["title"]: s["theme"] for s in got}["Old availability"], "inventory")

    def test_caps_per_audience(self):
        cat = [cat_entry(SV, True, "Harborline"), cat_entry("A.B.OTHER")]
        themes = ["NET_SALES", "GROSS_MARGIN_PCT", "IN_STOCK_RATE", "ON_TIME_DELIVERY_PCT", "RETURN_RATE", "ORDER_COUNT"]
        cat[0]["metrics"] = [{"id": f"T.{n}", "label": n.replace("_", " ").title()} for n in themes]
        sets = [{"ideas": [dict(idea(SV, "managers", f"M{k}"), metrics=[n.replace("_", " ").title()])
                           for k, n in enumerate(themes)]
                 + [idea("A.B.OTHER", "managers", f"O{k}") for k in range(3)]
                 + [dict(idea(f"A.B.X{k}", "managers", f"X{k}"), metrics=["Order Count"]) for k in range(3)]}]
        for k in range(3):
            e = cat_entry(f"A.B.X{k}")
            e["metrics"] = [{"id": "T.ORDER_COUNT", "label": "Order Count"}]
            cat.append(e)
        got = home.merge_ideas(sets, cat)
        self.assertEqual(len([s for s in got if s["semantic_view"] == SV]), 3)          # featured: 3 per audience
        self.assertEqual(len([s for s in got if s["semantic_view"] == "A.B.OTHER"]), 1)  # one per other dataset
        others = [s for s in got if s["semantic_view"] != SV]
        self.assertEqual(len(others), 2)                                                  # 2 per audience in total
        self.assertEqual(len({s["theme"] for s in others}), 2)                            # on different themes

    def test_saved_ideas_survive_a_catalog_change(self):
        """The bug: a deploy changed the catalog signature and Home threw the saved ideas away."""
        s = FakeSession()
        sources = list_semantic_views(s, ["WBR_DB.PUBLIC"])
        cat = home.build_catalog(sources, lambda f: describe_semantic_view(s, f), {SV: "Demo Retail (live)"})
        cx = Cortex(s, APP)
        cx.model_in_use = "claude-sonnet-4-5"
        first = home.ai_suggestions(cx, cat)
        st = Store(s, APP)
        st.save_ideas("WBR_OWNER", "old-signature", first, "WBR_OWNER")
        second = [idea(SV, "managers", "Brand new scorecard")]
        st.save_ideas("WBR_OWNER", home.catalog_signature(cat), second, "WBR_OWNER")
        sets = Store(s, APP).idea_history("WBR_OWNER")
        self.assertEqual(len(sets), 2)
        self.assertEqual(sets[0]["ideas"][0]["title"], "Brand new scorecard")     # newest first
        shown = home.ensure_featured(home.merge_ideas(sets, cat), cat)
        titles = {x["title"] for x in shown}
        self.assertIn("Brand new scorecard", titles)
        kept_themes = {(x["audience"], x["theme"]) for x in shown}
        lost = [x for x in first if (x["audience"], x["theme"]) not in kept_themes]
        self.assertLessEqual(len(lost), 1)          # only where the audience is full (3 per featured dataset)
        self.assertEqual(len([x for x in shown if x["audience"] == "managers"]), 3)

    def test_featured_matching_is_tolerant(self):
        f = {INF + "#VW_RETAIL_MASTER": "Infera Retail"}
        self.assertEqual(home.match_featured(INF + "#VW_RETAIL_MASTER", f), INF + "#VW_RETAIL_MASTER")
        self.assertIsNotNone(home.match_featured(INF.lower() + "#retail_master", f))
        self.assertIsNone(home.match_featured(INF + "#VW_HEALTHCARE_MASTER", f))
        self.assertIsNotNone(home.match_featured(INF + "#ANY_TABLE", {INF: ""}))    # bare view features all tables
        self.assertIsNone(home.match_featured("A.B.C", f))

    def test_cortex_bare_view_name_resolves_to_featured_table(self):
        cat = [cat_entry(INF + "#VW_RETAIL_MASTER", True, "Infera Retail"), cat_entry(INF + "#VW_HEALTHCARE_MASTER")]

        class Cx:
            def complete(self, prompt):
                import json
                return json.dumps({"suggestions": [idea(INF, a, f"{a} idea") for a in
                                                   ("executives", "managers", "daily_operations")]}), "m"
        out = home.ai_suggestions(Cx(), cat)
        self.assertTrue(all(s["semantic_view"] == INF + "#VW_RETAIL_MASTER" for s in out))
        self.assertTrue(all(s["featured"] for s in out))


class FeaturedGapTests(unittest.TestCase):
    def test_no_access_to_schema_is_explained(self):
        skipped = []
        f = {SV: "Harborline", INF + "#VW_RETAIL_MASTER": "Infera Retail"}
        added = home.featured_gaps([cat_entry(SV, True)], f, [{"fqn": SV}], skipped,
                                   {"SANDBOX.BI": "Schema 'SANDBOX.BI' does not exist or not authorized."})
        self.assertEqual(len(added), 1)
        self.assertEqual(added[0]["name"], "Infera Retail")
        self.assertIn("can't list semantic views in SANDBOX.BI", added[0]["reason"])

    def test_view_not_visible_and_table_mismatch(self):
        skipped = []
        home.featured_gaps([], {INF + "#VW_RETAIL_MASTER": "Infera Retail"}, [], skipped, {})
        self.assertIn("doesn't see it in SANDBOX.BI", skipped[0]["reason"])
        skipped = []
        home.featured_gaps([cat_entry(INF + "#RETAIL_FACTS")], {INF + "#VW_RETAIL_MASTER": "Infera Retail"},
                           [{"fqn": INF}], skipped, {})
        self.assertIn("view's tables are RETAIL_FACTS", skipped[0]["reason"])

    def test_already_explained_is_not_repeated(self):
        skipped = [{"fqn": INF, "name": "INFERA_SEMANTIC_VIEW", "reason": "it has no metrics"}]
        home.featured_gaps([], {INF + "#VW_RETAIL_MASTER": "Infera Retail"}, [{"fqn": INF}], skipped, {})
        self.assertEqual(len(skipped), 1)

    def test_schema_errors_are_reported(self):
        class S:
            def sql(self, text, params=None):
                class R:
                    def collect(self_inner):
                        if "SANDBOX" in text:
                            raise RuntimeError("Schema 'SANDBOX.BI' does not exist or not authorized.")
                        return [{"name": "RETAIL_ANALYTICS_SV", "database_name": "WBR_DB", "schema_name": "RETAIL_DEMO"}]
                return R()
        errs = {}
        found = list_semantic_views(S(), ["WBR_DB.RETAIL_DEMO", "SANDBOX.BI"], errs)
        self.assertEqual(len(found), 1)
        self.assertIn("SANDBOX.BI", errs)


if __name__ == "__main__":
    unittest.main()
