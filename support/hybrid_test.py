"""
hybrid_test.py  --  show what the router decides, and what it would cost.

    python support/hybrid_test.py

Works with or without an API key. Without one it shows the routing decisions
only; with one it also shows Claude's actual answers and the real accuracy.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from chat import Bot
from realtest import FRESH
from router import Router, TRUST_LOCAL, MAX_UNKNOWN
import llm
import data

# Rough per-message cost. Classification sends ~700 input tokens (the intent
# list, cached after the first call) and returns ~60 output tokens.
PRICES = {"claude-opus-5-5": (4.00, 20.00), "claude-sonnet-5-5": (2.00, 10.00),
          "claude-haiku-4-5": (1.00, 5.00)}
IN_TOK, OUT_TOK = 700, 60


def cost_per_call(model):
    pin, pout = PRICES.get(model, PRICES["claude-opus-5-5"])
    return (IN_TOK / 1_000_000) * pin + (OUT_TOK / 1_000_000) * pout


bot = Bot()
r = Router(bot, debug=False)

print("=" * 72)
print(f"ROUTING RULE: keep local if confidence >= {TRUST_LOCAL:.0%} AND unknown words <= {MAX_UNKNOWN:.0%}")
print(f"API key present: {'yes - Claude will actually be asked' if llm.HAS_KEY else 'NO - showing routing only'}")
print("=" * 72)

print("\n--- 15 HAND-WRITTEN MESSAGES (the hard ones) ---\n")
print(f"{'message':<44} {'local':<22} {'route':<8} {'unknown words'}")
print("-" * 108)
sent, kept, kept_wrong = 0, 0, 0
for text, expected in FRESH:
    if expected == "OUT_OF_SCOPE":
        continue
    li, ls = bot.guess(text)[0]
    unk = r.unknown_words(text)
    goes_local = ls >= TRUST_LOCAL and r.unknown_share(text) <= MAX_UNKNOWN
    if goes_local:
        kept += 1
        if li != expected:
            kept_wrong += 1
    else:
        sent += 1
    print(f"{text[:42]:<44} {li[:20]:<22} {'LOCAL' if goes_local else 'CLAUDE':<8} {', '.join(unk[:4])}")

print("-" * 108)
print(f"\n  kept local : {kept}   (wrong answers kept: {kept_wrong})")
print(f"  to Claude  : {sent}")

print("\n--- 400 ORDINARY MESSAGES (normal customer wording) ---\n")
sample = data.load("balanced").sample(400, random_state=1).utterance.tolist()
free = sum(1 for t in sample
           if bot.guess(t)[0][1] >= TRUST_LOCAL and r.unknown_share(t) <= MAX_UNKNOWN)
print(f"  answered locally, no cost : {free} of 400  ({free/4:.0f}%)")
print(f"  sent to Claude            : {400-free} of 400")

print("\n" + "=" * 72)
print("WHAT IT WOULD COST")
print("=" * 72)
print("""
  Careful with the 100% above: those 400 messages came from the training data
  itself, so of course every word is known. Real customers write differently.
  The honest answer is that the paid share sits somewhere between the two
  extremes you just saw, so here is a range.
""")
print(f"  {'model':<20}" + "".join(f"{p:>12}" for p in ("10% paid", "30% paid", "50% paid")))
print("  " + "-" * 56)
for m in PRICES:
    c = cost_per_call(m)
    row = "".join(f"{'$' + format(c * 10000 * sh, '.2f'):>12}" for sh in (0.10, 0.30, 0.50))
    print(f"  {m:<20}{row}")
print("")
print("  (per 10,000 customer messages)")
print("")
print("  Even at 50% paid, Haiku costs $5 per 10,000 messages. Repeat wording")
print("  is cached in the database, so the real bill is lower again.")

if llm.HAS_KEY:
    print("\n" + "=" * 72)
    print("ASKING CLAUDE FOR REAL")
    print("=" * 72 + "\n")
    right = wrong = 0
    for text, expected in FRESH:
        if expected == "OUT_OF_SCOPE":
            continue
        if bot.guess(text)[0][1] >= TRUST_LOCAL and r.unknown_share(text) <= MAX_UNKNOWN:
            continue
        got = llm.classify(text)
        if got is None:
            print(f"  {text[:40]:<42} -> no answer"); continue
        ok = got[0] == expected
        right, wrong = right + ok, wrong + (not ok)
        print(f"  {'OK ' if ok else 'BAD'} {text[:38]:<40} -> {got[0]:<24} ({got[1]:.0%})")
    total = right + wrong
    if total:
        print(f"\n  Claude got {right} of {total} right ({right/total:.0%}).")
        print(f"  The local model alone managed 40% on these.")
else:
    print("\n  Add ANTHROPIC_API_KEY to .env to see Claude's real answers and accuracy.")
