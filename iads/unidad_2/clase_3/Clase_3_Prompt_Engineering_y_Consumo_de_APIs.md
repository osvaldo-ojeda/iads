# Clase 3: Prompt Engineering, Structured Outputs y Consumo de APIs

**Asignatura:** Desarrollo de Sistemas de Inteligencia Artificial

**Objetivo Técnico:** Implementar esquemas de validación de datos en tiempo de ejecución con Pydantic y Structured Outputs multiplataforma, dominar las técnicas de Prompt Engineering para outputs estructurados, y consumir APIs de modelos fundacionales de forma segura y robusta desde Python.

> **Para quienes vienen de las Microcredenciales**
> En la Microcredencial vieron Prompt Engineering como herramienta de diseño de productos. Hoy damos el paso siguiente: convertir ese diseño en código Python que se ejecuta automáticamente, y agregar una capa de validación que garantiza que el contrato de datos se cumpla siempre — aunque el modelo falle.

---

## Planificación de la Clase (4 horas)

| Bloque             | Duración | Contenido                                                   |
| ------------------ | --------- | ----------------------------------------------------------- |
| **Bloque 1** | 30 min    | Debate de evidencia: los scripts rotos que trajeron de casa |
| **Bloque 2** | 45 min    | Prompt Engineering estructurado: Zero-shot, Few-shot y CoT  |
| **Bloque 3** | 75 min    | Pydantic V2 y Structured Outputs — cerrando el contrato    |
| **Bloque 4** | 60 min    | Integración completa: script Python con API real y`.env` |
| **Cierre**   | 30 min    | Resumen, material asincrónico y conexión con Clase 4      |

---

## Bloque 1: Debate de Evidencia — "El Contrato Roto" (30 min)

### Arranque con la tarea asincrónica

La clase arranca con los alumnos exponiendo sus reportes de falla. Cada uno corrió el script de Ortelana con el lote de correos y documentó cuántas veces `json.loads()` explotó.

**Preguntar al grupo:**

- ¿Cuántos tuvieron 0 fallas? ¿Cuántos tuvieron más de 3?
- ¿Qué tipo de error fue el más común — `JSONDecodeError`, `KeyError`, o tipo de dato incorrecto?
- ¿Cuál fue el correo que más rompió el formato?

**Mapear en el pizarrón los tres tipos de falla:**

| Tipo de error       | Qué pasó                                        | Ejemplo                                         |
| ------------------- | ------------------------------------------------- | ----------------------------------------------- |
| `JSONDecodeError` | El modelo agregó texto antes o después del JSON | `"Aquí tienes el JSON: {...}"`               |
| `KeyError`        | El modelo omitió un campo requerido              | Faltó`"intencion_principal"` en la respuesta |
| Tipo incorrecto     | El modelo puso string donde esperábamos float    | `"confianza_clasificacion": "muy alta"`       |

> **La conclusión que tiene que surgir**
> El Prompt Engineering solo no alcanza para garantizar un contrato de datos en producción. La solución tiene dos capas: primero le pedimos bien al modelo (Prompt Engineering + Structured Outputs), después validamos en código lo que devuelve (Pydantic). Hoy construimos las dos.

---

## Bloque 2: Prompt Engineering Estructurado (45 min)

### Conexión con clases anteriores

En Clase 2 diseñamos el System Prompt como validador de lógica y vimos que el LLM actúa como **traductor** — convierte texto informal en JSON estructurado. Hoy profundizamos en cómo diseñar ese traductor con precisión técnica.

> **El problema central**
> Un LLM puede responder en prosa, en Markdown, en JSON, en verso... lo que más probable le resulte. Si no le decimos exactamente qué formato queremos, el código que intenta parsear su respuesta va a fallar. **Prompt Engineering es escribir un contrato: el modelo promete entregar X formato, y el código confía en ese contrato.**

---

### Las tres técnicas fundamentales

#### Zero-shot

Le pedimos algo al modelo sin darle ejemplos. Confiamos en su entrenamiento general.

```text
[System]
Sos un agente de clasificación semántica para Ortelana Textil.
Respondé siempre en JSON con esta estructura exacta:
{"intencion_principal": "...", "identificador_fiscal": "...", "razon_social_declarada": "...", "tipo_tela": "...", "color": "...", "confianza_clasificacion": 0.0}

[User]
"Soy del taller Modas del Sur, CUIT 20-34556789-2, quiero cotizar 15 rollos de denim azul."
```

**Resultado esperado:**

```json
{"intencion_principal": "CONSULTA_STOCK", "identificador_fiscal": "20345567892", "razon_social_declarada": "Modas del Sur", "tipo_tela": "denim", "color": "azul", "confianza_clasificacion": 0.9}
```

**Cuándo usarlo:** Tareas simples y bien definidas.
**Riesgo:** Si el input es ambiguo o malicioso, el modelo puede romper el formato.

---

#### Few-shot

Damos ejemplos de input → output antes de la pregunta real. "Mostramos" en lugar de solo "describir".

```text
[System]
Sos un agente de clasificación semántica para Ortelana Textil.
Usá exactamente esta estructura JSON. Sin texto extra.

Ejemplos:
Input: "¿Tienen stock de gabardina azul?"
Output: {"intencion_principal": "CONSULTA_STOCK", "identificador_fiscal": null, "razon_social_declarada": null, "tipo_tela": "gabardina", "color": "azul", "confianza_clasificacion": 0.9}

Input: "Quiero abrir cuenta corriente, CUIT 20-12345678-9"
Output: {"intencion_principal": "ALTA_DISTRIBUIDOR", "identificador_fiscal": "20123456789", "razon_social_declarada": null, "tipo_tela": null, "color": null, "confianza_clasificacion": 0.95}

[User]
"El jersey que llegó vino manchado, somos el taller El Gaucho, CUIT 27-98765432-1"
```

**Resultado esperado:**

```json
{"intencion_principal": "RECLAMO_OPERATIVO", "identificador_fiscal": "27987654321", "razon_social_declarada": "El Gaucho", "tipo_tela": "jersey", "color": null, "confianza_clasificacion": 0.85}
```

**Cuándo usarlo:** Cuando el Zero-shot falla en casos límite o el formato es complejo.

> **Los ejemplos Few-shot son tests de regresión del prompt**
> Si el modelo falla un ejemplo, el prompt necesita ajuste. Antes de ir a producción, probá al menos 5 inputs distintos — incluyendo los casos que rompieron el script en la tarea asincrónica.

---

#### Chain of Thought (CoT)

Pedimos al modelo que "piense en voz alta" antes de responder. Útil para tareas con múltiples pasos lógicos.

```text
[System]
Sos un asistente de operaciones de Ortelana Textil.
Antes de responder, razonás paso a paso:
1. ¿Qué quiere hacer el distribuidor?
2. ¿Qué datos necesito para eso?
3. ¿Tengo todos los datos o necesito pedir más?
Luego respondé en JSON.

[User]
"Quiero abrir cuenta corriente"
```

**Resultado esperado:**

```
Razonamiento:
1. El distribuidor quiere darse de alta como mayorista.
2. Para validar necesito el identificador fiscal (CUIT).
3. No tengo el CUIT — la confianza de clasificación baja porque falta un dato clave.

{"intencion_principal": "ALTA_DISTRIBUIDOR", "identificador_fiscal": null, "razon_social_declarada": null, "tipo_tela": null, "color": null, "confianza_clasificacion": 0.6}
```

**Cuándo usarlo:** Cuando la respuesta depende de condiciones múltiples. El razonamiento explícito reduce alucinaciones.

---

### Las 4 reglas del prompt para JSON confiable

El salto clave: pasar de "el LLM responde bien" a "el LLM responde de forma que mi código puede leer".

**Regla 1 — Especificar el schema exacto**

```text
Respondé ÚNICAMENTE con un JSON con estas claves:
- "intencion_principal": string (una de: ALTA_DISTRIBUIDOR, CONSULTA_DISTRIBUIDOR, CONSULTA_STOCK, RECLAMO_OPERATIVO)
- "identificador_fiscal": string de 11 dígitos o null
- "razon_social_declarada": string o null
- "tipo_tela": string o null
- "color": string o null
- "confianza_clasificacion": número flotante entre 0.0 y 1.0
```

**Regla 2 — Prohibir texto extra**

```text
No incluyas explicaciones, saludos ni bloques de código (no uses ```json).
Tu respuesta debe comenzar con { y terminar con }.
```

**Regla 3 — El catálogo de intenciones es cerrado, sin comodín**

```text
"intencion_principal" acepta ÚNICAMENTE uno de estos 4 valores:
ALTA_DISTRIBUIDOR, CONSULTA_DISTRIBUIDOR, CONSULTA_STOCK, RECLAMO_OPERATIVO.
No inventes una categoría nueva aunque el mensaje no encaje perfecto.
```

A diferencia de otros diseños que agregan un valor `"DESCONOCIDO"` como comodín, el árbol de intenciones de Ortelana es un catálogo cerrado (así lo define la teoría de Unidad 2). Si el modelo intenta devolver una intención que no está en la lista — por ejemplo `"CANCELACION"` — el `Literal` de Pydantic la rechaza directamente con un `ValidationError`, en vez de dejarla pasar disfrazada de dato válido.

**Regla 4 — Validar en código, nunca confiar ciegamente**

```python
import json

raw = respuesta_llm
try:
    data = json.loads(raw)
    assert "intencion_principal" in data
except (json.JSONDecodeError, AssertionError):
    data = {"intencion_principal": "PARSE_ERROR", "raw": raw}
```

> **Conclusión del Bloque 2**
> El Prompt Engineering no es "hablar bonito con la IA". Es escribir una especificación de contrato. Pero ese contrato solo lo cumple el modelo cuando todo sale bien — Pydantic es el que lo hace cumplir cuando algo falla.

---

## Bloque 3: Pydantic V2 y Structured Outputs (75 min)

### Dos capas de garantía

La arquitectura robusta no confía en una sola capa de validación:

| Capa                               | Herramienta              | Qué garantiza                                                       |
| ---------------------------------- | ------------------------ | -------------------------------------------------------------------- |
| **Garantía del proveedor**  | Structured Outputs (API) | El modelo genera tokens que cumplen el schema matemáticamente       |
| **Garantía de aplicación** | Pydantic V2 (runtime)    | El objeto Python tiene los tipos correctos antes de tocar el backend |

Juntas, estas dos capas cierran el contrato entre el caos del lenguaje natural y la precisión del backend de Ortelana.

---

### Pydantic V2 — El contrato de datos en código

```python
# schemas.py
from pydantic import BaseModel, Field, field_validator
from typing import Literal, Optional

IntencionesPermitidas = Literal[
    "ALTA_DISTRIBUIDOR", "CONSULTA_DISTRIBUIDOR", "CONSULTA_STOCK", "RECLAMO_OPERATIVO"
]

class ConsultaClienteSchema(BaseModel):
    """
    Contrato de datos estricto para normalizar consultas
    recibidas por Ortelana Textil.
    """
    intencion_principal: IntencionesPermitidas = Field(
        description="Categoría raíz del mensaje según el árbol de intenciones del negocio."
    )
    identificador_fiscal: Optional[str] = Field(
        default=None,
        description="Identificador fiscal numérico (ej: CUIT de 11 dígitos), sin guiones ni espacios."
    )
    razon_social_declarada: Optional[str] = Field(
        default=None,
        description="Nombre de la empresa o razón social provista por el remitente."
    )
    tipo_tela: Optional[str] = Field(
        default=None,
        description="Nombre comercial de la tela solicitada (ej: gabardina, lona, denim)."
    )
    color: Optional[str] = Field(
        default=None,
        description="Color específico solicitado por el cliente."
    )
    confianza_clasificacion: float = Field(
        description="Nivel de certeza probabilística del modelo en la clasificación, de 0.0 a 1.0."
    )

    @field_validator('identificador_fiscal')
    @classmethod
    def validar_y_limpiar_idfiscal(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        idfiscal_limpio = "".join(filter(str.isdigit, v))
        if idfiscal_limpio and len(idfiscal_limpio) != 11:
            raise ValueError("El identificador fiscal debe contener exactamente 11 dígitos numéricos.")
        return idfiscal_limpio
```

> **Este es el mismo `ConsultaClienteSchema` de la Teoría de Unidad 2**
> No es una coincidencia de nombres — es el mismo contrato de datos que ya leíste. Acá lo programamos.

> **Pregunta #1**
> ¿Por qué usamos `Literal` (vía `IntencionesPermitidas`) para el campo `intencion_principal` en lugar de `str`?
>
> **Análisis:** Porque `str` acepta cualquier texto — el modelo podría devolver `"CONSULTA_DE_STOCK"` o `"consulta_stock"` y Pydantic lo aceptaría igual. `Literal` restringe los valores posibles exactamente a los 4 que definimos. Si el modelo devuelve algo distinto — incluso una intención que "suena" razonable como `"CANCELACION"` — Pydantic lanza una excepción en lugar de dejar pasar datos inválidos. El árbol de intenciones de Ortelana es un catálogo cerrado; no hay una quinta opción comodín.

---

### Gestión segura de credenciales con `.env`

Antes de conectar con la API, una regla no negociable:

```bash
# .env — NUNCA subir a Git (.gitignore)
OPENAI_API_KEY=sk-proj-XXXXXXXXXXXXXXXXXXXXXXXX
ANTHROPIC_API_KEY=sk-ant-XXXXXXXXXXXXXXXXXXXXXX
```

```python
# app.py
import os
from dotenv import load_dotenv

load_dotenv()  # Lee el archivo .env

api_key = os.getenv("OPENAI_API_KEY")  # ✅ Correcto
# api_key = "sk-proj-abc123..."        # ❌ NUNCA hardcodear
```

> **Si la API Key sube a GitHub, está comprometida en minutos.**
> Los bots escanean repositorios públicos en tiempo real buscando keys expuestas. Una key comprometida puede generar costos de miles de dólares en horas.

---

### Script completo con Structured Outputs (OpenAI)

```python
# app.py
import os
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import ValidationError
from schemas import ConsultaClienteSchema

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

correo_recibido = """
Hola gente de Ortelana!! Cómo andan??
Soy del taller 'Modas del Sur', mi CUIT es el 20-34556789-2.
Queríamos ver si tienen stock de denim de 12 en azul índigo.
Necesitamos cotizar unos 15 rollos urgente porque se nos cae un cliente grande.
Avisen porfa!! Gracias!!
"""

try:
    completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "Sos un agente de clasificación semántica para Ortelana Textil. "
                           "Tu único objetivo es extraer datos estructurados conforme al esquema proporcionado."
            },
            {"role": "user", "content": correo_recibido}
        ],
        response_format=ConsultaClienteSchema,  # Structured Output
    )

    datos: ConsultaClienteSchema = completion.choices[0].message.parsed

    print("--- PIPELINE EXITOSO ---")
    print(f"Intención:            {datos.intencion_principal}")
    print(f"Identificador fiscal: {datos.identificador_fiscal}")
    print(f"Razón social:         {datos.razon_social_declarada}")
    print(f"Tipo de tela:         {datos.tipo_tela}")
    print(f"Color:                {datos.color}")
    print(f"Confianza:            {datos.confianza_clasificacion:.2f}")

except ValidationError as e:
    print(f"ERROR: Los datos violaron el schema de Ortelana. Detalles: {e}")
except Exception as e:
    print(f"Falla de comunicación con el proveedor: {e}")
```

**Output esperado:**

```
--- PIPELINE EXITOSO ---
Intención:            CONSULTA_STOCK
Identificador fiscal: 20345567892
Razón social:         Modas del Sur
Tipo de tela:         denim
Color:                azul índigo
Confianza:            0.92
```

> **Pregunta #2**
> ¿Qué diferencia hay entre usar `.parse()` con `response_format=ConsultaClienteSchema` y usar `json.loads()` con el texto crudo?
>
> **Análisis:** Con `.parse()`, OpenAI restringe la generación del modelo para que matemáticamente solo pueda producir tokens válidos según el schema. El resultado ya llega como objeto Pydantic validado — no como string. Con `json.loads()` el string puede contener cualquier cosa y el parseo puede fallar. Es la diferencia entre garantía y esperanza.

---

### Abstracción multiproveedor — Evitando el Vendor Lock-in

Los tres proveedores resuelven el mismo problema de forma distinta:

| Proveedor           | Mecanismo                              | Código clave                                                                            |
| ------------------- | -------------------------------------- | ---------------------------------------------------------------------------------------- |
| **OpenAI**    | `response_format` con clase Pydantic | `client.beta.chat.completions.parse(..., response_format=MiSchema)`                    |
| **Anthropic** | Tool Use forzado                       | Define una "herramienta" ficticia con el schema y fuerza su uso                          |
| **Gemini**    | `generation_config` con schema       | `generation_config={"response_mime_type": "application/json", "response_schema": ...}` |

> **¿Por qué importa esto?**
> Los precios, capacidades y límites de los modelos cambian constantemente. Un sistema bien diseñado puede cambiar de proveedor sin reescribir la lógica de negocio — solo el adaptador de la API. Pydantic actúa como la interfaz común entre todos.

---

### Tabla comparativa de schemas de respuesta

|                             | OpenAI                                  | Anthropic                      | Gemini                |
| --------------------------- | --------------------------------------- | ------------------------------ | --------------------- |
| **Acceso al texto**   | `response.choices[0].message.content` | `response.content[0].text`   | `response.text`     |
| **Structured Output** | `.parse()` con Pydantic               | Tool Use                       | `response_schema`   |
| **System prompt**     | En`messages` con `role: "system"`   | Parámetro`system=` separado | Incluido en el prompt |
| **Modelo económico** | `gpt-4o-mini`                         | `claude-haiku-4-5-20251001`  | `gemini-1.5-flash`  |

---

## Bloque 4: Laboratorio Técnico — Pipeline completo (60 min)

### Consigna

Construir el pipeline completo de extracción y validación para Ortelana Textil. El script debe:

1. Leer las credenciales desde `.env` — nunca hardcodeadas.
2. Enviar un correo de Ortelana a la API eligiendo uno de los tres proveedores.
3. Usar Structured Outputs + Pydantic para garantizar el contrato.
4. Parsear la respuesta y mostrar los campos extraídos.
5. Manejar correctamente `ValidationError` y excepciones de red.

**Script base — completar eligiendo un proveedor:**

```python
import os
from dotenv import load_dotenv
from pydantic import ValidationError
from schemas import ConsultaClienteSchema

load_dotenv()

# ── Elegir proveedor (descomentar uno) ───────────────────────────────────────
# OPCIÓN A: OpenAI
# from openai import OpenAI
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# OPCIÓN B: Anthropic
# import anthropic
# client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# OPCIÓN C: Gemini
# import google.generativeai as genai
# genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# ── Input de prueba ──────────────────────────────────────────────────────────
correo = """
Buenas! Soy de Textiles Norpatagonia, CUIT 30-71234567-8.
Necesitamos jersey 40/60 algodón-poliéster en gris melange,
unos 25 rollos. ¿Tienen en filial Córdoba?
"""

# ── Llamada a la API (completar según proveedor elegido) ─────────────────────
datos_validados = None  # Reemplazar con la llamada real

# ── Mostrar resultado ────────────────────────────────────────────────────────
if datos_validados:
    print(f"Intención:            {datos_validados.intencion_principal}")
    print(f"Identificador fiscal: {datos_validados.identificador_fiscal}")
    print(f"Razón social:         {datos_validados.razon_social_declarada}")
    print(f"Tipo de tela:         {datos_validados.tipo_tela}")
    print(f"Color:                {datos_validados.color}")
    print(f"Confianza:            {datos_validados.confianza_clasificacion:.2f}")
```

**Preguntas de cierre:**

- ¿Qué pasa si cambiás `temperature=0` a `temperature=1`? ¿El JSON sigue siendo estable?
- ¿Qué técnica de prompting usaste? ¿Mejoraría con Few-shot?
- ¿En qué paso del flujo de Clase 2 conectarías este script con el SQL?

---

## Cierre y Material Asincrónico (30 min)

### Resumen de la clase

- **Zero-shot / Few-shot / CoT:** tres técnicas con distintos niveles de control sobre el output del modelo.
- **4 reglas del JSON confiable:** schema estricto + prohibir texto extra + fallback + validar en código.
- **Dos capas de garantía:** Structured Outputs (nivel API) + Pydantic (nivel aplicación).
- **`.env`:** las credenciales nunca van en el código — siempre en variables de entorno.
- **Multiproveedor:** el schema Pydantic es la interfaz común — el adaptador cambia, la lógica no.

---

### Material asincrónico — Entre Clase 3 y Clase 4

> **La Clase 4 arranca asumiendo que reflexionaron sobre esto**

**Desafío del contexto estático:**

Modificar el script de hoy e intentar que el LLM responda si hay stock físico de un producto, inyectando directamente en el prompt esta lista simulada de 100 artículos del catálogo de Ortelana:

```python
catalogo_simulado = [
    {"id": "TELA-001", "nombre": "Denim 12oz índigo", "stock": True, "sucursal": "central_bsas"},
    {"id": "TELA-002", "nombre": "Seda natural satinada", "stock": True, "sucursal": "filial_cordoba"},
    # ... 98 artículos más
]

prompt = f"""
Sos el asistente de stock de Ortelana.
Catálogo completo: {json.dumps(catalogo_simulado)}
Pregunta del distribuidor: "¿Tienen denim azul en Córdoba?"
"""
```

**Pregunta de reflexión — responder antes de la Clase 4:**

Si el catálogo de Ortelana cambia cada 3 minutos (ventas en tiempo real), ¿cuáles son los tres problemas críticos de ingeniería que surgen al meter todo el inventario dentro del System Prompt de forma estática?

*Pista: pensá en costo por token, ventana de contexto y latencia.*

---

### Conexión con Clase 4

En la Clase 4 resolvemos el problema que acabamos de crear: meter el catálogo entero en el prompt es costoso, lento y no escala. La solución son los **Embeddings y la búsqueda semántica** — en lugar de pasarle todo el catálogo al modelo, le pasamos solo los artículos más relevantes para la consulta. Eso es la base de RAG.

---

## Bibliografía de la Clase

- **Pydantic V2 Documentation.** Models, Fields and Custom Validators. docs.pydantic.dev
- **OpenAI API Reference.** Structured Outputs Guide. platform.openai.com/docs
- **Documentación oficial Anthropic.** Tool Use. docs.anthropic.com
- **Huyen, C. (2025).** *AI Engineering: Building Applications with Foundation Models.* O'Reilly. Capítulo 3.
- **White, J., et al. (2023).** *A Prompt Pattern Catalog to Enhance Prompt Engineering with ChatGPT.*
