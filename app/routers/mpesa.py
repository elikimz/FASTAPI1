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
@router.post("/callback")
async def mpesa_callback(request: Request, db: Session = Depends(get_db)):
    raw_data = await request.body()
    raw_text = raw_data.decode("utf-8").strip()

    # Log the raw request for debugging
    print(f"🔥 Raw Callback String: {raw_text}")

    # If the request body is empty, return an error response
    if not raw_text:
        logger.error("🚨 Received empty callback request!")
        return {"error": "Empty callback request"}

    try:
        data = await request.json()
        print(f"✅ Parsed JSON: {data}")  # Log parsed JSON data
    except Exception as e:
        logger.error(f"🚨 JSON Decode Error: {str(e)}")
        return {"error": "Invalid JSON format"}

    # Extract transaction ID from the callback
    callback = data.get("Body", {}).get("stkCallback", {})
    transaction_id = callback.get("CheckoutRequestID")

    if not transaction_id:
        logger.error("🚨 Callback missing transaction ID")
        return {"error": "Transaction ID not found in callback data"}

    # Find the transaction in the database
    transaction = db.query(MpesaTransaction).filter_by(transaction_id=transaction_id).first()
    if not transaction:
        logger.error(f"🚨 Transaction {transaction_id} not found in DB!")
        return {"error": "Transaction not found"}

    # Update the transaction status
    result_code = callback.get("ResultCode")
    if result_code == 0:
        transaction.status = "successful"
    else:
        transaction.status = "failed"
        error_message = callback.get("ResultDesc", "No description provided")
        logger.error(f"🚨 Transaction failed: {error_message}")

    db.commit()
    return {"message": "Callback received and processed"}