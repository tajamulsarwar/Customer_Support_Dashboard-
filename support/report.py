"""
report.py  --  read what the database has collected.

    python support/report.py

Every message the bot ever saw is stored, together with what it guessed and
how sure it was. That turns your live chats into real training data, which is
the only proper cure for the small-vocabulary problem.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import database as db


def head(t):
    print("\n" + "=" * 62)
    print(t)
    print("=" * 62)


with db.connect() as con:
    head("WHAT IS IN THE DATABASE")
    for table in ("customers", "orders", "refunds", "conversations", "messages"):
        n = con.execute(f"SELECT COUNT(*) c FROM {table}").fetchone()["c"]
        print(f"   {table:<16} {n:>5} rows")

    head("ORDERS BY STATUS")
    for r in con.execute("SELECT status, COUNT(*) n, SUM(total) v FROM orders GROUP BY status"):
        print(f"   {r['status']:<14} {r['n']:>3} orders   {r['v']:>8.2f} total")

    head("WHAT CUSTOMERS ASK ABOUT MOST")
    rows = con.execute("""
        SELECT predicted_intent i, COUNT(*) n, AVG(confidence) c
        FROM messages
        WHERE who = 'customer' AND predicted_intent IS NOT NULL
        GROUP BY predicted_intent ORDER BY n DESC LIMIT 10
    """).fetchall()
    if not rows:
        print("   Nothing logged yet. Run:  python support/cli.py")
    for r in rows:
        print(f"   {r['i']:<26} {r['n']:>4} times   average confidence {r['c']:.0%}")

    head("MESSAGES THE BOT DID NOT UNDERSTAND")
    print("   These are gold. Label them by hand and add them to training.\n")
    rows = db.unsure_messages(20)
    if not rows:
        print("   None yet.")
    for r in rows:
        print(f"   {r['confidence']:>4.0%}  \"{r['text']}\"")
        print(f"         it guessed: {r['predicted_intent']}")

    head("HOW TO USE THIS")
    print("""
   1. Let real customers chat with the bot.
   2. Run this report and look at the list above.
   3. For each message, write down the intent it SHOULD have been.
   4. Add those real sentences to your training data and run train.py again.

   Real customer wording is what the Bitext data is missing. Fifty real
   sentences collected this way beat thousands of generated ones.
""")
