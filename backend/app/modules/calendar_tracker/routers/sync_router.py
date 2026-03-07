"""
Endpoints de sincronización con calendarios externos.

GET  /calendar/integrations/                        — listar conexiones activas
POST /calendar/integrations/google/connect          — iniciar OAuth Google
GET  /calendar/integrations/google/callback         — callback OAuth Google
POST /calendar/integrations/apple/connect           — conectar Apple CalDAV
DELETE /calendar/integrations/{provider}/disconnect — desconectar
POST /calendar/integrations/{provider}/sync         — sync manual
GET  /calendar/integrations/{provider}/logs         — historial de syncs
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core import get_db
from app.core.dependencies import get_current_user
from app.modules.calendar_tracker.schemas.sync_schema import (
    AppleConnectRequest,
    CalendarConnectionResponse,
    SyncLogResponse,
    ManualSyncResponse,
)
from app.modules.calendar_tracker.services.sync_service import sync_service
from app.modules.calendar_tracker.integrations.google.auth import authorize_url, exchange_code
from app.modules.calendar_tracker.integrations.apple.auth import validate_credentials

router = APIRouter(prefix="/integrations", tags=["Calendar Integrations"])


@router.get("/", response_model=list[CalendarConnectionResponse])
def list_connections(
    db:           Session = Depends(get_db),
    current_user          = Depends(get_current_user),
):
    return sync_service.get_connections(current_user.id, db)


# ── Google ────────────────────────────────────────────────────────────────────

@router.post("/google/connect")
def google_connect(
    current_user = Depends(get_current_user),
):
    """Devuelve la URL de autorización de Google — el cliente redirige al usuario."""
    url = authorize_url(state=str(current_user.id))
    return {"auth_url": url}


@router.get("/google/callback")
def google_callback(
    code:         str,
    state:        str | None = None,
    sync_events:  bool       = True,
    sync_routines: bool      = True,
    calendar_id:  str | None = None,
    db:           Session    = Depends(get_db),
    current_user             = Depends(get_current_user),
):
    """Callback OAuth — intercambia el code por tokens y guarda la conexión."""
    try:
        tokens = exchange_code(code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error OAuth Google: {e}")

    connection = sync_service.create_google_connection(
        user_id       = current_user.id,
        access_token  = tokens["access_token"],
        refresh_token = tokens["refresh_token"],
        expires_at    = tokens["expires_at"],
        calendar_id   = calendar_id,
        sync_events   = sync_events,
        sync_routines = sync_routines,
        db            = db,
    )
    return CalendarConnectionResponse.model_validate(connection)


# ── Apple ─────────────────────────────────────────────────────────────────────

@router.post("/apple/connect", response_model=CalendarConnectionResponse)
def apple_connect(
    body:         AppleConnectRequest,
    db:           Session = Depends(get_db),
    current_user           = Depends(get_current_user),
):
    """Conecta Apple Calendar via CalDAV con app-specific password."""
    if not validate_credentials(body.username, body.password):
        raise HTTPException(status_code=401, detail="Credenciales de Apple inválidas")

    connection = sync_service.create_apple_connection(
        user_id       = current_user.id,
        username      = body.username,
        password      = body.password,
        calendar_id   = body.calendar_id,
        sync_events   = body.sync_events,
        sync_routines = body.sync_routines,
        db            = db,
    )
    return CalendarConnectionResponse.model_validate(connection)


# ── Compartidos ───────────────────────────────────────────────────────────────

@router.delete("/{provider}/disconnect")
def disconnect(
    provider:     str,
    db:           Session = Depends(get_db),
    current_user           = Depends(get_current_user),
):
    if provider not in ("google", "apple"):
        raise HTTPException(status_code=400, detail="Provider inválido")

    success = sync_service.disconnect(current_user.id, provider, db)
    if not success:
        raise HTTPException(status_code=404, detail="Conexión no encontrada")
    return {"disconnected": True, "provider": provider}


@router.post("/{provider}/sync", response_model=ManualSyncResponse)
def manual_sync(
    provider:     str,
    db:           Session = Depends(get_db),
    current_user           = Depends(get_current_user),
):
    if provider not in ("google", "apple"):
        raise HTTPException(status_code=400, detail="Provider inválido")

    connection = sync_service.get_connection(current_user.id, provider, db)
    if not connection:
        raise HTTPException(status_code=404, detail=f"No hay conexión activa con {provider}")

    log = sync_service.sync(connection, db)
    return ManualSyncResponse(
        provider        = log.provider,
        direction       = log.direction,
        events_created  = log.events_created,
        events_updated  = log.events_updated,
        events_deleted  = log.events_deleted,
        routines_synced = log.routines_synced,
        error           = log.error,
    )


@router.get("/{provider}/logs", response_model=list[SyncLogResponse])
def get_logs(
    provider:     str,
    db:           Session = Depends(get_db),
    current_user           = Depends(get_current_user),
):
    if provider not in ("google", "apple"):
        raise HTTPException(status_code=400, detail="Provider inválido")

    return sync_service.get_logs(current_user.id, provider, db)