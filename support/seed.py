"""
seed.py  --  build the database and put some example data in it.

    python support/seed.py          # create tables + sample rows
    python support/seed.py --reset  # delete everything and start again
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import db

CUSTOMERS = [
    ("Aisha Khan",   "aisha@example.com",  "12 Mill Road, Leeds, LS1 4AB"),
    ("Tom Bradley",  "tom@example.com",    "4 Oak Lane, Bristol, BS1 2XY"),
]

ORDERS = [
    # id,         customer, item,                        total, paid,            status,      placed,       arrives
    ("872304243", 1, "Blue Running Shoes, size 9",  59.99, "Visa ....4471", "in_transit", "2026-09-24", "2026-10-01"),
    ("54667",     1, "Desk Lamp, white",            24.50, "PayPal",        "preparing",  "2026-09-27", "2026-10-03"),
    ("100200",    1, "Wireless Keyboard",           39.00, "Visa ....4471", "delivered",  "2026-09-12", "2026-09-15"),
    ("770881",    2, "Coffee Grinder",              85.00, "Mastercard",    "delivered",  "2026-08-30", "2026-09-02"),
]


def main():
    if "--reset" in sys.argv and db.DB_FILE.exists():
        db.DB_FILE.unlink()
        print("Old database deleted.")

    db.create_tables()
    print(f"Tables ready in {db.DB_FILE.name}")

    with db.connect() as con:
        if con.execute("SELECT COUNT(*) c FROM customers").fetchone()["c"]:
            print("Data already there. Use --reset to start again.")
            return

        for name, email, addr in CUSTOMERS:
            con.execute("INSERT INTO customers (name,email,address) VALUES (?,?,?)",
                        (name, email, addr))

        for oid, cid, item, total, paid, status, placed, arrives in ORDERS:
            addr = con.execute("SELECT address FROM customers WHERE id=?", (cid,)).fetchone()["address"]
            con.execute("""INSERT INTO orders
                (id,customer_id,item,total,paid_with,status,placed_at,arrives_at,address)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (oid, cid, item, total, paid, status, placed, arrives, addr))

        con.execute("""INSERT INTO refunds (order_id, amount, status, reason)
                       VALUES ('770881', 85.00, 'approved', 'Arrived damaged')""")

    print(f"Added {len(CUSTOMERS)} customers, {len(ORDERS)} orders, 1 refund.")
    print("\nOrder numbers you can use:")
    with db.connect() as con:
        for r in con.execute("SELECT id,item,status FROM orders"):
            print(f"   {r['id']:<12} {r['item']:<28} {r['status']}")


if __name__ == "__main__":
    main()
