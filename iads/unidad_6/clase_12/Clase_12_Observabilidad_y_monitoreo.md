# Clase 12: Observabilidad y Monitoreo de Sistemas de IA

**Asignatura:** Desarrollo de Sistemas de Inteligencia Artificial

**Objetivo Técnico:** Implementar los tres pilares de observabilidad (logs estructurados, métricas de uso y trazabilidad) sobre la API de Ortelana Textil, usando Python para logs y métricas operativas y LangSmith para trazabilidad del agente — convirtiendo el sistema desplegado en Clase 11 en un sistema que puede monitorearse, diagnosticarse y mejorarse en producción.

> **Conexión con clases anteriores**
> En Clase 11 desplegamos la API de Ortelana con FastAPI y Docker. El sistema funciona — pero es una caja negra. Hoy le agregamos ojos: sabemos qué pasa adentro, cuánto cuesta, dónde falla y cómo mejorar.

---

## Planificación de la Clase (4 horas)

| Bloque | Duración | Contenido |
|---|---|---|
| **Bloque 1** | 35 min | Los tres pilares — logs, métricas y trazas |
| **Bloque 2** | 65 min | Logs estructurados en la API de Ortelana |
| **Bloque 3** | 60 min | LangSmith en producción — dashboards y costos |
| **Bloque 4** | 50 min | Métricas de uso y alertas |
| **Cierre** | 30 min | Resumen, tarea asincrónica y conexión con Clase 13 |

---

## Bloque 1: Los Tres Pilares de la Observabilidad (35 min)

### El problema de operar sin visibilidad

Escenario real: son las 2am del lunes. El equipo comercial de Ortelana abre el lunes a las 8am con 200 distribuidores esperando respuesta. A las 7:45am alguien llama: "el sistema no responde bien". ¿Qué hacés?

**Sin observabilidad:**
- No sabés si el problema empezó ahora o hace 6 horas
- No sabés si es el retriever, el LLM, la API o la red
- No sabés cuántos distribuidores fueron afectados
- No podés saber si ya se resolvió solo o sigue roto
- Revisás código a ciegas hasta que algo funcione

**Con observabilidad:**
- Los logs dicen exactamente cuándo empezó el error y en qué endpoint
- LangSmith muestra qué nodo del agente falló y con qué input
- Las métricas muestran que la latencia subió de 2s a 45s a las 1:30am
- El health check alertó automáticamente a las 1:31am
- Sabés que fue un timeout con la API de OpenAI y ya se resolvió solo

---

### Los tres pilares — no son lo mismo

```
┌─────────────────────────────────────────────────────────────┐
│                    OBSERVABILIDAD                           │
│                                                             │
│  LOGS          MÉTRICAS           TRAZAS                   │
│  ─────         ────────           ──────                   │
│  Qué pasó      Cuánto pasó        Cómo pasó                │
│  (eventos)     (números)          (flujo)                   │
│                                                             │
│  "Error en     "500 requests/     "Request → retriever     │
│  thread_id     hora, latencia      → reranker → LLM →      │
│  dist_001 a    promedio 2.3s"      fallo en LLM (timeout)" │
│  las 14:32"                                                 │
└─────────────────────────────────────────────────────────────┘
```

| Pilar | Herramienta | Pregunta que responde |
|---|---|---|
| **Logs** | Python `logging` + JSON | ¿Qué evento ocurrió y cuándo? |
| **Métricas** | Contadores en memoria / endpoint `/metricas` | ¿Cuántas veces? ¿Cuánto tarda? ¿Cuánto cuesta? |
| **Trazas** | LangSmith | ¿Qué paso exacto dentro del agente falló? |

> **Los tres son necesarios — ninguno reemplaza a los otros**
> Un log dice "el request falló". Una métrica dice "el 3% de los requests fallan". Una traza dice "el request falló en el nodo `agente_credito` porque el LLM devolvió un JSON malformado en el paso de reranking". Para diagnosticar necesitás los tres.

---

### Por qué `print` no es suficiente en producción

```python
# ❌ Lo que hace un desarrollador en Colab
print("El agente respondió")
print(f"Error: {e}")

# Problemas:
# - No tiene timestamp → ¿cuándo pasó?
# - No tiene nivel → ¿es un error grave o una advertencia?
# - No tiene contexto → ¿qué thread_id? ¿qué endpoint?
# - No se puede filtrar → para encontrar todos los errores hay que leer todo
# - No se puede indexar → ningún sistema de monitoreo puede procesarlo
```

```python
# ✅ Lo que hace un sistema en producción
import logging
import json

logger.error(
    "Falla en el agente multiagente",
    extra={
        "thread_id": "dist_001",
        "endpoint": "/consultar",
        "error_type": "LLMTimeout",
        "duracion_ms": 45231,
        "costo_tokens": 0,
    }
)

# Output JSON estructurado — indexable, filtrable, procesable:
# {
#   "timestamp": "2026-05-15T02:32:11.847Z",
#   "level": "ERROR",
#   "message": "Falla en el agente multiagente",
#   "thread_id": "dist_001",
#   "endpoint": "/consultar",
#   "error_type": "LLMTimeout",
#   "duracion_ms": 45231,
#   "costo_tokens": 0
# }
```

> **Pregunta #1**
> ¿Por qué el log estructurado usa JSON en lugar de texto plano?
>
> **Análisis:** Porque las herramientas de monitoreo (Datadog, Grafana, CloudWatch, incluso `grep`) pueden indexar y consultar JSON automáticamente. "Dame todos los logs de `thread_id: dist_001` donde `duracion_ms > 10000` en las últimas 2 horas" es una consulta trivial sobre JSON estructurado. Sobre texto plano libre es imposible sin regex muy frágiles.

---

## Bloque 2: Logs Estructurados en la API de Ortelana (65 min)

### Configurar el sistema de logging

```python
# logger_config.py
import logging
import json
import sys
from datetime import datetime, timezone

class JSONFormatter(logging.Formatter):
    """
    Formateador que convierte cada log en un JSON estructurado.
    Compatible con cualquier sistema de monitoreo (Datadog, CloudWatch, etc.)
    """
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "line": record.lineno,
        }

        # Agregar campos extra si existen
        for key, value in record.__dict__.items():
            if key not in logging.LogRecord.__dict__ and \
               not key.startswith('_') and \
               key not in ('args', 'msg', 'message'):
                log_data[key] = value

        # Incluir traceback si hay excepción
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


def configurar_logger(nombre: str) -> logging.Logger:
    """Crea un logger configurado con output JSON estructurado."""
    logger = logging.getLogger(nombre)
    logger.setLevel(logging.INFO)

    # Handler para stdout — Docker captura stdout automáticamente
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)

    return logger


# Logger principal de la aplicación
logger = configurar_logger("ortelana_api")
```

---

### Integrar logs en la API de Ortelana

```python
# api.py — versión con logs estructurados
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
import time
from logger_config import logger
from schemas import ConsultaRequest, ConsultaResponse

app = FastAPI(title="Ortelana Textil — API de Agente IA", version="1.0.0")


@app.middleware("http")
async def middleware_logging(request: Request, call_next):
    """
    Registra cada request HTTP con contexto completo.
    Se ejecuta antes y después de cada endpoint.
    """
    request_id = f"{request.method}_{request.url.path}_{int(time.time()*1000)}"
    inicio = time.time()

    # Log de entrada
    logger.info(
        "Request recibido",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "client_ip": request.client.host if request.client else "unknown",
        }
    )

    try:
        response = await call_next(request)
        duracion_ms = int((time.time() - inicio) * 1000)

        # Log de salida exitosa
        logger.info(
            "Request completado",
            extra={
                "request_id": request_id,
                "status_code": response.status_code,
                "duracion_ms": duracion_ms,
            }
        )
        return response

    except Exception as exc:
        duracion_ms = int((time.time() - inicio) * 1000)

        # Log de error
        logger.error(
            "Request fallido",
            extra={
                "request_id": request_id,
                "duracion_ms": duracion_ms,
                "error_type": type(exc).__name__,
                "error_message": str(exc),
            },
            exc_info=True
        )
        raise


@app.post("/consultar", response_model=ConsultaResponse)
async def consultar_agente(request: ConsultaRequest):
    inicio = time.time()

    logger.info(
        "Consulta iniciada",
        extra={
            "thread_id": request.thread_id,
            "pregunta_chars": len(request.pregunta),
        }
    )

    try:
        from langchain_core.messages import HumanMessage
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
        duracion_ms = int((time.time() - inicio) * 1000)

        herramientas = resultado.get("herramientas_usadas", [])
        respuesta_chars = len(resultado["messages"][-1].content)

        # Log de consulta exitosa con métricas del agente
        logger.info(
            "Consulta completada",
            extra={
                "thread_id": request.thread_id,
                "duracion_ms": duracion_ms,
                "herramientas_usadas": herramientas,
                "respuesta_chars": respuesta_chars,
                "iteraciones_agente": resultado.get("iteraciones", 0),
            }
        )

        return ConsultaResponse(
            respuesta=resultado["messages"][-1].content,
            thread_id=request.thread_id,
            herramientas_usadas=herramientas
        )

    except Exception as e:
        duracion_ms = int((time.time() - inicio) * 1000)

        logger.error(
            "Consulta fallida",
            extra={
                "thread_id": request.thread_id,
                "duracion_ms": duracion_ms,
                "error_type": type(e).__name__,
                "error_message": str(e),
            },
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=str(e))
```

---

### Leer los logs en producción

```bash
# Ver logs en tiempo real del contenedor Docker
docker-compose logs -f ortelana-api

# Output (JSON estructurado — uno por línea):
# {"timestamp":"2026-05-15T14:32:11Z","level":"INFO","message":"Consulta iniciada","thread_id":"norpatagonia_001","pregunta_chars":48}
# {"timestamp":"2026-05-15T14:32:13Z","level":"INFO","message":"Consulta completada","thread_id":"norpatagonia_001","duracion_ms":2341,"herramientas_usadas":["catalogo","credito"]}

# Filtrar solo errores (jq parsea JSON en terminal)
docker-compose logs ortelana-api | grep '"level":"ERROR"'

# Ver todos los logs de un thread_id específico
docker-compose logs ortelana-api | grep '"thread_id":"norpatagonia_001"'
```

> **jq — el grep para JSON**
> `jq` es una herramienta de terminal que parsea JSON igual que `grep` parsea texto. En producción con logs JSON es indispensable. Si no lo tienen instalado: `brew install jq` (Mac) o `apt install jq` (Linux).

---

## Bloque 3: LangSmith en Producción (60 min)

### De la trazabilidad al control operativo

En Clases 7 y 10 usaron LangSmith para debuggear el pipeline durante el desarrollo. En producción el uso es distinto: no están mirando trazas una por una — están monitoreando tendencias, detectando degradación y tomando decisiones de mejora basadas en datos reales.

```python
# .env — ya configurado desde Clase 7
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=ls__XXXXXXXXXXXXXXXX
LANGCHAIN_PROJECT=ortelana-produccion  # Proyecto separado del de desarrollo
```

---

### Los cuatro dashboards que importan en producción

**Dashboard 1 — Volumen y latencia**

```
smith.langchain.com → proyecto ortelana-produccion → Overview

Métricas clave a monitorear:
┌─────────────────────────────────────────┐
│ Requests últimas 24hs:     1.247        │
│ Latencia promedio:         2.3s         │
│ Latencia p95:              8.1s         │  ← el 5% más lento
│ Latencia p99:              22.4s        │  ← el 1% más lento
│ Tasa de error:             0.8%         │
└─────────────────────────────────────────┘
```

> **¿Por qué p95 y p99 en vez del promedio?**
> El promedio oculta los casos extremos. Si 999 requests tardan 1s y 1 tarda 1000s, el promedio es ~2s — parece bien. Pero ese distribuidor que esperó 1000s tuvo una experiencia terrible. El p99 lo captura: "el 1% de los requests más lentos tardaron 1000s".

**Dashboard 2 — Costo por consulta**

LangSmith registra los tokens consumidos en cada llamada al LLM:

```
Desglose de costos (últimas 24hs):
├── Consultas al catálogo:    847 runs  →  $0.0023 promedio
├── Consultas de crédito:     312 runs  →  $0.0041 promedio (RAG + reranking)
├── Gestión de reclamos:       88 runs  →  $0.0038 promedio
└── Total del día:                      →  $4.87
```

**Dashboard 3 — Trazas con errores**

```python
# Filtrar en LangSmith: runs con error en las últimas 6 horas
# smith.langchain.com → Runs → Filter: status=error, last 6h

# Lo que muestra cada traza de error:
# - Input exacto que disparó el error
# - Nodo donde falló (extraer_contexto / orquestador / agente_X)
# - Mensaje de excepción completo
# - Tiempo hasta el fallo
# - Tokens consumidos antes del fallo (costo sin respuesta útil)
```

**Dashboard 4 — Comparación de versiones de prompt**

```python
# Cuando mejoran el ROUTING_PROMPT del orquestador (Clase 10),
# LangSmith permite comparar:
# Versión A (antes): 87% de routing correcto
# Versión B (después): 94% de routing correcto
# → Mejora de 7 puntos medida con datos reales de producción
```

---

### Anotaciones y feedback humano

```python
# En producción, el equipo comercial puede marcar respuestas como correctas o incorrectas
# Esto crea un dataset de evaluación continuo

from langsmith import Client

client = Client()

# Marcar una traza como correcta/incorrecta desde el código
def registrar_feedback(run_id: str, correcto: bool, comentario: str = ""):
    client.create_feedback(
        run_id=run_id,
        key="correctness",
        score=1.0 if correcto else 0.0,
        comment=comentario
    )

# Ejemplo de uso en el endpoint
@app.post("/feedback")
async def recibir_feedback(run_id: str, correcto: bool, comentario: str = ""):
    """
    Endpoint para que el equipo comercial marque respuestas como correctas o incorrectas.
    El feedback alimenta el dataset de evaluación de RAGAS (Clase 8).
    """
    registrar_feedback(run_id, correcto, comentario)
    return {"mensaje": "Feedback registrado", "run_id": run_id}
```

> **El loop de mejora continua**
> Producción → Logs muestran errores → LangSmith muestra dónde falló → Feedback del equipo comercial marca qué respuestas fueron malas → RAGAS mide si el fix mejoró → Deploy de la nueva versión → vuelta a producción. Sin observabilidad, este loop no existe.

---

## Bloque 4: Métricas de Uso y Alertas (50 min)

### El contador de métricas en memoria

```python
# metrics.py
from dataclasses import dataclass, field
from collections import defaultdict
from datetime import datetime
import threading

@dataclass
class MetricasOrtelana:
    """
    Contador de métricas en memoria para la API de Ortelana.
    Thread-safe para manejar requests concurrentes.
    """
    _lock: threading.Lock = field(default_factory=threading.Lock)

    # Contadores de requests
    total_consultas: int = 0
    consultas_exitosas: int = 0
    consultas_fallidas: int = 0

    # Latencias (en ms)
    latencias: list = field(default_factory=list)

    # Herramientas usadas
    uso_herramientas: dict = field(default_factory=lambda: defaultdict(int))

    # Costo estimado (basado en tokens)
    costo_total_usd: float = 0.0

    # Por hora
    consultas_por_hora: dict = field(default_factory=lambda: defaultdict(int))

    def registrar_consulta(
        self,
        exito: bool,
        duracion_ms: int,
        herramientas: list[str],
        tokens_usados: int = 0
    ):
        with self._lock:
            self.total_consultas += 1
            hora_actual = datetime.now().strftime("%Y-%m-%d %H:00")
            self.consultas_por_hora[hora_actual] += 1

            if exito:
                self.consultas_exitosas += 1
            else:
                self.consultas_fallidas += 1

            self.latencias.append(duracion_ms)

            for herramienta in herramientas:
                self.uso_herramientas[herramienta] += 1

            # Estimación de costo: $0.00015 por 1000 tokens (gpt-4o-mini)
            self.costo_total_usd += (tokens_usados / 1000) * 0.00015

    def obtener_resumen(self) -> dict:
        with self._lock:
            latencias = self.latencias if self.latencias else [0]
            latencias_sorted = sorted(latencias)
            n = len(latencias_sorted)

            return {
                "total_consultas": self.total_consultas,
                "consultas_exitosas": self.consultas_exitosas,
                "consultas_fallidas": self.consultas_fallidas,
                "tasa_error_pct": round(
                    (self.consultas_fallidas / max(self.total_consultas, 1)) * 100, 2
                ),
                "latencia_promedio_ms": round(sum(latencias) / len(latencias)),
                "latencia_p95_ms": latencias_sorted[int(n * 0.95)],
                "latencia_p99_ms": latencias_sorted[int(n * 0.99)],
                "herramientas_mas_usadas": dict(
                    sorted(self.uso_herramientas.items(), key=lambda x: x[1], reverse=True)[:5]
                ),
                "costo_estimado_usd": round(self.costo_total_usd, 4),
                "consultas_por_hora": dict(
                    sorted(self.consultas_por_hora.items())[-24:]  # últimas 24hs
                ),
            }


# Instancia global — vive mientras el servidor está corriendo
metricas = MetricasOrtelana()
```

---

### El endpoint `/metricas`

```python
# api.py — agregar el endpoint de métricas
from metrics import metricas

@app.get("/metricas")
async def obtener_metricas():
    """
    Dashboard operativo de la API de Ortelana.
    Muestra el estado del sistema en tiempo real.
    """
    return metricas.obtener_resumen()

# Integrar el registro de métricas en el endpoint /consultar
@app.post("/consultar", response_model=ConsultaResponse)
async def consultar_agente(request: ConsultaRequest):
    inicio = time.time()
    try:
        # ... código del agente ...
        duracion_ms = int((time.time() - inicio) * 1000)

        metricas.registrar_consulta(
            exito=True,
            duracion_ms=duracion_ms,
            herramientas=herramientas,
            tokens_usados=500  # En producción: leer de la respuesta del LLM
        )
        return respuesta

    except Exception as e:
        duracion_ms = int((time.time() - inicio) * 1000)
        metricas.registrar_consulta(
            exito=False,
            duracion_ms=duracion_ms,
            herramientas=[]
        )
        raise HTTPException(status_code=500, detail=str(e))
```

**Output de `GET /metricas`:**

```json
{
  "total_consultas": 1247,
  "consultas_exitosas": 1237,
  "consultas_fallidas": 10,
  "tasa_error_pct": 0.80,
  "latencia_promedio_ms": 2341,
  "latencia_p95_ms": 8102,
  "latencia_p99_ms": 22431,
  "herramientas_mas_usadas": {
    "catalogo": 847,
    "credito": 312,
    "reclamos": 88
  },
  "costo_estimado_usd": 0.4823,
  "consultas_por_hora": {
    "2026-05-15 08:00": 312,
    "2026-05-15 09:00": 287,
    "2026-05-15 10:00": 198
  }
}
```

---

### El concepto de alertas

En producción no podés estar mirando `/metricas` todo el tiempo. Las alertas hacen ese trabajo automáticamente:

```python
# alerts.py
from logger_config import logger

UMBRALES = {
    "latencia_p95_ms": 10_000,    # Alerta si p95 > 10 segundos
    "tasa_error_pct": 5.0,         # Alerta si más del 5% de requests fallan
    "costo_por_hora_usd": 10.0,    # Alerta si el costo supera $10/hora
}

def verificar_alertas(resumen_metricas: dict) -> list[str]:
    """
    Evalúa las métricas actuales contra los umbrales definidos.
    Devuelve lista de alertas activas (vacía si todo está bien).
    """
    alertas = []

    if resumen_metricas["latencia_p95_ms"] > UMBRALES["latencia_p95_ms"]:
        alertas.append(
            f"⚠️ LATENCIA ALTA: p95 = {resumen_metricas['latencia_p95_ms']}ms "
            f"(umbral: {UMBRALES['latencia_p95_ms']}ms)"
        )

    if resumen_metricas["tasa_error_pct"] > UMBRALES["tasa_error_pct"]:
        alertas.append(
            f"🔴 TASA DE ERROR ALTA: {resumen_metricas['tasa_error_pct']}% "
            f"(umbral: {UMBRALES['tasa_error_pct']}%)"
        )

    for alerta in alertas:
        logger.warning(
            "ALERTA ACTIVA",
            extra={"alerta": alerta, "metricas": resumen_metricas}
        )

    return alertas


# Endpoint de alertas — para integrar con sistemas de monitoreo externos
@app.get("/alertas")
async def obtener_alertas():
    resumen = metricas.obtener_resumen()
    alertas_activas = verificar_alertas(resumen)
    return {
        "alertas_activas": alertas_activas,
        "sistema_saludable": len(alertas_activas) == 0,
        "metricas_actuales": resumen
    }
```

> **Pregunta #3**
> ¿Por qué definimos los umbrales como constantes separadas y no hardcodeados dentro de la función?
>
> **Análisis:** Porque los umbrales cambian según el contexto operativo. En horario pico (8-12am) la latencia aceptable es distinta que a las 3am. Con constantes centralizadas, el equipo de operaciones puede ajustar los umbrales sin tocar la lógica de evaluación. En producción real estos valores vienen de variables de entorno o de una base de datos de configuración.

---

## Cierre y Material Asincrónico (30 min)

### Resumen de la clase

- **Los tres pilares:** Logs (qué pasó), Métricas (cuánto pasó), Trazas (cómo pasó). Ninguno reemplaza a los otros.
- **Logs estructurados en JSON:** indexables, filtrables, procesables por cualquier sistema de monitoreo. `print` no escala en producción.
- **LangSmith en producción:** volumen, latencia p95/p99, costo por consulta, comparación de versiones de prompt, feedback humano.
- **Métricas en memoria:** contador thread-safe con latencias, herramientas usadas y costo estimado. Endpoint `/metricas` como dashboard operativo.
- **Alertas:** umbrales definidos sobre las métricas que disparan logs de warning. El primer paso hacia un sistema que se monitorea solo.

---

### Material asincrónico — Entre Clase 12 y Clase 13

> **La Clase 13 es la evaluación integradora — llegar con el sistema completo**

**Actividad — Observabilidad completa en el TP1:**

Agregar los tres pilares a la API del TP1:

```python
# Checklist de observabilidad para el TP1
# ✅ Logs estructurados en JSON en todos los endpoints
# ✅ Endpoint GET /metricas con al menos: total_consultas,
#    tasa_error_pct, latencia_promedio_ms, herramientas_mas_usadas
# ✅ Endpoint GET /alertas con al menos 2 umbrales definidos
# ✅ LangSmith activo con el proyecto del TP1
```

**Responder antes de Clase 13:**
- ¿Cuál es la herramienta más usada en su sistema? ¿Por qué tiene sentido?
- ¿Qué umbral de latencia definieron como alerta y por qué ese valor?
- ¿Encontraron algún error mirando los logs que no habían notado antes?

---

### Conexión con Clase 13

El sistema está desplegado, monitoreable y produce métricas reales. En Clase 13 es la **evaluación integradora** — cada grupo presenta su sistema completo: arquitectura, pipeline RAG, agente, API, observabilidad y métricas. Es el cierre técnico del TP1 antes de la defensa final.

---

## Bibliografía de la Clase

- **Documentación oficial Python logging** — docs.python.org/3/library/logging.html
- **Documentación oficial LangSmith** — smith.langchain.com (Production monitoring).
- **Kleppmann, M. (2017).** *Designing Data-Intensive Applications.* O'Reilly. Capítulo 1: Observability.
- **Huyen, C. (2025).** *AI Engineering: Building Applications with Foundation Models.* O'Reilly. Capítulo 10: Monitoring.
- **Google SRE Book (2016).** *Site Reliability Engineering.* Capítulo 6: Monitoring Distributed Systems.
