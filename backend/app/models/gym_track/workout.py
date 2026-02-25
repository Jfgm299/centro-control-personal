from sqlalchemy import Column, Integer, Text, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ...database import Base

class Workout(Base):
    __tablename__ = 'workouts'

    id = Column(Integer, primary_key=True, index=True)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    total_exercises = Column(Integer, nullable=True)
    total_sets = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)

    # Relación uno a muchos
    muscle_groups = relationship("WorkoutMuscleGroup", back_populates= 'workout', cascade='all, delete-orphan')
    exercises = relationship('Exercise', back_populates='workout', cascade='all, delete-orphan')