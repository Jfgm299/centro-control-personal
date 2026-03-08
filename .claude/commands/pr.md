Crea un Pull Request para la rama actual:

1. Revisa los commits desde `main`: `git log main..HEAD --oneline`
2. Revisa el diff completo: `git diff main..HEAD`
3. Asegúrate de que la rama tiene un nombre válido (`feat/`, `fix/`, `chore/`)
4. Haz push si no está en remoto: `git push -u origin HEAD`
5. Crea el PR con `gh pr create`:
   - **Título:** conciso, en imperativo, < 70 caracteres
   - **Body:** incluye qué hace, por qué, y cómo probarlo

**Template del body:**
```
## ¿Qué hace este PR?
<descripción breve>

## Cambios principales
-

## Cómo probar
- docker-compose exec api pytest app/modules/<mod>/tests -v

## Notas
<migraciones pendientes, breaking changes, dependencias, etc.>
```
