from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class AlbumCreate(BaseModel):
    name:        str
    description: Optional[str] = None
    position:    int = 0


class AlbumUpdate(BaseModel):
    name:        Optional[str] = None
    description: Optional[str] = None
    position:    Optional[int] = None


class AlbumReorderItem(BaseModel):
    album_id: int
    position: int


class AlbumResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:              int
    trip_id:         int
    user_id:         int
    name:            str
    description:     Optional[str]
    cover_photo_url: Optional[str]
    position:        int
    created_at:      datetime
    updated_at:      Optional[datetime]