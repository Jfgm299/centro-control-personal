# calendar_tracker

Schema: `calendar_tracker` | Automation contract: ✅ (implementación de referencia)

Módulo de calendario con eventos, recordatorios, rutinas, notificaciones push (Firebase), y sincronización con Google Calendar y Apple Calendar. Es el módulo más complejo y la implementación de referencia del automation contract.

## Models

| Model | Table | Descripción |
|-------|-------|-------------|
| `Event` | `calendar_tracker.events` | Evento de calendario |
| `Reminder` | `calendar_tracker.reminders` | Recordatorio con prioridad y fecha de vencimiento |
| `Routine` | `calendar_tracker.routines` | Evento recurrente |
| `RoutineException` | `calendar_tracker.routine_exceptions` | Excepción a una rutina (ej: día cancelado) |
| `Category` | `calendar_tracker.categories` | Categoría de evento/recordatorio |
| `Notification` | `calendar_tracker.notifications` | Notificación push pendiente/enviada |
| `FcmToken` | `calendar_tracker.fcm_tokens` | Token FCM de dispositivo (Firebase) |
| `CalendarConnection` | `calendar_tracker.calendar_connections` | Credenciales de Google/Apple Calendar |
| `SyncLog` | `calendar_tracker.sync_logs` | Log de sincronizaciones |

## User Relationships

```python
user.events               # List[Event]
user.reminders            # List[Reminder]
user.routines             # List[Routine]
user.calendar_categories  # List[Category]
user.notifications        # List[Notification]
user.fcm_tokens           # List[FcmToken]
user.calendar_connections # List[CalendarConnection]
user.sync_logs            # List[SyncLog]
```

## External Dependencies

> **Nota Railway:** `manifest.get_settings()` usa `os.environ` como fuente primaria. Ver patrón en `patterns.md`.

| Variable | Descripción |
|----------|-------------|
| `FIREBASE_CREDENTIALS_JSON` | JSON de credenciales Firebase Admin SDK |
| `GOOGLE_CLIENT_ID` | OAuth2 client ID para Google Calendar |
| `GOOGLE_CLIENT_SECRET` | OAuth2 client secret |
| `GOOGLE_REDIRECT_URI` | URI de callback OAuth2 |
| `ENCRYPTION_KEY` | Clave para cifrar tokens OAuth2 en BD |

## Integrations

```
integrations/
├── base.py     ← clase base abstracta CalendarIntegration
├── google/     ← OAuth2 + sync con Google Calendar
└── apple/      ← sync con Apple Calendar (CalDAV)
```

## Services

| Service | Responsabilidad |
|---------|----------------|
| `event_service.py` | CRUD eventos |
| `reminder_service.py` | CRUD recordatorios |
| `routine_service.py` | CRUD rutinas + generación de instancias |
| `category_service.py` | CRUD categorías |
| `notification_service.py` | Envío de push notifications via Firebase |
| `sync_service.py` | Orquesta sync con Google/Apple |
| `scheduler_service.py` | Scheduler de tareas periódicas (APScheduler, arranca desde `startup_event`) |
| `automation_handlers.py` | Handlers del automation contract |

## Automation Contract Implementation

### Triggers registrados

| trigger_ref | Cuándo dispara |
|-------------|---------------|
| `calendar_tracker.event_start` | Al iniciar un evento (con `advance_minutes` configurable) |
| `calendar_tracker.event_end` | Al finalizar un evento |
| `calendar_tracker.reminder_due` | Cuando vence un recordatorio |
| `calendar_tracker.no_events_in_window` | Cuando no hay eventos en ventana futura |
| `calendar_tracker.overdue_reminders_exist` | Cuando existen N+ recordatorios vencidos |

### Acciones registradas

| action_ref | Qué hace |
|------------|----------|
| `calendar_tracker.create_event` | Crea un evento |
| `calendar_tracker.create_reminder` | Crea un recordatorio |
| `calendar_tracker.mark_reminder_done` | Marca recordatorio como completado |
| `calendar_tracker.cancel_event` | Cancela un evento |
| `calendar_tracker.push_summary_overdue` | Construye resumen de recordatorios vencidos |
| `calendar_tracker.get_todays_schedule` | Devuelve eventos del día en el contexto |
| `calendar_tracker.bulk_mark_overdue_done` | Marca en bloque recordatorios vencidos |

### Scheduler (`scheduler_service.py`)

Arranca desde `startup_event` en `main.py` via `start_calendar_scheduler()` (exportado desde `calendar_tracker/__init__.py`). **No se arranca en import-time.**

| Job | Frecuencia | Qué hace |
|-----|-----------|----------|
| `job_check_event_starts` | cada 60s | Detecta eventos en `[now-60s, now+60s]` → dispara `event_start` |
| `job_check_event_ends` | cada 60s | Detecta eventos en `[now-60s, now+60s]` → dispara `event_end` |
| `job_check_reminders_due` | cada 5min | Recordatorios con `due_date == today` → dispara `reminder_due` |
| `job_check_free_windows` | cada 30min | Sin eventos en ventana de 2h → dispara `no_events_in_window` |
| `job_check_overdue_reminders` | diario 9:00 UTC | Recordatorios vencidos → dispara `overdue_reminders_exist` |
| `job_sync_calendars` | cada 10min | Sync con Google/Apple Calendar |
| `job_process_notifications` | cada 60s | Envía notificaciones FCM pendientes |

Los jobs de tiempo puntual (`event_start`, `event_end`, `reminder_due`) tienen **deduplicación en memoria** (`_dispatch_cache`, TTL 5min) para evitar dobles disparos en runs consecutivos del scheduler.

### Dispatcher

`automation_dispatcher.py` contiene `CalendarAutomationDispatcher` — conecta los eventos del scheduler con el motor de automatizaciones. Busca automations activas por `trigger_ref` y las ejecuta via `flow_executor`. Tras cada ejecución actualiza `last_run_at` y `run_count` en el modelo `Automation`.

Ver implementación completa:
- `backend/app/modules/calendar_tracker/automation_registry.py`
- `backend/app/modules/calendar_tracker/automation_dispatcher.py`
- `backend/app/modules/calendar_tracker/services/automation_handlers.py`
