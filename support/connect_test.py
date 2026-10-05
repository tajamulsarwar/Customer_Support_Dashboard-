"""
connect_test.py  --  check your Supabase connection and explain any problem.

    python support/connect_test.py

Run this BEFORE seed_pg.py. It checks the connection string looks right,
then tries to connect, and tells you in plain words what to fix.
"""
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse, unquote

from dotenv import load_dotenv

ROOT = Path(__file__).parent.parent
ENV = ROOT / ".env"


def fail(msg, fix=None):
    print(f"\n  PROBLEM: {msg}")
    if fix:
        print(f"  FIX    : {fix}")
    sys.exit(1)


def ok(msg):
    print(f"  OK     : {msg}")


print("=" * 64)
print("SUPABASE CONNECTION CHECK")
print("=" * 64 + "\n")

# ---------------------------------------------------------------- 1
if not ENV.exists():
    fail(f"There is no .env file at {ENV}",
         "Copy .env.example to .env and paste your connection string in.")
ok(f".env file found")

load_dotenv(ENV)
url = os.environ.get("DATABASE_URL", "").strip()

# ---------------------------------------------------------------- 2
if not url:
    fail("DATABASE_URL is empty in .env",
         "The line must look like:  DATABASE_URL=postgresql://postgres.xxx:PASS@...:5432/postgres")
if url.startswith('"') or url.startswith("'"):
    fail("DATABASE_URL is wrapped in quotes",
         "Remove the quotes. Write it bare, with no \" or ' around it.")
ok("DATABASE_URL is set")

# ---------------------------------------------------------------- 3
if not url.startswith(("postgresql://", "postgres://")):
    fail(f"DATABASE_URL does not start with postgresql://  (it starts '{url[:20]}...')",
         "You may have copied the API URL (https://xxx.supabase.co) instead of the\n"
         "           database URI. Go to: Project Settings -> Database -> Connection string -> URI")
ok("It is a postgresql:// address")

# Check placeholders BEFORE parsing: the square brackets in [YOUR-PASSWORD]
# make Python's URL parser think the host is an IPv6 address, and it crashes.
if "[YOUR-PASSWORD]" in url or "YOURPASSWORD" in url.upper().replace("-", ""):
    fail("The password placeholder is still in the string",
         "Replace [YOUR-PASSWORD] with the real database password you set when\n"
         "           you created the project. It is not your supabase.com login password.")
if "[" in url or "]" in url:
    fail("The connection string still contains square brackets [ ]",
         "Those brackets mark a placeholder. Delete them and the text inside,\n"
         "           and put your real value there instead.")

try:
    p = urlparse(url)
except ValueError as e:
    fail(f"the connection string could not be read ({e})",
         "Copy it again from the dashboard, then replace only the password part.")

# ---------------------------------------------------------------- 4
if not p.password:
    fail("There is no password in the connection string",
         "The format is  postgresql://USER:PASSWORD@HOST:PORT/postgres")
ok("A password is present")

pw = unquote(p.password)
risky = set("@#?/%: ") & set(pw)
if risky and p.password == pw:
    fail(f"The password contains {sorted(risky)} which must be percent-encoded",
         "Replace @ with %40, # with %23, ? with %3F, / with %2F, : with %3A, space with %20")

# ---------------------------------------------------------------- 5
host = p.hostname or ""
if "supabase" not in host:
    print(f"  NOTE   : host '{host}' does not look like Supabase. Continuing anyway.")
elif "pooler.supabase.com" in host:
    ok(f"Using the pooler ({host}) - this is the right choice")
elif host.startswith("db.") and host.endswith(".supabase.co"):
    print(f"\n  WARNING: '{host}' is the DIRECT connection. It is IPv6-only and most")
    print( "           home and office networks cannot reach it.")
    print( "           If this fails, go back and pick 'Session pooler' instead.")

if p.port not in (5432, 6543):
    print(f"  NOTE   : unusual port {p.port}. Session pooler uses 5432, transaction pooler 6543.")

# ---------------------------------------------------------------- 6
print("\n  Connecting...\n")
try:
    import psycopg
except ImportError:
    fail("the psycopg driver is not installed", "pip install \"psycopg[binary]\"")

try:
    with psycopg.connect(url, connect_timeout=15) as con:
        row = con.execute("SELECT current_database() d, version() v").fetchone()
        print("=" * 64)
        print("  CONNECTED")
        print("=" * 64)
        print(f"  database : {row[0]}")
        print(f"  server   : {row[1].split(',')[0]}")
        tables = con.execute("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' ORDER BY table_name
        """).fetchall()
        if tables:
            print(f"  tables   : {', '.join(t[0] for t in tables)}")
            print("\n  Tables already exist. Run the bot:   python support/cli.py")
        else:
            print("  tables   : none yet")
            print("\n  Next step:   python support/seed_pg.py")

except psycopg.OperationalError as e:
    msg = str(e).lower()
    print("=" * 64)
    print("  COULD NOT CONNECT")
    print("=" * 64)
    print(f"  {e}\n")
    if "password authentication failed" in msg:
        fail("the password is wrong",
             "This is the DATABASE password from when you created the project,\n"
             "           not your supabase.com login. Reset it at:\n"
             "           Project Settings -> Database -> Reset database password")
    elif "could not translate" in msg or "resolve host" in msg or "getaddrinfo" in msg:
        fail("the host name could not be found",
             "Check for typos. Also make sure the project is not PAUSED -\n"
             "           free projects pause after a week. Open the dashboard to wake it.")
    elif "timeout" in msg or "timed out" in msg:
        fail("the connection timed out",
             "You are probably on the IPv6-only direct connection. Go to\n"
             "           Connection string -> URI and choose 'Session pooler' instead.")
    elif "tenant or user not found" in msg or "tenant/user" in msg:
        fail("Supabase answered, but does not recognise that username",
             "Good news: your network can reach Supabase. The username is wrong.\n"
             "           It must be  postgres.<your-project-ref>  - the long code from\n"
             "           your project URL. Copy the whole URI from the dashboard again\n"
             "           and change only the password.")
    elif "does not exist" in msg:
        fail("that database or user does not exist",
             "Copy the whole URI again from the dashboard without editing it,\n"
             "           then only replace the password part.")
    else:
        fail("see the message above", "Paste this whole output back to me and I will sort it.")
except Exception as e:
    fail(f"unexpected error: {e}", "Paste this whole output back to me.")
