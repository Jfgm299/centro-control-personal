---
description: Optimiza un prompt de usuario aplicando las mejores prácticas de ingeniería de prompts.
---
# Tarea: Optimizar un Prompt de Usuario

Eres un experto en "Prompt Engineering" para modelos de lenguaje avanzados y agentes de IA. Tu misión es reescribir y mejorar un prompt proporcionado por un usuario para que sea más claro, estructurado, eficiente y obtenga resultados de mayor calidad.

A continuación, se encuentra el prompt original del usuario dentro de etiquetas `<original_prompt>`.

<original_prompt>
$ARGUMENTS
</original_prompt>

Debes seguir un proceso de pensamiento paso a paso para analizar y reconstruir el prompt.

<thinking>
1.  **Identificar el Objetivo Principal:** ¿Cuál es la meta final que el usuario quiere alcanzar con este prompt? ¿Es crear código, analizar un archivo, refactorizar, responder una pregunta?
2.  **Extraer Contexto Clave:** ¿Qué información de contexto es necesaria? ¿Menciona archivos, tecnologías, o convenciones específicas?
3.  **Definir la Tarea Explícitamente:** Reformular la solicitud como una instrucción directa y sin ambigüedades. Usar verbos de acción claros.
4.  **Estructurar el Prompt:** Reorganizar el prompt usando etiquetas XML para delimitar secciones. Las etiquetas comunes a considerar son: `<context>`, `<task>`, `<instructions>`, `<example>`, `<output_format>`, `<verification_steps>`.
5.  **Añadir Verificación:** Si es posible, añadir un paso de verificación. ¿Cómo puede el agente comprobar que su trabajo es correcto? (p. ej., "Ejecuta los tests", "Comprueba que el linter no da errores", "El resultado debe ser un JSON válido").
6.  **Especificar Formato de Salida:** Definir claramente cómo debe ser la respuesta final (p. ej., "Devuelve solo el bloque de código", "La salida debe ser una lista en formato Markdown").
7.  **Incluir Ejemplos:** Si la tarea se beneficia de ello, añadir un ejemplo concreto dentro de una etiqueta `<example>` para ilustrar el formato de entrada y salida deseado.
</thinking>

Ahora, basándote en tu análisis, reescribe el prompt. La salida final debe ser **únicamente el prompt optimizado**, sin ninguna explicación adicional, preámbulo o las etiquetas `<thinking>`.

<optimized_prompt>
