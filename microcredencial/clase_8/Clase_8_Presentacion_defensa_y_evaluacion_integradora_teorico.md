# Clase 8: Presentación, Defensa y Evaluación Integradora

**Programa:** Microcredencial #2 — Diseño de Aplicaciones Inteligentes
**Unidad 3 · Diseño de Proyectos con IA**

**Objetivo técnico:** Explicar y demostrar la solución diseñada durante las 8 clases (problema, arquitectura, evidencia, límites y próximos pasos), defenderla con evidencia concreta ante preguntas técnicas y funcionales, y cerrar el recorrido con una retrospectiva honesta.

**Origen reutilizado:** IADS 3, clase 16 (cierre general del cuatrimestre) y clase 15 (formato de defensa y criterios de "listo para defender"), adaptados al nivel y al alcance de la Micro 2 — una defensa de prototipo conceptual o funcional, no de un sistema en producción.

---

## Estructura de la clase

| Bloque | Contenido |
|---|---|
| **Bloque 1** | Cómo explicar una solución inteligente |
| **Bloque 2** | Demo convincente vs. solución productiva — la diferencia que hay que saber explicar |
| **Bloque 3** | Formato de la defensa y criterio de "listo para defender" |
| **Bloque 4** | Defensa del Trabajo Final Aplicado |
| **Cierre** | Retrospectiva y evolución posible |

---

## Bloque 1: Cómo explicar una solución inteligente

Después de 7 clases construyendo, la última habilidad a practicar es **comunicar** lo construido de forma clara y honesta. Toda buena explicación de una solución con IA sigue el mismo recorrido:

1. **El problema:** ¿qué necesidad real detectamos en la Clase 1? ¿Por qué importa?
2. **El usuario:** ¿quién vive ese problema hoy, y cómo lo resuelve sin el sistema?
3. **La arquitectura:** ¿cómo está armado el sistema? (concepto → workflow → RAG → agente → integración)
4. **La evidencia:** ¿qué datos concretos muestran que funciona? (matriz de pruebas, resultados antes/después, guardrails probados)
5. **Los límites:** ¿qué NO hace el sistema? ¿Qué se dejó explícitamente fuera de alcance?
6. **Los próximos pasos:** si este proyecto siguiera creciendo, ¿qué faltaría para que fuera una solución productiva real?

> **Por qué el orden importa:** empezar por el problema y el usuario, no por la tecnología. Un jurado o cliente se convence primero de que el problema es real y relevante — recién después de eso, la arquitectura técnica tiene sentido.

---

## Bloque 2: Demo convincente vs. solución productiva

No es lo mismo mostrar algo que "se ve bien" que mostrar algo diseñado con responsabilidad. Saber explicar esta diferencia es, en sí mismo, parte de la evaluación.

| | Demo convincente | Solución con criterio productivo |
|---|---|---|
| **Qué muestra** | El caso feliz, cuidadosamente elegido | El caso feliz + al menos un caso límite |
| **Qué oculta** | Los errores, ensayado de antemano | Nada — muestra también dónde falla y por qué |
| **Evidencia** | "Miren, funciona" | Matriz de pruebas, resultados documentados |
| **Honestidad** | Puede simular certeza que no tiene | Reconoce límites explícitamente |

**Retroalimentación técnica, funcional y ética:** al recibir feedback (del docente o de otros grupos), distinguir tres planos: ¿la arquitectura es sólida? (técnico), ¿resuelve el problema del usuario? (funcional), ¿tiene riesgos de privacidad, sesgo o manipulación? (ético). Una buena defensa contempla los tres, no solo el primero.

---

## Bloque 3: Formato de la defensa

### Estructura sugerida (15 minutos por grupo)

```
[0:00 – 3:00] Presentación del problema y la arquitectura
→ Una oración por componente: problema, usuario, arquitectura (concepto → workflow → RAG → agente)

[3:00 – 9:00] Demostración del flujo principal
→ Mostrar el prototipo funcionando de punta a punta con 2-3 consultas reales
→ Mostrar una conversación con memoria/estado si el proyecto lo incluye

[9:00 – 12:00] Evidencia de robustez y diseño responsable
→ Un intento de manipulación (Red Teaming) y cómo lo bloquea el guardrail
→ Un caso fuera de dominio y cómo responde ("no tengo información" en vez de inventar)
→ Mostrar la matriz de pruebas y la ficha de riesgos de la Clase 7

[12:00 – 15:00] Cierre y preguntas
→ Límites conocidos y próximos pasos
→ Preguntas del docente
```

### El criterio de "listo para defender"

Un proyecto está listo para la defensa si cumple estos mínimos — todo lo demás (empaquetado avanzado, más de un guardrail, métricas extensas) suma pero no es bloqueante:

- La solución responde de punta a punta al menos las consultas típicas del caso propio.
- Al menos una parte de la respuesta se fundamenta en datos reales (no solo en lo que el modelo "ya sabía").
- El agente o workflow usa al menos una herramienta o validación real.
- Al menos un guardrail está activo y se puede demostrar en vivo.
- Existe una matriz de pruebas y una ficha de riesgos, aunque sean breves.

> **El consejo más importante:** demostrar algo simple que funciona bien vale más que demostrar algo ambicioso que falla a mitad de la presentación. Si hay dudas sobre si algo va a funcionar en vivo, no incluirlo en la demo — o tener un plan B (una captura de pantalla del resultado esperado).

### Preguntas típicas de evaluación

- ¿Por qué eligieron este problema? ¿Cómo saben que es real?
- ¿Qué parte del sistema es determinista y cuál usa un LLM? ¿Por qué esa decisión?
- ¿Qué pasa si el sistema recibe una consulta para la que no tiene información?
- ¿Qué guardrail implementaron y qué tipo de ataque bloquea?
- ¿Cuál es la hipótesis más riesgosa del proyecto? ¿Qué pasaría si resulta falsa?
- Si tuvieran una clase más, ¿en qué invertirían el tiempo?

---

## Bloque 4: Defensa del Trabajo Final Aplicado

Cada grupo presenta su Trabajo Final Aplicado siguiendo el formato del Bloque 3: propuesta de solución, prototipo conceptual o funcional, evidencia de validación, límites y próximos pasos.

**Lo que se evalúa (recordar los pesos del sistema de evaluación de la microcredencial):**

- **Ejercicios prácticos (40%):** las entregas acumuladas de las Clases 1 a 7 (ficha de oportunidad, concepto de solución, prototipo, hitos 1 y 2, prototipo enriquecido, versión candidata).
- **Trabajo Final Aplicado (60%):** la propuesta de solución, el prototipo, la demostración, la fundamentación técnica y la defensa de hoy.
- **Promoción:** calificación mínima de 7/10 y cumplimiento del 100% de las entregas, con defensa obligatoria.

---

## Cierre: Retrospectiva y evolución posible

Para cerrar la microcredencial, cada grupo responde brevemente:

- ¿Qué parte del proyecto quedó más sólida? ¿Cuál quedó más frágil?
- ¿Qué aprendizaje técnico se llevan que no esperaban al empezar?
- Si este proyecto tuviera que convertirse en una solución productiva real, ¿cuáles serían los tres pasos siguientes? (pensar en los temas deliberadamente acotados en esta microcredencial: RAG avanzado, despliegue completo, AIOps, arquitecturas multiagente complejas — el camino natural de profundización).

> Este es el cierre de la Microcredencial #2. El caso propio que cada grupo construyó desde la Clase 1 —y las decisiones de arquitectura, grounding y agentes que fue incorporando— queda como base sobre la cual seguir construyendo, dentro o fuera de este programa.

---

## Bibliografía de la clase

- Mollick, E. (2024). *Co-Intelligence: Living and Working with AI.* Portfolio (cierre conceptual del programa).
- Huyen, C. (2025). *AI Engineering: Building Applications with Foundation Models.* O'Reilly (lectura de referencia para quien continúe profundizando).
