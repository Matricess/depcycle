from app.services import checkout_order


def checkout(customer_id: str, sku: str) -> str:
    return checkout_order(customer_id, sku)
