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



# Set up logging
@router.post("/callback")
async def mpesa_callback(request: Request, db: Session = Depends(get_db)):
    success_response = Response(
        content='<?xml version="1.0" encoding="UTF-8"?><Response><ResultCode>0</ResultCode><ResultDesc>Success</ResultDesc></Response>',
        media_type="application/xml"
    )

    try:
        raw_xml = await request.body()

        # Log raw XML content for debugging
        logger.debug(f"📨 Raw XML (bytes): {raw_xml}")
        logger.debug(f"📨 Raw XML (decoded): {raw_xml.decode()}")

        # Check if XML is empty
        if not raw_xml.strip():
            logger.warning("⚠️ Empty healthcheck or invalid XML received")
            return success_response

        # Try parsing the XML
        try:
            data = xmltodict.parse(raw_xml)
            logger.debug(f"📜 Parsed XML Data: {json.dumps(data, indent=2)}")
        except xml.parsers.expat.ExpatError as e:
            logger.error(f"🔥 XML Parsing Error: {str(e)}")
            return success_response

        # Extract STKCallback (handle XML namespaces)
        envelope = data.get("soapenv:Envelope", data.get("Envelope", {}))
        body = envelope.get("soapenv:Body", envelope.get("Body", {}))
        callback = body.get("stk:STKCallback", body.get("STKCallback", {}))

        logger.debug(f"🔍 Extracted Callback: {json.dumps(callback, indent=2)}")

        transaction_id = callback.get("CheckoutRequestID")
        result_code_str = callback.get("ResultCode")
        result_code = int(result_code_str) if result_code_str else -1

        logger.info(f"🔧 Processing: TransactionID={transaction_id}, ResultCode={result_code}")

        # Find transaction
        transaction = db.query(MpesaTransaction).filter_by(transaction_id=transaction_id).first()
        if not transaction:
            logger.error(f"❌ Transaction {transaction_id} not found!")
            return success_response

        logger.debug(f"💾 Current Status: {transaction.status}")

        # Update status
        new_status = "successful" if result_code == 0 else "failed"
        transaction.status = new_status
        logger.debug(f"🔄 New Status: {new_status}")

        # Handle metadata (for successful transactions)
        if result_code == 0:
            try:
                metadata = callback.get("CallbackMetadata", {}).get("Item", [])
                items = {item["Name"]: item["Value"] for item in metadata}
                transaction.mpesa_code = items.get("MpesaReceiptNumber")
                transaction.phone_number = items.get("PhoneNumber")
                logger.debug(f"📦 Metadata: {items}")
            except KeyError as e:
                logger.error(f"❗ Metadata Error: {e}")

        # Commit changes
        db.commit()
        db.refresh(transaction)  # Refresh to confirm update
        logger.info(f"✅ Updated Transaction: {transaction_id} -> {new_status}")
        logger.debug(f"💾 Post-Commit Status: {transaction.status}")

    except Exception as e:
        logger.error(f"🔥 Critical Error: {str(e)}", exc_info=True)
        db.rollback()  # Rollback on error

    return success_response
