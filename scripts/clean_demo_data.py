#!/usr/bin/env python3
"""
Elimina los datos de prueba/demostración para dejar la aplicación lista
para empezar a trabajar con datos reales.

Conserva:
- La configuración de la empresa (RUC, logo, certificado, SMTP, etc.).
- El usuario administrador indicado con --keep-email (por defecto admin@pos.com).
- El cliente genérico CONSUMIDOR FINAL.
- Los roles base del sistema.

Elimina:
- Facturas, cotizaciones, ítems y movimientos de inventario.
- Clientes, proveedores, productos y servicios de prueba.
- Usuarios de prueba (todos excepto el administrador indicado).
- PDFs, XMLs, imágenes de productos y exportaciones generadas.
- Reinicia la numeración de facturas y cotizaciones a 1.

Uso:
    python scripts/clean_demo_data.py
    python scripts/clean_demo_data.py --dry-run
    python scripts/clean_demo_data.py --keep-email otro@correo.com
"""
import argparse
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.database import get_connection, transaction
from core.paths import GENERATED_DIR

CONSUMIDOR_FINAL = "9999999999999"
DEFAULT_ADMIN_EMAIL = "admin@pos.com"
CLEARED_TABLES = (
    "invoice_items",
    "invoices",
    "quotation_items",
    "quotations",
    "inventory_movements",
    "products",
    "services",
    "suppliers",
)
COUNTED_TABLES = CLEARED_TABLES + ("clients", "users", "roles", "company")
GENERATED_FOLDERS = ("invoices", "quotations", "products", "exports")


def _counts(db):
    counts = {}
    for table in COUNTED_TABLES:
        try:
            counts[table] = db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        except Exception:
            counts[table] = "?"
    return counts


def _print_counts(title, counts):
    print(f"\n{title}")
    for table in COUNTED_TABLES:
        print(f"  {table:<22} {counts.get(table, '?')}")


def _remove_generated_files(dry_run=False):
    removed = []
    for folder in GENERATED_FOLDERS:
        path = GENERATED_DIR / folder
        if path.exists():
            removed.append(str(path))
            if not dry_run:
                shutil.rmtree(path)
    return removed


def clean_data(keep_emails, dry_run=False):
    db = get_connection()
    before = _counts(db)

    _print_counts("Antes:", before)

    keep_emails = [email.strip().lower() for email in keep_emails if email.strip()]
    if not keep_emails:
        raise SystemExit("Debes indicar al menos un correo para conservar como administrador.")

    placeholders = ",".join("?" for _ in keep_emails)
    kept_users = db.execute(
        f"SELECT COUNT(*) FROM users WHERE lower(email) IN ({placeholders})",
        tuple(keep_emails),
    ).fetchone()[0]
    if kept_users == 0:
        raise SystemExit(
            "No existe ningún usuario con los correos indicados. "
            "Usa --keep-email con el correo del administrador que deseas conservar."
        )

    if dry_run:
        print("\n[DRY-RUN] No se modificó la base de datos.")
        print("Se eliminarían los datos de las tablas:", ", ".join(CLEARED_TABLES))
        print("Se conservarían los usuarios:", ", ".join(keep_emails))
        print("Se conservaría el cliente CONSUMIDOR FINAL.")
        print("Se reiniciarían las numeraciones de factura y cotización a 1.")
        files = _remove_generated_files(dry_run=True)
        if files:
            print("Se eliminarían estos directorios generados:")
            for path in files:
                print(" -", path)
        return before, before

    with transaction(db):
        # Orden importante por las relaciones entre tablas.
        db.execute("DELETE FROM invoice_items")
        db.execute("DELETE FROM invoices")
        db.execute("DELETE FROM quotation_items")
        db.execute("DELETE FROM quotations")
        db.execute("DELETE FROM inventory_movements")
        db.execute("DELETE FROM products")
        db.execute("DELETE FROM services")
        db.execute("DELETE FROM suppliers")

        # Solo se conserva el cliente genérico.
        db.execute(
            "DELETE FROM clients WHERE identificacion <> ?",
            (CONSUMIDOR_FINAL,),
        )

        # Solo se conservan los administradores indicados.
        placeholders = ",".join("?" for _ in keep_emails)
        db.execute(
            f"DELETE FROM users WHERE lower(email) NOT IN ({placeholders})",
            tuple(keep_emails),
        )

        # El rol "Demo" era parte de los datos de prueba.
        db.execute("DELETE FROM roles WHERE name = 'Demo'")

        # Reiniciar la numeración de comprobantes.
        db.execute(
            "UPDATE company SET secuencial_factura = 1, secuencial_cotizacion = 1"
        )

        # Reiniciar los IDs de las tablas que quedaron vacías.
        for table in CLEARED_TABLES:
            db.execute("DELETE FROM sqlite_sequence WHERE name = ?", (table,))

        # Ajustar la secuencia de las tablas donde se conservan filas.
        for table in ("users", "clients"):
            max_id = db.execute(f"SELECT COALESCE(MAX(id), 0) FROM {table}").fetchone()[0]
            db.execute(
                "INSERT OR REPLACE INTO sqlite_sequence (name, seq) VALUES (?, ?)",
                (table, max_id),
            )

    removed = _remove_generated_files(dry_run=False)

    after = _counts(db)
    _print_counts("Después:", after)

    if removed:
        print("\nDirectorios generados eliminados:")
        for path in removed:
            print(" -", path)

    print("\n✅ Datos de prueba eliminados. La empresa y el usuario administrador se conservaron.")
    return before, after


def main():
    parser = argparse.ArgumentParser(
        description="Elimina datos de prueba y deja la aplicación lista para usar."
    )
    parser.add_argument(
        "--keep-email",
        action="append",
        default=[],
        metavar="CORREO",
        help=(
            "Correo de un usuario que se conservará. "
            f"Se puede repetir. Por defecto se conserva {DEFAULT_ADMIN_EMAIL}."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Muestra lo que se eliminaría sin modificar la base de datos.",
    )
    args = parser.parse_args()

    keep_emails = [DEFAULT_ADMIN_EMAIL] + args.keep_email
    clean_data(keep_emails, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
