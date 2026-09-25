# TP Integrador — Microcredencial #2: Diseño de Aplicaciones Inteligentes

Trabajo Práctico entregable y progresivo. Cada entrega suma una capa real de la solución sobre la anterior, siempre sobre el **caso propio** que cada grupo elige en la Entrega 1. Ortelana Textil es el caso guía de la cátedra, no el entregable.

| Entrega | Clases | Qué construye | Carpeta |
|---|---|---|---|
| **Entrega 1** | Clases 1 y 2 | Del diagnóstico al concepto de solución: ficha de oportunidad + user journey + Matriz de Intenciones | [`entrega_1/`](entrega_1/) |
| **Entrega 2** | Clase 3 | Primer prototipo operativo: prompt versionado + llamada a API real + salida JSON validada | [`entrega_2/`](entrega_2/) |
| **Entrega 3** | Clases 4, 5 y 6 | Workflow + RAG con corpus propio + primer agente (Hitos 1 y 2) | [`entrega_3/`](entrega_3/) |
| **Entrega 4** | Clase 7 | Versión candidata integrada de punta a punta + guardrails + ficha de riesgos | [`entrega_4/`](entrega_4/) |

Cada carpeta contiene:
- `TP_EntregaN_Consigna.md` — la consigna para los alumnos (estructura, qué se entrega, rúbrica).
- `guia_correccion_EntregaN.md` — material docente, no compartir.

## Por qué 4 entregas y no 8

El TP podría haberse estructurado con una entrega por clase. Se optó por **4 entregas que agrupan las clases según la capa de la arquitectura que construyen**, por las siguientes razones:

### 1. Una entrega evaluable debe producir un artefacto completo

Una entrega por clase generaría fragmentos sin contexto propio: la Clase 1 entregaría una ficha de oportunidad sin solución, la Clase 3 daría un script suelto sin saber a qué workflow pertenece. Ninguno de esos fragmentos responde a la pregunta *"¿esto resuelve algo?"*. Las 4 entregas agrupan las clases hasta que hay una capa completa que el alumno puede defender de forma autónoma.

### 2. Las entregas siguen la arquitectura del sistema

| Entrega | Capa | Razonamiento |
|---|---|---|
| **E1** | Diseño conceptual | Las Clases 1 y 2 forman un ciclo completo: identificar el problema (C1) + diseñar la solución (C2). Sin el concepto de solución, la ficha de oportunidad no tiene destino. |
| **E2** | Primera implementación | La Clase 3 es una unidad de acción completa: prompt + API + JSON validado. El primer artefacto que "corre". |
| **E3** | El sistema completo | Las Clases 4, 5 y 6 construyen la misma cosa en capas sucesivas: el workflow sin RAG alucina, el RAG sin workflow es una llamada suelta, el agente es la versión dinámica del workflow. Separar estas tres clases en tres entregas fragmentaría un sistema que necesita sus tres piezas para funcionar. |
| **E4** | Validación y calidad | La Clase 7 no agrega funcionalidad nueva — evalúa y refuerza lo construido. Su artefacto solo tiene sentido cuando ya existe algo completo que evaluar. |

### 3. Las entregas se alinean con los hitos del propio programa

Los materiales de la microcredencial ya definen dos checkpoints intermedios explícitos:

- **Hito 1** al cierre de la Clase 4: *concepto validado + workflow ejecutable*
- **Hito 2** al cierre de la Clase 6: *esquema técnico del agente*

Las Entregas 3 y 4 se alinean exactamente con esos hitos. Durante las Clases 4, 5 y 6 el avance es visible en el historial de commits del repositorio — no hace falta una entrega formal en cada clase para que el docente vea el progreso.

### 4. La coherencia transversal como competencia evaluada

Una de las competencias centrales de la microcredencial es que el alumno pueda **trazar una línea coherente desde el problema hasta el sistema**: ¿el prompt de la E2 refleja las intenciones diseñadas en la E1? ¿el agente de la E3 usa las herramientas que el diseño inicial planteaba? Esa coherencia solo se puede evaluar con un proyecto que crece clase a clase — no con siete ejercicios aislados.

---

> **En una oración:** las 4 entregas agrupan las 8 clases según la capa de la arquitectura que construyen — diseño, prototipo, sistema y validación — de forma que cada entrega produce un artefacto que el alumno puede defender de forma autónoma y que el docente puede evaluar con coherencia respecto al proyecto completo.

## Sistema de evaluación

| Componente | Peso en la nota final |
|---|---|
| Ejercicios prácticos (Entregas 1 a 4) | 40% |
| Trabajo Final Aplicado (Clase 8) | 60% |
| Promoción | Mínimo 7/10 + 100% de entregas + defensa obligatoria |

Dentro del 40% de ejercicios prácticos, cada entrega tiene **peso igual** (10% de la nota final cada una). El docente puede ajustar este criterio.

## Entrega

Un único repositorio Git **público** por grupo (GitHub o GitLab). Se entrega solo el link, sin gestión de accesos. Como es público, **ninguna clave ni API key entra al repo** — `.env` en `.gitignore` desde el primer commit, solo se sube `.env.example` sin valores. Cada entrega agrega archivos y commits al mismo repo — el historial incremental es parte de la evaluación.

## Material de clase

Los teóricos y guiones docentes de cada clase están en [`../clase_1/`](../clase_1/), [`../clase_2/`](../clase_2/), etc.
