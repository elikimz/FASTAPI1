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
# Callback endpoint to receive M-Pesa response
@router.post("/callback")
async def mpesa_callback(request: Request, db: Session = Depends(get_db)):
    success_response = {"ResultCode": 0, "ResultDesc": "Success"}

    try:
        # Log raw body
        raw_body = await request.body()  # Capture the raw request body
        raw_text = raw_body.decode(errors="ignore").strip()  # Decode the body as a string
        logger.debug(f"Raw Callback Body: {raw_text}")  # Log the raw body to see the full data

        # If the body is empty, log it and return success to avoid retry loops
        if not raw_text:
            logger.warning("⚠️ Empty request received from M-Pesa")
            return success_response

        # Try parsing JSON first
        try:
            json_body = await request.json()  # Try to parse as JSON
            logger.debug(f"Parsed JSON Data: {json_body}")
            return success_response  # You can choose to return success or handle accordingly
        except Exception as e:
            logger.debug(f"JSON Parsing Error: {str(e)}")  # If JSON parsing fails, log the error

        # Try parsing XML if JSON fails
        try:
            data = xmltodict.parse(raw_text)  # Try to parse the raw body as XML
            logger.debug(f"Parsed XML Data: {data}")  # Log the parsed XML data

            # Process the parsed data (e.g., extract important fields for transaction updates)
            if data and 'Body' in data:
                body = data['Body']
                if 'stkCallback' in body:
                    stk_callback = body['stkCallback']
                    result_code = stk_callback.get('ResultCode', None)
                    result_desc = stk_callback.get('ResultDesc', None)
                    checkout_request_id = stk_callback.get('CheckoutRequestID', None)

                    # Handle the data and update your database or any other logic
                    if result_code == '0':  # Success
                        # You can update the transaction status in the database here
                        transaction = db.query(MpesaTransaction).filter(MpesaTransaction.transaction_id == checkout_request_id).first()
                        if transaction:
                            transaction.status = "success"
                            transaction.mpesa_code = result_desc  # You can store the result description or any other code
                            db.commit()
                            logger.info(f"Transaction {checkout_request_id} updated to success.")
                    else:  # Failure
                        # Handle failure scenario
                        transaction = db.query(MpesaTransaction).filter(MpesaTransaction.transaction_id == checkout_request_id).first()
                        if transaction:
                            transaction.status = "failed"
                            db.commit()
                            logger.info(f"Transaction {checkout_request_id} marked as failed.")

        except xml.parsers.expat.ExpatError as e:
            logger.error(f"XML Parsing Error: {str(e)}")
            return success_response  # Return success to prevent retry loops
        except Exception as e:
            logger.error(f"General Error during XML parsing: {str(e)}")
            return success_response  # Return success to prevent retry loops

    except Exception as e:
        logger.error(f"Critical Error: {str(e)}", exc_info=True)

    return success_response