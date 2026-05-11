revoked = set()

def blacklist_token(jti):
    revoked.add(jti)

def is_token_blacklisted(jti):
    return jti in revoked