"""
db_pg.py  --  the Supabase (PostgreSQL) version of db.py.

Every function has the SAME NAME and returns the SAME SHAPE as db.py.
So bot.py, cli.py and report.py do not change at all.

Setup:
    1. supabase.com -> New project
    2. Project Settings -> Database -> Connection string -> URI (Session pooler)
    3. Put it in a file called .env next to this one:
           DATABASE_URL=postgresql://postgres.xxxx:PASSWORD@aws-0-eu-west-2.pooler.supabase.com:5432/postgres
    4. python support/seed_pg.py --reset
"""

import os
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

DATABASE_URL = os.environ.get("DATABASE_URL")
SCHEMA = Path(__file__).parent / "schema_postgres.sql"

# psycopg uses %s placeholders; sqlite3 used ?. That is the only SQL difference.


def _require_url():
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL is not set.\n"
            "Create a file called .env in the project folder containing:\n"
            "    DATABASE_URL=postgresql://postgres.xxx:PASSWORD@...pooler.supabase.com:5432/postgres\n"
            "Copy .env.example to .env and paste your own connection string in."
        )
    return DATABASE_URL


def connect():
    """Open a connection. Rows come back as dictionaries, like sqlite3.Row."""
    return psycopg.connect(_require_url(), row_factory=dict_row)


def create_tables():
    with connect() as con:
        con.execute(SCHEMA.read_text(encoding="utf-8"))
        con.commit()


def check():
    """Quick 'is it working?' test."""
    with connect() as con:
        row = con.execute("SELECT version() AS v, current_database() AS db").fetchone()
    return row


# ------------------------------------------------------------ customers
def get_customer_by_email(email):
    with connect() as con:
        return con.execute("SELECT * FROM customers WHERE email = %s", (email,)).fetchone()


def add_customer(name, email, address=None):
    with connect() as con:
        row = con.execute(
            "INSERT INTO customers (name, email, address) VALUES (%s, %s, %s) RETURNING id",
            (name, email, address)).fetchone()
        con.commit()
        return row["id"]


# ------------------------------------------------------------ orders
def get_order(order_id):
    with connect() as con:
        return con.execute("""
            SELECT o.*, c.name AS customer_name, c.email AS customer_email
            FROM orders o
            JOIN customers c ON c.id = o.customer_id
            WHERE o.id = %s
        """, (str(order_id).strip(),)).fetchone()


def get_orders_for_customer(customer_id, limit=10):
    with connect() as con:
        return con.execute(
            "SELECT * FROM orders WHERE customer_id = %s ORDER BY placed_at DESC LIMIT %s",
            (customer_id, limit)).fetchall()


def cancel_order(order_id):
    """
    One statement, not two. In Postgres the WHERE clause does the check and the
    update together, so two customers clicking cancel at the same moment cannot
    both succeed. The SQLite version read first and then wrote, which has a gap
    between the two where things can go wrong.
    """
    with connect() as con:
        row = con.execute("""
            UPDATE orders SET status = 'cancelled'
            WHERE id = %s AND status = 'preparing'
            RETURNING id
        """, (order_id,)).fetchone()
        con.commit()
        return row is not None


def can_cancel(order):
    return order is not None and order["status"] == "preparing"


# ------------------------------------------------------------ refunds
def create_refund(order_id, amount, reason=None):
    with connect() as con:
        row = con.execute("""
            INSERT INTO refunds (order_id, amount, status, reason)
            VALUES (%s, %s, 'requested', %s) RETURNING id
        """, (order_id, amount, reason)).fetchone()
        con.commit()
        return row["id"]


def get_refund_for_order(order_id):
    with connect() as con:
        return con.execute(
            "SELECT * FROM refunds WHERE order_id = %s ORDER BY id DESC LIMIT 1",
            (order_id,)).fetchone()


# ------------------------------------------------------------ chat logging
def start_conversation(customer_id=None):
    with connect() as con:
        row = con.execute(
            "INSERT INTO conversations (customer_id) VALUES (%s) RETURNING id",
            (customer_id,)).fetchone()
        con.commit()
        return row["id"]


def end_conversation(conversation_id):
    with connect() as con:
        con.execute("UPDATE conversations SET ended_at = NOW() WHERE id = %s",
                    (conversation_id,))
        con.commit()


def log_message(conversation_id, who, text, intent=None, confidence=None):
    with connect() as con:
        con.execute("""
            INSERT INTO messages (conversation_id, who, text, predicted_intent, confidence)
            VALUES (%s, %s, %s, %s, %s)
        """, (conversation_id, who, text, intent, confidence))
        con.commit()


def unsure_messages(limit=50):
    with connect() as con:
        return con.execute("""
            SELECT text, predicted_intent, confidence
            FROM messages
            WHERE who = 'customer' AND confidence IS NOT NULL AND confidence < 0.40
            ORDER BY confidence ASC LIMIT %s
        """, (limit,)).fetchall()


# ------------------------------------------------------------ llm cache
def _key(text):
    return " ".join(str(text).lower().split())


def get_cached_intent(text):
    with connect() as con:
        row = con.execute("SELECT * FROM llm_cache WHERE text_key = %s", (_key(text),)).fetchone()
        if row:
            con.execute("UPDATE llm_cache SET hits = hits + 1 WHERE text_key = %s", (_key(text),))
            con.commit()
        return row


def cache_intent(text, intent, confidence, reason=None, model=None):
    with connect() as con:
        con.execute("""INSERT INTO llm_cache (text_key, intent, confidence, reason, model)
                       VALUES (%s, %s, %s, %s, %s)
                       ON CONFLICT (text_key) DO UPDATE SET
                           intent = EXCLUDED.intent,
                           confidence = EXCLUDED.confidence,
                           reason = EXCLUDED.reason,
                           model = EXCLUDED.model""",
                    (_key(text), intent, confidence, reason, model))
        con.commit()


def cache_stats():
    with connect() as con:
        return con.execute(
            "SELECT COUNT(*) AS entries, COALESCE(SUM(hits),0) AS saved FROM llm_cache").fetchone()


if __name__ == "__main__":
    info = check()
    print("Connected to:", info["db"])
    print(info["v"].split(",")[0])
