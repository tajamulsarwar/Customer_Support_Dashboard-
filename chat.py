"""
chat.py  --  talk to the trained bot.

    python train.py      (first, once)
    python chat.py       (then, any time)

    python chat.py "where is my order"     # ask one question and exit
    python chat.py --debug                 # also show the top 3 guesses
"""

import sys
import joblib
from responses import RESPONSES, FALLBACK

MODEL_FILE = "model.joblib"

# If the bot is less than this sure, it admits it does not know
# instead of guessing. Raise it to be more careful, lower it to guess more.
CONFIDENCE_THRESHOLD = 0.40


class Bot:
    def __init__(self, path=MODEL_FILE):
        try:
            bundle = joblib.load(path)
        except FileNotFoundError:
            sys.exit(f"No {path} found. Run 'python train.py' first.")
        self.model = bundle["model"]
        self.labels = self.model.classes_

    def guess(self, text, top=3):
        """Return a list of (intent, confidence) sorted best first."""
        probs = self.model.predict_proba([text])[0]
        order = probs.argsort()[::-1][:top]
        return [(self.labels[i], float(probs[i])) for i in order]

    def reply(self, text):
        ranked = self.guess(text)
        intent, score = ranked[0]
        if score < CONFIDENCE_THRESHOLD:
            return FALLBACK, ranked, False
        return RESPONSES.get(intent, FALLBACK), ranked, True


def main():
    args = sys.argv[1:]
    debug = "--debug" in args
    args = [a for a in args if not a.startswith("--")]

    bot = Bot()

    if args:  # one-shot mode
        question = " ".join(args)
        answer, ranked, ok = bot.reply(question)
        print(f"You : {question}")
        print(f"Bot : {answer}")
        if debug or not ok:
            print("      (guesses: " + ", ".join(f"{i} {s:.0%}" for i, s in ranked) + ")")
        return

    print("Support bot ready. Type your question, or 'quit' to stop.\n")
    while True:
        try:
            text = input("You : ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye.")
            break
        if not text:
            continue
        if text.lower() in {"quit", "exit", "bye"}:
            print("Bot : Thanks for chatting. Goodbye.")
            break

        answer, ranked, ok = bot.reply(text)
        print(f"Bot : {answer}")
        if debug:
            print("      (guesses: " + ", ".join(f"{i} {s:.0%}" for i, s in ranked) + ")")
        print()


if __name__ == "__main__":
    main()
