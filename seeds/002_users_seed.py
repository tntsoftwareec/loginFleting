"""
Seed: 002_users_seed.py
Crea el usuario administrador inicial de la aplicación.
"""
import bcrypt


def run(db):
    cursor = db.cursor()

    cursor.execute("SELECT id, name FROM roles")
    roles = cursor.fetchall()
    if not roles:
        print("⚠️ No roles found. Skipping user seeding.")
        return

    role_map = {name: role_id for role_id, name in roles}
    admin_role_id = role_map.get("Admin", roles[0][0])

    admin_pass = bcrypt.hashpw(b"admin123", bcrypt.gensalt()).decode("utf-8")

    cursor.execute(
        """
        INSERT OR IGNORE INTO users (name, email, password, role_id, status)
        VALUES (?, ?, ?, ?, 'active')
        """,
        ("Administrador", "admin@pos.com", admin_pass, admin_role_id),
    )

    db.commit()
