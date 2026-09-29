import re


def extract_sms_fields(message):
    """
    Extract useful payment evidence from a bank SMS.

    SMS formats vary between banks, so missing fields
    are allowed.
    """

    fields = {}


    # --------------------------------------------------
    # AMOUNT
    # --------------------------------------------------

    amount_match = re.search(
        r"(?:LKR|Rs\.?|Rs)\s*"
        r"(\d+(?:,\d{3})*(?:\.\d{2})?)",
        message,
        re.IGNORECASE
    )

    if amount_match:
        amount_text = amount_match.group(1)

        fields["amount"] = float(
            amount_text.replace(",", "")
        )
    else:
        fields["amount"] = None


    # --------------------------------------------------
    # REFERENCE
    # --------------------------------------------------

    reference_match = re.search(
        r"(?:Ref|Reference)"
        r"[\s:#-]*"
        r"([A-Z0-9-]+)",
        message,
        re.IGNORECASE
    )

    fields["reference"] = (
        reference_match.group(1)
        if reference_match
        else None
    )


    # --------------------------------------------------
    # DATE + TIME
    # --------------------------------------------------

    datetime_match = re.search(
        r"\b\d{2}/\d{2}/\d{4}"
        r"\s+"
        r"\d{1,2}:\d{2}"
        r"\s*(?:AM|PM)?\b",
        message,
        re.IGNORECASE
    )

    fields["transaction_datetime"] = (
        datetime_match.group(0)
        if datetime_match
        else None
    )


    # --------------------------------------------------
    # ACCOUNT / ACCOUNT ENDING
    # --------------------------------------------------

    account_match = re.search(
        r"(?:A/C|Account|Acct)"
        r"[\s:*#-]*"
        r"(?:X+|\*+)?"
        r"(\d{4,16})",
        message,
        re.IGNORECASE
    )

    fields["account"] = (
        account_match.group(1)
        if account_match
        else None
    )


    return fields