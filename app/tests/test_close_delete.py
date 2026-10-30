"""Close the work on screen (Continue card) and delete a draft (hidden, versions kept). Added 28 Oct; nothing removed."""
import re
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUNDLE = (HERE.parent / "streamlit" / "app_bundle.js").read_text(encoding="utf-8")
APP = (HERE.parent / "streamlit" / "app.py").read_text(encoding="utf-8")
STORE = (HERE.parent / "streamlit" / "store.py").read_text(encoding="utf-8")


class CloseDeleteTests(unittest.TestCase):
    def test_continue_card_keeps_its_buttons_and_adds_close(self):
        for s in ('"Edit metrics & outline"', '"Open dashboard →"', 't("work_close"'):
            self.assertIn(s, BUNDLE)

    def test_close_asks_about_unsaved_changes(self):
        self.assertIn('"work_close"', re.search(r"LEAVE_ACTIONS = \{[^}]*\}", APP).group(0))
        self.assertIn('must_confirm_leave("work_close", p)', APP)

    def test_delete_hides_and_keeps_history(self):
        self.assertIn('store.set_setting(f"dash_hidden:{did}"', APP)
        self.assertNotRegex(APP + STORE, r"DELETE FROM \{self\.dashboards\}")
        self.assertIn('self.list_settings("dash_hidden:")', STORE)

    def test_delete_only_own_unpublished_drafts(self):
        self.assertIn("is published; it stays while it is in the Portal", APP)
        self.assertIn("Only the person who created", APP)
        self.assertIn("(e.dash_deletable || []).includes(b.dashboard_id)", BUNDLE)

    def test_builder_only(self):
        portal = re.search(r"VIEWER_ACTIONS = \{([^}]*)\}", APP).group(1)
        self.assertNotIn("dashboard_delete", portal)
        self.assertNotIn("work_close", portal)


if __name__ == "__main__":
    unittest.main()
