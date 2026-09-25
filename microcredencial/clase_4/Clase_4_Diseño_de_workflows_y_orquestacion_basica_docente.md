# Machete Docente — Clase 4: Diseño de Workflows y Orquestación Básica

**Microcredencial #2 · Unidad 2 · Clase 4 de 8**

---

## Planificación de tiempos

| Bloque | Duración sugerida | Objetivo del bloque |
|---|---|---|
| Bloque 1 | 15 min | De llamada aislada a flujo — el diagnóstico |
| Bloque 2 | 40 min | Cadenas, plantillas, salidas estructuradas y criterios de framework |
| Bloque 3 | 30 min | Herramientas (tools) y la diferencia con agentes |
| Bloque 4 | 55 min | Laboratorio: primer workflow ejecutable |
| Cierre | 10 min | Hito 1, repaso y conexión con Clase 5 |

---

## Bloque 1 — Guion rápido (15 min)

- Retomar el prototipo de Clase 3 (una sola llamada) y preguntar: "¿qué le falta a esto para ser un sistema real?" — dejar que el grupo llegue solo a "necesita más de un paso".
- Dibujar en el pizarrón el flujo de 4 pasos del teórico.

---

## Bloque 2 — Cadenas y frameworks (40 min)

- Explicar el patrón `plantilla | modelo | parser` con un ejemplo simple en vivo (15 min).
- Criterios para elegir framework (10 min) — frase ancla: "empezar por la opción más simple que resuelva el problema, no la más nueva."
- Diferenciar brevemente LangChain (cadenas fijas, hoy) de LangGraph (decisiones dinámicas, Clase 6) — sin entrar en código de LangGraph todavía (15 min).

**Cuidado:** no mezclar conceptualmente "cadena" con "agente" en esta clase — remarcar que hoy el orden de pasos lo fija el desarrollador, no el modelo. Esa distinción es la base de la Clase 6.

---

## Bloque 3 — Herramientas (30 min)

- Mostrar una función Python simple como "herramienta" (ej. `consultar_stock_tela`) y explicar que hoy se llama en un paso fijo del workflow.
- Puntos de control: preguntar al grupo "¿en qué paso de onboarding de Ortelana debería intervenir un humano?" — recoger 2-3 respuestas antes de dar la propia (caso de CUIT inválido o categoría dudosa).

---

## Bloque 4 — Laboratorio (55 min)

- Dar el esqueleto de `workflow_onboarding()` del teórico y pedir que cada grupo lo complete o adapte a su caso propio.
- Pedir explícitamente que prueben al menos un caso que debe fallar (CUIT inválido) y uno que debe completarse.
- Últimos 15 minutos: cada grupo actualiza su diagrama de arquitectura (de la Clase 2) agregando los pasos del workflow.

**Si el grupo tiene bajo dominio técnico:** proveer el workflow ya armado en un notebook y que solo ajusten los datos de prueba y el punto de validación — se evalúa el diseño del flujo y los puntos de control, no la sintaxis de LangChain.

---

## Cierre (10 min)

- Repasar el resumen.
- Confirmar el **Hito 1**: workflow básico ejecutable + diagrama actualizado, sobre el caso propio.
- Anticipar Clase 5: "el workflow de hoy solo usa lo que el modelo ya sabe. La próxima clase le damos datos reales para que no invente — eso es grounding y RAG."

---

## Notas para el docente

- El Hito 1 es el primer entregable formal ponderado del curso — recordarlo explícitamente al grupo, no dejarlo solo como mención al pasar.
- Si algún grupo ya intenta hacer que el modelo "decida" qué paso seguir, no corregirlo como error — es una buena entrada natural para presentar el gancho de la Clase 6 ("eso que están haciendo intuitivamente es exactamente un agente, lo formalizamos en dos clases").
