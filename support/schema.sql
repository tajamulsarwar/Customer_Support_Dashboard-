-- schema.sql -- the shape of the database.
-- Plain SQL, so you can move this to MySQL or PostgreSQL later with few changes.

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS customers (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    email       TEXT    NOT NULL UNIQUE,
    address     TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS orders (
    id           TEXT    PRIMARY KEY,          -- the order number the customer quotes
    customer_id  INTEGER NOT NULL REFERENCES customers(id),
    item         TEXT    NOT NULL,
    total        REAL    NOT NULL,
    paid_with    TEXT,
    status       TEXT    NOT NULL CHECK (status IN
                 ('preparing','shipped','in_transit','delivered','cancelled')),
    placed_at    TEXT    NOT NULL,
    arrives_at   TEXT,
    address      TEXT
);

CREATE TABLE IF NOT EXISTS refunds (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id    TEXT    NOT NULL REFERENCES orders(id),
    amount      REAL    NOT NULL,
    status      TEXT    NOT NULL CHECK (status IN ('requested','approved','paid','rejected')),
    reason      TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);

-- Every chat gets a row here.
CREATE TABLE IF NOT EXISTS conversations (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id  INTEGER REFERENCES customers(id),
    started_at   TEXT    NOT NULL DEFAULT (datetime('now')),
    ended_at     TEXT
);

-- Every single message gets a row here, WITH what the model guessed.
-- This is the most valuable table in the project: it becomes the real
-- training data that fixes the small-vocabulary problem.
CREATE TABLE IF NOT EXISTS messages (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_id  INTEGER NOT NULL REFERENCES conversations(id),
    who              TEXT    NOT NULL CHECK (who IN ('customer','bot')),
    text             TEXT    NOT NULL,
    predicted_intent TEXT,               -- what the model guessed
    confidence       REAL,               -- how sure it was
    correct_intent   TEXT,               -- you fill this in later if it was wrong
    created_at       TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_messages_conv   ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_intent ON messages(predicted_intent);

-- Answers Claude has already given, so the same wording is never paid for twice.
CREATE TABLE IF NOT EXISTS llm_cache (
    text_key    TEXT    PRIMARY KEY,   -- the message, lowercased and trimmed
    intent      TEXT    NOT NULL,
    confidence  REAL    NOT NULL,
    reason      TEXT,
    model       TEXT,
    hits        INTEGER NOT NULL DEFAULT 0,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
);
