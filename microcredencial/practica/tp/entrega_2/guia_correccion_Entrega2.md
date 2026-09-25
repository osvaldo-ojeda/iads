
# Guía de corrección — TP Integrador Entrega 2

*Material docente. No compartir con los alumnos.*

**Tiempo estimado:** ~25 min por grupo.
**Entrega:** link al mismo repositorio Git de la Entrega 1.

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
python entrega_2/app.py
```

1. **¿Corre punta a punta?** Si no corre por algo evitable (path absoluto hardcodeado, import faltante, dependencia no declarada) → criterio 2 baja un nivel. Anotar el error exacto para el feedback.
2. **¿Maneja un input roto?** Pasarle texto basura o vacío. Si crashea con traceback en vez de manejar `json.JSONDecodeError` → criterio 3 no llega a "Logrado".
3. **¿Se diferencia JSON inválido de falla de red?** Revisar que haya dos `except` distintos. Si hay un solo `except Exception` que captura todo → criterio 3 baja.

---

## Fase 2 — Cadena de coherencia (~8 min)

Este es el chequeo más importante de esta entrega: ¿el prototipo es coherente con el diseño de la Entrega 1?

| Chequeo | Dónde mirar | Si falla |
|---|---|---|
| Los valores de `intencion` en el prompt son **exactamente** los de la Matriz B.4 de la Entrega 1 | System prompt vs. `entrega_1/informe.md` | Criterio 1 no supera "En desarrollo" |
| El schema JSON del prompt tiene los mismos campos que se documentaron en el contrato de B.2 | System prompt vs. `entrega_2/informe.md` sección contrato | Criterio 1 baja |
| Los outputs de la tabla C.1 usan esas mismas intenciones | `entrega_2/resultados_lote.md` | Criterio 4 baja |

---

## Fase 3 — Calidad del prompt y del lote (~5 min, spot-checks)

- **A.2 — System prompt:** ¿está el schema exacto? ¿Prohíbe texto extra explícitamente? ¿Define `null` como fallback?
- **A.1 — Técnica:** ¿la justificación explica *por qué* esa técnica funciona para el dominio, o solo dice "elegimos few-shot"?
- **C.1 — Tabla:** ¿están los 4 inputs incluyendo el ambiguo y el de manipulación? ¿Están documentados los casos que fallaron?
- **C.2 — Reflexión:** ¿dice algo concreto sobre qué mejorarían, o es genérico ("el prompt funciona bien")?

---

## Fase 4 — Cierre

1. Completar la grilla de los 4 criterios y restar penalizaciones.
2. **Feedback 3 + 3:** tres cosas que están bien, tres a corregir para la Entrega 3. Priorizar:
   - Si hay inconsistencia entre el prompt y la Matriz de E1, es crítico resolverlo antes de armar el workflow.
   - Si el script no maneja errores, el workflow de la E3 va a ser frágil.
   - Si el prompt cedió ante el intento de manipulación del lote, anticipar que esto se agrava con un agente (E3 Parte C).

---

## Errores típicos de esta entrega

| Síntoma | Qué está pasando |
|---|---|
| Las intenciones del prompt no coinciden con la Matriz de E1 | Programaron el prototipo sin releer su propio diseño. Es el error de coherencia más común — y el que más duele en el workflow de la E3. |
| Un solo `except Exception` captura todo | No diferenciaron los tipos de error — les pasa a todos los que copian el ejemplo base sin adaptarlo. Mostrar la diferencia en el feedback. |
| El script corre pero la key está hardcodeada | Criterio 2 no supera "En desarrollo" + penalización de seguridad. |
| La tabla del lote tiene 4 casos "exitosos" | No eligieron inputs difíciles. El punto es ver dónde falla, no donde funciona. |
| La reflexión dice "el prompt funcionó bien" sin más | No extrajeron aprendizajes. Preguntarles en la devolución: "¿y el caso de manipulación?" |
