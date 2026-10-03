

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
    
    cursor = conn.cursor()

    # Table: roles
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        description TEXT,
        can_read INTEGER DEFAULT 1,
        can_write INTEGER DEFAULT 1,
        can_update INTEGER DEFAULT 1,
        can_delete INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Table: users
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role_id INTEGER NOT NULL,
        status TEXT DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE RESTRICT
    );
    """)
    conn.commit()

    # Auto-migration for existing databases missing permission columns
    cursor.execute("PRAGMA table_info(roles)")
    columns = [row[1] for row in cursor.fetchall()]
    for col in ("can_read", "can_write", "can_update", "can_delete"):
        if col not in columns:
            cursor.execute(f"ALTER TABLE roles ADD COLUMN {col} INTEGER DEFAULT 1")
    conn.commit()

    # Update default role permission presets for pre-existing records
    cursor.execute("UPDATE roles SET can_delete = 0 WHERE name = 'Cajero'")
    cursor.execute("UPDATE roles SET can_write = 0, can_update = 0, can_delete = 0 WHERE name = 'Usuario'")
    conn.commit()

    # Seed default roles if table is empty
    cursor.execute("SELECT COUNT(*) FROM roles")
    if cursor.fetchone()[0] == 0:
        default_roles = [
            ("Admin", "Administrador con acceso total al sistema", 1, 1, 1, 1),
            ("Cajero", "Operador de punto de venta (crea y edita)", 1, 1, 1, 0),
            ("Usuario", "Usuario estándar (solo lectura)", 1, 0, 0, 0)
        ]
        cursor.executemany(
            "INSERT INTO roles (name, description, can_read, can_write, can_update, can_delete) VALUES (?, ?, ?, ?, ?, ?)",
            default_roles
        )
        conn.commit()

    # Seed default users if table is empty
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] == 0:
        admin_pass = hashlib.sha256("admin123".encode("utf-8")).hexdigest()
        cajero_pass = hashlib.sha256("cajero123".encode("utf-8")).hexdigest()

        cursor.execute("SELECT id FROM roles WHERE name = 'Admin'")
        admin_row = cursor.fetchone()
        admin_role_id = admin_row[0] if admin_row else 1

        cursor.execute("SELECT id FROM roles WHERE name = 'Cajero'")
        cajero_row = cursor.fetchone()
        cajero_role_id = cajero_row[0] if cajero_row else 2

        default_users = [
            ("Administrador", "admin@pos.com", admin_pass, admin_role_id, "active"),
            ("Cajero Demo", "cajero@pos.com", cajero_pass, cajero_role_id, "active"),
        ]
        cursor.executemany(
            "INSERT INTO users (name, email, password, role_id, status) VALUES (?, ?, ?, ?, ?)",
            default_users
        )
        conn.commit()


