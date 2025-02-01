from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import MpesaTransaction
from mpesa import stk_push_request


router = APIRouter(prefix="/mpesa", tags=["M-Pesa"])

# Endpoint to initiate payment
@router.post("/pay")
def initiate_payment(phone_number: str, amount: float, db: Session = Depends(get_db)):
    response = stk_push_request(phone_number, amount)
    
    if response.get("ResponseCode") == "0":
        transaction = MpesaTransaction(phone_number=phone_number, amount=amount, transaction_id=response["CheckoutRequestID"], status="pending")
        db.add(transaction)
        db.commit()
        return {"message": "Payment request sent", "transaction_id": response["CheckoutRequestID"]}
    else:
        raise HTTPException(status_code=400, detail="Payment request failed")

# Endpoint to handle M-Pesa callbacks
@router.post("/callback")
def mpesa_callback(data: dict, db: Session = Depends(get_db)):
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