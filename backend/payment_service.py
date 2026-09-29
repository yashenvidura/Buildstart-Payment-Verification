from datetime import datetime
from PIL import Image

import pytesseract

from database import SessionLocal
from models import (Order, PaymentSubmission,BankSMS)

from receipt_parser import extract_receipt_fields
from verification_test import verify_basic_evidence
from fraud_checks import (
    calculate_file_hash,
    calculate_perceptual_hash,
    check_reference_reuse,
    check_exact_duplicate,
    check_similar_image,
)
from image_checks import check_image_quality
from decision_engine import make_decision

from sms_parser import extract_sms_fields

from sms_matching import (
    match_sms_evidence,
    parse_sms_datetime
)

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)

def process_payment(image_path, order_id,sms_text=None):
    """
    Process one payment receipt against one order.

    Returns a structured verification result.
    """

    # ---------------------------------
    # 1. IMAGE ANALYSIS
    # ---------------------------------

    image_hash = calculate_file_hash(
        image_path
    )

    perceptual_hash = calculate_perceptual_hash(
        image_path
    )

    image_quality = check_image_quality(
        image_path
    )


    # ---------------------------------
    # 2. OCR
    # ---------------------------------

    image = Image.open(image_path)

    raw_text = pytesseract.image_to_string(
        image
    )


    # ---------------------------------
    # 3. FIELD EXTRACTION
    # ---------------------------------

    fields = extract_receipt_fields(
        raw_text
    )


    # ---------------------------------
    # 4. LOAD ORDER
    # ---------------------------------

    db = SessionLocal()

    try:
        order = db.get(
            Order,
            order_id
        )

        if order is None:
            raise ValueError(
                f"Order {order_id} not found."
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

    finally:
        db.close()


    # ---------------------------------
    # 5. VERIFY RECEIPT
    # ---------------------------------

    verification_results = verify_basic_evidence(
        fields,
        expected_amount,
        expected_account,
        order_created_at
    )

        # ---------------------------------
    # SMS EVIDENCE
    # ---------------------------------

    sms_fields = None

    sms_results = {
        "status": "NO_SMS",
        "checks": {}
    }

    if sms_text:

        sms_fields = extract_sms_fields(
            sms_text
        )

        sms_results = match_sms_evidence(
            sms_fields=sms_fields,
            receipt_fields=fields,
            expected_amount=expected_amount,
            expected_account=expected_account
        )


    # ---------------------------------
    # 6. LOAD PAYMENT HISTORY
    # ---------------------------------

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


    # ---------------------------------
    # 7. FRAUD CHECKS
    # ---------------------------------

    reference_check = check_reference_reuse(
        fields.get("receipt_reference"),
        used_references
    )

    duplicate_check = check_exact_duplicate(
        image_hash,
        used_image_hashes
    )

    similar_check = check_similar_image(
        perceptual_hash,
        used_perceptual_hashes
    )

    fraud_results = {
        "reference_reuse": reference_check,
        "exact_duplicate": duplicate_check,
        "similar_image": similar_check,
    }


    # ---------------------------------
    # 8. DECISION
    # ---------------------------------

    decision = make_decision(
        verification_results,
        fraud_results,
        image_quality,
        sms_results
    )


        # ---------------------------------
    # SMS CONFLICT
    # ---------------------------------

    if (
        sms_results
        and sms_results.get("status")
        == "CONFLICT"
    ):
        return {
            "decision": "NEEDS VERIFICATION",
            "reason": (
                "The bank SMS conflicts with "
                "the submitted payment evidence."
            ),
            "next_action": (
                "Review the receipt and bank "
                "notification manually."
            )
        }

        # ---------------------------------
    # SAVE SMS EVIDENCE
    # ---------------------------------

    sms_record_id = None

    if sms_text:

        sms_datetime = parse_sms_datetime(
            sms_fields.get(
                "transaction_datetime"
            )
        )

        db = SessionLocal()

        try:

            sms_record = BankSMS(
                message_text=sms_text,

                amount=sms_fields.get(
                    "amount"
                ),

                account=sms_fields.get(
                    "account"
                ),

                reference=sms_fields.get(
                    "reference"
                ),

                transaction_datetime=sms_datetime
            )

            db.add(sms_record)

            db.commit()

            db.refresh(sms_record)

            sms_record_id = sms_record.id

        finally:
            db.close()

    # ---------------------------------
    # 9. PREPARE VALUES FOR DATABASE
    # ---------------------------------

    transaction_time = None

    if fields.get("transaction_datetime"):
        try:
            transaction_time = datetime.strptime(
                fields["transaction_datetime"],
                "%d/%m/%Y %I:%M %p"
            )
        except ValueError:
            transaction_time = None


    extracted_amount = None

    if verification_results["extracted_amounts"]:
        extracted_amount = verification_results[
            "extracted_amounts"
        ][0]


    extracted_account = None

    if verification_results["account_check"] == "MATCH":
        extracted_account = expected_account


    # ---------------------------------
    # 10. SAVE PAYMENT SUBMISSION
    # ---------------------------------

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
            transaction_status=fields.get("status"),
            sha256_hash=image_hash,
            perceptual_hash=perceptual_hash,
            raw_ocr_text=raw_text,
            final_decision=decision["decision"],
            decision_reason=decision["reason"]
        )

        db.add(payment)

        db.commit()

        db.refresh(payment)

        payment_id = payment.id

    finally:
        db.close()


    # ---------------------------------
    # 11. RETURN RESULT
    # ---------------------------------

    return {
        "payment_submission_id": payment_id,

        "decision": decision["decision"],
        "reason": decision["reason"],
        "next_action": decision["next_action"],

        "extracted_fields": fields,

        "verification": verification_results,

        "fraud": fraud_results,

        "image_quality": image_quality,

        "additional_reasons": decision.get(
            "additional_reasons",
            []
        ),

        "suspicious_indicators": decision.get(
            "suspicious_indicators",
            []
        ),

        "confidence": decision.get(
            "confidence",
            "UNKNOWN"
        )
    }
