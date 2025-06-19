# app/routers/dev_tools.py

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

# --- CORRECCIONES DE IMPORTACIÓN (VERSIÓN FINAL) ---
# 1. Apuntamos a tu archivo de sesión real. ¡Esto ya está correcto!
from app.db.session import get_db 

# 2. Apuntamos a los modelos correctos según tu estructura de archivos.
from app.models.user import User
from app.models.fee_payment import FeePayment
from app.models.client_profile import ClientProfile # CORRECCIÓN: Usamos ClientProfile

# --- FIN DE CORRECCIONES ---

router = APIRouter(
    prefix="/dev",
    tags=["Developer Tools"],
    include_in_schema=False
)

templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard", response_class=HTMLResponse)
async def get_dev_dashboard(request: Request, db: Session = Depends(get_db)):
    """
    Muestra un dashboard provisional con datos clave de la aplicación.
    """
    all_payments = db.query(FeePayment).order_by(FeePayment.created_at.desc()).all()
    all_users = db.query(User).all()
    # CORRECCIÓN: Consultamos el modelo ClientProfile
    all_client_profiles = db.query(ClientProfile).all()

    context = {
        "request": request,
        "payments": all_payments,
        "users": all_users,
        # CORRECCIÓN: Pasamos los perfiles de cliente al template
        "clients": all_client_profiles 
    }
    return templates.TemplateResponse("dev/dashboard.html", context)