from datetime import datetime

from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    DateTime,
    Text,
    ForeignKey,
)

from sqlalchemy.orm import relationship

from database import Base


# --------------------------------------------------
# ORDER TABLE
# --------------------------------------------------

class Order(Base):
    __tablename__ = "orders"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    customer_name = Column(
        String(120),
        nullable=False
    )

    expected_amount = Column(
        Numeric(12, 2),
        nullable=False
    )

    expected_account = Column(
        String(32),
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=datetime.now,
        nullable=False
    )

    payments = relationship(
        "PaymentSubmission",
        back_populates="order"
    )


# --------------------------------------------------
# PAYMENT SUBMISSION TABLE
# --------------------------------------------------

class PaymentSubmission(Base):
    __tablename__ = "payment_submissions"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    order_id = Column(
        Integer,
        ForeignKey("orders.id"),
        nullable=False
    )

    receipt_reference = Column(
        String(100),
        nullable=True,
        index=True
    )

    extracted_amount = Column(
        Numeric(12, 2),
        nullable=True
    )

    extracted_account = Column(
        String(32),
        nullable=True
    )

    transaction_datetime = Column(
        DateTime,
        nullable=True
    )

    transaction_status = Column(
        String(50),
        nullable=True
    )

    sha256_hash = Column(
        String(64),
        nullable=True,
        index=True
    )

    perceptual_hash = Column(
        String(64),
        nullable=True
    )

    raw_ocr_text = Column(
        Text,
        nullable=True
    )

    final_decision = Column(
        String(30),
        nullable=True
    )

    decision_reason = Column(
        Text,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.now,
        nullable=False
    )

    order = relationship(
        "Order",
        back_populates="payments"
    )


# --------------------------------------------------
# BANK SMS TABLE
# --------------------------------------------------

class BankSMS(Base):
    __tablename__ = "bank_sms"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    message_text = Column(
        Text,
        nullable=False
    )

    amount = Column(
        Numeric(12, 2),
        nullable=True
    )

    account = Column(
        String(32),
        nullable=True
    )

    reference = Column(
        String(100),
        nullable=True,
        index=True
    )

    transaction_datetime = Column(
        DateTime,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.now,
        nullable=False
    )