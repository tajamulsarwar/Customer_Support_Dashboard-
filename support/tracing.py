"""
tracing.py  --  send a log of each step to LangSmith, if it is set up.

Turn it on in .env:
    LANGSMITH_TRACING=true
    LANGSMITH_API_KEY=lsv2_...
    LANGSMITH_PROJECT=customer-support

Turn it off with LANGSMITH_TRACING=false. Then nothing is sent anywhere.

If the langsmith package is not installed, `traceable` does nothing and the bot
works exactly as before.

Note: when tracing is on, customer messages are sent to LangSmith's servers.
"""

try:
    from langsmith import traceable
except ImportError:
    def traceable(*args, **kwargs):
        # Used both as @traceable and as @traceable(...).
        if len(args) == 1 and callable(args[0]) and not kwargs:
            return args[0]
        return lambda fn: fn
