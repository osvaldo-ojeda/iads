# Clase 15: Clínica de Proyecto — Taller Integrador

**Asignatura:** Desarrollo de Sistemas de Inteligencia Artificial

**Objetivo Técnico:** Integrar los seis componentes del sistema completo (RAG + Agente + API + Docker + Observabilidad + Guardrails) sobre los datos reales del TP1, diagnosticar y resolver los cuellos de botella técnicos de cada grupo, y dejar cada sistema listo para la defensa de Clase 16.

> **Esta clase es distinta a todas las anteriores**
> No hay teoría nueva. El docente no da clase — facilita. Circula entre grupos, diagnostica problemas y desbloquea bloqueos técnicos. El objetivo es que todos los grupos salgan con algo funcionando y listo para defender. Un sistema simple que funciona vale más que un sistema ambicioso que no corre.

---

## Planificación de la Clase (4 horas)

| Bloque | Duración | Contenido |
|---|---|---|
| **Bloque 1** | 30 min | Diagnóstico grupal — self-assessment y priorización |
| **Bloque 2** | 75 min | Sprint de integración 1 — RAG + Agente |
| **Bloque 3** | 75 min | Sprint de integración 2 — API + Docker + Observabilidad |
| **Bloque 4** | 50 min | Ensayo de la demo — 5 minutos por grupo |
| **Cierre** | 10 min | Checklist final y preparación Clase 16 |

---

## Bloque 1: Diagnóstico Grupal (30 min)

### Self-assessment — 15 minutos en silencio

Cada grupo completa esta tabla honestamente antes de hablar con el docente. El objetivo no es mostrar que todo está bien — es identificar exactamente dónde están los bloqueos para priorizar el tiempo de hoy.

```
ESTADO DEL SISTEMA — TP1
Grupo: _______________  Dominio: _______________

COMPONENTE                          ESTADO          BLOQUEO (si aplica)
─────────────────────────────────────────────────────────────────────
Base de conocimiento (ChromaDB)   [ ] ✅ [ ] ⚠️ [ ] ❌   ________________
Pipeline RAG (Clase 6-7)          [ ] ✅ [ ] ⚠️ [ ] ❌   ________________
Dataset RAGAS + métricas          [ ] ✅ [ ] ⚠️ [ ] ❌   ________________
Agente con tools (Clase 9-10)     [ ] ✅ [ ] ⚠️ [ ] ❌   ________________
API FastAPI (Clase 11)            [ ] ✅ [ ] ⚠️ [ ] ❌   ________________
Docker funcionando (Clase 11)     [ ] ✅ [ ] ⚠️ [ ] ❌   ________________
Logs estructurados (Clase 12)     [ ] ✅ [ ] ⚠️ [ ] ❌   ________________
Guardrails activos (Clase 13)     [ ] ✅ [ ] ⚠️ [ ] ❌   ________________
Experimentos MLflow (Clase 14)    [ ] ✅ [ ] ⚠️ [ ] ❌   ________________

✅ = Funciona y está integrado
⚠️ = Funciona pero no integrado con el resto
❌ = No funciona o no empezado

PRIORIDAD HOY (marcar 3 máximo):
[ ] Integrar RAG con el agente
[ ] Levantar la API sin errores
[ ] Dockerizar el sistema
[ ] Mejorar métricas RAGAS
[ ] Agregar guardrails
[ ] Configurar LangSmith
[ ] Preparar la demo
```

---

### Puesta en común — 15 minutos

El docente recorre los self-assessments y agrupa los grupos por problema principal:

**Grupo A — Base inestable:** la base de conocimiento tiene problemas (pocos documentos, embeddings de baja calidad, filtros mal configurados). Prioridad: Bloque 2, enfocarse en el RAG antes que en la API.

**Grupo B — Integración pendiente:** los componentes funcionan por separado pero no están conectados. Prioridad: Bloques 2 y 3 en orden.

**Grupo C — API con errores:** el sistema funciona en notebook pero la API no levanta. Prioridad: Bloque 3, debugging de FastAPI/Docker.

**Grupo D — Listos para pulir:** el sistema funciona end-to-end pero falta calidad (métricas bajas, sin guardrails, demo desordenada). Prioridad: Bloque 4, preparar la presentación.

> **Para el docente**
> Asignar un bloqueo de 20 minutos a cada grupo durante la clase para sentarse con ellos específicamente. No tratar de ayudar a todos al mismo tiempo — mejor ir uno por uno con foco.

---

## Bloque 2: Sprint de Integración 1 — RAG + Agente (75 min)

### El objetivo del sprint

Al terminar este bloque, cada grupo debe poder ejecutar esta secuencia sin errores:

```python
# Test de integración RAG + Agente
pregunta_test = "pregunta real del dominio del TP1"

# Paso 1: RAG funciona solo
respuesta_rag = chain_rag.invoke(pregunta_test)
assert len(respuesta_rag) > 0, "RAG no devuelve respuesta"

# Paso 2: La tool RAG funciona dentro del agente
resultado_agente = agente_tp1.invoke(
    {"messages": [HumanMessage(content=pregunta_test)]}
)
assert resultado_agente["messages"][-1].content, "Agente no devuelve respuesta"

print("✅ Integración RAG + Agente: OK")
```

---

### Los cinco problemas más comunes en este sprint

**Problema 1 — La base de conocimiento es demasiado pequeña**

```
Síntoma: el RAG siempre devuelve los mismos 2-3 documentos para cualquier consulta.
         Las métricas RAGAS son inconsistentes.

Diagnóstico:
vectorstore._collection.count()  # Si devuelve < 15, es el problema

Solución rápida — enriquecer con el LLM:
prompt_enriquecimiento = """
Generá 10 documentos adicionales para una base de conocimiento de [dominio].
Cada documento debe ser un párrafo de 3-5 oraciones con información específica,
técnica y variada. Devolvé un JSON array con la estructura:
[{"id": "DOC-001", "texto": "...", "categoria": "..."}]
"""
documentos_extra = llm.invoke(prompt_enriquecimiento)
# Parsear y agregar a ChromaDB con upsert
```

**Problema 2 — El agente ignora la tool RAG y responde de memoria**

```python
# Síntoma: el agente responde sin llamar a ninguna herramienta

# Diagnóstico: revisar el docstring de la tool
@tool
def consultar_base_conocimiento(consulta: str) -> str:
    """
    ❌ MAL — demasiado genérico:
    Consulta la base de conocimiento.

    ✅ BIEN — específico con cuándo usarla:
    Busca información específica en la base de conocimiento de [dominio].
    Usar SIEMPRE cuando el usuario pregunta sobre [tema específico],
    [otro tema], o [tercer tema]. Esta herramienta tiene acceso a
    [descripción del contenido de la base].
    """
    return rag_chain.invoke(consulta)
```

**Problema 3 — El agente entra en loop infinito**

```python
# Síntoma: el agente sigue llamando herramientas sin terminar

# Solución: agregar límite explícito en la compilación
agente = grafo.compile(
    checkpointer=checkpointer,
    interrupt_before=[]  # Sin interrupciones
)

# Y en la invocación:
resultado = agente.invoke(
    estado_inicial,
    config={
        "configurable": {"thread_id": thread_id},
        "recursion_limit": 8  # Máximo 8 iteraciones
    }
)
```

**Problema 4 — Métricas RAGAS muy bajas (< 0.5)**

```
Síntoma: faithfulness < 0.5 o context_recall < 0.5

Diagnóstico por métrica:
- Faithfulness baja → el LLM agrega información que no está en el contexto
  Solución: bajar temperature a 0, reforzar el "ÚNICAMENTE el contexto" en el prompt

- Context_recall baja → el retriever no encuentra los documentos relevantes
  Solución: aumentar k, revisar chunk_size, verificar que los documentos
  tienen texto rico en la descripción semántica

- Context_precision baja → el retriever trae documentos irrelevantes
  Solución: agregar metadatos y filtros, implementar reranking de Clase 7
```

**Problema 5 — LangSmith no registra las trazas**

```python
# Verificar que las variables de entorno están bien configuradas
import os
print("LANGCHAIN_TRACING_V2:", os.getenv("LANGCHAIN_TRACING_V2"))
print("LANGCHAIN_API_KEY:", os.getenv("LANGCHAIN_API_KEY")[:10] + "...")
print("LANGCHAIN_PROJECT:", os.getenv("LANGCHAIN_PROJECT"))

# Si están bien pero no aparecen trazas, forzar un flush:
from langsmith import Client
client = Client()
print("Runs recientes:", len(list(client.list_runs(project_name=os.getenv("LANGCHAIN_PROJECT")))))
```

---

### Checkpoint del Bloque 2 — antes de seguir

```python
# Cada grupo corre este script antes de pasar al Bloque 3
def checkpoint_rag_agente(agente, chain_rag, preguntas_test: list) -> bool:
    print("=== CHECKPOINT RAG + AGENTE ===")
    todos_ok = True

    for pregunta in preguntas_test[:3]:  # Solo 3 preguntas para ser rápido
        try:
            # Test RAG directo
            resp_rag = chain_rag.invoke(pregunta)
            assert len(resp_rag) > 10
            print(f"✅ RAG: '{pregunta[:40]}...' → OK")

            # Test agente
            resp_agente = agente.invoke(
                {"messages": [HumanMessage(content=pregunta)],
                 "herramientas_usadas": [], "iteraciones": 0},
                config={"configurable": {"thread_id": "checkpoint_test"}}
            )
            assert resp_agente["messages"][-1].content
            print(f"✅ Agente: '{pregunta[:40]}...' → OK")

        except Exception as e:
            print(f"❌ FALLA: '{pregunta[:40]}...' → {e}")
            todos_ok = False

    if todos_ok:
        print("\n✅ CHECKPOINT PASSED — pueden avanzar al Bloque 3")
    else:
        print("\n❌ CHECKPOINT FAILED — resolver antes de avanzar")

    return todos_ok
```

---

## Bloque 3: Sprint de Integración 2 — API + Docker + Observabilidad (75 min)

### El objetivo del sprint

Al terminar este bloque, el comando `curl http://localhost:8000/health` debe devolver `200 OK` y `POST /consultar` debe responder con el agente del TP1.

---

### Los cinco problemas más comunes en este sprint

**Problema 1 — La API levanta pero `/consultar` da 500**

```bash
# Ver el error completo en los logs
docker-compose logs ortelana-api --tail=50

# El error más común: el sistema multiagente no puede inicializarse
# porque las rutas de ChromaDB o SQLite son distintas dentro del contenedor

# Solución: usar rutas relativas a /app/data dentro del Dockerfile
# En ortelana_agent.py:
PERSIST_DIR = os.getenv("PERSIST_DIR", "/app/data/vectordb")
MEMORY_DB = os.getenv("MEMORY_DB", "/app/data/memoria.db")

client = chromadb.PersistentClient(path=PERSIST_DIR)
checkpointer = SqliteSaver.from_conn_string(MEMORY_DB)
```

**Problema 2 — Docker build falla por dependencias**

```dockerfile
# Error común: librerías que necesitan compiladores C
# Solución: agregar build-essentials al Dockerfile

FROM python:3.11-slim

# Agregar dependencias del sistema antes de pip install
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Problema 3 — Las variables de entorno no llegan al contenedor**

```bash
# Verificar que el .env tiene las variables correctas
cat .env

# Verificar que docker-compose las lee
docker-compose config  # Muestra la config resuelta con las variables

# Si las variables no aparecen, forzarlas explícitamente:
# docker-compose.yml
environment:
  - OPENAI_API_KEY=${OPENAI_API_KEY:?Variable OPENAI_API_KEY no definida}
  # El :? hace que docker-compose falle con error claro si la variable no existe
```

**Problema 4 — La memoria del agente no persiste entre requests**

```python
# Síntoma: el segundo request no recuerda el primero aunque usen el mismo thread_id

# Causa: el checkpointer se inicializa dentro de la función del endpoint
# → cada request crea un nuevo checkpointer sin historia

# ❌ MAL — checkpointer dentro del endpoint
@app.post("/consultar")
async def consultar(request: ConsultaRequest):
    checkpointer = MemorySaver()  # Nuevo checkpointer en cada request
    agente = grafo.compile(checkpointer=checkpointer)
    ...

# ✅ BIEN — checkpointer como variable global del módulo
checkpointer = SqliteSaver.from_conn_string("/app/data/memoria.db")
agente_tp1 = grafo.compile(checkpointer=checkpointer)

@app.post("/consultar")
async def consultar(request: ConsultaRequest):
    resultado = agente_tp1.invoke(...)  # Usa el checkpointer global
```

**Problema 5 — El endpoint `/metricas` devuelve todo en cero**

```python
# Causa: el objeto MetricasTP1 se instancia dentro del endpoint
# en vez de ser una variable global compartida

# ❌ MAL
@app.get("/metricas")
async def metricas():
    m = MetricasTP1()  # Nueva instancia vacía en cada request
    return m.obtener_resumen()

# ✅ BIEN — instancia global
from metrics import MetricasTP1
metricas_globales = MetricasTP1()

@app.get("/metricas")
async def metricas():
    return metricas_globales.obtener_resumen()

@app.post("/consultar")
async def consultar(request):
    ...
    metricas_globales.registrar_consulta(...)  # Actualizar la instancia global
```

---

### Checklist de integración completa

```bash
# Script de verificación end-to-end
#!/bin/bash
echo "=== VERIFICACIÓN SISTEMA TP1 ==="

# 1. Health check
echo -n "Health check... "
STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
[ "$STATUS" = "200" ] && echo "✅ OK" || echo "❌ FALLA (HTTP $STATUS)"

# 2. Consulta básica
echo -n "Consulta al agente... "
RESP=$(curl -s -X POST http://localhost:8000/consultar \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "consulta de prueba del dominio", "thread_id": "verify_001"}')
echo $RESP | python3 -c "import sys,json; d=json.load(sys.stdin); print('✅ OK' if d.get('respuesta') else '❌ FALLA')"

# 3. Memoria entre turnos
echo -n "Memoria entre turnos... "
curl -s -X POST http://localhost:8000/consultar \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "primer mensaje de la sesión", "thread_id": "memory_test"}' > /dev/null
ESTADO=$(curl -s http://localhost:8000/estado/memory_test)
echo $ESTADO | python3 -c "import sys,json; d=json.load(sys.stdin); print('✅ OK' if d.get('mensajes') else '❌ FALLA')"

# 4. Métricas
echo -n "Endpoint métricas... "
M=$(curl -s http://localhost:8000/metricas)
echo $M | python3 -c "import sys,json; d=json.load(sys.stdin); print('✅ OK' if 'total_consultas' in d else '❌ FALLA')"

echo "=== FIN VERIFICACIÓN ==="
```

---

## Bloque 4: Ensayo de la Demo (50 min)

### El formato de la defensa de Clase 16

Cada grupo tiene **15 minutos** en Clase 16:
- **5 min** — presentación del problema y la arquitectura
- **7 min** — demo en vivo del sistema funcionando
- **3 min** — preguntas del docente

El ensayo de hoy simula esos 15 minutos. El docente cronometra y da feedback técnico.

---

### El template de la demo — 7 minutos en vivo

```
ESTRUCTURA DE LA DEMO (7 minutos)

[0:00 - 1:00] Mostrar la arquitectura
→ Diagrama del sistema: base de conocimiento, RAG, agente, API
→ Una oración por componente: "Acá están los documentos indexados..."

[1:00 - 3:30] Demo del caso feliz
→ Abrir Swagger UI en /docs o usar curl
→ Correr 2-3 consultas que muestren el valor del sistema
→ Mostrar que el agente usa las herramientas correctas
→ Mostrar una conversación multi-turno con memoria

[3:30 - 5:00] Demo de robustez
→ Un ataque de red teaming — mostrar que el guardrail lo bloquea
→ Una consulta fuera del dominio — mostrar que dice "no tengo información"
→ Mostrar el endpoint /metricas con datos reales

[5:00 - 6:30] Demo técnica
→ Mostrar los logs estructurados en la terminal
→ Mostrar una traza en LangSmith
→ Mostrar un experimento en MLflow (si tienen)

[6:30 - 7:00] Cierre
→ Una métrica RAGAS del sistema
→ "El sistema responde el X% de las consultas correctamente según RAGAS"
```

---

### Las preguntas que hace el docente en la defensa

> **Para el docente — estas son las preguntas de evaluación técnica**

**Sobre el RAG:**
- "¿Qué chunk_size eligieron y por qué?"
- "¿Cómo saben que el retriever está encontrando los documentos correctos?"
- "¿Qué pasa si alguien hace una consulta para la que no tienen documentos?"

**Sobre el agente:**
- "¿Cuántas herramientas tiene el agente y cuándo usa cada una?"
- "¿Cómo evitaron que el agente entre en loop?"
- "¿Cómo guarda la memoria entre turnos?"

**Sobre la API:**
- "¿Qué pasa si el LLM tarda 30 segundos en responder? ¿El request hace timeout?"
- "¿Cómo manejan requests concurrentes — si 10 distribuidores consultan al mismo tiempo?"

**Sobre observabilidad y seguridad:**
- "Mostrá un log de error en el sistema"
- "¿Qué guardrail implementaron y qué ataque bloquea?"
- "¿Cuál es tu métrica RAGAS más baja y cómo la mejorarías?"

---

### Feedback por grupo — lo que anota el docente

```
FEEDBACK TÉCNICO — ENSAYO DE DEMO
Grupo: _____________

FORTALEZAS:
□ Base de conocimiento sólida y bien diseñada
□ Agente toma decisiones correctas
□ API robusta con manejo de errores
□ Demo fluida y bien estructurada
□ Guardrails funcionando correctamente
□ Métricas RAGAS documentadas

A MEJORAR ANTES DE CLASE 16:
□ ___________________________________________
□ ___________________________________________
□ ___________________________________________

ESTADO: [ ] Listo para defender  [ ] Necesita trabajo  [ ] Crítico
```

---

### El criterio de "listo para defender"

Un sistema está listo para defender si cumple estos cinco mínimos:

```
✅ MÍNIMO 1: La API responde sin errores
   curl POST /consultar devuelve una respuesta coherente del dominio

✅ MÍNIMO 2: El RAG usa documentos reales
   Las respuestas se fundamentan en la base de conocimiento — no en el LLM solo

✅ MÍNIMO 3: Al menos una herramienta activa
   El agente llama al menos a una tool durante una consulta típica

✅ MÍNIMO 4: Al menos un guardrail activo
   Una consulta maliciosa o fuera de dominio es bloqueada o redirigida

✅ MÍNIMO 5: Métricas RAGAS documentadas
   Tienen un número — aunque sea bajo — que dice cuán bien funciona el sistema

Todo lo demás (Docker, MLflow, LangSmith, múltiples guardrails, A/B testing)
suma puntos pero no es bloqueante para defender.
```

---

## Cierre (10 min)

### Checklist final para Clase 16

```
PREPARACIÓN PARA LA DEFENSA — CLASE 16

TÉCNICO:
□ El sistema corre sin errores desde cero (nuevo entorno, nuevas credenciales)
□ requirements.txt actualizado con todas las dependencias
□ .env.example con las variables necesarias (sin valores reales)
□ README.md con instrucciones de instalación y ejecución
□ Dataset RAGAS con métricas documentadas

PRESENTACIÓN:
□ Diagrama de arquitectura listo (puede ser draw.io, Mermaid o papel)
□ Las 2-3 consultas de demo elegidas y probadas
□ El ataque de red teaming probado y funcionando el guardrail
□ Los números clave memorizados: docs en la base, métricas RAGAS, herramientas

DEMO:
□ Probada end-to-end en las últimas 24 horas
□ Funciona desde la URL pública o localmente con Docker
□ Tienen un plan B si algo falla en vivo (capturas de pantalla del sistema corriendo)
```

> **El consejo más importante para la defensa**
> Demostrar algo simple que funciona perfectamente vale más que demostrar algo ambicioso que falla a mitad. Si tienen dudas sobre si algo va a funcionar en vivo, no lo incluyan en la demo. La confianza técnica se demuestra sabiendo los límites del sistema.

---

## Bibliografía de la Clase

Esta clase no tiene bibliografía nueva — es la integración de todo lo visto en las clases anteriores. Para referencia rápida durante la clínica:

- **RAG + ChromaDB:** Clases 5, 6 y 7
- **Agente + LangGraph:** Clases 9 y 10
- **API + Docker:** Clase 11
- **Observabilidad:** Clase 12
- **Guardrails:** Clase 13
- **MLflow + PromptLayer:** Clase 14
