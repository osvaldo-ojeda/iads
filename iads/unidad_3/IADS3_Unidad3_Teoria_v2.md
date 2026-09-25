Instituto de Tecnología ORT

Técnico Superior en Inteligencia Artificial y Data Science (IADS)

# UNIDAD 3 - TEORÍA v2

## Grounding y Representación del Conocimiento

---

## 1. De los Embeddings a la Memoria Vectorial

En la Unidad 2 resolvimos el problema del formato: conseguimos que un modelo de lenguaje devuelva datos estructurados y validados con Pydantic. Pero ese logro no resuelve un problema más profundo. El modelo puede respetar perfectamente el contrato de datos y, aun así, desconocer por completo el catálogo real de Ortelana Textil, sus políticas comerciales o el estado actual del inventario.

Meter el catálogo entero dentro del System Prompt no es una alternativa viable. Ya vimos por qué: el costo en tokens crece sin control, el modelo pierde precisión cuando el dato relevante queda en medio de un bloque de texto masivo ("Lost in the Middle"), y el inventario de una tejeduría mayorista cambia todo el tiempo — un prompt estático queda desactualizado en minutos.

Necesitamos una **Memoria Vectorial Externa**: un mecanismo que le permita al sistema consultar solo la porción de conocimiento relevante para cada pregunta, sin cargar todo el catálogo en cada interacción.

### 1.1 ¿Qué es un Embedding?

**Definición conceptual:** un embedding es un proceso de traducción matemática que toma un fragmento de texto — una palabra, una oración, un párrafo completo — y lo convierte en un **vector**: una lista ordenada de números decimales de longitud fija.

Al transformar el lenguaje en vectores, dejamos de tratar al texto como letras sueltas y pasamos a representarlo como coordenadas en un espacio de múltiples dimensiones. En ese "espacio semántico", las ideas que comparten significado conceptual —aunque usen palabras completamente distintas— se ubican geométricamente cerca unas de otras.

**Ejemplo conceptual con el catálogo de Ortelana:**

```
"Denim pesado, tacto rústico, alta resistencia"  → [0.8, 0.1, 0.9, 0.2, ...]
"Lona industrial impermeable, muy resistente"    → [0.7, 0.1, 0.9, 0.3, ...]  (cercano)
"Seda natural satinada, caída fluida, liviana"   → [0.1, 0.9, 0.1, 0.8, ...]  (lejano)
```

Esto es lo que permite resolver el problema clásico de las bases de datos tradicionales: una consulta SQL con `WHERE descripcion LIKE '%fresco%'` no encuentra nada si el catálogo dice "transpirable" o "liviano". El sistema tradicional es sintáctico, no semántico — falla ante la sinonimia y la jerga informal de un cliente real. Los embeddings resuelven exactamente ese abismo.

**Modelos de embeddings disponibles en la industria:**

| Proveedor | Modelo | Dimensiones | Uso típico |
|---|---|---|---|
| OpenAI | `text-embedding-3-small` | 1536 | Prototipado y producción |
| OpenAI | `text-embedding-3-large` | 3072 | Mayor precisión, más costo |
| Anthropic | Vía Voyage AI | 1024 | Integración con Claude |
| Google | `text-embedding-004` | 768 | Ecosistema Google |
| Local | `sentence-transformers` | Variable | Sin costo, sin conexión a internet |

En esta materia trabajamos con `text-embedding-3-small` de OpenAI (1536 dimensiones) por su balance entre costo y calidad.

### 1.2 La Matemática de la Similitud Coseno

Para que un sistema determinista pueda decidir qué tan "cerca" están dos vectores, necesita una métrica. La métrica estándar en sistemas de IA es la **Similitud Coseno**: en lugar de medir la distancia entre las puntas de dos vectores, mide el **ángulo** que forman entre sí desde el origen del espacio.

**Intuición visual — el espacio de Ortelana en 2D**

Para desmitificar la fórmula, reducimos el universo semántico de Ortelana a un plano de dos ejes:

- **Eje X — Resistencia Industrial:** qué tan adecuada es la tela para trabajo pesado o protección (de 1 a 10).
- **Eje Y — Elasticidad / Suavidad:** qué tan flexible y confortable es al tacto (de 1 a 10).

Definimos dos vectores:

- **Vector A** — Lona de Alta Densidad: `A = [5, 1]` *(mucha resistencia, mínima elasticidad)*
- **Vector B** — Consulta del cliente ("Busco lona rígida para toldos"): `B = [4, 2]`

**Fórmula:**

```
Similitud Coseno(A, B) = (A · B) / (‖A‖ × ‖B‖)
```

**Paso 1 — Producto escalar (A · B):**

```
(5 × 4) + (1 × 2) = 20 + 2 = 22
```

**Paso 2 — Magnitudes (normas euclidianas):**

```
‖A‖ = √(5² + 1²) = √26 ≈ 5.10
‖B‖ = √(4² + 2²) = √20 ≈ 4.47
```

**Paso 3 — División final:**

```
Similitud = 22 / (5.10 × 4.47) = 22 / 22.80 ≈ 0.965
```

Un resultado de **0.965** (muy cercano a 1) significa que la consulta del cliente y la Lona de Alta Densidad apuntan casi en la misma dirección del espacio vectorial — el motor los emparejó correctamente sin que el cliente conociera el nombre técnico del producto.

El resultado de la similitud coseno oscila entre **-1.0** (direcciones opuestas) y **1.0** (misma dirección semántica). Esto permite definir en el backend un **umbral de aceptación (threshold)**: por ejemplo, "si el score es mayor a 0.80, recuperamos el producto; si es menor, asumimos que no tenemos esa tela en catálogo".

**¿Por qué el ángulo y no la distancia?** Porque nos importa la dirección — el significado — no la magnitud. Un párrafo largo sobre denim y una sola oración sobre denim deben resultar similares, aunque sus vectores tengan longitudes muy distintas por la cantidad de texto.

### 1.3 FAISS: Rompiendo el Cuello de Botella

Calcular la similitud coseno de forma secuencial contra cada artículo del catálogo mediante un bucle `for` es una excelente forma de entender la matemática, pero es un pésimo diseño de software. Si el catálogo de Ortelana escala a miles de artículos, comparar la consulta contra cada uno de ellos por fuerza bruta dispararía la latencia del sistema.

Para resolver esto usamos **FAISS** (Facebook AI Similarity Search): una librería de código abierto de Meta, optimizada en C++, que organiza vectores en estructuras de datos indexadas en memoria RAM y realiza búsquedas por similitud geométrica a velocidades muy altas.

**Tipos de índice en FAISS:**

| Índice | Funcionamiento | Cuándo usarlo |
|---|---|---|
| `IndexFlatL2` | Búsqueda exacta y exhaustiva. Compara contra *todos* los vectores. Complejidad O(N). 100% de precisión. | Catálogos pequeños o medianos (< 10.000 artículos). Es el que usamos en esta unidad. |
| `IndexFlatIP` | Búsqueda exacta por producto interno. Equivalente a similitud coseno si los vectores están normalizados. | Cuando se trabaja con embeddings normalizados de OpenAI. |
| `IndexIVFFlat` | Búsqueda aproximada. Agrupa vectores en clústeres con K-Means y busca solo en los más cercanos al centroide. Reduce el costo de O(N) a sub-lineal. | Catálogos masivos (millones de vectores). Requiere entrenamiento previo. |

Para el volumen de datos de Ortelana Textil, `IndexFlatL2` garantiza precisión milimétrica sin sacrificar velocidad.

### 1.4 El Diseño del Campo Semántico

Un detalle arquitectónico que suele pasarse por alto: el embedding se genera sobre un texto específico, y la calidad de ese texto determina directamente la calidad de la búsqueda. Por eso, en el catálogo de Ortelana cada artículo separa un campo dedicado, `descripcion_semantica`, del resto de sus atributos estructurados:

```json
{
  "id": "TELA-001",
  "descripcion_semantica": "Denim pesado de 12 oz, 100% algodón rígido con teñido índigo intenso. Presenta un tacto rústico, alta resistencia al roce y cuerpo firme. Ideal para camperas y pantalones de trabajo.",
  "metadatos": {
    "linea_textil": "indumentaria",
    "sucursal_disponible": "central_buenos_aires",
    "en_stock": true,
    "tags_regionales": ["jean", "vaquero", "mezclilla", "ropa de trabajo"]
  }
}
```

Un campo `nombre: "Denim 12oz"` solo aporta dos palabras para vectorizar. La `descripcion_semantica`, en cambio, es un párrafo rico en textura, usos y sinónimos — cuanto más descriptivo, mejor captura el embedding el significado real del producto. Esta separación entre **texto para vectorizar** (`descripcion_semantica`) y **datos estructurados para filtrar** (`metadatos`) es la base de todo lo que sigue en esta unidad.

---

## 2. De FAISS a la Base de Datos Vectorial: La Ilusión de la Memoria

### El costo oculto de indexar con FAISS

Es muy común tener la falsa ilusión de que haber implementado FAISS resuelve definitivamente la gestión de nuestras representaciones vectoriales. FAISS nos permite calcular distancias geométricas a una velocidad asombrosa en memoria RAM. Sin embargo, a la hora de llevar una solución a un entorno de producción real, actualizar, borrar o modificar vectores en un archivo `.index` resulta sumamente engorroso.

FAISS es una biblioteca matemática de alto rendimiento, pero **no es una base de datos**. Cuando el negocio de Ortelana Textil empieza a operar en el día a día, la rigidez del índice en memoria choca contra tres problemas operativos críticos:

**Desfase de Atomicidad: Relaciones de datos débiles**

En FAISS, el índice solo guarda una matriz de números *floats* y devuelve una posición física (ej: "el resultado es el índice 2"). La aplicación está obligada a sostener un archivo externo (como un JSON en disco) para mapear que el índice 2 corresponde a la "Seda natural de la sucursal Córdoba".

Si la aplicación de Ortelana sufre una caída de servidor mientras guarda un nuevo producto, el archivo `.index` de FAISS puede llegar a actualizarse pero el JSON de textos no. Al reiniciar, los datos quedan corridos: el sistema empezará a devolver descripciones de "Lona para camión" cuando la búsqueda geométrica había encontrado una "Gaza ligera".

**Ineficiencia CRUD: Costos elevados por indexación continua**

Si la sucursal de Buenos Aires modifica una sola palabra en la descripción de un producto o actualiza su precio, no existe una función simple para "editar" ese vector en FAISS. Como la matriz matemática es rígida, la única forma de modificar un registro es destruir el índice completo, reanalizar todo el catálogo desde cero, pagar nuevamente a la API de OpenAI para regenerar los embeddings de telas que no cambiaron, y reconstruir el archivo en disco.

**Ceguera de Filtrado: Buscar la aguja en el pajar**

Si un cliente pregunta por WhatsApp *"¿Tienen lona impermeable disponible en la sucursal Central?"*, un índice vectorial puro compara la consulta contra **todas** las telas del catálogo. Se desperdicia cómputo calculando distancias sobre productos sin stock o de otras provincias, simplemente porque FAISS no puede aplicar reglas condicionales duras (`WHERE sucursal = 'central'`) antes de calcular la matemática.

**FAISS (el cuaderno) vs. ChromaDB (la base de datos)**

| FAISS | ChromaDB |
|---|---|
| Es como anotar vectores en un cuaderno borrador: es veloz y sirve para una prueba en vivo, pero si se pierde el hilo o cambia una hoja, hay que rehacer el cuaderno entero. | Funciona como un motor de base de datos real: los datos persisten en disco, tienen estructura ACID, manejan metadatos nativos y soportan consultas complejas sin perder la sincronización. |

### La Arquitectura Atómica en ChromaDB

Para solucionar este desacoplamiento, una base de datos vectorial como ChromaDB unifica la información en un único contenedor atómico: almacena de forma conjunta un **ID** único, el **documento** en texto plano, su **vector de embedding** y los **metadatos** estructurados que permiten aplicar filtros y reglas de negocio sobre el registro.

```json
{
  "id": "G1-TELA-001",
  "documento": "Denim pesado de 12 oz, ideal para indumentaria de trabajo",
  "embedding": [0.014, -0.082, 0.311, "... 1536 dimensiones"],
  "metadatos": {
    "sucursal": "central_buenos_aires",
    "en_stock": true,
    "categoria": "pesados"
  }
}
```

Al agrupar el ID, el Vector, el Texto Plano y los Metadatos en una sola transacción, ChromaDB nos permite utilizar métodos transaccionales como `.upsert()` (insertar o actualizar en caliente) o `.delete()`, garantizando que si el stock de una tela cambia a `False`, la base se actualice en milisegundos sin romper la consistencia semántica.

---

## 3. Arquitectura Operativa y Persistencia en ChromaDB

### El Ecosistema Vectorial: Dónde se ubica ChromaDB

En el panorama actual existen múltiples alternativas para gestionar vectores. Comprender sus diferencias permite tomar decisiones de arquitectura fundamentadas según la escala del proyecto:

| Criterio / Característica | FAISS | ChromaDB | Pinecone | pgvector |
|---|---|---|---|---|
| Tipo de herramienta | Índice vectorial en memoria | BD Vectorial Open Source | BD Vectorial SaaS (Cloud) | Extensión para PostgreSQL |
| Persistencia | ❌ Solo memoria RAM | ✅ Disco local (SQLite) | ✅ Cloud distribuida | ✅ Base de datos SQL |
| Filtrado de Metadatos | ❌ Requiere mapeo externo | ✅ Nativo (Pre-filtrado) | ✅ Nativo | ✅ Consultas SQL + Vectores |
| Caso de Uso Principal | Búsqueda ultrarrápida en memoria | Prototipado, Colab y desarrollo | Producción masiva y alta concurrencia | Sistemas corporativos existentes |

**Nota de Arquitectura:** en esta materia utilizamos ChromaDB porque corre 100% de manera local dentro de entornos Colab sin requerir infraestructura cloud ni API Keys de terceros. Más adelante en la cursada evaluaremos cómo migrar esta misma lógica hacia servicios gestionados de producción como Pinecone.

### Modos de Ejecución y Persistencia Real en Colab

ChromaDB puede inicializarse en dos modos de trabajo según la etapa de desarrollo:

**Modo Volátil (en memoria):** útil para pruebas unitarias rápidas. Al cerrar la sesión, los vectores se destruyen.

```python
client = chromadb.Client()  # Se borra al finalizar la ejecución
```

**Modo Persistente (disco local):** escribe el estado de la base de datos en una estructura de archivos físicos.

```python
client = chromadb.PersistentClient(path="./ortelana_vectordb")
```

**Volatilidad en Google Colab:** Colab elimina el sistema de archivos local (`/content`) cada vez que la sesión se desconecta. Para que el índice vectorial de Ortelana sobreviva entre clases y no requiera regenerar los embeddings continuamente, montamos el almacenamiento directamente sobre Google Drive:

```python
from google.colab import drive
import chromadb

drive.mount('/content/drive')

RUTA_PERSISTENTE = "/content/drive/MyDrive/Ortelana_VectorDB"
client = chromadb.PersistentClient(path=RUTA_PERSISTENTE)
```

### Operaciones Transaccionales en Caliente con `.upsert()`

En el catálogo de Ortelana, las descripciones de las telas pueden mantenerse relativamente estables, pero el stock cambia constantemente. Si intentamos usar el método habitual `.add()` sobre un ID que ya existe, la base arrojará una excepción de clave duplicada. Para evitar esto usamos `.upsert()` (*Update + Insert*):

```python
coleccion.upsert(
    ids=["G1-TELA-001"],
    documents=["Denim pesado de 12 oz, reingreso de stock con nuevo acabado soft."],
    metadatas=[{
        "sucursal": "central_buenos_aires",
        "en_stock": True,
        "categoria": "pesados"
    }]
)
```

¿Qué ocurre por detrás? Si el ID no existe, se inserta. Si ya existe, ChromaDB actualiza atómicamente el texto, regenera únicamente el embedding de ese documento y actualiza sus metadatos, dejando intacto el resto de los miles de vectores del catálogo.

### Del Mantenimiento del Conocimiento a las Reglas de Negocio

Una base de datos vectorial persistente permite actualizar documentos individuales sin reconstruir todo el índice, manteniendo sincronizados datos dinámicos como la disponibilidad de un producto. Sin embargo, esto no significa que la base vectorial reemplace al sistema transaccional de la empresa.

El metadato `en_stock` permite que la búsqueda semántica descarte productos agotados desde el comienzo, pero no representa el stock real ni la cantidad exacta de unidades disponibles. Si un cliente solicita una cantidad determinada de rollos o desea concretar una reserva, la respuesta ya no depende únicamente de la base vectorial — es imprescindible consultar el ERP.

> La base vectorial puede convertirse en la fuente de verdad del conocimiento semántico, pero no necesariamente en la fuente de verdad del estado transaccional del negocio.

---

## 4. Búsqueda Híbrida y Filtrado por Metadatos

Cuando el índice vectorial no dispone de información suficiente sobre el estado del negocio, aparece la **ceguera de filtrado**: la búsqueda semántica identifica correctamente los documentos más parecidos a la consulta, pero no puede determinar por sí sola si esos documentos cumplen reglas de negocio como disponibilidad de stock, sucursal o estado comercial.

Existen dos formas de resolver esto, y la diferencia entre ambas es puramente de **orden de operaciones**:

**Post-filtering** (lo que hacíamos con FAISS): primero se ejecuta la búsqueda semántica sobre **todo** el índice vectorial, y luego los resultados obtenidos se envían a otro componente del sistema para aplicar las restricciones que el índice no puede evaluar por sí mismo.

**Pre-filtering** (lo que hace ChromaDB de forma nativa): antes de calcular las distancias vectoriales, el propio motor reduce el espacio de búsqueda aplicando reglas lógicas sobre los metadatos. La similitud semántica ya no se calcula sobre todo el catálogo, sino únicamente sobre el subconjunto de documentos que cumplen las condiciones establecidas.

**Para que esto no quede como una caja negra, tracemos el flujo con números concretos.** Supongamos que el catálogo de Ortelana tiene 500 telas y un cliente de la sucursal de Córdoba pregunta por algo "fresco para un vestido, con stock disponible":

```
POST-FILTERING (enfoque ineficiente):
Consulta → calcular similitud coseno contra las 500 telas → devolver el top-10
         → recién ahí filtrar en Python por sucursal y stock
                                                            ↑ ya se calculó todo, para nada

PRE-FILTERING (ChromaDB nativo):
Consulta → aplicar where: sucursal='cordoba' AND stock=True → quedan 8 telas candidatas
         → calcular similitud coseno SOLO sobre esas 8
         → devolver el top-2
```

Con 500 telas y un filtro que deja 8 candidatas, el pre-filtering le ahorra al motor **492 cálculos de similitud coseno** que en el enfoque post-filtering se hacen y se descartan. En producción, con catálogos de millones de documentos, esa diferencia es la que separa una respuesta en milisegundos de una respuesta en minutos — es lo que hace viable la búsqueda híbrida a escala.

### Sintaxis de Consulta con Operadores Lógicos Nativos

ChromaDB utiliza operadores como `$and`, `$or`, `$eq` (igual) o `$ne` (distinto) para estructurar restricciones complejas:

```python
resultados = coleccion.query(
    query_texts=["Necesito una tela bien resistente para confeccionar camperas"],
    n_results=3,
    where={
        "$and": [
            {"sucursal": {"$eq": "central_buenos_aires"}},
            {"en_stock": {"$eq": True}}
        ]
    }
)
```

**La Regla del Arquitecto para Metadatos:** definir como metadato todo campo del negocio sobre el cual el usuario o la aplicación necesite aplicar un filtro duro (ej: `sucursal`, `en_stock`, `categoria`). Los campos puramente descriptivos o narrativos deben permanecer dentro del documento textual para ser procesados por la búsqueda semántica — nunca al revés. Si un alumno escribe código Python condicional para filtrar los resultados después de la consulta, está haciendo post-filtering manual: el sistema va a funcionar, pero de forma ineficiente.

---

## 5. Puesta en Común: La Fricción de los Datos en el Mundo Real

Hasta aquí hicimos una evolución directa y simplificada: entendimos que teníamos dos mundos muy distintos, donde una consulta llega como un chat desestructurado y requiere procesamiento complejo para obtener información desde los sistemas de Ortelana. Pero en la realidad, el primer trabajo fuerte es entender cómo integrar distintas fuentes de información y partes del negocio, desde clientes y proveedores hasta los sistemas internos de la empresa que no siempre trabajan al unísono.

Cuando Ortelana Textil decide implementar IA, se encuentra con que su información no está centralizada. A lo largo de los años, las distintas secciones de la empresa (Ventas, Producción, Logística) han adoptado sistemas en tiempos y con tecnologías radicalmente diferentes. Esta diversidad genera discrepancias estructurales graves, colisiones de IDs primarios y tipificaciones erróneas.

Para solucionar este caos, es necesario diseñar un flujo **ETL (Extract, Transform, Load)** que actúe como capa de integración:

1. **Extracción y Normalización:** el script lee la información de estos sistemas dispares, estandariza las llaves y tipos de datos, y resuelve la colisión inminente de identificadores agregando prefijos según el sistema de origen (ej: `TELA-001` → `G1-TELA-001`).
2. **Enriquecimiento:** se inyectan metadatos clave para identificar de qué área de la empresa o tecnología proviene el dato.

### El Problema de los "Casi Duplicados" y la Purga Semántica

Incluso con una estructura normalizada a la fuerza, el software tradicional falla al detectar colisiones semánticas entre distintos departamentos. Para consolidar esta información dispar, el sistema realiza una **Purga Semántica** apoyándose en la base de datos vectorial:

1. Se inicializa la base, se vectorizan las descripciones provenientes de todos los sistemas y se calcula la distancia angular en vivo.
2. Aquellos registros cuya similitud sea extrema son detectados automáticamente como duplicados por significado y se eliminan algorítmicamente (mediante `.delete()`) para dejar una única versión de la verdad.

### El Manejo de Alias: Nombres Técnicos, Comerciales y Regionalismos

Este proceso semántico no solo sirve para borrar duplicados, sino para resolver un problema de negocio aún más complejo: los **alias**. Producción registra el artículo con su nombre técnico internacional ("Denim 12 oz"), pero Ventas o los clientes lo llaman "Jean", "Vaquero" o "Mezclilla".

Para un sistema de búsqueda tradicional, un cliente preguntando por "Vaquero" recibiría un error, porque el sistema interno solo tiene registrado "Denim". Con la arquitectura vectorial, los embeddings comprenden la relación de significado entre estas palabras. El proceso ETL inteligente mapea estas diferencias: mantiene el ID único del producto, pero guarda los distintos términos como **alias** dentro de los metadatos.

El resultado final es un **Súper-Catálogo unificado**, limpio, rico en alias comerciales y agnóstico a las tecnologías de origen. Este es el cimiento sobre el cual la arquitectura RAG y los LLMs pueden operar eficientemente y sin alucinar.

---

## 6. Recuperación de Datos y Devolución al Usuario Final: del JSON al Chat

Una vez que el catálogo de Ortelana está unificado, purgado semánticamente mediante la detección de alias, y la base de datos vectorial está persistida en disco, el sistema está listo para ejecutar consultas.

A través de una búsqueda híbrida (similitud semántica + filtrado estricto de metadatos), el motor logra extraer con precisión la información exacta que resuelve la necesidad. Sin embargo, tras evaluar este sistema de recuperación (*Retrieval*), surge un nuevo problema de negocio: la salida cruda que devuelve ChromaDB es un objeto informático estructurado, típicamente en formato JSON.

Si un usuario final pregunta por WhatsApp *"¿Tienen telas abrigadas en la sucursal sur?"*, es inaceptable que reciba como respuesta un bloque de código con arrays, distancias matemáticas y llaves de metadatos anidadas.

```python
{
  'documents': [['Seda natural satinada, caída fluida...']],
  'metadatas': [[{'en_stock': True, 'sucursal': 'cordoba', 'linea_textil': 'alta_costura'}]],
  'distances': [[0.214]],
  'ids': [['TELA-002']]
}
```

El sistema de recuperación funciona a la perfección: es rápido, persistente, respeta el stock y la sucursal. Pero un diccionario de Python no es una respuesta comercial. Nos falta un componente que tome este dato preciso y lo traduzca en lenguaje natural, cordial y persuasivo para el cliente.

Ese es exactamente el punto donde termina el trabajo de esta unidad: tenemos una base de conocimiento sólida, consultable, filtrable y persistente. Lo que hace falta —un orquestador que conecte esta recuperación con un modelo de lenguaje para generar la respuesta final— es el tema central de la próxima unidad.

---

## Bibliografía

- Lewis, M., et al. (2020). *Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks.*
- Alammar, J., & Grootendorst, M. (2024). *Hands-On Large Language Models.* O'Reilly. Capítulos 5 y 6: "Text Embeddings and Vector Spaces" / "Vector Databases".
- Johnson, J., et al. (2019). *Billion-scale similarity search with GPUs.* IEEE Transactions on Big Data.
- Documentación oficial de ChromaDB — docs.trychroma.com
- Documentación oficial de FAISS — github.com/facebookresearch/faiss/wiki
