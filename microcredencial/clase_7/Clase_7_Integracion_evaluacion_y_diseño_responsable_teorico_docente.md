# Machete Docente — Clase 7: Integración, Evaluación y Diseño Responsable

**Microcredencial #2 · Unidad 3 · Clase 7 de 8**

---

## Planificación de tiempos

| Bloque | Duración sugerida | Objetivo del bloque |
|---|---|---|
| Bloque 1 | 25 min | Criterios de calidad — de "funciona en la demo" a evaluación real |
| Bloque 2 | 25 min | Trazabilidad mínima: logs, versión de prompt, registro de pruebas |
| Bloque 3 | 45 min | Guardrails de diseño responsable + opciones de empaquetado |
| Bloque 4 | 75 min | Laboratorio: integración de punta a punta + matriz de pruebas + ficha de riesgos |
| Cierre | 20 min | Entrega, repaso, conexión con Clase 8 |

---

## Bloque 1 — Guion rápido (25 min)

- Abrir con la pregunta directa: "¿alguien puede mostrar su prototipo funcionando ahora mismo, sin preparar nada antes?" — es normal que la respuesta sea incómoda, es el gancho de la clase.
- Presentar los 6 criterios de calidad en el pizarrón y pedir que cada grupo autoevalúe su proyecto en 1 minuto por criterio (bien / regular / no lo sabemos).

---

## Bloque 2 — Trazabilidad (25 min)

- Insistir en que **no se pide infraestructura de producción** — un log simple en una lista de Python o un archivo de texto alcanza para este nivel.
- Mostrar el ejemplo de registro mínimo del teórico y pedir que cada grupo lo adapte a su caso en 5 minutos.

**Frase ancla:** "sin ningún registro, no hay forma de defender que el sistema funciona — con tres registros simples, ya hay evidencia."

---

## Bloque 3 — Guardrails y empaquetado (45 min)

Orden sugerido:

1. Repasar brevemente el anclaje al contexto (ya visto en Clase 5) — no repetir la teoría completa, solo recordar la frase "únicamente el contexto provisto" (5 min).
2. PII: mostrar un ejemplo simple de qué NO debería aparecer en una respuesta según el dominio de cada grupo (10 min).
3. Sesgo: proponer que cada grupo piense 2 variaciones de la misma consulta para probar en el laboratorio (10 min).
4. Seguridad ante manipulación: retomar el Red Teaming — pedir que recuerden el ataque que usaron en Clase 5-6 (10 min).
5. Opciones de empaquetado — tabla de 3 niveles, remarcar que el notebook alcanza para la mayoría (10 min).

**No profundizar** en Guardrails AI, NeMo Guardrails, Docker ni FastAPI en producción — son herramientas de nivel productivo fuera del alcance de esta microcredencial. Si el grupo tiene el nivel técnico y quiere ir más allá, mencionarlo como "camino opcional", no como expectativa.

---

## Bloque 4 — Laboratorio (75 min)

- Dar 35 minutos para que cada grupo integre sus componentes de las Clases 2-6 en un solo recorrido ejecutable.
- Dar 25 minutos para completar la matriz de pruebas (5 casos mínimo) y aplicar al menos un guardrail.
- Dar 15 minutos para redactar la ficha de riesgos y controles.

**Si el grupo tiene bajo dominio técnico:** aceptar que la integración sea manual/secuencial (correr cada componente por separado y armar el resultado a mano) en lugar de un pipeline totalmente automatizado — lo que se evalúa es que los componentes estén coherentemente conectados y probados, no la automatización completa.

---

## Cierre (20 min)

- Repasar el resumen de la clase.
- Confirmar la entrega: prototipo integrado + matriz de pruebas + ficha de riesgos/controles.
- Anticipar Clase 8: "la próxima clase es la defensa. Hoy generamos la evidencia que van a mostrar ahí."

---

## Notas para el docente

- Esta clase es la más densa de la Unidad 3 en términos de entregables — si el tiempo aprieta, priorizar el Bloque 4 (integración + matriz de pruebas) sobre profundizar la teoría de los Bloques 1-3, que pueden resumirse más si es necesario.
- El objetivo pedagógico central es que cada grupo llegue a la Clase 8 con evidencia concreta (no solo una demo) de que pensaron en calidad, trazabilidad y responsabilidad — remarcarlo explícitamente al cerrar.
