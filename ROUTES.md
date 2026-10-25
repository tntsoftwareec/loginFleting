# ROUTES.md — Rutas y vistas de TntPos

> **Objetivo:** documentar el enrutador de la aplicación, las rutas disponibles, la vista asociada, los parámetros que recibe y su propósito en la interfaz.
>
> **Archivos principales:**
> - `main.py` — punto de entrada; crea el `Router` y navega a `/login`.
> - `configs/routes.py` — registro declarativo de rutas (`ROUTES`) y carga perezosa de vistas.
> - `core/router.py` — motor de navegación, historial y guards de autenticación y módulo.
> - `app/views/pages/` — implementación de cada vista.

---

## 1. Cómo funciona el enrutador

No existe un `app.py`; el arranque está en `main.py` y la configuración de rutas en `configs/routes.py`.

```text
main.py
  └── core/router.py
        ├── configs/routes.py        # ROUTES: path → "app.views.pages.<vista>.<Clase>"
        └── app/views/pages/*.py     # clase de la vista
              └── app/views/layouts/main_layout.py
```

### Flujo de resolución

1. `main.py` crea `Router(page)` y llama a `router.navigate("/login")`.
2. `Router._load_routes()` importa `routes` y `ROUTES` desde `configs/routes.py`.
3. `Router._resolve(route)` aplica el guard:
   - Ruta desconocida → `/`.
   - Ruta protegida sin sesión → `/login`.
   - Ruta pública o con sesión → se mantiene.
4. `Router._render(route)` limpia `page.controls`, `page.overlay`, `page.appbar` y el diálogo anterior.
5. `get_routes()` construye una función por ruta que:
   - Importa la clase con `importlib` (carga perezosa).
   - La instancia con `(page, router)`.
   - Llama a `render()`.
6. El control devuelto por `render()` se agrega a la página.

### Contrato de una vista

Todas las vistas de este proyecto siguen el mismo contrato:

```python
class NombreView:
    def __init__(self, page: ft.Page, router):
        self.page = page
        self.router = router

    def render(self):
        return MainLayout(
            page=self.page,
            content=content,
            router=self.router,
        )
```

- **Constructor:** recibe `page: ft.Page` y `router: Router`.
- **`render()`:** no recibe parámetros y devuelve un control de Flet.
- **Layout:** las vistas de módulo devuelven `MainLayout`; el login es la excepción y devuelve un `ft.Column` propio.
- **Parámetros de URL:** no hay rutas dinámicas (`/clients/:id`, etc.). Los identificadores se manejan con estado interno, diálogos o `AppState`.

---

## 2. Tabla de rutas

| Ruta (URL) | Vista | Parámetros que recibe | Propósito en la interfaz |
|---|---|---|---|
| `/` | `HomeView` | `page`, `router` | Panel de inicio con bienvenida, tarjetas de estadísticas y accesos directos a los módulos. |
| `/login` | `LoginView` | `page`, `router` | Inicio de sesión con correo y contraseña. Es la única ruta pública y no usa `MainLayout`. |
| `/pos` | `POSView` | `page`, `router` + `AppState.pending_cart_items` opcional | Punto de venta: catálogo de productos/servicios, carrito, cliente, descuentos, propina, forma de pago y emisión de factura. |
| `/invoices` | `InvoicesView` | `page`, `router` | Listado y detalle de facturas: envío al SRI, consulta de autorización, RIDE/XML, reenvío por correo e importación/exportación. |
| `/quotations` | `QuotationsView` | `page`, `router` | Listado de cotizaciones: ver PDF, enviar por correo o WhatsApp, convertir a factura y eliminar. |
| `/quotations/new` | `QuotationNewView` | `page`, `router` + `AppState.pending_cart_items` opcional | Creación de una cotización con el mismo patrón de catálogo y carrito del POS, sin emitir factura. |
| `/clients` | `ClientsView` | `page`, `router` | CRUD de clientes, búsqueda por identificación/nombre/correo y acciones de importar/exportar. |
| `/suppliers` | `SuppliersView` | `page`, `router` | CRUD de proveedores, datos de contacto y exportación a Excel. |
| `/products` | `ProductsView` | `page`, `router` | CRUD de productos: precios, costos, stock, stock mínimo, proveedor, imagen, ICE e importación/exportación. |
| `/inventory` | `InventoryView` | `page`, `router` | Resumen de existencias, alertas de stock bajo, entradas/salidas/ajustes e historial de movimientos. |
| `/services` | `ServicesView` | `page`, `router` | CRUD de servicios, tarifas, IVA/ICE y acciones para enviarlos al POS o a una nueva cotización. |
| `/company` | `CompanyView` | `page`, `router` | Configuración de la empresa: datos fiscales, SRI, SMTP, logo, certificado `.p12/.pfx` y secuenciales. |
| `/users` | `UsersView` | `page`, `router` | CRUD de usuarios: nombre, correo, rol, estado y contraseña. |
| `/roles` | `RolesView` | `page`, `router` | CRUD de roles y matriz de permisos por módulo (Ver / Crear / Editar / Eliminar) con presets para vendedor, bodeguero, cajero y supervisor. |
| `/settings` | `SettingsView` | `page`, `router` | Preferencias de la aplicación: tema claro/oscuro/sistema e idioma. |
| `/help` | `HelpView` | `page`, `router` | Pantalla de ayuda con enlaces a documentación, reporte de problemas y soporte. Contenido legado de Fleting. |

> **Sobre los parámetros:** todas las vistas reciben `page` y `router` en el constructor. Las rutas `/pos` y `/quotations/new` además leen `AppState.pending_cart_items` para precargar un producto o servicio cuando el usuario pulsa **Facturar** o **Cotizar** desde el catálogo de servicios.

---

## 3. Metadatos de navegación

| Ruta | Archivo de la vista | Módulo | ¿Requiere sesión? | Barra superior | Barra inferior | Etiqueta |
|---|---|---|---|---|---|---|
| `/` | `app/views/pages/home_view.py` | `home` | Sí | Sí | Sí | `menu.home` |
| `/login` | `app/views/pages/login_view.py` | — | **No** | No | No | `Login` |
| `/pos` | `app/views/pages/pos_view.py` | `pos` | Sí | Sí | Sí | `menu.pos` |
| `/invoices` | `app/views/pages/invoices_view.py` | `invoices` | Sí | Sí | Sí | `menu.invoices` |
| `/quotations` | `app/views/pages/quotations_view.py` | `quotations` | Sí | Sí | Sí | `menu.quotations` |
| `/quotations/new` | `app/views/pages/quotation_new_view.py` | `quotations` | Sí | No | No | `Nueva Cotización` |
| `/clients` | `app/views/pages/clients_view.py` | `clients` | Sí | Sí | Sí | `menu.clients` |
| `/suppliers` | `app/views/pages/suppliers_view.py` | `suppliers` | Sí | Sí | No | `menu.suppliers` |
| `/products` | `app/views/pages/products_view.py` | `products` | Sí | Sí | No | `menu.products` |
| `/inventory` | `app/views/pages/inventory_view.py` | `inventory` | Sí | Sí | No | `menu.inventory` |
| `/services` | `app/views/pages/services_view.py` | `services` | Sí | Sí | No | `menu.services` |
| `/company` | `app/views/pages/company_view.py` | `company` | Sí | Sí | No | `menu.company` |
| `/users` | `app/views/pages/users_view.py` | `users` | Sí | Sí | No | `menu.users` |
| `/roles` | `app/views/pages/roles_view.py` | `roles` | Sí | Sí | No | `menu.roles` |
| `/settings` | `app/views/pages/settings_view.py` | `settings` | Sí | Sí | No | `menu.settings` |
| `/help` | `app/views/pages/help_view.py` | `help` | Sí | Sí | No | `menu.help` |

### Resumen de navegación

- **Ruta pública:** solo `/login`.
- **Barra inferior:** `/`, `/pos`, `/invoices`, `/quotations`, `/clients`, filtradas por el permiso `can_read` del módulo.
- **Barra superior:** todas las rutas excepto `/login` y `/quotations/new`, filtradas por permiso de módulo.
- **Rutas ocultas de la navegación:** `/login` y `/quotations/new` (esta última se abre desde Cotizaciones).
- **Etiquetas:** si contienen un punto (`menu.home`), se traducen con `I18n.t()`; si no, se muestran literalmente.
- **Módulos:** cada ruta protegida declara `module`; el router redirige a la primera ruta permitida si el rol no tiene `can_read`.

---

## 4. Cómo agregar una ruta nueva

### 1. Crear la vista

```bash
fleting create view reportes
```

Esto crea `app/views/pages/reportes_view.py` con la clase `ReportesView`.

### 2. Implementar el contrato

```python
import flet as ft
from core import theme as T
from app.views.layouts.main_layout import MainLayout

class ReportesView:
    def __init__(self, page: ft.Page, router):
        self.page = page
        self.router = router

    def render(self):
        content = ft.Column(
            controls=[
                ft.Text("Reportes", size=24, weight=ft.FontWeight.BOLD, color=T.TEXT),
            ],
            spacing=16,
        )
        return MainLayout(page=self.page, content=content, router=self.router)
```

### 3. Registrar la ruta en `configs/routes.py`

```python
{
    "path": "/reports",
    "view": "app.views.pages.reportes_view.ReportesView",
    "label": "Reportes",
    "icon": ft.Icons.BAR_CHART_ROUNDED,
    "module": "reports",
    "show_in_top": True,
    "show_in_bottom": False,
    # "auth_required": True es el valor por defecto; se puede omitir.
},
```

El orden dentro de `ROUTES` determina el orden de los elementos en la barra superior e inferior.

### 4. Registrar el módulo y sus permisos

Agrega el módulo a `MODULES` en `core/permissions.py`:

```python
{
    "key": "reports",
    "label": "Reportes",
    "description": "Reportes de ventas y compras",
    "route": "/reports",
    "icon": "BAR_CHART_ROUNDED",
    "actions": ("can_read", "can_write"),
},
```

La vista debe comprobar `AppState.has_permission("can_read", "reports")` antes
de cargar datos y usar el mismo módulo para sus acciones de escritura.

### 5. Verificar

```bash
fleting list routes
fleting run
```

---

## 5. Consideraciones y deuda técnica

| Tema | Detalle |
|---|---|
| Sin parámetros de URL | No existen rutas como `/invoices/123`; el detalle se abre en un `AlertDialog` desde la vista de listado. |
| Guard de autenticación | `auth_required` es `True` por defecto. Solo `/login` lo desactiva. |
| Permisos por módulo | Cada ruta declara `module`; el router valida `can_read` y cada vista comprueba `AppState.has_permission("can_read", "modulo")`. La matriz se guarda en `role_permissions` y se edita en `/roles`. |
| `MainLayout` | Instala `page.appbar` y la barra inferior. El router limpia ambos antes de renderizar para evitar herencia entre rutas. |
| Login | Es la única vista que no devuelve `MainLayout`; retorna un `ft.Column` con su propio fondo y tarjeta. |
| Historial | `Router` mantiene pilas de atrás/adelante; `navigate(..., clear_history=True)` se usa al cerrar sesión. |
| Re-render | `router.rerender()` se usa al cambiar tema, idioma o categoría de dispositivo. |
| `/help` | Conserva textos en portugués y enlaces del proyecto Fleting original; pendiente de adaptar a TntPos. |
| `/quotations/new` | No aparece en menús; se llega desde el botón **Nueva Cotización** en `/quotations`. |

---

## 6. Referencias rápidas

```python
# Navegar desde una vista
self.router.navigate("/pos")
self.router.navigate("/login", clear_history=True)

# Historial
self.router.go_back()
self.router.go_forward()
self.router.can_go_back()
self.router.can_go_forward()

# Re-renderizar la ruta actual
self.router.rerender()
```

**Última revisión:** 2026-10-24
**Mantenedores:** equipo TntPos
