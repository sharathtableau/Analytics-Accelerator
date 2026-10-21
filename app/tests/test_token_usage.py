"""Token usage is read from AI_COMPLETE show_details and from the agent response, without ACCOUNT_USAGE."""
import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "streamlit"))

import ai_services  # noqa: E402
from ai_services import Cortex  # noqa: E402


class _Row(dict):
    def as_dict(self):
        return dict(self)


class _Q:
    def __init__(self, rows):
        self.rows = rows

    def collect(self):
        return self.rows


class DetailSession:
    """Answers the show_details call with the documented JSON shape."""
    def __init__(self, text, fail_details=False):
        self.text, self.fail_details, self.calls = text, fail_details, []

    def sql(self, q, params=None):
        self.calls.append(q)
        if "show_details" in q:
            if self.fail_details:
                raise RuntimeError("invalid argument show_details")
            return _Q([_Row(R=json.dumps({"choices": [{"messages": self.text}], "created": 1, "model": "m",
                                          "usage": {"prompt_tokens": 2950, "completion_tokens": 640,
                                                    "total_tokens": 3590}}))])
        return _Q([_Row(R=json.dumps(self.text))])


class TokenUsageTest(unittest.TestCase):
    def setUp(self):
        ai_services._DETAILS["ok"] = True

    def test_show_details_text_and_usage(self):
        ledger = []
        c = Cortex(DetailSession('{"a": 1}'), "DB.SCH", usage=ledger)
        text, prov = c.complete("design a dashboard")
        self.assertEqual(text, '{"a": 1}')
        self.assertIn("2,950 in / 640 out tokens", prov)
        self.assertEqual((ledger[0]["in"], ledger[0]["out"]), (2950, 640))

    def test_falls_back_when_show_details_rejected(self):
        s = DetailSession("hello", fail_details=True)
        c = Cortex(s, "DB.SCH")
        text, prov = c.complete("x")
        self.assertEqual(text, "hello")
        self.assertNotIn("tokens", prov)
        self.assertFalse(ai_services._DETAILS["ok"])
        n = len(s.calls)
        c.complete("y")                      # does not retry show_details once rejected
        self.assertEqual(sum("show_details" in q for q in s.calls[n:]), 0)

    def test_agent_tokens_from_response_metadata(self):
        import agent_service
        payload = {"role": "assistant", "content": [{"type": "text", "text": "Because of HLO-INV-008."}],
                   "metadata": {"run_id": "r1", "usage": {"tokens_consumed": [
                       {"model_name": "claude-sonnet-4-5",
                        "input_tokens": {"total": 21000, "cache_read": 9000, "cache_write": 4000, "uncached": 8000},
                        "output_tokens": {"total": 700}},
                       {"model_name": "claude-sonnet-4-5", "input_tokens": {"total": 4000}, "output_tokens": {"total": 300}}]}}}

        class AgentSession:
            def sql(self, q, params=None):
                return _Q([_Row(R=json.dumps(payload))])

        ans = agent_service.ask_agent(AgentSession(), "DB.SCH.AA_X_AGENT", "why?", None)
        self.assertEqual(ans["tokens"], {"in": 25000, "cache_read": 9000, "cache_write": 4000, "out": 1000})


if __name__ == "__main__":
    unittest.main()
