

---

## Unit 9 — Verdicts and Diagnoses

A criterion is MET only if every run held the target, so one run below it is a MISSED. No criterion was revised: all five were measurable as written, and the targets stay where I set them.

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 | Warm service completes a matching query | 5 of 5 | MISSED | 5, 5, 5 and 3 of 5 across the four before-runs. Run 4 fell to 3 because Render restarted the instance. |
| 2 | Warm matching run time | median ≤ 15,000 ms, max ≤ 60,000 ms | MET | Every measured run, before and after, is inside both limits. Across all eight runs the worst median was 8,563 ms and the worst max 21,940 ms. Only run 1 had all 10 records (runs 2 to 4 lost records to a log gap or a restart), so the target held on all the data I have, not on a full 10 every time. |
| 3 | Wake from sleep | ≤ 90 s, 1 trial | MET | 41.1 s before, 46.4 s after. The service really did go to sleep (see the logs below), so the trial was a real cold start. |
| 4 | Every request leaves a complete record, failures included | 10 of 10 | MISSED | 0 of 10 in all four before-runs. |
| 5 | Cost counters are real | ≥ 9 of 10 runs | MISSED | 9, 9, 8 and 3 of 10. Run 3 and 4 fell below 9 because of the restarts. |

**Diagnoses**

*Criterion 4 (code).* The stage is the request handler, `serve.py::ask`, and there were two mechanisms in it:
1. A request with no `query` returned HTTP 400 on line one of the handler, before any logging ran, so the two empty requests in every mix left no record.
2. The record `_log` wrote had no `output` field, so even the eight requests that were logged were missing a required field.

That is why the score was 0 of 10 and not 8 of 10: the criterion asks for a complete record. The tool and the model worked. The logging layer didn't write what the criterion needs.

*Criteria 1 and 5, and the short counts in criterion 2: one problem with several symptoms.* The stage is the hosting platform, not any of the four stages of my agent. Render stopped and restarted the instance in the middle of my test runs, three times in the before and after runs combined (21:48:10, 22:12:14 and 22:38:27 UTC). Each time gunicorn logged `Handling signal: term` and Render logged `Instance ... restarted`. For about 15 to 20 seconds in the two restarts I can time from the logs, the proxy answered every request with a 502 itself, so those requests never reached `serve.py` and left no record. That explains every short or failing run:
- Run 3 (before) lost 12 requests, and run 4 (before) lost 17, so criterion 1 fell to 3 of 5 and criterion 5 to 3 of 10.
- In every record that did reach the log, `model_calls` was 2, `cache_hits` was 0 and `tokens` was above 0, so the cost counters themselves are correct. The cost criterion missed because the runs were missing, not because the counters were wrong.

I don't know why Render restarts the instance. It isn't an out-of-memory kill, because that would log a kill and not a graceful SIGTERM, and the Events tab showed nothing for the 21:47 restart. The restarts don't follow a fixed uptime or request count: the first lasted about 8.5 minutes and about 105 requests, the second about 1 minute and 5 requests, the third 2.7 minutes after a deploy.

*Pattern.* Criteria 1 and 5 and the short counts in criterion 2 all trace to one stage, the restart. Criterion 4 in the before-runs traces to a different stage, my request handler, and it was the only miss that was mine to fix. The restart is the larger of the two problems, and this code can't prevent it.

## Unit 9 — The Improvement

**What I changed:** one change to the logging layer in `serve.py` (commit `878ce3c`). Every `/ask` outcome now writes the same record through one helper, `_ask_record`. The record has a new `output` field (the fit card, or the error message when there is no card). A request with no `query` is now logged as `outcome: rejected_input` with `error_type: missing_query` before the 400 is returned. A model failure is logged with `error_type: ModelUnavailable` and its message. The service also writes one `{"event": "boot"}` line at startup, so a restart is visible in the log. `agent.py`, the tools, the prompts and `render.yaml` are unchanged.

**Which failure it was meant to fix:** criterion 4, the handler defect above. It was not meant to fix criteria 1 and 5, because their misses come from the restarts, which the change can't stop. The boot line was added only so that restarts would show up in the log.

### Run Log — After

| Criterion | Target | Run 1 | Run 2 | Run 3 | Run 4 | Verdict |
|---|---|---|---|---|---|---|
| 1. Warm service completes a matching query | 5 of 5 | 5/5 | 0/5 | 5/5 | 5/5 | MISSED |
| 2. Warm matching run time (log `total_ms`) | median ≤ 15,000 ms, max ≤ 60,000 ms | 6,441 / 17,768 ms (n=10) | no records (all 502) | 5,982 / 21,940 ms (n=10) | 7,339 / 14,101 ms (n=10) | MET |
| 3. Wake from sleep within 90 s | ≤ 90 s, 1 trial | not run | not run | not run | 46.4 s (single trial) | MET |
| 4. Every request leaves a complete record, failures included | 10 of 10 | 0/10 (all 10 got 502) | 0/10 (all 10 got 502) | 10/10 | 10/10 | MISSED |
| 5. Cost counters are real | ≥ 9 of 10 runs | 10/10 | 0/10 (all 502) | 10/10 | 10/10 | MISSED |

Run 1 and run 2 were hit by the restart at 22:38:27 UTC. Run 1's phase A finished before it, and its phase B returned 502 for all 10 requests. Run 2 ran entirely inside it, 21 requests in 11 seconds, all 502. The warm-up of run 3 also returned 502 and is excluded from every criterion.

### Before and after, side by side

| Criterion | Before: Run 1 | Run 2 | Run 3 | Run 4 | After: Run 1 | Run 2 | Run 3 | Run 4 |
|---|---|---|---|---|---|---|---|---|
| 1 | 5/5 | 5/5 | 5/5 | 3/5 | 5/5 | 0/5 | 5/5 | 5/5 |
| 2 (median / max ms) | 8,563 / 15,347 | 8,031 / 9,449 | 7,098 / 12,287 | 6,111 / 6,658 | 6,441 / 17,768 | none | 5,982 / 21,940 | 7,339 / 14,101 |
| 3 | not run | not run | not run | 41.1 s | not run | not run | not run | 46.4 s |
| 4 | 0/10 | 0/10 | 0/10 | 0/10 | 0/10 | 0/10 | 10/10 | 10/10 |
| 5 | 9/10 | 9/10 | 8/10 | 3/10 | 10/10 | 0/10 | 10/10 | 10/10 |

The fair comparison for criterion 4 is the runs where the service stayed up for the whole request mix. Before: runs 1 and 2 had 8 of the 10 requests logged and none complete, so 0 of 10. After: runs 3 and 4 had all 10 requests logged and complete, so 10 of 10.

### Real output, after

**Criterion 4** (`serve.py::ask` through `_ask_record`; `results/render_log_after_runs1-3.jsonl`, run 3). An empty request is now logged, and a no-match request now records what it told the user:

```
{"event": "ask", "ts": "2026-11-18T22:40:19Z", "query": "", "outcome": "rejected_input", "error_type": "missing_query", "output": "Send JSON with a 'query' field, e.g. {\"query\": \"vintage graphic tee under $30\"}", "total_ms": 0, "steps_ms": {}, "model_calls": 0, "cache_hits": 0, "tokens": 0}
{"event": "ask", "ts": "2026-11-18T22:40:30Z", "query": "designer ballgown size XXS under $5", "outcome": "no_results", "error_type": null, "output": "Nothing matched your search. You could raise the price limit above $5, drop the size filter (size XXS), or try fewer or different keywords than \"designer ballgown\".", "total_ms": 4408, "steps_ms": {"search": 4408}, "model_calls": 0, "cache_hits": 0, "tokens": 0}
```

**The restart** (`results/render_log_after_runs1-3.jsonl`). Render's SIGTERM, then the boot record the change added:

```
2026-11-18T22:38:27Z [57] [INFO] Handling signal: term
2026-11-18T22:38:31Z ==> Instance srv-dbv1lnff3r2c73eq0tp0-kk7cz restarted
2026-11-18T22:38:36Z ==> Running 'gunicorn serve:app --timeout 120'
2026-11-18T22:38:40Z {"event": "boot", "ts": "2026-11-18T22:38:40Z", "pid": 39}
```

**Criterion 3** (`results/live_after_cold.json`, `run_live_test.py::run_cold`; `results/render_log_after_cold_run4.jsonl`). The service stopped at 22:56:05, 15 minutes after the last request at 22:41:04, and the timed request started at 23:03:21:

```
2026-11-18T22:56:05Z [39] [INFO] Handling signal: term
2026-11-18T22:56:07Z [39] [INFO] Shutting down: Master
2026-11-18T23:03:40Z [39] [INFO] Starting gunicorn 23.0.0
{"start_utc": "2026-11-18T23:03:21.053625Z", "end_utc": "2026-11-18T23:04:07.418596Z", "wall_ms": 46365, "status": 200, ...}
```

### Did it help

**For the failure it was aimed at, yes. For the verdicts, no.** On the runs where the service stayed up, criterion 4 went from 0 of 10 to 10 of 10 twice, and the two empty requests in each mix now leave a record with an error type and message. But criterion 4 is still MISSED overall, because runs 1 and 2 of the after-set hit a Render restart, and criteria 1 and 5 are still MISSED for the same reason. The change did not make any of them worse. Latency is about the same before and after (medians 6.0 to 8.6 s), as expected for a change that only touches logging.

One thing did not work as intended. The boot record appeared in the log for the 22:38 restart but I could not find one for the wake at 23:03:40, even though the gunicorn lines around it are in the export. I don't know whether the line was dropped by Render's log stream (another record of mine went missing from an earlier export the same way) or never written. So the log can make a restart visible, but I can't yet say it always will.

## Unit 9 — What's Still Broken

- **Render restarts the instance mid-use (criteria 1, 5, and the 502s in 2 and 4).** I don't know why, so I can't fix it from the code. Things I would try, in order: ask whether a paid plan restarts less, add a client retry on 502 with a short wait, and capture the instance's memory and event history at the moment of a restart. I stopped here because the cause isn't visible from inside the app, and the unit's time went to the testing.
- **A 502 leaves no record on the server.** Requests that arrive while the instance is down never reach `serve.py`, so criterion 4 can't be met for them from inside the app. Only a client-side or proxy-side log can see them, and I only have the client-side one in `run_live_test.py`.
- **Missing log lines.** One 24-second request in the before-run 2 has no record in the export although the lines around it are there, and one boot line is missing. The app prints with a flush, so I suspect Render's log stream drops lines, but I haven't shown it.
- **A model error is logged as an outcome.** `outcome: model_unavailable` carries the text of the failure now, but the record doesn't say whether it was a 503 or a bad key, only the message.
- **Cold start is a single trial** in the before-set and one in the after-set (41.1 s and 46.4 s). Both are inside 90 s, but two trials is not a distribution.
