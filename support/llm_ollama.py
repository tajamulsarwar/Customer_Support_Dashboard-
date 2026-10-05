"""
llm_ollama.py  --  the same job as llm.py, but using a model on YOUR computer.

No API key. No cost. No internet. Nothing about your customers leaves the machine.

Needs Ollama running (you already have it) and one model pulled:
    ollama pull qwen2.5:7b

Set the model in .env if you want a different one:
    OLLAMA_MODEL=qwen2.5:3b
"""

import json
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent))
load_dotenv(Path(__file__).parent.parent / ".env")

from llm import INTENT_HELP, SYSTEM_V1, SYSTEM_V2   # same intent descriptions as the Claude backend
from tracing import traceable

PROMPT = os.environ.get("OLLAMA_PROMPT", "v2")
SYSTEM = SYSTEM_V1 if PROMPT == "v1" else SYSTEM_V2

HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
MODEL = os.environ.get("OLLAMA_MODEL", "qwen2.5:7b")
TIMEOUT = float(os.environ.get("OLLAMA_TIMEOUT", "60"))

# Ollama can force the reply to match a JSON shape. Without this, small models
# wander off and write a sentence instead of a label.
SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {"type": "string", "enum": sorted(INTENT_HELP) + ["none"]},
        "confidence": {"type": "number"},
        "reason": {"type": "string"},
    },
    "required": ["intent", "confidence", "reason"],
}


def available():
    """Is Ollama running and does it have our model?"""
    try:
        r = requests.get(f"{HOST}/api/tags", timeout=5)
        names = [m["name"] for m in r.json().get("models", [])]
        return any(n == MODEL or n.startswith(MODEL.split(":")[0]) for n in names)
    except Exception:
        return False


@traceable(
    name="ollama",
    run_type="llm",
    metadata={"ls_provider": "ollama", "ls_model_name": MODEL},
    process_outputs=lambda r: {
        "output": r.get("message", {}).get("content"),
        "usage_metadata": {
            "input_tokens": r.get("prompt_eval_count", 0),
            "output_tokens": r.get("eval_count", 0),
            "total_tokens": r.get("prompt_eval_count", 0) + r.get("eval_count", 0),
        },
    },
)
def _ask_ollama(text):
    r = requests.post(
        f"{HOST}/api/chat",
        timeout=TIMEOUT,
        json={
            "model": MODEL,
            "format": SCHEMA,          # forces valid JSON in our shape
            "stream": False,
            "keep_alive": "30m",       # stay loaded; reloading costs ~20s
            "options": {
                "temperature": 0,      # classification wants the same answer every time
                "num_predict": 200,
            },
            "messages": [
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": f"Customer message: {text}"},
            ],
        },
    )
    r.raise_for_status()
    return r.json()


@traceable(name="ollama classify")
def classify(text):
    """
    Returns (intent, confidence, reason), or None to fall back.
    Never raises - a broken local model must not break the chat.
    """
    try:
        raw = _ask_ollama(text)["message"]["content"]
        g = json.loads(raw)

        intent = str(g.get("intent", "")).strip()
        if intent != "none" and intent not in INTENT_HELP:
            return None                                  # invented a label

        conf = float(g.get("confidence", 0))
        if conf > 1:                                     # some models answer 0-100
            conf = conf / 100
        conf = max(0.0, min(1.0, conf))

        return (intent, conf, str(g.get("reason", ""))[:200])

    except requests.exceptions.ConnectionError:
        print("  [ollama] not running - start it, or fall back")
        return None
    except requests.exceptions.Timeout:
        print(f"  [ollama] took longer than {TIMEOUT:.0f}s - falling back")
        return None
    except (KeyError, ValueError, json.JSONDecodeError):
        print("  [ollama] gave an answer we could not read - falling back")
        return None
    except Exception as e:
        print(f"  [ollama] {type(e).__name__} - falling back")
        return None


if __name__ == "__main__":
    import time
    if not available():
        print(f"Ollama is not reachable at {HOST}, or '{MODEL}' is not pulled.")
        print(f"Try:  ollama pull {MODEL}")
        raise SystemExit(1)
    print(f"Model: {MODEL} at {HOST}\n")
    for t in sys.argv[1:] or ["my parcel still has not arrived",
                              "i forgot my login details",
                              "stop sending me emails"]:
        t0 = time.time()
        print(f"  {t!r}\n      -> {classify(t)}   ({time.time()-t0:.1f}s)\n")
