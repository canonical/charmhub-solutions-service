import hmac
import hashlib
import time
import os
from functools import wraps
from flask import request, abort, g
import jwt

HMAC_SECRET_KEY = os.environ.get("HMAC_SECRET_KEY")
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY")


TOKEN_EXPIRATION = 300  # 5 minutes


def verify_signature(username, timestamp, signature):
    try:
        message = f"{username}|{timestamp}".encode()
        expected = hmac.new(HMAC_SECRET_KEY.encode(), message, hashlib.sha256).hexdigest()

        if not hmac.compare_digest(expected, signature):
            return False

        if abs(time.time() - int(timestamp)) > TOKEN_EXPIRATION:
            return False

        return True
    except Exception:
        return False

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            abort(401, description="Missing or invalid Authorization header")

        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            g.user = {
                "username": payload["sub"],
                "teams": payload.get("teams", [])
            }

        except jwt.ExpiredSignatureError:
            abort(401, description="Token expired")
        except jwt.InvalidTokenError:
            abort(401, description="Invalid token")

        return f(*args, **kwargs)
    return decorated_function

