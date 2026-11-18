"""Run actual new benchmark with small fictional SQLite and check cache signals."""
import json
import subprocess
import sys
import unittest
from pathlib import Path


class GeoCacheBenchmarkSmoke(unittest.TestCase):
    def test_measurement_contract_and_durable_reopen(self):
        script = Path(__file__).resolve().parents[2] / "scripts" / "benchmark_geo_cache_97.py"
        completed = subprocess.run([sys.executable, str(script), "--addresses", "60",
            "--cards", "3", "--history", "4", "--roads", "2", "--buildings", "4",
            "--runs", "3"], check=True, capture_output=True, text=True, timeout=60)
        report = json.loads(completed.stdout)
        self.assertEqual(report["dataset"]["addresses"], 60)
        self.assertEqual(len(report["cases"]), 3)
        for case in report["cases"]:
            self.assertEqual(len(case["geo_generation_deltas"]), 3)
            self.assertGreater(case["payload"]["receipt_json_bytes"], 0)
            self.assertGreater(case["payload"]["receipt_gzip_bytes"], 0)
            self.assertEqual(case["payload"]["geo_address_count"], 60)
            for durations in case["samples_ms"].values():
                self.assertEqual(len(durations), 3)
            if case["scenario"] == "loan_finish_plus_polygon":
                self.assertEqual(case["geo_generation_deltas"], [1] * 3)
                self.assertEqual(case["geo_cache_reused"], [False] * 3)
            else:
                self.assertEqual(case["geo_generation_deltas"], [0] * 3)
                self.assertEqual(case["geo_cache_reused"], [True] * 3)


if __name__ == "__main__":
    unittest.main()
