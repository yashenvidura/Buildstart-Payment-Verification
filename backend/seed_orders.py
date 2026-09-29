from datetime import datetime
from decimal import Decimal

from database import SessionLocal
from models import Order


# --------------------------------------------------
# DEMO / TEST ORDERS
# --------------------------------------------------

DEMO_ORDERS = [
    {
        "customer_name":
            "Commercial Bank Test Customer",

        "expected_amount":
            Decimal("4000.00"),

        "expected_account":
            "276100180023877",

        "created_at":
            datetime(2025, 3, 24, 19, 30),
    },

    {
        "customer_name":
            "Commercial Bank Test Customer 2",

        "expected_amount":
            Decimal("70000.00"),

        "expected_account":
            "8020039983",

        "created_at":
            datetime(2022, 9, 4, 15, 30),
    },

    {
        "customer_name":
            "BOC Test Customer",

        "expected_amount":
            Decimal("40000.00"),

        "expected_account":
            "0000092973509",

        "created_at":
            datetime(2024, 12, 30, 20, 30),
    },

    {
        "customer_name":
            "CRDB Test Customer",

        "expected_amount":
            Decimal("140000.00"),

        "expected_account":
            "0752618111",

        "created_at":
            datetime(2022, 2, 23, 15, 0),
    },

    {
        "customer_name":
            "Sampath Test Customer",

        "expected_amount":
            Decimal("5000.00"),

        "expected_account":
            "013510002282",

        "created_at":
            datetime(2018, 9, 20, 13, 30),
    },

    {
        "customer_name":
            "Wrong Amount Test Customer",

        "expected_amount":
            Decimal("75000.00"),

        "expected_account":
            "8020039983",

        "created_at":
            datetime(
                2022,
                9,
                4,
                15,
                30
            ),
    },

    {
        "customer_name":
            "Wrong Account Test Customer",

        "expected_amount":
            Decimal("70000.00"),

        # Deliberately wrong account
        "expected_account":
            "9999999999",

        "created_at":
            datetime(
                2022,
                9,
                4,
                15,
                30
            ),
    },
]


# --------------------------------------------------
# SEED FUNCTION
# --------------------------------------------------

def seed_orders():

    db = SessionLocal()

    try:

        added_count = 0
        skipped_count = 0

        for data in DEMO_ORDERS:

            existing_order = (
                db.query(Order)
                .filter(
                    Order.customer_name
                    == data["customer_name"],

                    Order.expected_account
                    == data["expected_account"],
                )
                .first()
            )


            if existing_order:

                print(
                    f"Skipping existing order "
                    f"#{existing_order.id}: "
                    f"{existing_order.customer_name}"
                )

                skipped_count += 1

                continue


            new_order = Order(
                customer_name=
                    data["customer_name"],

                expected_amount=
                    data["expected_amount"],

                expected_account=
                    data["expected_account"],

                created_at=
                    data["created_at"],
            )


            db.add(new_order)

            db.flush()

            print(
                f"Added order "
                f"#{new_order.id}: "
                f"{new_order.customer_name}"
            )

            added_count += 1


        db.commit()


        print("\n------------------------------")
        print("Seed complete")
        print("------------------------------")

        print(
            f"Added: {added_count}"
        )

        print(
            f"Already existed: "
            f"{skipped_count}"
        )


    except Exception as error:

        db.rollback()

        print(
            "Error while seeding orders:",
            error
        )

        raise


    finally:

        db.close()


# --------------------------------------------------
# RUN
# --------------------------------------------------

if __name__ == "__main__":
    seed_orders()