"""Review page: '+ Add or remove metrics' works on every layout, including reviewed layout packs (regression 27 Oct)."""
import re
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "streamlit"))
sys.path.insert(0, str(HERE))

from composer import apply_review  # noqa: E402
from persona_layouts import compose_persona  # noqa: E402
import test_persona as tp  # noqa: E402

BUNDLE = (HERE.parent / "streamlit" / "app_bundle.js").read_text(encoding="utf-8")
APP = (HERE.parent / "streamlit" / "app.py").read_text(encoding="utf-8")


def used(spec):
    return list(dict.fromkeys(m for pg in spec["pages"] for c in pg["components"]
                              for m in [c.get("metric_id"), c.get("metric2_id"), c.get("metric"), c.get("metric2"), *(c.get("metrics") or [])] if isinstance(m, str) and m))


class ReviewMetricsEditorTests(unittest.TestCase):
    def test_editor_is_never_hidden_for_reviewed_layouts(self):
        self.assertIn("+ Add or remove metrics", BUNDLE)
        self.assertNotIn("metrics are fixed", BUNDLE)
        # the editor section must not be conditional on the layout being a pack
        i = BUNDLE.index('"+ Add or remove metrics"')
        head = BUNDLE[BUNDLE.rindex('className: "rv2-block"', 0, i) - 200:i]
        self.assertNotRegex(head, r"s\.pack\s*(&&|\|\|)|!s\.pack")

    def test_pack_draft_starts_with_its_own_metrics_selected(self):
        self.assertIn('"selected": used, "used": used}', APP)


class ReviewAddMetricOnPackTests(unittest.TestCase):
    setUp = tp.PersonaTests.setUp
    ctx = tp.PersonaTests.ctx

    def test_added_metric_keeps_pack_tiles_and_adds_a_card(self):
        ctx = self.ctx("managers")[0]
        spec = compose_persona(None, ctx, "")
        own = used(spec)
        extra = next(m.id for m in self.model.metrics if m.id not in own)
        tiles_before = sum(len(p["components"]) for p in spec["pages"])
        out, _gov = apply_review(ctx, spec, own + [extra], [])
        tiles_after = [c for p in out["pages"] for c in p["components"]]
        self.assertGreater(len(tiles_after), tiles_before - 1)
        self.assertIn(extra, used(out))


if __name__ == "__main__":
    unittest.main()
