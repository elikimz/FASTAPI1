import logging
import xmltodict
from fastapi import APIRouter, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import MpesaTransaction
from .mpesa_aouth import stk_push_request  # Ensure correct import

router = APIRouter(prefix="/mpesa", tags=["M-Pesa"])
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# XML Response Templates
XML_RESPONSES = {
    "success": """<?xml version="1.0" encoding="UTF-8"?>
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
        <soapenv:Body>
            <CheckoutResponse>
                <ResultCode>0</ResultCode>
                <ResultDesc>Success</ResultDesc>
            </CheckoutResponse>
        </soapenv:Body>
    </soapenv:Envelope>""",
    
    "error": """<?xml version="1.0" encoding="UTF-8"?>
    <soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
        <soapenv:Body>
            <CheckoutResponse>
                <ResultCode>1</ResultCode>
                <ResultDesc>Error processing request</ResultDesc>
            </CheckoutResponse>
        </soapenv:Body>
    </soapenv:Envelope>"""
}

def normalize_phone_number(phone_number: str) -> str:
    """Normalize Kenyan phone numbers to 2547XXXXXXXX format."""
    digits = "".join(filter(str.isdigit, str(phone_number)))  # Ensure string conversion
    
    if len(digits) == 9 and digits.startswith("7"):
        return f"254{digits}"
    elif len(digits) == 10 and digits.startswith("0"):
        return f"254{digits[1:]}"
    elif len(digits) == 12 and digits.startswith("254"):
        return digits
    raise ValueError("Invalid phone number format. Use 07XXXXXXXX or 2547XXXXXXXX")

@router.post("/pay")
async def initiate_payment(request: Request, db: Session = Depends(get_db)):
    """Process payment requests with M-Pesa STK Push."""
    try:
        data = await request.json()
        phone_number = data.get("phone_number")
        amount = data.get("amount")

        if not phone_number or not amount:
            raise HTTPException(status_code=400, detail="Phone number and amount are required")

        phone_number = normalize_phone_number(phone_number)
        logger.info(f"Initiating payment for {phone_number}, Amount: {amount}")

        # Process payment request
        stk_response = stk_push_request(phone_number, amount)

        if stk_response.get("ResponseCode") != "0":
            error_msg = stk_response.get("errorMessage", "Payment request failed")
            logger.error(f"STK Error: {error_msg}")
            raise HTTPException(status_code=400, detail=error_msg)

        # Save transaction
        transaction = MpesaTransaction(
            phone_number=phone_number,
            amount=amount,
            checkout_request_id=stk_response["CheckoutRequestID"],
            status="pending"
        )
        db.add(transaction)
        db.commit()

        return {"message": "Payment initiated", "checkout_id": stk_response["CheckoutRequestID"]}

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        logger.error(f"Payment error: {str(e)}", exc_info=True)
        db.rollback()
        raise HTTPException(status_code=500, detail="Internal server error")
