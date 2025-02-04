import logging
from fastapi import APIRouter, HTTPException, Depends,Request ,Response 
from sqlalchemy.orm import Session
import xml
from ..database import get_db
from ..models import MpesaTransaction
from .mpesa_aouth import stk_push_request  # import for stk_push_request
import json 
import xmltodict 
from app import schemas 
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
def initiate_payment(request: schemas.PaymentRequest, db: Session = Depends(get_db)):
    try:
        phone_number = normalize_phone_number(request.phone_number)  # Normalize the phone number
        response = stk_push_request(phone_number, request.amount)        
        logger.info(f"M-Pesa Response: {response}")  # Log the full response

        response_code = response.get("ResponseCode", "unknown")
        if response_code == "0":
            transaction = MpesaTransaction(
                phone_number=phone_number,
                amount=request.amount,
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





# XML response templates
SUCCESS_XML_RESPONSE = """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
   <soapenv:Body>
      <CheckoutResponse>
         <ResultCode>0</ResultCode>
         <ResultDesc>Success</ResultDesc>
      </CheckoutResponse>
   </soapenv:Body>
</soapenv:Envelope>"""

ERROR_XML_RESPONSE = """<?xml version="1.0" encoding="UTF-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
   <soapenv:Body>
      <CheckoutResponse>
         <ResultCode>1</ResultCode>
         <ResultDesc>Error processing request</ResultDesc>
      </CheckoutResponse>
   </soapenv:Body>
</soapenv:Envelope>"""

@router.post("/callback")
async def mpesa_callback(request: Request, db: Session = Depends(get_db)):
    try:
        raw_body = await request.body()
        if not raw_body:
            logger.error("Callback body is empty")
            return Response(content=ERROR_XML_RESPONSE, media_type="application/xml")

        content_type = request.headers.get("Content-Type", "").lower()

        # Parse XML data
        if "xml" in content_type:
            try:
                xml_data = raw_body.decode("utf-8")
                callback_data = xmltodict.parse(xml_data)
                logger.debug(f"Parsed XML callback data: {callback_data}")
            except Exception as e:
                logger.error(f"Error parsing XML: {str(e)}")
                return Response(content=ERROR_XML_RESPONSE, media_type="application/xml")

            # Extract data from parsed XML (adjust based on actual XML structure)
            try:
                envelope = callback_data.get("soapenv:Envelope", {})
                body = envelope.get("soapenv:Body", {})
                checkout_response = body.get("CheckoutResponse", {})
                
                result_code = checkout_response.get("ResultCode")
                checkout_request_id = checkout_response.get("CheckoutRequestID")
                merchant_request_id = checkout_response.get("MerchantRequestID")
                result_desc = checkout_response.get("ResultDesc")

                logger.info(f"ResultCode: {result_code}, CheckoutRequestID: {checkout_request_id}")

                # Update transaction status
                if result_code == "0":
                    transaction = db.query(MpesaTransaction).filter(
                        MpesaTransaction.checkout_request_id == checkout_request_id
                    ).first()

                    if transaction:
                        transaction.status = "completed"
                        transaction.merchant_request_id = merchant_request_id
                        transaction.result_code = result_code
                        transaction.result_desc = result_desc
                        db.commit()
                        logger.info(f"Transaction {checkout_request_id} updated to 'completed'")
                    else:
                        logger.warning(f"Transaction {checkout_request_id} not found")
                else:
                    logger.error(f"Transaction failed: {result_desc}")

            except Exception as e:
                logger.error(f"Error processing callback data: {str(e)}", exc_info=True)
                return Response(content=ERROR_XML_RESPONSE, media_type="application/xml")

        else:
            logger.error(f"Unsupported content type: {content_type}")
            return Response(content=ERROR_XML_RESPONSE, media_type="application/xml")

        return Response(content=SUCCESS_XML_RESPONSE, media_type="application/xml")

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        return Response(content=ERROR_XML_RESPONSE, media_type="application/xml")