# Recorrido por el Código — Clase 4

**Microcredencial #2 · Clase 4 · Práctica: `practica/clase_4/`**

> **Cómo usar este documento:** es la clase entera, contada **desde el código**. No hace falta pasar antes por una presentación: cada parada abre con **la idea teórica en dos o tres frases** y enseguida muestra **dónde vive esa idea en el código** y **qué se ve en la terminal**.
>
> Abrilo de un lado de la pantalla y VS Code del otro, con `practica/clase_4/` abierta y una terminal lista. El teórico (`Clase_4_..._teorico.md`) queda como **lectura para los alumnos**, y el guion docente, como respaldo con más preguntas.
>
> Cada parada tiene la misma estructura:
> - 🎯 **Teoría**: la idea, en pocas palabras
> - 📂 **Archivo** y líneas a mirar
> - 👀 **Qué mirar** en el código
> - 🖥️ **Qué se ve** en la terminal (cuando aplica)
> - 💬 **Qué decir** en clase
> - ❓ **Pregunta** para el grupo (con respuesta)

---

## Parte 0 · Antes de entrar

### La idea que tiene que quedar

> ### **En un workflow, el orden de los pasos lo decide el desarrollador. El modelo solo trabaja en los pasos que le tocan.**

### Dónde estamos (la hoja de ruta)

- **Clase 1:** el problema. Elegimos un dolor real (el onboarding de distribuidores de Ortelana) y vimos que una aplicación inteligente tiene seis piezas: usuario, datos, modelo, herramientas, reglas y salida. Todavía sin código.
- **Clase 2:** el diseño. El journey de 11 pasos, el alcance del MVP y la decisión central de la cursada: qué hace el LLM y qué hace una regla. *El LLM interpreta, el código decide.*
- **Clase 3:** una llamada suelta. El LLM extrae, el código valida y ahí termina.
- **➜ Clase 4 (hoy):** esa llamada pasa a ser **un paso** de una secuencia, con reglas, una herramienta, puntos de control y una persona que aprueba.
- **Clase 5:** el sistema deja de responder de memoria. La normativa entra como **base de conocimiento (RAG)**, y las consultas que hoy se derivan con un texto fijo se responden citando la regla.
- **Clase 6:** cuando el que decide qué paso sigue sea **el modelo**, va a ser un **agente**.
- **Clase 7:** todo junto, de punta a punta, con guardrails, pruebas y una ficha de riesgos.
- **Clase 8:** la defensa. Mostrar el sistema, justificar las decisiones y responder preguntas con evidencia.

### Plan de la clase (40 min)

| Min | Paradas | Bloque del teórico |
|---|---|---|
| 0–5 | **Arranque:** correr `python app.py` y hacer la pregunta del caso 2 | Repaso de la Clase 3 |
| 5–15 | Paradas 1 a 5 | **Bloque 1:** de llamada aislada a workflow |
| 15–20 | Parada 6 | **Bloque 2:** cadenas y frameworks (LangChain) |
| 20–35 | Paradas 7 a 12 | **Bloque 3:** herramientas y puntos de control |
| 35–40 | Parada 13, `--manual` en vivo y consigna del Hito 1 | Cierre |

> Si el tiempo aprieta, las paradas 4, 10 y 13 se pueden saltear: el hilo de la clase no se corta.

### El mapa

```
clase_4/
├── app.py                    ← EL BOTÓN DE ENCENDIDO: corre el lote, muestra la traza y la tabla
├── datos/
│   ├── lote_prueba.json      ← QUÉ ENTRA: 9 mensajes, cada uno con el estado esperado
│   └── sistema_gestion.json  ← EL "ERP" de mentira que consulta la herramienta
├── prompts/
│   ├── extraccion_v1.txt     ← el mismo prompt de la Clase 3
│   └── redaccion_v1.txt      ← NUEVO: el prompt para redactar la respuesta
├── ortelana/
│   ├── workflow.py           ← NUEVO · EL CORAZÓN: el orden de los pasos y dónde se frena
│   ├── extractor.py          ←         igual que en la Clase 3 (ahora es UN paso)
│   ├── reglas.py             ← AMPLÍA: CUIT + documentación, categoría, deuda
│   ├── herramientas.py       ← NUEVO · la herramienta: consultar el sistema de gestión
│   ├── redactor.py           ← NUEVO · el LLM redacta la respuesta final
│   ├── llm.py                ← cambio menor: modo JSON o texto, y temperatura
│   ├── cadena_lcel.py        ← NUEVO · OPCIONAL: el paso de extracción escrito con LangChain
│   ├── contrato.py · config.py ← igual que en la Clase 3
└── tests/
    ├── test_contrato.py      ← las pruebas de la Clase 3 (siguen pasando)
    └── test_workflow.py      ← NUEVO: reglas, herramienta y un test por caso del lote
```

**Para decir al empezar:**
> "Lo de la Clase 3 **no se tiró**: `extractor.py` está igual. Lo que hicimos fue ponerlo **adentro** de algo más grande. La llamada aislada pasó a ser el paso 2 de once."

### El viaje de un mensaje (el índice del recorrido)

```
app.py ─ correr_lote()                                         ← Parada 2
   │  para cada caso de datos/lote_prueba.json                     ← Parada 1
   │
   └─▶ workflow.workflow_onboarding()                          ← Parada 3: el mapa del workflow
          │   (cada paso queda anotado en la Traza)                ← Parada 4
          │
          ├─ 1      Acuse de recibo ............ 📏 Regla
          ├─ 2-4-5  procesar_mensaje() ......... 🤖📏 lo de la Clase 3   ← Parada 5 (y su versión LangChain: Parada 6)
          │           └─ ✋ falla → REVISION_HUMANA
          ├─        Enrutar por intención ...... 📏 Regla               ← Parada 7
          │           └─ no es un alta → DERIVADO
          ├─        Alertas (VIP Oro) .......... 📏 Regla               ← Parada 10
          ├─ 6      Datos mínimos y documentos . 📏 Regla               ← Parada 8
          │           └─ ✋ faltan datos → PENDIENTE
          ├─ 7      consultar_sistema_gestion()  🔧 Herramienta         ← Parada 9
          ├─ 8      determinar_condiciones() ... 📏 Regla               ← Parada 10
          │           └─ ✋ cuenta corriente sin documentos → PENDIENTE
          ├─ 9      Armar el legajo ............ 📏 Regla               ← Parada 11
          └─ 10     ✋ esperar a una persona ..... 🙋 Humano → PENDIENTE_APROBACION

app.py ─ decidir()  (vos o el "jefe simulado")                 ← Parada 11
   └─▶ workflow.registrar_decision()  → APROBADA / RECHAZADA
          └─ 11     redactar_respuesta() ....... 🤖 LLM                 ← Parada 12
```

---

## Parte 1 · Mini-glosario de Python (lo nuevo respecto de la Clase 3)

El glosario de la Clase 3 sigue valiendo. Esto es lo que aparece por primera vez:

| Si ves… | Significa… |
|---|---|
| `class Traza:` | Una **clase**: un molde para crear objetos que guardan datos y tienen funciones propias. |
| `def __init__(self):` | Lo que se ejecuta al crear el objeto (`Traza()`). `self` es "este objeto". |
| `self.pasos = []` | Un dato que guarda el objeto. Cada `Traza` tiene su propia lista de pasos. |
| `traza.registrar(...)` | Llamar a una función del objeto (un **método**). |
| `def _terminar(traza, estado, **extra):` | `**extra` junta en un diccionario **todos los parámetros con nombre que sobren**. `_terminar(t, "X", motivo="...", datos={...})` → `extra = {"motivo": ..., "datos": ...}`. |
| `def _pedir_faltantes(...)` | El guion bajo inicial es una convención: "función interna, no la llames desde afuera". |
| `[c for c in DATOS_MINIMOS if datos[c] is None]` | Una **lista por comprensión**: "armá una lista con cada `c` que cumpla la condición". |
| `raise ValueError("...")` | Cortar el programa a propósito con un error, porque algo no debería pasar. |
| `input("¿Aprobás? [s/n]: ")` | Frenar y esperar a que la persona escriba algo en la terminal. |
| `150_000_000` | Es el número 150000000. Los `_` son solo para leerlo mejor. |

---

## Arranque (5 min) · Correr antes de explicar

Antes de abrir un solo archivo, correr:

```bash
cd practica/clase_4
python app.py
```

Ir directo al final, a la tabla:

```
#  Caso                        Esperado                Obtenido
1  Completo (B)                PENDIENTE_APROBACION    PENDIENTE_APROBACION  ✅
2  Falta un documento          PENDIENTE               PENDIENTE             ✅
3  CUIT inválido               REVISION_HUMANA         REVISION_HUMANA       ✅
4  Manipulación                PENDIENTE               PENDIENTE             ✅
5  Nuevo que factura como A    PENDIENTE_APROBACION    PENDIENTE_APROBACION  ✅
6  Cliente antiguo (A)         PENDIENTE_APROBACION    PENDIENTE_APROBACION  ✅
7  Cliente con deuda           PENDIENTE_APROBACION    PENDIENTE_APROBACION  ✅
8  Consulta normativa          DERIVADO                DERIVADO              ✅
9  Fuera de alcance            DERIVADO                DERIVADO              ✅
```

❓ **El caso 2 es el mismo mensaje de "Modas del Sur" que en la Clase 3 salía perfecto. ¿Por qué hoy queda PENDIENTE?**
> Porque en la Clase 3 la pregunta era *"¿extrajo bien los datos?"*, y sí, los extrajo bien. Hoy la pregunta es *"¿se le puede dar la cuenta corriente?"*, y para eso la normativa pide **tres documentos** y el mensaje menciona dos. **La extracción estaba bien, pero el negocio pide más.** Para descubrir eso hacen falta **más pasos** después de la extracción. Eso es un workflow, y es lo que vamos a ver.

❓ **Y con lo de la Clase 3, ¿el distribuidor recibía alguna respuesta?**
> **No.** Teníamos un JSON validado y ahí terminaba todo. Nadie revisaba los documentos, nadie consultaba si era cliente, nadie calculaba la categoría y nadie le contestaba. **Teníamos un paso del sistema, no el sistema.**

---

## Parte 2 · Las paradas

## Bloque 1 · De una llamada aislada a un workflow

### Parada 1 · Qué entra: `datos/lote_prueba.json`

🎯 **Teoría:** para probar un workflow no alcanza con ver si "anda". Hay que saber **dónde se tiene que detener** cada caso y comprobar que se detenga ahí.

📂 `datos/lote_prueba.json` (9 casos)

👀 **Qué mirar:** es el mismo formato de la Clase 3, con **un campo nuevo**:

```json
{
  "tipo": "CUIT inválido",
  "estado_esperado": "REVISION_HUMANA",     ← NUEVO: dónde DEBERÍA terminar el workflow
  "mensaje": "buenas, quiero ser distribuidor. mi cuit es veinte guion 34556789 guion 2...",
  "observar": "El flujo se detiene en el paso 5...",
  "simulacion": "{\"intencion\": \"ALTA_DISTRIBUIDOR\", \"cuit\": \"20-34556789-2\", ...}"
}
```

| Campo | Para qué sirve | ¿Va al LLM? |
|---|---|---|
| `tipo` | Nombre corto del caso | No |
| `estado_esperado` | **Dónde tendría que terminar** el workflow. Contra esto se arma la tabla | No |
| `mensaje` | Lo que escribe el distribuidor | **Sí** (solo con API key) |
| `observar` | Qué mirar en la traza | No |
| `simulacion` | La respuesta de mentira del LLM para el paso 2, cuando no hay API key | No: **ocupa su lugar** |

> 🔁 **Igual que en la Clase 3:** con API key se usa `mensaje` y la `simulacion` se ignora; sin key, la `simulacion` reemplaza a la llamada. La `simulacion` solo cubre el **paso 2** (extraer). El paso 11 (redactar) sin key usa una **plantilla fija** (Parada 12).

💬 **Qué decir:**
> "Ahora cada caso dice **qué esperamos que pase**. En la Clase 3 comparábamos a ojo contra `observar`. Hoy la tabla compara sola el estado esperado con el obtenido y pone ✅ o ❌. Esa es la **Prueba de falla** que pide el Hito 1: probar un caso que se completa y uno que se detiene, y decir **en qué paso**."

---

### Parada 2 · El botón de encendido: `app.py`

🎯 **Teoría:** el punto de entrada no sabe nada de LLMs ni de reglas. Solo recorre los casos, llama al workflow y muestra qué pasó.

📂 `app.py` — líneas 57 a 85 (`correr_lote`)

👀 **Qué mirar:** compararlo con el `app.py` de la Clase 3. **Cambió una sola línea importante**:

```python
# Clase 3
resultado = procesar_mensaje(caso["mensaje"], caso["simulacion"], version)

# Clase 4 (línea 64)
resultado = workflow_onboarding(caso["mensaje"], caso["simulacion"])
```

Y después:

```python
mostrar_traza(resultado)                                  # qué pasos recorrió (Parada 4)
if resultado["estado"] == "PENDIENTE_APROBACION":         # ¿llegó hasta la persona?
    aprobada, aprobador, motivo = decidir(...)            #   la persona decide (Parada 11)
    resultado = registrar_decision(resultado, ...)        #   y se redacta la respuesta (Parada 12)
```

💬 **Qué decir:**
> "Antes llamábamos a `procesar_mensaje`, que era **todo** el sistema. Hoy llamamos a `workflow_onboarding`, y `procesar_mensaje` quedó **adentro**, como un paso más. Fijense también que hay **dos momentos**: el workflow corre hasta la persona y se frena. Recién cuando la persona decide, sigue."

---

### Parada 3 · El mapa del workflow: `workflow.py`

🎯 **Teoría:** un **workflow** es una secuencia de pasos donde cada uno usa el resultado del anterior, con decisiones en el medio. Tres palabras para el pizarrón:
- **Pasos:** cada uno hace **una** cosa (extraer, validar, consultar, calcular, redactar).
- **Dependencias:** no se puede calcular la categoría sin la facturación, ni consultar el sistema sin un CUIT válido.
- **Decisiones:** según el resultado de un paso, el flujo sigue, toma otro camino o **se detiene**.

> **Analogía:** una línea de producción. Cada estación hace su parte y le pasa la pieza a la siguiente. Si una estación detecta una falla, la pieza sale de la línea y no sigue avanzando con el defecto.

📂 `ortelana/workflow.py` — el docstring, líneas 1 a 34

👀 **Qué mirar:** el diagrama que está escrito arriba de todo del archivo. **Es el índice del código**: cada paso del diagrama es un bloque comentado más abajo (`# ── Paso 7 · ...`).

```
Mensaje
  ├─ 1  Acuse de recibo ................................ [Regla]
  ├─ 2  Extraer intención y datos ...................... [LLM]       ┐
  ├─ 4  Validar el contrato (json.loads + Pydantic) .... [Regla]     ├ Clase 3
  ├─ 5  Validar el CUIT (dígito verificador) ........... [Regla]     ┘
  │       └─ ✋ si falla → REVISION_HUMANA
  ├─    Enrutar según la intención ..................... [Regla]
  ├─ 6  Verificar documentación (NOR-DOC) .............. [Regla]
  ├─ 7  Consultar el sistema de gestión ................ [Herramienta]
  ├─ 8  Determinar categoría, plazo y límite ........... [Regla]
  ├─ 9  Armar el legajo ................................ [Regla]
  ├─ 10 ✋ Aprobación del Jefe de Administración ......... [Humano]
  └─ 11 Redactar la respuesta .......................... [LLM]
```

💬 **Qué decir — contar los tipos de paso:**
> "¿Cuántos pasos son LLM? **Dos**: el 2 y el 11. Y son **opuestos**: el 2 pasa de lenguaje a datos (*'95 palos'* → `95000000`) y el 11 pasa de datos a lenguaje (`categoría B, 30 días` → *'Tu solicitud fue aprobada…'*). Todo lo del medio es código o una persona. **El LLM está en los bordes**: es la puerta de entrada y la de salida."

> "Los números salen del **journey de 11 pasos de la Entrega 1**. El teórico lo resume en 4 (extraer → validar → acción → redactar). Es lo mismo, con más detalle."

| Teórico (4 pasos) | En el código | Tipo |
|---|---|---|
| 1. El LLM extrae | Paso 2 | 🤖 LLM |
| 2. El código valida | Pasos 4, 5 y 6 | 📏 Regla |
| 3. Acción o consulta | Pasos 7, 8 y 9 | 🔧 Herramienta + 📏 Regla |
| — | Paso 10 | 🙋 Humano |
| 4. El LLM redacta | Paso 11 | 🤖 LLM |

❓ **¿Por qué no hacemos todo en una sola llamada? Le pasamos al LLM el mensaje y la normativa y le pedimos "decime si califica y redactá la respuesta".**
> Porque volvemos a las Clases 1 y 2. El modelo puede **calcular mal** la categoría, **obedecer** el *"apruébennos como VIP Oro"* y **no sabe** si el distribuidor debe plata (eso está en el sistema de gestión). Además, si algo sale mal, no sabemos **en qué parte** falló. Separar en pasos permite validar cada uno y detener el flujo en el lugar exacto.

> 💡 El paso 3 (identificar qué documento es cada adjunto) no está: hoy trabajamos solo con texto, así que usamos los documentos que el distribuidor **dice** que manda.

---

### Parada 4 · Ver qué pasó en cada paso: la `Traza`

🎯 **Teoría:** si un workflow falla, la pregunta es **en qué paso**. Para responderla, cada paso deja anotado qué hizo. Es el "registro de vuelo" del sistema.

📂 `ortelana/workflow.py` — líneas 58 a 69 · `app.py` líneas 22 y 33-35

👀 **Qué mirar:**

```python
class Traza:
    def __init__(self):
        self.pasos = []                                   # empieza vacía

    def registrar(self, paso, tipo, nombre, resultado):
        self.pasos.append({"paso": paso, "tipo": tipo, "nombre": nombre, "resultado": resultado})
```

Y cada paso del workflow termina con una línea así:

```python
traza.registrar("7", "Herramienta", "Consultar sistema de gestión", "distribuidor nuevo")
```

`app.py` le pone un ícono según el tipo:

```python
ICONOS = {"LLM": "🤖", "Regla": "📏", "Herramienta": "🔧", "Humano": "🙋", "LLM + Regla": "🤖📏"}
```

🖥️ **Qué se ve** (caso 1):

```
  📏 [  1] Acuse de recibo                          Recibimos tu mensaje. Te respondemos en el día.
  🤖 [  2] Extraer intención y datos                intención = ALTA_DISTRIBUIDOR
  📏 [4-5] Validar contrato y CUIT                  ✅ CUIT válido
  📏 [  —] Enrutar por intención                    ALTA_DISTRIBUIDOR → flujo de alta
  📏 [  6] Verificar documentación (NOR-DOC)        ✅ completa
  🔧 [  7] Consultar sistema de gestión             distribuidor nuevo
  📏 [  8] Determinar condiciones                   categoría B, 30 días, límite $5.000.000 (NOR-CAT-B)
  📏 [  9] Armar legajo                             0 alerta(s) para quien revisa
  🙋 [ 10] Aprobación del Jefe de Administración    ⏸ esperando decisión
```

💬 **Qué decir:**
> "Lean solo la columna de íconos: 📏🤖📏📏📏🔧📏📏🙋. Hay **un solo** 🤖 hasta acá. La mayor parte del trabajo la hace el código."

> "Los pasos sin número (`—`) no están en el journey de la Entrega 1. Son **decisiones internas** del workflow, como elegir el camino según la intención."

---

### Parada 5 · La Clase 3 convertida en un paso + el primer punto de control

🎯 **Teoría:** un **punto de validación** es el lugar donde se revisa que el dato sea correcto **antes** de seguir. Si no lo es, el flujo **se detiene**: no se avanza con datos en los que no se puede confiar.

📂 `ortelana/workflow.py` — líneas 82 a 96

👀 **Qué mirar:**

```python
r = procesar_mensaje(mensaje, simulacion)        # ← TODA la Clase 3 en una línea
if not r["ok"]:
    if r["error"] == "REGLA":                      # falló el CUIT
        traza.registrar("5", "Regla", "Validar CUIT", f"❌ {r['detalle']}")
    else:                                          # falló COMUNICACION, FORMATO o CONTRATO
        traza.registrar("2-4", ...)
    # ✋ Punto de control: no seguimos con datos que no son confiables
    return _terminar(traza, "REVISION_HUMANA", motivo=..., mensaje_original=mensaje)

datos = r["extraccion"]                          # de acá en adelante, los datos son confiables
```

🖥️ **Qué se ve** (caso 3, CUIT inválido): la traza tiene **dos líneas** y nada más.

```
  📏 [  1] Acuse de recibo                          Recibimos tu mensaje. Te respondemos en el día.
  📏 [  5] Validar CUIT                             ❌ CUIT 20-34556789-2: Dígito verificador incorrecto (esperado 6, recibido 2)

  ➜ Estado final: REVISION_HUMANA
```

💬 **Qué decir:**
> "Las 4 etapas de error de la Clase 3 (comunicación, formato, contrato, regla) siguen ahí, dentro de `procesar_mensaje`. Lo nuevo es **qué hacemos cuando fallan**: el flujo devuelve `REVISION_HUMANA` y **corta**. No consulta el sistema ni calcula nada. Ese `return` es el punto de control."

> "¿Por qué una persona y no un rechazo automático? Porque el error puede ser **del distribuidor** (escribió mal el CUIT) **o del LLM** (lo leyó mal). Una persona mira el mensaje original y decide."

> ⚠️ **Detalle que puede confundir:** en el caso 3 la traza salta del 1 al 5. El LLM **sí** se llamó (paso 2) y el contrato **sí** pasó (paso 4), pero el código solo anota el paso donde falló. Lo importante es **dónde se cortó**.

❓ **¿Cómo sabemos que de verdad no siguió? ¿Y si consultó el sistema igual y no lo anotó?**
> Hay un test que lo comprueba: `test_cuit_invalido_se_detiene_antes_de_consultar_el_sistema` revisa que los pasos 7 y 8 **no estén** en la traza. Y en el código se ve el `return`: después de un `return`, la función termina.

---

## Bloque 2 · Cadenas y frameworks

### Parada 6 · El mismo paso, con LangChain: `cadena_lcel.py`

🎯 **Teoría:** en **cada** llamada a un modelo se hacen siempre las mismas tres cosas: **armar el mensaje** (plantilla), **llamar al modelo** y **convertir la respuesta en algo usable** (parser). Un framework como **LangChain** les pone nombre y las conecta con un `|`, que se lee "y después":

```python
cadena = plantilla | modelo | parser
```

> **Analogía:** una tubería. Lo que sale de un caño entra en el siguiente; el `|` es la unión.

📂 `ortelana/cadena_lcel.py` (archivo completo) · correr `python app.py lcel`

👀 **Qué mirar:** las tres piezas, una por una.

```python
# 1) PLANTILLA: el mensaje con huecos para las variables
plantilla = ChatPromptTemplate.from_messages([
    ("system", "{instrucciones}"),                                  # ← el prompt de la Clase 3
    ("user", "...<mensaje>\n{mensaje}\n</mensaje>"),                # ← el mensaje delimitado
])

# 2) MODELO: Gemini real si hay key; si no, un modelo FALSO de LangChain que devuelve las simulaciones
modelo = ChatGoogleGenerativeAI(...)   o   FakeListChatModel(responses=...)

# 3) PARSER: saca el texto y lo valida con NUESTRO código de la Clase 3
parser = StrOutputParser() | RunnableLambda(_validar_y_aplicar_reglas)

cadena = plantilla | modelo | parser
```

💬 **Qué decir — lo más importante de este bloque:** el paso 2 de la Clase 3 **ya era una cadena**, solo que escrita a mano.

| Pieza | Clase 3 (a mano) | LangChain |
|---|---|---|
| Plantilla | `armar_mensaje_usuario()` + `cargar_prompt()` | `ChatPromptTemplate` |
| Modelo | `llamar_con_reintentos()` + `_llamar_gemini()` | `ChatGoogleGenerativeAI` |
| Parser | `json.loads()` + Pydantic + regla CUIT | `StrOutputParser()` + **la misma validación** |

🖥️ **Qué se ve** con `python app.py lcel`:

```
PASO 2 COMO CADENA LCEL:  plantilla | modelo | parser   (LangChain + modelo FALSO (simulación))
  Completo (B)                 → ALTA_DISTRIBUIDOR      OK
  CUIT inválido                → ALTA_DISTRIBUIDOR      REGLA
  ...
Mismo resultado que extractor.py: el framework cambió la plomería, no la validación.
```

❓ **Si usamos LangChain, ¿nos podemos olvidar de Pydantic y de la regla del CUIT?**
> **No.** El framework ahorra la **plomería**: armar los mensajes, llamar a la API, sacar el texto. **La validación y las reglas siguen siendo nuestras.** Miren la pieza 3: adentro llama a `validar_respuesta`, la misma función de la Clase 3.

❓ **Entonces, ¿por qué el workflow principal (`workflow.py`) no está hecho con LangChain?**
> Por el criterio del teórico: *"empezar por la opción más simple que resuelva el problema"*. Son pasos fijos y solo dos llamadas al LLM, y un framework no simplificaba nada. Conviene sumarlo cuando hay **muchos pasos encadenados que se repiten**, cuando la estructura se **reutiliza** en varios lugares o cuando un equipo lo va a **mantener en el tiempo**. Para el Hito 1, **Python directo vale**.

> 💡 **Dato de color:** el prompt entra como **valor** de `{instrucciones}` y no escrito en la plantilla, porque LangChain usa las llaves `{ }` para marcar variables, y el prompt tiene llaves en los ejemplos de JSON. Es un ejemplo de algo que el framework **complica**.

| | LangChain (hoy) | LangGraph (Clase 6) |
|---|---|---|
| Forma | Cadena: A → B → C | Grafo: con ciclos y bifurcaciones |
| ¿Quién decide el camino? | El **desarrollador**, de antemano | El **modelo**, en tiempo real |

---

## Bloque 3 · Herramientas, reglas y puntos de control

### Parada 7 · El modelo pone la etiqueta, el código elige el camino: el enrutamiento

🎯 **Teoría:** según la intención, el flujo toma caminos distintos. Pero **el modelo no elige el camino**: solo **clasifica**. Qué hacer con cada clasificación lo escribió el desarrollador. Es la **Matriz de Intenciones** de la Clase 2 convertida en código.

📂 `ortelana/workflow.py` — líneas 45 a 53 (`RESPUESTAS_FIJAS`) y 98 a 103

👀 **Qué mirar:**

```python
RESPUESTAS_FIJAS = {                                     # la Matriz de Intenciones, en un diccionario
    "CONSULTA_NORMATIVA": "Gracias por tu consulta. La derivamos al área comercial...",
    "FUERA_DE_ALCANCE":   "Este canal es para altas de distribuidores. Para pedidos, stock...",
    "CONSULTA_ESTADO":    "Derivamos tu consulta a Administración...",
    "COMPLETAR_DOCUMENTACION": "Recibimos la documentación...",
}

if datos["intencion"] != "ALTA_DISTRIBUIDOR":            # ← el CÓDIGO decide el camino
    respuesta = RESPUESTAS_FIJAS[datos["intencion"]]
    return _terminar(traza, "DERIVADO", ...)
```

🖥️ **Qué se ve** (caso 9):

```
  🤖 [  2] Extraer intención y datos                intención = FUERA_DE_ALCANCE
  📏 [  —] Enrutar por intención                    FUERA_DE_ALCANCE → respuesta fija
  ➜ Estado final: DERIVADO
  ✉️  Respuesta al distribuidor [RESPUESTA FIJA]:
     Este canal es para altas de distribuidores. Para pedidos, stock o reclamos, escribinos a ventas@ortelana.com.ar.
```

❓ **Si según la intención el flujo toma caminos distintos, ¿no es que "decide el modelo"? ¿No es un agente?**
> **No, y es una distinción fina.** El modelo **pone una etiqueta** (paso 2). El `if` que está en el código tiene **el mapa** de qué camino corresponde a cada etiqueta. El modelo nunca ve ese mapa ni lo puede cambiar. Si mañana queremos que `CONSULTA_ESTADO` siga otro camino, cambiamos el código, no el prompt.

❓ **Las 5 intenciones están en el prompt, en el contrato Pydantic y ahora en este diccionario. ¿Qué pasa si agrego una sexta solo en el prompt?**
> La frena Pydantic (Parada 9 de la Clase 3): no está en el `Literal`, así que es error de CONTRATO y va a `REVISION_HUMANA`. Para agregar una intención hay que tocar **los tres lugares**: prompt, contrato y enrutamiento. Por eso se deriva todo de **un** diseño, la Matriz.

> 🔗 Los casos 8 y 9 hoy reciben un texto fijo. En la **Clase 5**, `CONSULTA_NORMATIVA` se va a responder con **RAG**, citando la normativa real.

---

### Parada 8 · Detener no es rechazar: datos mínimos y documentación (NOR-DOC)

🎯 **Teoría:** "detener el flujo" no siempre es "rechazar". A veces es **pedir lo que falta**. El estado `PENDIENTE` significa: *"no puedo seguir, pero te digo qué necesito"*.

📂 `ortelana/workflow.py` líneas 112 a 122 y 162 a 171 · `ortelana/reglas.py` líneas 59 a 61

👀 **Qué mirar — dos chequeos distintos:**

```python
DATOS_MINIMOS = ("razon_social", "cuit", "facturacion_anual")

datos_faltantes = [c for c in DATOS_MINIMOS if datos[c] is None]          # ¿qué datos faltan?
docs_faltantes  = verificar_documentacion(datos["documentos_mencionados"]) # ¿qué documentos faltan?

if datos_faltantes:                                  # sin CUIT no puedo consultar el sistema,
    return _pedir_faltantes(...)                     # sin facturación no puedo calcular la categoría
```

Y la regla NOR-DOC es una línea:

```python
def verificar_documentacion(documentos_mencionados):
    return [doc for doc in DOCUMENTOS_OBLIGATORIOS if doc not in documentos_mencionados]
    #       "dame los obligatorios que NO estén en lo que mencionó"
```

💬 **Qué decir — las dependencias, en vivo:**
> "Acá se ve la palabra **dependencia** de la Parada 3. Sin CUIT, el paso 7 no tiene qué buscar. Sin facturación, el paso 8 no tiene con qué calcular. Por eso este chequeo va **antes**."

> "Fijense lo que hace `_pedir_faltantes`: **no rechaza**. Arma un pedido con lo que falta y lo redacta (paso 11). Rechazar a alguien porque se olvidó un papel haría perder clientes."

🖥️ **Qué se ve** (caso 4, manipulación):

```
  📏 [  6] Verificar documentación (NOR-DOC)        faltan: CONSTANCIA_ARCA, HABILITACION, INGRESOS_BRUTOS ...
  📏 [  —] Datos mínimos                            ✋ faltan: cuit, facturacion_anual
  🤖 [ 11] Redactar pedido de faltantes             PLANTILLA (sin API key)
  ➜ Estado final: PENDIENTE
```

❓ **¿Por qué en el paso 6 se *verifican* los documentos pero no se *exigen* hasta después del paso 8?**
> Porque NOR-DOC los exige **solo para cuenta corriente**, y recién en el paso 8 sabemos si le corresponde cuenta corriente. Un cliente con deuda (caso 7) opera al contado, así que no se le piden documentos. **El orden de los pasos también es una decisión de diseño.** Lo vemos en la Parada 10.

---

### Parada 9 · La herramienta: `herramientas.py` y `sistema_gestion.json`

🎯 **Teoría:** hasta ahora el modelo solo **habla** (genera texto). Una **herramienta (tool)** es una **función de código que el sistema ejecuta para hacer algo real**: consultar una base de datos, llamar a otra API, hacer un cálculo. Con herramientas, el sistema **hace**.

📂 `ortelana/herramientas.py` (archivo completo) · `datos/sistema_gestion.json` · `workflow.py` líneas 124 a 128

👀 **Qué mirar — la herramienta:**

```python
def consultar_sistema_gestion(cuit: str) -> dict:
    """
    Busca un distribuidor por CUIT en el sistema de gestión de Ortelana.
    Tipo: SENSOR (solo lee, no modifica nada) → riesgo bajo.
    """
    base = json.loads(ARCHIVO_SISTEMA_GESTION.read_text(...))   # en la vida real: una base de datos o el ERP
    registro = base.get(cuit)
    if registro is None:
        return {"es_cliente": False, "antiguedad_meses": 0, "dias_deuda_vencida": 0}   # no está → es nuevo
    return {"es_cliente": True, **registro}
```

👀 **Qué mirar — la "base de datos":**

```json
{
  "30-71402587-9": { "razon_social": "Grupo Norte Moda SA",     "antiguedad_meses": 18, "dias_deuda_vencida": 0 },
  "30-71122334-3": { "razon_social": "Confecciones Pampa SRL",  "antiguedad_meses": 30, "dias_deuda_vencida": 45 },
  ...
}
```

👀 **Qué mirar — dónde se llama** (línea 125):

```python
# ── Paso 7 · Sistema de gestión [Herramienta] ──
cliente = consultar_sistema_gestion(datos["cuit"])     # ← un paso FIJO: siempre acá, siempre en este orden
```

💬 **Qué decir — por qué hace falta:**
> "Hay datos que **el distribuidor no dice y el LLM no puede saber**: si ya es cliente, desde cuándo y si debe plata. **La base de datos es la autoridad.** Si le preguntáramos al LLM, lo inventaría."

🖥️ **La prueba de que la herramienta cambia la decisión — comparar los casos 5 y 6:**

| | Caso 5 · Distribuidora Andina | Caso 6 · Grupo Norte Moda |
|---|---|---|
| Facturación (del mensaje) | $450M | $400M |
| Paso 7 (herramienta) | `distribuidor nuevo` | `cliente existente, 18 meses` |
| Paso 8 (resultado) | **Categoría B**, 30 días (NOR-NUEVO) | **Categoría A**, 60 días |

> "Andina factura **más** y le toca **menos**. ¿Por qué? Porque es nueva. **La diferencia no está en el mensaje: la pone la herramienta.**"

💬 **Sensor vs. actuador (adelanto de la Clase 6):**

| Tipo | Qué hace | Riesgo | Ejemplo |
|---|---|---|---|
| **Sensor** | Solo **lee** | Bajo | `consultar_sistema_gestion` |
| **Actuador** | **Escribe** o tiene un efecto real | Alto | Dar de alta la cuenta corriente |

> "En esta práctica **no hay ningún actuador automático**. El alta la hace una persona. Es la Matriz de la Clase 2: lo que escribe o compromete plata lleva más control."

❓ **¿Qué diferencia hay entre una herramienta y una función común?**
> En el código, **ninguna**: es una función. Se le dice "herramienta" por **el rol que cumple**: le da al sistema la capacidad de hacer algo en el mundo real. En la Clase 6 la diferencia se va a notar, porque el **docstring** pasa a ser lo que el modelo lee para decidir cuándo usarla.

❓ **El teórico usa de ejemplo `consultar_stock_tela`. ¿Por qué acá no está?**
> Porque en nuestro MVP **el stock quedó fuera de alcance** (Entrega 1, el caso 9 lo deriva). La herramienta que pide **nuestro journey** es la del paso 7. Es el mismo concepto; cambia **qué** consulta.

---

### Parada 10 · Lo que decide el código: `determinar_condiciones()` y las alertas

🎯 **Teoría:** la decisión con **consecuencia financiera** (categoría, plazo, límite de crédito) es una cuenta con reglas fijas: si entra X, siempre sale Y. **Por eso la hace el código, nunca el LLM.** Es la idea de la Clase 2 (*el LLM interpreta, el código decide*) llevada al paso más delicado.

📂 `ortelana/reglas.py` — líneas 17 a 32 (constantes) y 75 a 138 · `workflow.py` líneas 105 a 110 y 130 a 143

👀 **Qué mirar — la normativa como constantes** (un solo lugar para cambiarla):

```python
TOPE_CATEGORIA_C = 80_000_000      # NOR-CAT-C: hasta $80M
TOPE_CATEGORIA_B = 300_000_000     # NOR-CAT-B: hasta $300M
ANTIGUEDAD_MINIMA_A = 12           # NOR-CAT-A: al menos 12 meses como cliente
DIAS_DEUDA_MAXIMOS = 30            # NOR-DEUDA: más de 30 días → solo contado

CONDICIONES_POR_CATEGORIA = {
    "A": {"plazo_maximo_dias": 60, "limite_credito": 15_000_000, ...},
    "B": {"plazo_maximo_dias": 30, "limite_credito": 5_000_000, ...},
    "C": {"plazo_maximo_dias": 0,  "limite_credito": 0, ...},
}
```

👀 **Qué mirar — la decisión, leída como un árbol:**

```python
if facturacion_anual <= TOPE_CATEGORIA_C:          categoria = "C"
elif facturacion_anual <= TOPE_CATEGORIA_B:        categoria = "B"
elif not cliente["es_cliente"]:                    categoria = "B"   # NOR-NUEVO  ← usa la herramienta
elif cliente["antiguedad_meses"] < 12:             categoria = "B"   #            ← usa la herramienta
else:                                              categoria = "A"

if cliente["dias_deuda_vencida"] > 30:             # NOR-DEUDA                 ← usa la herramienta
    plazo_maximo, limite = 0, 0                    #   solo contado
```

💬 **Qué decir:**
> "Fijense cuántas veces aparece `cliente[...]`: es lo que devolvió la herramienta. **El paso 8 depende del paso 7.** Sin la herramienta, esta función no podría decidir."

> "Cada regla deja anotado su código (`NOR-CAT-B`, `NOR-NUEVO`, `NOR-DEUDA`). Así el legajo y la respuesta pueden **citar en qué se basa** la decisión. Es auditable."

🖥️ **Qué se ve** (caso 7, cliente con deuda):

```
  📏 [  6] Verificar documentación (NOR-DOC)        faltan: CONSTANCIA_ARCA, HABILITACION, INGRESOS_BRUTOS ...
  🔧 [  7] Consultar sistema de gestión             cliente existente, 30 meses, deuda vencida 45 días
  📏 [  8] Determinar condiciones                   categoría B, 0 días, límite $0 (NOR-CAT-B, NOR-DEUDA)
  📏 [  9] Armar legajo                             ...
```

> "No mandó **ningún** documento y aun así llega al legajo. ¿Por qué? Porque NOR-DEUDA lo deja **solo al contado**, y para contado no hace falta documentación. Ese es el `if` de las líneas 140-143: los documentos se exigen **solo si hay cuenta corriente**."

👀 **Qué mirar — las alertas** (`workflow.py` líneas 105-110 y 136-138):

```python
categoria_pedida = normalizar_categoria(datos["categoria_solicitada"])   # "categoría A" → "A" · "VIP Oro" → None
if datos["categoria_solicitada"] and categoria_pedida is None:
    alertas.append("Pidió una categoría inexistente ('VIP Oro'): posible intento de saltear la validación...")

if categoria_pedida and categoria_pedida != condiciones["categoria"]:
    alertas.append("Pidió categoría A; según la normativa le corresponde B.")
```

💬 **Qué decir:**
> "¿Se acuerdan del VIP Oro de la Clase 3? El LLM lo **copió** en `categoria_solicitada`. Hoy, `normalizar_categoria` se fija si es A, B o C, y como no es ninguna, queda como **alerta**. Las alertas **no frenan** el flujo: son información para la persona que aprueba."

❓ **El LLM extrajo "categoría A" del mensaje de Andina. ¿Le damos la A?**
> **No.** Lo que pide el distribuidor es un **dato**, no una orden. La categoría la calcula `determinar_condiciones` con la normativa. Lo pedido solo sirve para avisarle a la persona que hay una diferencia.

---

### Parada 11 · El punto de control humano: legajo, `PENDIENTE_APROBACION` y `--manual`

🎯 **Teoría:** un **punto de intervención humana** es un lugar donde el flujo **se pausa y espera a una persona**, porque el riesgo es demasiado alto para seguir solo. En Ortelana lo exige la normativa (**NOR-APROB**): ninguna cuenta corriente se aprueba sin el Jefe de Administración. **El sistema recomienda; la persona decide.**

> **Frase ancla:** *"Un workflow sin puntos de control es una llamada larga al LLM."*

📂 `ortelana/workflow.py` líneas 145 a 159 y 174 a 199 · `app.py` líneas 38 a 54

👀 **Qué mirar — el workflow termina antes de aprobar:**

```python
# ── Paso 9 · Legajo ──
legajo = {"razon_social": ..., "cliente": cliente, "recomendacion": condiciones,
          "alertas": alertas, "mensaje_original": mensaje}

# ── Paso 10 · ✋ Aprobación humana ──
traza.registrar("10", "Humano", "Aprobación del Jefe de Administración", "⏸ esperando decisión")
return _terminar(traza, "PENDIENTE_APROBACION", legajo=legajo)     # ← acá TERMINA workflow_onboarding
```

👀 **Qué mirar — aprobar es otra función, y necesita a alguien:**

```python
def registrar_decision(resultado, aprobada, aprobador, motivo=None):
    if resultado["estado"] != "PENDIENTE_APROBACION":
        raise ValueError("No hay nada que aprobar...")      # no se puede aprobar un CUIT inválido
    if not aprobada and not motivo:
        raise ValueError("Un rechazo necesita un motivo...") # hay que explicarle al distribuidor por qué
    ...
```

💬 **Qué decir:**
> "`workflow_onboarding` **no tiene ningún camino** que termine en `APROBADA`. Búsquenlo: no está. Para aprobar hay que llamar a **otra** función, `registrar_decision`, y pasarle **quién** aprueba. Hay un test que lo garantiza: `test_ningun_alta_se_aprueba_sin_una_persona`."

🖥️ **En vivo — vos sos el Jefe de Administración:**

```bash
python app.py --manual
```

```
  📋 LEGAJO — Distribuidora Andina SA (30-68912345-3)
     Recomendación: categoría B, 30 días, límite $5.000.000  [NOR-CAT-B, NOR-NUEVO]
     · Factura como categoría A, pero es distribuidor nuevo: ingresa en B (NOR-NUEVO).
     · Pidió 60 días; el máximo para su categoría es 30.
     ⚠️  Pidió categoría A; según la normativa le corresponde B.
     ¿Aprobás? [s/n]:
```

> 💡 Aprobar uno y **rechazar otro** escribiendo un motivo. Se ve cómo cambia la respuesta redactada.

> ⚠️ Sin `--manual`, `app.py` aprueba todo con un "Jefe de Administración (simulado)" para no frenar la demo. Por eso la tabla aclara: *"el estado es el del workflow, antes de la decisión humana"*.

❓ **¿En qué pasos del onboarding interviene una persona? (recoger 2 o 3 respuestas antes de dar la propia)**
> En **dos** lugares, por motivos distintos:
> 1. **Cuando algo falló** (`REVISION_HUMANA`): CUIT inválido o extracción rota. Puede ser un error del distribuidor **o del LLM**.
> 2. **Siempre, antes de aprobar** (`PENDIENTE_APROBACION`): lo exige NOR-APROB, no importa qué tan bien funcione el sistema.

**Los estados de salida, todos juntos:**

| Estado | Cuándo | ¿Qué pasa después? | Casos |
|---|---|---|---|
| `REVISION_HUMANA` | CUIT inválido o extracción rota | Una persona mira el mensaje original | 3 |
| `DERIVADO` | No es un alta | Respuesta fija según la Matriz | 8, 9 |
| `PENDIENTE` | Faltan datos o documentos | **Se le piden** al distribuidor (no se rechaza) | 2, 4 |
| `PENDIENTE_APROBACION` | Legajo completo | Espera al Jefe de Administración | 1, 5, 6, 7 |
| `APROBADA` / `RECHAZADA` | La persona decidió | Se redacta y envía la respuesta | (después del paso 10) |

---

### Parada 12 · El LLM vuelve al final: `redactor.py`

🎯 **Teoría:** el paso 11 es el **camino inverso** al paso 2. El 2 pasa de lenguaje a datos; el 11, de una **decisión ya tomada** a lenguaje. El LLM **comunica** la decisión, **no la toma**.

📂 `ortelana/redactor.py` · `prompts/redaccion_v1.txt` · `ortelana/llm.py` líneas 36-48 · `workflow.py` líneas 190-194

👀 **Qué mirar — qué recibe el LLM:**

```python
decision = {"tipo": "APROBADA", "razon_social": ..., **legajo["recomendacion"]}
decision.pop("observaciones")    # ← las notas internas NO le llegan al LLM
```

```python
usuario = f"<decision>\n{json.dumps(decision, ...)}\n</decision>"     # le llega SOLO un JSON
texto = llamar_con_reintentos(system, usuario, ..., json_mode=False, temperatura=0.3)
```

👀 **Qué mirar — el prompt** (`redaccion_v1.txt`):

```
1. Comunicá la decisión, no la cambies. No agregues beneficios, plazos, montos ni condiciones...
2. Usá exactamente los números del JSON...
3. Si el JSON trae "reglas_aplicadas", mencioná los códigos (por ejemplo NOR-CAT-B)...
```

👀 **Qué mirar — el respaldo:**

```python
if proveedor is None:
    return {"texto": plantilla_fija(decision), "origen": "PLANTILLA (sin API key)"}
try:
    texto = llamar_con_reintentos(...)
except (urllib.error.URLError, ...):
    return {"texto": plantilla_fija(decision), "origen": "PLANTILLA (falló la API: ...)"}
```

💬 **Qué decir — tres decisiones de diseño:**

| Decisión | Por qué |
|---|---|
| Le llega **solo un JSON** con la decisión | No puede "decidir" otra cosa: no tiene el mensaje original ni la normativa. Y como `observaciones` se saca, no puede filtrar notas internas al distribuidor |
| **Temperatura 0.3** (en la extracción era 0) | En la extracción queremos el JSON más estable posible. Acá queremos un texto que suene natural; los números no cambian porque vienen fijos en el JSON |
| **Plantilla fija** si no hay key o falla la API | Para el paso 11 la decisión **ya está tomada**. Sería absurdo que un error al redactar frenara una aprobación |

> "Por eso `llm.py` tiene dos parámetros nuevos, `json_mode` y `temperatura`: hoy el modelo se usa **dos veces y para cosas distintas**."

🖥️ **Qué se ve** (sin API key):

```
  ✉️  Respuesta al distribuidor [PLANTILLA (sin API key)]:
     Hola, Distribuidora Andina SA. Tu solicitud fue aprobada en categoría B, con cuenta corriente
     a 30 días con un límite de $5.000.000. Esta decisión se basa en la normativa comercial (NOR-CAT-B, NOR-NUEVO).
```

❓ **¿El paso 11 no es peligroso? El LLM podría inventar condiciones.**
> Puede pasar, y por eso tiene **tres capas**: solo recibe la decisión, el prompt le prohíbe cambiarla y, si falla, hay plantilla. Igual no es 100% seguro: **controlar la salida del LLM (guardrails) es tema de la Clase 7.**

---

### Parada 13 · Las pruebas: `tests/test_workflow.py`

🎯 **Teoría:** en un workflow, lo que más importa probar no es "que ande" sino **que se detenga donde tiene que detenerse** y **que nunca haga lo que no debe**.

📂 `tests/test_workflow.py` — líneas 96 a 144

👀 **Qué mirar — los nombres de los tests cuentan la teoría:**

```python
def test_lote_termina_en_el_estado_esperado(caso):                    # cada caso, donde tiene que terminar
def test_cuit_invalido_se_detiene_antes_de_consultar_el_sistema():    # punto de control (Parada 5)
def test_manipulacion_no_aprueba_y_deja_alerta():                     # VIP Oro (Parada 10)
def test_ningun_alta_se_aprueba_sin_una_persona():                    # NOR-APROB (Parada 11)
def test_rechazo_necesita_motivo():                                   # (Parada 11)
def test_no_se_puede_aprobar_lo_que_no_esta_pendiente_de_aprobacion():
```

El más importante de todos:

```python
def test_ningun_alta_se_aprueba_sin_una_persona():
    """NOR-APROB: el workflow nunca termina en APROBADA por sí solo."""
    for caso in LOTE:
        assert workflow_onboarding(caso["mensaje"], caso["simulacion"])["estado"] != "APROBADA"
```

🖥️ **Qué se ve:**

```bash
python -m pytest
```

```
..................................................                       [100%]
50 passed in 0.17s
```

💬 **Qué decir:**
> "Si mañana alguien 'optimiza' el workflow y agrega un atajo que aprueba solo, este test se pone rojo. **Las reglas importantes no se confían a la memoria del equipo: se escriben como test.**"

---

## Parte 3 · Leer la terminal

### 3.1 · Cada caso

```
==============================================================================
Caso 5 — Nuevo que factura como A
==============================================================================
  Mensaje: Buen día, les escribe Distribuidora Andina SA ...      ← lo que escribió el distribuidor
  Qué observar: Factura como A, pero es nuevo: entra en B ...      ← la pista del lote

  📏 [  1] Acuse de recibo ...                                     ← la TRAZA: un renglón por paso
  ...
  🙋 [ 10] Aprobación del Jefe de Administración    ⏸ esperando decisión

  📋 LEGAJO — ...                                                  ← lo que ve la persona (paso 10)
     Recomendación: categoría B, 30 días ...
     · ...                                                         ← observaciones (internas)
     ⚠️  ...                                                       ← alertas

  🙋 [ 10] ... ✅ aprobada por Jefe de Administración (simulado)   ← la decisión
  🤖 [ 11] Redactar respuesta                       PLANTILLA (sin API key)

  ➜ Estado final: APROBADA
  ✉️  Respuesta al distribuidor [PLANTILLA (sin API key)]:         ← entre corchetes: quién la escribió
```

| Ícono | Tipo de paso | Quién lo hace |
|---|---|---|
| 🤖 | LLM | El modelo (pasos 2 y 11) |
| 📏 | Regla | El código |
| 🔧 | Herramienta | El código, consultando un sistema externo |
| 🙋 | Humano | Una persona |
| ✋ | Punto de control | El flujo se detiene acá |
| ⏸ | En pausa | Esperando a la persona |

**El origen de la respuesta** (entre corchetes después de ✉️):

| Dice… | Significa… |
|---|---|
| `RESPUESTA FIJA` | Un texto de `RESPUESTAS_FIJAS` (caso derivado) |
| `PLANTILLA (sin API key)` | No hay key: se usó `plantilla_fija()` |
| `PLANTILLA (falló la API: ...)` | Había key, pero la llamada falló |
| `LLM (gemini)` | La redactó el modelo |

### 3.2 · La tabla del lote

Compara el estado **esperado** (del lote) con el **obtenido** (del workflow). Es el estado **antes** de la decisión humana: por eso los casos 1, 5, 6 y 7 dicen `PENDIENTE_APROBACION`, aunque más arriba se vea `APROBADA`.

### 3.3 · Con API key, ¿qué cambia?

- La extracción la hace el modelo, así que **algún caso puede dar ❌** en la tabla. El más probable es el **4 (manipulación)**: si el modelo lo clasifica como `FUERA_DE_ALCANCE`, termina en `DERIVADO` en vez de `PENDIENTE`. **Y aun así no se aprueba nada.** Ese es el punto: el diseño del workflow protege aunque el modelo se equivoque.
- Las respuestas dicen `LLM (gemini)` y el texto cambia entre corridas (temperatura 0.3). **Los números no**: vienen del JSON.

---

## Parte 4 · Para experimentar en vivo

Cambios chicos para mostrar que **cada archivo responde una pregunta**:

| Quiero ver… | Toco… | Qué pasa |
|---|---|---|
| Que la herramienta decide | En `sistema_gestion.json`, agregar el CUIT de Andina (`30-68912345-3`) con `"antiguedad_meses": 15` | El caso 5 pasa a **categoría A**, 60 días |
| Que el orden de los pasos importa | En `sistema_gestion.json`, bajarle la deuda a Confecciones Pampa a `10` días | El caso 7 ahora tiene cuenta corriente… y como no mandó documentos, pasa a **`PENDIENTE`** (la tabla da ❌ porque el esperado era otro: está bien) |
| Que la normativa vive en un solo lugar | En `reglas.py`, cambiar `TOPE_CATEGORIA_B` a `100_000_000` | El caso 1 (150M, nuevo) sigue en B por NOR-NUEVO; probar qué pasa con el 7 |
| El punto de control de formato | En `lote_prueba.json`, agregar `"Claro! "` al principio de una `simulacion` | Ese caso va a **`REVISION_HUMANA`** con traza `[2-4]` |
| Una intención nueva sin tocar el código | Cambiar en una `simulacion` la intención a `"CONSULTA_ESTADO"` | Termina en `DERIVADO` con la respuesta fija de Administración |
| Que no se aprueba solo | `python app.py --manual` y rechazar con un motivo | `RECHAZADA` y la respuesta cita el motivo |

> ⚠️ Después de experimentar, volver los archivos a como estaban: `git checkout -- datos/ ortelana/` (funciona solo si la práctica ya está commiteada; si no, deshacer con Ctrl+Z en el editor) y confirmar con `python -m pytest` que siguen pasando las 50 pruebas.

---

## Parte 5 · Cierre: workflow vs. agente

Para cerrar, volver a la idea del principio con la tabla más importante de la clase:

| | Workflow (hoy) | Agente (Clase 6) |
|---|---|---|
| ¿Quién decide qué paso sigue? | **El desarrollador**, en `workflow.py` | **El modelo**, en tiempo real |
| ¿Quién decide cuándo usar la herramienta? | El código: siempre en el paso 7 | El modelo, leyendo el docstring |
| Previsibilidad | Alta: siempre el mismo camino | Menor: puede elegir distinto |
| Cuándo conviene | Procesos conocidos y regulados | Consultas abiertas e impredecibles |

> **Analogía:** el workflow es una **receta** (paso 1, paso 2, paso 3). El agente es un **cocinero con la heladera llena**: mira qué le pidieron y decide qué usar.

❓ **El onboarding de Ortelana, ¿conviene hacerlo con un workflow o con un agente?**
> Con un **workflow**. El proceso está definido por la normativa: siempre hay que validar el CUIT, verificar documentos, consultar el sistema y calcular la categoría, en ese orden. Además tiene consecuencia financiera: queremos que sea **predecible y auditable**. El agente conviene para cosas abiertas, como una consulta libre que puede necesitar distintas fuentes.

### Consigna del Hito 1 (dejar proyectada)

Cada grupo, **sobre su caso propio**:

1. Un workflow de **al menos 3 pasos** en secuencia (pueden reusar el prompt de la Entrega 2).
2. **Al menos una validación en código** con lógica real del dominio. No vale `if True`.
3. **Al menos un punto de control** donde el flujo se detiene antes de seguir.
4. Probarlo con **un caso que se completa** y **uno que se detiene**, y documentar **en qué paso** se detuvo (la traza sirve para eso).
5. Actualizar el **diagrama** de la Clase 2 con los pasos, las decisiones y qué es LLM y qué es regla.

> Ejemplo resuelto (nivel "Destacado"): `practica/clase_4/docs/ortelana_entrega_3_informe.md`, Parte A. Las Partes B y C están marcadas como pendientes: se completan en las Clases 5 y 6, igual que el informe de cada grupo. En la misma carpeta están los informes de las Entregas 1 y 2. Si el grupo tiene bajo dominio técnico, que parta de `workflow.py` y lo adapte: se evalúa el **diseño del flujo y los puntos de control**, no la sintaxis.

**Lo que viene:**
- Hoy las consultas normativas se derivan con un texto fijo → **Clase 5:** RAG con la normativa real.
- Hoy el desarrollador decide el camino → **Clase 6:** el modelo decide (agentes).

---

## Resumen: cada concepto, en qué archivo

| Concepto de la teoría | Dónde se ve |
|---|---|
| Workflow: pasos + dependencias + decisiones | El docstring y el cuerpo de `workflow_onboarding()` en `workflow.py` |
| El LLM en los bordes (entrada y salida) | Paso 2 (`procesar_mensaje`) y paso 11 (`redactar_respuesta`) |
| La llamada aislada pasa a ser un paso | `procesar_mensaje()` adentro de `workflow_onboarding()` |
| Saber en qué paso falló | La clase `Traza` y `mostrar_traza()` en `app.py` |
| Punto de validación | El `return ... REVISION_HUMANA` después de `procesar_mensaje` |
| Cadena `plantilla \| modelo \| parser` | `cadena_lcel.py` + `python app.py lcel` |
| El framework ahorra plomería, no validación | El parser de `cadena_lcel.py` llama a `validar_respuesta()` |
| El modelo clasifica, el código enruta | `RESPUESTAS_FIJAS` + el `if` de enrutamiento |
| Detener ≠ rechazar | `_pedir_faltantes()` y el estado `PENDIENTE` |
| Herramienta (tool), tipo sensor | `consultar_sistema_gestion()` en `herramientas.py` |
| La herramienta cambia la decisión | Casos 5 vs. 6 |
| Decisión financiera = código determinista | `determinar_condiciones()` en `reglas.py` |
| El orden de los pasos es una decisión de diseño | NOR-DOC verificada en el paso 6 y exigida después del 8 (caso 7) |
| Punto de intervención humana | `PENDIENTE_APROBACION` + `registrar_decision()` + `--manual` |
| El LLM comunica, no decide | `redactor.py` + `prompts/redaccion_v1.txt` |
| Respaldo si falla el LLM | `plantilla_fija()` en `redactor.py` |
| Probar que nunca haga lo que no debe | `test_ningun_alta_se_aprueba_sin_una_persona` |
