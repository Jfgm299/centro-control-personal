from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from ...database import Base
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

class Exercise(Base):
    __tablename__ = 'exercises'

    id = Column(Integer, primary_key=True, index=True)
    order = Column(Integer)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    workout_id = Column(Integer, ForeignKey('workouts.id', ondelete='CASCADE'))
    exercise_catalog_id = Column(Integer, ForeignKey('exercise_catalog.id'))

    workout = relationship('Workout', back_populates='excercises')
    exercise_catalog = relationship('ExerciseCatalog')
    sets = relationship('Set', back_populates='exercise',cascade='all, delete-orphan')

