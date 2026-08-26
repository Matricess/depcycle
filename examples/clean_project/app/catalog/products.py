from app.domain.orders import Order


def price_for(sku: str, customer_id: str) -> Order:
    prices = {"sku-laptop-15": 129900, "sku-monitor-27": 39900}
    return Order(customer_id=customer_id, sku=sku, amount=prices.get(sku, 0))