"""
Microcredencial Clase 3 — Primer prototipo operativo de Ortelana
================================================================
Corre el lote de prueba (datos/lote_prueba.json) contra el modelo y muestra:
  1. El resultado de cada caso.
  2. La tabla del lote, con el formato de la Entrega 2 (Parte C).
  3. Una demostración de errores: qué etapa frena cada respuesta rota.

Uso:
    python app.py             → prompt v1
    python app.py v2          → otra versión del prompt (prompts/extraccion_v2.txt)
"""

import json
import sys

from ortelana.config import RAIZ_PROYECTO, detectar_proveedor
from ortelana.extractor import PROMPT_VERSION, aplicar_reglas, procesar_mensaje, validar_respuesta

# Respuestas rotas típicas de un LLM, para ver qué etapa frena cada una (no requiere API).
RESPUESTAS_ROTAS = [
    ("Texto antes del JSON", '¡Claro! Acá tenés los datos: {"intencion": "ALTA_DISTRIBUIDOR"}'),
    ("Bloque de código Markdown", '```json\n{"intencion": "ALTA_DISTRIBUIDOR"}\n```'),
    ("Intención inventada", '{"intencion": "APROBAR_VIP_ORO", "razon_social": "Modas del Sur"}'),
    ("CUIT sin guiones y facturación como texto",
     '{"intencion": "ALTA_DISTRIBUIDOR", "cuit": "30715896326", "facturacion_anual": "mucha"}'),
    ("Formato perfecto, CUIT inválido",
     '{"intencion": "ALTA_DISTRIBUIDOR", "cuit": "20-12345678-9"}'),
]


def titulo(texto: str) -> None:
    print("\n" + "=" * 78 + f"\n{texto}\n" + "=" * 78)


def correr_lote(version: str) -> list[tuple[int, str, dict]]:
    lote = json.loads((RAIZ_PROYECTO / "datos" / "lote_prueba.json").read_text(encoding="utf-8"))
    resultados = []
    for i, caso in enumerate(lote, start=1):
        print(f"\n▶ Caso {i} — {caso['tipo']}")
        print(f"  Qué observar: {caso['observar']}")
        resultado = procesar_mensaje(caso["mensaje"], caso["simulacion"], version)
        print(json.dumps({k: v for k, v in resultado.items() if k != "respuesta_cruda"}, indent=2, ensure_ascii=False))
        resultados.append((i, caso["tipo"], resultado))
    return resultados


def imprimir_tabla(resultados: list[tuple[int, str, dict]]) -> None:
    titulo("TABLA DEL LOTE (formato de la Entrega 2, Parte C)")
    print(f"{'#':<3}{'Tipo':<14}{'Intención':<26}{'¿JSON válido?':<15}{'Etapa que falló'}")
    for i, tipo, r in resultados:
        intencion = r.get("extraccion", {}).get("intencion", "—")
        json_ok = "No" if r.get("error") in ("FORMATO", "COMUNICACION") else "Sí"
        print(f"{i:<3}{tipo:<14}{intencion:<26}{json_ok:<15}{r.get('error', '—')}")


def demostrar_errores() -> None:
    titulo("DEMOSTRACIÓN DE ERRORES — ¿qué etapa frena cada respuesta rota?")
    for descripcion, texto in RESPUESTAS_ROTAS:
        r = validar_respuesta(texto)
        if r["ok"]:
            r = aplicar_reglas(r["extraccion"])
        print(f"\n▶ {descripcion}")
        print(f"  Respuesta: {texto!r}")
        print(f"  Resultado: {r.get('error', 'OK')} → {r.get('detalle', '')}")


if __name__ == "__main__":
    version = sys.argv[1] if len(sys.argv) > 1 else PROMPT_VERSION
    titulo(f"MICROCREDENCIAL CLASE 3 — EXTRACCIÓN ESTRUCTURADA (prompt {version})")
    imprimir_tabla(correr_lote(version))
    demostrar_errores()

    if detectar_proveedor() is None:
        print("\n⚠️  MODO SIMULACIÓN: el lote usó respuestas de ejemplo. Para usar un LLM real:")
        print("    cp .env.example .env   y completá GEMINI_API_KEY (gratis en https://aistudio.google.com)")
