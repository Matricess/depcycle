# AI-generated example code for demonstrating DepCycle.
# Intended for learning and testing, not as production-ready application code.

"""Order orchestration service."""

import realistic_app.notifications.sender
from realistic_app.models.order import Order
from realistic_app.repositories.orders import save_order


def is_valid(order: Order) -> bool:
    """Return whether an order has a non-empty identifier."""
    return bool(order.order_id.strip())


def create_order(order_id: str) -> Order:
    """Create, persist, and announce an order."""
    order = Order(order_id=order_id)
    save_order(order)
    if is_valid(order):
        realistic_app.notifications.sender.send_order_created(order)
    return order
