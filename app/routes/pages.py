# app/routes/pages.py
from fastapi import APIRouter, Request, Depends, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel

from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.client_profile import ClientProfile
from app.models.user_client_access import UserClientAccess

from app.core.templating import templates
from app.core.config import settings
from app.models.user import User, UserRole

# Importaciones necesarias para el guardián y las rutas
from app.apis.deps import get_current_user_from_cookie, require_login_for_pages

# --- ¡NUEVA VERSIÓN DEL GUARDIÁN! ---
async def user_flow_guardian(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_from_cookie)
):
    if not current_user:
        return

    current_path = request.url.path
    user_role = current_user.role

    # Definimos rutas clave
    home_path = str(request.url_for("home_page"))
    onboarding_path = str(request.url_for("onboarding_start_page"))
    client_dashboard_path = str(request.url_for("client_dashboard_page"))
    supervisor_dashboard_path = str(request.url_for("supervisor_dashboard_page"))
    
    # Definimos Zonas Prohibidas
    staff_zone_prefix = "/dashboard/super"
    client_zone_prefix = "/dashboard/client"

    # Roles
    client_roles = {UserRole.CLIENT_FREEMIUM, UserRole.CLIENT_PAID}
    staff_roles = {
        UserRole.STAFF_COLLABORATOR,
        UserRole.STAFF_MANAGER,
        UserRole.STAFF_CEO,
        UserRole.ADMIN
    }

    # Regla 1: Usuario en Onboarding
    if user_role == UserRole.AUTHENTICATED:
        if current_path != onboarding_path:
            raise HTTPException(status_code=307, detail="Redirecting to onboarding", headers={"Location": onboarding_path})
        return

    # Regla 2: Usuario Cliente
    elif user_role in client_roles:
        if current_path.startswith(staff_zone_prefix):
            raise HTTPException(status_code=307, detail="Redirecting to client dashboard", headers={"Location": client_dashboard_path})
        if current_path == onboarding_path:
            raise HTTPException(status_code=307, detail="Redirecting to client dashboard", headers={"Location": client_dashboard_path})
        if current_path == home_path:
            raise HTTPException(status_code=307, detail="Redirecting to client dashboard", headers={"Location": client_dashboard_path})

    # Regla 3: Usuario Staff
    elif user_role in staff_roles:
        if current_path.startswith(client_zone_prefix):
             raise HTTPException(status_code=307, detail="Redirecting to staff dashboard", headers={"Location": supervisor_dashboard_path})
        if current_path == home_path:
             raise HTTPException(status_code=307, detail="Redirecting to staff dashboard", headers={"Location": supervisor_dashboard_path})

# --- Router y Rutas ---
APP_DIR_FOR_STATIC = Path(__file__).resolve().parent.parent.parent.parent
router = APIRouter(tags=["Frontend Pages"])

# --- PÁGINAS ---

@router.get("/", response_class=HTMLResponse, name="home_page", dependencies=[Depends(user_flow_guardian)])
async def serve_home_page(request: Request, current_user: Optional[User] = Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse("index.html", {"request": request, "current_user": current_user, "settings": settings})

@router.get("/onboarding", response_class=HTMLResponse, name="onboarding_start_page", dependencies=[Depends(require_login_for_pages)])
async def serve_onboarding_page(request: Request, current_user: User = Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse("dashboard_onboarding.html", {"request": request, "current_user": current_user, "settings": settings})

@router.get("/dashboard/client", response_class=HTMLResponse, name="client_dashboard_page", dependencies=[Depends(require_login_for_pages), Depends(user_flow_guardian)])
async def serve_client_dashboard_page(
    request: Request,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    client_profiles = (
        db.query(ClientProfile)
        .join(UserClientAccess, UserClientAccess.client_profile_id == ClientProfile.id)
        .filter(UserClientAccess.user_id == current_user.id)
        .order_by(ClientProfile.business_name)
        .all()
    )
    context = {
        "request": request,
        "current_user": current_user,
        "settings": settings,
        "client_profiles": client_profiles
    }
    return templates.TemplateResponse("dashboard_client.html", context)

# --- La ruta del dashboard de staff/supervisor ha sido movida a su propio módulo ---

# --- RUTAS DE UTILIDAD ---

@router.get("/terms", response_class=HTMLResponse, name="terms_page")
async def serve_terms_page(request: Request, current_user: Optional[User] = Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse("terms_placeholder.html", {"request": request, "current_user": current_user, "settings": settings})

@router.get("/login", response_class=HTMLResponse, name="login_page")
async def serve_login_page(request: Request):
    home_url_with_hash = str(request.url_for("home_page")) + "#auth-login"
    return RedirectResponse(url=home_url_with_hash)

@router.get("/register/client", response_class=HTMLResponse, name="register_client_page")
async def serve_register_client_page(request: Request):
    home_url_with_hash = str(request.url_for("home_page")) + "#auth-register"
    return RedirectResponse(url=home_url_with_hash)

@router.get("/logout", name="logout", summary="Cierra sesión y borra la cookie")
async def logout_user_and_clear_cookie(request: Request):
    home_url = str(request.url_for("home_page"))
    response = RedirectResponse(url=home_url)
    response.delete_cookie(settings.ACCESS_TOKEN_COOKIE_NAME, path="/")
    return response

@router.get("/favicon.ico", include_in_schema=False)
async def favicon():
    favicon_path = APP_DIR_FOR_STATIC / "static" / "img" / "favicon.ico"
    if favicon_path.is_file():
        return FileResponse(favicon_path)
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

# --- Rutas para modales y componentes HTMX que pueden ser llamadas desde cualquier página ---

class OnboardingForm(BaseModel):
    client_ruc_modal: str
    sol_password_modal: str

@router.get("/onboarding/get-register-form", response_class=HTMLResponse, name="onboarding_get_form")
async def get_register_ruc_form(request: Request):
    return templates.get_template("onboarding/partials/_register_ruc_form_content.html").render({"request": request})

@router.post("/onboarding/finalize-htmx", response_class=HTMLResponse, name="onboarding_finalize_htmx")
async def onboarding_finalize_htmx(request: Request):
    return HTMLResponse("""
        <div class="text-center p-4">
            <h3 class="font-bold text-lg text-green-300">¡Solicitud Recibida!</h3>
            <p class="text-gray-300">Verificaremos los datos y te notificaremos. Puedes cerrar esta ventana.</p>
        </div>
    """)