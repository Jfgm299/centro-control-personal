from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from ..enums import GymSetType


class ExerciseCatalog(Base):
    __tablename__ = 'exercise_catalog'
    __table_args__ = {'schema': 'gym_tracker', 'extend_existing': True}

    id            = Column(Integer, primary_key=True)
    name          = Column(String(150), nullable=False)
    
    # --- AQUÍ ESTÁ LA CORRECCIÓN ---
    exercise_type = Column(
        Enum(
            GymSetType, 
            name='gymsettype',
            values_callable=lambda obj: [e.value for e in obj] # <--- Esto hace la magia
        ), 
        nullable=False
    )
    # -------------------------------
    
    # Lista de valores de MuscleGroupCategory: ["Chest", "Triceps"]
    muscle_groups = Column(JSON, nullable=False, default=list)
    is_custom     = Column(Boolean, nullable=False, default=False)
    # null → ejercicio global/predefinido; not null → custom del usuario
    user_id       = Column(Integer, ForeignKey('core.users.id', ondelete='CASCADE'), nullable=True)