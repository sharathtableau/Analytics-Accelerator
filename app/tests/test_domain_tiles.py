"""Analysis tiles (domain_tiles.py) over the real Finance and CPG pack data (fake_domains.py): each tile finds the
story the data holds, its numbers add up, and the layouts built from the domain packs compute without errors."""
import datetime as dt
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "streamlit"))
sys.path.insert(0, str(HERE))
os.environ["AA_FAKE_DOMAINS"] = "1"

import domain_packs  # noqa: E402
import fake_domains  # noqa: E402
from composer import DataContext, Governance, Validator  # noqa: E402
from engine import Engine  # noqa: E402
from fake_snowflake import FakeSession  # noqa: E402
from inventory import build_profile, infer_bindings  # noqa: E402
from persona_layouts import compose_persona  # noqa: E402
from semantic_catalog import describe_semantic_view, metric_dimension_map  # noqa: E402
from semantic_query import SemanticQuery  # noqa: E402
from test_composer import FEATURES  # noqa: E402

TODAY = dt.date(2026, 10, 22)
HAVE_DATA = (fake_domains.SETUP / "finance" / "data" / "finance_fact_credit_week.csv").exists()


@unittest.skipUnless(HAVE_DATA, "pack CSVs not in this package")
class DomainTileTests(unittest.TestCase):
    views = {}

    @classmethod
    def load(cls, fqn, domain, aud):
        key = (fqn, domain, aud)
        if key not in cls.views:
            s = FakeSession(fail_top_insights=False)
            model = describe_semantic_view(s, fqn)
            model.metric_dims = metric_dimension_map(s, model)
            b = infer_bindings(model)
            distinct = SemanticQuery(s, model).distinct_counts([d.id for d in model.categorical_dimensions])
            prof = build_profile(s, model, b, aud, FEATURES, today=TODAY)
            cls.views[key] = (s, model, b, prof, DataContext(model, b, prof, distinct, aud, domain))
        return cls.views[key]

    def engine(self, fqn, aud="managers"):
        s, model, b, prof, ctx = self.load(fqn, "", aud)
        return Engine(s, model, b, prof, None, None, {}, []), model

    @staticmethod
    def ids(model):
        return {m.name: m.id for m in model.metrics}, {d.name: d.id for d in model.categorical_dimensions}

    # ---------------------------------------------------------------- finance
    def test_outlier_lines_highlight_the_deteriorating_segment(self):
        e, model = self.engine(fake_domains.FIN)
        m, d = self.ids(model)
        out = e.outlier_lines({"metric_id": m["DELINQUENCY_RATE"], "dimension": d["SEGMENT_NAME"]})
        self.assertEqual([x["name"] for x in out["series"] if x["highlight"]], ["Near-Prime Revolver"])
        self.assertTrue(out["finding"].startswith("Near-Prime Revolver averaged"))
        self.assertIn("on a year earlier", out["finding"])

    def test_reference_line_breach_is_highlighted(self):
        e, model = self.engine(fake_domains.FIN)
        m, d = self.ids(model)
        out = e.outlier_lines({"metric_id": m["REWARDS_TO_INTERCHANGE_RATIO"], "dimension": d["PRODUCT_NAME"],
                               "opts": {"reference": 0.85, "better": "down", "filter": {d["PRODUCT_TYPE"]: ["Credit Card"]}}})
        self.assertEqual([x["name"] for x in out["series"] if x["highlight"]], ["Keystone Travel Signature Card"])
        self.assertEqual(len(out["series"]), 4)                 # cards only: the filter applies
        self.assertIn("above the 85.0% line", out["finding"])

    def test_level_bars_around_zero(self):
        e, model = self.engine(fake_domains.FIN)
        m, d = self.ids(model)
        out = e.change_bars({"metric_id": m["RISK_ADJUSTED_YIELD"], "dimension": d["SEGMENT_NAME"],
                             "opts": {"mode": "level", "reference": 0, "better": "up"}})
        below = [r["segment"] for r in out["rows"] if r["current"] < 0]
        self.assertEqual(set(below), {"Near-Prime Revolver", "Subprime Builder"})
        self.assertEqual(out["rows"][0]["segment"], "Subprime Builder")     # worst first
        gap = e.change_bars({"metric_id": m["RATE_GAP"], "metric2_id": m["DEPOSIT_BALANCE"], "dimension": d["SEGMENT_NAME"],
                             "opts": {"mode": "level", "reference": 0, "better": "down"}})
        self.assertTrue(gap["finding"].startswith("Only Mass Affluent Saver is above 0"))
        mas = next(r for r in gap["rows"] if r["segment"] == "Mass Affluent Saver")
        self.assertLess(mas["m2_change"], -0.05)

    def test_change_bars_compare_whole_windows_with_last_year(self):
        e, model = self.engine(fake_domains.FIN)
        m, d = self.ids(model)
        out = e.change_bars({"metric_id": m["NET_CHARGEOFFS"], "dimension": d["SEGMENT_NAME"]})
        self.assertEqual(out["base_label"], "same weeks last year")
        self.assertEqual(out["current_label"], "last 13 weeks")
        top = out["rows"][0]
        self.assertEqual(top["segment"], "Near-Prime Revolver")
        self.assertAlmostEqual(top["change"], (top["current"] - top["base"]) / top["base"])

    def test_ageing_stack_shows_buckets_of_the_worst_segment(self):
        e, model = self.engine(fake_domains.FIN)
        m, d = self.ids(model)
        out = e.stacked_trend({"metrics": [m["DPD_30_BALANCE"], m["DPD_60_BALANCE"], m["DPD_90_BALANCE"]],
                               "dimension": d["SEGMENT_NAME"], "metric2_id": m["DELINQUENCY_RATE"],
                               "opts": {"cumulative": True}})
        self.assertEqual(out["focus"], "Near-Prime Revolver")
        self.assertEqual(out["series_names"], ["30–59 days", "60–89 days", "90+ days"])
        last = out["bars"][-1]
        dpd30 = e.outlier_lines({"metric_id": m["DPD_30_BALANCE"], "dimension": d["SEGMENT_NAME"]})
        np_now = next(x for x in dpd30["series"] if x["name"] == "Near-Prime Revolver")["now"]
        self.assertAlmostEqual(last["total"], np_now, delta=1)   # buckets add back up to the 30+ balance

    # ---------------------------------------------------------------- CPG
    def test_velocity_split_adds_up_and_finds_the_velocity_problem(self):
        e, model = self.engine(fake_domains.CPG)
        m, d = self.ids(model)
        out = e.velocity_split({"metric_id": m["POS_DOLLARS"], "metric2_id": m["ACV_DISTRIBUTION"],
                                "dimension": d["PRODUCT_NAME"], "opts": {"filter": {d["CHANNEL"]: ["Wholesale"]}}})
        for r in out["rows"]:
            self.assertAlmostEqual(r["distribution_effect"] + r["velocity_effect"], r["current"] - r["base"], delta=1)
        worst = min(out["rows"], key=lambda r: r["total_effect"])
        self.assertEqual(worst["segment"], "Running Shoes")
        self.assertLess(worst["velocity_effect"], 5 * worst["distribution_effect"])     # both negative, velocity dominates
        self.assertTrue(out["finding"].startswith("Running Shoes -17%"))

    def test_gross_to_net_reconciles(self):
        e, model = self.engine(fake_domains.CPG)
        m, _ = self.ids(model)
        steps = [{"metric": m["GROSS_SALES"], "op": "start"}, {"metric": m["TRADE_SPEND"], "op": "minus"},
                 {"metric": m["NET_SALES"], "op": "total"}, {"metric": m["RETURN_DOLLARS"], "op": "minus"},
                 {"metric": None, "op": "total", "label": "Net of returns"}]
        out = e.metric_waterfall({"opts": {"steps": steps}})
        self.assertEqual(out["notes"], [])
        self.assertTrue(all(s["reconciled"] for s in out["steps"] if s["kind"] == "end"))
        bad = e.metric_waterfall({"opts": {"steps": [steps[0], steps[2]]}})       # net sales != gross sales
        self.assertTrue(bad["notes"])

    def test_promotions_judged_event_by_event(self):
        e, model = self.engine(fake_domains.CPG)
        m, d = self.ids(model)
        out = e.scatter({"metric_id": m["PROMO_SPEND"], "metric2_id": m["PROMO_ROI"], "dimension": d["PROMO_ID"],
                         "dimension2": d["PROMO_TYPE"], "opts": {"periods": 52, "reference_y": 0, "noun": "promotions"}})
        below = [p for p in out["points"] if p["y"] < 0]
        self.assertTrue(out["finding"].startswith(f"{len(below)} of {len(out['points'])} promotions below"))
        self.assertTrue(all(p.get("group") for p in out["points"]))
        tactic = e.change_bars({"metric_id": m["PROMO_ROI"], "dimension": d["PROMO_TYPE"],
                                "opts": {"mode": "level", "reference": 0, "periods": 52}})
        self.assertTrue(all(r["current"] > 0 for r in tactic["rows"]))    # the averages hide the losing events

    def test_weeks_of_supply_outlier_and_band(self):
        e, model = self.engine(fake_domains.CPG)
        m, d = self.ids(model)
        wholesale = {"filter": {d["CHANNEL"]: ["Wholesale"]}}
        out = e.outlier_lines({"metric_id": m["WEEKS_OF_SUPPLY"], "dimension": d["PRODUCT_NAME"],
                               "opts": {"band": [6, 12], "better": "down", "smooth": 4, **wholesale}})
        self.assertEqual([x["name"] for x in out["series"] if x["highlight"]], ["Running Shoes"])
        hm = e.heatmap({"metric_id": m["WEEKS_OF_SUPPLY"], "dimension": d["CUSTOMER_NAME"], "dimension2": d["PRODUCT_NAME"],
                        "opts": {"band": [6, 12], "better": "down", **wholesale}})
        self.assertIn("Running Shoes", hm["finding"])
        self.assertNotIn("Apex Owned Retail", hm["rows"])          # DTC accounts are filtered out

    def test_neutral_change_bars_sort_biggest_first(self):
        e, model = self.engine(fake_domains.CPG)
        m, d = self.ids(model)
        out = e.change_bars({"metric_id": m["DTC_MIX"], "dimension": d["PRODUCT_NAME"], "opts": {"better": "none"}})
        self.assertEqual(out["rows"][0]["segment"], "Womens Leggings")
        self.assertTrue(out["finding"].startswith("Womens Leggings up most"))

    # ---------------------------------------------------------------- packs end to end
    def test_every_pack_layout_builds_without_errors(self):
        for fqn, dom, pack in ((fake_domains.FIN, "finance", domain_packs.FINANCE), (fake_domains.CPG, "cpg", domain_packs.CPG)):
            for aud, variants in pack.items():
                for v in variants:
                    s, model, b, prof, ctx = self.load(fqn, dom, aud)
                    spec = compose_persona(None, ctx, v["title"], variant=v["id"])
                    built = {c["title"] for p in spec["pages"] for c in p["components"]}
                    for pg in v["pages"]:
                        for t in pg["tiles"]:
                            self.assertIn(t["title"], built, f"{v['id']}: '{t['title']}' was dropped")
                    res, _ = Engine(s, model, b, prof, None, None, {}, []).build(spec)
                    for cid, r in res.items():
                        self.assertEqual(r["status"], "ready", f"{v['id']} {cid}: {r.get('error')}")
                        comp = next(c for p in spec["pages"] for c in p["components"]
                                    if f"{p['page_id']}/{c['component_id']}" == cid)
                        if comp["type"] in ("outlier_lines", "change_bars", "velocity_split", "stacked_trend",
                                            "metric_waterfall", "driver_split"):
                            self.assertTrue(r["data"]["headline"], f"{v['id']} {cid} has no finding")


class TileOptionTests(unittest.TestCase):
    def setUp(self):
        from fake_snowflake import SV
        from test_composer import TODAY as T0
        self.s = FakeSession(fail_top_insights=False)
        self.model = describe_semantic_view(self.s, SV)
        self.b = infer_bindings(self.model)
        distinct = SemanticQuery(self.s, self.model).distinct_counts([d.id for d in self.model.categorical_dimensions])
        prof = build_profile(self.s, self.model, self.b, "managers", FEATURES, today=T0)
        self.ctx = DataContext(self.model, self.b, prof, distinct, "managers")

    def tile(self, raw):
        return Validator(self.ctx, Governance()).tile(raw, "P", set())

    def test_options_are_sanitised(self):
        t = self.tile({"type": "change_bars", "metric": "PROFIT", "dimension": "REGION",
                       "opts": {"reference": "12", "better": "sideways", "mode": "level", "evil": "DROP TABLE",
                                "filter": {"SEGMENT": ["Consumer"], "NOPE": ["x"]}, "periods": 9999, "label": "x" * 99}})
        self.assertEqual(t["opts"]["reference"], 12.0)
        self.assertNotIn("better", t["opts"])
        self.assertNotIn("evil", t["opts"])
        self.assertEqual(t["opts"]["periods"], 104)
        self.assertEqual(len(t["opts"]["label"]), 40)
        self.assertEqual(list(t["opts"]["filter"]), [next(d.id for d in self.model.categorical_dimensions if d.name == "SEGMENT")])

    def test_analysis_tiles_need_their_metrics(self):
        self.assertIsNone(self.tile({"type": "driver_split", "metrics": ["SALES", "ORDER_COUNT"]}))
        self.assertIsNotNone(self.tile({"type": "driver_split", "metrics": ["SALES", "ORDER_COUNT", "QUANTITY"]}))
        self.assertIsNone(self.tile({"type": "metric_waterfall", "opts": {"steps": [["SALES", "minus"], ["PROFIT", "total"]]}}))
        ok = self.tile({"type": "metric_waterfall", "opts": {"steps": [["SALES", "start"], ["PROFIT", "minus"], [None, "total", "Rest"]]}})
        self.assertEqual([s["op"] for s in ok["opts"]["steps"]], ["start", "minus", "total"])

    def test_extra_domain_packs_come_after_the_generic_layouts(self):
        from persona_layouts import pick_variant, variant_ids
        saved = domain_packs.PACKS["retail"]
        domain_packs.PACKS["retail"] = {"managers": [{"id": "r_x", "title": "Extra", "when": "x", "summary": "x",
            "pages": [{"label": "X", "question": "x", "tiles": [{"type": "change_bars", "title": "Profit by region",
                       "metric": "PROFIT", "dimension": "REGION", "width": 6}]}]}]}
        saved_rules = domain_packs.RULES["retail"]
        domain_packs.RULES["retail"] = {"managers": [("r_x", r"regional profit")]}
        try:
            self.ctx.domain = "retail"
            ids = variant_ids("managers", self.ctx)
            self.assertEqual(ids[-1], "r_x")
            self.assertNotEqual(pick_variant("managers", "weekly review", self.ctx), "r_x")
            self.assertEqual(pick_variant("managers", "show regional profit", self.ctx), "r_x")
        finally:
            domain_packs.PACKS["retail"] = saved
            domain_packs.RULES["retail"] = saved_rules


if __name__ == "__main__":
    unittest.main()


@unittest.skipUnless(HAVE_DATA, "pack CSVs not in this package")
class PersonaBuildTests(unittest.TestCase):
    def test_each_persona_gets_its_own_layout(self):
        for fqn, dom in ((fake_domains.FIN, "finance"), (fake_domains.CPG, "cpg")):
            for per in domain_packs.personas(dom):
                s, model, b, prof, ctx = DomainTileTests.load(fqn, dom, per["audience"])
                spec = compose_persona(None, ctx, per["questions"][0], variant=per["layout"], asked=per["questions"][0])
                self.assertEqual(spec["layout_variant"], per["layout"], per["id"])


@unittest.skipUnless(HAVE_DATA, "pack CSVs not in this package")
class PersonaIdeaTests(unittest.TestCase):
    """Home ideas for a persona come from that persona's decisions and questions, over the workspace's metrics."""

    @staticmethod
    def catalog(fqn):
        import home
        s = FakeSession(fail_top_insights=False)
        return s, home.build_catalog([{"fqn": fqn, "name": fqn.split(".")[-1]}], lambda f: describe_semantic_view(s, f),
                                     {fqn: ""})

    def test_cortex_ideas_are_persona_specific_and_governed(self):
        import home
        from ai_services import Cortex
        for fqn, dom in ((fake_domains.FIN, "finance"), (fake_domains.CPG, "cpg")):
            s, cat = self.catalog(fqn)
            labels = {m["label"] for m in cat[0]["metrics"]}
            for per in domain_packs.personas(dom):
                if len(per["questions"]) < 3:
                    continue
                ideas = home.persona_ideas(Cortex(s, "WBR_DB.ANALYTICS_ENTERPRISE"), cat, per, "Co")
                self.assertGreaterEqual(len(ideas), 3, per["id"])
                titles = [x["title"] for x in ideas]
                self.assertEqual(len(titles), len(set(titles)))                  # duplicate dropped
                self.assertNotIn("Only invented", titles)                         # no governed metric: dropped
                for x in ideas:
                    self.assertEqual((x["persona"], x["audience"]), (per["id"], per["audience"]))
                    self.assertTrue(set(x["metrics"]) <= labels, x["metrics"])   # 'Invented Metric' removed
                    self.assertIn(per["label"], x["goal"])

    def test_fallback_uses_the_persona_questions_and_layout_metrics(self):
        import home
        s, cat = self.catalog(fake_domains.FIN)
        per = domain_packs.persona("finance", "fin_credit")
        ideas = home.persona_fallback(cat, per, domain_packs.persona_tiles("finance", "fin_credit"))
        self.assertEqual([x["title"] for x in ideas], [q.rstrip("?.")[:80] for q in per["questions"]])
        labels = {m["label"] for m in cat[0]["metrics"]}
        for x in ideas:
            self.assertTrue(x["metrics"] and set(x["metrics"]) <= labels)
            self.assertEqual(x["persona"], "fin_credit")
        # questions about different things get different metrics from the persona's layout
        self.assertGreater(len({tuple(x["metrics"]) for x in ideas}), 1)

    def test_every_pack_persona_has_layout_tiles(self):
        for dom in ("finance", "cpg", "retail"):
            for per in domain_packs.personas(dom):
                if per["layout"]:
                    self.assertTrue(domain_packs.persona_tiles(dom, per["id"]), per["id"])


@unittest.skipUnless(HAVE_DATA, "pack CSVs not in this package")
class PersonaIdeasV2Tests(unittest.TestCase):
    """Runtime, data-aware persona ideas: movers from governed SQL, Cortex writes, code keeps ideas in lane."""

    def setUp(self):
        import home
        from ai_services import Cortex
        self.home = home
        self.s, self.cat = PersonaIdeaTests.catalog(fake_domains.FIN)
        self.cx = Cortex(self.s, "WBR_DB.ANALYTICS_ENTERPRISE")
        self.per = domain_packs.persona("finance", "fin_credit")
        self.lane = home._labels_for(self.cat[0], domain_packs.lane_metrics("finance", "fin_credit"))

    def movers(self):
        e, model = DomainTileTests().engine(fake_domains.FIN)
        m, d = DomainTileTests.ids(model)
        out = []
        for name in ("DELINQUENCY_RATE", "NET_CHARGEOFFS"):
            r = e.change_bars({"metric_id": m[name], "dimension": d["SEGMENT_NAME"]})
            out.append({"metric": e.mlabel(m[name]), "dimension": "Segment",
                        "finding": f"{e.mlabel(m[name])} by segment: {r['finding']}"})
        return out

    def test_movers_come_from_governed_sql_and_find_the_story(self):
        mv = self.movers()
        self.assertIn("Near-Prime Revolver", mv[0]["finding"])

    def test_ideas_stay_in_lane_and_carry_the_exact_finding(self):
        mv = self.movers()
        ideas = self.home.persona_ideas(self.cx, self.cat, self.per, "Keystone", None,
                                        domain_packs.lens_seed("finance", "fin_credit"), self.lane, mv, "2026-10-18")
        lane = {x.lower() for x in self.lane}
        self.assertGreaterEqual(len(ideas), 3)
        self.assertNotIn("Out of lane", [x["title"] for x in ideas])
        for x in ideas:
            outside = [m for m in x["metrics"] if m.lower() not in lane]
            self.assertLessEqual(len(outside), 1, x["metrics"])          # at most one supporting metric
            self.assertTrue(any(m.lower() in lane for m in x["metrics"]))
        self.assertEqual(ideas[0]["signal"], mv[0]["finding"])          # SQL text, not the model's paraphrase

    def test_in_lane_rule(self):
        lane = {"a", "b"}
        self.assertTrue(self.home._in_lane(["A", "B"], lane))
        self.assertTrue(self.home._in_lane(["A", "X"], lane))
        self.assertFalse(self.home._in_lane(["A", "X", "Y"], lane))
        self.assertFalse(self.home._in_lane(["X"], lane))
        self.assertTrue(self.home._in_lane(["X"], set()))                # leadership: whole workspace

    def test_fallback_without_cortex_uses_the_movers(self):
        mv = self.movers()
        ideas = self.home.movers_fallback(self.cat, self.per, mv, self.lane)
        self.assertEqual([x["signal"] for x in ideas], [m["finding"] for m in mv])

    def test_typed_in_persona_is_drafted_from_real_metrics(self):
        d = self.home.draft_persona(self.cx, self.cat, "I'm a collections manager", "Keystone")
        labels = {m["label"] for m in self.cat[0]["metrics"]}
        self.assertEqual(d["label"], "Collections Manager")
        self.assertTrue(d["custom"] and d["audience"] == "managers")
        self.assertTrue(set(d["metrics"]) <= labels and "Made Up" not in d["metrics"])
        with self.assertRaises(ValueError):
            self.home.draft_persona(self.cx, self.cat, "hi", "Keystone")

    def test_every_built_in_persona_has_seeded_guidance(self):
        for dom in ("finance", "cpg", "retail"):
            for per in domain_packs.personas(dom):
                self.assertTrue(domain_packs.lens_seed(dom, per["id"]), per["id"])
