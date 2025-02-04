import json
import requests
import base64
from datetime import datetime
from ..config import setting  # Assuming your settings (MPESA_CONSUMER_KEY, MPESA_CONSUMER_SECRET, etc.) are in a config file

# Function to get M-Pesa access token
def get_mpesa_token():
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    auth = ("MY678jeKGHNhLGvgkq0BS0BHCrSDWHpP8zmSGhWEoTCdZYxf", "g0G8T6vhKEk5rAy3uXxCqLibZzwUO0D7VpBjIpDEOU1hL4RRg6V7N0PYPLxagvMU")
    
    response = requests.get(url, auth=auth)

    if response.status_code == 200:
        token = response.json().get('access_token')
        print("Generated token:", token)  # Prints the token to verify
        return token
    else:
        print(f"Failed to generate token: {response.text}")
        raise Exception("Failed to generate token")

# Function to initiate STK push (Payment Request)

def get_mpesa_token():
    url = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"
    auth = ("MY678jeKGHNhLGvgkq0BS0BHCrSDWHpP8zmSGhWEoTCdZYxf", "g0G8T6vhKEk5rAy3uXxCqLibZzwUO0D7VpBjIpDEOU1hL4RRg6V7N0PYPLxagvMU")
    
    response = requests.get(url, auth=auth)
    print(f"Token generation response: {response.text}")

    if response.status_code == 200:
        token = response.json().get('access_token')
        print("Generated token:", token)
        return token
    else:
        raise Exception("Failed to generate token")

def stk_push_request(phone_number, amount):
    access_token = get_mpesa_token()
    
    # Dynamically generate the timestamp
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    
    url = "https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest"
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }
    
    payload = {
        "BusinessShortCode": "174379",
        "Password": "MTc0Mzc5YmZiMjc5ZjlhYTliZGJjZjE1OGU5N2RkNzFhNDY3Y2QyZTBjODkzMDU5YjEwZjc4ZTZiNzJhZGExZWQyYzkxOTIwMjUwMjA0MTEwMDU4",  # Base64 encoded
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": amount,
        "PartyA": phone_number,
        "PartyB": "174379",
        "PhoneNumber": phone_number,
        "CallBackURL": "http://127.0.0.1:8000/mpesa/callback",
        "AccountReference": "Test",
        "TransactionDesc": "Payment"
    }

    print(f"Request Headers: {headers}")
    print(f"Request Payload: {payload}")
    
    response = requests.post(url, json=payload, headers=headers)
    
    print(f"Response Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")

    if response.status_code == 200:
        print("Payment initiated successfully!")
        return response.json()
    else:
        print(f"Failed to initiate STK Push, Status Code: {response.status_code}, Response: {response.text}")
        raise Exception(f"Error initiating payment: {response.status_code} - {response.text}")