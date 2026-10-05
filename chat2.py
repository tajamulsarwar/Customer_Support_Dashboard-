"""
chat2.py  --  the bot with a MEMORY and a DATABASE.

chat.py judges every message on its own, so a bare number means nothing to it.
This version remembers what it just asked, and looks the order up for real.

    python chat2.py
    python chat2.py --debug
"""

import sys
from chat import Bot, CONFIDENCE_THRESHOLD
from responses import RESPONSES, FALLBACK
import orders

# Intents that cannot be answered without an order number.
NEEDS_ORDER = {
    "track_order":  "track your order",
    "cancel_order": "cancel your order",
    "change_order": "change your order",
    "get_refund":   "start your refund",
    "track_refund": "check your refund",
    "get_invoice":  "send your invoice",
    "check_invoice":"check your invoice",
}


class Conversation:
    """This class IS the memory. chat.py has nothing like it."""

    def __init__(self, debug=False):
        self.bot = Bot()
        self.debug = debug
        self.waiting_for = None   # the intent we are still waiting on
        self.order_id = None      # the order number, once we know it

    # ---------------------------------------------------------- answers
    def answer_with_order(self, intent, o, oid):
        if intent == "track_order":
            return (f"Order {oid} - {o['item']}\n"
                    f"      Status  : {o['status']}\n"
                    f"      Arrives : {o['arrives']}\n"
                    f"      Sent to : {o['address']}")
        if intent == "cancel_order":
            if o["cancellable"]:
                return (f"Order {oid} ({o['item']}) can still be cancelled - it has not shipped.\n"
                        f"      Shall I cancel it? The {o['total']} will go back to {o['paid']}.")
            return (f"Order {oid} ({o['item']}) is already {o['status'].lower()}, so it cannot be\n"
                    f"      cancelled now. You can return it once it arrives for a full refund.")
        if intent == "change_order":
            if o["cancellable"]:
                return f"Order {oid} has not shipped yet, so I can still change it. What would you like to change?"
            return f"Order {oid} is already {o['status'].lower()}. It is too late to change it, sorry."
        if intent in ("get_refund", "track_refund"):
            return (f"Order {oid} - {o['item']}, {o['total']} paid by {o['paid']}.\n"
                    f"      I have started the refund. It reaches {o['paid']} in 5 to 7 working days.")
        if intent in ("get_invoice", "check_invoice"):
            return (f"Invoice for order {oid}\n"
                    f"      {o['item']} - {o['total']}\n"
                    f"      Placed {o['placed']}, paid by {o['paid']}\n"
                    f"      I have emailed you a copy.")
        return RESPONSES.get(intent, FALLBACK)

    # ---------------------------------------------------------- main logic
    def reply(self, text):
        # 1. Did the user just send a bare order number?
        if orders.looks_like_order_number(text):
            o = orders.find(text)
            if not o:
                return (f"I could not find order {text.strip()}. Please check the number.\n"
                        f"      (For this demo, try 872304243, 54667 or 100200.)")
            self.order_id = text.strip()
            if self.waiting_for:                 # <-- THE MEMORY DOING ITS JOB
                intent = self.waiting_for
                self.waiting_for = None
                return self.answer_with_order(intent, o, self.order_id)
            return (f"Found order {self.order_id} - {o['item']}, {o['status'].lower()}.\n"
                    f"      What would you like to do with it?")

        # 2. Otherwise work out the topic, as chat.py does.
        ranked = self.bot.guess(text)
        intent, score = ranked[0]
        if self.debug:
            print("      [guesses: " + ", ".join(f"{i} {s:.0%}" for i, s in ranked) + "]")

        if score < CONFIDENCE_THRESHOLD:
            return FALLBACK

        # 3. Does this topic need an order number?
        if intent in NEEDS_ORDER:
            if self.order_id:                    # we already know it - no need to ask twice
                return self.answer_with_order(intent, orders.find(self.order_id), self.order_id)
            self.waiting_for = intent            # <-- REMEMBER WHAT WE ASKED
            return f"Happy to {NEEDS_ORDER[intent]}. What is the order number?"

        return RESPONSES.get(intent, FALLBACK)


def main():
    debug = "--debug" in sys.argv
    c = Conversation(debug=debug)
    print("Support bot with memory. Type 'quit' to stop.")
    print("Demo order numbers you can use: 872304243, 54667, 100200\n")
    while True:
        try:
            text = input("You : ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nBye."); break
        if not text:
            continue
        if text.lower() in {"quit", "exit", "bye"}:
            print("Bot : Goodbye."); break
        print("Bot :", c.reply(text), "\n")


if __name__ == "__main__":
    main()
