# app/main.py

# --- 1. Importaciones de Librerías Estándar y de Terceros ---
from fastapi import FastAPI, Request, Depends
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from fastapi.routing import APIRoute

from app.core.templating import templates
from app.core.config import settings

from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse


# --- 2. Importaciones del Proyecto (Organizadas por Módulo) ---
from app.core.config import settings
from app.core.templating import mount_static_files

# La importación de 'models' es crucial y debe ir antes de los routers
# para asegurar que SQLAlchemy conozca todos los modelos de antemano.
from app import models

# Importamos los routers que se registrarán en la aplicación principal.
# Se usan alias para mayor claridad.
from app.apis.v1.api import api_router as v1_api_router
from app.routes import pages as pages_router
from app.routes import payments as web_payments_router
from app.routes import dev_tools as dev_tools_router
from app.routes import declarations as web_declarations_router

# ¡NUEVOS ROUTERS DE DASHBOARDS!
from app.routes.dashboards import supervisor as supervisor_dashboard_router
# Aquí agregarás los otros routers de dashboard (client, staff, ceo) en el futuro

from app.routes.dashboards import staff as staff_dashboard_router

# --- 3. Inicialización de la Aplicación FastAPI ---
app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# --- 4. Configuración de Middlewares ---
# Middleware para manejar correctamente los headers de proxies.
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# Middleware para manejar las sesiones de usuario a través de cookies.
IS_PRODUCTION = settings.ENVIRONMENT == "production"
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    https_only=IS_PRODUCTION,  # Solo cookies seguras en producción
    same_site="lax",
    max_age=14 * 24 * 60 * 60  # Sesión expira en 14 días
)

# Middleware para la configuración de CORS.
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# --- 5. Montaje de Archivos Estáticos ---
# Sirve la carpeta /static para CSS, JS, imágenes, etc.
mount_static_files(app)

# --- 6. Inclusión de Routers (Organizados por Tipo) ---
# Para este punto, SQLAlchemy ya conoce todos los modelos.

# a) Rutas de la Aplicación Web (Sirven principalmente HTML)
app.include_router(pages_router.router, tags=["Web App - Pages"])
app.include_router(web_payments_router.router, prefix="/app", tags=["Web App - Payments"])
app.include_router(dev_tools_router.router, prefix="/dev", tags=["Developer Tools"])
app.include_router(web_declarations_router.router, prefix="/app/declarations", tags=["Web App - Declarations"])

# b) Rutas de Dashboards por Rol
# Por ahora solo el de supervisor, el de cliente se moverá aquí en una futura refactorización
app.include_router(supervisor_dashboard_router.router, prefix="/dashboard/super", tags=["Dashboard - Supervisor"])

# c) Rutas de la API (Sirven principalmente JSON)
app.include_router(v1_api_router, prefix=settings.API_V1_STR)

# ¡AÑADE ESTA LÍNEA PARA REGISTRAR EL ROUTER!
app.include_router(staff_dashboard_router.router, prefix="/dashboard/staff", tags=["Dashboard - Staff"])



# --- 7. Endpoints de Utilidad (directamente en la raíz) ---
@app.get("/health", tags=["Utilities"])
async def health_check():
    """Endpoint simple para verificar que la aplicación está en funcionamiento."""
    return {"status": "healthy"}

# --- 8. Código de Depuración (Opcional) ---
# Este bloque es útil durante el desarrollo para verificar las rutas registradas.
if not IS_PRODUCTION:
    print("\n--- LISTA DE RUTAS REGISTRADAS ---")
    for route in app.routes:
        if isinstance(route, APIRoute):
            print(f"Path: {route.path}, Name: {route.name}, Methods: {route.methods}")
    print("----------------------------------\n")


#PWA CANDI
@app.get("/pwa", response_class=HTMLResponse)
async def pwa_candi(request: Request):

    return templates.TemplateResponse("pwa/index.html", {"request": request})


#ALDO - IDEAS YASTA
@app.get("/ideas1", response_class=HTMLResponse)
async def ideas1(request: Request):
    return templates.TemplateResponse("ideas1.html", {"request": request})


@app.get("/ideas2", response_class=HTMLResponse)
async def ideas2(request: Request):
    return templates.TemplateResponse("ideas2.html", {"request": request})


@app.get("/ideas3", response_class=HTMLResponse)
async def ideas3(request: Request):
    return templates.TemplateResponse("ideas3.html", {"request": request})

