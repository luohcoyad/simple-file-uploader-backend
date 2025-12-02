import base64
import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

import bcrypt
from jose import JWTError, jwt

import schemas
from config import settings


def _prehash_password(secret: str) -> bytes:
    """Hash to 32 bytes (sha256) then base64 encode so bcrypt sees a fixed-length input."""
    sha_digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.b64encode(sha_digest)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    candidate = _prehash_password(plain_password)
    return bcrypt.checkpw(candidate, hashed_password.encode("utf-8"))


def get_password_hash(password: str) -> str:
    prehashed = _prehash_password(password)
    hashed = bcrypt.hashpw(prehashed, bcrypt.gensalt())
    return hashed.decode("utf-8")


def create_access_token(
    subject: str, user_id: uuid.UUID, expires_delta: Optional[timedelta] = None
) -> str:
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.access_token_expire_minutes))
    to_encode = {
        "sub": subject,
        "uid": user_id.hex,
        "iat": now,
        "exp": expire,
        "jti": uuid.uuid4().hex,
    }
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        headers={"alg": settings.jwt_algorithm, "typ": "JWT"},
    )
    return encoded_jwt


def _payload_to_token_data(payload: dict) -> schemas.TokenData:
    uid_raw = payload.get("uid")
    try:
        uid_value = uuid.UUID(uid_raw) if uid_raw else None
    except (ValueError, TypeError):
        uid_value = None
    return schemas.TokenData(
        sub=payload.get("sub"),
        exp=payload.get("exp"),
        jti=payload.get("jti"),
        user_id=uid_value,
    )


def decode_access_token(token: str, allow_expired: bool = False) -> schemas.TokenData:
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
            options={"verify_exp": not allow_expired},
        )
        return _payload_to_token_data(payload)
    except JWTError:
        return schemas.TokenData(sub=None)
