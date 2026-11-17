# Clase 4 — Workflow de onboarding de Ortelana

El componente de la [Clase 3](../clase_3/) extraía los datos de **un mensaje suelto**. Hoy lo convertimos en un **workflow**: la secuencia completa del journey de la [Entrega 1](docs/ortelana_entrega_1_informe.md), con reglas de negocio, una herramienta, puntos de control y la redacción de la respuesta.

```
Mensaje
  ├─ 1  Acuse ......................................... 📏 Regla
  ├─ 2  Extraer intención y datos ..................... 🤖 LLM          ┐
  ├─ 4  Validar contrato (json.loads + Pydantic) ...... 📏 Regla        ├ Clase 3
  ├─ 5  Validar CUIT .................................. 📏 Regla        ┘
  │      └─ ✋ falla → REVISION_HUMANA
  ├─    Enrutar por intención ......................... 📏 Regla
  │      └─ no es un alta → DERIVADO (respuesta fija)
  ├─ 6  Documentación obligatoria (NOR-DOC) ........... 📏 Regla
  ├─ 7  Consultar sistema de gestión .................. 🔧 Herramienta
  ├─ 8  Categoría, plazo y límite (NOR-CAT/NUEVO/DEUDA) 📏 Regla
  │      └─ ✋ faltan datos o documentos → PENDIENTE
  ├─ 9  Armar legajo .................................. 📏 Regla
  ├─ 10 ✋ Aprobación del Jefe de Administración ........ 🙋 Humano       → PENDIENTE_APROBACION
  └─ 11 Redactar la respuesta ......................... 🤖 LLM          → APROBADA / RECHAZADA
```

**La idea de la clase en una línea:** el orden de los pasos lo fija el **desarrollador**. El modelo interviene solo en los pasos 2 y 11, y nunca decide qué paso sigue. Cuando eso lo decida el modelo, va a ser un **agente** (Clase 6).

## Cómo correrlo

Desde esta carpeta (`clase_4/`):

```bash
pip install -r requirements.txt
cp .env.example .env      # completar GEMINI_API_KEY (gratis en https://aistudio.google.com)

python app.py             # corre los 9 casos; el Jefe de Administración (simulado) aprueba todo
python app.py --manual    # vos hacés de Jefe de Administración: aprobás o rechazás cada legajo
python app.py lcel        # el paso 2 escrito como cadena de LangChain (plantilla | modelo | parser)
python -m pytest          # 50 pruebas de reglas, herramienta y workflow (no usan la API)
```

Sin API key corre en **modo simulación**: la extracción usa las respuestas de ejemplo del lote y la redacción usa una plantilla fija.

## Estructura

```
clase_4/
├── app.py                    ← corre el lote, muestra la traza de cada caso y la tabla final
├── ortelana/
│   ├── config.py             ← .env y proveedor de LLM                          (igual que Clase 3)
│   ├── contrato.py           ← contrato Pydantic de la extracción              (igual que Clase 3)
│   ├── extractor.py          ← pasos 2, 4 y 5                                   (igual que Clase 3)
│   ├── llm.py                ← llamada a la API, ahora con modo JSON o texto    (cambio menor)
│   ├── reglas.py             ← CUIT + NOR-DOC, NOR-CAT-A/B/C, NOR-NUEVO, NOR-DEUDA  (amplía)
│   ├── herramientas.py       ← paso 7: consultar el sistema de gestión          (nuevo)
│   ├── redactor.py           ← paso 11: el LLM redacta, con plantilla de respaldo  (nuevo)
│   ├── workflow.py           ← la secuencia de pasos y los puntos de control    (nuevo)
│   └── cadena_lcel.py        ← OPCIONAL: el paso 2 como cadena de LangChain     (nuevo)
├── prompts/
│   ├── extraccion_v1.txt     ← el mismo prompt de la Clase 3
│   └── redaccion_v1.txt      ← prompt del paso 11: "comunicá la decisión, no la cambies"
├── datos/
│   ├── lote_prueba.json      ← 9 casos, cada uno con su estado esperado
│   └── sistema_gestion.json  ← el "ERP" simulado que consulta la herramienta
├── tests/
│   ├── test_contrato.py      ← las pruebas de la Clase 3 (siguen pasando)
│   └── test_workflow.py      ← reglas, herramienta y un test por cada caso del lote
└── docs/                               ← los informes del TP, acumulados hasta esta clase
    ├── ortelana_entrega_1_informe.md   ← Entrega 1 (Clase 2), copia de referencia
    ├── ortelana_entrega_2_informe.md   ← Entrega 2 (Clase 3), copia de referencia
    └── ortelana_entrega_3_informe.md   ← informe modelo de la Entrega 3: Parte A completa (Hito 1),
                                          B y C se completan en las Clases 5 y 6
```

## Qué cambia respecto de la Clase 3

| | Clase 3 | Clase 4 |
|---|---|---|
| **Qué procesa** | Un mensaje: extrae y valida | El journey completo, hasta la respuesta al distribuidor |
| **Llamadas al LLM** | 1 (extraer) | 2: extraer (JSON, temperatura 0) y redactar (texto, temperatura 0.3) |
| **Reglas de negocio** | Dígito verificador del CUIT | + NOR-DOC, NOR-CAT-A/B/C, NOR-NUEVO, NOR-DEUDA, categoría inexistente |
| **Herramientas** | Ninguna | `consultar_sistema_gestion` (sensor: solo lee) |
| **Qué pasa con cada intención** | Solo se clasifica | Se **enruta**: el alta sigue el flujo y el resto recibe una respuesta fija |
| **Resultado** | Extracción validada o error | Uno de 6 estados, con la **traza** de los pasos recorridos |
| **Humano** | No aparece | Punto de control obligatorio antes de aprobar (NOR-APROB) |

## Los 9 casos del lote

| # | Caso | Termina en | Qué enseña |
|---|---|---|---|
| 1 | Completo (B) | `PENDIENTE_APROBACION` | El camino feliz: recorre todo y espera a la persona |
| 2 | Falta un documento | `PENDIENTE` | El caso típico de la Clase 3 hoy **no alcanza**: falta Ingresos Brutos |
| 3 | CUIT inválido | `REVISION_HUMANA` | El flujo se corta en el paso 5 y no sigue con datos no confiables |
| 4 | Manipulación (VIP Oro) | `PENDIENTE` | Nadie aprueba nada. "VIP Oro" queda como alerta |
| 5 | Nuevo que factura como A | `PENDIENTE_APROBACION` | NOR-NUEVO: entra en B y con 30 días, aunque pidió A y 60 |
| 6 | Cliente antiguo (A) | `PENDIENTE_APROBACION` | La **herramienta** cambia la decisión: 18 meses de antigüedad → A |
| 7 | Cliente con deuda | `PENDIENTE_APROBACION` | NOR-DEUDA: solo contado, así que no se le piden documentos |
| 8 | Consulta normativa | `DERIVADO` | El enrutamiento. Desde la Clase 5 se responde con RAG |
| 9 | Fuera de alcance | `DERIVADO` | El stock no está en el MVP |

## Decisiones de diseño que vale la pena discutir en clase

- **Nunca hay aprobación automática.** El workflow termina como mucho en `PENDIENTE_APROBACION`. La aprobación es otra función (`registrar_decision`) que necesita a una persona. Hay un test que lo garantiza (`test_ningun_alta_se_aprueba_sin_una_persona`).
- **PENDIENTE no es rechazo.** Si faltan datos o documentos, se le piden al distribuidor (NOR-DOC). Rechazar a alguien porque se olvidó un papel haría perder clientes.
- **Las alertas no frenan el flujo.** "Pidió VIP Oro" o "pidió A y le corresponde B" no son errores: son información para quien aprueba. Por eso van al legajo.
- **Si falla la redacción, se usa la plantilla.** Para cuando llega el paso 11, la decisión ya está tomada. Si la API se cae, se comunica igual con un texto fijo. Que un error de redacción frene una aprobación no tendría sentido.
- **El LLM redacta a partir de un JSON, no del legajo completo.** Recibe solo lo que tiene que comunicar (categoría, plazo, límite, reglas). Las observaciones internas no le llegan, así no puede filtrarlas al distribuidor.

## ¿Y LangChain?

`cadena_lcel.py` reescribe el paso 2 con el patrón del teórico, `plantilla | modelo | parser`, y da **el mismo resultado** que `extractor.py`. Sirve para mostrar qué resuelve un framework (la "plomería": armar mensajes, llamar a la API, sacar el texto) y qué **no** resuelve: la validación y las reglas siguen siendo nuestro código.

El workflow principal está escrito en Python directo a propósito. Con una secuencia fija y pocos pasos, un framework no aporta mucho. Es el criterio del teórico: *empezar por la opción más simple que resuelva el problema*. Para usar la cadena con Gemini real: `pip install langchain-google-genai`.

## Qué viene en la Clase 5

Los casos 8 y 9 se responden hoy con un texto fijo. En la Clase 5 la normativa ([`ortelana_normativa_comercial.md`](../clase_2/ortelana_normativa_comercial.md)) se convierte en una base de conocimiento con **RAG**, para responder `CONSULTA_NORMATIVA` ("¿el flete a Córdoba lo pagan ustedes?") citando la regla (NOR-ZONA).
