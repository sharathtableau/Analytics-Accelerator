import unittest
from headlines import headline
from engine import fmt


class HeadlineTests(unittest.TestCase):
    def test_ranked(self):
        d = {"metric_label": "Profit", "kind": "currency", "prior_label": "last week",
             "rows": [{"segment": "South", "current": 1800, "change": 1.31},
                      {"segment": "Central", "current": 596, "change": 0.2}]}
        h = headline("ranked_bar", d, fmt)
        self.assertTrue(h.startswith("South leads Profit"))
        self.assertIn("+131%", h); self.assertIn("Central trails", h)

    def test_trend_peak(self):
        d = {"metric_label": "Sales", "kind": "number",
             "points": [{"label": "Jan", "value": 1}, {"label": "Feb", "value": 2}, {"label": "Mar", "value": 5}]}
        self.assertIn("the highest in 3 periods", headline("trend_chart", d, fmt))

    def test_donut_and_pareto(self):
        self.assertIn("60% of Sales", headline("share_donut", {"metric_label": "Sales",
                      "slices": [{"label": "West", "share": 0.6}]}, fmt))
        self.assertIn("3 of 20", headline("pareto", {"n80": 3, "total_count": 20, "dimension_label": "Products",
                      "metric_label": "Sales"}, fmt))

    def test_unknown_or_bad_data_is_silent(self):
        self.assertEqual(headline("kpi_strip", {}, fmt), "")
        self.assertEqual(headline("ranked_bar", {"rows": None}, fmt), "")
        self.assertEqual(headline("trend_chart", {"points": [{"label": "x"}]}, fmt), "")


if __name__ == "__main__":
    unittest.main()
