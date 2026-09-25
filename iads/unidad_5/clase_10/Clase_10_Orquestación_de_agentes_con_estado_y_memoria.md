# Clase 10: Orquestación de Agentes con Estado y Memoria

**Asignatura:** Desarrollo de Sistemas de Inteligencia Artificial

**Objetivo Técnico:** Implementar estado persistente y memoria entre sesiones con checkpointers de LangGraph, construir un sistema multiagente con orquestador y subagentes especializados para Ortelana Textil, y trazar el flujo completo con LangSmith para diagnosticar decisiones de routing en tiempo real.

> **Conexión con clases anteriores**
> En Clase 9 construimos un agente con tres herramientas que funciona bien para una sola consulta. Hoy resolvemos sus dos limitaciones fundamentales: la amnesia entre turnos y la incapacidad de coordinar tareas complejas entre dominios distintos.

---

## Planificación de la Clase (4 horas)

| Bloque | Duración | Contenido |
|---|---|---|
| **Bloque 1** | 30 min | El problema de la amnesia — reproducir la falla en vivo |
| **Bloque 2** | 60 min | Estado enriquecido y checkpointers — memoria dentro y entre sesiones |
| **Bloque 3** | 80 min | Laboratorio: orquestador multiagente de Ortelana |
| **Bloque 4** | 30 min | Trazabilidad completa con LangSmith en sistemas multiagente |
| **Cierre** | 20 min | Resumen, tarea asincrónica y conexión con Clase 11 |

---

## Bloque 1: El Problema de la Amnesia (30 min)

### Reproducir la falla en vivo

Tomar el agente de Clase 9 y ejecutar esta conversación de dos turnos:

**Turno 1:**
```python
consultar_agente("Soy Textiles Norpatagonia, CUIT 30-71234567-8. "
                 "¿Tengo stock de denim azul disponible en Córdoba?")
```
El agente responde correctamente — valida el CUIT, consulta el stock.

**Turno 2 (nueva invocación):**
```python
consultar_agente("¿Y para el jersey gris? ¿También está disponible en la misma sucursal?")
```

**Lo que pasa:** el agente no sabe quién es "yo", no recuerda que la sucursal era Córdoba, y no tiene el CUIT del turno anterior. Empieza desde cero — pregunta por el CUIT de nuevo o directamente alucina.

**Preguntar al grupo:**
- ¿Cuántos turnos necesita un distribuidor real para cerrar una compra?
- ¿Qué información debería recordar el sistema entre turnos?
- ¿Qué pasa si son dos distribuidores distintos usando el sistema al mismo tiempo?

---

### Los tres tipos de memoria que necesita un agente de producción

| Tipo | ¿Qué guarda? | ¿Cuánto dura? | En LangGraph |
|---|---|---|---|
| **Memoria de trabajo** | Estado de la sesión actual | Durante la conversación | `TypedDict` enriquecido |
| **Memoria de corto plazo** | Historial de la sesión completa | Hasta que cierra la sesión | `MemorySaver` (RAM) |
| **Memoria de largo plazo** | Historial entre sesiones distintas | Indefinido | `SqliteSaver` (disco) |

> **El problema que resolvemos hoy**
> El agente de Clase 9 no tiene ninguno de los tres. Hoy implementamos los tres niveles para el sistema de Ortelana.

---

## Bloque 2: Estado Enriquecido y Checkpointers (60 min)

### Estado enriquecido — más que mensajes

En Clase 9 el estado solo tenía `messages`. En producción el estado lleva toda la información de contexto que el agente necesita para tomar decisiones sin tener que re-preguntar:

```python
from typing import TypedDict, Annotated, Sequence, Optional
from langchain_core.messages import BaseMessage
import operator

class EstadoOrtelana(TypedDict):
    """
    Estado completo del agente de Ortelana.
    Viaja entre todos los nodos del grafo y persiste entre turnos.
    """
    # Historial de mensajes (se acumula)
    messages: Annotated[Sequence[BaseMessage], operator.add]

    # Contexto del distribuidor identificado en la sesión
    cuit_identificado: Optional[str]          # CUIT detectado en cualquier turno
    categoria_distribuidor: Optional[str]     # A, B, C — para decisiones de routing
    sucursal_preferida: Optional[str]         # Recordar preferencias del usuario

    # Control del flujo
    herramientas_usadas: Annotated[list, operator.add]  # Registro de qué tools se llamaron
    iteraciones: int                          # Contador para evitar loops infinitos
```

> **Pregunta #1**
> ¿Por qué `herramientas_usadas` usa `operator.add` como anotación?
>
> **Análisis:** Porque LangGraph necesita saber cómo combinar el estado cuando múltiples nodos escriben en él. `operator.add` en una lista significa "concatenar" — cada nodo agrega sus herramientas a la lista existente sin pisarla. Sin esto, el último nodo en escribir pierde los datos de los anteriores.

---

### Nodo de extracción de contexto

Un nodo dedicado que enriquece el estado al inicio de cada turno:

```python
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
import re

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def nodo_extraer_contexto(estado: EstadoOrtelana) -> dict:
    """
    Extrae información estructurada del último mensaje del usuario
    y la guarda en el estado para que otros nodos la usen.
    """
    ultimo_mensaje = estado["messages"][-1].content

    prompt = ChatPromptTemplate.from_template("""
Analizá el siguiente mensaje y extraé:
1. CUIT (si aparece, formato numérico sin guiones)
2. Sucursal mencionada (central_buenos_aires o filial_cordoba, si aparece)

Respondé SOLO en este formato exacto:
CUIT: [número o null]
SUCURSAL: [nombre o null]

Mensaje: {mensaje}
""")

    chain = prompt | llm | StrOutputParser()
    resultado = chain.invoke({"mensaje": ultimo_mensaje})

    # Parsear resultado
    cuit_match = re.search(r"CUIT: (\d+|null)", resultado)
    sucursal_match = re.search(r"SUCURSAL: (\w+|null)", resultado)

    actualizaciones = {}

    cuit = cuit_match.group(1) if cuit_match else "null"
    if cuit != "null" and not estado.get("cuit_identificado"):
        actualizaciones["cuit_identificado"] = cuit
        print(f"🆔 CUIT identificado: {cuit}")

    sucursal = sucursal_match.group(1) if sucursal_match else "null"
    if sucursal != "null" and not estado.get("sucursal_preferida"):
        actualizaciones["sucursal_preferida"] = sucursal
        print(f"📍 Sucursal identificada: {sucursal}")

    return actualizaciones
```

---

### Checkpointers — memoria entre sesiones

```python
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver

# ── Opción 1: Memoria en RAM (dura mientras el proceso está vivo) ─────────────
checkpointer_ram = MemorySaver()

# ── Opción 2: Memoria en disco SQLite (persiste entre reinicios) ──────────────
checkpointer_disco = SqliteSaver.from_conn_string("./ortelana_memoria.db")

# El thread_id identifica a cada distribuidor o conversación
# Mismo thread_id = misma sesión = misma memoria
config_distribuidor_A = {"configurable": {"thread_id": "textiles_norpatagonia_001"}}
config_distribuidor_B = {"configurable": {"thread_id": "modas_del_sur_002"}}
```

**Demostración de memoria persistente:**

```python
# Compilar el agente CON checkpointer
agente_con_memoria = grafo.compile(checkpointer=checkpointer_disco)

# Turno 1 — el distribuidor se presenta
agente_con_memoria.invoke(
    {"messages": [HumanMessage(
        content="Soy Textiles Norpatagonia, CUIT 30-71234567-8. "
                "¿Tienen denim azul en Córdoba?"
    )], "cuit_identificado": None, "sucursal_preferida": None,
       "categoria_distribuidor": None, "herramientas_usadas": [], "iteraciones": 0},
    config=config_distribuidor_A
)

# Turno 2 — nueva invocación, MISMO thread_id
# El agente recuerda quién es y cuál era la sucursal
agente_con_memoria.invoke(
    {"messages": [HumanMessage(
        content="¿Y el jersey gris también está disponible ahí?"
    )]},
    config=config_distribuidor_A  # ← mismo thread_id = misma memoria
)
```

> **Pregunta #2**
> ¿Qué pasa si dos distribuidores distintos usan el mismo `thread_id`?
>
> **Análisis:** Comparten memoria — el agente mezclaría el contexto de ambos. El `thread_id` debe ser único por distribuidor o por sesión. En producción se usa el ID de usuario del sistema, el CUIT o un UUID generado al iniciar la sesión.

---

## Bloque 3: Orquestador Multiagente de Ortelana (80 min)

### Arquitectura del sistema

```
Consulta del distribuidor
        │
        ▼
┌───────────────────┐
│   ORQUESTADOR     │  ← Analiza la consulta y decide el routing
│   (Router LLM)    │
└────────┬──────────┘
         │
    ┌────┴────────────────┐
    │                     │                    │
    ▼                     ▼                    ▼
┌──────────┐      ┌────────────┐      ┌──────────────┐
│ Agente   │      │  Agente    │      │   Agente     │
│ Catálogo │      │  Crédito   │      │  Reclamos    │
│ y Stock  │      │ y Onboard  │      │  y Calidad   │
└──────────┘      └────────────┘      └──────────────┘
Tools:             Tools:              Tools:
consultar_stock    validar_dist        abrir_ticket
buscar_tela        recuperar_norm      escalar_reclamo
                   check_financiac     notif_calidad
```

---

### Del selector simple al supervisor multiagente

En las primeras clases resolvimos el "a dónde va esta consulta" con clasificadores de intención simples (Clase 3: Pydantic + `Literal`) o con búsqueda semántica pre-filtrada (Clases 5-6). Ese selector operaba como un recepcionista: leía el mensaje, le asignaba una categoría rígida (`CONSULTA_STOCK`, `RECLAMO_CALIDAD`, etc.) y derivaba a un único flujo estático.

Ese enfoque colapsa apenas la consulta es compuesta. Si un distribuidor escribe *"Tengo un rollo fallado de Denim, quiero devolverlo y ajustar mi crédito para reservar otra tela"*, un clasificador de una sola etiqueta no puede resolverlo — necesita elegir una sola categoría para algo que en realidad son tres pasos encadenados.

El orquestador de hoy reemplaza esa lógica puntual por una **orquestación con estado**: no encasilla la consulta en una categoría, sino que coordina una red de expertos — activa al agente de reclamos, transfiere el resultado al agente de crédito y termina en logística si hace falta.

| Dimensión | Selector simple (Clases 3-6) | Supervisor multiagente (hoy) |
|---|---|---|
| **Mecánica de selección** | Estática (clasificación con `Literal`/Pydantic o similitud semántica por umbral) | Dinámica (grafo dirigido con aristas condicionales y evaluación continua de estado) |
| **Manejo de ambigüedad** | Colapsa o fuerza una única categoría ante consultas compuestas | Descompone la consulta en fases y deriva secuencialmente a múltiples subagentes |
| **Memoria y contexto** | Evaluación puntual sobre el mensaje entrante (single-turn) | Estado enriquecido con persistencia a corto y largo plazo (checkpointers) |
| **Resultado de la ruta** | Devuelve una plantilla de prompt o ejecuta una cadena RAG informativa | Invoca subagentes que ejecutan herramientas y modifican el entorno del negocio |

> **El subagente como "actuador abstracto":** desde la perspectiva del orquestador, cada subagente (`agente_catalogo`, `agente_credito`, `agente_reclamos`) se comporta como una capacidad de alto nivel más — igual que cualquier tool, pero que en lugar de ejecutar una única operación, encapsula todo un proceso de decisión dentro de su dominio. El orquestador no necesita saber *cómo* el agente de crédito resuelve una situación crediticia — solo necesita derivarle la consulta y esperar el resultado. La complejidad no desaparece: queda encapsulada detrás de una responsabilidad bien definida.

---

### El nodo orquestador — el router

```python
from langchain_core.messages import AIMessage
from langgraph.graph import StateGraph, END

ROUTING_PROMPT = """Sos el orquestador del sistema de Ortelana Textil.
Analizá la consulta del distribuidor y decidí qué agente especializado debe manejarla.

Agentes disponibles:
- "catalogo": preguntas sobre telas, stock, disponibilidad, características de materiales
- "credito": alta de distribuidores, validación de CUIT, financiación, cuenta corriente
- "reclamos": defectos de material, problemas con pedidos, devoluciones, quejas
- "general": saludos, consultas que no encajan en ninguna categoría anterior

Respondé SOLO con el nombre del agente (una sola palabra).
"""

def nodo_orquestador(estado: EstadoOrtelana) -> dict:
    """
    Analiza la consulta y decide qué subagente debe manejarla.
    Guarda la decisión en el estado para que la arista condicional la use.
    """
    ultimo_mensaje = estado["messages"][-1].content

    respuesta = llm.invoke([
        SystemMessage(content=ROUTING_PROMPT),
        HumanMessage(content=ultimo_mensaje)
    ])

    agente_elegido = respuesta.content.strip().lower()
    print(f"\n🔀 Router → Derivando a: [{agente_elegido}]")

    # Guardar la decisión en el estado
    return {"messages": [AIMessage(content=f"[ROUTING: {agente_elegido}]")]}


def decidir_subagente(estado: EstadoOrtelana) -> str:
    """Arista condicional que lee la decisión del orquestador."""
    ultimo = estado["messages"][-1].content
    if "[ROUTING: catalogo]" in ultimo:
        return "agente_catalogo"
    elif "[ROUTING: credito]" in ultimo:
        return "agente_credito"
    elif "[ROUTING: reclamos]" in ultimo:
        return "agente_reclamos"
    else:
        return "agente_general"
```

---

### Los tres subagentes especializados

```python
from langgraph.prebuilt import create_react_agent

# ── Subagente 1: Catálogo y Stock ────────────────────────────────────────────
PROMPT_CATALOGO = """Sos el especialista en catálogo y stock de Ortelana Textil.
Tu expertise es buscar telas, verificar disponibilidad y recomendar materiales.
Si el cliente pregunta algo fuera de tu dominio (crédito, reclamos), decile que
lo vas a derivar al área correspondiente."""

agente_catalogo = create_react_agent(
    model=llm,
    tools=[consultar_stock_tela],
    state_modifier=PROMPT_CATALOGO
)

# ── Subagente 2: Crédito y Onboarding ────────────────────────────────────────
PROMPT_CREDITO = """Sos el especialista en crédito y onboarding de Ortelana Textil.
Tu expertise es validar distribuidores, evaluar financiación y gestionar altas.
Siempre verificá el CUIT antes de dar información de crédito."""

agente_credito = create_react_agent(
    model=llm,
    tools=[validar_distribuidor, recuperar_normativa],
    state_modifier=PROMPT_CREDITO
)

# ── Subagente 3: Reclamos y Calidad ─────────────────────────────────────────
PROMPT_RECLAMOS = """Sos el especialista en reclamos y calidad de Ortelana Textil.
Tu expertise es gestionar devoluciones, abrir tickets y escalar problemas de calidad.
Siempre pedí el CUIT y una descripción detallada del problema antes de abrir un ticket."""

agente_reclamos = create_react_agent(
    model=llm,
    tools=[abrir_ticket_reclamo, recuperar_normativa],
    state_modifier=PROMPT_RECLAMOS
)
```

---

### El grafo multiagente completo

```python
# Wrappers para que cada subagente funcione como nodo del grafo
def nodo_catalogo(estado: EstadoOrtelana) -> dict:
    resultado = agente_catalogo.invoke(estado)
    return {"messages": resultado["messages"], "herramientas_usadas": ["catalogo"]}

def nodo_credito(estado: EstadoOrtelana) -> dict:
    resultado = agente_credito.invoke(estado)
    return {"messages": resultado["messages"], "herramientas_usadas": ["credito"]}

def nodo_reclamos(estado: EstadoOrtelana) -> dict:
    resultado = agente_reclamos.invoke(estado)
    return {"messages": resultado["messages"], "herramientas_usadas": ["reclamos"]}

def nodo_general(estado: EstadoOrtelana) -> dict:
    respuesta = llm.invoke([
        SystemMessage(content="Sos el asistente general de Ortelana Textil. "
                              "Respondé amablemente y derivá a quien corresponda."),
        *estado["messages"]
    ])
    return {"messages": [respuesta]}

# ── Construir el grafo multiagente ───────────────────────────────────────────
grafo_multi = StateGraph(EstadoOrtelana)

# Agregar todos los nodos
grafo_multi.add_node("extraer_contexto", nodo_extraer_contexto)
grafo_multi.add_node("orquestador", nodo_orquestador)
grafo_multi.add_node("agente_catalogo", nodo_catalogo)
grafo_multi.add_node("agente_credito", nodo_credito)
grafo_multi.add_node("agente_reclamos", nodo_reclamos)
grafo_multi.add_node("agente_general", nodo_general)

# Flujo: extracción → orquestador → subagente → fin
grafo_multi.set_entry_point("extraer_contexto")
grafo_multi.add_edge("extraer_contexto", "orquestador")

# Arista condicional desde el orquestador
grafo_multi.add_conditional_edges(
    "orquestador",
    decidir_subagente,
    {
        "agente_catalogo": "agente_catalogo",
        "agente_credito":  "agente_credito",
        "agente_reclamos": "agente_reclamos",
        "agente_general":  "agente_general",
    }
)

# Todos los subagentes terminan en END
for nodo in ["agente_catalogo", "agente_credito", "agente_reclamos", "agente_general"]:
    grafo_multi.add_edge(nodo, END)

# Compilar CON checkpointer
sistema_ortelana = grafo_multi.compile(checkpointer=checkpointer_disco)
```

---

### Tests del sistema multiagente

```python
def consultar_sistema(pregunta: str, thread_id: str = "test_001") -> None:
    config = {"configurable": {"thread_id": thread_id}}
    estado_inicial = {
        "messages": [HumanMessage(content=pregunta)],
        "cuit_identificado": None,
        "sucursal_preferida": None,
        "categoria_distribuidor": None,
        "herramientas_usadas": [],
        "iteraciones": 0
    }
    resultado = sistema_ortelana.invoke(estado_inicial, config=config)
    print(f"\n💬 Respuesta: {resultado['messages'][-1].content}")
    print(f"🔧 Herramientas usadas: {resultado['herramientas_usadas']}")

# Test 1: Routing a catálogo
consultar_sistema(
    "¿Tienen seda natural disponible en la sucursal de Córdoba?",
    thread_id="dist_001"
)

# Test 2: Routing a crédito
consultar_sistema(
    "Soy nuevo distribuidor, CUIT 30-71234567-8. ¿Puedo abrir cuenta corriente?",
    thread_id="dist_002"
)

# Test 3: Routing a reclamos
consultar_sistema(
    "El jersey que recibimos la semana pasada vino con manchas de aceite.",
    thread_id="dist_003"
)

# Test 4: Conversación multi-turno con memoria
consultar_sistema(
    "Soy Textiles Norpatagonia, CUIT 30-71234567-8, trabajo desde Córdoba.",
    thread_id="dist_norpatagonia"
)
consultar_sistema(
    "¿Y el denim también está disponible por acá?",  # "acá" = Córdoba (lo recuerda)
    thread_id="dist_norpatagonia"  # mismo thread_id → memoria activa
)
```

> **Discutir el Test 4 con el grupo**
> ¿El sistema recuerda que "acá" es Córdoba del turno anterior? ¿Recuerda el CUIT? Si no, ¿en qué nodo falla — en el checkpointer, en el nodo de extracción de contexto o en el subagente? LangSmith nos va a decir exactamente dónde.

---

## Bloque 4: Trazabilidad con LangSmith en Multiagente (30 min)

### Por qué LangSmith es crítico en multiagente

En un agente simple de Clase 9, si algo falla hay 3 nodos que revisar. En el sistema multiagente de hoy hay 6 nodos, aristas condicionales, checkpointers y subagentes anidados. Sin trazabilidad, debuggear es imposible.

```python
import os
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "ortelana-multiagente"
# Ya configurado en .env desde Clase 7 — solo cambiar el nombre del proyecto
```

**Lo que LangSmith muestra en una consulta multiagente:**

```
Traza: "El jersey vino manchado, soy CUIT 30-71234567-8"

├── extraer_contexto (0.8s)
│   ├── Input: mensaje del distribuidor
│   ├── CUIT detectado: 30712345678 ✅
│   └── Sucursal detectada: null
│
├── orquestador (0.6s)
│   ├── Input: mensaje + contexto
│   ├── Decisión: "reclamos"
│   └── Confianza: alta (palabras clave: manchado, jersey)
│
└── agente_reclamos (3.2s)
    ├── Tool: recuperar_normativa("política devoluciones defecto")
    │   └── Resultado: Artículo 3 — 30 días corridos...
    ├── Tool: abrir_ticket_reclamo(cuit="30712345678", ...)
    │   └── Resultado: Ticket #ORN-2847 creado
    └── Respuesta final: "Abrimos el ticket #ORN-2847..."
```

---

### Detectar errores de routing con LangSmith

El error más común en multiagente es que el orquestador derive mal. LangSmith permite verlo inmediatamente:

```python
# Consulta ambigua que puede confundir al router
consultar_sistema(
    "Necesito información sobre la devolución del pedido de denim "
    "y también si puedo pedir más en cuotas.",
    thread_id="test_ambiguo"
)
```

En LangSmith: ¿el router eligió `reclamos` o `credito`? ¿O debería haber derivado a ambos? Esta discusión abre el concepto de **routing paralelo** — cuando una consulta requiere más de un subagente al mismo tiempo. Queda como extensión conceptual para el TP1.

> **Pregunta #3**
> Si el router elige mal consistentemente para un tipo de consulta, ¿qué es lo primero que ajustan?
>
> **Análisis:** El `ROUTING_PROMPT` — específicamente los ejemplos y descripciones de cada agente. Es el mismo principio que los docstrings de las tools en Clase 9: el LLM toma decisiones basándose en texto, no en código. Mejorar el texto mejora las decisiones.

---

## Cierre y Material Asincrónico (20 min)

### Resumen de la clase

- **Estado enriquecido:** el `TypedDict` lleva más que mensajes — contexto del distribuidor, preferencias, flags de control.
- **Checkpointers:** `MemorySaver` para RAM (sesión), `SqliteSaver` para disco (entre sesiones). El `thread_id` identifica cada conversación.
- **Orquestador:** un nodo router que analiza la consulta y deriva al subagente correcto. Su calidad depende del `ROUTING_PROMPT`.
- **Subagentes especializados:** cada uno tiene su propio conjunto de tools y system prompt. Menos tools por agente = mejores decisiones.
- **LangSmith en multiagente:** muestra cada nodo, cada decisión de routing y cada herramienta. Imprescindible para debuggear sistemas complejos.

---

### Material asincrónico — Entre Clase 10 y Clase 11

> **Hito del TP1 — Sistema RAG + Agente integrado**

**Actividad — Integrar el pipeline completo:**

Conectar el pipeline RAG avanzado de Clase 7 como herramienta del `agente_credito` y correr el dataset de evaluación de Clase 8 sobre el sistema multiagente completo.

```python
# La herramienta RAG avanzada para el agente de crédito
@tool
def consultar_normativa_avanzada(consulta: str) -> str:
    """
    Consulta el reglamento comercial de Ortelana usando RAG avanzado con
    reranking. Usar para preguntas sobre políticas, condiciones, plazos
    y procedimientos internos de la empresa.
    """
    # Conectar con el pipeline RAG avanzado de Clase 7
    resultado = rag_avanzado_ortelana(consulta)
    return resultado["respuesta"]
```

**Documentar:**
- ¿Las métricas RAGAS mejoran o empeoran cuando la normativa pasa por el agente en lugar de ir directo al RAG?
- ¿El orquestador routea bien las preguntas de normativa al `agente_credito`?
- ¿Qué tipo de consultas confunden más al router?

---

### Conexión con Clase 11

Hasta hoy el sistema vive en Google Colab — solo lo pueden usar ustedes. En Clase 11 lo exponemos al mundo: construimos una **API con FastAPI** que envuelve el sistema multiagente en endpoints HTTP. Cualquier sistema externo — el WhatsApp de Ortelana, el formulario web, el ERP — podrá consultar al agente enviando un POST request. Es el paso de prototipo a producto.

### Tres preguntas pendientes antes de llamarlo "producto"

Tener el grafo funcionando en Colab no alcanza para un estándar profesional. Quedan tres interrogantes abiertos que la Unidad 6 responde una por una:

1. **¿Cómo lo transformamos en un producto accesible?** Un distribuidor real no consume código Python. ¿Cómo exponemos el flujo agéntico como un microservicio *stateless* y de alta disponibilidad (API HTTP + contenedores), garantizando que la memoria persistente en SQLite quede correctamente aislada por cliente? → **Clase 11.**
2. **¿Cómo controlamos y medimos lo que pasa "adentro" del agente?** Cuando el flujo depende de decisiones dinámicas del orquestador, el sistema se vuelve una caja negra. Si el bot responde mal, ¿cómo detectamos si el fallo fue del ruteo, de una alucinación del LLM o de la recuperación del sensor RAG? → **Clase 12.**
3. **¿Cómo lo blindamos y lo hacemos evolucionar sin romperlo?** Los prompts de control conviven con el texto libre del usuario — ¿cómo evitamos prompt injection o fugas de datos de otros distribuidores (PII)? Y como el catálogo cambia y el lenguaje de los clientes muta, ¿cómo versionamos y probamos cambios sin degradar el servicio? → **Clase 13 y siguientes.**

> No se trata solo de lograr que la IA "piense" o "actúe" — se trata de construir la infraestructura para que opere de manera predecible, segura y auditable en el mundo real. Eso es lo que arranca en la Unidad 6.

---

## Bibliografía de la Clase

- **Documentación oficial LangGraph** — langchain-ai.github.io/langgraph (Checkpointers, Multi-agent).
- **Documentación oficial LangSmith** — smith.langchain.com (Tracing multi-agent).
- **Shinn, N., et al. (2023).** *Reflexion: Language Agents with Verbal Reinforcement Learning.* arXiv:2303.11366.
- **Chase, H. (2023).** *LangChain: Building Applications with LLMs.* (Orquestación y memoria).
- **Russell, S., & Norvig, P. (2021).** *Artificial Intelligence: A Modern Approach.* Capítulo 2. (Arquitecturas multiagente).
