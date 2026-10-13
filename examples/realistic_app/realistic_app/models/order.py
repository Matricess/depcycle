# AI-generated example code for demonstrating DepCycle.
# Intended for learning and testing, not as production-ready application code.

"""Order domain model."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Order:
    """A simplified order record."""

    order_id: str
