import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone

import jwt


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

JWT_ALGORITHM = "HS256"

JWT_SECRET_KEY = os.getenv(
    "JWT_SECRET_KEY",
    "change-this-secret-key-before-deployment",
)

ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24


# ---------------------------------------------------------
# Password hashing
# ---------------------------------------------------------

def hash_password(password: str) -> str:
    """
    Securely hash a password using PBKDF2-HMAC-SHA256.
    """

    salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        310_000,
    )

    return (
        f"pbkdf2_sha256$310000$"
        f"{salt.hex()}$"
        f"{password_hash.hex()}"
    )


def verify_password(
    plain_password: str,
    stored_hash: str,
) -> bool:
    """
    Verify a password against its stored hash.
    """

    try:
        algorithm, iterations, salt_hex, hash_hex = (
            stored_hash.split("$")
        )

        if algorithm != "pbkdf2_sha256":
            return False

        salt = bytes.fromhex(salt_hex)
        expected_hash = bytes.fromhex(hash_hex)

        calculated_hash = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt,
            int(iterations),
        )

        return hmac.compare_digest(
            calculated_hash,
            expected_hash,
        )

    except (ValueError, TypeError):
        return False


# ---------------------------------------------------------
# JWT access tokens
# ---------------------------------------------------------

def create_access_token(
    user_id: int,
    role: str,
    authority_id: int | None = None,
) -> str:
    """
    Create a JWT access token containing the user's
    identity and authorization information.
    """

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "role": role,
        "authority_id": authority_id,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM,
    )


def decode_access_token(token: str) -> dict:
    """
    Decode and validate a JWT access token.
    """

    return jwt.decode(
        token,
        JWT_SECRET_KEY,
        algorithms=[JWT_ALGORITHM],
    )