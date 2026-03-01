from sqlalchemy import Column, Integer, String, Float, Date, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Trip(Base):
    __tablename__ = "trips"
    __table_args__ = {"schema": "travels_tracker"}

    id              = Column(Integer, primary_key=True)
    user_id         = Column(Integer, ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False, index=True)
    title           = Column(String(200), nullable=False)
    destination     = Column(String(200), nullable=False)
    country_code    = Column(String(3), nullable=True)
    lat             = Column(Float, nullable=True)
    lon             = Column(Float, nullable=True)
    start_date      = Column(Date, nullable=True)
    end_date        = Column(Date, nullable=True)
    description     = Column(Text, nullable=True)
    cover_photo_key = Column(String(500), nullable=True)
    cover_photo_url = Column(String(1000), nullable=True)
    created_at      = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Relationships
    user       = relationship("User", back_populates="trips")
    albums     = relationship("Album", back_populates="trip", cascade="all, delete-orphan")
    activities = relationship("Activity", back_populates="trip", cascade="all, delete-orphan")
    photos     = relationship("Photo", back_populates="trip", cascade="all, delete-orphan")