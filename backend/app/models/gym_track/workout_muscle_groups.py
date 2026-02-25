from sqlalchemy import Column, Integer, Enum, ForeignKey
from ...database import Base
from ...enums import MuscleGroupCategory
from sqlalchemy.orm import relationship

class WorkoutMuscleGroup(Base):
    __tablename__ = 'workout_muscle_groups'

    id = Column(Integer, primary_key=True, index=True)
    workout_id = Column(Integer, ForeignKey('workouts.id', ondelete='CASCADE'))
    muscle_group = Column(Enum(MuscleGroupCategory), nullable=False)

    workout = relationship("Workout", back_populates='muscle_groups')