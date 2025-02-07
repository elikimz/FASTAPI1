from pydantic import BaseModel 
import logging
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import MpesaTransaction
from .mpesa_aouth import stk_push_request

router = APIRouter(prefix="/mpesa", tags=["M-Pesa"])
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class PaymentRequest(BaseModel):
    phone_number: str
    amount: float

def normalize_phone_number(phone_number: str) -> str:
    """Normalize Kenyan phone numbers to 2547XXXXXXXX format."""
    digits = "".join(filter(str.isdigit, str(phone_number)))
    
    if len(digits) == 9 and digits.startswith("7"):
        return f"254{digits}"
    elif len(digits) == 10 and digits.startswith("0"):
        return f"254{digits[1:]}"
    elif len(digits) == 12 and digits.startswith("254"):
        return digits
    raise ValueError("Invalid phone number format. Use 07XXXXXXXX or 2547XXXXXXXX")

@router.post("/pay")
async def initiate_payment(
    request: PaymentRequest, 
    db: Session = Depends(get_db)
):
    """Process payment requests with M-Pesa STK Push."""
    try:
        phone_number = normalize_phone_number(request.phone_number)
        amount = request.amount

        logger.info(f"Initiating payment for {phone_number}, Amount: {amount}")

        stk_response = stk_push_request(phone_number, amount)

        if stk_response.get("ResponseCode") != "0":
            raise HTTPException(status_code=400, detail=stk_response.get("errorMessage", "Payment failed"))

        transaction = MpesaTransaction(
            phone_number=phone_number,
            amount=amount,
            checkout_request_id=stk_response["CheckoutRequestID"],
            status="pending"
        )
        db.add(transaction)
        db.commit()

        return {"message": "Payment initiated", "checkout_id": stk_response["CheckoutRequestID"]}

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
