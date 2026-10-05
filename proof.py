"""
proof.py  --  proves the 99.9% score is caused by near-copies.

We train the SAME model twice on the SAME data. The only difference is
HOW we split it into practice and exam.

  Split 1 (random)  : near-copies allowed on both sides  -> the usual way
  Split 2 (grouped) : all copies of one sentence kept on ONE side only
"""
import re
from collections import Counter
from sklearn.model_selection import train_test_split, GroupShuffleSplit
from sklearn.metrics import accuracy_score
import data
from train import build_model

STOP = {"i","a","the","to","my","me","can","you","do","how","is","it","of","for",
        "please","could","need","want","help","with","have","am","are","on","an","that","this"}

def skeleton(s):
    s = re.sub(r"[^a-z ]", "", str(s).lower())
    return " ".join(sorted(w for w in s.split() if w not in STOP))

df = data.load("balanced")
X, y = df["utterance"].values, df["intent"].values
groups = df["utterance"].map(skeleton).values
print(f"{len(df)} sentences, but only {len(set(groups))} truly different shapes.\n")

# ---- Split 1: the normal random way -------------------------------
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=.2, random_state=42, stratify=y)
m = build_model().fit(Xtr, ytr)
a1 = accuracy_score(yte, m.predict(Xte))
print(f"Split 1  RANDOM   : {a1*100:5.1f}% correct   <- the flattering number")

# ---- Split 2: keep each family of copies on one side only ----------
gss = GroupShuffleSplit(n_splits=1, test_size=.2, random_state=42)
tr, te = next(gss.split(X, y, groups))
m2 = build_model().fit(X[tr], y[tr])
a2 = accuracy_score(y[te], m2.predict(X[te]))
print(f"Split 2  GROUPED  : {a2*100:5.1f}% correct   <- the honest number")

print(f"\nSame model. Same data. The {(a1-a2)*100:.0f} point drop is pure leaking.")
print("In Split 1 the exam contained sentences the model had already")
print("practised on, just with a word or two changed.")
