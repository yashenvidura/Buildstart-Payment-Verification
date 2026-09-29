from pathlib import Path
from datetime import datetime

from PIL import Image
import pytesseract

from receipt_parser import extract_receipt_fields
from verification_test import verify_basic_evidence
from fraud_checks import (
    check_reference_reuse,
    calculate_file_hash,
    check_exact_duplicate,
    calculate_perceptual_hash,
    check_similar_image,
)
from decision_engine import make_decision
from image_checks import check_image_quality

from database import SessionLocal
from models import Order, PaymentSubmission


# --------------------------------------------------
# TESSERACT CONFIGURATION
# --------------------------------------------------

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


# --------------------------------------------------
# 1. LOAD PAYMENT RECEIPT
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

image_path = BASE_DIR / "test_images" / "1.webp"


# Calculate exact and perceptual image hashes
image_hash = calculate_file_hash(image_path)

perceptual_hash = calculate_perceptual_hash(
    image_path
)


# Check receipt image quality
image_quality_results = check_image_quality(
    image_path
)

print("\n----- IMAGE QUALITY CHECKS -----")

for key, value in image_quality_results.items():
    print(f"{key}: {value}")


# Open image for OCR
image = Image.open(image_path)


print("\n----- IMAGE HASHES -----")
print(f"SHA-256: {image_hash}")
print(f"Perceptual hash: {perceptual_hash}")


# --------------------------------------------------
# 2. OCR
# --------------------------------------------------

text = pytesseract.image_to_string(image)

print("\n----- OCR OUTPUT -----")
print(text)


# --------------------------------------------------
# 3. EXTRACT RECEIPT FIELDS
# --------------------------------------------------

fields = extract_receipt_fields(text)

print("\n----- EXTRACTED FIELDS -----")

for key, value in fields.items():
    print(f"{key}: {value}")


# --------------------------------------------------
# 4. LOAD ORDER FROM DATABASE
# --------------------------------------------------

db = SessionLocal()

try:
    order_id = 1

    order = db.get(
        Order,
        order_id
    )

    if order is None:
        raise ValueError(
            f"Order {order_id} was not found."
        )

    expected_amount = float(
        order.expected_amount
    )

    expected_account = (
        order.expected_account
    )

    order_created_at = (
        order.created_at
    )

    print("\n----- ORDER FROM DATABASE -----")
    print(f"Order ID: {order.id}")
    print(f"Customer: {order.customer_name}")
    print(
        f"Expected amount: "
        f"{order.expected_amount}"
    )
    print(
        f"Expected account: "
        f"{order.expected_account}"
    )
    print(
        f"Created at: "
        f"{order.created_at}"
    )

finally:
    db.close()


# --------------------------------------------------
# 5. VERIFY RECEIPT EVIDENCE
# --------------------------------------------------

verification_results = verify_basic_evidence(
    fields,
    expected_amount,
    expected_account,
    order_created_at
)

print("\n----- VERIFICATION CHECKS -----")

for key, value in verification_results.items():
    print(f"{key}: {value}")


# --------------------------------------------------
# 6. LOAD PREVIOUS PAYMENTS FROM DATABASE
# --------------------------------------------------

db = SessionLocal()

try:
    previous_payments = db.query(
        PaymentSubmission
    ).all()

    used_references = {
        payment.receipt_reference
        for payment in previous_payments
        if payment.receipt_reference
    }

    used_image_hashes = {
        payment.sha256_hash
        for payment in previous_payments
        if payment.sha256_hash
    }

    used_perceptual_hashes = {
        payment.perceptual_hash
        for payment in previous_payments
        if payment.perceptual_hash
    }

finally:
    db.close()


# --------------------------------------------------
# 6A. FRAUD CHECKS
# --------------------------------------------------

reference_reuse_check = check_reference_reuse(
    fields.get("receipt_reference"),
    used_references
)

exact_duplicate_check = check_exact_duplicate(
    image_hash,
    used_image_hashes
)

similar_image_check = check_similar_image(
    perceptual_hash,
    used_perceptual_hashes
)

fraud_results = {
    "reference_reuse": reference_reuse_check,
    "exact_duplicate": exact_duplicate_check,
    "similar_image": similar_image_check,
}

print("\n----- FRAUD CHECKS -----")

for key, value in fraud_results.items():
    print(f"{key}: {value}")


# --------------------------------------------------
# 7. SUSPICIOUS INDICATORS
# --------------------------------------------------

suspicious_indicators = []


if image_quality_results.get(
    "metadata_suspicious"
):
    suspicious_indicators.append(
        "Image contains editing-software metadata."
    )


if (
    fraud_results["similar_image"]["status"]
    == "SIMILAR"
):
    suspicious_indicators.append(
        "Image is visually similar "
        "to a previous submission."
    )


print("\n----- SUSPICIOUS INDICATORS -----")

if suspicious_indicators:

    for indicator in suspicious_indicators:
        print(f"- {indicator}")

else:
    print("None")


# --------------------------------------------------
# 8. FINAL DECISION
# --------------------------------------------------

decision = make_decision(
    verification_results,
    fraud_results,
    image_quality_results
)

print("\n----- FINAL DECISION -----")

for key, value in decision.items():
    print(f"{key}: {value}")


# --------------------------------------------------
# 9. PREPARE DATABASE VALUES
# --------------------------------------------------

# Convert OCR transaction date text
# into a Python datetime object.

transaction_time = None

if fields.get("transaction_datetime"):

    try:
        transaction_time = datetime.strptime(
            fields["transaction_datetime"],
            "%d/%m/%Y %I:%M %p"
        )

    except ValueError:
        transaction_time = None


# Get the extracted payment amount.

extracted_amount = None

if verification_results["extracted_amounts"]:

    extracted_amount = (
        verification_results[
            "extracted_amounts"
        ][0]
    )


# Only store the expected business account
# if we actually confirmed that it appeared
# in the receipt.

extracted_account = None

if (
    verification_results["account_check"]
    == "MATCH"
):
    extracted_account = (
        expected_account
    )


# --------------------------------------------------
# 10. SAVE PAYMENT SUBMISSION
# --------------------------------------------------

db = SessionLocal()

try:

    payment = PaymentSubmission(
        order_id=order_id,

        receipt_reference=fields.get(
            "receipt_reference"
        ),

        extracted_amount=extracted_amount,

        extracted_account=extracted_account,

        transaction_datetime=transaction_time,

        transaction_status=fields.get(
            "status"
        ),

        sha256_hash=image_hash,

        perceptual_hash=perceptual_hash,

        raw_ocr_text=text,

        final_decision=decision[
            "decision"
        ],

        decision_reason=decision[
            "reason"
        ]
    )

    db.add(payment)

    db.commit()

    db.refresh(payment)

    print("\n----- DATABASE -----")

    print(
        f"Payment submission saved "
        f"with ID: {payment.id}"
    )

finally:
    db.close()