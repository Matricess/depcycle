from app.models import Order


def save_order(customer_id: str, sku: str) -> Order:
    return Order(customer_id, sku)
