import re
from datetime import datetime


# ==========================================================
# BANK IDENTIFICATION
# ==========================================================

BANK_ALIASES = {
    "Amana Bank": [
        "AMANA BANK",
    ],

    "Bank of Ceylon": [
        "BANK OF CEYLON",
        "BOC",
    ],

    "Bank of China": [
        "BANK OF CHINA",
    ],

    "Cargills Bank": [
        "CARGILLS BANK",
    ],

    "Citibank": [
        "CITIBANK",
        "CITI BANK",
    ],

    "Commercial Bank of Ceylon": [
        "COMMERCIAL BANK OF CEYLON",
        "COMMERCIAL BANK",
        "COMBANK",
    ],

    "Deutsche Bank": [
        "DEUTSCHE BANK",
    ],

    "DFCC Bank": [
        "DFCC BANK",
        "DFCC",
    ],

    "Habib Bank": [
        "HABIB BANK",
        "HBL",
    ],

    "Hatton National Bank": [
        "HATTON NATIONAL BANK",
        "HNB",
    ],

    "Indian Bank": [
        "INDIAN BANK",
    ],

    "Indian Overseas Bank": [
        "INDIAN OVERSEAS BANK",
        "IOB",
    ],

    "MCB Bank": [
        "MCB BANK",
    ],

    "NDB Bank": [
        "NATIONAL DEVELOPMENT BANK",
        "NDB BANK",
        "NDB",
    ],

    "Nations Trust Bank": [
        "NATIONS TRUST BANK",
        "NTB",
    ],

    "Pan Asia Bank": [
        "PAN ASIA BANK",
        "PAN ASIA BANKING",
        "PABC",
    ],

    "People's Bank": [
        "PEOPLE'S BANK",
        "PEOPLES BANK",
    ],

    "Public Bank": [
        "PUBLIC BANK BERHAD",
        "PUBLIC BANK",
    ],

    "Sampath Bank": [
        "SAMPATH BANK",
        "SAMPATH",
    ],

    "Seylan Bank": [
        "SEYLAN BANK",
        "SEYLAN",
    ],

    "Standard Chartered Bank": [
        "STANDARD CHARTERED BANK",
        "STANDARD CHARTERED",
    ],

    "State Bank of India": [
        "STATE BANK OF INDIA",
        "SBI",
    ],

    "HSBC": [
        "HONGKONG AND SHANGHAI BANKING CORPORATION",
        "HSBC",
    ],

    "Union Bank": [
        "UNION BANK OF COLOMBO",
        "UNION BANK",
    ],

    "HDFC Bank": [
        "HDFC BANK",
    ],

    "National Savings Bank": [
        "NATIONAL SAVINGS BANK",
        "NSB",
    ],

    "Regional Development Bank": [
        "REGIONAL DEVELOPMENT BANK",
        "RDB",
    ],

    "Sanasa Development Bank": [
        "SANASA DEVELOPMENT BANK",
        "SDB BANK",
    ],

    "Sri Lanka Savings Bank": [
        "SRI LANKA SAVINGS BANK",
        "SLSB",
    ],

    "State Mortgage & Investment Bank": [
        "STATE MORTGAGE",
        "SMIB",
    ],
}


# ==========================================================
# COMMON PATTERNS
# ==========================================================

CURRENCY_PATTERN = (
    r"(?:"
    r"LKR|SLR|RS\.?|"
    r"USD|EUR|GBP|AUD|JPY|SGD|CAD|CHF|INR|TZS"
    r")"
)


MONEY_PATTERN = (
    r"(?:"
    r"\d{1,3}(?:[,\s]\d{3})+"
    r"|"
    r"\d+"
    r")"
    r"(?:\.\d{1,2})?"
)


REFERENCE_LABELS = [
    "cyber receipt reference",

    "bank reference number",
    "bank reference no",
    "bank reference",

    "receipt reference number",
    "receipt reference",

    "transaction reference number",
    "transaction reference",
    "transaction ref",

    "reference number",
    "reference no",
    "ref no",

    "transaction id",
    "payment id",

    "trace number",
    "trace no",

    "depositor related reference",
    "ceft reference",
]


# ==========================================================
# BASIC HELPERS
# ==========================================================

def clean_text(text):
    """
    Light OCR cleanup while keeping line structure.
    """

    if not text:
        return ""

    text = text.replace(
        "\r",
        "\n"
    )

    text = (
        text
        .replace("–", "-")
        .replace("—", "-")
        .replace("’", "'")
        .replace("“", '"')
        .replace("”", '"')
    )

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    return text.strip()


def flatten_text(text):
    """
    Convert OCR line breaks into spaces.

    Useful when OCR splits:

    Bank Reference
    Number C500015026152
    """

    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


def unique(values):
    """
    Preserve order while removing duplicates.
    """

    result = []
    seen = set()

    for value in values:

        if (
            value
            and value not in seen
        ):
            seen.add(value)
            result.append(value)

    return result


# ==========================================================
# BANK
# ==========================================================

def detect_bank(text):

    upper_text = text.upper()

    matches = []

    for bank, aliases in BANK_ALIASES.items():

        for alias in aliases:

            pattern = (
                r"\b"
                + re.escape(alias)
                + r"\b"
            )

            if re.search(
                pattern,
                upper_text,
                re.IGNORECASE
            ):

                matches.append(
                    (
                        len(alias),
                        bank
                    )
                )

    if not matches:
        return None

    return max(matches)[1]


# ==========================================================
# MONEY
# ==========================================================

def normalize_money(value):

    if not value:
        return None

    value = re.sub(
        r"[,\s]",
        "",
        value
    )

    try:
        number = float(value)

    except ValueError:
        return None

    if "." in value:
        return f"{number:.2f}"

    if number.is_integer():
        return str(
            int(number)
        )

    return str(number)


def extract_amount_candidates(text):

    amounts = []

    flat_text = flatten_text(
        text
    )


    # ------------------------------------------------------
    # Labelled amounts
    # ------------------------------------------------------

    amount_labels = (
        r"(?:"
        r"transfer amount|"
        r"transaction amount|"
        r"payment amount|"
        r"paid amount|"
        r"deposit amount|"
        r"cash deposit amount|"
        r"total amount|"
        r"amount"
        r")"
    )


    labelled_pattern = (
        amount_labels
        + r"\s*[:#-]?\s*"
        + rf"(?:{CURRENCY_PATTERN}\s*)?"
        + rf"({MONEY_PATTERN})"
    )


    for match in re.finditer(
        labelled_pattern,
        flat_text,
        re.IGNORECASE
    ):

        amount = normalize_money(
            match.group(1)
        )

        if amount:
            amounts.append(amount)


    # ------------------------------------------------------
    # Currency followed by number
    # ------------------------------------------------------

    currency_amount_pattern = (
        rf"\b{CURRENCY_PATTERN}"
        rf"\s*[:#-]?\s*"
        rf"({MONEY_PATTERN})"
    )


    for match in re.finditer(
        currency_amount_pattern,
        flat_text,
        re.IGNORECASE
    ):

        amount = normalize_money(
            match.group(1)
        )

        if amount:
            amounts.append(amount)


    # ------------------------------------------------------
    # Generic decimal fallback
    # ------------------------------------------------------

    for match in re.finditer(
        r"\b("
        r"\d+(?:,\d{3})*"
        r"\.\d{2}"
        r")\b",
        text
    ):

        amount = normalize_money(
            match.group(1)
        )

        if amount:
            amounts.append(amount)


    return unique(amounts)


# ==========================================================
# CURRENCY
# ==========================================================

def extract_currency(text):

    upper_text = text.upper()

    flat_text = flatten_text(
        upper_text
    )


    # Explicit label first.
    label_match = re.search(
        r"(?:"
        r"transfer currency|"
        r"transaction currency|"
        r"currency"
        r")"
        r"\s*[:#-]?\s*"
        r"(LKR|SLR|USD|EUR|GBP|AUD|JPY|SGD|CAD|CHF|INR|TZS)",
        flat_text,
        re.IGNORECASE
    )


    if label_match:

        currency = (
            label_match
            .group(1)
            .upper()
        )

        if currency == "SLR":
            return "LKR"

        return currency


    currency_codes = [
        "LKR",
        "SLR",
        "USD",
        "EUR",
        "GBP",
        "AUD",
        "JPY",
        "SGD",
        "CAD",
        "CHF",
        "INR",
        "TZS",
    ]


    for currency in currency_codes:

        if re.search(
            rf"\b{currency}\b",
            upper_text
        ):

            if currency == "SLR":
                return "LKR"

            return currency


    # Sri Lankan receipts sometimes use Rs.
    if re.search(
        r"\bRS\.?\s*\d",
        upper_text
    ):
        return "LKR"


    return None


# ==========================================================
# REFERENCES
# ==========================================================

def extract_reference(text):

    flat_text = flatten_text(
        text
    )


    # Try longer, more specific labels first.
    labels = sorted(
        REFERENCE_LABELS,
        key=len,
        reverse=True
    )


    label_pattern = "|".join(
        re.escape(label)
        for label in labels
    )


    pattern = (
        rf"(?:{label_pattern})"
        r"\s*"
        r"(?:(?:no\.?|number)\s*)?"
        r"[:#-]?\s*"
        r"([A-Z0-9]"
        r"[A-Z0-9/_-]{3,80})"
    )


    invalid_values = {
        "NUMBER",
        "REFERENCE",
        "REF",
        "TRANSACTION",
        "PAYMENT",
        "NO",
    }


    for match in re.finditer(
        pattern,
        flat_text,
        re.IGNORECASE
    ):

        reference = (
            match.group(1)
            .strip()
        )


        if (
            reference.upper()
            not in invalid_values
        ):
            return reference


    return None


# ==========================================================
# ACCOUNTS
# ==========================================================

def normalize_account(value):

    if not value:
        return None

    value = value.strip()

    value = re.sub(
        r"[\s-]",
        "",
        value
    )

    value = value.replace(
        "•",
        "*"
    )

    return value


def looks_like_account(value):

    value = normalize_account(
        value
    )

    if not value:
        return False


    number_of_digits = sum(
        character.isdigit()
        for character in value
    )


    return (
        number_of_digits >= 4
        and len(value) >= 6
    )


def extract_accounts(text):

    beneficiary_account = None
    sender_account = None

    candidates = []


    # Account-like token:
    #
    # 276100180023877
    # 0872******9205
    # 4385 XXXX XXXX 1234

    account_token = (
        r"("
        r"[0-9Xx*•]"
        r"[0-9Xx*•\-\s]{4,24}"
        r"[0-9Xx*•]"
        r")"
    )


    # ------------------------------------------------------
    # BENEFICIARY ACCOUNT
    # ------------------------------------------------------

    beneficiary_labels = (
        r"(?:"
        r"beneficiary account number|"
        r"beneficiary account no|"
        r"beneficiary account|"
        r"beneficiary a/c|"
        r"recipient account|"
        r"payee account|"
        r"credit account|"
        r"credited to|"
        r"paid to|"
        r"to account|"
        r"to a/c"
        r")"
    )


    beneficiary_pattern = (
        beneficiary_labels
        + r"\s*"
        + r"(?:no\.?|number)?"
        + r"\s*[:#-]?\s*"
        + account_token
    )


    match = re.search(
        beneficiary_pattern,
        text,
        re.IGNORECASE
    )


    if match:

        possible_account = (
            match.group(1)
        )

        if looks_like_account(
            possible_account
        ):

            beneficiary_account = (
                normalize_account(
                    possible_account
                )
            )


    # ------------------------------------------------------
    # SENDER ACCOUNT
    # ------------------------------------------------------

    sender_labels = (
        r"(?:"
        r"sender account number|"
        r"sender account no|"
        r"sender account|"
        r"from account|"
        r"debit account|"
        r"debited from|"
        r"paid from|"
        r"from a/c"
        r")"
    )


    sender_pattern = (
        sender_labels
        + r"\s*"
        + r"(?:no\.?|number)?"
        + r"\s*[:#-]?\s*"
        + account_token
    )


    match = re.search(
        sender_pattern,
        text,
        re.IGNORECASE
    )


    if match:

        possible_account = (
            match.group(1)
        )

        if looks_like_account(
            possible_account
        ):

            sender_account = (
                normalize_account(
                    possible_account
                )
            )


    if beneficiary_account:
        candidates.append(
            beneficiary_account
        )


    if sender_account:
        candidates.append(
            sender_account
        )


    # ------------------------------------------------------
    # GENERIC ACCOUNT FALLBACK
    # ------------------------------------------------------

    skip_words = [
        "REFERENCE",
        "REF ",
        "DATE",
        "TIME",
        "AMOUNT",
        "SERVICE CHARGE",
        "COMMISSION",
        "PHONE",
        "MOBILE",
    ]


    for line in text.splitlines():

        upper_line = line.upper()


        if any(
            word in upper_line
            for word in skip_words
        ):
            continue


        # Avoid ATM date/time:
        #
        # 30 12 24 20 50

        if re.fullmatch(
            r"\s*"
            r"\d{2}\s+"
            r"\d{2}\s+"
            r"\d{2,4}\s+"
            r"\d{2}\s+"
            r"\d{2}"
            r"\s*",
            line
        ):
            continue


        for match in re.finditer(
            r"(?<!\w)"
            r"(?:\d|[Xx*•])"
            r"(?:[\dXx*• -]{6,22})"
            r"(?:\d|[Xx*•])"
            r"(?!\w)",
            line
        ):

            possible_account = (
                normalize_account(
                    match.group(0)
                )
            )


            if not looks_like_account(
                possible_account
            ):
                continue


            digits_only = re.sub(
                r"\D",
                "",
                possible_account
            )


            if (
                8
                <= len(digits_only)
                <= 18
            ):
                candidates.append(
                    possible_account
                )


    return (
        beneficiary_account,
        sender_account,
        unique(candidates)
    )


# ==========================================================
# DATE / TIME
# ==========================================================

def normalize_datetime(value):

    value = re.sub(
        r"\s+",
        " ",
        value.strip()
    )


    # OCR variants:
    #
    # A.M.
    # A M
    # P.M.

    value = re.sub(
        r"\bA\.?\s*M\.?\b",
        "AM",
        value,
        flags=re.IGNORECASE
    )

    value = re.sub(
        r"\bP\.?\s*M\.?\b",
        "PM",
        value,
        flags=re.IGNORECASE
    )

        # Some receipts combine 24-hour time
    # with AM/PM, for example:
    #
    # 16:07 PM
    #
    # Treat this as 16:07.

    value = re.sub(
        r"\b(1[3-9]|2[0-3]):(\d{2})"
        r"\s*(?:AM|PM)\b",
        r"\1:\2",
        value,
        flags=re.IGNORECASE
    )


    # OCR sometimes reads:
    #
    # 08.08
    #
    # instead of:
    #
    # 08:08

    value = re.sub(
        r"(?<=\d)\.(?=\d{2}(?:\s*(?:AM|PM))?$)",
        ":",
        value,
        flags=re.IGNORECASE
    )


    formats = [
        "%d/%m/%Y %I:%M %p",
        "%d/%m/%Y %H:%M",

        "%d-%m-%Y %I:%M %p",
        "%d-%m-%Y %H:%M",

        "%d/%m/%y %I:%M %p",
        "%d/%m/%y %H:%M",

        "%d-%m-%y %I:%M %p",
        "%d-%m-%y %H:%M",

        "%d %m %Y %H %M",
        "%d %m %y %H %M",

        "%d-%b-%Y %I:%M %p",
        "%d %b %Y %I:%M %p",

        "%d-%b-%Y %H:%M",
        "%d %b %Y %H:%M",

        "%Y-%m-%d %H:%M",
    ]


    for date_format in formats:

        try:

            result = datetime.strptime(
                value,
                date_format
            )


            return result.strftime(
                "%d/%m/%Y %I:%M %p"
            )


        except ValueError:
            continue


    return None


def extract_datetime(text):

    flat_text = flatten_text(
        text
    )


    patterns = [

        # 24/03/2025 08:08 PM
        # 24/03/2025 08.08 P.M.
        (
            r"\b"
            r"\d{1,2}/\d{1,2}/\d{4}"
            r"\s+"
            r"\d{1,2}[:.]\d{2}"
            r"\s*"
            r"(?:A\.?\s*M\.?|P\.?\s*M\.?)?"
        ),

        # 24-03-2025 20:08
        (
            r"\b"
            r"\d{1,2}-\d{1,2}-\d{4}"
            r"\s+"
            r"\d{1,2}[:.]\d{2}"
            r"\s*"
            r"(?:A\.?\s*M\.?|P\.?\s*M\.?)?"
        ),

        # 24/03/25 08:08 PM
        (
            r"\b"
            r"\d{1,2}/\d{1,2}/\d{2}"
            r"\s+"
            r"\d{1,2}[:.]\d{2}"
            r"\s*"
            r"(?:A\.?\s*M\.?|P\.?\s*M\.?)?"
        ),

        # 24-03-25 20:08
        (
            r"\b"
            r"\d{1,2}-\d{1,2}-\d{2}"
            r"\s+"
            r"\d{1,2}[:.]\d{2}"
            r"\s*"
            r"(?:A\.?\s*M\.?|P\.?\s*M\.?)?"
        ),

        # ATM:
        # 30 12 24 20 50
        (
            r"\b"
            r"\d{2}\s+"
            r"\d{2}\s+"
            r"\d{2,4}\s+"
            r"\d{2}\s+"
            r"\d{2}"
            r"\b"
        ),

        # 06-Apr-2020 03:34 PM
        (
            r"\b"
            r"\d{1,2}[- ]"
            r"(?:"
            r"Jan|Feb|Mar|Apr|May|Jun|"
            r"Jul|Aug|Sep|Oct|Nov|Dec"
            r")"
            r"[- ]\d{4}"
            r"\s+"
            r"\d{1,2}[:.]\d{2}"
            r"\s*"
            r"(?:A\.?\s*M\.?|P\.?\s*M\.?)?"
        ),

        # ISO style
        (
            r"\b"
            r"\d{4}-\d{2}-\d{2}"
            r"\s+"
            r"\d{1,2}:\d{2}"
            r"\b"
        ),
    ]


    for pattern in patterns:

        for match in re.finditer(
            pattern,
            flat_text,
            re.IGNORECASE
        ):

            result = normalize_datetime(
                match.group(0)
            )

            if result:
                return result


    return None


# ==========================================================
# STATUS
# ==========================================================

def extract_status(text):

    upper_text = text.upper()


    # Convert punctuation / OCR separators
    # into spaces.

    normalized = re.sub(
        r"[^A-Z0-9]+",
        " ",
        upper_text
    )


    # ------------------------------------------------------
    # FAILED
    # ------------------------------------------------------

    failed_patterns = [
        r"\bUNSUCCESSFUL\b",
        r"\bFAILED\b",
        r"\bDECLINED\b",
        r"\bREJECTED\b",
        r"\bCANCELLED\b",
        r"\bCANCELED\b",
    ]


    for pattern in failed_patterns:

        if re.search(
            pattern,
            normalized
        ):
            return "FAILED"


    # ------------------------------------------------------
    # PENDING
    # ------------------------------------------------------

    pending_patterns = [
        r"\bPENDING\b",
        r"\bPROCESSING\b",
        r"\bSCHEDULED\b",
    ]


    for pattern in pending_patterns:

        if re.search(
            pattern,
            normalized
        ):
            return "PENDING"


    # ------------------------------------------------------
    # SUCCESS
    # ------------------------------------------------------

    success_patterns = [
        r"\bCOMPLETED\b",

        # Small OCR mistakes:
        # COMPIETED
        # COMP1ETED
        r"\bCOMP[LI1]ETED\b",

        r"\bSUCCESSFUL\b",
        r"\bSUCCESS\b",
        r"\bAPPROVED\b",
        r"\bPROCESSED\b",
    ]


    for pattern in success_patterns:

        if re.search(
            pattern,
            normalized
        ):
            return "SUCCESS"


    # IMPORTANT:
    #
    # A receipt without a printed status
    # is NOT considered failed.

    return "NOT_STATED"


# ==========================================================
# MAIN PARSER
# ==========================================================

def extract_receipt_fields(text):

    text = clean_text(
        text
    )


    bank = detect_bank(
        text
    )


    receipt_reference = (
        extract_reference(
            text
        )
    )


    amount_candidates = (
        extract_amount_candidates(
            text
        )
    )


    (
        beneficiary_account,
        sender_account,
        account_candidates

    ) = extract_accounts(
        text
    )


    transaction_datetime = (
        extract_datetime(
            text
        )
    )


    currency = extract_currency(
        text
    )


    status = extract_status(
        text
    )


    return {
        "bank":
            bank,

        "receipt_reference":
            receipt_reference,

        "amount_candidates":
            amount_candidates,

        "account_candidates":
            account_candidates,

        "transaction_datetime":
            transaction_datetime,

        "currency":
            currency,

        "status":
            status,

        "beneficiary_account":
            beneficiary_account,

        "sender_account":
            sender_account,
    }