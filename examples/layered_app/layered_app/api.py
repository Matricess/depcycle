# AI-generated example code for demonstrating DepCycle.
# Intended for learning and testing, not as production-ready application code.

"""API-facing functions for the layered example."""

from layered_app.models import User
from layered_app.services import register_user


def create_user_endpoint(user_id: int, name: str) -> User:
    """Stand in for an API route that registers a user."""
    return register_user(user_id, name)
