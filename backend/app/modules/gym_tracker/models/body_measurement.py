from sqlalchemy import Integer, Text, Column, Float, DateTime
from sqlalchemy.sql import func
from app.core.database import Base

class BodyMeasurement(Base):
    __tablename__ = 'body_measurements'
    __table_args__ = {'extend_existing': True}

    id = Column(Integer, primary_key=True)
    weight_kg = Column(Float, nullable=False)
    body_fat_percent = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())