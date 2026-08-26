from app.domain.orders import Order


def create_label(order: Order) -> str:
    return f"label-created:{order.sku}"