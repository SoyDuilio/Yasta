# app/apis/v1/endpoints/dev_tools.py

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

# --- IMPORTACIONES CORREGIDAS PARA TU PROYECTO ---
from app.db.session import get_db
from app.models.user import User
from app.models.fee_payment import FeePayment
from app.models.client_profile import ClientProfile

# ¡LA IMPORTACIÓN CLAVE! Usamos tu dependencia existente.
from app.apis.deps import get_current_active_staff

# --- FIN DE IMPORTACIONES ---

# Creamos un nuevo router que vivirá aquí.
router = APIRouter()

# La inicialización de templates debe estar aquí
templates = Jinja2Templates(directory="app/templates")

@router.get("/dev/dashboard", response_class=HTMLResponse, tags=["Developer Tools"])
async def get_dev_dashboard(
    request: Request, 
    db: Session = Depends(get_db),
    # ¡LA PROTECCIÓN! Usamos tu dependencia para asegurar que el usuario es staff.
    current_staff: User = Depends(get_current_active_staff) 
):
    """
    Muestra un dashboard provisional con datos clave de la aplicación.
    Solo accesible para usuarios con rol de staff.
    """
    all_payments = db.query(FeePayment).order_by(FeePayment.created_at.desc()).all()
    all_users = db.query(User).all()
    all_client_profiles = db.query(ClientProfile).all()

    context = {
        "request": request,
        "payments": all_payments,
        "users": all_users,
        "clients": all_client_profiles
    }
    return templates.TemplateResponse("dev/dashboard.html", context)