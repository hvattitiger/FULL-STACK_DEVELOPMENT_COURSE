"""
Security utilities: password hashing, JWT token creation and verification.
Follows Single Responsibility Principle - handles only auth token logic.

Password hashing strategy — bcrypt + SHA-256 pre-hash:
───────────────────────────────────────────────────────
bcrypt has a hard 72-byte input limit. In bcrypt 4.x this became a strict
error instead of silent truncation. To safely support passwords of any
length we first SHA-256 hash the plaintext (always 32 bytes / 64 hex chars),
then bcrypt-hash the result. This is a well-known pattern (used by Django,
Authlib, etc.) and does not weaken security — SHA-256 output is uniformly
distributed and bcrypt still provides the salt + work-factor protection.

Important: existing password hashes (created without pre-hashing) will
NOT verify with the new approach. If migrating an existing database, run a
one-time re-hash on next login using the legacy path before switching fully.
"""
import hashlib
import base64
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
import bcrypt

# bcrypt password hashing context
_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def _prehash_password(plain_password: str) -> str:
    """
    SHA-256 pre-hash a plaintext password to work around bcrypt's 72-byte limit.

    Steps:
      1. UTF-8 encode the password.
      2. SHA-256 digest → always 32 bytes.
      3. Base64-encode → always 44 ASCII chars (well within bcrypt's 72-byte limit).

    Returns a base64 string that is safe to pass directly to bcrypt.
    """
    password_bytes = plain_password.encode("utf-8")
    sha256_digest = hashlib.sha256(password_bytes).digest()   # 32 bytes
    return base64.b64encode(sha256_digest).decode("ascii")    # 44 ASCII chars


# def hash_password(plain_password: str) -> str:
#     """
#     Hash a plaintext password for secure storage.

#     Applies SHA-256 pre-hashing before bcrypt to support passwords of any
#     length without hitting bcrypt's 72-byte hard limit (enforced in bcrypt 4.x).
#     """
#     return _pwd_context.hash(_prehash_password(plain_password))


# def verify_password(plain_password: str, hashed_password: str) -> bool:
#     """
#     Verify a plaintext password against a stored bcrypt hash.

#     Applies the same SHA-256 pre-hash used during hashing so the comparison
#     is consistent regardless of the original password length.
#     """
#     return _pwd_context.verify(_prehash_password(plain_password), hashed_password)
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed):
    if isinstance(hashed, str):
        hashed = hashed.encode()
    return bcrypt.checkpw(password.encode(), hashed)


def create_access_token(subject: str, extra_claims: Optional[dict] = None) -> str:
    """
    Create a signed JWT access token.

    Args:
        subject: Usually the user's ID or username.
        extra_claims: Additional payload fields (e.g. roles).

    Returns:
        Encoded JWT string.
    """
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": subject, "exp": expire}
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(subject: str, jti: Optional[str] = None) -> tuple[str, str]:
    """
    Create a signed JWT refresh token with a unique JTI (JWT ID).
    
    Returns:
        Tuple of (token, jti) where jti is the unique session identifier.
    """
    if jti is None:
        jti = str(uuid.uuid4())
    
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES
    )
    payload = {"sub": subject, "exp": expire, "type": "refresh", "jti": jti}
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return token, jti


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT access token.

    Returns:
        Decoded payload dict, or None if invalid/expired.
    """
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None


def decode_refresh_token(token: str) -> Optional[dict]:
    """
    Decode and validate a JWT refresh token.

    Returns:
        Decoded payload dict, or None if invalid/expired/wrong type.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        return None
    if payload.get("type") != "refresh":
        return None
    return payload