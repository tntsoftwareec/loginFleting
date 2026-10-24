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


if __name__ == "__main__":
    unittest.main()
