import hmac
import hashlib
import time
import os
from functools import wraps
from flask import request, abort, g
import jwt
import logging

from app.public.launchpad import get_user_teams

logger = logging.getLogger(__name__)

HMAC_SECRET_KEY = os.environ.get("FLASK_HMAC_SECRET_KEY")
SECRET_KEY = os.environ.get("FLASK_SECRET_KEY")


TOKEN_EXPIRATION = 300  # 5 minutes


def verify_signature(username, timestamp, signature):
    """Verify the HMAC signature and timestamp."""
    try:
        message = f"{username}|{timestamp}".encode()
        expected = hmac.new(
            HMAC_SECRET_KEY.encode(), message, hashlib.blake2b
        ).hexdigest()

        if not hmac.compare_digest(expected, signature):
            return False

        if abs(time.time() - int(timestamp)) > TOKEN_EXPIRATION:
            return False

        return True
    except Exception as e:
        logger.error(f"Error verifying signature: {e}")
        return False


def decode_jwt_token(token):
    """Decode and validate the JWT token."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        abort(401, description="Token expired")
    except jwt.InvalidTokenError:
        abort(401, description="Invalid token")


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            abort(401, description="Missing or invalid Authorization header")

        token = auth_header.split(" ")[1]
        payload = decode_jwt_token(token)
        teams = get_user_teams(payload["sub"])

        g.user = {
            "username": payload["sub"],
            "teams": teams,
        }

        return f(*args, **kwargs)

    return decorated_function
