def make_decision(
    results,
    fraud_results,
    image_quality,
    sms_results=None
):
    """
    Combine verification, fraud, image quality,
    and SMS evidence into a final decision.

    Decisions:
    - APPROVED
    - REJECTED
    - NEEDS VERIFICATION
    """

    reject_reasons = []
    verification_reasons = []
    suspicious_indicators = []

    sms_results = sms_results or {
        "status": "NO_SMS",
        "checks": {}
    }


    # --------------------------------------------------
    # 1. STRONG FRAUD / REJECTION EVIDENCE
    # --------------------------------------------------

    if (
        fraud_results.get("exact_duplicate")
        == "DUPLICATE"
    ):
        reject_reasons.append(
            "This exact payment receipt image "
            "has already been submitted."
        )


    if (
        fraud_results.get("reference_reuse")
        == "REUSED"
    ):
        reject_reasons.append(
            "The receipt reference has already "
            "been used in a previous submission."
        )


    # --------------------------------------------------
    # 2. ORDER / RECEIPT MISMATCHES
    # --------------------------------------------------

    if results.get("amount_check") == "MISMATCH":
        reject_reasons.append(
            "The submitted payment amount does "
            "not match the order amount."
        )


    if results.get("account_check") == "MISMATCH":
        reject_reasons.append(
            "The payment receipt does not match "
            "the expected beneficiary account."
        )


    if results.get("status_check") == "FAILED":
        reject_reasons.append(
            "The receipt indicates that the "
            "transaction failed."
        )


    if results.get("date_check") == "OLD":
        reject_reasons.append(
            "The payment occurred before this "
            "order was created."
        )


    # --------------------------------------------------
    # 3. MISSING / UNCERTAIN RECEIPT EVIDENCE
    # --------------------------------------------------

    if results.get("amount_check") == "MISSING":
        verification_reasons.append(
            "The payment amount could not be "
            "reliably extracted."
        )


    if results.get("account_check") == "MISSING":
        verification_reasons.append(
            "The beneficiary account could not "
            "be reliably extracted."
        )


    if results.get("status_check") in {
        "MISSING",
        "UNKNOWN",
        "PENDING"
    }:
        verification_reasons.append(
            "The transaction status is not "
            "confirmed as successful."
        )


    if results.get("reference_check") == "MISSING":
        verification_reasons.append(
            "No reliable receipt reference "
            "was detected."
        )


    if results.get("date_check") in {
        "MISSING",
        "INVALID"
    }:
        verification_reasons.append(
            "The transaction date could not "
            "be reliably verified."
        )


    if (
        results.get("date_check")
        == "OUTSIDE_WINDOW"
    ):
        verification_reasons.append(
            "The payment is outside the normal "
            "verification time window."
        )


    # --------------------------------------------------
    # 4. IMAGE QUALITY
    # --------------------------------------------------

    if image_quality.get("readable") is False:
        verification_reasons.append(
            "The submitted image could not "
            "be read reliably."
        )


    if (
        image_quality.get("resolution_check")
        == "LOW"
    ):
        verification_reasons.append(
            "The receipt image resolution "
            "is too low for reliable verification."
        )


    if (
        image_quality.get("blur_check")
        == "BLURRY"
    ):
        verification_reasons.append(
            "The receipt image appears blurry."
        )


    if image_quality.get(
        "brightness_check"
    ) in {
        "TOO_DARK",
        "TOO_BRIGHT"
    }:
        verification_reasons.append(
            "The receipt image lighting makes "
            "automatic verification unreliable."
        )


    # Metadata is only suspicious evidence.
    # It is NOT proof of fraud.

    if image_quality.get(
        "metadata_suspicious"
    ):
        suspicious_indicators.append(
            "Editing-software metadata was "
            "detected in the submitted image."
        )


    # --------------------------------------------------
    # 5. PERCEPTUAL IMAGE SIMILARITY
    # --------------------------------------------------

    similar_result = fraud_results.get(
        "similar_image"
    )

    if isinstance(similar_result, dict):

        if (
            similar_result.get("status")
            == "SIMILAR"
        ):
            verification_reasons.append(
                "The receipt image is visually "
                "similar to a previous submission."
            )

            suspicious_indicators.append(
                "Perceptual image similarity "
                "was detected."
            )


    # --------------------------------------------------
    # 6. BANK SMS EVIDENCE
    # --------------------------------------------------

    sms_status = sms_results.get(
        "status",
        "NO_SMS"
    )


    if sms_status == "CONFLICT":
        verification_reasons.append(
            "The bank SMS conflicts with "
            "the submitted payment evidence."
        )


    elif sms_status == "PARTIAL":
        suspicious_indicators.append(
            "The bank SMS only partially "
            "matches the payment evidence."
        )


    # NO_SMS is allowed.
    # Missing SMS is not automatically suspicious.


    # --------------------------------------------------
    # 7. FINAL DECISION
    # --------------------------------------------------

    if reject_reasons:

        return {
            "decision": "REJECTED",

            "reason": reject_reasons[0],

            "additional_reasons":
                reject_reasons[1:]
                + verification_reasons,

            "suspicious_indicators":
                suspicious_indicators,

            "confidence": "HIGH",

            "next_action": (
                "Review the listed issues and "
                "ask the customer to provide "
                "valid payment evidence for "
                "this order."
            )
        }


    if verification_reasons:

        return {
            "decision": "NEEDS VERIFICATION",

            "reason":
                verification_reasons[0],

            "additional_reasons":
                verification_reasons[1:],

            "suspicious_indicators":
                suspicious_indicators,

            "confidence": "LOW",

            "next_action": (
                "Review the evidence manually "
                "or request clearer supporting "
                "payment evidence."
            )
        }


    # --------------------------------------------------
    # 8. APPROVED
    # --------------------------------------------------

    confidence = "HIGH"

    if sms_status in {
        "NO_SMS",
        "INSUFFICIENT"
    }:
        confidence = "MEDIUM"


    return {
        "decision": "APPROVED",

        "reason": (
            "The available payment evidence "
            "matches the order and no strong "
            "fraud indicators were detected."
        ),

        "additional_reasons": [],

        "suspicious_indicators":
            suspicious_indicators,

        "confidence": confidence,

        "next_action": (
            "The payment can proceed to "
            "business processing."
        )
    }