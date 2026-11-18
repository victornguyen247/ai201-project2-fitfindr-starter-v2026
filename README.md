# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

You type what you want in plain language, for example `vintage graphic tee under $30, size M`. FitFindr searches 40 mock thrift listings, picks the best match, and suggests one or two outfits that combine it with pieces from your wardrobe. It then writes a short social-media caption (a fit card) about the find. If nothing matches, it stops and tells you what to change, such as raising the price limit, dropping the size, or using different keywords, instead of making up an outfit.



---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Searches the 40 mock listings for items whose text matches the user's keywords, optionally narrowed by size and a price ceiling, and ranks them best match first. It does not call the model.
- **Inputs:** `description` (str) — keywords such as "vintage graphic tee"; `size` (str or None) — a size to match, None skips size filtering; `max_price` (float or None) — inclusive ceiling, None skips price filtering.
  - *Size match rule:* compare case-insensitively after deleting any parenthetical (so "XL (oversized)" becomes "XL"), splitting on `/` ("S/M" becomes "S" and "M"), and splitting on whitespace ("W30 L30" becomes "W30" and "L30"). A listing matches when the requested size equals one of those whole tokens. "M" matches "M", "S/M" and "M/L"; "S" matches "S" and "S/M" but never "US 9" or "XL"; "L" matches "L", "L/XL" and "W30 L30" but never "XL".
  - *Score:* the number of distinct lowercase words in `description` that appear as whole words in a listing's title, description, category, style_tags, colors and brand. Listings scoring 0 are dropped. A word is a run of letters and digits, lowercased, with filler words (a, the, under, size, looking, and so on) ignored. Ties are broken by how many keywords appear in the title, then by order in the data file.
- **Returns:** A `list[dict]` of at most `config.SEARCH_RESULT_LIMIT` (10) listing dicts, highest score first. Each dict has `id` (str), `title` (str), `description` (str), `category` (str: tops, bottoms, outerwear, shoes or accessories), `style_tags` (list[str]), `size` (str), `condition` (str: excellent, good or fair), `price` (float), `colors` (list[str]), `brand` (str or None; None for most listings) and `platform` (str: depop, thredUp or poshmark). The dicts are the unmodified listing records.
- **When it has nothing:** Returns an empty list `[]` — never None, never an exception. This covers no keyword match, every match filtered out by size or price, and a blank `description`.

### `suggest_outfit`

- **What it does:** Asks the model for one or two outfits built around the thrifted item, naming pieces from the user's wardrobe when there are any.
- **Inputs:** `new_item` (dict) — one listing dict as returned by `search_listings`, using its `title`, `category`, `colors`, `style_tags` and `price`; `wardrobe` (dict) — has an `items` key holding a list[dict], each with `id`, `name`, `category`, `colors`, `style_tags` and `notes` (str or None). `items` may be an empty list.
- **Returns:** A non-empty `str` of plain text. With a populated wardrobe it describes one or two outfits that name specific wardrobe items by their `name`. With an empty wardrobe it gives general styling advice for the item and names no owned pieces.
- **When it has nothing:** An empty wardrobe is not a failure: it returns the general-advice string above, so the result is still non-empty. It never returns `""` or None and does not raise on an empty `items` list. If the model call fails, `generate.ModelUnavailable` is allowed to propagate and the loop handles it.

### `create_fit_card`

- **What it does:** Asks the model for a short social-media caption about the find, built from the outfit text and the item's details.
- **Inputs:** `outfit` (str) — the string returned by `suggest_outfit`; `new_item` (dict) — the same listing dict, using its `title`, `price` (float) and `platform` (str).
- **Returns:** A `str` of two to four sentences, written like a post rather than a product description. It mentions the item, its price and its platform once each, and is specific about the vibe. Different inputs, or repeated calls, give different wording, which depends on `config.CACHE_ENABLED` and `config.TEMPERATURE`.
- **When it has nothing:** If `outfit` is `""` or whitespace only, it makes no model call and returns the message `"No outfit to write a caption for — run suggest_outfit first."` (a non-empty str). It does not raise.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, put a message in `session["error"]` that tells the user what to change (loosen the price, drop the size, or use fewer or different keywords), return the session, and do not call `suggest_outfit` or `create_fit_card`, so `outfit_suggestion` and `fit_card` stay None. Otherwise, put the first result in `session["selected_item"]` and go to `suggest_outfit`, then `create_fit_card` with its output.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** regular expressions, with no model call (`agent.py::parse_query`). A price comes from `under`, `below`, `less than`, `up to`, `max` or a bare `$N`. A size comes from `size X`, and may include a waist/length pair like `W30 L30`. What is left, minus punctuation, is the description. `'vintage graphic tee under $30, size M'` becomes description `vintage graphic tee`, size `M`, max_price `30.0`.

**What moves through the session:** `query` -> `parsed` -> `search_results` (and `searched`, set to True once the search has run) -> `selected_item` -> `outfit_suggestion` -> `fit_card`; `error` is set only when the run stops early. `run_agent` is a loop. Each pass reads the session to decide which one tool to run next, runs it, writes the result back and goes round again. `suggest_outfit` is called with `session['selected_item']` and `create_fit_card` with `session['outfit_suggestion']` and `session['selected_item']`, never with a local variable. `trace.check_iterations` is called on every pass.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**
python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"   
Output:
Hey friend! Those vintage Levi's 501s are an absolute holy grail find—that medium wash is so versatile! Since they’re a classic straight fit, let’s play with proportions using what you already have.

**Look 1: Casual Streetwear**
Tuck in your **White ribbed tank top**, loop your **Brown leather belt** through the waist, and layer on your **Oversized grey crewneck sweatshirt**. Finish with your **Chunky white sneakers** and **Black crossbody bag**. It’s effortlessly cool!

**Look 2: Edgy & Cropped**
Wear your **White ribbed tank top** under the **Black cropped zip hoodie**, and top it off with your **Vintage black denim jacket**. Rock them with your **Black combat boots** for a killer downtown vibe.

You're going to wear these out!

python -c "from tools import suggest_outfit; from utils.data_loader import get_empty_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_empty_wardrobe()))"
Output:       
Hey there! Those vintage 501s are absolute gold. Since I don't know your closet yet, let's build two effortless looks with basics you likely already own!

**1. The Off-Duty Cool Look (Streetwear Vibe):**
Pair the jeans with an oversized, thrifted grey crewneck sweatshirt. Tuck the front in slightly and add crisp white leather sneakers. Accessorize with a simple black belt and a silver chain necklace. It’s comfy, classic, and instantly chic.

**2. The Timeless Coffee Run (Casual Classic):**
Tuck a fitted plain black or white baby tee into the waistband. Layer an unbuttoned oversized white linen button-down over top. Slip on some retro canvas sneakers (like Converse or Vans) and toss a canvas tote bag over your shoulder.

How do those sound for starters?

python -c "from tools import create_fit_card; from utils.data_loader import load_listings; i=load_listings()[0]; [print(create_fit_card('jeans and white sneakers', i), chr(10)) for _ in range(3)]"
Output:
Absolute perfection for under forty bucks. Scored these vintage Levi's 501 jeans on Depop for just $38 and the wash is honestly unmatched. Paired them with crisp white sneakers for that effortlessly cool, running-errands-all-day energy.

Absolute perfection for under forty bucks. Scored these vintage Levi's 501 jeans on Depop for just $38 and the wash is honestly unmatched. Paired them with crisp white sneakers for that effortlessly cool, running-errands-all-day energy.

Absolute perfection for under forty bucks. Scored these vintage Levi's 501 jeans on Depop for just $38 and the wash is honestly unmatched. Paired them with crisp white sneakers for that effortlessly cool, running-errands-all-day energy.

```
$ python app.py ask 'vintage graphic tee under $30'
Found:    Graphic Tee — 2003 Tour Bootleg Style — $24.0 on depop

  Outfit:   Hey! That 2003 tour bootleg tee is a fantastic, grunge-ready find. Here is how you can style it with pieces you already own:

**Outfit 1: Effortless Streetwear**
Pair the graphic tee with your baggy straight-leg jeans, dark wash. Cinch the waist with the brown leather belt, and layer the slightly cropped vintage black denim jacket on top. Finish the look with your black combat boots and the black crossbody bag for an edgy, everyday vibe. 

**Outfit 2: Contrast Grunge**
Tuck the tee into your wide-leg khaki trousers. Throw on your black cropped zip hoodie unzipped over it, and step into your chunky white sneakers for a cool, balanced mix of slouchy and structured.

  Fit card: Scored this 2003 tour bootleg tee on Depop for just $24 and it's officially my new personality. Threw it on with baggy denim and combat boots for the ultimate effortless grunge look. Honestly, nothing beats a good thrift win.

0 model calls this session, 2 served from cache
```

The empty path (`python agent.py`, second example):

```
  stopped: Nothing matched your search. You could raise the price limit above $5, drop the size filter (size XXS), or try fewer or different keywords than "designer ballgown".
  fit_card is None, as it should be
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
[{'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', 'description': 'Vintage-style bootleg tee with faded graphic. Slightly boxy fit. 100% cotton, soft and worn-in.', 'category': 'tops', 'style_tags': ['graphic tee', 'vintage', 'grunge', 'streetwear', 'band tee'], 'size': 'L', 'condition': 'good', 'price': 24.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', 'description': 'Super cute early 2000s baby tee with butterfly graphic. Fitted crop length. Tag says medium but fits like a small.', 'category': 'tops', 'style_tags': ['y2k', 'vintage', 'graphic tee', 'cottagecore'], 'size': 'S/M', 'condition': 'excellent', 'price': 18.0, 'colors': ['white', 'pink', 'purple'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_033', 'title': 'Vintage Band Tee — Faded Grey', 'description': 'Faded grey band-style tee with distressed graphic. Crew neck. Fits boxy. Well-loved but no holes or major damage.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'band tee', 'graphic tee', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 19.0, 'colors': ['grey', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_017', 'title': 'Mesh Long-Sleeve Top — Black', 'description': 'Sheer black mesh long-sleeve. Great for layering under a graphic tee or over a bralette. Stretchy material, fits true to size.', 'category': 'tops', 'style_tags': ['y2k', 'grunge', 'goth', 'layering'], 'size': 'S/M', 'condition': 'excellent', 'price': 15.0, 'colors': ['black'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_015', 'title': 'Vintage Graphic Hoodie — Faded Black', 'description': 'Faded black pullover hoodie with barely-visible vintage graphic on the chest. Cozy interior. Some pilling but adds to the worn-in look.', 'category': 'tops', 'style_tags': ['vintage', 'grunge', 'graphic', 'streetwear'], 'size': 'L', 'condition': 'fair', 'price': 26.0, 'colors': ['black', 'charcoal'], 'brand': None, 'platform': 'depop'}, {'id': 'lst_011', 'title': 'Low-Rise Cargo Pants — Khaki', 'description': 'Y2K era low-rise cargo pants. Lots of pockets. Khaki color, slightly distressed at the hems. Great for layering with a long tee.', 'category': 'bottoms', 'style_tags': ['y2k', 'cargo', '2000s', 'streetwear'], 'size': 'W29', 'condition': 'fair', 'price': 27.0, 'colors': ['khaki', 'tan'], 'brand': None, 'platform': 'poshmark'}]
```

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
Hey friend! Those vintage Levi's 501s are an absolute holy grail find—that medium wash is so versatile! Since they’re a classic straight fit, let’s play with proportions using what you already have.

**Look 1: Casual Streetwear**
Tuck in your **White ribbed tank top**, loop your **Brown leather belt** through the waist, and layer on your **Oversized grey crewneck sweatshirt**. Finish with your **Chunky white sneakers** and **Black crossbody bag**. It’s effortlessly cool!

**Look 2: Edgy & Cropped**
Wear your **White ribbed tank top** under the **Black cropped zip hoodie**, and top it off with your **Vintage black denim jacket**. Rock them with your **Black combat boots** for a killer downtown vibe. 

You're going to wear these out!
```

With an empty wardrobe (`get_empty_wardrobe()` in place of the example one):

```
Hey there! Those vintage 501s are absolute gold. Since I don't know your closet yet, let's build two effortless looks with basics you likely already own!

**1. The Off-Duty Cool Look (Streetwear Vibe):**
Pair the jeans with an oversized, thrifted grey crewneck sweatshirt. Tuck the front in slightly and add crisp white leather sneakers. Accessorize with a simple black belt and a silver chain necklace. It’s comfy, classic, and instantly chic.

**2. The Timeless Coffee Run (Casual Classic):**
Tuck a fitted plain black or white baby tee into the waistband. Layer an unbuttoned oversized white linen button-down over top. Slip on some retro canvas sneakers (like Converse or Vans) and toss a canvas tote bag over your shoulder. 

How do those sound for starters?
```

```
$ AI201_CACHE=0 python -c "from tools import create_fit_card; from utils.data_loader import load_listings; i=load_listings()[0]; [print(create_fit_card('jeans and white sneakers', i)) for _ in range(3)]"
The hunt is finally over. Snagged these vintage Levi's 501 jeans on Depop for $38 and they fit like an absolute dream. Paired them with crisp white sneakers for that effortlessly cool 90s off-duty look.

Found my new favorite pair of vintage Levi's 501 jeans on Depop for just $38. Threw them on with fresh white sneakers for that effortlessly lived-in, 90s off-duty look. Honestly not taking these off anytime soon.

Found my new holy grail pair of vintage Levi's 501 jeans on Depop for just $38. They’ve got that perfectly broken-in medium wash and fit like an absolute dream. Honestly can't wait to wear these on repeat with crisp white sneakers and an oversized tee.
```

(Three runs on the same item with the cache off; the wording differs each time.)

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

**Moment 1**

- *What I asked for:* I gave Claude my Tool Inventory spec for `search_listings` (keyword overlap, whole-token size matching, empty list on no match) and asked it to implement the tool in `tools.py`.
- *What came back:* It worked on the spec's cases: `S` returned `S` and `S/M` but no `US 9` shoes, and an impossible query returned `[]`. But for `'graphic tee'` it ranked "Y2K Baby Tee" above "Graphic Tee — 2003 Tour Bootleg Style", because both scored 2 and ties kept data-file order.
- *What I changed:* I added a tie-break on how many keywords appear in the title, so the "Graphic Tee" listing now comes first, and I updated the scoring line in the Tool Inventory so the spec matches the code. I also ignore filler words (`under`, `size`, `looking`) so they can't score matches, and wrote that into the spec.

**Moment 2**

- *What I asked for:* I asked Claude to build `run_agent` so it follows my branch rule and reads each tool's input back out of the session instead of passing values along.
- *What came back:* It gave me a loop that picks the next tool from session state, with the empty-search branch returning before `suggest_outfit`. Separately, its first write of `tools.py` turned the `n` escapes inside the prompt strings into real line breaks, which gave a `SyntaxError` the first time the module was imported.
- *What I changed:* I didn't take the loop on trust: I ran it with the model stubbed and confirmed the same object in `session["selected_item"]` reached both `suggest_outfit` and `create_fit_card`, and that the empty path left `fit_card` as None. The broken string literals were repaired and the import re-run until it compiled, and I kept the no-results message naming only the filters the user actually set (price, size, keywords).

**Moment 3 (unit 4: building the test)**

- *What I asked for:* I asked Claude to write the scenarios for criteria 3, 4 and 5 in `scenarios.py`, and then to cut them to one scenario per criterion because 14 scenarios x 5 tries was too many calls.
- *What came back:* It picked queries by running `search_listings` first, so each one returns the listing I expected (for example `lst_002` for the baby tee), and it rewrote criteria 4 and 5 in `criteria.md` underneath the originals. It told me the original 5-item and 5-query versions would cost 25 runs each. That was wrong: they need 5 runs each, since the five items or queries are the five tries.
- *What I changed:* I kept the one-scenario-per-criterion file, but the verdicts now state that those two revisions were made for run cost and not because the criteria couldn't be measured, and that the original wording was never run. Claude also pointed out that criterion 3 had only been scored by title, not by the ids the criterion names, and added `check_ids.py` to record the ids; I reviewed that result before moving on.

**Moment 4 (unit 4: scoring and the fix)**

- *What I asked for:* I asked Claude to score the before-run against my criteria and to make one fix for the miss my diagnosis named.
- *What came back:* It scored every fit card with a script and found a problem my table had hidden: 3 of 20 cards wrote the price as "forty bucks", and all 20 opened with "Scored this" or "Found the". It then rewrote the `create_fit_card` prompt to require `$N` and ban those openers.
- *What I changed:* The after-run was measured instead of assumed fixed, and I reviewed the numbers before moving on: the price problem went from 3 cards to 0, but the banned phrase was replaced by "Snagged ..." in 14 of 20 cards. I recorded that as a partial fix in the README and kept it as the top item in What's Still Broken.
---

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

<!-- Five criteria, five tries each, in this exact format.

     Five, because your criteria are written out of five. Mark each try PASS
     or FAIL, count the passes, and read that count against your target — a
     row targeting 4 of 5 with three PASS cells is MISSED (3/5).

     `python run_eval.py --label before` runs everything and writes the table
     into results/. Paste it here and fill in the verdicts. -->

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Full three-tool run returns a fit card (`vintage graphic tee under $30`) | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Empty search stops before tool 2 (`designer ballgown size XXS under $5`) | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Item in session matches item passed on (`denim jacket under $50`) | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card for one item: 2-4 sentences, price, platform, distinct openers (`y2k baby tee under $20`) | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Price and size filter holds (`vintage size L under $45`) | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

Run: `python run_eval.py --label before`, 5 scenarios x 5 tries, caching off,
temperature 0.9. Full output: `results/run_2026-10-11_1651_before.md`.
Criteria 4 and 5 use the revised wording in `criteria.md` (one item / one query
instead of five).

**How each try was scored**

- 1: `session["error"]` is None, trace has all of `search_listings`, `suggest_outfit`, `create_fit_card`, and a fit card came back. 5/5.
- 2: trace ends at `branch: search empty`, with no `suggest_outfit` or `create_fit_card` step, and the message names what to change. 5/5.
- 3: in `results/run_2026-10-11_1651_before.md` the trace's `selected_item` was the first `search_listings` title in every try, and the fit card named the jacket and `$42`. That compared titles, not ids, so I added `check_ids.py`. It wraps `suggest_outfit` and `create_fit_card` to record the `id` each receives, then compares the ids as `criteria.md` #3 describes. It was run for 5 tries on `denim jacket under $50` (output below, which is what the PASS cells for criterion 3 rest on).
- 4: scored by script on the five cards. Each has 3 sentences, contains `$18` and `Depop`, and all five first sentences are different strings.
- 5: `search_listings("vintage", "L", 45.0)` re-run directly (deterministic, no model). It returns 5 listings (`lst_010`, `lst_015`, `lst_018`, `lst_033`, `lst_006`). All have price <= 45 and sizes `L` or `M/L`, with no `XL` and no `US` shoe. The trace shows 5 items in all five tries.

**Real output from one try**, pasted as text, naming the file and function
that produced it:

**Criterion 1** — `agent.py::run_agent` (trace) and `tools.py::create_fit_card` (card), try 1:

```
[1] parse_query
      in:  dict with keys: query
      out: dict with keys: description, size, max_price
[2] search_listings (Via MCP)
      in:  dict with keys: description, size, max_price
      out: 10 items: Graphic Tee — 2003 Tour Bootleg Style, Vintage Band Tee — Faded Grey, Y2K Baby Tee — Butterfly Print … +7 more
[3] selected_item
      in:  dict with keys: search_results
      out: Graphic Tee — 2003 Tour Bootleg Style ($24.0, depop)
[4] suggest_outfit
      in:  dict with keys: selected_item, wardrobe
      out: Hey there! That 2003 tour bootleg tee is an absolute score—it’s got that perfect lived-in grunge vibe. Since i…
[5] create_fit_card
      in:  dict with keys: outfit_suggestion, selected_item
      out: Scored this 2003 tour bootleg tee on Depop for $24 and it has the absolute best lived-in grunge vibe. Finally …

Fit card:
Scored this 2003 tour bootleg tee on Depop for $24 and it has the absolute best lived-in grunge vibe. Finally found a piece that looks genuinely vintage without trying too hard. Can't wait to live in this oversized fit all fall.
```

**Criterion 2** — `agent.py::run_agent` (branch) and `agent.py::_no_results_message` (message), try 1:

```
[2] search_listings (Via MCP)
      in:  dict with keys: description, size, max_price
      out: [] (empty)
[3] branch: search empty
      in:  dict with keys: description, size, max_price
      out: Nothing matched your search. You could raise the price limit above $5, drop the size filter (size XXS), or try…
      →    suggest_outfit and create_fit_card not called

session["error"]:
Nothing matched your search. You could raise the price limit above $5, drop the size filter (size XXS), or try fewer or different keywords than "designer ballgown".
```

**Criterion 3** — `agent.py::run_agent`, try 1 (`selected_item` step, then the two tools that read it):

```
[2] search_listings (Via MCP)
      out: 7 items: Denim Jacket — Light Wash, Cropped, 90s Track Jacket — Navy/White Stripe, High-Waisted Denim Shorts — Cutoff … +4 more
[3] selected_item
      in:  dict with keys: search_results
      out: Denim Jacket — Light Wash, Cropped ($42.0, poshmark)
[4] suggest_outfit
      in:  dict with keys: selected_item, wardrobe
      out: Hey friend! That cropped Wrangler denim jacket is an absolute vintage gem—it’ll add such a cool, classic textu…
[5] create_fit_card
      in:  dict with keys: outfit_suggestion, selected_item
      out: Scored this cropped vintage Wrangler jacket on Poshmark for $42 and I'm honestly obsessed. The light wash give…
```

Id check — `check_ids.py` (wraps `agent.py::run_agent`'s two tool calls), 5 tries:

```
try 1: suggest_outfit=lst_007 selected=lst_007 results[0]=lst_007 create_fit_card=lst_007 -> PASS
try 2: suggest_outfit=lst_007 selected=lst_007 results[0]=lst_007 create_fit_card=lst_007 -> PASS
try 3: suggest_outfit=lst_007 selected=lst_007 results[0]=lst_007 create_fit_card=lst_007 -> PASS
try 4: suggest_outfit=lst_007 selected=lst_007 results[0]=lst_007 create_fit_card=lst_007 -> PASS
try 5: suggest_outfit=lst_007 selected=lst_007 results[0]=lst_007 create_fit_card=lst_007 -> PASS
```

**Criterion 4** — `tools.py::create_fit_card`, all five tries for `y2k baby tee under $20` (`lst_002`, $18, depop):

```
1: Scored this butterfly print Y2K baby tee on Depop for just $18 and I am officially obsessed with the early-2000s energy. Already planning to wear it with baggy denim and sneakers for running errands, or dressed up a bit with trousers and combat boots. Such a good little wardrobe win.
2: Scored this butterfly baby tee on Depop for just $18 and I am officially living my 2000s pop star fantasy. The graphics are so nostalgic and it fits like an absolute glove. Can't wait to style this with some baggy denim all summer long.
3: Scored this butterfly print Y2K baby tee on Depop for just $18 and I am obsessed. It’s giving major early-2000s mallrat energy, especially paired with baggy denim and combat boots. Can't wait to live in this all through autumn.
4: Scored this butterfly Y2K baby tee on Depop for just $18 and I am obsessed. The proportions are giving major 2000s streetwear when paired with baggy denim and chunky sneakers. Honestly such a win for the wardrobe rotation!
5: Scored this Y2K butterfly baby tee on Depop for just $18 and I’m obsessed. It gives the ultimate early 2000s streetwear energy when paired with baggy dark denim and combat boots. Can't wait to style it with wide-leg trousers for a softer look, too.
```

**Criterion 5** — `tools.py::search_listings("vintage", "L", 45.0)` (via `agent.py::run_agent`, try 1 trace, then the full list re-run directly):

```
[2] search_listings (Via MCP)
      in:  dict with keys: description, size, max_price
      out: 5 items: Vintage Windbreaker — Color Block Purple/Teal, Vintage Graphic Hoodie — Faded Black, Vintage Linen Blazer — Cream … +2 more

lst_010 Vintage Windbreaker — Color Block Purple/Teal   size L    $40.0
lst_015 Vintage Graphic Hoodie — Faded Black            size L    $26.0
lst_018 Vintage Linen Blazer — Cream                    size M/L  $38.0
lst_033 Vintage Band Tee — Faded Grey                   size L    $19.0
lst_006 Graphic Tee — 2003 Tour Bootleg Style           size L    $24.0
```

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 | Full three-tool run returns a fit card | 4 of 5 | MET (5/5) | Counted tries where `session["error"]` was None and the trace shows all three tools plus a fit card: 5 of 5. |
| 2 | Empty search stops before tool 2 | 5 of 5 | MET (5/5) | All 5 traces end at `branch: search empty` with no `suggest_outfit` or `create_fit_card` step, and `session["error"]` names the price, size and keywords to change. |
| 3 | Item in session matches item passed on | 5 of 5 | MET (5/5) | `check_ids.py` recorded the ids: `lst_007` was the same at `search_results[0]`, `selected_item`, `suggest_outfit` and `create_fit_card` in all 5 tries, and every card named the jacket and `$42`. |
| 4 | Fit card: 2-4 sentences, price, platform, distinct openers | 4 of 5 | MET (5/5) | Scored the 5 cards for `lst_002` by script: all have 3 sentences, `$18` and `Depop`, and the 5 first sentences are different strings. Read plainly this passes, but see the caveat in the diagnoses. |
| 5 | Price and size filter holds | 5 of 5 | MET (5/5) | `search_listings("vintage","L",45.0)` returns 5 listings, all price <= 45 and size `L` or `M/L`, with no `XL` and no `US` shoe, and the trace shows 5 results in all 5 tries. |

**Diagnoses**

**No criterion missed, so there is no miss to diagnose.** Reading that plainly, it
says less than it looks like it does:

- **Criterion 4's pass depends on which item I ran.** The same check would have
  failed on the other fit cards in the log. In the `vintage size L under $45`
  scenario, tries 1, 2 and 5 produced cards for the windbreaker that say
  "for forty bucks" instead of "$40". The price is there, but the `$40` check
  would not find it, so 3 of those 5 cards would fail part (b). That would be a
  miss on the model's output: `tools.py::create_fit_card` hands the model
  `$40.00` and asks it to "mention the price", and at temperature 0.9 the model
  sometimes spells it out. The `y2k baby tee` run didn't hit that, so a 5/5
  there does not show that the price rule holds in general.
- **Criterion 4's distinct-opening rule passes on a technicality.** All five
  first sentences are different strings, but they are one template:
  "Scored this ... on Depop for just $18 and I am obsessed...". Tries 3 and 4
  differ by a single word ("print"). The criterion only compares strings, so it
  passed. This is the failure I wrote down as the one I'd dislike most, and the
  criterion didn't catch it.
- **Criteria 2, 3 and 5 are deterministic code and passed identically in every
  try.** Five identical results show the branch, the session hand-off and the
  filter are stable, and they carry no model variation to measure.
- **Criterion 1's 4-of-5 target had slack I never used.** It got 5/5, so the
  allowance for model failure and synonym misses was not tested at all.

**Were my targets too low?** Not in the numbers, but criterion 4 is the one I'd
tighten. I would require that the opening `Scored this ... on <platform> for $N`
phrasing not repeat (for example, no two cards start with the same first four
words), and that the price appears as digits. That would turn today's technical
pass into the miss it behaves like. I have not applied this as a revision,
because the current wording was measurable and I met it as written.

**A note on the two revisions I made in `criteria.md`.** Criteria 4 and 5 were
rewritten before the run, from "5 different items" and "5 queries" to one item
and one query. The reason I gave, run cost, is not the kind of change the unit
counts as a valid revision (the criteria were measurable). I also overstated the
cost: the original wording needs one run per item or query, so 5 runs each, not
25. The numeric targets did not change, so no target was lowered. But the
original versions (5 different items, 5 different size+price queries) were never
run, so the verdicts above are for the revised wording only.

---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```
python app.py ask 'I have a Straight Leg Black Jeans, what should i pair with them?' --trace
[1] parse_query
      in:  dict with keys: query
      out: dict with keys: description, size, max_price
[2] search_listings (Via MCP)
      in:  dict with keys: description, size, max_price
      out: 10 items: Straight Leg Black Jeans — Faded, Straight Leg Khaki Trousers — Olive, Vintage Levi's 501 Jeans — Medium Wash … +7 more
[3] selected_item
      in:  dict with keys: search_results
      out: Straight Leg Black Jeans — Faded ($30.0, thredUp)
[4] suggest_outfit
      in:  dict with keys: selected_item, wardrobe
      out: Hey there! Those faded black Levi’s are an absolute thrift find—you *need* them. Since you already love baggy …
[5] create_fit_card
      in:  dict with keys: outfit_suggestion, selected_item
      out: Scored these perfectly faded black Levi's on thredUp for just $30. They have that exact broken-in, 90s grunge …

  Found:    Straight Leg Black Jeans — Faded — $30.0 on thredUp

  Outfit:   Hey there! Those faded black Levi’s are an absolute thrift find—you *need* them. Since you already love baggy jeans, this straight-leg fit will give you that effortlessly cool vintage look while mixing up your silhouettes. 

Here are two ways to style them using pieces right from your closet:

**Outfit 1 (Grunge-Off-Duty):** 
Pair the jeans with the **White ribbed tank top** tucked in, topped with the **Vintage black denim jacket**. Slip into your **Black combat boots** and toss on the **Black crossbody bag**. Instant 90s icon vibes.

**Outfit 2 (Cozy Contrast):** 
Layer the **Oversized grey crewneck sweatshirt** over the jeans for that slouchy, lived-in feel. Finish it with your **Chunky white sneakers** for a fresh, casual look.

  Fit card: Scored these perfectly faded black Levi's on thredUp for just $30. They have that exact broken-in, 90s grunge look I've been hunting for. Can't wait to live in these with an oversized sweatshirt and chunky sneakers all fall.

2 model calls this session, 574 prompt + 238 output tokens

```

**Empty search**

```
ython app.py ask 'does backpack under 50$?' --trace
[1] parse_query
      in:  dict with keys: query
      out: dict with keys: description, size, max_price
[2] search_listings (Via MCP)
      in:  dict with keys: description, size, max_price
      out: [] (empty)
[3] branch: search empty
      in:  dict with keys: description, size, max_price
      out: Nothing matched your search. You could raise the price limit above $50, or try fewer or different keywords tha…
      →    suggest_outfit and create_fit_card not called

  Nothing matched your search. You could raise the price limit above $50, or try fewer or different keywords than "does backpack $?".

0 model calls this session

```

**On the MCP move:** I moved `search_listings` (the one tool with no model call)
behind an MCP server. `mcp_server.py` now registers it with `@mcp.tool()`,
typed inputs (`description: str`, `size: str | None`, `max_price: float | None`)
and a docstring that states the inputs and the empty case, and calls the real
implementation in `tools.py` under an alias. In `agent.py::run_agent` the direct
call was swapped for `call_tool("search_listings", {...})` from `mcp_client.py`,
which is why the trace now reads `search_listings (Via MCP)`. The return value
did not change: for the three queries I compared (`vintage` size L under $45,
`designer ballgown` size XXS under $5, `denim jacket` under $50), the list from
`call_tool` was `==` to the list from calling `search_listings` directly, with
the same count (5, 0, 7) and `price` still a `float`, and the empty search still
came back as `[]`, so the loop's `if not results` branch kept working. The one
thing that did behave differently is speed: each `call_tool` starts the server
as a fresh process, and it took 0.3–0.7 s per search against about 0.0005 s
direct. That is invisible next to the model calls, but it is a real cost of the
seam. Nothing broke, so there's no failure to document.

---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:** one prompt, the one in `tools.py::create_fit_card`. I added
two rules to what it sends the model, and changed nothing else (not the model,
temperature, tools, loop or scenarios):

```
Write the price in digits with a dollar sign, like $40 — never spell it out as words like 'forty bucks'.
Do not start the caption with 'Scored this' or 'Found this'; open with the vibe or the way you'll wear it.
```

**Which failure it was meant to fix:** both findings in my diagnosis for
criterion 4, which point at the same model call. (1) In the criterion 5
scenario, 3 of 5 windbreaker cards said "forty bucks" and would fail the `$40`
price check. (2) All 20 fit cards in the before-log opened with "Scored this" or
"Found the". I counted these as one change, a rewrite of one prompt, but they
are two instructions. I measure them separately below so each can be judged on
its own.

### Run Log — After

`python run_eval.py --label after`, same 5 scenarios, 5 tries each, caching off
(`results/run_2026-10-11_1715_after.md`). Scored the same way as the before-log.
Criterion 3 re-scored with `check_ids.py` (all 5 tries: `lst_007` at every step).

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Full three-tool run returns a fit card | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Empty search stops before tool 2 | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Item in session matches item passed on | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card for one item: 2-4 sentences, price, platform, distinct openers | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Price and size filter holds | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

**Before and after, side by side.** The five criteria scored identically (all
MET, 5/5), so the table above can't show whether the change did anything. These
are the measurements that can, from `score_runs.py` run on both logs:

| Measure (all fit cards in the log, 20 cards unless noted) | Before | After |
|---|---|---|
| Five criteria verdicts | all MET | all MET |
| Price written as digits (`$N`) | 17 / 20 | 20 / 20 |
| Cards opening "Scored this" / "Found the" | 20 / 20 | 0 / 20 |
| Cards using the word "obsessed" | 13 / 20 | 0 / 20 |
| Cards containing the word "snagged" | 0 / 20 | 14 / 20 |
| Cards starting "Channeling" | 0 / 20 | 4 / 20 |
| 2-4 sentences / platform named | 20 / 20, 20 / 20 | 20 / 20, 20 / 20 |
| Criterion 4 item: distinct first sentences | 5 / 5 | 5 / 5 |
| Criterion 4 item: distinct first 4 words | 4 / 5 | 5 / 5 |

Real output, criterion 4 (`tools.py::create_fit_card`, `y2k baby tee under $20`),
all five tries after the change:

```
1: Pink, purple, and butterfly graphics are doing all the heavy lifting for my inner 2000s pop star. Snagged this Depop baby tee for $18 and I'm already rotating it between baggy low-rise denim and oversized zip-ups. Main character energy for under twenty bucks.
2: Unironically living in this butterfly baby tee for the rest of spring. Snagged it on depop for $18 and honestly, the Y2K nostalgia is undefeated. Pair it with baggy denim and chunky sneakers or wide-leg trousers for that effortless off-duty look.
3: The sweet-meets-grunge contrast of this butterfly baby tee is everything. Snagged it on depop for $18 and I'm already planning a million ways to style it. Time to live out all my 2000s pop star dreams.
4: Channeling absolute 2000s pop princess energy with this pink and purple butterfly baby tee. Got it on Depop for just $18 and I am already living in it. Can't decide if I want to lean into baggy denim streetwear or give it a grungy edge with combat boots today.
5: Channeling serious 2000s mall-rat energy with this little butterfly tee. Got lucky on Depop and snagged it for only $18. Already planning to wear it with baggy denim and chunky sneakers until further notice.
```

**Did it help, and how do I know:** Yes, for the price problem, and only
partly for the repetition problem.

- **Price in digits: it helped.** The three "forty bucks" cards were the only
  cards in the before-log without a `$` figure (17 of 20). After the change all
  20 cards have one. The cards for the same windbreaker that failed before now
  read "...on thredUp for $40" in all 5 tries. That is 3 failures to 0 on a
  small sample at temperature 0.9, so it is strong evidence, not proof.
  Side note: after-try 1 for the baby tee also says "under twenty bucks" after
  giving `$18`; the rule banned spelling the price out but the model still
  rounded it in words once.
- **Repeated opening: it moved the template, it didn't remove it.** Banning
  "Scored this" worked literally (20 of 20 down to 0 of 20) and the five
  openers for one item are now all different in their first four words. But
  14 of 20 cards now put "Snagged ... on <platform> for $N" in the second
  sentence, and 4 start with "Channeling". The model replaced one template with
  another. A phrase-ban prompt can only chase phrases.
- **No verdict changed.** All five criteria were MET before and after, so the
  five-row table is identical. The improvement shows up only in the extra
  measurements above, which I chose after seeing the before-log, so treat them as
  a fair but not pre-registered test.
- **Nothing got worse on what the criteria check:** 2-4 sentences and platform
  named held at 20 of 20, and the average card went from 237 to 250 characters.
- Only the prompt changed between the two runs, but the model is not
  deterministic, so each run is one sample of five tries per scenario.

---

## What's Still Broken

No criterion is MISSED in either run log: all five were MET (5/5) before and after.
That is not the same as nothing being left. These are the things I would still
fix, in order of how much I'd worry about them:

1. **Criterion 4's "distinct openers" rule is weaker than what I care about.**
   The prompt fix removed the "Scored this ... for $N and I am obsessed" template
   but the model replaced it: 14 of 20 cards now say "Snagged ... on <platform>
   for $N" in the second sentence and 4 start with "Channeling". The criterion
   still passes because it only compares first sentences as strings. *What I'd
   do:* tighten the criterion (no two cards share their first four words, and no
   shared second-sentence verb), and change the prompt to give each call a
   different angle to write from (for example a randomly chosen "mention the
   fit / the colour / the occasion") instead of banning phrases one at a time.
   *Why I stopped:* the prompt change is one change and the unit asked for one;
   a second round of ban-list prompting would have been the same fix again.
2. **I never ran the original wording of criteria 4 and 5.** I rewrote them to
   one item and one query before the run, citing run cost, and the cost was
   really 5 runs each, not 25. My verdicts are for the revised wording. *What
   I'd do:* run "5 different items" and "5 size+price queries" once each (about
   10 model calls and 5 model-free searches). *Why I stopped:* I noticed after
   the before-run and chose to report it instead of re-running at the end.
3. **Criterion 1's slack was never tested.** I set 4 of 5 because a keyword
   search can miss on synonyms ("t-shirt" vs "tee"), and the one query I ran,
   `vintage graphic tee`, has no synonym problem, so 5/5 says nothing about
   that risk. *What I'd do:* add a scenario like `t-shirt under $30` and expect
   it to fail until `search_listings` handles synonyms.
4. **The price rule still leaks.** After the fix every card has `$N`, but one
   baby-tee card also said "under twenty bucks" after giving `$18`. *What I'd
   do:* count any spelled-out price as a failure in the scorer and add that to
   the prompt. *Why I stopped:* it didn't break the criterion as written.
5. **`parse_query` leaves a stray `$` in the description** when the price is
   written after the number: `does backpack under 50$?` searched for
   `"does backpack $?"` (see the empty-search trace above). It happened to be an
   empty search anyway, but the same bug could drop a matching word. *What I'd
   do:* strip a trailing `$` in `parse_query`. *Why I stopped:* no scenario in my
   five hit it, so it is outside what I measured.
6. **Criteria 2, 3 and 5 can't vary between tries.** They are deterministic
   code, so five tries is five copies of one result. They are worth having as
   regression checks, but they don't show reliability.

<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

## Capstone

Everything below this heading is the deploy-and-instrument capstone. The sections above it belong to the earlier project and are unchanged.

## The Shape

<!-- Unit 9, Milestone 1. Shape A: Deploy and instrument. -->

**Shape A — Deploy and instrument.** FitFindr has only ever run from my laptop's command line, so I am adding the operational layer that lets it run on its own on Render's free web service (`gunicorn serve:app`, with `GEMINI_API_KEY` set as a Render environment variable instead of a `.env` file). In `serve.py` I will add one structured JSON log line per `/ask` request, written to stdout where Render's log viewer picks it up. It records the outcome (found, no results, model unavailable, or server error), total latency in milliseconds, time spent in each step (`search_listings`, `suggest_outfit`, `create_fit_card`), and the model calls, cache hits and tokens that request used, read from the counters `generate.py` already keeps. A small `GET /metrics` route will report request counts by outcome and p50/p95 latency since the process started, and I will time the first request after the free tier's idle sleep so the cold start becomes a measured number. The agent's behavior stays exactly what it is now; the extension is the run path, the instrumentation, and the numbers that come out of it.

**Out of scope**

- **Changing the MCP setup.** `run_agent` already searches through MCP (`mcp_client.call_tool` starts `mcp_server.py` as a separate process for each search). I am deploying that path as it is and only timing it. I am not moving more tools onto MCP and not reverting the search to a direct call. The extra process per request matters on a 512 MB instance, which is why `serve.py` already runs one request at a time and why the start command stays plain `gunicorn serve:app`.
- **Changing what the agent does.** No new tools, no changes to `parse_query`, search scoring, prompts or `config.TEMPERATURE`, and no fixes to quality problems found along the way. Those go in What's Still Broken, because this unit measures the system as it is.
- **Real monitoring infrastructure.** No external uptime pinger, no Datadog or Prometheus, no database, no dashboard, and no alerting. The numbers come from stdout logs and an in-memory `/metrics` route that resets on every restart or sleep.
- **A user interface, auth or rate limiting.** It stays an API with `POST /ask` and `GET /health`, and I am not adding a front end, accounts, or a way to keep strangers from spending my Gemini quota beyond what `generate.py` already does.

**Size check.** Estimated build time is about 80 minutes: per-step timing and the JSON log line in `serve.py` (~30 min), the `/metrics` route with in-memory counters and percentiles (~20 min), Render setup with a start command, environment variable and health check path (~15 min), and a first deploy plus a smoke test (~15 min). That is under the ninety-minute ceiling. Per-step timing is done in `serve.py` by wrapping `agent.call_tool` (the MCP search) and `agent.suggest_outfit` and `agent.create_fit_card`, so `agent.py` itself is not edited. If that wrapping turns out to be fiddly, I will time the whole `run_agent` call instead and drop the per-step numbers.

---

## Unit 9 — Run Log — Before

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

## Instrumentation

**What gets logged.** Every `POST /ask` writes one JSON line to stdout, which Render's Logs tab collects. I read the records back by setting the time range in that tab and downloading the lines; the exports are in `results/render_log_*.jsonl`. It is stdout and not a file on the server because Render's free tier wipes the filesystem on every restart or sleep. The fields:

| Field | What it holds |
|---|---|
| `ts` | UTC time the request finished |
| `query` | the input text (empty string for a rejected request) |
| `outcome` | `found`, `no_results`, `model_unavailable`, `server_error` or `rejected_input` |
| `error_type` | `missing_query`, `ModelUnavailable`, an exception class name, or null |
| `output` | the fit card, or the message the user got when there was no card |
| `total_ms` | time inside `run_agent` |
| `steps_ms` | milliseconds per step: `search` (the MCP call), `outfit`, `fit_card` |
| `model_calls`, `cache_hits`, `tokens` | what this one request used, from the counters in `generate.py` |

A `{"event": "boot"}` line is written when the app starts, so a restart shows up as a new boot line.

**Ten entries** (the criterion 4 mix from after-run 3, 6 matching, 2 no-match and 2 empty requests, in the order they ran; `output` is cut to 110 characters here and complete in the log):

```
{"event": "ask", "ts": "2026-11-18T22:40:19Z", "query": "vintage graphic tee under $30", "outcome": "found", "error_type": null, "output": "Already living in this 2003 tour bootleg tee. Snagged it on depop for $24 and it adds the exact amount of f...", "total_ms": 5758, "steps_ms": {"search": 4021, "outfit": 1118, "fit_card": 618}, "model_calls": 2, "cache_hits": 0, "tokens": 853}
{"event": "ask", "ts": "2026-11-18T22:40:19Z", "query": "", "outcome": "rejected_input", "error_type": "missing_query", "output": "Send JSON with a 'query' field, e.g. {\"query\": \"vintage graphic tee under $30\"}", "total_ms": 0, "steps_ms": {}, "model_calls": 0, "cache_hits": 0, "tokens": 0}
{"event": "ask", "ts": "2026-11-18T22:40:26Z", "query": "vintage graphic tee under $30", "outcome": "found", "error_type": null, "output": "Channeling heavy 2003 garage-show energy with this oversized bootleg tour tee. Snagged it on Depop for $24 ...", "total_ms": 6356, "steps_ms": {"search": 4128, "outfit": 1324, "fit_card": 904}, "model_calls": 2, "cache_hits": 0, "tokens": 886}
{"event": "ask", "ts": "2026-11-18T22:40:30Z", "query": "designer ballgown size XXS under $5", "outcome": "no_results", "error_type": null, "output": "Nothing matched your search. You could raise the price limit above $5, drop the size filter (size XXS), or ...", "total_ms": 4408, "steps_ms": {"search": 4408}, "model_calls": 0, "cache_hits": 0, "tokens": 0}
{"event": "ask", "ts": "2026-11-18T22:40:36Z", "query": "vintage graphic tee under $30", "outcome": "found", "error_type": null, "output": "Unlocking the ultimate grunge-streetwear vibe with this oversized 2003 tour bootleg tee. Snagged it on Depo...", "total_ms": 5714, "steps_ms": {"search": 3913, "outfit": 1136, "fit_card": 664}, "model_calls": 2, "cache_hits": 0, "tokens": 885}
{"event": "ask", "ts": "2026-11-18T22:40:42Z", "query": "vintage graphic tee under $30", "outcome": "found", "error_type": null, "output": "Nothing beats the perfect faded wash on a Y2K graphic tee, especially when you find it on Depop for just $2...", "total_ms": 5894, "steps_ms": {"search": 4023, "outfit": 1061, "fit_card": 810}, "model_calls": 2, "cache_hits": 0, "tokens": 859}
{"event": "ask", "ts": "2026-11-18T22:40:43Z", "query": "", "outcome": "rejected_input", "error_type": "missing_query", "output": "Send JSON with a 'query' field, e.g. {\"query\": \"vintage graphic tee under $30\"}", "total_ms": 0, "steps_ms": {}, "model_calls": 0, "cache_hits": 0, "tokens": 0}
{"event": "ask", "ts": "2026-11-18T22:40:49Z", "query": "vintage graphic tee under $30", "outcome": "found", "error_type": null, "output": "Channeling peak 90s rock-show energy with this 2003 tour bootleg tee. Snagged it on Depop for just $24 and ...", "total_ms": 5974, "steps_ms": {"search": 3747, "outfit": 1423, "fit_card": 803}, "model_calls": 2, "cache_hits": 0, "tokens": 867}
{"event": "ask", "ts": "2026-11-18T22:40:54Z", "query": "designer ballgown size XXS under $5", "outcome": "no_results", "error_type": null, "output": "Nothing matched your search. You could raise the price limit above $5, drop the size filter (size XXS), or ...", "total_ms": 4390, "steps_ms": {"search": 4390}, "model_calls": 0, "cache_hits": 0, "tokens": 0}
{"event": "ask", "ts": "2026-11-18T22:41:05Z", "query": "vintage graphic tee under $30", "outcome": "found", "error_type": null, "output": "Nothing beats leaning into that early-2000s grunge aesthetic. Just grabbed this vintage tour tee on Depop f...", "total_ms": 10776, "steps_ms": {"search": 3758, "outfit": 2611, "fit_card": 4406}, "model_calls": 2, "cache_hits": 0, "tokens": 809}
```

**Failed runs.** Entries 2 and 7 above are rejected inputs: an empty request returns HTTP 400 and now leaves a record with `error_type: missing_query`. Before the fix it left none. A failure from the model looks like this, from before-run 1 (the first model call got a 503 from Gemini; this is the older record shape, with no `output` or error text):

```
{"event": "ask", "ts": "2026-11-18T21:42:28Z", "query": "vintage graphic tee under $30", "outcome": "model_unavailable", "error_type": null, "total_ms": 4271, "steps_ms": {"search": 4139, "outfit": 131}, "model_calls": 1, "cache_hits": 0, "tokens": 0}
```

One kind of failure still leaves no entry: when Render restarts the instance, requests during the downtime get a 502 from Render's proxy and never reach the app. I only know about those from my own test client (`results/live_*.json`). The restart shows up only as a gap and, when the line survives, a boot record.

## What It Costs

**The measurement.** Ten matching requests, `vintage graphic tee under $30`, sent one at a time to the live service with the cache off (`AI201_CACHE=0`, so every run made real model calls). That is phase A of after-run 3, 2026-11-18 22:38 to 22:41 UTC. The numbers come from each request's own log record: `tokens` is the difference in `generate.token_counts()["total"]` before and after the run, and `total_ms` is the time inside `run_agent`.

| Run | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | Mean |
|---|---|---|---|---|---|---|---|---|---|---|---|
| Tokens | 859 | 866 | 842 | 843 | 848 | 833 | 848 | 837 | 842 | 880 | **849.8** |
| `total_ms` | 18,823 | 5,921 | 5,504 | 6,043 | 6,319 | 5,681 | 5,548 | 21,940 | 6,837 | 5,846 | **8,846** |

Every one of the ten made exactly 2 model calls. Runs 1 and 8 are slow outliers (the first came right after a restart), so the median time is 5,982 ms (about 6.0 s) while the mean is 8.8 s. As a cross-check, the 20 clean matching runs of after-runs 3 and 4 average 850.05 tokens and 8,341 ms.

**Cost of one run.** About **850 tokens and 8.8 seconds of compute**, with two model calls. The log only keeps the total, not the split between input and output tokens, so I price it as a range. With Gemini 3.5 Flash-Lite at $0.30 per million input tokens and $2.50 per million output tokens (from third-party price pages, not checked against Google's own page):

- All tokens at the input price: 849.8 × $0.30 / 1,000,000 = **$0.000255** per run
- All tokens at the output price: 849.8 × $2.50 / 1,000,000 = **$0.002125** per run

The real cost is somewhere between those. During my testing it was $0, because I was on the free tier.

**For a hundred people a day.** I assume each person runs 5 searches a day, so 100 × 5 = 500 runs a day.

- Model: 500 × $0.000255 = $0.13 a day and 500 × $0.002125 = $1.06 a day, so about **$3.82 to $31.87 for a 30-day month**.
- Hosting: the free instance sleeps and restarts, so I would pay for a $7 a month Starter instance (also a third-party figure).
- Compute: 500 × 8.846 s = 4,423 s, about 74 minutes a day, so one worker doing one request at a time is busy about 5% of the day.

That makes **about $11 to $39 a month in total** ($7 + $3.82, and $7 + $31.87), and the Gemini free tier's per-minute limit of 15 requests (two per run) is not a problem at 500 runs a day spread out.

## What's Still Broken

Criteria 1, 4 and 5 are still MISSED in the after-set. Criteria 2 and 3 were MET.

- **Criterion 1 (warm query completes 5 of 5), still missed: 5, 0, 5, 5.** What I'd do: find out whether the restarts are a free-tier behavior. I would run the same three trials on a paid instance, and add a client-side retry with a short wait on a 502. I stopped because the cause isn't visible from inside the app (the Events tab showed nothing and the log shows only Render's SIGTERM), and each experiment needs a deploy plus a log export, which is where the time of this unit went.
- **Criterion 4 (complete record for every request), still missed: 0, 0, 10, 10.** The part that was my code is fixed. What is left is structural: a request that Render answers with a 502 never reaches my app, so my app can't log it. What I'd do is keep a client-side log (what `run_live_test.py` already does) or put a logging layer in front of the service. I stopped because that is a different system from the one I scoped. I'd also look into why one record and one boot line were missing from the exports.
- **Criterion 5 (cost counters real), still missed: 10, 0, 10, 10.** The counters are correct in every record that exists. It missed because run 2 happened entirely during a restart, so the fix is the same as for criterion 1.
- **Targets set too low (criteria 2 and 3, both met).** The latency target was loose: I set a median of 15,000 ms and a maximum of 60,000 ms, and the worst median I saw was 8,563 ms and the worst maximum 21,940 ms. I'd tighten it to a median of 10,000 ms and a maximum of 30,000 ms. The wake-up target of 90 s was also loose against 41 to 46 s measured, and I'd tighten it to 60 s. Each was measured once or twice, so I'd also run the cold start more than once before trusting 60 s.

**What I'd do next.** The first thing is to move the service to a paid instance for a day and rerun the same three trials, because that tells me whether the 502s come from the free tier or from my app, and every miss that is left depends on that answer. Until I know that, any further work on logging or retries is aimed at a cause I haven't identified.

## How I Used AI

*(This is for the deploy-and-instrument capstone. The earlier project's section is above and unchanged.)*

**Moment 1: Scope against the real code.**
- *What I asked for:* to build the deploy-and-instrument extension I had scoped, with a README paragraph saying the MCP move was out of scope and that I'd deploy the direct-call path.
- *What came back:* before writing anything, Claude read `agent.py` and found that `run_agent` already searched through MCP (`mcp_client.call_tool`), so my scope bullet was wrong. It asked me whether to deploy that as it was or revert it.
- *What I changed:* I chose to deploy as-is and only time it. Claude corrected the out-of-scope bullet (commit `7bfe738`) and timed the MCP step by wrapping `agent.call_tool` in `serve.py` instead of editing `agent.py`.

**Moment 2: The cache I thought was off.**
- *What I asked for:* a live test of five criteria against the deployed service, with the cache off so each run made real model calls.
- *What came back:* the first service's `/metrics` showed 2 model calls and 102 cache hits after 59 requests, and matching runs took the same 5 seconds as the no-match query. Claude traced it to my deploy: I had created the service by hand, so `render.yaml` and its `AI201_CACHE=0` were never applied.
- *What I changed:* I deleted that service and recreated it as a Blueprint, kept the old results as `results/old_service_run1-3.json` to show the difference, and reran everything.

**Moment 3: A wrong diagnosis, withdrawn.**
- *What I asked for:* why runs 3 and 4 returned 502.
- *What came back:* Claude first guessed the 512 MB memory limit, because each request starts a second Python process for the MCP search. When I exported the logs, they showed a graceful `Handling signal: term` followed by `Instance ... restarted`, which is not what an out-of-memory kill looks like.
- *What I changed:* I dropped the memory explanation and wrote in the README that the cause of the restarts is unknown. I did not claim a mechanism I couldn't show.

**Moment 4: Following my own instructions.**
- *What I asked for:* a fresh clone of my repo, following `RUNNING.md` alone.
- *What came back:* it failed twice: plain `python` on my machine is 3.14.0, which the pinned packages don't support, and `.env.example` holds a placeholder key. Neither was in my instructions.
- *What I changed:* I added both to `RUNNING.md`, then rebuilt the environment with a 3.13 interpreter and confirmed `test.py` passes 10 of 10 and `serve.py` answers a request.

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
