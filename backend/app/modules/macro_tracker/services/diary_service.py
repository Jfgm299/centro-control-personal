from datetime import date
from collections import defaultdict
from sqlalchemy.orm import Session, joinedload
from ..diary_entry import DiaryEntry
from ..user_goal import UserGoal
from ..product import Product
from ..macro_schema import (
    DiaryEntryCreate,
    DailySummaryResponse,
    MealSummary,
    NutrientTotals,
    GoalProgress,
)
from ..exceptions import DiaryEntryNotFoundError, ProductNotFoundError
from ..enums.meal_type import MealType


def _calc_nutrient(value_100g: float | None, amount_g: float) -> float | None:
    """Calcula el nutriente para amount_g a partir del valor por 100g."""
    if value_100g is None:
        return None
    return round(value_100g * amount_g / 100.0, 2)


def _get_or_create_goal(db: Session, user_id: int) -> UserGoal:
    """Devuelve el UserGoal del usuario, creándolo con defaults si no existe."""
    goal = db.query(UserGoal).filter(UserGoal.user_id == user_id).first()
    if not goal:
        goal = UserGoal(user_id=user_id)
        db.add(goal)
        db.commit()
        db.refresh(goal)
    return goal


class DiaryService:

    def add_entry(self, db: Session, user_id: int, data: DiaryEntryCreate) -> DiaryEntry:
        # Verificar que el producto existe
        product = db.query(Product).filter(Product.id == data.product_id).first()
        if not product:
            raise ProductNotFoundError(data.product_id)

        entry = DiaryEntry(
            user_id=user_id,
            product_id=data.product_id,
            entry_date=data.entry_date,
            meal_type=data.meal_type,
            amount_g=data.amount_g,
            notes=data.notes,
            # Calcular todos los nutrientes para amount_g
            energy_kcal=    _calc_nutrient(product.energy_kcal_100g,   data.amount_g),
            proteins_g=     _calc_nutrient(product.proteins_100g,      data.amount_g),
            carbohydrates_g=_calc_nutrient(product.carbohydrates_100g, data.amount_g),
            sugars_g=       _calc_nutrient(product.sugars_100g,        data.amount_g),
            fat_g=          _calc_nutrient(product.fat_100g,           data.amount_g),
            saturated_fat_g=_calc_nutrient(product.saturated_fat_100g, data.amount_g),
            fiber_g=        _calc_nutrient(product.fiber_100g,         data.amount_g),
            salt_g=         _calc_nutrient(product.salt_100g,          data.amount_g),
        )
        db.add(entry)
        db.commit()
        db.refresh(entry)
        # Eager load del producto para la respuesta
        db.refresh(entry)
        entry = (
            db.query(DiaryEntry)
            .options(joinedload(DiaryEntry.product))
            .filter(DiaryEntry.id == entry.id)
            .first()
        )
        return entry

    def get_entry(self, db: Session, user_id: int, entry_id: int) -> DiaryEntry:
        entry = (
            db.query(DiaryEntry)
            .options(joinedload(DiaryEntry.product))
            .filter(DiaryEntry.id == entry_id, DiaryEntry.user_id == user_id)
            .first()
        )
        if not entry:
            raise DiaryEntryNotFoundError(entry_id)
        return entry

    def get_entries(
        self,
        db: Session,
        user_id: int,
        start: date | None = None,
        end: date | None = None,
        meal_type: MealType | None = None,
        limit: int = 100,
    ) -> list[DiaryEntry]:
        q = (
            db.query(DiaryEntry)
            .options(joinedload(DiaryEntry.product))
            .filter(DiaryEntry.user_id == user_id)
        )
        if start:
            q = q.filter(DiaryEntry.entry_date >= start)
        if end:
            q = q.filter(DiaryEntry.entry_date <= end)
        if meal_type:
            q = q.filter(DiaryEntry.meal_type == meal_type)
        return q.order_by(DiaryEntry.entry_date.desc()).limit(limit).all()

    def get_entries_range(
        self, db: Session, user_id: int, start: date, end: date
    ) -> list[DiaryEntry]:
        return (
            db.query(DiaryEntry)
            .options(joinedload(DiaryEntry.product))
            .filter(
                DiaryEntry.user_id == user_id,
                DiaryEntry.entry_date >= start,
                DiaryEntry.entry_date <= end,
            )
            .order_by(DiaryEntry.entry_date.asc())
            .all()
        )

    def get_daily_summary(
        self, db: Session, user_id: int, target_date: date
    ) -> DailySummaryResponse:
        entries = (
            db.query(DiaryEntry)
            .options(joinedload(DiaryEntry.product))
            .filter(
                DiaryEntry.user_id == user_id,
                DiaryEntry.entry_date == target_date,
            )
            .all()
        )

        # Agrupar por meal_type en orden lógico
        meal_order = list(MealType)
        by_meal: dict[MealType, list[DiaryEntry]] = defaultdict(list)
        for e in entries:
            by_meal[e.meal_type].append(e)

        meals = []
        for mt in meal_order:
            if mt not in by_meal:
                continue
            meal_entries = by_meal[mt]
            meals.append(MealSummary(
                meal_type=mt,
                entries=meal_entries,
                total_energy_kcal=    sum(e.energy_kcal     or 0 for e in meal_entries),
                total_proteins_g=     sum(e.proteins_g      or 0 for e in meal_entries),
                total_carbohydrates_g=sum(e.carbohydrates_g or 0 for e in meal_entries),
                total_fat_g=          sum(e.fat_g           or 0 for e in meal_entries),
            ))

        totals = NutrientTotals(
            energy_kcal=    sum(e.energy_kcal     or 0 for e in entries),
            proteins_g=     sum(e.proteins_g      or 0 for e in entries),
            carbohydrates_g=sum(e.carbohydrates_g or 0 for e in entries),
            sugars_g=       sum(e.sugars_g        or 0 for e in entries),
            fat_g=          sum(e.fat_g           or 0 for e in entries),
            saturated_fat_g=sum(e.saturated_fat_g or 0 for e in entries),
            fiber_g=        sum(e.fiber_g         or 0 for e in entries),
            salt_g=         sum(e.salt_g          or 0 for e in entries),
        )

        goal = _get_or_create_goal(db, user_id)
        progress = GoalProgress(
            energy_pct=       round(totals.energy_kcal     / goal.energy_kcal     * 100, 1) if goal.energy_kcal     else 0.0,
            proteins_pct=     round(totals.proteins_g      / goal.proteins_g      * 100, 1) if goal.proteins_g      else 0.0,
            carbohydrates_pct=round(totals.carbohydrates_g / goal.carbohydrates_g * 100, 1) if goal.carbohydrates_g else 0.0,
            fat_pct=          round(totals.fat_g           / goal.fat_g           * 100, 1) if goal.fat_g           else 0.0,
        )

        return DailySummaryResponse(
            date=target_date,
            meals=meals,
            totals=totals,
            goals=goal,
            progress=progress,
        )

    def update_entry_amount(
        self, db: Session, user_id: int, entry_id: int, amount_g: float
    ) -> DiaryEntry:
        entry = self.get_entry(db, user_id, entry_id)
        product = entry.product

        entry.amount_g          = amount_g
        entry.energy_kcal       = _calc_nutrient(product.energy_kcal_100g,   amount_g)
        entry.proteins_g        = _calc_nutrient(product.proteins_100g,      amount_g)
        entry.carbohydrates_g   = _calc_nutrient(product.carbohydrates_100g, amount_g)
        entry.sugars_g          = _calc_nutrient(product.sugars_100g,        amount_g)
        entry.fat_g             = _calc_nutrient(product.fat_100g,           amount_g)
        entry.saturated_fat_g   = _calc_nutrient(product.saturated_fat_100g, amount_g)
        entry.fiber_g           = _calc_nutrient(product.fiber_100g,         amount_g)
        entry.salt_g            = _calc_nutrient(product.salt_100g,          amount_g)

        db.commit()
        db.refresh(entry)
        return entry

    def update_entry_notes(
        self, db: Session, user_id: int, entry_id: int, notes: str | None
    ) -> DiaryEntry:
        entry = self.get_entry(db, user_id, entry_id)
        entry.notes = notes
        db.commit()
        db.refresh(entry)
        return entry

    def delete_entry(self, db: Session, user_id: int, entry_id: int) -> None:
        entry = (
            db.query(DiaryEntry)
            .filter(DiaryEntry.id == entry_id, DiaryEntry.user_id == user_id)
            .first()
        )
        if not entry:
            raise DiaryEntryNotFoundError(entry_id)
        db.delete(entry)
        db.commit()

    def get_goals(self, db: Session, user_id: int) -> UserGoal:
        return _get_or_create_goal(db, user_id)

    def upsert_goals(self, db: Session, user_id: int, data) -> UserGoal:
        goal = _get_or_create_goal(db, user_id)
        update_data = data.model_dump(exclude_none=True)
        for key, value in update_data.items():
            setattr(goal, key, value)
        db.commit()
        db.refresh(goal)
        return goal