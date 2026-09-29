from pathlib import Path
import shutil
import tempfile

from pydantic import BaseModel, Field

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Form,
    HTTPException,
)

from fastapi.middleware.cors import CORSMiddleware

from database import SessionLocal
from models import Order
from payment_service import process_payment


# --------------------------------------------------
# FASTAPI APP
# --------------------------------------------------

app = FastAPI(
    title="BuildStart Payment Verification API",
    version="1.0.0"
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --------------------------------------------------
# REQUEST MODELS
# --------------------------------------------------

class OrderCreate(BaseModel):

    customer_name: str = Field(
        min_length=1,
        max_length=120
    )

    expected_amount: float = Field(
        gt=0
    )

    expected_account: str = Field(
        min_length=4,
        max_length=32
    )


# --------------------------------------------------
# ROOT
# --------------------------------------------------

@app.get("/")
def root():

    return {
        "message":
            "BuildStart Payment Verification API"
    }


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.get("/health")
def health_check():

    return {
        "status": "ok"
    }


# --------------------------------------------------
# GET ALL ORDERS
# --------------------------------------------------

@app.get("/orders")
def get_orders():

    db = SessionLocal()

    try:

        orders = (
            db.query(Order)
            .order_by(Order.id.desc())
            .all()
        )

        return [
            {
                "id": order.id,

                "customer_name":
                    order.customer_name,

                "expected_amount":
                    float(
                        order.expected_amount
                    ),

                "expected_account":
                    order.expected_account,

                "created_at":
                    order.created_at,
            }

            for order in orders
        ]

    finally:

        db.close()


# --------------------------------------------------
# CREATE NEW ORDER
# --------------------------------------------------

@app.post(
    "/orders",
    status_code=201
)
def create_order(
    order_data: OrderCreate
):

    db = SessionLocal()

    try:

        customer_name = (
            order_data.customer_name
            .strip()
        )

        expected_account = (
            order_data.expected_account
            .strip()
        )


        # Extra safety after stripping spaces.
        if not customer_name:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Customer name cannot "
                    "be empty."
                )
            )


        if not expected_account:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Expected account cannot "
                    "be empty."
                )
            )


        new_order = Order(
            customer_name=customer_name,
            expected_amount=(
                order_data.expected_amount
            ),
            expected_account=expected_account,
        )


        db.add(
            new_order
        )

        db.commit()

        db.refresh(
            new_order
        )


        return {
            "id": new_order.id,

            "customer_name":
                new_order.customer_name,

            "expected_amount":
                float(
                    new_order.expected_amount
                ),

            "expected_account":
                new_order.expected_account,

            "created_at":
                new_order.created_at,
        }


    except HTTPException:

        db.rollback()

        raise


    except Exception as error:

        db.rollback()

        print(
            "Create order error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Could not create order."
            )
        )


    finally:

        db.close()


# --------------------------------------------------
# PAYMENT VERIFICATION
# --------------------------------------------------

@app.post("/payments/verify")
async def verify_payment(
    order_id: int = Form(...),
    receipt: UploadFile = File(...),
    sms_text: str | None = Form(None)
):
    """
    Verify a submitted bank payment receipt
    against an existing order.
    """

    # ---------------------------------
    # 1. BASIC FILE CHECK
    # ---------------------------------

    if not receipt.content_type:

        raise HTTPException(
            status_code=400,
            detail="Missing file type."
        )


    if not receipt.content_type.startswith(
        "image/"
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Uploaded file must be "
                "an image."
            )
        )


    # ---------------------------------
    # 2. CREATE TEMPORARY IMAGE FILE
    # ---------------------------------

    suffix = Path(
        receipt.filename or "receipt.jpg"
    ).suffix


    if not suffix:

        suffix = ".jpg"


    with tempfile.NamedTemporaryFile(
        delete=False,
        suffix=suffix
    ) as temp_file:

        shutil.copyfileobj(
            receipt.file,
            temp_file
        )

        temp_path = Path(
            temp_file.name
        )


    # ---------------------------------
    # 3. RUN VERIFICATION PIPELINE
    # ---------------------------------

    try:

        result = process_payment(
            temp_path,
            order_id,
            sms_text
        )

        return result


    except ValueError as error:

        raise HTTPException(
            status_code=404,
            detail=str(error)
        )


    except Exception as error:

        print(
            "Payment verification error:",
            error
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "Payment verification failed."
            )
        )


    # ---------------------------------
    # 4. CLEAN TEMPORARY FILE
    # ---------------------------------

    finally:

        temp_path.unlink(
            missing_ok=True
        )

        await receipt.close()