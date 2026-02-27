from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base

class Workout(Base):
    __tablename__ = 'workouts'
    __table_args__ = {'schema':'gym_tracker', 'extend_existing': True}

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('core.users.id', ondelete='CASCADE'), nullable=False)
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    total_exercises = Column(Integer, nullable=True)
    total_sets = Column(Integer, nullable=True)
    notes = Column(Text, nullable=True)

    # Relación uno a muchos
    muscle_groups = relationship("WorkoutMuscleGroup", back_populates= 'workout', cascade='all, delete-orphan')
    exercises = relationship('Exercise', back_populates='workout', cascade='all, delete-orphan')
    user = relationship("User", back_populates="workouts")