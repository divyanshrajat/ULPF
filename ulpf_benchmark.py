#!/usr/bin/env python3
"""ULPF latency / throughput benchmark (standard library only).

Sends single events to a ULPF HTTP endpoint (for example POST /api/v1/convert)
and reports throughput and latency percentiles.

Example:
  python ulpf_benchmark.py --url http://127.0.0.1:8000/api/v1/convert \
      --token YOUR_API_KEY --events sample_events.txt \
      --body-template '{"payload": "{{EVENT}}"}' --n 2000 --warmup 100 --concurrency 4

The body template must match the OpenAPI schema of your running instance
(see http://127.0.0.1:8000/docs). {{EVENT}} is replaced by one raw event,
JSON-escaped so it can sit inside a quoted string.
"""
import argparse, json, platform, statistics, sys, time, urllib.request, urllib.error
from concurrent.futures import ThreadPoolExecutor


def load_events(path):
    with open(path, encoding="utf-8", errors="replace") as f:
        ev = [ln.rstrip("\n") for ln in f if ln.strip()]
    if not ev:
        sys.exit("events file is empty")
    return ev


def make_body(template, event):
    return template.replace("{{EVENT}}", json.dumps(event)[1:-1]).encode("utf-8")


def one_request(url, token, body, timeout):
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            r.read()
            ok = 200 <= r.status < 300
    except urllib.error.HTTPError as e:
        ok = False
        e.read()
    except Exception:
        ok = False
    return time.perf_counter() - t0, ok


def pct(sorted_vals, p):
    if not sorted_vals:
        return float("nan")
    k = min(len(sorted_vals) - 1, max(0, int(round(p / 100.0 * len(sorted_vals) + 0.5)) - 1))
    return sorted_vals[k]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--url", required=True)
    ap.add_argument("--token", default="")
    ap.add_argument("--events", required=True, help="text file, one raw event per line")
    ap.add_argument("--body-template", default='{"payload": "{{EVENT}}"}')
    ap.add_argument("--n", type=int, default=1000, help="measured requests")
    ap.add_argument("--warmup", type=int, default=100, help="discarded requests")
    ap.add_argument("--concurrency", type=int, default=1)
    ap.add_argument("--timeout", type=float, default=30.0)
    ap.add_argument("--out", default="", help="write JSON summary to this file")
    a = ap.parse_args()

    events = load_events(a.events)
    bodies = [make_body(a.body_template, e) for e in events]
    total = a.warmup + a.n
    seq = [bodies[i % len(bodies)] for i in range(total)]

    print(f"Warm-up: {a.warmup} requests ...", flush=True)
    with ThreadPoolExecutor(max_workers=a.concurrency) as ex:
        list(ex.map(lambda b: one_request(a.url, a.token, b, a.timeout), seq[: a.warmup]))

    print(f"Measuring: {a.n} requests, concurrency {a.concurrency} ...", flush=True)
    t_start = time.perf_counter()
    with ThreadPoolExecutor(max_workers=a.concurrency) as ex:
        res = list(ex.map(lambda b: one_request(a.url, a.token, b, a.timeout), seq[a.warmup:]))
    wall = time.perf_counter() - t_start

    lat = sorted(r[0] * 1000.0 for r in res)
    errors = sum(1 for r in res if not r[1])
    summary = {
        "url": a.url, "requests": a.n, "concurrency": a.concurrency, "errors": errors,
        "error_rate_pct": round(100.0 * errors / max(1, a.n), 2),
        "wall_seconds": round(wall, 3), "throughput_events_per_s": round(a.n / wall, 2),
        "latency_ms": {"mean": round(statistics.fmean(lat), 2), "p50": round(pct(lat, 50), 2),
                       "p95": round(pct(lat, 95), 2), "p99": round(pct(lat, 99), 2),
                       "min": round(lat[0], 2), "max": round(lat[-1], 2)},
        "environment": {"python": platform.python_version(), "os": platform.platform(),
                        "machine": platform.machine(), "processor": platform.processor()},
    }
    print(json.dumps(summary, indent=2))
    print("\nRecord alongside the result: CPU model and cores, RAM, queue backend, database, "
          "number of workers, mock or real LLM mode, and whether uvicorn --reload was on.")
    if a.out:
        with open(a.out, "w") as f:
            json.dump(summary, f, indent=2)


if __name__ == "__main__":
    main()
