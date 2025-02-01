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
@router.post("/callback")
async def mpesa_callback(request: Request, db: Session = Depends(get_db)):
    try:
        # Get raw request body
        raw_body = await request.body()
        data = json.loads(raw_body)
        
        logger.info(f"🔥 Raw Callback Data: {raw_body.decode()}")
        
        # Extract transaction ID from multiple possible locations
        transaction_id = (
            data.get("Body", {}).get("stkCallback", {}).get("CheckoutRequestID") or
            data.get("CheckoutRequestID")  # Sometimes at root
        )
        
        if not transaction_id:
            logger.error("🚨 Missing transaction ID in callback")
            return {"ResultCode": 1, "ResultDesc": "Missing transaction ID"}
            
        # Find transaction in database
        transaction = db.query(MpesaTransaction).filter_by(
            transaction_id=transaction_id
        ).first()
        
        if not transaction:
            logger.error(f"Transaction {transaction_id} not found")
            return {"ResultCode": 1, "ResultDesc": "Transaction not found"}
            
        # Update status based on result code
        result_code = data.get("Body", {}).get("stkCallback", {}).get("ResultCode", 1)
        
        if result_code == 0:
            transaction.status = "completed"
        else:
            transaction.status = "failed"
            logger.warning(f"Payment failed: {data.get('Body', {}).get('stkCallback', {}).get('ResultDesc')}")
        
        db.commit()
        logger.info(f"Updated transaction {transaction_id} to {transaction.status}")
        
        return {"ResultCode": 0, "ResultDesc": "Success"}
        
    except json.JSONDecodeError:
        logger.error("🚨 Invalid JSON in callback")
        return {"ResultCode": 1, "ResultDesc": "Invalid JSON format"}
    except Exception as e:
        logger.error(f"Callback processing failed: {str(e)}")
        return {"ResultCode": 1, "ResultDesc": "Server error"}