"""
El workflow del onboarding: la llamada suelta de la Clase 3 convertida en una SECUENCIA de pasos.

El orden de los pasos lo fija EL DESARROLLADOR (este archivo). El modelo no decide qué paso
sigue: solo interviene en los pasos marcados [LLM]. Esa es la diferencia con un agente (Clase 6).

    Mensaje
      │
      ├─ 1  Acuse de recibo ................................ [Regla]
      ├─ 2  Extraer intención y datos ...................... [LLM]       ┐
      ├─ 4  Validar el contrato (json.loads + Pydantic) .... [Regla]     ├ Clase 3 (extractor.py)
      ├─ 5  Validar el CUIT (dígito verificador) ........... [Regla]     ┘
      │       └─ ✋ si falla → REVISION_HUMANA
      ├─    Enrutar según la intención ..................... [Regla]
      │       └─ si no es ALTA_DISTRIBUIDOR → DERIVADO (respuesta fija)
      ├─    ¿Están los datos mínimos? ...................... [Regla]
      ├─ 6  Verificar documentación (NOR-DOC) .............. [Regla]
      ├─ 7  Consultar el sistema de gestión ................ [Herramienta]
      ├─ 8  Determinar categoría, plazo y límite ........... [Regla]
      │       └─ ✋ si faltan datos o documentos → PENDIENTE (se le pide al distribuidor)
      ├─ 9  Armar el legajo ................................ [Regla]
      ├─ 10 ✋ Aprobación del Jefe de Administración ......... [Humano]    → PENDIENTE_APROBACION
      └─ 11 Redactar la respuesta .......................... [LLM]       → registrar_decision()

El paso 3 (identificar qué documento es cada adjunto) queda fuera: hoy trabajamos solo con texto,
así que usamos los documentos que el distribuidor DICE que adjunta.

Estados posibles al terminar:
    REVISION_HUMANA        → algo falló (extracción o CUIT): una persona revisa el mensaje original
    DERIVADO               → no es un alta: respuesta fija según la Matriz de Intenciones
    PENDIENTE              → faltan datos o documentos: se le pide al distribuidor (no se rechaza)
    PENDIENTE_APROBACION   → legajo completo, esperando al Jefe de Administración (NOR-APROB)
    APROBADA / RECHAZADA   → la persona decidió y se redactó la respuesta
"""

from typing import Optional

from .extractor import procesar_mensaje
from .herramientas import consultar_sistema_gestion
from .redactor import NOMBRES_FALTANTES, formatear_pesos, redactar_respuesta
from .reglas import determinar_condiciones, normalizar_categoria, verificar_documentacion

ACUSE = "Recibimos tu mensaje. Te respondemos en el día."

# Matriz de Intenciones (Entrega 1, B.4): respuestas fijas del MVP para lo que no es un alta.
RESPUESTAS_FIJAS = {
    "CONSULTA_NORMATIVA": "Gracias por tu consulta. La derivamos al área comercial, que te va a responder "
                          "con las condiciones vigentes.",
    "FUERA_DE_ALCANCE": "Este canal es para altas de distribuidores. Para pedidos, stock o reclamos, "
                        "escribinos a ventas@ortelana.com.ar.",
    "CONSULTA_ESTADO": "Derivamos tu consulta a Administración para que revise el estado de tu solicitud.",
    "COMPLETAR_DOCUMENTACION": "Recibimos la documentación. Administración la va a asociar a tu solicitud.",
}

DATOS_MINIMOS = ("razon_social", "cuit", "facturacion_anual")


class Traza:
    """Registro de qué pasó en cada paso. Sirve para depurar y para la Prueba de falla (A.3)."""

    def __init__(self):
        self.pasos: list[dict] = []

    def registrar(self, paso: str, tipo: str, nombre: str, resultado: str) -> None:
        self.pasos.append({"paso": paso, "tipo": tipo, "nombre": nombre, "resultado": resultado})


def _terminar(traza: Traza, estado: str, **extra) -> dict:
    return {"estado": estado, "traza": traza.pasos, **extra}


def workflow_onboarding(mensaje: str, simulacion: Optional[str] = None) -> dict:
    """
    Ejecuta el journey de onboarding hasta el punto de control humano (paso 10).
    `simulacion` es la respuesta de ejemplo del LLM que se usa cuando no hay API key.
    """
    traza = Traza()

    # ── Paso 1 · Acuse [Regla] ───────────────────────────────────────────────
    traza.registrar("1", "Regla", "Acuse de recibo", ACUSE)

    # ── Pasos 2, 4 y 5 · Extraer y validar [LLM + Regla] — el componente de la Clase 3 ──
    r = procesar_mensaje(mensaje, simulacion)
    if not r["ok"]:
        if r["error"] == "REGLA":
            traza.registrar("5", "Regla", "Validar CUIT", f"❌ {r['detalle']}")
            motivo = r["detalle"]
        else:
            traza.registrar("2-4", "LLM + Regla", "Extraer y validar contrato", f"❌ {r['error']}: {r['detalle']}")
            motivo = f"Falló la extracción ({r['error']})"
        # ✋ Punto de control: no seguimos con datos que no son confiables
        return _terminar(traza, "REVISION_HUMANA", motivo=motivo, mensaje_original=mensaje)

    datos = r["extraccion"]
    traza.registrar("2", "LLM", "Extraer intención y datos", f"intención = {datos['intencion']}")
    traza.registrar("4-5", "Regla", "Validar contrato y CUIT", f"✅ {r.get('regla_cuit', 'OK')}")

    # ── Enrutamiento [Regla]: el CÓDIGO decide el camino según la intención ────
    if datos["intencion"] != "ALTA_DISTRIBUIDOR":
        respuesta = RESPUESTAS_FIJAS[datos["intencion"]]
        traza.registrar("—", "Regla", "Enrutar por intención", f"{datos['intencion']} → respuesta fija")
        return _terminar(traza, "DERIVADO", datos=datos, respuesta={"texto": respuesta, "origen": "RESPUESTA FIJA"})
    traza.registrar("—", "Regla", "Enrutar por intención", "ALTA_DISTRIBUIDOR → flujo de alta")

    # Alertas para quien revisa: no frenan el flujo, quedan en el legajo
    alertas = []
    categoria_pedida = normalizar_categoria(datos["categoria_solicitada"])
    if datos["categoria_solicitada"] and categoria_pedida is None:
        alertas.append(f"Pidió una categoría inexistente ('{datos['categoria_solicitada']}'): "
                       "posible intento de saltear la validación. Se ignora el pedido.")

    # ── ¿Datos mínimos? + Paso 6 · Documentación (NOR-DOC) [Regla] ────────────
    datos_faltantes = [c for c in DATOS_MINIMOS if datos[c] is None]
    docs_faltantes = verificar_documentacion(datos["documentos_mencionados"])
    traza.registrar("6", "Regla", "Verificar documentación (NOR-DOC)",
                    "✅ completa" if not docs_faltantes
                    else f"faltan: {', '.join(docs_faltantes)} (obligatoria solo para cuenta corriente)")

    if datos_faltantes:
        # Sin CUIT no se puede consultar el sistema y sin facturación no se puede calcular la categoría.
        traza.registrar("—", "Regla", "Datos mínimos", f"✋ faltan: {', '.join(datos_faltantes)}")
        return _pedir_faltantes(traza, datos, datos_faltantes + docs_faltantes, alertas)

    # ── Paso 7 · Sistema de gestión [Herramienta] ─────────────────────────────
    cliente = consultar_sistema_gestion(datos["cuit"])
    traza.registrar("7", "Herramienta", "Consultar sistema de gestión",
                    f"cliente existente, {cliente['antiguedad_meses']} meses, deuda vencida "
                    f"{cliente['dias_deuda_vencida']} días" if cliente["es_cliente"] else "distribuidor nuevo")

    # ── Paso 8 · Categoría, plazo y límite [Regla] ────────────────────────────
    condiciones = determinar_condiciones(datos["facturacion_anual"], cliente, datos["plazo_solicitado_dias"])
    traza.registrar("8", "Regla", "Determinar condiciones",
                    f"categoría {condiciones['categoria']}, {condiciones['plazo_dias']} días, "
                    f"límite {formatear_pesos(condiciones['limite_credito'])} ({', '.join(condiciones['reglas_aplicadas'])})")

    if categoria_pedida and categoria_pedida != condiciones["categoria"]:
        alertas.append(f"Pidió categoría {categoria_pedida}; según la normativa le corresponde "
                       f"{condiciones['categoria']}.")

    # La documentación solo es obligatoria para cuenta corriente (NOR-DOC)
    if condiciones["cuenta_corriente"] and docs_faltantes:
        traza.registrar("—", "Regla", "Punto de control NOR-DOC", "✋ cuenta corriente sin documentación completa")
        return _pedir_faltantes(traza, datos, docs_faltantes, alertas)

    # ── Paso 9 · Legajo [Regla] ───────────────────────────────────────────────
    legajo = {
        "razon_social": datos["razon_social"],
        "cuit": datos["cuit"],
        "facturacion_anual": datos["facturacion_anual"],
        "cliente": cliente,
        "recomendacion": condiciones,
        "alertas": alertas,
        "mensaje_original": mensaje,
    }
    traza.registrar("9", "Regla", "Armar legajo", f"{len(alertas)} alerta(s) para quien revisa")

    # ── Paso 10 · ✋ Aprobación humana (NOR-APROB) ─────────────────────────────
    traza.registrar("10", "Humano", "Aprobación del Jefe de Administración", "⏸ esperando decisión")
    return _terminar(traza, "PENDIENTE_APROBACION", legajo=legajo)


def _pedir_faltantes(traza: Traza, datos: dict, faltantes: list[str], alertas: list[str]) -> dict:
    """Estado PENDIENTE: no se rechaza, se le pide al distribuidor lo que falta (NOR-DOC)."""
    decision = {
        "tipo": "PENDIENTE",
        "razon_social": datos["razon_social"],
        "faltantes": [NOMBRES_FALTANTES.get(f, f) for f in faltantes],
    }
    respuesta = redactar_respuesta(decision)
    traza.registrar("11", "LLM", "Redactar pedido de faltantes", respuesta["origen"])
    return _terminar(traza, "PENDIENTE", datos=datos, faltantes=faltantes, alertas=alertas, respuesta=respuesta)


def registrar_decision(resultado: dict, aprobada: bool, aprobador: str, motivo: Optional[str] = None) -> dict:
    """
    Pasos 10 y 11: la persona decide sobre el legajo y el LLM redacta la respuesta.
    Solo se puede llamar sobre un resultado en PENDIENTE_APROBACION.
    """
    if resultado["estado"] != "PENDIENTE_APROBACION":
        raise ValueError(f"No hay nada que aprobar: el estado es {resultado['estado']}")
    if not aprobada and not motivo:
        raise ValueError("Un rechazo necesita un motivo para poder comunicarlo")

    legajo = resultado["legajo"]
    traza = Traza()
    traza.pasos = list(resultado["traza"])
    traza.registrar("10", "Humano", "Aprobación del Jefe de Administración",
                    f"{'✅ aprobada' if aprobada else '❌ rechazada'} por {aprobador}")

    if aprobada:
        decision = {"tipo": "APROBADA", "razon_social": legajo["razon_social"], **legajo["recomendacion"]}
        decision.pop("observaciones")  # son notas internas para quien revisa, no para el distribuidor
    else:
        decision = {"tipo": "RECHAZADA", "razon_social": legajo["razon_social"], "motivo": motivo}

    respuesta = redactar_respuesta(decision)
    traza.registrar("11", "LLM", "Redactar respuesta", respuesta["origen"])
    return _terminar(traza, "APROBADA" if aprobada else "RECHAZADA",
                     legajo=legajo, aprobador=aprobador, respuesta=respuesta)
