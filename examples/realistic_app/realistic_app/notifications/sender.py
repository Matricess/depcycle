# AI-generated example code for demonstrating DepCycle.
# Intended for learning and testing, not as production-ready application code.

"""Order notification adapter with an intentional service dependency."""

import requests
import realistic_app.services.orders

from realistic_app.models.order import Order


def send_order_created(order: Order) -> str:
    """Prepare a notification message without sending a network request."""
    # This reference creates a deliberate architecture-level import cycle.
    if realistic_app.services.orders.is_valid(order):
        return f"Order {order.order_id} created"
    return "Invalid order"
