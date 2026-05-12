from functools import wraps
from flask import request, jsonify
import jwt
import os

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        
        try:
            if token.startswith("Bearer "):
                token = token.split(" ")[1]
            data = jwt.decode(token, os.getenv('SECRET_KEY', 'dev-secret'), algorithms=["HS256"])
            
            # Extract user info and roles
            current_user_id = data.get('user_id')
            user_roles = data.get('roles', [])
            user_permissions = data.get('permissions', [])

            # Example: Ensure user is not banned or has basic access
            if not current_user_id:
                raise Exception("Invalid token data")
                
        except Exception as e:
            return jsonify({'message': 'Token is invalid!', 'error': str(e)}), 401
        
        return f(current_user_id, *args, **kwargs)
    
    return decorated
