"""
orders.py  --  a pretend order database.

The Bitext dataset has NO orders in it. A real bot needs to look things up
somewhere. In a real company this would be your real database. Here it is
just a small Python dictionary so you can see how it works.
"""

ORDERS = {
    "872304243": {"item": "Blue Running Shoes, size 9", "status": "In transit",
                  "placed": "24 Sep 2026", "arrives": "1 Oct 2026",
                  "total": "59.99", "address": "12 Mill Road, Leeds, LS1 4AB",
                  "paid": "Visa ending 4471", "cancellable": False},
    "54667":     {"item": "Desk Lamp, white", "status": "Preparing",
                  "placed": "27 Sep 2026", "arrives": "3 Oct 2026",
                  "total": "24.50", "address": "12 Mill Road, Leeds, LS1 4AB",
                  "paid": "PayPal", "cancellable": True},
    "100200":    {"item": "Wireless Keyboard", "status": "Delivered",
                  "placed": "12 Sep 2026", "arrives": "15 Sep 2026 (delivered)",
                  "total": "39.00", "address": "12 Mill Road, Leeds, LS1 4AB",
                  "paid": "Visa ending 4471", "cancellable": False},
}


def find(order_id):
    """Return the order, or None if there is no such order."""
    return ORDERS.get(str(order_id).strip())


def looks_like_order_number(text):
    """Is the whole message just a number? Then treat it as an order number."""
    t = text.strip().replace("#", "").replace("-", "")
    return t.isdigit() and 4 <= len(t) <= 12
