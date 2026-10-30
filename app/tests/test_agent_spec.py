"""The domain agent answers from governed data first; documents are optional context, used only when they help."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "streamlit"))
from agent_service import agent_spec  # noqa: E402

SV = "WBR_DB.FINANCE_DEMO.FINANCE_ANALYTICS_SV"


class AgentSpecTests(unittest.TestCase):
    def test_without_documents_never_mentions_them(self):
        spec = agent_spec(SV, "Keystone", ["q"], "WH", "", "")
        text = str(spec["instructions"]).lower()
        self.assertNotIn("document", text)
        self.assertEqual([t["tool_spec"]["name"] for t in spec["tools"]], ["analyst"])

    def test_with_documents_data_comes_first_and_documents_are_optional(self):
        spec = agent_spec(SV, "Keystone", ["q"], "WH", "WBR_DB.FINANCE_DEMO.FINANCE_DOCS_SEARCH", "")
        orch = spec["instructions"]["orchestration"]
        self.assertTrue(orch.startswith("Answer from the governed data first"))
        self.assertIn("never required", orch)
        self.assertIn("only when you used it", spec["instructions"]["response"])
        self.assertNotIn("then look for a documented cause", orch)


if __name__ == "__main__":
    unittest.main()
