"""
heldout.py  --  30 messages the prompt was NOT tuned on.

realtest.FRESH is what I looked at while building things, so scores on it are
optimistic. These were written separately and are only used to check whether a
change to the prompt really helps.
"""

HELDOUT = [
    ("the courier says delivered but nothing is here",       "track_order"),
    ("any update on my shipment?",                           "track_order"),
    ("where has my stuff got to",                            "track_order"),
    ("i ordered the wrong size, can you cancel it",          "cancel_order"),
    ("please withdraw my order before it ships",             "cancel_order"),
    ("can i swap the colour on my order",                    "change_order"),
    ("i want to buy two of the blue kettles",                "place_order"),
    ("the postcode on my delivery is wrong",                 "change_shipping_address"),
    ("add my work address for deliveries",                   "set_up_shipping_address"),
    ("do you charge if i cancel?",                           "check_cancellation_fee"),
    ("what is your returns policy",                          "check_refund_policy"),
    ("this item was faulty, refund me",                      "get_refund"),
    ("has my refund been processed yet",                     "track_refund"),
    ("my card was charged twice",                            "payment_issue"),
    ("can i pay by bank transfer",                           "check_payment_methods"),
    ("email me the vat receipt for order 4421",              "get_invoice"),
    ("show me my past bills",                                "check_invoice"),
    ("i can't sign in, wrong password",                      "recover_password"),
    ("the sign up page just spins forever",                  "registration_problems"),
    ("change the email on my profile",                       "edit_account"),
    ("i would like to erase my account and data",            "delete_account"),
    ("open a new account for me",                            "create_account"),
    ("i have two logins, how do i move between them",        "switch_account"),
    ("give me a phone number for your team",                 "contact_customer_service"),
    ("can i talk to someone real",                           "contact_human_agent"),
    ("unsubscribe me from your mailing list",                "newsletter_subscription"),
    ("i want to leave a five star rating",                   "review"),
    ("your staff were rude and i am furious",                "complaint"),
    ("do you offer next day shipping",                       "delivery_options"),
    ("how many days until it arrives",                       "delivery_period"),
]


# Harder: typos, slang, vague wording, and the pairs of intents that are easy to
# mix up (track_order vs delivery_period, get_refund vs check_refund_policy,
# get_invoice vs check_invoice, cancel_order vs delete_account).
HARD = [
    ("its been 3 weeks and my package still isnt here",        "track_order"),
    ("whens my order landing",                                 "track_order"),
    ("tracking hasnt updated in days",                         "track_order"),
    ("usually how long does shipping take to scotland",        "delivery_period"),
    ("can i send this back for my money",                      "get_refund"),
    ("am i allowed to return worn shoes",                      "check_refund_policy"),
    ("give me my cash back now",                               "get_refund"),
    ("send me a copy of the receipt",                          "get_invoice"),
    ("what invoices do i have",                                "check_invoice"),
    ("scrap the order i placed this morning",                  "cancel_order"),
    ("get rid of my profile",                                  "delete_account"),
    ("cant get in, forgot everything",                         "recover_password"),
    ("my bank took the money but the site says failed",        "payment_issue"),
    ("do you take amex",                                       "check_payment_methods"),
    ("id like to swap the size on what i bought",              "change_order"),
    ("send it to my mums house instead",                       "change_shipping_address"),
    ("stop the marketing stuff",                               "newsletter_subscription"),
    ("this is a joke, three broken items in a row",            "complaint"),
    ("get me a human",                                         "contact_human_agent"),
    ("whats your opening hours",                               "contact_customer_service"),
]
