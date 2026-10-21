"""Layout variety (L6): several reviewed layouts per audience, chosen from the person's question, switchable
without an AI call, the question answered first, and every layout renders."""
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "streamlit"))
sys.path.insert(0, str(HERE))

import persona_layouts as pl  # noqa: E402
import test_persona as tp  # noqa: E402


class CountingCortex(tp.StubCortex):
    calls = 0

    def complete(self, prompt):
        CountingCortex.calls += 1
        return super().complete(prompt)


class LayoutVariantTests(unittest.TestCase):
    setUp, ctx, build = tp.PersonaTests.setUp, tp.PersonaTests.ctx, tp.PersonaTests.build

    def test_every_layout_renders(self):
        for aud in pl.PERSONAS:
            ctx, _ = self.ctx(aud)
            base = pl.compose_persona(None, ctx, "")
            self.assertEqual(base["layout_variant"], pl.variant_ids(aud)[0])        # no question: today's layout
            self.assertEqual([o["id"] for o in base["layout_options"]], pl.variant_ids(aud))
            for v in pl.variant_ids(aud):
                spec = pl.compose_persona(None, ctx, "", variant=v, reuse=base)
                self.assertEqual(spec["layout_variant"], v)
                res, _ = self.build(aud, spec)
                bad = {k: r for k, r in res.items() if r["status"] != "ready"}
                self.assertEqual(bad, {}, (aud, v))

    def test_layouts_differ(self):
        ctx, _ = self.ctx("executives")
        base = pl.compose_persona(None, ctx, "")
        kinds = {o["id"]: tuple(t["type"] for t in o["tiles"]) for o in base["layout_options"]}
        self.assertEqual(len(set(kinds.values())), len(kinds))

    def test_question_picks_the_layout(self):
        cases = [("executives", "Show me profit by region", "question"),
                 ("executives", "How is our growth and mix trending?", "growth_mix"),
                 ("executives", "How is the year going", "plan"),
                 ("managers", "Which regions are off track this week?", "exceptions"),
                 ("managers", "Compare categories best and worst", "compare"),
                 ("managers", "category managers", "scorecard"),
                 ("daily_operations", "How did the last 7 days go?", "daily"),
                 ("daily_operations", "Are we OK right now?", "live")]
        for aud, q, want in cases:
            spec = pl.compose_persona(None, self.ctx(aud)[0], q)
            self.assertEqual(spec["layout_variant"], want, q)

    def test_question_tile_comes_first_and_is_marked(self):
        spec = pl.compose_persona(None, self.ctx("managers")[0], "x", asked="Compare categories best and worst")
        first = spec["pages"][0]["components"][0]
        self.assertTrue(first.get("focus"))
        self.assertEqual(first["dimension_id"] if "dimension_id" in first else first.get("dimension"),
                         "ORDERS.CATEGORY")

    def test_rewritten_goal_does_not_invent_a_question(self):
        # the router may rewrite "How did the last 7 days go?" into a goal naming a metric and breakdown
        spec = pl.compose_persona(None, self.ctx("daily_operations")[0], "Operations view of profit by region",
                                  asked="How did the last 7 days go?")
        self.assertEqual(spec["layout_variant"], "daily")
        self.assertFalse(any(c.get("focus") for p in spec["pages"] for c in p["components"]))

    def test_cortex_layout_choice_is_validated_and_switching_makes_no_ai_call(self):
        ctx = self.ctx("executives")[0]
        CountingCortex.calls = 0
        spec = pl.compose_persona(CountingCortex({"layout": "growth_mix", "slots": {}, "focus": {"metric": "X.NOPE"}}),
                                  ctx, "anything")
        self.assertEqual(spec["layout_variant"], "growth_mix")
        self.assertIsNone(spec["focus"]["metric"])                              # unknown id dropped
        bad = pl.compose_persona(CountingCortex({"layout": "made_up", "slots": {}}), ctx, "anything")
        self.assertEqual(bad["layout_variant"], "plan")
        n = CountingCortex.calls
        pl.compose_persona(None, ctx, "anything", variant="question", reuse=spec)
        self.assertEqual(CountingCortex.calls, n)


class FocusTagTests(unittest.TestCase):
    setUp, ctx, build = tp.PersonaTests.setUp, tp.PersonaTests.ctx, tp.PersonaTests.build

    def test_answer_first_without_a_named_breakdown_is_not_tagged(self):
        # Cortex chose "Answer first" but the person named no breakdown: lead tile uses the main breakdown, untagged
        ctx = self.ctx("executives")[0]
        cx = tp.StubCortex({"layout": "question", "slots": {}, "focus": {"metric": "ORDERS.SALES", "dimension": None}})
        spec = pl.compose_persona(cx, ctx, "give me a view of sales")
        self.assertFalse(any(c.get("focus") for p in spec["pages"] for c in p["components"]))
        forced = pl.compose_persona(None, ctx, "give me a view of sales", variant="question", reuse=spec)
        first = forced["pages"][0]["components"][0]
        self.assertEqual(first["type"], "ranked_bar")
        self.assertFalse(first.get("focus"))                      # main breakdown, not "Your question"
        # a trend question is a real question: the trend tile is tagged
        trend = pl.compose_persona(cx, ctx, "how are sales trending this month")
        self.assertTrue(any(c.get("focus") and c["type"] == "trend_chart"
                            for p in trend["pages"] for c in p["components"]))

    def test_kpi_thumbnails_know_how_many_cards(self):
        ctx = self.ctx("executives")[0]
        base = pl.compose_persona(None, ctx, "")
        kpi = next(t for o in base["layout_options"] for t in o["tiles"] if t["type"] in ("kpi_plan", "kpi_grid"))
        self.assertGreaterEqual(kpi["n"], 4)


class HonestyTests(unittest.TestCase):
    setUp, ctx, build = tp.PersonaTests.setUp, tp.PersonaTests.ctx, tp.PersonaTests.build

    def test_plan_words_only_when_there_is_a_plan(self):
        self.assertEqual(pl.without_plan("Sales & Growth vs Plan YTD"), "Sales & Growth vs last year YTD")
        self.assertEqual(pl.without_plan("Year vs plan brief"), "Year vs last year brief")
        ctx = self.ctx("executives")[0]
        self.assertTrue(pl.has_plan(ctx, {"headline_kpis": ["ORDERS.SALES"]}))       # PLAN_SALES exists here
        self.assertFalse(pl.has_plan(ctx, {"headline_kpis": ["ORDERS.PROFIT"]}))

    def test_tile_subtitle_is_never_the_instruction(self):
        ctx = self.ctx("executives")[0]
        goal = "Show executives Sales growth with Sales metrics for year-to-date outcomes"
        spec = pl.compose_persona(None, ctx, goal, asked=goal)
        for p in spec["pages"]:
            for c in p["components"]:
                self.assertNotIn("Show executives", c.get("question") or "")
        f = {"metric": "ORDERS.SALES", "dimension": None}
        self.assertEqual(pl.focus_tile(ctx, f, "how are sales trending?", {})["question"], "how are sales trending?")
        self.assertEqual(pl.focus_tile(ctx, f, "show me sales growth please", {})["question"], "How is Sales moving?")

    def test_margin_is_money_and_ratio_changes_are_points(self):
        import engine
        self.assertEqual(engine.fmt_kind("GROSS_MARGIN", 15_600_000.0), "currency")
        self.assertEqual(engine.fmt_kind("GROSS_MARGIN", 0.31), "percent")
        self.assertEqual(engine.fmt_kind("DISCOUNT_RATE", 0.047), "percent")


if __name__ == "__main__":
    unittest.main()
