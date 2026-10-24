import os
import unittest

from tests.base import ensure_faker, reset_db, use_temp_db

ensure_faker()
TMP_DB = use_temp_db()

from core.database import get_connection, transaction
from app.models.role_model import RoleModel
from app.models.user_model import UserModel


class ORMTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reset_db()
        cls.conn = get_connection()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        if os.path.exists(TMP_DB):
            os.remove(TMP_DB)

    def test_create_returns_dict(self):
        role = RoleModel.create(
            name="TestRol", description="desc",
            can_read=1, can_write=1, can_update=1, can_delete=0,
        )
        self.assertIsInstance(role, dict)
        self.assertEqual(role["name"], "TestRol")

    def test_find_where_all_count(self):
        role = RoleModel.create(name="BuscarRol")
        self.assertEqual(RoleModel.find(role["id"])["name"], "BuscarRol")
        self.assertEqual(RoleModel.where(name="BuscarRol")[0]["id"], role["id"])
        self.assertGreaterEqual(RoleModel.count(), 1)
        self.assertTrue(RoleModel.exists(name="BuscarRol"))

    def test_foreign_key_relation_returns_dict(self):
        users = UserModel.where(email="admin@pos.com")
        self.assertTrue(users)
        user = UserModel.with_("role").find(users[0]["id"])
        self.assertIsInstance(user["role"], dict)
        self.assertEqual(user["role"]["name"], "Admin")

    def test_shared_row_factory_not_mutated(self):
        # Las migraciones/seeds dependen de filas tipo tupla.
        self.assertIsNone(self.conn.row_factory)

    def test_transaction_rolls_back_on_error(self):
        with self.assertRaises(RuntimeError):
            with transaction():
                RoleModel.create(name="TxRol")
                raise RuntimeError("boom")
        self.assertFalse(RoleModel.where(name="TxRol"))

    def test_transaction_commits_on_success(self):
        with transaction():
            RoleModel.create(name="TxRolOk")
        self.assertTrue(RoleModel.where(name="TxRolOk"))

    def test_nested_transaction(self):
        with transaction():
            RoleModel.create(name="Outer")
            with transaction():
                RoleModel.create(name="Inner")
        self.assertTrue(RoleModel.where(name="Outer"))
        self.assertTrue(RoleModel.where(name="Inner"))


if __name__ == "__main__":
    unittest.main()
