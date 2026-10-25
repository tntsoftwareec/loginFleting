import os
import unittest

from tests.base import ensure_faker, reset_db, use_temp_db

ensure_faker()
TMP_DB = use_temp_db()

from core.database import get_connection
from core.permissions import preset_permissions
from core.state import AppState
from app.controllers.role_controller import RoleController
from app.models.user_model import UserModel


class RolePermissionsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        reset_db()
        cls.conn = get_connection()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()
        if os.path.exists(TMP_DB):
            os.remove(TMP_DB)

    def setUp(self):
        self._previous_user = AppState.current_user
        AppState.current_user = None

    def tearDown(self):
        AppState.current_user = self._previous_user

    def _role_by_name(self, name):
        for role in RoleController.get_all():
            if role["name"].lower() == name.lower():
                return role
        return None

    def test_seed_creates_vendedor_and_bodeguero_with_module_access(self):
        vendedor = self._role_by_name("vendedor")
        bodeguero = self._role_by_name("bodeguero")
        self.assertIsNotNone(vendedor)
        self.assertIsNotNone(bodeguero)

        self.assertEqual(vendedor["allowed_modules"], ["pos", "clients"])
        self.assertEqual(bodeguero["allowed_modules"], ["inventory"])

        self.assertTrue(
            vendedor["module_permissions"]["clients"]["can_write"]
        )
        self.assertFalse(
            vendedor["module_permissions"]["inventory"]["can_read"]
        )
        self.assertTrue(
            bodeguero["module_permissions"]["inventory"]["can_update"]
        )
        self.assertFalse(
            bodeguero["module_permissions"]["pos"]["can_read"]
        )

    def test_admin_has_all_modules(self):
        admin = self._role_by_name("admin")
        self.assertIsNotNone(admin)
        self.assertEqual(len(admin["allowed_modules"]), 14)

    def test_create_role_with_permissions(self):
        success, role = RoleController.create(
            name="Vendedor Test",
            description="Solo POS y clientes",
            permissions=preset_permissions("vendedor"),
        )
        self.assertTrue(success, role)
        self.assertEqual(role["allowed_modules"], ["pos", "clients"])
        self.assertTrue(role["module_permissions"]["pos"]["can_write"])
        self.assertFalse(role["module_permissions"]["roles"]["can_read"])

    def test_create_role_requires_at_least_one_readable_module(self):
        success, message = RoleController.create(
            name="Rol Vacío",
            permissions={},
        )
        self.assertFalse(success)
        self.assertIn("al menos un módulo", message)

    def test_update_role_permissions(self):
        success, role = RoleController.create(
            name="Bodeguero Test",
            permissions=preset_permissions("bodeguero"),
        )
        self.assertTrue(success, role)

        permissions = preset_permissions("bodeguero")
        permissions["products"] = {"can_read": True}
        success, updated = RoleController.update(
            role_id=role["id"],
            name=role["name"],
            description=role["description"],
            permissions=permissions,
        )
        self.assertTrue(success, updated)
        self.assertEqual(updated["allowed_modules"], ["products", "inventory"])
        self.assertTrue(
            updated["module_permissions"]["products"]["can_read"]
        )

    def test_authenticate_returns_module_permissions(self):
        user = UserModel.authenticate("admin@pos.com", "admin123")
        self.assertIsNotNone(user)
        self.assertIn("module_permissions", user)
        self.assertEqual(len(user["module_permissions"]), 14)
        self.assertTrue(user["module_permissions"]["pos"]["can_read"])

    def test_assign_role_to_user_and_authenticate(self):
        success, role = RoleController.create(
            name="Vendedor Auth Test",
            permissions=preset_permissions("vendedor"),
        )
        self.assertTrue(success, role)

        user = UserModel.create(
            name="Vendedor Auth",
            email="vendedor-auth@test.com",
            password=UserModel.hash_password("clave123"),
            role_id=role["id"],
            status="active",
        )
        self.assertIsNotNone(user)

        authenticated = UserModel.authenticate(
            "vendedor-auth@test.com", "clave123"
        )
        self.assertIsNotNone(authenticated)
        self.assertTrue(
            authenticated["module_permissions"]["pos"]["can_write"]
        )
        self.assertFalse(
            authenticated["module_permissions"]["inventory"]["can_read"]
        )

    def test_cannot_remove_own_roles_access(self):
        admin = self._role_by_name("admin")
        self.assertIsNotNone(admin)
        AppState.current_user = {
            "id": 1,
            "role_id": admin["id"],
            "permissions": {"can_read": True},
        }

        success, message = RoleController.update(
            role_id=admin["id"],
            name=admin["name"],
            description=admin["description"],
            permissions=preset_permissions("vendedor"),
        )
        self.assertFalse(success)
        self.assertIn("Roles y permisos", message)

    def test_delete_role_removes_permissions(self):
        success, role = RoleController.create(
            name="Rol Temporal",
            permissions=preset_permissions("vendedor"),
        )
        self.assertTrue(success, role)

        success, _ = RoleController.delete(role["id"])
        self.assertTrue(success)
        rows = self.conn.execute(
            "SELECT COUNT(*) FROM role_permissions WHERE role_id = ?",
            (role["id"],),
        ).fetchone()[0]
        self.assertEqual(rows, 0)


if __name__ == "__main__":
    unittest.main()
