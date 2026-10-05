"""
database.py  --  chooses which database to use.

    no .env file          -> SQLite, the local file. Works offline.
    DATABASE_URL in .env  -> Supabase (PostgreSQL), on the internet.

Everything else imports THIS file, so nothing else ever needs to know
which one is running.

    import database as db
    db.get_order("54667")
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

USING_SUPABASE = bool(os.environ.get("DATABASE_URL"))

if USING_SUPABASE:
    from db_pg import *          # noqa: F401,F403
    from db_pg import connect, create_tables, get_order  # noqa: F401
    from db_pg import get_cached_intent, cache_intent, cache_stats  # noqa: F401
    BACKEND = "Supabase (PostgreSQL)"
else:
    from db import *             # noqa: F401,F403
    from db import connect, create_tables, get_order     # noqa: F401
    from db import get_cached_intent, cache_intent, cache_stats    # noqa: F401
    BACKEND = "SQLite (local file)"


def which():
    return BACKEND


if __name__ == "__main__":
    print("Using:", BACKEND)
    if USING_SUPABASE:
        import db_pg
        info = db_pg.check()
        print("Connected to database:", info["db"])
