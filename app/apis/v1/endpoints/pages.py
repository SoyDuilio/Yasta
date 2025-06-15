# app/apis/v1/endpoints/pages.py
from fastapi import APIRouter, Request, Depends, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from pathlib import Path
from typing import Optional

from app.core.templating import templates
from app.core.config import settings
from app.models.user import User, UserRole

# Importaciones necesarias para el guardián y las rutas
from app.apis.deps import get_current_user_from_cookie, require_login_for_pages

# --- ¡EL GUARDIÁN VIVE AQUÍ AHORA! ---
# --- ¡NUEVA VERSIÓN DEL GUARDIÁN! ---
# En app/apis/v1/endpoints/pages.py
async def user_flow_guardian(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_from_cookie)
):
    """
    Dependencia de flujo de usuario final.
    Envía a cada rol a su zona, pero permite explícitamente a los clientes
    visitar la página de onboarding.
    """
    if not current_user or request.url.path.endswith("/logout"):
        return

    current_path = request.url.path
    user_role = current_user.role

    # --- Definimos las rutas de destino y las rutas permitidas ---
    onboarding_path = str(request.url_for("onboarding_start_page"))
    client_dashboard_path = str(request.url_for("client_dashboard_page"))
    staff_dashboard_path = str(request.url_for("staff_dashboard_page"))

    # Roles
    client_roles = {UserRole.CLIENT_FREEMIUM, UserRole.CLIENT_PAID}
    staff_roles = {UserRole.STAFF_COLLABORATOR, UserRole.STAFF_MANAGER, UserRole.STAFF_CEO, UserRole.ADMIN}

    # --- LÓGICA DE REDIRECCIÓN POR ZONAS ---

    # Regla 1: Un usuario recién autenticado siempre debe ir a onboarding.
    if user_role == UserRole.AUTHENTICATED:
        if current_path != onboarding_path:
            raise HTTPException(
                status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                headers={"Location": onboarding_path},
            )
        return # Si ya está en onboarding, no hacemos nada más.

    # Regla 2: Un usuario Cliente.
    elif user_role in client_roles:
        client_zone_prefix = "/dashboard/client"
        # Si el cliente está intentando acceder a una página FUERA de su zona...
        if not current_path.startswith(client_zone_prefix):
            # ...PERMITIMOS explícitamente que visite la página de onboarding.
            if current_path == onboarding_path:
                return  # Lo dejamos en paz, rompiendo el bucle.
            
            # Para cualquier otra página fuera de su zona, lo mandamos a su dashboard.
            raise HTTPException(
                status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                headers={"Location": client_dashboard_path},
            )

    # Regla 3: Un usuario Staff.
    elif user_role in staff_roles:
        staff_zone_prefix = "/dashboard/staff"
        if not current_path.startswith(staff_zone_prefix):
            raise HTTPException(
                status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                headers={"Location": staff_dashboard_path},
            )

    # Si ninguna regla de redirección se aplicó, significa que el usuario está
    # en una página permitida para su rol. El flujo continúa.

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
async def serve_client_dashboard_page(request: Request, current_user: User = Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse("dashboard_client.html", {"request": request, "current_user": current_user, "settings": settings})

@router.get("/dashboard/staff", response_class=HTMLResponse, name="staff_dashboard_page", dependencies=[Depends(require_login_for_pages), Depends(user_flow_guardian)])
async def serve_staff_dashboard_page(request: Request, current_user: User = Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse("dashboard_staff.html", {"request": request, "current_user": current_user, "settings": settings})

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