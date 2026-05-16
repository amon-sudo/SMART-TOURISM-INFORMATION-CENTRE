from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import datetime
from flask import current_app

def hash_password(password: str) -> str:
    return generate_password_hash(password)

def verify_password(hashed_password: str, password: str) -> bool:
    return check_password_hash(hashed_password, password)

def encode_jwt(user_id: str) -> str:
    secret = current_app.config.get("SECRET_KEY")
    token = jwt.encode({"user_id": user_id, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)}, secret, algorithm="HS256")
    return token if isinstance(token, str) else token.decode("utf-8")

def decode_jwt(token: str) -> dict:
    secret = current_app.config.get("SECRET_KEY")
    return jwt.decode(token, secret, algorithms=["HS256"])
