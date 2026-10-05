# The `support/` project

The chatbot with a real database behind it.

## Files

| file | what it is |
|---|---|
| `schema.sql` | the database design, in plain SQL |
| `db.py` | **every** SQL query lives here, and nowhere else |
| `seed.py` | builds the database and adds sample data |
| `bot.py` | the brain: understand the message, then use the database |
| `router.py` | decides who answers: the local model, the cache, or a language model |
| `llm_ollama.py` | asks Ollama, a free language model on your own computer |
| `llm.py` | asks Claude instead (paid, needs an API key) |
| `tracing.py` | sends a log of each step to LangSmith, if it is turned on |
| `database.py` | picks SQLite (`db.py`) or Supabase (`db_pg.py`) |
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

## Who answers each message

```
message
   │
   ▼
1. local model   - at least 70% sure AND knows every word?  -> answer (0.01s, free)
2. cache         - seen this exact message before?          -> saved answer (free)
3. Ollama        - understands new words and typos          -> answer (10-30s, free)
4. nothing worked                                           -> best guess, or "I did not understand"
```

Choose the language model in `.env`:

```
LLM_BACKEND=ollama        # ollama, claude, auto or none
OLLAMA_MODEL=qwen2.5:7b   # qwen2.5:3b is faster, a little less accurate
```

Do not use a very small model like `gemma3:270m`. It cannot follow the long
list of intents and gives confident wrong answers.

The cache only reuses answers from the model you use now. Switching models
does not leave the old model's answers behind.

## LangSmith tracing

LangSmith shows every message on a web page: what the customer typed, who
answered, what Ollama was asked and said, how long it took, and the tokens used.

Turn it on in `.env`:

```
LANGSMITH_TRACING=true
LANGSMITH_API_KEY=lsv2_...         # smith.langchain.com -> Settings -> API Keys
LANGSMITH_PROJECT=customer-support
```

Then chat as normal and open **smith.langchain.com -> Tracing Projects ->
customer-support**. Each message is one `router decide` row. Click it to see
the steps inside (`ollama classify` -> `ollama`).

Set `LANGSMITH_TRACING=false` to send nothing. If the `langsmith` package is
not installed, the bot works the same, with no tracing.

**Privacy:** while tracing is on, customer messages are sent to LangSmith's
servers, even when Ollama runs on your own computer.

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

## What used to be broken

`"what about my parcel"` returned an **invoice**, at 70% confidence. Confidently
wrong, because "parcel" is not a word the local model has ever seen.

The router fixes this. Any unknown word sends the message to Ollama, which
understands it. The loop above is still worth doing: every sentence you add to
the training data is one the local model can answer instantly next time.
