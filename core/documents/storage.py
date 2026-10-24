"""Rutas y utilidades para el almacenamiento de documentos generados
(exportaciones de listados a Excel/PDF).
"""
import os
import re

from core.paths import BASE_DIR, GENERATED_DIR

PROJECT_ROOT = str(BASE_DIR)
ASSETS_DIR = str(BASE_DIR / "assets")
# En Android GENERATED_DIR vive fuera del directorio de la app para sobrevivir
# a las actualizaciones; en escritorio coincide con <proyecto>/assets.
EXPORTES_DIR = str(GENERATED_DIR / "exports")


def ensure_dirs():
    os.makedirs(EXPORTES_DIR, exist_ok=True)


def _slug(value: str) -> str:
    value = str(value or "doc")
    return re.sub(r"[^A-Za-z0-9_.-]", "_", value)


def exportes_path(filename: str) -> str:
    """Ruta absoluta dentro de ``assets/exports`` para el nombre indicado."""
    ensure_dirs()
    return os.path.join(EXPORTES_DIR, _slug(filename))


def relative(path: str) -> str:
    """Ruta relativa a la raíz del proyecto (para mostrar al usuario)."""
    try:
        rel = os.path.relpath(path, PROJECT_ROOT)
    except ValueError:
        return path
    # En Android los documentos generados quedan fuera de la raíz del código.
    return path if rel.startswith("..") else rel
