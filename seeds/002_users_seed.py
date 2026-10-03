"""
Seed: 002_users_seed.py
Seeds users using Faker (es_ES) and hashed passwords.
"""
import hashlib
import random
import re
from faker import Faker

fake = Faker('es_ES')
Faker.seed(12345)
random.seed(12345)

def clean_email_username(text: str) -> str:
    """Removes special characters and accents to create a clean email prefix."""
    text = text.lower()
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'ü': 'u', 'ñ': 'n', ' ': '.'
    }
    for orig, repl in replacements.items():
        text = text.replace(orig, repl)
    return re.sub(r'[^a-z0-9\.]', '', text)

def run(db):
    cursor = db.cursor()

    # Get available role IDs from roles table
    cursor.execute("SELECT id, name FROM roles")
    roles = cursor.fetchall()
    
    if not roles:
        print("⚠️ No roles found. Skipping user seeding.")
        return

    role_map = {name: role_id for role_id, name in roles}
    role_ids = [role_id for role_id, name in roles]
    
    admin_role_id = role_map.get("Admin", role_ids[0])
    cajero_role_id = role_map.get("Cajero", role_ids[0])

    # Core default users
    admin_pass = hashlib.sha256("admin123".encode("utf-8")).hexdigest()
    cajero_pass = hashlib.sha256("cajero123".encode("utf-8")).hexdigest()
    default_pass = hashlib.sha256("password123".encode("utf-8")).hexdigest()

    default_users = [
        ("Administrador Sistema", "admin@pos.com", admin_pass, admin_role_id, "active"),
        ("Cajero Principal", "cajero@pos.com", cajero_pass, cajero_role_id, "active"),
    ]

    for name, email, password, role_id, status in default_users:
        cursor.execute(
            """
            INSERT OR IGNORE INTO users (name, email, password, role_id, status)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, email, password, role_id, status)
        )

    # Generate 25 additional fake users with Faker
    num_fake_users = 25
    for _ in range(num_fake_users):
        name = fake.name()
        prefix = clean_email_username(name)
        email = f"{prefix}.{random.randint(10, 999)}@{fake.free_email_domain()}"
        role_id = random.choice(role_ids)
        status = random.choices(["active", "inactive"], weights=[85, 15])[0]
        created_at = fake.date_time_between(start_date="-1y", end_date="now").strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            """
            INSERT OR IGNORE INTO users (name, email, password, role_id, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (name, email, default_pass, role_id, status, created_at)
        )

    db.commit()
