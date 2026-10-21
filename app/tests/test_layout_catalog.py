import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'streamlit'))

from layout_catalog import (
    AUDIENCES,
    CATALOG,
    MetricInventory,
    bind_template,
    cortex_allowlist,
    list_templates,
    picker_options,
    select_template,
    validate_catalog,
    validate_cortex_output,
)


class LayoutCatalogTests(unittest.TestCase):
    def setUp(self):
        self.ops_inventory = MetricInventory(
            role_to_metric_id={
                "backlog": "METRIC_OPEN_WORK",
                "sla_attainment": "METRIC_SLA_RATE",
                "queue": "DIM_QUEUE",
            },
            validated_capabilities=frozenset({
                "fresh_data", "event_time", "operating_scope_authorized", "target",
                "comparable_intraday_series",
            }),
        )

    def test_catalog_is_valid_and_covers_each_audience(self):
        self.assertEqual(validate_catalog(), ())
        self.assertEqual(len(CATALOG), 11)
        self.assertEqual(
            {template.audience_id for template in CATALOG},
            set(AUDIENCES),
        )
        self.assertTrue(all(len(template.pages) >= 2 for template in CATALOG))

    def test_templates_are_filtered_by_audience(self):
        for audience in AUDIENCES:
            templates = list_templates(audience)
            self.assertGreaterEqual(len(templates), 2)
            self.assertTrue(all(item.audience_id == audience for item in templates))

    def test_picker_explains_compatibility(self):
        options = picker_options("daily_operations", self.ops_inventory)
        selectable = [item for item in options if item["selectable"]]
        self.assertIn("ops_queue_sla_triage", [item["template_id"] for item in selectable])
        self.assertTrue(all(item["page_map"] for item in options))

    def test_cortex_allowlist_is_audience_scoped_and_ready_only(self):
        allowlist = cortex_allowlist("daily_operations", self.ops_inventory)
        self.assertIn("ops_queue_sla_triage", allowlist)
        self.assertNotIn("exec_enterprise_performance", allowlist)
        self.assertNotIn("ops_capacity_flow", allowlist)

    def test_valid_cortex_suggestion_is_accepted_then_validated(self):
        result = validate_cortex_output(
            "daily_operations",
            self.ops_inventory,
            {"template_id": "ops_queue_sla_triage", "reason": "queue and SLA fields exist"},
        )
        self.assertEqual(result.status, "ready")
        self.assertEqual(result.selected_by, "cortex")
        self.assertEqual(result.template.template_id, "ops_queue_sla_triage")

    def test_wrong_audience_cortex_suggestion_is_rejected(self):
        result = validate_cortex_output(
            "daily_operations",
            self.ops_inventory,
            {"template_id": "exec_enterprise_performance", "reason": "hallucinated or wrong audience"},
        )
        self.assertEqual(result.status, "ready")
        self.assertEqual(result.selected_by, "catalog_rules")
        self.assertEqual(result.template.template_id, "ops_queue_sla_triage")
        self.assertIsNotNone(result.rejected_cortex_suggestion)

    def test_unknown_cortex_suggestion_cannot_create_new_template(self):
        result = validate_cortex_output(
            "daily_operations",
            self.ops_inventory,
            {"template_id": "generated_new_layout", "reason": "model invented it"},
        )
        self.assertNotEqual(result.template.template_id, "generated_new_layout")
        self.assertEqual(result.selected_by, "catalog_rules")

    def test_user_selection_has_precedence_and_is_validated(self):
        result = select_template(
            "daily_operations",
            self.ops_inventory,
            user_selected_template_id="ops_queue_sla_triage",
            cortex_suggested_template_id="ops_capacity_flow",
        )
        self.assertEqual(result.status, "ready")
        self.assertEqual(result.selected_by, "user")
        self.assertEqual(result.template.template_id, "ops_queue_sla_triage")

    def test_cross_audience_user_selection_is_blocked(self):
        result = select_template(
            "daily_operations",
            self.ops_inventory,
            user_selected_template_id="exec_enterprise_performance",
        )
        self.assertEqual(result.status, "blocked")
        self.assertIsNone(result.template)

    def test_no_compatible_template_returns_unavailable(self):
        empty_inventory = MetricInventory({}, frozenset())
        result = select_template("executives", empty_inventory)
        self.assertEqual(result.status, "unavailable")
        self.assertIsNone(result.template)
        self.assertFalse(cortex_allowlist("executives", empty_inventory))

    def test_bind_returns_multitab_spec_and_metric_ids(self):
        result = select_template(
            "daily_operations", self.ops_inventory,
            user_selected_template_id="ops_queue_sla_triage",
        )
        spec = bind_template(result.template, self.ops_inventory)
        self.assertEqual(spec["audience_id"], "daily_operations")
        self.assertEqual(len(spec["pages"]), 3)
        backlog_component = spec["pages"][0]["components"][0]
        self.assertEqual(backlog_component["metric_id"], "METRIC_OPEN_WORK")
        self.assertEqual(backlog_component["state"], "ready")

    def test_optional_component_is_omitted_if_its_metric_is_absent(self):
        result = select_template(
            "daily_operations", self.ops_inventory,
            user_selected_template_id="ops_queue_sla_triage",
        )
        spec = bind_template(result.template, self.ops_inventory)
        exception_component = next(
            component
            for page in spec["pages"]
            for component in page["components"]
            if component["component_id"] == "breaches"
        )
        self.assertEqual(exception_component["state"], "omitted")


if __name__ == "__main__":
    unittest.main()
