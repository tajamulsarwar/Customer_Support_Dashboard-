"""
router.py  --  decides who answers: the local model, or Claude.

This is the hybrid.

    familiar wording, confident  ->  local model. Free, instant.
    any unfamiliar word          ->  Claude. Costs a fraction of a penny.
    seen this exact message before -> the stored answer. Free.

WHY THE UNFAMILIAR-WORD CHECK, AND NOT JUST CONFIDENCE

The obvious design is "ask Claude when the local model is unsure". Measured on
15 hand-written messages, that does not work: the local model was 98% sure and
WRONG on "scrap my order please i changed my mind", and 94% sure and wrong on
"i forgot my login details". Confidence tells you almost nothing about whether
it is right on wording it has not seen.

What does work is checking the words themselves. The training data only ever
used 2,363 different words. If a message contains a word outside that list, the
local model is guessing, however confident it sounds.

Measured with this rule (confidence >= 70% AND every word known):

    all 15 hand-written messages  -> sent to Claude, 0 wrong answers kept
    400 ordinary messages         -> 100% answered locally, nothing paid

That is the whole point of the hybrid: pay only for the messages the local
model genuinely cannot handle.
"""

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

import database as db
import llm
import llm_ollama
from tracing import traceable

# Which language model answers the hard messages:
#   auto    free local Ollama if it is running, else Claude if there is a key, else none
#   ollama  always the local model (free, private, works offline)
#   claude  always Claude (paid, needs internet and an API key)
#   none    never ask a language model; use only the small local classifier
BACKEND = os.environ.get("LLM_BACKEND", "auto").lower()


def pick_backend():
    if BACKEND == "none":
        return None
    if BACKEND == "claude":
        return llm
    if BACKEND == "ollama":
        return llm_ollama
    if llm_ollama.available():
        return llm_ollama
    if llm.HAS_KEY:
        return llm
    return None


# Trust the local model only when BOTH are true.
TRUST_LOCAL = float(os.environ.get("TRUST_LOCAL", "0.70"))
# Share of words in the message that may be unknown. 0.0 = every word must be
# one the model was trained on. Raising this saves money and costs accuracy.
MAX_UNKNOWN = float(os.environ.get("MAX_UNKNOWN", "0.0"))

# Below this, even Claude is not sure enough - say "I don't understand".
MIN_ANSWER = float(os.environ.get("MIN_ANSWER", "0.45"))


class Router:
    def __init__(self, local_model, debug=False):
        self.local = local_model
        self.debug = debug
        self.vocab = self._load_vocab()
        self.backend = pick_backend()
        self.backend_name = self._backend_name()
        self.stats = {"local": 0, "cached": 0, "llm": 0, "llm_failed": 0}

    def _backend_name(self):
        if self.backend is None:
            return "no language model (local classifier only)"
        if self.backend is llm_ollama:
            return f"Ollama {llm_ollama.MODEL} (free, on this computer)"
        return f"Claude {llm.MODEL} (paid)"

    def _load_vocab(self):
        import joblib
        bundle = joblib.load(Path(__file__).parent.parent / "model.joblib")
        v = bundle.get("vocab")
        if v:
            return v
        # Older model file without the vocabulary - rebuild it from the data.
        import data
        vocab = set()
        for u in data.load("both").utterance:
            vocab.update(re.findall(r"[a-z]+", str(u).lower()))
        return vocab

    def unknown_share(self, text):
        """What fraction of the words has the model never seen?"""
        words = re.findall(r"[a-z]+", text.lower())
        if not words:
            return 1.0
        return sum(w not in self.vocab for w in words) / len(words)

    def unknown_words(self, text):
        return [w for w in re.findall(r"[a-z]+", text.lower()) if w not in self.vocab]

    def _say(self, msg):
        if self.debug:
            print(f"      [{msg}]")

    # One LangSmith trace per message. Drop `self` so only the text is logged.
    @traceable(name="router decide", process_inputs=lambda i: {"text": i.get("text")})
    def decide(self, text):
        """
        Returns (intent, confidence, source).
        source is 'local', 'cache', 'llm' or 'unsure'.
        intent is None when nothing is confident enough to answer.
        """
        intent, score = self.local.guess(text)[0]
        unknown = self.unknown_share(text)

        # 1. Familiar wording AND confident -> the local model is reliable here.
        if score >= TRUST_LOCAL and unknown <= MAX_UNKNOWN:
            self.stats["local"] += 1
            self._say(f"local: {intent} {score:.0%} - all words known, free")
            return intent, score, "local"

        why = (f"unknown words: {', '.join(self.unknown_words(text))}"
               if unknown > MAX_UNKNOWN else f"only {score:.0%} sure")

        # 2. Have we already paid to answer this exact wording?
        # Only trust answers from the model we use now - a weaker model's old
        # answer must not stick around after switching models.
        hit = db.get_cached_intent(text)
        if hit and self.backend is not None and hit["model"] != self.backend.MODEL:
            hit = None
        if hit:
            self.stats["cached"] += 1
            self._say(f"cache: {hit['intent']} {hit['confidence']:.0%} - free repeat")
            return hit["intent"], float(hit["confidence"]), "cache"

        # 3. Ask the language model (Ollama or Claude, whichever is set up).
        result = None
        if self.backend is not None:
            self._say(f"{why} - asking {self.backend_name}")
            result = self.backend.classify(text)

        if result is None:
            # No model set up, not running, or it failed. Never crash the chat.
            self.stats["llm_failed"] += 1
            self._say("no language model answer - using the local guess")
            if score >= MIN_ANSWER:
                return intent, score, "local"
            return None, score, "unsure"

        llm_intent, llm_score, reason = result
        self.stats["llm"] += 1
        self._say(f"language model: {llm_intent} {llm_score:.0%} - {reason}")

        db.cache_intent(text, llm_intent, llm_score, reason, self.backend.MODEL)

        if llm_intent == "none" or llm_score < MIN_ANSWER:
            return None, llm_score, "unsure"
        return llm_intent, llm_score, "llm"

    def summary(self):
        s = self.stats
        total = sum(s.values())
        if not total:
            return "No messages yet."
        paid = s["llm"] if self.backend is llm else 0
        free = total - paid
        return (f"{total} messages: {s['local']} local, {s['cached']} cached, "
                f"{s['llm']} sent to {self.backend_name}, {s['llm_failed']} fell back. "
                f"{100 * free / total:.0f}% cost nothing.")
