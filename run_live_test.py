#!/usr/bin/env python3
"""
Unit 9, Milestone 5: one pass of the live test against the Render service.

    python run_live_test.py --run 1
    python run_live_test.py --cold            (one cold-start trial; see below)

A pass is identical every time, so three passes are comparable:

  warm-up        1 matching request, excluded from every criterion
  phase A        10 matching requests, one after another
                 -> criterion 1 uses the first 5 (HTTP result)
                 -> criteria 2 and 5 use all 10 (their log records)
  phase B        the criterion 4 mix, in a fixed order:
                 6 matching, 2 no-match, 2 empty ({} body)
                 -> criterion 4 counts the log records for these 10

The client records what it can see (status, wall time, whether a fit card came
back). Criteria 2, 4 and 5 are scored from the server's log records, which come
from the Render log export, not from here. Each request's UTC start and end are
saved so the export can be split by pass.

Output: results/live_run<N>.json (or live_cold.json).
"""

import argparse
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import os
BASE = os.environ.get("FITFINDR_URL", "https://fitfindr-qzrp.onrender.com")
MATCH = "vintage graphic tee under $30"
NO_MATCH = "designer ballgown size XXS under $5"
TIMEOUT_S = 130  # a little over the 120 s gunicorn timeout

# criterion 4's mix, fixed order
MIX = ["match", "empty", "match", "nomatch", "match", "match",
       "empty", "match", "nomatch", "match"]


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def post(body: dict) -> dict:
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        BASE + "/ask", data=data, method="POST",
        headers={"Content-Type": "application/json"},
    )
    started = now()
    t0 = time.perf_counter()
    status, payload, failure = None, None, None
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
            status = resp.status
            payload = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        status = exc.code
        try:
            payload = json.loads(exc.read().decode())
        except Exception:  # noqa: BLE001
            payload = None
    except Exception as exc:  # noqa: BLE001 — timeouts and resets are results too
        failure = f"{type(exc).__name__}: {exc}"
    wall_ms = round((time.perf_counter() - t0) * 1000)
    return {
        "start_utc": started, "end_utc": now(), "wall_ms": wall_ms,
        "status": status, "client_failure": failure,
        "fit_card": (payload or {}).get("fit_card"),
        "error": (payload or {}).get("error"),
        "selected": ((payload or {}).get("selected_item") or {}).get("id"),
    }


def request_for(kind: str) -> tuple[str, dict]:
    if kind == "match":
        return kind, {"query": MATCH}
    if kind == "nomatch":
        return kind, {"query": NO_MATCH}
    return "empty", {}


def get_metrics() -> dict | None:
    try:
        with urllib.request.urlopen(BASE + "/metrics", timeout=30) as resp:
            return json.loads(resp.read().decode())
    except Exception:  # noqa: BLE001
        return None


def run_pass(n: int) -> None:
    out = {"run": n, "started_utc": now(), "requests": []}

    def go(phase: str, kind: str) -> None:
        kind, body = request_for(kind)
        r = post(body)
        r.update(phase=phase, kind=kind, seq=len(out["requests"]) + 1)
        out["requests"].append(r)
        print(f"  {r['seq']:>2} {phase:<7} {kind:<7} status={r['status']} "
              f"{r['wall_ms']:>6} ms  card={bool(r['fit_card'])}", flush=True)

    print(f"Pass {n}: warm-up")
    go("warmup", "match")
    out["metrics_before"] = get_metrics()
    print("phase A: 10 matching requests")
    for _ in range(10):
        go("A", "match")
    print("phase B: the criterion 4 mix")
    for kind in MIX:
        go("B", kind)
    out["ended_utc"] = now()
    out["metrics_after"] = get_metrics()

    path = Path("results") / f"live_run{n}.json"
    path.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"saved {path}")


def run_cold() -> None:
    """One request, timed by this client. Run it >= 20 minutes after the last."""
    print("cold-start trial (service should have been idle for 20+ minutes)")
    kind, body = request_for("match")
    r = post(body)
    r.update(phase="cold", kind=kind)
    print(f"  status={r['status']} {r['wall_ms']} ms card={bool(r['fit_card'])} "
          f"failure={r['client_failure']}")
    Path("results/live_cold.json").write_text(
        json.dumps(r, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=int)
    ap.add_argument("--cold", action="store_true")
    a = ap.parse_args()
    if a.cold:
        run_cold()
    elif a.run:
        run_pass(a.run)
    else:
        ap.error("give --run N or --cold")
