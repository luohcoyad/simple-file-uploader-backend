from typing import Optional

from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

import models
import security
from database import get_db
from schemas import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


def _unauthorized(code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={"code": code, "message": message},
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    token: str = Depends(oauth2_scheme),
    access_token_cookie: Optional[str] = Cookie(default=None, alias="access_token"),
    db: Session = Depends(get_db),
) -> models.User:
    if not token or not access_token_cookie:
        raise _unauthorized("missing_token", "No access token provided")
    if token != access_token_cookie:
        raise _unauthorized("token_mismatch", "Header and cookie tokens must match")

    token_data: TokenData = security.decode_access_token(token)
    if not token_data.sub or not token_data.jti or not token_data.user_id:
        raise _unauthorized("invalid_token_claims", "Token is invalid or missing claims")
    session = (
        db.query(models.UserSession)
        .filter(
            models.UserSession.user_id == token_data.user_id,
            models.UserSession.jti == token_data.jti,
        )
        .first()
    )
    if session is None:
        raise _unauthorized("session_not_found", "Session not found for token")
    if session.deleted_at is not None:
        raise _unauthorized("session_revoked", "Session has been revoked")
    user = db.get(models.User, token_data.user_id)
    if user is None:
        raise _unauthorized("user_not_found", "User not found")
    return user
