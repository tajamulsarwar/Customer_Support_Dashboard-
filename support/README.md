# The `support/` project

The chatbot with a real database behind it.

## Files

| file | what it is |
|---|---|
| `schema.sql` | the database design, in plain SQL |
| `db.py` | **every** SQL query lives here, and nowhere else |
| `seed.py` | builds the database and adds sample data |
| `bot.py` | the brain: understand the message, then use the database |
| `cli.py` | the screen you type into |
| `report.py` | read back what the database has collected |
| `support.db` | the database file itself (created by `seed.py`) |

## Run it

```
python support/seed.py --reset      # build the database
python support/cli.py               # chat
python support/report.py            # see what was collected
```

Extra options:

```
python support/cli.py --debug                 # show the model's guesses
python support/cli.py --as aisha@example.com  # chat as a known customer
```

## The five tables

```
customers  ──< orders ──< refunds
     │
     └──< conversations ──< messages
```

- **customers** — name, email, address
- **orders** — order number, item, price, status, dates
- **refunds** — linked to an order, with a status
- **conversations** — one row per chat
- **messages** — one row per message, **with what the model guessed and how sure it was**

That last table is the important one. See "The loop" below.

## Why `db.py` exists

No other file writes SQL. `bot.py` calls `db.get_order(...)`, it never writes
`SELECT`. So when you move from SQLite to MySQL or PostgreSQL later, `db.py` is
the only file you change.

## It really changes the data

The bot does not read from a script. It checks the database, so the same
question gives different answers:

```
cancel order 54667      -> still preparing, so it asks "shall I go ahead?"
cancel order 872304243  -> already in transit, so it refuses and offers a return
```

And when you say yes, the row actually changes:

```sql
UPDATE orders SET status = 'cancelled' WHERE id = ?
```

Anything that changes data or money asks for a yes/no first. Never act on a
guess from a model that is sometimes wrong.

## The loop (this is the point)

The `messages` table stores every customer sentence with the model's guess and
its confidence. `report.py` shows you the ones it was unsure about:

```
28%  "stop sending me emails"
     it guessed: contact_customer_service     <- wrong
```

So:

1. Real customers chat with the bot
2. `report.py` lists what it did not understand
3. You write down the correct intent for each one
4. Add them to the training data and run `train.py` again

This is the only real cure for the small-vocabulary problem. The Bitext data
uses fewer than 2,000 words. Your customers use words like *parcel*, *receipt*
and *login* that appear in it zero times. Fifty real sentences collected this
way beat thousands of generated ones.

## Still broken

`"what about my parcel"` returns an **invoice**, at 70% confidence. Confidently
wrong, which is worse than saying "I don't know". Same cause: "parcel" is not a
word the model has ever seen. The database fixed the *doing*. It did not fix
the *understanding*.
