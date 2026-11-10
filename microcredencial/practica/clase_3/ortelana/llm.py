"""
Llamada a la API real del modelo (request → response).

Soporta Gemini y el formato compatible con OpenAI (OpenAI y Groq).
El proveedor y el modelo se eligen por variables de entorno: el resto
del sistema no depende de cuál se use.
"""

import json
import os
import time
import urllib.error
import urllib.request

from .config import SSL_CONTEXT

REINTENTOS = 3
CODIGOS_REINTENTABLES = (429, 503)  # 429: límite de uso · 503: servidor saturado


def _post_json(url: str, payload: dict, headers: dict) -> dict:
    """Request HTTP POST: manda un JSON y devuelve el JSON de la respuesta."""
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
    )
    with urllib.request.urlopen(req, context=SSL_CONTEXT, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _llamar_gemini(system: str, usuario: str, api_key: str) -> str:
    modelo = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"
    payload = {
        "systemInstruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": [{"text": usuario}]}],
        "generationConfig": {"temperature": 0, "responseMimeType": "application/json"},
    }
    data = _post_json(url, payload, {"x-goog-api-key": api_key})
    return data["candidates"][0]["content"]["parts"][0]["text"]


def _llamar_chat_completions(system: str, usuario: str, api_key: str, url: str, modelo: str) -> str:
    """Formato compatible con OpenAI (sirve para OpenAI y para Groq)."""
    payload = {
        "model": modelo,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": usuario},
        ],
        "temperature": 0,
        "response_format": {"type": "json_object"},
    }
    data = _post_json(url, payload, {"Authorization": f"Bearer {api_key}"})
    return data["choices"][0]["message"]["content"]


def llamar_modelo(system: str, usuario: str, proveedor: str, api_key: str) -> str:
    """Una sola llamada. Devuelve el TEXTO crudo del modelo (todavía no es un dict)."""
    if proveedor == "gemini":
        return _llamar_gemini(system, usuario, api_key)
    if proveedor == "openai":
        return _llamar_chat_completions(
            system, usuario, api_key,
            "https://api.openai.com/v1/chat/completions",
            os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        )
    if proveedor == "groq":
        return _llamar_chat_completions(
            system, usuario, api_key,
            "https://api.groq.com/openai/v1/chat/completions",
            os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
        )
    raise ValueError(f"Proveedor desconocido: {proveedor}")


def llamar_con_reintentos(system: str, usuario: str, proveedor: str, api_key: str) -> str:
    """
    Un error de comunicación transitorio (503, 429) se reintenta con espera creciente (2s, 4s).
    Una key inválida (401/403) o un pedido mal armado (400) NO se reintenta: fallaría igual.
    """
    for intento in range(1, REINTENTOS + 1):
        try:
            return llamar_modelo(system, usuario, proveedor, api_key)
        except urllib.error.HTTPError as e:
            if e.code in CODIGOS_REINTENTABLES and intento < REINTENTOS:
                espera = 2 ** intento
                print(f"  ⏳ HTTP {e.code} (intento {intento}/{REINTENTOS}). Reintento en {espera}s...")
                time.sleep(espera)
                continue
            raise
    raise RuntimeError("No debería llegar acá")
