# app/apis/v1/api.py
from fastapi import APIRouter

# Importamos todos los módulos de endpoints en una sola línea.
from app.apis.v1.endpoints import (
    auth,
    onboarding,
    clients,
    staff,
    management,
    chatbot,
    utils  # <-- NUEVO ROUTER DE UTILIDADES
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(onboarding.router, tags=["Onboarding"]) # Prefix ya está en el router
api_router.include_router(clients.router, prefix="/clients", tags=["Clients"])
api_router.include_router(staff.router, prefix="/staff", tags=["Staff"])
api_router.include_router(management.router, prefix="/management", tags=["Management"])
api_router.include_router(chatbot.router, prefix="/chatbot", tags=["Chatbot"])

# Incluimos el nuevo router de utilidades
api_router.include_router(utils.router, tags=["Utilities"]) # Prefix ya está en el router