"""Unusual (anomaly) alerts: the normal range comes from the metric's own recent history, per series."""
import datetime as dt
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "streamlit"))
import alerts_core as core  # noqa: E402

NOW = dt.datetime(2026, 10, 27, 9, tzinfo=dt.timezone.utc)


def weeks(values, seg=None, end=dt.date(2026, 10, 19)):
    """Weekly rows ending with the week starting `end` (complete by NOW)."""
    out = []
    for i, v in enumerate(values):
        d = end - dt.timedelta(weeks=len(values) - 1 - i)
        r = {"PERIOD": d, "M0": v}
        if seg is not None:
            r["SEG"] = seg
        out.append(r)
    return out


SPEC = {"rule": "unusual", "grain": "week", "metric_label": "Delinquency Rate", "kind": "percent",
        "schedule": {"tz": "UTC"}, "direction": "either", "sensitivity": "normal"}


class UnusualTests(unittest.TestCase):
    def test_total_inside_range_does_not_fire(self):
        rows = weeks([0.055, 0.056, 0.054, 0.057, 0.055, 0.056, 0.055, 0.054, 0.056, 0.055, 0.057, 0.056, 0.055, 0.0565])
        r = core.evaluate(SPEC, rows, NOW)
        self.assertEqual(r["status"], "ok")
        self.assertIn("within its normal range", r["headline"])

    def test_segment_breaking_out_fires_and_is_named(self):
        calm = [0.055, 0.056, 0.054, 0.057, 0.055, 0.056, 0.055, 0.054, 0.056, 0.055, 0.057, 0.056, 0.055]
        rows = (weeks(calm + [0.0555], "(All)") + weeks(calm + [0.087], "Near-Prime Revolver")
                + weeks(calm + [0.056], "Prime Transactor"))
        spec = {**SPEC, "by": "SEG", "by_label": "Segment"}
        r = core.evaluate(spec, rows, NOW)
        self.assertEqual(r["status"], "fired")
        self.assertIn("Near-Prime Revolver", r["headline"])
        self.assertIn("above its normal range", r["headline"])
        self.assertTrue(r["key"].endswith("Near-Prime Revolver"))       # emailed once per period and segment set
        flagged = [x for x in r["series"] if x["unusual"]]
        self.assertEqual([x["segment"] for x in flagged], ["Near-Prime Revolver"])

    def test_direction_up_ignores_drops(self):
        calm = [100, 102, 98, 101, 99, 100, 103, 97, 100, 101, 99, 100, 102]
        r = core.evaluate({**SPEC, "kind": "number", "direction": "up"}, weeks(calm + [60]), NOW)
        self.assertEqual(r["status"], "ok")
        r = core.evaluate({**SPEC, "kind": "number", "direction": "down"}, weeks(calm + [60]), NOW)
        self.assertEqual(r["status"], "fired")

    def test_high_sensitivity_fires_earlier(self):
        calm = [100, 102, 98, 101, 99, 100, 103, 97, 100, 101, 99, 100, 102]
        rows = weeks(calm + [104])
        self.assertEqual(core.evaluate({**SPEC, "kind": "number"}, rows, NOW)["status"], "ok")
        self.assertEqual(core.evaluate({**SPEC, "kind": "number", "sensitivity": "high"}, rows, NOW)["status"], "fired")

    def test_a_build_up_over_recent_weeks_still_fires(self):
        calm = [100, 102, 98, 101, 99, 100, 103, 97, 100, 101, 99, 100, 102]
        r = core.evaluate({**SPEC, "kind": "number", "direction": "up"}, weeks(calm + [106, 110, 114, 118]), NOW)
        self.assertEqual(r["status"], "fired")                    # the 3 weeks before the latest are not 'normal'
        self.assertIn("13 weeks before the last 4", dict(r["facts"])["Normal range based on"])

    def test_not_enough_history(self):
        r = core.evaluate(SPEC, weeks([0.05, 0.06, 0.05]), NOW)
        self.assertEqual(r["status"], "no_data")

    def test_unfinished_week_is_ignored(self):
        calm = [100, 102, 98, 101, 99, 100, 103, 97, 100, 101, 99, 100, 102]
        rows = weeks(calm) + [{"PERIOD": dt.date(2026, 10, 26), "M0": 5}]       # this week, still arriving
        self.assertEqual(core.evaluate({**SPEC, "kind": "number"}, rows, NOW)["status"], "ok")

    def test_rule_text(self):
        self.assertIn("normal range", core.describe({**SPEC, "by": "X", "by_label": "Segment"}))
        self.assertIn("any Segment", core.threshold_text({**SPEC, "by": "X", "by_label": "Segment"}))


class UnusualSpecTests(unittest.TestCase):
    def test_check_sql_has_total_and_segments(self):
        import os
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        os.environ.setdefault("AA_FAKE_SNOWFLAKE", "1")
        import alerts
        from fake_snowflake import FakeSession
        from semantic_catalog import describe_semantic_view
        s = FakeSession()
        m = describe_semantic_view(s, "WBR_DB.PUBLIC.SUPERSTORE_DEMO_SV")
        dim = m.categorical_dimensions[0]
        met = m.metrics[0]
        tdim = m.time_dimensions[0].id
        spec, issues = alerts.normalize(m, {"metric": met.id, "rule": "unusual", "by": dim.label, "grain": "week",
                                            "recipients": ["a@b.com"]}, {dim.id: ["x", "y"]}, tdim)
        self.assertEqual(issues, [])
        self.assertEqual((spec["rule"], spec["by"], spec["sensitivity"], spec["direction"]), ("unusual", dim.id, "normal", "either"))
        sql = alerts.check_sql(m, spec)
        self.assertIn("UNION ALL", sql)
        self.assertIn("'(All)' AS SEG", sql)
        self.assertIn("AS SEG", sql.split("UNION ALL")[1])

    def test_plain_english_reads_unusual(self):
        import alerts
        opts = {"metrics": [{"id": "M.DELINQUENCY_RATE", "label": "Delinquency Rate", "kind": "percent", "plan": False}],
                "dims": [{"id": "S.SEGMENT_NAME", "label": "Segment", "values": ["Prime"]}]}
        out = alerts.fallback_read(opts, "Tell me when delinquency rate looks unusual for any segment", {})
        self.assertEqual((out["rule"], out.get("by")), ("unusual", "S.SEGMENT_NAME"))


if __name__ == "__main__":
    unittest.main()
