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
@router.post("/callback")
async def mpesa_callback(request: Request, db: Session = Depends(get_db)):
    success_response = {"ResultCode": 0, "ResultDesc": "Success"}

    try:
        raw_body = await request.body()
        raw_text = raw_body.decode(errors="ignore").strip()
        logger.debug(f"📨 Raw Callback Body: {raw_text}")

        if not raw_text:
            logger.warning("⚠️ Empty request received from M-Pesa")
            return success_response

        # Try parsing JSON first
        try:
            json_body = await request.json()
            logger.debug(f"📜 Parsed JSON Data: {json.dumps(json_body, indent=2)}")

            result_code = json_body.get("Body", {}).get("stkCallback", {}).get("ResultCode")
            checkout_request_id = json_body.get("Body", {}).get("stkCallback", {}).get("CheckoutRequestID")

            if result_code == 0:
                # Extract transaction details
                callback_metadata = json_body["Body"]["stkCallback"]["CallbackMetadata"]["Item"]
                mpesa_receipt_number = None
                phone_number = None

                for item in callback_metadata:
                    if item["Name"] == "MpesaReceiptNumber":
                        mpesa_receipt_number = item["Value"]
                    if item["Name"] == "PhoneNumber":
                        phone_number = str(item["Value"])

                if not mpesa_receipt_number:
                    logger.error("❌ MpesaReceiptNumber not found in callback")
                    return success_response

                # Find the transaction using CheckoutRequestID
                transaction = db.query(MpesaTransaction).filter_by(transaction_id=checkout_request_id).first()

                if transaction:
                    transaction.mpesa_code = mpesa_receipt_number
                    transaction.status = "Success"
                    db.commit()
                    logger.info(f"✅ Transaction {checkout_request_id} updated with M-Pesa code {mpesa_receipt_number}")

            else:
                # Failed Transaction
                transaction = db.query(MpesaTransaction).filter_by(transaction_id=checkout_request_id).first()
                if transaction:
                    transaction.status = "Failed"
                    db.commit()
                    logger.warning(f"⚠️ Transaction {checkout_request_id} marked as Failed")

        except Exception as e:
            logger.error(f"🔥 JSON Parsing Error: {str(e)}")

    except Exception as e:
        logger.error(f"🔥 Critical Error: {str(e)}", exc_info=True)

    return success_response
