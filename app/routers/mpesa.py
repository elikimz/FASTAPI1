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
    try:
        raw_xml = await request.body()
        logger.info(f"🔥 Raw Callback Content: {raw_xml.decode()}")

        # Check for empty payload first
        if not raw_xml.strip():
            logger.warning("⚠️ Received empty callback payload")
            return Response(
                content='<Response><ResultCode>0</ResultCode><ResultDesc>Success</ResultDesc></Response>',
                media_type="application/xml"
            )

        # Attempt XML parsing
        try:
            data = xmltodict.parse(raw_xml)
        except Exception as parse_error:
            logger.error(f"🚨 XML Parsing Error: {str(parse_error)}")
            return Response(
                content='<Response><ResultCode>0</ResultCode><ResultDesc>Success</ResultDesc></Response>',
                media_type="application/xml"
            )

        # Process valid XML
        callback = data.get('soapenv:Envelope', {}).get('soapenv:Body', {}).get('ns0:STKCallback')
        
        if not callback:
            logger.error("🚨 Invalid callback structure")
            return Response(
                content='<Response><ResultCode>0</ResultCode><ResultDesc>Success</ResultDesc></Response>',
                media_type="application/xml"
            )

        transaction_id = callback.get('CheckoutRequestID')
        result_code = int(callback.get('ResultCode'))
        result_desc = callback.get('ResultDesc')

        transaction = db.query(MpesaTransaction).filter_by(transaction_id=transaction_id).first()
        if transaction:
            if result_code == 0:
                transaction.status = "successful"
                if 'CallbackMetadata' in callback:
                    items = {item['Name']: item['Value'] for item in callback['CallbackMetadata']['Item']}
                    transaction.mpesa_code = items.get('MpesaReceiptNumber')
            else:
                transaction.status = "failed"
            db.commit()

        # Always return success response to M-Pesa
        return Response(
            content='<Response><ResultCode>0</ResultCode><ResultDesc>Success</ResultDesc></Response>',
            media_type="application/xml"
        )

    except Exception as e:
        logger.error(f"🚨 Critical error: {str(e)}", exc_info=True)
        return Response(
            content='<Response><ResultCode>0</ResultCode><ResultDesc>Success</ResultDesc></Response>',
            media_type="application/xml"
        )