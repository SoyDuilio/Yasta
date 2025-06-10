# app/apis/v1/api.py
from fastapi import APIRouter

# Importamos todos los módulos de endpoints en una sola línea.
from app.apis.v1.endpoints import (
    auth,
    onboarding, # Añadimos onboarding a esta lista
    clients,
    staff,
    management,
    chatbot
)

api_router = APIRouter()

# Incluimos los routers.
# El prefijo de /auth ya está en el router de auth.py, no es necesario aquí,
# pero tenerlo aquí lo hace más explícito. Lo dejaremos.
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# --- CORRECCIÓN ---
# El router de onboarding ya tiene su propio prefijo "/onboarding",
# así que no necesitamos añadir otro aquí. Solo lo incluimos y le ponemos una etiqueta.
api_router.include_router(onboarding.router, tags=["Onboarding"])

# El resto de tus routers están bien.
api_router.include_router(clients.router, prefix="/clients", tags=["Clients"])
api_router.include_router(staff.router, prefix="/staff", tags=["Staff"])
api_router.include_router(management.router, prefix="/management", tags=["Management"])
api_router.include_router(chatbot.router, prefix="/chatbot", tags=["Chatbot"])
# Puedes añadir más routers a medida que los necesites