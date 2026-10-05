"""
eval_llm.py  --  score the local LLM on the three test sets.

    python support/eval_llm.py                      # default model, prompt v2
    python support/eval_llm.py qwen2.5:3b           # pick a model
    python support/eval_llm.py qwen2.5:7b --v1      # the older prompt, to compare
    python support/eval_llm.py --sets hard          # only one set
    python support/eval_llm.py --show-misses        # list the wrong ones

Sets:
    fresh    15 hand-written messages I looked at while building (optimistic)
    heldout  30 clear messages written separately
    hard     20 messy or ambiguous ones (typos, slang, easily confused intents)
"""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

argv = sys.argv[1:]
positional = [a for a in argv if not a.startswith("--")]
if positional:
    os.environ["OLLAMA_MODEL"] = positional[0]
for a in argv:
    if a in ("--v1", "--v2"):
        os.environ["OLLAMA_PROMPT"] = a[2:]

only = None
if "--sets" in argv:
    only = argv[argv.index("--sets") + 1].split(",")
    positional = [p for p in positional if p not in only]
    if positional:
        os.environ["OLLAMA_MODEL"] = positional[0]

import llm_ollama as O
from heldout import HELDOUT, HARD
from realtest import FRESH

SETS = {
    "fresh": [(t, e) for t, e in FRESH if e != "OUT_OF_SCOPE"],
    "heldout": HELDOUT,
    "hard": HARD,
}

if not O.available():
    sys.exit(f"Ollama is not reachable, or {O.MODEL} is not pulled.")

print(f"model {O.MODEL}   prompt {O.PROMPT}\n")
O.classify("warm up")          # load the model once, not timed

total_right = total = 0
all_times = []
for name, cases in SETS.items():
    if only and name not in only:
        continue
    right, misses = 0, []
    for text, expected in cases:
        t0 = time.time()
        r = O.classify(text)
        all_times.append(time.time() - t0)
        got = r[0] if r else "FAILED"
        if got == expected:
            right += 1
        else:
            misses.append((text, expected, got))
    total_right += right
    total += len(cases)
    print(f"  {name:<8} {right:>2}/{len(cases):<2} = {right / len(cases):>4.0%}")
    if "--show-misses" in argv:
        for text, exp, got in misses:
            print(f"      MISS {text[:42]:<44} wanted {exp:<24} got {got}")

all_times.sort()
print(f"\n  overall  {total_right}/{total} = {total_right / total:.0%}   "
      f"median {all_times[len(all_times) // 2]:.1f}s per message")
