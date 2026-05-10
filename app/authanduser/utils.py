import jwt
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app

def hash_password(password: str) -> str:
    return generate_password_hash(password)

def verify_password(hash: str, password: str) -> bool:
    return check_password_hash(hash, password)

def generate_jwt(user_id: str, expires_minutes: int = 30) -> str:
    secret = current_app.config.get("SECRET_KEY")
    payload = {
        "user_id": str(user_id),
        "exp": datetime.datetime.utcnow() + datetime.timedelta(minutes=expires_minutes)
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    # PyJWT may return bytes in some versions; ensure a str is returned
    if isinstance(token, bytes):
        token = token.decode("utf-8")
    return token

def decode_jwt(token: str) -> dict:
    secret = current_app.config.get("SECRET_KEY")
    return jwt.decode(token, secret, algorithms=["HS256"])
