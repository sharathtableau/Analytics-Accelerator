import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "streamlit"))
sys.path.insert(0, str(HERE))

import agent_service as ag  # noqa: E402
import config  # noqa: E402

SV = "WBR_DB.RETAIL_DEMO.RETAIL_ANALYTICS_SV"
SRCH = "WBR_DB.RETAIL_DEMO.RETAIL_DOCS_SEARCH"


class _Row(dict):
    def as_dict(self):
        return dict(self)


class _Sess:
    def __init__(self, reply):
        self.sqls, self.reply = [], reply

    def sql(self, q, params=None):
        self.sqls.append((q, params))
        outer = self

        class R:
            def collect(self_inner):
                return [_Row(R=json.dumps(outer.reply))] if "DATA_AGENT_RUN" in q else []
        return R()


class AgentSpecTests(unittest.TestCase):
    def test_domain_agent_has_analyst_and_search(self):
        spec = ag.agent_spec(SV, "Retail", ["q1"], "POWERHOUSE", SRCH)
        types = [t["tool_spec"]["type"] for t in spec["tools"]]
        self.assertEqual(types, ["cortex_analyst_text_to_sql", "cortex_search"])
        self.assertEqual(spec["tool_resources"]["documents"], {"search_service": SRCH, "max_results": 4, "id_column": "DOC_ID", "title_column": "TITLE"})
        self.assertEqual(spec["tool_resources"]["analyst"]["execution_environment"]["warehouse"], "POWERHOUSE")
        self.assertIn("documents tool", spec["instructions"]["orchestration"])

    def test_without_search_only_analyst(self):
        spec = ag.agent_spec(SV, "Retail", [], "POWERHOUSE")
        self.assertEqual(len(spec["tools"]), 1)
        self.assertNotIn("documents", spec["tool_resources"])

    def test_create_agent_sql_carries_version_and_search(self):
        s = _Sess({})
        made = ag.create_agent(s, "WBR_DB.ANALYTICS_ENTERPRISE", SV, "Retail", ["q"], "POWERHOUSE", True, SRCH)
        sql = s.sqls[0][0]
        self.assertTrue(sql.startswith("CREATE OR REPLACE AGENT"))
        self.assertIn(ag.SPEC_VERSION, sql)
        self.assertIn(SRCH, sql)
        self.assertTrue(made["has_search"])
        with self.assertRaises(ValueError):
            ag.create_agent(s, "WBR_DB.ANALYTICS_ENTERPRISE", SV, "Retail", [], "", True, "bad name; drop")

    def test_citations_are_extracted(self):
        reply = {"content": [
            {"type": "text", "text": "Free shipping share fell because the threshold rose to 119 USD."},
            {"type": "tool_result", "tool_result": {"content": [{"json": {"search_results": [
                {"doc_id": "HLO-POL-014", "doc_title": "Free Shipping Policy", "text": "From 1 March 2026 ..."},
                {"doc_id": "HLO-WBR", "doc_title": "WBR notes", "text": "intended effect"}]}}]}}],
            "metadata": {"run_id": "r1"}}
        out = ag.ask_agent(_Sess(reply), "WBR_DB.ANALYTICS_ENTERPRISE.AA_X_AGENT", "why?")
        self.assertEqual([c["label"] for c in out["citations"]],
                         ["HLO-POL-014 · Free Shipping Policy", "HLO-WBR · WBR notes"])

    def test_retail_view_is_mapped_to_its_search_service(self):
        self.assertEqual(config.SEARCH_SERVICES.get(SV), SRCH)


if __name__ == "__main__":
    unittest.main()


class ActionToolTests(unittest.TestCase):
    PROC = "WBR_DB.ANALYTICS_ENTERPRISE.AA_CREATE_DECISION"

    def test_spec_v3_has_log_decision_procedure_tool(self):
        spec = ag.agent_spec(SV, "Retail", [], "POWERHOUSE", SRCH, self.PROC)
        tool = next(t["tool_spec"] for t in spec["tools"] if t["tool_spec"]["name"] == "log_decision")
        self.assertEqual(tool["type"], "generic")
        self.assertTrue(all(k.startswith("p_") for k in tool["input_schema"]["properties"]))
        self.assertIn("p_owner", tool["input_schema"]["required"])
        res = spec["tool_resources"]["log_decision"]
        self.assertEqual(res, {"type": "procedure", "identifier": self.PROC,
                               "execution_environment": {"type": "warehouse", "warehouse": "POWERHOUSE"}})
        self.assertIn(SV, spec["instructions"]["orchestration"])
        self.assertIn("Never log a decision the user did not ask for", spec["instructions"]["orchestration"])

    def test_create_agent_rejects_bad_proc_name(self):
        with self.assertRaises(ValueError):
            ag.create_agent(_Sess({}), "WBR_DB.ANALYTICS_ENTERPRISE", SV, "Retail", [], "", True, "", "x; drop")

    def test_logged_decision_is_reported_as_action(self):
        reply = {"content": [{"type": "text", "text": "Done."},
                             {"type": "tool_result", "tool_result": {"name": "log_decision", "content": [
                                 {"type": "text", "text": "Logged decision 3fa2c9d01b7e: Expedite, owner M. Alvarez"}]}}]}
        out = ag.ask_agent(_Sess(reply), "WBR_DB.ANALYTICS_ENTERPRISE.AA_X_AGENT", "log it")
        self.assertEqual(out["actions"], [{"kind": "decision", "id": "3fa2c9d01b7e"}])

    def test_config_points_at_app_schema_proc(self):
        self.assertEqual(config.DECISION_TOOL, self.PROC)


class EvaluationTests(unittest.TestCase):
    """D1: Snowflake-native Cortex Agent evaluations (EXECUTE_AI_EVALUATION / GET_AI_EVALUATION_DATA)."""
    AGENT = "WBR_DB.ANALYTICS_ENTERPRISE.AA_RETAIL_ANALYTICS_SV_AGENT"

    def test_config_maps_retail_agent_and_gate(self):
        self.assertTrue(config.EVAL_CONFIGS[self.AGENT].endswith("AA_EVAL_CONFIG/aa_agent_eval.yaml"))
        self.assertEqual(set(config.EVAL_GATE), {"answer_correctness", "logical_consistency",
                                                 "tool_selection_accuracy", "cites_sources"})

    def test_start_list_and_read_results(self):
        from store import Store
        from fake_snowflake import FakeSession
        s = FakeSession()
        st = Store(s, "WBR_DB.ANALYTICS_ENTERPRISE")
        st.eval_start(self.AGENT, config.EVAL_CONFIGS[self.AGENT], "aa_run_1")
        self.assertEqual(s.eval_started, ["aa_run_1"])
        self.assertEqual([r["run_name"] for r in st.eval_runs(self.AGENT)], ["aa_run_1"])
        res = st.eval_results(self.AGENT, "aa_run_1")
        self.assertEqual(res["error"], "")
        self.assertEqual({r["metric_name"] for r in res["summary"]},
                         {"answer_correctness", "cites_sources", "logical_consistency"})
        q, params = next((q, p) for q, p in s.sqls if "GET_AI_EVALUATION_DATA" in q)
        self.assertEqual(params, ["WBR_DB", "ANALYTICS_ENTERPRISE", "AA_RETAIL_ANALYTICS_SV_AGENT", "aa_run_1"])
        self.assertIn("COMPLETED", st.eval_status(config.EVAL_CONFIGS[self.AGENT], "aa_run_1"))

    def test_yaml_points_at_same_agent_and_dataset_schema(self):
        yml = (HERE.parent.parent / "setup" / "eval" / "aa_agent_eval.yaml")
        if not yml.exists():
            self.skipTest("setup folder not present")
        text = yml.read_text()
        self.assertIn(f'agent_name: "{self.AGENT}"', text)
        self.assertIn('"WBR_DB.ANALYTICS_ENTERPRISE.AA_RETAIL_AGENT_EVALSET"', text)
