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

1. Mostrar en vivo un zero-shot simple funcionando (10 min).
2. Romperlo con un input ambiguo — reconectar con el laboratorio de la Clase 2 ("Modas del Sur") (5 min).
3. Mostrar cómo few-shot lo arregla, agregando 2 ejemplos (10 min).
4. Las 4 reglas del JSON confiable — escribirlas en el pizarrón mientras se explican, dejarlas visibles el resto de la clase (15 min).
5. Mencionar Pydantic como profundización opcional, sin dar la clase completa de validación — 1 frase basta: "si querés blindarlo más, este es el nombre a buscar."

**No profundizar** en Chain-of-Thought como técnica separada — se puede nombrar en una oración si surge la pregunta, pero no es contenido evaluable de esta microcredencial.

---

## Bloque 3 — API (30 min)

- Diagrama simple en el pizarrón: caja "tu código" ↔ caja "API del modelo", con flechas request/response.
- Demostración en vivo de `.env` + `load_dotenv()` — mostrar la API key en el archivo y remarcar el `.gitignore`.
- Ejemplo rápido de manejo de errores con `try/except` sobre `json.loads()`.

**Punto de seguridad no negociable:** remarcar en voz alta que ninguna API key debe aparecer hardcodeada en ningún notebook o script que se entregue.

---

## Bloque 4 — Laboratorio (50 min)

- Dar 30 minutos para que cada grupo arme su script contra la API elegida (o Postman si prefieren no programar todavía).
- Correr el test de estrés con los 3 mensajes del teórico — pedir que cada grupo comparta cuántas fallas tuvo.
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
