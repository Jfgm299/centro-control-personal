---
description: Analiza los cambios recientes y actualiza la documentación para reflejar el estado actual.
---
# Tarea: Actualizar la Documentación del Proyecto

Tu misión es analizar los cambios recientes en el código y actualizar la documentación correspondiente en el directorio `.claude/docs/` para que siempre esté sincronizada.

## Proceso a seguir

1.  **Identificar qué cambió:**
    - Ejecuta `git diff develop..HEAD --name-only` para obtener una lista de todos los archivos modificados desde la última sincronización con `develop`.

2.  **Determinar qué documentación se ve afectada:**
    - Usa la siguiente tabla de correspondencia para decidir qué archivos de documentación necesitas editar:

   | Si cambió...                                    | Actualizar...                                                                    |
   | ----------------------------------------------- | -------------------------------------------------------------------------------- |
   | `app/modules/<mod>/models/`                     | `.claude/docs/modules/<mod>.md` — sección Models                               |
   | `app/modules/<mod>/routers/`                    | `.claude/docs/modules/<mod>.md` — sección Endpoints                            |
   | `app/modules/<mod>/manifest.py`                 | `.claude/docs/modules/<mod>.md` y `.claude/docs/module-system.md`                |
   | `app/modules/<mod>/automation_registry.py`      | `.claude/docs/modules/<mod>.md` — sección Automation Contract                  |
   | `app/core/module_loader.py`                     | `.claude/docs/architecture.md` y `.claude/docs/module-system.md`                |
   | `app/main.py`                                   | `.claude/docs/architecture.md` — Startup Sequence                              |
   | `alembic/versions/`                             | `.claude/docs/database.md` si introduce nuevos patrones                        |
   | Un módulo nuevo (`app/modules/<nuevo_mod>/`) | Crear `.claude/docs/modules/<nuevo_mod>.md` y añadirlo a `.claude/docs/modules/README.md` |

3.  **Leer y Comprender los Cambios:**
    - Lee el contenido de los archivos de código que han cambiado para entender la naturaleza exacta de las modificaciones (nuevos campos, endpoints modificados, etc.).
    - Lee también los archivos de documentación correspondientes para saber qué secciones específicas necesitas actualizar.

4.  **Editar la Documentación:**
    - Actualiza los archivos de documentación de manera precisa y concisa. No reescribas secciones enteras, solo la información que ha cambiado.

5.  **Sincronizar con el Frontend:**
    - **Si** los cambios afectan a la interfaz entre el backend y el frontend (endpoints, schemas Pydantic, etc.), es **crítico** que también actualices el archivo de contexto compartido: `../centro-control-app/.claude/docs/shared-context.md`.

6.  **Confirmar la Actualización:**
    - Al finalizar, informa al usuario de los archivos de documentación que has modificado.
