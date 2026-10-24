"""
Migration: 005_encrypt_smtp_pass.py
Encrypt existing plaintext smtp_pass values in the company table.
"""
from app.services.encryption_service import EncryptionService


def up(db):
    cursor = db.cursor()
    cursor.execute("SELECT id, smtp_pass FROM company WHERE smtp_pass IS NOT NULL AND smtp_pass != ''")
    rows = cursor.fetchall()

    if not rows:
        print("No plaintext smtp_pass values found — skipping.")
        return

    encrypted_count = 0
    for row in rows:
        company_id = row[0]
        plaintext = row[1]

        # Skip if already encrypted (Fernet tokens start with 'gAAAA')
        if plaintext.startswith("gAAAA"):
            continue

        encrypted = EncryptionService.encrypt(plaintext)
        cursor.execute("UPDATE company SET smtp_pass = ? WHERE id = ?", (encrypted, company_id))
        encrypted_count += 1

    db.commit()
    print(f"Encrypted {encrypted_count} smtp_pass value(s).")


def down(db):
    print("Warning: smtp_pass encryption is not reversible without the original SECRET_KEY.")
    pass
