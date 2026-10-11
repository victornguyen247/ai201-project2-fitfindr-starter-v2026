import sys
sys.path.insert(0, ".")
import config
config.CACHE_ENABLED = False
import agent
from utils.data_loader import get_example_wardrobe

real_outfit, real_card = agent.suggest_outfit, agent.create_fit_card
seen = {}
def wrap_outfit(item, wardrobe):
    seen["outfit"] = item["id"]
    return real_outfit(item, wardrobe)
def wrap_card(outfit, item):
    seen["card"] = item["id"]
    return real_card(outfit, item)
agent.suggest_outfit, agent.create_fit_card = wrap_outfit, wrap_card

for n in range(1, 6):
    seen.clear()
    s = agent.run_agent("denim jacket under $50", get_example_wardrobe())
    sel, first = s["selected_item"], s["search_results"][0]
    ok = seen["outfit"] == sel["id"] == first["id"] == seen["card"]
    card = s["fit_card"]
    names = sel["title"].split(" — ")[0].lower() in card.lower() or f"${sel['price']:.0f}" in card
    print(f"try {n}: suggest_outfit={seen['outfit']} selected={sel['id']} results[0]={first['id']} create_fit_card={seen['card']} -> {'PASS' if ok and names else 'FAIL'}")
