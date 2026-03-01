from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from ..enums.photo_status import PhotoStatus


class Photo(Base):
    __tablename__ = "photos"
    __table_args__ = {"schema": "travels_tracker"}

    id           = Column(Integer, primary_key=True)
    album_id     = Column(Integer, ForeignKey("travels_tracker.albums.id", ondelete="CASCADE"), nullable=False, index=True)
    trip_id      = Column(Integer, ForeignKey("travels_tracker.trips.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id      = Column(Integer, ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename     = Column(String(255), nullable=False)
    r2_key       = Column(String(500), nullable=False)
    public_url   = Column(String(1000), nullable=True)
    content_type = Column(String(50), nullable=True)
    size_bytes   = Column(Integer, nullable=True)
    width        = Column(Integer, nullable=True)
    height       = Column(Integer, nullable=True)
    caption      = Column(String(500), nullable=True)
    taken_at     = Column(DateTime(timezone=True), nullable=True)
    position     = Column(Integer, nullable=False, default=0)
    status       = Column(
        SAEnum(PhotoStatus, name="photostatus", schema="travels_tracker"),
        nullable=False,
        default=PhotoStatus.pending,
    )
    is_favorite  = Column(Boolean, nullable=False, default=False)
    created_at   = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at   = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    album = relationship("Album", back_populates="photos")
    trip  = relationship("Trip", back_populates="photos")