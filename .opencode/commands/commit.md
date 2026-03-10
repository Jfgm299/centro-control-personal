---
description: Analiza los cambios, crea una rama y propone un commit para aprobación.
---
# Tarea: Crear un Commit con Aprobación del Usuario

Tu tarea es gestionar el proceso de crear un commit de manera segura y siguiendo las convenciones del proyecto. No debes hacer push a remoto.

**Convenciones de Commit del Proyecto:**
Este proyecto sigue la especificación de **Conventional Commits**. El formato del mensaje debe ser:
`<tipo>(<scope-opcional>): <descripción breve en imperativo>`

Los tipos de commit más comunes que debes usar son:
- `feat:` Nuevas funcionalidades.
- `fix:` Correcciones de errores.
- `refactor:` Cambios en el código que no alteran la funcionalidad.
- `test:` Añadir o modificar tests.
- `docs:` Cambios en la documentación.
- `chore:` Tareas de mantenimiento (actualizar dependencias, etc.).

**Proceso a seguir:**

1.  **Verificar Necesidad de Actualizar Documentación (Paso Crítico):**
    - Primero, analiza los cambios (`git diff develop..HEAD --name-only`) para ver si se ha modificado código en archivos clave como `models/`, `routers/`, `schemas/`, `module_loader.py`, etc.
    - **Si** los cambios son significativos y requieren una actualización de la documentación, **detente y pide permiso explícito al usuario antes de continuar.**
    - Usa un mensaje claro:
      > "He detectado cambios en el código que probablemente requieran una actualización de la documentación. ¿Me das tu autorización para analizar y actualizar los archivos en `.claude/docs/` ahora mismo?"
    - **No continúes con el commit hasta que recibas una respuesta.**
      - Si la respuesta es afirmativa, ejecuta el proceso de actualización de documentos.
      - Si la respuesta es negativa, continúa con el proceso de commit, pero advierte al usuario que la documentación podría quedar desactualizada.
    - Si los cambios no requieren actualizar la documentación, continúa directamente al siguiente paso.

2.  **Analizar Cambios para el Commit:**
    - Revisa todos los cambios (staged, unstaged y untracked) para comprender la naturaleza completa del trabajo a commitear.

3.  **Verificar y Crear Rama:**
    - Comprueba la rama actual. Si es `main` o `develop`, crea una nueva rama descriptiva (p. ej., `feat/new-auth-flow`). De lo contrario, continúa en la rama actual.

4.  **Proponer Mensaje de Commit:**
    - Redacta un mensaje de commit claro y conciso que siga el estándar de Conventional Commits.

5.  **Pedir Aprobación Explícita para el Commit:**
    - **Paso más importante:** Presenta el mensaje de commit redactado y pregunta al usuario si procede.
      > He analizado los cambios y he preparado el siguiente mensaje de commit:
      >
      > ```
      > feat(auth): Implementar sistema de autenticación de dos factores
      > ```
      >
      > ¿Procedo con el commit en la rama `feat/auth-2fa`?

6.  **Ejecutar el Commit (SOLO si se aprueba):**
    - Solo tras la aprobación explícita del usuario, añade todos los cambios y ejecuta el commit.
      ```bash
      git add .
      git commit -m "El mensaje de commit aprobado"
      ```
