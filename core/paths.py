"""Rutas de la aplicación, separando recursos de solo lectura y datos.

En Android, ``serious_python`` descomprime la app en
``getApplicationSupportDirectory()/flet/app`` y **borra y vuelve a extraer**
ese directorio en cada instalación/actualización. Por eso la base de datos y
los documentos generados (PDF, XML, exportaciones, certificados) no pueden
vivir dentro de la app: se guardan en el directorio de trabajo persistente
``getApplicationSupportDirectory()/data``, que serious_python conserva entre
actualizaciones.

En escritorio ambas rutas coinciden con la raíz del proyecto para mantener el
comportamiento actual.
"""
import os
import sys
from pathlib import Path

# Raíz del código de la app (recursos estáticos de solo lectura).
BASE_DIR = Path(__file__).resolve().parent.parent


def is_android() -> bool:
    return sys.platform == "android"


def _runtime_dir() -> Path:
    if is_android():
        # serious_python hace chdir a <support>/data antes de iniciar Python.
        return Path(os.getcwd())
    return BASE_DIR


# Directorio persistente para datos del usuario.
DATA_DIR = _runtime_dir()

# Recursos de solo lectura empaquetados con la app (logo, íconos, etc.).
ASSETS_DIR = BASE_DIR / "assets"

# Documentos generados en tiempo de ejecución (persistentes).
GENERATED_DIR = DATA_DIR / "assets"
