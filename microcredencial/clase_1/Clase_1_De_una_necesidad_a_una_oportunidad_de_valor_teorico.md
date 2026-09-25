# Clase 1: De una Necesidad a una Oportunidad de Valor

**Programa:** Microcredencial #2 — Diseño de Aplicaciones Inteligentes
**Unidad 1 · Pensamiento de Soluciones con IA**

**Objetivo técnico:** Distinguir una aplicación inteligente de una automatización convencional, entender la arquitectura conceptual básica de un sistema con IA (usuario, datos, modelo, herramientas, reglas y salida) y aplicar criterios simples para reconocer una oportunidad de valor viable.

**Origen reutilizado:** IADS 3, Unidad 1; clases 1 y 2 (arquitectura, casos de uso y productos con IA). Se omite la profundidad técnica de PEAS extendido, embeddings y Russell & Norvig — quedan como marco conceptual liviano, no como competencia a evaluar.

---

## Estructura de la clase

| Bloque | Contenido |
|---|---|
| **Bloque 1** | El caso del curso: Ortelana Textil y el problema real de un negocio digitalizándose |
| **Bloque 2** | Taller express: experimentar la alucinación en vivo |
| **Bloque 3** | De un modelo aislado a un sistema inteligente — el mapa conceptual |
| **Bloque 4** | Taller: mapear la oportunidad de Ortelana y elegir el caso propio |
| **Cierre** | Ficha de oportunidad (entrega) y conexión con Clase 2 |

---

## Bloque 1: El caso del curso — Ortelana Textil

A lo largo de las 8 clases de esta microcredencial vamos a trabajar sobre **un mismo caso que evoluciona clase a clase**: Ortelana Textil, una fábrica y distribuidora mayorista de indumentaria en plena digitalización post-pandemia.

**El problema:** el crecimiento de canales como WhatsApp y e-commerce generó una avalancha de mensajes desestructurados — certificados fiscales, capturas de pantalla, consultas en texto libre. El equipo administrativo pasa gran parte del día transcribiendo datos a mano a un sistema de gestión antiguo, y decidiendo manualmente si un distribuidor califica para comprar a cuenta corriente.

**Por qué este caso funciona para aprender:** tiene datos desestructurados, reglas de negocio reales, sistemas legados y un dolor de negocio concreto. Cada clase de la microcredencial va a sumarle una capa de solución — desde el diagnóstico de hoy hasta el prototipo defendible de la Clase 8.

> **Para reflexionar:** ¿qué parte de ese proceso automatizarían primero — la de más volumen, la más compleja, o la que más tarda? Esa pregunta es exactamente la que resolvemos en la Clase 2 con las tres señales de oportunidad.

---

## Bloque 2: Taller express — "El Proveedor Enojado"

**Antes de explicar nada, experimentamos el problema central del curso.**

En grupos de 3, abrir ChatGPT, Claude o Gemini (versión web gratuita) e intentar que el modelo responda este mensaje como si fuera el sistema de atención de Ortelana Textil:

```
"Buen día. Soy distribuidor mayorista de Rosario. Mando mis datos:
CUIT 20-12345678-9, categoría B, facturación anual $180M.
Quiero saber si califico para cuenta corriente a 60 días según la
normativa interna de Ortelana. Adjunto certificado de habilitación."
```

**Objetivo:** que el modelo diga si el distribuidor califica, citando la normativa interna de Ortelana.

**Lo que va a pasar:** el modelo va a inventar una normativa que no existe, o va a dar una respuesta genérica que suena profesional pero es completamente falsa. Documentar la respuesta y marcar qué parte es inventada.

**Puesta en común:**
- ¿El modelo inventó normativas? ¿Con qué nivel de confianza?
- ¿Alguien logró que dijera "no sé"?

> **Conclusión clave:** el modelo no falló porque sea malo. Falló porque no tiene acceso a la normativa real de Ortelana. Su naturaleza es predecir la palabra más probable, no "decir la verdad". Cuando no tiene datos reales, inventa algo que *suena* correcto — eso se llama **alucinación**, y es el problema que resolvemos con grounding/RAG en la Clase 5.

---

## Bloque 3: De un modelo aislado a un sistema inteligente

### Modelo aislado vs. sistema inteligente

El taller mostró el límite de un modelo sin sistema alrededor.

**El modelo aislado** es el LLM solo, sin contexto ni capacidad de actuar por sí mismo — responde en el vacío, con lo que "suena bien".

**El sistema inteligente** es el ecosistema que rodea al modelo: usuario, datos reales, herramientas, reglas de negocio y una salida controlada. El modelo es una pieza del sistema — no el sistema completo.

> *Ejemplo: un modelo que detecta fraude con 99% de precisión pero tarda 10 segundos y no está conectado a la pasarela de pagos, no bloquea nada a tiempo. La utilidad no se mide solo por la precisión del modelo — se mide por su capacidad de actuar en el momento justo.*

### El mapa conceptual de una arquitectura inteligente

Toda aplicación inteligente, sin importar su complejidad, puede describirse con seis piezas:

| Pieza | Pregunta que responde | En Ortelana Textil |
|---|---|---|
| **Usuario** | ¿Quién interactúa con el sistema? | Distribuidor mayorista, equipo administrativo |
| **Datos** | ¿Qué información entra? | Correos, WhatsApp, PDFs, formularios |
| **Modelo** | ¿Qué razona sobre esos datos? | Un LLM (GPT, Claude, Gemini) |
| **Herramientas** | ¿Qué puede ejecutar el sistema? | Consultas a un ERP, envío de mails, alta de registros |
| **Reglas** | ¿Qué límites y validaciones existen? | Normativa comercial, validación de CUIT |
| **Salida** | ¿Qué recibe finalmente el usuario? | Una respuesta clara, una acción, un dato validado |

> **Conexión con el taller:** si el sistema de Ortelana tuviera acceso a la normativa real como dato (no solo el modelo respondiendo solo), la salida sería correcta en lugar de inventada. Ese es el hilo que conecta esta clase con toda la cursada: un modelo aislado alucina, un sistema con datos reales y reglas no.

### Criterios para reconocer un caso de uso viable

No toda idea con IA es una buena oportunidad. Cuatro criterios simples para evaluarla:

- **Valor:** ¿el resultado le importa de verdad a alguien? ¿Ahorra tiempo, dinero o reduce error?
- **Factibilidad:** ¿existe un modelo o herramienta capaz de resolverlo hoy, sin inventar tecnología?
- **Disponibilidad de datos:** ¿hay información real (aunque sea desordenada) sobre la que trabajar?
- **Riesgo:** ¿qué pasa si el sistema se equivoca? ¿Es tolerable o crítico?

> **Aplicado a Ortelana:** el onboarding de distribuidores tiene alto valor (reduce de días a minutos), es factible (LLM + validación de datos), tiene datos disponibles (correos, PDFs) y el riesgo es moderado (se puede supervisar antes de aprobar cuentas grandes).

---

## Bloque 4: Taller — Mapa inicial y elección del caso propio

### Parte A — Mapear la oportunidad de Ortelana (en grupo)

Completar en Markdown, usando el mapa conceptual de seis piezas:

```markdown
## Mapa inicial — Onboarding de Ortelana Textil

- Usuario: ...
- Datos: ...
- Modelo: ...
- Herramientas: ...
- Reglas: ...
- Salida: ...

### Aplicación de los 4 criterios
- Valor: ...
- Factibilidad: ...
- Disponibilidad de datos: ...
- Riesgo: ...
```

### Parte B — Elegir el caso propio (individual o por grupo de proyecto)

A partir de hoy, cada grupo elige (o inventa) su propia empresa o situación — real o ficticia, de cualquier rubro. La condición: debe tener un problema de la misma naturaleza que el de Ortelana — **datos desestructurados, procesos manuales, o decisiones que hoy dependen de que una persona interprete algo**.

Este caso propio es el que va a evolucionar durante las 8 clases hasta convertirse en el **Trabajo Final Aplicado**.

---

## Cierre y entrega

### Resumen de la clase

- Un **modelo aislado** predice; un **sistema inteligente** actúa con datos reales y reglas.
- Toda aplicación inteligente se describe con seis piezas: usuario, datos, modelo, herramientas, reglas y salida.
- Una oportunidad viable cumple cuatro criterios: **valor, factibilidad, datos disponibles y riesgo aceptable**.
- La **alucinación** no es un defecto del modelo — es la ausencia de datos reales y reglas en el sistema que lo rodea.

### Evidencia / entrega de la clase

**Ficha de oportunidad** (Markdown, individual o grupal): problema, usuario, proceso actual, intervención de IA propuesta, valor esperado y riesgo principal — aplicada al caso propio elegido en el Bloque 4.

### Herramientas usadas

ChatGPT / Claude / Gemini · Aula virtual

### Conexión con Clase 2

Hoy identificamos *que* hay una oportunidad. En la Clase 2 vamos a diseñar el producto: el recorrido del usuario, el alcance del MVP y el dilema técnico central de toda la cursada — ¿qué parte del sistema debe ser una regla determinista y qué parte necesita un LLM?

---

## Bibliografía de la clase

- Russell, S., & Norvig, P. (2021). *Artificial Intelligence: A Modern Approach.* 4th Ed. Pearson. Capítulos 1 y 2 (lectura introductoria, no evaluable).
- Huyen, C. (2025). *AI Engineering: Building Applications with Foundation Models.* O'Reilly. Capítulo 1.
- Mollick, E. (2024). *Co-Intelligence: Living and Working with AI.* Portfolio.
