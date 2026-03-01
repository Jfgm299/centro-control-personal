from datetime import date
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.core.auth.user import User

from .macro_schema import (
    DiaryEntryCreate,
    DiaryEntryAmountUpdate,
    DiaryEntryNotesUpdate,
    DiaryEntryResponse,
    DailySummaryResponse,
    ProductResponse,
    StatsResponse,
    UserGoalResponse,
    UserGoalUpdate,
)
from .enums.meal_type import MealType
from .services import FoodService, DiaryService, StatsService

router = APIRouter(prefix="/macros", tags=["Macros"])

food_service  = FoodService()
diary_service = DiaryService()
stats_service = StatsService()


# ── RUTAS LITERALES PRIMERO (antes que /{param}) ──────────────────────────────

@router.get("/products/barcode/{barcode}", response_model=ProductResponse)
async def get_product_by_barcode(
    barcode: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Busca un producto por código de barras. Si no está en caché llama a OFF (1 llamada)."""
    return await food_service.get_or_fetch_by_barcode(db, barcode)


@router.get("/products/search", response_model=list[ProductResponse])
async def search_products(
    q: str = Query(..., min_length=1),
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Busca productos por nombre. Primero en BD local, luego en OFF si hay pocos resultados."""
    return await food_service.search_products(db, q, limit)


@router.get("/diary/summary", response_model=DailySummaryResponse)
def get_daily_summary(
    target_date: date = Query(default_factory=date.today, alias="date"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Resumen del día: entradas agrupadas por comida, totales y % de objetivos."""
    return diary_service.get_daily_summary(db, user.id, target_date)


@router.get("/stats", response_model=StatsResponse)
def get_stats(
    days: int = Query(default=30, ge=7, le=365),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Estadísticas del período: medias diarias, productos más frecuentes, consistencia."""
    from datetime import timedelta
    end   = date.today()
    start = end - timedelta(days=days)
    entries = diary_service.get_entries_range(db, user.id, start, end)
    return stats_service.calculate_stats(entries, period_days=days)


@router.get("/goals", response_model=UserGoalResponse)
def get_goals(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Devuelve los objetivos nutricionales del usuario. Los crea con defaults si no existen."""
    return diary_service.get_goals(db, user.id)


@router.put("/goals", response_model=UserGoalResponse)
def upsert_goals(
    data: UserGoalUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Crea o actualiza los objetivos nutricionales del usuario."""
    return diary_service.upsert_goals(db, user.id, data)


# ── RUTAS CON PARÁMETROS — SIEMPRE AL FINAL ───────────────────────────────────

@router.get("/products/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Obtiene un producto del catálogo local por ID."""
    return food_service.get_product_by_id(db, product_id)


@router.get("/diary", response_model=list[DiaryEntryResponse])
def get_diary(
    start:     Optional[date]     = Query(default=None),
    end:       Optional[date]     = Query(default=None),
    meal_type: Optional[MealType] = Query(default=None),
    limit:     int                = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Lista entradas del diario con filtros opcionales de fecha y comida."""
    return diary_service.get_entries(db, user.id, start, end, meal_type, limit)


@router.post("/diary", response_model=DiaryEntryResponse, status_code=201)
def add_diary_entry(
    data: DiaryEntryCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Añade una entrada al diario. Calcula automáticamente los nutrientes para amount_g."""
    return diary_service.add_entry(db, user.id, data)


@router.patch("/diary/{entry_id}/amount", response_model=DiaryEntryResponse)
def update_entry_amount(
    entry_id: int,
    data: DiaryEntryAmountUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Actualiza la cantidad (g) de una entrada y recalcula todos los nutrientes."""
    return diary_service.update_entry_amount(db, user.id, entry_id, data.amount_g)


@router.patch("/diary/{entry_id}/notes", response_model=DiaryEntryResponse)
def update_entry_notes(
    entry_id: int,
    data: DiaryEntryNotesUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Actualiza las notas personales de una entrada."""
    return diary_service.update_entry_notes(db, user.id, entry_id, data.notes)


@router.delete("/diary/{entry_id}", status_code=204)
def delete_diary_entry(
    entry_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Elimina una entrada del diario."""
    diary_service.delete_entry(db, user.id, entry_id)