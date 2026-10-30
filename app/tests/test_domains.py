import unittest

import domains


SRC = [{"fqn": "WBR_DB.RETAIL_DEMO.RETAIL_ANALYTICS_SV", "name": "RETAIL_ANALYTICS_SV"},
       {"fqn": "WBR_DB.PUBLIC.SUPERSTORE_DEMO_SV", "name": "SUPERSTORE_DEMO_SV"},
       {"fqn": "WBR_DB.FINANCE_DEMO.FINANCE_ANALYTICS_SV", "name": "FINANCE_ANALYTICS_SV"},
       {"fqn": "WBR_DB.ANALYTICS_ENTERPRISE.AA_CARDS_SV", "name": "AA_CARDS_SV"}]


class DomainTests(unittest.TestCase):
    def setUp(self):
        self.d = domains.merge()

    def test_three_builtin_workspaces_retail_default(self):
        self.assertEqual([x["id"] for x in self.d], ["retail", "finance", "cpg"])
        self.assertEqual(domains.default_id(self.d), "retail")
        names = " ".join(x["company"] for x in self.d)
        for real in ("Walmart", "Visa", "Capital One"):
            self.assertNotIn(real, names)

    def test_view_belongs_by_schema_else_default(self):
        self.assertEqual(domains.of_view("WBR_DB.FINANCE_DEMO.FINANCE_ANALYTICS_SV", self.d), "finance")
        self.assertEqual(domains.of_view("wbr_db.cpg_demo.cpg_analytics_sv#fact", self.d), "cpg")
        self.assertEqual(domains.of_view("WBR_DB.PUBLIC.SUPERSTORE_DEMO_SV", self.d), "retail")
        self.assertEqual(domains.of_view("", self.d), "retail")

    def test_view_built_in_app_keeps_its_workspace(self):
        tags = {"WBR_DB.ANALYTICS_ENTERPRISE.AA_CARDS_SV": "finance"}
        self.assertEqual(domains.of_view("WBR_DB.ANALYTICS_ENTERPRISE.AA_CARDS_SV", self.d, tags), "finance")
        self.assertEqual(len(domains.sources_in(SRC, "finance", self.d, tags)), 2)
        self.assertEqual(len(domains.sources_in(SRC, "retail", self.d, tags)), 2)

    def test_dashboard_domain_from_layout_or_view(self):
        self.assertEqual(domains.of_dashboard({"semantic_view": "WBR_DB.PUBLIC.X", "layout": {"domain": "cpg"}}, self.d), "cpg")
        self.assertEqual(domains.of_dashboard({"semantic_view": "WBR_DB.FINANCE_DEMO.X", "layout": None}, self.d), "finance")

    def test_discovery_adds_domain_schemas_once(self):
        out = domains.discovery_schemas(["WBR_DB.RETAIL_DEMO", "WBR_DB.FINANCE_DEMO"], self.d)
        self.assertEqual(out.count("WBR_DB.FINANCE_DEMO"), 1)
        self.assertIn("WBR_DB.CPG_DEMO", out)

    def test_overrides_and_new_domain_from_table(self):
        rows = [{"domain_id": "finance", "spec": '{"company": "Acme Card Co"}', "active": True},
                {"domain_id": "health", "spec": '{"name": "Healthcare", "schemas": ["wbr_db.health_demo"]}', "active": True},
                {"domain_id": "cpg", "spec": "{}", "active": False}]
        d = domains.merge(rows)
        self.assertEqual(domains.get(d, "finance")["company"], "Acme Card Co")
        self.assertEqual(domains.of_view("WBR_DB.HEALTH_DEMO.V", d), "health")
        self.assertIsNone(domains.get(d, "cpg"))

    def test_summary_ready_only_with_data(self):
        dash = [{"dashboard_id": "a", "semantic_view": "WBR_DB.PUBLIC.SUPERSTORE_DEMO_SV"},
                {"dashboard_id": "b", "semantic_view": "WBR_DB.FINANCE_DEMO.FINANCE_ANALYTICS_SV"}]
        rows = [{"dashboard_id": "a", "state": "rejected"}]
        alerts = [{"semantic_view": "WBR_DB.FINANCE_DEMO.FINANCE_ANALYTICS_SV"}]
        out = {x["id"]: x for x in domains.summary(self.d, SRC[:3], dash, {}, rows, alerts)}
        self.assertTrue(out["retail"]["ready"] and out["finance"]["ready"])
        self.assertFalse(out["cpg"]["ready"])
        self.assertEqual((out["retail"]["n_dashboards"], out["retail"]["n_reviews"]), (1, 1))
        self.assertEqual((out["finance"]["n_dashboards"], out["finance"]["n_alerts"]), (1, 1))

    def test_featured_default_falls_back_to_config(self):
        r = domains.get(self.d, "retail")
        self.assertEqual(domains.featured(r, ["X.Y.Z"], {"X.Y.Z": "Lbl"}), {"X.Y.Z": "Lbl"})
        self.assertIn("WBR_DB.FINANCE_DEMO.FINANCE_ANALYTICS_SV",
                      domains.featured(domains.get(self.d, "finance"), ["X.Y.Z"], {}))


if __name__ == "__main__":
    unittest.main()
