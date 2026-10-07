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
