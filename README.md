# Automated Bank Payment Verification System

A prototype payment-verification system built for the **BuildStart Software Engineering Intern — 2-Day Engineering Challenge**.

The system determines whether a customer's bank-transfer payment can be safely accepted using the evidence available to the business, without requiring direct access to a bank API.

---

## Problem

In a typical WhatsApp-based ordering flow:

1. A customer places an order.
2. The business provides its bank account details.
3. The customer makes a bank transfer.
4. The customer sends a screenshot or photograph of the payment receipt.
5. The business must decide whether the payment is genuine and belongs to the correct order.

Because no direct bank API is available, the system must make a decision using evidence such as:

- payment receipt images
- OCR-extracted receipt information
- order information
- bank SMS notifications
- previous payment submissions
- duplicate and fraud indicators

The system produces one of three outcomes:

- `APPROVED`
- `REJECTED`
- `NEEDS VERIFICATION`

---

# Features

## Order Management

The business dashboard allows the user to:

- create a new order
- view recorded orders
- select an order for verification

Each order stores:

- customer name
- expected payment amount
- expected receiving bank account
- order creation time

Expected order information is stored **before the receipt is submitted**.

This prevents the system from simply trusting values extracted from the customer's receipt.

---

## Receipt OCR

Payment receipts are processed using:

- Tesseract OCR
- `pytesseract`
- OpenCV
- Pillow

The system attempts to extract:

- amount
- beneficiary account
- transaction reference
- transaction date and time
- currency
- payment status
- bank information

Receipt formats vary between banks, so the parser uses multiple patterns rather than depending on one fixed receipt layout.

---

## Payment Verification

Extracted receipt information is compared with the selected order.

Important checks include:

- expected amount vs submitted amount
- expected beneficiary account vs detected account
- transaction date
- transaction status
- receipt reference availability

The system does not approve a payment based only on the amount.

Multiple pieces of evidence are considered together.

---

## Receipt Status Handling

Some physical bank receipts do not explicitly print words such as:

- `Successful`
- `Completed`
- `Approved`

The system therefore distinguishes between:

- `SUCCESS`
- `FAILED`
- `PENDING`
- `NOT_STATED`

`NOT_STATED` does **not** automatically mean the payment failed.

Instead, the system continues evaluating the remaining evidence.

---

## Fraud and Duplicate Detection

The system stores previous submissions and performs several checks.

### Exact duplicate detection

A SHA-256 hash is generated for each uploaded receipt.

If the exact same image is submitted again, the system can detect it.

### Receipt reference reuse

Previously used transaction references are compared with new submissions.

Reusing the same transaction reference can result in rejection.

### Similar image detection

A perceptual image hash is also calculated.

This can help identify images that may have been:

- resized
- recompressed
- screenshotted
- slightly modified

A similar image alone is treated as suspicious evidence rather than absolute proof of fraud.

---

## Image Quality Analysis

Uploaded receipt images are checked for:

- resolution
- blur
- brightness
- contrast
- editing-related metadata

Low-quality evidence may result in:

`NEEDS VERIFICATION`

rather than unsafe automatic approval.

---

## Bank SMS Evidence

Bank SMS notifications can optionally be submitted as additional evidence.

The system can compare SMS information such as:

- amount
- account
- reference
- transaction time

SMS is supporting evidence.

A missing SMS does **not** automatically reject a payment because:

- SMS notifications may be delayed
- SMS notifications may not always arrive
- formatting differs between banks

The system also avoids treating the SMS amount alone as proof that the payment belongs to the order.

---

# Decision Logic

The system uses deterministic rules instead of relying on a black-box AI model for every payment.

## APPROVED

A payment can be approved when important evidence matches and no strong fraud indicators are found.

Example:

```text
Amount              MATCH
Account             MATCH
Date                VALID
Reference           PRESENT
Status              SUCCESS / NOT_STATED
Exact duplicate     NEW
Reference reuse     NEW