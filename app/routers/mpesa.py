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
        # Get raw request body
        raw_body = await request.body()
        logger.debug(f"Raw callback body length: {len(raw_body)} bytes")

        # Handle empty body immediately
        if not raw_body:
            logger.error("Received empty callback body")
            return Response(
                content='<?xml version="1.0" encoding="UTF-8"?><Response><ResultCode>1</ResultCode><ResultDesc>Empty request</ResultDesc></Response>',
                media_type="application/xml"
            )

        # Convert bytes to string for inspection
        raw_text = raw_body.decode('utf-8', errors='replace').strip()
        logger.debug(f"Raw callback content:\n{raw_text}")

        # Validate basic XML structure
        if not raw_text.startswith('<'):
            logger.error("Received non-XML content in callback")
            return Response(
                content='<?xml version="1.0" encoding="UTF-8"?><Response><ResultCode>1</ResultCode><ResultDesc>Invalid format</ResultDesc></Response>',
                media_type="application/xml"
            )

        # Parse XML with error handling
        try:
            data = xmltodict.parse(raw_body)
            logger.debug(f"Parsed XML data: {json.dumps(data, indent=2)}")
        except Exception as e:
            logger.error(f"XML parsing failed: {str(e)}")
            logger.error(f"Faulty XML content: {raw_text}")
            return Response(
                content='<?xml version="1.0" encoding="UTF-8"?><Response><ResultCode>1</ResultCode><ResultDesc>Invalid XML</ResultDesc></Response>',
                media_type="application/xml"
            )

        # Extract transaction details based on M-Pesa's actual structure
        try:
            stk_call = data.get('soapenv:Envelope', {}).get('soapenv:Body', {}).get('stkCallback', {})
            if not stk_call:
                stk_call = data.get('SOAP-ENV:Envelope', {}).get('SOAP-ENV:Body', {}).get('stkCallback', {})

            result_code = stk_call.get('ResultCode')
            checkout_id = stk_call.get('CheckoutRequestID')
            merchant_id = stk_call.get('MerchantRequestID')

            if not all([result_code, checkout_id, merchant_id]):
                logger.error("Missing required fields in callback")
                logger.error(f"Full callback data: {data}")
                return Response(
                    content='<?xml version="1.0" encoding="UTF-8"?><Response><ResultCode>1</ResultCode><ResultDesc>Missing fields</ResultDesc></Response>',
                    media_type="application/xml"
                )

            # Update database transaction
            transaction = db.query(MpesaTransaction).filter(
                MpesaTransaction.checkout_request_id == checkout_id
            ).first()

            if transaction:
                transaction.status = "completed" if result_code == "0" else "failed"
                transaction.result_code = result_code
                transaction.merchant_request_id = merchant_id
                db.commit()
                logger.info(f"Updated transaction {checkout_id} with result code {result_code}")
            else:
                logger.warning(f"Transaction not found for CheckoutID: {checkout_id}")

        except Exception as e:
            logger.error(f"Callback processing failed: {str(e)}")
            return Response(
                content='<?xml version="1.0" encoding="UTF-8"?><Response><ResultCode>1</ResultCode><ResultDesc>Processing error</ResultDesc></Response>',
                media_type="application/xml"
            )

        # Always return XML response
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response><ResultCode>0</ResultCode><ResultDesc>Success</ResultDesc></Response>',
            media_type="application/xml"
        )

    except Exception as e:
        logger.error(f"Unexpected error in callback: {str(e)}", exc_info=True)
        return Response(
            content='<?xml version="1.0" encoding="UTF-8"?><Response><ResultCode>1</ResultCode><ResultDesc>Server error</ResultDesc></Response>',
            media_type="application/xml"
        )