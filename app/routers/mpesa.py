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
        # Get raw XML body
        raw_body = await request.body()
        logger.debug(f"Raw Callback Body: {raw_body.decode()}")

        if not raw_body:
            logger.warning("Empty callback received")
            return Response(content="<Response><ResultCode>1</ResultCode><ResultDesc>Empty request</ResultDesc></Response>", media_type="application/xml")

        # Parse XML to dict
        data = xmltodict.parse(raw_body)
        logger.debug(f"Parsed Callback Data: {data}")

        # Extract critical information
        callback_data = data.get("SOAP-ENV:Envelope", {}).get("SOAP-ENV:Body", {}).get("CheckoutRequestResponse", {})
        result_code = callback_data.get("ResultCode")
        checkout_id = callback_data.get("CheckoutRequestID")

        if not checkout_id:
            logger.error("Missing CheckoutRequestID in callback")
            return Response(content="<Response><ResultCode>1</ResultCode><ResultDesc>Missing CheckoutRequestID</ResultDesc></Response>", media_type="application/xml")

        # Update database
        transaction = db.query(MpesaTransaction).filter(
            MpesaTransaction.checkout_request_id == checkout_id
        ).first()

        if transaction:
            transaction.status = "completed" if result_code == "0" else "failed"
            db.commit()
            logger.info(f"Updated transaction {checkout_id} to status {transaction.status}")
        else:
            logger.warning(f"Transaction not found for CheckoutRequestID: {checkout_id}")

        # Return XML response as required by M-Pesa
        return Response(
            content=f'<Response><ResultCode>0</ResultCode><ResultDesc>Success</ResultDesc></Response>',
            media_type="application/xml"
        )

    except Exception as e:
        logger.error(f"Callback processing error: {str(e)}", exc_info=True)
        return Response(content="<Response><ResultCode>1</ResultCode><ResultDesc>Error processing request</ResultDesc></Response>", media_type="application/xml")