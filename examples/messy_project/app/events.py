from app.utils import notify_customer


def publish_order_event(order) -> None:
    notify_customer(order.customer_id)
