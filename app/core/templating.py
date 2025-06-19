# app/core/templating.py
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from fastapi import FastAPI # Solo para el ejemplo de montaje
from datetime import datetime

# Definir la ruta base de la aplicación para construir las rutas a templates y static
BASE_APP_DIR = Path(__file__).resolve().parent.parent # Sube dos niveles (core -> app)

templates = Jinja2Templates(directory=str(BASE_APP_DIR / "templates"))

# --- 2. AÑADIR LA FUNCIÓN AL CONTEXTO GLOBAL ---
templates.env.globals['now'] = datetime.now
# -----------------------------------------------

def mount_static_files(app: FastAPI):
    app.mount("/static", StaticFiles(directory=str(BASE_APP_DIR / "static")), name="static")

# No necesitas instanciar `templates` en `main.py` si lo importas desde aquí.
# Solo necesitarías llamar a `mount_static_files(app)` en `main.py`.