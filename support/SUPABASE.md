https://supabase.com/dashboard/new# Moving to Supabase

Supabase **is** PostgreSQL with a web dashboard on top. So this is not a rewrite
— it is a swap of one file.

## Why it is easy

`bot.py` never writes SQL. It calls `db.get_order("54667")`. All the SQL lives
in one file. So there are now two of those files, and a switch that picks one:

```
bot.py / cli.py / report.py
            |
     database.py          <- the switch
       /        \
   db.py      db_pg.py
  (SQLite)   (Supabase)
```

`bot.py`, `cli.py` and `report.py` were **not changed** to support this. They
import `database` and never know which one is running.

## The switch

| | |
|---|---|
| no `.env` file | SQLite, local file, works offline |
| `DATABASE_URL` in `.env` | Supabase |

Check which one you are on:

```
python support/database.py
```

## Setup, step by step

**1. Make a project.** Go to supabase.com, sign up, New project. Pick a region
near you. **Write down the database password** — it is shown once.

**2. Get the connection string.**
Project Settings → Database → Connection string → URI → choose **Session pooler**.

Use the pooler, not the direct connection. The direct one is IPv6-only and most
home and office networks cannot reach it.

**3. Make your `.env` file.** In the project folder:

```
DATABASE_URL=postgresql://postgres.abcdefghijk:YOURPASSWORD@aws-0-eu-west-2.pooler.supabase.com:5432/postgres
```

Copy `.env.example` and paste your own string in. If the password has symbols
like `@` or `#`, percent-encode them (`@` → `%40`, `#` → `%23`).

**4. Build the tables.**

```
python support/seed_pg.py --reset
```

**5. Run it. Nothing else changes.**

```
python support/cli.py
python support/report.py
```

## What changed in the SQL

| SQLite | Supabase (Postgres) | why |
|---|---|---|
| `INTEGER PRIMARY KEY AUTOINCREMENT` | `BIGSERIAL PRIMARY KEY` | Postgres spelling |
| `REAL` for money | `NUMERIC(10,2)` | exact. `REAL` loses pennies |
| `TEXT` for dates | `DATE`, `TIMESTAMPTZ` | real dates you can sort and filter |
| `CHECK (x IN (...))` | `CREATE TYPE ... AS ENUM` | the database rejects bad values |
| `?` placeholder | `%s` placeholder | different driver |
| `datetime('now')` | `NOW()` | different function name |

## One real improvement, not just a translation

The SQLite cancel read the order, then wrote it — two steps. Two customers
clicking cancel at the same moment could both pass the check.

The Postgres version does it in one statement:

```sql
UPDATE orders SET status = 'cancelled'
WHERE id = %s AND status = 'preparing'
RETURNING id
```

The check and the write happen together, so only one can win. This matters now
that the database is on the internet and more than one person can use it at once.

## Security — this part is new

Your SQLite file sat on your laptop. Supabase is on the public internet.

`schema_postgres.sql` turns on **Row Level Security** on every table. That
blocks all access until you write a rule allowing it. If your anon key ever
leaks, nobody can read your customers' data.

Your bot connects as the database owner, which bypasses RLS, so it keeps working.

Three rules:

- `.env` is in `.gitignore`. **Never commit it.**
- Never put the `service_role` key in a browser or a phone app. Backend only.
- The free tier pauses after a week of no use. Open the dashboard to wake it.

## Honest note

I could not test this against a real Supabase project, because that needs your
account and password. What I did test: the files all parse, the SQLite path
still works unchanged, and a bad connection string gives a clear error instead
of a crash.

The first real run may still need a small fix. Paste me the error if you get one.

## Moving your existing SQLite data up

The sample data is recreated by `seed_pg.py`, so you usually do not need this.
If you have collected real chat logs in `support.db` and want to keep them, say
so and I will write the copy script.
