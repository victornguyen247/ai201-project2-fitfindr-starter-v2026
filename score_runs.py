"""Score a run log from results/ against the criteria. Usage: python score_runs.py results/run_X.md"""
import re, sys

def load(path):
    t = open(path).read()
    out = {}
    for sec in re.split(r"\n### ", t)[1:]:
        name = sec.split("\n")[0]
        q = re.search(r"Query: `(.*?)`", sec).group(1)
        tries = []
        for tr in re.split(r"\n\*\*Try \d\*\*\n", sec)[1:]:
            card = re.search(r"Fit card:\n\n```\n(.*?)\n```", tr, re.S)
            item = re.search(r"selected_item: .*?\(\$([\d.]+), (\w+)\)", tr)
            steps = re.findall(r"^\[\d\] (.+)$", tr.split("Trace:")[-1], re.M)
            err = re.search(r"stopped early: yes — (.*)", tr)
            n = re.search(r"search_results: (\d+)", tr)
            tries.append(dict(card=card.group(1) if card else None,
                              price=float(item.group(1)) if item else None,
                              platform=item.group(2) if item else None,
                              steps=steps, err=err.group(1) if err else None,
                              n=int(n.group(1)) if n else 0))
        out[name] = (q, tries)
    return out

def sentences(card):
    return [s for s in re.split(r"(?<=[.!?])\s+", card.strip()) if s]

def card_ok(t):
    c = t["card"]
    if not c: return False, False, False, False
    s = sentences(c)
    digits = f"${t['price']:.0f}" in c
    return (2 <= len(s) <= 4), digits, t["platform"].lower() in c.lower(), True

def main(path):
    d = load(path)
    print("==", path)
    allcards = []
    for name, (q, tries) in d.items():
        if name.startswith("matching"):
            print("C1", sum(1 for t in tries if t["card"] and not t["err"]), "/5")
        elif name.startswith("impossible"):
            print("C2", sum(1 for t in tries if t["err"] and "suggest_outfit" not in t["steps"] and "create_fit_card" not in t["steps"]), "/5")
        elif name.startswith("fit card"):
            res = [card_ok(t) for t in tries]
            passes = sum(1 for a, b, c, _ in res if a and b and c)
            firsts = [sentences(t["card"])[0] for t in tries]
            four = [" ".join(f.lower().split()[:4]) for f in firsts]
            print("C4 cards passing (sentences, $digits, platform):", passes, "/5;",
                  "distinct first sentences:", len(set(firsts)), "/5;",
                  "distinct first-4-words:", len(set(four)), "/5")
            for f in firsts: print("    ", f)
        for t in tries:
            if t["card"]: allcards.append((name, card_ok(t), t))
    dig = sum(1 for _, r, _ in allcards if r[1])
    print(f"price written as digits across ALL {len(allcards)} fit cards in the log: {dig}/{len(allcards)}")
    for name, r, t in allcards:
        if not r[1]: print("   no $ digits:", name, "|", sentences(t["card"])[0])
    opens = [" ".join(t["card"].lower().split()[:2]) for _, _, t in allcards]
    print("cards starting 'scored this' / 'found the|this':", sum(1 for o in opens if o in ("scored this", "found this", "found the")), "/", len(opens))

main(sys.argv[1])
