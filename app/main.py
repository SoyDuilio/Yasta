# app/main.py
from app.core.config import settings
print("--- INICIANDO VERIFICACIÓN DE SECRET_KEY ---")
try:
    # Usamos str() para asegurarnos de que funciona aunque Pydantic use un tipo SecretStr
    key_str = str(settings.SECRET_KEY)
    if len(key_str) > 8:
        print(f"SECRET_KEY cargada correctamente. Fragmento: {key_str[:4]}...{key_str[-4:]}")
    else:
        print("ADVERTENCIA: SECRET_KEY es demasiado corta o no se cargó.")
    print(f"ENVIRONMENT: {settings.ENVIRONMENT}")
except Exception as e:
    print(f"ERROR al leer la SECRET_KEY de la configuración: {e}")
print("------------------------------------------")

from fastapi import FastAPI
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.core.templating import mount_static_files

# --- ¡LA SOLUCIÓN DEFINITIVA ESTÁ AQUÍ! ---
# 1. Se importa el paquete de modelos. Esto ejecuta app/models/__init__.py
#    y carga TODOS los modelos en el orden correcto en la memoria de SQLAlchemy.
from app import models

# 2. Se importan los routers DESPUÉS de que los modelos ya son conocidos.
from app.apis.v1.api import api_router as v1_api_router
from app.apis.v1.endpoints import pages as pages_router


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
)

# --- MIDDLEWARES (Session, CORS) ---
# Versión corregida y segura para producción
# Leemos una variable de entorno. Si no existe, asumimos que no es producción.
# El '0' al final es el valor por defecto si la variable no se encuentra.
IS_PRODUCTION = settings.ENVIRONMENT == "production"

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    # El valor de https_only ahora depende del entorno
    https_only=IS_PRODUCTION,
    same_site="lax",
    max_age=14 * 24 * 60 * 60  # 14 días
)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# --- Montar archivos estáticos ---
mount_static_files(app)

# --- ROUTERS ---
# Para cuando se incluyen los routers, SQLAlchemy ya conoce todos los modelos.
app.include_router(v1_api_router, prefix=settings.API_V1_STR)
app.include_router(pages_router.router)

# --- Health Check ---
@app.get("/health", tags=["Utilities"])
async def health_check():
    return {"status": "healthy"}
