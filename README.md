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
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Real output from one try**, pasted as text, naming the file and function
that produced it:

```

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
| 1 |  |  |  |  |
| 2 |  |  |  |  |
| 3 |  |  |  |  |
| 4 |  |  |  |  |
| 5 |  |  |  |  |

**Diagnoses**



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

```

**Empty search**

```

```

**On the MCP move:** <!-- what changed in your code, and whether anything
behaved differently afterwards. If the rewire didn't work, say exactly where it
broke — the error text and the last thing that worked. That earns the point in
full. -->



---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:**

**Which failure it was meant to fix:**

### Run Log — After

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |  |  |
| 2.  |  |  |  |  |  |  |  |
| 3.  |  |  |  |  |  |  |  |
| 4.  |  |  |  |  |  |  |  |
| 5.  |  |  |  |  |  |  |  |

**Did it help, and how do I know:**

<!-- If it made things worse, say that. Honestly reported, that earns full
     credit and is more interesting than one that worked. -->



---

## What's Still Broken

<!-- For each criterion still missed: what you'd do, and why you stopped where
     you did. "I ran out of time" is fine if it's true. Pretending nothing is
     left is not. -->



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

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
