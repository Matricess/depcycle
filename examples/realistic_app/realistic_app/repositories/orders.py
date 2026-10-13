# AI-generated example code for demonstrating DepCycle.
# Intended for learning and testing, not as production-ready application code.

"""In-memory repository for orders."""

from realistic_app.models.order import Order

_ORDERS: dict[str, Order] = {}


def save_order(order: Order) -> None:
    """Save an order in a minimal in-memory store."""
    _ORDERS[order.order_id] = order
