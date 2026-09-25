
# Guía de Corrección — Entrega 3: Sistema RAG Completo con Evaluación

*Documento interno de la cátedra — no distribuir a alumnos*

**Unidad 4: Clases 6, 7 y 8**

---

## Niveles de calificación

| Nivel | Significado | % del máximo del criterio |
|---|---|---|
| **No logrado** | Ausente o con errores fundamentales que impiden la comprensión | 0 % |
| **En desarrollo** | Presente pero incompleto, con errores conceptuales o técnicos significativos | 40 % |
| **Logrado** | Cumple lo esperado para el nivel de la cursada | 75 % |
| **Destacado** | Supera lo esperado: mayor profundidad, análisis crítico o innovación técnica | 100 % |

---

## Criterio 1 — Pipeline RAG con guardrails (A.2, A.3) · 20 puntos

### ¿Qué evaluar?

Que el chain LCEL funcione de punta a punta y que el prompt tenga al menos 4 de las 5 reglas de negocio. Que la matriz de validación esté completa con los 4 tipos de prueba.

### Niveles

| Nivel | Indicadores |
|---|---|
| **No logrado** | El pipeline no corre, o conecta con una base ad-hoc sin relación con la Entrega 2 |
| **En desarrollo** | El pipeline corre pero el prompt no tiene guardrails o la matriz de validación tiene solo 1–2 tipos de prueba |
| **Logrado** | Chain LCEL completo con retriever + prompt + llm + parser; prompt con ≥4 reglas de negocio; matriz con los 4 tipos (factual / fuera de dominio / ataque / sinónimos) con resultados documentados |
| **Destacado** | Adicional: MMR implementado, variaciones de temperature comparadas, guardrail por rol (distintos prompts según perfil del usuario) |

### Señales de alerta

- El grupo reutiliza literalmente el prompt de Ortelana sin adaptarlo a su dominio → **En desarrollo** en prompt, discutir con el docente
- Los 4 ataques de la matriz los inventaron sin correrlos realmente → pedir evidencia (output del notebook)
- El pipeline conecta con una base nueva distinta a la de la Entrega 2 → penalización automática, criterio baja un nivel

---

## Criterio 2 — Trazabilidad de fuentes (A.4) · 10 puntos

### ¿Qué evaluar?

Que el grupo pueda mostrar explícitamente qué documentos usó el sistema para fundamentar la respuesta. No alcanza con "el retriever devuelve k documentos" — tiene que mostrarse el contenido del fragmento y los metadatos relevantes.

### Niveles

| Nivel | Indicadores |
|---|---|
| **No logrado** | No implementado |
| **En desarrollo** | Solo muestra el índice de los documentos sin contenido ni metadatos |
| **Logrado** | ≥2 consultas con `RunnableParallel` (o equivalente) mostrando contenido (primeros 100 chars) y metadatos del dominio propio |
| **Destacado** | Además analiza si los documentos fuente son coherentes con la respuesta dada ("el sistema respondió X porque recuperó el fragmento Y") |

---

## Criterio 3 — Falla del RAG básico identificada y explicada (B.1) · 15 puntos

### ¿Qué evaluar?

Que la falla sea real y reproducible (no inventada), y que la explicación técnica sea correcta.

### Categorías de falla válidas

| Categoría | Cómo verificar que es real |
|---|---|
| **Chunk cortado** | Mostrar el chunk A y el chunk B que quedaron separados + la respuesta incompleta |
| **Ruido en el contexto** | Mostrar los 3 chunks que recuperó el retriever + demostrar que ninguno contiene la respuesta aunque existe en la base |
| **Lost in the Middle** | Recuperar 5+ chunks, mostrar cuál quedó en el medio y demostrar que la respuesta lo ignoró |

### Niveles

| Nivel | Indicadores |
|---|---|
| **No logrado** | No identificaron ninguna falla o la falla es inventada (no reproducible) |
| **En desarrollo** | Identificaron una falla pero la explicación técnica es incorrecta (ej: dicen que es "chunk cortado" pero en realidad es ruido en el contexto) |
| **Logrado** | La falla es real, reproducible y la causa técnica está correctamente categorizada con evidencia |
| **Destacado** | Identificaron más de una falla o además midieron el impacto de la falla en las métricas RAGAS |

---

## Criterio 4 — RAG avanzado implementado (B.2, B.3) · 15 puntos

### ¿Qué evaluar?

Chunking con solapamiento aplicado sobre su propio corpus; reranking implementando y funcionando. La falla de B.1 se resolvió (o se explica técnicamente por qué persiste).

### Niveles

| Nivel | Indicadores |
|---|---|
| **No logrado** | No implementaron chunking con solapamiento ni reranking |
| **En desarrollo** | Implementaron uno de los dos (solo chunking o solo reranking) sin comparación |
| **Logrado** | Chunking con solapamiento (chunk_overlap ≥ 15% del chunk_size) aplicado sobre su corpus; reranking con k_candidatos > k_final funcionando; la falla de B.1 se aborda |
| **Destacado** | Adicional: Parent Document Retriever, posicionamiento estratégico de chunks (Lost in the Middle mitigation), comparación cuantitativa de chunking básico vs avanzado |

### Señales de alerta

- Usan chunk_overlap=0 → no cumple la consigna de solapamiento
- El reranking recupera k=8 pero pasan los 8 al LLM → no entendieron el concepto de "filtrar"
- Dicen que "la falla se resolvió" sin mostrar evidencia → pedir el output antes y después

---

## Criterio 5 — Dataset de evaluación (C.1) · 15 puntos

### ¿Qué evaluar?

Que el dataset tenga ≥10 preguntas con la distribución correcta y que las `ground_truth` sean verificables contra la base propia.

### Checklist de distribución

| Tipo | Mínimo requerido |
|---|---|
| Preguntas simples (1 chunk) | 3 |
| Preguntas complejas (múltiples chunks) | 3 |
| Preguntas de escape ("no sé") | 2 |
| Preguntas con lenguaje informal/ambiguo | 2 |
| **Total** | ≥ 10 |

### Niveles

| Nivel | Indicadores |
|---|---|
| **No logrado** | Dataset con < 5 preguntas o sin ground_truth |
| **En desarrollo** | ≥10 preguntas pero sin la distribución requerida (ej: todas son preguntas simples), o las ground_truth no coinciden con los documentos reales de la base |
| **Logrado** | ≥10 preguntas con la distribución completa; las ground_truth son verificables contrastando contra la base |
| **Destacado** | ≥15 preguntas; dataset comentado explicando por qué cada pregunta representa un caso de prueba importante; las preguntas de escape están elegidas con criterio (no son absurdas, son plausibles pero fuera del corpus) |

### Señales de alerta

- Las preguntas son todas triviales (una palabra en el documento = respuesta exacta) → **En desarrollo**
- Las ground_truth fueron generadas por el LLM sin verificar → pedir que señalen el fragmento del documento que respalda cada ground_truth
- Las preguntas de escape son absurdas ("¿Cuántos planetas tiene el sistema solar?") en lugar de ser plausibles para el dominio → **En desarrollo**

---

## Criterio 6 — RAGAS corriendo + comparación (C.2, C.3) · 15 puntos

### ¿Qué evaluar?

Que las 4 métricas de RAGAS estén documentadas y que la comparación RAG básico vs avanzado muestre al menos una métrica que mejoró.

### Niveles

| Nivel | Indicadores |
|---|---|
| **No logrado** | RAGAS no corrió o no se documentaron los resultados |
| **En desarrollo** | RAGAS corrió pero solo con 1–2 métricas, o la comparación básico vs avanzado no existe |
| **Logrado** | Las 4 métricas documentadas (faithfulness, answer_relevancy, context_precision, context_recall); la comparación muestra al menos 1 métrica que mejoró con evidencia |
| **Destacado** | Además: los resultados por pregunta (no solo el promedio); identificaron cuáles preguntas tienen peor performance y por qué; corrieron RAGAS con LangSmith activo y muestran la traza |

### Señales de alerta

- Los 4 números del RAG básico y del RAG avanzado son idénticos → algo no funcionó (o usaron la misma base sin reconstruir) → **No supera "En desarrollo"**
- Los números parecen demasiado altos (todas las métricas > 0.95 con 10 preguntas variadas) → pedir evidencia del notebook con el dataset corriendo
- Solo reportan el promedio sin la tabla por pregunta → **Logrado** pero no **Destacado**

---

## Criterio 7 — Diagnóstico y acción (C.4) · 10 puntos

### ¿Qué evaluar?

Que la métrica más baja esté correctamente diagnosticada y que la acción propuesta sea coherente con esa causa.

### Tabla de coherencia esperada

| Si la métrica más baja es... | La causa correcta es... | La acción coherente es... |
|---|---|---|
| **Faithfulness** | El LLM agrega datos no presentes en el contexto | Reforzar System Prompt + temperature=0 |
| **Answer Relevancy** | El LLM responde algo relacionado pero no la pregunta puntual | Mejorar la instrucción de "responder directamente" en el prompt |
| **Context Precision** | El retriever trae chunks irrelevantes | Ajustar reranking o metadatos de filtrado |
| **Context Recall** | El retriever no encuentra toda la información necesaria | Ajustar chunk_size y overlap |

### Niveles

| Nivel | Indicadores |
|---|---|
| **No logrado** | No hay diagnóstico |
| **En desarrollo** | La métrica más baja está identificada pero la causa o la acción no son coherentes (ej: context_recall bajo → proponen mejorar el System Prompt) |
| **Logrado** | La métrica más baja está correctamente identificada con su causa técnica; la acción propuesta es coherente |
| **Destacado** | Además implementaron la acción y muestran evidencia de que mejoró la métrica (re-corrieron RAGAS después del fix) |

---

## Penalizaciones

| Situación | Penalización |
|---|---|
| API key real en algún commit del historial de Git | −15 puntos + aviso inmediato al grupo para rotar |
| El pipeline no conecta con la base de la Entrega 2 | Criterio 1 baja automáticamente a **En desarrollo** |
| Dataset con preguntas triviales sin distribución requerida | Criterio 5 baja un nivel |
| Comparación RAG básico vs avanzado con valores idénticos | Criterio 6 no supera **En desarrollo** |

---

## Cómo corregir eficientemente

1. **Verificar primero que el pipeline conecta con la Entrega 2** (no con una base nueva). Si no conecta, aplicar penalización antes de revisar el resto.
2. **Correr el notebook en el entorno del corrector** para verificar que funciona. Si hay un error de dependencia que el grupo no documentó en el `requirements.txt`, bajar un nivel en el criterio afectado.
3. **La matriz de validación** es el indicador más honesto del criterio 1. Si hay 4 tipos de prueba con resultados reales, el grupo entendió el concepto de seguridad del RAG.
4. **La comparación RAGAS** es el indicador más honesto de que realmente mejoraron algo. Si los números son idénticos, pedir explicación al grupo.
5. **El diagnóstico (C.4)** revela si el grupo entendió la relación causa-efecto entre cada métrica y el componente del pipeline que la afecta. Una respuesta vaga como "mejorar el sistema" no alcanza.

---

## Retroalimentación sugerida para grupos

**Si están en "En desarrollo" en el criterio de Pipeline (1):**
> "El chain LCEL corre pero el prompt no tiene guardrails suficientes. Para producción, el LLM necesita instrucciones explícitas sobre qué no puede confirmar. Revisar el PROMPT_RAG_BLINDADO de la Clase 6 y adaptarlo al dominio de su sistema."

**Si están en "En desarrollo" en el dataset de evaluación (5):**
> "Las preguntas del dataset tienen que ser representativas de casos reales. Las preguntas de escape tienen que ser plausibles para el dominio — que un usuario real podría hacer — pero que no están en la base. Ejemplo para un sistema legal: '¿Cuánto cuesta un divorcio?' es plausible pero puede no estar en la normativa indexada."

**Si la comparación RAGAS da igual (criterio 6):**
> "Si las métricas del RAG básico y avanzado son iguales, revisá que realmente reindexaste con solapamiento (verificá con `vectorstore._collection.count()` que el número de chunks cambió) y que el reranking efectivamente está filtrando antes de pasar al LLM."
