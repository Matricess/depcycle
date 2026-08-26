from app.domain.orders import Order


def authorize(order: Order) -> str:
    return f"payment-authorized:{order.customer_id}"