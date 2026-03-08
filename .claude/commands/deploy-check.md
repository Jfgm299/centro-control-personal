Checklist de pre-deploy. Revisa punto por punto antes de hacer merge a main:

## 1. Tests
```bash
docker-compose exec api pytest
```
Todos deben pasar. Si hay fallos, NO hacer deploy.

## 2. Migraciones
```bash
docker-compose exec api alembic upgrade head
docker-compose exec api alembic current
```
- ¿El `current` apunta al head esperado?
- ¿Hay migraciones pendientes que no se han generado para cambios de modelo?

## 3. Generar migración si hay cambios de modelo
```bash
docker-compose exec api alembic revision --autogenerate -m "descripcion"
```
Revisar el archivo generado — confirmar que solo toca las tablas esperadas.

## 4. Variables de entorno
- ¿Todas las vars nuevas están en `.env.example`?
- ¿Están configuradas en staging/prod?

## 5. Revisión de seguridad rápida
- ¿Ningún endpoint nuevo expone datos de otro usuario? (ownership checks)
- ¿No hay credenciales hardcodeadas?
- ¿Los handlers de excepción cubren los nuevos errores?

## 6. Si hay cambio en el automation contract
- ¿Se actualizó `automation_registry.py` del módulo?
- ¿Los handlers nuevos siguen el contrato `(payload, config, db, user_id) -> dict`?

## 7. Documentación
- ¿Los docs en `.claude/docs/` reflejan los cambios?
- Si añadiste modelo, endpoint, módulo nuevo, o automation handler — ejecuta `/update-docs` para actualizar los `.md` correspondientes.
