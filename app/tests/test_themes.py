"""Company themes: parsing brand inputs, derived tokens, WCAG checks and fixes, storage."""
import base64
import io
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "streamlit"))
sys.path.insert(0, str(HERE))

import themes as T  # noqa: E402
from fake_snowflake import FakeSession  # noqa: E402
from store import Store  # noqa: E402
from test_composer import APP  # noqa: E402


class ThemeTests(unittest.TestCase):
    def test_contrast_maths(self):
        self.assertAlmostEqual(T.contrast("#000000", "#ffffff"), 21.0, places=1)
        self.assertAlmostEqual(T.contrast("#777777", "#ffffff"), 4.48, places=1)
        self.assertLess(T.delta_e("#ff0000", "#fe0101"), 2)
        self.assertEqual(T.norm("#ABC"), "#aabbcc")
        self.assertIsNone(T.norm("red"))

    def test_build_meets_wcag_after_fixes(self):
        for inp in ({"primary": "#F40009"}, {"primary": "#ffd100", "chart": ["#ffd100", "#ffe14d", "#00a3e0"]},
                    {"primary": "#7fdbff", "background": "#0b0f14"}, {"primary": "#29B5E8", "text": "#999999"}):
            out = T.build(inp)
            k = out["tokens"]
            self.assertGreaterEqual(T.contrast(k["ink"], k["card"]), 4.5, inp)
            self.assertGreaterEqual(T.contrast(k["ink"], k["bg"]), 4.5, inp)
            self.assertGreaterEqual(T.contrast(k["muted"], k["card"]), 4.5, inp)
            self.assertGreaterEqual(T.contrast(k["on-primary"], k["primary"]), 4.5, inp)
            chart = [k[f"c{i}"] for i in range(1, 7)]
            for c in chart:
                self.assertGreaterEqual(T.contrast(c, k["card"]), 3.0, (inp, c))
            for a in range(6):
                for b in range(a):
                    self.assertGreaterEqual(T.delta_e(chart[a], chart[b]), 15, (inp, chart[a], chart[b]))
            self.assertNotEqual(out["status"], "fail", (inp, [c for c in out["checks"] if c["status"] == "fail"]))

    def test_fixes_are_reported_with_before_and_after(self):
        out = T.build({"primary": "#0b5394", "text": "#aaaaaa"})
        t01 = [c for c in out["checks"] if c["id"] == "T-01" and c["role"] == "text"]
        self.assertEqual(t01[0]["status"], "fixed")
        self.assertEqual(t01[0]["from"], "#aaaaaa")
        self.assertGreaterEqual(T.contrast(t01[0]["to"], out["tokens"]["card"]), 4.5)
        self.assertEqual(out["status"], "fixed")

    def test_same_colour_family_for_good_and_bad_fails(self):
        out = T.build({"primary": "#0b5394", "positive": "#c0392b", "negative": "#e74c3c"})
        self.assertEqual(next(c for c in out["checks"] if c["label"].startswith("Positive and negative"))["status"], "fail")
        self.assertEqual(out["status"], "fail")

    def test_needs_a_primary(self):
        with self.assertRaises(ValueError):
            T.build({"accent": "#ff0000"})

    def test_parse_json_tokens_any_shape(self):
        doc = {"color": {"brand": {"primary": {"value": "#003da5"}, "secondary": {"$value": "#e4002b"}},
                         "text": {"default": "#222"}, "feedback": {"success": "#1e8449", "danger": "#c0392b"},
                         "chart": ["#003da5", "#6cace4", "#e4002b"]}}
        got = T.parse_tokens(json.dumps(doc))
        self.assertEqual(got["primary"], "#003da5")
        self.assertEqual(got["accent"], "#e4002b")
        self.assertEqual(got["text"], "#222222")
        self.assertEqual(got["positive"], "#1e8449")
        self.assertEqual(got["negative"], "#c0392b")
        self.assertEqual(got["chart"], ["#003da5", "#6cace4", "#e4002b"])

    def test_parse_css_variables(self):
        got = T.parse_tokens(":root{--brand-primary:#0b5394;--color-success:#1e8449;--bg-page:#fafafa;"
                             "--chart-1:#0b5394;--chart-2:#e69138}")
        self.assertEqual((got["primary"], got["positive"], got["background"]), ("#0b5394", "#1e8449", "#fafafa"))
        self.assertEqual(got["chart"], ["#0b5394", "#e69138"])

    def test_logo_colours(self):
        svg = (b'<svg xmlns="http://www.w3.org/2000/svg"><rect fill="#0b5394"/><rect fill="#0b5394"/>'
               b'<path fill="#e69138"/><text fill="#222222">x</text></svg>')
        got = T.parse_logo(svg, "logo.svg")
        self.assertEqual(got["primary"], "#0b5394")
        self.assertEqual(got["accent"], "#e69138")
        from PIL import Image
        img = Image.new("RGB", (60, 40), "#ffffff")
        for x in range(40):
            for y in range(40):
                img.putpixel((x, y), (11, 83, 148))
        buf = io.BytesIO()
        img.save(buf, "PNG")
        got = T.parse_upload("logo", "logo.png", base64.b64encode(buf.getvalue()).decode())
        self.assertLess(T.delta_e(got["primary"], "#0b5394"), 6)

    def test_upload_limits_and_junk(self):
        with self.assertRaises(ValueError):
            T.parse_upload("logo", "x.png", base64.b64encode(b"0" * 1_600_000).decode())
        self.assertEqual(T.parse_tokens("<script>alert(1)</script>"), {"chart": []})

    def test_css_vars_only_pass_colours(self):
        v = T.css_vars({"bg": "#ffffff", "c1": "url(javascript:x)", "x;y": "#000000", "ink": "#111111"})
        self.assertEqual(v, {"--bg": "#ffffff", "--ink": "#111111"})

    def test_store_round_trip_and_history(self):
        s = Store(FakeSession(), APP)
        out = T.build({"primary": "#0b5394"})
        tid = s.save_theme("", "Harborline", "form", out["inputs"], out["tokens"], out["checks"], out["status"])
        s.save_theme(tid, "Harborline v2", "form", out["inputs"], out["tokens"], out["checks"], out["status"])
        ts = s.list_themes()
        self.assertEqual([t["name"] for t in ts], ["Harborline v2"])
        self.assertEqual(ts[0]["tokens"]["c1"], out["tokens"]["c1"])
        s.set_setting("default_theme", "t:" + tid)
        self.assertEqual(s.get_setting("default_theme")["setting_value"], "t:" + tid)
        s.save_theme(tid, "Harborline v2", "form", {}, {}, [], "pass", active=False)
        self.assertEqual(s.list_themes(), [])


if __name__ == "__main__":
    unittest.main()
