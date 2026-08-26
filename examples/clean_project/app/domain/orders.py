from dataclasses import dataclass


@dataclass
class Order:
    customer_id: str
    sku: str
    amount: int