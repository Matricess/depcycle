from app.events import publish_order_event


class Order:
    def __init__(self, customer_id: str, sku: str):
        self.customer_id = customer_id
        self.sku = sku
        publish_order_event(self)
