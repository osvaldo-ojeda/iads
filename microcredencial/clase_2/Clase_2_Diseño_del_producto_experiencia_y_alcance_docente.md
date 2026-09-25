# Machete Docente — Clase 2: Diseño del Producto, Experiencia y Alcance

**Microcredencial #2 · Unidad 1 · Clase 2 de 8**

---

## Planificación de tiempos

| Bloque | Duración sugerida | Objetivo del bloque |
|---|---|---|
| Bloque 1 | 25 min | Laboratorio de fallas — mostrar el límite del prompting solo |
| Bloque 2 | 40 min | Dilema técnico, patrón híbrido y matriz de intenciones |
| Bloque 3 | 40 min | User journey, alcance del MVP, priorización |
| Bloque 4 | 40 min | Taller: concepto de solución (Ortelana + caso propio) |
| Cierre | 15 min | Entrega, repaso, conexión con Clase 3 |

---

## Bloque 1 — Guion rápido (25 min)

- Retomar la pregunta abierta de Clase 1 ("¿qué automatizarían primero?") antes de arrancar — conecta las dos clases.
- Dar 10 minutos para que cada grupo pruebe el prompt contra el mensaje de "Modas del Sur" (está en el teórico).
- Puesta en común (10 min): pedir ejemplos concretos de dónde se rompió el formato.

**Cierre obligatorio del bloque, en voz alta:** "Esto no se arregla escribiendo un prompt mejor. Se arregla con código que valide — eso es Clase 3. Hoy nos importa entender *por qué* pasa esto: el modelo no distingue instrucción de manipulación."

---

## Bloque 2 — Dilema técnico (40 min)

Orden sugerido:

1. Tabla determinista vs. probabilístico (10 min) — preguntar en vivo: "¿el CUIT lo valida el LLM o el código?"
2. Patrón híbrido y la analogía del restaurante (10 min).
3. Matriz de mapeo de intenciones (15 min) — completarla en el pizarrón con 3 ejemplos de Ortelana, pidiendo que el grupo proponga la "Acción de backend" y el "Riesgo" antes de revelarlo.
4. Cierre del bloque (5 min): remarcar la regla de oro — "el LLM interpreta, el dato real decide".

**Punto de atención:** si algún grupo propone que el LLM decida directamente si un distribuidor califica para crédito, usarlo como contraejemplo en vivo — es exactamente el error que la regla de oro previene.

---

## Bloque 3 — User journey y MVP (40 min)

- Dibujar el user journey de onboarding de Ortelana en el pizarrón, paso a paso, marcando en cada paso "¿regla o LLM?" con el grupo.
- Explicar alcance del MVP con la frase ancla: "el MVP no es la versión incompleta, es la más chica que ya genera valor real."
- Introducir la matriz valor-esfuerzo-riesgo con un ejemplo rápido: comparar "responder consultas de stock" (alto valor, bajo esfuerzo) vs. "aprobar crédito automáticamente" (alto riesgo) — ¿cuál entra primero al MVP?

---

## Bloque 4 — Taller (40 min)

- Repartir la consigna del Concepto de Solución. Cada grupo trabaja en paralelo sobre Ortelana (como ejercicio guiado) y sobre su caso propio (el que sostiene el proyecto final).
- Circular activamente: el error más común es que el user journey quede sin marcar qué pasos son LLM y cuáles reglas — insistir en esa marca.
- Últimos 10 minutos: puesta en común con 2-3 grupos mostrando su matriz valor-esfuerzo-riesgo.

---

## Cierre (15 min)

- Repasar el resumen de la clase.
- Confirmar la entrega: Concepto de solución (user journey + alcance del MVP + criterios de éxito) sobre el caso propio.
- Anticipar Clase 3: "ya sabemos qué construir y qué parte es LLM. Ahora vamos a construirlo de verdad: prompts confiables + código Python que consume una API real."

---

## Notas para el docente

- Esta clase es la más "conceptual" de la Unidad 1 antes de entrar a código — si el grupo tiene ansiedad por no haber tocado Python todavía, tranquilizar: "todo lo de hoy es el plano; en la Clase 3 empezamos a construir sobre este plano."
- No es necesario que la matriz de intenciones tenga más de 3-4 filas para el MVP — el objetivo es que entiendan el mecanismo, no que cubran todos los casos posibles.
- El "Concepto de solución" de hoy es la base directa del Brief técnico que se profundiza en Clase 3 — dejarlo guardado y accesible para retomarlo la próxima clase.
