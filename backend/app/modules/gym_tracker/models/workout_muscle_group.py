from sqlalchemy import Column, Integer, Enum, ForeignKey
from app.core.database import Base
from ..enums import MuscleGroupCategory
from sqlalchemy.orm import relationship

class WorkoutMuscleGroup(Base):
    __tablename__ = 'workout_muscle_groups'
    __table_args__ = {'schema':'gym_tracker', 'extend_existing': True}

    id = Column(Integer, primary_key=True)
    workout_id = Column(Integer, ForeignKey('gym_tracker.workouts.id', ondelete='CASCADE'))
    muscle_group = Column(Enum(MuscleGroupCategory), nullable=False)

    workout = relationship("Workout", back_populates='muscle_groups')