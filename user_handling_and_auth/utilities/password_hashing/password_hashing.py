import os 

import hashlib
import hmac

def hash_password(plain:str):

    salt = os.urandom(16)  # Generate a random salt
    hashed_password = hashlib.pbkdf2_hmac(
        hash_name='sha256',  # Use SHA-256 as the hashing algorithm
        password=plain.encode('utf-8'),  # Convert the password to bytes
        salt=salt,  # Use the generated salt
        iterations=100000  # Number of iterations for key stretching
    )

    return f"(salt:{salt.hex()}|hash:{hashed_password.hex()})"

def verify_password(plain:str, hashed:str):

    try:
        # Extract the salt and hash from the stored value
        salt_hex, hash_hex = hashed.split('|')
        salt = bytes.fromhex(salt_hex.split(':')[1])
        stored_hash = bytes.fromhex(hash_hex.split(':')[1])

        # Hash the provided password using the same salt and parameters
        new_hash = hashlib.pbkdf2_hmac(
            hash_name='sha256',
            password=plain.encode('utf-8'),
            salt=salt,
            iterations=100000
        )

        # Use hmac.compare_digest for a secure comparison
        return hmac.compare_digest(new_hash, stored_hash)
    except Exception as e:
        # Handle any exceptions that may occur during parsing or hashing
        print(f"Error verifying password: {e}")
        return False