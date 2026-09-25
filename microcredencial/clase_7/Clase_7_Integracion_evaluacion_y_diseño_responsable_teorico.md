# Clase 7: Integración, Evaluación y Diseño Responsable

**Programa:** Microcredencial #2 — Diseño de Aplicaciones Inteligentes
**Unidad 3 · Diseño de Proyectos con IA**

**Objetivo técnico:** Integrar los componentes construidos hasta ahora (concepto, workflow, RAG, agente) en un recorrido de punta a punta, aplicar criterios de calidad y trazabilidad mínima, incorporar al menos un guardrail de diseño responsable, y elegir una forma simple de empaquetar el prototipo.

**Origen reutilizado:** Recorte de IADS 3, Unidad 6; clases 11 a 13 y 15. Observabilidad y despliegue se tratan como **criterios de calidad**, no como especialización técnica de AIOps: no se espera que el grupo levante Docker, FastAPI en producción ni un stack completo de monitoreo — se espera que sepan *qué* se debería medir y controlar, y lo apliquen a nivel de prototipo.

---

## Estructura de la clase

| Bloque | Contenido |
|---|---|
| **Bloque 1** | Criterios de calidad de un sistema con IA |
| **Bloque 2** | Trazabilidad mínima: qué registrar y por qué |
| **Bloque 3** | Guardrails de diseño responsable: PII, sesgo, seguridad y límites de uso |
| **Bloque 4** | Laboratorio: integración de punta a punta + matriz de pruebas |
| **Cierre** | Versión candidata del proyecto y conexión con Clase 8 |

---

## Bloque 1: Criterios de calidad de un sistema con IA

Hasta la Clase 6 construimos piezas: un concepto validado, un workflow, un RAG, un agente. Hoy estas piezas se juntan en **un solo recorrido de punta a punta**, y ese recorrido se evalúa con criterios de calidad, no solo con "¿funciona la demo?".

| Criterio | Pregunta que responde |
|---|---|
| **Utilidad** | ¿Resuelve el problema real que identificamos en la Clase 1? |
| **Corrección** | ¿La respuesta es precisa frente a los datos reales? |
| **Fidelidad** | ¿La respuesta se basa en el contexto recuperado o inventa? |
| **Robustez** | ¿Qué pasa ante un input ambiguo, hostil o fuera de dominio? |
| **Latencia** | ¿Responde en un tiempo razonable para el usuario? |
| **Costo** | ¿Cuánto cuesta cada consulta, aproximadamente? |

> Un prototipo que se ve bien en una demo controlada pero no resiste estos seis criterios no está listo — está maquillado. El objetivo de esta clase es someter el proyecto de cada grupo a esa prueba antes de la defensa final.

---

## Bloque 2: Trazabilidad mínima

En producción real, un sistema de IA necesita poder explicar qué pasó y por qué. La observabilidad completa se apoya en tres pilares — **logs** (qué pasó), **métricas** (cuánto pasó) y **trazas** (cómo pasó) — pero para el nivel de esta microcredencial alcanza con una versión mínima de cada uno, no un stack de observabilidad completo:

- **Logs de eventos:** un registro simple de qué consulta entró, qué respondió el sistema y cuánto tardó (puede ser un archivo, una lista en memoria o un print estructurado — no hace falta un sistema de logging productivo).
- **Versionado de prompts:** guardar qué versión del prompt (o system prompt) se usó al obtener cada resultado, para poder comparar antes/después cuando se lo mejora.
- **Registro de pruebas:** un documento simple con las preguntas de prueba usadas y si la respuesta fue correcta, parcial o incorrecta.

```python
# Ejemplo mínimo de registro — no requiere infraestructura de producción
registro = {
    "consulta": pregunta,
    "respuesta": respuesta,
    "duracion_seg": duracion,
    "version_prompt": "v2_blindado",
    "resultado": "correcto",  # correcto | parcial | incorrecto
}
```

> **Por qué importa incluso en un prototipo:** sin ningún registro, no hay forma de defender frente a la pregunta "¿cómo saben que esto funciona?" en la Clase 8. Con tres o cuatro registros simples, ya hay evidencia.

---

## Bloque 3: Guardrails de diseño responsable

Un sistema elocuente que inventa con confianza es más peligroso que uno honesto que dice "no sé". Cuatro guardrails mínimos, aplicables sin infraestructura pesada:

### 1. Anclaje al contexto (ya construido en Clase 5)

Reforzar la instrucción "responder únicamente con el contexto provisto" y el fallback "no tengo información sobre eso" — la primera línea de defensa contra la alucinación.

### 2. Privacidad y PII

Si el sistema maneja datos sensibles (nombres, documentos de identidad, datos de salud, datos financieros), el prototipo debe al menos **evitar exponer esos datos en la respuesta** cuando no corresponde. No hace falta un framework de detección automática — alcanza con una regla simple de "no repetir el dato completo en la respuesta" o enmascararlo manualmente en los casos de prueba.

> **Extensión simple si el sistema tiene más de un tipo de usuario:** no todos deberían ver lo mismo. Si el caso propio distingue, por ejemplo, un rol interno (que puede ver costos) de uno externo (que no debería verlos), alcanza con ajustar el system prompt según quién consulta — sin necesidad de un sistema de permisos completo.

### 3. Sesgo — una revisión simple, no exhaustiva

Probar la misma consulta con variaciones superficiales (distinto registro de lenguaje, distinto origen geográfico simulado, distinto género en el nombre) y verificar que la calidad de la respuesta no cambie de forma injusta. No se espera una batería de tests estadísticos — alcanza con 2-3 comparaciones documentadas.

### 4. Seguridad ante manipulación (prompt injection)

Retomar el Red Teaming de la Clase 5-6: probar al menos un intento de manipulación (un usuario que intenta que el sistema confirme un descuento, un dato falso o una instrucción que contradice las reglas de negocio) y verificar que el guardrail lo rechaza.

### Opciones de empaquetado del prototipo

No hace falta desplegar un servicio de producción para defender el proyecto. Tres niveles válidos, de más simple a más completo:

| Nivel | Formato | Cuándo alcanza |
|---|---|---|
| **Notebook** | Un Colab o Jupyter que corre de punta a punta | Suficiente para la mayoría de los proyectos de esta microcredencial |
| **Interfaz simple** | Un front mínimo (Streamlit, Gradio o similar) | Si el grupo quiere una demo más visual |
| **Endpoint FastAPI** | Una API real, aunque sea corriendo localmente | Opcional — para grupos con más dominio técnico que quieran ir un paso más allá |

> La elección del empaquetado no cambia la evaluación de fondo: lo que se evalúa es el diseño, la integración y la evidencia — no la infraestructura.

---

## Bloque 4: Laboratorio — Integración de punta a punta

### Consigna

1. Integrar en un único recorrido ejecutable los componentes de las Clases 2 a 6 sobre el caso propio: concepto → workflow → RAG → agente.
2. Elegir el empaquetado (notebook, interfaz simple o endpoint).
3. Diseñar una **matriz de pruebas** de al menos 5 casos, cubriendo: una consulta típica, una consulta con sinónimos/jerga, una consulta fuera de dominio, un intento de manipulación y un caso límite propio del dominio.
4. Aplicar al menos un guardrail de los cuatro del Bloque 3 y documentar el resultado.
5. Redactar una **ficha de riesgos y controles**: qué puede fallar, con qué probabilidad/impacto, y qué control mitiga cada riesgo.

### Plantilla de matriz de pruebas

```markdown
| # | Consulta | Tipo | Resultado esperado | Resultado obtenido | ¿Correcto? |
|---|---|---|---|---|---|
| 1 | ... | Típica | ... | ... | |
| 2 | ... | Sinónimos/jerga | ... | ... | |
| 3 | ... | Fuera de dominio | "No tengo información" | ... | |
| 4 | ... | Intento de manipulación | Rechaza / no confirma | ... | |
| 5 | ... | Caso límite del dominio | ... | ... | |
```

---

## Cierre y entrega

### Resumen de la clase

- Un sistema se evalúa con seis criterios: **utilidad, corrección, fidelidad, robustez, latencia y costo** — no solo con "funciona en la demo".
- La **trazabilidad mínima** (logs simples, versión de prompt, registro de pruebas) es indispensable incluso en un prototipo.
- Cuatro **guardrails** cubren lo esencial del diseño responsable: anclaje al contexto, privacidad/PII, revisión de sesgo y resistencia a manipulación.
- El **empaquetado** (notebook, interfaz simple o endpoint) es una decisión secundaria — lo evaluable es el diseño, no la infraestructura.

### Evidencia / entrega de la clase

**Versión candidata del proyecto final:** prototipo integrado de punta a punta, matriz de pruebas y ficha de riesgos/controles.

### Herramientas usadas

Logs propios o notebook con registro simple · Guardrails de prompt · FastAPI opcional

### Conexión con Clase 8

El proyecto ya está integrado y probado. En la Clase 8 se prepara y ejecuta la defensa: cómo explicar la solución, demostrar el flujo principal, presentar evidencia de validación y responder preguntas técnicas y éticas sobre las decisiones tomadas.

---

## Bibliografía de la clase

- Huyen, C. (2025). *AI Engineering: Building Applications with Foundation Models.* O'Reilly. Capítulos 9-11 (lectura de referencia, no evaluable en profundidad técnica).
- OWASP LLM Top 10 (2023). *Top 10 risks for LLM applications* — owasp.org (referencia conceptual de riesgos).
