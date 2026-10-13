# AI-generated example code for demonstrating DepCycle.
# Intended for learning and testing, not as production-ready application code.

"""Domain model shared by the service and repository layers."""

from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    """A user record."""

    user_id: int
    name: str
