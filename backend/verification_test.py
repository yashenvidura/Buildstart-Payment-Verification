from datetime import datetime, timedelta
def normalize_amount(amount_text):
    if amount_text is None:
        return None

    try:
        cleaned = amount_text.replace(",", "")
        return float(cleaned)
    except ValueError:
        return None


def verify_basic_evidence(fields, expected_amount, expected_account,order_created_at):
    results = {}

    # -------------------------
    # AMOUNT CHECK
    # -------------------------

    amount_candidates = fields.get("amount_candidates", [])

    normalized_amounts = []

    for amount in amount_candidates:
        normalized = normalize_amount(amount)

        if normalized is not None:
            normalized_amounts.append(normalized)

    results["extracted_amounts"] = normalized_amounts

    if not normalized_amounts:
        results["amount_check"] = "MISSING"

    elif expected_amount in normalized_amounts:
        results["amount_check"] = "MATCH"

    else:
        results["amount_check"] = "MISMATCH"


    # -------------------------
    # ACCOUNT CHECK
    # -------------------------

    account_candidates = fields.get("account_candidates", [])

    results["account_candidates"] = account_candidates

    if not account_candidates:
        results["account_check"] = "MISSING"

    elif expected_account in account_candidates:
        results["account_check"] = "MATCH"

    else:
        results["account_check"] = "MISMATCH"


    # -------------------------
    # STATUS CHECK
    # -------------------------

    status = fields.get("status")

    if status is None:
        results["status_check"] = "MISSING"

    elif status == "SUCCESS":
        results["status_check"] = "SUCCESS"

    elif status == "FAILED":
        results["status_check"] = "FAILED"

    elif status == "PENDING":
        results["status_check"] = "PENDING"

    elif status == "NOT_STATED":
        results["status_check"] = "NOT_STATED"

    else:
        results["status_check"] = "UNKNOWN"

    


    # -------------------------
    # REFERENCE / DATE
    # -------------------------

    results["reference_check"] = (
        "PRESENT"
        if fields.get("receipt_reference")
        else "MISSING"
    )

    results["date_check"] = check_transaction_date(
    fields.get("transaction_datetime"),
    order_created_at
    )
    
   

    return results

def check_transaction_date(
    transaction_datetime,
    order_created_at,
    max_payment_days=7
):
    """
    Check whether the payment date is reasonable for the order.
    """

    if transaction_datetime is None:
        return "MISSING"

    try:
        payment_time = datetime.strptime(
            transaction_datetime,
            "%d/%m/%Y %I:%M %p"
        )

    except ValueError:
        return "INVALID"

    # Payment occurred before the order existed
    if payment_time < order_created_at:
        return "OLD"

    # Payment occurred too long after the order was created
    latest_allowed_time = order_created_at + timedelta(
        days=max_payment_days
    )

    if payment_time > latest_allowed_time:
        return "OUTSIDE_WINDOW"

    return "VALID"