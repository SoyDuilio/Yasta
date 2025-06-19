# app/apis/v1/api.py (Corregido)

from fastapi import APIRouter

# Importamos solo los endpoints que son verdaderamente de la API
from app.apis.v1.endpoints import (
    auth,
    onboarding,
    clients,
    staff,
    management,
    chatbot,
    utils
)

api_router = APIRouter()

# Registramos los routers de la API
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(onboarding.router, tags=["Onboarding"])
api_router.include_router(clients.router, prefix="/clients", tags=["Clients"])
api_router.include_router(staff.router, prefix="/staff", tags=["Staff"])
api_router.include_router(management.router, prefix="/management", tags=["Management"])
api_router.include_router(chatbot.router, prefix="/chatbot", tags=["Chatbot"])
api_router.include_router(utils.router, tags=["Utilities"])

# La referencia a 'pages.router' ha sido eliminada.