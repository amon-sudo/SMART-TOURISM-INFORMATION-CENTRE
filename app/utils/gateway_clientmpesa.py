import requests
import base64
import datetime
import os

DARAJA_BASE_URL = "https://sandbox.safaricom.co.ke"
CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET")
PASSKEY = os.getenv("MPESA_PASSKEY")
SHORTCODE = os.getenv("MPESA_SHORTCODE")
CALLBACK_URL = os.getenv("MPESA_CALLBACK_URL")

# Validate env vars helper
def _validate_mpesa_config():
    if not all([CONSUMER_KEY, CONSUMER_SECRET, PASSKEY, SHORTCODE, CALLBACK_URL]):
        raise RuntimeError("Missing required M-Pesa environment variables in .env")

def get_access_token():
    _validate_mpesa_config()
    response = requests.get(
        f"{DARAJA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials",
        auth=(CONSUMER_KEY, CONSUMER_SECRET),
        timeout=10
    )
    if response.status_code != 200:
        raise Exception(f"Failed to get access token: {response.text}")
    return response.json().get("access_token")

def stk_push(phone_number, amount, reference):
    token = get_access_token()
    if not token:
        raise Exception("Access token is None")

    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    password = base64.b64encode((SHORTCODE + PASSKEY + timestamp).encode()).decode()

    payload = {
        "BusinessShortCode": SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": str(amount),
        "PartyA": phone_number,
        "PartyB": SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": CALLBACK_URL,
        "AccountReference": reference,
        "TransactionDesc": "Tourism Payment"
    }

    headers = {"Authorization": f"Bearer {token}"}
    response = requests.post(
        f"{DARAJA_BASE_URL}/mpesa/stkpush/v1/processrequest",
        json=payload,
        headers=headers,
        timeout=10
    )
    if response.status_code != 200:
        raise Exception(f"STK Push failed: {response.text}")
    return response.json()
