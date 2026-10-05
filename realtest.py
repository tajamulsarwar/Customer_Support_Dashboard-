"""
realtest.py  --  the honest test.

train.py scores 99.9%, but that score is flattering -- NOT because of
leaking between practice and exam (a grouped split scores 99.9% too), but
because the whole dataset uses under 2,000 different words. Any sentence
built from those words is easy. Real customers use other words.

These sentences are written by hand and use everyday wording.
This is much closer to how the bot will do with real customers.
"""

from chat import Bot, CONFIDENCE_THRESHOLD

FRESH = [
    ("my parcel still has not arrived, where is it?",        "track_order"),
    ("been waiting 2 weeks for my package",                  "track_order"),
    ("the shirt doesnt fit, can i send it back",             "check_refund_policy"),
    ("i want my money back for the broken lamp",             "get_refund"),
    ("card got declined twice",                              "payment_issue"),
    ("do you take apple pay",                                "check_payment_methods"),
    ("i forgot my login details",                            "recover_password"),
    ("put me through to a real person please",               "contact_human_agent"),
    ("stop sending me emails",                               "newsletter_subscription"),
    ("scrap my order please i changed my mind",              "cancel_order"),
    ("moved house, need to update where you send things",    "change_shipping_address"),
    ("need the receipt for tax purposes",                    "get_invoice"),
    ("this is the worst service i have ever had",            "complaint"),
    ("how long till it gets here",                           "delivery_period"),
    ("close my profile permanently",                         "delete_account"),
    # These are deliberately outside the 27 intents. A good bot says
    # "I don't know" instead of guessing.
    ("what is the weather today",                            "OUT_OF_SCOPE"),
    ("do you sell laptops",                                  "OUT_OF_SCOPE"),
    ("are you a robot",                                      "OUT_OF_SCOPE"),
]

def run():
  bot = Bot()
  right = wrong = refused = 0
  in_scope = [t for t in FRESH if t[1] != "OUT_OF_SCOPE"]

  print(f"Confidence threshold: {CONFIDENCE_THRESHOLD:.0%}\n")
  print(f"{'sentence':<50} {'expected':<24} {'bot said':<24} {'sure':>5}  ")
  print("-" * 112)

  for text, expected in FRESH:
      ranked = bot.guess(text)
      got, score = ranked[0]
      said_idk = score < CONFIDENCE_THRESHOLD

      if expected == "OUT_OF_SCOPE":
          mark = "GOOD (said I don't know)" if said_idk else "BAD (guessed anyway)"
          shown = "-- don't know --" if said_idk else got
      elif said_idk:
          refused += 1; mark = "unsure"; shown = "-- don't know --"
      elif got == expected:
          right += 1; mark = "correct"; shown = got
      else:
          wrong += 1; mark = "WRONG"; shown = got

      print(f"{text[:48]:<50} {expected:<24} {shown:<24} {score:>4.0%}  {mark}")

  print("-" * 112)
  total = len(in_scope)
  print(f"\nOn {total} real questions:  {right} correct, {wrong} wrong, {refused} said 'I don't know'.")
  print(f"Correct rate on new, unseen wording: {right/total:.0%}")
  print("")
  print("Compare that with the 99.9% from train.py. Run 'python why.py' to see")
  print("exactly which words caused each failure.")


if __name__ == "__main__":
    run()
