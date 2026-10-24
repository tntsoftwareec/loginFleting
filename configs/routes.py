import flet as ft
from core import theme as T
import importlib

from core.logger import get_logger

logger = get_logger("Routes")

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
        "label": "Login",
        "icon": ft.Icons.LOGIN,
        "show_in_top": False,
        "show_in_bottom": False,
        # Única ruta pública: el resto requiere sesión (ver Router._resolve).
        "auth_required": False,
    },
    {
        "path": "/pos",
        "view": "app.views.pages.pos_view.POSView",
        "label": "menu.pos",
        "icon": ft.Icons.POINT_OF_SALE_ROUNDED,
        "show_in_top": True,
        "show_in_bottom": True,
    },
    {
        "path": "/invoices",
        "view": "app.views.pages.invoices_view.InvoicesView",
        "label": "menu.invoices",
        "icon": ft.Icons.RECEIPT_LONG_ROUNDED,
        "show_in_top": True,
        "show_in_bottom": True,
    },
    {
        "path": "/quotations",
        "view": "app.views.pages.quotations_view.QuotationsView",
        "label": "menu.quotations",
        "icon": ft.Icons.DESCRIPTION_ROUNDED,
        "show_in_top": True,
        "show_in_bottom": True,
    },
    {
        "path": "/quotations/new",
        "view": "app.views.pages.quotation_new_view.QuotationNewView",
        "label": "Nueva Cotización",
        "icon": ft.Icons.NOTE_ADD_ROUNDED,
        "show_in_top": False,
        "show_in_bottom": False,
    },
    {
        "path": "/clients",
        "view": "app.views.pages.clients_view.ClientsView",
        "label": "menu.clients",
        "icon": ft.Icons.PEOPLE_ROUNDED,
        "show_in_top": True,
        "show_in_bottom": True,
    },
    {
        "path": "/suppliers",
        "view": "app.views.pages.suppliers_view.SuppliersView",
        "label": "menu.suppliers",
        "icon": ft.Icons.LOCAL_SHIPPING_ROUNDED,
        "show_in_top": True,
        "show_in_bottom": False,
    },
    {
        "path": "/products",
        "view": "app.views.pages.products_view.ProductsView",
        "label": "menu.products",
        "icon": ft.Icons.INVENTORY_2_ROUNDED,
        "show_in_top": True,
        "show_in_bottom": False,
    },
    {
        "path": "/inventory",
        "view": "app.views.pages.inventory_view.InventoryView",
        "label": "menu.inventory",
        "icon": ft.Icons.WAREHOUSE_ROUNDED,
        "show_in_top": True,
        "show_in_bottom": False,
    },
    {
        "path": "/services",
        "view": "app.views.pages.services_view.ServicesView",
        "label": "menu.services",
        "icon": ft.Icons.MISCELLANEOUS_SERVICES_ROUNDED,
        "show_in_top": True,
        "show_in_bottom": False,
    },
    {
        "path": "/company",
        "view": "app.views.pages.company_view.CompanyView",
        "label": "menu.company",
        "icon": ft.Icons.BUSINESS_ROUNDED,
        "show_in_top": True,
        "show_in_bottom": False,
    },
    {
        "path": "/users",
        "view": "app.views.pages.users_view.UsersView",
        "label": "menu.users",
        "icon": ft.Icons.SUPERVISED_USER_CIRCLE_ROUNDED,
        "show_in_top": True,
        "show_in_bottom": False,
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
        "show_in_bottom": False,
    }
]


def load_view(view_path: str):
    module_name, class_name = view_path.rsplit(".", 1)

    try:
        module = importlib.import_module(module_name)
        view_class = getattr(module, class_name)
        return view_class
    except (ImportError, AttributeError) as e:
        logger.error(f"Error al cargar la vista {view_path}: {e}")
        return None


def _fallback_view(view_path: str):
    """Vista mostrada cuando no se puede cargar una ruta."""
    return ft.Container(
        content=ft.Column(
            controls=[
                ft.Icon(ft.Icons.ERROR_OUTLINE, size=48, color=T.DANGER),
                ft.Text("No se pudo cargar la vista", size=18, weight=ft.FontWeight.BOLD),
                ft.Text(view_path, size=12, color=T.TEXT_MUTED),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=8,
        ),
        alignment=ft.Alignment(0, 0),
        expand=True,
    )


def get_routes():
    routes = {}

    for r in ROUTES:
        def create_view_lambda(path=r["view"]):
            def view(page, router):
                view_class = load_view(path)
                if view_class is None:
                    return _fallback_view(path)
                return view_class(page, router).render()

            return view

        routes[r["path"]] = create_view_lambda()

    return routes


routes = get_routes()
