"""
bot.py  --  the brain. Understands the message, then uses the database.

Kept separate from the screen, so the same brain can later serve a web page
or WhatsApp without any changes.
"""
import sys, re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

import database as db
from router import Router
from chat import Bot as IntentModel
from responses import RESPONSES, FALLBACK

NEEDS_ORDER = {
    "track_order":   "track your order",
    "cancel_order":  "cancel your order",
    "change_order":  "change your order",
    "get_refund":    "start your refund",
    "track_refund":  "check your refund",
    "get_invoice":   "send your invoice",
    "check_invoice": "check your invoice",
}

STATUS_TEXT = {"preparing": "being prepared", "shipped": "shipped",
               "in_transit": "on its way", "delivered": "delivered",
               "cancelled": "cancelled"}

YES = {"yes", "y", "yeah", "yep", "ok", "okay", "go ahead", "please do", "sure"}
NO = {"no", "n", "nope", "stop", "nevermind", "never mind"}


def looks_like_order_number(text):
    t = re.sub(r"[#\s-]", "", text.strip())
    return t.isdigit() and 4 <= len(t) <= 12


class Session:
    """One chat with one customer. Holds the memory and writes to the database."""

    def __init__(self, customer_email=None, debug=False):
        self.router = Router(IntentModel(), debug=debug)
        self.debug = debug
        self.customer = db.get_customer_by_email(customer_email) if customer_email else None
        self.conversation_id = db.start_conversation(
            self.customer["id"] if self.customer else None)
        self.waiting_for = None      # intent still needing an order number
        self.order_id = None         # the order we are talking about
        self.pending_confirm = None  # an action waiting for a yes/no

    def close(self):
        db.end_conversation(self.conversation_id)

    # ------------------------------------------------------------- replies
    def describe(self, o):
        s = STATUS_TEXT.get(o["status"], o["status"])
        return f"Order {o['id']} - {o['item']}, currently {s}."

    def act(self, intent, o):
        oid = o["id"]

        if intent == "track_order":
            if o["status"] == "cancelled":
                return f"Order {oid} was cancelled, so it is not on its way."
            return (f"Order {oid} - {o['item']}\n"
                    f"      Status  : {STATUS_TEXT.get(o['status'])}\n"
                    f"      Arrives : {o['arrives_at']}\n"
                    f"      Sent to : {o['address']}")

        if intent == "cancel_order":
            if o["status"] == "cancelled":
                return f"Order {oid} is already cancelled."
            if not db.can_cancel(o):
                return (f"Order {oid} is already {STATUS_TEXT.get(o['status'])}, so it is too\n"
                        f"      late to cancel. You can return it for a full refund instead.")
            self.pending_confirm = ("cancel", oid)
            return (f"Order {oid} ({o['item']}, {o['total']:.2f}) can still be cancelled.\n"
                    f"      Shall I go ahead? Type yes or no.")

        if intent == "change_order":
            if db.can_cancel(o):
                return f"Order {oid} has not shipped, so I can still change it. What would you like to change?"
            return f"Order {oid} is already {STATUS_TEXT.get(o['status'])}. Too late to change it, sorry."

        if intent == "get_refund":
            existing = db.get_refund_for_order(oid)
            if existing:
                return (f"There is already a refund on order {oid}: "
                        f"{existing['amount']:.2f}, status {existing['status']}.")
            if o["status"] not in ("delivered", "in_transit", "shipped"):
                return f"Order {oid} has not shipped yet, so cancelling is better than refunding."
            self.pending_confirm = ("refund", oid)
            return (f"Order {oid} ({o['item']}) cost {o['total']:.2f}, paid by {o['paid_with']}.\n"
                    f"      Shall I request the refund? Type yes or no.")

        if intent == "track_refund":
            r = db.get_refund_for_order(oid)
            if not r:
                return f"There is no refund on order {oid} yet. Would you like me to start one?"
            return (f"Refund on order {oid}\n"
                    f"      Amount : {r['amount']:.2f}\n"
                    f"      Status : {r['status']}\n"
                    f"      Opened : {r['created_at']}")

        if intent in ("get_invoice", "check_invoice"):
            return (f"Invoice for order {oid}\n"
                    f"      {o['item']} - {o['total']:.2f}\n"
                    f"      Placed {o['placed_at']}, paid by {o['paid_with']}\n"
                    f"      Sent to {o['customer_email']}.")

        return RESPONSES.get(intent, FALLBACK)

    # ------------------------------------------------------------- main
    def reply(self, text):
        low = text.strip().lower()

        # 1. Are we waiting for a yes/no?
        if self.pending_confirm:
            action, oid = self.pending_confirm
            if low in YES:
                self.pending_confirm = None
                if action == "cancel":
                    ok = db.cancel_order(oid)
                    return (f"Done. Order {oid} is cancelled. Your money goes back within 5 working days."
                            if ok else f"Sorry, order {oid} can no longer be cancelled.")
                o = db.get_order(oid)
                db.create_refund(oid, o["total"], "Requested in chat")
                return (f"Done. A refund of {o['total']:.2f} is requested on order {oid}. "
                        f"It takes 5 to 7 working days.")
            if low in NO:
                self.pending_confirm = None
                return "No problem, I have not changed anything. Anything else?"
            # anything else: fall through and treat it as a new question

        # 2. Is it a bare order number?
        if looks_like_order_number(text):
            oid = re.sub(r"[#\s-]", "", text.strip())
            o = db.get_order(oid)
            if not o:
                return f"I cannot find order {oid}. Please check the number."
            self.order_id = oid
            if self.waiting_for:
                intent, self.waiting_for = self.waiting_for, None
                return self.act(intent, o)
            return self.describe(o) + "\n      What would you like to do with it?"

        # 3. Work out the topic. The router picks local model or Claude.
        intent, score, source = self.router.decide(text)
        db.log_message(self.conversation_id, "customer", text, intent, score)

        if intent is None:
            return FALLBACK

        if intent in NEEDS_ORDER:
            # An order number may be written inside the sentence.
            found = re.findall(r"\b\d{4,12}\b", text)
            if found:
                self.order_id = found[0]
            if self.order_id:
                o = db.get_order(self.order_id)
                if o:
                    return self.act(intent, o)
            self.waiting_for = intent
            return f"Happy to {NEEDS_ORDER[intent]}. What is the order number?"

        return RESPONSES.get(intent, FALLBACK)
