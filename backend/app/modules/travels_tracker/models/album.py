from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Album(Base):
    __tablename__ = "albums"
    __table_args__ = {"schema": "travels_tracker"}

    id              = Column(Integer, primary_key=True)
    trip_id         = Column(Integer, ForeignKey("travels_tracker.trips.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id         = Column(Integer, ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False, index=True)
    name            = Column(String(200), nullable=False)
    description     = Column(Text, nullable=True)
    cover_photo_key = Column(String(500), nullable=True)
    cover_photo_url = Column(String(1000), nullable=True)
    position        = Column(Integer, nullable=False, default=0)
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    trip   = relationship("Trip", back_populates="albums")
    photos = relationship("Photo", back_populates="album", cascade="all, delete-orphan")