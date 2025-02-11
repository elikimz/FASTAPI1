import logging
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from datetime import datetime
import base64, httpx
from ..database import SessionLocal
from ..models import MpesaTransaction
from .mpesa_aouth import get_mpesa_token
from ..config import setting

router = APIRouter(
    tags=["Mpesa"]
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def generate_password():
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    data_to_encode = f"{setting.MPESA_SHORTCODE}{setting.MPESA_PASSKEY}{timestamp}"
    encoded_password = base64.b64encode(data_to_encode.encode()).decode('utf-8')
    return encoded_password, timestamp

@router.post("/stk_push/")
async def initiate_stk_push(phone_number: str, amount: int, db: Session = Depends(get_db)):
    access_token = await get_mpesa_token()
    print(f"Access Token Used: {access_token}")  # Debug token

    password, timestamp = generate_password()
    print(f"Generated Password: {password}, Timestamp: {timestamp}")  # Debug password

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    print(f"Headers Sent: {headers}")  # Debug headers

    payload = {
        "BusinessShortCode": setting.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": setting.MPESA_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": setting.CALLBACK_URL,
        "AccountReference": "FastAPI Payment",
        "TransactionDesc": "Payment for goods"
    }
    print(f"Payload Sent: {payload}")  # Debug payload

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{setting.MPESA_BASE_URL}/mpesa/stkpush/v1/processrequest", json=payload, headers=headers)
        print(f"STK Push Response: {response.status_code}, {response.text}")  # Debug response
        
        res_data = response.json()

        # Save transaction in DB
        transaction = MpesaTransaction(
            merchant_request_id=res_data.get('MerchantRequestID'),
            checkout_request_id=res_data.get('CheckoutRequestID'),
            amount=amount,
            phone_number=phone_number,
            status='pending',
            created_at=datetime.now()
        )
        db.add(transaction)
        db.commit()
        db.refresh(transaction)

        return {"message": "STK Push initiated", "transaction": res_data}


@router.api_route("/callback", methods=["GET", "POST"])
async def mpesa_callback(request: Request):
    if request.method == "GET":
        logging.info("Received GET request (likely a health check from Safaricom)")
        return {"message": "GET request received, URL is live"}

    # Handle POST request (actual transaction callback)
    body = await request.body()
    logging.info(f"Raw callback body: {body.decode('utf-8')}")

    try:
        data = await request.json()
        logging.info(f"Parsed JSON: {data}")
        return {"ResultCode": 0, "ResultDesc": "Accepted"}
    except Exception as e:
        logging.error(f"Error processing callback: {e}")
        return {"ResultCode": 1, "ResultDesc": "Error"}