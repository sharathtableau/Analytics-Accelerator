"""Guard test (29 Oct, Option A): with a persona picked, its ideas sit right under the prompt box and the
'About this role' card sits beside them. Nothing on the card may be lost in the move."""
import pathlib
import unittest

BUNDLE = (pathlib.Path(__file__).resolve().parent.parent / "streamlit" / "app_bundle.js").read_text(encoding="utf-8")
CSS = (pathlib.Path(__file__).resolve().parent.parent / "streamlit" / "app_styles.css").read_text(encoding="utf-8")


class HomeLayoutTests(unittest.TestCase):
    def _split(self):
        i = BUNDLE.index('className: "persona-split"')
        j = BUNDLE.index('o && !per && (f.length ?', i)
        return BUNDLE[i:j]

    def test_ideas_then_card_side_by_side(self):
        part = self._split()
        self.assertLess(part.index('"ideas persona-ideas"'), part.index('"persona-card side"'))
        self.assertIn(".aa .persona-split{", CSS)

    def test_card_keeps_everything(self):
        part = self._split()
        for must in ("About this role", "Owns: ", "Decides: ", "Watches: ", "pc-edit", "lens_save", '"Approve"', '"Edit"',
                     '"pc-chip"', "Uses these metrics: ", "Alerts they own: ", "Not in this data: "):
            self.assertIn(must, part, must)
        self.assertEqual(BUNDLE.count('className: "persona-card", children'), 0)   # not also drawn above the ideas

    def test_data_strip_kept_for_both_cases(self):
        self.assertIn('o && !per && /* @__PURE__ */ l.jsxs("div", { className: "featured-bar"', BUNDLE)
        self.assertIn('o && per && /* @__PURE__ */ l.jsxs("div", { className: "featured-bar"', BUNDLE)
        self.assertEqual(BUNDLE.count("Connect a Snowflake table"), 2)
        self.assertEqual(BUNDLE.count('" found but not used for ideas"'), 2)


if __name__ == "__main__":
    unittest.main()
