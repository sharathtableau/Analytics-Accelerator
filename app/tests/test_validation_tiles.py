"""QA-02 / QA-03 for the persona tiles and newer charts: every type passes on clean data and catches a planted error."""
import copy
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

RAW = {"pages": [{"label": "A", "tiles": [
    {"type": "kpi_plan", "metrics": ["ORDERS.SALES", "ORDERS.PROFIT", "ORDERS.PROFIT_RATIO"]},
    {"type": "ytd_trajectory", "metric": "ORDERS.SALES"},
    {"type": "scorecard", "metrics": ["ORDERS.SALES", "ORDERS.PROFIT", "ORDERS.PROFIT_RATIO"], "dimension": "ORDERS.REGION"},
    {"type": "status_tiles", "metrics": ["ORDERS.SALES", "ORDERS.QUANTITY"]},
    {"type": "pace_chart", "metric": "ORDERS.SALES"},
    {"type": "worklist", "metrics": ["ORDERS.SALES"], "dimensions": ["ORDERS.REGION", "ORDERS.CATEGORY"]},
]}, {"label": "B", "tiles": [
    {"type": "small_multiples", "metric": "ORDERS.SALES", "dimension": "ORDERS.REGION"},
    {"type": "scatter", "metric": "ORDERS.SALES", "metric2": "ORDERS.PROFIT", "dimension": "ORDERS.REGION"},
    {"type": "heatmap", "metric": "ORDERS.SALES", "dimension": "ORDERS.REGION", "dimension2": "ORDERS.CATEGORY"},
    {"type": "exception_table", "metric": "ORDERS.SALES", "dimension": "ORDERS.REGION"},
    {"type": "combo_chart", "metric": "ORDERS.SALES", "metric2": "ORDERS.PROFIT_RATIO"},
]}]}


class TileChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        s = FakeSession()
        model = describe_semantic_view(s, SV)
        b = infer_bindings(model)
        dist = SemanticQuery(s, model).distinct_counts([d.id for d in model.categorical_dimensions])
        prof = build_profile(s, model, b, "executives", FEATURES, today=TODAY)
        pages = validate_layout(DataContext(model, b, prof, dist, "executives"), RAW, Governance())
        cls.spec = {"pages": pages}
        cache = {}
        e = Engine(s, model, b, prof, None, Store(s, APP), cache)
        cls.res, _ = e.build(cls.spec)
        cls.v = V.Validator(s, Engine(s, model, b, prof, None, Store(s, APP), cache), V.Physical.describe(s, SV))
        cls.rep = cls.v.run(cls.spec, [p["page_id"] for p in pages], cls.res, e.tile_keys, cache)
        cls.by = {}
        for p in pages:
            for c in p["components"]:
                cid = f"{p['page_id']}/{c['component_id']}"
                cls.by[c["type"]] = (c, cls.res[cid]["data"], cls.rep["tiles"][cid])

    def checks(self, t):
        return {c["id"]: c["status"] for c in self.by[t][2]["checks"]}

    def test_every_type_now_has_arithmetic_and_reconciliation(self):
        want = {"kpi_plan": ("QA-02", "QA-03"), "ytd_trajectory": ("QA-02", "QA-03"), "scorecard": ("QA-02", "QA-03"),
                "status_tiles": ("QA-02",), "pace_chart": ("QA-02",), "worklist": ("QA-02",),
                "small_multiples": ("QA-02", "QA-03"), "scatter": ("QA-03",), "heatmap": ("QA-02", "QA-03"),
                "exception_table": ("QA-02", "QA-03"), "combo_chart": ("QA-02", "QA-03")}
        for t, ids in want.items():
            got = self.checks(t)
            for i in ids:
                self.assertEqual(got.get(i), "pass", f"{t} {i}: {got}")

    def bad(self, t, fn, qa):
        comp, data, _ = self.by[t]
        d = copy.deepcopy(data)
        fn(d)
        out = (self.v.qa02 if qa == "QA-02" else self.v.qa03)(comp, d)
        self.assertEqual(out["status"], "mismatch", f"{t}: {out}")

    def test_planted_display_errors_are_caught(self):
        self.bad("kpi_plan", lambda d: d["items"][0].update(delta=d["items"][0]["delta"] + 0.05), "QA-02")
        self.bad("scorecard", lambda d: d["rows"][1]["cells"][0].update(delta=0.5), "QA-02")
        self.bad("status_tiles", lambda d: d["items"][0].update(delta=-0.2), "QA-02")
        self.bad("pace_chart", lambda d: d.update(projected=(d.get("projected") or 0) * 1.3 + 1), "QA-02")
        self.bad("worklist", lambda d: d["rows"][0].update(severity="High" if d["rows"][0]["severity"] != "High" else "Watch"), "QA-02")
        self.bad("exception_table", lambda d: d["rows"][0].update(direction="below" if d["rows"][0]["direction"] == "above" else "above"), "QA-02")
        self.bad("ytd_trajectory", lambda d: d["series"][0]["values"].__setitem__(-1, 123.0), "QA-02")
        self.bad("combo_chart", lambda d: d["points"].reverse(), "QA-02")

    def test_planted_reconciliation_errors_are_caught(self):
        self.bad("kpi_plan", lambda d: d["items"][0]["spark"].__setitem__(0, d["items"][0]["spark"][0] * 2), "QA-03")
        self.bad("ytd_trajectory", lambda d: d["series"][0].update(values=[(v or 0) * 1.02 if v is not None else None
                                                                          for v in d["series"][0]["values"]]), "QA-03")
        self.bad("scorecard", lambda d: d["rows"][0]["cells"][0].update(value=d["rows"][0]["cells"][0]["value"] + 500), "QA-03")
        self.bad("small_multiples", lambda d: [p.update(value=(p["value"] or 0) + 99) for p in d["panels"][0]["points"]], "QA-03")
        self.bad("scatter", lambda d: d["points"][0].update(x=d["points"][0]["x"] * 3), "QA-03")
        self.bad("exception_table", lambda d: d["rows"][0].update(current=d["rows"][0]["current"] * 1.1), "QA-03")
        self.bad("combo_chart", lambda d: d["points"][-1].update(line=d["points"][-1]["line"] + 0.02), "QA-03")

    def test_ratio_metrics_are_not_forced_to_add_up(self):
        comp, data, _ = self.by["scorecard"]
        out = self.v.qa03(comp, data)
        self.assertIn("Profit Ratio not additive", out["summary"])

    def test_change_helper(self):
        self.assertAlmostEqual(V._chg("percent", 0.12, 0.10), 0.02)
        self.assertAlmostEqual(V._chg("currency", 110, 100), 0.10)
        self.assertIsNone(V._chg("currency", 110, 0))


if __name__ == "__main__":
    unittest.main()
