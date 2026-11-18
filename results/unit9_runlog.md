
---

## Unit 9 — Run Log

Target service: `https://fitfindr-qzrp.onrender.com`, deployed from `render.yaml` (Blueprint), free web service, `gunicorn serve:app --timeout 120`, cache off. Code is unchanged between runs. Each run is one pass of `run_live_test.py`: 1 warm-up request (excluded), 10 matching requests (phase A: criteria 1, 2, 5), then the criterion 4 mix of 6 matching, 2 no-match and 2 empty requests (phase B). Server-side numbers (2, 4, 5) come from the Render log export, matched to client requests by query and completion second (`score_live.py`). Raw results are in `results/live_run1-4.json`, the Render exports in `results/render_log_*.jsonl`, and the scoring output in `results/unit9_scoring.txt`.

I ran three passes. Run 3 was cut short when Render restarted the instance, so I ran a fourth pass after the cold-start trial. It was cut short the same way. I kept all four rather than pick the clean ones. Runs 1 and 2 are the only ones that completed.

| Criterion | Target | Run 1 | Run 2 | Run 3 | Run 4 | Verdict |
|---|---|---|---|---|---|---|
| 1. Warm hosted service completes a matching query | 5 of 5 | 5/5 | 5/5 | 5/5 | 3/5 | MISSED |
| 2. Warm matching run time (log `total_ms`) | median ≤ 15,000 ms, max ≤ 60,000 ms over 10 runs | 8,563 / 15,347 ms (n=10) | 8,031 / 9,449 ms (n=9) | 7,098 / 12,287 ms (n=8) | 6,111 / 6,658 ms (n=3) | MET on every measured run, but only run 1 had all 10 |
| 3. Wake from sleep within 90 s | ≤ 90 s, 1 trial | not run | not run | not run | 41.1 s (single trial) | MET |
| 4. Every request leaves a complete record, failures included | 10 of 10 | 0/10 (8 records, none with `output`) | 0/10 (8 records, none with `output`) | 0/10 (all 10 requests got 502, no records) | 0/10 (same, 502) | MISSED |
| 5. Cost counters are real | ≥ 9 of 10 runs: `model_calls`=2, `cache_hits`=0, `tokens`>0 | 9/10 | 9/10 | 8/10 | 3/10 | MISSED |

Cell notes:
- **Criterion 1, Run 4:** the first three phase A requests returned 200, then Render restarted the instance and the fourth and fifth got 502.
- **Criterion 2:** the medians and maxima are over the log records that exist. Run 2 is missing one record: the request that took 24,369 ms by the client's clock has no `"event": "ask"` line in the Render export, although the lines before and after it are there. The client wall time of 24.4 s is still under the 60 s limit.
- **Criterion 4:** the 8 records in runs 1 and 2 are the 6 matching and 2 no-match requests. The 2 empty requests got HTTP 400 and no record at all. None of the 8 has an `output` field.
- **Criterion 5, Run 1:** the one miss is a Gemini `503 UNAVAILABLE` on the first model call: `model_calls` was 1 and `tokens` was 0. Runs 3 and 4 lost their other runs to the restart. Every record that did reach the log shows `model_calls` 2, `cache_hits` 0 and `tokens` above 0.

**Restarts.** Render stopped and restarted the instance twice during testing, both times with SIGTERM (not a kill) and no explanation in the Events tab:

```
2026-11-18T21:48:10Z [57] [INFO] Handling signal: term
2026-11-18T21:48:16Z ==> Instance srv-dbv1lnff3r2c73eq0tp0-f4slr restarted
2026-11-18T22:12:14Z [39] [INFO] Handling signal: term
2026-11-18T22:12:19Z ==> Instance srv-dbv1lnff3r2c73eq0tp0-vzz4m restarted
```

Requests that arrived while the instance was down got Render's 502 page. They never reached the app, so they left no record. The first life lasted about 8.5 minutes and about 105 requests, and the second about 1 minute and 5 requests, so it is not a fixed request count. I don't know the cause. It is not an out-of-memory kill, because that would not log a graceful SIGTERM.

### Real output, by criterion

**Criterion 1** (client, `run_live_test.py::post`, from `results/live_passes_console.txt` and `results/live_pass4_console.txt`). Run 1, first five phase A requests, then run 4:

```
   2 A       match   status=200   7215 ms  card=True
   3 A       match   status=200  10817 ms  card=True
   4 A       match   status=200  12935 ms  card=True
   5 A       match   status=200   7496 ms  card=True
   6 A       match   status=200   6487 ms  card=True
Pass 4: warm-up
   1 warmup  match   status=200   6602 ms  card=True
   2 A       match   status=200   6959 ms  card=True
   3 A       match   status=200   5825 ms  card=True
   4 A       match   status=200   6459 ms  card=True
   5 A       match   status=502    398 ms  card=False
   6 A       match   status=502    267 ms  card=False
```

**Criterion 2** (`serve.py::ask`, written by `_log`; Render export `results/render_log_runs1-3.jsonl`, run 1):

```
{"event": "ask", "ts": "2026-11-18T21:41:39Z", "query": "vintage graphic tee under $30", "outcome": "found", "error_type": null, "total_ms": 10512, "steps_ms": {"search": 3850, "outfit": 1440, "fit_card": 5222}, "model_calls": 2, "cache_hits": 0, "tokens": 872}
{"event": "ask", "ts": "2026-11-18T21:41:52Z", "query": "vintage graphic tee under $30", "outcome": "found", "error_type": null, "total_ms": 12759, "steps_ms": {"search": 3937, "outfit": 6481, "fit_card": 2340}, "model_calls": 2, "cache_hits": 0, "tokens": 826}
{"event": "ask", "ts": "2026-11-18T21:42:00Z", "query": "vintage graphic tee under $30", "outcome": "found", "error_type": null, "total_ms": 7049, "steps_ms": {"search": 4289, "outfit": 1537, "fit_card": 1222}, "model_calls": 2, "cache_hits": 0, "tokens": 831}
{"event": "ask", "ts": "2026-11-18T21:42:06Z", "query": "vintage graphic tee under $30", "outcome": "found", "error_type": null, "total_ms": 6046, "steps_ms": {"search": 4066, "outfit": 1313, "fit_card": 667}, "model_calls": 2, "cache_hits": 0, "tokens": 835}
```

**Criterion 3** (`results/live_cold.json`, from `run_live_test.py::run_cold`; the sleep is in `results/render_log_cold_run4.jsonl`). The service had its last request at 21:48 and Render stopped it at 22:03:15. The timed request started at 22:11:08:

```
2026-11-18T22:03:10Z 10.238.26.184 - - "GET /health HTTP/1.1" 200 16 "-" "Render/1.0"
2026-11-18T22:03:15Z [38] [INFO] Handling signal: term
2026-11-18T22:03:15Z [38] [INFO] Shutting down: Master
{"start_utc": "2026-11-18T22:11:08.026493Z", "end_utc": "2026-11-18T22:11:49.116658Z", "wall_ms": 41090, "status": 200, "fit_card": "Absolute peak 2000s grunge energy with this bootleg tour tee. Snagged it on depop for $24 ..."}
{"event": "ask", "ts": "2026-11-18T22:11:49Z", "query": "vintage graphic tee under $30", "outcome": "found", "error_type": null, "total_ms": 18704, "steps_ms": {"search": 9240, "outfit": 8598, "fit_card": 864}, "model_calls": 2, "cache_hits": 0, "tokens": 823}
```

Render's own health checks every 5 seconds did not keep the service awake. The client waited 41.1 s but the log's `total_ms` is 18.7 s, so about 22 s went to starting the instance before the app saw the request.

**Criterion 4** (`serve.py::ask`). An empty request, run 1: the access line is there and no `"event": "ask"` line follows it. The next record in the log is for a later request:

```
2026-11-18T21:43:08Z 127.0.0.1 - - [18/Nov/2026:21:43:08 +0000] "POST /ask HTTP/1.1" 400 96 "-" "Python-urllib/3.13"
{"event": "ask", "ts": "2026-11-18T21:43:21Z", "query": "designer ballgown size XXS under $5", "outcome": "no_results", "error_type": null, "total_ms": 3998, "steps_ms": {"search": 3998}, "model_calls": 0, "cache_hits": 0, "tokens": 0}
```

That second record also shows the other gap: it has no `output` field.

Run 3 phase B, client side (`run_live_test.py::post`): every request got a 502 and no record exists for any of them:

```
  12 B       match   status=502    302 ms  card=False
  13 B       empty   status=502    447 ms  card=False
  14 B       match   status=502    151 ms  card=False
  15 B       nomatch status=502    503 ms  card=False
```

**Criterion 5** (`serve.py::ask`, counters read from `generate.py::call_count` and `token_counts`). Run 1, the one request that missed. A model failure is logged as `outcome: model_unavailable` with `error_type: null`, and the record has no failure message:

```
{"event": "ask", "ts": "2026-11-18T21:42:28Z", "query": "vintage graphic tee under $30", "outcome": "model_unavailable", "error_type": null, "total_ms": 4271, "steps_ms": {"search": 4139, "outfit": 131}, "model_calls": 1, "cache_hits": 0, "tokens": 0}
```

### Earlier service, kept for comparison

My first deployment was created by hand in the dashboard, so `AI201_CACHE` was never set and the cache stayed on. I measured it before I deleted it. After 59 requests `/metrics` showed 2 model calls and 102 cache hits, and matching runs took about 5 s, the same as the no-match query. Criterion 5 would have been MISSED on that service, and every latency number would have been wrong. Files: `results/old_service_run1-3.json`.
