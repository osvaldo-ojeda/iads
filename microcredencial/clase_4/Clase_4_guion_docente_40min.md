# Guion Docente — Clase 4: Diseño de Workflows y Orquestación Básica

**Microcredencial #2 · Unidad 2 · Clase 4 de 8**
**Formato:** unos 40 minutos de exposición con preguntas al grupo, recorrida por el código (`practica/clase_4/`) y después laboratorio (Hito 1).

> Este guion es para **dar la clase hablando**. Las preguntas al grupo tienen la respuesta debajo: dejá que contesten primero y después completá.
> El teórico de referencia sigue siendo `Clase_4_Diseño_de_workflows_y_orquestacion_basica_teorico.md`. Donde la práctica va más allá del teórico, el guion lo marca con **🔗 Puente con el teórico**.

---

## La idea que tiene que quedar

> ### **En un workflow, el orden de los pasos lo decide el desarrollador. El modelo solo trabaja en los pasos que le tocan.**

- **Clase 3:** una llamada suelta (el LLM extrae, el código valida).
- **Clase 4 (hoy):** esa llamada pasa a ser **un paso** dentro de una secuencia, con reglas, una herramienta, puntos de control y una persona que aprueba.
- **Clase 6:** cuando el que decide qué paso sigue sea el **modelo**, va a ser un **agente**.

Esta clase es la base de la Clase 6: si no queda claro *quién decide el orden*, después no se entiende qué tiene de distinto un agente.

---

## Mapa de tiempos

| Min | Bloque | Qué se llevan |
|---|---|---|
| 0–8 | **Repaso de las Clases 1 a 3** con preguntas | Qué tenemos y qué le falta para ser un sistema |
| 8–14 | **Bloque 1:** de llamada aislada a workflow | Qué es un workflow: pasos + dependencias + decisiones |
| 14–22 | **Bloque 2:** cadenas y frameworks | `plantilla \| modelo \| parser`, y cuándo vale la pena un framework |
| 22–32 | **Bloque 3:** herramientas y puntos de control | Tool = código que el sistema ejecuta. Workflow vs. agente. Dónde frena el flujo |
| 32–40 | **Recorrida por el código** y consigna del Hito 1 | La traza de los casos en `practica/clase_4/` |
| 40+ | **Laboratorio** | Workflow propio (Hito 1) |

---

## 0–8 min · Repaso: de dónde venimos

**Para contar (2 min):**
> "En la Clase 1 vimos que el modelo solo **inventa**. En la Clase 2 decidimos que el LLM **interpreta** y el código **decide**. En la Clase 3 lo bajamos a código: el LLM extrae los datos del mensaje, `json.loads()` y Pydantic verifican el formato, y una regla verifica el CUIT."

Recordar el flujo de la Clase 3 en el pizarrón:

```
Mensaje → [LLM extrae] → json.loads() → Pydantic → regla CUIT → extracción validada
```

**❓ Pregunta 1:** *Con lo que armamos en la Clase 3, si llega "Somos Modas del Sur, CUIT 30-71589632-6, facturamos 95 palos, queremos cuenta corriente", ¿el distribuidor recibe una respuesta?*

> **Respuesta:** **no.** Obtenemos un JSON validado y ahí termina. Nadie revisa si mandó la documentación, nadie consulta si ya es cliente o si debe plata, nadie calcula la categoría y nadie le contesta. Tenemos **un paso** del sistema, no el sistema.

**❓ Pregunta 2:** *¿Qué le falta a eso para ser un sistema real? Nombren cosas.*

> **Respuesta (dejar que lleguen solos):** verificar la documentación, consultar el sistema de gestión, calcular la categoría, que una persona apruebe y responderle al distribuidor. En una frase: **le faltan más pasos, en orden, y que unos dependan de otros.** Eso es un workflow.

**❓ Pregunta 3:** *En la Clase 3, el caso de manipulación a veces daba `ALTA_DISTRIBUIDOR` y a veces `FUERA_DE_ALCANCE`. ¿Pydantic lo detectaba?*

> **Respuesta:** **no.** Las dos son intenciones válidas. Pydantic garantiza que esté **bien formado**, no que sea **correcto**. Hoy vamos a ver que, aunque el modelo se equivoque, **el diseño del workflow hace que no se apruebe nada**: el modelo nunca tiene en sus manos la decisión.

---

## 8–14 min · Bloque 1: de llamada aislada a workflow

### ¿Qué es un workflow?

> **Un workflow es una secuencia de pasos donde cada paso usa el resultado del anterior, con decisiones en el medio.**

Tres palabras clave para escribir en el pizarrón:
- **Pasos:** cada uno hace **una** cosa (extraer, validar, consultar, calcular, redactar).
- **Dependencias:** no se puede calcular la categoría sin la facturación, ni consultar el sistema sin un CUIT válido.
- **Decisiones:** según el resultado de un paso, el flujo sigue, toma otro camino o **se detiene**.

> **Analogía:** una línea de producción. Cada estación hace su parte y le pasa la pieza a la siguiente. Si una estación detecta una falla, la pieza **sale de la línea** y no sigue avanzando con el defecto.

### El flujo del teórico y el journey real

El teórico muestra el esqueleto con 4 pasos:

```
[1] LLM extrae  →  [2] código valida  →  [3] acción o consulta  →  [4] LLM redacta
```

**🔗 Puente con el teórico:** esos 4 pasos son una **versión resumida** del journey de 11 pasos de la Entrega 1. Mostrar cómo se expanden:

| Teórico (4 pasos) | Journey de la Entrega 1 | Tipo |
|---|---|---|
| 1. El LLM extrae | 2. Extraer datos | 🤖 LLM |
| 2. El código valida | 4. Contrato · 5. CUIT · 6. Documentación | 📏 Regla |
| 3. Acción o consulta | 7. Sistema de gestión · 8. Categoría · 9. Legajo | 🔧 Herramienta + 📏 Regla |
| — | 10. Aprobación | 🙋 Humano |
| 4. El LLM redacta | 11. Redactar respuesta | 🤖 LLM |

**Para remarcar:** el LLM aparece en **2 pasos** y son **opuestos**:
- **Paso 2:** lenguaje → datos (*"95 palos"* → `95000000`).
- **Paso 11:** datos → lenguaje (`categoría B, 30 días` → *"Tu solicitud fue aprobada…"*).

Todo lo del medio es código o una persona. El LLM está **en los bordes**: es la interfaz de entrada y de salida.

**❓ Pregunta 4:** *¿Por qué no hacemos todo en una sola llamada? Le pasamos al LLM el mensaje y la normativa y le pedimos "decime si califica y redactá la respuesta".*

> **Respuesta:** porque volvemos a la Clase 1 y a la Clase 2. El modelo puede **calcular mal** la categoría, **obedecer** el "apruébennos como VIP Oro" y **no sabe** si el distribuidor debe plata (eso está en el sistema de gestión). Además, si algo sale mal no sabemos **en qué parte** falló. Separar en pasos permite validar cada uno y detener el flujo en el lugar exacto.

---

## 14–22 min · Bloque 2: cadenas y frameworks

### El patrón de cadena

En cada llamada al modelo hay que hacer siempre las mismas tres cosas:

1. **Armar el mensaje** (instrucciones + datos del usuario) → **plantilla**
2. **Llamar al modelo** → **modelo**
3. **Convertir la respuesta en algo usable** → **parser**

LangChain le pone nombre a eso y lo conecta con un `|` (se lee "y después"):

```python
cadena = plantilla | modelo | parser
resultado = cadena.invoke({"mensaje": mensaje_del_distribuidor})
```

> **Analogía:** es una **tubería**. Lo que sale de un caño entra en el siguiente. El `|` es la unión entre caños.

**Clave para que no se confundan:** el paso 2 de la Clase 3 **ya era una cadena**, solo que escrita a mano:

| Pieza de la cadena | En la Clase 3 (a mano) | En LangChain |
|---|---|---|
| Plantilla | `armar_mensaje_usuario()` + el archivo del prompt | `ChatPromptTemplate` |
| Modelo | `llamar_con_reintentos()` | `ChatGoogleGenerativeAI`, etc. |
| Parser | `json.loads()` + Pydantic + regla CUIT | `StrOutputParser()` + **nuestra validación** |

**❓ Pregunta 5:** *Si usamos LangChain, ¿nos podemos olvidar de Pydantic y de la regla del CUIT?*

> **Respuesta:** **no.** El framework ahorra la **plomería**: armar los mensajes, llamar a la API, sacar el texto de la respuesta. La **validación y las reglas de negocio siguen siendo nuestras**. En la práctica, `python app.py lcel` corre el paso 2 como cadena LCEL y da **el mismo resultado**: el parser es la misma función de la Clase 3.

### ¿Cuándo conviene un framework?

> **Frase ancla:** *"Empezar por la opción más simple que resuelva el problema, no la más nueva."*

Conviene sumar un framework cuando:
- Hay **más de dos pasos encadenados** que se repiten en muchos lugares.
- La misma estructura se **reutiliza** en distintos contextos.
- El equipo va a **mantenerlo en el tiempo** y le sirve un patrón estándar.

No hace falta para una llamada sola, o cuando el flujo es corto y fijo.

**Para contar:** el workflow de la práctica está escrito **en Python directo, a propósito**. Son pasos fijos y solo dos llamadas al LLM. Un framework no simplificaba nada. LangChain aparece solo en un archivo opcional, para comparar.

### LangChain vs. LangGraph (1 min, sin código)

| | LangChain (hoy) | LangGraph (Clase 6) |
|---|---|---|
| Forma | Cadena: A → B → C | Grafo: con ciclos y bifurcaciones |
| ¿Quién decide el camino? | El **desarrollador**, de antemano | El **modelo**, en tiempo real |

> ⚠️ **Del machete:** no mezclar "cadena" con "agente" hoy. El orden lo fija el desarrollador.

**❓ Pregunta 6:** *¿Es obligatorio usar LangChain para el Hito 1?*

> **Respuesta:** **no.** Python directo vale. Se evalúa que el workflow tenga **pasos claros, dependencias y puntos de control**, no la sintaxis de un framework. Lo dice la consigna de la Entrega 3.

---

## 22–32 min · Bloque 3: herramientas y puntos de control

### ¿Qué es una herramienta (tool)?

> **Una herramienta es una función de código que el sistema ejecuta para hacer algo real:** consultar una base de datos, llamar a otra API, hacer un cálculo.

Hasta ahora el modelo solo **habla** (genera texto). Con herramientas, el sistema **hace**.

**🔗 Puente con el teórico:** el teórico usa de ejemplo `consultar_stock_tela`. Sirve para entender la idea, pero **en nuestro MVP el stock quedó fuera de alcance** (Entrega 1). La herramienta que pide **nuestro journey** es la del paso 7:

```python
def consultar_sistema_gestion(cuit: str) -> dict:
    """
    Busca un distribuidor por CUIT en el sistema de gestión de Ortelana.
    Devuelve si ya es cliente, su antigüedad en meses y los días de deuda vencida.
    Tipo: SENSOR (solo lee).
    """
```

Es el mismo concepto: una función que el sistema llama. Cambia **qué** consulta.

**❓ Pregunta 7:** *¿Por qué hace falta esta herramienta? ¿No alcanza con lo que dice el mensaje?*

> **Respuesta:** porque hay datos que **el distribuidor no dice y el LLM no puede saber**: si ya es cliente, desde cuándo y si debe plata. **La base de datos es la autoridad.** En la práctica hay dos casos que lo muestran: *Distribuidora Andina* factura 450M y entra en **B** (es nueva, NOR-NUEVO), mientras que *Grupo Norte Moda* factura 400M y entra en **A** (es cliente hace 18 meses). **La diferencia la pone la herramienta, no el mensaje.**

### Sensor vs. actuador (adelanto para la Clase 6)

| Tipo | Qué hace | Riesgo | Ejemplo |
|---|---|---|---|
| **Sensor** | Solo **lee** | Bajo | Consultar el sistema de gestión |
| **Actuador** | **Escribe** o tiene efecto real | Alto | Dar de alta la cuenta corriente |

Conecta con la Matriz de la Clase 2: *lo que escribe o compromete plata lleva más control.* Fijate que en la práctica **no hay ningún actuador automático**: el alta la hace una persona.

### Workflow vs. agente: quién decide

> **La diferencia más importante de la clase.**

| | Workflow (hoy) | Agente (Clase 6) |
|---|---|---|
| ¿Quién decide qué herramienta usar y cuándo? | **El desarrollador**, en el código | **El modelo**, en tiempo real |
| Previsibilidad | Alta: siempre el mismo camino | Menor: puede elegir distinto |
| Cuándo conviene | Procesos conocidos y regulados | Consultas abiertas e impredecibles |

> **Analogía:** el workflow es una **receta**: paso 1, paso 2, paso 3. El agente es un **cocinero con la heladera llena**: mira qué le pidieron y decide qué usar.

**❓ Pregunta 8:** *El onboarding de Ortelana, ¿conviene hacerlo con un workflow o con un agente?*

> **Respuesta:** con un **workflow**. El proceso está **definido por la normativa**: siempre hay que validar el CUIT, verificar documentos, consultar el sistema y calcular la categoría, en ese orden. No hay nada que "decidir" sobre el camino. Además tiene **consecuencia financiera**: queremos que sea predecible y auditable. El agente conviene para cosas abiertas, como una consulta libre que puede necesitar distintas fuentes.

**❓ Pregunta 9:** *En la práctica, según la intención, el flujo toma caminos distintos: un alta sigue y una consulta de stock se deriva. ¿Eso no es que "decide el modelo"?*

> **Respuesta:** **no, y es una distinción fina.** El modelo **clasifica** la intención (paso 2), pero **qué se hace con cada intención** lo escribió el desarrollador en un `if`. El modelo no elige el camino: pone una etiqueta, y el código tiene el mapa de qué camino corresponde a cada etiqueta. Es la **Matriz de Intenciones** de la Clase 2 convertida en código.

### Puntos de control

En todo workflow hay que definir explícitamente:

- **Puntos de validación:** ¿dónde se revisa que el dato sea correcto **antes** de seguir?
- **Puntos de intervención humana:** ¿qué casos, por su riesgo, tienen que **pausar** el flujo y esperar a una persona?

> **Frase ancla:** *"Un workflow sin puntos de control es una llamada larga al LLM."*

**❓ Pregunta 10 (del machete — recoger 2 o 3 respuestas antes de dar la propia):** *¿En qué paso del onboarding de Ortelana debería intervenir una persona?*

> **Respuesta:** hay **dos** lugares, por motivos distintos:
> 1. **Cuando algo falló:** CUIT inválido o extracción rota. Puede ser un error del distribuidor **o del LLM**, así que una persona revisa el mensaje original.
> 2. **Siempre, antes de aprobar** una cuenta corriente: lo exige **NOR-APROB**. No importa qué tan bien funcione el sistema, **el sistema recomienda y la persona decide**.

### Los estados de salida

La práctica tiene **4 lugares donde el flujo se detiene**. Conviene mostrarlos así:

| Estado | Cuándo | ¿Qué pasa después? |
|---|---|---|
| `REVISION_HUMANA` | CUIT inválido o extracción rota | Una persona mira el mensaje original |
| `DERIVADO` | No es un alta (stock, consulta normativa…) | Respuesta fija según la Matriz |
| `PENDIENTE` | Faltan datos o documentos | **Se le piden** al distribuidor. **No se rechaza** (NOR-DOC) |
| `PENDIENTE_APROBACION` | Legajo completo | Espera al Jefe de Administración |

**❓ Pregunta 11:** *Si a un distribuidor le falta la constancia de Ingresos Brutos, ¿lo rechazamos?*

> **Respuesta:** **no.** NOR-DOC dice que queda **pendiente** hasta que la complete. Rechazar a alguien por olvidarse un papel haría perder clientes. "Detener el flujo" no es lo mismo que "rechazar": a veces es **pedir lo que falta**.

**🔗 Puente con el teórico:** el laboratorio del teórico dice que alcanza con validar el **formato** del CUIT. Nosotros **ya tenemos el dígito verificador completo desde la Clase 3**, así que lo usamos. Es la misma consigna, con una validación más fuerte.

---

## 32–40 min · Recorrida por el código

Proyectar `practica/clase_4/` y correr:

```bash
cd practica/clase_4
python app.py
```

Corre **sin API key** (modo simulación). Cada caso muestra su **traza**: los pasos que recorrió, con un ícono para el tipo (🤖 LLM, 📏 Regla, 🔧 Herramienta, 🙋 Humano) y dónde se detuvo.

**Casos para mostrar (con 3 alcanza):**

| Caso | Qué mostrar | Concepto |
|---|---|---|
| **1 · Completo (B)** | Recorre todo y se detiene en el paso 10 | El camino feliz y el punto de control humano |
| **3 · CUIT inválido** | La traza tiene **2 líneas** y termina en `REVISION_HUMANA` | La falla controlada: **no sigue con datos malos** |
| **2 · Falta un documento** | Es el caso "típico" de la Clase 3, y hoy queda `PENDIENTE` | La extracción estaba bien, pero el negocio pide más |

Si sobra tiempo: **5 vs. 6** (la herramienta cambia la categoría) y **4 · Manipulación** ("VIP Oro" queda como alerta y nadie aprueba nada).

**Los archivos, uno por pregunta:**

| Archivo | ¿Qué responde? |
|---|---|
| `ortelana/workflow.py` | ¿En qué orden pasan las cosas? **(el corazón de la clase)** |
| `ortelana/reglas.py` | ¿Qué decide el código? (NOR-DOC, NOR-CAT, NOR-NUEVO, NOR-DEUDA) |
| `ortelana/herramientas.py` | ¿Qué consulta el sistema? (la tool) |
| `ortelana/redactor.py` | ¿Cómo se comunica la decisión? (paso 11) |
| `ortelana/extractor.py` | Lo mismo que en la Clase 3, sin cambios |

**Para el final, en vivo:**

```bash
python app.py --manual
```

Vos hacés de Jefe de Administración: el sistema muestra el legajo con la recomendación y las alertas, y vos escribís `s` o `n`. Es la forma más clara de mostrar que **la decisión es de una persona**.

---

## Consigna del Hito 1 (para dejar proyectada)

Cada grupo, **sobre su caso propio**:

1. Un workflow de **al menos 3 pasos** en secuencia (pueden reusar el prompt de la Entrega 2).
2. **Al menos una validación en código** con lógica real del dominio. No vale `if True`.
3. **Al menos un punto de control** donde el flujo se detiene antes de seguir.
4. Probarlo con **un caso que se completa** y **uno que se detiene**, y documentar **en qué paso** se detuvo.
5. Actualizar el **diagrama** de la Clase 2 con los pasos, las decisiones y qué es LLM y qué es regla.

> **El Hito 1 es el primer entregable formal ponderado.** Recordarlo explícitamente.

El ejemplo resuelto (nivel "Destacado") está en `practica/clase_4/docs/ortelana_entrega_3_informe.md`, Parte A. En la misma carpeta están los informes de las Entregas 1 y 2, para tener el proyecto completo a la vista.

**Si el grupo tiene bajo dominio técnico:** que partan de `workflow.py` y lo adapten a su dominio. Se evalúa el **diseño del flujo y los puntos de control**, no la sintaxis.

---

## Cierre (lo que tienen que llevarse)

- Un **workflow** convierte una llamada suelta en una **secuencia de pasos con dependencias y decisiones**.
- En un workflow, **el orden lo decide el desarrollador**. El modelo solo trabaja en sus pasos (los bordes: extraer y redactar).
- Una **cadena** (`plantilla | modelo | parser`) ahorra plomería, **no validación**.
- Un framework se suma cuando simplifica, **no por defecto**.
- Una **herramienta** es código que el sistema ejecuta. Hoy se llama en un paso fijo; en la Clase 6, la elige el modelo.
- Todo workflow necesita **puntos de control**: dónde se valida y dónde decide una persona.

**Lo que viene:**
- Hoy las consultas normativas se **derivan** con un texto fijo → **Clase 5:** RAG con la normativa real.
- Hoy el desarrollador decide el camino → **Clase 6:** el modelo decide (agentes).

---

## Preguntas que pueden aparecer (con respuesta)

**¿El paso 11 no es peligroso? El LLM podría inventar condiciones en la respuesta.**
Por eso recibe **solo un JSON con la decisión ya tomada** (categoría, plazo, límite, reglas) y el prompt dice *"comunicá la decisión, no la cambies"*. Las notas internas del legajo no le llegan. Igual puede equivocarse: controlar la salida del LLM (guardrails) es tema de la Clase 7.

**¿Qué pasa si la API se cae en el paso 11?**
Se usa una **plantilla fija**. La decisión ya está tomada, así que se puede comunicar igual. No tendría sentido que un error al redactar frene una aprobación.

**¿Por qué la redacción usa temperatura 0.3 y la extracción 0?**
En la extracción queremos el resultado **más estable posible** (un JSON). En la redacción queremos un texto que suene natural, y un poco de variación ayuda. Los datos no cambian porque vienen fijos en el JSON.

**¿Por qué a un cliente con deuda no se le pide la documentación?**
Porque NOR-DOC la exige **solo para cuenta corriente**, y con deuda vencida (NOR-DEUDA) opera al contado. Por eso el workflow verifica los documentos en el paso 6, pero los **exige** recién después del paso 8, cuando ya sabe la categoría. **El orden de los pasos también es una decisión de diseño.**

**¿El paso 3 (identificar los adjuntos) dónde está?**
Queda fuera: hoy trabajamos solo con texto, así que usamos los documentos que el distribuidor **dice** que manda. Leer PDFs o imágenes sería otro paso con LLM.

**¿Qué diferencia hay entre una herramienta y una función común?**
En código, ninguna: es una función. Se le dice "herramienta" por **el rol que cumple**: le da al sistema la capacidad de hacer algo en el mundo real (consultar, escribir). En la Clase 6 la diferencia se nota, porque el **docstring** pasa a ser lo que el modelo lee para decidir cuándo usarla.
