"""
llm.py  --  ask Claude which intent a message is, when the local model is unsure.

This is the second half of the hybrid. The local model (train.py) handles the
easy messages for free. Only the ones it is unsure about come here.

Needs an API key:
    setx ANTHROPIC_API_KEY sk-ant-...      (then open a new terminal)
or put ANTHROPIC_API_KEY=sk-ant-... in the .env file.

If there is no key, every function here returns None and the bot quietly falls
back to the local model. Nothing crashes.

The prompt text (INTENT_HELP, SYSTEM_V1, SYSTEM_V2) is shared with the free
local-LLM backend in llm_ollama.py, so both backends are told the same thing.
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).parent))
load_dotenv(Path(__file__).parent.parent / ".env")

from tracing import traceable

# claude-opus-5-5 is the default. For a cheaper, faster classifier set
# LLM_MODEL=claude-haiku-4-5 in your .env - classification is simple enough
# that Haiku usually does it just as well for a fraction of the price.
MODEL = os.environ.get("LLM_MODEL", "claude-opus-5-5")
HAS_KEY = bool(os.environ.get("ANTHROPIC_API_KEY"))

# What each intent means. The model reads these, so plain English matters more
# than matching the training data's wording.
INTENT_HELP = {
    "cancel_order": "stop an order they already placed",
    "change_order": "modify an order they already placed",
    "change_shipping_address": "correct or update a delivery address already on file",
    "check_cancellation_fee": "ask what it costs to cancel",
    "check_invoice": "look at or query an existing invoice or receipt",
    "check_payment_methods": "ask which ways they can pay",
    "check_refund_policy": "ask the rules for returns and refunds",
    "complaint": "express anger or report bad service",
    "contact_customer_service": "ask for phone, email or opening hours",
    "contact_human_agent": "ask to speak to a real person",
    "create_account": "sign up or register",
    "delete_account": "close or remove their account",
    "delivery_options": "ask what delivery methods exist",
    "delivery_period": "ask how long delivery takes",
    "edit_account": "change details on their account",
    "get_invoice": "be sent a copy of an invoice or receipt",
    "get_refund": "get their money back",
    "newsletter_subscription": "subscribe to, or stop, marketing emails",
    "payment_issue": "a payment failed, was declined or was charged wrongly",
    "place_order": "buy something now",
    "recover_password": "they are locked out or forgot login details",
    "registration_problems": "signing up is not working",
    "review": "leave feedback or a rating",
    "set_up_shipping_address": "add a delivery address for the first time",
    "switch_account": "move between two accounts they own",
    "track_order": "ask where their order or parcel is",
    "track_refund": "ask where a refund they already requested has got to",
    # Small talk. Bitext has none of these; our own smalltalk.csv teaches them.
    "greeting": "only say hello, with no request",
    "thanks": "only say thank you, with no request",
    "goodbye": "only say bye or end the chat, with no request",
}

_LIST = "\n".join(f"- {k}: {v}" for k, v in sorted(INTENT_HELP.items()))

# v1: the first version. Kept so eval_llm.py can show whether v2 really is better.
SYSTEM_V1 = (
    "You label customer support messages for an online shop.\n"
    "Choose exactly one intent from this list:\n\n" + _LIST + "\n\n"
    "Rules:\n"
    "- Judge what the customer WANTS, not the words they used.\n"
    "- 'parcel', 'package' and 'delivery' usually mean their order.\n"
    "- If the message fits none of these intents, use intent 'none'.\n"
    "- Set confidence honestly. Use below 0.5 when the message is vague."
)

# v2: adds rules for the pairs of intents that are easy to mix up. The rules
# describe how the intents differ; none of them copies a test message.
SYSTEM_V2 = (
    "You label customer support messages for an online shop.\n"
    "Choose exactly one intent from this list:\n\n" + _LIST + "\n\n"
    "General rules:\n"
    "- Judge what the customer WANTS, not the words they used. Ignore typos and slang.\n"
    "- 'parcel', 'package', 'shipment' and 'delivery' usually mean their order.\n"
    "- If the message fits none of these intents, use intent 'none'.\n"
    "- Set confidence honestly. Use below 0.5 when the message is vague.\n\n"
    "Pairs that are easy to confuse. Decide using these:\n"
    "- track_order vs delivery_period: track_order is about ONE order the customer has\n"
    "  already placed (late, missing, stuck, 'where is it'). delivery_period is a general\n"
    "  question about how long shipping normally takes.\n"
    "- get_refund vs check_refund_policy: get_refund means they want the money back for a\n"
    "  specific purchase. check_refund_policy means they are asking what the rules are.\n"
    "- get_refund vs track_refund: track_refund is only when a refund was ALREADY requested.\n"
    "- get_invoice vs check_invoice: get_invoice is 'send me a copy'. check_invoice is\n"
    "  'show me / look up' invoices.\n"
    "- cancel_order vs delete_account: cancel_order is about a purchase. delete_account is\n"
    "  about closing the login itself.\n"
    "- change_shipping_address vs set_up_shipping_address: change fixes or replaces an\n"
    "  address for an order or one already saved. set_up adds an address for the first time.\n"
    "- complaint vs contact_human_agent: complaint is about bad service or products.\n"
    "  contact_human_agent is only a request to speak to a person, with no grievance.\n"
    "- contact_customer_service is for contact details and opening hours.\n"
    "- greeting, thanks and goodbye are only for messages with NO request in them.\n"
    "  If the message also asks for something, label the request instead."
)

SYSTEM = SYSTEM_V2


class IntentGuess(BaseModel):
    intent: str = Field(description="One intent from the list, or 'none'.")
    confidence: float = Field(ge=0.0, le=1.0, description="How sure you are, 0 to 1.")
    reason: str = Field(description="One short sentence saying why.")


_client = None


def client():
    global _client
    if _client is None:
        import anthropic
        _client = anthropic.Anthropic()
    return _client


def _usage(response):
    """Token counts in the shape LangSmith uses to work out cost."""
    u = response.usage
    return {
        "input_tokens": u.input_tokens,
        "output_tokens": u.output_tokens,
        "total_tokens": u.input_tokens + u.output_tokens,
        "input_token_details": {
            "cache_read": u.cache_read_input_tokens or 0,
            "cache_creation": u.cache_creation_input_tokens or 0,
        },
    }


@traceable(
    name="claude",
    run_type="llm",
    metadata={"ls_provider": "anthropic", "ls_model_name": MODEL},
    process_outputs=lambda r: {
        "output": r.parsed.model_dump() if r.parsed else None,
        "stop_reason": r.stop_reason,
        "usage_metadata": _usage(r),
    },
)
def _ask_claude(text):
    return client().messages.parse(
        model=MODEL,
        max_tokens=256,                      # a label and one sentence, no more
        output_config={"effort": "low"},     # classification is easy; keep it cheap
        system=[{
            "type": "text",
            "text": SYSTEM,
            "cache_control": {"type": "ephemeral"},   # the intent list never changes
        }],
        messages=[{"role": "user", "content": f"Customer message: {text}"}],
        output_format=IntentGuess,
    )


@traceable(name="claude classify")
def classify(text):
    """
    Ask Claude what this message means.

    Returns (intent, confidence, reason), or None if the LLM could not be used.
    None always means 'fall back to the local model' - never a crash.
    """
    if not HAS_KEY:
        return None

    import anthropic

    try:
        response = _ask_claude(text)

        if response.stop_reason == "refusal":
            return None

        g = response.parsed
        if g is None:
            return None
        intent = g.intent.strip()
        if intent != "none" and intent not in INTENT_HELP:
            return None                          # model invented a label
        return (intent, float(g.confidence), g.reason)

    # Most specific first. Any failure means: fall back, do not crash the chat.
    except anthropic.AuthenticationError:
        print("  [llm] API key rejected - falling back to the local model")
        return None
    except anthropic.RateLimitError:
        print("  [llm] rate limited - falling back to the local model")
        return None
    except anthropic.APIStatusError as e:
        print(f"  [llm] API error {e.status_code} - falling back")
        return None
    except anthropic.APIConnectionError:
        print("  [llm] no internet - falling back to the local model")
        return None
    except Exception as e:
        print(f"  [llm] unexpected: {type(e).__name__} - falling back")
        return None


if __name__ == "__main__":
    if not HAS_KEY:
        print("No ANTHROPIC_API_KEY found.")
        print("Add it to .env as:  ANTHROPIC_API_KEY=sk-ant-...")
        raise SystemExit(1)
    print(f"Model: {MODEL}\n")
    for t in sys.argv[1:] or [
        "my parcel still has not arrived",
        "i forgot my login details",
        "stop sending me emails",
        "what is the weather today",
    ]:
        r = classify(t)
        print(f"  {t!r}\n      -> {r}\n")
