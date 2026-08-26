from app.repositories import save_order


def checkout_order(customer_id: str, sku: str) -> str:
    order = save_order(customer_id, sku)
    return f"created:{order.sku}"
