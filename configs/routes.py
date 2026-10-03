
import flet as ft
import importlib

ROUTES = [
    {
        "path": "/",
        "view": "app.views.pages.home_view.HomeView",
        "label": "menu.home",
        "icon": ft.Icons.HOME,
        "show_in_top": True,
        "show_in_bottom": True,
    },
    {
        "path": "/login",
        "view": "app.views.pages.login_view.LoginView",
        "label": "menu.login",
        "icon": ft.Icons.LOGIN,
        "show_in_top": False,
        "show_in_bottom": False,
    },

    {
        "path": "/users",
        "view": "app.views.pages.users_view.UsersView",
        "label": "menu.users",
        "icon": ft.Icons.SUPERVISED_USER_CIRCLE_ROUNDED,
        "show_in_top": True,
        "show_in_bottom": True,
    },
    {
        "path": "/roles",
        "view": "app.views.pages.roles_view.RolesView",
        "label": "menu.roles",
        "icon": ft.Icons.ADMIN_PANEL_SETTINGS_ROUNDED,
        "show_in_top": True,
        "show_in_bottom": False,
    },
    {
        "path": "/settings",
        "view": "app.views.pages.settings_view.SettingsView",
        "label": "menu.settings",
        "icon": ft.Icons.SETTINGS,
        "show_in_top": True,
        "show_in_bottom": False,
    },
    {
        "path": "/help",
        "view": "app.views.pages.help_view.HelpView",
        "label": "menu.help",
        "icon": ft.Icons.HELP,
        "show_in_top": True,
        "show_in_bottom": True,
    }
]


def load_view(view_path: str):
    module_name, class_name = view_path.rsplit(".", 1)

    try:
        module = importlib.import_module(module_name)
        view_class = getattr(module, class_name)
        return view_class
    except (ImportError, AttributeError) as e:
        print(f"Erro ao carregar view {view_path}: {e}")
        return None


def get_routes():
    routes = {}

    for r in ROUTES:
        def create_view_lambda(path=r["view"]):
            return lambda page, router: load_view(path)(page, router).render()

        routes[r["path"]] = create_view_lambda()

    return routes


routes = get_routes()
