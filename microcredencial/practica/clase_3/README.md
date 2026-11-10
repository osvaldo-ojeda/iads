# Clase 3 — Primer prototipo operativo de Ortelana

Componente de extracción del **onboarding de distribuidores** de Ortelana Textil: recibe el mensaje de un distribuidor en texto libre y devuelve sus datos estructurados y validados.

Construye los **pasos 2, 4 y 5 del user journey** diseñado en la [Entrega 1](../clase_2/ortelana_entrega_1_informe.md):

```
Mensaje → [LLM + prompt v1] → json.loads() → Pydantic → regla CUIT → extracción validada
           paso 2              └──── paso 4 ────────┘   └─ paso 5 ─┘
                               ¿es JSON?  ¿cumple el    ¿el CUIT es
                                           contrato?     válido?
```

## Cómo correrlo

Desde esta carpeta (`clase_3/`):

```bash
pip install -r requirements.txt
cp .env.example .env      # completar GEMINI_API_KEY (gratis en https://aistudio.google.com)

python app.py             # corre el lote de prueba con el prompt v1
python app.py v2          # lo mismo con otra versión del prompt (si existe prompts/extraccion_v2.txt)
python -m pytest          # pruebas del contrato y las reglas (no usan la API)
```

Sin API key, `app.py` corre en **modo simulación**, con respuestas de ejemplo.

> **Cada alumno con su propia key.** La capa gratuita de Gemini tiene un límite de pedidos por minuto y por día. Si varios comparten una key, se bloquea enseguida (error 429).

## Estructura

```
clase_3/
├── README.md              ← este archivo
├── app.py                 ← punto de entrada: corre el lote y muestra la tabla
├── requirements.txt       ← dependencias
├── .env.example           ← variables de entorno SIN valores (el .env real no se sube)
│
├── ortelana/              ← el componente, un módulo por responsabilidad
│   ├── config.py          ← lee el .env y detecta qué proveedor de LLM hay
│   ├── contrato.py        ← contrato de datos (Pydantic): qué debe devolver el LLM
│   ├── llm.py             ← llamada a la API (Gemini / OpenAI / Groq) con reintentos
│   ├── reglas.py          ← reglas de negocio en código (dígito verificador del CUIT)
│   └── extractor.py       ← el flujo: mensaje → LLM → json.loads → Pydantic → reglas
│
├── prompts/
│   └── extraccion_v1.txt  ← system prompt versionado (few-shot)
│
├── datos/
│   └── lote_prueba.json   ← los 4 casos del lote: típico, ambiguo, manipulación, alcance
│
├── tests/
│   └── test_contrato.py   ← 16 pruebas del contrato y las reglas, sin API
│
└── docs/
    └── ortelana_entrega_2_informe.md  ← informe modelo de la Entrega 2 (nivel "Destacado")
```

**¿Por qué separado así?** Cada archivo responde una sola pregunta, y cada uno cambia por motivos distintos:

| Si quiero... | Toco... |
|---|---|
| Mejorar cómo extrae el modelo | `prompts/` (y creo una versión nueva, no piso la anterior) |
| Agregar un campo o una intención | `contrato.py` **y** el prompt (tienen que coincidir) |
| Cambiar de proveedor de LLM | Solo el `.env` |
| Agregar una regla de negocio | `reglas.py` |
| Probar un caso nuevo | `datos/lote_prueba.json` |

## Qué evoluciona respecto de la Clase 2

La [práctica de la Clase 2](../clase_2/clase_2_practica.py) ya tenía la idea central: el LLM extrae, Pydantic valida el contrato y una regla verifica el CUIT. La Clase 3 la convierte en un prototipo operativo:

| | Clase 2 | Clase 3 |
|---|---|---|
| **Intenciones** | No clasificaba intenciones | Las 5 de la Matriz de la Entrega 1 |
| **Prompt** | Dentro del código | Archivo versionado aparte, few-shot |
| **Mensaje del distribuidor** | Pegado dentro del prompt | Separado como mensaje de usuario, delimitado con `<mensaje>` |
| **Errores** | Contrato y regla separados, pero comunicación y formato en un mismo error | Cuatro etapas por separado: comunicación, formato, contrato y regla |
| **Saturación de la API** | Fallaba | Reintenta ante 503 y 429 |
| **Casos de prueba** | 3, dentro del código | 4 en un archivo de datos, con el formato de la Entrega 2 |
| **Pruebas automáticas** | No tenía | 16 pruebas sin API |
| **Estructura** | Un solo archivo | Un módulo por responsabilidad |

## Qué viene en la Clase 4

El componente de hoy procesa **un mensaje suelto**. En la Clase 4 se convierte en un **workflow** con el journey completo: se suman a `reglas.py` la documentación obligatoria (NOR-DOC), la categoría y el plazo (NOR-CAT, NOR-NUEVO) y el rechazo de categorías inexistentes ("VIP Oro"), y se agrega la redacción de la respuesta al distribuidor (paso 11).
