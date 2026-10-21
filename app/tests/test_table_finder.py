"""Finding tables in a big account: joins, hiding noise, already-covered tags, Cortex suggestions."""
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "streamlit"))
sys.path.insert(0, str(HERE))

from fake_snowflake import FakeSession  # noqa: E402
import semantic_builder as sb  # noqa: E402
import table_finder as tf  # noqa: E402


class Rows:
    def __init__(self, rows):
        self.rows = rows

    def collect(self):
        return self.rows


class StubSession:
    """DESCRIBE of two semantic views: one on a base table, one built by the app on an AA_SRC_ view."""
    def sql(self, q, params=None):
        if "INFORMATION_SCHEMA.VIEWS" in q:
            return Rows([{"TABLE_NAME": "AA_SRC_SALES_X",
                          "COMMENT": "Analytics Accelerator source view for DB.RAW.SALES"}])
        if "DESCRIBE SEMANTIC VIEW DB.SEM.RETAIL_SV" in q:
            return Rows([{"object_kind": "TABLE", "object_name": "STORES", "property": p, "property_value": v}
                         for p, v in (("BASE_TABLE_DATABASE_NAME", "DB"), ("BASE_TABLE_SCHEMA_NAME", "RAW"),
                                      ("BASE_TABLE_NAME", "STORES"))])
        if "DESCRIBE SEMANTIC VIEW APP.S.AA_SALES_SV" in q:
            return Rows([{"object_kind": "TABLE", "object_name": "t", "property": p, "property_value": v}
                         for p, v in (("BASE_TABLE_DATABASE_NAME", "APP"), ("BASE_TABLE_SCHEMA_NAME", "S"),
                                      ("BASE_TABLE_NAME", "AA_SRC_SALES_X"))])
        raise RuntimeError("unexpected " + q)


class TableFinderTests(unittest.TestCase):
    def test_related_rules(self):
        rel = tf.related([
            {"fqn": "D.S.ORDERS", "name": "ORDERS", "columns": ["ORDER_ID", "CUSTOMER_ID", "PRODUCT_ID"]},
            {"fqn": "D.S.CUSTOMERS", "name": "CUSTOMERS", "columns": ["CUSTOMER_ID", "NAME"]},
            {"fqn": "D.S.PRODUCTS", "name": "PRODUCTS", "columns": ["ID", "NAME"]},
            {"fqn": "D.S.LOGS", "name": "LOGS", "columns": ["ID", "MSG"]}])
        self.assertEqual({h["fqn"] for h in rel["D.S.ORDERS"]}, {"D.S.CUSTOMERS", "D.S.PRODUCTS"})
        self.assertNotIn("D.S.LOGS", rel)                       # a bare shared ID is not a join

    def test_catalog_hides_noise_but_keeps_small_lookups(self):
        s = FakeSession()
        tables = sb.list_tables(s, ["WBR_DB.PUBLIC"])
        cat = tf.catalog(s, tables, ["WBR_DB.PUBLIC"], [], "WBR_DB.ANALYTICS_ENTERPRISE")
        by = {t["name"]: t for t in cat["tables"]}
        self.assertFalse(by["CARRIERS"]["tiny"])                # 4 rows, but SHIPMENTS joins to it
        self.assertTrue(by["APP_SETTINGS"]["tiny"])             # 3 rows, joins nothing
        self.assertTrue(by["CALLS"]["empty"])
        self.assertIn("SLA_DAYS", by["CARRIERS"]["columns"])
        self.assertEqual(cat["related"]["WBR_DB.PUBLIC.SHIPMENTS"][0]["fqn"], "WBR_DB.PUBLIC.CARRIERS")

    def test_already_covered_tables_are_tagged(self):
        cov = tf.covered_by_views(StubSession(), [{"fqn": "DB.SEM.RETAIL_SV"}, {"fqn": "APP.S.AA_SALES_SV"}], "APP.S")
        self.assertEqual(cov["DB.RAW.STORES"], ["RETAIL_SV"])
        self.assertEqual(cov["DB.RAW.SALES"], ["AA_SALES_SV"])      # app's own view traced back to its table

    def test_suggestions_only_return_listed_tables(self):
        class Cx:
            def complete(self, prompt):
                self.prompt = prompt
                return json.dumps({"tables": [{"fqn": "wbr_db.public.shipments", "why": "facts"},
                                              {"fqn": "X.Y.INVENTED"}, {"fqn": "WBR_DB.PUBLIC.SHIPMENTS"}]}), "m"
        s = FakeSession()
        tables = tf.catalog(s, sb.list_tables(s, ["WBR_DB.PUBLIC"]), ["WBR_DB.PUBLIC"], [], "A.B")["tables"]
        cx = Cx()
        out = tf.suggest(cx, tables, "freight by carrier")
        self.assertEqual([t["fqn"] for t in out["tables"]], ["WBR_DB.PUBLIC.SHIPMENTS"])
        self.assertEqual(out["ignored"], 2)
        self.assertNotIn("CALLS", cx.prompt)                    # empty tables are not offered to Cortex
        with self.assertRaises(ValueError):
            tf.suggest(cx, tables, "  ")


class PickerHelpersTests(unittest.TestCase):
    def test_system_like_and_views_are_flagged_and_nearest_falls_back(self):
        tabs = [{"fqn": "D.S.AI_BI_STUDIO_EVENTS", "name": "AI_BI_STUDIO_EVENTS", "rows": 18, "columns": ["ID"], "type": "BASE TABLE"},
                {"fqn": "D.S.ORDER_CACHE", "name": "ORDER_CACHE", "rows": 90, "columns": ["ID"], "type": "BASE TABLE"},
                {"fqn": "D.S.SHIPMENTS", "name": "SHIPMENTS", "rows": 500, "columns": ["FREIGHT_COST", "CARRIER"], "type": "VIEW"},
                {"fqn": "D.S.CARRIERS", "name": "CARRIERS", "rows": 80, "columns": ["CARRIER"], "type": "BASE TABLE"}]
        cat = tf.catalog(StubSession(), tabs, [], [], "APP.S")
        by = {t["name"]: t for t in cat["tables"]}
        self.assertTrue(by["AI_BI_STUDIO_EVENTS"]["system"] and by["ORDER_CACHE"]["system"])
        self.assertFalse(by["SHIPMENTS"]["system"])
        self.assertTrue(by["SHIPMENTS"]["view"] and not by["CARRIERS"]["view"])
        by["SHIPMENTS"]["columns"], by["CARRIERS"]["columns"] = ["FREIGHT_COST", "CARRIER"], ["CARRIER"]   # catalog() reads real columns
        near = tf.nearest(cat["tables"], "freight cost by carrier")
        self.assertEqual({n["fqn"] for n in near}, {"D.S.SHIPMENTS", "D.S.CARRIERS"})
        self.assertNotIn("D.S.ORDER_CACHE", [n["fqn"] for n in tf.nearest(cat["tables"], "order cache")])
        self.assertEqual(tf.nearest(cat["tables"], "harboline retail"), [])

    def test_no_match_returns_nearest(self):
        class Cx:
            def complete(self, prompt):
                return json.dumps({"tables": [], "note": "Nothing about harboline."}), "m"
        s = FakeSession()
        tables = tf.catalog(s, sb.list_tables(s, ["WBR_DB.PUBLIC"]), ["WBR_DB.PUBLIC"], [], "A.B")["tables"]
        out = tf.suggest(Cx(), tables, "harboline carrier")
        self.assertEqual(out["tables"], [])
        self.assertTrue(out["nearest"])


if __name__ == "__main__":
    unittest.main()
