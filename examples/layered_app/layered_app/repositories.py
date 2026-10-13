# AI-generated example code for demonstrating DepCycle.
# Intended for learning and testing, not as production-ready application code.

"""Persistence layer for user records."""

from layered_app.models import User


_STORAGE: dict[int, User] = {}


def save_user(user: User) -> None:
    """Save a user in an in-memory store for demonstration purposes."""
    _STORAGE[user.user_id] = user


def get_user(user_id: int) -> User | None:
    """Return a stored user, if present."""
    return _STORAGE.get(user_id)
