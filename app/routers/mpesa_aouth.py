import requests
import base64
import datetime
from ..config import setting

# Function to get M-Pesa access token
def get_mpesa_token():
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    response = requests.get(url, auth=(setting.MPESA_CONSUMER_KEY, setting.MPESA_CONSUMER_SECRET))

    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        raise Exception("Failed to authenticate with M-Pesa")

# Function to initiate an STK Push request
def stk_push_request(phone_number, amount):
    access_token = get_mpesa_token()

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode(f"{setting.MPESA_SHORTCODE}{setting.MPESA_PASSKEY}{timestamp}".encode()).decode()

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
        "AccountReference": "Test",
        "TransactionDesc": "Payment"
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    response = requests.post("https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest", json=payload, headers=headers)

    return response.json()
