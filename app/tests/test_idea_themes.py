"""Home ideas = audience x metric theme: each audience gets different themes with metrics fit for it,
and an idea's metrics lead the persona dashboard it opens."""
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "streamlit"))
sys.path.insert(0, str(HERE))

import home  # noqa: E402

HARBOR = ("NET_SALES GROSS_SALES DISCOUNT_RATE GROSS_MARGIN GROSS_MARGIN_PCT UNITS_SOLD ORDER_COUNT AVERAGE_ORDER_VALUE "
          "ACTIVE_CUSTOMERS ONLINE_NET_SALES ONLINE_SALES_SHARE AVG_CLICK_TO_SHIP_HOURS AVG_DELIVERY_DAYS "
          "ON_TIME_DELIVERY_PCT RETURN_RATE NET_SALES_AFTER_RETURNS LOST_SALES_UNITS STOCKOUT_RATE IN_STOCK_RATE "
          "WEEKS_OF_SUPPLY PLAN_NET_SALES").split()


def harbor(featured=True):
    return {"fqn": "WBR_DB.RETAIL_DEMO.RETAIL_ANALYTICS_SV", "label": "Harborline Retail", "featured": featured,
            "test_like": False, "comment": "", "time": ["SALES.ORDER_DATE"],
            "metrics": [{"id": f"SALES.{n}", "label": n.replace("_", " ").title(), "theme": home.metric_theme(n)}
                        for n in HARBOR],
            "dimensions": [{"id": "SALES.REGION", "label": "Region"}, {"id": "SALES.CATEGORY", "label": "Category"},
                           {"id": "PRODUCTS.SUBCATEGORY", "label": "Subcategory"},
                           {"id": "REGIONS.DISTRIBUTION_CENTER", "label": "Distribution Center"},
                           {"id": "SALES.CARRIER", "label": "Carrier"}, {"id": "SALES.ORDER_HOUR", "label": "Order Hour"}]}


class ThemeTests(unittest.TestCase):
    def test_metric_themes(self):
        t = home.metric_theme
        self.assertEqual(t("NET_SALES"), "revenue")
        self.assertEqual(t("NET_SALES_AFTER_RETURNS"), "returns")
        self.assertEqual(t("LOST_SALES_UNITS"), "inventory")
        self.assertEqual(t("ON_TIME_DELIVERY_PCT"), "fulfilment")
        self.assertEqual(t("GROSS_MARGIN_PCT"), "margin")
        self.assertEqual(t("AVERAGE_ORDER_VALUE"), "customer")
        self.assertEqual(t("ONLINE_SALES_SHARE"), "channel")
        self.assertEqual(t("PLAN_NET_SALES"), "plan")
        self.assertEqual(t("BILLING_AMOUNT"), "care")

    def test_each_audience_gets_its_own_themes_and_metrics(self):
        ideas = home.fallback_suggestions([harbor()])
        by = {}
        for i in ideas:
            by.setdefault(i["audience"], []).append(i)
        self.assertEqual({a: len(v) for a, v in by.items()}, {"executives": 3, "managers": 3, "daily_operations": 3})
        for aud, items in by.items():
            self.assertEqual(len({i["theme"] for i in items}), 3, aud)                    # 3 different themes
            self.assertEqual(len({frozenset(i["metrics"]) for i in items}), 3, aud)       # never the same metrics
            self.assertTrue(all(len(i["metrics"]) >= 2 for i in items), aud)
            self.assertFalse(any(i["theme"] == "plan" for i in items))
        self.assertEqual(by["executives"][0]["theme"], "revenue")                          # outcomes first
        self.assertEqual(by["managers"][0]["theme"], "inventory")                          # levers
        self.assertNotIn("margin", {i["theme"] for i in by["daily_operations"]})           # not an ops theme
        self.assertIn("Stockout Rate", by["daily_operations"][0]["metrics"])
        self.assertIn("Region", by["managers"][0]["title"])
        self.assertIn("Stockout Rate", by["daily_operations"][0]["goal"])                 # goal names the metrics

    def test_cortex_duplicate_themes_dropped_and_thin_ideas_topped_up(self):
        c = harbor(featured=False)

        class Cx:
            def complete(self, prompt):
                self.prompt = prompt
                items = [{"audience": "managers", "title": "In-stock by region", "metrics": ["Stockout Rate"],
                          "semantic_view": c["fqn"]},
                         {"audience": "managers", "title": "Same theme again", "metrics": ["In Stock Rate"],
                          "semantic_view": c["fqn"]},
                         {"audience": "managers", "title": "On-time by region", "metrics": ["On Time Delivery Pct",
                                                                                           "Avg Delivery Days"],
                          "semantic_view": c["fqn"]},
                         {"audience": "executives", "title": "Sales vs plan", "metrics": ["Net Sales", "Gross Sales"],
                          "semantic_view": c["fqn"]}]
                return json.dumps({"suggestions": items}), "x"
        cx = Cx()
        out = home.ai_suggestions(cx, [c])
        titles = [i["title"] for i in out]
        self.assertNotIn("Same theme again", titles)
        first = next(i for i in out if i["title"] == "In-stock by region")
        self.assertGreaterEqual(len(first["metrics"]), 2)                                 # topped up from its theme
        self.assertTrue(all(home.metric_theme(m.upper().replace(" ", "_")) == "inventory" for m in first["metrics"]))
        self.assertIn("Inventory & availability:", cx.prompt)                             # metrics shown by theme
        self.assertIn("DIFFERENT theme", cx.prompt)

    def test_old_repetitive_ideas_collapse_when_merged(self):
        c = harbor()
        same = lambda t: {"audience": "executives", "title": t, "metrics": ["Net Sales", "Gross Sales"],
                          "semantic_view": c["fqn"]}
        got = home.merge_ideas([{"ideas": [same("A"), same("B"), same("C")]}], [c])
        self.assertEqual([i["title"] for i in got], ["A"])


class IdeaLeadsDashboardTests(unittest.TestCase):
    def test_idea_metrics_lead_persona_slots(self):
        from test_persona import PersonaTests
        from persona_layouts import slot_options
        t = PersonaTests("test_grain_per_persona")
        t.setUp()
        ids = [m.id for m in t.model.metrics]
        qty = next(x for x in ids if x.endswith("QUANTITY"))
        orders = next(x for x in ids if x.endswith("ORDER_COUNT"))
        t.b.primary_metric, t.b.supporting_metrics, t.b.source = qty, [orders], "idea"
        for aud, slot in (("executives", "headline_kpis"), ("managers", "scorecard_kpis"),
                          ("daily_operations", "status_kpis")):
            ctx, _ = t.ctx(aud)
            self.assertEqual(slot_options(ctx, aud)[slot]["default"][:2], [qty, orders], aud)


class PromptBarTests(unittest.TestCase):
    def test_data_brief_two_lines(self):
        other = {"fqn": "A.B.OTHER", "label": "Superstore", "featured": False, "metrics": [], "dimensions": []}
        lines = home.data_brief([harbor(), other])
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[0].startswith("Harborline Retail: 21 governed metrics on "))
        self.assertIn("(with plan)", lines[0])
        self.assertIn("by region, category", lines[0])
        self.assertEqual(lines[1], "Also available: Superstore.")

    def test_starter_prompts_per_audience_name_real_metrics(self):
        ps = home.starter_prompts([harbor()])
        self.assertEqual([p["audience"] for p in ps],
                         ["executives"] * 2 + ["managers"] * 2 + ["daily_operations"] * 2)
        ex, mg, op = ps[0]["text"], ps[2]["text"], ps[4]["text"]
        self.assertIn("net sales and gross margin % year to date vs plan", ex)
        self.assertIn("Weekly scorecard by region", mg)
        self.assertIn("in stock rate, on time delivery % and return rate vs plan", mg)
        self.assertIn("by hour vs the same day last week", op)
        self.assertTrue(op.endswith("worklist by subcategory, distribution center and carrier."), op)
        self.assertNotEqual(ps[0]["metrics"], ps[1]["metrics"])          # second prompt = next themes

    def test_no_plan_says_last_year(self):
        c = harbor()
        c["metrics"] = [m for m in c["metrics"] if m["theme"] != "plan"]
        self.assertIn("vs last year", home.starter_prompts([c])[0]["text"])

    def test_typed_prompt_metrics_are_found_in_order(self):
        from types import SimpleNamespace as NS
        names = ["NET_SALES", "ONLINE_NET_SALES", "GROSS_MARGIN", "GROSS_MARGIN_PCT", "ON_TIME_DELIVERY_PCT",
                 "IN_STOCK_RATE", "PLAN_NET_SALES"]
        model = NS(metrics=[NS(id=f"S.{n}", name=n, label=n.replace("_", " ").title()) for n in names])
        ps = home.starter_prompts([harbor()])
        got = home.mentioned_metrics(model, ps[2]["text"])
        self.assertEqual(got, ["S.IN_STOCK_RATE", "S.ON_TIME_DELIVERY_PCT"])
        got = home.mentioned_metrics(model, "Online net sales vs net sales and gross margin % by region")
        self.assertEqual(got, ["S.ONLINE_NET_SALES", "S.NET_SALES", "S.GROSS_MARGIN_PCT"])


class NewIdeasRotationTests(unittest.TestCase):
    def test_new_ideas_use_themes_not_on_screen(self):
        c = harbor()
        first = home.ensure_featured(home.fallback_suggestions([c]), [c])
        avoid = home.shown_themes(first, [c])
        self.assertEqual(avoid[(c["fqn"], "Executive")], {"revenue", "margin", "channel"})

        class Cx:   # Cortex repeats an on-screen theme and proposes one fresh one
            def complete(self, prompt):
                self.prompt = prompt
                return json.dumps({"suggestions": [
                    {"audience": "executives", "title": "Sales again", "metrics": ["Net Sales"], "semantic_view": c["fqn"]},
                    {"audience": "executives", "title": "Availability", "metrics": ["In Stock Rate", "Lost Sales Units"],
                     "semantic_view": c["fqn"]},
                    {"audience": "managers", "title": "Basket", "metrics": ["Average Order Value"], "semantic_view": c["fqn"]},
                    {"audience": "daily_operations", "title": "Returns", "metrics": ["Return Rate"],
                     "semantic_view": c["fqn"]}]}), "x"
        cx = Cx()
        new = home.ai_suggestions(cx, [c], avoid)
        self.assertIn("use exactly these themes", cx.prompt)
        self.assertNotIn("Sales again", [i["title"] for i in new])                 # on-screen theme dropped
        for grp, aud in (("Executive", "executives"), ("Manager", "managers"), ("Operations", "daily_operations")):
            mine = [i for i in new if home.AUDIENCE_GROUP[i["audience"]] == grp]
            themes = [i["theme"] for i in mine]
            self.assertEqual(len(themes), 3, grp)
            self.assertEqual(len(set(themes)), 3, grp)                           # all different
            self.assertFalse(set(themes) & avoid[(c["fqn"], grp)], grp)          # none repeated from screen
        # what Home shows after the click: only the new themes per audience
        shown = home.ensure_featured(home.merge_ideas([{"ideas": new}, {"ideas": first, "created_at": "x"}], [c]), [c])
        for grp in ("Executive", "Manager", "Operations"):
            themes = [i["theme"] for i in shown if home.AUDIENCE_GROUP[i["audience"]] == grp]
            self.assertEqual(len(themes), len(set(themes)), grp)
            self.assertFalse(set(themes) & avoid[(c["fqn"], grp)], grp)

    def test_rotation_wraps_when_themes_run_out(self):
        c = harbor()
        allt = [t for t, _ in home.audience_themes(c, "executives", 99)]
        nxt = [t for t, _ in home.next_themes(c, "executives", 3, set(allt[:-1]))]
        self.assertEqual(nxt[0], allt[-1])                                         # the unseen one first
        self.assertEqual(len(set(nxt)), 3)


class VarianceMetricTests(unittest.TestCase):
    def test_variance_metrics_never_lead(self):
        from persona_layouts import SKIP
        for name in ("NET_SALES_VS_PLAN", "PLAN_NET_SALES", "MARGIN_VARIANCE", "HELPER_UNIT_DAYS"):
            self.assertTrue(SKIP.search(name), name)
        for name in ("NET_SALES", "IN_STOCK_RATE", "WEEKS_OF_SUPPLY"):
            self.assertFalse(SKIP.search(name), name)
        c = harbor()
        c["metrics"].append({"id": "SALES.NET_SALES_VS_PLAN", "label": "Net Sales Vs Plan", "theme": "plan"})
        got = home.merge_ideas([{"ideas": [{"audience": "daily_operations", "title": "Sales pace", "semantic_view": c["fqn"],
                                            "metrics": ["Net Sales Vs Plan", "Order Count"]}]}], [c])
        self.assertEqual(got[0]["metrics"], ["Order Count"])


class KpiDisplayTests(unittest.TestCase):
    def test_display_from_text(self):
        from composer import display_from_text as d
        self.assertEqual(d("show these as a table"), "table")
        self.assertEqual(d("use arrows instead of bars"), "variance")
        self.assertEqual(d("display variance numbers with conditional formatting"), "variance")
        self.assertEqual(d("switch back to bullet bars"), "bullet")
        self.assertIsNone(d("why is the net sales number down?"))         # a question, not a display change
        self.assertIsNone(d("net sales by region"))

    def test_display_survives_revalidation(self):
        from test_persona import PersonaTests
        from composer import revalidate_tile
        from persona_layouts import compose_persona
        t = PersonaTests("test_grain_per_persona")
        t.setUp()
        ctx, _ = t.ctx("executives")
        spec = compose_persona(None, ctx, "")
        page = spec["pages"][0]
        tile = next(c for c in page["components"] if c["type"] == "kpi_plan")
        tile["display"] = "table"
        new, _ = revalidate_tile(ctx, spec, page["page_id"], tile, {"width": 12})
        self.assertEqual(new["display"], "table")


if __name__ == "__main__":
    unittest.main()
