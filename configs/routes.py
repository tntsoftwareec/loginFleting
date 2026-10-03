import flet as ft
import importlib

ROUTES = [
    {
        "path": "/",
        "view": "app.views.pages.home_view.HomeView",
        "label": "Inicio",
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
    },
    {
        "path": "/pos",
        "view": "app.views.pages.pos_view.POSView",
        "label": "Punto de Venta (POS)",
        "icon": ft.Icons.POINT_OF_SALE_ROUNDED,
        "show_in_top": True,
        "show_in_bottom": True,
    },
    {
        "path": "/invoices",
        "view": "app.views.pages.invoices_view.InvoicesView",
        "label": "Facturas",
        "icon": ft.Icons.RECEIPT_LONG_ROUNDED,
        "show_in_top": True,
        "show_in_bottom": True,
    },
    {
        "path": "/clients",
        "view": "app.views.pages.clients_view.ClientsView",
        "label": "Clientes",
        "icon": ft.Icons.PEOPLE_ROUNDED,
        "show_in_top": True,
        "show_in_bottom": True,
    },
    {
        "path": "/suppliers",
        "view": "app.views.pages.suppliers_view.SuppliersView",
        "label": "Proveedores",
        "icon": ft.Icons.LOCAL_SHIPPING_ROUNDED,
        "show_in_top": True,
        "show_in_bottom": False,
    },
    {
        "path": "/products",
        "view": "app.views.pages.products_view.ProductsView",
        "label": "Productos",
        "icon": ft.Icons.INVENTORY_2_ROUNDED,
        "show_in_top": True,
        "show_in_bottom": False,
    },
    {
        "path": "/services",
        "view": "app.views.pages.services_view.ServicesView",
        "label": "Servicios",
        "icon": ft.Icons.MISCELLANEOUS_SERVICES_ROUNDED,
        "show_in_top": True,
        "show_in_bottom": False,
    },
    {
        "path": "/company",
        "view": "app.views.pages.company_view.CompanyView",
        "label": "Mi Empresa & Firma",
        "icon": ft.Icons.BUSINESS_ROUNDED,
        "show_in_top": True,
        "show_in_bottom": False,
    },
    {
        "path": "/users",
        "view": "app.views.pages.users_view.UsersView",
        "label": "Usuarios",
        "icon": ft.Icons.SUPERVISED_USER_CIRCLE_ROUNDED,
        "show_in_top": True,
        "show_in_bottom": False,
    },
    {
        "path": "/roles",
        "view": "app.views.pages.roles_view.RolesView",
        "label": "Roles y Permisos",
        "icon": ft.Icons.ADMIN_PANEL_SETTINGS_ROUNDED,
        "show_in_top": True,
        "show_in_bottom": False,
    },
    {
        "path": "/settings",
        "view": "app.views.pages.settings_view.SettingsView",
        "label": "Ajustes",
        "icon": ft.Icons.SETTINGS,
        "show_in_top": True,
        "show_in_bottom": False,
    },
    {
        "path": "/help",
        "view": "app.views.pages.help_view.HelpView",
        "label": "Ayuda",
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
