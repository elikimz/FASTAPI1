import logging
from fastapi import APIRouter, HTTPException, Depends,Request ,Response 
from sqlalchemy.orm import Session
import xml
from ..database import get_db
from ..models import MpesaTransaction
from .mpesa_aouth import stk_push_request  # import for stk_push_request
import json 
import xmltodict  
router = APIRouter(prefix="/mpesa",
                    tags=["M-Pesa"])

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
                checkout_request_id=response["CheckoutRequestID"],  # Correct field
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
async def mpesa_callback(request: Request, db: Session = Depends(get_db)):
    try:
        raw_body = await request.body()
        if not raw_body:
            logging.error("Callback body is empty")
            return {"ResultCode": 1, "ResultDesc": "Empty request"}

        content_type = request.headers.get("Content-Type", "")

        if "application/json" in content_type:
            callback_data = json.loads(raw_body.decode())
        elif "application/xml" in content_type:
            try:
                callback_data = xmltodict.parse(raw_body)
            except Exception as e:
                logging.error(f"Failed to parse XML: {e}")
                return {"ResultCode": 1, "ResultDesc": "Invalid XML"}
        else:
            logging.error(f"Unsupported Content-Type: {content_type}")
            return {"ResultCode": 1, "ResultDesc": "Unsupported Content-Type"}

        logging.info(f"Received M-Pesa Callback: {callback_data}")

        return {"ResultCode": 0, "ResultDesc": "Success"}
    
    except Exception as e:
        logging.error(f"Error processing callback: {str(e)}")
        return {"ResultCode": 1, "ResultDesc": "Error processing callback"}
