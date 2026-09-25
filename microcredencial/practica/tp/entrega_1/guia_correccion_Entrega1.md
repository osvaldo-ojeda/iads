
# Guía de corrección — TP Integrador Entrega 1

*Material docente. No compartir con los alumnos.*

**Tiempo estimado:** ~20 min por grupo.
**Entrega:** link a repositorio Git (GitHub/GitLab).

---

## Fase 0 — Escaneo rápido del repo (~3 min)

Antes que nada: verificar que el repo existe y tiene historial real.

```bash
git clone <url> grupo_X && cd grupo_X
git log --oneline
```

| Resultado | Acción |
|---|---|
| Un único commit "entrega final" | **−5**. Anotar para feedback. |
| Historial con varios commits | Continuar. |

---

## Fase 1 — Lectura de la Parte A (~8 min)

Abrir `entrega_1/informe.md` y revisar con esta lista:

### A.1 — El caso

- ¿El caso es concreto? Un caso aceptable nombra la empresa/situación, el proceso específico que se automatiza, y quién lo sufre.
- **Trampa frecuente:** "una IA para ayudar a las empresas a ser más eficientes" — esto no es un caso, es una idea genérica. Si el docente detecta esto, el criterio 1 no supera "En desarrollo" y arrastra los criterios 3, 4 y 6.

### A.2 — Evidencia de alucinación

Checklist:
- [ ] ¿Está la respuesta real del modelo pegada (copy-paste), no parafraseada?
- [ ] ¿Está marcado específicamente qué parte inventó el modelo?
- [ ] ¿Se menciona el nivel de confianza con que lo presentó ("dijo con seguridad que...")?

Si dicen "el modelo se equivocó" sin mostrar la respuesta → criterio 1 baja a "En desarrollo".

### A.3 — 4 criterios de viabilidad

Elegir 2 criterios al azar. ¿La respuesta es específica del dominio o genérica?

- **Genérico:** "el valor es que ahorra tiempo". → "En desarrollo".
- **Específico:** "el valor es reducir de 45 minutos a 5 minutos el tiempo de clasificación manual de CVs para el área de RRHH". → "Logrado" o "Destacado".

### A.4 — Mapa de seis piezas

- ¿Confunden "modelo" con "sistema"? (Error típico: poner "ChatGPT" como todo el sistema.)
- ¿Las herramientas son reales para el dominio, o genéricas ("puede hacer muchas cosas")?

---

## Fase 2 — Lectura de la Parte B (~8 min)

### B.2 — User journey

- ¿Cada paso está marcado como [Regla] o [LLM]?
- ¿La justificación existe o solo dice "lo hace el LLM"? La justificación debe mencionar por qué (lenguaje natural de por medio → LLM; resultado matemático o binario → regla).

**Prueba rápida:** tomar el paso que marcaron como [LLM]. ¿Hay lenguaje natural de por medio? Si es un cálculo o una validación de formato → debería ser regla.

### B.3 — MVP

- ¿Hay capacidades **y** límites explícitos? Si solo dicen lo que hace pero no lo que explícitamente NO hace → criterio 5 no llega a "Logrado".
- ¿El criterio de éxito es concreto y medible? "que funcione bien" no es un criterio. "responder correctamente el 80% de las consultas sin intervención humana" sí.

### B.4 — Matriz de Intenciones

- ¿Hay mínimo 3 filas?
- ¿Hay al menos 1 de riesgo ALTO con escritura o consecuencia financiera? Un conjunto de solo-lecturas no refleja el patrón híbrido.
- ¿El riesgo está justificado o es arbitrario?

**Prueba de coherencia para la Entrega 2:** las intenciones que definieron acá (ej. `CONSULTA_STOCK`, `ALTA_CLIENTE`) deberían ser exactamente las que van a aparecen en el prompt de la Entrega 2. Si ya se ven nombres raros o inconsistentes, anotarlo para el feedback.

---

## Fase 3 — Cierre (~4 min)

1. Completar la grilla de los 6 criterios con su nivel.
2. Restar penalizaciones.
3. **Feedback 3 + 3:** tres cosas que están bien, tres a corregir **para la Entrega 2**.

Priorizar en el feedback:
- Un dominio vago o genérico va a hacer colapsar todo el resto — pedir que lo acoten antes de seguir.
- Una Matriz sin riesgo ALTO es una señal de que no pensaron el caso de escritura. Eso afecta directamente el diseño del workflow (Entrega 3).
- Un user journey sin justificación de la frontera regla/LLM va a generar problemas en la arquitectura del prototipo (Entrega 2).

---

## Errores típicos de esta entrega

| Síntoma | Qué está pasando |
|---|---|
| El dominio es "un asistente que ayuda con consultas" | No hay caso concreto — todo lo demás sale genérico. Pedir que lo acoten antes de seguir. |
| La respuesta del modelo está parafraseada, no pegada | No hicieron el taller de verdad, o lo resumieron para que parezca mejor. Pedir la evidencia real. |
| La Matriz tiene solo intenciones de lectura | No pensaron el caso de escritura (el que justifica el patrón híbrido). Señalar que falta una de riesgo ALTO. |
| El criterio de éxito del MVP es "que funcione bien" | No entendieron qué es un criterio medible. Dar un ejemplo del dominio en el feedback. |
| Un único commit con todo | No hay evidencia de proceso. Anotar −5 y anticipar que en la Entrega 2 se sigue evaluando el historial. |
