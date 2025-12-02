from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = Field("", alias="DATABASE_URL")
    jwt_secret_key: str = Field("", alias="JWT_SECRET_KEY")

    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(60 * 24, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    is_debug: bool = Field(False, alias="IS_DEBUG")

    supabase_url: str = Field("", alias="SUPABASE_URL")
    supabase_access_key: str = Field("", alias="SUPABASE_ACCESS_KEY")
    supabase_bucket: str = Field("uploads", alias="SUPABASE_BUCKET")
    supabase_thumbnail_bucket: str = Field("thumbnails", alias="SUPABASE_THUMBNAIL_BUCKET")

    max_upload_size_bytes: int = Field(50 * 1024 * 1024, alias="MAX_UPLOAD_SIZE_BYTES")

    allow_origins: List[str] = ["http://localhost:5173"]

    class Config:  # pylint: disable=too-few-public-methods
        env_file = ".env"


settings = Settings()  # type: ignore
