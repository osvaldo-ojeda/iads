# Clase 5 — Workflow de Ortelana + RAG sobre la normativa

El workflow de la [Clase 4](../clase_4/) respondía las consultas normativas con un texto fijo ("la derivamos al área comercial"). Hoy las responde con **RAG**: busca en la [normativa comercial](../clase_2/ortelana_normativa_comercial.md) las reglas que tienen que ver con la pregunta y el LLM responde **usando solo esas reglas** y citándolas.

```
Mensaje
  ├─ 1  Acuse ......................................... 📏 Regla
  ├─ 2  Extraer intención y datos ..................... 🤖 LLM          ┐
  ├─ 4  Validar contrato (json.loads + Pydantic) ...... 📏 Regla        ├ Clase 3
  ├─ 5  Validar CUIT .................................. 📏 Regla        ┘
  ├─    Enrutar por intención ......................... 📏 Regla
  │      ├─ CONSULTA_NORMATIVA → RAG .................. 📚 RAG + 🤖 LLM  ← NUEVO
  │      │     ├─ algún fragmento supera el umbral → RESPONDIDA (citando la regla)
  │      │     └─ ✋ ninguno → DERIVADO ("No tengo información oficial")
  │      └─ otra que no es alta → DERIVADO (respuesta fija)
  ├─ 6 a 11  el alta, igual que en la Clase 4 ......... 📏 🔧 🙋 🤖     ┘ Clase 4
```

**La idea de la clase en una línea:** el modelo no sabe la normativa de Ortelana. En vez de confiar en su memoria, **le damos el texto de la regla en el momento de la consulta**. Eso es *grounding*, y RAG es la forma más común de hacerlo.

## Cómo correrlo

Desde esta carpeta (`clase_5/`):

```bash
pip install -r requirements.txt
cp .env.example .env      # opcional: GEMINI_API_KEY para que el LLM redacte de verdad

python app.py                           # los 12 casos del lote, con la traza de cada uno
python app.py buscar "¿El flete a Córdoba lo pagan ustedes?"           # qué recupera y con qué similitud
python app.py buscar "¿El flete a Córdoba lo pagan ustedes?" --todas   # sin filtro: aparece la regla DEROGADA
python app.py comparar                  # la misma pregunta sin RAG y con RAG (Entrega 3, B.3)
python app.py telas                     # el ejemplo del teórico: "busco algo fresco para un vestido de verano"
python app.py indexar                   # rehace los índices (el paso OFFLINE)
python -m pytest                        # 71 pruebas (no usan la API)
```

> ⏳ **La primera vez tarda:** descarga el modelo de embeddings (~640 MB) y lo guarda en `~/.cache/fastembed`. Después arranca en segundos.

**Sin API key** también funciona. La **búsqueda semántica corre de verdad** (embeddings, ChromaDB, filtro y umbral): los embeddings se calculan en la compu, no en una API. Lo único simulado es el LLM: en vez de redactar, muestra el fragmento recuperado tal cual.

## Estructura

```
clase_5/
├── app.py                        ← el lote + las demos de RAG (buscar, comparar, telas, indexar)
├── ortelana/
│   ├── base_conocimiento.py      ← NUEVO · embeddings + ChromaDB: indexar (offline) y buscar (online)
│   ├── rag.py                    ← NUEVO · la cadena RAG de LangChain: recuperar | plantilla | modelo | parser
│   ├── workflow.py               ← CONSULTA_NORMATIVA ahora va al RAG (antes: respuesta fija)
│   ├── extractor.py, contrato.py, reglas.py, herramientas.py, redactor.py, llm.py, config.py
│   │                               ← igual que en la Clase 4
│   └── cadena_lcel.py            ← el paso 2 como cadena LCEL (de la Clase 4)
├── prompts/
│   ├── rag_v1.txt                ← NUEVO · "usá ÚNICAMENTE el contexto; si no está, decí que no sabés"
│   ├── sin_grounding_v1.txt      ← NUEVO · la misma pregunta sin contexto, para comparar
│   ├── extraccion_v1.txt         ← igual que en la Clase 3
│   └── redaccion_v1.txt          ← igual que en la Clase 4
├── datos/
│   ├── corpus_normativa.json     ← NUEVO · 12 reglas (9 vigentes + 3 derogadas) con descripcion_semantica y metadatos
│   ├── catalogo_telas.json       ← NUEVO · 12 telas: el ejemplo del teórico (fuera del workflow)
│   ├── preguntas_comparacion.json← NUEVO · 4 preguntas para el antes/después
│   ├── lote_prueba.json          ← 12 casos (los 9 de la Clase 4 + 3 consultas normativas)
│   └── sistema_gestion.json      ← el "ERP" simulado (igual que en la Clase 4)
├── indice_chroma/                ← se genera solo; no se sube a git
├── tests/
│   ├── test_rag.py               ← NUEVO · recuperación, filtro, umbral y cadena
│   ├── test_workflow.py, test_contrato.py
│   └── conftest.py               ← las pruebas nunca llaman a una API
└── docs/                         ← los informes del TP, acumulados hasta esta clase
    ├── ortelana_entrega_1_informe.md   ← Entrega 1 (Clase 2), copia de referencia
    ├── ortelana_entrega_2_informe.md   ← Entrega 2 (Clase 3), copia de referencia
    └── ortelana_entrega_3_informe.md   ← Entrega 3: Parte A (Clase 4) + Parte B (hoy); la C, en la Clase 6
```

## Qué cambia respecto de la Clase 4

| | Clase 4 | Clase 5 |
|---|---|---|
| **`CONSULTA_NORMATIVA`** | Respuesta fija: "la derivamos al área comercial" | RAG: responde citando la regla, o dice "No tengo información oficial" |
| **Estados posibles** | 6 | 7: se suma `RESPONDIDA` |
| **Base de conocimiento** | Ninguna | ChromaDB con la normativa (12 documentos) y el catálogo de telas (12) |
| **LangChain** | Opcional (`cadena_lcel.py`) | **La cadena RAG está hecha con LangChain** (`rag.py`) |
| **Puntos de control** | 4 | 5: se suma el **umbral de similitud** |
| **Lote** | 9 casos | 12 casos |

## Los casos nuevos del lote

| # | Caso | Termina en | Qué enseña |
|---|---|---|---|
| 8 | Consulta normativa (flete a Córdoba) | `RESPONDIDA` | Antes era `DERIVADO`. La versión **derogada** de la regla decía lo contrario: el filtro `vigente=True` la deja afuera |
| 10 | Consulta con sinónimos | `RESPONDIDA` | "Transporte de la mercadería" encuentra la regla del "flete": busca por **significado** |
| 11 | Consulta de documentación | `RESPONDIDA` | NOR-DOC se usa para **informar** (RAG) y para **decidir** (`reglas.py`) |
| 12 | Consulta sin respuesta (criptomonedas) | `DERIVADO` | Nada supera el umbral: **el LLM ni se llama**. Sin RAG, el modelo lo inventa |

## Decisiones de diseño que vale la pena discutir en clase

- **El RAG informa, las reglas deciden.** NOR-CAT-B está en el corpus para *responder preguntas* ("¿cuánto crédito me dan en B?"). La categoría de un alta la sigue calculando `reglas.py`. Un texto recuperado por similitud no es una fuente confiable para una decisión con plata de por medio.
- **Un documento por regla.** El *chunking* se hizo a mano: cada regla es una unidad de sentido. Cortar el documento cada 500 caracteres partiría reglas por la mitad.
- **Lo que se filtra va en metadatos.** `vigente`, `seccion` y `en_stock` son metadatos: se comparan exacto. Lo que se busca por significado va en `descripcion_semantica`. Probá `python app.py telas "tela de jean"`: "jean" está solo en los metadatos, y por eso no lo encuentra.
- **El umbral es una decisión, no un número mágico.** Con este corpus y este modelo, lo que está en la normativa da 0.38 o más, y lo que no está, 0.30-0.32. Por eso 0.35. Con otro modelo hay que recalibrarlo.
- **Dos capas contra la invención.** El umbral evita llamar al LLM sin contexto. Si algo pasa el umbral pero no responde la pregunta, el prompt le pide decir *"No tengo información oficial"*, y el workflow lo deriva igual.
- **Embeddings en la compu, no en una API.** Son gratis, funcionan sin conexión y sin key, y el modelo (`jina-embeddings-v2-base-es`) está entrenado en español. Con el modelo que trae ChromaDB por defecto (en inglés), la búsqueda acertaba 3 de 7 preguntas de prueba; con este, 6 de 7.

## ¿Y LangChain?

`rag.py` arma el RAG como una cadena LCEL. Es la misma idea de la Clase 4 (`plantilla | modelo | parser`) con **un paso nuevo adelante**: recuperar el contexto.

```python
cadena = RunnableParallel(pregunta=RunnablePassthrough(), documentos=recuperar).assign(
    respuesta=RunnableBranch(
        (no_hay_contexto, lambda x: "No tengo información oficial..."),   # ✋ el umbral
        armar_contexto | plantilla | modelo | StrOutputParser(),
    )
)
```

Lo que aporta LangChain acá: `Document` (texto + metadatos), la interfaz `Embeddings`, `Chroma` como base vectorial, `ChatPromptTemplate` y el modelo intercambiable (Gemini, OpenAI o el simulado, sin cambiar la cadena). La Clase 6 se apoya en todo esto: LangGraph está construido sobre LangChain.

## Qué viene en la Clase 6

Hoy el RAG responde **una** pregunta con **una** fuente. Si un distribuidor pregunta *"¿con mi facturación me corresponden cuotas sin interés?"*, hace falta consultar el sistema de gestión (la herramienta), aplicar las reglas **y** buscar en la normativa, en el orden que convenga. En la Clase 6 es el **modelo** el que decide qué herramienta usar: eso es un **agente**.
