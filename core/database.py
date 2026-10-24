
import importlib
import pkgutil
import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path

from configs.database import DATABASE
from core.paths import BASE_DIR, DATA_DIR

_connection = None
_initialized = False
_write_lock = threading.RLock()
_tls = threading.local()


def commit(conn):
    """Confirma una escritura, salvo que estemos dentro de una transacción."""
    if getattr(_tls, "tx_depth", 0) == 0:
        conn.commit()


@contextmanager
def transaction(conn=None):
    """Agrupa varias escrituras en una única transacción atómica.

    Los métodos del ORM usan commit(), que es no-op dentro de la transacción,
    así que si algo falla se revierte todo el bloque.
    """
    conn = conn or get_connection()
    _tls.tx_depth = getattr(_tls, "tx_depth", 0) + 1
    with _write_lock:
        try:
            yield conn
            if _tls.tx_depth == 1:
                conn.commit()
        except Exception:
            if _tls.tx_depth == 1:
                conn.rollback()
            raise
        finally:
            _tls.tx_depth -= 1


def get_connection():
    global _connection, _initialized

    if _connection is not None:
        return _connection

    engine = DATABASE.get("ENGINE", "sqlite").lower()

    if engine == "sqlite":
        _connection = _connect_sqlite()
    elif engine == "mysql":
        _connection = _connect_mysql()
    else:
        raise RuntimeError(f"Unsupported database engine: {engine}")

    if not _initialized:
        _initialized = True
        init_db(_connection)

    return _connection


# =========================
# SQLITE
# =========================
def _connect_sqlite():
    cfg = DATABASE.get("SQLITE", {})
    path_cfg = cfg.get("PATH", "data/fleting.db")

    db_path = DATA_DIR / Path(path_cfg)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


# =========================
# MYSQL
# =========================
def _connect_mysql():
    # Pendiente de implementación. Antes devolvía None (y colapsaba en
    # init_db); ahora falla de forma explícita para no ocultar el problema.
    raise NotImplementedError(
        "El motor MySQL aún no está implementado. Usa ENGINE=sqlite."
    )


# =========================
# INITIALIZATION & MIGRATIONS
# =========================
def _iter_modules(package_dir, exclude=()):
    """Importa y devuelve (nombre, módulo) de un paquete en orden alfabético."""
    package_dir = Path(package_dir)
    package_name = package_dir.name

    infos = sorted(pkgutil.iter_modules([str(package_dir)]), key=lambda i: i.name)
    for info in infos:
        if info.name in exclude:
            continue
        module = importlib.import_module(f"{package_name}.{info.name}")
        yield info.name, module


def init_db(conn=None):
    """Aplica migraciones y seeds pendientes usando el framework unificado."""
    if conn is None:
        conn = get_connection()

    from core.migrations import (
        apply_migration,
        applied_migrations,
        ensure_migrations_table,
    )

    # ── Migraciones ──────────────────────────────────────────────────────
    ensure_migrations_table()
    applied = applied_migrations()

    for name, module in _iter_modules(BASE_DIR / "migrations", exclude={"__init__", "initial"}):
        if name in applied:
            continue
        apply_migration(name, module.up)

    # ── Seeds (idempotentes) ─────────────────────────────────────────────
    # 'initial.py' está obsoleto (usa columnas que ya no existen) y se omite.
    for name, module in _iter_modules(BASE_DIR / "seeds", exclude={"__init__", "initial"}):
        if name in applied:
            continue
        apply_migration(name, module.run)
