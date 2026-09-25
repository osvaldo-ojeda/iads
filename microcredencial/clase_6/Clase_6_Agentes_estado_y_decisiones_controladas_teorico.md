# Clase 6: Agentes, Estado y Decisiones Controladas

**Programa:** Microcredencial #2 — Diseño de Aplicaciones Inteligentes
**Unidad 2 · Herramientas y Prototipado con IA**

**Objetivo técnico:** Distinguir un workflow determinista de un agente, implementar un agente simple que elija entre herramientas acotadas usando LangGraph, y diseñar un mínimo de estado y una condición de control o aprobación humana.

**Origen reutilizado:** IADS 3, Unidad 5; clases 9 y 10 (agentes, tool use, estado, memoria y orquestación). Se deja fuera de alcance la arquitectura multiagente completa (orquestador + subagentes especializados) de la Clase 10 original — se presenta solo como extensión conceptual. El foco de esta clase es un único agente con autonomía limitada y control humano.

---

## Estructura de la clase

| Bloque | Contenido |
|---|---|
| **Bloque 1** | De la cadena al agente — qué cambia y por qué |
| **Bloque 2** | Function calling y herramientas: cómo decide el LLM |
| **Bloque 3** | Estado, memoria mínima y condiciones de finalización |
| **Bloque 4** | Laboratorio: primer agente de Ortelana con LangGraph |
| **Cierre** | Hito 2 — esquema técnico y conexión con Clase 7 |

---

## Bloque 1: De la cadena al agente

En la Clase 4 construimos un **workflow**: una secuencia de pasos fija, definida de antemano por el desarrollador. Eso funciona bien cuando sabemos exactamente qué pasos se necesitan y en qué orden.

Pero hay consultas que no siguen un único camino. Por ejemplo:

> *"Soy Textiles Norpatagonia, CUIT 30-71234567-8. ¿Califico para financiación y tienen stock de denim en Córdoba?"*

Esta consulta necesita **dos verificaciones distintas** (validar el distribuidor y consultar stock), y no sabemos de antemano cuál hace falta hasta que el sistema interpreta la pregunta. Un workflow fijo tendría que anticipar todas las combinaciones posibles — algo que no escala.

> **La diferencia clave:** una **cadena** (workflow) ejecuta siempre los mismos pasos en el mismo orden. Un **agente** decide en tiempo de ejecución qué paso dar y en qué orden, según lo que va observando en cada resultado intermedio.

### Inversión de control de flujo

Esta diferencia tiene un nombre: en un workflow o un RAG, el programador define el camino de antemano — el código dicta los pasos y el LLM solo procesa texto en un punto fijo. En un agente, el programador ya no define esa secuencia — define un **entorno con capacidades (herramientas) y un objetivo**, y es el modelo quien decide en tiempo de ejecución qué acción tomar según el estado actual.

> En términos simples: hasta ahora el flujo determinaba lo que pasaba; con un agente, **lo que pasa determina el flujo**.

### El patrón ReAct (Reason → Act → Observe)

El ciclo que sostiene a un agente moderno:

```
Thought: "¿qué necesito para responder esta consulta?"
Action:  elegir una herramienta + sus parámetros
Observation: el resultado de esa herramienta
¿Alcanza para responder? → No: volver a razonar / Sí: responder
```

> **Sobre los loops infinitos:** un agente mal diseñado puede quedar iterando sin parar si las herramientas devuelven resultados ambiguos. Por eso siempre se define un límite máximo de iteraciones y condiciones de salida explícitas.

---

## Bloque 2: Function calling y herramientas

El LLM no ejecuta código directamente. Genera una descripción estructurada de qué herramienta quiere usar y con qué parámetros; el framework (LangGraph) intercepta esa descripción, ejecuta la función real en Python, y le devuelve el resultado al modelo como una "observación".

```python
from langchain_core.tools import tool

@tool
def validar_distribuidor(cuit: str) -> str:
    """
    Valida el estado comercial de un distribuidor en la base de Ortelana.
    Usar cuando el cliente menciona su CUIT o pregunta si califica para
    crédito o cuenta corriente.
    """
    ...

@tool
def consultar_stock_tela(material: str, sucursal: str = "cualquiera") -> str:
    """
    Busca telas disponibles por material y sucursal.
    Usar cuando el cliente pregunta por disponibilidad o stock.
    """
    ...

TOOLS = [validar_distribuidor, consultar_stock_tela]
```

> **Lo que hace que el agente elija bien:** la descripción (docstring) de cada herramienta. El LLM no ve el código — solo lee esa descripción para decidir cuándo usarla. Una descripción vaga produce un agente que elige mal; una descripción precisa, con ejemplos de cuándo usarla, produce decisiones consistentes.

### Sensores y actuadores — no todas las herramientas pesan igual

Aunque las dos tools del ejemplo se programan igual, tienen impacto muy distinto sobre el entorno:

- **`validar_distribuidor` y `consultar_stock_tela` son sensores:** leen información y no producen ningún efecto secundario — bajo riesgo.
- Una herramienta que **escriba** algo (por ejemplo, aprobar una cuenta o abrir un ticket) es un **actuador**: muta el estado real del negocio — mayor riesgo.

> Nombrar bien esta diferencia ayuda a decidir dónde poner control humano (Bloque 3): un agente puede tener autonomía total para usar sensores, pero un actuador de alto riesgo debería requerir aprobación antes de ejecutarse.

---

## Bloque 3: Estado, memoria mínima y condiciones de finalización

### Estado del agente

Un agente necesita un **estado** que viaje entre cada paso de razonamiento: qué se preguntó, qué herramientas ya se usaron, qué resultados se obtuvieron.

```python
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
import operator

class EstadoAgente(TypedDict):
    messages: Annotated[Sequence[BaseMessage], operator.add]
    iteraciones: int
```

Para un caso más completo también puede llevar campos propios del dominio (por ejemplo, el CUIT ya identificado en la conversación), de forma que el agente no tenga que volver a pedirlo en cada turno.

### Nodos, aristas y control de flujo (LangGraph)

LangGraph modela el agente como un grafo: cada **nodo** es una función que transforma el estado, y las **aristas** definen el flujo entre nodos — incluyendo aristas condicionales que deciden "¿sigo iterando o ya puedo responder?".

```python
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

def nodo_agente(estado):
    respuesta = llm_con_tools.invoke(estado["messages"])
    return {"messages": [respuesta]}

def debe_continuar(estado):
    ultimo = estado["messages"][-1]
    if hasattr(ultimo, "tool_calls") and ultimo.tool_calls:
        return "usar_herramienta"
    return END

grafo = StateGraph(EstadoAgente)
grafo.add_node("agente", nodo_agente)
grafo.add_node("herramientas", ToolNode(TOOLS))
grafo.set_entry_point("agente")
grafo.add_conditional_edges("agente", debe_continuar, {"usar_herramienta": "herramientas", END: END})
grafo.add_edge("herramientas", "agente")

agente_ortelana = grafo.compile()
```

### Autonomía limitada y human-in-the-loop

Un agente de producción no debería tener autonomía total sobre decisiones de alto riesgo. El mismo criterio de la Clase 2 (matriz de intenciones y riesgo) se aplica acá: las acciones de bajo riesgo (consultar stock) puede resolverlas el agente solo; las de alto riesgo (aprobar una cuenta corriente) deberían pausar el flujo y esperar una aprobación humana antes de ejecutarse.

> **Registro de decisiones:** por cada corrida del agente conviene registrar qué herramientas se usaron, en qué orden y con qué parámetros — esto no es opcional en un sistema real: es lo que permite auditar por qué el sistema tomó una decisión, algo que retomamos con más profundidad en la Clase 7.

---

## Bloque 4: Laboratorio — Primer agente de Ortelana

### Consigna

1. Definir 2-3 herramientas acotadas para el caso propio de cada grupo (o para Ortelana, si prefieren empezar por el caso guiado).
2. Construir el agente con LangGraph siguiendo el patrón del Bloque 3.
3. Definir el estado mínimo necesario (al menos `messages` y un campo de control de iteraciones).
4. Agregar una condición de control: si el agente identifica una acción de alto riesgo (por ejemplo, aprobar crédito), debe detenerse y marcar el caso para revisión humana en lugar de resolverlo solo.

### Test de validación

Ejecutar el agente con una consulta que necesite **dos herramientas distintas** (como el ejemplo del Bloque 1) y verificar en el registro de mensajes que el agente:
- Usó ambas herramientas en un orden razonable.
- No entró en un loop.
- Se detuvo correctamente si detectó el caso de alto riesgo.

> **Nota conceptual — cuando un agente no alcanza:** si un sistema necesita coordinar muchas herramientas muy distintas entre sí (por ejemplo, catálogo, crédito y reclamos como especialidades separadas), la arquitectura evoluciona hacia un **orquestador con subagentes especializados** — un router que deriva cada consulta al experto correspondiente. Esta microcredencial no profundiza esa arquitectura; alcanza con entender que existe como próximo escalón.

---

## Cierre y entrega

### Resumen de la clase

- Una **cadena** ejecuta siempre los mismos pasos; un **agente** decide en tiempo de ejecución según lo que observa (patrón ReAct).
- El **docstring de cada herramienta** es lo que el LLM lee para decidir cuándo usarla.
- **LangGraph** modela el agente como nodos + aristas, incluyendo aristas condicionales de control de flujo.
- La **autonomía debe ser limitada**: las decisiones de alto riesgo requieren intervención humana, no solo la decisión del modelo.

### Evidencia / entrega de la clase — Hito 2

**Hito 2 — Esquema técnico:** diagrama de componentes, estados, herramientas, datos y controles del agente diseñado para el caso propio.

### Herramientas usadas

LangGraph · LangChain · Ollama o API de un modelo

### Conexión con Clase 7

Hasta acá construimos capacidades técnicas: prompting, workflows, RAG, agentes. En la Clase 7 damos un paso distinto: integrar todo en un recorrido de punta a punta y someterlo a criterios de calidad, pruebas y guardrails — la diferencia entre un prototipo que "funciona en la demo" y uno diseñado con responsabilidad.

---

## Bibliografía de la clase

- Yao, S., et al. (2022). *ReAct: Synergizing Reasoning and Acting in Language Models.* arXiv:2210.03629.
- Documentación oficial de LangGraph — langchain-ai.github.io/langgraph
- Documentación oficial de Ollama — ollama.ai
