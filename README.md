# Customer Support Chatbot (Bitext dataset)

## The files

| file | what it does |
|---|---|
| `call.py` | downloads the dataset from Kaggle into this folder |
| `data.py` | loads the CSVs and tidies them (used by the others) |
| `explore.py` | **look at the data** — run this first |
| `train.py` | trains the intent model, saves `model.joblib` |
| `chat.py` | talk to the bot |
| `responses.py` | **the bot's answers — edit this file to make it yours** |
| `realtest.py` | honest test on hand-written sentences |
| `check.py` | **is the data clean?** — 10 quality checks |
| `why.py` | shows exactly which words the data never learned |
| `proof.py` | tests whether near-copies inflate the score (they don't) |

## How to run

```
python explore.py                 # understand the data
python explore.py get_refund      # look at one intent closely
python train.py --both            # train (about 1 minute)
python chat.py                    # talk to it
python realtest.py                # see the honest score
```

## What the data is

27 intents in 11 categories. Every row is one customer sentence plus a label.

**There are no support-agent replies in the dataset.** It teaches the bot to
understand the question only. The answers in `responses.py` are written by hand.

## Is the data clean?

Run `python check.py` (add `--big` for the large file). Ten checks.

Clean: no empty values, no blank sentences, no sentence labelled two different
ways, and the category/intent structure is consistent. That is genuinely good.

Small issues: 41 rows with a double space; one undocumented flag letter `V`.
The big file also has 12 duplicate rows and is badly unbalanced (121 to 1).

## The important warning

`train.py` reports about 99.9%. `realtest.py` scores about 40% on hand-written
sentences. Trust `realtest.py`.

## Why it gets things wrong

**Not** because of leaking between practice and exam. A grouped split (run
`python proof.py`) still scores 99.9%.

The real reason: **all 29,505 sentences use fewer than 2,000 different words.**
Run `python why.py` to see it. Words like *parcel, receipt, login, refund
status, arrived, stop* never appear even once.

So the model learns the dataset's small vocabulary perfectly, and meets a wall
the moment a customer uses a normal English word the data never contained.

## Tuning

- `CONFIDENCE_THRESHOLD` in `chat.py` — higher means the bot says
  "I don't know" more often instead of giving a wrong answer.
- Add your own real customer sentences to the training data. Even 20 real
  examples per intent will help more than 20,000 generated ones.
