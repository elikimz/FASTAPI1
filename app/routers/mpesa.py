import logging
from fastapi import APIRouter, HTTPException, Depends,Request ,Response 
from sqlalchemy.orm import Session
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



@router.post("/callback")
async def mpesa_callback(request: Request, db: Session = Depends(get_db)):
    success_response = Response(
        content='<?xml version="1.0" encoding="UTF-8"?>'
                '<Response>'
                '<ResultCode>0</ResultCode>'
                '<ResultDesc>Success</ResultDesc>'
                '</Response>',
        media_type="application/xml"
    )

    try:
        raw_xml = await request.body()

        if not raw_xml.strip():
            logger.warning("⚠️ Received empty ping/healthcheck")
            return success_response

        logger.debug(f"📨 Raw Callback Content:\n{raw_xml.decode()}")

        try:
            data = xmltodict.parse(raw_xml)
        except Exception as e:
            logger.error(f"🚨 XML Parsing Failed: {str(e)}")
            return success_response

        logger.debug(f"📜 Parsed Callback Data:\n{data}")

        # Dynamically find STKCallback element regardless of namespace
        envelope = data.get('soapenv:Envelope', {})
        body = envelope.get('soapenv:Body', {})
        callback_key = next((key for key in body if key.endswith('STKCallback')), None)

        if not callback_key:
            logger.error("❌ STKCallback not found in XML data")
            return success_response

        callback = body[callback_key]

        # Extract CheckoutRequestID dynamically
        checkout_request_id_key = next((k for k in callback if k.endswith('CheckoutRequestID')), None)
        transaction_id = callback.get(checkout_request_id_key) if checkout_request_id_key else None

        # Extract ResultCode dynamically
        result_code_key = next((k for k in callback if k.endswith('ResultCode')), None)
        result_code = int(callback.get(result_code_key, -1)) if result_code_key else -1

        if not transaction_id:
            logger.error("❌ CheckoutRequestID missing in callback")
            return success_response

        transaction = db.query(MpesaTransaction).filter_by(transaction_id=transaction_id).first()
        if transaction:
            transaction.status = "successful" if result_code == 0 else "failed"
            
            if result_code == 0:
                # Extract CallbackMetadata items
                metadata_key = next((k for k in callback if k.endswith('CallbackMetadata')), None)
                if metadata_key:
                    items = callback[metadata_key].get('Item', [])
                    item_dict = {}
                    for item in items:
                        name_key = next((k for k in item if k.endswith('Name')), None)
                        value_key = next((k for k in item if k.endswith('Value')), None)
                        if name_key and value_key:
                            name = item[name_key]
                            value = item[value_key]
                            item_dict[name] = value
                    transaction.mpesa_code = item_dict.get('MpesaReceiptNumber')
                    transaction.phone_number = item_dict.get('PhoneNumber')
            
            db.commit()
            logger.info(f"✅ Updated transaction {transaction_id} to {transaction.status}")
        else:
            logger.warning(f"⚠️ Transaction {transaction_id} not found")

        return success_response

    except Exception as e:
        logger.error(f"🔥 Critical Error: {str(e)}", exc_info=True)
        return success_response