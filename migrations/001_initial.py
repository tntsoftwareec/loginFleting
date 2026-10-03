"""
Migration: 001_initial.py
Creates the base tables 'roles' and 'users'.
"""

def up(db):
    db.execute('''
        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT,
            can_read INTEGER DEFAULT 1,
            can_write INTEGER DEFAULT 1,
            can_update INTEGER DEFAULT 1,
            can_delete INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role_id INTEGER NOT NULL,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE RESTRICT
        )
    ''')
    db.commit()

def down(db):
    db.execute('DROP TABLE IF EXISTS users')
    db.execute('DROP TABLE IF EXISTS roles')
    db.commit()
