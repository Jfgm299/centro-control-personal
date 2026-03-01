from sqlalchemy import (
    Column, Integer, Float, Date, DateTime, Text,
    Enum as SAEnum, ForeignKey, Index,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
from .enums.meal_type import MealType


class DiaryEntry(Base):
    __tablename__ = "diary_entries"
    __table_args__ = (
        Index("ix_diary_user_date", "user_id", "entry_date"),
        Index("ix_diary_user_meal", "user_id", "entry_date", "meal_type"),
        {"schema": "macro_tracker", "extend_existing": True},
    )

    id         = Column(Integer, primary_key=True)
    user_id    = Column(Integer, ForeignKey("core.users.id", ondelete="CASCADE"), nullable=False)
    product_id = Column(Integer, ForeignKey("macro_tracker.products.id"), nullable=False)
    entry_date = Column(Date, nullable=False)
    meal_type  = Column(
        SAEnum(MealType, name="mealtype", schema="macro_tracker", create_type=True),
        nullable=False,
    )
    amount_g = Column(Float, nullable=False)

    # Nutrientes calculados para amount_g
    energy_kcal    = Column(Float, nullable=True)
    proteins_g     = Column(Float, nullable=True)
    carbohydrates_g = Column(Float, nullable=True)
    sugars_g       = Column(Float, nullable=True)
    fat_g          = Column(Float, nullable=True)
    saturated_fat_g = Column(Float, nullable=True)
    fiber_g        = Column(Float, nullable=True)
    salt_g         = Column(Float, nullable=True)

    notes      = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user    = relationship("User", back_populates="diary_entries")
    product = relationship("Product", back_populates="diary_entries")