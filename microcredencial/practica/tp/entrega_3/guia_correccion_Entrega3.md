
# Guía de corrección — TP Integrador Entrega 3

*Material docente. No compartir con los alumnos.*

**Tiempo estimado:** ~35 min por grupo.
**Entrega:** mismo repositorio Git.

---

## Fase 0 — Escaneo de seguridad (~3 min)

```bash
git clone <url> grupo_X && cd grupo_X
git log --all -p | grep -nE "sk-[A-Za-z0-9_-]{20,}|sk-ant-|AIza[A-Za-z0-9_-]{20,}"
git log --oneline   # verificar historial incremental
```

| Resultado | Acción |
|---|---|
| API key en algún commit | **−15**. Avisar para rotar. |
| Un único commit para toda la entrega | **−5**. Anotar. |

---

## Fase 1 — Parte A: Workflow (~10 min)

```bash
python entrega_3/workflow.py
```

Checklist:

- [ ] **¿Corre punta a punta?** Si no corre por algo evitable → criterio 1 baja un nivel.
- [ ] **¿Hay al menos 3 pasos distinguibles?** Si es una sola función con todo adentro, no es un workflow.
- [ ] **¿La validación es en código con lógica real?** Si el "Paso 2" es `if True` o equivalente → criterio 2 no supera "En desarrollo".
- [ ] **¿El punto de control detiene el flujo correctamente?** Probar con un input que debería fallar. Si sigue hasta el final igual → criterio 2 baja.

**Prueba rápida de falla controlada:**
- Pasarle un input que debería fallar la validación del Paso 2.
- El resultado debe ser algo como `{"estado": "REVISION_HUMANA", "motivo": "..."}`, no una respuesta final.

---

## Fase 2 — Parte B: RAG (~12 min)

### B.1 — Corpus

- ¿Hay mínimo 10-15 documentos?
- ¿Las `descripcion_semantica` son específicas del dominio? (Si dicen "descripción del documento 1" → no califican como semánticamente ricas → criterio 3 no supera "En desarrollo".)
- ¿Hay al menos 2 metadatos con valores reales y útiles?

**Trampa frecuente:** corpus con metadatos vacíos (`"categoria": ""`). Si los metadatos están vacíos no sirven para filtrado híbrido.

### B.2 — Recuperación

```bash
python entrega_3/rag.py
```

- ¿La recuperación devuelve resultados relevantes para una consulta del dominio?
- ¿Hay filtrado híbrido (semántica + metadato)? Si solo hay búsqueda semántica sin filtro → criterio 4 es "Logrado" pero no llega a "Destacado".
- ¿El system prompt dice explícitamente "usar únicamente el contexto provisto"?

### B.3 — Comparación antes/después

- ¿Están las 2+ preguntas comparadas en la tabla de `informe.md`?
- ¿La columna "sin grounding" muestra una respuesta inventada real (no solo "no tenía contexto")?
- ¿El RAG mejoró la fidelidad de manera verificable?

**Check de oro:** probar una pregunta fuera del corpus. ¿El sistema dice "no tengo información" o inventa algo? Si inventa → el system prompt de RAG no está blindado correctamente → criterio 4 baja.

---

## Fase 3 — Parte C: Agente (~10 min)

### C.1 — Herramientas

- ¿Están los docstrings de las herramientas? ¿Son precisos?
- **Trampa frecuente:** docstring de una línea genérica ("busca cosas en la base de datos"). Eso hace que el agente elija mal. Si los docstrings son vagos → criterio 5 no supera "En desarrollo".
- ¿Están clasificadas como sensor o actuador?

### C.2 — Agente

```bash
python entrega_3/agente.py
```

- ¿Hay un `StateGraph` de LangGraph (o equivalente)?
- ¿El estado tiene `messages` y al menos un campo de control?
- ¿Hay una condición de finalización (no loop infinito)?
- ¿El punto de control de riesgo detiene el flujo ante una acción de alto riesgo?

**Test de validación:** pasarle la consulta que necesita dos herramientas distintas. Revisar la traza:
- ¿Usó ambas herramientas?
- ¿En un orden razonable?
- ¿Se detuvo si llegó al actuador de alto riesgo?

### C.3 — Diagrama

- ¿El diagrama del agente está en `informe.md`?
- ¿Muestra herramientas, estados y condición de riesgo?

---

## Fase 4 — Cadena de coherencia transversal (~5 min)

Esta entrega es donde los proyectos divergen más. Revisar si hay coherencia entre las tres partes:

| Chequeo | Si falla |
|---|---|
| El prompt del workflow (Paso 1) es el mismo que el de la E2, o una versión mejorada con justificación | Si es completamente distinto sin justificación → señalar en feedback |
| Las herramientas del agente son consistentes con las acciones de backend de la Matriz de la E1 | Si el agente tiene herramientas que nunca aparecieron en el diseño → el diseño inicial fue ignorado |
| El corpus del RAG es del mismo dominio que el caso de la E1 | Si es un corpus genérico de ejemplo → criterio 3 baja |

---

## Fase 5 — Cierre

1. Completar la grilla de los 6 criterios y restar penalizaciones.
2. **Feedback 3 + 3:** tres cosas bien, tres a mejorar para la Entrega 4.

Priorizar en el feedback:
- Si el corpus es débil (pocas entradas, semántica pobre), el RAG de la E4 no va a funcionar bien en la demo.
- Si el agente no tiene control de riesgo, la ficha de riesgos de la E4 no va a tener evidencia de que fue pensado.
- Si hay incoherencia entre E1, E2 y E3, anticipar que la "coherencia transversal" de la E4 va a ser el criterio más difícil de aprobar.

---

## Errores típicos de esta entrega

| Síntoma | Qué está pasando |
|---|---|
| El "workflow" es una función de 40 líneas sin pasos distinguibles | Entienden el concepto como secuencia de código, no como pasos con dependencias. Mostrar la estructura de función por paso en el feedback. |
| El corpus tiene 10 documentos con `descripcion_semantica: "texto de ejemplo"` | Copiaron la estructura pero no la llenaron con datos reales. El RAG va a recuperar ruido. |
| Los docstrings de las herramientas son de una línea genérica | El agente va a elegir las herramientas mal o no elegirlas. Mostrar un ejemplo de docstring bueno. |
| No hay condición de riesgo en el agente | El sistema tiene autonomía total — es el error de diseño más importante de la E3. Marcar como "En desarrollo" el criterio 6. |
| Un único commit para toda la entrega | −5. Señalar que el historial es parte de la evaluación del proceso. |
