"""Fictional Store benchmark smoke; never uses the installed data directory."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
from benchmark_geo_store import execute


class SyntheticStoreBenchmarkSmoke(unittest.TestCase):
    def test_fictional_store_counts_survive_small_write(self):
        report = execute(addresses=30, cards=3, roads=2, buildings=5,
                         history=4, runs=3)
        self.assertEqual(report["dataset"]["addresses"], 30)
        self.assertEqual(report["dataset"]["cards"], 3)
        self.assertEqual(report["dataset"]["history"], 4)
        self.assertGreater(report["dataset"]["geo_json_bytes"], 0)
        self.assertEqual(len(report["small_store_write_plus_refresh"]["repetitions_ms"]), 3)
        self.assertEqual(len(report["cold_geo_state"]["repetitions_ms"]), 3)


if __name__ == "__main__":
    unittest.main()
