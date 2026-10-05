"""
responses.py  --  the bot's answers.

IMPORTANT: the Bitext data does NOT contain any answers. It only teaches
the bot to RECOGNISE what a customer wants. The replies below are written
by hand. This is the file you edit to make the bot yours.
"""

RESPONSES = {
    "cancel_order":            "I can help you cancel an order. Please give me your order number and I will cancel it for you.",
    "change_order":            "I can change your order. Tell me the order number and what you would like to change.",
    "change_shipping_address": "To change the delivery address, go to My Orders, pick the order, and press Edit Address. I can also do it for you if you send me the new address.",
    "check_cancellation_fee":  "Cancelling is free before the order is shipped. After it ships, a fee of 5% of the order value applies.",
    "check_invoice":           "You can see all your invoices under My Account > Invoices. Which one would you like me to check?",
    "check_payment_methods":   "We accept Visa, Mastercard, American Express, PayPal, and bank transfer.",
    "check_refund_policy":     "You can return anything within 30 days of delivery for a full refund, as long as it is unused.",
    "complaint":               "I am sorry this happened, and thank you for telling us. Please describe the problem and I will pass it to the right team today.",
    "contact_customer_service":"You can reach our team at support@example.com, or on 0800 123 456, Monday to Friday, 9am to 6pm.",
    "contact_human_agent":     "Of course. I am connecting you to a human agent now. Please wait a moment.",
    "create_account":          "Creating an account is quick. Go to the Sign Up page, enter your email, and choose a password.",
    "delete_account":          "I can delete your account. Please note this cannot be undone. Shall I go ahead?",
    "delivery_options":        "We offer standard delivery (3 to 5 days, free), express delivery (1 to 2 days), and collection from a local pickup point.",
    "delivery_period":         "Standard delivery takes 3 to 5 working days. Express delivery arrives in 1 to 2 working days.",
    "edit_account":            "You can update your details under My Account > Settings. Which detail would you like to change?",
    "get_invoice":             "I can send your invoice by email. Please tell me the order number.",
    "get_refund":              "I can start your refund. Please give me the order number. Refunds reach your account in 5 to 7 working days.",
    "newsletter_subscription": "I can add you to or remove you from our newsletter. Which one would you like?",
    "payment_issue":           "I am sorry the payment did not work. Please check the card details and the expiry date. If it still fails, try another card, and I will look into it from our side.",
    "place_order":             "Happy to help you order. Tell me the item you want and how many, and I will add it to your basket.",
    "recover_password":        "No problem. Press 'Forgot password' on the login page and we will email you a reset link straight away.",
    "registration_problems":   "Sorry the sign up is not working. Could you tell me the error message you see? Often the email is already registered.",
    "review":                  "Thank you for wanting to leave a review. You will find a Review button on the product page, or reply here and I will record it.",
    "set_up_shipping_address": "I can add a delivery address to your account. Please send me the full address including the postcode.",
    "switch_account":          "To switch account, log out from the menu in the top right, then log in with the other email address.",
    "track_order":             "I can track your order. Please give me the order number and I will tell you exactly where it is.",
    "track_refund":            "I can check your refund. Please give me the order number. Refunds normally take 5 to 7 working days after approval.",

    # Small talk
    "greeting":                "Hello! How can I help you today?",
    "thanks":                  "You are welcome! Is there anything else I can help with?",
    "goodbye":                 "Goodbye, and thank you for contacting us. Have a nice day!",
}

# Said when the bot is not confident enough about any intent.
FALLBACK = ("I am not sure I understood that. Could you say it a different way? "
            "Or type 'agent' and I will pass you to a person.")
