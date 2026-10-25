# TntPos

**Punto de venta y facturación electrónica para Ecuador**, construido con **Python + Flet** y organizado con la arquitectura MVC de **Fleting**.

TntPos es un ERP ligero para pequeños y medianos negocios. Funciona como aplicación de escritorio y móvil, usa **SQLite** como base de datos local y solo necesita internet para comunicarse con el **SRI** y con el servidor **SMTP**.

## Funcionalidades principales

- **Punto de venta (POS):** carrito, clientes, descuentos, IVA, ICE, propina y formas de pago.
- **Facturación electrónica SRI:** clave de acceso de 49 dígitos, XML, firma XAdES-BES, envío SOAP, consulta de autorización y RIDE en PDF.
- **Cotizaciones:** creación, PDF, envío por correo o WhatsApp y conversión a factura.
- **Inventario:** entradas, salidas, ajustes, alertas de stock bajo e historial de movimientos.
- **Catálogos:** clientes, proveedores, productos (con imagen) y servicios.
- **Administración:** usuarios, roles y permisos.
- **Importación/exportación:** Excel y PDF de los listados principales.
- **Configuración:** datos de la empresa, logo, certificado digital `.p12/.pfx`, SMTP y secuenciales.
- **Interfaz adaptable:** móvil, tablet y escritorio, con temas claro, oscuro y sistema.

---

## Tecnologías

| Componente | Tecnología |
|---|---|
| Lenguaje | Python 3.11 o superior |
| Interfaz | Flet 1.x |
| Estructura y CLI | Fleting (MVC: modelos, controladores y vistas) |
| Base de datos | SQLite (MySQL configurado pero no implementado) |
| PDF / RIDE | ReportLab, Pillow, qrcode |
| XML y firma electrónica | `xml.etree`, `signxml`, `cryptography` |
| SRI | Web services SOAP con `requests` |
| Excel | openpyxl |
| Seguridad | bcrypt para contraseñas y Fernet para datos sensibles |

---

## Requisitos previos

- Python **3.11+** (probado con Python 3.13).
- Git.
- En Linux, las dependencias gráficas habituales de Flet/Flutter.
- Para compilar APK: Flutter SDK y Android SDK configurados (solo si vas a generar el móvil).

Verifica la versión de Python:

```bash
python3 --version
```

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/tntsoftwareec/loginFleting.git
cd loginFleting
```

### 2. Crear y activar el entorno virtual

**Linux / macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows (PowerShell)**

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
```

**Windows (CMD)**

```bat
py -3.11 -m venv .venv
.venv\Scripts\activate.bat
```

Al activarlo, el prompt debe mostrar `(.venv)`.

### 3. Instalar las dependencias

```bash
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
```

`requirements-dev.txt` incluye:

- `requirements.txt` → dependencias de ejecución de la app.
- `flet-cli` y `flet-desktop` → necesarias para ejecutar y compilar con Flet.

Si vas a usar los comandos de Fleting (`fleting run`, `fleting create view`, etc.), instala también la CLI del framework:

```bash
pip install fleting
```

> **Nota:** `requirements.txt` contiene solo dependencias directas. No lo reemplaces por un `pip freeze`, porque el build móvil resuelve las dependencias transitivas según la plataforma y algunas versiones no existen para Android/iOS.

### 4. Ejecutar la aplicación

Con el entorno virtual activo y desde la raíz del proyecto:

```bash
fleting run
```

También puedes ejecutarla directamente con Flet:

```bash
flet run main.py
```

El repositorio incluye el lanzador `bin/fleting`, que apunta al entorno virtual de la máquina donde se creó el proyecto:

```bash
bin/fleting run
```

> Si `bin/fleting` no funciona en tu equipo, usa `fleting run` o `flet run main.py`. El lanzador es solo un atajo.

### 5. Primer inicio

En el primer arranque se crea automáticamente:

- La base de datos `data/fleting.db`.
- Las tablas mediante las migraciones de `migrations/`.
- Los datos iniciales de `seeds/`.
- El usuario administrador:

```text
Correo:   admin@pos.com
Password: admin123
```

> Cambia la contraseña del administrador después del primer ingreso y completa los datos del negocio en **Mi Empresa** antes de emitir facturas.

---

## Estructura del proyecto

```text
loginFleting/
│
├── main.py                      # Punto de entrada: inicia Flet, tema, i18n y router
├── .fleting                     # Marca que identifica el proyecto como Fleting
├── requirements.txt             # Dependencias de runtime
├── requirements-dev.txt         # Runtime + herramientas de desarrollo (Flet CLI)
├── README.md                    # Este documento
├── SPEC.md                      # Especificación técnica detallada
│
├── bin/
│   └── fleting                  # Lanzador local de la CLI de Fleting
│
├── configs/                     # Configuración de la aplicación
│   ├── app_config.py            # Nombre de la app, tamaños de pantalla y tema
│   ├── database.py              # Motor de BD (SQLite/MySQL) y ruta del archivo
│   ├── routes.py                # Registro de rutas → vistas (carga perezosa)
│   └── languages/               # Traducciones es.json, en.json, pt.json
│
├── core/                        # Núcleo reutilizable del framework
│   ├── database.py              # Conexión SQLite, transacciones e inicialización
│   ├── migrations.py            # Aplicación y rollback de migraciones
│   ├── base_model.py            # QuerySet y CRUD genérico
│   ├── orm.py                   # Relaciones ForeignKey / HasMany
│   ├── router.py                # Navegación, historial, guard de auth y de módulo
│   ├── state.py                 # Estado global: usuario, permisos, idioma, dispositivo
│   ├── permissions.py           # Catálogo de módulos, acciones y presets de roles
│   ├── theme.py                 # Paleta y temas claro/oscuro/sistema
│   ├── i18n.py                  # Carga de traducciones
│   ├── responsive.py            # Breakpoints y tamaños de diálogo
│   ├── preferences.py           # Persistencia de tema e idioma
│   ├── logger.py                # Logs a consola y a logs/fleting.log
│   ├── error_handler.py         # Manejo global de errores de la interfaz
│   ├── import_export.py         # Adaptadores de importación/exportación
│   ├── table_filters.py         # Utilidades de filtros de tablas
│   ├── paths.py                 # Rutas de datos persistentes (escritorio/Android)
│   └── documents/               # Lectura/escritura de Excel y PDF de listados
│       ├── excel_io.py
│       ├── list_pdf.py
│       ├── pdf_common.py
│       └── storage.py
│
├── app/                         # Código de la aplicación (patrón MVC)
│   ├── models/                  # Modelos: representan tablas de la BD
│   │   ├── client_model.py
│   │   ├── product_model.py
│   │   ├── invoice_model.py
│   │   ├── role_permission_model.py  # Permisos CRUD por rol y módulo
│   │   └── ...
│   │
│   ├── controllers/             # Lógica de negocio y casos de uso
│   │   ├── invoice_controller.py
│   │   ├── quotation_controller.py
│   │   ├── inventory_controller.py
│   │   └── ...
│   │
│   ├── services/                # Integraciones y servicios técnicos
│   │   ├── sri_service.py       # Firma, SOAP y autorización del SRI
│   │   ├── xml_service.py       # Clave de acceso y XML de factura
│   │   ├── pdf_service.py       # RIDE, cotizaciones, Code 128 y QR
│   │   ├── email_service.py     # Envío SMTP con adjuntos
│   │   ├── encryption_service.py
│   │   ├── signature_service.py
│   │   ├── sri_catalogs.py
│   │   ├── excel_service.py
│   │   └── whatsapp_service.py
│   │
│   └── views/                   # ★ VISTAS DE FLETING
│       ├── layouts/
│       │   └── main_layout.py   # Barra superior + contenido + navegación inferior
│       ├── components/
│       │   └── import_export.py # Barra reutilizable Importar/Plantilla/Excel/PDF
│       ├── pages/               # ★ Una vista por ruta
│       │   ├── login_view.py
│       │   ├── home_view.py
│       │   ├── pos_view.py
│       │   ├── invoices_view.py
│       │   ├── quotations_view.py
│       │   ├── quotation_new_view.py
│       │   ├── clients_view.py
│       │   ├── suppliers_view.py
│       │   ├── products_view.py
│       │   ├── inventory_view.py
│       │   ├── services_view.py
│       │   ├── company_view.py
│       │   ├── users_view.py
│       │   ├── roles_view.py
│       │   ├── settings_view.py
│       │   └── help_view.py
│       └── ui_helpers.py        # Diálogos, toasts, FilePicker, share y URLs
│
├── migrations/                  # Migraciones incrementales 001–014
├── seeds/                       # Datos iniciales idempotentes (incluye roles Vendedor/Bodeguero)
├── scripts/
│   └── clean_demo_data.py       # Limpia datos de demostración de una BD existente
├── tests/                       # Pruebas automatizadas con unittest
│
├── assets/                      # Recursos estáticos y documentos generados
│   ├── icon.png
│   ├── image.png
│   ├── logo.jpg
│   ├── escudo.jpg
│   ├── certs/                   # Certificado digital .p12/.pfx (no versionado)
│   ├── company/                 # Logo de la empresa (no versionado)
│   ├── products/images/         # Imágenes de productos (no versionado)
│   ├── invoices/pdf/            # RIDE generados (no versionado)
│   ├── invoices/xml/            # XML generados/firmados (no versionado)
│   └── quotations/pdf/          # PDF de cotizaciones (no versionado)
│
├── data/                        # Datos persistentes
│   ├── fleting.db               # Base de datos SQLite (no versionada)
│   └── .secret_key              # Clave local de cifrado (no versionada)
│
├── logs/                        # Registros de ejecución (no versionados)
├── build/                       # Artefactos de compilación (no versionado)
└── .flet/                       # Estado local de Flet (no versionado)
```

> Los directorios marcados como “no versionados” están incluidos en `.gitignore` y se crean en tiempo de ejecución.

---

## ¿Dónde se alojan las vistas de Fleting?

Las vistas viven en **`app/views/pages/`**. Cada archivo representa una pantalla y sigue la convención de Fleting:

```text
app/views/pages/<nombre>_view.py  →  class <Nombre>View
```

Una vista recibe `page` y `router`, y su método `render()` devuelve el layout con el contenido:

```python
# app/views/pages/clients_view.py
import flet as ft
from app.views.layouts.main_layout import MainLayout

class ClientsView:
    def __init__(self, page, router):
        self.page = page
        self.router = router

    def render(self):
        content = ft.Column(
            controls=[ft.Text("Clientes", size=24)],
            spacing=16,
        )
        return MainLayout(
            page=self.page,
            content=content,
            router=self.router,
        )
```

### Flujo de una ruta hasta la vista

```text
main.py
  └── core/router.py            # Navega y aplica los guards de auth y módulo
        └── configs/routes.py   # ROUTES: "/clients" → "app.views.pages.clients_view.ClientsView"
              └── app/views/pages/clients_view.py
                    └── app/views/layouts/main_layout.py
```

1. `main.py` crea el `Router` y navega a `/login`.
2. `configs/routes.py` contiene la lista `ROUTES` con la ruta, la vista, el icono, el módulo de permisos y si aparece en la barra superior o inferior.
3. El router importa la vista de forma perezosa con `importlib`, la instancia y llama a `render()`.
4. `MainLayout` envuelve el contenido con la barra superior, el área central y la navegación inferior.
5. Si no hay sesión, el router redirige a `/login`. Si el rol no tiene `can_read` sobre el módulo de la ruta, redirige a la primera ruta permitida.

### Permisos por módulo

Cada rol puede tener permisos independientes para **Inicio, POS, Facturas,
Cotizaciones, Clientes, Proveedores, Productos, Inventario, Servicios,
Empresa, Usuarios, Roles, Ajustes y Ayuda**.

- `core/permissions.py` define el catálogo de módulos, las acciones válidas y los presets (`vendedor`, `bodeguero`, `cajero`, etc.).
- `migrations/014_role_permissions.py` crea la tabla `role_permissions`.
- `seeds/007_advanced_roles_seed.py` aplica presets a los roles base y crea los roles de ejemplo **Vendedor** y **Bodeguero** si no existen.
- `AppState.has_permission("can_read", "pos")` consulta la matriz del rol.
- `configs/routes.py` asigna un `module` a cada ruta; `core/router.py` y `MainLayout` ocultan o redirigen lo que el rol no puede ver.
- En **Roles y permisos** se edita la matriz con casillas Ver / Crear / Editar / Eliminar y botones de preset.

Ejemplo: un **Vendedor** solo ve POS y Clientes; un **Bodeguero** solo ve
Inventario. El administrador puede ajustar esos permisos en cualquier momento.

### Carpetas relacionadas con las vistas

| Ruta | Para qué sirve |
|---|---|
| `app/views/pages/` | Vistas completas, una por ruta o pantalla. |
| `app/views/layouts/` | Estructura visual compartida (`MainLayout`). |
| `app/views/components/` | Componentes reutilizables entre varias vistas. |
| `app/views/ui_helpers.py` | Funciones comunes: diálogos, toasts, archivos, compartir y URLs. |
| `configs/routes.py` | Registro de rutas y metadatos de navegación. |
| `core/router.py` | Motor de navegación, historial y control de acceso. |

### Mapa de rutas a vistas

| Ruta | Vista | Archivo |
|---|---|---|
| `/login` | `LoginView` | `app/views/pages/login_view.py` |
| `/` | `HomeView` | `app/views/pages/home_view.py` |
| `/pos` | `POSView` | `app/views/pages/pos_view.py` |
| `/invoices` | `InvoicesView` | `app/views/pages/invoices_view.py` |
| `/quotations` | `QuotationsView` | `app/views/pages/quotations_view.py` |
| `/quotations/new` | `QuotationNewView` | `app/views/pages/quotation_new_view.py` |
| `/clients` | `ClientsView` | `app/views/pages/clients_view.py` |
| `/suppliers` | `SuppliersView` | `app/views/pages/suppliers_view.py` |
| `/products` | `ProductsView` | `app/views/pages/products_view.py` |
| `/inventory` | `InventoryView` | `app/views/pages/inventory_view.py` |
| `/services` | `ServicesView` | `app/views/pages/services_view.py` |
| `/company` | `CompanyView` | `app/views/pages/company_view.py` |
| `/users` | `UsersView` | `app/views/pages/users_view.py` |
| `/roles` | `RolesView` | `app/views/pages/roles_view.py` |
| `/settings` | `SettingsView` | `app/views/pages/settings_view.py` |
| `/help` | `HelpView` | `app/views/pages/help_view.py` |

### Crear una vista nueva

Con la CLI de Fleting:

```bash
fleting create view ventas
```

Esto crea `app/views/pages/ventas_view.py`. Después debes registrar la ruta en `configs/routes.py`:

```python
{
    "path": "/ventas",
    "view": "app.views.pages.ventas_view.VentasView",
    "label": "Ventas",
    "icon": ft.Icons.SELL_ROUNDED,
    "show_in_top": True,
    "show_in_bottom": False,
},
```

También puedes crear la página completa (modelo + controlador + vista + ruta):

```bash
fleting create page ventas
```

Otros comandos útiles:

```bash
fleting list views        # Lista las vistas
fleting list routes       # Lista las rutas
fleting list models       # Lista los modelos
fleting list controllers  # Lista los controladores
```

---

## Base de datos y datos iniciales

La base de datos se configura en `configs/database.py`:

```python
DATABASE = {
    "ENGINE": "sqlite",
    "SQLITE": {"PATH": "data/fleting.db"},
    ...
}
```

Al abrir la primera conexión, `core/database.py` aplica automáticamente:

- Las migraciones pendientes de `migrations/` (incluida `014_role_permissions.py`).
- Los seeds pendientes de `seeds/` (incluido `007_advanced_roles_seed.py`, que crea los roles de ejemplo Vendedor y Bodeguero).

No es necesario ejecutar `fleting db migrate` ni `fleting db seed` manualmente en el uso normal, aunque los comandos están disponibles.

### Limpiar datos de demostración

Si tu base ya contiene datos de prueba:

```bash
python scripts/clean_demo_data.py
```

Para ver qué se eliminaría sin modificar la base:

```bash
python scripts/clean_demo_data.py --dry-run
```

Para conservar otro administrador:

```bash
python scripts/clean_demo_data.py --keep-email tu-correo@dominio.com
```

---

## Variables de entorno y seguridad

La aplicación cifra datos sensibles (por ejemplo, la contraseña SMTP) con una clave Fernet.

- En el primer uso se genera automáticamente `data/.secret_key` con permisos restringidos.
- Si existe la variable `FLETING_SECRET_KEY`, tiene prioridad sobre el archivo local.

```bash
python -c "from app.services.encryption_service import generate_secret_key; print(generate_secret_key())"
export FLETING_SECRET_KEY="la-clave-generada"
```

> Si cambias la clave, los valores cifrados con la anterior no podrán descifrarse. Vuelve a guardar la contraseña SMTP desde **Mi Empresa**.

---

## Ejecutar las pruebas

```bash
python -m unittest discover -s tests -t .
```

Las pruebas usan una base de datos temporal y stubs para dependencias opcionales, por lo que no modifican `data/fleting.db`.

---

## Compilar para móvil o escritorio

```bash
flet build apk      # Android
flet build linux    # Escritorio Linux
```

Si aparece un error como:

```text
ERROR: Could not find a version that satisfies the requirement
       cffi==2.1.1 (from versions: 2.0.0)
```

significa que `requirements.txt` contiene versiones transitivas que no existen en el índice de la plataforma destino. Usa el `requirements.txt` depurado del repositorio (solo dependencias directas) y no un `pip freeze` completo.

---

## Importación y exportación

Las vistas de **Clientes**, **Productos**, **Facturas** y **Cotizaciones** incluyen una barra con cuatro acciones:

- **Importar:** carga un archivo Excel (`.xlsx`).
- **Plantilla:** descarga un Excel vacío con una hoja de instrucciones.
- **Excel:** exporta el listado actual.
- **PDF:** exporta el listado actual a PDF.

Reglas:

- **Clientes:** se actualizan por `identificacion`.
- **Productos:** se actualizan por `codigo`; si falta, se busca por nombre y se genera uno.
- **Facturas/Cotizaciones:** cada `grupo` del archivo genera un comprobante nuevo. La importación **no** descuenta stock ni envía correos.

La lógica está en `core/import_export.py` y `core/documents/`.

---

## Solución de problemas

| Problema | Solución |
|---|---|
| `flet: command not found` | Activa el entorno virtual e instala `requirements-dev.txt`. |
| `fleting: command not found` | Ejecuta `pip install fleting` dentro del entorno virtual. |
| `❌ main.py not found` | Ejecuta el comando desde la raíz del proyecto. |
| `bin/fleting` no funciona | El lanzador apunta al `.venv` de otra máquina; usa `fleting run` o `flet run main.py`. |
| La app abre sin datos | Verifica que `data/fleting.db` exista y que las migraciones/seeds se hayan aplicado. |
| Error de MySQL | MySQL aún no está implementado; usa `ENGINE = "sqlite"`. |
| No se puede enviar al SRI | Revisa el certificado `.p12`, la clave de firma y la configuración de la empresa. |
| No llegan correos | Configura y prueba el SMTP en **Mi Empresa**. |

---

## Documentación adicional

- `SPEC.md`: especificación técnica completa (arquitectura, modelo de datos, flujos SRI, seguridad y deuda técnica).
- Código del framework: [Fleting](https://github.com/alexyucra/fleting).
- Documentación de Flet: [flet.dev](https://flet.dev).

---

Hecho con Python, Flet y Fleting.
