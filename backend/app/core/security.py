import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any
from uuid import uuid4

import jwt
from cryptography.fernet import Fernet
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

from .config import settings
from .exceptions import UnauthorizedException

# Configure hashing with recommended settings
hashing_context = PasswordHash.recommended()

# Initialize data encryption
fernet_cipher = Fernet(settings.encryption_key.encode("utf-8"))

# Bearer Auth token extractor; missing header handled below so it raises our exception
token_auth_scheme = HTTPBearer(auto_error=False)

# Constants
TOKEN_ISSUER = settings.token_issuer
TOKEN_AUDIENCE = settings.token_audience


# --------------- Hash ---------------
def create_hardened_hash(entity: str):
    """Hash plaintext entity using Argon2id"""
    return hashing_context.hash(entity)


def verify_hardened_hash(entity: str, hashed_entity: str):
    """
    Verify plaintext entity against Argon2id hash;
    a malformed stored hash counts as a mismatch, not a server error
    """
    try:
        return hashing_context.verify(entity, hashed_entity)
    except UnknownHashError:
        return False


def verify_and_update_hardened_hash(entity: str, hashed_entity: str):
    """
    Verify the hash and return an updated hash if cost parameters changed;
    a malformed stored hash counts as a mismatch, not a server error
    """
    try:
        return hashing_context.verify_and_update(entity, hashed_entity)
    except UnknownHashError:
        return False, None


def create_fast_hash(entity: str):
    """
    Generate deterministic SHA-256 hex digest;
    Only for high-entropy values
    """
    return hashlib.sha256(entity.encode("utf-8")).hexdigest()


def verify_fast_hash(entity: str, hashed_entity: str):
    """Verify plaintext entity against a SHA-256 hash"""
    calculated_hash = create_fast_hash(entity=entity)
    return secrets.compare_digest(calculated_hash, hashed_entity)


# --------------- Encryption ---------------
def encrypt_entity(entity: str):
    """Two-Way Symmetric Encryption for secrets stored at rest"""
    return fernet_cipher.encrypt(entity.encode("utf-8")).decode("utf-8")


def decrypt_entity(entity: str):
    """Decrypt a Fernet ciphertext string back into plaintext"""
    return fernet_cipher.decrypt(entity.encode("utf-8")).decode("utf-8")


# --------------- Token ---------------
def _create_token(
    sub: str,
    token_type: str,
    expires_in: int,
    fingerprint: str,
    family_id: str | None = None,
    additional_claims: dict[str, Any] | None = None,
):
    """Create a signed JWT; reserved claims always override additional claims"""
    now = datetime.now(UTC)
    key_id, jwt_secret_key = list(settings.jwt_signing_keys.items())[-1]

    payload = {
        "sub": sub,  # Subject
        "iat": now,  # IssuedAt
        "nbf": now,  # Not Before; Invalid before time
        "exp": now + timedelta(seconds=expires_in),  # Expiration
        "iss": TOKEN_ISSUER,  # Issuer
        "aud": TOKEN_AUDIENCE,  # Audience
        "jti": str(uuid4()),  # JWT ID; Unique identifier
        "fgp": fingerprint,  # Client device identifier
        "type": token_type,
        **({"fid": family_id} if family_id else {}),  # Token family identifier
        **(additional_claims or {}),
    }

    headers = {
        "kid": key_id,  # Key identifier that encoded the token
    }

    return jwt.encode(
        payload=payload,
        key=jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        headers=headers,
    )


def _decode_token(token: str, expected_type: str):
    """
    Decode and validate a JWT, returning its payload
    """
    kid = jwt.get_unverified_header(token).get("kid")
    jwt_secret_key = settings.jwt_signing_keys.get(kid) if kid else None

    if jwt_secret_key is None:
        raise InvalidTokenError("Invalid or missing Key ID (kid)")

    payload = jwt.decode(
        token,
        key=jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
        audience=TOKEN_AUDIENCE,
        issuer=TOKEN_ISSUER,
        leeway=settings.jwt_leeway_seconds,  # exp and iat claim will have room of 30s; clock skew
        options={
            "require": [
                "exp",
                "iat",
                "sub",
                "jti",
                "type",
                "aud",
                "nbf",
                "fgp",
            ]
        },
    )

    if payload["type"] != expected_type:
        raise InvalidTokenError("Invalid token type")

    return payload


# --------------- Access Token ---------------
def create_access_token(
    sub: str,
    fingerprint: str,
    additional_claims: dict[str, Any] | None = None,
):
    """Create a signed JWT Access token"""
    return _create_token(
        sub=sub,
        fingerprint=fingerprint,
        token_type="access",
        expires_in=settings.access_token_expires_in,
        additional_claims=additional_claims,
    )


def decode_access_token(access_token: str):
    """
    Decode and validate a JWT access token;
    returns only the user id (`sub`), all a route needs
    """
    return str(_decode_token(access_token, "access")["sub"])


# --------------- Refresh Token ---------------
def create_refresh_token(
    sub: str,
    fingerprint: str,
    family_id: str,
    additional_claims: dict[str, Any] | None = None,
):
    """Create a signed JWT Refresh token"""
    return _create_token(
        sub=sub,
        token_type="refresh",
        expires_in=settings.refresh_token_expires_in,
        fingerprint=fingerprint,
        family_id=family_id,
        additional_claims=additional_claims,
    )


def decode_refresh_token(refresh_token: str):
    """
    Decode and validate a JWT refresh token;
    returns the full payload: `jti`/`exp` are needed for rotation and revocation
    """
    return _decode_token(refresh_token, "refresh")


# --------------- FastAPI Dependency ---------------
async def get_current_user_id(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(token_auth_scheme)
    ],
):
    """FastAPI route dependency to parse Bearer authorization header"""
    if credentials is None:
        raise UnauthorizedException("Not authenticated")

    try:
        return decode_access_token(credentials.credentials)

    except ExpiredSignatureError:
        raise UnauthorizedException("Token has expired") from None

    except InvalidTokenError:
        raise UnauthorizedException("Could not validate credentials") from None
