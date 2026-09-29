from datetime import datetime


def parse_sms_datetime(value):
    if not value:
        return None

    formats = [
        "%d/%m/%Y %I:%M %p",
        "%d/%m/%Y %H:%M",
    ]

    for date_format in formats:
        try:
            return datetime.strptime(
                value,
                date_format
            )
        except ValueError:
            continue

    return None


def match_sms_evidence(
    sms_fields,
    receipt_fields,
    expected_amount,
    expected_account
):
    """
    Compare parsed bank SMS evidence with
    the receipt and order information.
    """

    checks = {}

    # ---------------------------------
    # AMOUNT
    # ---------------------------------

    sms_amount = sms_fields.get("amount")

    if sms_amount is None:
        checks["amount"] = "MISSING"

    elif float(sms_amount) == float(expected_amount):
        checks["amount"] = "MATCH"

    else:
        checks["amount"] = "MISMATCH"


    # ---------------------------------
    # ACCOUNT
    # ---------------------------------

    sms_account = sms_fields.get("account")

    if not sms_account:
        checks["account"] = "MISSING"

    else:
        sms_account = str(sms_account)
        expected_account = str(expected_account)

        if (
            expected_account == sms_account
            or expected_account.endswith(sms_account)
        ):
            checks["account"] = "MATCH"

        else:
            checks["account"] = "MISMATCH"


    # ---------------------------------
    # REFERENCE
    # ---------------------------------

    sms_reference = sms_fields.get("reference")

    receipt_reference = receipt_fields.get(
        "receipt_reference"
    )

    if not sms_reference or not receipt_reference:
        checks["reference"] = "MISSING"

    elif (
        sms_reference.upper()
        == receipt_reference.upper()
    ):
        checks["reference"] = "MATCH"

    else:
        # Different banks may use different
        # reference identifiers, so we don't
        # immediately treat this as fraud.
        checks["reference"] = "DIFFERENT"


    # ---------------------------------
    # TIME
    # ---------------------------------

    sms_time = parse_sms_datetime(
        sms_fields.get("transaction_datetime")
    )

    receipt_time = parse_sms_datetime(
        receipt_fields.get(
            "transaction_datetime"
        )
    )

    if sms_time is None or receipt_time is None:
        checks["time"] = "MISSING"

    else:
        difference = abs(
            (
                sms_time - receipt_time
            ).total_seconds()
        )

        # Within 30 minutes
        if difference <= 1800:
            checks["time"] = "MATCH"

        else:
            checks["time"] = "DIFFERENT"


    # ---------------------------------
    # OVERALL SMS RESULT
    # ---------------------------------

    strong_matches = sum(
        value == "MATCH"
        for value in checks.values()
    )

    strong_mismatches = sum(
        value == "MISMATCH"
        for value in checks.values()
    )

    if strong_mismatches > 0:
        status = "CONFLICT"

    elif strong_matches >= 2:
        status = "MATCH"

    elif strong_matches == 1:
        status = "PARTIAL"

    else:
        status = "INSUFFICIENT"


    return {
        "status": status,
        "checks": checks
    }