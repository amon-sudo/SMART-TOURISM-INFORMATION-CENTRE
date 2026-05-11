import base64
import json
import hmac
import uuid
from datetime import datetime, timezone


from flask import current_app

def secret_key():
    return current_app.config['SECRET_KEY']

def expiry_time():
    expiration_seconds = current_app.config.get('TOKEN_EXPIRATION_SECONDS', 3600)
                                                
    return datetime.utcnow(timezone.utc).timestamp() + expiration_seconds

def _b64url_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')  

def _b64url_decode(data):
    padding = '=' * (-len(data) % 4)  
    return base64.urlsafe_b64decode(data + padding)

def sign(message):
    raw = hmac.new(secret_key().encode(), message.encode(), digestmod='sha256').digest()
    return _b64url_encode(raw)

def generate_token(user_id):
    header = json.dumps({"alg": "HS256", "typ": "JWT"})
    payload = json.dumps({
        "user_id": user_id,
        "exp": expiry_time(),
        "jti": str(uuid.uuid4())
    })
    token = f"{_b64url_encode(header.encode())}.{_b64url_encode(payload.encode())}"
    signature = sign(token)
    return f"{token}.{signature}"

def decode_token(token):
    try:
        header_b64, payload_b64, signature = token.split('.')
        expected_signature = sign(f"{header_b64}.{payload_b64}")
        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("Invalid token signature")
        payload_json = _b64url_decode(payload_b64).decode('utf-8')
        payload = json.loads(payload_json)
        if payload.get('exp', 0) < datetime.utcnow(timezone.utc).timestamp():
            raise ValueError("Token has expired")
        return payload
    except Exception as error:
        raise ValueError("Invalid token") from error
    