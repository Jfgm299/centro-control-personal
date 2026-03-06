from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum
from sqlalchemy.dialects.postgresql import JSON
from app.core.database import Base
from ..enums import GymSetType
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship


class Exercise(Base):
    __tablename__ = 'exercises'
    __table_args__ = {'schema': 'gym_tracker', 'extend_existing': True}

    id            = Column(Integer, primary_key=True)
    name          = Column(String(150), nullable=False)
    order         = Column(Integer)
    notes         = Column(String, nullable=True)
    exercise_type = Column(Enum(GymSetType, name='gymsettype', values_callable=lambda x: [e.value for e in x]), nullable=False)
    # Snapshot de los muscle groups en el momento de añadir el ejercicio
    muscle_groups = Column(JSON, nullable=False, default=list)
    # FK opcional al catálogo (null si se creó manualmente sin catálogo)
    catalog_id    = Column(Integer, ForeignKey('gym_tracker.exercise_catalog.id', ondelete='SET NULL'), nullable=True)
    created_at    = Column(DateTime(timezone=True), server_default=func.now())

    workout_id = Column(Integer, ForeignKey('gym_tracker.workouts.id', ondelete='CASCADE'))

    workout = relationship('Workout', back_populates='exercises')
    sets    = relationship('Set', back_populates='exercise', cascade='all, delete-orphan')