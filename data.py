"""
data.py  --  one place that loads the Bitext data for every other script.

Nothing here trains anything. It just finds the CSV files, cleans them up
a little, and hands back a pandas table with 4 columns:

    flags | utterance | category | intent
"""

from pathlib import Path
import pandas as pd

ROOT = Path(__file__).parent
BASE = ROOT / "datasets/bitext/training-dataset-for-chatbotsvirtual-assistants/versions/2"

# The small, FAIR file (about 300 rows for every intent).
FILE_B = BASE / "Bitext_Sample_Customer_Service_Training_Dataset/Training/Bitext_Sample_Customer_Service_Training_Dataset.csv"

# The big, UNFAIR file (from 36 up to 4366 rows per intent).
FILE_A = BASE / ("20000-Utterances-Training-dataset-for-chatbots-virtual-assistant-Bitext-sample/"
                 "20000-Utterances-Training-dataset-for-chatbots-virtual-assistant-Bitext-sample/"
                 "20000-Utterances-Training-dataset-for-chatbots-virtual-assistant-Bitext-sample.csv")

# Our own hand-written file: greetings, thanks and goodbyes. Bitext has no small
# talk, so without this the bot answered "thank you" with "I did not understand".
FILE_SMALLTALK = ROOT / "smalltalk.csv"

# The two files spell a few labels differently. We make them the same
# so the files can be joined together without creating fake extra labels.
RENAME_INTENT = {"check_invoices": "check_invoice"}
RENAME_CATEGORY = {"INVOICES": "INVOICE", "REFUNDS": "REFUND", "SHIPPING": "SHIPPING_ADDRESS"}


def load(which="balanced"):
    """which = 'balanced' (file B), 'big' (file A), or 'both'."""
    if which == "balanced":
        paths = [FILE_B]
    elif which == "big":
        paths = [FILE_A]
    elif which == "both":
        paths = [FILE_B, FILE_A]
    else:
        raise ValueError("which must be 'balanced', 'big' or 'both'")

    frames = []
    for p in paths:
        if not p.exists():
            raise FileNotFoundError(f"Missing data file:\n  {p}\nRun call.py first to download it.")
        # utf-8-sig removes the invisible marker character at the start of the file
        frames.append(pd.read_csv(p, encoding="utf-8-sig"))
    frames.append(pd.read_csv(FILE_SMALLTALK, encoding="utf-8-sig"))

    df = pd.concat(frames, ignore_index=True)

    df["intent"] = df["intent"].replace(RENAME_INTENT)
    df["category"] = df["category"].replace(RENAME_CATEGORY)

    # Tidy the text and drop rows that say exactly the same thing.
    df["utterance"] = df["utterance"].astype(str).str.strip()
    df["flags"] = df["flags"].astype(str).str.strip()
    df = df.drop_duplicates(subset=["utterance", "intent"]).reset_index(drop=True)

    return df
