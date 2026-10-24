"""Preferencias locales del usuario (tema, idioma, etc.).

Se guardan en ``data/preferences.json`` dentro del directorio persistente de
la aplicación (ver :mod:`core.paths`), por lo que sobreviven a reinicios y
actualizaciones.
"""
from __future__ import annotations

import json

from core.paths import DATA_DIR

_FILE = DATA_DIR / "preferences.json"


def load() -> dict:
    try:
        with open(_FILE, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save(**values) -> dict:
    data = load()
    data.update(values)
    try:
        _FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(_FILE, "w", encoding="utf-8") as fh:
            json.dump(data, fh, ensure_ascii=False, indent=2)
    except OSError:
        # Las preferencias no son críticas: si no se pueden escribir, la app
        # sigue funcionando con los valores de la sesión.
        pass
    return data
