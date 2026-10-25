# SPEC.md — Especificación técnica de TntPos

> **Documento:** especificación de arquitectura, módulos, dependencias y estructura del proyecto.
> **Aplicación:** TntPos — punto de venta y facturación electrónica para Ecuador (SRI).
> **Repositorio:** `loginFleting`
> **Fecha de análisis:** 2026-10-24
> **Estado de referencia:** commit `1f4b9ff` (`fix: recuperar autorización cuando el SRI reporta clave registrada`)
> **Pruebas:** 69 pruebas automatizadas aprobadas.

---

## 1. Resumen ejecutivo

TntPos es una aplicación monolítica de escritorio y móvil construida con **Python + Flet 1.x**. Implementa un ERP ligero orientado a pequeños y medianos negocios de Ecuador:

- Punto de venta (POS) con carrito, descuentos, IVA, ICE, propina y formas de pago.
- Facturación electrónica con generación de XML, firma XAdES-BES, envío a los web services del SRI, consulta de autorización y generación del RIDE en PDF.
- Cotizaciones/proformas con PDF, envío por correo y WhatsApp, y conversión a factura.
- Inventario con entradas, salidas, ventas, ajustes e historial de movimientos.
- Catálogos de clientes, proveedores, productos y servicios.
- Administración de usuarios, roles y permisos.
- Importación/exportación de datos a Excel y exportación de listados a PDF.
- Configuración de empresa, logo, certificado digital `.p12/.pfx` y SMTP.

La aplicación usa **SQLite** como base de datos local y no requiere un servidor propio; solo necesita conexión a internet para el SRI y el SMTP. Las migraciones y los seeds se aplican automáticamente al iniciar.

---

## 2. Objetivos y alcance

### 2.1 Objetivos funcionales

1. Emitir facturas electrónicas válidas para el SRI de Ecuador.
2. Mantener trazabilidad completa del comprobante: XML generado, XML firmado, XML autorizado, RIDE y respuesta del SRI.
3. Permitir operar el negocio sin infraestructura adicional: base local, archivos locales y SMTP.
4. Ofrecer una interfaz adaptable a móvil, tablet y escritorio.
5. Mantener permisos por rol y por módulo para lectura, escritura, actualización y eliminación.

### 2.2 Fuera de alcance actual

- Servidor multiusuario o API HTTP.
- Motor MySQL operativo.
- Facturación de notas de crédito, retenciones, guías de remisión o comprobantes distintos de factura.
- Integración con bancos, pasarelas de pago o lectores de código de barras.
- Firma electrónica con certificados distintos de PKCS#12.
- Envío automático al SRI al crear la factura: el envío es una acción explícita desde la vista de facturas.

---

## 3. Stack tecnológico y dependencias

### 3.1 Runtime

| Dependencia | Versión declarada | Uso |
|---|---:|---|
| `flet` | `>=0.86.5` | Framework de UI, escritorio y móvil. Se usa `ft.run()` (Flet 1.x). |
| `bcrypt` | `>=4.0.0` | Hash y verificación de contraseñas de usuarios. |
| `cryptography` | `>=42.0.0` | Cifrado Fernet del SMTP, lectura de certificados PKCS#12 y firma. |
| `openpyxl` | `>=3.1.0` | Importación/exportación de archivos `.xlsx`. |
| `qrcode` | `>=7.4.2` | Generación del QR de verificación del RIDE. |
| `reportlab` | `>=4.0.0` | Generación de RIDE, cotizaciones, listados PDF y Code 128. |
| `pillow` | `>=10.0.0` | Procesamiento y optimización de logos e imágenes de productos. |
| `Faker` | `>=24.0.0` | Dependencia declarada; las pruebas incluyen un stub si no está instalada. La aplicación no la importa directamente. |
| `signxml` | `>=5.0` | Firma XAdES-BES del XML del SRI. |
| `requests` | `>=2.31` | Cliente HTTP para los web services SOAP del SRI. |

Dependencias transitivas relevantes: `lxml` (usada por `signxml`), `cffi` y otras utilidades de Flet. El proyecto evita fijar el árbol completo con `pip freeze` porque algunas versiones no existen para Android.

La aplicación también usa la librería estándar: `sqlite3`, `smtplib`, `email`, `xml.etree`, `threading`, `pathlib`, `subprocess`, `tempfile` y `unittest`.

### 3.2 Desarrollo

| Dependencia | Uso |
|---|---|
| `flet-cli` | Ejecutar y compilar la app. |
| `flet-desktop` | Runtime de escritorio para desarrollo. |

Archivo: `requirements-dev.txt`, que incluye `-r requirements.txt`.

### 3.3 Dependencias opcionales / carga diferida

- `signxml` y `lxml` se importan dentro de `_SRIXAdESSigner.create()` y `_firmar_xml()`. Si no están disponibles, el envío al SRI devuelve un error explicativo, pero el resto de la app sigue funcionando.
- `PIL` se importa dentro de los controladores de logo/producto.
- `qrcode` se importa al inicio de `pdf_service.py`.

### 3.4 Plataformas

- Escritorio: Windows, Linux, macOS.
- Móvil: Android/iOS mediante Flet/serious_python.
- En Android, los datos persistentes se separan del código de la app para sobrevivir a actualizaciones (ver `core/paths.py`).

---

## 4. Estructura del proyecto

```text
loginFleting/
├── main.py                       # Punto de entrada Flet
├── requirements.txt              # Dependencias de runtime
├── requirements-dev.txt          # Dependencias de desarrollo
├── README.md                     # Plantilla genérica de Flet (no específica del proyecto)
├── SPEC.md                       # Este documento
├── .fleting                      # Marca de proyecto Flet
├── bin/
│   └── fleting                   # Lanzador local que usa .venv
├── configs/
│   ├── app_config.py             # Nombre, tamaños de pantalla, tema por defecto
│   ├── database.py               # Configuración SQLite/MySQL
│   ├── routes.py                 # Definición y carga perezosa de rutas
│   └── languages/
│       ├── es.json
│       ├── en.json
│       └── pt.json
├── core/
│   ├── base_model.py             # QuerySet y CRUD genérico
│   ├── database.py               # Conexión SQLite, transacciones, init de BD
│   ├── migrations.py             # Tabla de migraciones y aplicación/rollback
│   ├── orm.py                    # ForeignKey / HasMany
│   ├── router.py                 # Router propio, historial y guards de auth/módulo
│   ├── state.py                  # Estado global de sesión y permisos
│   ├── theme.py                  # Paleta semántica claro/oscuro/sistema
│   ├── i18n.py                   # Traducciones JSON
│   ├── responsive.py             # Breakpoints y tamaños de diálogo
│   ├── preferences.py            # Persistencia de tema/idioma
│   ├── logger.py                 # Logging a archivo y consola
│   ├── error_handler.py          # Manejo global de errores de UI
│   ├── import_export.py          # Importación/exportación Excel y PDF de listados
│   ├── table_filters.py          # Utilidad auxiliar de filtros de tablas
│   └── documents/
│       ├── excel_io.py           # Lectura/escritura de Excel
│       ├── list_pdf.py           # Exportación de listados a PDF
│       ├── pdf_common.py         # Estilos y utilidades PDF
│       └── storage.py            # Rutas de exportaciones
├── app/
│   ├── models/                   # Modelos de tabla
│   ├── controllers/              # Lógica de negocio y casos de uso
│   ├── services/                 # Integraciones y servicios técnicos
│   └── views/
│       ├── layouts/
│       │   └── main_layout.py    # AppBar + contenido + NavigationBar
│       ├── components/
│       │   └── import_export.py  # Barra reutilizable de importar/exportar
│       ├── pages/                # Vistas por ruta
│       └── ui_helpers.py         # Diálogos, toasts, archivos, share, URLs
├── migrations/                   # Migraciones idempotentes 001–014
├── seeds/                        # Datos iniciales idempotentes (incluye 007_advanced_roles_seed)
├── scripts/
│   └── clean_demo_data.py        # Limpieza de datos de prueba
├── tests/                        # Pruebas unittest
├── assets/                       # Recursos estáticos y documentos generados
├── data/                         # SQLite, clave local y preferencias
└── logs/                         # Logs de ejecución
```

### 4.1 Directorios generados

No deben versionarse; están cubiertos por `.gitignore`:

- `assets/invoices/xml/`
- `assets/invoices/pdf/`
- `assets/quotations/pdf/`
- `assets/products/images/`
- `assets/company/`
- `assets/certs/`
- `assets/exports/`
- `data/fleting.db`
- `data/.secret_key`
- `preferences.json`
- `logs/`

---

## 5. Arquitectura

### 5.1 Estilo arquitectónico

La aplicación sigue una arquitectura en capas inspirada en MVC:

```text
┌─────────────────────────────────────────────────────────────┐
│ Presentación                                                │
│ app/views/pages/*, app/views/layouts/*, ui_helpers          │
└───────────────────────────┬─────────────────────────────────┘
                            │ llama
┌───────────────────────────▼─────────────────────────────────┐
│ Aplicación / casos de uso                                   │
│ app/controllers/*                                           │
└───────────────┬───────────────────────────────┬─────────────┘
                │ usa                           │ usa
┌───────────────▼───────────────┐   ┌───────────▼─────────────┐
│ Dominio / persistencia        │   │ Servicios               │
│ app/models/*                  │   │ app/services/*          │
│ core/base_model.py            │   │ XML, SRI, PDF, correo,  │
│ core/orm.py                   │   │ cifrado, WhatsApp, etc. │
└───────────────┬───────────────┘   └───────────┬─────────────┘
                │                               │
┌───────────────▼───────────────────────────────▼─────────────┐
│ Infraestructura                                             │
│ core/database.py, core/paths.py, core/logger.py             │
│ SQLite, archivos locales, SMTP, HTTP SOAP                   │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Reglas de dependencia

- Las vistas **no deberían** acceder directamente a SQL; usan controladores.
- Los controladores orquestan modelos, transacciones y servicios.
- Los modelos solo mapean tablas y relaciones; no contienen reglas de negocio complejas.
- Los servicios encapsulan integraciones (SRI, SMTP, PDF, Excel, cifrado) y utilidades de catálogo.
- `core` contiene infraestructura reutilizable e independiente de la pantalla.

**Excepciones observadas:**

- `app/views/pages/quotations_view.py` y `quotation_new_view.py` importan `CompanyModel` para obtener el nombre de la empresa.
- Varias vistas importan `app.services.sri_catalogs` para mostrar etiquetas y opciones.
- `core/import_export.py` importa controladores de `app`, lo que invierte parcialmente la dirección de dependencia (`core → app`).

### 5.3 Flujo de arranque

```text
main.py
  ├─ configura página, assets y título
  ├─ carga preferencias (tema/idioma)
  ├─ aplica tema y carga traducciones
  ├─ crea Router(page)
  ├─ detecta dispositivo y registra on_resize / brillo
  ├─ navega a /login
  └─ si hay error global → GlobalErrorHandler
```

`Router` carga las rutas desde `configs.routes`, aplica los guards de autenticación y de módulo, y renderiza la vista correspondiente dentro de `page.controls`.

### 5.4 Navegación

- Router propio, sin `ft.Route` ni `page.views`.
- `Router.navigate(path)` resuelve la ruta, aplica auth, valida el módulo y renderiza.
- Cada ruta declara un `module` (`pos`, `clients`, `inventory`, etc.). Si el rol no tiene `can_read` sobre ese módulo, el router redirige a la primera ruta permitida.
- Historial de ida/vuelta (`go_back`, `go_forward`).
- `rerender()` se usa al cambiar tema, idioma o categoría de dispositivo.
- En cada render se limpian `page.controls`, `page.overlay`, `page.appbar`, `page.bottom_app_bar` y `page.dialog`.

### 5.5 Autenticación y sesión

- `LoginView` llama a `LoginController.authenticate`.
- `UserModel.authenticate` verifica `bcrypt` y devuelve un diccionario con:
  - `id`, `name`, `email`, `role_id`, `role`, `permissions`, `module_permissions`, `status`.
- `permissions` conserva los flags globales heredados (`can_read/write/update/delete`).
- `module_permissions` es la matriz `módulo -> acciones` y es la fuente de verdad para el acceso.
- `AppState.current_user` guarda la sesión **en memoria**.
- `AppState.has_permission(clave, modulo=None)` falla de forma segura:
  - Con `modulo`, consulta `module_permissions`; si la matriz existe y el módulo no está, deniega.
  - Sin `modulo`, consulta los flags globales (compatibilidad y pruebas).
  - Sin sesión o sin permisos devuelve `False`.
- `Router._resolve` redirige a `/login` para rutas protegidas sin sesión y a la primera ruta permitida cuando falta el permiso de módulo.
- La única ruta pública es `/login`.

> No hay persistencia de sesión: al reiniciar la app se debe volver a iniciar sesión.

### 5.6 UI adaptable

- `core/responsive.py`: móvil `< 800`, tablet `<= 1024`, escritorio `> 1024`.
- `MainLayout` usa `page.appbar` y `NavigationBar`; en escritorio muestra acciones rápidas.
- Las vistas usan `is_mobile_page(page)` para cambiar entre tablas y tarjetas.
- `core/theme.py` expone tokens semánticos (`T.TEXT`, `T.SURFACE`, `T.BORDER`, etc.) y paletas clara/oscura/sistema.
- `ui_helpers.py` centraliza diálogos, toasts, FilePicker, Share, UrlLauncher, apertura de archivos y WhatsApp.

---

## 6. Núcleo (`core/`)

### 6.1 Módulos principales

| Módulo | Responsabilidad |
|---|---|
| `core/paths.py` | Define `BASE_DIR`, `DATA_DIR`, `ASSETS_DIR` y `GENERATED_DIR`. En Android separa código de datos persistentes. |
| `core/database.py` | Conexión SQLite singleton, `PRAGMA foreign_keys=ON`, lock de escritura, transacciones anidadas y arranque de migraciones/seeds. |
| `core/migrations.py` | Crea `_fleting_migrations`, consulta aplicadas, aplica y revierte migraciones. |
| `core/orm.py` | `ForeignKey` y `HasMany` para resolver relaciones. |
| `core/base_model.py` | `QuerySet` (`all`, `first`, `find`, `where`, `count`, `exists`) y CRUD (`create`, `update_by_id`, `delete_by_id`, instancia `save/update/delete`). |
| `core/router.py` | Carga de vistas, guards de auth y módulo, historial y renderizado. |
| `core/state.py` | Estado global: dispositivo, idioma, tema, ruta, usuario, permisos y carrito pendiente. |
| `core/theme.py` | Paletas y tokens de color; `apply(page, mode)` y seguimiento del brillo del sistema. |
| `core/i18n.py` | Carga `configs/languages/{lang}.json` y resuelve claves anidadas con `I18n.t("menu.pos")`. |
| `core/responsive.py` | Breakpoints y utilidades de ancho de diálogo. |
| `core/preferences.py` | Lee/escribe `DATA_DIR/preferences.json`. |
| `core/logger.py` | Configura logging a archivo y consola. |
| `core/error_handler.py` | Pantalla genérica de error global. |
| `core/import_export.py` | Importación/exportación de clientes, productos, facturas y cotizaciones; plantillas Excel y listados PDF. |
| `core/table_filters.py` | Utilidad para excluir tablas internas al generar modelos; sin referencias en el código actual. |
| `core/documents/*` | Lectura/escritura Excel, PDF de listados, estilos compartidos y rutas de exportación. |

### 6.2 Base de datos y transacciones

- `get_connection()` crea una única conexión SQLite (`check_same_thread=False`) y ejecuta `init_db()` una sola vez.
- `transaction()` agrupa escrituras y usa `_write_lock` (RLock). Los `commit()` del ORM son no-op dentro de la transacción.
- Si una operación falla, se hace rollback y se propaga la excepción.
- Las transacciones anidadas incrementan `tx_depth`; solo la transacción externa confirma o revierte.
- `DATABASE["ENGINE"]` acepta `sqlite`; `mysql` existe en configuración pero `_connect_mysql()` lanza `NotImplementedError`.

### 6.3 Migraciones y seeds automáticos

Al inicializar:

1. Se crea `_fleting_migrations` si no existe.
2. Se leen las migraciones aplicadas.
3. Se importan los módulos de `migrations/` en orden alfabético y se aplican los pendientes.
4. Se importan los módulos de `seeds/` en orden alfabético y se aplican los pendientes.
5. Se excluyen `__init__` e `initial` (el seed `initial.py` está obsoleto).

La misma tabla registra migraciones y seeds, por lo que ambos son idempotentes a nivel de ejecución.

### 6.4 ORM

- `BaseModel.table_name` define la tabla.
- `QuerySet` usa `SELECT *` y convierte filas a diccionarios sin modificar `conn.row_factory`.
- Relaciones:
  - `ForeignKey("clients", "client_id")` resuelve el objeto relacionado.
  - `HasMany("invoice_items", "invoice_id")` resuelve listas.
- `with_("items", "client")` activa relaciones por consulta.
- No hay migraciones automáticas de esquema ni validación de tipos; los controladores validan.

---

## 7. Configuración (`configs/`)

| Archivo | Contenido |
|---|---|
| `configs/app_config.py` | `APP_NAME = "TntPos"`, tamaños móvil/tablet/escritorio y `DEFAULT_THEME_MODE = "system"`. |
| `configs/database.py` | Motor (`sqlite` por defecto), ruta SQLite (`data/fleting.db`) y parámetros MySQL no implementados. |
| `configs/routes.py` | Lista `ROUTES` con path, clase de vista, etiqueta i18n, icono, módulo de permisos y visibilidad en barra superior/inferior. Carga perezosa con `importlib`. |
| `configs/languages/es.json` | Traducciones español. |
| `configs/languages/en.json` | Traducciones inglés. |
| `configs/languages/pt.json` | Traducciones portugués. |

Las traducciones actuales cubren menú, inicio y ajustes; muchas cadenas de las vistas están escritas directamente en español.

---

## 8. Modelo de datos

### 8.1 Entidades y relaciones

```text
roles 1 ──── N users
roles 1 ──── N role_permissions
clients 1 ── N invoices
clients 1 ── N quotations
suppliers 1 ─ N products
invoices 1 ─ N invoice_items
quotations 1 ─ N quotation_items
products 1 ─ N inventory_movements
quotations 0..1 ── 0..1 invoices   (quotations.invoice_id)
```

### 8.2 Esquema físico

#### `roles`

```text
id INTEGER PK AUTOINCREMENT
name TEXT NOT NULL UNIQUE
description TEXT
can_read INTEGER DEFAULT 1
can_write INTEGER DEFAULT 1
can_update INTEGER DEFAULT 1
can_delete INTEGER DEFAULT 1
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

#### `role_permissions`

```text
id INTEGER PK AUTOINCREMENT
role_id INTEGER NOT NULL FK roles(id) ON DELETE CASCADE
module TEXT NOT NULL                  -- home, pos, invoices, clients, ...
can_read INTEGER DEFAULT 0
can_write INTEGER DEFAULT 0
can_update INTEGER DEFAULT 0
can_delete INTEGER DEFAULT 0
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
UNIQUE (role_id, module)
```

> Las columnas globales de `roles` se conservan por compatibilidad. La fuente de
> verdad para el acceso es `role_permissions`. El catálogo de módulos y presets
> vive en `core/permissions.py`.

#### `users`

```text
id INTEGER PK AUTOINCREMENT
name TEXT NOT NULL
email TEXT NOT NULL UNIQUE
password TEXT NOT NULL                 -- bcrypt
role_id INTEGER NOT NULL FK roles(id) ON DELETE RESTRICT
status TEXT DEFAULT 'active'
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

#### `clients`

```text
id INTEGER PK AUTOINCREMENT
tipo_documento TEXT DEFAULT 'CEDULA'
identificacion TEXT NOT NULL UNIQUE
razon_social TEXT NOT NULL
email TEXT NOT NULL
telefono TEXT
direccion TEXT
status TEXT DEFAULT 'active'
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

#### `suppliers`

```text
id INTEGER PK AUTOINCREMENT
tipo_documento TEXT DEFAULT 'RUC'
identificacion TEXT NOT NULL UNIQUE
razon_social TEXT NOT NULL
email TEXT NOT NULL
telefono TEXT
direccion TEXT
contacto TEXT
status TEXT DEFAULT 'active'
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

#### `products`

```text
id INTEGER PK AUTOINCREMENT
codigo TEXT NOT NULL UNIQUE
nombre TEXT NOT NULL
descripcion TEXT
precio REAL NOT NULL DEFAULT 0.0
costo REAL DEFAULT 0.0
stock INTEGER DEFAULT 0
iva_porcentaje REAL DEFAULT 15.0
categoria TEXT DEFAULT 'General'
status TEXT DEFAULT 'active'
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
stock_minimo INTEGER DEFAULT 5            -- migración 010
imagen_path TEXT DEFAULT ''               -- migración 008
supplier_id INTEGER                       -- migración 012
ice_codigo TEXT DEFAULT ''                -- migración 013
ice_porcentaje REAL DEFAULT 0.0           -- migración 013
```

#### `services`

```text
id INTEGER PK AUTOINCREMENT
codigo TEXT NOT NULL UNIQUE
nombre TEXT NOT NULL
descripcion TEXT
precio REAL NOT NULL DEFAULT 0.0
iva_porcentaje REAL DEFAULT 15.0
categoria TEXT DEFAULT 'Servicios'
status TEXT DEFAULT 'active'
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
ice_codigo TEXT DEFAULT ''                -- migración 013
ice_porcentaje REAL DEFAULT 0.0           -- migración 013
```

#### `company`

```text
id INTEGER PK AUTOINCREMENT
ruc TEXT NOT NULL DEFAULT '1790000000001'
razon_social TEXT NOT NULL DEFAULT 'MI EMPRESA S.A.'
nombre_comercial TEXT DEFAULT 'MI NEGOCIO'
direccion_matriz TEXT DEFAULT 'Av. Principal 123'
telefono TEXT DEFAULT '0999999999'
email TEXT DEFAULT 'facturacion@empresa.com'
ambiente_sri INTEGER DEFAULT 1            -- 1 pruebas, 2 producción
establecimiento TEXT DEFAULT '001'
punto_emision TEXT DEFAULT '001'
secuencial_factura INTEGER DEFAULT 1
contribuyente_especial TEXT DEFAULT ''
obligado_contabilidad TEXT DEFAULT 'NO'
firma_path TEXT DEFAULT ''
firma_pass TEXT DEFAULT ''
sri_email TEXT DEFAULT 'recepcion.sri@sri.gob.ec'
smtp_host TEXT DEFAULT 'smtp.gmail.com'
smtp_port INTEGER DEFAULT 587
smtp_user TEXT DEFAULT ''
smtp_pass TEXT DEFAULT ''                 -- cifrado Fernet
smtp_ssl INTEGER DEFAULT 0
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
secuencial_cotizacion INTEGER DEFAULT 1  -- migración 006
logo_path TEXT DEFAULT ''                 -- migración 011
direccion_establecimiento TEXT DEFAULT '' -- migración 013
agente_retencion TEXT DEFAULT ''          -- migración 013
```

#### `invoices`

```text
id INTEGER PK AUTOINCREMENT
secuencial TEXT NOT NULL UNIQUE
clave_acceso TEXT UNIQUE
client_id INTEGER FK clients(id) ON DELETE SET NULL
client_nombre TEXT NOT NULL
client_identificacion TEXT NOT NULL
client_email TEXT NOT NULL
client_direccion TEXT
fecha_emision TEXT NOT NULL
subtotal_15 REAL DEFAULT 0.0
subtotal_0 REAL DEFAULT 0.0
subtotal_sin_impuestos REAL DEFAULT 0.0
total_descuento REAL DEFAULT 0.0
iva_total REAL DEFAULT 0.0
importe_total REAL DEFAULT 0.0
forma_pago TEXT DEFAULT 'EFECTIVO'
estado TEXT DEFAULT 'GENERADA'
xml_path TEXT
pdf_path TEXT
sri_mensaje TEXT
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
email_estado TEXT DEFAULT ''              -- migración 012
sri_respuesta TEXT DEFAULT ''             -- migración 012
sri_autorizacion TEXT DEFAULT ''          -- migración 012
sri_fecha_autorizacion TEXT DEFAULT ''    -- migración 012
sri_fecha_envio TEXT DEFAULT ''           -- migración 012
ice_total REAL DEFAULT 0.0                -- migración 013
propina REAL DEFAULT 0.0                  -- migración 013
```

#### `invoice_items`

```text
id INTEGER PK AUTOINCREMENT
invoice_id INTEGER NOT NULL FK invoices(id) ON DELETE CASCADE
tipo TEXT NOT NULL                        -- producto | servicio
item_id INTEGER
codigo TEXT NOT NULL
descripcion TEXT NOT NULL
cantidad REAL NOT NULL DEFAULT 1
precio_unitario REAL NOT NULL DEFAULT 0.0
descuento REAL DEFAULT 0.0
subtotal REAL NOT NULL DEFAULT 0.0
iva_porcentaje REAL DEFAULT 15.0
valor_iva REAL DEFAULT 0.0
total REAL NOT NULL DEFAULT 0.0
ice_codigo TEXT DEFAULT ''                -- migración 013
ice_porcentaje REAL DEFAULT 0.0           -- migración 013
valor_ice REAL DEFAULT 0.0                -- migración 013
```

#### `quotations`

```text
id INTEGER PK AUTOINCREMENT
secuencial TEXT NOT NULL UNIQUE
client_id INTEGER FK clients(id) ON DELETE SET NULL
client_nombre TEXT NOT NULL
client_identificacion TEXT NOT NULL
client_email TEXT NOT NULL
client_direccion TEXT
fecha_emision TEXT NOT NULL
fecha_validez TEXT NOT NULL
subtotal_15 REAL DEFAULT 0.0
subtotal_0 REAL DEFAULT 0.0
subtotal_sin_impuestos REAL DEFAULT 0.0
total_descuento REAL DEFAULT 0.0
iva_total REAL DEFAULT 0.0
importe_total REAL DEFAULT 0.0
estado TEXT DEFAULT 'EMITIDA'
pdf_path TEXT
notas TEXT
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
enviada_whatsapp INTEGER DEFAULT 0        -- migración 007
invoice_id INTEGER                        -- migración 009
ice_total REAL DEFAULT 0.0                -- migración 013
```

#### `quotation_items`

```text
id INTEGER PK AUTOINCREMENT
quotation_id INTEGER NOT NULL FK quotations(id) ON DELETE CASCADE
tipo TEXT NOT NULL
item_id INTEGER
codigo TEXT NOT NULL
descripcion TEXT NOT NULL
cantidad REAL NOT NULL DEFAULT 1
precio_unitario REAL NOT NULL DEFAULT 0.0
descuento REAL DEFAULT 0.0
subtotal REAL NOT NULL DEFAULT 0.0
iva_porcentaje REAL DEFAULT 15.0
valor_iva REAL DEFAULT 0.0
total REAL NOT NULL DEFAULT 0.0
ice_codigo TEXT DEFAULT ''                -- migración 013
ice_porcentaje REAL DEFAULT 0.0           -- migración 013
valor_ice REAL DEFAULT 0.0                -- migración 013
```

#### `inventory_movements`

```text
id INTEGER PK AUTOINCREMENT
product_id INTEGER FK products(id) ON DELETE SET NULL
product_codigo TEXT
product_nombre TEXT
tipo TEXT NOT NULL                        -- INICIAL | ENTRADA | SALIDA | VENTA | AJUSTE
cantidad INTEGER NOT NULL DEFAULT 0
stock_anterior INTEGER NOT NULL DEFAULT 0
stock_nuevo INTEGER NOT NULL DEFAULT 0
motivo TEXT
referencia TEXT
created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
```

Índices:

```text
idx_inventory_movements_product(product_id, id)
idx_inventory_movements_created(created_at)
```

#### `_fleting_migrations`

```text
id INTEGER PK AUTOINCREMENT
name TEXT UNIQUE
```

### 8.3 Tablas no implementadas

`SettingsModel` (`settings`) y `HelpModel` (`help`) existen como modelos/controladores de marcador, pero **no tienen migración ni tabla en la base actual**. Las vistas de ajustes y ayuda no persisten datos en esas tablas: ajustes solo guarda tema/idioma en preferencias y ayuda es estática.

---

## 9. Módulos de la aplicación

### 9.1 Modelos (`app/models/`)

| Modelo | Tabla | Particularidades |
|---|---|---|
| `ClientModel` | `clients` | CRUD simple. |
| `CompanyModel` | `company` | `get_info()` devuelve la primera fila o crea una configuración vacía. |
| `HelpModel` | `help` | Marcador sin tabla. |
| `InventoryMovementModel` | `inventory_movements` | Historial de stock. |
| `InvoiceModel` | `invoices` | Relaciones `items` (HasMany) y `client` (ForeignKey). |
| `InvoiceItemModel` | `invoice_items` | Relación `invoice`. |
| `ProductModel` | `products` | Relación `supplier`. |
| `QuotationModel` | `quotations` | Relaciones `items` y `client`. |
| `QuotationItemModel` | `quotation_items` | Relación `quotation`. |
| `RoleModel` | `roles` | Relación `users` (HasMany). |
| `RolePermissionModel` | `role_permissions` | Permisos CRUD de un rol por módulo. |
| `ServiceModel` | `services` | CRUD simple. |
| `SettingsModel` | `settings` | Marcador sin tabla. |
| `SupplierModel` | `suppliers` | CRUD simple. |
| `UserModel` | `users` | Hash bcrypt, autenticación y permisos derivados del rol. |

### 9.2 Controladores (`app/controllers/`)

| Controlador | Responsabilidad y métodos principales |
|---|---|
| `LoginController` | `authenticate(email, password)` → delega en `UserModel`. |
| `ClientController` | CRUD de clientes, validación de email/identificación y unicidad. |
| `SupplierController` | CRUD de proveedores con validación y unicidad. |
| `ProductController` | CRUD de productos, imágenes optimizadas, proveedor, stock mínimo, ICE y movimientos de stock. |
| `ServiceController` | CRUD de servicios, validación de ICE y precios. |
| `InventoryController` | Resumen de inventario, alertas, historial, entradas/salidas/ventas, ajuste absoluto y registro de cambios. |
| `CompanyController` | Configuración de empresa, logo, certificado `.p12`, SMTP cifrado, secuenciales y datos SRI. |
| `InvoiceController` | Creación de facturas, XML, RIDE, envío al SRI, recuperación de autorización, correo y reenvío. |
| `QuotationController` | Creación de cotizaciones, PDF regenerable, correo, WhatsApp, conversión a factura y borrado protegido. |
| `UserController` | CRUD de usuarios, roles, estado y contraseña. |
| `RoleController` | CRUD de roles, matriz de permisos por módulo y presets (`vendedor`, `bodeguero`, etc.). |
| `SettingsController` | Marcador; solo devuelve el título de la vista. |
| `HelpController` | Marcador; solo devuelve el título de la vista. |

### 9.3 Servicios (`app/services/`)

| Servicio | Responsabilidad |
|---|---|
| `xml_service.py` | Genera la clave de acceso de 49 dígitos (módulo 11) y el XML de factura SRI v1.1.0: `infoTributaria`, `infoFactura`, impuestos, ICE, propina, pagos y detalles. |
| `sri_service.py` | Firma XAdES-BES (RSA-SHA1/SHA1), envía recepción SOAP, consulta autorización con reintentos, parsea mensajes, detecta error 43 y guarda el XML autorizado. |
| `sri_catalogs.py` | Catálogo de formas de pago SRI, normalización/etiquetas, validación de ICE y cálculo de línea (subtotal, ICE, base IVA, IVA, total). |
| `pdf_service.py` | Genera el RIDE de factura y el PDF de cotización. Incluye Code 128, QR de verificación SRI, cabecera, comprador, detalle, totales y leyendas. |
| `email_service.py` | Envío SMTP con TLS/SSL, validación de destinatarios, adjuntos PDF/XML, plantillas de factura y cotización. |
| `encryption_service.py` | Cifrado simétrico Fernet con clave derivada por PBKDF2-SHA256; usa `FLETING_SECRET_KEY` o `DATA_DIR/data/.secret_key`. |
| `signature_service.py` | Valida y copia certificados `.p12/.pfx` a `assets/certs/`. |
| `excel_service.py` | Exportaciones Excel independientes; actualmente solo la usa la vista de proveedores. |
| `whatsapp_service.py` | Normaliza teléfonos, construye enlaces `wa.me` y mensajes de cotización. |

### 9.4 Vistas y rutas (`app/views/pages/`)

| Ruta | Vista | Descripción |
|---|---|---|
| `/` | `HomeView` | Dashboard con bienvenida, estadísticas y tarjetas de módulos. |
| `/login` | `LoginView` | Inicio de sesión; única ruta pública. |
| `/pos` | `POSView` | Punto de venta: catálogo, carrito, cliente, descuentos, propina, pago y emisión. |
| `/invoices` | `InvoicesView` | Listado de facturas, detalle, envío al SRI, respuesta, reenvío de correo, PDF/XML e importación/exportación. |
| `/quotations` | `QuotationsView` | Listado de cotizaciones, PDF, correo, WhatsApp, conversión a factura y borrado. |
| `/quotations/new` | `QuotationNewView` | Creación de cotización con el mismo patrón de carrito del POS. |
| `/clients` | `ClientsView` | CRUD de clientes, búsqueda e importación/exportación. |
| `/suppliers` | `SuppliersView` | CRUD de proveedores y exportación Excel. |
| `/products` | `ProductsView` | CRUD de productos, imágenes, proveedor, stock, ICE e importación/exportación. |
| `/inventory` | `InventoryView` | Resumen, alertas, movimientos manuales e historial. |
| `/services` | `ServicesView` | CRUD de servicios, ICE y envío al POS/cotización. |
| `/company` | `CompanyView` | Datos de empresa, SRI, SMTP, logo, firma y secuenciales. |
| `/users` | `UsersView` | CRUD de usuarios, rol, estado y contraseña. |
| `/roles` | `RolesView` | CRUD de roles y permisos. |
| `/settings` | `SettingsView` | Tema e idioma. |
| `/help` | `HelpView` | Enlaces de ayuda (contenido legado de Fleting). |

### 9.5 Layout y componentes

- `app/views/layouts/main_layout.py`
  - `AppBar` con usuario, rol, historial atrás/adelante, acciones rápidas y menú.
  - Contenido central.
  - `NavigationBar` inferior con rutas marcadas `show_in_bottom`.
  - Logout limpia `AppState.current_user` y navega a `/login`.

- `app/views/components/import_export.py`
  - Barra “Importar Excel · Plantilla · Excel · PDF”.
  - Usa `core.import_export` y `ui_helpers`.
  - Se integra en clientes, productos, facturas y cotizaciones.

- `app/views/ui_helpers.py`
  - Diálogos (`open_dialog`, `close_dialog`), toasts, FilePicker, Share, UrlLauncher.
  - Apertura de archivos en escritorio/móvil.
  - Compartición de PDF para WhatsApp.
  - Diálogo de servicio manual.
  - Tarjetas de estadísticas y anchos responsive.

---

## 10. Flujos principales

### 10.1 Inicio de sesión

1. `main.py` navega a `/login`.
2. `LoginView` valida campos y llama a `LoginController.authenticate`.
3. `UserModel.authenticate` busca por email, verifica bcrypt y obtiene el rol y su matriz de permisos por módulo.
4. Se construye `AppState.current_user` con `permissions` y `module_permissions`.
5. `Router.navigate("/")` valida el módulo `home`; si el rol no lo tiene, redirige a la primera ruta permitida (por ejemplo `/pos` o `/inventory`).

### 10.2 Emisión de factura en POS

1. El usuario selecciona cliente (o se usa `CONSUMIDOR FINAL`).
2. Agrega productos/servicios al carrito, ajusta cantidad/descuento y propina.
3. Elige forma de pago y si desea enviar correo al autorizar.
4. `InvoiceController.create_invoice`:
   - Valida carrito y stock.
   - Calcula cada línea con `calcular_totales_linea`:
     - `subtotal = cantidad * precio - descuento`
     - `valor_ice = subtotal * tarifa_ice / 100`
     - `base_iva = subtotal + valor_ice`
     - `valor_iva = base_iva * tarifa_iva / 100`
     - `total = subtotal + valor_ice + valor_iva`
   - Acumula subtotales, IVA, ICE, descuento y propina.
   - Genera secuencial `estab-ptoEmi-9dígitos`.
   - Genera clave de acceso y XML.
   - Genera RIDE marcado como pendiente de autorización.
   - Registra factura e ítems, descuenta stock y registra movimientos.
   - Incrementa `company.secuencial_factura`.
5. La factura queda en estado `GENERADA` y con correo `PENDIENTE` o `NO_ENVIAR`.
6. El envío al SRI se realiza desde `/invoices`.

### 10.3 Envío al SRI

1. `InvoicesView` llama a `InvoiceController.send_to_sri(invoice_id)`.
2. Si la factura ya está `AUTORIZADO`, no se reenvía: se regenera el RIDE y se devuelve el estado existente.
3. Si falta el XML, se regenera desde la factura y sus ítems.
4. `SRIService.send_invoice`:
   - Determina ambiente desde el XML (1 pruebas, 2 producción).
   - Firma el XML con XAdES-BES usando el `.p12` configurado.
   - Envía a `RecepcionComprobantesOffline`.
   - Si la recepción es `RECIBIDA` o hay error 43, consulta `AutorizacionComprobantesOffline` hasta 6 veces con espera de 1.5 s.
   - Parsea estado, número y fecha de autorización, mensajes y comprobante autorizado.
   - Guarda el XML autorizado como `FAC_{clave}_autorizado.xml`.
5. `InvoiceController` actualiza la factura:
   - `estado`, `sri_mensaje`, `sri_respuesta`, `sri_autorizacion`, `sri_fecha_autorizacion`, `sri_fecha_envio`, `xml_path`.
6. Si el estado es `AUTORIZADO`:
   - Regenera el RIDE con número/fecha de autorización.
   - Envía correo si `email_estado` no es `NO_ENVIAR` ni `ENVIADA`.
7. Si hay error de configuración, firma o conexión, la factura pasa a `ERROR` y se guarda el mensaje.

#### Error 43 — “CLAVE ACCESO REGISTRADA”

- Significa que la clave ya fue recibida por el SRI, normalmente por un reenvío.
- `_tiene_error_clave_registrada()` detecta el identificador `43` o el texto `CLAVE ACCESO REGISTRADA`.
- En lugar de tratarlo como rechazo definitivo, se consulta la autorización existente.
- Si la consulta devuelve `AUTORIZADO`, la factura se recupera y se regenera el RIDE.
- Si devuelve otro estado, se informa que la clave está registrada pero no autorizada.
- Una factura `AUTORIZADO` no se vuelve a enviar al SRI.

### 10.4 Generación del RIDE

`PDFService.generate_factura_pdf` produce un A4 con:

1. Cabecera: logo, razón social, nombre comercial, dirección matriz, dirección de establecimiento, contribuyente especial, agente de retención, obligado a contabilidad, teléfono, email.
2. Bloque derecho: RUC, “FACTURA”, número de comprobante, clave de acceso, número y fecha de autorización (o `PENDIENTE DE AUTORIZACION`), ambiente y tipo de emisión.
3. Datos del comprador: razón social, identificación, dirección, email, tipo de identificación y forma de pago legible.
4. Detalle: código, código auxiliar, cantidad, unidad, descripción, precio unitario, descuento, ICE y total sin impuestos.
5. Información adicional + QR.
6. Totales: subtotal sin impuestos, subtotal 0%, subtotal 15%, descuentos, IVA, ICE, propina y total.
7. Code 128 con la clave de acceso y la clave numérica impresa.
8. Leyenda de comprobante electrónico y texto “Generado por TntPos”.

El QR contiene:

```text
https://srienlinea.sri.gob.ec/comprobantes-electronicos-internet/publico/validezComprobantes.jsf?claveAcceso={clave}
```

La etiqueta del código de barras cambia a “CLAVE DE ACCESO / NUMERO DE AUTORIZACION” solo cuando la factura está autorizada.

### 10.5 Correo

- El correo de factura se envía **después** de la autorización, salvo que el usuario haya desactivado el envío.
- `EmailService.send_invoice_email` adjunta PDF (RIDE) y XML.
- Destinatarios:
  - Email del cliente, si es válido y no es `consumidor@mail.com`.
  - Email SRI configurado (`sri_email`), si es válido.
- `resend_email` usa el XML autorizado si existe y regenera el RIDE con los datos de autorización.
- Estados de correo: `PENDIENTE`, `ENVIADA`, `ERROR`, `NO_ENVIAR`.

### 10.6 Cotizaciones

1. `QuotationNewView` reutiliza el patrón de carrito del POS.
2. `QuotationController.create_quotation`:
   - Genera secuencial `COT-estab-ptoEmi-9dígitos`.
   - Calcula IVA/ICE con la misma lógica de facturas.
   - Genera PDF con imágenes de productos.
   - Guarda cotización e ítems en una transacción.
   - Incrementa `company.secuencial_cotizacion`.
3. Estado inicial: `EMITIDA`.
4. Acciones:
   - Abrir/regenerar PDF (`ensure_quotation_pdf(force=True)`).
   - Enviar por correo (`send_quotation_email`), marca `ENVIADA` si no está `FACTURADA`.
   - Compartir por WhatsApp y marcar `enviada_whatsapp`.
   - Convertir a factura (`invoice_quotation`), conservando ICE y datos del cliente.
   - Borrar solo si no está facturada.
5. La conversión marca la cotización como `FACTURADA` y guarda `invoice_id` para impedir duplicados.

### 10.7 Inventario

- `InventoryController.get_summary()` calcula productos, unidades, agotados, bajo stock y valor de inventario.
- `register_movement` admite `ENTRADA`, `SALIDA` y `VENTA`; actualiza stock y registra movimiento en una transacción.
- `set_stock` fija un valor absoluto y registra un `AJUSTE`.
- `log_stock_change` registra cambios ya aplicados (alta/edición de producto) sin volver a actualizar el stock.
- La venta en POS registra un movimiento `VENTA` con referencia al secuencial de la factura.

### 10.8 Configuración de empresa

`CompanyController`:

- `get_info()` devuelve la empresa con `smtp_pass` descifrado.
- `update_info()` valida RUC/razón social y secuenciales; cifra `smtp_pass` antes de guardar.
- `upload_logo()` optimiza la imagen a JPEG/PNG y la guarda en `assets/company/`.
- `upload_signature()` valida el `.p12/.pfx` y lo copia a `assets/certs/`.
- Los datos SRI incluyen ambiente, establecimiento, punto de emisión, contribuyente especial, obligado a contabilidad, agente de retención y dirección de establecimiento.

### 10.9 Importación/exportación

`core/import_export.py` define cuatro tipos:

| Clave | Entidad | Formato |
|---|---|---|
| `customers` | Clientes | Una fila por cliente. |
| `products` | Productos | Una fila por producto. |
| `invoices` | Facturas | Una fila por ítem, agrupadas por `grupo`. |
| `quotes` | Cotizaciones | Una fila por ítem, agrupadas por `grupo`. |

- Genera plantillas Excel con hoja de instrucciones.
- Exporta a Excel y PDF.
- Importa clientes/productos con actualización por identificación/código.
- Importa facturas/cotizaciones creando nuevos comprobantes (no reimportar el mismo archivo).
- Usa transacciones para las importaciones.

---

## 11. Reglas de negocio y convenciones SRI

### 11.1 Numeración

- Factura: `001-001-000000001` (`establecimiento-puntoEmisión-secuencial`).
- Cotización: `COT-001-001-000000001`.
- `company.secuencial_factura` y `company.secuencial_cotizacion` se incrementan dentro de la transacción de creación.

### 11.2 Clave de acceso (49 dígitos)

```text
Fecha de emisión (8)       ddmmaaaa
Tipo de comprobante (2)    01 = factura
RUC (13)
Ambiente (1)               1 = pruebas, 2 = producción
Serie (6)                  establecimiento (3) + punto de emisión (3)
Secuencial (9)
Código numérico (8)        aleatorio
Tipo de emisión (1)        1 = normal
Dígito verificador (1)     módulo 11
```

La clave se conserva como texto numérico y se usa en el XML, el Code 128 y el QR.

### 11.3 Formas de pago

| Clave interna | Código SRI | Etiqueta |
|---|---:|---|
| `EFECTIVO` | `01` | Efectivo / Sin utilización del sistema financiero |
| `TARJETA_DEBITO` | `16` | Tarjeta de débito |
| `TARJETA_CREDITO` | `19` | Tarjeta de crédito |
| `TRANSFERENCIA` | `20` | Transferencia bancaria / Otros con utilización del sistema financiero |
| `TARJETA` | `20` | Tarjeta (sin especificar) — compatibilidad |
| `OTROS` | `20` | Otros con utilización del sistema financiero |

`normalizar_forma_pago` acepta alias como `CONTADO`, `DEBITO`, `CREDITO`, `DEPOSITO`, etc.

### 11.4 ICE e IVA

- El código ICE del SRI es un código de producto de **4 dígitos** (ej. `3031`), no la tarifa.
- La tarifa ICE es un porcentaje independiente.
- Si la tarifa ICE es 0, el código se normaliza a vacío.
- `subtotal` es el precio total sin impuestos.
- `valor_ice = subtotal * tarifa_ice / 100`.
- La base del IVA incluye el ICE: `base_iva = subtotal + valor_ice`.
- `valor_iva = base_iva * tarifa_iva / 100`.
- En el RIDE, `subtotal_15` y `subtotal_0` siguen siendo el subtotal antes de ICE; el ICE se muestra en una línea aparte.
- En el XML, el IVA se declara con `codigo=2` y `codigoPorcentaje=4` cuando la tarifa es mayor a 0; con `codigoPorcentaje=0` cuando es 0.
- La UI de facturación usa tarifas 15% y 0%; el XML usa el código `4` para cualquier tarifa mayor a 0.

### 11.5 Propina

- Se ingresa manualmente en el POS.
- Se suma al total: `importe_total = subtotal_sin_impuestos + iva_total + ice_total + propina`.
- Se declara en el XML como `<propina>`.

### 11.6 Estados de factura

| Estado | Significado |
|---|---|
| `GENERADA` | Factura creada, aún no enviada al SRI. |
| `RECIBIDA` | El SRI recibió el comprobante. |
| `EN PROCESO` | El SRI aún no devuelve autorización. |
| `AUTORIZADO` | Comprobante autorizado; se muestran número y fecha. |
| `DEVUELTA` | El SRI devolvió el comprobante con errores. |
| `NO AUTORIZADO` | El SRI no autorizó el comprobante. |
| `ERROR` | Error local de configuración, firma, conexión o envío. |

### 11.7 Estados de correo

| Estado | Significado |
|---|---|
| `PENDIENTE` | Se enviará al autorizar. |
| `ENVIADA` | Correo enviado correctamente. |
| `ERROR` | Falló el envío. |
| `NO_ENVIAR` | El usuario desactivó el envío. |

### 11.8 Reglas del RIDE

- La clave de acceso se imprime como número y en Code 128.
- La clave de acceso **no** se etiqueta como número de autorización antes de autorizar.
- Antes de autorizar se muestra `PENDIENTE DE AUTORIZACION`.
- El número y la fecha de autorización solo aparecen cuando el SRI devuelve `AUTORIZADO`.
- El RIDE se regenera después de la autorización para incorporar los datos reales.
- El QR es opcional pero se mantiene con la URL de verificación del SRI.

---

## 12. Persistencia y rutas de archivos

### 12.1 Escritorio

| Dato | Ruta |
|---|---|
| Código/recursos | `BASE_DIR` (raíz del proyecto) |
| Base de datos | `BASE_DIR/data/fleting.db` |
| Documentos generados | `BASE_DIR/assets/` |
| XML | `assets/invoices/xml/` |
| RIDE | `assets/invoices/pdf/` |
| Cotizaciones | `assets/quotations/pdf/` |
| Imágenes de productos | `assets/products/images/` |
| Logo de empresa | `assets/company/` |
| Certificados | `assets/certs/` |
| Exportaciones | `assets/exports/` |
| Preferencias | `BASE_DIR/preferences.json` |
| Clave de cifrado | `BASE_DIR/data/.secret_key` |
| Logs | `BASE_DIR/logs/fleting.log` |

### 12.2 Android

- `BASE_DIR`: código empaquetado (se borra y reextrae en cada actualización).
- `DATA_DIR`: directorio de trabajo persistente (`getApplicationSupportDirectory()/data`).
- La base, documentos, preferencias y clave se guardan fuera del código para sobrevivir actualizaciones.
- `GENERATED_DIR = DATA_DIR/assets`.

### 12.3 Archivos generados por factura

```text
assets/invoices/xml/FAC_{clave}.xml
assets/invoices/xml/FAC_{clave}_firmado.xml
assets/invoices/xml/FAC_{clave}_autorizado.xml
assets/invoices/pdf/FAC_{clave}.pdf
```

---

## 13. Seguridad

### 13.1 Controles existentes

- Contraseñas con **bcrypt**; migración 004 rehashea usuarios antiguos.
- Permisos por rol y por módulo (`can_read`, `can_write`, `can_update`, `can_delete`) con validación en router, menú y vistas.
- `AppState.has_permission` falla cerrado; un módulo no configurado se deniega cuando existe matriz.
- El menú superior, la barra inferior y las tarjetas de inicio solo muestran módulos con `can_read`.
- SMTP se cifra con Fernet; la clave se obtiene de `FLETING_SECRET_KEY` o se genera en `data/.secret_key`.
- El certificado `.p12/.pfx` se valida con su contraseña antes de guardarse.
- La sesión no persiste en disco.
- El XML se firma con SHA-1 porque lo exige la ficha técnica del SRI.

### 13.2 Observaciones de seguridad

- `firma_pass` se guarda en texto plano en `company.firma_pass`.
- `smtp_pass` se cifra, pero la clave Fernet puede quedar junto a la base de datos si no se configura `FLETING_SECRET_KEY`.
- No hay bloqueo por intentos fallidos de login.
- No hay auditoría de acciones de usuario.
- Los logs pueden contener mensajes de error del SRI o SMTP; no se registra la contraseña SMTP.
- La aplicación es local; no expone una API de red.

---

## 14. Pruebas

### 14.1 Comando

```bash
python -m unittest discover -s tests
```

Resultado actual: **69 pruebas OK**.

### 14.2 Cobertura por archivo

| Archivo | Cobertura |
|---|---|
| `tests/test_auth.py` | Permisos globales, permisos por módulo y fail-closed. |
| `tests/test_role_permissions.py` | Presets, CRUD de roles, matriz por módulo y autenticación con permisos. |
| `tests/test_orm.py` | CRUD, relaciones, transacciones y rollback. |
| `tests/test_migrations.py` | Creación de tablas, columnas nuevas, seeds e idempotencia. |
| `tests/test_router.py` | Guard de auth, guard por módulo, rutas desconocidas y limpieza de chrome. |
| `tests/test_sri_catalogs.py` | Formas de pago, ICE y cálculo de línea. |
| `tests/test_sri_service.py` | Parseo de respuestas, error 43, recuperación de autorización y guardado de XML autorizado (plano/base64). |
| `tests/test_xml_service.py` | Dirección de establecimiento, agente de retención, ICE, propina, pagos y base IVA. |
| `tests/test_pdf_service.py` | RIDE, Code 128, QR, autorización, ICE, propina y forma de pago. |
| `tests/test_invoice_email_flow.py` | Correo solo tras autorización, desactivación y bloqueo de reenvío. |

`tests/base.py` redirige la BD a un archivo temporal y crea stubs de `faker`/`flet` si no están instalados.

---

## 15. Operación y despliegue

### 15.1 Instalación

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

### 15.2 Ejecución

```bash
flet run
# o
python main.py
```

`main.py` usa `ft.run(main)` (Flet 1.x).

### 15.3 Compilación

El proyecto usa `flet build` (serious_python). No hay un archivo de configuración de build adicional versionado; las dependencias de runtime están en `requirements.txt` y las de desarrollo en `requirements-dev.txt`. No se debe incluir `flet-cli`/`flet-desktop` en el build móvil.

### 15.4 Base de datos y seeds

- Al primer arranque se crea `data/fleting.db`, se aplican las 14 migraciones y los seeds.
- Seeds incluidos:
  - Roles base: Admin, Cajero, Usuario, Supervisor, Gerente, Auditor, Soporte.
  - Roles de ejemplo: Vendedor (POS y clientes) y Bodeguero (inventario), con permisos por módulo.
  - Usuario administrador: `admin@pos.com` / `admin123` (cambiar en producción).
  - Cliente `CONSUMIDOR FINAL` (`9999999999999`).
  - Configuración vacía de empresa.
  - Sin productos, servicios ni proveedores de demostración.
- `scripts/clean_demo_data.py` limpia datos de prueba, conserva empresa, admin, consumidor final y roles, y reinicia secuenciales.

### 15.5 Configuración mínima para facturar

1. Ir a **Mi Empresa** y completar RUC, razón social, dirección, establecimiento y punto de emisión.
2. Configurar ambiente SRI (pruebas/producción).
3. Cargar certificado `.p12/.pfx` y contraseña.
4. Configurar SMTP (host, puerto, usuario, contraseña de aplicación, SSL si aplica).
5. Verificar el secuencial inicial.
6. Crear/importar clientes y productos.
7. Emitir una factura y enviarla al SRI desde **Facturas**.

---

## 16. Deuda técnica y observaciones

1. **MySQL no implementado**: `configs/database.py` lo permite, pero `core/database.py` lanza `NotImplementedError`.
2. **Modelos `settings` y `help` sin tabla**: son marcadores; no persistir datos en ellos sin crear migración.
3. **`core/table_filters.py` sin uso**: utilidad heredada.
4. **Dos rutas de exportación Excel**: `core/import_export.py` (clientes, productos, facturas, cotizaciones) y `app/services/excel_service.py` (proveedores). Conviene unificar.
5. **Sesión en memoria**: no hay “recordarme” ni persistencia de sesión.
6. **`firma_pass` en texto plano**: considerar cifrarla con `EncryptionService`.
7. **Envío al SRI manual**: no hay cola automática ni reintento programado.
8. **XML con un solo pago**: no soporta pagos divididos o plazos.
9. **IVA limitado en UI**: la interfaz usa 15%/0%; el XML usa código `4` para cualquier tarifa > 0.
10. **Importación de pagos legacy**: `core/import_export.PAYMENT_MAP` mapea códigos antiguos de forma más gruesa que `sri_catalogs`.
11. **Ayuda con contenido legado**: `HelpView` apunta a enlaces de Fleting y texto en portugués.
12. **README genérico**: no describe la aplicación real; este `SPEC.md` lo complementa.
13. **Acoplamiento `core → app`**: `core/import_export.py` importa controladores, lo que dificulta reutilizar `core` de forma aislada.
14. **Sin `pyproject.toml`**: no hay configuración formal de empaquetado, linting o tipado.

---

## 17. Guía para extender el proyecto

### 17.1 Agregar una entidad nueva

1. Crear migración en `migrations/014_...py` con `up(db)` y `down(db)`.
2. Crear modelo en `app/models/` con `table_name`.
3. Crear controlador en `app/controllers/` con validaciones y transacciones.
4. Crear vista en `app/views/pages/`.
5. Registrar la ruta en `configs/routes.py`.
6. Agregar etiquetas i18n en `configs/languages/*.json` si aplica.
7. Agregar pruebas en `tests/`.
8. Ejecutar `python -m unittest discover -s tests`.

### 17.2 Agregar un campo a una entidad existente

1. Crear migración idempotente con `PRAGMA table_info` y `ALTER TABLE ... ADD COLUMN`.
2. Actualizar el modelo/controlador y las vistas.
3. Actualizar XML/RIDE si el campo es tributario.
4. Agregar prueba de migración y de flujo.

### 17.3 Reglas de consistencia

- Usar `transaction()` para operaciones que afecten varias tablas.
- No confiar en datos de la UI: validar en el controlador.
- Mantener los códigos SRI en `app/services/sri_catalogs.py`.
- Mantener la generación de XML en `xml_service.py` y la del RIDE en `pdf_service.py`.
- No reenviar al SRI una factura `AUTORIZADO`.
- Si el SRI responde error 43, consultar la autorización antes de concluir que la factura fue rechazada.
- Regenerar el RIDE después de la autorización.
- No enviar correo de factura antes de la autorización.

---

## 18. Mapa rápido de dependencias

```text
main.py
 └─ configs.app_config
 └─ core.logger
 └─ core.error_handler
 └─ core.responsive
 └─ core.state
 └─ core.preferences / core.theme / core.i18n
 └─ core.router
      └─ configs.routes
           └─ app.views.pages.*
                ├─ app.views.layouts.main_layout
                ├─ app.views.ui_helpers
                ├─ app.controllers.*
                │    ├─ app.models.*
                │    │    └─ core.base_model → core.orm → core.database
                │    └─ app.services.*
                │         ├─ core.paths / core.logger
                │         └─ app.services.sri_catalogs
                └─ app.services.sri_catalogs / whatsapp_service / excel_service
```

---

## 19. Glosario

| Término | Significado |
|---|---|
| **RIDE** | Representación impresa del documento electrónico. |
| **SRI** | Servicio de Rentas Internas de Ecuador. |
| **Clave de acceso** | Código numérico de 49 dígitos que identifica el comprobante. |
| **XAdES-BES** | Firma electrónica XML requerida por el SRI. |
| **ICE** | Impuesto a los Consumos Especiales. |
| **IVA** | Impuesto al Valor Agregado. |
| **Secuencial** | Número consecutivo del comprobante dentro de un establecimiento/punto de emisión. |
| **P12/PFX** | Formato de certificado digital PKCS#12. |
| **POS** | Punto de venta. |

---

*Fin de la especificación.*
