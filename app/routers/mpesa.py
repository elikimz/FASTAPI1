from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.mpesa import MpesaTransaction

router = APIRouter(prefix="/mpesa", tags=["M-Pesa"])

@router.post("/payment")
def process_payment(phone_number: str, amount: float, db: Session = Depends(get_db)):
    transaction = MpesaTransaction(phone_number=phone_number, amount=amount, transaction_id="TXN123456")
    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return {"message": "Payment initiated", "transaction": transaction}
