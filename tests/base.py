"""Utilidades compartidas por las pruebas.

- Apunta la base de datos a un archivo temporal.
- Si faker/flet no están instalados, instala stubs mínimos para que las
  pruebas se puedan ejecutar en entornos sin todas las dependencias.
"""
import sys
import tempfile
import types
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def ensure_faker():
    try:
        import faker  # noqa: F401
        return
    except ImportError:
        pass

    class _FakeMeta(type):
        def __getattr__(cls, name):
            return lambda *a, **k: None

    class Faker(metaclass=_FakeMeta):
        def __init__(self, *a, **k):
            pass

        def __getattr__(self, name):
            if name == "date_time_between":
                import datetime
                return lambda **k: datetime.datetime(2026, 1, 1)
            return lambda *a, **k: "x"

    module = types.ModuleType("faker")
    module.Faker = Faker
    sys.modules["faker"] = module


def ensure_flet():
    try:
        import flet  # noqa: F401
        return
    except ImportError:
        pass

    class _Any:
        def __getattr__(self, name):
            return _Any()

        def __call__(self, *a, **k):
            return _Any()

    module = types.ModuleType("flet")
    module.__getattr__ = lambda name: _Any()
    sys.modules["flet"] = module


def use_temp_db():
    """Apunta la BD a un archivo temporal y devuelve su ruta."""
    import configs.database as dbcfg

    tmp = tempfile.mktemp(suffix=".db")
    dbcfg.DATABASE["SQLITE"]["PATH"] = tmp
    return tmp


def reset_db():
    """Cierra y reinicia la conexión global (aislar módulos de prueba)."""
    import core.database as db

    if db._connection is not None:
        try:
            db._connection.close()
        except Exception:
            pass
    db._connection = None
    db._initialized = False
