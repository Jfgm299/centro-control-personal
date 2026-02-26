from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from app.core.database import Base
from ..enums import GymSetType
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

class Exercise(Base):
    __tablename__ = 'exercises'
    __table_args__ = {'schema':'gym_tracker', 'extend_existing': True}

    id = Column(Integer, primary_key=True)
    name = Column(String(150), nullable=False)
    order = Column(Integer)
    notes = Column(String, nullable=True)
    exercise_type = Column(Enum(GymSetType), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    workout_id = Column(Integer, ForeignKey('gym_tracker.workouts.id', ondelete='CASCADE'))

    workout = relationship('Workout', back_populates='exercises')
    sets = relationship('Set', back_populates='exercise',cascade='all, delete-orphan')

