"""
Handlers de automatización para macro_tracker.

Cada función sigue la firma estándar:
    def handle_X(payload: dict, config: dict, db: Session, user_id: int) -> dict

Triggers devuelven {"matched": True/False, ...} — NUNCA lanzan excepciones.
Acciones devuelven {"done": True/False, ...}    — NUNCA lanzan excepciones.
"""
import logging
from sqlalchemy.orm import Session

from .diary_entry import DiaryEntry
from .user_goal import UserGoal
from .product import Product

logger = logging.getLogger(__name__)

MACRO_FIELDS = ["energy_kcal", "proteins_g", "carbohydrates_g", "fat_g", "fiber_g"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def _entry_to_dict(entry: DiaryEntry) -> dict:
    """Serializa un DiaryEntry + su Product a dict."""
    meal_type = entry.meal_type
    if hasattr(meal_type, "value"):
        meal_type = meal_type.value
    return {
        "entry_id":        entry.id,
        "product_name":    entry.product.product_name if entry.product else None,
        "brand":           entry.product.brand if entry.product else None,
        "meal_type":       meal_type,
        "amount_g":        entry.amount_g,
        "entry_date":      str(entry.entry_date),
        "energy_kcal":     entry.energy_kcal or 0.0,
        "proteins_g":      entry.proteins_g or 0.0,
        "carbohydrates_g": entry.carbohydrates_g or 0.0,
        "fat_g":           entry.fat_g or 0.0,
        "fiber_g":         entry.fiber_g or 0.0,
        "nutriscore":      entry.product.nutriscore if entry.product else None,
    }


# ── TRIGGER HANDLERS ──────────────────────────────────────────────────────────

def handle_meal_logged(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Trigger: al registrar una comida.
    Payload: entry_id (mínimo — el resto lo cargamos desde la BD).
    Config filters: meal_type, min_energy_kcal, max_energy_kcal, min_proteins_g,
                    nutriscore, product_name_contains — todos opcionales, lógica AND.
    """
    try:
        entry_id = payload.get("entry_id")
        if not entry_id:
            return {"matched": False, "reason": "no entry_id in payload"}

        from sqlalchemy.orm import joinedload
        entry = (
            db.query(DiaryEntry)
            .options(joinedload(DiaryEntry.product))
            .filter(DiaryEntry.id == entry_id, DiaryEntry.user_id == user_id)
            .first()
        )
        if not entry:
            return {"matched": False, "reason": f"entry {entry_id} not found"}

        entry_dict = _entry_to_dict(entry)

        # Filtros opcionales — lógica AND, omitir si ausente/None
        meal_type_filter = config.get("meal_type")
        if meal_type_filter and entry_dict["meal_type"] != meal_type_filter:
            return {"matched": False, "reason": "meal_type filter not met"}

        min_kcal = config.get("min_energy_kcal")
        if min_kcal is not None and (entry_dict["energy_kcal"] or 0.0) < float(min_kcal):
            return {"matched": False, "reason": "min_energy_kcal filter not met"}

        max_kcal = config.get("max_energy_kcal")
        if max_kcal is not None and (entry_dict["energy_kcal"] or 0.0) > float(max_kcal):
            return {"matched": False, "reason": "max_energy_kcal filter not met"}

        min_proteins = config.get("min_proteins_g")
        if min_proteins is not None and (entry_dict["proteins_g"] or 0.0) < float(min_proteins):
            return {"matched": False, "reason": "min_proteins_g filter not met"}

        nutriscore_filter = config.get("nutriscore")
        if nutriscore_filter:
            product_nutriscore = entry_dict.get("nutriscore")
            if not product_nutriscore or product_nutriscore.upper() != nutriscore_filter.upper():
                return {"matched": False, "reason": "nutriscore filter not met"}

        name_contains = config.get("product_name_contains")
        if name_contains:
            product_name = entry_dict.get("product_name") or ""
            if name_contains.lower() not in product_name.lower():
                return {"matched": False, "reason": "product_name_contains filter not met"}

        return {"matched": True, "entry": entry_dict}

    except Exception as e:
        logger.error(f"handle_meal_logged error: {e}")
        return {"matched": False, "reason": "internal error"}


def handle_daily_macro_threshold(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Trigger: al superar/bajar de un % del objetivo diario de un macro.
    Payload: date, macro, actual_value, goal_value, progress_pct (pre-computados por el dispatcher).
    Config: macro (requerido), threshold_pct (default 100), direction (default "above").

    Nota: la deduplicación vive en el dispatcher, no aquí.
    """
    try:
        macro         = payload.get("macro")
        actual_value  = payload.get("actual_value", 0.0)
        goal_value    = payload.get("goal_value")
        progress_pct  = payload.get("progress_pct", 0.0)

        if not macro or goal_value is None:
            return {"matched": False, "reason": "missing macro data in payload"}

        threshold_pct = float(config.get("threshold_pct", 100))
        direction     = config.get("direction", "above")

        if direction == "above":
            matched = progress_pct >= threshold_pct
        else:  # below
            matched = progress_pct <= threshold_pct

        if not matched:
            return {"matched": False, "reason": "threshold not met"}

        return {
            "matched":       True,
            "macro":         macro,
            "actual_value":  actual_value,
            "goal_value":    goal_value,
            "progress_pct":  progress_pct,
            "direction":     direction,
            "threshold_pct": threshold_pct,
            "date":          payload.get("date"),
        }

    except Exception as e:
        logger.error(f"handle_daily_macro_threshold error: {e}")
        return {"matched": False, "reason": "internal error"}


def handle_goal_updated(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Trigger: al actualizar los objetivos nutricionales.
    Payload: energy_kcal, proteins_g, carbohydrates_g, fat_g, fiber_g, changed_fields (list[str]).
    Config: macro_changed (opcional) — solo dispara si cambió este macro específico.
    """
    try:
        changed_fields = payload.get("changed_fields", [])

        macro_changed = config.get("macro_changed")
        if macro_changed and macro_changed not in changed_fields:
            return {
                "matched": False,
                "reason":  f"target macro '{macro_changed}' did not change",
            }

        return {
            "matched":        True,
            "changed_fields": changed_fields,
            "goals":          {f: payload.get(f) for f in MACRO_FIELDS},
        }

    except Exception as e:
        logger.error(f"handle_goal_updated error: {e}")
        return {"matched": False, "reason": "internal error"}


def handle_no_entry_logged_today(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Trigger: si no hay entradas hoy.
    El scheduler ya verificó la hora y la ausencia de entradas.
    Este handler hace una doble-verificación contra la BD.
    """
    try:
        from datetime import date
        today = date.today()

        entry_count = db.query(DiaryEntry).filter(
            DiaryEntry.user_id    == user_id,
            DiaryEntry.entry_date == today,
        ).count()

        if entry_count > 0:
            return {"matched": False, "reason": "entries exist for today"}

        return {
            "matched":               True,
            "days_since_last_entry": payload.get("days_since_last_entry", 0),
            "last_entry_date":       payload.get("last_entry_date"),
        }

    except Exception as e:
        logger.error(f"handle_no_entry_logged_today error: {e}")
        return {"matched": False, "reason": "internal error"}


def handle_logging_streak(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Trigger: al alcanzar exactamente N días consecutivos.
    Payload: streak_days (racha computada), streak_start_date.
    Config: streak_days (requerido) — coincidencia exacta, NO >=.
    """
    try:
        computed_streak = payload.get("streak_days", 0)
        target_streak   = int(config.get("streak_days", 0))

        if not target_streak:
            return {"matched": False, "reason": "streak_days not configured"}

        if computed_streak != target_streak:
            return {
                "matched": False,
                "reason":  f"streak is {computed_streak}, target is {target_streak}",
            }

        return {
            "matched":           True,
            "streak_days":       computed_streak,
            "streak_start_date": payload.get("streak_start_date"),
        }

    except Exception as e:
        logger.error(f"handle_logging_streak error: {e}")
        return {"matched": False, "reason": "internal error"}


# ── ACTION HANDLERS ───────────────────────────────────────────────────────────

def action_get_daily_summary(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Acción: resumen de macros del día.
    Config: date_offset (default 0). 0=hoy, -1=ayer.
    """
    try:
        from datetime import date, timedelta
        from sqlalchemy.orm import joinedload
        from collections import defaultdict

        date_offset = int(config.get("date_offset", 0))
        target_date = date.today() + timedelta(days=date_offset)

        entries = (
            db.query(DiaryEntry)
            .options(joinedload(DiaryEntry.product))
            .filter(DiaryEntry.user_id == user_id, DiaryEntry.entry_date == target_date)
            .all()
        )

        # Totales
        totals = {f: 0.0 for f in MACRO_FIELDS}
        for e in entries:
            for f in MACRO_FIELDS:
                totals[f] = round(totals[f] + (getattr(e, f) or 0.0), 2)

        # Comidas agrupadas por tipo — incluir todas las claves aunque estén vacías
        meals = defaultdict(list)
        for e in entries:
            meal_key = e.meal_type.value if hasattr(e.meal_type, "value") else e.meal_type
            meals[meal_key].append(_entry_to_dict(e))

        all_meal_types = [
            "breakfast", "morning_snack", "lunch", "afternoon_snack", "dinner", "other"
        ]
        meals_dict = {k: meals.get(k, []) for k in all_meal_types}

        # Objetivos y progreso
        goal = db.query(UserGoal).filter(UserGoal.user_id == user_id).first()
        if goal:
            goals_dict = {f: getattr(goal, f) for f in MACRO_FIELDS}
            progress_pct = {
                f: round(totals[f] / goals_dict[f] * 100, 1) if goals_dict[f] else None
                for f in MACRO_FIELDS
            }
        else:
            goals_dict   = {f: None for f in MACRO_FIELDS}
            progress_pct = {f: None for f in MACRO_FIELDS}

        return {
            "done":         True,
            "date":         str(target_date),
            "totals":       totals,
            "goals":        goals_dict,
            "progress_pct": progress_pct,
            "meals":        meals_dict,
        }

    except Exception as e:
        logger.error(f"action_get_daily_summary error: {e}")
        return {"done": False, "reason": "internal error"}


def action_get_weekly_stats(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Acción: estadísticas semanales de macros.
    Config: week_offset (default 0). Semana = Lun–Dom.
    """
    try:
        from datetime import date, timedelta
        from collections import defaultdict
        from sqlalchemy.orm import joinedload

        week_offset = int(config.get("week_offset", 0))
        today       = date.today()
        monday      = today - timedelta(days=today.weekday())
        week_start  = monday + timedelta(weeks=week_offset)
        week_end    = week_start + timedelta(days=6)

        entries = (
            db.query(DiaryEntry)
            .options(joinedload(DiaryEntry.product))
            .filter(
                DiaryEntry.user_id    == user_id,
                DiaryEntry.entry_date >= week_start,
                DiaryEntry.entry_date <= week_end,
            )
            .all()
        )

        # Días distintos con entradas
        logged_dates = set(e.entry_date for e in entries)
        days_logged  = len(logged_dates)
        consistency  = round(days_logged / 7 * 100, 1)

        # Medias diarias sobre los días con entradas (no sobre 7)
        daily_sums = defaultdict(float)
        for e in entries:
            for f in MACRO_FIELDS:
                daily_sums[f] += (getattr(e, f) or 0.0)

        if days_logged > 0:
            daily_averages = {f: round(daily_sums[f] / days_logged, 2) for f in MACRO_FIELDS}
        else:
            daily_averages = {f: 0.0 for f in MACRO_FIELDS}

        # Top 5 productos por frecuencia
        product_data: dict = defaultdict(
            lambda: {"count": 0, "total_g": 0.0, "total_kcal": 0.0, "name": "", "brand": None}
        )
        for e in entries:
            pid = e.product_id
            product_data[pid]["count"]      += 1
            product_data[pid]["total_g"]    += e.amount_g or 0.0
            product_data[pid]["total_kcal"] += e.energy_kcal or 0.0
            if e.product:
                product_data[pid]["name"]  = e.product.product_name
                product_data[pid]["brand"] = e.product.brand

        top_products = sorted(
            [
                {
                    "product_id":   pid,
                    "product_name": v["name"],
                    "brand":        v["brand"],
                    "entry_count":  v["count"],
                    "avg_amount_g": round(v["total_g"] / v["count"], 2) if v["count"] else 0.0,
                }
                for pid, v in product_data.items()
            ],
            key=lambda x: x["entry_count"],
            reverse=True,
        )[:5]

        return {
            "done":            True,
            "week_start":      str(week_start),
            "week_end":        str(week_end),
            "days_logged":     days_logged,
            "consistency_pct": consistency,
            "daily_averages":  daily_averages,
            "top_products":    top_products,
        }

    except Exception as e:
        logger.error(f"action_get_weekly_stats error: {e}")
        return {"done": False, "reason": "internal error"}


def action_get_goal_progress(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Acción: progreso del día vs objetivos.
    Config: ninguna.
    """
    try:
        from datetime import date

        goal = db.query(UserGoal).filter(UserGoal.user_id == user_id).first()
        if not goal:
            return {"done": False, "reason": "no goal configured for user"}

        today = date.today()
        entries = db.query(DiaryEntry).filter(
            DiaryEntry.user_id    == user_id,
            DiaryEntry.entry_date == today,
        ).all()

        actuals = {f: sum(getattr(e, f) or 0.0 for e in entries) for f in MACRO_FIELDS}

        progress = {}
        for f in MACRO_FIELDS:
            goal_val = getattr(goal, f) or 0.0
            actual   = round(actuals[f], 2)
            progress[f] = {
                "goal":         goal_val,
                "actual":       actual,
                "remaining":    round(goal_val - actual, 2),
                "progress_pct": round(actual / goal_val * 100, 1) if goal_val else 0.0,
            }

        return {
            "done":     True,
            "date":     str(today),
            "progress": progress,
        }

    except Exception as e:
        logger.error(f"action_get_goal_progress error: {e}")
        return {"done": False, "reason": "internal error"}


def action_log_meal(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Acción: registrar una comida.
    CRÍTICO: llama add_entry() con skip_dispatch=True para evitar doble-dispatch.
    Config: product_id (requerido), amount_g (requerido), meal_type (requerido),
            date_offset (default 0).
    """
    try:
        from datetime import date, timedelta
        from .services.diary_service import DiaryService
        from .macro_schema import DiaryEntryCreate
        diary_service = DiaryService()
        from .enums.meal_type import MealType

        product_id  = config.get("product_id")
        amount_g    = config.get("amount_g")
        meal_type   = config.get("meal_type")
        date_offset = int(config.get("date_offset", 0))

        if product_id is None:
            return {"done": False, "reason": "product_id not configured"}
        if amount_g is None:
            return {"done": False, "reason": "amount_g not configured"}
        if not meal_type:
            return {"done": False, "reason": "meal_type not configured"}

        # Verificar que el producto existe antes de llamar al servicio
        product = db.query(Product).filter(Product.id == int(product_id)).first()
        if not product:
            return {"done": False, "reason": f"product {product_id} not found"}

        target_date = date.today() + timedelta(days=date_offset)

        data = DiaryEntryCreate(
            product_id=int(product_id),
            amount_g=float(amount_g),
            meal_type=MealType(meal_type),
            entry_date=target_date,
        )
        entry = diary_service.add_entry(db, user_id, data, skip_dispatch=True)

        return {
            "done":            True,
            "entry_id":        entry.id,
            "product_name":    product.product_name,
            "amount_g":        entry.amount_g,
            "meal_type":       meal_type,
            "energy_kcal":     entry.energy_kcal or 0.0,
            "proteins_g":      entry.proteins_g or 0.0,
            "carbohydrates_g": entry.carbohydrates_g or 0.0,
            "fat_g":           entry.fat_g or 0.0,
        }

    except Exception as e:
        logger.error(f"action_log_meal error: {e}")
        return {"done": False, "reason": str(e)}


def action_get_top_products(payload: dict, config: dict, db: Session, user_id: int) -> dict:
    """
    Acción: productos más usados en N días.
    Config: days (default 30), limit (default 5, máx. 10).
    """
    try:
        from datetime import date, timedelta
        from collections import defaultdict
        from sqlalchemy.orm import joinedload

        days  = int(config.get("days", 30))
        limit = min(int(config.get("limit", 5)), 10)

        since = date.today() - timedelta(days=days)

        entries = (
            db.query(DiaryEntry)
            .options(joinedload(DiaryEntry.product))
            .filter(
                DiaryEntry.user_id    == user_id,
                DiaryEntry.entry_date >= since,
            )
            .all()
        )

        product_data: dict = defaultdict(
            lambda: {"count": 0, "total_g": 0.0, "total_kcal": 0.0, "name": "", "brand": None}
        )
        for e in entries:
            pid = e.product_id
            product_data[pid]["count"]      += 1
            product_data[pid]["total_g"]    += e.amount_g or 0.0
            product_data[pid]["total_kcal"] += e.energy_kcal or 0.0
            if e.product:
                product_data[pid]["name"]  = e.product.product_name
                product_data[pid]["brand"] = e.product.brand

        products = sorted(
            [
                {
                    "product_id":        pid,
                    "product_name":      v["name"],
                    "brand":             v["brand"],
                    "entry_count":       v["count"],
                    "avg_amount_g":      round(v["total_g"] / v["count"], 2) if v["count"] else 0.0,
                    "total_energy_kcal": round(v["total_kcal"], 2),
                }
                for pid, v in product_data.items()
            ],
            key=lambda x: x["entry_count"],
            reverse=True,
        )[:limit]

        return {
            "done":        True,
            "period_days": days,
            "products":    products,
        }

    except Exception as e:
        logger.error(f"action_get_top_products error: {e}")
        return {"done": False, "reason": "internal error"}
