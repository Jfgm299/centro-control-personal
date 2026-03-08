Ejecuta los tests del proyecto. Usa el argumento proporcionado para determinar el alcance:

- Sin argumento → suite completa:
  ```bash
  docker-compose exec api pytest
  ```

- Nombre de módulo (ej: `gym_tracker`) → tests del módulo:
  ```bash
  docker-compose exec api pytest app/modules/$ARGUMENTO/tests -v
  ```

- Ruta de archivo (ej: `calendar_tracker/tests/test_sync.py`) → archivo específico:
  ```bash
  docker-compose exec api pytest app/modules/$ARGUMENTO -v
  ```

- Clase o función (ej: `test_sync.py::TestAppleIntegration`) → test específico:
  ```bash
  docker-compose exec api pytest app/modules/$ARGUMENTO -v
  ```

Tras ejecutar, resume: cuántos pasaron, cuántos fallaron, y si hay fallos muestra el error relevante.
