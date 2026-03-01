from sqlalchemy import Column, Integer, String, Text, Float, Date, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from ..enums.activity_category import ActivityCategory


class Activity(Base):
    __tablename__ = "activities"
    __table_args__ = {"schema": "travels_tracker"}

    id          = Column(Integer, primary_key=True)
    trip_id     = Column(Integer, ForeignKey("travels_tracker.trips.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id     = Column(Integer, ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False, index=True)
    title       = Column(String(200), nullable=False)
    category    = Column(
        SAEnum(ActivityCategory, name="activitycategory", schema="travels_tracker"),
        nullable=True,
    )
    description = Column(Text, nullable=True)
    date        = Column(Date, nullable=True)
    lat         = Column(Float, nullable=True)
    lon         = Column(Float, nullable=True)
    rating      = Column(Integer, nullable=True)
    position    = Column(Integer, nullable=False, default=0)
    created_at  = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    trip = relationship("Trip", back_populates="activities")