from database import SessionLocal
from models import (
    PaymentSubmission,
    BankSMS,
)


def clear_test_data():

    db = SessionLocal()

    try:

        deleted_payments = (
            db.query(
                PaymentSubmission
            )
            .delete()
        )

        deleted_sms = (
            db.query(
                BankSMS
            )
            .delete()
        )


        db.commit()


        print(
            f"Deleted {deleted_payments} "
            f"payment submissions."
        )

        print(
            f"Deleted {deleted_sms} "
            f"bank SMS records."
        )

        print(
            "Test payment data cleared successfully."
        )

        print(
            "Orders were NOT deleted."
        )


    except Exception as error:

        db.rollback()

        print(
            "Failed to clear test data:"
        )

        print(error)

        raise


    finally:

        db.close()


if __name__ == "__main__":
    clear_test_data()