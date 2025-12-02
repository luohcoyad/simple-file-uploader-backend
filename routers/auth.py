from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

import models
import schemas
import security
from config import settings
from database import get_db

router = APIRouter(prefix="/auth", tags=["auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


@router.post("/signup", response_model=schemas.UserOut, status_code=status.HTTP_201_CREATED)
def signup(payload: schemas.UserCreate, db: Session = Depends(get_db)):
    existing = db.query(models.User).filter(models.User.email == payload.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )
    hashed = security.get_password_hash(payload.password)
    user = models.User(email=payload.email, hashed_password=hashed)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=schemas.Token)
def login(
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user: Optional[models.User] = (
        db.query(models.User).filter(models.User.email == form_data.username).first()
    )

    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password"
        )
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    token = security.create_access_token(
        subject=user.email, user_id=user.id, expires_delta=access_token_expires
    )
    token_data = security.decode_access_token(token)
    if not token_data.jti:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create session",
        )
    session = models.UserSession(
        user_id=user.id,
        jti=token_data.jti,
        created_at=datetime.now(timezone.utc),
    )
    db.add(session)
    db.commit()
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=int(access_token_expires.total_seconds()),
    )
    return schemas.Token(access_token=token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    response: Response,
    token: str = Depends(oauth2_scheme),
    access_token_cookie: Optional[str] = Cookie(default=None, alias="access_token"),
    db: Session = Depends(get_db),
):
    token_value = token or access_token_cookie
    if not token_value:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    token_data = security.decode_access_token(token_value, allow_expired=True)
    if not token_data.sub or not token_data.jti or not token_data.user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    session: Optional[models.UserSession] = (
        db.query(models.UserSession)
        .filter(
            models.UserSession.jti == token_data.jti,
            models.UserSession.user_id == token_data.user_id,
        )
        .first()
    )
    if not session or session.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    session.deleted_at = datetime.now(timezone.utc)
    db.add(session)
    db.commit()
    response.delete_cookie(key="access_token")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
