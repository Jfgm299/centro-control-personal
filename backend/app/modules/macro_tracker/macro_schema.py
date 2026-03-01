from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import date, datetime
from typing import Optional
from .enums.meal_type import MealType


# ── Producto ──────────────────────────────────────────────────────────────────

class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:                 int
    barcode:            Optional[str]
    product_name:       str
    brand:              Optional[str]
    serving_size_text:  Optional[str]
    serving_quantity_g: Optional[float]
    nutriscore:         Optional[str]
    image_url:          Optional[str]
    energy_kcal_100g:   Optional[float]
    proteins_100g:      Optional[float]
    carbohydrates_100g: Optional[float]
    sugars_100g:        Optional[float]
    fat_100g:           Optional[float]
    saturated_fat_100g: Optional[float]
    fiber_100g:         Optional[float]
    salt_100g:          Optional[float]
    source:             str


# ── Diary Entry ───────────────────────────────────────────────────────────────

class DiaryEntryCreate(BaseModel):
    product_id: int
    entry_date: date
    meal_type:  MealType
    amount_g:   float = Field(..., gt=0, le=5000)
    notes:      Optional[str] = None

    @field_validator("amount_g")
    @classmethod
    def round_amount(cls, v: float) -> float:
        return round(v, 1)


class DiaryEntryAmountUpdate(BaseModel):
    amount_g: float = Field(..., gt=0, le=5000)

    @field_validator("amount_g")
    @classmethod
    def round_amount(cls, v: float) -> float:
        return round(v, 1)


class DiaryEntryNotesUpdate(BaseModel):
    notes: Optional[str] = None


class DiaryEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:              int
    product_id:      int
    entry_date:      date
    meal_type:       MealType
    amount_g:        float
    energy_kcal:     Optional[float]
    proteins_g:      Optional[float]
    carbohydrates_g: Optional[float]
    sugars_g:        Optional[float]
    fat_g:           Optional[float]
    saturated_fat_g: Optional[float]
    fiber_g:         Optional[float]
    salt_g:          Optional[float]
    notes:           Optional[str]
    created_at:      datetime
    updated_at:      Optional[datetime]
    product:         ProductResponse


# ── Nutrient Totals ───────────────────────────────────────────────────────────

class NutrientTotals(BaseModel):
    energy_kcal:     float = 0.0
    proteins_g:      float = 0.0
    carbohydrates_g: float = 0.0
    sugars_g:        float = 0.0
    fat_g:           float = 0.0
    saturated_fat_g: float = 0.0
    fiber_g:         float = 0.0
    salt_g:          float = 0.0


# ── Meal Summary (agrupado por comida) ────────────────────────────────────────

class MealSummary(BaseModel):
    meal_type:       MealType
    entries:         list[DiaryEntryResponse]
    total_energy_kcal:     float
    total_proteins_g:      float
    total_carbohydrates_g: float
    total_fat_g:           float


# ── Goal Progress ─────────────────────────────────────────────────────────────

class GoalProgress(BaseModel):
    energy_pct:       float
    proteins_pct:     float
    carbohydrates_pct: float
    fat_pct:          float


# ── User Goal ─────────────────────────────────────────────────────────────────

class UserGoalResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:              int
    energy_kcal:     float
    proteins_g:      float
    carbohydrates_g: float
    fat_g:           float
    fiber_g:         Optional[float]
    updated_at:      Optional[datetime]


class UserGoalUpdate(BaseModel):
    energy_kcal:     Optional[float] = Field(None, gt=0)
    proteins_g:      Optional[float] = Field(None, gt=0)
    carbohydrates_g: Optional[float] = Field(None, gt=0)
    fat_g:           Optional[float] = Field(None, gt=0)
    fiber_g:         Optional[float] = Field(None, gt=0)


# ── Daily Summary ─────────────────────────────────────────────────────────────

class DailySummaryResponse(BaseModel):
    date:     date
    meals:    list[MealSummary]
    totals:   NutrientTotals
    goals:    Optional[UserGoalResponse]
    progress: Optional[GoalProgress]


# ── Stats ─────────────────────────────────────────────────────────────────────

class DailyAverage(BaseModel):
    period_days:        int
    days_logged:        int
    avg_energy_kcal:    float = 0.0
    avg_proteins_g:     float = 0.0
    avg_carbohydrates_g: float = 0.0
    avg_fat_g:          float = 0.0
    avg_fiber_g:        float = 0.0


class ProductFrequency(BaseModel):
    product:      ProductResponse
    entry_count:  int


class StatsResponse(BaseModel):
    period_days:      int
    days_logged:      int
    total_entries:    int
    consistency_pct:  float
    daily_average:    DailyAverage
    top_products:     list[ProductFrequency]