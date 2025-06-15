# app/main.py
from fastapi import FastAPI
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
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
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
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
