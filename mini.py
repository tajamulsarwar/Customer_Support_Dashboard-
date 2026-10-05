"""
mini.py  --  training, explained with only 6 sentences.

Same idea as train.py, just small enough to see every number.
Run:  python mini.py
"""
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
import pandas as pd

# Six sentences. Three mean "cancel", three mean "refund".
sentences = ["cancel my order",
             "please cancel the order",
             "i want to cancel",
             "i want a refund",
             "give me a refund",
             "refund my money"]
labels    = ["CANCEL", "CANCEL", "CANCEL", "REFUND", "REFUND", "REFUND"]

print("=" * 60)
print("WHAT WE START WITH")
print("=" * 60)
for s, l in zip(sentences, labels):
    print(f"   {s:<26} -> {l}")

print("\n" + "=" * 60)
print("STEP 1: MAKE A LIST OF EVERY WORD")
print("=" * 60)
v = TfidfVectorizer()
table = v.fit_transform(sentences)
words = v.get_feature_names_out()
print(f"\n   The computer found {len(words)} different words:")
print("   " + ", ".join(words))

print("\n" + "=" * 60)
print("STEP 2: TURN EACH SENTENCE INTO A ROW OF NUMBERS")
print("=" * 60)
print("\n   0 means 'this word is not in the sentence'.")
print("   A bigger number means 'this word matters more here'.\n")
df = pd.DataFrame(table.toarray().round(2), columns=words, index=sentences)
print(df.to_string())

print("\n   Look at the word 'my'. It appears in a CANCEL sentence and in a")
print("   REFUND sentence, so it is useless. The word 'cancel' only appears")
print("   in CANCEL sentences, so it is very useful.")
print("   Nobody told the computer this. It counted.")

print("\n" + "=" * 60)
print("STEP 3: LEARN WHICH WORDS POINT WHERE")
print("=" * 60)
model = LinearSVC().fit(table, labels)
score = pd.Series(model.coef_[0], index=words).sort_values()
print("\n   Each word gets a score:\n")
for w, s in score.items():
    side = "REFUND" if s > 0 else "CANCEL"
    bar = "#" * round(abs(s) * 12)
    print(f"      {w:<10} {s:+.2f}  {bar:<14} points to {side}")

print("\n" + "=" * 60)
print("STEP 4: USE IT ON A NEW SENTENCE")
print("=" * 60)
for new in ["cancel this please", "i need my money back as a refund", "hello there"]:
    row = v.transform([new])
    guess = model.predict(row)[0]
    used = [w for w in v.get_feature_names_out()[row.nonzero()[1]]]
    print(f"\n   \"{new}\"")
    print(f"      words it recognised : {used if used else 'NONE'}")
    print(f"      answer              : {guess}")

print("\n   The last one has no known words at all, so the answer is a")
print("   coin flip. That is exactly what happens with the word 'parcel'")
print("   in the real data.\n")
