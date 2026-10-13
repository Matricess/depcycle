# AI-generated example code for demonstrating DepCycle.
# Intended for learning and testing, not as production-ready application code.

"""API-facing handlers for the order service."""

from realistic_app.services.orders import create_order
from realistic_app.models.order import Order


def create_order_route(order_id: str) -> Order:
    """Stand in for an API route that creates an order."""
    return create_order(order_id)
