from database import SessionLocal
from models import (
    PaymentSubmission,
    BankSMS,
    Order,
)


def clear_all_data():

    db = SessionLocal()

    try:
        # Delete payment submissions first
        # because they reference orders.
        deleted_payments = (
            db.query(PaymentSubmission)
            .delete()
        )

        # Delete stored SMS records.
        deleted_sms = (
            db.query(BankSMS)
            .delete()
        )

        # Delete orders last.
        deleted_orders = (
            db.query(Order)
            .delete()
        )

        db.commit()

        print(
            f"Deleted {deleted_payments} "
            "payment submissions."
        )

        print(
            f"Deleted {deleted_sms} "
            "bank SMS records."
        )

        print(
            f"Deleted {deleted_orders} "
            "orders."
        )

        print(
            "\nAll database data cleared successfully."
        )

        print(
            "Database tables were NOT deleted."
        )

    except Exception as error:

        db.rollback()

        print(
            "Failed to clear database:"
        )

        print(error)

        raise

    finally:
        db.close()


if __name__ == "__main__":
    clear_all_data()