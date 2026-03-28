# travels_tracker

Schema: `travels_tracker` | Automation contract: ❌

Módulo de seguimiento de viajes con soporte para fotos almacenadas en Cloudflare R2.

## Models

| Model | Table | Descripción |
|-------|-------|-------------|
| `Trip` | `travels_tracker.trips` | Viaje (contenedor principal) |
| `Album` | `travels_tracker.albums` | Álbum de fotos dentro de un viaje |
| `Photo` | `travels_tracker.photos` | Foto individual (metadatos + referencia a R2) |
| `Activity` | `travels_tracker.activities` | Actividad dentro de un viaje |

## User Relationships

```python
user.trips  # List[Trip]
```

## Storage: Cloudflare R2 (NO es S3)

Las fotos se almacenan en **Cloudflare R2**. Se usa `boto3` con el endpoint de R2 (`https://<account_id>.r2.cloudflarestorage.com`). La interfaz es compatible con S3 pero el backend es R2.

```python
# storage_service.py — cómo se inicializa el cliente
self.client = boto3.client(
    "s3",
    endpoint_url=f"https://{R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
    aws_access_key_id=R2_ACCESS_KEY_ID,
    aws_secret_access_key=R2_SECRET_ACCESS_KEY,
    config=Config(signature_version="s3v4"),
    region_name="auto",
)
```

El modelo `Photo` guarda:
- `r2_key` — clave del objeto en R2 (path interno)
- `public_url` — URL pública para servir la foto al frontend

## External Dependencies (env vars vía `get_settings()`)

> **Nota Railway:** `manifest.get_settings()` usa `os.environ` como fuente primaria. Ver patrón en `patterns.md`.



| Variable | Descripción |
|----------|-------------|
| `R2_ACCOUNT_ID` | ID de cuenta Cloudflare |
| `R2_ACCESS_KEY_ID` | Access key de R2 |
| `R2_SECRET_ACCESS_KEY` | Secret key de R2 |
| `R2_BUCKET_NAME` | Nombre del bucket |
| `R2_PUBLIC_URL` | URL pública base para servir archivos |

## Structure

```
travels_tracker/
├── manifest.py           ← get_settings() con todas las vars R2
├── models/               ← trip.py, album.py, photo.py, activity.py
├── schemas/
├── routers/
├── services/
│   ├── trip_service.py
│   ├── album_service.py
│   ├── photo_service.py
│   ├── activity_service.py
│   └── storage_service.py  ← gestiona uploads/deletes en R2
├── enums/
├── exceptions/
├── handlers/
└── tests/
```
