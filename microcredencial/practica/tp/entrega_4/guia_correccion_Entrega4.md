
# Guía de corrección — TP Integrador Entrega 4

*Material docente. No compartir con los alumnos.*

**Tiempo estimado:** ~30 min por grupo.
**Entrega:** mismo repositorio Git — es la versión candidata que se defiende en la Clase 8.

---

## Fase 0 — Escaneo de seguridad (~3 min)

```bash
git clone <url> grupo_X && cd grupo_X
git log --all -p | grep -nE "sk-[A-Za-z0-9_-]{20,}|sk-ant-|AIza[A-Za-z0-9_-]{20,}"
```

| Resultado | Acción |
|---|---|
| API key en algún commit | **−15**. Avisar para rotar. |

---

## Fase 1 — Gate técnico: integración punta a punta (~10 min)

```bash
cp .env.example .env
# completar .env con TU key
python entrega_4/main.py
# o abrir entrega_4/prototipo_integrado.ipynb
```

1. **¿Corre de punta a punta con al menos una consulta real?** Si no corre por algo evitable → criterio 1 baja un nivel.
2. **¿Las piezas están conectadas o son scripts sueltos?** Pasar por los imports. Si `main.py` importa de `entrega_2/` y `entrega_3/` (o tiene la lógica integrada), las piezas están conectadas. Si son tres archivos que no se relacionan → criterio 1 no supera "En desarrollo".
3. **¿El empaquetado está documentado?** ¿El `informe.md` explica qué correr y cómo?

---

## Fase 2 — Matriz de pruebas (~8 min)

Abrir `entrega_4/matriz_pruebas.md` y verificar:

- [ ] ¿Hay 5 o más casos?
- [ ] **¿Está el Caso 3 (fuera de dominio)?** Si el sistema dice "no tengo información" → correcto. Si inventa algo → el guardrail de anclaje no funciona correctamente.
- [ ] **¿Está el Caso 4 (manipulación)?** ¿El sistema rechazó o no?
- [ ] ¿Tienen "resultado esperado" y "resultado obtenido" en cada fila?
- [ ] ¿Los resultados son reales (corrieron el sistema) o inventados (pusieron lo que "debería pasar" sin correrlo)?

**Prueba de validación cruzada:** elegir 1 o 2 casos de la tabla y re-ejecutarlos con el sistema. ¿El resultado coincide con lo documentado? Si no coincide → criterio 2 baja (documentaron algo que no probaron).

---

## Fase 3 — Guardrail (~5 min)

- [ ] ¿Cuál guardrail eligieron?
- [ ] ¿Hay evidencia documentada de que funciona? (Output real, no solo "se implementó".)
- [ ] ¿Se puede demostrar en vivo durante la Clase 8?

| Guardrail | Cómo verificarlo |
|---|---|
| Anclaje al contexto | El Caso 3 de la matriz devuelve "no tengo información" en vez de inventar |
| PII | Input con dato sensible → la respuesta no lo repite innecesariamente |
| Sesgo | Tabla con 2-3 variaciones del mismo input → calidad similar |
| Manipulación | El Caso 4 de la matriz muestra rechazo explícito |

Si el guardrail está documentado como "lo implementamos" pero no hay evidencia → criterio 3 no supera "En desarrollo".

---

## Fase 4 — Trazabilidad y ficha de riesgos (~5 min)

### Trazabilidad

- [ ] ¿Hay algún registro de interacciones (aunque sea una lista o print estructurado)?
- [ ] ¿El registro incluye la versión del prompt?
- [ ] ¿Se puede seguir la trazabilidad de al menos los casos de la matriz?

### Ficha de riesgos

- [ ] ¿Hay al menos 3 riesgos?
- [ ] ¿Los riesgos son específicos del dominio (no genéricos como "el modelo puede equivocarse")?
- [ ] ¿Cada riesgo tiene probabilidad, impacto y un control real implementado (no "vamos a agregar un control después")?

---

## Fase 5 — Coherencia transversal (~5 min)

Esta es la revisión más importante para la nota de coherencia (criterio 5):

| Chequeo | Dónde mirar | Si falla |
|---|---|---|
| Las intenciones del sistema integrado son exactamente las de la Matriz de E1 | `entrega_1/informe.md` vs. código de extracción en `entrega_4/` | Criterio 5 baja |
| El prompt de E2 está integrado (o su versión mejorada, con justificación) | `entrega_2/informe.md` vs. system prompt en `entrega_4/` | Criterio 5 baja |
| El RAG y/o el agente de E3 están efectivamente en el recorrido | `entrega_3/rag.py` y `entrega_3/agente.py` vs. imports en `entrega_4/` | Criterio 1 y 5 bajan |
| La ficha de riesgos cubre los mismos riesgos que se identificaron en el diseño de E1 (hipótesis más riesgosa de B.5) | `entrega_1/informe.md` vs. `entrega_4/ficha_riesgos.md` | Criterio 4 baja |

---

## Fase 6 — Preparación para la Clase 8

Esta guía también sirve para preparar las preguntas de la defensa. Notar, antes de la clase:

- ¿Cuál es el punto más débil del sistema? (El componente con criterio más bajo.)
- ¿Hay algún riesgo del dominio que no cubrieron?
- ¿Pueden demostrar el guardrail en vivo, o solo tienen la evidencia documentada?

**Preguntas que suelen generar más debate:**
- "¿Qué pasa si el modelo inventa datos que no están en el corpus?"
- "¿Por qué eligieron ese guardrail y no otro?"
- "¿Cuál es la hipótesis más riesgosa del proyecto?" (viene de B.5 de E1)
- "Si tuvieran una clase más, ¿en qué invertirían el tiempo?"

---

## Fase 7 — Cierre

1. Completar la grilla de los 5 criterios y restar penalizaciones.
2. Esta nota es la última de los ejercicios prácticos (40%). Junto con la nota de la defensa del TFA (60%) da la nota final.
3. **Feedback** orientado a la defensa: qué tres cosas deberían destacar en la Clase 8, y qué una limitación deberían mencionar ellos antes de que la pregunte el docente (es mejor reconocerla que que se la señalen).

---

## Errores típicos de esta entrega

| Síntoma | Qué está pasando |
|---|---|
| La integración es solo un notebook que llama a tres funciones sin importar de E2/E3 | No integraron — juntaron. Las piezas de entregas anteriores deben estar realmente conectadas. |
| Los 5 casos de la matriz son todos exitosos | No probaron los casos difíciles (fuera de dominio, manipulación). El sistema "funciona" en la demo controlada pero no está preparado para la realidad. |
| El guardrail es "tenemos un system prompt" | El anclaje al contexto es un guardrail legítimo, pero tiene que estar demostrado con el Caso 3 de la matriz — no solo mencionado. |
| La ficha de riesgos tiene riesgos genéricos ("el modelo puede fallar") | Los riesgos tienen que ser específicos del dominio — "el modelo puede confundir el stock de la sucursal central con el de sucursales regionales" es un riesgo de Ortelana. |
| La integración corre pero es frágil (falla con cualquier variación) | Es "Logrado" si corre con los casos de la matriz, pero señalar en el feedback para la defensa que no convienen las demos arriesgadas. |
