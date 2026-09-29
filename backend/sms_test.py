from sms_parser import extract_sms_fields
from sms_matching import match_sms_evidence
from datetime import datetime

from database import SessionLocal
from models import BankSMS



message = """
Dear Customer,
Your Account 23877 was credited with
LKR 4,000.00 on 24/03/2025 08:10 PM.
Ref: ABC123
"""


sms_fields = extract_sms_fields(
    message
)


receipt_fields = {
    "receipt_reference": "ABC123",
    "transaction_datetime":
        "24/03/2025 08:08 PM"
}


result = match_sms_evidence(
    sms_fields=sms_fields,
    receipt_fields=receipt_fields,
    expected_amount=4000.00,
    expected_account="276100180023877"
)


print("----- SMS FIELDS -----")

for key, value in sms_fields.items():
    print(f"{key}: {value}")


print("\n----- SMS MATCH -----")

print(f"Status: {result['status']}")

for key, value in result["checks"].items():
    print(f"{key}: {value}")


sms_datetime = None

if sms_fields.get("transaction_datetime"):

    sms_datetime = datetime.strptime(
        sms_fields["transaction_datetime"],
        "%d/%m/%Y %I:%M %p"
    )


db = SessionLocal()

try:

    sms_record = BankSMS(
        message_text=message,
        amount=sms_fields.get("amount"),
        account=sms_fields.get("account"),
        reference=sms_fields.get("reference"),
        transaction_datetime=sms_datetime
    )

    db.add(sms_record)

    db.commit()

    db.refresh(sms_record)

    print(
        f"\nBank SMS saved with ID: "
        f"{sms_record.id}"
    )

finally:
    db.close()