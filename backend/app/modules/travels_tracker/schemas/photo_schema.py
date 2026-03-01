from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional
from ..enums.photo_status import PhotoStatus


class PhotoUploadRequest(BaseModel):
    filename:     str
    content_type: str


class PhotoUploadResponse(BaseModel):
    photo_id:   int
    upload_url: str
    r2_key:     str
    expires_in: int


class PhotoConfirmRequest(BaseModel):
    size_bytes: int
    width:      Optional[int]      = None
    height:     Optional[int]      = None
    taken_at:   Optional[datetime] = None


class PhotoUpdate(BaseModel):
    caption:     Optional[str]  = None
    position:    Optional[int]  = None
    is_favorite: Optional[bool] = None


class PhotoReorderItem(BaseModel):
    photo_id: int
    position: int


class PhotoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:           int
    album_id:     int
    trip_id:      int
    user_id:      int
    filename:     str
    public_url:   Optional[str]
    content_type: Optional[str]
    size_bytes:   Optional[int]
    width:        Optional[int]
    height:       Optional[int]
    caption:      Optional[str]
    taken_at:     Optional[datetime]
    position:     int
    status:       PhotoStatus
    is_favorite:  bool
    created_at:   datetime
    updated_at:   Optional[datetime]