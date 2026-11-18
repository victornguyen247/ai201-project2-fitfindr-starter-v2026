"""Score the unit 9 live runs: client JSON (results/live_run*.json) + Render log exports."""
import json, statistics, sys
from datetime import datetime, timezone

REQUIRED = ["ts", "query", "outcome", "output", "total_ms", "steps_ms", "model_calls", "tokens"]

def parse_logs(paths):
    recs = []
    for p in paths:
        for line in open(p, encoding="utf-8"):
            i = line.find('{"event": "ask"')
            if i != -1:
                try:
                    r = json.loads(line[i:])
                except Exception:
                    continue
                recs.append(r)
    seen, out = set(), []
    for r in recs:                       # the two exports overlap; dedupe
        k = json.dumps(r, sort_keys=True)
        if k not in seen:
            seen.add(k); out.append(r)
    return sorted(out, key=lambda r: r["ts"])

def secs(s): return datetime.strptime(s[:19], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc).timestamp()

_used = set()

def match(req, recs):
    """The unassigned record for this query whose ts is closest to the request's end second."""
    end = int(secs(req["end_utc"]))
    best = None
    for i, r in enumerate(recs):
        if i in _used or r["query"] != req.get("query"):
            continue
        gap = abs(secs(r["ts"]) - end)
        if gap <= 2 and (best is None or gap < best[0]):
            best = (gap, i)
    if best is None:
        return None
    _used.add(best[1])
    return recs[best[1]]

QUERY = {"match": "vintage graphic tee under $30", "nomatch": "designer ballgown size XXS under $5"}

def score(n, recs):
    d = json.load(open(f"results/live_run{n}.json"))
    reqs = d["requests"]
    for r in reqs: r["query"] = QUERY.get(r["kind"])
    A = [r for r in reqs if r["phase"] == "A"]
    B = [r for r in reqs if r["phase"] == "B"]
    c1 = sum(1 for r in A[:5] if r["status"] == 200 and r["fit_card"] and not r["error"])
    la = [match(r, recs) for r in A]
    tot = [x["total_ms"] for x in la if x]
    c2 = (statistics.median(tot) if tot else None, max(tot) if tot else None, len(tot))
    lb = [match(r, recs) if r["kind"] != "empty" else None for r in B]
    present = sum(1 for x in lb if x)
    complete = sum(1 for x in lb if x and all(k in x and x[k] is not None for k in REQUIRED))
    c5 = sum(1 for x in la if x and x["model_calls"] == 2 and x["cache_hits"] == 0 and x["tokens"] > 0)
    c5_detail = [(x["model_calls"], x["cache_hits"], x["tokens"], x["outcome"]) if x else None for x in la]
    bad = [r["status"] for r in reqs if r["status"] != 200 and r["status"] != 400]
    return dict(run=n, c1=c1, c2=c2, c4_present=present, c4_complete=complete, c5=c5, c5_detail=c5_detail,
                non200=len(bad), statuses_b=[r["status"] for r in B])

recs = parse_logs(["host_log_run.jsonl", "host_log_cold.jsonl"])
print("log records:", len(recs))
for n in (1, 2, 3, 4):
    s = score(n, recs)
    print(json.dumps(s))
