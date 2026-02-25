from sqlalchemy import Column, Integer, Float, String, Text, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ...database import Base
from ...enums import GymSetType

class Set(Base):
    __tablename__ = 'sets'

    id = Column(Integer, primary_key=True, index=True)
    exercise_id = Column(Integer, ForeignKey('exercises.id', ondelete='CASCADE'))
    set_number = Column(Integer, nullable=False)
    set_type = Column(Enum(GymSetType), nullable=False) # Cardio or Weight_reps
    rpe = Column(Integer, nullable=True) # Rate of perceived Exertion (1-10)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # ============= Fields for Cardio =====================

    speed_kmh = Column(Float, nullable=True)
    incline_percent = Column(Float, nullable=True)
    duration_seconds = Column(Integer, nullable=True)

    # ============ Fields for Weights_reps =================

    weight_kg = Column(Float, nullable=True)
    reps = Column(Integer, nullable=True)

    # =========== Relationships =============

    exercise = relationship('Exercise', back_populates='sets')


