from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class DBModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserBase(BaseModel):
    email: EmailStr = Field(max_length=254)


class UserCreate(UserBase):
    password: str = Field(min_length=8)


class UserOut(UserBase, DBModel):
    id: UUID
    created_at: datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    sub: Optional[str] = None
    exp: Optional[datetime] = None
    jti: Optional[str] = None
    user_id: Optional[UUID] = None


class FileBase(BaseModel):
    display_name: str = Field(max_length=500)


class FileUpdate(FileBase):
    pass


class FileOut(FileBase, DBModel):
    id: UUID
    stored_name: str = Field(max_length=537)
    thumbnail_name: Optional[str] = Field(default=None, max_length=600)
    size: int
    content_type: Optional[str] = Field(max_length=16)
    created_at: datetime
    updated_at: datetime


class FileListResponse(BaseModel):
    total: int
    items: List[FileOut]
