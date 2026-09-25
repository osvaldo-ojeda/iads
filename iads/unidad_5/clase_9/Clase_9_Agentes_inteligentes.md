# Clase 9: Agentes Inteligentes — Tool Use, Function Calling y LangGraph

**Asignatura:** Desarrollo de Sistemas de Inteligencia Artificial

**Objetivo Técnico:** Comprender la diferencia entre una cadena RAG y un agente inteligente, implementar el patrón ReAct con LangGraph dotando al agente de herramientas reales de Ortelana Textil, y entender cómo el LLM decide qué herramienta usar y cuándo.

> **Cierre del círculo con Clase 1**
> En Clase 1 vieron el ciclo del agente: percepción → razonamiento → acción → observación. Hoy lo implementan en código real. El PEAS que modelaron para Ortelana en Clase 1 se convierte hoy en un agente funcional con herramientas, estado y decisiones autónomas.

---

## Planificación de la Clase (4 horas)

| Bloque | Duración | Contenido |
|---|---|---|
| **Bloque 1** | 30 min | De la cadena al agente — qué cambia y por qué |
| **Bloque 2** | 50 min | Tool use y function calling — cómo el LLM decide |
| **Bloque 3** | 80 min | Laboratorio: primer agente de Ortelana con LangGraph |
| **Bloque 4** | 40 min | Multiagente conceptual + Ollama como alternativa local |
| **Cierre** | 20 min | Resumen, tarea asincrónica y conexión con Clase 10 |

---

## Bloque 1: De la Cadena al Agente (30 min)

### El límite del RAG para casos complejos

En Clase 8 cerramos con esta pregunta: *"¿Qué pasa cuando responder requiere múltiples pasos?"*

Simulemos en vivo. Un distribuidor de Ortelana escribe:

> *"Hola, soy Textiles Norpatagonia, CUIT 30-71234567-8. Quiero saber si califico para financiación en cuotas y si tienen stock de denim azul en la sucursal de Córdoba para mandar esta semana."*

**El RAG solo (pipeline de Clases 6-7) hace esto:**
```
Pregunta → ChromaDB recupera chunks sobre financiación y denim → LLM responde
```

El problema: el LLM va a inventar si Textiles Norpatagonia califica para financiación porque no tiene acceso a la BD SQL. Y va a inventar el stock porque no puede consultar el inventario en tiempo real. El RAG recupera documentos estáticos — no puede ejecutar acciones sobre sistemas externos.

**Lo que necesitamos — un agente:**
```
Pregunta
    │
    ▼
LLM razona: "necesito validar el CUIT primero"
    │
    ▼
Llama a validar_distribuidor(cuit="30712345678")
    │
    ▼
Recibe resultado: {"categoria": "A", "deuda": false, "elegible_financiacion": true}
    │
    ▼
LLM razona: "ahora necesito el stock de denim en Córdoba"
    │
    ▼
Llama a consultar_stock(material="denim", sucursal="filial_cordoba")
    │
    ▼
Recibe resultado: {"tela": "TELA-001", "en_stock": true, "metros_disponibles": 450}
    │
    ▼
LLM razona: "tengo todo lo que necesito para responder"
    │
    ▼
Respuesta completa y fundamentada en datos reales
```

> **La diferencia clave**
> Una **cadena** (chain) ejecuta siempre los mismos pasos en el mismo orden. Un **agente** decide en tiempo de ejecución qué pasos dar y en qué orden, según lo que va observando. Es la diferencia entre un script y un razonador.

---

### El patrón ReAct — Reason, Act, Observe

El ciclo que implementamos hoy se llama **ReAct** (Reasoning + Acting):

```
┌─────────────────────────────────────────────┐
│                CICLO ReAct                  │
│                                             │
│  Thought: "¿Qué necesito para responder?"  │
│      │                                      │
│      ▼                                      │
│  Action: elegir herramienta + parámetros   │
│      │                                      │
│      ▼                                      │
│  Observation: resultado de la herramienta  │
│      │                                      │
│      ▼                                      │
│  ¿Tengo suficiente info? ──No──► volver    │
│      │ Sí                                   │
│      ▼                                      │
│  Final Answer: respuesta al usuario        │
└─────────────────────────────────────────────┘
```

> **Pregunta #1**
> ¿Cuántas veces puede iterar el ciclo ReAct? ¿Puede quedar en un loop infinito?
>
> **Análisis:** Sí puede quedar en loop si las herramientas siempre devuelven resultados ambiguos o si el LLM no sabe cuándo parar. Por eso LangGraph permite definir un límite máximo de iteraciones (`max_iterations`) y condiciones de salida explícitas. En producción siempre se define un tope.

---

### Inversión de Control de Flujo

El cambio más drástico al pasar de un workflow (Clase 4) o un RAG (Clases 5-6) a un agente no es "cuánto sabe" el modelo, sino **quién controla la ejecución**.

En una arquitectura tradicional —incluido el RAG— el programador define un pipeline rígido: la consulta entra, se vectoriza obligatoriamente, se recuperan fragmentos y se genera una respuesta. El código dicta el camino; el LLM es un analizador de texto en nodos fijos.

En un agente, el programador ya no define una secuencia predeterminada. En su lugar, establece un **entorno con capacidades (herramientas) y un objetivo**. Es el modelo quien, en tiempo de ejecución, determina qué acción resulta adecuada a partir del objetivo, del estado actual y de los resultados obtenidos. El orquestador (LangGraph) se limita a ejecutar esa decisión y devolver el resultado al contexto del agente.

> **En términos simples:** hasta ahora, el flujo determinaba lo que pasaba; a partir de ahora, **lo que pasa determina el flujo**.

Bajo este paradigma, las acciones no responden a un guion rígido, sino que reaccionan a cada estado del sistema. El agente evalúa continuamente la situación y elige dinámicamente el mejor camino para alcanzar el objetivo, adaptando su recorrido paso a paso según las circunstancias.

---

### Traza de ejecución — ejemplo extendido

Para ver el ciclo ReAct funcionando en un caso con varias herramientas encadenadas, sigamos un mensaje de un distribuidor que condiciona una reserva a su situación crediticia:

> *"Hola, soy Distribuidora Norte (CUIT 30-71234567-8). Necesitamos reservar 300 metros de Gabardina Pesada Azul Marino si tenemos margen disponible en nuestra cuenta corriente."*

El desarrollador no programó un flujo rígido paso a paso (no escribió condiciones anidadas que obliguen a validar crédito antes de consultar stock). Simplemente habilitó un conjunto de herramientas — en este ejemplo extendido: `consultar_cuenta_corriente`, `consultar_producto`, `consultar_stock`, `obtener_cotizacion` y `crear_reserva` — y el agente construye dinámicamente el camino:

```
[Iteración 1]
Pensamiento: El usuario pide una reserva condicionada a su margen de crédito.
             Antes de ver stock, corroboro el estado comercial del CUIT.
Acción: consultar_cuenta_corriente(cuit="30-71234567-8")
Observación: {"estado": "Habilitado", "margen_disponible": 1500000}

[Iteración 2]
Pensamiento: Está habilitado con margen de $1.500.000. Ahora necesito
             el identificador técnico de "Gabardina Pesada Azul Marino".
Acción: consultar_producto("Gabardina Pesada Azul Marino")
Observación: {"id": "TEL-00427", "descripcion": "Gabardina 12 OZ Azul Marino"}

[Iteración 3]
Pensamiento: Confirmo si hay 300 metros disponibles de TEL-00427.
Acción: consultar_stock(articulo_id="TEL-00427", metros=300)
Observación: {"disponible": true, "sucursal": "Córdoba"}

[Iteración 4]
Pensamiento: Hay stock. Necesito el costo total antes de afectar el saldo.
Acción: obtener_cotizacion(articulo_id="TEL-00427", metros=300)
Observación: {"total_operacion": 960000}

[Iteración 5 — Condición de corte]
Pensamiento: El total ($960.000) es menor al margen ($1.500.000).
             Cumplo las condiciones de negocio, procedo con la reserva.
Acción: crear_reserva(cuit="30-71234567-8", articulo_id="TEL-00427", metros=300)
Observación: {"id_reserva": "RES-89421", "estado": "Confirmada"}

Respuesta Final: "Confirmamos la reserva de 300 metros de Gabardina Azul
Marino bajo el comprobante RES-89421. Se afectaron $960.000 a su cuenta
corriente, con un saldo disponible de $540.000."
```

> **Lo que hay que remarcar de esta traza:** cada iteración depende del resultado de la anterior — si el CUIT no estuviera habilitado, o si no hubiera stock, el agente habría tomado un camino completamente distinto (informar el problema, ofrecer una alternativa) sin que el desarrollador haya escrito esa rama a mano. Eso es exactamente la inversión de control de flujo.

---

## Bloque 2: Tool Use y Function Calling (50 min)

### Cómo el LLM decide qué herramienta usar

El LLM no ejecuta código directamente. Lo que hace es generar una descripción estructurada de qué herramienta quiere llamar y con qué parámetros. El framework (LangGraph) intercepta esa descripción, ejecuta la función real en Python, y le devuelve el resultado al LLM.

**El flujo técnico:**

```
LLM genera:
{
  "tool": "consultar_stock",
  "args": {"material": "denim", "sucursal": "filial_cordoba"}
}

LangGraph intercepta → ejecuta consultar_stock("denim", "filial_cordoba")
                     → obtiene resultado real
                     → lo pasa de vuelta al LLM como "Observation"
```

**Lo que hace que el LLM elija bien:** la **descripción de la herramienta**. Si la descripción es vaga, el LLM elige mal o no elige. Si es precisa, el LLM sabe exactamente cuándo usarla.

---

### Las tres herramientas de Ortelana

```python
from langchain_core.tools import tool
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
import os
from dotenv import load_dotenv

load_dotenv()

# ── Tool 1: Consultar stock del catálogo de telas ────────────────────────────
@tool
def consultar_stock_tela(material: str, sucursal: str = "cualquiera") -> str:
    """
    Busca telas disponibles en el catálogo de Ortelana Textil por tipo de material
    y sucursal. Usar cuando el cliente pregunta por disponibilidad, stock o
    características de una tela específica.

    Args:
        material: Tipo de tela o material buscado (ej: 'denim', 'seda', 'gabardina').
        sucursal: Sucursal donde buscar. Valores: 'central_buenos_aires',
                  'filial_cordoba', 'cualquiera'. Por defecto busca en todas.

    Returns:
        Información de las telas más similares disponibles con su stock y ubicación.
    """
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma(
        collection_name="catalogo_ortelana",
        embedding_function=embeddings,
        persist_directory="./ortelana_vectordb"
    )

    # Filtro híbrido: metadatos + semántica
    filtros = {"en_stock": True}
    if sucursal != "cualquiera":
        filtros["sucursal_disponible"] = sucursal

    resultados = vectorstore.similarity_search(
        query=material,
        k=2,
        filter=filtros
    )

    if not resultados:
        return f"No hay stock de '{material}' disponible en {sucursal}."

    respuesta = []
    for doc in resultados:
        meta = doc.metadata
        respuesta.append(
            f"[{meta.get('id', 'N/A')}] {doc.page_content[:100]}... "
            f"| Sucursal: {meta.get('sucursal_disponible')} "
            f"| Stock: {'✅' if meta.get('en_stock') else '❌'}"
        )
    return "\n".join(respuesta)


# ── Tool 2: Validar distribuidor por CUIT ────────────────────────────────────
@tool
def validar_distribuidor(cuit: str) -> str:
    """
    Valida el estado comercial de un distribuidor en la base de datos de Ortelana.
    Usar cuando el cliente menciona su CUIT o quiere saber si califica para
    crédito, financiación o cuenta corriente.

    Args:
        cuit: Número de CUIT del distribuidor (11 dígitos, con o sin guiones).

    Returns:
        Estado del distribuidor: categoría, deuda pendiente y elegibilidad
        para financiación según las normativas de Ortelana.
    """
    # En producción: consulta real a la BD SQL y API ARCA
    # Para el laboratorio: simulación con datos de prueba
    cuit_limpio = "".join(filter(str.isdigit, cuit))

    distribuidores_simulados = {
        "30712345678": {
            "razon_social": "Textiles Norpatagonia",
            "categoria": "A",
            "deuda_pendiente": False,
            "antiguedad_años": 3,
            "elegible_financiacion": True
        },
        "20345567892": {
            "razon_social": "Modas del Sur",
            "categoria": "B",
            "deuda_pendiente": True,
            "antiguedad_años": 1,
            "elegible_financiacion": False
        },
    }

    if cuit_limpio not in distribuidores_simulados:
        return f"CUIT {cuit} no encontrado en la base de datos de Ortelana. " \
               f"Puede ser un distribuidor nuevo o un CUIT inválido."

    datos = distribuidores_simulados[cuit_limpio]
    estado_financiacion = "✅ Elegible" if datos["elegible_financiacion"] else \
                          "❌ No elegible (deuda pendiente o categoría insuficiente)"

    return (
        f"Distribuidor: {datos['razon_social']}\n"
        f"Categoría: {datos['categoria']}\n"
        f"Deuda pendiente: {'Sí ❌' if datos['deuda_pendiente'] else 'No ✅'}\n"
        f"Antigüedad: {datos['antiguedad_años']} años\n"
        f"Financiación en cuotas: {estado_financiacion}"
    )


# ── Tool 3: Recuperar normativa comercial (RAG) ───────────────────────────────
@tool
def recuperar_normativa(consulta: str) -> str:
    """
    Busca en el reglamento comercial de Ortelana Textil para responder preguntas
    sobre políticas, condiciones, plazos y procedimientos. Usar cuando el cliente
    pregunta sobre reglas, requisitos, plazos de devolución, condiciones de
    financiación o cualquier política interna de la empresa.

    Args:
        consulta: La pregunta o tema sobre el cual buscar en el reglamento.

    Returns:
        Los artículos del reglamento más relevantes para la consulta.
    """
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma(
        collection_name="reglamento_ortelana_v2",
        embedding_function=embeddings,
        persist_directory="./ortelana_vectordb"
    )

    docs = vectorstore.similarity_search(consulta, k=3)

    if not docs:
        return "No encontré información sobre ese tema en el reglamento de Ortelana."

    return "\n\n---\n\n".join(doc.page_content for doc in docs)


# Lista de herramientas disponibles para el agente
TOOLS = [consultar_stock_tela, validar_distribuidor, recuperar_normativa]
```

> **Pregunta #2**
> ¿Por qué el docstring de cada tool es tan importante?
>
> **Análisis:** Porque es literalmente lo que el LLM lee para decidir cuándo usar cada herramienta. El LLM no ve el código Python — solo lee la descripción. Si el docstring dice "usar cuando el cliente menciona su CUIT", el LLM va a llamar a `validar_distribuidor` cada vez que detecte un CUIT en el mensaje. Un docstring vago = un agente que elige mal las herramientas.

---

### Sensores y actuadores — dos tipos de herramientas

No todas las tools tienen el mismo impacto sobre el entorno. Aunque las tres se programan con la misma sintaxis (`@tool`), conviene distinguirlas por su responsabilidad:

- **Herramientas de percepción (sensores):** leen el entorno y traen evidencia factual, sin producir ningún efecto secundario. `consultar_stock_tela`, `validar_distribuidor` y `recuperar_normativa` son sensores — son de bajo riesgo porque solo consultan información.
- **Herramientas de acción (actuadores):** mutan el estado del mundo real — bloquean stock, generan un compromiso comercial, modifican un saldo. La tarea asincrónica de esta clase (`abrir_ticket_reclamo`) ya es un actuador: al ejecutarse, crea un ticket real en el sistema de Ortelana.

```
Agente
  ├── consultar_stock_tela   → Consulta (sensor, bajo riesgo)
  ├── validar_distribuidor   → Consulta (sensor, bajo riesgo)
  ├── recuperar_normativa    → Consulta (sensor, bajo riesgo)
  └── abrir_ticket_reclamo   → Mutación (actuador, mayor riesgo)
```

> **Por qué importa la distinción:** delimitar de forma explícita qué tools son de solo lectura y cuáles escriben permite auditar el comportamiento del sistema (¿qué se consultó? ¿qué se modificó?) y decidir dónde conviene agregar una aprobación humana antes de ejecutar — el mismo criterio de riesgo que vimos en la Matriz de Intenciones de Clase 2, ahora aplicado a nivel de herramientas.

> **RAG como sensor de conocimiento:** notar que `recuperar_normativa` es, ni más ni menos, el pipeline RAG de las Clases 5-6 — pero acá ya no es "el sistema completo", es una herramienta de percepción más dentro del catálogo del agente. Cuando el agente detecta que necesita validar una normativa, invoca esa tool como un sensor para traer contexto, igual que invocaría cualquier otra.

---

### El desafío del diseñador: nombrar bien las capacidades

El modelo no ve el código Python de una tool — recibe una descripción textual de una capacidad. Por eso el nombre de la herramienta, sus parámetros y el significado de lo que devuelve **no son detalles menores de implementación**: son el lenguaje con el que la arquitectura le dice al modelo qué puede hacer y qué pasó cuando lo hizo.

No es lo mismo una herramienta llamada `consultar_stock_tela()` que una llamada `gestionar_producto()`. La primera expone una capacidad concreta y acotada; la segunda obliga al modelo a inferir qué operación puede realizar en cada caso, con mayor riesgo de que "invente" un uso incorrecto.

Lo mismo pasa con los parámetros: un argumento como `cantidad=300` es ambiguo si no queda claro si son metros, unidades o rollos. Y con el retorno: una respuesta como `True` dice mucho menos que `{"disponible": true, "cantidad": 450, "unidad": "metros"}` — el segundo formato le da al agente evidencia explícita para decidir el siguiente paso.

> **Regla práctica:** cuantas más tools ambiguas o "todo-en-uno" tenga el agente, mayor el riesgo de que elija mal o invente parámetros (*tool hallucination*). Herramientas pequeñas, con una única responsabilidad y nombres/parámetros/retornos explícitos, son más fáciles de combinar correctamente.

> **Conexión con principios de diseño de software:** esto no es un concepto nuevo — es SOLID (responsabilidad única) aplicado a un contexto nuevo. Una tool puede necesitar acceder a servicios de negocio o clientes de APIs sin quedar acoplada a su implementación concreta (Inyección de Dependencias), igual que cualquier otro componente de una arquitectura bien diseñada. Los agentes no reemplazan lo que ya se sabe de ingeniería de software — lo ponen a trabajar en un contexto donde, además de código, hay que diseñar el "lenguaje" con el que el modelo entiende sus propias capacidades.

---

## Bloque 3: Primer Agente de Ortelana con LangGraph (80 min)

### Instalación

```python
!pip install langgraph langchain-openai langchain-chroma --quiet
```

---

### El agente con LangGraph

LangGraph modela el agente como un grafo de nodos y aristas. Cada nodo es una función que transforma el estado. Las aristas definen el flujo — incluyendo condiciones (¿seguir iterando o responder?).

```python
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
import operator

# ── 1. Definir el estado del agente ─────────────────────────────────────────
class EstadoAgente(TypedDict):
    """
    El estado que viaja entre nodos del grafo.
    messages acumula toda la conversación: preguntas, respuestas del LLM
    y resultados de las herramientas.
    """
    messages: Annotated[Sequence[BaseMessage], operator.add]


# ── 2. El LLM con las herramientas disponibles ───────────────────────────────
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
llm_con_tools = llm.bind_tools(TOOLS)

SYSTEM_PROMPT = """Sos el asistente comercial inteligente de Ortelana Textil.
Tenés acceso a herramientas para consultar stock, validar distribuidores
y recuperar normativas. Usá las herramientas necesarias para dar respuestas
precisas y fundamentadas en datos reales.
Si necesitás múltiples datos para responder, usá las herramientas en el orden
que tenga más sentido. Respondé siempre en español."""


# ── 3. Nodo de razonamiento ──────────────────────────────────────────────────
def nodo_agente(estado: EstadoAgente) -> dict:
    """El LLM razona y decide si usar una herramienta o responder."""
    mensajes = [SystemMessage(content=SYSTEM_PROMPT)] + list(estado["messages"])
    respuesta = llm_con_tools.invoke(mensajes)
    return {"messages": [respuesta]}


# ── 4. Condición de salida ───────────────────────────────────────────────────
def debe_continuar(estado: EstadoAgente) -> str:
    """
    Si el último mensaje del LLM tiene tool_calls → ir al nodo de herramientas.
    Si no → el agente terminó, responder al usuario.
    """
    ultimo_mensaje = estado["messages"][-1]
    if hasattr(ultimo_mensaje, "tool_calls") and ultimo_mensaje.tool_calls:
        return "usar_herramienta"
    return END


# ── 5. Construir el grafo ────────────────────────────────────────────────────
nodo_herramientas = ToolNode(TOOLS)

grafo = StateGraph(EstadoAgente)

# Agregar nodos
grafo.add_node("agente", nodo_agente)
grafo.add_node("herramientas", nodo_herramientas)

# Punto de entrada
grafo.set_entry_point("agente")

# Aristas condicionales
grafo.add_conditional_edges(
    "agente",
    debe_continuar,
    {
        "usar_herramienta": "herramientas",
        END: END
    }
)

# Después de usar una herramienta, siempre volver al agente
grafo.add_edge("herramientas", "agente")

# Compilar
agente_ortelana = grafo.compile()
```

---

### Visualizar el grafo

```python
# Mostrar la estructura del grafo
print(agente_ortelana.get_graph().draw_ascii())
```

```
        +-----------+
        | __start__ |
        +-----------+
               │
               ▼
         +---------+
         |  agente  |◄──────────────┐
         +---------+                │
               │                    │
    ┌──────────┴──────────┐         │
    │                     │         │
    ▼                     ▼         │
  [END]           +--------------+  │
                  | herramientas |──┘
                  +--------------+
```

---

### Ejecutar el agente con la consulta compleja

```python
def consultar_agente(pregunta: str) -> str:
    """Ejecuta el agente y devuelve la respuesta final."""
    print(f"\n{'='*60}")
    print(f"CONSULTA: {pregunta}")
    print('='*60)

    resultado = agente_ortelana.invoke(
        {"messages": [HumanMessage(content=pregunta)]},
        config={"recursion_limit": 10}  # Máximo 10 iteraciones
    )

    # Mostrar el razonamiento paso a paso
    for i, mensaje in enumerate(resultado["messages"]):
        tipo = type(mensaje).__name__
        if tipo == "HumanMessage":
            continue
        elif tipo == "AIMessage":
            if hasattr(mensaje, "tool_calls") and mensaje.tool_calls:
                for tc in mensaje.tool_calls:
                    print(f"\n🔧 Herramienta elegida: {tc['name']}")
                    print(f"   Parámetros: {tc['args']}")
            else:
                print(f"\n💬 RESPUESTA FINAL:\n{mensaje.content}")
        elif tipo == "ToolMessage":
            print(f"\n📊 Resultado de herramienta:\n{mensaje.content[:200]}...")

    return resultado["messages"][-1].content


# Test con la consulta compleja del Bloque 1
respuesta = consultar_agente(
    "Hola, soy Textiles Norpatagonia, CUIT 30-71234567-8. "
    "Quiero saber si califico para financiación en cuotas y si tienen "
    "stock de denim azul en la sucursal de Córdoba para esta semana."
)
```

**Output esperado:**
```
============================================================
CONSULTA: Hola, soy Textiles Norpatagonia, CUIT 30-71234567-8...
============================================================

🔧 Herramienta elegida: validar_distribuidor
   Parámetros: {"cuit": "30-71234567-8"}

📊 Resultado de herramienta:
   Distribuidor: Textiles Norpatagonia | Categoría: A | Deuda: No ✅ | Financiación: ✅ Elegible...

🔧 Herramienta elegida: consultar_stock_tela
   Parámetros: {"material": "denim", "sucursal": "filial_cordoba"}

📊 Resultado de herramienta:
   [TELA-001] Denim pesado de 12 oz, 100% algodón... | Sucursal: filial_cordoba | Stock: ✅...

💬 RESPUESTA FINAL:
   ¡Hola Textiles Norpatagonia! Verificamos sus datos:

   ✅ Financiación en cuotas: Califican. Son distribuidores Categoría A sin
   deuda pendiente, por lo que acceden a financiación en 3 cuotas sin interés
   para órdenes superiores a $500.000.

   ✅ Stock de denim en Córdoba: Tenemos denim disponible en la sucursal
   filial_cordoba. Les recomendamos TELA-001 (Denim 12oz índigo, alta
   resistencia). Pueden coordinar el retiro esta semana.

   ¿Querés que te pasemos la cotización?
```

---

### Tests adicionales — casos edge

```python
# Test 1: Solo necesita una herramienta
consultar_agente("¿Cuáles son las condiciones para devolver material con defecto?")

# Test 2: CUIT no registrado
consultar_agente("Soy un distribuidor nuevo, CUIT 20-99999999-1, ¿puedo comprar?")

# Test 3: Consulta ambigua — ¿qué herramienta elige?
consultar_agente("Quiero saber todo sobre la gabardina elastizada")

# Test 4: Consulta que no requiere herramientas
consultar_agente("¿En qué horario puedo llamar al área comercial de Ortelana?")
```

> **Discutir el Test 4 con el grupo**
> El agente no tiene una herramienta para responder horarios de atención. ¿Qué hace? ¿Intenta usar `recuperar_normativa`? ¿Responde de memoria? ¿Dice que no sabe? Observar el comportamiento real y discutir cómo manejarlo — esto conecta con Guardrails en Clase 13.

---

## Bloque 4: Multiagente y Ollama (40 min)

### Cuándo un solo agente no alcanza

El agente de hoy funciona bien para Ortelana porque tiene 3 herramientas y un dominio acotado. Pero en sistemas más complejos, un solo agente empieza a fallar:

- **Demasiadas herramientas:** si el agente tiene 20 herramientas disponibles, el LLM se confunde al elegir
- **Tareas muy distintas:** el agente de stock no debería encargarse también de gestión de reclamos y análisis financiero
- **Paralelismo:** algunas tareas pueden ejecutarse al mismo tiempo — un agente solo es secuencial

**La solución — Arquitectura multiagente:**

```
                    ┌─────────────────┐
    Consulta ──────►│   Orquestador   │
                    │  (Router LLM)   │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
    ┌──────────────┐ ┌──────────┐ ┌──────────────┐
    │ Agente Stock │ │ Agente   │ │ Agente       │
    │ y Catálogo   │ │ Crédito  │ │ Reclamos     │
    └──────────────┘ └──────────┘ └──────────────┘
         Tools:           Tools:        Tools:
         consultar_stock  validar_cuit  abrir_ticket
         buscar_tela      check_deuda   escalar_caso
```

**El orquestador** recibe la consulta, decide qué agente(s) activar y consolida las respuestas. Cada subagente es experto en su dominio — tiene pocas herramientas bien definidas.

> **Esto lo construimos en Clase 10**
> En Clase 10 implementamos el orquestador con LangGraph: nodos que son agentes, aristas que son decisiones de routing, y estado compartido entre agentes. Hoy dejamos el concepto claro para que la implementación de la próxima clase tenga contexto.

---

### Ollama — El agente sin internet

**Ollama** permite correr modelos de lenguaje localmente sin consumir tokens ni necesitar internet. Útil para:
- Experimentar sin costo durante el desarrollo
- Datos sensibles que no pueden salir de la red (ej: datos fiscales de Ortelana)
- Entornos sin conexión o con restricciones de privacidad

```python
# Instalación: ollama.ai → descargar e instalar
# En terminal: ollama pull llama3.2

from langchain_ollama import ChatOllama

# Reemplazar el LLM de OpenAI por uno local
llm_local = ChatOllama(model="llama3.2", temperature=0)
llm_local_con_tools = llm_local.bind_tools(TOOLS)

# El resto del grafo LangGraph es idéntico — solo cambia el LLM
```

> **¿Cuándo usar Ollama vs OpenAI en el TP1?**
> - **Desarrollo y prototipado:** Ollama (sin costo, sin límites de rate)
> - **Evaluación con RAGAS:** OpenAI (mejor calidad para métricas)
> - **Producción:** depende del caso de uso, los datos y el presupuesto
>
> La ventaja de LangGraph es que el grafo no cambia — solo se intercambia el LLM.

---

## Cierre y Material Asincrónico (20 min)

### Resumen de la clase

- Una **cadena** (chain) ejecuta siempre los mismos pasos. Un **agente** decide en runtime qué pasos dar según lo que observa.
- El **docstring de cada tool** es lo que el LLM lee para decidir cuándo usarla — tiene que ser preciso y con ejemplos de cuándo usarla.
- **LangGraph** modela el agente como un grafo: nodo agente → condición → nodo herramientas → volver al agente → hasta que termine.
- El ciclo **ReAct** (Reason → Act → Observe) es el patrón detrás de todo agente moderno.
- **Multiagente** = orquestador que distribuye tareas a subagentes especializados. Lo implementamos en Clase 10.
- **Ollama** permite correr el mismo agente localmente sin consumir tokens.

---

### Material asincrónico — Entre Clase 9 y Clase 10

> **La Clase 10 arranca con este entregable**

**Actividad — Agregar una cuarta herramienta al agente:**

Implementar `abrir_ticket_reclamo(cuit, descripcion_problema, material)` y agregarla al agente de Ortelana.

```python
@tool
def abrir_ticket_reclamo(cuit: str, descripcion_problema: str, material: str) -> str:
    """
    Abre un ticket de reclamo de calidad en el sistema de Ortelana Textil.
    Usar cuando el cliente reporta un defecto, problema con el material recibido
    o cualquier inconveniente con un pedido anterior.

    Args:
        cuit: CUIT del distribuidor que hace el reclamo.
        descripcion_problema: Descripción del defecto o problema reportado.
        material: Tipo de material o tela con el problema.

    Returns:
        Número de ticket generado y pasos siguientes.
    """
    # Implementar la lógica de apertura de ticket
    pass  # ← completar
```

**Documentar:**
- ¿En qué consultas el agente elige esta herramienta vs las otras?
- ¿Hubo algún caso donde el agente confundió `abrir_ticket_reclamo` con `recuperar_normativa`? ¿Por qué?
- ¿Cómo mejorarías el docstring para que el agente elija mejor?

---

### Conexión con Clase 10

El agente de hoy funciona bien para consultas de un solo distribuidor. Pero Ortelana necesita que el sistema maneje flujos más complejos: un distribuidor que primero consulta stock, después hace un pedido, después reclama un defecto — todo en la misma sesión. Para eso el agente necesita **memoria y estado persistente entre turnos**. En Clase 10 implementamos eso con LangGraph: checkpointers, estado compartido y el orquestador multiagente.

---

## Bibliografía de la Clase

- **Yao, S., et al. (2022).** *ReAct: Synergizing Reasoning and Acting in Language Models.* arXiv:2210.03629. (El paper que define el patrón ReAct).
- **Documentación oficial LangGraph** — langchain-ai.github.io/langgraph
- **Documentación oficial LangChain** — python.langchain.com (Tools, Agents).
- **Documentación oficial Ollama** — ollama.ai
- **Russell, S., & Norvig, P. (2021).** *Artificial Intelligence: A Modern Approach.* Capítulo 2. (El ciclo del agente — cierre con Clase 1).
