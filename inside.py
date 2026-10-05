"""
inside.py  --  open the trained model and look at how it works.
"""
import numpy as np, joblib
import data

b = joblib.load("model.joblib")
model = b["model"]
union = model.named_steps["featureunion"]
words = dict(union.transformer_list)["words"]
letters = dict(union.transformer_list)["letters"]
clf = model.named_steps["calibratedclassifiercv"]

print("=" * 68)
print("STEP 1: TURN A SENTENCE INTO NUMBERS")
print("=" * 68)
print(f"\n  word columns   : {len(words.vocabulary_):>7}   (single words + word pairs)")
print(f"  letter columns : {len(letters.vocabulary_):>7}   (3-5 letter chunks)")
total = len(words.vocabulary_) + len(letters.vocabulary_)
print(f"  TOTAL columns  : {total:>7}")

s = "i want to cancel my order"
print(f"\n  Example sentence: \"{s}\"")
v = model.named_steps["featureunion"].transform([s])
print(f"  Becomes a row of {v.shape[1]} numbers.")
print(f"  Only {v.nnz} of them are not zero. The rest are 0.")

print("\n  The non-zero WORD columns (and their weight):")
wv = words.transform([s]); names = words.get_feature_names_out()
idx = wv.nonzero()[1]
for i in sorted(idx, key=lambda i: -wv[0, i])[:10]:
    print(f"      {names[i]:<22} {wv[0, i]:.3f}")

print("\n  A few non-zero LETTER columns (this is the typo insurance):")
lv = letters.transform([s]); lnames = letters.get_feature_names_out()
lidx = lv.nonzero()[1]
for i in sorted(lidx, key=lambda i: -lv[0, i])[:8]:
    print(f"      {repr(lnames[i]):<22} {lv[0, i]:.3f}")

print("\n" + "=" * 68)
print("STEP 2: THE TYPO TEST")
print("=" * 68)
pairs = [("cancel my order", "cancle my ordr"), ("track my refund", "trak my refnud")]
for good, typo in pairs:
    a = model.predict_proba([good])[0]; c = model.predict_proba([typo])[0]
    ga, gc = model.classes_[a.argmax()], model.classes_[c.argmax()]
    print(f"\n  \"{good}\"  -> {ga} ({a.max():.0%})")
    print(f"  \"{typo}\"  -> {gc} ({c.max():.0%})")
    print(f"      same answer? {'YES - the letter chunks saved it' if ga == gc else 'no'}")

print("\n" + "=" * 68)
print("STEP 3: WHICH WORDS PUSH TOWARDS WHICH INTENT")
print("=" * 68)
# average the weights across the calibrated folds
inner = [c.estimator for c in clf.calibrated_classifiers_]
W = np.mean([e.coef_ for e in inner], axis=0)
allnames = np.concatenate([names, lnames])
for intent in ["cancel_order", "recover_password", "payment_issue", "complaint"]:
    row = W[list(model.classes_).index(intent)]
    top = np.argsort(row)[::-1][:8]
    print(f"\n  {intent}")
    print("      " + " | ".join(repr(allnames[i]).strip("'\"") for i in top))

print("\n" + "=" * 68)
print("STEP 4: THE FINAL SCORES FOR ONE SENTENCE")
print("=" * 68)
p = model.predict_proba([s])[0]
print(f"\n  \"{s}\"\n")
for i in p.argsort()[::-1][:5]:
    bar = "#" * round(p[i] * 40)
    print(f"      {model.classes_[i]:<26} {p[i]:>6.1%}  {bar}")
print(f"\n  All 27 scores add up to {p.sum():.2f}. The bot picks the biggest,")
print(f"  but only if it is above the 40% threshold set in chat.py.")
