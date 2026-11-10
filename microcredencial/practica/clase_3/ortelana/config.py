"""
Configuración: API keys desde .env y detección del proveedor de LLM.

La API key NUNCA se escribe en el código: se lee de un archivo .env que
está en el .gitignore. En el repositorio solo se sube .env.example.
"""

import os
import ssl
from pathlib import Path
from typing import Optional

# Carpeta raíz del proyecto (clase_3/), un nivel arriba de este paquete.
RAIZ_PROYECTO = Path(__file__).resolve().parent.parent

# Orden de preferencia: se usa el primer proveedor que tenga una key válida.
PROVEEDORES = (
    ("gemini", "GEMINI_API_KEY"),
    ("openai", "OPENAI_API_KEY"),
    ("groq", "GROQ_API_KEY"),
)


def cargar_env() -> None:
    """Carga el .env de la raíz del proyecto. Usa python-dotenv si está instalado."""
    env_path = RAIZ_PROYECTO / ".env"
    try:
        from dotenv import load_dotenv
        load_dotenv(env_path)
    except ImportError:
        # Alternativa sin librerías: leer el archivo línea por línea.
        if env_path.exists():
            for linea in env_path.read_text(encoding="utf-8").splitlines():
                linea = linea.strip()
                if linea and not linea.startswith("#") and "=" in linea:
                    clave, valor = linea.split("=", 1)
                    os.environ.setdefault(clave.strip(), valor.strip().strip("'\""))


def crear_contexto_ssl() -> ssl.SSLContext:
    """Contexto SSL con verificación. Usa `certifi` si está instalado (útil en macOS)."""
    try:
        import certifi
        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def key_valida(variable: str) -> Optional[str]:
    """Devuelve la API key si está configurada y no es el texto de ejemplo del .env.example."""
    valor = os.getenv(variable, "").strip()
    if not valor or "tu_api_key" in valor:
        return None
    return valor


def detectar_proveedor() -> Optional[tuple[str, str]]:
    """Devuelve (proveedor, api_key) del primero disponible, o None si no hay ninguno."""
    for nombre, variable in PROVEEDORES:
        key = key_valida(variable)
        if key:
            return nombre, key
    return None


cargar_env()
SSL_CONTEXT = crear_contexto_ssl()
