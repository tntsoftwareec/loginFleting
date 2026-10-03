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
