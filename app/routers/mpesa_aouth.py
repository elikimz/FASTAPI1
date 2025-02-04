import requests
import base64
from datetime import datetime

from ..config import setting  # Assuming your settings (MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET, etc.) are in a config file

# Function to get M-Pesa access token
def get_mpesa_token():
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    try:
        response = requests.get(url, auth=(setting.MPESA_CONSUMER_KEY, setting.MPESA_CONSUMER_SECRET))

        if response.status_code == 200:
            return response.json().get("access_token")
        else:
            raise Exception(f"Failed to authenticate with M-Pesa, Status Code: {response.status_code}, Response: {response.text}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error occurred while fetching token: {str(e)}")

# Function to initiate an STK Push reques
def stk_push_request(phone_number, amount):
    amount = int(amount)  # Convert to integer
    try:
        access_token = get_mpesa_token()

        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        password = base64.b64encode(f"{setting.MPESA_SHORTCODE}{setting.MPESA_PASSKEY}{timestamp}".encode()).decode()

        payload = {
            "BusinessShortCode": setting.MPESA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": phone_number,  # Must be 2547XXXXXXXX (no +)
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

        # Send the request to M-Pesa
        response = requests.post("https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest", json=payload, headers=headers)

        # Log the request and response for debugging
        print("M-Pesa Request Payload:", payload)
        print("M-Pesa Response Status Code:", response.status_code)
        print("M-Pesa Response Body:", response.json())

        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"Failed to initiate STK Push, Status Code: {response.status_code}, Response: {response.text}")

    except Exception as e:
        print(f"Error initiating payment: {str(e)}")  # Detailed error log
        raise Exception(f"Error initiating payment: {str(e)}")