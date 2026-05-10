import re

email_regex = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

def validate_email(email):
    if not email:
        return False, "Email is required."
    if not isinstance(email, str):
        return False, "Email must be a string."
    if not email_regex.match(email):
        return False, "Invalid email format."
    return True, ""

def validate_password(password):
    if not password:
        return False, "Password is required."
    if not isinstance(password, str):
        return False, "Password must be a string."
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    return True, ""

def validate_username(username):
    if not username:
        return False, "Username is required."
    if not isinstance(username, str):
        return False, "Username must be a string."
    if len(username) < 3 or len(username) > 30:
        return False, "Username must be between 3 and 30 characters long."
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, "Username can only contain letters, numbers, and underscores."
    return True, "" 

def validate_user_registration(data):
    email_valid, email_msg = validate_email(data.get('email'))
    if not email_valid:
        return False, email_msg

    password_valid, password_msg = validate_password(data.get('password'))
    if not password_valid:
        return False, password_msg

    username_valid, username_msg = validate_username(data.get('username'))
    if not username_valid:
        return False, username_msg

    return True, ""     

def validate_user_login(data):
    username = data.get('username')
    email = data.get('email')
    if not username and not email:
        return False, "Either username or email is required."

    if email:
        email_valid, email_msg = validate_email(email)
        if not email_valid:
            return False, email_msg

    if username:
        username_valid, username_msg = validate_username(username)
        if not username_valid:
            return False, username_msg

    password_valid, password_msg = validate_password(data.get('password'))
    if not password_valid:
        return False, password_msg

    return True, ""

def validate_user_update(data):
    if 'email' in data:
        email_valid, email_msg = validate_email(data.get('email'))
        if not email_valid:
            return False, email_msg

    if 'password' in data:
        password_valid, password_msg = validate_password(data.get('password'))
        if not password_valid:
            return False, password_msg

    if 'username' in data:
        username_valid, username_msg = validate_username(data.get('username'))
        if not username_valid:
            return False, username_msg

    return True, ""

def validate_user_deletion(data):
    if 'user_id' not in data:
        return False, "User ID is required for deletion."
    if not isinstance(data['user_id'], int):
        return False, "User ID must be an integer."
    if data['user_id'] <= 0:
        return False, "User ID must be greater than zero."
    return True, ""


def validate_user_retrieval(data):
    if 'user_id' not in data:
        return False, "User ID is required for retrieval."
    if not isinstance(data['user_id'], int):
        return False, "User ID must be an integer."
    if data['user_id'] <= 0:
        return False, "User ID must be greater than zero."
    return True, ""


def validate_user_roles(data):
    if 'user_id' not in data:
        return False, "User ID is required to retrieve roles."
    if not isinstance(data['user_id'], int):
        return False, "User ID must be an integer."
    if data['user_id'] <= 0:
        return False, "User ID must be greater than zero."
    return True, ""
    
    

