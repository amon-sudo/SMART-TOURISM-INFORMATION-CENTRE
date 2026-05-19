import requests
import base64
import datetime
import os

DARAJA_BASE_URL = "https://sandbox.safaricom.co.ke"
CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET")
PASSKEY = os.getenv("MPESA_PASSKEY", "bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f9e0f6a0c8b8f9f0f2c")
SHORTCODE = os.getenv("MPESA_SHORTCODE", "174379")
CALLBACK_URL = os.getenv("MPESA_CALLBACK_URL", "http://localhost:5000/api/payments/callback/mpesa")


def _require_credentials():
    if not all([CONSUMER_KEY, CONSUMER_SECRET]):
        raise RuntimeError("Missing required M-Pesa Consumer Key/Secret")

def get_access_token():
    _require_credentials()
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
