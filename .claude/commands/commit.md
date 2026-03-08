Genera un commit siguiendo las convenciones del proyecto:

1. Revisa los cambios con `git diff --staged` y `git status`
2. Escribe un mensaje siguiendo **Conventional Commits**:
   - `feat:` nueva funcionalidad
   - `fix:` corrección de bug
   - `chore:` mantenimiento, deps, config
   - `docs:` documentación
   - `test:` tests
   - `refactor:` refactoring sin cambio de comportamiento
3. Formato: `<tipo>(<scope-opcional>): <descripción breve en imperativo>`
4. Si hay contexto relevante, añade un cuerpo con una línea en blanco de separación
5. Ejecuta el commit

**Reglas:**
- Nunca usar `--no-verify`
- Nunca commitear `.env` ni archivos con credenciales
- Nunca commitear directamente a `main`
