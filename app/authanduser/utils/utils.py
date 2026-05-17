from werkzeug.security import generate_password_hash, check_password_hash
import jwt
import re
import datetime
from flask import current_app

def hash_password(password: str) -> str:
    return generate_password_hash(password)

def verify_password(hashed_password: str, password: str) -> bool:
    return check_password_hash(hashed_password, password)

def validate_password_strength(password: str) -> list[str]:
    """Return a list of validation error messages; empty list means OK.

    Policy (STORY011): min 8 chars, at least one uppercase, one digit,
    one special character.
    """
    errors: list[str] = []
    if not isinstance(password, str) or len(password) < 8:
        errors.append("Password must be at least 8 characters long")
    if not isinstance(password, str):
        return errors
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter")
    if not re.search(r"\d", password):
        errors.append("Password must contain at least one digit")
    if not re.search(r"[^A-Za-z0-9]", password):
        errors.append("Password must contain at least one special character")
    return errors

def encode_jwt(user_id: str) -> str:
    secret = current_app.config.get("SECRET_KEY")
    token = jwt.encode({"user_id": user_id, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)}, secret, algorithm="HS256")
    return token if isinstance(token, str) else token.decode("utf-8")

def decode_jwt(token: str) -> dict:
    secret = current_app.config.get("SECRET_KEY")
    return jwt.decode(token, secret, algorithms=["HS256"])
