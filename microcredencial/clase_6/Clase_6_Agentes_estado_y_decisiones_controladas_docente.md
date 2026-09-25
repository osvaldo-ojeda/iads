# Machete Docente — Clase 6: Agentes, Estado y Decisiones Controladas

**Microcredencial #2 · Unidad 2 · Clase 6 de 8 (cierre de Unidad 2)**

---

## Planificación de tiempos

| Bloque | Duración sugerida | Objetivo del bloque |
|---|---|---|
| Bloque 1 | 25 min | De la cadena al agente — el límite del workflow fijo |
| Bloque 2 | 35 min | Function calling y herramientas — cómo decide el LLM |
| Bloque 3 | 40 min | Estado, memoria mínima, nodos/aristas y control humano |
| Bloque 4 | 55 min | Laboratorio: primer agente con LangGraph |
| Cierre | 15 min | Hito 2, repaso y conexión con Clase 7 |

---

## Bloque 1 — Guion rápido (25 min)

- Retomar el workflow de la Clase 4 y presentar en vivo la consulta de doble verificación (CUIT + stock) del teórico — dejar que el grupo note que un workflow fijo no alcanza sin duplicar código para cada combinación.
- Presentar el ciclo ReAct dibujado en el pizarrón.

**Frase ancla para remarcar:** "una cadena ejecuta, un agente decide."

---

## Bloque 2 — Herramientas (35 min)

- Mostrar 2 herramientas ya escritas (`validar_distribuidor`, `consultar_stock_tela`) y leer los docstrings en voz alta.
- Ejercicio rápido en el pizarrón: tapar el docstring de una y preguntar "¿el agente sabría cuándo usarla?" — mostrar cómo un docstring vago produce decisiones erráticas.

---

## Bloque 3 — Estado y control (40 min)

Orden sugerido:

1. `EstadoAgente` (TypedDict) — explicar `messages` y por qué se necesita un contador de iteraciones (10 min).
2. Nodos y aristas de LangGraph — dibujar el grafo simple (agente ↔ herramientas) en el pizarrón (15 min).
3. Autonomía limitada y human-in-the-loop — retomar la matriz de riesgo de la Clase 2 y aplicarla a decisiones del agente (15 min).

**No profundizar** en checkpointers (`MemorySaver`/`SqliteSaver`) ni en el orquestador multiagente completo — mencionarlos solo como "el próximo escalón si el sistema crece", sin implementarlos en esta clase.

---

## Bloque 4 — Laboratorio (55 min)

- Dar el esqueleto de grafo del teórico (nodo agente + nodo herramientas + arista condicional) y pedir que cada grupo defina sus propias 2-3 herramientas sobre su caso propio.
- Insistir en que agreguen la condición de control de riesgo (detenerse si detecta una acción de alto riesgo).
- Últimos 15 minutos: correr el test de validación (consulta que necesita 2 herramientas) y revisar en el log de mensajes que el orden tuvo sentido.

**Si el grupo tiene bajo dominio técnico:** dar el agente de Ortelana ya armado y funcional, y que solo cambien las herramientas y los docstrings para su caso propio — se evalúa el diseño del esquema (Hito 2), no la sintaxis de LangGraph desde cero.

---

## Cierre (15 min)

- Repasar el resumen.
- Confirmar el **Hito 2**: esquema técnico (diagrama de componentes, estados, herramientas, datos y controles).
- Anticipar Clase 7: "hasta acá construimos piezas. La próxima clase las integramos de punta a punta y las sometemos a criterios de calidad y guardrails."

---

## Notas para el docente

- Esta es la clase de cierre de la Unidad 2 (Herramientas y Prototipado) — antes de pasar a Clase 7, verificar que cada grupo tenga ya reunidos: el concepto de solución (Clase 2), el workflow (Clase 4), el RAG (Clase 5) y el agente (hoy). La Clase 7 los integra todos.
- Si surge la pregunta de "¿por qué no dejamos que el agente apruebe todo solo?", usarla como cierre pedagógico: conecta directamente con el tema de guardrails y diseño responsable que se profundiza en la Clase 7.
