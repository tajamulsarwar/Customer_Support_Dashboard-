"""
why.py  --  the REAL reason the bot fails on new sentences.

It is not leaking. It is vocabulary: the data uses a very small set of words.
"""
import re
from collections import Counter
import data
from realtest import FRESH

df = data.load("both")
def words(s): return set(re.findall(r"[a-z]+", str(s).lower()))

vocab = Counter(w for s in df["utterance"] for w in words(s))
print(f"{len(df)} sentences in total.")
print(f"But only {len(vocab)} different words are ever used.\n")
print("A normal English speaker uses 20,000+ words. This data uses under 2,000.")
print("That is the problem in one line.\n")

print("The 25 most used words:")
print("  " + ", ".join(w for w, _ in vocab.most_common(25)))

print("\n" + "=" * 66)
print("MY TEST SENTENCES: which words does the data NOT KNOW AT ALL?")
print("=" * 66)
for text, expected in FRESH:
    if expected == "OUT_OF_SCOPE":
        continue
    unknown = sorted(w for w in words(text) if w not in vocab)
    rare = sorted(w for w in words(text) if 0 < vocab.get(w, 0) < 10)
    if unknown or rare:
        print(f"\n  \"{text}\"")
        if unknown:
            print(f"      NEVER SEEN : {', '.join(unknown)}")
        if rare:
            print(f"      seen <10x  : {', '.join(rare)}")

print("\n" + "=" * 66)
print("PROOF: say the SAME thing using the data's own words")
print("=" * 66)
from chat import Bot
bot = Bot()
pairs = [
    ("i forgot my login details",        "I forgot my password"),
    ("my parcel still has not arrived",  "where is my order"),
    ("scrap my order i changed my mind", "I want to cancel my order"),
    ("this is the worst service ever",   "I want to file a complaint"),
    ("stop sending me emails",           "unsubscribe from the newsletter"),
]
print(f"\n  {'my wording':<36} {'->':<3} {'guess':<26} {'sure':>5}")
for mine, theirs in pairs:
    for label, s in (("MINE ", mine), ("THEIRS", theirs)):
        i, sc = bot.guess(s)[0]
        print(f"  {label} {s[:30]:<30} {'->':<3} {i:<26} {sc:>4.0%}")
    print()
