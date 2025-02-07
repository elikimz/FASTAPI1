import os
import base64
import datetime
import requests
from sqlalchemy.orm import Session
from ..models import MpesaTransaction
from..config import setting

# Load credentials from environment variables
BUSINESS_SHORTCODE = setting.MPESA_SHORTCODE
PASSKEY = setting.MPESA_PASSKEY
CALLBACK_URL = setting.CALLBACK_URL

def get_access_token():
    """Fetch M-Pesa access token."""
    auth_url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(auth_url, auth=(setting.MPESA_CONSUMER_KEY, setting.MPESA_CONSUMER_SECRET))
    
    if response.status_code == 200:
        return response.json().get("access_token")
    return None

def stk_push_request(phone_number: str, amount: int):
    """Initiate Lipa na M-Pesa STK Push."""
    access_token = get_access_token()
    if not access_token:
        return {"error": "Failed to obtain access token"}

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(f"{BUSINESS_SHORTCODE}{PASSKEY}{timestamp}".encode()).decode()

    payload = {
        "BusinessShortCode": BUSINESS_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": BUSINESS_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": CALLBACK_URL,
        "AccountReference": "HospitalMgt",
        "TransactionDesc": "Payment for services"
    }
    

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.post(
        "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest",
        json=payload,
        headers=headers
    )

    if response.status_code == 200:
        return response.json()
    
    return {"error": "Failed to initiate payment"}
