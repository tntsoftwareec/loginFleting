
import flet as ft
from core.logger import get_logger
from core.state import AppState

logger = get_logger("Router")


class Router:
    def __init__(self, page):
        self.page = page
        self.current_route = "/"
        self.route_defs = {}
        self.routes = self._load_routes()
        self._history = []      # stack of previously visited routes
        self._forward = []      # stack of routes for forward navigation

    def _load_routes(self):
        from configs.routes import routes, ROUTES
        self.route_defs = {r["path"]: r for r in ROUTES}
        return routes

    # ── Public API ──────────────────────────────────────────────────────────

    def navigate(self, route, clear_history=False):
        """Navigate to a route, pushing the current route to history.

        Args:
            route: The target route path (e.g. "/pos")
            clear_history: If True, clear both history stacks (used on login/logout)
        """
        if clear_history:
            self._history.clear()
            self._forward.clear()

        route = self._resolve(route)

        if route not in self.routes:
            route = "/"

        # Don't push to history if we're navigating to the same route
        if route == self.current_route and not clear_history:
            logger.debug(f"Already at route: {route}")
            return

        # Push current route to history (unless it's the initial empty state)
        if self.current_route != "/":
            self._history.append(self.current_route)
            # Any new navigation invalidates the forward stack
            self._forward.clear()

        logger.info(f"Navigating to: {route} (history depth: {len(self._history)})")
        self._render(route)

    def go_back(self):
        """Navigate to the previous route in history. Returns True if successful."""
        if not self._can_go_back():
            logger.debug("Cannot go back — history is empty")
            return False

        previous_route = self._resolve(self._history.pop())
        self._forward.append(self.current_route)

        logger.info(f"Going back to: {previous_route}")
        self._render(previous_route)
        return True

    def go_forward(self):
        """Navigate to the next route in forward history. Returns True if successful."""
        if not self._can_go_forward():
            logger.debug("Cannot go forward — forward stack is empty")
            return False

        next_route = self._resolve(self._forward.pop())
        self._history.append(self.current_route)

        logger.info(f"Going forward to: {next_route}")
        self._render(next_route)
        return True

    def can_go_back(self) -> bool:
        """Check if there is a previous route in history."""
        return len(self._history) > 0

    def can_go_forward(self) -> bool:
        """Check if there is a next route in forward history."""
        return len(self._forward) > 0

    def clear_history(self):
        """Clear both history stacks (e.g. on login/logout)."""
        self._history.clear()
        self._forward.clear()

    def get_history(self) -> list:
        """Return a copy of the history stack (for debugging/display)."""
        return self._history.copy()

    def rerender(self):
        """Re-render the current route (e.g. when the device type changes)."""
        self._render(self._resolve(self.current_route))

    # ── Internal ────────────────────────────────────────────────────────────

    def _resolve(self, route):
        """Resolve a route applying the authentication guard.

        - Unknown route      -> "/"
        - Protected route without an authenticated user -> "/login"
        """
        if route not in self.routes:
            logger.warning(f"Route not found: {route}")
            return "/"

        route_def = self.route_defs.get(route, {})
        if route_def.get("auth_required", True) and not AppState.current_user:
            logger.info(f"Route requires authentication: {route}")
            return "/login"

        return route

    def _can_go_back(self) -> bool:
        return len(self._history) > 0

    def _can_go_forward(self) -> bool:
        return len(self._forward) > 0

    def _render(self, route):
        """Render the given route."""
        self.current_route = route
        AppState.current_route = route
        self.page.controls.clear()
        self.page.overlay.clear()
        # Limpia el chrome de la página; MainLayout lo vuelve a fijar si aplica.
        self.page.appbar = None
        if hasattr(self.page, "bottom_app_bar"):
            self.page.bottom_app_bar = None
        if hasattr(self.page, "dialog"):
            self.page.dialog = None

        try:
            view = self.routes[route](self.page, self)
            self.page.add(view)
        except Exception as e:
            logger.exception("Error rendering view")
            self.page.add(ft.Text("Internal application error"))

        self.page.update()
