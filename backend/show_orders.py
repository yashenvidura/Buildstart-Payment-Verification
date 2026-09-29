from database import SessionLocal
from models import Order

db = SessionLocal()

try:
    orders = db.query(Order).all()

    print("\n----- ORDERS -----")

    for order in orders:
        print(
            f"ID: {order.id} | "
            f"Customer: {order.customer_name} | "
            f"Amount: {order.expected_amount} | "
            f"Account: {order.expected_account}"
        )

finally:
    db.close()