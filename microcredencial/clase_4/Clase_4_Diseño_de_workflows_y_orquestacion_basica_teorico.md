# Clase 4: Diseño de Workflows y Orquestación Básica

**Programa:** Microcredencial #2 — Diseño de Aplicaciones Inteligentes
**Unidad 2 · Herramientas y Prototipado con IA**

**Objetivo técnico:** Convertir una llamada aislada a un modelo en un workflow: una secuencia de pasos con decisiones, dependencias y al menos una herramienta o validación. Entender qué resuelve un framework de orquestación como LangChain y cuándo conviene usarlo.

**Origen reutilizado:** Adaptación de IADS 3, Unidades 2 y 5; clases 3 y 9 (integración, tool use y flujos). Se toma de la Clase 9 únicamente el concepto de *herramienta* (tool) como función que el sistema puede ejecutar — la decisión autónoma de cuándo usarla (agentes) se profundiza en la Clase 6 de esta microcredencial.

---

## Estructura de la clase

| Bloque | Contenido |
|---|---|
| **Bloque 1** | De una llamada aislada a un flujo con pasos |
| **Bloque 2** | Cadenas, plantillas y salidas estructuradas |
| **Bloque 3** | Herramientas (tools): darle al sistema capacidad de ejecutar algo real |
| **Bloque 4** | Laboratorio: primer workflow ejecutable de Ortelana |
| **Cierre** | Hito 1 — concepto validado y conexión con Clase 5 |

---

## Bloque 1: De una llamada aislada a un flujo

En la Clase 3 logramos que el modelo extraiga intención y datos de un mensaje suelto. Pero el sistema real de Ortelana necesita encadenar pasos:

```
Mensaje del distribuidor
    → [Paso 1] El LLM extrae intención y datos
    → [Paso 2] El código valida esos datos
    → [Paso 3] Se ejecuta una acción o consulta
    → [Paso 4] El LLM redacta la respuesta final
```

Cada paso depende del resultado del anterior. Eso es un **workflow**: una secuencia de pasos con dependencias, no una llamada aislada.

> **Por qué importa:** un sistema que solo hace una llamada al modelo no puede validar, consultar datos reales ni tomar más de una decisión. El workflow es lo que permite que el sistema haga *varias cosas en orden* para llegar a una respuesta confiable.

---

## Bloque 2: Cadenas, plantillas y salidas estructuradas

### El "pegamento" de la lógica

Escribir a mano cada paso del flujo (formatear el prompt, llamar al modelo, parsear la salida, pasarla al siguiente paso) implica bastante código repetitivo. Los frameworks de orquestación —como **LangChain**— existen para reducir ese código de "plomería" y dejar visible solo la lógica de negocio.

**El patrón de cadena (chain):** una secuencia de componentes conectados, donde la salida de uno es la entrada del siguiente.

```python
# Idea conceptual de una cadena simple
cadena = plantilla_prompt | modelo | parser_de_salida

resultado = cadena.invoke({"mensaje": mensaje_del_distribuidor})
```

- **Plantilla de prompt:** define la estructura del mensaje que recibe el modelo, con espacios para variables (el mensaje del cliente, contexto adicional, etc.).
- **Modelo:** el LLM que procesa la plantilla ya completada.
- **Parser de salida:** transforma la respuesta cruda del modelo (texto) en un dato utilizable (JSON, string limpio, etc.).

### Criterios para elegir un framework de orquestación

No siempre hace falta un framework — para una sola llamada, código simple alcanza. Conviene sumar un framework cuando:

- Hay **más de dos pasos encadenados** con dependencias entre sí.
- Se necesita **reutilizar** la misma estructura de flujo en distintos contextos.
- El equipo va a mantener el proyecto en el tiempo y se beneficia de un patrón estándar en vez de código artesanal.

**LangChain** es la opción más extendida para armar cadenas y conectar modelos, herramientas y bases de datos. **LangGraph** (que vemos en la Clase 6) extiende esa idea para flujos donde el sistema debe *decidir* dinámicamente qué paso seguir. Existen alternativas (LlamaIndex, CrewAI, AutoGen) orientadas a casos más específicos — la recomendación es empezar por la opción más simple que resuelva el problema, no la más nueva o la más completa.

---

## Bloque 3: Herramientas — darle al sistema capacidad de ejecutar algo real

Hasta ahora el modelo solo "habla" — genera texto. Una **herramienta (tool)** es una función real de código que el sistema puede ejecutar como parte del flujo: consultar una base de datos, llamar a otra API, hacer un cálculo.

```python
def consultar_stock_tela(material: str, sucursal: str = "cualquiera") -> str:
    """
    Busca telas disponibles en el catálogo de Ortelana Textil por
    material y sucursal. Devuelve las coincidencias con su stock.
    """
    # En un workflow básico, esta función se llama en un paso fijo
    # de la secuencia — no la decide el modelo en tiempo real (eso es agentes, Clase 6).
    ...
```

> **Diferencia clave con un agente:** en el workflow de hoy, **el desarrollador decide** en qué paso de la secuencia se llama a cada herramienta — el orden está fijo de antemano. En un agente (Clase 6), es **el modelo quien decide** en tiempo real qué herramienta usar y cuándo. Hoy construimos la versión más simple y controlada: la secuencia fija.

### Puntos de control y validación

En cualquier workflow, conviene definir explícitamente:

- **Puntos de validación:** ¿dónde se revisa que el dato extraído sea correcto antes de avanzar al siguiente paso?
- **Puntos de intervención humana:** ¿qué casos, por su riesgo, deberían pausar el flujo y esperar una aprobación manual en lugar de seguir automáticamente?

---

## Bloque 4: Laboratorio — Primer workflow de Ortelana

### Consigna

Construir un workflow simple (3-4 pasos) para el caso de onboarding de Ortelana:

1. El LLM extrae intención y datos del mensaje del distribuidor.
2. El código valida el formato del CUIT extraído (una validación simple, no necesita ser el algoritmo de checksum completo).
3. Si la validación falla, el flujo se detiene y pide revisión humana; si pasa, continúa.
4. El LLM redacta una respuesta usando el resultado del paso anterior.

```python
def workflow_onboarding(mensaje: str) -> dict:
    datos = extraer_datos_llm(mensaje)          # Paso 1
    es_valido = validar_cuit(datos["cuit"])     # Paso 2

    if not es_valido:
        return {"estado": "REVISION_HUMANA", "motivo": "CUIT inválido"}

    respuesta = redactar_respuesta_llm(datos)   # Paso 4
    return {"estado": "COMPLETADO", "respuesta": respuesta}
```

### Revisión de fallas y control

Ejecutar el workflow contra al menos un caso que debería fallar (CUIT inválido o incompleto) y un caso que debería completarse. Documentar qué pasó en cada uno y en qué paso se detuvo el flujo con error.

---

## Cierre y entrega

### Resumen de la clase

- Un **workflow** convierte una llamada aislada en una secuencia de pasos con dependencias.
- Una **cadena** (chain) es el patrón que conecta plantilla → modelo → parser, reduciendo código repetitivo.
- Una **herramienta (tool)** es código real que el sistema ejecuta como parte del flujo — en un workflow básico, el orden de uso lo define el desarrollador, no el modelo.
- Todo workflow necesita **puntos de control**: dónde se valida y dónde interviene un humano antes de seguir.

### Evidencia / entrega de la clase — Hito 1

**Hito 1 — Concepto validado:** workflow básico ejecutable (mínimo 3 pasos, con al menos una validación o herramienta) y diagrama actualizado de la solución del caso propio de cada grupo.

### Herramientas usadas

LangChain · Python/Colab · Cursor AI o VS Code

### Conexión con Clase 5

El workflow de hoy usa solo lo que el modelo sabe de memoria. Pero Ortelana necesita respuestas ancladas en datos reales y actualizados —el catálogo de telas, la normativa vigente— para no alucinar. En la Clase 5 incorporamos **grounding**: embeddings y RAG como patrón de diseño para darle al sistema una base de conocimiento real.

---

## Bibliografía de la clase

- Documentación oficial de LangChain — python.langchain.com (conceptos de Chains y LCEL).
- Chase, H. (2023). *LangChain: Building Applications with LLMs* (capítulo introductorio de orquestación).
