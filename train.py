"""
train.py  --  teach the computer to recognise the 27 intents.

    python train.py              # train on the fair file (recommended)
    python train.py --both       # train on both files together

It saves the finished brain to  model.joblib  so chat.py can use it.
"""

import re
import sys
import joblib
import numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score

import data

MODEL_FILE = "model.joblib"


def build_model():
    """
    Two steps joined together:

    1. TfidfVectorizer turns a sentence into numbers. Two of them:

       - "words"   : single words and word pairs ("my order", "to cancel").
                     Accurate, but one typo makes a word disappear completely.
       - "letters" : 3-to-5 letter chunks inside words ("canc", "ance", "ncel").
                     A typo only breaks some chunks, so most still match.

       The letters are given 3x the weight and the words 0.5x, because
       measured on real typos that scores 5/6 instead of 3/6, and it costs
       nothing on the normal exam.

    2. LinearSVC draws the dividing lines between the 27 intents.
       CalibratedClassifierCV is wrapped around it so we also get a
       confidence score, not just a guess. We need that to decide
       when the bot should say "sorry, I did not understand".
    """
    words = TfidfVectorizer(ngram_range=(1, 2), sublinear_tf=True, min_df=2)
    letters = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), sublinear_tf=True, min_df=2)

    from sklearn.pipeline import FeatureUnion
    features = FeatureUnion(
        [("words", words), ("letters", letters)],
        transformer_weights={"words": 0.5, "letters": 3.0},
    )

    classifier = CalibratedClassifierCV(LinearSVC(C=1.0), cv=3)
    return make_pipeline(features, classifier)


def main():
    which = "both" if "--both" in sys.argv else "balanced"

    df = data.load(which)
    X = df["utterance"].values
    y = df["intent"].values
    print(f"Loaded {len(df)} sentences, {len(set(y))} intents, from the '{which}' data.\n")

    # Keep 20% hidden away. The model never sees it while learning,
    # so testing on it tells us how it does on new sentences.
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )
    print(f"Practice sentences : {len(X_train)}")
    print(f"Exam sentences     : {len(X_test)}  (hidden during training)\n")

    print("Training... (this takes under a minute)")
    model = build_model()
    model.fit(X_train, y_train)

    pred = model.predict(X_test)
    acc = accuracy_score(y_test, pred)
    print(f"\nScore on the hidden exam: {acc * 100:.1f}% correct\n")

    print("Per-intent detail (recall = how often this intent was caught):\n")
    print(classification_report(y_test, pred, zero_division=0))

    # Which intents get mixed up with each other?
    print("Most common mistakes:")
    wrong = [(t, p) for t, p in zip(y_test, pred) if t != p]
    if not wrong:
        print("  none")
    else:
        from collections import Counter
        for (true_i, pred_i), n in Counter(wrong).most_common(10):
            print(f"  {n:3}x  '{true_i}' was guessed as '{pred_i}'")

    # Save every word the model has ever seen. The router uses this to spot
    # messages containing words we never trained on - a far better warning sign
    # than confidence, which is often high and wrong on unfamiliar wording.
    vocab = set()
    for u in X:
        vocab.update(re.findall(r"[a-z]+", str(u).lower()))
    print(f"Vocabulary: {len(vocab)} distinct words seen in training.")

    joblib.dump({"model": model, "intents": sorted(set(y)), "vocab": vocab,
                 "trained_on": which, "accuracy": acc}, MODEL_FILE)
    print(f"\nSaved to {MODEL_FILE}. Now run:  python chat.py")


if __name__ == "__main__":
    main()
