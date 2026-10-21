"""QA validation: independent recompute, display arithmetic, reconciliation, joins, periods, grounding."""
import datetime as dt
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "streamlit"))
sys.path.insert(0, str(HERE))

from fake_snowflake import FakeSession, SV  # noqa: E402
from engine import Engine  # noqa: E402
from inventory import build_profile, infer_bindings  # noqa: E402
from layout_catalog import bind_template, select_template  # noqa: E402
from semantic_catalog import Field, SemanticModel, describe_semantic_view  # noqa: E402
from store import Store  # noqa: E402
import validation as V  # noqa: E402

APP = "WBR_DB.ANALYTICS_ENTERPRISE"
TODAY = dt.date(2025, 1, 2)
FEATURES = {"forecast": True, "top_insights": True, "complete": True}


def multi_physical():
    rows = [
        {"object_kind": "TABLE", "object_name": "ORDERS", "property": "BASE_TABLE_DATABASE_NAME", "property_value": "DB"},
        {"object_kind": "TABLE", "object_name": "ORDERS", "property": "BASE_TABLE_SCHEMA_NAME", "property_value": "S"},
        {"object_kind": "TABLE", "object_name": "ORDERS", "property": "BASE_TABLE_NAME", "property_value": "ORDERS_T"},
        {"object_kind": "TABLE", "object_name": "ORDERS", "property": "PRIMARY_KEY", "property_value": '["ORDER_ID"]'},
        {"object_kind": "TABLE", "object_name": "CUSTOMERS", "property": "BASE_TABLE_NAME", "property_value": "CUST_T"},
        {"object_kind": "TABLE", "object_name": "CUSTOMERS", "property": "PRIMARY_KEY", "property_value": '["CUST_ID"]'},
        {"object_kind": "TABLE", "object_name": "REGIONS", "property": "BASE_TABLE_NAME", "property_value": "REG_T"},
        {"object_kind": "TABLE", "object_name": "REGIONS", "property": "PRIMARY_KEY", "property_value": '["REGION_ID"]'},
        {"object_kind": "RELATIONSHIP", "object_name": "ORD_CUST", "parent_entity": "ORDERS", "property": "TABLE", "property_value": "ORDERS"},
        {"object_kind": "RELATIONSHIP", "object_name": "ORD_CUST", "property": "REF_TABLE", "property_value": "CUSTOMERS"},
        {"object_kind": "RELATIONSHIP", "object_name": "ORD_CUST", "property": "FOREIGN_KEY", "property_value": '["CUST_ID"]'},
        {"object_kind": "RELATIONSHIP", "object_name": "ORD_CUST", "property": "REF_KEY", "property_value": '["CUST_ID"]'},
        {"object_kind": "RELATIONSHIP", "object_name": "CUST_REG", "property": "TABLE", "property_value": "CUSTOMERS"},
        {"object_kind": "RELATIONSHIP", "object_name": "CUST_REG", "property": "REF_TABLE", "property_value": "REGIONS"},
        {"object_kind": "RELATIONSHIP", "object_name": "CUST_REG", "property": "FOREIGN_KEY", "property_value": "REGION_ID"},
        {"object_kind": "FACT", "object_name": "NET", "parent_entity": "ORDERS", "property": "EXPRESSION", "property_value": "AMOUNT - DISCOUNT"},
        {"object_kind": "DIMENSION", "object_name": "ORDER_DATE", "parent_entity": "ORDERS", "property": "EXPRESSION", "property_value": "orders.order_date"},
        {"object_kind": "DIMENSION", "object_name": "SEGMENT", "parent_entity": "CUSTOMERS", "property": "EXPRESSION", "property_value": "UPPER(SEG)"},
        {"object_kind": "DIMENSION", "object_name": "REGION", "parent_entity": "REGIONS", "property": "EXPRESSION", "property_value": "REGION_NAME"},
        {"object_kind": "METRIC", "object_name": "NET_SALES", "parent_entity": "ORDERS", "property": "EXPRESSION", "property_value": "SUM(orders.net)"},
        {"object_kind": "METRIC", "object_name": "ORDERS", "parent_entity": "ORDERS", "property": "EXPRESSION", "property_value": "COUNT(DISTINCT order_id)"},
        {"object_kind": "METRIC", "object_name": "AOV", "parent_entity": "ORDERS", "property": "EXPRESSION", "property_value": "orders.net_sales / orders.orders"},
        {"object_kind": "METRIC", "object_name": "ENDING_NET", "parent_entity": "ORDERS", "property": "EXPRESSION", "property_value": "SUM(orders.net)"},
        {"object_kind": "METRIC", "object_name": "ENDING_NET", "parent_entity": "ORDERS", "property": "NON_ADDITIVE_DIMENSIONS", "property_value": '["ORDERS.ORDER_DATE"]'},
        {"object_kind": "METRIC", "object_name": "FIRST_NET", "parent_entity": "ORDERS", "property": "EXPRESSION", "property_value": "NON ADDITIVE BY (orders.order_date DESC) AS SUM(orders.net)"},
        {"object_kind": "METRIC", "object_name": "RATIO_END", "parent_entity": "ORDERS", "property": "EXPRESSION", "property_value": "orders.ending_net / orders.net_sales"},
        {"object_kind": "METRIC", "object_name": "CUSTOMERS_N", "parent_entity": "CUSTOMERS", "property": "EXPRESSION", "property_value": "COUNT(cust_id)"},
    ]
    return V.Physical.parse("DB.S.SALES_SV", rows)


def multi_model():
    f = lambda e, n, k: Field(entity=e, name=n, kind=k)
    return SemanticModel(fqn="DB.S.SALES_SV", comment="", tables=["ORDERS", "CUSTOMERS", "REGIONS"],
                         dimensions=[f("ORDERS", "ORDER_DATE", "dimension"), f("CUSTOMERS", "SEGMENT", "dimension"),
                                     f("REGIONS", "REGION", "dimension")],
                         metrics=[f("ORDERS", "NET_SALES", "metric"), f("ORDERS", "AOV", "metric"),
                                  f("CUSTOMERS", "CUSTOMERS_N", "metric")], facts=[])


class TranslatorTests(unittest.TestCase):
    def setUp(self):
        self.p = multi_physical()
        self.t = V.Translator(self.p, multi_model())

    def test_parse_tables_keys_relationships(self):
        self.assertEqual(self.p.tables["ORDERS"]["fqn"], "DB.S.ORDERS_T")
        self.assertEqual(self.p.tables["CUSTOMERS"]["fqn"], "DB.S.CUST_T")      # db/schema default to the view's
        self.assertEqual(self.p.tables["ORDERS"]["pk"], ["ORDER_ID"])
        rel = {r["name"]: r for r in self.p.rels}
        self.assertEqual(rel["CUST_REG"]["right_cols"], ["REGION_ID"])           # REF_KEY falls back to the PK
        self.assertEqual(rel["CUST_REG"]["left_cols"], ["REGION_ID"])

    def test_multi_hop_join_and_expressions(self):
        sql, rels = self.t.derived({"dims": ["REGIONS.REGION AS D0", "DATE_TRUNC('month', ORDERS.ORDER_DATE) AS PERIOD"],
                                    "metrics": ["ORDERS.NET_SALES AS M0"],
                                    "where": "CUSTOMERS.SEGMENT IN ('CUSTOMERS.SEGMENT', 'Corp')"})
        self.assertIn("FROM DB.S.ORDERS_T T0", sql)
        self.assertIn("LEFT JOIN DB.S.CUST_T T1 ON T0.CUST_ID = T1.CUST_ID", sql)
        self.assertIn("LEFT JOIN DB.S.REG_T T2 ON T1.REGION_ID = T2.REGION_ID", sql)
        self.assertIn("SUM((T0.AMOUNT - T0.DISCOUNT))", sql)                 # fact expanded to columns
        self.assertIn("(T2.REGION_NAME) AS D0", sql)
        self.assertIn("DATE_TRUNC('month', (T0.order_date)) AS PERIOD", sql)    # self-named dimension is a column
        self.assertIn("IN ('CUSTOMERS.SEGMENT', 'Corp')", sql)                   # literals never rewritten
        self.assertIn("UPPER(T1.SEG)", sql)
        self.assertIn("GROUP BY 1, 2", sql)
        self.assertEqual([r["name"] for r in rels], ["ORD_CUST", "CUST_REG"])

    def test_metric_of_metrics_and_distinct(self):
        sql, _ = self.t.derived({"dims": [], "metrics": ["ORDERS.AOV AS M0"], "where": ""})
        self.assertIn("COUNT(DISTINCT T0.order_id)", sql)
        self.assertIn("/", sql)
        self.assertNotIn("GROUP BY", sql)
        self.assertNotIn("JOIN", sql)                                            # no dimension: no join needed

    def test_metrics_from_two_tables_are_aggregated_separately(self):
        sql, _ = self.t.derived({"dims": ["REGIONS.REGION AS D0"],
                                 "metrics": ["ORDERS.NET_SALES AS M0", "CUSTOMERS.CUSTOMERS_N AS M1"], "where": ""})
        self.assertIn("UNION ALL", sql)
        self.assertIn("MAX(M0) AS M0", sql)
        self.assertIn("NULL AS M1", sql)
        self.assertIn("FROM DB.S.CUST_T T0", sql)                                # customers counted at their own grain

    def test_union_parts_list_columns_in_the_same_order(self):
        sql, _ = self.t.derived({"dims": ["REGIONS.REGION AS D0"],
                                 "metrics": ["CUSTOMERS.CUSTOMERS_N AS M0", "ORDERS.NET_SALES AS M1", "ORDERS.AOV AS M2"],
                                 "where": ""})
        parts = sql.split("UNION ALL")
        self.assertEqual(len(parts), 2)
        for part in parts:
            sel = part[part.index("SELECT D0") if "SELECT D0" in part else part.index("SELECT ("):]
            i0, i1, i2 = sel.index(" AS M0"), sel.index(" AS M1"), sel.index(" AS M2")
            self.assertLess(i0, i1)
            self.assertLess(i1, i2)

    def test_semi_additive_metric_uses_latest_date_per_group(self):
        sql, _ = self.t.derived({"dims": ["DATE_TRUNC('month', ORDERS.ORDER_DATE) AS PERIOD"],
                                 "metrics": ["ORDERS.NET_SALES AS M0", "ORDERS.ENDING_NET AS M1"], "where": ""})
        self.assertIn("UNION ALL", sql)                                    # own part, so the date rule hits only it
        self.assertIn("IN (SELECT DATE_TRUNC('month', (T0.order_date)), MAX((T0.order_date))", sql)
        sql2, _ = self.t.derived({"dims": [], "metrics": ["ORDERS.FIRST_NET AS M0"], "where": ""})
        self.assertIn("MIN((T0.order_date))", sql2)                        # DESC -> earliest
        self.assertNotIn("NON ADDITIVE", sql2)
        with self.assertRaises(V.Unchecked):
            self.t.derived({"dims": [], "metrics": ["ORDERS.RATIO_END AS M0"], "where": ""})

    def test_unreachable_table_is_not_checkable(self):
        with self.assertRaises(V.Unchecked):
            self.t.derived({"dims": ["ORDERS.ORDER_DATE AS D0"], "metrics": ["CUSTOMERS.CUSTOMERS_N AS M0"], "where": ""})
        with self.assertRaises(V.Unchecked):
            self.t.derived({"dims": [], "metrics": ["ORDERS.MADE_UP AS M0"], "where": ""})

    def test_custom_formula_and_adhoc_metrics(self):
        m = multi_model()
        m.virtual = {"ORDERS.NET_PER_CUSTOMER": ("FORMULA", ("/", ("m", "a"), ("m", "b")),
                                                 {"a": "ORDERS.NET_SALES", "b": "ORDERS.AOV"}),
                     "ORDERS.AVG_NET": ("AVG", "ORDERS.NET")}
        t = V.Translator(self.p, m)
        sql, _ = t.derived({"dims": [], "metrics": ["ORDERS.NET_PER_CUSTOMER AS M0", "ORDERS.AVG_NET AS M1"], "where": ""})
        self.assertIn("DIV0(", sql)
        self.assertIn("AVG((T0.AMOUNT - T0.DISCOUNT))", sql)

    def test_no_base_tables_is_unchecked(self):
        with self.assertRaises(V.Unchecked):
            V.Translator(V.Physical("X.Y.Z", {}, [], {}), multi_model())


class CompareTests(unittest.TestCase):
    def test_tolerance_and_empty_values(self):
        self.assertTrue(V.close(100.0, 100.00000001))
        self.assertFalse(V.close(100.0, 100.01))
        self.assertTrue(V.close(None, 0))
        self.assertFalse(V.close(None, 5))

    def test_limit_extra_rows_only_matter_above_the_cutoff(self):
        app = [{"d0": "A", "m0": 10.0}, {"d0": "B", "m0": 8.0}]
        ind = app + [{"d0": "C", "m0": 3.0}]
        self.assertTrue(V.compare_rows(app, ind, ["d0"], ["m0"], 2)["ok"])
        ind2 = app + [{"d0": "C", "m0": 9.0}]
        out = V.compare_rows(app, ind2, ["d0"], ["m0"], 2)
        self.assertFalse(out["ok"])
        self.assertEqual(out["extra"], ["C"])
        out = V.compare_rows(app, ind, ["d0"], ["m0"], None)      # no LIMIT: every base row must be on the tile
        self.assertEqual(out["extra"], ["C"])

    def test_dates_and_numbers_match_as_keys(self):
        app = [{"period": dt.date(2024, 1, 1), "m0": 1.0}]
        ind = [{"period": dt.datetime(2024, 1, 1), "m0": 1.0}]
        self.assertTrue(V.compare_rows(app, ind, ["period"], ["m0"], None)["ok"])

    def test_narrative_grounding(self):
        facts = ["Sales Nov 2024 = $212.3K (+34.6% vs Nov 2023, $157.7K)", "Profit Ratio = 10.9% (-0.7 percentage points)"]
        ok, bad = V.grounded("Sales reached $212K, up 35% on last year; margin 10.9% (-0.7 pt) across 4 regions in 2024.", facts)
        self.assertEqual(bad, [])
        self.assertGreaterEqual(len(ok), 4)
        _, bad = V.grounded("Sales hit $250K, up 41%.", facts)
        self.assertEqual(len(bad), 2)
        self.assertEqual(V.narrative_check("Sales hit $250K.", facts)["status"], "review")
        self.assertEqual(V.narrative_check("Sales held steady.", facts)["status"], "pass")


class ValidatorTests(unittest.TestCase):
    def setUp(self):
        self.s = FakeSession()
        self.model = describe_semantic_view(self.s, SV)
        self.b = infer_bindings(self.model)
        self.prof = build_profile(self.s, self.model, self.b, "executives", FEATURES, today=TODAY)
        sel = select_template("executives", self.prof.inventory(), user_selected_template_id="exec_growth_baseline")
        self.spec = bind_template(sel.template, self.prof.inventory())

    def run_all(self, opts=None, **fake):
        for k, v in fake.items():
            setattr(self.s, k, v)
        cache = {}
        e = Engine(self.s, self.model, self.b, self.prof, None, Store(self.s, APP), cache, opts=opts or {})
        res, _ = e.build(self.spec)
        e2 = Engine(self.s, self.model, self.b, self.prof, None, Store(self.s, APP), cache, opts=opts or {})
        rep = V.Validator(self.s, e2, V.Physical.describe(self.s, SV)).run(
            self.spec, [p["page_id"] for p in self.spec["pages"]], res, e.tile_keys, cache)
        return rep, res

    def test_every_tile_verified_against_base_table(self):
        rep, res = self.run_all()
        data_tiles = [k for k, v in res.items() if v["status"] == "ready" and not k.endswith("/actions")]
        self.assertEqual(set(rep["tiles"]), set(data_tiles))
        for cid, t in rep["tiles"].items():
            qa01 = next(c for c in t["checks"] if c["id"] == "QA-01")
            self.assertEqual(qa01["status"], "pass", (cid, qa01))
            self.assertIn("ORDERS_SAMPLE_SUPERSTORE", qa01["sql"]["independent"])
            self.assertNotIn("SEMANTIC_VIEW", qa01["sql"]["independent"])
            self.assertNotEqual(t["status"], "mismatch", cid)
        dash = {c["id"]: c for c in rep["dashboard"]}
        self.assertEqual(dash["QA-04"]["status"], "pass")
        self.assertEqual(dash["QA-05"]["status"], "pass", dash["QA-05"])
        self.assertTrue(any(r["label"].startswith("Data coverage") and r["ok"] for r in dash["QA-05"]["rows"]))
        self.assertLessEqual(rep["queries"], V.MAX_QUERIES + 2)
        self.assertTrue(all(sql.lstrip().upper().startswith("SELECT") for sql in self.s.base_sqls))   # read-only

    def test_planted_error_is_caught_on_the_right_tiles_only(self):
        rep, _ = self.run_all(base_skew={"PROFIT": 1.0005})
        bad = {cid for cid, t in rep["tiles"].items() if t["status"] == "mismatch"}
        self.assertTrue(bad)
        for cid in bad:
            qa01 = next(c for c in rep["tiles"][cid]["checks"] if c["id"] == "QA-01")
            self.assertEqual(qa01["status"], "mismatch")
            self.assertTrue(any(r.get("column") in ("Profit", "Profit Ratio") for r in qa01["rows"]), qa01["rows"][:2])
        sales_only = [cid for cid, t in rep["tiles"].items()
                      if all("PROFIT" not in (c.get("sql") or {}).get("dashboard", "") for c in t["checks"])]
        for cid in sales_only:
            self.assertNotEqual(rep["tiles"][cid]["status"], "mismatch", cid)

    def test_base_table_access_failure_is_never_a_pass(self):
        rep, _ = self.run_all(fail_base=True)
        for t in rep["tiles"].values():
            qa01 = next(c for c in t["checks"] if c["id"] == "QA-01")
            self.assertEqual(qa01["status"], "na")
            self.assertIn("insufficient privileges", qa01["summary"].lower() + qa01.get("detail", "").lower())

    def test_filters_reach_the_independent_query(self):
        rep, _ = self.run_all(opts={"filters": {"ORDERS.REGION": ["West"]}})
        t = next(iter(rep["tiles"].values()))
        qa07 = next(c for c in t["checks"] if c["id"] == "QA-07")
        self.assertEqual(qa07["status"], "pass")
        self.assertTrue(any("IN ('West')" in s for s in self.s.base_sqls))
        self.assertTrue(all(c["status"] != "mismatch" for t in rep["tiles"].values() for c in t["checks"]))

    def test_display_arithmetic_and_reconciliation(self):
        rep, res = self.run_all()
        kinds = {c["id"]: c["status"] for t in rep["tiles"].values() for c in t["checks"]}
        self.assertEqual(kinds.get("QA-02"), "pass")
        self.assertEqual(kinds.get("QA-03"), "pass")
        e = Engine(self.s, self.model, self.b, self.prof, None, Store(self.s, APP), {})
        v = V.Validator(self.s, e, None)
        tampered = {"items": [{"label": "Sales", "current": 110.0, "prior": 100.0, "yoy": 50.0, "base": 100.0,
                               "change": 0.25, "yoy_change": 1.0, "delta": 0.1}]}
        out = v.qa02({"type": "kpi_grid"}, tampered)
        self.assertEqual(out["status"], "mismatch")
        self.assertEqual(len(out["rows"]), 2)
        ratio = v.qa03({"type": "ranked_bar", "metric_id": "ORDERS.PROFIT_RATIO", "dimension": "ORDERS.REGION"}, {})
        self.assertEqual(ratio["status"], "na")

    def test_period_logic_catches_a_wrong_boundary(self):
        e = Engine(self.s, self.model, self.b, self.prof, None, Store(self.s, APP), {})
        e.cal.current_start = dt.date(2024, 12, 1)              # December is incomplete (data through 29 Dec)
        out = V.Validator(self.s, e, V.Physical.describe(self.s, SV)).qa05()
        self.assertEqual(out["status"], "mismatch")

    def test_progress_reports_tiles_as_they_finish_and_cancel_stops(self):
        cache = {}
        e = Engine(self.s, self.model, self.b, self.prof, None, Store(self.s, APP), cache)
        res, _ = e.build(self.spec)
        events = []
        v = V.Validator(self.s, Engine(self.s, self.model, self.b, self.prof, None, Store(self.s, APP), dict(cache)),
                        V.Physical.describe(self.s, SV))
        rep = v.run(self.spec, [p["page_id"] for p in self.spec["pages"]], res, e.tile_keys, cache,
                    progress=lambda kind, data: events.append((kind, data)))
        tiles = [d[0] for k, d in events if k == "tile"]
        self.assertEqual(sorted(tiles), sorted(rep["tiles"]))
        self.assertEqual(len(tiles), len(set(tiles)))                     # each tile reported once
        queries = [d for k, d in events if k == "query"]
        self.assertEqual(queries[-1][0], queries[-1][1])                  # done == total at the end
        first_tile = next(i for i, (k, _) in enumerate(events) if k == "tile")
        self.assertLess(first_tile, len(events) - 1)                      # tiles arrive before the run ends
        v2 = V.Validator(self.s, Engine(self.s, self.model, self.b, self.prof, None, Store(self.s, APP), dict(cache)),
                         V.Physical.describe(self.s, SV))
        v2.cancelled = True
        rep2 = v2.run(self.spec, [p["page_id"] for p in self.spec["pages"]], res, e.tile_keys, cache)
        self.assertEqual(rep2["tiles"], {})
        self.assertEqual(rep2["dashboard"], [])

    def _build_and_check(self, after_build=None, **validator_attrs):
        cache = {}
        e = Engine(self.s, self.model, self.b, self.prof, None, Store(self.s, APP), cache)
        res, _ = e.build(self.spec)
        if after_build:
            after_build()
        v = V.Validator(self.s, Engine(self.s, self.model, self.b, self.prof, None, Store(self.s, APP), dict(cache)),
                        V.Physical.describe(self.s, SV))
        for k, val in validator_attrs.items():
            setattr(v, k, val)
        return v.run(self.spec, [p["page_id"] for p in self.spec["pages"]], res, e.tile_keys, cache)

    def test_diagnosis_finds_data_that_changed_during_the_check(self):
        self.s.sv_skew = {"PROFIT": 1.01}                 # dashboard loaded while the data said +1%
        rep = self._build_and_check(after_build=lambda: setattr(self.s, "sv_skew", {}))   # then the data moved
        diags = [c["diagnosis"] for t in rep["tiles"].values() for c in t["checks"] if c.get("diagnosis")]
        self.assertTrue(diags)
        self.assertLessEqual(len(diags), V.MAX_DIAGNOSES)
        self.assertEqual(diags[0]["cause"], "live")
        self.assertTrue(diags[0]["proven"])
        self.assertEqual(diags[0]["action"], "refresh")

    def test_diagnosis_never_guesses(self):
        self.s.base_skew = {"PROFIT": 1.01}               # a real difference no variant explains
        rep = self._build_and_check()
        diags = [c["diagnosis"] for t in rep["tiles"].values() for c in t["checks"] if c.get("diagnosis")]
        self.assertTrue(diags)
        self.assertEqual({d["cause"] for d in diags}, {"unknown"})
        self.assertFalse(any(d["proven"] for d in diags))
        self.assertTrue(diags[0]["ruled_out"])

    def test_report_has_lineage_and_values_compared(self):
        rep = self._build_and_check()
        self.assertEqual(rep["lineage"]["tables"], ["WBR_DB.PUBLIC.ORDERS_SAMPLE_SUPERSTORE"])
        qa01 = [c for t in rep["tiles"].values() for c in t["checks"] if c["id"] == "QA-01"]
        self.assertTrue(all(c.get("compared", 0) > 0 for c in qa01))

    def test_accepted_finding_counts_separately(self):
        rep = {"tiles": {"p/a": {"status": "mismatch", "status_eff": "accepted", "page_id": "p", "checks": []},
                         "p/b": {"status": "pass", "page_id": "p", "checks": []}}, "dashboard": []}
        summ = V.page_summary(rep, "p")
        self.assertEqual(summ["counts"]["accepted"], 1)
        self.assertEqual(summ["counts"]["mismatch"], 0)
        self.assertEqual(summ["status"], "accepted")                   # never shown as fully verified

    def test_resolution_roundtrip(self):
        st = Store(self.s, APP)
        st.save_resolution({"dashboard_id": "", "sv": SV, "tile_key": "p/a", "title": "T", "check_id": "QA-01",
                            "action": "accepted", "reason": "Known restatement", "expires": "2026-11-14", "sig": "abc"})
        rows = st.list_resolutions(SV, "")
        self.assertEqual((rows[0]["tile_key"], rows[0]["action"], rows[0]["tile_sig"]), ("p/a", "accepted", "abc"))
        self.assertEqual(st.validation_history(SV, ""), [])

    def test_signature_changes_with_the_numbers(self):
        a = V.signature({"status": "ready", "data": {"v": 1}}, {})
        self.assertEqual(a, V.signature({"status": "ready", "data": {"v": 1}}, {}))
        self.assertNotEqual(a, V.signature({"status": "ready", "data": {"v": 2}}, {}))
        self.assertNotEqual(a, V.signature({"status": "ready", "data": {"v": 1}}, {"R": ["West"]}))

    def test_page_summary_and_store(self):
        rep, _ = self.run_all()
        page = self.spec["pages"][0]["page_id"]
        summ = V.page_summary(rep, page)
        self.assertIn(summ["status"], ("pass", "review"))
        self.assertGreater(summ["counts"]["pass"], 0)
        Store(self.s, APP).save_validation("r1", "d1", SV, page, summ, rep["queries"], rep)
        row = self.s.tables["VALIDATION"][-1]
        self.assertEqual((row["RUN_ID"], row["PAGE_ID"], row["VERIFIED"]), ("r1", page, summ["counts"]["pass"]))


if __name__ == "__main__":
    unittest.main()
