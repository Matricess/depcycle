from app.catalog.products import price_for
from app.payments.processor import authorize
from app.shipping.labels import create_label


def place_order(customer_id: str, sku: str) -> str:
    order = price_for(sku, customer_id)
    authorize(order)
    return create_label(order)