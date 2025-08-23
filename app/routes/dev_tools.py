# app/routes/dev_tools.py

from fastapi import APIRouter, Depends, HTTPException, Request, Query, status
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.user import User, UserRole
from app.core.security import create_access_token
from app.core.config import settings
# --- ¡LA IMPORTACIÓN CLAVE QUE FALTABA! ---
from app.core.templating import templates

router = APIRouter()

# En app/routes/dev_tools.py

@router.get("/login-as/{user_id}", name="dev_login_as_user")
async def dev_login_as_user(request: Request, user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail=f"Usuario con ID {user_id} no encontrado.")

    # --- ¡LÓGICA MEJORADA DE REDIRECCIÓN! ---
    redirect_url = ""
    if user.role == UserRole.STAFF_COLLABORATOR:
        redirect_url = request.url_for("staff_dashboard_page")
    elif user.role in [UserRole.STAFF_MANAGER, UserRole.STAFF_CEO, UserRole.ADMIN]:
        redirect_url = request.url_for("supervisor_dashboard_page")
    elif user.role in [UserRole.CLIENT_FREEMIUM, UserRole.CLIENT_PAID]:
        redirect_url = request.url_for("client_dashboard_page")
    else:
        redirect_url = request.url_for("home_page")

    access_token = create_access_token(subject=user.id)
    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key=settings.ACCESS_TOKEN_COOKIE_NAME, value=access_token, httponly=True)
    return response


# --- ENDPOINT PARA EL MODAL DE ALERTA GENÉRICO ---
@router.get("/alert-modal", response_class=HTMLResponse, name="get_alert_modal")
async def get_alert_modal(
    request: Request,
    title: str = Query("Atención"),
    message: str = Query("Ha ocurrido un error inesperado.")
):
    """
    Genera el contenido HTML para un modal de alerta genérico.
    """
    return templates.TemplateResponse("partials/_alert_modal.html", {
        "request": request,
        "title": title,
        "message": message
    })