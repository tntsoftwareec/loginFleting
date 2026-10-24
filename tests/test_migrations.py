import os
import unittest

from tests.base import ensure_faker, reset_db, use_temp_db

ensure_faker()
TMP_DB = use_temp_db()

from core.database import get_connection, init_db
from core.migrations import applied_migrations

EXPECTED_TABLES = {
    "roles", "users", "clients", "suppliers", "products", "services",
    "company", "invoices", "invoice_items", "quotations", "quotation_items",
    "inventory_movements", "_fleting_migrations",
}


class MigrationsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reset_db()
        cls.conn = get_connection()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        if os.path.exists(TMP_DB):
            os.remove(TMP_DB)

    def test_tables_created(self):
        rows = self.conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        tables = {r[0] for r in rows}
        self.assertFalse(EXPECTED_TABLES - tables)

    def test_migrations_and_seeds_registered(self):
        applied = applied_migrations()
        for name in ("001_initial", "006_company_secuencial",
                     "001_roles_seed", "006_company_seed"):
            self.assertIn(name, applied)
        # seeds/initial.py está obsoleto y no debe ejecutarse
        self.assertNotIn("initial", applied)

    def test_company_secuencial_cotizacion_column(self):
        cols = {r[1] for r in self.conn.execute("PRAGMA table_info(company)").fetchall()}
        self.assertIn("secuencial_cotizacion", cols)

    def test_inventory_schema_and_initial_movements(self):
        cols = {
            r[1] for r in self.conn.execute("PRAGMA table_info(products)").fetchall()
        }
        self.assertIn("stock_minimo", cols)

        products_with_stock = self.conn.execute(
            "SELECT COUNT(*) FROM products WHERE stock > 0"
        ).fetchone()[0]
        initial_movements = self.conn.execute(
            "SELECT COUNT(*) FROM inventory_movements WHERE tipo = 'INICIAL'"
        ).fetchone()[0]
        self.assertEqual(products_with_stock, initial_movements)

    def test_company_logo_column(self):
        cols = {
            r[1] for r in self.conn.execute("PRAGMA table_info(company)").fetchall()
        }
        self.assertIn("logo_path", cols)

    def test_product_supplier_and_sri_columns(self):
        product_cols = {
            r[1] for r in self.conn.execute("PRAGMA table_info(products)").fetchall()
        }
        self.assertIn("supplier_id", product_cols)

        invoice_cols = {
            r[1] for r in self.conn.execute("PRAGMA table_info(invoices)").fetchall()
        }
        for column in (
            "email_estado", "sri_respuesta", "sri_autorizacion",
            "sri_fecha_autorizacion", "sri_fecha_envio",
        ):
            self.assertIn(column, invoice_cols)

    def test_seeds_populated(self):
        users = self.conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        products = self.conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        company = self.conn.execute("SELECT COUNT(*) FROM company").fetchone()[0]
        self.assertGreaterEqual(users, 2)
        self.assertEqual(products, 6)
        self.assertEqual(company, 1)

    def test_second_run_is_idempotent(self):
        before_users = self.conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        before = len(applied_migrations())
        init_db(self.conn)
        after_users = self.conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        after = len(applied_migrations())
        self.assertEqual(before_users, after_users)
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
