"""
explore.py  --  look at the data before training anything.

Run it plain:            python explore.py
Look at one intent:      python explore.py get_refund
Use the big file:        python explore.py --big
"""

import sys
from collections import Counter
import data

FLAG_MEANING = {
    "B": "basic sentence",       "I": "a question",         "L": "different words, same meaning",
    "M": "plural / past tense",  "C": "long, two-part sentence", "P": "polite",
    "Q": "casual / slang",       "E": "no short forms (do not, I am)", "Z": "spelling mistakes",
    "W": "rude words",           "D": "asks an agent to do it",  "K": "keywords only",
}


def line(title):
    print("\n" + "=" * 62)
    print(title)
    print("=" * 62)


def show_one_intent(df, name):
    rows = df[df.intent == name]
    if rows.empty:
        print(f"No intent called '{name}'. Try one of these:")
        print("  " + ", ".join(sorted(df.intent.unique())))
        return
    line(f"INTENT: {name}   (category: {rows.category.iloc[0]}, {len(rows)} rows)")
    print("\n20 examples of what customers say:\n")
    for i, r in enumerate(rows.rename(columns={"flags":"flg"}).sample(min(20, len(rows)), random_state=0).itertuples(), 1):
        print(f"  {i:2}. [{r.flg:<6}] {r.utterance}")


def show_overview(df):
    line("1. WHAT ONE ROW LOOKS LIKE")
    r = df.iloc[0]
    print(f"\n  utterance : {r.utterance}")
    print(f"  intent    : {r.intent}      <- what the customer wants")
    print(f"  category  : {r.category}      <- the bigger group")
    print(f"  flags     : {r['flags']}      <- the writing style")

    line("2. THE 11 CATEGORIES AND THE 27 INTENTS INSIDE THEM")
    for cat, g in df.groupby("category"):
        print(f"\n  {cat}  ({len(g)} rows)")
        for intent, gg in g.groupby("intent"):
            print(f"      {intent:<26} {len(gg):>5} rows")

    line("3. IS THE DATA FAIR? (rows per intent)")
    counts = df.intent.value_counts()
    biggest = counts.max()
    print()
    for intent, n in counts.items():
        bar = "#" * max(1, round(40 * n / biggest))
        print(f"  {intent:<26} {n:>5}  {bar}")
    print(f"\n  Biggest intent has {counts.max()} rows, smallest has {counts.min()} rows.")
    print(f"  That is {counts.max() / counts.min():.0f} times more.")
    if counts.max() / counts.min() > 3:
        print("  -> UNFAIR. The model will be weak on the small intents.")
    else:
        print("  -> Fair enough. Every intent gets a similar amount of practice.")

    line("4. WRITING STYLES (the flags column)")
    tally = Counter(ch for s in df["flags"] for ch in s)
    print()
    for ch, n in tally.most_common():
        pct = 100 * n / len(df)
        print(f"  {ch}  {FLAG_MEANING.get(ch, '(not in the manual)'):<36} {pct:5.1f}% of rows")

    line("5. THE SAME REQUEST, WRITTEN IN DIFFERENT STYLES")
    print("\n  All of these mean 'get_refund':\n")
    seen = set()
    for r in df[df.intent == "get_refund"].itertuples():
        key = "".join(sorted(set(r.flags) - {"B"}))
        if key not in seen and len(seen) < 8:
            seen.add(key)
            styles = ", ".join(FLAG_MEANING.get(c, c) for c in r.flags if c != "B") or "plain"
            print(f"  {r.utterance}")
            print(f"       -> {styles}\n")

    line("6. HOW LONG ARE THE SENTENCES?")
    words = df.utterance.str.split().str.len()
    print(f"\n  shortest: {words.min()} words, typical: {int(words.median())} words, longest: {words.max()} words")
    print(f"\n  shortest one : {df.loc[words.idxmin(), 'utterance']}")
    print(f"  longest one  : {df.loc[words.idxmax(), 'utterance']}")

    line("7. THE THING THE DATA DOES NOT HAVE")
    print("""
  There is NO reply from support staff anywhere in this data.
  Only the customer's words and a label.

  So this data can teach a bot to UNDERSTAND the question.
  It cannot teach the bot what to ANSWER. You write the answers yourself.
""")

    print("\nTip: look at one intent closely with:   python explore.py get_refund\n")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:]]
    which = "big" if "--big" in args else "balanced"
    args = [a for a in args if not a.startswith("--")]

    df = data.load(which)
    print(f"Loaded the '{which}' file: {len(df)} rows.")

    if args:
        show_one_intent(df, args[0])
    else:
        show_overview(df)
