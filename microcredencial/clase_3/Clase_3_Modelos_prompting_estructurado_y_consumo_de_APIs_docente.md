# Machete Docente — Clase 3: Modelos, Prompting Estructurado y Consumo de APIs

**Microcredencial #2 · Unidad 2 · Clase 3 de 8**

---

## Planificación de tiempos

| Bloque | Duración sugerida | Objetivo del bloque |
|---|---|---|
| Bloque 1 | 15 min | El rol del modelo fundacional dentro de la arquitectura |
| Bloque 2 | 45 min | Prompting estructurado: zero-shot, few-shot, reglas de JSON confiable |
| Bloque 3 | 30 min | API: request/response, `.env`, manejo de errores |
| Bloque 4 | 50 min | Laboratorio: primer prototipo con API real |
| Cierre | 10 min | Entrega y conexión con Clase 4 |

---

## Bloque 1 — Guion rápido (15 min)

- Conectar con la Clase 2: "definimos que el LLM es el intérprete, no la autoridad. Hoy vemos cómo se implementa eso técnicamente."
- Frase ancla: "comprar un motor en vez de fundirlo" — usarla tal cual, es fácil de recordar.

---

## Bloque 2 — Prompting estructurado (45 min)

Orden sugerido:

0. Proyectar el contrato de Ortelana v1 y mostrar de dónde sale cada parte: las intenciones de la Matriz de la Entrega 1 y los campos del paso 2 del journey (5 min). Frase ancla: "el prompt no se inventa, se deriva del diseño".
1. Mostrar en vivo un zero-shot simple funcionando (8 min).
2. Romperlo con un input ambiguo, por ejemplo "¿Tienen stock de denim?" (debería dar `FUERA_DE_ALCANCE`) — reconectar con el laboratorio de la Clase 2 (5 min).
3. Mostrar cómo few-shot lo arregla, agregando 2 o 3 ejemplos (8 min).
4. Las 4 reglas del JSON confiable — escribirlas en el pizarrón mientras se explican, dejarlas visibles el resto de la clase (9 min).
5. Validación en dos niveles: `json.loads()` ("¿es JSON?") y Pydantic ("¿cumple el contrato?") (10 min). Mostrar el modelo `ExtraccionOrtelana` y romperlo en vivo con `"intencion": "VIP_ORO"` y con un CUIT sin guiones. Usar solo lo básico de Pydantic: `BaseModel`, tipos, `Optional`, `Literal` y `Field(pattern=..., ge=...)`. Cerrar con la diferencia entre contrato y regla de negocio: el formato del CUIT lo valida Pydantic, el dígito verificador lo valida la regla de la Clase 2, que hoy se aplica después de Pydantic.

**No profundizar** en Chain-of-Thought como técnica separada — se puede nombrar en una oración si surge la pregunta, pero no es contenido evaluable de esta microcredencial.

---

## Bloque 3 — API (30 min)

- Diagrama simple en el pizarrón: caja "tu código" ↔ caja "API del modelo", con flechas request/response.
- Demostración en vivo de `.env` + `load_dotenv()` — mostrar la API key en el archivo y remarcar el `.gitignore`.
- Ejemplo de manejo de errores con los tres `except` separados: comunicación, formato (`json.JSONDecodeError`) y contrato (`ValidationError`). Preguntar al grupo qué haría en cada caso antes de mostrarlo: reintentar, ajustar el prompt o revisar la extracción.

**Punto de seguridad no negociable:** remarcar en voz alta que ninguna API key debe aparecer hardcodeada en ningún notebook o script que se entregue.

---

## Bloque 4 — Laboratorio (50 min)

- Dar 30 minutos para que cada grupo arme su script contra la API elegida (o Postman si prefieren no programar todavía).
- Correr el test de estrés con los 3 mensajes del teórico — pedir que cada grupo comparta cuántas fallas tuvo y si fallaron en `json.loads()` o en Pydantic.
- Cerrar el test con la pregunta del CUIT `20-34556789-2`: pasa Pydantic pero lo frena la regla. Remarcar que hacen falta las dos capas.
- Pedir que corran el caso de manipulación 3 o 4 veces: con Gemini 2.5 Flash, la intención cambia entre corridas (`ALTA_DISTRIBUIDOR` o `FUERA_DE_ALCANCE`) aun con temperatura 0. Es el gancho para el prompt v2 y para la Clase 4: Pydantic no puede detectar una intención equivocada pero válida.
- **Cada alumno con su propia API key.** La capa gratuita de Gemini devuelve 429 después de unas decenas de pedidos; si comparten una key, el laboratorio se traba. Pedir que creen la key en AI Studio antes de la clase.
- Últimos 10 minutos: puesta en común de qué técnica (zero-shot/few-shot) usó cada grupo y por qué.

**Si el grupo tiene bajo dominio técnico:** ofrecer un notebook base con el script ya armado y que solo completen el prompt y el mensaje de prueba — la evaluación es sobre el diseño del prompt y el contrato, no sobre escribir el cliente de la API desde cero.

---

## Cierre (10 min)

- Repasar el resumen.
- Confirmar entrega: prototipo operativo (prompt + llamada + JSON validado) con el contrato documentado.
- Anticipar Clase 4: "hoy logramos una llamada aislada. La próxima clase la convertimos en una secuencia de pasos — un workflow real."

---

## Notas para el docente

- Si algún grupo no consigue una API key a tiempo, permitir que use Ollama local o que documente el prototipo con capturas de Postman contra un modelo gratuito — lo evaluable es el diseño del contrato, no el proveedor.
- El "Test de estrés" es el gancho pedagógico más importante del bloque 4 — no saltearlo aunque falte tiempo, porque conecta directamente con la necesidad de validación que se profundiza más adelante en la cursada.
