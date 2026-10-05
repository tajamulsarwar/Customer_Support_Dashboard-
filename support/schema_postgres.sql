-- schema_postgres.sql -- the same design, written for Supabase (PostgreSQL).
--
-- Paste this into the Supabase dashboard: SQL Editor -> New query -> Run.
--
-- What changed from the SQLite version:
--   INTEGER PRIMARY KEY AUTOINCREMENT  ->  BIGSERIAL PRIMARY KEY
--   TEXT dates                         ->  DATE and TIMESTAMPTZ (real date types)
--   REAL money                         ->  NUMERIC(10,2) (exact, no rounding errors)
--   datetime('now')                    ->  NOW()
--   CHECK (x IN (...))                 ->  a proper ENUM type

CREATE TYPE order_status  AS ENUM ('preparing','shipped','in_transit','delivered','cancelled');
CREATE TYPE refund_status AS ENUM ('requested','approved','paid','rejected');
CREATE TYPE speaker       AS ENUM ('customer','bot');

CREATE TABLE IF NOT EXISTS customers (
    id          BIGSERIAL PRIMARY KEY,
    name        TEXT        NOT NULL,
    email       TEXT        NOT NULL UNIQUE,
    address     TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS orders (
    id           TEXT         PRIMARY KEY,
    customer_id  BIGINT       NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    item         TEXT         NOT NULL,
    total        NUMERIC(10,2) NOT NULL CHECK (total >= 0),
    paid_with    TEXT,
    status       order_status NOT NULL,
    placed_at    DATE         NOT NULL,
    arrives_at   DATE,
    address      TEXT
);

CREATE TABLE IF NOT EXISTS refunds (
    id          BIGSERIAL     PRIMARY KEY,
    order_id    TEXT          NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    amount      NUMERIC(10,2) NOT NULL CHECK (amount >= 0),
    status      refund_status NOT NULL DEFAULT 'requested',
    reason      TEXT,
    created_at  TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS conversations (
    id           BIGSERIAL   PRIMARY KEY,
    customer_id  BIGINT      REFERENCES customers(id) ON DELETE SET NULL,
    started_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at     TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS messages (
    id               BIGSERIAL   PRIMARY KEY,
    conversation_id  BIGINT      NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    who              speaker     NOT NULL,
    text             TEXT        NOT NULL,
    predicted_intent TEXT,
    confidence       REAL        CHECK (confidence BETWEEN 0 AND 1),
    correct_intent   TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_orders_customer ON orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_messages_conv   ON messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_messages_intent ON messages(predicted_intent);

-- Finds the messages worth labelling by hand. Partial index: it only stores
-- the low-confidence rows, so it stays small however big the table gets.
CREATE INDEX IF NOT EXISTS idx_messages_unsure
    ON messages(confidence) WHERE confidence < 0.40;


CREATE TABLE IF NOT EXISTS llm_cache (
    text_key    TEXT        PRIMARY KEY,
    intent      TEXT        NOT NULL,
    confidence  REAL        NOT NULL,
    reason      TEXT,
    model       TEXT,
    hits        INTEGER     NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);


-- ---------------------------------------------------------------------------
-- SECURITY. Supabase is on the public internet, unlike a local SQLite file.
-- Row Level Security blocks ALL access until you write a policy that allows it.
-- Turning it on means a leaked anon key cannot read your customers' data.
-- Your bot connects as the database owner, which bypasses RLS.
-- ---------------------------------------------------------------------------
ALTER TABLE customers     ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders        ENABLE ROW LEVEL SECURITY;
ALTER TABLE refunds       ENABLE ROW LEVEL SECURITY;
ALTER TABLE conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages      ENABLE ROW LEVEL SECURITY;
ALTER TABLE llm_cache     ENABLE ROW LEVEL SECURITY;
