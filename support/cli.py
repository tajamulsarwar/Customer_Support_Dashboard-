"""
cli.py  --  talk to the database-backed bot.

    python support/cli.py
    python support/cli.py --debug
    python support/cli.py --as aisha@example.com
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
import database as db
import bot


def main():
    args = sys.argv[1:]
    debug = "--debug" in args
    email = args[args.index("--as") + 1] if "--as" in args else None

    if not db.USING_SUPABASE and not db.DB_FILE.exists():
        sys.exit("No database yet. Run:  python support/seed.py")

    print("Database:", db.which())
    s = bot.Session(customer_email=email, debug=debug)
    who = s.customer["name"] if s.customer else "guest"
    print(f"Support bot (chat #{s.conversation_id}, you are {who}). Type 'quit' to stop.")
    with db.connect() as con:
        ids = [r["id"] for r in con.execute("SELECT id FROM orders")]
    print("Order numbers in the database:", ", ".join(ids), "\n")

    while True:
        try:
            text = input("You : ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not text:
            continue
        if text.lower() in {"quit", "exit", "bye"}:
            print("Bot : Goodbye.")
            break
        answer = s.reply(text)
        db.log_message(s.conversation_id, "bot", answer)
        print("Bot :", answer, "\n")

    s.close()
    print(f"Chat #{s.conversation_id} saved to the database.")


if __name__ == "__main__":
    main()
