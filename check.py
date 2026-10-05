"""
check.py  --  is this data clean?

Runs the checks one by one and says PASS or PROBLEM for each.
"""
import re, sys
from collections import Counter
import pandas as pd
import data

results = []
def report(name, ok, detail=""):
    results.append(ok)
    mark = "PASS   " if ok else "PROBLEM"
    print(f"\n[{mark}] {name}")
    if detail:
        print(detail)

which = "big" if "--big" in sys.argv else "balanced"
raw_path = data.FILE_A if which == "big" else data.FILE_B
df = pd.read_csv(raw_path, encoding="utf-8-sig")   # raw, before any cleaning
print("=" * 64)
print(f"CHECKING THE '{which}' FILE   ({len(df)} rows, before any cleaning)")
print("=" * 64)

# ---------------------------------------------------------------- 1
miss = df.isna().sum()
report("1. Any empty boxes?", miss.sum() == 0,
       "   Every row has all 4 values filled in." if miss.sum() == 0
       else f"   {miss.to_dict()}")

# ---------------------------------------------------------------- 2
blank = (df["utterance"].astype(str).str.strip() == "").sum()
report("2. Any blank sentences?", blank == 0,
       "   No sentence is empty or only spaces." if blank == 0 else f"   {blank} blank")

# ---------------------------------------------------------------- 3
dup_rows = int(df.duplicated().sum())
dup_utt = int(df.duplicated(subset=["utterance"]).sum())
report("3. Any repeated rows?", dup_rows == 0,
       "   No row is an exact copy of another." if dup_rows == 0
       else f"   {dup_rows} rows are exact copies.\n   {dup_utt} sentences appear more than once.")

# ---------------------------------------------------------------- 4  (the dangerous one)
conflict = df.groupby(df["utterance"].str.strip().str.lower())["intent"].nunique()
bad = conflict[conflict > 1]
if len(bad) == 0:
    report("4. Same sentence given two different labels?", True,
           "   No sentence is labelled two different ways. This is the\n"
           "   most important check, and the data passes it.")
else:
    lines = []
    for utt in bad.index[:5]:
        labs = df[df["utterance"].str.strip().str.lower() == utt]["intent"].unique()
        lines.append(f"   \"{utt}\"\n       labelled as: {', '.join(labs)}")
    report("4. Same sentence given two different labels?", False,
           f"   {len(bad)} sentences have conflicting labels. Examples:\n" + "\n".join(lines))

# ---------------------------------------------------------------- 5
pairs = df.groupby("intent")["category"].nunique()
report("5. Does each intent always sit in the same category?", (pairs == 1).all(),
       "   Yes. The category/intent structure is consistent." if (pairs == 1).all()
       else f"   {(pairs>1).sum()} intents appear under more than one category.")

# ---------------------------------------------------------------- 6
DOC = set("BSLMICPQWEDZK")
used = Counter(ch for s in df["flags"].astype(str) for ch in s)
undoc = {c: n for c, n in used.items() if c not in DOC}
report("6. Are all flag letters explained in the manual?", not undoc,
       "   Every letter used is described in the README." if not undoc
       else f"   These letters are used but never explained: {undoc}\n"
            "   Small issue, but it means the README is not complete.")

# ---------------------------------------------------------------- 7
weird = df[df["utterance"].astype(str).str.contains(r"[^\x00-\x7F]", regex=True)]
report("7. Any strange or broken characters?", len(weird) == 0,
       "   All text is plain English letters. No broken symbols." if len(weird) == 0
       else f"   {len(weird)} rows contain non-English characters, e.g.\n"
            + "\n".join("     " + u for u in weird["utterance"].head(3)))

# ---------------------------------------------------------------- 8
dbl = df["utterance"].astype(str).str.contains("  ").sum()
edge = (df["utterance"].astype(str) != df["utterance"].astype(str).str.strip()).sum()
report("8. Untidy spacing?", dbl == 0 and edge == 0,
       "   No double spaces, no spaces at the start or end." if dbl == 0 and edge == 0
       else f"   {dbl} rows have a double space inside.\n   {edge} rows have spaces at the start or end.\n"
            "   Harmless, but tidy it before training.")

# ---------------------------------------------------------------- 9
counts = df["intent"].value_counts()
ratio = counts.max() / counts.min()
report("9. Is each intent given a fair amount of data?", ratio <= 3,
       f"   Biggest {counts.max()}, smallest {counts.min()}. Ratio {ratio:.0f} to 1. Fine."
       if ratio <= 3 else
       f"   Biggest intent: {counts.idxmax()} with {counts.max()} rows\n"
       f"   Smallest intent: {counts.idxmin()} with {counts.min()} rows\n"
       f"   That is {ratio:.0f} times more. The model will be weak on the small ones.")

# ---------------------------------------------------------------- 10  (the real issue)
def skeleton(s):
    """Strip out the small words so near-copies collapse together."""
    s = re.sub(r"[^a-z ]", "", str(s).lower())
    stop = {"i","a","the","to","my","me","can","you","do","how","is","it","of","for",
            "please","could","need","want","help","with","have","am","are","on","an","that","this"}
    return " ".join(sorted(w for w in s.split() if w not in stop))

sk = df["utterance"].map(skeleton)
n_unique = sk.nunique()
copy_rate = 1 - n_unique / len(df)
report("10. Are the sentences genuinely different from each other?", copy_rate < 0.15,
       f"   {n_unique} truly different sentences out of {len(df)} rows.\n"
       f"   That means {copy_rate:.0%} of rows are near-copies of another row.\n"
       "   THIS IS THE BIG ONE. The data was made by a machine from templates.\n"
       "   Near-copies land in both the practice set and the exam set, so the\n"
       "   exam score looks far better than the bot really is.")
top = Counter(sk).most_common(3)
print("   The most repeated shapes:")
for shape, n in top:
    ex = df[sk == shape]["utterance"].head(3).tolist()
    print(f"     appears {n} times, e.g.")
    for e in ex:
        print(f"       - {e}")

# ---------------------------------------------------------------- summary
print("\n" + "=" * 64)
ok = sum(results); tot = len(results)
print(f"RESULT: {ok} of {tot} checks passed.")
print("=" * 64)
