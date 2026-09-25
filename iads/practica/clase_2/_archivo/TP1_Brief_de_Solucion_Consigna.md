# TP1 — Brief de Solución Técnica

**Materia:** Desarrollo de Sistemas de IA (IADS 3)
**Entrega:** Antes del inicio de la Clase 3
**Formato:** Un archivo Markdown (`.md`) por grupo
**Modalidad:** Grupal (según los grupos ya conformados)

---

## Contexto

Durante las Clases 1 y 2 trabajamos con el caso de Ortelana Textil para aprender a modelar agentes con PEAS extendido, distinguir qué partes de un sistema deben ser deterministas y cuáles probabilísticas, y diseñar una Matriz de Intenciones que traduce lenguaje natural en acciones de backend.

Este TP1 es el primer paso de un **Proyecto Integrador** que va a acompañarlos durante todo el cuatrimestre. No se entrega una sola vez y se olvida: cada clase nueva le va a agregar una capa real de implementación (APIs, embeddings, RAG, agentes, deploy) sobre la base que diseñen ahora. Por eso, la calidad de este diseño inicial importa — es la base sobre la que van a programar después.

---

## Consigna

Elijan **un dominio propio** (no pueden usar Ortelana Textil — ese es el caso de la cátedra). Puede ser una idea propia o alguno de estos, a modo de guía:

| Dominio | Caso de uso sugerido | Por qué funciona bien |
|---|---|---|
| Legal | Consulta de jurisprudencia | Alto volumen de documentos + lenguaje técnico |
| Salud | Asistente de pre-diagnóstico | Complejidad cognitiva alta |
| Finanzas | Análisis de balances | Datos estructurados + lenguaje natural |
| Retail | Asistente de stock y pedidos | Latencia + volumen |
| RRHH | Clasificación de CVs | Volumen repetitivo + criterios complejos |

Diseñen un sistema de IA que resuelva un problema real dentro de ese dominio, aplicando todo lo visto en Clases 1 y 2.

---

## Estructura del entregable

El archivo `.md` debe tener estas 7 secciones, en este orden:

**1. Problema identificado**
¿Qué señal de dolor resuelve — volumen repetitivo, carga cognitiva o latencia humana? ¿Quién lo sufre, con qué frecuencia, y qué consecuencia tiene no resolverlo?

**2. Usuario objetivo**
¿Quién usa el sistema? ¿Qué hace hoy sin la IA?

**3. PEAS extendido (5 pilares)**

| Pilar | Aplicado a su sistema |
|---|---|
| Performance | |
| Environment | |
| Actuators | |
| Sensors | |
| Base de Conocimiento | |

**4. Matriz de Mapeo de Intenciones**
Mínimo 3 filas, cada una con Riesgo de Negocio justificado (BAJO / MEDIO / ALTO):

| Entrada del usuario (caos) | Intención (LLM) | Parámetros (LLM) | Acción de backend (determinista) | Riesgo |
|---|---|---|---|---|
| | | | | |

**5. Decisión técnica**
Para cada parte del sistema: ¿es determinista (código/SQL) o probabilística (LLM)? Justificar cada elección — no alcanza con decir "esto lo hace el LLM", hay que explicar por qué.

**6. Flujo de valor simplificado**
Una línea: `Input del usuario → paso 1 → paso 2 → Output → valor generado`

**7. Hipótesis más riesgosa**
Una sola oración: la suposición que, si resulta falsa, hace colapsar todo el diseño.

---

## Criterios de evaluación

| Criterio | Puntos |
|---|---|
| Problema y usuario claramente identificados, con señal de dolor justificada | 15 |
| PEAS extendido completo y coherente con el dominio elegido | 20 |
| Matriz de Intenciones con al menos 3 casos y riesgo bien justificado | 25 |
| Decisión técnica (determinista vs. LLM) argumentada, no solo enunciada | 25 |
| Hipótesis más riesgosa identifica un supuesto real y relevante | 15 |
| **Total** | **100** |

> [!NOTE]
> Este TP1 no requiere código ni implementación — es un documento de diseño. La parte de programación (consumo de API, extracción estructurada) se suma en la Clase 3 sobre esta misma base.

---

## Preguntas frecuentes

**¿Podemos cambiar de dominio después de entregar el TP1?**
No es recomendable — el proyecto integrador se construye sobre esta base durante todo el cuatrimestre. Elijan un dominio que les interese sostener 16 clases.

**¿Tiene que ser 100% realista?**
No hace falta que sea una empresa real. Sí tiene que ser un caso concreto y creíble — evitar planteos demasiado abstractos ("una IA que ayuda a la gente") que no permitan definir un PEAS específico.

**¿Cuántas páginas tiene que tener?**
No hay mínimo de extensión. Alcanza con completar las 7 secciones con contenido específico, no genérico.
