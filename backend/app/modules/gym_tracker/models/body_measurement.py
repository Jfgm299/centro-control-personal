from sqlalchemy import Integer, Text, Column, Float, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class BodyMeasurement(Base):
    __tablename__ = 'body_measurements'
    __table_args__ = {'schema':'gym_tracker', 'extend_existing': True}

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('core.users.id', ondelete='CASCADE'), nullable=False)
    weight_kg = Column(Float, nullable=False)
    body_fat_percent = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="body_measurements")