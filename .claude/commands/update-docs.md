Analiza los cambios recientes y actualiza la documentación en `.claude/docs/` para que refleje el estado actual del código.

## Proceso

1. **Identificar qué cambió:**
   ```bash
   git diff main..HEAD --name-only
   ```

2. **Por cada archivo cambiado, determinar qué doc afecta:**

   | Si cambió... | Actualizar... |
   |---|---|
   | `app/modules/<mod>/models/` | `docs/modules/<mod>.md` — sección Models |
   | `app/modules/<mod>/routers/` | `docs/modules/<mod>.md` — sección Endpoints |
   | `app/modules/<mod>/manifest.py` | `docs/modules/<mod>.md` y `docs/module-system.md` si cambia el contrato |
   | `app/modules/<mod>/automation_registry.py` | `docs/modules/<mod>.md` — sección Automation Contract |
   | `app/core/module_loader.py` | `docs/architecture.md` y `docs/module-system.md` |
   | `app/main.py` | `docs/architecture.md` — Startup Sequence |
   | `alembic/versions/` | `docs/database.md` si introduce nuevos patrones |
   | Nuevo módulo completo | Crear `docs/modules/<mod>.md` y añadir fila en `docs/modules/README.md` |

3. **Leer los archivos afectados** para entender exactamente qué cambió.

4. **Editar los docs** con la información actualizada. Ser preciso — no reescribir secciones que no cambiaron.

5. **Confirmar** qué archivos se actualizaron y qué se cambió en cada uno.

## Cambios que afectan al frontend

Si el cambio afecta a la interfaz backend↔frontend (endpoints nuevos o modificados, cambios en schemas de respuesta, módulos nuevos), actualizar también el `shared-context.md` del repo del frontend (`centro-control-app/.claude/docs/shared-context.md`) para mantenerlo sincronizado.
