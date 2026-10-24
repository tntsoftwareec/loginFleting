¡Hola!

Has creado un proyecto de Flet y ahora quieres poner en marcha la aplicación. Para iniciar el proyecto, debes ejecutar el comando `flet run` desde la carpeta raíz del proyecto.

A continuación te explico los pasos a seguir:

# 1. Verificar que la estructura es correcta

Tu proyecto debe tener una estructura de carpetas similar a esta:

```text
nombre_de_tu_app/
│
├── main.py
├── requirements.txt
├── assets/
└── README.md
```

### 1.1 ¿Qué debe contener main.py?

**main.py** es el punto de entrada de tu aplicación. Debe importar el módulo **flet** y definir la función principal de la aplicación.

Aquí tienes un ejemplo básico:

```python
import flet as ft
from views.login_view import LoginView

def main(page: ft.Page):
    page.title = "Mi App"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    # Ruta: / -> login
    page.add(LoginView(page))

ft.app(target=main)
```

# 2. Ejecutar la aplicación

Para iniciar la aplicación, navega hasta la carpeta raíz de tu proyecto y ejecuta el siguiente comando:

```bash
flet run
```

**Nota:** Si no has instalado Flet globalmente, puedes usar **uvx** para ejecutar el comando sin necesidad de una instalación global:

```bash
uvx flet run
```

# 3. Solución de problemas comunes

## Error: "❌ main.py not found"

Este error indica que estás ejecutando el comando desde una carpeta donde no se encuentra el archivo **main.py**. Debes asegurarte de estar en la raíz del proyecto.

```bash
cd nombre_de_tu_app/
flet run
```

## Error: "App session started"

Este mensaje confirma que Flet ha iniciado la aplicación, pero es posible que no puedas ver la interfaz gráfica.

Verifica lo siguiente:

1.  **¿Tienes un entorno virtual activo?**

```bash
source .venv/bin/activate
flet run
```

2.  **¿Está Flet instalado correctamente?**

```bash
pip list | grep flet
```

21/02/2026 por Richar Tonato
añadido a git para control de versiones

COMO CREAR UNA RAMA Y TRABAJAR EN LA RAMA GITHUB
Visión general creada por IA
Para crear una rama y trabajar en ella usando la terminal y GitHub, debes actualizar tu repositorio local, crear la nueva rama, hacer cambios, subirlos y abrir un Pull Request.

1. Actualizar la rama principal
   Antes de empezar, asegúrate de tener la versión más reciente del código principal (main o master):

git pull

2. Crear y cambiar a la nueva rama
   Crea una nueva rama local y cámbiate a ella de inmediato con un solo comando:

git checkout -b nombre_de_tu_rama

(Sustituye nombre_de_tu_rama por un nombre corto y descriptivo, por ejemplo: feature/nuevo-login).

3. Trabajar y guardar los cambios
   Modifica los archivos que necesites en tu proyecto. Luego, guarda y confirma los cambios:

Agrega los archivos modificados a la zona de espera:

git add .

Confirma los cambios con un mensaje que describa lo que hiciste:

git commit -m "Mensaje descriptivo de tus cambios"

4. Subir la rama a GitHub
   Envía tu rama local al repositorio remoto por primera vez vinculándola correctamente:

git push -u origin nombre_de_tu_rama

5. Crear un Pull Request (Solicitud de extracción)
   Entra a tu repositorio en la página web de GitHub.
   Verás un aviso que dice que acabas de subir una nueva rama. Haz clic en el botón verde Compare & pull request.

---

## Variables de entorno

La app cifra datos sensibles (p. ej. la contraseña SMTP) usando una clave secreta.

- En el primer uso se genera automáticamente en `data/.secret_key` con permisos
  restringidos, por lo que no hace falta configurar nada.
- Si existe la variable de entorno `FLETING_SECRET_KEY`, tiene prioridad sobre
  el archivo local (útil en servidores o despliegues gestionados).

```bash
python -c "from app.services.encryption_service import generate_secret_key; print(generate_secret_key())"
export FLETING_SECRET_KEY="la-clave-generada"
```

> Si cambias la clave, los valores ya cifrados con la anterior no podrán
> descifrarse; vuelve a guardar la contraseña SMTP desde Mi Empresa.

## Dependencias

- `requirements.txt`: dependencias de **runtime**.

  ```bash
  pip install -r requirements.txt
  ```

  ⚠️ **No** pongas aquí un `pip freeze` completo ni herramientas como
  `flet-cli`/`flet-desktop`. El build móvil resuelve las dependencias
  transitivas según la plataforma destino, y esas herramientas no tienen
  wheels para Android/iOS.

- `requirements-dev.txt`: `requirements.txt` + la CLI y el runtime de
  escritorio de Flet (necesarios para `flet run`).

  ```bash
  pip install -r requirements-dev.txt
  ```

La app usa `ft.run()` como entry point (el antiguo `ft.app()` fue
eliminado en Flet 1.x), y `ft.Colors`/`ft.Icons` (nombres de Flet 1.x).

## Build

```bash
flet build apk            # móvil Android
flet build linux          # escritorio Linux
```

Si aparece un error como:

```text
ERROR: Could not find a version that satisfies the requirement
       cffi==2.1.1 (from versions: 2.0.0)
```

significa que `requirements.txt` contiene un `pip freeze` con versiones de
dependencias transitivas que no existen en el índice de la plataforma
destino (en Android solo hay `cffi 2.0.0`). Solución: usar el
`requirements.txt` depurado del repo (solo dependencias directas).

## Datos iniciales

Una instalación nueva **no carga clientes, productos, proveedores, servicios,
facturas ni cotizaciones de demostración**. Solo se crea:

- El usuario administrador: `admin@pos.com` / `admin123`.
- El cliente genérico `CONSUMIDOR FINAL`.
- Los roles base del sistema.
- Una configuración de empresa vacía para completar en **Mi Empresa**.

Cambia la contraseña del administrador después del primer ingreso.

### Limpiar datos de prueba de una base existente

Si ya estás usando una base con datos de demostración, ejecuta:

```bash
python scripts/clean_demo_data.py
```

El script conserva la configuración de la empresa y el usuario
`admin@pos.com`, y elimina facturas, cotizaciones, movimientos de inventario,
clientes, proveedores, productos, servicios y usuarios de prueba. También
borra los PDFs/XMLs generados y reinicia la numeración a 1.

Para revisar qué se eliminaría sin tocar la base:

```bash
python scripts/clean_demo_data.py --dry-run
```

Si tu administrador usa otro correo:

```bash
python scripts/clean_demo_data.py --keep-email tu-correo@dominio.com
```

## Ejecutar las pruebas

```bash
python -m unittest discover -s tests -t .
```

## Importación / Exportación de datos

Las vistas de **Clientes**, **Productos**, **Facturas** y **Cotizaciones**
incluyen una barra con cuatro acciones:

- **Importar**: carga un archivo Excel (`.xlsx`).
- **Plantilla**: descarga un Excel vacío con una hoja *Instrucciones*.
- **Excel**: exporta el listado actual a Excel.
- **PDF**: exporta el listado actual a PDF.

El formato exportado es el mismo que el del importador, por lo que un archivo
exportado puede reimportarse. Reglas:

- Clientes: se actualizan por `identificacion`.
- Productos: se actualizan por `codigo` (si falta, se busca por nombre y se
  genera un código).
- Facturas/Cotizaciones: cada `grupo` del archivo genera un comprobante nuevo
  (no reimportes el mismo archivo). La importación **no** descuenta stock ni
  envía correos.

La lógica está en `core/import_export.py` (adaptadores) y `core/documents/`
(Excel y PDF).

## Otras mejoras de las vistas

- **Listados responsive**: en móvil (< 800 px) las tablas se muestran como
  tarjetas.
- **Tarjetas de estadísticas**: resumen en Inicio, Facturas (nº y total
  facturado) y Cotizaciones (nº, total, enviadas y vigentes).
- **Facturación y cotización de servicios**: el POS y la nueva cotización
  incluyen una pestaña **Servicios**. También se puede agregar un servicio
  manual (sin registrarlo en el catálogo) con el botón `+` junto a las
  pestañas. Desde el catálogo de servicios se puede pulsar **Facturar** o
  **Cotizar** para abrir el flujo con ese servicio ya cargado.
- **Imágenes de productos**: al crear o editar un producto se puede
  seleccionar una imagen JPG, PNG o WEBP. La app la optimiza y guarda en
  `assets/products/images`; el listado muestra una miniatura y el PDF de las
  cotizaciones incluye la imagen de cada producto. Al abrir o enviar una
  cotización existente, su PDF se regenera con las imágenes actuales.
- **Logo de la empresa**: en **Mi Empresa** se puede seleccionar una imagen
  JPG, PNG o WEBP y quitarla cuando se desee. El logo se optimiza y guarda en
  `assets/company/`; se muestra en el encabezado de las facturas y
  cotizaciones en PDF. Si no hay logo personalizado, se usa el logo
  predeterminado de la app.
- **Inventario**: el módulo **Inventario** (`/inventory`) muestra el stock
  actual, el mínimo configurable por producto, las alertas de bajo stock y el
  valor total al costo. Permite registrar entradas, salidas y ajustes, y
  consultar el historial de movimientos por producto o general. Las ventas
  descuentan stock y quedan registradas automáticamente; la edición de un
  producto y la importación desde Excel también generan su movimiento.
- **Facturar cotizaciones**: desde el historial o el detalle de una
  cotización se puede generar una factura eligiendo la forma de pago y, si se
  desea, enviarla por correo. La cotización queda marcada como `FACTURADA`,
  se vincula con la factura creada, se descuenta el stock de los productos y
  se impide facturarla dos veces.
- **Envío de cotizaciones**:
  - **Correo**: adjunta el PDF y usa la configuración SMTP de Mi Empresa.
  - **WhatsApp**: comparte el PDF con la hoja nativa (en Android/iOS permite
    elegir WhatsApp y enviar el archivo adjunto). En escritorio abre WhatsApp
    con el mensaje y la carpeta del PDF para adjuntarlo.
