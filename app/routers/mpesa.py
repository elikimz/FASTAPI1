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

@router.post("/callback")
async def mpesa_callback(request: Request, db: Session = Depends(get_db)):
    try:
        # Get raw callback data and decode
        raw_body = await request.body()
        raw_json = raw_body.decode('utf-8')  # Convert bytes to string
        
        # Log raw data for debugging
        logger.info(f"🔥 Raw Callback String: {raw_json}")
        print(f"🔥 Raw Callback String: {raw_json}")

        # Clean non-printable characters (common in M-Pesa callbacks)
        cleaned_json = ''.join(c for c in raw_json if c.isprintable())
        
        # Parse JSON manually
        data = json.loads(cleaned_json)
        
        # Extract transaction ID - M-Pesa's actual structure
        callback = data.get("Body", {}).get("stkCallback", {})
        transaction_id = callback.get("CheckoutRequestID")

        # Alternative extraction if above fails
        if not transaction_id:
            transaction_id = data.get("CheckoutRequestID")

        if not transaction_id:
            logger.error("🚨 Missing transaction ID in:\n%s", data)
            return {"ResultCode": 1, "ResultDesc": "Missing transaction ID"}

        # Rest of your logic to update database...

    except json.JSONDecodeError as e:
        logger.error(f"🚨 JSON Decode Error: {str(e)}\nRaw Data: {raw_json}")
        return {"ResultCode": 1, "ResultDesc": "Invalid JSON format"}
    except Exception as e:
        logger.error(f"Callback failed: {str(e)}")
        return {"ResultCode": 1, "ResultDesc": "Server error"}