"""
db.py  --  everything that talks to the database lives here.

No other file writes SQL. If you later move to MySQL or PostgreSQL,
this is the only file you have to change.
"""

import sqlite3
from pathlib import Path

DB_FILE = Path(__file__).parent / "support.db"
SCHEMA = Path(__file__).parent / "schema.sql"


def connect():
    """Open the database. Rows come back so you can use row['name']."""
    con = sqlite3.connect(DB_FILE)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def create_tables():
    with connect() as con:
        con.executescript(SCHEMA.read_text(encoding="utf-8"))


# ------------------------------------------------------------ customers
def get_customer_by_email(email):
    with connect() as con:
        return con.execute("SELECT * FROM customers WHERE email = ?", (email,)).fetchone()


def add_customer(name, email, address=None):
    with connect() as con:
        cur = con.execute(
            "INSERT INTO customers (name, email, address) VALUES (?, ?, ?)",
            (name, email, address))
        return cur.lastrowid


# ------------------------------------------------------------ orders
def get_order(order_id):
    """One order, plus the customer's name, in a single query."""
    with connect() as con:
        return con.execute("""
            SELECT o.*, c.name AS customer_name, c.email AS customer_email
            FROM orders o
            JOIN customers c ON c.id = o.customer_id
            WHERE o.id = ?
        """, (str(order_id).strip(),)).fetchone()


def get_orders_for_customer(customer_id, limit=10):
    with connect() as con:
        return con.execute(
            "SELECT * FROM orders WHERE customer_id = ? ORDER BY placed_at DESC LIMIT ?",
            (customer_id, limit)).fetchall()


def cancel_order(order_id):
    """Only allowed before the parcel leaves. Returns True if it worked."""
    with connect() as con:
        row = con.execute("SELECT status FROM orders WHERE id = ?", (order_id,)).fetchone()
        if row is None or row["status"] not in ("preparing",):
            return False
        con.execute("UPDATE orders SET status = 'cancelled' WHERE id = ?", (order_id,))
        return True


def can_cancel(order):
    return order is not None and order["status"] == "preparing"


# ------------------------------------------------------------ refunds
def create_refund(order_id, amount, reason=None):
    with connect() as con:
        cur = con.execute(
            "INSERT INTO refunds (order_id, amount, status, reason) VALUES (?, ?, 'requested', ?)",
            (order_id, amount, reason))
        return cur.lastrowid


def get_refund_for_order(order_id):
    with connect() as con:
        return con.execute(
            "SELECT * FROM refunds WHERE order_id = ? ORDER BY id DESC LIMIT 1",
            (order_id,)).fetchone()


# ------------------------------------------------------------ chat logging
def start_conversation(customer_id=None):
    with connect() as con:
        cur = con.execute("INSERT INTO conversations (customer_id) VALUES (?)", (customer_id,))
        return cur.lastrowid


def end_conversation(conversation_id):
    with connect() as con:
        con.execute("UPDATE conversations SET ended_at = datetime('now') WHERE id = ?",
                    (conversation_id,))


def log_message(conversation_id, who, text, intent=None, confidence=None):
    with connect() as con:
        con.execute("""INSERT INTO messages
                       (conversation_id, who, text, predicted_intent, confidence)
                       VALUES (?, ?, ?, ?, ?)""",
                    (conversation_id, who, text, intent, confidence))


def unsure_messages(limit=50):
    """Customer messages the bot was NOT confident about.
    These are the ones worth labelling by hand and adding to training."""
    with connect() as con:
        return con.execute("""
            SELECT text, predicted_intent, confidence
            FROM messages
            WHERE who = 'customer' AND confidence IS NOT NULL AND confidence < 0.40
            ORDER BY confidence ASC LIMIT ?
        """, (limit,)).fetchall()


# ------------------------------------------------------------ llm cache
def _key(text):
    return " ".join(str(text).lower().split())


def get_cached_intent(text):
    """An answer Claude already gave for this exact wording, or None."""
    with connect() as con:
        row = con.execute("SELECT * FROM llm_cache WHERE text_key = ?", (_key(text),)).fetchone()
        if row:
            con.execute("UPDATE llm_cache SET hits = hits + 1 WHERE text_key = ?", (_key(text),))
        return row


def cache_intent(text, intent, confidence, reason=None, model=None):
    with connect() as con:
        con.execute("""INSERT OR REPLACE INTO llm_cache
                       (text_key, intent, confidence, reason, model)
                       VALUES (?, ?, ?, ?, ?)""",
                    (_key(text), intent, confidence, reason, model))


def cache_stats():
    with connect() as con:
        return con.execute(
            "SELECT COUNT(*) AS entries, COALESCE(SUM(hits),0) AS saved FROM llm_cache").fetchone()
