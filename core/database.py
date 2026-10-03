

import sqlite3
import hashlib
from configs.database import DATABASE
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
_connection = None
_initialized = False

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

    db_path = BASE_DIR / Path(path_cfg)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

# =========================
# MYSQL
# =========================
def _connect_mysql():
    pass

# =========================
# INITIALIZATION & MIGRATIONS
# =========================
def init_db(conn=None):
    if conn is None:
        conn = get_connection()

    import importlib
    mig1 = importlib.import_module("migrations.001_initial")
    mig2 = importlib.import_module("migrations.002_business_and_pos")
    seed1 = importlib.import_module("seeds.001_roles_seed")
    seed2 = importlib.import_module("seeds.002_users_seed")
    seed3 = importlib.import_module("seeds.003_clients_seed")
    seed4 = importlib.import_module("seeds.004_suppliers_seed")
    seed5 = importlib.import_module("seeds.005_products_services_seed")
    seed6 = importlib.import_module("seeds.006_company_seed")

    mig1.up(conn)
    mig2.up(conn)

    seed1.run(conn)
    seed2.run(conn)
    seed3.run(conn)
    seed4.run(conn)
    seed5.run(conn)
    seed6.run(conn)



