# UI_KIT.md — Guía de interfaz de TntPos

> **Objetivo:** documentar el tema, la paleta, la tipografía y los componentes reutilizables de Flet para que cualquier desarrollador pueda crear pantallas nuevas sin romper la consistencia visual.
>
> **Fuente de verdad:** `core/theme.py`, `app/views/ui_helpers.py`, `app/views/layouts/main_layout.py` y `app/views/components/import_export.py`.

---

## 1. Principios de diseño

1. **Usar tokens semánticos, nunca colores hexadecimales directamente.**
   ```python
   from core import theme as T

   ft.Text("Total", color=T.TEXT)
   ft.Container(bgcolor=T.SURFACE, border=T.border())
   ```
2. **La app tiene un solo sistema de tema:** claro, oscuro y “sistema”. Todos los tokens cambian de valor según el modo activo.
3. **No capturar tokens al importar.** `T.TEXT` debe leerse en el momento de construir el control, no con `from core.theme import TEXT`.
4. **Reutilizar los helpers de `app/views/ui_helpers.py`** antes de crear diálogos, toasts, botones o campos propios.
5. **Diseñar primero para móvil** y usar `is_mobile_page()` para alternar entre tarjetas y tablas.
6. **Toda vista de módulo debe devolver `MainLayout`**, salvo pantallas especiales como el login.

---

## 2. Cómo funciona el tema

### 2.1 Archivos implicados

| Archivo | Responsabilidad |
|---|---|
| `core/theme.py` | Define las paletas, los tokens y `apply(page)`. |
| `main.py` | Carga la preferencia guardada y aplica el tema al iniciar. |
| `core/preferences.py` | Persiste `theme_mode` y `language` en `data/preferences.json`. |
| `app/views/pages/settings_view.py` | Permite al usuario cambiar entre claro, oscuro y sistema. |
| `core/router.py` | Re-renderiza la vista cuando cambia el tema o el brillo del sistema. |

### 2.2 Flujo de aplicación

```text
main.py
  ├── preferences.load()                 # lee theme_mode guardado
  ├── theme.apply(page, AppState.theme_mode)
  │     ├── set_mode()                   # resuelve light/dark/system
  │     ├── instala la paleta en los globals del módulo
  │     ├── page.theme_mode = LIGHT | DARK
  │     ├── page.bgcolor = T.BG
  │     ├── page.theme = ft.Theme(...)       # tema claro
  │     └── page.dark_theme = ft.Theme(...)  # tema oscuro
  └── Router.navigate("/login")
```

Cuando el usuario cambia el tema en **Configuración**:

```python
# app/views/pages/settings_view.py
def _change_theme(self, mode: str):
    AppState.theme_mode = mode
    preferences.save(theme_mode=mode)
    theme.apply(self.page, mode)
    self.router.rerender()
```

El `rerender()` es obligatorio: los controles ya construidos conservan los colores anteriores. Al reconstruir la vista, cada `T.TOKEN` toma el valor de la nueva paleta.

### 2.3 Modos disponibles

| Constante | Valor | Comportamiento |
|---|---|---|
| `theme.LIGHT` | `"light"` | Fuerza la paleta clara. |
| `theme.DARK` | `"dark"` | Fuerza la paleta oscura. |
| `theme.SYSTEM` | `"system"` | Sigue el brillo del sistema operativo. |

La paleta inicial, antes de que `main.py` aplique la preferencia, es la **oscura**.

### 2.4 `page.theme` y `page.dark_theme`

`theme.apply()` configura ambos temas de Flet:

```python
page.theme = ft.Theme(
    color_scheme_seed=ft.Colors.BLUE,
    icon_theme=ft.IconTheme(color=T.ICON_NEON, size=24),
)

page.dark_theme = ft.Theme(
    color_scheme=ft.ColorScheme(
        primary=T.PRIMARY,
        on_primary=T.ON_ACCENT,
        secondary=T.ICON_NEON_ALT,
        surface=T.SURFACE,
        on_surface=T.TEXT,
        on_surface_variant=T.ICON_NEON,
        outline=T.BORDER_STRONG,
        error=T.DANGER,
        on_error=T.ON_ACCENT,
    ),
    icon_theme=ft.IconTheme(color=T.ICON_NEON, size=24),
    appbar_theme=ft.AppBarTheme(bgcolor=T.APPBAR_BG, color=T.TEXT),
    navigation_bar_theme=ft.NavigationBarTheme(
        bgcolor=T.NAV_BG,
        indicator_color=T.ICON_NEON + "22",
        label_text_style=ft.TextStyle(color=T.ICON_NEON, size=11),
    ),
    scaffold_bgcolor=T.BG,
    canvas_color=T.BG,
    card_bgcolor=T.SURFACE,
    divider_color=T.BORDER,
    hint_color=T.TEXT_SUBTLE,
)
```

> **Regla:** no configures `page.theme` ni `page.dark_theme` dentro de una vista. El tema se centraliza en `core/theme.py`.

---

## 3. Paleta de colores

### 3.1 Tokens base

| Token | Oscuro | Claro | Uso recomendado |
|---|---|---|---|
| `T.BG` | `#000000` | `#f1f5f9` | Fondo general de la página. |
| `T.SURFACE` | `#050505` | `#ffffff` | Tarjetas, tablas y contenedores principales. |
| `T.SURFACE_ALT` | `#0d0d0d` | `#e2e8f0` | Encabezados de tabla, fondos secundarios. |
| `T.SURFACE_INSET` | `#000000` | `#f8fafc` | Bloques hundidos: XML, respuestas SRI, consola. |
| `T.BORDER` | `#1a1a1a` | `#cbd5e1` | Bordes normales. |
| `T.BORDER_STRONG` | `#333333` | `#94a3b8` | Separadores y bordes de énfasis. |
| `T.TEXT` | `#f5f5f5` | `#0f172a` | Texto principal. |
| `T.TEXT_MUTED` | `#a3a3a3` | `#475569` | Texto secundario, descripciones. |
| `T.TEXT_SECONDARY` | `#d4d4d4` | `#334155` | Texto de apoyo con más contraste. |
| `T.TEXT_SUBTLE` | `#737373` | `#64748b` | Metadatos, placeholders, texto terciario. |
| `T.ON_ACCENT` | `#ffffff` | `#ffffff` | Texto sobre botones de color. |
| `T.APPBAR_BG` | `#000000` | `#ffffff` | Fondo de la barra superior. |
| `T.NAV_BG` | `#000000` | `#ffffff` | Fondo de la navegación inferior. |
| `T.TABLE_HEAD` | `#0d0d0d` | `#e2e8f0` | Cabecera de tablas. |
| `T.INPUT_BG` | `#050505` | `#ffffff` | Fondo de campos de texto. |
| `T.INPUT_BORDER` | `#2a2a2a` | `#94a3b8` | Borde de campos de texto. |
| `T.DISABLED_BG` | `#333333` | `#64748b` | Controles deshabilitados. |
| `T.SHADOW` | `#000000aa` | `#0f172a22` | Sombras de tarjetas. |

### 3.2 Login

| Token | Oscuro | Claro | Uso |
|---|---|---|---|
| `T.LOGIN_BG` | `#000000` | `#f1f5f9` | Fondo de la pantalla de login. |
| `T.LOGIN_CARD` | `#050505` | `#ffffff` | Tarjeta central del login. |
| `T.LOGIN_INPUT` | `#050505` | `#ffffff` | Fondo de inputs del login. |
| `T.LOGIN_BORDER` | `#39ff1444` | `#cbd5e1` | Borde del logo y la tarjeta de login. |

### 3.3 Marca y acción principal

| Token | Oscuro | Claro | Uso |
|---|---|---|---|
| `T.PRIMARY` | `#0057ff` | `#1d4ed8` | Botón primario, acentos de acción. |
| `T.PRIMARY_DARK` | `#003ecc` | `#1e40af` | Gradientes y estados hover. |
| `T.PRIMARY_SHADOW` | `#0057ff55` | `#1d4ed833` | Sombra del botón de login. |

### 3.4 Estados semánticos

| Token | Oscuro | Claro | Uso |
|---|---|---|---|
| `T.SUCCESS` | `#10b981` | `#047857` | Toast de éxito, iconos positivos. |
| `T.SUCCESS_STRONG` | `#059669` | `#047857` | Énfasis de éxito. |
| `T.SUCCESS_TEXT` | `#39ff14` | `#047857` | Texto/icono de éxito. |
| `T.SUCCESS_BG` | `#00ff9c22` | `#d1fae5` | Fondo de chips “Activo”. |
| `T.SUCCESS_BG_SOFT` | `#00ff9c11` | `#ecfdf5` | Fondo suave de éxito. |
| `T.DANGER` | `#ef4444` | `#dc2626` | Error, eliminar, toast de error. |
| `T.DANGER_TEXT` | `#ff5c5c` | `#b91c1c` | Texto de error. |
| `T.DANGER_BG` | `#ff313122` | `#fee2e2` | Fondo de chips “Inactivo” o error. |
| `T.WARNING` | `#ffd60a` | `#b45309` | Advertencia. |
| `T.AMBER` | `#ffb703` | `#b45309` | Iconos de confirmación. |
| `T.WARNING_BG` | `#ffd60a22` | `#fef3c7` | Fondo de advertencia. |
| `T.WARNING_BG_SOFT` | `#ffd60a11` | `#fffbeb` | Fondo suave de advertencia. |
| `T.INFO` | `#00bfff` | `#1d4ed8` | Acción informativa, envío al SRI. |
| `T.INFO_TEXT` | `#00e5ff` | `#1d4ed8` | Texto informativo. |
| `T.INFO_BG` | `#00bfff22` | `#dbeafe` | Fondo informativo. |
| `T.INFO_BG_SOFT` | `#00bfff11` | `#e0f2fe` | Fondo informativo suave. |

### 3.5 Acentos

| Token | Oscuro | Claro | Uso |
|---|---|---|---|
| `T.INDIGO` | `#7c3aed` | `#4338ca` | Login, acciones especiales. |
| `T.INDIGO_DARK` | `#5b21b6` | `#3730a3` | Gradiente del login. |
| `T.INDIGO_TEXT` | `#c084fc` | `#4338ca` | Texto índigo. |
| `T.INDIGO_BG` | `#7c3aed22` | `#e0e7ff` | Fondo índigo. |
| `T.PURPLE` | `#d946ef` | `#7e22ce` | Cotizaciones, acentos. |
| `T.PURPLE_TEXT` | `#e879f9` | `#6d28d9` | Texto morado. |
| `T.PURPLE_BTN` | `#7c3aed` | `#6d28d9` | Botón morado. |
| `T.PURPLE_BG` | `#d946ef22` | `#ede9fe` | Fondo morado. |
| `T.CYAN` | `#00ffff` | `#0e7490` | Acentos cian. |
| `T.CYAN_TEXT` | `#22d3ee` | `#0369a1` | Texto cian. |
| `T.PINK` | `#ff2d95` | `#be185d` | Acento rosa. |
| `T.SKY` | `#00bfff` | `#0369a1` | Acento celeste. |
| `T.CHIP_BG` | `#00ff9c1a` | `#d1fae5` | Fondo por defecto de `chip()`. |
| `T.MUTED_BG` | `#a3a3a31a` | `#e2e8f0` | Fondo de controles deshabilitados. |

### 3.6 Iconografía

| Token | Oscuro | Claro |
|---|---|---|
| `T.ICON_NEON` | `#39ff14` | `#1d4ed8` |
| `T.ICON_NEON_ALT` | `#00ffff` | `#0e7490` |
| `T.ICON_NEON_PINK` | `#ff2d95` | `#be185d` |
| `T.ICON_NEON_PURPLE` | `#d946ef` | `#7e22ce` |
| `T.ICON_NEON_YELLOW` | `#ffd60a` | `#b45309` |
| `T.ICON_NEON_ORANGE` | `#ff7a00` | `#c2410c` |
| `T.ICON_NEON_BLUE` | `#00bfff` | `#1d4ed8` |
| `T.ICON_MUTED` | `#4ade80` | `#64748b` |

> En tema claro los “neón” se sustituyen por tonos accesibles. No asumas que un icono será neón en ambos modos.

### 3.7 Colores de marca

| Token | Valor | Uso |
|---|---|---|
| `T.WHATSAPP` | `#25d366` | Acciones de WhatsApp. |
| `T.LOGO_START` | `#8CA326` | Gradiente de marca. |
| `T.LOGO_END` | `#55FD07` | Gradiente de marca. |

### 3.8 Reglas de contraste

- Sobre `T.PRIMARY`, `T.DANGER`, `T.INDIGO` o `T.PURPLE`, usar siempre `T.ON_ACCENT`.
- No usar `T.TEXT` sobre un fondo de estado (`SUCCESS_BG`, `DANGER_BG`, etc.); usar el `*_TEXT` correspondiente.
- Para texto secundario usar `T.TEXT_MUTED`; para metadatos pequeños, `T.TEXT_SUBTLE`.
- Evitar `#000000` o `#ffffff` fijos: en tema oscuro/claro pueden perder contraste.
- Los únicos hexadecimales aceptables son los de marca (`WHATSAPP`, gradientes del logo) y los que ya están encapsulados en tokens.

---

## 4. Tipografía

### 4.1 Fuente

La aplicación **no incluye fuentes personalizadas** ni `GoogleFonts`. Usa la fuente por defecto de Flet/Flutter (Roboto o la del sistema, según la plataforma).

El único uso explícito de otra familia es:

```python
# app/views/pages/invoices_view.py
ft.Text(respuesta_sri, font_family="monospace", size=11)
```

Se usa **monospace** para la respuesta cruda del SRI porque conserva la alineación de mensajes y códigos.

### 4.2 Escala tipográfica observada

| Tamaño | Uso típico | Peso recomendado |
|---:|---|---|
| 10 | Metadatos, claves de acceso, subtítulos de tarjetas. | `W_500` / normal |
| 11 | Chips de estado, celdas secundarias, texto de tablas. | `W_600` / `BOLD` |
| 12 | Cuerpo de tablas, descripciones, botones compactos. | normal |
| 13 | Texto de tabla principal, títulos de sección pequeños. | `W_500` / normal |
| 14 | Subtítulos, cuerpo de diálogos. | normal |
| 15 | Títulos de tarjetas y módulos. | `BOLD` |
| 16 | Encabezados de sección y formularios. | `BOLD` / `W_600` |
| 18 | Valores destacados. | `BOLD` |
| 19 | Valor de `stat_card()`. | `BOLD` |
| 22 | Título de página en vistas de acceso restringido. | `BOLD` |
| 24 | Título de bienvenida y encabezados grandes. | `BOLD` |
| 28 | Título principal de Login y Configuración. | `BOLD` |

### 4.3 Pesos

| Peso | Uso |
|---|---|
| `ft.FontWeight.BOLD` | Títulos, totales, encabezados de tabla, chips. |
| `ft.FontWeight.W_600` | Chips y botones compactos. |
| `ft.FontWeight.W_500` | Texto de énfasis suave y celdas principales. |
| Normal (sin peso) | Cuerpo de texto y descripciones. |

### 4.4 Ejemplo

```python
ft.Column(
    controls=[
        ft.Text("Facturas emitidas", size=24, weight=ft.FontWeight.BOLD, color=T.TEXT),
        ft.Text("Comprobantes electrónicos del período", size=14, color=T.TEXT_MUTED),
    ],
    spacing=4,
)
```

---

## 5. Espaciado, radios, bordes y sombras

### 5.1 Espaciado

| Contexto | Valor habitual |
|---|---|
| Padding del contenido en `MainLayout` | `10` |
| Separación entre secciones | `16`–`24` |
| Separación dentro de tarjetas | `8`–`12` |
| `spacing` de formularios y diálogos | `12` |
| Padding de tarjetas | `14`–`16` |
| Padding de tablas contenedoras | `10` |
| Padding de estados vacíos | `40` |
| Separación de filas de botones | `8`–`10` |

### 5.2 Radios

| Radio | Uso |
|---:|---|
| `4`–`6` | Contenedores pequeños, miniaturas. |
| `8` | Botones, inputs compactos, bloques de código. |
| `10` | Tarjetas, tablas, tarjetas móviles, botones secundarios. |
| `12` | Chips de estado, campos del login, tarjetas de configuración. |
| `16` | Diálogos (`RoundedRectangleBorder`). |
| `20`–`24` | Logo y tarjeta principal del login. |

### 5.3 Bordes

Usar los helpers del tema:

```python
ft.Container(border=T.border())                  # 1 px, T.BORDER
ft.Container(border=T.border(1, T.SURFACE_ALT))  # borde de tarjeta
ft.Container(border=T.all_border(1, T.BORDER_STRONG))
```

`T.border()` y `T.all_border()` son equivalentes; `all_border` existe por compatibilidad con el patrón `_all_border` repetido en varias vistas.

> **Deuda técnica:** 14 vistas definen su propio `_all_border`. En código nuevo usa `T.border()` directamente.

### 5.4 Sombras

Las sombras se reservan para elementos destacados, principalmente el login:

```python
shadow=ft.BoxShadow(
    spread_radius=0,
    blur_radius=60,
    color=T.SHADOW,
    offset=ft.Offset(0, 20),
)
```

No agregues sombras a todas las tarjetas: la jerarquía visual se basa en `SURFACE`, `SURFACE_ALT` y bordes.

---

## 6. Componentes reutilizables

### 6.1 Resumen

| Componente | Ubicación | Para qué sirve |
|---|---|---|
| `MainLayout` | `app/views/layouts/main_layout.py` | Shell de todas las vistas de módulo. |
| `stat_card()` | `app/views/ui_helpers.py` | Tarjeta de estadística. |
| `chip()` | `app/views/ui_helpers.py` | Etiqueta compacta de estado. |
| `primary_button()` | `app/views/ui_helpers.py` | Botón principal con icono opcional. |
| `field()` | `app/views/ui_helpers.py` | `TextField` con `expand=True`. |
| `section_title()` | `app/views/ui_helpers.py` | Título de sección pequeño. |
| `build_import_export_bar()` | `app/views/components/import_export.py` | Barra Importar / Plantilla / Excel / PDF. |
| `open_dialog()` / `close_dialog()` | `app/views/ui_helpers.py` | Abrir y cerrar diálogos. |
| `show_toast()` | `app/views/ui_helpers.py` | SnackBar de éxito o error. |
| `wide_dialog_width()` / `form_dialog_width()` | `app/views/ui_helpers.py` | Ancho responsive de diálogos. |
| `is_mobile_page()` | `app/views/ui_helpers.py` | Decidir entre tarjetas y tabla. |
| `is_mobile_platform()` | `app/views/ui_helpers.py` | Detectar Android/iOS real. |
| `get_file_picker()` | `app/views/ui_helpers.py` | Selector de archivos registrado por página. |
| `share_file()` / `open_path()` / `open_url()` | `app/views/ui_helpers.py` | Compartir o abrir archivos y URLs. |
| `send_whatsapp_document()` | `app/views/ui_helpers.py` | Compartir PDF por WhatsApp. |
| `open_manual_service_dialog()` | `app/views/ui_helpers.py` | Alta rápida de un servicio manual. |

### 6.2 `MainLayout`

Envuelve el contenido con:

- `page.appbar`: barra superior con usuario, rol, historial y menú.
- Contenedor central con `padding=10`.
- `NavigationBar` inferior con las rutas `show_in_bottom`.

```python
from app.views.layouts.main_layout import MainLayout

return MainLayout(
    page=self.page,
    content=content,
    router=self.router,
)
```

> No agregues otro `AppBar` dentro de una vista: `MainLayout` ya lo instala en `page.appbar`.
> El login es la excepción: devuelve un `ft.Column` propio sin `MainLayout`.

### 6.3 `stat_card()`

```python
from app.views.ui_helpers import stat_card

stat_card(
    "Facturas emitidas",
    "128",
    ft.Icons.RECEIPT_LONG_ROUNDED,
    T.PRIMARY,
    subtitle="Total $4,520.00",
)
```

- Fondo `T.SURFACE`, borde `T.border()`, radio `12`.
- `col={"xs": 12, "sm": 6, "md": 3}` para usarse dentro de `ft.ResponsiveRow`.

### 6.4 `chip()`

```python
from app.views.ui_helpers import chip

chip("Activo")                                  # verde por defecto
chip("Inactivo", bgcolor=T.DANGER_BG, color=T.DANGER_TEXT)
chip("Pendiente", bgcolor=T.WARNING_BG, color=T.WARNING)
```

Para estados de factura se usa el mismo patrón con colores según el estado SRI.

### 6.5 `primary_button()`

```python
from app.views.ui_helpers import primary_button

primary_button(
    "Guardar",
    on_click=save,
    icon=ft.Icons.SAVE_ROUNDED,
)
```

- Usa `FilledButton` (con respaldo a `ElevatedButton`/`TextButton`).
- Texto `T.ON_ACCENT`, radio `8`, padding `14`.
- Permite cambiar `bgcolor` para acciones destructivas:
  ```python
  primary_button("Eliminar", on_click=delete, icon=ft.Icons.DELETE, bgcolor=T.DANGER)
  ```

### 6.6 `field()` y `section_title()`

```python
from app.views.ui_helpers import field, section_title

field("RUC / Cédula", value=client["identificacion"])
field("Correo", value=client["email"], keyboard_type=ft.KeyboardType.EMAIL)
section_title("Datos del comprobante")
```

`field()` crea un `TextField` con `expand=True`; pasa cualquier argumento extra de Flet mediante `**kwargs`.

### 6.7 Barra de importación/exportación

```python
from app.views.components.import_export import build_import_export_bar

build_import_export_bar(
    self.page,
    kind="customers",        # customers | products | invoices | quotes
    on_changed=load_data,
)
```

Devuelve un `ft.Row` con:

- **Importar**: abre un `.xlsx`.
- **Plantilla**: descarga un Excel vacío.
- **Excel**: exporta el listado actual.
- **PDF**: exporta el listado actual.

### 6.8 Diálogos y toasts

```python
from app.views.ui_helpers import (
    open_dialog,
    close_dialog,
    show_toast,
    form_dialog_width,
)

dlg = ft.AlertDialog(
    title=ft.Text("Nuevo cliente", weight=ft.FontWeight.BOLD),
    content=ft.Container(
        content=ft.Column([...], spacing=12, tight=True),
        width=form_dialog_width(self.page, 500),
    ),
    actions=[
        ft.TextButton("Cancelar", on_click=lambda e: close_dialog(self.page, dlg)),
        ft.FilledButton(
            "Guardar",
            on_click=save,
            style=ft.ButtonStyle(bgcolor=T.PRIMARY, color=T.ON_ACCENT),
        ),
    ],
    actions_alignment=ft.MainAxisAlignment.END,
)
open_dialog(self.page, dlg)
```

```python
show_toast(self.page, "Cliente guardado correctamente.")
show_toast(self.page, "No se pudo guardar.", is_error=True)
```

- `show_toast()` usa `T.SUCCESS` o `T.DANGER` y `T.ON_ACCENT`.
- `open_dialog()` usa `page.show_dialog()` y tiene respaldo en `page.overlay`.
- `close_dialog()` usa `page.pop_dialog()` y limpia el overlay si hace falta.

### 6.9 Anchos responsive

```python
from app.views.ui_helpers import wide_dialog_width, form_dialog_width

wide_dialog_width(page, 900)   # diálogos grandes: detalles, carrito
form_dialog_width(page, 500)   # formularios de crear/editar
```

En móvil ambos se ajustan al ancho disponible; no uses `width=900` fijo en un diálogo nuevo.

### 6.10 Archivos, URLs y compartir

```python
from app.views.ui_helpers import (
    get_file_picker,
    share_file,
    open_path,
    open_url,
    send_whatsapp_document,
)

picker = get_file_picker(page)          # una instancia por página
open_url(page, "https://flet.dev")      # no bloquea la UI
open_path(page, pdf_path)               # visor del sistema o share en móvil
share_file(page, pdf_path, title="Compartir RIDE")
send_whatsapp_document(
    page,
    link=wa_link,
    pdf_path=pdf_path,
    message="Adjunto su cotización.",
)
```

> `FilePicker`, `Share` y `UrlLauncher` son **servicios** en Flet 1.x. Los helpers los registran una sola vez en `page.services` y usan `page.run_task`.

### 6.11 Responsive

```python
from app.views.ui_helpers import is_mobile_page, is_mobile_platform
from core.responsive import MOBILE_BREAKPOINT, get_device_type

is_mobile_page(page)       # True si el ancho < 800: usar tarjetas
is_mobile_platform(page)   # True solo en Android/iOS reales
get_device_type(width)     # "mobile" (<=600), "tablet" (<=1024), "desktop"
```

Hay dos conceptos distintos:

- **Layout de la vista:** `is_mobile_page()` usa el breakpoint de **800 px** para pasar de tabla a tarjetas.
- **Categoría de dispositivo:** `AppState.device` y `get_device_type()` usan **600/1024 px** para decidir la navegación y los tamaños de ventana.

---

## 7. Patrones de pantalla

### 7.1 Esqueleto de una vista nueva

```python
import flet as ft
from core import theme as T
from core.state import AppState
from app.views.layouts.main_layout import MainLayout
from app.views.ui_helpers import is_mobile_page, show_toast

MODULE = "example"

class ExampleView:
    def __init__(self, page: ft.Page, router):
        self.page = page
        self.router = router

    def render(self):
        if not AppState.has_permission("can_read", MODULE):
            return MainLayout(
                page=self.page,
                content=self._access_denied(),
                router=self.router,
            )

        content = ft.Column(
            controls=[
                ft.Text("Ejemplo", size=24, weight=ft.FontWeight.BOLD, color=T.TEXT),
                ft.Text("Descripción del módulo", size=14, color=T.TEXT_MUTED),
            ],
            spacing=16,
            scroll=ft.ScrollMode.AUTO,
            expand=True,
        )
        return MainLayout(page=self.page, content=content, router=self.router)

    def _access_denied(self):
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Icon(ft.Icons.LOCK_OUTLINED, color=T.DANGER, size=64),
                    ft.Text("Acceso restringido", color=T.TEXT, size=22, weight=ft.FontWeight.BOLD),
                    ft.Text("No tienes permisos para este módulo.", color=T.TEXT_MUTED),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=12,
            ),
            padding=60,
            alignment=ft.Alignment(0, 0),
            expand=True,
        )
```

### 7.2 Cabecera de módulo

Patrón usado en clientes, productos, facturas y cotizaciones:

```python
header = ft.Container(
    content=ft.Row(
        controls=[
            ft.Column(
                controls=[
                    ft.Text("Clientes", size=24, weight=ft.FontWeight.BOLD, color=T.TEXT),
                    ft.Text("Directorio de clientes", size=13, color=T.TEXT_MUTED),
                ],
                spacing=2,
                expand=True,
            ),
            build_import_export_bar(self.page, kind="customers", on_changed=load_data),
            ft.FilledButton(
                "Nuevo",
                icon=ft.Icons.ADD,
                on_click=open_create,
                style=ft.ButtonStyle(bgcolor=T.PRIMARY, color=T.ON_ACCENT),
            ),
        ],
        wrap=True,
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    ),
    padding=16,
    bgcolor=T.SURFACE,
    border_radius=10,
    border=T.border(),
)
```

### 7.3 Tabla en escritorio

```python
table = ft.DataTable(
    columns=[
        ft.DataColumn(ft.Text("NOMBRE", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
        ft.DataColumn(ft.Text("ESTADO", weight=ft.FontWeight.BOLD, color=T.TEXT_MUTED)),
    ],
    rows=rows,
    heading_row_color=T.SURFACE_ALT,
    horizontal_margin=15,
    column_spacing=20,
)

ft.Container(
    content=table,
    bgcolor=T.SURFACE,
    border_radius=10,
    border=T.border(1, T.SURFACE_ALT),
    padding=10,
)
```

Convenciones:

- Encabezados en mayúsculas, `BOLD` y `T.TEXT_MUTED`.
- `heading_row_color=T.SURFACE_ALT`.
- `horizontal_margin=15`, `column_spacing=20` (en tablas densas: `12`/`16`).
- Texto de celdas: `size=12` o `13`; dato principal con `W_500`.
- Acciones con `ft.IconButton` y colores semánticos.

### 7.4 Tarjetas en móvil

Cuando `is_mobile_page(self.page)` es `True`, reemplaza la tabla por tarjetas:

```python
ft.Container(
    content=ft.Column(
        controls=[
            ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text(name, size=15, weight=ft.FontWeight.BOLD, color=T.TEXT),
                            ft.Text(subtitle, size=11, color=T.TEXT_MUTED),
                        ],
                        spacing=2,
                        expand=True,
                    ),
                    status_chip,
                ],
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            ft.Row([
                ft.Icon(ft.Icons.EMAIL_OUTLINED, size=14, color=T.TEXT_SUBTLE),
                ft.Text(email, size=12, color=T.TEXT_SECONDARY),
            ], spacing=6),
            ft.Row([actions], alignment=ft.MainAxisAlignment.END),
        ],
        spacing=8,
    ),
    padding=14,
    bgcolor=T.SURFACE,
    border_radius=10,
    border=T.border(1, T.SURFACE_ALT),
)
```

### 7.5 Chips de estado

```python
status_chip = ft.Container(
    content=ft.Text(
        "Activo",
        size=11,
        color=T.SUCCESS_TEXT,
        weight=ft.FontWeight.BOLD,
    ),
    bgcolor=T.SUCCESS_BG,
    padding=ft.Padding.symmetric(horizontal=8, vertical=4),
    border_radius=12,
)
```

Equivalencias habituales:

| Estado | Texto | Fondo |
|---|---|---|
| Activo / Autorizado | `T.SUCCESS_TEXT` | `T.SUCCESS_BG` |
| Inactivo / Error | `T.DANGER_TEXT` | `T.DANGER_BG` |
| Pendiente / Advertencia | `T.WARNING` | `T.WARNING_BG` |
| Informativo / Enviado | `T.INFO_TEXT` | `T.INFO_BG` |
| Neutro | `T.TEXT_MUTED` | `T.SURFACE_ALT` |

### 7.6 Estado vacío

```python
ft.Container(
    content=ft.Column(
        controls=[
            ft.Icon(ft.Icons.SEARCH_OFF_ROUNDED, size=48, color=T.ICON_MUTED),
            ft.Text("No se encontraron registros", color=T.TEXT_MUTED, size=16),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=10,
    ),
    padding=40,
    alignment=ft.Alignment(0, 0),
)
```

### 7.7 Formularios en diálogo

- Contenedor con `width=form_dialog_width(page, 500)`.
- `ft.Column(..., spacing=12, tight=True)`.
- Campos en filas de dos cuando el ancho lo permita.
- Acciones: `TextButton("Cancelar")` + `FilledButton("Guardar")`.
- Para errores, un `ft.Text` rojo (`T.DANGER_TEXT`) dentro del diálogo, no un toast silencioso.

### 7.8 Botones

| Tipo | Uso | Color |
|---|---|---|
| `FilledButton` / `primary_button()` | Acción principal. | `T.PRIMARY` + `T.ON_ACCENT` |
| `FilledButton` con `T.DANGER` | Eliminar o acción destructiva. | `T.DANGER` + `T.ON_ACCENT` |
| `OutlinedButton` | Acción secundaria. | Borde `T.BORDER`, texto `T.TEXT` |
| `TextButton` | Cancelar, enlaces, acciones terciarias. | `T.TEXT_MUTED` o acento |
| `IconButton` | Acciones de fila. | `T.INFO`, `T.CYAN_TEXT`, `T.DANGER`, etc. |

### 7.9 Permisos por módulo

Cada vista declara su módulo y consulta la matriz del rol. No uses permisos
globales en código nuevo:

```python
MODULE = "clients"

if not AppState.has_permission("can_read", MODULE):
    return MainLayout(page=self.page, content=acceso_restringido(), router=self.router)

can_write = AppState.has_permission("can_write", MODULE)
can_update = AppState.has_permission("can_update", MODULE)
can_delete = AppState.has_permission("can_delete", MODULE)

ft.IconButton(
    icon=ft.Icons.EDIT_OUTLINED,
    icon_color=T.INFO if can_update else T.TEXT_SUBTLE,
    disabled=not can_update,
    tooltip="Editar" if can_update else "Sin permiso",
    on_click=...,
)
```

- El catálogo de módulos vive en `core/permissions.py`.
- La matriz se guarda en `role_permissions` y se edita en `/roles`.
- `MainLayout` y `core/router.py` ya filtran rutas sin `can_read`; la comprobación
  dentro de la vista es la segunda barrera.
- Si una acción escribe datos de otro módulo (por ejemplo, crear un cliente
  desde el POS), valida también ese módulo: `AppState.has_permission("can_write", "clients")`.
- En la matriz de roles, marca `can_read` automáticamente cuando se concede
  Crear, Editar o Eliminar.

### 7.10 Login

`LoginView` es una excepción al layout estándar:

- No usa `MainLayout`.
- Devuelve un `ft.Column` con fondo `T.LOGIN_BG`.
- Tarjeta central `T.LOGIN_CARD`, radio `24`, borde `T.LOGIN_BORDER`.
- Botón con gradiente `T.INDIGO → T.INDIGO_DARK` y sombra `T.PRIMARY_SHADOW`.
- Inputs con radio `12`, `label_style=ft.TextStyle(color=T.TEXT_MUTED)`.

No reutilices los tokens `LOGIN_*` fuera de la pantalla de login.

---

## 8. Checklist para una pantalla nueva

- [ ] La vista está en `app/views/pages/<nombre>_view.py` y la clase termina en `View`.
- [ ] La ruta está registrada en `configs/routes.py` con su clave `module`.
- [ ] El módulo está en `MODULES` de `core/permissions.py`.
- [ ] Devuelve `MainLayout(page, content, router)`.
- [ ] Usa `from core import theme as T` y tokens semánticos.
- [ ] Tiene guard de `AppState.has_permission("can_read", MODULE)`.
- [ ] Las acciones de escritura respetan `can_write`, `can_update` y `can_delete` con el mismo módulo.
- [ ] En móvil (`is_mobile_page`) usa tarjetas; en escritorio, tabla.
- [ ] Los diálogos usan `form_dialog_width()` o `wide_dialog_width()`.
- [ ] Los avisos usan `show_toast()`.
- [ ] Los estados vacíos tienen icono y mensaje.
- [ ] No hay colores hexadecimales fuera de tokens.
- [ ] No se capturan tokens con `from core.theme import ...`.
- [ ] Se probó en tema claro y oscuro.
- [ ] Se probó en ancho móvil (< 800 px) y escritorio.

---

## 9. Inconsistencias conocidas y deuda técnica

| Tema | Detalle | Recomendación |
|---|---|---|
| `_all_border` duplicado | 14 vistas definen la misma función local. | Usar `T.border()` o `T.all_border()` en código nuevo. |
| Diálogos con ancho fijo | Algunas vistas usan `width=500` o `width=680` directo. | Migrar a `form_dialog_width()` / `wide_dialog_width()`. |
| Toasts y diálogos locales | Varias vistas redefinen `show_dialog`/`show_toast`. | Importar los helpers de `ui_helpers.py`. |
| Paleta pastel de Proveedores | `suppliers_view.py` usa colores hexadecimales fijos (`PASTEL_*`). | Es una excepción visual; no copiarla. Migrar a tokens para soportar bien el tema oscuro. |
| Sin tokens de espaciado/tipografía | Los tamaños y paddings están dispersos en las vistas. | Si se necesita, crear constantes en `core/theme.py` o un futuro `ui_tokens.py`. |
| `font_family="monospace"` aislado | Solo se usa para la respuesta del SRI. | Mantenerlo así; no usar monospace para texto general. |
| `SettingsModel` y `HelpModel` | Son marcadores sin tabla. | No son referencias de UI; no afectan al tema. |

---

## 10. Referencias rápidas

```python
# Tema y tokens
from core import theme as T
T.apply(page, T.DARK)
T.border()
T.is_dark()

# Layout
from app.views.layouts.main_layout import MainLayout

# Helpers de UI
from app.views.ui_helpers import (
    open_dialog, close_dialog, show_toast,
    form_dialog_width, wide_dialog_width,
    stat_card, chip, primary_button, field, section_title,
    is_mobile_page, is_mobile_platform,
    get_file_picker, share_file, open_path, open_url,
)

# Importación / exportación
from app.views.components.import_export import build_import_export_bar

# Responsive
from core.responsive import MOBILE_BREAKPOINT, get_device_type, is_mobile
```

---

**Última revisión:** 2026-10-24
**Mantenedores:** equipo TntPos
