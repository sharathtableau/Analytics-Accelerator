import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "streamlit"))
sys.path.insert(0, str(HERE))

import semantic_builder as sb  # noqa: E402

PROFILE = {"fqn": "WBR_DB.PUBLIC.SHIPMENTS", "table": "SHIPMENTS", "rows_profiled": 1000, "columns": [
    {"column": "SHIP_DATE", "type": "DATE", "kind": "time", "distinct": 400, "nulls": 0, "min": "2025-01-01", "max": "2026-09-30", "samples": [], "comment": ""},
    {"column": "CARRIER", "type": "TEXT", "kind": "text", "distinct": 4, "nulls": 0, "min": None, "max": None, "samples": ["UPS", "USPS"], "comment": ""},
    {"column": "Region Name", "type": "TEXT", "kind": "text", "distinct": 5, "nulls": 0, "min": None, "max": None, "samples": ["West"], "comment": ""},
    {"column": "SHIPMENT_ID", "type": "NUMBER", "kind": "number", "distinct": 1000, "nulls": 0, "min": "1", "max": "1000", "samples": [], "comment": ""},
    {"column": "FREIGHT_COST", "type": "NUMBER", "kind": "number", "distinct": 900, "nulls": 3, "min": "1.2", "max": "88", "samples": [], "comment": ""},
    {"column": "TRANSIT_DAYS", "type": "FLOAT", "kind": "number", "distinct": 40, "nulls": 0, "min": "1", "max": "9", "samples": [], "comment": ""},
]}

DRAFT = {"view_name": "Shipments", "description": "Parcel shipments", "time_dimension": "SHIP_DATE",
         "dimensions": [{"column": "CARRIER", "name": "carrier", "synonyms": ["shipper"], "comment": "Carrier name."},
                        {"column": "Region Name", "name": "region", "synonyms": [], "comment": "Sales region."},
                        {"column": "NOT_A_COLUMN", "name": "ghost", "synonyms": [], "comment": ""}],
         "metrics": [{"name": "freight_cost", "agg": "SUM", "column": "FREIGHT_COST", "synonyms": ["shipping cost"], "comment": "Total freight (USD)."},
                     {"name": "shipments", "agg": "COUNT_DISTINCT", "column": "SHIPMENT_ID", "synonyms": [], "comment": "Shipments."},
                     {"name": "avg transit", "agg": "AVG", "column": "TRANSIT_DAYS", "synonyms": [], "comment": "Days."},
                     {"name": "carrier_total", "agg": "SUM", "column": "CARRIER", "synonyms": [], "comment": ""},
                     {"name": "made_up", "agg": "MEDIAN", "column": "FREIGHT_COST", "synonyms": [], "comment": ""}],
         "ratios": [{"name": "cost_per_shipment", "numerator": "freight_cost", "denominator": "shipments", "comment": "USD per shipment."},
                    {"name": "bad", "numerator": "nope", "denominator": "shipments", "comment": ""}],
         "questions": ["Which carrier is most expensive per shipment?"]}


class ValidateTests(unittest.TestCase):
    def setUp(self):
        self.spec, self.notes = sb.validate_draft(DRAFT, PROFILE)
        self.why = {n["item"]: n for n in self.notes}

    def test_unknown_column_and_aggregation_are_dropped(self):
        self.assertEqual(self.why["ghost"]["action"], "dropped")
        self.assertEqual(self.why["made_up"]["action"], "dropped")
        self.assertEqual(self.why["bad"]["action"], "dropped")

    def test_sum_on_text_is_repaired(self):
        m = next(m for m in self.spec["metrics"] if m["column"] == "CARRIER")
        self.assertEqual(m["agg"], "COUNT_DISTINCT")

    def test_names_are_normalised_and_time_dimension_added(self):
        self.assertIn("avg_transit", [m["name"] for m in self.spec["metrics"]])
        self.assertEqual(self.spec["time_dimension"], "SHIP_DATE")
        self.assertEqual(self.spec["dimensions"][0]["column"], "SHIP_DATE")
        self.assertEqual(self.spec["view_name"], "shipments")

    def test_duplicate_names_are_renamed_and_ratios_follow(self):
        d = dict(DRAFT, metrics=DRAFT["metrics"] + [{"name": "freight_cost", "agg": "MAX", "column": "FREIGHT_COST",
                                                    "synonyms": [], "comment": ""}],
                 ratios=[{"name": "f_ratio", "numerator": "freight_cost", "denominator": "shipments", "comment": ""}])
        spec, notes = sb.validate_draft(d, PROFILE)
        names = [m["name"] for m in spec["metrics"]] + [r["name"] for r in spec["ratios"]]
        self.assertEqual(len(names), len(set(names)))
        self.assertIn("freight_cost_value", names)
        self.assertIn("ratio_value", names)                       # f_ prefix is reserved for facts
        self.assertEqual(spec["ratios"][0]["numerator"], "freight_cost")


class DdlTests(unittest.TestCase):
    def setUp(self):
        spec, _ = sb.validate_draft(DRAFT, PROFILE)
        self.ddl = sb.build_ddl(spec, PROFILE, "WBR_DB.ANALYTICS_ENTERPRISE")

    def test_source_view_prefixes_and_quotes_columns(self):
        v = self.ddl["view_sql"]
        self.assertIn('"Region Name" AS C_REGION_NAME', v)
        self.assertIn("FREIGHT_COST AS C_FREIGHT_COST", v)
        self.assertTrue(self.ddl["source_view"].startswith("WBR_DB.ANALYTICS_ENTERPRISE.AA_SRC_"))

    def test_metrics_aggregate_facts_and_ratios_use_div0(self):
        q = self.ddl["sv_sql"]
        self.assertIn("t.f_freight_cost AS C_FREIGHT_COST", q)
        self.assertIn("SUM(t.f_freight_cost)", q)
        self.assertIn("COUNT(DISTINCT t.f_shipment_id)", q)
        self.assertIn("DIV0(t.freight_cost, t.shipments)", q)
        self.assertIn("WITH SYNONYMS = ('shipping cost')", q)
        self.assertNotIn("FREIGHT_COST)", q.replace("C_FREIGHT_COST", ""))   # no raw column inside a metric

    def test_names_and_test_query(self):
        self.assertEqual(self.ddl["semantic_view"], "WBR_DB.ANALYTICS_ENTERPRISE.AA_SHIPMENTS_SV")
        self.assertTrue(self.ddl["test_sql"].startswith("SELECT * FROM SEMANTIC_VIEW(WBR_DB.ANALYTICS_ENTERPRISE.AA_SHIPMENTS_SV METRICS t."))

    def test_excluded_items_are_left_out(self):
        spec, _ = sb.validate_draft(DRAFT, PROFILE)
        spec["metrics"][0]["include"] = False
        ddl = sb.build_ddl(spec, PROFILE, "WBR_DB.ANALYTICS_ENTERPRISE")
        self.assertNotIn("t.freight_cost AS", ddl["sv_sql"])
        self.assertNotIn("cost_per_shipment", ddl["sv_sql"])        # ratio depends on an excluded metric

    def test_rejects_bad_target_schema(self):
        spec, _ = sb.validate_draft(DRAFT, PROFILE)
        with self.assertRaises(ValueError):
            sb.build_ddl(spec, PROFILE, "x; drop table y")


class FallbackTests(unittest.TestCase):
    def test_fallback_draft_is_valid(self):
        spec, _ = sb.validate_draft(sb.fallback_draft(PROFILE), PROFILE)
        self.assertTrue(spec["metrics"])
        self.assertEqual(spec["time_dimension"], "SHIP_DATE")
        sb.build_ddl(spec, PROFILE, "WBR_DB.ANALYTICS_ENTERPRISE")


if __name__ == "__main__":
    unittest.main()
