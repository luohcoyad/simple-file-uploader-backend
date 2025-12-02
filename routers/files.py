from datetime import datetime, timezone
from enum import IntEnum
from pathlib import Path
from typing import Optional
from urllib.parse import quote
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

import models
import schemas
import storage
from config import settings
from database import get_db
from dependencies import get_current_user

router = APIRouter(prefix="/files", tags=["files"])


class StorageAccessExpireTime(IntEnum):
    FILE = 60 * 60 * 12
    THUMBNAIL = 60 * 60


@router.post("/upload", response_model=schemas.FileOut, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    stored_name, thumbnail_name = storage.save_upload_file(
        file,
        Path(current_user.id.hex),
    )
    if not file.size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Empty file",
        )

    if file.size > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File too large; max 50MB",
        )

    asset = models.FileAsset(
        display_name=file.filename,
        stored_name=stored_name,
        thumbnail_name=thumbnail_name,
        content_type=file.content_type,
        size=file.size,
        owner_id=current_user.id,
    )
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@router.get("", response_model=schemas.FileListResponse)
def list_files(
    limit: int = Query(default=10, le=100),
    offset: int = Query(default=0, ge=0),
    sort: Optional[str] = Query(default="desc", regex="^(asc|desc)$"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = db.query(models.FileAsset).filter(models.FileAsset.owner_id == current_user.id)
    total = query.count()
    order = (
        models.FileAsset.created_at.asc() if sort == "asc" else models.FileAsset.created_at.desc()
    )
    items = query.order_by(order).offset(offset).limit(limit).all()
    return schemas.FileListResponse(
        total=total, items=[schemas.FileOut.model_validate(item) for item in items]
    )


@router.get("/{file_id}", response_model=schemas.FileOut)
def get_file(
    file_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    asset = (
        db.query(models.FileAsset)
        .filter(models.FileAsset.owner_id == current_user.id, models.FileAsset.id == file_id)
        .first()
    )
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    return asset


@router.put("/{file_id}", response_model=schemas.FileOut)
def update_file(
    file_id: UUID,
    payload: schemas.FileUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    asset = (
        db.query(models.FileAsset)
        .filter(models.FileAsset.owner_id == current_user.id, models.FileAsset.id == file_id)
        .first()
    )
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    asset.display_name = payload.display_name
    asset.updated_at = datetime.now(timezone.utc)
    db.add(asset)
    db.commit()
    db.refresh(asset)
    return asset


@router.delete("/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_file(
    file_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    asset: Optional[models.FileAsset] = (
        db.query(models.FileAsset)
        .filter(models.FileAsset.owner_id == current_user.id, models.FileAsset.id == file_id)
        .first()
    )
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    storage.delete_file(Path(current_user.id.hex), asset.stored_name, asset.thumbnail_name)
    db.delete(asset)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{file_id}/download")
def download_file(
    file_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    asset: Optional[models.FileAsset] = (
        db.query(models.FileAsset)
        .filter(models.FileAsset.owner_id == current_user.id, models.FileAsset.id == file_id)
        .first()
    )
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    signed_url = storage.get_signed_url(
        Path(current_user.id.hex),
        asset.stored_name,
        thumbnail=False,
        expires_in=StorageAccessExpireTime.FILE.value,
    )

    return JSONResponse(
        content={"url": signed_url, "filename": quote(asset.display_name)},
        headers={
            "Cache-Control": f"public, max-age={StorageAccessExpireTime.FILE.value}",
        },
    )


@router.get("/{file_id}/thumbnail")
def get_thumbnail(
    file_id: UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    asset: Optional[models.FileAsset] = (
        db.query(models.FileAsset)
        .filter(models.FileAsset.owner_id == current_user.id, models.FileAsset.id == file_id)
        .first()
    )
    if not asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found")
    if not asset.thumbnail_name:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Thumbnail not available")
    signed_url = storage.get_signed_url(
        Path(current_user.id.hex),
        asset.thumbnail_name,
        thumbnail=True,
        expires_in=StorageAccessExpireTime.THUMBNAIL.value,
    )
    return JSONResponse(
        content={"url": signed_url},
        headers={"Cache-Control": f"public, max-age={StorageAccessExpireTime.THUMBNAIL.value}"},
    )
