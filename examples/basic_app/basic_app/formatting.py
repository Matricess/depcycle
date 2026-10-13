# AI-generated example code for demonstrating DepCycle.
# Intended for learning and testing, not as production-ready application code.

"""Format messages for display."""

from basic_app.greetings import greeting


def welcome_message(name: str) -> str:
    """Build a formatted welcome message."""
    return f"*** {greeting(name)} ***"
