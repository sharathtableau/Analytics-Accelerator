"""Set me up (27 Oct): interview -> proposal to tick -> built drafts + alerts. Added beside existing features, never
replacing them; builder app only."""
import re
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
BUNDLE = (HERE.parent / "streamlit" / "app_bundle.js").read_text(encoding="utf-8")
APP = (HERE.parent / "streamlit" / "app.py").read_text(encoding="utf-8")


class SetMeUpTests(unittest.TestCase):
    def test_actions_registered(self):
        for a in ("setup_start", "setup_propose", "setup_build", "setup_close", "setup_open"):
            self.assertRegex(APP, rf'"{a}": {a}\b')

    def test_builder_only(self):
        portal = re.search(r"VIEWER_ACTIONS = \{([^}]*)\}", APP).group(1)
        self.assertNotIn("setup_", portal)

    def test_unsaved_work_is_asked_first(self):
        self.assertIn('"setup_build"', re.search(r"LEAVE_ACTIONS = \{[^}]*\}", APP).group(0))
        self.assertIn('must_confirm_leave("setup_build", p)', APP)

    def test_cortex_call_is_rate_limited(self):
        self.assertIn('"setup_propose"', re.search(r"AI_ACTIONS = \{[^}]*\}", APP, re.S).group(0))

    def test_proposal_is_ticked_before_building(self):
        self.assertIn("Draft my setup", BUNDLE)
        self.assertIn('send("setup_build", { dashboards: [...ds], alerts: [...as], tz }', BUNDLE)

    def test_existing_home_features_kept(self):
        for label in ('"✦ Set me up"', '"+ Add or remove metrics"', "Ideas for the "):
            self.assertIn(label, BUNDLE)
        self.assertIn('t("route_prompt"', BUNDLE)


    def test_your_role_merged_into_set_me_up(self):
        # 28 Oct, Sharath: '+ Your role' merged into Set me up; the quick path stays as 'Just create my persona'
        self.assertNotIn('children: "+ Your role"', BUNDLE)
        self.assertIn('"Just create my persona →"', BUNDLE)
        self.assertRegex(APP, r'"setup_quick": setup_quick')


if __name__ == "__main__":
    unittest.main()
