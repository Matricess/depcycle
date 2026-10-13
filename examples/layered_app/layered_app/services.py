# AI-generated example code for demonstrating DepCycle.
# Intended for learning and testing, not as production-ready application code.

"""Business logic layer for users."""

from layered_app.models import User
from layered_app.repositories import save_user


def register_user(user_id: int, name: str) -> User:
    """Create a user and save it through the repository layer."""
    user = User(user_id=user_id, name=name)
    save_user(user)
    return user
