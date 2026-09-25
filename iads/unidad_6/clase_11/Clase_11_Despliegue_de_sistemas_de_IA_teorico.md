# Clase 11: Despliegue de Sistemas de IA — APIs con FastAPI y Docker

**Asignatura:** Desarrollo de Sistemas de Inteligencia Artificial

**Objetivo Técnico:** Exponer el sistema multiagente de Ortelana Textil como una API HTTP con FastAPI, definir endpoints REST con schemas Pydantic, y containerizar el sistema completo con Docker para que pueda ejecutarse en cualquier entorno — el paso de prototipo en Colab a producto desplegable.

> **Conexión con clases anteriores**
> En Clase 10 construimos el sistema multiagente de Ortelana con memoria y orquestador. Hoy lo sacamos de Colab y lo convertimos en un producto real: una API que cualquier sistema externo puede consumir — el WhatsApp de Ortelana, el formulario web, el ERP — sin saber nada de Python ni de LangGraph.

---

## Estructura de la Clase

| Bloque | Contenido |
|---|---|
| **Bloque 1** | Del prototipo al producto — por qué Colab no es suficiente |
| **Bloque 2** | FastAPI: exponer el agente como API REST |
| **Bloque 3** | Laboratorio: los tres endpoints de Ortelana |
| **Bloque 4** | Docker: containerizar el sistema completo |
| **Cierre** | Resumen, tarea asincrónica y conexión con Clase 12 |

---

## Bloque 1: Del Prototipo al Producto

### El problema de Colab en producción

El sistema multiagente de Ortelana funciona perfectamente — en Colab. Pero tiene cinco problemas que lo hacen inusable como producto real:

**Problema 1 — Solo lo pueden usar ustedes**
Un distribuidor no puede abrir un Jupyter notebook. El equipo comercial de Ortelana tampoco. El sistema existe pero nadie más puede accederlo.

**Problema 2 — Muere cuando cierran la pestaña**
Colab desconecta el runtime después de un tiempo de inactividad. El `SqliteSaver` con la memoria de los distribuidores desaparece.

**Problema 3 — "En mi máquina funciona"**
El sistema depende de que tengan instaladas exactamente las mismas librerías, la misma versión de Python y las mismas variables de entorno. En otra máquina — o en un servidor — puede romperse por cualquier dependencia.

**Problema 4 — No escala**
Si 50 distribuidores consultan al mismo tiempo, Colab no puede manejar 50 kernels concurrentes. Un servidor necesita manejar múltiples requests simultáneos.

**Problema 5 — No se integra con nada**
El WhatsApp Business API de Ortelana manda HTTP requests. El formulario web manda HTTP requests. El ERP manda HTTP requests. Colab no habla HTTP — habla Python interactivo.

> **La solución**
> Una **API HTTP** es la interfaz universal. Cualquier sistema que pueda hacer un request HTTP puede consumir el agente — sin importar el lenguaje, la plataforma o el dispositivo. FastAPI convierte el sistema Python en una API. Docker garantiza que corre igual en cualquier entorno.

---

### La arquitectura del sistema desplegado

```
                    Internet
                       │
            ┌──────────▼──────────┐
            │    API FastAPI       │  ← Puerto 8000
            │  /consultar         │
            │  /estado/{id}       │
            │  /health            │
            └──────────┬──────────┘
                       │
            ┌──────────▼──────────┐
            │  Sistema Ortelana   │
            │  (Clase 10)         │
            │  LangGraph +        │
            │  Checkpointer       │
            └──────────┬──────────┘
                       │
         ┌─────────────┼─────────────┐
         ▼             ▼             ▼
    ChromaDB       SQLite DB      OpenAI API
  (catálogo +    (memoria de    (LLM + embeddings)
   reglamento)    sesiones)
```

---

### HTTP en 3 minutos — lo que necesitan saber

```
REQUEST (lo que manda el cliente):
POST /consultar HTTP/1.1
Content-Type: application/json

{"pregunta": "¿Tienen denim azul en Córdoba?", "thread_id": "dist_001"}

RESPONSE (lo que devuelve el servidor):
HTTP/1.1 200 OK
Content-Type: application/json

{"respuesta": "Sí, tenemos TELA-001 disponible...", "herramientas_usadas": ["catalogo"]}
```

**Los status codes que van a usar:**

| Código | Significado | Cuándo usarlo |
|---|---|---|
| `200 OK` | Todo bien | Respuesta exitosa |
| `422 Unprocessable Entity` | El body del request está mal | Pydantic rechazó los datos |
| `500 Internal Server Error` | Algo explotó en el servidor | Excepción no manejada |

---

## Bloque 2: FastAPI — Exponer el Agente

### Por qué FastAPI y no Flask o Django

| | FastAPI | Flask | Django |
|---|---|---|---|
| **Velocidad** | Muy alta (async nativo) | Media | Media |
| **Validación automática** | ✅ Pydantic integrado | ❌ Manual | Parcial |
| **Docs automáticas** | ✅ Swagger en /docs | ❌ No | ❌ No |
| **Para APIs de IA** | ✅ Ideal | Funciona | Excesivo |
| **Curva de aprendizaje** | Baja | Muy baja | Alta |

> **El argumento definitivo**
> FastAPI genera documentación interactiva automática en `/docs`. Apenas levanten el servidor pueden probar todos los endpoints desde el navegador — sin Postman, sin escribir código de test. Para una clase, es invaluable.

---

### Instalación

```bash
pip install fastapi uvicorn[standard] pydantic
```

`uvicorn` es el servidor ASGI que corre FastAPI. `[standard]` incluye soporte para WebSockets y otras features.

---

### El archivo de la API — estructura base

```python
# api.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv

load_dotenv()

# ── Importar el sistema de Ortelana de Clase 10 ───────────────────────────────
# from ortelana_agent import sistema_ortelana, EstadoOrtelana
# (en el laboratorio conectamos con el código real)

app = FastAPI(
    title="Ortelana Textil — API de Agente IA",
    description="Sistema multiagente para consultas comerciales de distribuidores",
    version="1.0.0"
)
```

---

### Los schemas Pydantic — el contrato de la API

Ya conocen Pydantic de Clase 3. Acá lo usamos para definir qué acepta y qué devuelve cada endpoint:

```python
# schemas.py
from pydantic import BaseModel, Field
from typing import Optional, List

class ConsultaRequest(BaseModel):
    """Lo que manda el cliente en el body del POST /consultar"""
    pregunta: str = Field(
        description="Consulta del distribuidor en lenguaje natural",
        example="¿Tienen denim azul disponible en Córdoba?"
    )
    thread_id: str = Field(
        description="ID único de la sesión/conversación del distribuidor",
        example="textiles_norpatagonia_001"
    )

class ConsultaResponse(BaseModel):
    """Lo que devuelve el servidor"""
    respuesta: str
    thread_id: str
    herramientas_usadas: List[str]
    exito: bool = True

class EstadoResponse(BaseModel):
    """Historial de una sesión"""
    thread_id: str
    mensajes: List[dict]
    cuit_identificado: Optional[str]
    sucursal_preferida: Optional[str]

class HealthResponse(BaseModel):
    """Estado del servidor"""
    status: str
    version: str
    sistema_activo: bool
```

> **Pregunta #1**
> ¿Por qué definimos schemas separados para Request y Response en lugar de usar un solo dict?
>
> **Análisis:** Por las mismas razones que en Clase 3 — el contrato explícito garantiza que el servidor rechaza automáticamente requests malformados (Pydantic valida antes de que toque el agente) y documenta exactamente qué devuelve el sistema. FastAPI usa estos schemas para generar la documentación automática en `/docs`.

---

### Los tres endpoints

```python
# api.py (continuación)
from langchain_core.messages import HumanMessage

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Verificar que el servidor está vivo.
    Usado por sistemas de monitoreo para saber si la API está operativa.
    """
    return HealthResponse(
        status="ok",
        version="1.0.0",
        sistema_activo=True
    )


@app.post("/consultar", response_model=ConsultaResponse)
async def consultar_agente(request: ConsultaRequest):
    """
    Endpoint principal. Recibe una consulta de un distribuidor
    y devuelve la respuesta del sistema multiagente de Ortelana.
    """
    try:
        config = {"configurable": {"thread_id": request.thread_id}}
        estado_inicial = {
            "messages": [HumanMessage(content=request.pregunta)],
            "cuit_identificado": None,
            "sucursal_preferida": None,
            "categoria_distribuidor": None,
            "herramientas_usadas": [],
            "iteraciones": 0
        }

        resultado = sistema_ortelana.invoke(estado_inicial, config=config)

        return ConsultaResponse(
            respuesta=resultado["messages"][-1].content,
            thread_id=request.thread_id,
            herramientas_usadas=resultado.get("herramientas_usadas", [])
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error en el sistema multiagente: {str(e)}"
        )


@app.get("/estado/{thread_id}", response_model=EstadoResponse)
async def obtener_estado(thread_id: str):
    """
    Devuelve el historial y el contexto de una sesión específica.
    Útil para el equipo comercial de Ortelana para ver el historial
    de conversaciones de un distribuidor.
    """
    try:
        config = {"configurable": {"thread_id": thread_id}}
        estado = sistema_ortelana.get_state(config)

        if not estado or not estado.values:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontró sesión con thread_id: {thread_id}"
            )

        valores = estado.values
        mensajes = [
            {"rol": type(m).__name__, "contenido": m.content}
            for m in valores.get("messages", [])
        ]

        return EstadoResponse(
            thread_id=thread_id,
            mensajes=mensajes,
            cuit_identificado=valores.get("cuit_identificado"),
            sucursal_preferida=valores.get("sucursal_preferida")
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

---

### Levantar el servidor

```bash
# En la terminal, desde el directorio del proyecto
uvicorn api:app --reload --port 8000

# --reload: reinicia el servidor automáticamente al guardar cambios
# --port 8000: el puerto donde escucha

# Output esperado:
# INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
# INFO:     Started reloader process
```

Abrir en el navegador: **http://localhost:8000/docs**

> **Lo que aparece en /docs**
> Swagger UI generado automáticamente con todos los endpoints, sus schemas, ejemplos y un botón "Try it out" para probarlos en vivo. Es la documentación que se auto-actualiza cada vez que cambian el código.

---

## Bloque 3: Laboratorio — Los Tres Endpoints de Ortelana

### Estructura de archivos del proyecto

```
ortelana_api/
├── api.py                  ← FastAPI app y endpoints
├── schemas.py              ← Modelos Pydantic
├── ortelana_agent.py       ← Sistema multiagente de Clase 10
├── tools.py                ← Las tres herramientas del agente
├── .env                    ← Variables de entorno (NO subir a Git)
├── .gitignore
├── requirements.txt        ← Dependencias del proyecto
├── Dockerfile              ← Para Docker (Bloque 4)
└── docker-compose.yml      ← Para Docker Compose (Bloque 4)
```

---

### El `requirements.txt` — dependencias explícitas

```txt
fastapi==0.111.0
uvicorn[standard]==0.30.0
langchain==0.2.0
langchain-openai==0.1.7
langchain-chroma==0.1.1
langgraph==0.1.1
pydantic==2.7.0
python-dotenv==1.0.1
chromadb==0.5.0
tiktoken==0.7.0
```

> **Por qué fijar versiones exactas**
> Sin versiones fijas, `pip install` instala la última versión disponible. Si en 6 meses una librería cambia su API, el sistema se rompe silenciosamente. Las versiones fijas garantizan que el sistema que funciona hoy sigue funcionando en 6 meses.

---

### Probar la API con curl

```bash
# Test 1: Health check
curl http://localhost:8000/health

# Output: {"status":"ok","version":"1.0.0","sistema_activo":true}

# Test 2: Consulta al agente
curl -X POST http://localhost:8000/consultar \
  -H "Content-Type: application/json" \
  -d '{
    "pregunta": "Soy Textiles Norpatagonia, CUIT 30-71234567-8. ¿Tienen denim en Córdoba?",
    "thread_id": "norpatagonia_001"
  }'

# Test 3: Segunda consulta — misma sesión (memoria activa)
curl -X POST http://localhost:8000/consultar \
  -H "Content-Type: application/json" \
  -d '{
    "pregunta": "¿Y jersey gris también tienen ahí?",
    "thread_id": "norpatagonia_001"
  }'

# Test 4: Ver el estado de la sesión
curl http://localhost:8000/estado/norpatagonia_001
```

> **Pregunta #2**
> En el Test 3, el agente debería recordar que "ahí" es Córdoba y que el CUIT ya fue validado. ¿Dónde vive esa memoria — en FastAPI, en LangGraph o en SQLite?
>
> **Análisis:** En SQLite, a través del `SqliteSaver` de LangGraph. FastAPI es stateless — no guarda nada entre requests. Cada request llega con el `thread_id` y LangGraph usa ese ID para recuperar el estado de SQLite. Esta separación es correcta: la API maneja el protocolo HTTP, LangGraph maneja la lógica del agente, SQLite maneja la persistencia.

---

### Manejo de errores — lo que no puede faltar en producción

```python
# api.py — agregar middleware de logging
import logging
from fastapi import Request
from fastapi.responses import JSONResponse
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Registra cada request: método, path, tiempo de respuesta."""
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time

    logger.info(
        f"{request.method} {request.url.path} "
        f"→ {response.status_code} "
        f"({duration:.3f}s)"
    )
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Captura cualquier excepción no manejada y devuelve un JSON limpio."""
    logger.error(f"Error no manejado: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Error interno del servidor", "detalle": str(exc)}
    )
```

---

## Bloque 4: Docker — Containerizar el Sistema

### El problema que Docker resuelve

```
Sin Docker:
Dev: "Funciona en mi máquina"
Servidor: pip install falla porque Python es 3.10 en vez de 3.11
          chromadb necesita una librería del sistema que no está instalada
          las variables de entorno no están configuradas
          → El sistema no arranca

Con Docker:
"Mi máquina" está empaquetada en una imagen
Servidor descarga la imagen y corre exactamente lo mismo
→ Funciona siempre, en cualquier lado
```

**La analogía:** Docker es como enviar el sistema completo en una caja sellada — no solo el código, sino también el sistema operativo mínimo, las librerías, las configuraciones y las instrucciones de arranque. El destinatario solo necesita abrir la caja.

---

### El Dockerfile — la receta de la imagen

```dockerfile
# Dockerfile
# Imagen base: Python 3.11 liviano
FROM python:3.11-slim

# Directorio de trabajo dentro del contenedor
WORKDIR /app

# Copiar primero el requirements.txt (optimización de cache)
# Si no cambian las dependencias, Docker reutiliza esta capa
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Crear directorio para la base de datos SQLite y ChromaDB
RUN mkdir -p /app/data

# El puerto que expone el contenedor
EXPOSE 8000

# Comando para arrancar el servidor
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

> **¿Por qué `--host 0.0.0.0`?**
> Sin esto, uvicorn solo escucha en `localhost` — dentro del contenedor. Con `0.0.0.0` escucha en todas las interfaces de red, lo que permite que el tráfico externo llegue al contenedor.

---

### El docker-compose.yml — orquestar el sistema completo

```yaml
# docker-compose.yml
version: "3.8"

services:
  ortelana-api:
    build: .                          # Usar el Dockerfile del directorio actual
    ports:
      - "8000:8000"                   # Puerto local:puerto contenedor
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}          # Leer del .env del host
      - LANGCHAIN_API_KEY=${LANGCHAIN_API_KEY}
      - LANGCHAIN_TRACING_V2=${LANGCHAIN_TRACING_V2}
    volumes:
      - ./data:/app/data              # Persistir la BD SQLite y ChromaDB
    restart: unless-stopped           # Reiniciar si el contenedor falla
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

> **Variables de entorno en Docker — regla de oro**
> Las API keys NUNCA van en el Dockerfile ni en el docker-compose.yml — esos archivos se suben a Git. Las variables sensibles se pasan desde el `.env` del host en tiempo de ejecución. El `${OPENAI_API_KEY}` en el compose lee la variable del sistema operativo del host, no del código.

---

### Comandos Docker esenciales

```bash
# Construir la imagen
docker build -t ortelana-api .

# Levantar con docker-compose (lee el .env automáticamente)
docker-compose up

# Levantar en background
docker-compose up -d

# Ver los logs
docker-compose logs -f ortelana-api

# Detener
docker-compose down

# Verificar que el contenedor está corriendo
docker ps

# Entrar al contenedor para debuggear
docker exec -it ortelana-api bash
```

---

### Probar el sistema containerizado

```bash
# Con el contenedor corriendo, los mismos tests de antes
curl http://localhost:8000/health
curl -X POST http://localhost:8000/consultar \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "¿Tienen seda natural?", "thread_id": "test_docker_001"}'
```

> **Pregunta #3**
> Si el contenedor se reinicia (por un deploy o por un error), ¿se pierde la memoria de los distribuidores?
>
> **Análisis:** No, porque el SQLite está en un **volume** (`./data:/app/data`). Los volumes persisten fuera del contenedor — aunque el contenedor se destruya y recree, los datos siguen ahí. Sin el volume, sí se perdería todo al reiniciar.

---

## Cierre y Material Asincrónico

### Resumen de la clase

- **FastAPI** convierte el sistema Python en una API HTTP consumible por cualquier plataforma. Schemas Pydantic + documentación automática en `/docs`.
- **Los tres endpoints:** `POST /consultar` (el agente), `GET /estado/{id}` (historial), `GET /health` (monitoreo).
- **Separación de responsabilidades:** FastAPI maneja HTTP, LangGraph maneja la lógica del agente, SQLite maneja la persistencia. Cada capa hace una sola cosa.
- **Docker** empaqueta el sistema completo — código + dependencias + configuración — en una imagen portable. Resuelve el "en mi máquina funciona".
- **Variables de entorno:** nunca en el código, nunca en el Dockerfile. Siempre desde el entorno del host en runtime.

---

### Material asincrónico — Entre Clase 11 y Clase 12

> **La Clase 12 arranca con este entregable**

**Actividad — API del TP1 funcionando:**

Cada grupo expone su sistema del TP1 como una API FastAPI con al menos estos dos endpoints:

```python
# Endpoint obligatorio 1: consulta al agente/RAG del TP1
POST /consultar
Body: {"pregunta": str, "thread_id": str}

# Endpoint obligatorio 2: health check
GET /health
```

**Checklist de entrega:**
```
✅ La API levanta con uvicorn sin errores
✅ POST /consultar responde con el agente del TP1
✅ GET /health devuelve 200 OK
✅ Las API keys están en .env, no en el código
✅ El requirements.txt tiene todas las dependencias con versiones
✅ (Bonus) Dockerfile que buildea sin errores
```

**Probar con curl o desde /docs antes de la clase:**
```bash
curl -X POST http://localhost:8000/consultar \
  -H "Content-Type: application/json" \
  -d '{"pregunta": "pregunta de prueba de tu dominio", "thread_id": "test_001"}'
```

---

### Conexión con Clase 12

La API ya existe y funciona. Pero en producción una API sin control es un pasivo: cualquiera puede usarla, no sabemos cuánto cuesta cada request, no detectamos cuando algo falla, y no podemos mejorarla si no medimos su rendimiento. En Clase 12 vemos los **trade-offs técnicos de producción** — costo, latencia y calidad — y cómo tomar decisiones arquitectónicas basadas en datos reales del sistema.

---

## Bibliografía de la Clase

- **Documentación oficial FastAPI** — fastapi.tiangolo.com
- **Documentación oficial Docker** — docs.docker.com
- **Documentación oficial uvicorn** — www.uvicorn.org
- **Huyen, C. (2025).** *AI Engineering: Building Applications with Foundation Models.* O'Reilly. Capítulo 9: Deployment.
- **Merkel, D. (2014).** *Docker: Lightweight Linux Containers for Consistent Development and Deployment.* Linux Journal.
