"""
Scheduler de macro_tracker.
Detecta días sin registro y rachas de logging.

Dos jobs:
  - job_check_no_entry_today:  cada hora, comprueba si no hay entradas hoy
  - job_check_logging_streak:  diario a las 00:05 UTC, comprueba rachas consecutivas

Deduplicación en memoria independiente por trigger.

IMPORTANTE: Nunca llamar job_check_*() directamente en tests — usan SessionLocal()
que apunta al DB de dev (puerto 5432). En tests, llamar dispatcher.on_*() directamente
con la sesión de test.
"""
import logging
from datetime import date, timedelta

from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

# ── Deduplicación en memoria ──────────────────────────────────────────────────
_no_entry_today_cache: dict = {}   # (user_id, "YYYY-MM-DD") -> today_str
_logging_streak_cache: dict = {}   # (user_id, streak_days, "YYYY-MM-DD") -> today_str


def _try_dispatch(method_name: str, *args, **kwargs) -> None:
    try:
        from .automation_dispatcher import dispatcher
        getattr(dispatcher, method_name)(*args, **kwargs)
    except ImportError:
        pass
    except Exception as e:
        logger.warning(f"automation_dispatcher.{method_name} falló: {e}")


def job_check_no_entry_today() -> None:
    """
    Runs every hour. Para cada automation activa con trigger_ref=macro_tracker.no_entry_logged_today:
    1. Extraer check_hour del config del nodo trigger (default 20 UTC)
    2. Saltar si hora UTC actual < check_hour
    3. Saltar si dedup key (user_id, today_str) ya disparó hoy
    4. Contar DiaryEntry del usuario hoy — saltar si > 0
    5. Calcular days_since_last_entry
    6. Despachar via _try_dispatch
    """
    from datetime import datetime, timezone
    db = SessionLocal()
    try:
        from app.modules.automations_engine.models.automation import Automation
        from .diary_entry import DiaryEntry

        now       = datetime.now(timezone.utc)
        today     = now.date()
        today_str = str(today)

        automations = db.query(Automation).filter(
            Automation.trigger_ref == "macro_tracker.no_entry_logged_today",
            Automation.is_active   == True,
        ).all()

        processed_users: set = set()  # evitar consultas duplicadas para el mismo usuario

        for automation in automations:
            user_id = automation.user_id

            flow         = automation.flow or {}
            nodes        = flow.get("nodes", [])
            trigger_node = next((n for n in nodes if n.get("type") == "trigger"), None)
            config       = trigger_node.get("config", {}) if trigger_node else {}
            check_hour   = int(config.get("check_hour", 20))

            # Comprobación de hora
            if now.hour < check_hour:
                continue

            # Dedup
            dedup_key = (user_id, today_str)
            if _no_entry_today_cache.get(dedup_key) == today_str:
                continue

            if user_id in processed_users:
                continue

            # Contar entradas de hoy
            count = db.query(DiaryEntry).filter(
                DiaryEntry.user_id    == user_id,
                DiaryEntry.entry_date == today,
            ).count()

            if count > 0:
                processed_users.add(user_id)
                continue

            # Calcular days_since_last_entry
            last_entry = (
                db.query(DiaryEntry)
                .filter(DiaryEntry.user_id == user_id, DiaryEntry.entry_date < today)
                .order_by(DiaryEntry.entry_date.desc())
                .first()
            )
            if last_entry:
                days_since = (today - last_entry.entry_date).days
                last_date  = str(last_entry.entry_date)
            else:
                days_since = 0
                last_date  = None

            logger.info(f"Sin entradas hoy para user {user_id} (last={last_date})")
            _no_entry_today_cache[dedup_key] = today_str
            processed_users.add(user_id)

            _try_dispatch(
                "on_no_entry_logged_today",
                user_id=user_id,
                days_since_last=days_since,
                last_entry_date=last_date,
                db=db,
            )

    except Exception as e:
        logger.error(f"job_check_no_entry_today error: {e}")
    finally:
        db.close()


def job_check_logging_streak() -> None:
    """
    Runs daily at 00:05 UTC. Para cada automation activa con trigger_ref=macro_tracker.logging_streak:
    1. Extraer streak_days del config del nodo trigger
    2. Dedup: (user_id, streak_days, today_str)
    3. Computar racha hacia atrás desde AYER (hoy puede estar incompleto a las 00:05)
       Ventana limitada a streak_days+1 días para eficiencia
    4. Despachar solo si racha == target (coincidencia exacta)
    """
    from datetime import datetime, timezone
    db = SessionLocal()
    try:
        from app.modules.automations_engine.models.automation import Automation
        from .diary_entry import DiaryEntry

        now       = datetime.now(timezone.utc)
        today     = now.date()
        today_str = str(today)
        yesterday = today - timedelta(days=1)

        automations = db.query(Automation).filter(
            Automation.trigger_ref == "macro_tracker.logging_streak",
            Automation.is_active   == True,
        ).all()

        # Cache de racha por usuario para evitar recalcular
        streak_cache: dict = {}        # user_id -> streak_count
        streak_start_cache: dict = {}  # user_id -> streak_start_date str

        for automation in automations:
            user_id = automation.user_id

            flow         = automation.flow or {}
            nodes        = flow.get("nodes", [])
            trigger_node = next((n for n in nodes if n.get("type") == "trigger"), None)
            config       = trigger_node.get("config", {}) if trigger_node else {}
            target_streak = int(config.get("streak_days", 0))

            if not target_streak:
                continue

            # Dedup
            dedup_key = (user_id, target_streak, today_str)
            if _logging_streak_cache.get(dedup_key) == today_str:
                continue

            # Calcular racha (limitada a target_streak+1 días para eficiencia)
            if user_id not in streak_cache:
                lookback_start = yesterday - timedelta(days=target_streak)
                entries = db.query(DiaryEntry.entry_date).filter(
                    DiaryEntry.user_id    == user_id,
                    DiaryEntry.entry_date >= lookback_start,
                    DiaryEntry.entry_date <= yesterday,
                ).distinct().all()

                logged_dates = set(e.entry_date for e in entries)

                streak = 0
                d = yesterday
                while d >= lookback_start and d in logged_dates:
                    streak += 1
                    d -= timedelta(days=1)

                streak_start = (
                    str(yesterday - timedelta(days=streak - 1)) if streak > 0 else str(yesterday)
                )
                streak_cache[user_id]       = streak
                streak_start_cache[user_id] = streak_start
            else:
                streak       = streak_cache[user_id]
                streak_start = streak_start_cache[user_id]

            if streak != target_streak:
                continue

            logger.info(f"Racha de {streak} días para user {user_id} (start={streak_start})")
            _logging_streak_cache[dedup_key] = today_str

            _try_dispatch(
                "on_logging_streak",
                user_id=user_id,
                streak_days=streak,
                streak_start_date=streak_start,
                db=db,
            )

    except Exception as e:
        logger.error(f"job_check_logging_streak error: {e}")
    finally:
        db.close()
