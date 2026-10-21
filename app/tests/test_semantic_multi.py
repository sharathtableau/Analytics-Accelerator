"""B6: one semantic view over several tables - joins found and checked, Cortex can't invent joins, totals reconcile."""
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "streamlit"))
sys.path.insert(0, str(HERE))

from fake_snowflake import FakeSession  # noqa: E402
import semantic_multi as smu  # noqa: E402

TABLES = ["WBR_DB.PUBLIC.SHIPMENTS", "WBR_DB.PUBLIC.CARRIERS"]
APP = "WBR_DB.ANALYTICS_ENTERPRISE"


class NoCortex:
    def complete(self, prompt):
        raise RuntimeError("Cortex unavailable")


class StubCortex:
    def __init__(self, payload):
        self.payload, self.prompt = payload, ""

    def complete(self, prompt):
        self.prompt = prompt
        return json.dumps(self.payload), "stub"


class MultiTableTests(unittest.TestCase):
    def setUp(self):
        self.s = FakeSession()

    def test_keys_and_join_are_found_and_checked(self):
        out = smu.draft(NoCortex(), self.s, TABLES)
        rel = out["spec"]["relationships"]
        self.assertEqual([(r["from"], r["from_col"], r["to"], r["to_col"]) for r in rel],
                         [("shipments", "CARRIER", "carriers", "CARRIER")])
        self.assertEqual({t["alias"]: t["key"] for t in out["spec"]["tables"]},
                         {"shipments": "SHIPMENT_ID", "carriers": "CARRIER"})
        self.assertTrue(all(c["status"] == "ok" for c in out["checks"]))
        # the lookup table has dimensions only; the fact table has the metrics
        self.assertFalse([m for m in out["spec"]["metrics"] if m["table"] == "carriers"])
        self.assertTrue([d for d in out["spec"]["dimensions"] if d["table"] == "carriers"])

    def test_low_coverage_is_a_warning(self):
        self.s.fake_miss = 200
        out = smu.draft(NoCortex(), self.s, TABLES)
        join = next(c for c in out["checks"] if c["check"].startswith("join"))
        self.assertEqual(join["status"], "warn")
        self.assertEqual(out["spec"]["relationships"][0]["coverage"], 0.8)

    def test_cortex_can_drop_but_not_invent_joins(self):
        cx = StubCortex({"view_name": "freight", "drop_joins": [], "tables": {
            "shipments": {"metrics": [{"name": "freight", "agg": "SUM", "column": "FREIGHT_COST"}],
                          "dimensions": [{"column": "SHIP_DATE", "name": "ship_date"}]},
            "carriers": {"dimensions": [{"column": "CARRIER_TYPE", "name": "carrier_type"}],
                         "metrics": [{"name": "freight", "agg": "SUM", "column": "SLA_DAYS"}]}},
            "joins": [{"from": "carriers", "to": "shipments"}]})
        out = smu.draft(cx, self.s, TABLES)
        self.assertEqual(out["origin"], "cortex")
        self.assertIn("shipments_to_carriers", cx.prompt)
        self.assertEqual(len(out["spec"]["relationships"]), 1)                 # the invented one is ignored
        names = [m["name"] for m in out["spec"]["metrics"]]
        self.assertEqual(len(names), len(set(names)))                          # unique across tables
        cx2 = StubCortex({"drop_joins": ["shipments_to_carriers"], "tables": {
            "shipments": {"metrics": [{"name": "freight", "agg": "SUM", "column": "FREIGHT_COST"}]}}})
        out2 = smu.draft(cx2, self.s, TABLES)
        self.assertFalse(out2["spec"]["relationships"][0]["include"])
        with self.assertRaisesRegex(ValueError, "would not be joined"):
            smu.build_ddl(out2["spec"], out2["profiles"], APP)

    def test_ddl_declares_keys_relationships_and_a_join_test(self):
        out = smu.draft(NoCortex(), self.s, TABLES)
        ddl = smu.build_ddl(out["spec"], out["profiles"], APP)
        sql = ddl["sv_sql"]
        self.assertIn("carriers AS WBR_DB.ANALYTICS_ENTERPRISE.AA_SRC_", sql)
        self.assertIn("PRIMARY KEY (C_CARRIER)", sql)
        self.assertIn("shipments_to_carriers AS shipments (C_CARRIER) REFERENCES carriers", sql)
        self.assertNotIn("SHIPMENTS PRIMARY KEY", sql.upper().replace("AA_SRC_SHIPMENTS_CARRIERS_SHIPMENTS PRIMARY", ""))
        self.assertIn("DIMENSIONS carriers.", ddl["test_sql"])                  # test query crosses the join
        self.assertEqual(len(ddl["view_sqls"]), 2)
        self.assertTrue(all("C_CARRIER" in v for v in ddl["view_sqls"]))       # join column in both source views

    def test_create_reconciles_totals(self):
        out = smu.draft(NoCortex(), self.s, TABLES)
        ddl = smu.build_ddl(out["spec"], out["profiles"], APP)
        ok = smu.create(self.s, ddl)
        self.assertTrue(ok["checks"] and all(c["status"] == "ok" for c in ok["checks"]))
        self.s.fake_sv_total = 246913.56                                         # a join that doubled the rows
        bad = smu.create(self.s, ddl)
        self.assertTrue(all(c["status"] == "fail" for c in bad["checks"]))

    def test_reviewer_edits_are_revalidated(self):
        out = smu.draft(NoCortex(), self.s, TABLES)
        edited = json.loads(json.dumps(out["spec"]))
        edited["metrics"][0]["include"] = False
        edited["dimensions"].append({"table": "carriers", "column": "NOT_A_COLUMN", "name": "x"})
        spec, notes = smu.revalidate(edited, out["profiles"])
        self.assertNotIn(out["spec"]["metrics"][0]["name"], [m["name"] for m in spec["metrics"]])
        self.assertTrue(any("NOT_A_COLUMN" in n["why"] for n in notes))

    def test_tables_without_a_join_are_refused(self):
        with self.assertRaisesRegex(ValueError, "Pick 2"):
            smu.draft(NoCortex(), self.s, TABLES[:1])


if __name__ == "__main__":
    unittest.main()
