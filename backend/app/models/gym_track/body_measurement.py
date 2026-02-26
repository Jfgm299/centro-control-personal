from sqlalchemy import Integer, Text, Column, Float, DateTime
from sqlalchemy.sql import func
from ...core.database import Base

class BodyMeasurement(Base):
    __tablename__ = 'body_measurements'

    id = Column(Integer, primary_key=True, index=True)
    weight_kg = Column(Float, nullable=False)
    body_fat_percentage = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())