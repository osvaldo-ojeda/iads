"""
Microcredencial Clase 4 — Workflow de onboarding de Ortelana
============================================================
Corre el lote de prueba (datos/lote_prueba.json) por el workflow y muestra:
  1. La TRAZA de cada caso: qué pasos recorrió y dónde se detuvo.
  2. La decisión humana (paso 10) y la respuesta redactada (paso 11).
  3. La tabla del lote: estado obtenido vs. estado esperado.

Uso:
    python app.py              → el Jefe de Administración (simulado) aprueba todos los legajos
    python app.py --manual     → vos hacés de Jefe de Administración: aprobás o rechazás cada legajo
    python app.py lcel         → el paso 2 como cadena de LangChain (requiere langchain-core)
"""

import json
import sys

from ortelana.config import RAIZ_PROYECTO, detectar_proveedor
from ortelana.redactor import formatear_pesos
from ortelana.workflow import registrar_decision, workflow_onboarding

ICONOS = {"LLM": "🤖", "Regla": "📏", "Herramienta": "🔧", "Humano": "🙋", "LLM + Regla": "🤖📏"}


def titulo(texto: str) -> None:
    print("\n" + "=" * 78 + f"\n{texto}\n" + "=" * 78)


def cargar_lote() -> list[dict]:
    return json.loads((RAIZ_PROYECTO / "datos" / "lote_prueba.json").read_text(encoding="utf-8"))


def mostrar_traza(resultado: dict) -> None:
    for p in resultado["traza"]:
        print(f"  {ICONOS.get(p['tipo'], '  ')} [{p['paso']:>3}] {p['nombre']:<40} {p['resultado']}")


def decidir(legajo: dict, manual: bool) -> tuple[bool, str, str | None]:
    """Paso 10. Devuelve (aprobada, aprobador, motivo)."""
    rec = legajo["recomendacion"]
    print(f"\n  📋 LEGAJO — {legajo['razon_social']} ({legajo['cuit']})")
    print(f"     Recomendación: categoría {rec['categoria']}, {rec['plazo_dias']} días, "
          f"límite {formatear_pesos(rec['limite_credito'])}  [{', '.join(rec['reglas_aplicadas'])}]")
    for obs in rec["observaciones"]:
        print(f"     · {obs}")
    for alerta in legajo["alertas"]:
        print(f"     ⚠️  {alerta}")

    if not manual:
        return True, "Jefe de Administración (simulado)", None
    opcion = input("     ¿Aprobás? [s/n]: ").strip().lower()
    if opcion.startswith("s"):
        return True, "Jefe de Administración", None
    return False, "Jefe de Administración", input("     Motivo del rechazo: ").strip() or "Sin motivo informado"


def correr_lote(manual: bool) -> list[tuple[str, str, str]]:
    filas = []
    for i, caso in enumerate(cargar_lote(), start=1):
        titulo(f"Caso {i} — {caso['tipo']}")
        print(f"  Mensaje: {caso['mensaje']}")
        print(f"  Qué observar: {caso['observar']}\n")

        resultado = workflow_onboarding(caso["mensaje"], caso["simulacion"])
        mostrar_traza(resultado)
        estado_workflow = resultado["estado"]

        if resultado["estado"] == "PENDIENTE_APROBACION":
            aprobada, aprobador, motivo = decidir(resultado["legajo"], manual)
            resultado = registrar_decision(resultado, aprobada, aprobador, motivo)
            print()
            mostrar_traza({"traza": resultado["traza"][-2:]})

        print(f"\n  ➜ Estado final: {resultado['estado']}")
        if "motivo" in resultado:
            print(f"    Motivo: {resultado['motivo']}")
        for alerta in resultado.get("alertas", []):
            print(f"    ⚠️  {alerta}")
        if "respuesta" in resultado:
            print(f"\n  ✉️  Respuesta al distribuidor [{resultado['respuesta']['origen']}]:")
            for linea in resultado["respuesta"]["texto"].splitlines():
                print(f"     {linea}")

        filas.append((caso["tipo"], caso["estado_esperado"], estado_workflow))
    return filas


def imprimir_tabla(filas: list[tuple[str, str, str]]) -> None:
    titulo("TABLA DEL LOTE — ¿el workflow se detuvo donde tenía que detenerse?")
    print(f"{'#':<3}{'Caso':<28}{'Esperado':<24}{'Obtenido':<24}")
    for i, (tipo, esperado, obtenido) in enumerate(filas, start=1):
        marca = "✅" if esperado == obtenido else "❌"
        print(f"{i:<3}{tipo:<28}{esperado:<24}{obtenido:<22}{marca}")
    print("\n(El estado es el del workflow, antes de la decisión humana del paso 10.)")


def demo_lcel() -> None:
    try:
        from ortelana.cadena_lcel import crear_cadena, extraer
    except ImportError:
        print("Falta LangChain:  pip install langchain-core")
        return

    lote = cargar_lote()
    cadena, origen = crear_cadena([c["simulacion"] for c in lote])
    titulo(f"PASO 2 COMO CADENA LCEL:  plantilla | modelo | parser   ({origen})")
    for caso in lote:
        r = extraer(cadena, caso["mensaje"])
        intencion = r.get("extraccion", {}).get("intencion", "—")
        print(f"  {caso['tipo']:<28} → {intencion:<22} {'OK' if r['ok'] else r['error']}")
    print("\nMismo resultado que extractor.py: el framework cambió la plomería, no la validación.")


if __name__ == "__main__":
    if "lcel" in sys.argv[1:]:
        demo_lcel()
        sys.exit()

    titulo("MICROCREDENCIAL CLASE 4 — WORKFLOW DE ONBOARDING")
    imprimir_tabla(correr_lote(manual="--manual" in sys.argv[1:]))

    if detectar_proveedor() is None:
        print("\n⚠️  MODO SIMULACIÓN: la extracción usó respuestas de ejemplo y la redacción, la plantilla fija.")
        print("    Para usar un LLM real:  cp .env.example .env   y completá GEMINI_API_KEY")
