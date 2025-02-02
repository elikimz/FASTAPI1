# import logging
# from fastapi import APIRouter, HTTPException, Depends,Request ,Response 
# from sqlalchemy.orm import Session
# import xml
# from ..database import get_db
# from ..models import MpesaTransaction
from .mpesa_aouth import stk_push_request  # Correct import for stk_push_request
# import json 
# import xmltodict  # Add this at top of file

# router = APIRouter(prefix="/mpesa", tags=["M-Pesa"])

# # Set up logging
# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)

# # Helper function to normalize phone number
# def normalize_phone_number(phone_number: str):
#     # Remove all non-digit characters (e.g., +, spaces)
#     digits = "".join(filter(str.isdigit, phone_number))
    
#     if digits.startswith("0") and len(digits) == 9:  # Handle 07XXXXXXXX
#         return "254" + digits[1:]
#     elif digits.startswith("254") and len(digits) == 12:  # Already valid
#         return digits
#     else:
#         raise ValueError("Invalid phone number. Use 07XXXXXXXX or 2547XXXXXXXX.")
    
# # Endpoint to initiate payment
# @router.post("/pay")
# def initiate_payment(phone_number: str, amount: float, db: Session = Depends(get_db)):
#     try:
#         phone_number = normalize_phone_number(phone_number)  # Normalize the phone number
#         response = stk_push_request(phone_number, amount)
#         logger.info(f"M-Pesa Response: {response}")  # Log the full response

#         response_code = response.get("ResponseCode", "unknown")
#         if response_code == "0":
#             transaction = MpesaTransaction(
#                 phone_number=phone_number,
#                 amount=amount,
#                 transaction_id=response["CheckoutRequestID"],
#                 status="pending"
#             )
#             db.add(transaction)
#             db.commit()
#             return {"message": "Payment request sent", "transaction_id": response["CheckoutRequestID"]}
#         else:
#             error_message = response.get('errorMessage', 'Unknown error')
#             raise HTTPException(status_code=400, detail=f"Payment request failed: {error_message}")
#     except Exception as e:
#         logger.error(f"Error initiating payment: {str(e)}")  # Log the exception
#         raise HTTPException(status_code=500, detail="Internal server error while initiating payment")



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


# app/routers/mpesa.py
import logging
from fastapi import APIRouter, HTTPException, Depends, Request, Response
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import MpesaTransaction
import xmltodict
import json
from collections import OrderedDict

router = APIRouter(prefix="/mpesa", tags=["M-Pesa"])
logger = logging.getLogger(__name__)

def normalize_phone_number(phone_number: str):
    digits = "".join(filter(str.isdigit, phone_number))
    if digits.startswith("0") and len(digits) == 9:
        return "254" + digits[1:]
    elif digits.startswith("254") and len(digits) == 12:
        return digits
    raise ValueError("Invalid phone number format")

def parse_mpesa_callback(raw_xml: bytes) -> dict:
    """Robust XML parser with namespace handling"""
    try:
        data = xmltodict.parse(
            raw_xml,
            process_namespaces=True,
            namespaces={
                "http://schemas.xmlsoap.org/soap/envelope/": "soapenv",
                "http://safaricom.co.ke/LNM/": "stk"
            }
        )
        
        # Try different XML structure variations
        callback = (
            data.get("soapenv:Envelope", {})
            .get("soapenv:Body", {})
            .get("stk:STKCallback") or
            data.get("Envelope", {})
            .get("Body", {})
            .get("STKCallback")
        )
        
        if not callback:
            for key in data.get("Envelope", {}).get("Body", {}).keys():
                if "STKCallback" in key:
                    callback = data["Envelope"]["Body"][key]
                    break

        return callback or {}
    except Exception as e:
        logger.error(f"XML parsing failed: {str(e)}")
        return {}

@router.post("/pay")
def initiate_payment(phone_number: str, amount: float, db: Session = Depends(get_db)):
    try:
        normalized_phone = normalize_phone_number(phone_number)
        response = stk_push_request(normalized_phone, amount)
        
        if response.get("ResponseCode") == "0":
            transaction = MpesaTransaction(
                phone_number=normalized_phone,
                amount=amount,
                transaction_id=response["CheckoutRequestID"],
                status="pending"
            )
            db.add(transaction)
            db.commit()
            return {
                "message": "Payment request sent",
                "transaction_id": response["CheckoutRequestID"]
            }
        raise HTTPException(status_code=400, detail=response.get("errorMessage", "Payment request failed"))
    except Exception as e:
        logger.error(f"Payment initiation error: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/callback")
async def mpesa_callback(request: Request, db: Session = Depends(get_db)):
    success_response = Response(
        content='<?xml version="1.0" encoding="UTF-8"?>'
                '<Response><ResultCode>0</ResultCode><ResultDesc>Success</ResultDesc></Response>',
        media_type="application/xml"
    )

    try:
        raw_xml = await request.body()
        if not raw_xml.strip():
            logger.warning("Empty healthcheck received")
            return success_response

        logger.debug(f"Raw XML received:\n{raw_xml.decode()}")

        # Parse XML data
        callback_data = parse_mpesa_callback(raw_xml)
        logger.debug(f"Parsed callback data: {json.dumps(callback_data, indent=2)}")

        # Extract critical fields
        transaction_id = callback_data.get("CheckoutRequestID")
        result_code = callback_data.get("ResultCode", "1")
        
        if not transaction_id:
            logger.error("Missing transaction ID in callback")
            return success_response

        # Database operation
        transaction = db.query(MpesaTransaction).filter_by(
            transaction_id=transaction_id
        ).with_for_update().first()

        if not transaction:
            logger.error(f"Transaction not found: {transaction_id}")
            return success_response

        # Update transaction status
        new_status = "successful" if result_code == "0" else "failed"
        transaction.status = new_status

        # Handle successful transaction metadata
        if result_code == "0":
            metadata_items = callback_data.get("CallbackMetadata", {}).get("Item", [])
            metadata = {item["Name"]: item["Value"] for item in metadata_items}
            transaction.mpesa_code = metadata.get("MpesaReceiptNumber")
            transaction.phone_number = metadata.get("PhoneNumber", "")

        db.commit()
        logger.info(f"Updated transaction {transaction_id} to {new_status}")

    except Exception as e:
        logger.error(f"Callback processing error: {str(e)}", exc_info=True)
        db.rollback()

    return success_response