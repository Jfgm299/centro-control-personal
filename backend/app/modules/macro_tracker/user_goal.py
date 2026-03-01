from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class UserGoal(Base):
    __tablename__ = "user_goals"
    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_goals_user_id"),
        {"schema": "macro_tracker", "extend_existing": True},
    )

    id              = Column(Integer, primary_key=True)
    user_id         = Column(Integer, ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False)
    energy_kcal     = Column(Float, nullable=False, default=2000.0)
    proteins_g      = Column(Float, nullable=False, default=150.0)
    carbohydrates_g = Column(Float, nullable=False, default=250.0)
    fat_g           = Column(Float, nullable=False, default=65.0)
    fiber_g         = Column(Float, nullable=True,  default=25.0)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())
    updated_at      = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="user_goal")