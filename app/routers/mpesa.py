from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import MpesaTransaction
from .mpesa_aouth import stk_push_request


router = APIRouter(prefix="/mpesa", tags=["M-Pesa"])

# Helper function to normalize phone number
def normalize_phone_number(phone_number: str):
    if phone_number.startswith("0"):
        phone_number = "+254" + phone_number[1:]  # Convert 07x to +2547xx
    elif not phone_number.startswith("+254"):
        raise ValueError("Invalid phone number format, should start with +254")
    return phone_number

# Endpoint to initiate payment
@router.post("/pay")
def initiate_payment(phone_number: str, amount: float, db: Session = Depends(get_db)):
    try:
        phone_number = normalize_phone_number(phone_number)  # Normalize the phone number
        response = stk_push_request(phone_number, amount)
        print(f"M-Pesa Response: {response}")  # Log the full response

        if response.get("ResponseCode") == "0":
            transaction = MpesaTransaction(phone_number=phone_number, amount=amount, transaction_id=response["CheckoutRequestID"], status="pending")
            db.add(transaction)
            db.commit()
            return {"message": "Payment request sent", "transaction_id": response["CheckoutRequestID"]}
        else:
            raise HTTPException(status_code=400, detail=f"Payment request failed: {response.get('errorMessage')}")
    except Exception as e:
        print(f"Error initiating payment: {e}")  # Log the exception
        raise HTTPException(status_code=500, detail="Internal server error while initiating payment")

# Endpoint to handle M-Pesa callbacks
@router.post("/callback")
def mpesa_callback(data: dict, db: Session = Depends(get_db)):
    print(f"Received callback data: {data}")  # Log the callback data for inspection

    callback = data.get("Body", {}).get("stkCallback", {})
    transaction_id = callback.get("CheckoutRequestID")
    
    transaction = db.query(MpesaTransaction).filter_by(transaction_id=transaction_id).first()
    
    if not transaction:
        return {"error": "Transaction not found"}

    if callback.get("ResultCode") == 0:
        transaction.status = "successful"
    else:
        transaction.status = "failed"

    db.commit()
    return {"message": "Callback received"}
