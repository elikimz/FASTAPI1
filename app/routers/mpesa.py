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

# Endpoint to handle M-Pesa callbacks
import json  # Make sure this is imported at the top
from fastapi import Request

from fastapi import Request

# Add these imports at the top
import json
import logging
from fastapi import Request

@router.post("/callback")
async def mpesa_callback(request: Request, db: Session = Depends(get_db)):
    # Log incoming request metadata
    client_ip = request.client.host if request.client else "unknown"
    logger.info(f"🌐 Callback received from IP: {client_ip}")
    
    try:
        # Get raw request body
        raw_body = await request.body()
        
        # Handle empty callback (common issue)
        if not raw_body:
            logger.error("💥 EMPTY CALLBACK BODY RECEIVED")
            return {"ResultCode": 1, "ResultDesc": "Empty callback"}
        
        # Decode and clean the data
        decoded_body = raw_body.decode('utf-8').strip()
        logger.info(f"📝 Raw Callback Content:\n{decoded_body}")
        
        # Clean non-printable characters
        cleaned_body = "".join(c for c in decoded_body if c.isprintable())
        
        # Parse JSON
        data = json.loads(cleaned_body)
        
        # Extract transaction ID from M-Pesa's structure
        callback = data.get("Body", {}).get("stkCallback", {})
        transaction_id = callback.get("CheckoutRequestID")
        
        # Fallback extraction if structure differs
        if not transaction_id:
            transaction_id = data.get("CheckoutRequestID")
        
        if not transaction_id:
            logger.error("🚨 Missing CheckoutRequestID in:\n%s", data)
            return {"ResultCode": 1, "ResultDesc": "Transaction ID missing"}
        
        # Update transaction status
        transaction = db.query(MpesaTransaction).filter_by(
            transaction_id=transaction_id
        ).first()
        
        if not transaction:
            logger.error(f"❌ Transaction {transaction_id} not found")
            return {"ResultCode": 1, "ResultDesc": "Transaction not found"}
        
        # Determine success/failure
        result_code = callback.get("ResultCode", 1)
        transaction.status = "completed" if result_code == 0 else "failed"
        db.commit()
        
        logger.info(f"✅ Updated transaction {transaction_id} to {transaction.status}")
        return {"ResultCode": 0, "ResultDesc": "Success"}
        
    except json.JSONDecodeError as e:
        logger.error(f"🚨 JSON Error: {str(e)}\nRaw Data:\n{decoded_body}")
        return {"ResultCode": 1, "ResultDesc": "Invalid JSON"}
    except Exception as e:
        logger.error(f"🔥 Unexpected error: {str(e)}")
        return {"ResultCode": 1, "ResultDesc": "Processing failed"}