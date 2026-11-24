"""
Microcredencial Clase 5 — Workflow de onboarding de Ortelana + RAG sobre la normativa
=====================================================================================
El workflow de la Clase 4, con una novedad: las consultas normativas ya no se derivan con un
texto fijo. Se responden con RAG (embeddings + ChromaDB + LLM), citando la regla.

Uso:
    python app.py                 → corre el lote (12 casos) y muestra la traza de cada uno
    python app.py --manual        → igual, pero vos aprobás o rechazás cada legajo
    python app.py buscar "texto"  → busca en la normativa y muestra la similitud de cada regla
    python app.py buscar "texto" --todas   → lo mismo SIN el filtro vigente=True (aparecen las derogadas)
    python app.py comparar        → la misma pregunta sin RAG y con RAG (Entrega 3, B.3)
    python app.py telas           → demo del teórico: el catálogo de telas ("busco algo fresco...")
    python app.py telas "texto"   → buscar una tela
    python app.py indexar         → rehace los índices (el paso OFFLINE de RAG)
    python app.py lcel            → el paso 2 como cadena de LangChain (de la Clase 4)
"""

import json
import sys

from ortelana.config import RAIZ_PROYECTO, detectar_proveedor
from ortelana.redactor import formatear_pesos
from ortelana.workflow import registrar_decision, workflow_onboarding

ICONOS = {"LLM": "🤖", "Regla": "📏", "Herramienta": "🔧", "Humano": "🙋", "LLM + Regla": "🤖📏", "RAG": "📚"}


def titulo(texto: str) -> None:
    print("\n" + "=" * 78 + f"\n{texto}\n" + "=" * 78)


def cargar_json(nombre: str) -> list[dict]:
    return json.loads((RAIZ_PROYECTO / "datos" / nombre).read_text(encoding="utf-8"))


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
    for i, caso in enumerate(cargar_json("lote_prueba.json"), start=1):
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
            r = resultado["respuesta"]
            print(f"\n  ✉️  Respuesta al distribuidor [{r['origen']}]:")
            for linea in r["texto"].splitlines():
                print(f"     {linea}")
            if r.get("fuentes"):
                print(f"     📚 Fuentes: {', '.join(r['fuentes'])}")

        filas.append((caso["tipo"], caso["estado_esperado"], estado_workflow))
    return filas


def imprimir_tabla(filas: list[tuple[str, str, str]]) -> None:
    titulo("TABLA DEL LOTE — ¿el workflow se detuvo donde tenía que detenerse?")
    print(f"{'#':<4}{'Caso':<30}{'Esperado':<24}{'Obtenido':<24}")
    for i, (tipo, esperado, obtenido) in enumerate(filas, start=1):
        marca = "✅" if esperado == obtenido else "❌"
        print(f"{i:<4}{tipo:<30}{esperado:<24}{obtenido:<22}{marca}")
    print("\n(El estado es el del workflow, antes de la decisión humana del paso 10.)")


# ── Demos de RAG ─────────────────────────────────────────────────────────────

def mostrar_busqueda(documentos, umbral: float) -> None:
    for d in documentos:
        m = d.metadata
        marca = "✅" if m["supera_umbral"] else "✗ "
        vigencia = "" if m.get("vigente", True) else f"  ⚠️ DEROGADA (v{m['version']})"
        print(f"  {marca} {m['similitud']:.2f}  {m['id']:<16} {m['titulo']}{vigencia}")
    print(f"  {'─' * 60}\n  Umbral: {umbral}. Solo los ✅ se usan como contexto.")


def demo_buscar(consulta: str, todas: bool) -> None:
    from ortelana.base_conocimiento import UMBRAL_SIMILITUD, abrir, buscar
    filtro = None if todas else {"vigente": True}
    titulo(f"BÚSQUEDA EN LA NORMATIVA  ·  filtro: {filtro or 'ninguno (incluye derogadas)'}")
    print(f"  Consulta: {consulta}\n")
    mostrar_busqueda(buscar(abrir("normativa"), consulta, filtro=filtro), UMBRAL_SIMILITUD)


def demo_comparar() -> None:
    from ortelana.rag import responder_consulta, responder_sin_grounding
    for p in cargar_json("preguntas_comparacion.json"):
        titulo(f"❓ {p['pregunta']}")
        sin = responder_sin_grounding(p["pregunta"], p["simulacion_sin_rag"])
        con = responder_consulta(p["pregunta"])
        print(f"  ❌ SIN grounding [{sin['origen']}]:\n     {sin['texto']}\n")
        print(f"  ✅ CON RAG [{con['origen']}]  fuentes: {', '.join(con['fuentes']) or '—'}\n     {con['texto']}\n")
        print(f"  👀 {p['que_mirar']}")


def demo_telas(consulta: str | None) -> None:
    from ortelana.base_conocimiento import UMBRAL_SIMILITUD, abrir, buscar, cargar_corpus
    base = abrir("telas")
    if consulta:
        titulo(f"CATÁLOGO DE TELAS  ·  {consulta}")
        mostrar_busqueda(buscar(base, consulta), UMBRAL_SIMILITUD)
        return

    titulo("DEMO 1 · Buscar por PALABRA vs. buscar por SIGNIFICADO")
    consulta = "busco algo fresco para un vestido de verano"
    print(f"  Consulta: {consulta}\n")
    por_palabra = [d.metadata["titulo"] for d in cargar_corpus("telas") if "fresco" in d.page_content.lower()]
    print(f"  🔤 Por palabra (como un WHERE descripcion LIKE '%fresco%'): {por_palabra or 'NINGÚN resultado'}\n")
    print("  🧭 Por significado (embeddings):")
    mostrar_busqueda(buscar(base, consulta), UMBRAL_SIMILITUD)

    titulo("DEMO 2 · Filtrado híbrido: significado + metadato")
    consulta = "Necesito una tela abrigada y gruesa para camperas de invierno"
    print(f"  Consulta: {consulta}\n\n  Sin filtro:")
    mostrar_busqueda(buscar(base, consulta), UMBRAL_SIMILITUD)
    print("\n  Con filtro {'en_stock': True}:")
    mostrar_busqueda(buscar(base, consulta, filtro={"en_stock": True}), UMBRAL_SIMILITUD)
    print("\n  El paño de lana es lo más parecido, pero no hay stock: el filtro lo descarta.")


def demo_indexar() -> None:
    from ortelana.base_conocimiento import cargar_corpus, indexar
    titulo("PASO OFFLINE · corpus → embeddings → ChromaDB")
    for nombre in ("normativa", "telas"):
        base = indexar(nombre)
        print(f"  ✅ {nombre:<10} {len(cargar_corpus(nombre))} documentos → {base._collection.count()} vectores en indice_chroma/")


def demo_lcel() -> None:
    try:
        from ortelana.cadena_lcel import crear_cadena, extraer
    except ImportError:
        print("Falta LangChain:  pip install langchain-core")
        return
    lote = cargar_json("lote_prueba.json")
    cadena, origen = crear_cadena([c["simulacion"] for c in lote])
    titulo(f"PASO 2 COMO CADENA LCEL:  plantilla | modelo | parser   ({origen})")
    for caso in lote:
        r = extraer(cadena, caso["mensaje"])
        intencion = r.get("extraccion", {}).get("intencion", "—")
        print(f"  {caso['tipo']:<28} → {intencion:<22} {'OK' if r['ok'] else r['error']}")
    print("\nMismo resultado que extractor.py: el framework cambió la plomería, no la validación.")


def _texto_despues_de(comando: str) -> str | None:
    args = [a for a in sys.argv[sys.argv.index(comando) + 1:] if not a.startswith("--")]
    return " ".join(args) or None


if __name__ == "__main__":
    args = sys.argv[1:]
    if "lcel" in args:
        demo_lcel()
    elif "buscar" in args:
        demo_buscar(_texto_despues_de("buscar") or "¿El flete a Córdoba lo pagan ustedes?", "--todas" in args)
    elif "comparar" in args:
        demo_comparar()
    elif "telas" in args:
        demo_telas(_texto_despues_de("telas"))
    elif "indexar" in args:
        demo_indexar()
    else:
        titulo("MICROCREDENCIAL CLASE 5 — WORKFLOW DE ONBOARDING + RAG")
        imprimir_tabla(correr_lote(manual="--manual" in args))

    if detectar_proveedor() is None and "indexar" not in args:
        print("\n⚠️  MODO SIMULACIÓN: sin API key, los LLM se simulan. La búsqueda semántica (embeddings,")
        print("    ChromaDB, filtro y umbral) corre de verdad. Para usar un LLM real:")
        print("    cp .env.example .env   y completá GEMINI_API_KEY")
