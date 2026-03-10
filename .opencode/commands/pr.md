---
description: Crea un Pull Request para la rama actual, espera aprobación y luego hace merge.
---
# Tarea: Gestionar el Flujo Completo de un Pull Request

Tu misión es automatizar la creación, y posteriormente el merge, de un Pull Request desde la rama de trabajo actual hacia la rama `develop`. El proceso se divide en dos fases principales, cada una requiriendo la **aprobación explícita del usuario**.

---

### FASE 1: Creación del Pull Request

1.  **Verificar Cambios sin Commit:**
    - Ejecuta `git status` para comprobar si hay archivos modificados o sin seguimiento.
    - Si encuentras cambios, **detente** y pregunta al usuario:
      > "He detectado cambios sin commitear. ¿Quieres que los añada en un nuevo commit antes de crear el Pull Request? Responde 'sí' para confirmar o 'no' para continuar sin ellos."
    - **No continúes** hasta recibir una respuesta explícita. Si la respuesta es 'sí', utiliza el flujo del comando `/commit` para crear un commit con los cambios.

2.  **Asegurar que la Rama está Sincronizada:**
    - Obtén el nombre de la rama actual (`git rev-parse --abbrev-ref HEAD`).
    - Haz push de la rama al repositorio remoto para asegurarte de que está actualizada. Usa `git push -u origin HEAD`.

3.  **Analizar Cambios y Redactar el PR:**
    - Revisa los commits hechos en esta rama en comparación con `develop`: `git log develop..HEAD --oneline`.
    - Revisa el diff completo para entender todos los cambios: `git diff develop..HEAD`.
    - Basado en el análisis, redacta un **título** y un **cuerpo** para el Pull Request.
      - **Título:** Debe ser conciso, en imperativo y menor de 70 caracteres.
      - **Cuerpo:** Usa la siguiente plantilla OBLIGATORIA:
        ```
        ## ¿Qué hace este PR?
        <descripción breve y clara de la finalidad del PR>

        ## Cambios principales
        - <Punto 1 del cambio>
        - <Punto 2 del cambio>

        ## Cómo probar
        <Instrucciones claras. Por ejemplo: `docker-compose exec api pytest app/modules/<nombre_modulo>/tests -v`>

        ## Notas
        <Cualquier información adicional: migraciones, breaking changes, etc.>
        ```

4.  **Crear el Pull Request:**
    - Ejecuta el comando de `gh` para crear el PR, asegurándote de que la rama base sea `develop`:
      `gh pr create --base develop --title "<tu-titulo-redactado>" --body "<tu-cuerpo-redactado>"`

5.  **Notificar al Usuario y Esperar Aprobación (FIN DE LA FASE 1):**
    - Muestra la URL del Pull Request creado al usuario.
    - Comunica claramente que estás esperando su revisión y aprobación para la siguiente fase con este mensaje:
      > "He creado el Pull Request. Puedes revisarlo aquí: [URL_DEL_PR]. Por favor, verifica que todo es correcto. **Cuando estés listo, dame tu confirmación explícita para que proceda con el merge y la limpieza de la rama.**"

---

### FASE 2: Merge y Limpieza (Solo tras confirmación explícita)

**NO PROCEDAS a esta fase sin la confirmación del usuario de la Fase 1.**

1.  **Hacer Merge del PR:**
    - Utiliza `gh pr merge <URL_o_número_del_PR> --merge` para hacer merge a `develop`.

2.  **Limpieza de Ramas:**
    - Cambia a la rama `develop`: `git checkout develop`.
    - **IMPORTANTE:** Actualiza tu copia local de `develop` para evitar conflictos futuros: `git pull`.
    - Borra la rama de trabajo localmente: `git branch -d <nombre_de_la_rama>`.
    - Borra la rama de trabajo del repositorio remoto: `git push origin --delete <nombre_de_la_rama>`.

3.  **Confirmar Finalización:**
    - Informa al usuario que el proceso ha finalizado:
      > "Hecho. El PR ha sido mergeado en `develop` y la rama de trabajo ha sido eliminada. Tu rama local `develop` está actualizada."
