from datetime import datetime

from database import SessionLocal
from models import Order


db = SessionLocal()

try:
    new_order = Order(
        customer_name="Test Customer",
        expected_amount=4000.00,
        expected_account="276100180023877",
        created_at=datetime(
            2025,
            3,
            24,
            19,
            30
        )
    )

    db.add(new_order)

    db.commit()

    db.refresh(new_order)

    print("Order created successfully")

    print(f"Order ID: {new_order.id}")
    print(f"Customer: {new_order.customer_name}")
    print(f"Expected amount: {new_order.expected_amount}")
    print(f"Expected account: {new_order.expected_account}")
    print(f"Created at: {new_order.created_at}")

finally:
    db.close()