
# Guía de corrección — TP Integrador Entrega 2

*Material docente. No compartir con los alumnos.*

**Tiempo estimado:** ~30 min por grupo.
**Entrega:** el mismo repositorio Git de la Entrega 1, con los archivos nuevos de la Unidad 3.

---

## Fase 0 — Escaneo de seguridad y de higiene del repo (~5 min)

```bash
cd grupo_X && git pull

# API keys en TODO el historial (incluye lo agregado en la Entrega 2)
git log --all -p | grep -nE "sk-[A-Za-z0-9_-]{20,}|sk-ant-|AIza[A-Za-z0-9_-]{20,}"

# .env nunca commiteado
git log --all --full-history -- .env
grep -E "^\.env$" .gitignore

# La base binaria NO debería estar en el repo
git ls-files | grep -E "\.index$|\.sqlite3$|chroma/|chroma\.sqlite"
```

| Resultado | Acción |
|---|---|
| Key en algún commit (aunque esté borrada) | **−15**. Avisar por privado que rote la key **hoy**. |
| `.env` en `git log` con valor real | Cuenta como key filtrada. Si está vacío, **−5**. |
| `.gitignore` no ignora `.env` | **−5** |
| `*.index`, `chroma.sqlite3` o el directorio persistente commiteados | **−5**. La base se reconstruye desde `base_conocimiento.json` + scripts. |
| Repo privado (se pidió público) | Pedir que lo pasen a público o den acceso. No penaliza si responden al aviso. |
| `.env.example` no existe o le faltan variables que los scripts usan | Bloquea la Fase 1. Pedir que lo completen — si es lo único que falta, no penaliza; si además el script no corre, criterio 4/5 baja. |

> El repo es **público**: el escaneo de keys del historial no es opcional. Correr el `grep` de arriba sobre `git log --all -p` completo, no solo sobre el estado actual.

---

## Fase 1 — Gate técnico y prueba de reconstrucción (~10 min)

Clonar **en limpio** (no reusar una carpeta donde ya corrió). Si la base no se levanta desde cero, algo quedó fuera del repo.

```bash
git clone <url> grupo_X_limpio && cd grupo_X_limpio
cp .env.example .env      # completar con TU key
pip install -r requirements.txt
python pipeline_vectorial.py    # Parte A — FAISS
python etl_purga.py             # Parte B.5 — ETL + purga
python vector_db.py             # Parte B — ChromaDB + búsqueda híbrida
```

Si `.env.example` no lista una variable que el script pide, o falta una dependencia en `requirements.txt`, o un dato solo existía en un notebook que no está en el repo → la base **no es reconstruible** → criterio 4 o 5 no llega a "Logrado".

1. **¿`pipeline_vectorial.py` corre punta a punta?** Debe generar embeddings la primera vez y **recargar desde disco** la segunda sin volver a llamar a la API (avisar por consola "0 tokens"). Si regenera siempre → criterio 4 no llega a "Logrado".
2. **¿ChromaDB persiste?** Correr `vector_db.py`, borrar la variable en memoria / reiniciar, volver a correr. Si vuelve a pagar embeddings → no implementaron `PersistentClient` bien → criterio 5 baja.
3. **Re-correr las Killer Queries** y comparar con `resultados_killer_queries.md`. Si no coincide → criterio 8 baja (documentaron algo que no probaron).
4. **Inspeccionar el `where` de la búsqueda híbrida.** Abrir `vector_db.py` y buscar el filtro. Si hay un `for`/`if` de Python filtrando `resultados["metadatas"]` después de la query → post-filtering manual → criterio 6 baja un nivel.

---

## Fase 2 — Cadena de coherencia con la Entrega 1 (~10 min)

Leer `informe_entrega2.md` con la Entrega 1 al lado. Es lo que separa un integrador de dos TPs pegados.

| Chequeo | Dónde mirar | Si falla |
|---|---|---|
| Los **metadatos** de `base_conocimiento.json` son los **campos de filtrado** de la Matriz de Intenciones B.3 de la Entrega 1 | `base_conocimiento.json` vs. Matriz E1 | Criterio 9 baja |
| La **Base de Conocimiento** de la columna del PEAS (A.3 de E1) es exactamente esta colección | PEAS E1 vs. C.1 | Criterio 9 baja |
| El esquema de metadatos sigue la Regla del Arquitecto (filtro duro afuera, narrativa adentro) | A.3 justificación | Criterio 3 baja |
| Definieron un **umbral** y el sistema responde honestamente cuando nada lo supera | C.2 + Killer Query 3 | Criterio 9 no llega a Destacado |
| C.3 identifica que falta el **orquestador RAG** (no dice "el sistema ya está completo") | C.3 | Criterio 9 baja |

---

## Fase 3 — Calidad de contenido (~5 min, spot-checks)

- **A.2:** ¿los ejes semánticos son propios y tienen sentido para el dominio, o copiaron "Resistencia / Suavidad" de Ortelana? ¿El cálculo a mano tiene los tres pasos o solo pegaron el resultado de NumPy?
- **A.3:** abrir 3 documentos al azar. ¿La `descripcion_semantica` es un párrafo rico o son dos palabras tipo `"Ley 24.240"`? (pobre → criterio 3 "En desarrollo").
- **B.5:** ¿los casi-duplicados son genuinamente el mismo concepto con distinto texto, o son dos cosas distintas? ¿El umbral de distancia está justificado o es un número mágico? ¿El ETL realmente normaliza la clave mal nombrada y el booleano-string?
- **B.6:** leer las 3 queries. ¿La #1 usa jerga sin ninguna palabra del documento? ¿La #2 realmente traería un desastre sin el filtro? ¿La #3 es una consulta fuera de catálogo? (si las tres son "buscar X normal" → criterio 8 "En desarrollo").
- **B.4:** pegar el `where` en la doc de ChromaDB mentalmente: ¿usa `$and`/`$eq`? ¿o es `{"campo": valor}` plano (funciona pero es la forma vieja)?

---

## Fase 4 — Cierre

1. Completar la grilla de niveles (9 criterios) y restar penalizaciones.
2. **Feedback 3 + 3:** tres cosas bien, tres a corregir **para la Entrega 3 (RAG)**. Priorizar lo que va a arrastrar: base pobre en descripciones (el RAG recupera basura), metadatos que no matchean la Matriz, sin umbral (el RAG va a alucinar sobre el peor match).

Esta entrega no tiene defensa oral individual — se concentra en la defensa final (Entrega 5 / Clase 16).

---

## Errores típicos de esta entrega (para anticipar el feedback)

| Síntoma | Qué está pasando en realidad |
|---|---|
| Las `descripcion_semantica` son títulos, no párrafos | El embedding tiene poco con qué trabajar → la búsqueda semántica va a fallar en el RAG. Es el error que más se paga después. |
| Los metadatos no coinciden con la Matriz de Intenciones de la E1 | Diseñaron la base sin releer su propio diseño. Error de coherencia más común. |
| El filtro híbrido se hace con un `if` en Python | No entendieron el pre-filtering. Funciona con 15 docs, colapsa a escala. |
| La purga semántica "no encontró duplicados" | O no agregaron casi-duplicados reales, o el umbral está mal calibrado. Pedir que muestren las distancias de los pares. |
| Commitearon `chroma.sqlite3` (10+ MB) | No leyeron el `.gitignore` sugerido. −5 y nota para la próxima. |
| C.3 dice "el sistema ya responde al usuario" | No entendieron que ChromaDB devuelve un dict, no una respuesta. Es justo lo que abre la Unidad 4. |
| Reutilizaron el catálogo de Ortelana | Rehacer con el dominio propio. La base es el cimiento del RAG de su proyecto. |
