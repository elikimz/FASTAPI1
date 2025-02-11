from fastapi import FastAPI, Request
import httpx
import base64
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

app = FastAPI()

# Load environment variables
CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET")
SHORTCODE = os.getenv("MPESA_SHORTCODE")
PASSKEY = os.getenv("MPESA_PASSKEY")
BASE_URL = os.getenv("MPESA_BASE_URL")
CALLBACK_URL = os.getenv("CALLBACK_URL")


async def get_access_token():
    url = f"{BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, auth=(CONSUMER_KEY, CONSUMER_SECRET))
        response_data = response.json()
        return response_data["access_token"]


def generate_password():
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    data_to_encode = SHORTCODE + PASSKEY + timestamp
    encoded_password = base64.b64encode(data_to_encode.encode()).decode('utf-8')
    return encoded_password, timestamp


@app.post("/stk_push/")
async def stk_push(phone_number: str, amount: int):
    access_token = await get_access_token()
    password, timestamp = generate_password()

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    payload = {
        "BusinessShortCode": SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": CALLBACK_URL,
        "AccountReference": "TestPayment",
        "TransactionDesc": "Payment for goods"
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/mpesa/stkpush/v1/processrequest", json=payload, headers=headers)
        return response.json()


@app.post("/callback/")
async def mpesa_callback(request: Request):
    callback_data = await request.json()
    print("Callback received:", callback_data)
    return {"message": "Callback received successfully"}
