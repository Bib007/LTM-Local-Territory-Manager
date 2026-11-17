"""Reproducible local-only Store/SQLite profiling with disposable, fictional data.

Run: python scripts/benchmark_geo_store.py --addresses 12000 --cards 240 --runs 7
This is not a profile-authenticated HTTP benchmark and does not bypass any
application permission checks: writes here are direct temporary Store fixtures.
"""
from __future__ import annotations

import argparse
import json
import platform
import sqlite3
import sys
import tempfile
import time
from pathlib import Path
from statistics import median

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "distrikt" / "app"))
from store import Store  # noqa: E402


def measure(fn, runs):
    times = []
    for _ in range(runs):
        started = time.perf_counter()
        fn()
        times.append(round((time.perf_counter() - started) * 1000, 3))
    return {"median_ms": median(times), "repetitions_ms": times}


def fixture(store, addresses, cards, roads, buildings, history):
    card_rows = [
        {
            "id": f"fictional-c{i}", "number": str(i + 1), "kind": "By",
            "name": "Fiktivt distrikt", "area_id": "", "temporary": False,
            "addresses": [], "geo_addresses": [], "address_ids": [],
            "geo_polygon": [], "in_folder": True, "map_color": "#477596",
        }
        for i in range(cards)
    ]
    for i in range(addresses):
        if i % 5:
            card_rows[i % cards]["address_ids"].append(f"fictional-a{i}")
    with store.transaction():
        for row in card_rows:
            store.put("cards", row)
        for i in range(addresses):
            store.put("geo", {
                "id": f"fictional-a{i}", "entity": "address",
                "road": f"Fiktivvej {i // 120}", "number": str(i % 120 + 1),
                "postcode": "7000", "floor": "", "door": "",
                "lat": 55.5 + (i % 300) * .00005,
                "lng": 9.5 + (i // 300) * .00005, "count": 1,
                "source": "synthetic", "label": "Kun fiktive data",
            })
        for i in range(roads):
            store.put("geo", {
                "id": f"fictional-r{i}", "entity": "road",
                "name": f"Fiktivvej {i}", "road_type": "residential",
                "points": [[9.5 + i * .00001, 55.5], [9.51 + i * .00001, 55.51]],
            })
        for i in range(buildings):
            x = 9.5 + i * .000005
            store.put("geo", {
                "id": f"fictional-b{i}", "entity": "building", "points": [
                    [x, 55.5], [x + .00005, 55.5],
                    [x + .00005, 55.50005], [x, 55.50005],
                ],
            })
        for i in range(history):
            store.put("loans", {
                "id": f"fictional-loan-{i}",
                "card_id": card_rows[i % cards]["id"],
                "assigned": "2026-01-01", "returned": "2026-02-01",
                "publisher_id": "fictional-only",
            })
    return card_rows


def execute(addresses=12000, cards=240, roads=900, buildings=2800, history=2000, runs=7):
    if not (10 <= addresses <= 100000 and 1 <= cards <= 5000 and
            0 <= roads <= 50000 and 0 <= buildings <= 50000 and
            0 <= history <= 100000 and 3 <= runs <= 40):
        raise ValueError("Invalid synthetic benchmark sizes")
    with tempfile.TemporaryDirectory(prefix="ltm-fictional-bench-") as temp:
        store = Store(temp)
        try:
            setup_start = time.perf_counter()
            fixture(store, addresses, cards, roads, buildings, history)
            setup_ms = (time.perf_counter() - setup_start) * 1000
            cold_geo = measure(
                lambda: (setattr(store, "_geo_cache", None),
                         setattr(store, "_info_cache", None), store.geo_state()), runs
            )
            warm_geo = measure(store.geo_state, runs)
            full_state = measure(store.state, runs)
            geo_payload = store.geo_state()
            state_payload = store.state()
            geo_bytes = len(json.dumps(geo_payload, ensure_ascii=False).encode("utf-8"))
            state_bytes = len(json.dumps(state_payload, ensure_ascii=False).encode("utf-8"))
            counter = 0

            def small_write_and_refresh():
                nonlocal counter
                with store.transaction():
                    card = store.require("cards", "fictional-c0")
                    card["map_color"] = "#477596" if counter % 2 else "#587596"
                    store.put("cards", card)
                counter += 1
                store.geo_state()
                store.state()

            post_save = measure(small_write_and_refresh, runs)
            assert len(store.all("geo")) == addresses + roads + buildings
            assert len(store.all("cards")) == cards
            assert len(store.all("loans")) == history
            file_bytes = sum(p.stat().st_size for p in Path(temp).glob("*.sqlite3"))
            return {
                "environment": {"python": sys.version.split()[0],
                                "platform": platform.platform(), "sqlite": sqlite3.sqlite_version},
                "dataset": {"addresses": addresses, "cards": cards, "roads": roads,
                            "buildings": buildings, "history": history,
                            "database_bytes": file_bytes,
                            "geo_json_bytes": geo_bytes, "state_json_bytes": state_bytes},
                "repetitions": runs, "fixture_insert_ms": round(setup_ms, 2),
                "cold_geo_state": cold_geo, "warm_geo_state": warm_geo,
                "full_state": full_state, "small_store_write_plus_refresh": post_save,
                "not_measured": [
                    "HTTP response time, profile authorization and concurrent writes",
                    "actual browser rendering and network latency"
                ],
            }
        finally:
            store.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--addresses", type=int, default=12000)
    parser.add_argument("--cards", type=int, default=240)
    parser.add_argument("--roads", type=int, default=900)
    parser.add_argument("--buildings", type=int, default=2800)
    parser.add_argument("--history", type=int, default=2000)
    parser.add_argument("--runs", type=int, default=7)
    print(json.dumps(execute(**vars(parser.parse_args())), ensure_ascii=False, indent=2))
