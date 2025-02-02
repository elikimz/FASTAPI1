import logging
from fastapi import APIRouter, HTTPException, Depends,Request ,Response 
from sqlalchemy.orm import Session
import xml
from ..database import get_db
from ..models import MpesaTransaction
from .mpesa_aouth import stk_push_request  # Correct import for stk_push_request
import json 
import xmltodict  # Add this at top of file

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



# Set up logging
@router.post("/callback")
async def mpesa_callback(request: Request, db: Session = Depends(get_db)):
    success_response = {"ResultCode": 0, "ResultDesc": "Success"}

    try:
        # Log raw body
        raw_body = await request.body()
        raw_text = raw_body.decode(errors="ignore").strip()
        logger.debug(f"📨 Raw Request Body: {raw_text}")

        if not raw_text:
            logger.warning("⚠️ Empty request received")
            return success_response  # Return success to avoid retries

        # Try parsing JSON
        try:
            json_body = await request.json()
            logger.debug(f"📜 Parsed JSON Data: {json.dumps(json_body, indent=2)}")
            return success_response  # Stop here for now to analyze logs
        except Exception:
            logger.debug("📌 Not JSON, attempting XML parsing...")

        # Try parsing XML
        try:
            data = xmltodict.parse(raw_text)
            logger.debug(f"📜 Parsed XML Data: {json.dumps(data, indent=2)}")
        except Exception as e:
            logger.error(f"🔥 XML Parsing Error: {str(e)}")
            return success_response  # Return success to prevent retry loops

    except Exception as e:
        logger.error(f"🔥 Critical Error: {str(e)}", exc_info=True)

    return success_response
