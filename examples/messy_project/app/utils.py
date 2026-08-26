from app.repositories import save_order


def notify_customer(customer_id: str) -> None:
    save_order(customer_id, "notification-audit")
