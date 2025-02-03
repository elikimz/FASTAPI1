import logging
from fastapi import APIRouter, HTTPException, Depends,Request ,Response 
from sqlalchemy.orm import Session
import xml
from ..database import get_db
from ..models import MpesaTransaction
from .mpesa_aouth import stk_push_request  # import for stk_push_request
import json 
import xmltodict  
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
# Callback endpoint to receive M-Pesa response
@router.post("/mpesa/callback")
async def mpesa_callback(request: Request):
    # Log raw body
    raw_body = await request.body()
    raw_text = raw_body.decode(errors="ignore").strip()
    logger.debug(f"Raw Callback Body: {raw_text}")
    
    # Try parsing as JSON
    try:
        json_body = await request.json()
        logger.debug(f"Parsed JSON Callback: {json_body}")
    except Exception as e:
        logger.warning(f"Error parsing JSON: {str(e)}")
    
    # Try parsing as XML if JSON parsing fails
    if not json_body:
        try:
            xml_body = await request.body()
            logger.debug(f"Parsed XML Callback: {xml_body}")
            # You can further process XML if necessary
        except Exception as e:
            logger.warning(f"Error parsing XML: {str(e)}")
    
    return {"ResultCode": 0, "ResultDesc": "Success"}
