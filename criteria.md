# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:**
I picked 4 of 5 and not 5 of 5 because `search_listings` is a plain keyword
match with no synonyms, so a phrasing like "t-shirt" can miss a listing titled
"tee" and return nothing even though a human would call it a match. Two of the
three tools also call a model, which can fail or time out on any given try.
Allowing one miss in five covers those two causes without letting the happy
path be unreliable.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:**
5 of 5 because this path has no model in it. `search_listings` returns an
empty list for a query like "designer ballgown size XXS under $5", and the
branch in `run_agent` is a plain `if not results` check, so the outcome is the
same every time. If it fails even once, the branch itself is wrong, not unlucky.
The message must tell the user what to change (loosen the price, drop the size,
use other keywords). A bare "No results" does not count.

---

## 3. Something about state

In 5 of 5 runs of a matching query, the `id` of the item that reaches
`suggest_outfit` equals `session["selected_item"]["id"]`, which equals
`search_results[0]["id"]`, and the item that reaches `create_fit_card` has that
same `id`. I check it by wrapping the two tools to record the `id` they receive
and comparing the three values after each run. The fit card must also name the
selected item's title or price, not some other listing's.

**Why this target:**
5 of 5 because passing state between tools is ordinary code with no model
choosing anything. The loop either reads the item back out of the session or it
doesn't, so a single mismatch means a bug such as a stale variable or
`search_results[1]` used by mistake. A state bug looks like a bad outfit or
caption, so I compare ids directly instead of reading the output and guessing.

---

## 4. Something about the fit card

For 5 different items, at least 4 of the 5 fit cards each (a) are 2 to 4
sentences long, (b) contain the item's price (for example "$24"), and (c)
contain its platform name (depop, thredUp or poshmark). Across the 5 cards, no
two share the same first sentence.

**Why this target:**
The wording will vary, since the card comes from a model, so I score what has
to be true of every card instead of exact text. The 4 of 5 allows for the
sentence count, because the model sometimes writes a fifth sentence or a very
short one, and a splitter that counts on periods can be off by one. The
distinct-opening rule has no slack because a template-like opener on every card
is the failure I'd dislike most, and it points at `CACHE_ENABLED` or
`TEMPERATURE` in `config.py`.

> **Revised in unit 4:** For one item (`"y2k baby tee under $20"`, which
> returns `lst_002`, $18, depop), run 5 times, at least 4 of the 5 fit cards
> each (a) are 2 to 4 sentences long, (b) contain the price "$18", and (c)
> contain the platform name "depop". Across the 5 cards, no two share the same
> first sentence.
>
> **Why revised:** the original used 5 different items, which meant 5 queries
> and 25 runs. Running the same item five times is what the 5 tries already
> do, and it is a stricter test of the distinct-opening rule, because the
> input is identical and only the model's variation can make the openings
> differ. The 4-of-5 target and the distinct-first-sentence rule are unchanged.

---

## 5. Your choice

For 5 queries that each include a `max_price` and a `size`, every listing in
`search_results` has `price <= max_price` and a size that matches the request
under the Tool Inventory rule, in 5 of 5 queries with zero violating listings.
At least one of the 5 queries asks for a single-letter size ("S" or "L") so the
substring trap is exercised: no `US 9` shoe and no `XL` item may come back for
a request for `S` or `L`.

**Why this target:**
5 of 5 and zero violations because filtering is deterministic code. One wrong
listing is a bug, not variation, and a price ceiling the user typed is a hard
limit. I chose this one because `"s" in "us 9"` is true, so a naive size test
returns shoes for a small top and the search looks broken even though the
keyword scoring is fine. A target I could miss is the point, and this is where
my first draft is most likely to slip.

> **Revised in unit 4:** For the query `"vintage size L under $45"`, run 5
> times, every listing in `search_results` has `price <= 45` and a size that
> matches `L` as a whole token (`L`, `M/L`, `L/XL`), with zero violating
> listings in 5 of 5 tries. No `XL` item and no `US` shoe may come back.
>
> **Why revised:** the original needed 5 different queries, which means 5
> separate agent runs per try and 25 model-backed runs for one criterion. One
> query that returns several listings and uses a single-letter size still
> exercises the substring trap, and the 5 tries match the "5 of 5" scoring of
> every other criterion. The target (5 of 5, zero violations) is unchanged.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->

---
---

# Unit 9 criteria — Deploy and instrument

The five criteria above are the ones from units 3 and 4 and are left exactly as
they were. These five are for the extension: FitFindr running on Render
(`https://ai201-fitfindr-z60z.onrender.com`) with a structured log and a
`/metrics` route. All five are about the extension, and number 4 is about the
bad paths. They were written before any measurement of the deployed service.

**Words used below.** *Warm* means the service has answered a request in the
last 10 minutes. *Matching query* means `vintage graphic tee under $30`.
*No-match query* means `designer ballgown size XXS under $5`. *Empty request*
means `POST /ask` with the body `{}`. *Log record* means one JSON line with
`"event": "ask"`.

---

## 1. The hosted service completes a matching query

Send a matching query to `POST /ask` on the Render URL 5 times in a row, with the
service already warm. In 5 of 5 tries the response is HTTP 200, `fit_card` is a
non-empty string, and `error` is null.

**Why this target:**
5 of 5, not the 4 of 5 I allowed for the same query on my laptop. That allowance
was for model failures, and `generate.py` already retries up to
`MAX_RETRIES = 5` times and paces itself to 15 requests a minute, so five
sequential runs (ten model calls) stay under the limit. If a warm run still
fails, the cause is the deployment: gunicorn's worker killed at the timeout, the
512 MB instance running out of memory when the MCP search starts its second
Python process, or a missing `GEMINI_API_KEY`. Those are exactly the things this
extension introduced, so one miss is a finding and not noise. The first request
after a sleep is excluded here and has its own criterion (3).

---

## 2. A warm matching run finishes in a bounded time

Across 10 warm runs of the matching query, the median `total_ms` in the log
records is at most 15,000 and no run is over 60,000.

**Why this target:**
On my laptop one matching run with a real model call took about 8,100 ms, of
which the MCP search was 700 to 2,200 ms (a new Python process per search) and
the caption call was most of the rest. A run now makes two model calls and runs
on a free-tier CPU, so 15,000 ms is roughly twice what I saw locally: tight
enough that a stuck rate-limit wait shows up, loose enough that ordinary model
latency does not. The 60,000 ms ceiling is half of the 120 s gunicorn timeout in
`render.yaml`. A run past that is close to being killed, and a user has long
given up by then. I use the median and a maximum because a single slow Gemini
call should not fail the median, but nothing should come near the timeout.

---

## 3. The service wakes from sleep within 90 seconds

After the service has been idle for at least 20 minutes (Render's free tier
sleeps after about 15), the first matching-query request, timed by the client's
own stopwatch, returns HTTP 200 with a non-empty `fit_card` in at most 90
seconds.

**Why this target:**
`RUNNING.md` says a wake-up takes "around a minute", so 90 seconds allows about
half as long again for the model call that follows the wake-up. I measure it
from the client because the server's own `total_ms` cannot include time before
the app was running. It is a single trial because each one costs at least 20
minutes of waiting, and the number I report is the one measured value, not an
average. Past 90 seconds a browser or `curl` with a default timeout starts to
fail, and a reviewer opening the link would conclude the app is broken.

---

## 4. Every request leaves a complete record, failures included

Send 10 requests to the service in one sitting: 6 matching queries, 2 no-match
queries and 2 empty requests. Afterwards the log (the Render Logs tab, searched
for `"event": "ask"`) holds exactly 10 records for them: 10 of 10, with none
missing. Every one of the 10 has a value for each of `ts`, `query`, `outcome`,
`output` (the fit card text, or the error message), `total_ms`, `steps_ms`,
`model_calls` and `tokens`. The 2 empty requests have `outcome` set to a
rejected-input value, and the 2 no-match queries have `outcome` `no_results`.

**Why this target:**
10 of 10 with no slack, because the cost of being wrong here is invisible: a
request that leaves no record looks the same as a request that never happened,
and I would never find it while diagnosing in Milestone 5. I put the two empty
requests in on purpose. In `serve.py` as it stands, a missing `query` returns
400 before `run_agent` is reached and before any log line is written, so I
expect to miss this target at first and the failure to be the useful part. The
two no-match queries cover the second bad path, which is a 200 response that
still carries an error, and which a status-code check alone would call a
success. The field list is the one the run-log needs later: input, output,
duration, and the per-step numbers that say where the time went.

---

## 5. The logged cost counters are real, not zeros

For 10 matching-query runs made with the cache off, at least 9 of 10 log records
show `model_calls` equal to 2, `cache_hits` equal to 0, and `tokens` greater
than 0.

**Why this target:**
This protects the cost number I will report. A matching run makes exactly two
model calls (`suggest_outfit` and `create_fit_card`), so `model_calls` should be
2. `generate.py` counts every attempt, so a retry after a rate-limit response
makes it 3, which is why I allow one run in ten to differ and not zero. The
failure I most expect is the cache: `render.yaml` sets `AI201_CACHE=0`, but if
that variable is missing or not read, repeated queries come back from cache with
`model_calls` 0 and `tokens` 0, and a cost average taken from those logs would
look like a very cheap system when it is not. A looser target (say 5 of 10)
would let a half-cached run through. A stricter one (10 of 10) would fail on a
single legitimate retry.
