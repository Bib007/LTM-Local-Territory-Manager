"""#97: real disposable SQLite Store benchmark; all records are fictional.

Run in candidate checkout:
 python scripts/benchmark_geo_cache_97.py --addresses 50000 --cards 180 --history 12000
Run against old develop in the same CI runner:
 python scripts/benchmark_geo_cache_97.py --app-dir /path/to/develop/distrikt/app ...

Measures Store mutation, cache read, full Store.state(), JSON and gzip separately.
It does NOT measure a live HA device, profile authorization, network or browser.
"""
import argparse
import gzip
import json
import platform
import sqlite3
import sys
import tempfile
import time
from datetime import date
from pathlib import Path
from statistics import median


def fixture(store, addresses, cards, roads, buildings, history):
    rows = [{"id": "fictional-c" + str(i), "number": str(i + 1),
             "name": "Fiktivt distrikt", "kind": "By", "temporary": True,
             "in_folder": True, "addresses": [], "geo_addresses": [],
             "address_ids": [], "geo_polygon": [], "map_color": "#477596"}
            for i in range(cards)]
    for i in range(addresses):
        if i % 5:
            rows[i % cards]["address_ids"].append("fictional-a" + str(i))
    with store.transaction():
        for row in rows:
            store.put("cards", row)
        for i in range(addresses):
            store.put("geo", {
                "id": "fictional-a" + str(i), "entity": "address",
                "road": "Fiktivvej " + str(i // 120),
                "number": str(i % 120 + 1), "postcode": "9999",
                "floor": "", "door": "", "count": 1,
                "lat": 55.5 + (i % 300) * .00005,
                "lng": 9.5 + (i // 300) * .00005,
                "label": "Kun fiktive data"})
        for i in range(roads):
            store.put("geo", {"id": "fictional-road" + str(i),
                "entity": "road", "name": "Fiktivvej " + str(i),
                "points": [[9.5 + i * .00001, 55.5], [9.51 + i * .00001, 55.51]]})
        for i in range(buildings):
            x = 9.5 + i * .000005
            store.put("geo", {"id": "fictional-building" + str(i),
                "entity": "building", "points": [[x, 55.5], [x + .00005, 55.5],
                    [x + .00005, 55.50005], [x, 55.50005]]})
        for i in range(history):
            store.put("loans", {"id": "fictional-history" + str(i),
                "card_id": rows[i % cards]["id"], "publisher_id": "fictional",
                "assigned": "2026-01-01", "cycle_start": "2026-01-01",
                "returned": "2026-02-01"})
    return rows


def bench(store, scenario, repeats, publisher):
    durations = {key: [] for key in ("sqlite_and_store_mutation_ms",
        "geo_state_read_ms", "full_state_ms", "receipt_json_ms", "receipt_gzip_ms",
        "total_ms")}
    generations = []
    reused = []
    payload = {}
    day = date.today().isoformat()
    for i in range(repeats):
        # Prepare a new active loan before timing; even the old invalidation
        # logic is given the same warm cache immediately before each sample.
        loan = None
        if scenario in ("loan_finish", "loan_finish_plus_polygon"):
            loan = store.mutate("loan.issue", {
                "card_id": "fictional-c0", "publisher_id": publisher,
                "date": day, "initial": True})["id"]
        original_cache = store.geo_state()
        generation = store.geo_generation
        t0 = time.perf_counter()
        if scenario == "card_color":
            store.mutate("card.color", {"card_id": "fictional-c0",
                "map_color": "#477596" if i % 2 else "#587596"})
        elif scenario == "loan_finish":
            store.mutate("loan.finish", {"id": loan, "date": day,
                "complete": bool(i % 2), "retain": False})
        elif scenario == "loan_finish_plus_polygon":
            # Combined Store transaction (not an HTTP loan.finish action).
            # Its additional polygon write is intentionally geo-relevant.
            with store.transaction():
                store._mutate("loan.finish", {
                    "id": loan, "date": day, "complete": bool(i % 2),
                    "retain": False})
                card = store.require("cards", "fictional-c0")
                east = 9.520 if i % 2 else 9.521
                card["geo_polygon"] = [[9.49, 55.49], [east, 55.49],
                                        [east, 55.53], [9.49, 55.53]]
                store.put("cards", card)
        else:
            raise ValueError("Unknown fictional scenario")
        t1 = time.perf_counter()
        geo = store.geo_state()
        t2 = time.perf_counter()
        state = store.state()
        t3 = time.perf_counter()
        receipt = {"ok": True, "result": {"id": "fictional-c0"},
                   "revision": store.revision,
                   "geo_changed": store.geo_generation != generation,
                   "state": state}
        wire = json.dumps(receipt, ensure_ascii=False).encode("utf8")
        t4 = time.perf_counter()
        zipped = gzip.compress(wire, compresslevel=4)
        t5 = time.perf_counter()
        stages = (t0, t1, t2, t3, t4, t5)
        for name, a, b in zip(durations, stages[:-1], stages[1:]):
            durations[name].append(round((b - a) * 1000, 3))
        durations["total_ms"].append(round((t5 - t0) * 1000, 3))
        generations.append(store.geo_generation - generation)
        reused.append(geo is original_cache)
        payload = {"receipt_json_bytes": len(wire),
                   "receipt_gzip_bytes": len(zipped),
                   "geo_address_count": len(geo["addresses"])}
    return {"scenario": scenario, "repetitions": repeats,
            "median_ms": {k: round(median(v), 3) for k, v in durations.items()},
            "samples_ms": durations,
            "geo_generation_deltas": generations, "geo_cache_reused": reused,
            "payload": payload}


def run(args):
    app_dir = Path(args.app_dir).resolve() if args.app_dir else Path(__file__).resolve().parents[1] / "distrikt" / "app"
    # Import the Store under test, not Store from this script's checkout.
    sys.path.insert(0, str(app_dir))
    from store import Store
    with tempfile.TemporaryDirectory(prefix="ltm-97-fake-sqlite-") as temp:
        store = Store(temp)
        try:
            fixture_started = time.perf_counter()
            fixture(store, args.addresses, args.cards, args.roads,
                    args.buildings, args.history)
            fixture_ms = round((time.perf_counter() - fixture_started) * 1000, 3)
            publisher = store.mutate("publisher.save", {
                "name": "Fiktiv kontakt"})["id"]
            cases = [bench(store, name, args.runs, publisher) for name in
                ("card_color", "loan_finish", "loan_finish_plus_polygon")]
            assert len(store.all("cards")) == args.cards
            assert len(store.all("geo")) == args.addresses + args.roads + args.buildings
            assert len(store.all("loans")) == args.history + args.runs * 2
            assert all(c["payload"]["geo_address_count"] == args.addresses for c in cases)
            store.close()
            # The measured cache policy must not influence durable SQLite.
            reopened = Store(temp)
            try:
                assert len(reopened.all("cards")) == args.cards
                assert len(reopened.all("loans")) == args.history + args.runs * 2
                assert len(reopened.geo_state()["addresses"]) == args.addresses
            finally:
                reopened.close()
            return {"environment": {"python": sys.version.split()[0],
                "sqlite": sqlite3.sqlite_version, "platform": platform.platform()},
                "app_dir": str(app_dir), "dataset": {
                    "addresses": args.addresses, "cards": args.cards,
                    "history": args.history, "roads": args.roads,
                    "buildings": args.buildings},
                "fixture_ms": fixture_ms, "cases": cases,
                "scope": "Real temporary SQLite Store and Python JSON/gzip; not authenticated HTTP, HA, LAN or browser"}
        finally:
            # close is safe even when the successful path already closed it.
            try:
                store.close()
            except sqlite3.ProgrammingError:
                pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--app-dir")
    parser.add_argument("--addresses", type=int, default=1000)
    parser.add_argument("--cards", type=int, default=20)
    parser.add_argument("--history", type=int, default=200)
    parser.add_argument("--roads", type=int, default=100)
    parser.add_argument("--buildings", type=int, default=200)
    parser.add_argument("--runs", type=int, default=3)
    args = parser.parse_args()
    if not (10 <= args.addresses <= 100000 and 1 <= args.cards <= 5000
            and 0 <= args.history <= 100000 and 0 <= args.roads <= 50000
            and 0 <= args.buildings <= 50000 and 3 <= args.runs <= 20):
        parser.error("Only bounded fictional fixtures are supported")
    print(json.dumps(run(args), ensure_ascii=False, indent=2))
