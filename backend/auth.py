"""JWT authentication and role/ownership checks."""

import os
from datetime import datetime, timedelta, timezone
from functools import wraps

import jwt
from flask import g, jsonify, request

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
ALGORITHM = "HS256"
TOKEN_TTL = timedelta(hours=12)


def generate_token(user):
    payload = {
        "user_id": user["user_id"],
        "role": user["role"],
        "building_id": user["building_id"],
        "exp": datetime.now(timezone.utc) + TOKEN_TTL,
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def _unauthorized(message):
    return jsonify(error=message), 401


def token_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return _unauthorized("missing or malformed Authorization header")
        token = header.removeprefix("Bearer ").strip()
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        except jwt.ExpiredSignatureError:
            return _unauthorized("token expired")
        except jwt.InvalidTokenError:
            return _unauthorized("invalid token")
        g.current_user = payload
        return view(*args, **kwargs)

    return wrapped


def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if g.current_user["role"] not in roles:
                return jsonify(error="you do not have access to this resource"), 403
            return view(*args, **kwargs)

        return wrapped

    return decorator


def require_self_or_manager(user_id):
    """403s unless the current user IS user_id, or is a manager."""
    current = g.current_user
    if current["role"] == "manager" or current["user_id"] == user_id:
        return None
    return jsonify(error="you do not have access to this resource"), 403
