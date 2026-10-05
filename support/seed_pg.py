"""
seed_pg.py  --  build the tables in Supabase and add the sample rows.

    python support/seed_pg.py           # create tables + sample data
    python support/seed_pg.py --reset   # wipe everything first

Needs DATABASE_URL in a .env file. See .env.example.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import db_pg as db
from seed import CUSTOMERS, ORDERS   # reuse the same sample data


def main():
    reset = "--reset" in sys.argv

    try:
        info = db.check()
    except Exception as e:
        sys.exit(f"Could not connect to Supabase.\n\n{e}\n\n"
                 "Check DATABASE_URL in your .env file.")
    print(f"Connected to '{info['db']}' on Supabase.")

    if reset:
        with db.connect() as con:
            con.execute("""DROP TABLE IF EXISTS messages, conversations,
                           refunds, orders, customers CASCADE""")
            con.execute("""DROP TYPE IF EXISTS order_status, refund_status, speaker CASCADE""")
            con.commit()
        print("Old tables dropped.")

    db.create_tables()
    print("Tables ready.")

    with db.connect() as con:
        n = con.execute("SELECT COUNT(*) AS c FROM customers").fetchone()["c"]
        if n:
            print("Data already there. Use --reset to start again.")
            return

        for name, email, addr in CUSTOMERS:
            con.execute("INSERT INTO customers (name,email,address) VALUES (%s,%s,%s)",
                        (name, email, addr))

        for oid, cid, item, total, paid, status, placed, arrives in ORDERS:
            addr = con.execute("SELECT address FROM customers WHERE id=%s",
                               (cid,)).fetchone()["address"]
            con.execute("""INSERT INTO orders
                (id,customer_id,item,total,paid_with,status,placed_at,arrives_at,address)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (oid, cid, item, total, paid, status, placed, arrives, addr))

        con.execute("""INSERT INTO refunds (order_id, amount, status, reason)
                       VALUES ('770881', 85.00, 'approved', 'Arrived damaged')""")
        con.commit()

    print(f"Added {len(CUSTOMERS)} customers, {len(ORDERS)} orders, 1 refund.")
    with db.connect() as con:
        for r in con.execute("SELECT id,item,status FROM orders ORDER BY id"):
            print(f"   {r['id']:<12} {r['item']:<28} {r['status']}")


if __name__ == "__main__":
    main()
