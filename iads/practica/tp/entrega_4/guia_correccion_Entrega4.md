
# Guía de Corrección — Entrega 4: Agente Inteligente con LangGraph

*Documento interno de la cátedra — no distribuir a alumnos*

**Unidad 5: Clases 9 y 10**

---

## Niveles de calificación

| Nivel | Significado | % del máximo del criterio |
|---|---|---|
| **No logrado** | Ausente o con errores fundamentales que impiden la comprensión | 0 % |
| **En desarrollo** | Presente pero incompleto, con errores conceptuales o técnicos significativos | 40 % |
| **Logrado** | Cumple lo esperado para el nivel de la cursada | 75 % |
| **Destacado** | Supera lo esperado: mayor profundidad, análisis crítico o innovación técnica | 100 % |

---

## Criterio 1 — Herramientas diseñadas (A.1, A.2) · 20 puntos

### ¿Qué evaluar?

Que el grupo haya diseñado herramientas con docstrings que le permiten al LLM elegir correctamente. La distinción sensor/actuador tiene que estar clara.

### ¿Cómo verificar la calidad de los docstrings?

Leer el docstring en aislamiento — sin ver el código. Si al leerlo queda claro:
1. ¿Qué tipo de input recibe la herramienta?
2. ¿Cuándo exactamente la usaría el agente?
3. ¿Cuándo NO debería usarla?
4. ¿Qué tipo de dato devuelve?

Si las 4 preguntas tienen respuesta clara → docstring de calidad.

### Niveles

| Nivel | Indicadores |
|---|---|
| **No logrado** | Solo tiene `recuperar_informacion` (el RAG); no diseñaron herramientas propias del dominio |
| **En desarrollo** | ≥2 herramientas propias pero los docstrings no incluyen "Usar cuando" / "NO usar cuando" o son vagos; no hay distinción sensor/actuador |
| **Logrado** | ≥3 herramientas (RAG + sensor + actuador); docstrings con cuándo usar / cuándo no; la descripción del retorno es específica |
| **Destacado** | ≥4 herramientas bien diseñadas; docstrings con ejemplos de input/output; el actuador tiene guardrail de confirmación explícito en el docstring |

### Señales de alerta

- El docstring del actuador no advierte que produce un efecto en el sistema → el grupo no entiende la diferencia sensor/actuador
- Las herramientas tienen nombres genéricos (`procesar_consulta`, `gestionar_solicitud`) → herramientas ambiguas con mayor riesgo de tool hallucination → bajar un nivel
- Todas las herramientas son sensores → el grupo no llegó al concepto de actuador

---

## Criterio 2 — Test de elección de herramientas (A.3) · 10 puntos

### ¿Qué evaluar?

Que el grupo efectivamente probó que el LLM elige la herramienta correcta para cada tipo de consulta. El test tiene que ser ejecutado, no solo descrito.

### Niveles

| Nivel | Indicadores |
|---|---|
| **No logrado** | No hay test de elección |
| **En desarrollo** | Hay un test pero solo con 1–2 consultas, o los resultados no están documentados |
| **Logrado** | ≥4 consultas con resultado documentado (qué herramienta eligió el agente para cada una); si alguna elección fue incorrecta, el docstring fue ajustado |
| **Destacado** | Además analizaron el caso donde el agente eligió mal antes de ajustar vs después — mostrando el impacto del docstring en la decisión del LLM |

### Señales de alerta

- El test muestra solo las consultas donde el agente eligió bien → sesgo de confirmación; pedir que también muestren un caso donde eligió mal y cómo lo resolvieron
- El agente nunca dice "sin herramienta" → el grupo no probó el caso 4 (consulta sin herramienta necesaria)

---

## Criterio 3 — Agente ReAct con LangGraph (B.1, B.2) · 20 puntos

### ¿Qué evaluar?

Que el grafo LangGraph esté correctamente construido y que las 4 consultas obligatorias muestren trazas reales del ciclo ReAct.

### Checklist del grafo

- [ ] Nodo `agente` (LLM con tools) definido
- [ ] Nodo `herramientas` (ToolNode) definido
- [ ] `set_entry_point("agente")` definido
- [ ] Arista condicional: `agente` → `herramientas` si hay tool_calls; `agente` → END si no hay
- [ ] Arista fija: `herramientas` → `agente`
- [ ] `recursion_limit` definido (protección contra loops infinitos)
- [ ] ASCII del grafo documentado en el informe

### Las 4 consultas obligatorias

| # | Tipo | Señal de que está bien |
|---|---|---|
| 1 | Solo RAG | La traza muestra exactamente 1 llamada a `recuperar_informacion` |
| 2 | Solo sensor propio | La traza muestra 1 llamada al sensor; el resultado es coherente con lo que ese sensor devuelve |
| 3 | ≥2 herramientas en secuencia | La traza muestra ≥2 iteraciones del ciclo ReAct; el orden de las herramientas es lógico según la consulta |
| 4 | Sin herramienta | La traza no muestra ningún tool_call; el agente responde directamente |

### Niveles

| Nivel | Indicadores |
|---|---|
| **No logrado** | El grafo no corre o produce errores en la ejecución |
| **En desarrollo** | El grafo corre pero las 4 consultas no están todas presentes, o la consulta 3 no muestra ≥2 iteraciones |
| **Logrado** | Las 4 consultas corren con trazas completas; el grafo está correctamente construido; el ASCII del grafo está documentado |
| **Destacado** | Adicional: Ollama como alternativa al LLM de OpenAI demostrado; visualización del grafo con Mermaid o imagen; tests de edge cases (loop infinito, herramienta que falla, parámetro inválido) |

### Señales de alerta

- La consulta 3 muestra 2 llamadas pero a la misma herramienta → el agente usó la misma herramienta dos veces innecesariamente → revisar docstrings y prompts
- La consulta 4 igual invoca alguna herramienta → el agente no sabe cuándo NO usar herramientas → revisar el System Prompt
- No hay `recursion_limit` → riesgo de loop infinito en producción

---

## Criterio 4 — Análisis del ciclo ReAct (B.3) · 10 puntos

### ¿Qué evaluar?

Que el grupo comprenda el flujo de razonamiento del agente y no solo que "funcionó".

### Las 4 preguntas del análisis — qué esperar

| Pregunta | Respuesta esperada (nivel Logrado) |
|---|---|
| ¿En qué orden usó las herramientas? ¿Tiene sentido? | Describir el orden y justificarlo ("primero consultó X porque necesitaba ese dato para decidir si ejecutar Y") |
| ¿Cuántas iteraciones se ejecutaron? | Número exacto con evidencia de la traza |
| ¿Hubo iteraciones innecesarias? | Honestidad: si las hubo, describir cuáles y por qué pasaron |
| ¿Hubiera tomado otro camino con distinto resultado? | Análisis condicional ("si la herramienta X hubiera devuelto Y en lugar de Z, el agente hubiera...") |

### Niveles

| Nivel | Indicadores |
|---|---|
| **No logrado** | No hay análisis |
| **En desarrollo** | Las preguntas están respondidas pero de forma vaga o sin evidencia de la traza |
| **Logrado** | Las 4 preguntas están respondidas con evidencia de la traza real; el análisis del camino alternativo es coherente |
| **Destacado** | Además identifica el punto exacto donde el agente tomó la "decisión" más importante y explica qué información la disparó |

---

## Criterio 5 — Memoria persistente (C.1) · 20 puntos

### ¿Qué evaluar?

Que el checkpointer realmente persista entre llamadas separadas (no solo en el mismo invoke). El test tiene que mostrar que la memoria sobrevive entre llamadas distintas al agente.

### Cómo verificar que la memoria es real

El test tiene que cumplir esto: si cierro y abro el notebook, y llamo al agente con el mismo `thread_id` del turno 3, ¿recuerda información del turno 1?

Si solo la "recuerda" porque está en la misma sesión de Python → no es memoria persistente real → bajar un nivel.

### Los 3 turnos — qué verificar

| Turno | Señal de que la memoria funciona |
|---|---|
| 1 | El agente usa información del turno para su respuesta |
| 2 | La respuesta del turno 2 hace referencia implícita a lo dicho en el turno 1 sin que el usuario lo repita |
| 3 | La respuesta del turno 3 es imposible de dar correctamente sin los datos de ambos turnos anteriores |

### Niveles

| Nivel | Indicadores |
|---|---|
| **No logrado** | No implementaron checkpointer o los 3 turnos están en la misma cadena de mensajes (no son llamadas separadas) |
| **En desarrollo** | El checkpointer está configurado pero los turnos no demuestran que la información persiste (ej: el turno 3 no depende de los anteriores) |
| **Logrado** | Los 3 turnos separados muestran evidencia clara de memoria; la respuesta del turno 3 usa información de los turnos 1 y 2 de forma demostrable |
| **Destacado** | Además: verifican que la memoria persiste en un archivo `.db` real (muestran que al reiniciar el kernel y volver a invocar con el mismo thread_id, el agente recuerda); o implementan limpieza de sesión expirada |

### Señales de alerta

- Los 3 "turnos" están en el mismo `invoke` como lista de mensajes → no es memoria persistente
- El `thread_id` cambia entre turnos → no hay continuidad de sesión

---

## Criterio 6 — Arquitectura multiagente (C.2) · 15 puntos

### ¿Qué evaluar?

El diseño de la arquitectura y que el routing esté implementado con LLM (no con if/else sobre palabras clave).

### Lo que importa del routing

Un buen orquestador LLM puede clasificar consultas que no contienen las palabras clave exactas. Ejemplo: "Tengo una pregunta sobre la validez del permiso de mi empresa" → debería ir a `CATEGORIA_LEGAL` aunque no diga "legal".

Si el routing está implementado con `if "legal" in consulta.lower()` → no es routing con LLM → bajar un nivel.

### Niveles

| Nivel | Indicadores |
|---|---|
| **No logrado** | No hay arquitectura multiagente |
| **En desarrollo** | El diagrama está pero el routing no está implementado, o el routing es if/else sobre palabras clave |
| **Logrado** | Diagrama completo; orquestador implementado con LLM; ≥6 consultas probadas (2 por categoría) con resultados documentados |
| **Destacado** | El orquestador es un nodo de un grafo LangGraph; los subagentes también son grafos LangGraph; se demuestra que el orquestador clasifica correctamente consultas ambiguas que no contienen las palabras clave de la categoría |

### Señales de alerta

- El diagrama tiene solo 1 subagente → no es multiagente
- Las 6 consultas de prueba son obvias (contienen explícitamente la palabra de la categoría) → el routing no está realmente probado con variedad

---

## Criterio 7 — Comparación RAGAS (C.3) · 5 puntos

### ¿Qué evaluar?

Que el grupo corrió RAGAS sobre el agente (no solo sobre el RAG solo) y que documentó si agregar el agente degradó o no la calidad.

### Niveles

| Nivel | Indicadores |
|---|---|
| **No logrado** | No hay comparación RAGAS |
| **En desarrollo** | Hay números pero sin análisis; o los números son idénticos a E3 sin explicación |
| **Logrado** | Tabla E3 vs E4 completa; si alguna métrica bajó >0.10 hay análisis de por qué |
| **Destacado** | Además propone y documenta una mejora concreta para restaurar la métrica que bajó |

---

## Penalizaciones

| Situación | Penalización |
|---|---|
| API key real en algún commit | −15 puntos + aviso |
| El agente siempre usa todas las herramientas independientemente de la consulta | Criterio 3 no supera "En desarrollo" |
| La "memoria" funciona solo dentro de un mismo invoke | Criterio 5 baja un nivel |
| El routing es if/else sobre palabras clave | Criterio 6 baja un nivel |

---

## Retroalimentación sugerida

**Si el docstring es vago (criterio 1):**
> "Un buen criterio: si leés el docstring sin ver el código, ¿podés responder exactamente cuándo llamarías a esta herramienta y cuándo no? Si hay ambigüedad, hay riesgo de tool hallucination. Agregá las secciones 'Usar cuando' y 'NO usar cuando' con ejemplos concretos del dominio."

**Si la memoria no es persistente (criterio 5):**
> "La diferencia entre memoria de sesión y memoria persistente: la sesión vive mientras el kernel de Python está corriendo. La persistencia vive en disco. El SqliteSaver escribe en un archivo .db — si el grupo cierra el notebook y abre uno nuevo con el mismo thread_id, el agente debería recordar. Probar ese escenario."

**Si el routing es if/else (criterio 6):**
> "El valor de usar un LLM para routing es que puede clasificar consultas que no contienen las palabras clave exactas. 'Necesito información sobre mi situación de deuda' no contiene la palabra 'crédito' pero debería ir al subagente de crédito. Implementar el routing con un chain LLM que clasifica por intención, no por palabras clave."
