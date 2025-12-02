import uuid
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple

from fastapi import HTTPException, UploadFile, status
from PIL import Image

from config import settings
from vendor.supabase_client import get_supabase_client


def _build_object_path(storage_dir: Path, stored_name: str) -> str:
    """Build the Supabase object key using the configured prefix (storage_dir)."""
    prefix = storage_dir.as_posix().strip("/")
    return f"{prefix}/{stored_name}" if prefix else stored_name


def _upload_to_bucket(bucket: str, object_path: str, data: bytes, content_type: str) -> None:
    supabase = get_supabase_client()
    response = supabase.storage.from_(bucket).upload(
        object_path,
        data,
        file_options={"content-type": content_type},
    )
    if getattr(response, "error", None):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to upload file to storage",
        )


def _generate_thumbnail(data: bytes) -> Optional[bytes]:
    with Image.open(BytesIO(data)) as image:
        if image.width == 0 or image.height == 0:
            return None
        ratio = 64 / float(image.width)
        new_height = max(1, int(image.height * ratio))
        thumb = image.copy()
        thumb.thumbnail((64, new_height))
        buf = BytesIO()
        thumb.save(buf, format="PNG")
        return buf.getvalue()


def save_upload_file(upload: UploadFile, storage_dir: Path) -> Tuple[str, Optional[str]]:
    """Upload file to Supabase Storage; returns (stored_name, size, thumbnail_name)."""
    stored_name = f"{uuid.uuid4().hex}_{upload.filename}"
    object_path = _build_object_path(storage_dir, stored_name)

    data = upload.file.read()

    _upload_to_bucket(
        settings.supabase_bucket,
        object_path,
        data,
        upload.content_type or "application/octet-stream",
    )

    thumbnail_name = None
    if upload.content_type and upload.content_type.startswith("image/"):
        thumb_data = _generate_thumbnail(data)
        if thumb_data:
            thumbnail_name = f"{stored_name}.png"
            thumb_path = _build_object_path(storage_dir, thumbnail_name)
            try:
                _upload_to_bucket(
                    settings.supabase_thumbnail_bucket,
                    thumb_path,
                    thumb_data,
                    "image/png",
                )
            except HTTPException:
                thumbnail_name = None

    return stored_name, thumbnail_name


def delete_file(storage_dir: Path, stored_name: str, thumbnail_name: Optional[str] = None) -> None:
    supabase = get_supabase_client()
    object_path = _build_object_path(storage_dir, stored_name)
    response = supabase.storage.from_(settings.supabase_bucket).remove([object_path])
    if getattr(response, "error", None):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete file from storage",
        )
    if thumbnail_name:
        thumb_path = _build_object_path(storage_dir, thumbnail_name)
        supabase.storage.from_(settings.supabase_thumbnail_bucket).remove([thumb_path])


def get_signed_url(
    storage_dir: Path, stored_name: str, *, thumbnail: bool = False, expires_in: int = 3600
) -> str:
    supabase = get_supabase_client()
    bucket = settings.supabase_thumbnail_bucket if thumbnail else settings.supabase_bucket
    object_path = _build_object_path(storage_dir, stored_name)
    response = supabase.storage.from_(bucket).create_signed_url(object_path, expires_in=expires_in)
    if getattr(response, "error", None):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thumbnail not found in storage" if thumbnail else "File not found in storage",
        )

    url = response.get("signedUrl")

    if not url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate signed URL",
        )
    return url
