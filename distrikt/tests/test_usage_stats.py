"""Regression tests for read-only historical usage estimates (fictional events)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "app"))
from usage_stats import summarize


def event(at, actor=None, name=""):
    return {"at": "2026-11-21T" + at + "+00:00", "actor_id": actor,
            "actor_name": name, "action": "card.save",
            "cards": ["fictional-private-card"], "fields": ["name"]}


class UsageStatsTests(unittest.TestCase):
    def test_no_events_and_single_edit_are_not_invented_hours(self):
        self.assertEqual(summarize([])["person_minutes"], 0)
        single = summarize([event("10:00:00", "user-one")])
        self.assertEqual(single["person_minutes"], 0)
        self.assertEqual(single["system_minutes"], 0)
        self.assertEqual(single["actions"], 1)
        self.assertEqual(single["users"][0]["active_days"], 1)

    def test_15_minute_boundary_long_pause_and_out_of_order_events(self):
        result = summarize([event("11:00:00", "a"), event("10:15:00", "a"),
                            event("10:00:00", "a"), event("10:40:00", "a")])
        # 10:00->10:15 counts, 10:15->10:40 and 10:40->11:00 do not.
        self.assertEqual(result["person_minutes"], 15)
        self.assertEqual(result["system_minutes"], 15)
        self.assertEqual(result["actions"], 4)
        self.assertEqual(result["users"][0]["months"][0]["minutes"], 15)

    def test_same_actor_short_intervals_and_concurrent_actors(self):
        result = summarize([event("10:00:00", "a", "Person A"),
                            event("10:10:00", "a", "Person A"),
                            event("10:05:00", "b", "Person B"),
                            event("10:15:00", "b", "Person B")])
        self.assertEqual(result["person_minutes"], 20)
        self.assertEqual(result["system_minutes"], 15)
        self.assertEqual(len(result["users"]), 2)
        self.assertEqual(result["months"][0]["actions"], 4)

    def test_shared_login_is_not_attributed_to_named_users(self):
        result = summarize([event("10:00:00"),
                            event("10:10:00", None, "Untrusted supplied name"),
                            event("10:12:00", "known", "Recorded user")])
        self.assertEqual(result["actions"], 3)
        self.assertEqual(result["person_minutes"], 10)
        unknown = next(user for user in result["users"] if user["actor_id"] is None)
        self.assertEqual(unknown["actor_name"], "")
        self.assertEqual(unknown["minutes"], 10)
        self.assertEqual(next(user for user in result["users"]
                             if user["actor_id"] == "known")["minutes"], 0)
        self.assertNotIn("fictional-private-card", str(result))
        self.assertNotIn("Untrusted supplied name", str(result))

    def test_bad_stamps_do_not_break_dashboard(self):
        result = summarize([event("10:00:00", "known"),
                            {"at": "not-a-timestamp", "actor_id": "known"},
                            {"at": None}, {"at": "2026-11-21T12:00:00"}])
        self.assertEqual(result["actions"], 1)
        self.assertEqual(result["person_minutes"], 0)


if __name__ == "__main__":
    unittest.main()
