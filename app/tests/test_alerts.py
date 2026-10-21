"""Data alerts: rules, schedule, once-per-period email, plain-English reading, governed check SQL, procedure body."""
import datetime as dt
import os
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "streamlit"))
sys.path.insert(0, str(HERE))

import alerts  # noqa: E402
import alerts_core as core  # noqa: E402
from ai_services import Cortex  # noqa: E402
from fake_snowflake import FakeSession, SV  # noqa: E402
from inventory import infer_bindings  # noqa: E402
from semantic_catalog import describe_semantic_view  # noqa: E402
from semantic_query import SemanticQuery, distinct_values  # noqa: E402
from store import Store  # noqa: E402
from test_composer import APP  # noqa: E402

UTC = dt.timezone.utc


def rows(vals, start=dt.date(2026, 10, 1), plan=None):
    return [{"PERIOD": start + dt.timedelta(days=i), "M0": v, **({"M1": plan[i]} if plan else {})}
            for i, v in enumerate(vals)]


class RuleTests(unittest.TestCase):
    def test_threshold_percent_and_amount(self):
        sp = {"rule": "threshold", "op": "below", "value": 0.5, "kind": "percent", "grain": "day"}
        r = core.evaluate(sp, rows([0.55, 0.487]))
        self.assertTrue(r["fired"])
        self.assertIn("48.7% vs limit 50.0%", r["detail"])
        self.assertEqual(r["key"], "threshold:2026-10-02")
        self.assertFalse(core.evaluate({**sp, "op": "above"}, rows([0.55, 0.487]))["fired"])

    def test_unfinished_period_and_amount_named_like_a_ratio(self):
        now = dt.datetime(2026, 10, 21, 11, tzinfo=UTC)
        sp = {"rule": "change", "direction": "down", "pct": 60, "compare": "year", "kind": "percent", "grain": "day",
              "metric_label": "Gross Margin", "schedule": {"tz": "UTC"}}
        data = [{"PERIOD": dt.date(2025, 10, 21), "M0": 540000}, {"PERIOD": dt.date(2025, 10, 22), "M0": 545000},
                {"PERIOD": dt.date(2026, 10, 20), "M0": 548000}, {"PERIOD": dt.date(2026, 10, 21), "M0": 52000}]
        r = core.evaluate(sp, data, now)
        self.assertEqual(r["period"], "2026-10-20")                  # today (still loading) is not used
        self.assertEqual(r["kind"], "currency")                      # GROSS_MARGIN values are amounts, not %
        self.assertFalse(r["fired"])
        self.assertIn("$548.0K", r["facts"][0][1])
        subj, body = core.email(sp, r, test=True, app_url="https://x")
        self.assertTrue(subj.startswith("[TEST] Alert check: Gross Margin rose"))
        self.assertNotIn("pt", subj)

    def test_missing_limit_does_not_crash(self):
        r = core.evaluate({"rule": "threshold", "op": "below", "kind": "number"}, rows([5, 4]))
        self.assertEqual((r["status"], r["fired"]), ("incomplete", False))
        self.assertIn("enter a value", core.describe({"metric_label": "Orders", "rule": "threshold", "grain": "day"}))
        self.assertEqual(core.evaluate({"rule": "change", "kind": "number"}, rows([5, 4]))["status"], "incomplete")

    def test_change_prior_and_year(self):
        sp = {"rule": "change", "direction": "down", "pct": 10, "compare": "prior", "kind": "currency", "grain": "day"}
        self.assertTrue(core.evaluate(sp, rows([100, 85]))["fired"])
        self.assertFalse(core.evaluate(sp, rows([100, 95]))["fired"])
        self.assertTrue(core.evaluate({**sp, "direction": "either"}, rows([100, 120]))["fired"])
        yr = [{"PERIOD": dt.date(2025, 10, 3), "M0": 200},                       # same weekday, 364 days back {"PERIOD": dt.date(2026, 10, 1), "M0": 150},
              {"PERIOD": dt.date(2026, 10, 2), "M0": 170}]
        r = core.evaluate({**sp, "compare": "year"}, yr)
        self.assertTrue(r["fired"])
        self.assertEqual(r["compare"], 200)
        pt = {"rule": "change", "direction": "down", "pct": 2, "compare": "prior", "kind": "percent", "grain": "day"}
        self.assertTrue(core.evaluate(pt, rows([0.52, 0.49]))["fired"])        # 3 points down
        self.assertFalse(core.evaluate(pt, rows([0.52, 0.51]))["fired"])

    def test_plan_and_freshness(self):
        sp = {"rule": "plan", "plan_dir": "below", "pct": 10, "kind": "currency", "grain": "day"}
        self.assertTrue(core.evaluate(sp, rows([100, 85], plan=[100, 100]))["fired"])
        self.assertFalse(core.evaluate(sp, rows([100, 95], plan=[100, 100]))["fired"])
        self.assertEqual(core.evaluate(sp, rows([100, 95]))["status"], "no_data")
        fr = {"rule": "freshness", "days": 1, "kind": "number", "schedule": {"tz": "UTC"}}
        now = dt.datetime(2026, 10, 21, 9, tzinfo=UTC)
        self.assertFalse(core.evaluate(fr, rows([5], start=dt.date(2026, 10, 20)), now)["fired"])
        self.assertTrue(core.evaluate(fr, rows([5], start=dt.date(2026, 10, 18)), now)["fired"])
        self.assertTrue(core.evaluate(fr, [], now)["fired"])

    def test_schedule_due(self):
        now = dt.datetime(2026, 10, 21, 3, 30, tzinfo=UTC)              # 09:00 in Kolkata
        daily9 = {"freq": "daily", "hour": 9, "tz": "Asia/Kolkata"}
        self.assertTrue(core.is_due(daily9, None, now))
        self.assertTrue(core.is_due(daily9, "2026-10-20T03:30:00+00:00", now))
        self.assertFalse(core.is_due(daily9, "2026-10-21T03:31:00+00:00", now))
        self.assertFalse(core.is_due(daily9, "2026-10-21T03:30:00+00:00", dt.datetime(2026, 10, 21, 3, 20, tzinfo=UTC)))
        self.assertTrue(core.is_due({"freq": "hourly"}, "2026-10-21T02:59:00+00:00", now))
        self.assertIn("Weekly, Monday 08:00", core.schedule_text({"freq": "weekly", "weekday": 0, "hour": 8, "tz": "UTC"}))


class AppSideTests(unittest.TestCase):
    def setUp(self):
        self.s = FakeSession()
        self.m = describe_semantic_view(self.s, SV)
        self.t = infer_bindings(self.m).time_dimension
        q = SemanticQuery(self.s, self.m)
        self.dv = {d.id: distinct_values(q, d.id) for d in self.m.categorical_dimensions}
        self.opts = alerts.options(self.m, self.dv)

    def test_normalize_checks_every_part(self):
        sp, issues = alerts.normalize(self.m, {"metric": "Profit Ratio", "filters": {"Region": ["west"]},
                                               "rule": "threshold", "value_input": 50, "recipients": ["A@X.com", "bob"],
                                               "schedule": {"freq": "daily", "hour": 9, "tz": "Asia/Kolkata"}},
                                      self.dv, self.t)
        self.assertEqual((sp["metric"], sp["value"], sp["filters"]), ("ORDERS.PROFIT_RATIO", 0.5, {"ORDERS.REGION": ["West"]}))
        self.assertEqual(sp["recipients"], ["a@x.com"])
        self.assertTrue(any("bob" in i for i in issues))
        _, issues = alerts.normalize(self.m, {"metric": "ORDERS.NOPE", "filters": {"ORDERS.REGION": ["Mars"]},
                                              "recipients": []}, self.dv, self.t)
        self.assertTrue(any("not a metric" in i for i in issues))
        self.assertTrue(any("Mars" in i for i in issues))
        self.assertTrue(any("email" in i for i in issues))
        _, issues = alerts.normalize(self.m, {"metric": "ORDERS.PROFIT", "rule": "plan", "pct": 5,
                                              "recipients": ["a@x.com"]}, self.dv, self.t)
        self.assertTrue(any("no plan" in i for i in issues))
        sp, issues = alerts.normalize(self.m, {"metric": "ORDERS.SALES", "rule": "plan", "pct": 5,
                                               "recipients": ["a@x.com"]}, self.dv, self.t)
        self.assertEqual((sp["plan_metric"], issues), ("ORDERS.PLAN_SALES", []))

    def test_check_sql_is_governed_and_runs(self):
        sp, _ = alerts.normalize(self.m, {"metric": "ORDERS.SALES", "rule": "plan", "pct": 5, "grain": "month",
                                          "filters": {"ORDERS.REGION": ["West"]}, "recipients": ["a@x.com"]}, self.dv, self.t)
        sql = alerts.check_sql(self.m, sp)
        self.assertIn("SEMANTIC_VIEW(", sql)
        self.assertIn("ORDERS.PLAN_SALES AS M1", sql)
        self.assertIn("ORDERS.REGION IN ('West')", sql)
        got = SemanticQuery(self.s, self.m).run(sql)
        self.assertGreater(len(got), 6)
        self.assertIn(core.evaluate(sp, got)["status"], ("ok", "fired"))

    def test_plain_english_with_cortex_and_fallback(self):
        cx = Cortex(self.s, APP, ["claude-sonnet-4-5"], [], [])
        f, q, prov = alerts.parse_text(cx, self.opts, "Email me@blend360.com if West profit ratio drops below 12%", {})
        self.assertEqual((f["metric"], f["filters"], f["recipients"]), ("ORDERS.PROFIT_RATIO", {"ORDERS.REGION": ["West"]},
                                                                      ["me@blend360.com"]))
        self.assertIn("Cortex", prov)
        f, q, _ = alerts.parse_text(cx, self.opts, "tell priya if west margin is low", {})
        self.assertIn("Priya", q)
        self.assertIn("Profit Ratio", q)
        fb, _, prov = alerts.parse_text(None, self.opts, "a@b.com wants Sales for East more than 10% behind plan weekly", {})
        self.assertEqual((fb["metric"], fb["rule"], fb["pct"], fb["filters"]), ("ORDERS.SALES", "plan", 10.0, {"ORDERS.REGION": ["East"]}))
        self.assertEqual(fb["schedule"]["freq"], "weekly")
        self.assertIn("rule-based", prov)
        fb, _, _ = alerts.parse_text(None, self.opts, "if there is no new data for 2 days at 7am email x@y.com", {"metric": "ORDERS.SALES"})
        self.assertEqual((fb["rule"], fb["days"], fb["schedule"]["hour"]), ("freshness", 2, 7))

    def test_run_emails_once_per_period_and_logs_failures(self):
        st = Store(self.s, APP)
        st.actor = "SHARATH"
        sp, _ = alerts.normalize(self.m, {"metric": "ORDERS.PROFIT_RATIO", "rule": "threshold", "value_input": 99,
                                          "recipients": ["sharath.kammari@blend360.com"]}, self.dv, self.t)
        aid = st.save_alert(sp, alerts.check_sql(self.m, sp))
        out = core.run_alerts(self.s, APP, force=True, trigger="manual")
        self.assertEqual((out[0]["fired"], out[0]["emailed"]), (True, True))
        self.assertEqual(len(self.s.tables["EMAILS"]), 1)
        self.assertIn("Profit Ratio", self.s.tables["EMAILS"][0]["subject"])
        self.assertEqual(self.s.tables["EMAILS"][0]["integration"], "AA_EMAIL_INT")
        out = core.run_alerts(self.s, APP, force=True, trigger="manual")
        self.assertEqual((out[0]["emailed"], out[0]["note"]), (False, "Already emailed for this period."))
        st.set_alert(aid, active=False)
        self.assertEqual(core.run_alerts(self.s, APP, trigger="schedule"), [])          # paused: skipped
        st.set_alert(aid, active=True)
        st.save_alert(sp, alerts.check_sql(self.m, sp), aid)                           # edit resets the period key
        os.environ["AA_FAKE_NO_EMAIL"] = "1"
        try:
            out = core.run_alerts(self.s, APP, only_id=aid, trigger="manual")
        finally:
            del os.environ["AA_FAKE_NO_EMAIL"]
        self.assertIn("Email not sent", out[0]["note"])
        runs = st.alert_runs(aid)
        self.assertEqual(len(runs), 3)
        self.assertEqual(st.list_alerts()[0]["last_status"], "fired")
        st.set_alert(aid, deleted=True)
        self.assertEqual(st.list_alerts(), [])

    def test_procedure_body_is_the_core(self):
        ddl = alerts.proc_ddl(APP, "https://app")
        self.assertIn("AA_RUN_ALERTS(ALERT_ID VARCHAR, FORCE BOOLEAN, TRIGGER_KIND VARCHAR)", ddl)
        body = ddl.split("AS $$\n", 1)[1].rsplit("\n$$", 1)[0]
        ns = {}
        exec(compile(body, "proc", "exec"), ns)
        self.assertEqual(ns["SCHEMA"], APP)
        self.assertIn("SCHEDULE = 'USING CRON 0 * * * * UTC'", alerts.task_ddl(APP, "POWERHOUSE")[0])


if __name__ == "__main__":
    unittest.main()
