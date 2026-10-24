import unittest

from tests.base import ensure_flet

ensure_flet()

from core.router import Router
from core.state import AppState


class _FakeRouter(Router):
    """Router sin __init__ (evita necesitar un page real)."""

    def __init__(self):
        from configs.routes import ROUTES, routes
        self.route_defs = {r["path"]: r for r in ROUTES}
        self.routes = routes
        self.current_route = "/"
        self._history = []
        self._forward = []


class RouterAuthTest(unittest.TestCase):
    def setUp(self):
        self._previous = AppState.current_user
        self.router = _FakeRouter()

    def tearDown(self):
        AppState.current_user = self._previous

    def test_protected_route_redirects_to_login_without_session(self):
        AppState.current_user = None
        self.assertEqual(self.router._resolve("/pos"), "/login")
        self.assertEqual(self.router._resolve("/"), "/login")

    def test_login_is_public(self):
        AppState.current_user = None
        self.assertEqual(self.router._resolve("/login"), "/login")

    def test_unknown_route_falls_back_to_home(self):
        self.assertEqual(self.router._resolve("/no-existe"), "/")

    def test_authenticated_user_accesses_protected_route(self):
        AppState.current_user = {"id": 1, "permissions": {"can_read": True}}
        self.assertEqual(self.router._resolve("/pos"), "/pos")

    def test_render_syncs_current_route(self):
        import inspect
        source = inspect.getsource(Router._render)
        self.assertIn("AppState.current_route = route", source)


class _FakePage:
    def __init__(self):
        self.controls = ["old"]
        self.overlay = ["old"]
        self.dialog = object()
        self.appbar = "stale-appbar"
        self.bottom_app_bar = "stale-bottom"
        self.added = None
        self.updated = False

    def add(self, control):
        self.added = control

    def update(self):
        self.updated = True


class _RouteRouter(Router):
    def __init__(self):
        self.current_route = "/"
        self.route_defs = {}
        self.routes = {"/test": lambda page, router: "VIEW"}
        self._history = []
        self._forward = []


class RouterRenderTest(unittest.TestCase):
    def test_render_clears_page_chrome(self):
        page = _FakePage()
        router = _RouteRouter()
        router.page = page

        router._render("/test")

        self.assertIsNone(page.appbar)
        self.assertIsNone(page.bottom_app_bar)
        self.assertEqual(page.controls, [])
        self.assertEqual(page.overlay, [])
        self.assertIsNone(page.dialog)
        self.assertEqual(page.added, "VIEW")
        self.assertTrue(page.updated)
        self.assertEqual(AppState.current_route, "/test")


if __name__ == "__main__":
    unittest.main()
