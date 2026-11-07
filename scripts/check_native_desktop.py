#!/usr/bin/env python3
"""Isolated native-bundle smoke test. Never reads the user's LTM data."""
import argparse
import json
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path


def request(base, url, token=None, body=None):
    headers = {}
    if token:
        headers["X-Distrikt-Token"] = token
    if body is not None:
        headers["Content-Type"] = "application/json"
    payload = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(base + url, data=payload, headers=headers)
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(req, timeout=8) as response:
        return json.load(response)


def check(executable):
    executable = Path(executable).resolve()
    assert executable.is_file(), str(executable)
    with tempfile.TemporaryDirectory(prefix="ltm-native-fake-") as folder:
        data = Path(folder) / "fictional"
        def execute(*args):
            return subprocess.run([str(executable), *args], capture_output=True, timeout=50)
        def launch():
            result = execute("--data-dir", str(data), "--no-browser")
            assert result.returncode == 0, result.stderr[:1000]
            path = data / "run.json"
            for _ in range(100):
                if path.is_file():
                    try:
                        return json.loads(path.read_text())
                    except (ValueError, OSError):
                        pass
                time.sleep(.1)
            raise AssertionError("Native LTM never started")
        info = None
        try:
            info = launch()
            assert info["url"].startswith("http://127.0.0.1:")
            assert request(info["url"], "/api/ping")["app"] == "Distrikt"
            saved = request(info["url"], "/api/mutate", info["token"], {
                "action": "card.save", "data": {"number": "990", "temporary": True}
            })
            assert saved.get("result", {}).get("id"), saved
            # The same executable must also support the isolated PDF worker.
            worker = execute("--ltm-read-s13")
            assert worker.returncode == 0, worker.stderr[:1000]
            assert "error" in json.loads(worker.stdout), worker.stdout[:500]
            execute("--data-dir", str(data), "--stop")
            for _ in range(100):
                if not (data / "run.json").exists():
                    break
                time.sleep(.1)
            assert not (data / "run.json").exists(), "Server did not stop"
            info = launch()
            state = request(info["url"], "/api/state", info["token"])
            assert any(card["number"] == "990" for card in state["cards"]), "Existing card lost on restart"
            print("PASS: native offline launch, loopback, isolated PDF worker, stop and preserved fictional data")
        finally:
            if info is not None:
                execute("--data-dir", str(data), "--stop")
            # On Windows run.json is removed just before the server releases its
            # app.lock file. Allow the child to exit before deleting test data.
            lock = data / "app.lock"
            for _ in range(100):
                try:
                    lock.unlink(missing_ok=True)
                    break
                except PermissionError:
                    time.sleep(.1)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--executable", required=True)
    check(p.parse_args().executable)
