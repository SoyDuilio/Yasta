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
async def user_flow_guardian(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_from_cookie)
):
    """
    Dependencia inteligente que redirige al usuario a la página correcta
    según su rol, evitando bucles.
    """
    # Si no hay usuario, o si la ruta es la de logout, no hacemos nada.
    if not current_user or request.url.path == request.url_for("logout"):
        return

    current_path = request.url.path
    
    # 1. Usuario recién autenticado -> DEBE ir a onboarding
    if current_user.role == UserRole.AUTHENTICATED:
        onboarding_path = request.url_for("onboarding_start_page")
        if current_path != onboarding_path:
            raise HTTPException(
                status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                headers={"Location": onboarding_path},
            )
            
    # 2. Usuario Cliente -> DEBE ir al dashboard de cliente
    elif current_user.role.value.startswith("client_"):
        client_dashboard_path = request.url_for("client_dashboard_page")
        if current_path != client_dashboard_path:
             # Excepción: un cliente puede visitar la página de onboarding, no lo redirijas
            if current_path == request.url_for("onboarding_start_page"):
                return
            raise HTTPException(
                status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                headers={"Location": client_dashboard_path},
            )

    # 3. Usuario Staff/Admin -> DEBE ir al dashboard de staff
    elif current_user.role.value.startswith("staff_") or current_user.role == UserRole.ADMIN:
        staff_dashboard_path = request.url_for("staff_dashboard_page")
        if current_path != staff_dashboard_path:
            raise HTTPException(
                status_code=status.HTTP_307_TEMPORARY_REDIRECT,
                headers={"Location": staff_dashboard_path},
            )

# --- FIN DEL GUARDIÁN ---

APP_DIR_FOR_STATIC = Path(__file__).resolve().parent.parent.parent.parent
router = APIRouter(tags=["Frontend Pages"])

# --- PÁGINAS ---

@router.get("/", response_class=HTMLResponse, name="home_page", dependencies=[Depends(user_flow_guardian)])
async def serve_home_page(request: Request, current_user: Optional[User] = Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse("index.html", {"request": request, "current_user": current_user, "settings": settings})

@router.get("/onboarding", response_class=HTMLResponse, name="onboarding_start_page", dependencies=[Depends(require_login_for_pages)])
async def serve_onboarding_page(request: Request, current_user: User = Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse("onboarding.html", {"request": request, "current_user": current_user, "settings": settings})

@router.get("/dashboard/client", response_class=HTMLResponse, name="client_dashboard_page", dependencies=[Depends(require_login_for_pages), Depends(user_flow_guardian)])
async def serve_client_dashboard_page(request: Request, current_user: User = Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse("client/dashboard.html", {"request": request, "current_user": current_user, "settings": settings})

@router.get("/dashboard/staff", response_class=HTMLResponse, name="staff_dashboard_page", dependencies=[Depends(require_login_for_pages), Depends(user_flow_guardian)])
async def serve_staff_dashboard_page(request: Request, current_user: User = Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse("staff/dashboard.html", {"request": request, "current_user": current_user, "settings": settings})

# --- RUTAS DE UTILIDAD ---

@router.get("/terms", response_class=HTMLResponse, name="terms_page")
async def serve_terms_page(request: Request, current_user: Optional[User] = Depends(get_current_user_from_cookie)):
    return templates.TemplateResponse("terms.html", {"request": request, "current_user": current_user, "settings": settings})

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