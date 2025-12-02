from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from database import get_db

router = APIRouter(tags=["health"])


@router.get("/live", summary="Liveness probe")
def live_check():
    return {"status": "ok"}


@router.get("/healthz", summary="Readiness probe")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database_unavailable",
        ) from exc
    return {"status": "ok"}
