import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "streamlit"))
sys.path.insert(0, str(HERE))

from fake_snowflake import FakeSession  # noqa: E402
from store import Store  # noqa: E402


class AiLimitTests(unittest.TestCase):
    def test_runs_are_attributed_to_the_person_and_counted(self):
        st = Store(FakeSession(), "WBR_DB.ANALYTICS_ENTERPRISE")
        st.ready = True
        st.actor = "ANNA"
        for f in ("prompt_routing", "agent_question", "page_summary", "agent_question"):
            st.log_ai(f, "", "in", "out", "Cortex", "ok", 0.1)
        st.actor = "BEN"
        st.log_ai("tile_edit", "", "in", "out", "Cortex", "ok", 0.1)
        self.assertEqual(st.ai_usage_today("ANNA"), {"all": 3, "agent": 2})   # page summaries are free
        self.assertEqual(st.ai_usage_today("BEN"), {"all": 1, "agent": 0})
        self.assertEqual(st.ai_usage_today("CARL"), {"all": 0, "agent": 0})

    def test_without_a_person_the_insert_falls_back_to_current_user(self):
        s = FakeSession()
        st = Store(s, "WBR_DB.ANALYTICS_ENTERPRISE")
        st.ready = True
        st.log_ai("tile_edit", "", "in", "out", "Cortex", "ok", 0.1)
        sql, params = [x for x in s.sqls if "INSERT" in x[0]][-1]
        self.assertIn("COALESCE(NULLIF(?, ''), CURRENT_USER())", sql)
        self.assertEqual(params[-1], "")


if __name__ == "__main__":
    unittest.main()
