"""Meeting brief + Share snapshot (28 Oct): builder app and Portal; brief figures checked against governed facts."""
import re
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "streamlit"))
import validation  # noqa: E402

BUNDLE = (HERE.parent / "streamlit" / "app_bundle.js").read_text(encoding="utf-8")
APP = (HERE.parent / "streamlit" / "app.py").read_text(encoding="utf-8")


class BriefShareTests(unittest.TestCase):
    def test_available_in_builder_and_portal(self):
        viewer = re.search(r"VIEWER_ACTIONS = \{([^}]*)\}", APP).group(1)
        self.assertIn('"meeting_brief"', viewer)
        self.assertIn('"brief_close"', viewer)
        self.assertRegex(APP, r'"meeting_brief": meeting_brief')

    def test_brief_is_rate_limited(self):
        self.assertIn('"meeting_brief"', re.search(r"AI_ACTIONS = \{[^}]*\}", APP, re.S).group(0))

    def test_unmatched_figures_are_dropped(self):
        facts = ["Delinquency Rate = 3.9% (+0.2 pts vs prior)", "Net Chargeoffs = $39.5M"]
        _m, bad = validation.grounded("Revenue could fall 37.3% next quarter", facts)
        self.assertTrue(bad)
        _m, bad = validation.grounded("Delinquency is 3.9%, up 0.2 pts; charge-offs $39.5M", facts)
        self.assertFalse(bad)
        self.assertIn("validation.grounded(t, facts)", APP)

    def test_buttons_added_beside_existing_ones(self):
        for s in ('children: "Meeting brief"', 'children: "Share snapshot"', 'children: "Save draft"', '"← Metrics & outline"'):
            self.assertIn(s, BUNDLE)
        self.assertIn("Snapshot · not live", BUNDLE)

    def test_snapshot_covers_every_page(self):
        self.assertIn("aaSnapshot(ev.currentTarget, e, r.pages, a, u)", BUNDLE)
        self.assertIn("Page ${n + 1} of ${sections.length}", BUNDLE)
        self.assertIn("break-before:page", BUNDLE)

    def test_brief_cleared_when_another_dashboard_opens(self):
        self.assertIn('S["brief"] = None', APP)


if __name__ == "__main__":
    unittest.main()
