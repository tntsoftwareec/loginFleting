import unittest

from core.state import AppState


class HasPermissionTest(unittest.TestCase):
    def setUp(self):
        self._previous = AppState.current_user
        AppState.current_user = None

    def tearDown(self):
        AppState.current_user = self._previous

    def test_fail_closed_without_user(self):
        self.assertFalse(AppState.has_permission("can_read"))

    def test_fail_closed_without_permissions(self):
        AppState.current_user = {"id": 1}
        self.assertFalse(AppState.has_permission("can_read"))

    def test_fail_closed_when_permissions_not_dict(self):
        AppState.current_user = {"id": 1, "permissions": None}
        self.assertFalse(AppState.has_permission("can_read"))

    def test_allows_when_permission_true(self):
        AppState.current_user = {"permissions": {"can_read": True}}
        self.assertTrue(AppState.has_permission("can_read"))

    def test_denies_when_permission_false(self):
        AppState.current_user = {"permissions": {"can_read": False}}
        self.assertFalse(AppState.has_permission("can_read"))

    def test_unknown_permission_denied_by_default(self):
        AppState.current_user = {"permissions": {"can_read": True}}
        self.assertFalse(AppState.has_permission("can_delete"))

    def test_module_permission_uses_module_matrix(self):
        AppState.current_user = {
            "permissions": {"can_read": True},
            "module_permissions": {
                "pos": {"can_read": True, "can_write": True},
                "clients": {"can_read": True, "can_write": False},
            },
        }
        self.assertTrue(AppState.has_permission("can_read", "pos"))
        self.assertTrue(AppState.has_permission("can_write", "pos"))
        self.assertTrue(AppState.has_permission("can_read", "clients"))
        self.assertFalse(AppState.has_permission("can_write", "clients"))

    def test_module_permission_denied_when_module_missing(self):
        AppState.current_user = {
            "permissions": {"can_read": True},
            "module_permissions": {
                "pos": {"can_read": True},
            },
        }
        # La matriz existe y no incluye inventario: no se hereda el global.
        self.assertFalse(AppState.has_permission("can_read", "inventory"))
        self.assertFalse(AppState.can_access_module("inventory"))

    def test_module_permission_falls_back_to_global_without_matrix(self):
        AppState.current_user = {"permissions": {"can_read": True}}
        self.assertTrue(AppState.has_permission("can_read", "pos"))
        self.assertTrue(AppState.can_access_module("pos"))


if __name__ == "__main__":
    unittest.main()
