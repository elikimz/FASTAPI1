import logging
from fastapi import APIRouter, HTTPException, Depends,Request 
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import MpesaTransaction
from .mpesa_aouth import stk_push_request  # Correct import for stk_push_request
import json 

router = APIRouter(prefix="/mpesa", tags=["M-Pesa"])

# Set up logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Helper function to normalize phone number
def normalize_phone_number(phone_number: str):
    # Remove all non-digit characters (e.g., +, spaces)
    digits = "".join(filter(str.isdigit, phone_number))
    
    if digits.startswith("0") and len(digits) == 9:  # Handle 07XXXXXXXX
        return "254" + digits[1:]
    elif digits.startswith("254") and len(digits) == 12:  # Already valid
        return digits
    else:
        raise ValueError("Invalid phone number. Use 07XXXXXXXX or 2547XXXXXXXX.")
    
# Endpoint to initiate payment
@router.post("/pay")
def initiate_payment(phone_number: str, amount: float, db: Session = Depends(get_db)):
    try:
        phone_number = normalize_phone_number(phone_number)  # Normalize the phone number
        response = stk_push_request(phone_number, amount)
        logger.info(f"M-Pesa Response: {response}")  # Log the full response

        response_code = response.get("ResponseCode", "unknown")
        if response_code == "0":
            transaction = MpesaTransaction(
                phone_number=phone_number,
                amount=amount,
                transaction_id=response["CheckoutRequestID"],
                status="pending"
            )
            db.add(transaction)
            db.commit()
            return {"message": "Payment request sent", "transaction_id": response["CheckoutRequestID"]}
        else:
            error_message = response.get('errorMessage', 'Unknown error')
            raise HTTPException(status_code=400, detail=f"Payment request failed: {error_message}")
    except Exception as e:
        logger.error(f"Error initiating payment: {str(e)}")  # Log the exception
        raise HTTPException(status_code=500, detail="Internal server error while initiating payment")



@router.post("/callback")
def mpesa_callback(data: dict = None, db: Session = Depends(get_db)):
    if not data:  # Handle empty request
        logger.error("🚨 Received empty callback request!")
        return {"error": "Empty request received"}
    
    logger.info(f"🔥 Raw Callback Data: {data}")  # Log callback data

    callback = data.get("Body", {}).get("stkCallback", {})
    if not callback:
        logger.error(f"🚨 Missing 'stkCallback' in: {data}")
        return {"error": "Invalid callback format"}

    transaction_id = callback.get("CheckoutRequestID")
    if not transaction_id:
        logger.error("🚨 Callback missing transaction ID")
        return {"error": "Transaction ID not found in callback data"}

    transaction = db.query(MpesaTransaction).filter_by(transaction_id=transaction_id).first()
    if not transaction:
        return {"error": "Transaction not found"}

    result_code = callback.get("ResultCode")
    if result_code == 0:
        transaction.status = "successful"
    else:
        error_message = callback.get("ResultDesc", "No description provided")
        logger.error(f"Transaction failed: {error_message}")
        transaction.status = "failed"

    db.commit()
    return {"message": "Callback received"}