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



# # Set up logging
# @router.post("/callback")
# async def mpesa_callback(request: Request, db: Session = Depends(get_db)):
#     success_response = {"ResultCode": 0, "ResultDesc": "Success"}

#     try:
#         # Log request method and headers
#         logger.debug(f"🔍 Request Method: {request.method}")
#         logger.debug(f"📨 Request Headers: {dict(request.headers)}")

#         # Read and log raw body
#         raw_body = await request.body()
#         raw_text = raw_body.decode(errors="ignore").strip()
#         logger.debug(f"📨 Raw Request Body: {raw_text}")

#         # If body is empty, log it and return success to avoid retry loops
#         if not raw_text:
#             logger.warning("⚠️ Empty request received from M-Pesa")
#             return success_response

#         # Try parsing JSON first
#         try:
#             json_body = await request.json()
#             logger.debug(f"📜 Parsed JSON Data: {json.dumps(json_body, indent=2)}")
#             return success_response  # Stop here to analyze logs
#         except Exception as e:
#             logger.debug("📌 Not JSON, attempting XML parsing...")
#             logger.error(f"🔥 JSON Parsing Error: {str(e)}")  # Log JSON parsing error

#         # Try parsing XML
#         try:
#             data = xmltodict.parse(raw_text)
#             logger.debug(f"📜 Parsed XML Data: {json.dumps(data, indent=2)}")
#         except xml.parsers.expat.ExpatError as e:
#             logger.error(f"🔥 XML Parsing Error (Expat): {str(e)}")
#             return success_response  # Return success to prevent retry loops
#         except Exception as e:
#             logger.error(f"🔥 General XML Parsing Error: {str(e)}")
#             return success_response  # Return success to prevent retry loops

#     except Exception as e:
#         logger.error(f"🔥 Critical Error: {str(e)}", exc_info=True)

#     return success_response


@router.post("/callback")
async def mpesa_callback(request: Request, db: Session = Depends(get_db)):
    success_response = {"ResultCode": 0, "ResultDesc": "Success"}
    error_response = {"ResultCode": 1, "ResultDesc": "Failed"}

    try:
        # Read raw request body
        raw_body = await request.body()
        raw_text = raw_body.decode(errors="ignore").strip()
        
        if not raw_text:
            logger.warning("⚠️ Empty request received from M-Pesa")
            return success_response

        # Parse XML data
        data = xmltodict.parse(raw_text)
        logger.debug(f"📜 Parsed XML Data: {json.dumps(data, indent=2)}")

        # Extract relevant information from the XML structure
        callback_data = data.get('SOAP-ENV:Envelope', {}).get('SOAP-ENV:Body', {}).get('ns0:CBPayBillResult', {})
        result_code = int(callback_data.get('ResultCode'))
        result_desc = callback_data.get('ResultDesc')
        checkout_request_id = callback_data.get('CheckoutRequestID')
        mpesa_receipt_number = callback_data.get('MpesaReceiptNumber')

        logger.info(f"📩 Callback received - ResultCode: {result_code}, CheckoutRequestID: {checkout_request_id}")

        # Find transaction in database
        transaction = db.query(MpesaTransaction).filter(
            MpesaTransaction.transaction_id == checkout_request_id
        ).first()

        if not transaction:
            logger.error(f"❌ Transaction not found: {checkout_request_id}")
            return error_response

        # Update transaction status based on result code
        if result_code == 0:
            transaction.status = "success"
            transaction.mpesa_code = mpesa_receipt_number
            logger.info(f"✅ Updated transaction {checkout_request_id} to success")
        else:
            transaction.status = "failed"
            logger.warning(f"❌ Transaction {checkout_request_id} failed: {result_desc}")

        db.commit()

    except Exception as e:
        logger.error(f"🔥 Critical Error: {str(e)}", exc_info=True)
        db.rollback()
        return error_response

    return success_response