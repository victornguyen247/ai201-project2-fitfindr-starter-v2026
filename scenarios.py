"""
The runs your test needs. ← UNIT 4, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
the empty-search branch needs an impossible query. One about the fit card needs
the same item run more than once. Working that out is Milestone 3's first step,
and this file is where you write it down.

`run_eval.py` runs everything here five times and writes the run log — five
because your criteria are written out of five.

Three scenarios are filled in to show the shape. Add or change whatever your
own criteria need — these are a starting point, not a fixed set.
"""

SCENARIOS = [
    {
        # A query the data can match. Criterion 1.
        "name": "matching query completes",
        "query": "vintage graphic tee under $30",
        "wardrobe": "example",
        "criterion": 1,
    },
    {
        # A query nothing can match. Criterion 2 — the branch.
        "name": "impossible query stops early",
        "query": "designer ballgown size XXS under $5",
        "wardrobe": "example",
        "criterion": 2,
    },
    # Criterion 3 — state. Any matching query works; what gets checked is the
    # id that reaches suggest_outfit == session["selected_item"]["id"] ==
    # search_results[0]["id"] == the id that reaches create_fit_card.
    # Top result is lst_007.
    {
        "name": "item id carries through the session",
        "query": "denim jacket under $50",
        "wardrobe": "example",
        "criterion": 3,
    },
    # Criterion 4 — fit card. ONE item (lst_002, $18, depop) run five times, so
    # the five tries give five cards of the same item: each is checked for
    # 2-4 sentences, the price and the platform, and no two may share a first
    # sentence.
    {
        "name": "fit card for one item, five tries",
        "query": "y2k baby tee under $20",
        "wardrobe": "example",
        "criterion": 4,
    },
    # Criterion 5 — price + size filter. One query carrying a size and a
    # max_price, with a single-letter size so the substring trap is exercised:
    # no XL item may come back for "L". Returns 5 listings, all price <= 45.
    {
        "name": "price and size filter holds",
        "query": "vintage size L under $45",
        "wardrobe": "example",
        "criterion": 5,
    },
]

WARDROBES = ("example", "empty")


def validate() -> list[str]:
    """Complain about anything malformed, before a long run rather than during."""
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("query", "").strip():
            problems.append(f"scenario {i} has no query")
        if scenario.get("wardrobe") not in WARDROBES:
            problems.append(
                f"scenario {i} has wardrobe {scenario.get('wardrobe')!r} — "
                f"it should be one of {WARDROBES}"
            )
    return problems
