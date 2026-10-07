"""
The three FitFindr tools.

Each one is a standalone function you can call and test on its own, before any
of them are wired into the loop. Build and test them one at a time — three
untested tools joined by a loop is one problem that looks like six, because you
can't tell which layer is lying to you.

    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)             → str
    create_fit_card(outfit, new_item)              → str

All three are stubs right now. They run and they do nothing — that's the
starting position and it's deliberate.

⚠️ Before you write any of them, fill in the **Tool Inventory** section of your
README (Milestone 2). Four lines per tool: what it does, each input with its
type, exactly what it returns, and what it returns when it has nothing to give.
That last line is what your loop branches on. "Returns a list" earns nothing —
the description has to say what is *in* the list.
"""

import re

import config
from generate import generate
from utils.data_loader import load_listings


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the listings data for items matching a description, and optionally a
    size and a price ceiling.

    This is the tool that doesn't call the model, which makes it the easiest one
    to test and the one to move onto MCP in unit 4.

    Args:
        description: keywords describing what the user wants
                     (e.g. "vintage graphic tee").
        size:        a size string to filter by, or None to skip size filtering.
                     Match case-insensitively — "M" should match "S/M".

                     ⚠️ Read the sizes in the data before you reach for a plain
                     substring test. `"s" in "us 9"` is True, and so is
                     `"l" in "xl"`. A filter that returns shoes when someone
                     asked for a small top reads like a broken search, and it
                     will quietly cost you in unit 4 when you test criterion 1.
                     What counts as a size match is part of your spec — decide
                     it and write it into your Tool Inventory.
        max_price:   maximum price, inclusive, or None to skip price filtering.

    Returns:
        A list of matching listing dicts, best match first.
        **Returns an empty list when nothing matches — an empty list, not None,
        and not an exception.** Your loop branches on this.

    Each listing dict has these fields:
        id, title, description, category, style_tags (list), size,
        condition, price (float), colors (list), brand (str or None), platform

    Note that `brand` is None for most listings. That is deliberate and
    realistic — thrift listings often have no brand. If something you write
    assumes a brand is always there, you will find out in unit 4.

    TODO:
        1. Load every listing with load_listings().
        2. Filter by max_price and by size, when each is provided.
        3. Score what's left by keyword overlap with `description`.
        4. Drop anything scoring zero.
        5. Sort by score, highest first, and return the listing dicts —
           at most config.SEARCH_RESULT_LIMIT of them.

    Test it from a terminal before you move on:
        python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
    """
    keywords = {w for w in _words(description) if w not in _STOPWORDS}
    wanted_size = size.strip().lower() if size and size.strip() else None

    scored = []
    for listing in load_listings():
        if max_price is not None and listing["price"] > max_price:
            continue
        if wanted_size and not _size_matches(wanted_size, listing["size"]):
            continue
        score = len(keywords & _listing_words(listing))
        if score > 0:
            # Title hits break ties: a title is a better signal than a description.
            title_hits = len(keywords & set(_words(listing["title"])))
            scored.append(((score, title_hits), listing))

    # sorted() is stable, so remaining ties keep their order in the data file.
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [listing for _, listing in scored[: config.SEARCH_RESULT_LIMIT]]


_STOPWORDS = {
    "a", "an", "and", "the", "for", "in", "of", "on", "or", "to", "with",
    "i", "me", "my", "want", "looking", "need", "find", "some", "under",
    "size", "below", "than", "less",
}


def _words(text: str) -> list[str]:
    """Lowercase alphanumeric words — 'Y2K-style' becomes ['y2k', 'style']."""
    return re.findall(r"[a-z0-9]+", (text or "").lower())


def _listing_words(listing: dict) -> set[str]:
    parts = [
        listing.get("title"),
        listing.get("description"),
        listing.get("category"),
        listing.get("brand"),          # None for most listings
        *(listing.get("style_tags") or []),
        *(listing.get("colors") or []),
    ]
    return {w for part in parts for w in _words(part)}


def _size_matches(wanted: str, listing_size: str) -> bool:
    """
    Whole-token size match. Parentheticals are dropped, then the size is split
    on '/' and whitespace, so 'S' matches 'S/M' but not 'US 9' or 'XL'.
    """
    cleaned = re.sub(r"\(.*?\)", " ", listing_size.lower())
    tokens = {t for part in cleaned.split("/") for t in part.split()}
    # "one size" is two tokens but one size; accept it as a whole too.
    tokens |= {part.strip() for part in cleaned.split("/")}
    return wanted in tokens



# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest one or two outfits.

    This one calls the model, through `generate()`. You don't need to think
    about rate limits — the adapter handles pacing for you.

    Args:
        new_item: a listing dict — the item the user is considering.
        wardrobe: a wardrobe dict with an 'items' key holding a list of items.
                  **It may be empty.** Handle that.

    Returns:
        A non-empty string with outfit suggestions.
        With an empty wardrobe, return general styling advice rather than
        raising or returning "". Unit 4 has you trigger the empty wardrobe on
        purpose, so decide now what it should do.

    TODO:
        1. Check whether wardrobe['items'] is empty.
        2. If it is, ask the model for general styling ideas for this item.
        3. If it isn't, format the wardrobe items into the prompt and ask for
           specific combinations naming pieces the user already owns.
        4. Return the model's response.

    Test it from a terminal before you move on:
        python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
    """
    item_text = _describe_item(new_item)
    items = (wardrobe or {}).get("items") or []

    if not items:
        prompt = (
            f"Someone is thinking of buying this thrifted piece:\n{item_text}\n\n"
            "They haven't told me what's in their wardrobe. Suggest one or two "
            "outfits built around it, using common basics anyone might own "
            "(for example plain jeans, white sneakers). Be specific about the "
            "pieces and the vibe, and keep it under 120 words."
        )
    else:
        owned = "\n".join(_describe_wardrobe_item(w) for w in items)
        prompt = (
            f"Someone is thinking of buying this thrifted piece:\n{item_text}\n\n"
            f"Here is their wardrobe:\n{owned}\n\n"
            "Suggest one or two outfits that combine the new piece with items "
            "they already own. Name the wardrobe items exactly as listed. Do "
            "not invent pieces they don't have. Keep it under 120 words."
        )

    outfit = generate(
        prompt,
        system="You are a friendly, specific secondhand-fashion stylist.",
    )
    return outfit or "Pair it with simple basics — straight-leg jeans and clean sneakers let the piece do the talking."


def _describe_item(item: dict) -> str:
    brand = f", brand: {item['brand']}" if item.get("brand") else ""
    return (
        f"{item.get('title')} ({item.get('category')}, size {item.get('size')}, "
        f"colors: {', '.join(item.get('colors') or [])}, "
        f"style: {', '.join(item.get('style_tags') or [])}{brand})"
    )


def _describe_wardrobe_item(w: dict) -> str:
    note = f" — {w['notes']}" if w.get("notes") else ""
    return (
        f"- {w.get('name')} ({w.get('category')}, "
        f"colors: {', '.join(w.get('colors') or [])}){note}"
    )


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Write a short caption someone would actually post about the find.

    This calls the model too.

    Args:
        outfit:   the outfit suggestion string from suggest_outfit().
        new_item: the listing dict for the item.

    Returns:
        A two-to-four sentence caption.
        If `outfit` is empty or whitespace, return a descriptive message rather
        than raising.

    The caption should read like a real post rather than a product description,
    mention the item and its price and platform once each, and be specific about
    the vibe.

    It should also come out **differently for different inputs**. If you run
    this three times on the same item and get three word-for-word identical
    strings, it's one of two things, and both are near the top of `config.py`:

        • CACHE_ENABLED — the adapter handed back an answer it already had
        • TEMPERATURE   — at 0.0 the model gives the same words every time

    TODO:
        1. Guard against an empty or whitespace-only `outfit`.
        2. Build a prompt with the item details and the outfit.
        3. Call generate() and return the response.

    Test it from a terminal before you move on:
        python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
    """
    if not outfit or not outfit.strip():
        return "No outfit to write a caption for — run suggest_outfit first."

    prompt = (
        "Write a caption someone would actually post about a thrift find.\n\n"
        f"The find: {new_item.get('title')}, ${new_item.get('price'):.2f} on "
        f"{new_item.get('platform')}.\n"
        f"The outfit idea: {outfit}\n\n"
        "Rules: two to four sentences. Mention the item, its price and the "
        "platform once each. Be specific about the vibe. Sound like a person "
        "posting, not a product description. Don't use hashtags or a "
        "greeting like 'Hey guys'."
    )
    return generate(prompt, system="You write short, natural social-media captions.")
