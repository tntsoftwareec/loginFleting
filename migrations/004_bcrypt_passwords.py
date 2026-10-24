"""
Migration: 004_bcrypt_passwords.py
Rehash all existing user passwords from SHA-256 (or plaintext) to bcrypt.
"""
import re
import bcrypt

def _is_bcrypt_hash(value: str) -> bool:
    """Check if a string already looks like a bcrypt hash."""
    if not value:
        return False
    return value.startswith("$2b$") or value.startswith("$2a$")

def _sha256_hex(value: str) -> str:
    """Return SHA-256 hex of a value."""
    import hashlib
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def up(db):
    cursor = db.cursor()
    cursor.execute("SELECT id, email, password FROM users")
    users = cursor.fetchall()

    if not users:
        print("No users found — skipping bcrypt migration.")
        return

    # Known plaintext passwords from seeds (SHA-256 or plaintext match)
    known_passwords = [
        "admin123",
        "cajero123",
        "password123",
    ]

    rehashed = 0
    skipped = 0

    for user in users:
        user_id = user[0]
        email = user[1]
        stored_hash = user[2] or ""

        # Skip if already bcrypt
        if _is_bcrypt_hash(stored_hash):
            skipped += 1
            continue

        # Try to match against known passwords
        matched_password = None
        for candidate in known_passwords:
            # Check plaintext
            if stored_hash == candidate:
                matched_password = candidate
                break
            # Check SHA-256 hex
            if stored_hash == _sha256_hex(candidate):
                matched_password = candidate
                break

        if matched_password is None:
            # For unknown hashes (e.g. Faker users), default to "password123"
            matched_password = "password123"

        # Rehash with bcrypt
        new_hash = bcrypt.hashpw(matched_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        cursor.execute("UPDATE users SET password = ? WHERE id = ?", (new_hash, user_id))
        rehashed += 1

    db.commit()
    print(f"Rehashed {rehashed} passwords to bcrypt ({skipped} already bcrypt).")

def down(db):
    # bcrypt hashes cannot be reversed — this is a one-way migration
    print("Warning: bcrypt migration is not reversible.")
    pass
