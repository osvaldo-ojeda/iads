# TP Integrador — IADS 3 (Desarrollo de Sistemas de IA)

Trabajo Práctico entregable y progresivo. Cada entrega suma una capa real de implementación sobre la anterior, siempre sobre el **dominio propio** que cada grupo elige en la Entrega 1. Ortelana Textil es el caso guía de la cátedra, no el entregable.

| Entrega | Unidad / Clases | Qué construye | Carpeta |
|---|---|---|---|
| **Entrega 1** | Unidad 1–2 · Clases 1 a 3 | Del diagnóstico al pipeline validado: caso + PEAS extendido + Matriz de Intenciones + contrato (JSON/SQL/System Prompt) + pipeline Pydantic con API real | [`entrega_1/`](entrega_1/) |
| **Entrega 2** | Unidad 3 · Clases 4 y 5 | Base de conocimiento vectorial: embeddings + similitud coseno + índice FAISS + ChromaDB persistente con filtrado híbrido + ETL y purga semántica | [`entrega_2/`](entrega_2/) |
| **Entrega 3** | Unidad 4 · Clases 6, 7 y 8 | Sistema RAG completo con evaluación: pipeline LCEL con guardrails + chunking con solapamiento + reranking + evaluación automática con RAGAS (faithfulness, relevancy, precision, recall) | [`entrega_3/`](entrega_3/) |
| **Entrega 4** | Unidad 5 · Clases 9 y 10 | Agente inteligente: herramientas con `@tool` + agente ReAct con LangGraph + memoria persistente con SQLite + arquitectura multiagente con orquestador | [`entrega_4/`](entrega_4/) |
| **Entrega 5** | Unidad 6 · Clases 11 a 14 (ensayo C15, defensa C16) | Sistema de IA en producción: FastAPI + Docker + logs estructurados + métricas/alertas + LangSmith + guardrails de seguridad + versionado de prompts + experimentos MLflow + ficha técnica + defensa formal en Clase 16 | [`entrega_5/`](entrega_5/) |

Cada carpeta contiene:
- `TP_EntregaN_Consigna.md` — la consigna para los alumnos (estructura, qué se entrega, rúbrica).
- `guia_correccion_EntregaN.md` — material docente, no compartir.

## Hilo conductor del año

```
E1: ¿Qué problema resuelve? → PEAS + Matriz de Intenciones + Pydantic
        ↓
E2: ¿Con qué conocimiento? → ChromaDB + ETL + embeddings
        ↓
E3: ¿Cómo responde? → RAG LCEL + chunking + reranking + RAGAS
        ↓
E4: ¿Cómo razona? → Agente ReAct + LangGraph + memoria + multiagente
        ↓
E5: ¿Cómo funciona en producción? → FastAPI + Docker + observabilidad + seguridad
```

## Entrega

Un único repositorio Git **público** por grupo (GitHub/GitLab). Se entrega solo el link, sin gestión de accesos. Como es público, **ninguna clave ni API key entra al repo** — `.env` en `.gitignore` desde el primer commit, solo se sube `.env.example` sin valores. Cada entrega agrega archivos y commits al mismo repo — el historial incremental es parte de la evaluación.

**Penalización automática:** API key real detectada en cualquier commit de cualquier entrega → −1.5 puntos de esa entrega + aviso inmediato al grupo para rotar la clave.

## Material de clase

Los ejercicios y demos por clase están en [`../clase_1/`](../clase_1/), [`../clase_2/`](../clase_2/), etc. La teoría de cada unidad está en `../../unidad_N/`.
