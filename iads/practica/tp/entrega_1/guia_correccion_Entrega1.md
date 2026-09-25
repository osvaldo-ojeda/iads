
# Guía de corrección — TP Integrador Entrega 1

*Material docente. No compartir con los alumnos.*

**Tiempo estimado:** ~30 min por grupo.
**Entrega:** link a repositorio Git (GitHub/GitLab).

---

## Fase 0 — Escaneo de seguridad (antes que nada, ~5 min)

Clonar el repo y revisar el **historial completo**, no solo el estado actual:

```bash
git clone <url> grupo_X && cd grupo_X

# Buscar API keys en TODO el historial
git log --all -p | grep -nE "sk-[A-Za-z0-9_-]{20,}|sk-ant-|AIza[A-Za-z0-9_-]{20,}"

# Verificar que .env esté ignorado y que NO haya sido commiteado nunca
git log --all --full-history -- .env
cat .gitignore | grep -E "^\.env$"
```

| Resultado | Acción |
|---|---|
| Hay una key en algún commit (aunque esté borrada) | **−15**. Avisar al grupo por privado que rote la key **hoy**. |
| `.env` aparece en `git log` | Cuenta como key filtrada si tiene valor real; si está vacío, **−5**. |
| `.gitignore` no ignora `.env` | **−5** |

---

## Fase 1 — Gate técnico (~10 min)

```bash
cp .env.example .env
# completar .env con TU key
pip install -r requirements.txt   # o lo que diga el README
python app.py
```

1. **¿Corre punta a punta?** Si no corre por algo evitable (path absoluto hardcodeado, import faltante, dependencia no declarada) → criterio 7 baja un nivel. Anotar el error exacto para el feedback.
2. **¿Maneja un input roto?** Pasarle un texto basura o vacío. Si crashea con traceback en vez de manejar `ValidationError` → criterio 7 no llega a "Logrado".
3. **Re-correr su lote de C.3.** Comparar la salida con la tabla de `resultados_lote.md`. Si no coincide con lo que documentaron → criterio 8 baja (documentaron algo que no probaron).

---

## Fase 2 — Cadena de coherencia (~10 min)

Leer `informe.md` con esta lista al lado. Es lo que separa un integrador de tres mini-TPs pegados.

| Chequeo | Dónde mirar | Si falla |
|---|---|---|
| Los valores del `Literal` de `schemas.py` son **exactamente** las intenciones de la Matriz B.3 | `schemas.py` vs. tabla B.3 | Criterio 9 baja |
| El JSON de B.5 tiene los mismos campos que el modelo Pydantic de C.1 | B.5 vs. `schemas.py` | Criterio 9 baja |
| Las salidas de la tabla C.3 usan esas mismas intenciones | `resultados_lote.md` | Criterio 9 baja |
| El System Prompt de B.5 pide lo que el schema exige (null, sin texto extra, valores del Literal) | B.5 c) | Criterio 5 baja |
| La Base de Conocimiento del PEAS (A.3) aparece mencionada como "lo que falta" en C.5 | A.3 vs. C.5 | Criterio 9 no llega a Destacado |

---

## Fase 3 — Calidad de contenido (~5 min, spot-checks)

- **A.2:** ¿está la respuesta real del modelo pegada, con lo inventado marcado? ¿O es un "el modelo se equivocó" genérico? (genérico → "En desarrollo")
- **B.3:** elegir 2 filas al azar. ¿El riesgo está justificado por *escribe vs. lee* y *consecuencia financiera*, o es arbitrario?
- **B.4:** marcar componente por componente. ¿Dice "esto es LLM" **y explica por qué**, o solo lo enuncia?
- **B.5 c):** pegar el System Prompt en un modelo y tirarle el input de inyección del lote. ¿Aguanta? (aguanta → criterio 5 a Destacado)
- **C.1:** ¿el `@field_validator` hace algo real (limpia, normaliza, rechaza un rango) o es un `return v`?

---

## Fase 4 — Cierre

1. Completar la grilla de niveles (los 9 criterios) y restar penalizaciones.
2. **Feedback 3 + 3:** tres cosas que están bien, tres a corregir **para la Entrega 2**. Priorizar las que van a arrastrar problemas al Proyecto Integrador (dominio mal elegido, PEAS sin Base de Conocimiento clara, Matriz sin casos de escritura).
3. Si se hace defensa oral: ±10 sobre la nota grupal, según si cada integrante puede explicar su parte.

---

## Errores típicos de esta entrega (para anticipar el feedback)

| Síntoma | Qué está pasando en realidad |
|---|---|
| El dominio es "un asistente que ayuda con consultas" | No hay caso concreto → todo lo demás sale genérico. Pedir que lo acoten antes de seguir. |
| La Matriz tiene 3 filas todas de solo-lectura | No pensaron el caso de escritura, que es el de riesgo ALTO y el que justifica el patrón híbrido. |
| El `Literal` tiene más valores que la Matriz (o menos) | Programaron el schema sin releer su propio diseño. Es el error de coherencia más común. |
| El script corre pero con la key hardcodeada y `.env.example` de adorno | Criterio 7 no supera "En desarrollo" + penalización de seguridad. |
| Un solo commit "TP terminado" | No hay evidencia de proceso ni de quién hizo qué → −5 y nota para la próxima. |
| C.5 dice "el sistema ya está completo" | No entendieron que falta el grounding / Base de Conocimiento. Es justo lo que abre la Unidad 3. |
