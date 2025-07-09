# app/apis/v1/endpoints/pages.py
from fastapi import APIRouter, Request, Depends, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.client_profile import ClientProfile
from app.models.user_client_access import UserClientAccess

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
    if not current_user:
        print("[Guardian] No hay usuario, permitiendo acceso.")
        return

    current_path = request.url.path
    user_role = current_user.role

    print(f"\n--- [Guardian Debug Tick] ---")
    print(f"User: {current_user.email}, Role: {user_role.value}")
    print(f"Requested Path: {current_path}")

    # Definimos rutas clave
    home_path = str(request.url_for("home_page"))
    onboarding_path = str(request.url_for("onboarding_start_page"))
    client_dashboard_path = str(request.url_for("client_dashboard_page"))
    staff_dashboard_path = str(request.url_for("staff_dashboard_page"))
    
    # Definimos Zonas Prohibidas
    staff_zone_prefix = "/dashboard/staff"
    client_zone_prefix = "/dashboard/client"

    # --- Roles Corregidos ---
    client_roles = {UserRole.CLIENT_FREEMIUM, UserRole.CLIENT_PAID}
    staff_roles = {
        UserRole.STAFF_COLLABORATOR,
        UserRole.STAFF_MANAGER,
        UserRole.STAFF_CEO,
        UserRole.ADMIN
    }

    # Regla 1: Usuario en Onboarding (rol 'authenticated')
    if user_role == UserRole.AUTHENTICATED:
        if current_path != onboarding_path:
            print(f"✅ [Guardian Decision] REDIRECT: 'authenticated' user en '{current_path}' a '{onboarding_path}'.")
            raise HTTPException(status_code=307, detail="Redirecting to onboarding", headers={"Location": onboarding_path})
        print(f"✅ [Guardian Decision] ALLOW: 'authenticated' user ya está en onboarding.")
        return

    # Regla 2: Usuario Cliente (roles 'client_*')
    elif user_role in client_roles:
        # Un cliente NO PUEDE estar en la zona de staff.
        if current_path.startswith(staff_zone_prefix):
            print(f"✅ [Guardian Decision] REDIRECT: client en zona de staff a '{client_dashboard_path}'.")
            raise HTTPException(status_code=307, detail="Redirecting to client dashboard", headers={"Location": client_dashboard_path})
        
        # Un cliente que ya pasó el onboarding no debería volver a la página de onboarding.
        if current_path == onboarding_path:
            print(f"✅ [Guardian Decision] REDIRECT: client ya 'onboarded' a '{client_dashboard_path}'.")
            raise HTTPException(status_code=307, detail="Redirecting to client dashboard", headers={"Location": client_dashboard_path})
        
        # ✅ NUEVA REGLA DE SEGURIDAD: Un cliente logueado no debería estar en la home page.
        if current_path == home_path:
            print(f"✅ [Guardian Decision] REDIRECT: client logueado en home a '{client_dashboard_path}'.")
            raise HTTPException(status_code=307, detail="Redirecting to client dashboard", headers={"Location": client_dashboard_path})


    # Regla 3: Usuario Staff (roles 'staff_*' y 'admin')
    elif user_role in staff_roles:
        # Un staff NO PUEDE estar en la zona de cliente.
        if current_path.startswith(client_zone_prefix):
             print(f"✅ [Guardian Decision] REDIRECT: staff en zona de cliente a '{staff_dashboard_path}'.")
             raise HTTPException(status_code=307, detail="Redirecting to staff dashboard", headers={"Location": staff_dashboard_path})
        
        # ✅ NUEVA REGLA DE SEGURIDAD: Un staff logueado no debería estar en la home page.
        if current_path == home_path:
             print(f"✅ [Guardian Decision] REDIRECT: staff logueado en home a '{staff_dashboard_path}'.")
             raise HTTPException(status_code=307, detail="Redirecting to staff dashboard", headers={"Location": staff_dashboard_path})


    print(f"✅ [Guardian Decision] ALLOW: No hay reglas de redirección para '{current_path}'.")
    # Si ninguna regla de redirección se aplicó, se permite el acceso.

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
    db: Session = Depends(get_db)  # Asegura que la sesión de DB esté inyectada
):
    """
    Renderiza el dashboard del cliente, obteniendo primero los perfiles
    de cliente (RUCs) a los que el usuario tiene acceso.
    """
    
    # --- LÓGICA CLAVE PARA OBTENER LOS RUCs ---
    client_profiles = (
        db.query(ClientProfile)
        .join(UserClientAccess, UserClientAccess.client_profile_id == ClientProfile.id)
        .filter(UserClientAccess.user_id == current_user.id)
        .order_by(ClientProfile.business_name)
        .all()
    )
    
    # (Opcional pero recomendado) Imprime para verificar en la consola del servidor
    print(f"--- DEBUG: Perfiles para {current_user.email}: {[p.ruc for p in client_profiles]} ---")

    context = {
        "request": request, 
        "current_user": current_user, 
        "settings": settings,
        "client_profiles": client_profiles # Pasamos la lista a la plantilla
    }
    
    return templates.TemplateResponse("dashboard_client.html", context)

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



@router.get("/test-modal", response_class=HTMLResponse)
async def test_modal_page(request: Request):
    """
    Ruta de prueba para aislar el problema del modal, HTMX e Hyperscript.
    """
    return templates.TemplateResponse("test_modal.html", {"request": request})

@router.get("/test-modal/content", response_class=HTMLResponse)
async def test_modal_content(request: Request):
    """
    Ruta que devuelve el contenido del modal (el mensaje de éxito).
    """
    return templates.TemplateResponse("partials/_test_success.html", {"request": request})


"""
#NUEVA RUTA PARA EL MODAL LIBERADO DE REGISTRAR RUC (PIMERO O OTROS)
"""
@router.get("/onboarding/get-register-form", response_class=HTMLResponse, name="onboarding_get_form")
async def get_register_ruc_form(request: Request):
    """Devuelve el contenido del formulario para registrar un RUC."""
    return templates.get_template("onboarding/partials/_register_ruc_form_content.html").render({"request": request})

# Necesitaremos una nueva ruta para el envío con HTMX
# Asumimos que la lógica es similar a 'onboarding_finalize', pero devuelve HTML
@router.post("/onboarding/finalize-htmx", response_class=HTMLResponse, name="onboarding_finalize_htmx")
async def onboarding_finalize_htmx(request: Request):
    # TODO: Aquí va la lógica para procesar el formulario de registro de RUC.
    # Por ahora, devolvemos un mensaje de éxito para HTMX.
    return HTMLResponse("""
        <div class="text-center p-4">
            <h3 class="font-bold text-lg text-green-300">¡Solicitud Recibida!</h3>
            <p class="text-gray-300">Verificaremos los datos de tu nuevo RUC y te notificaremos. Puedes cerrar esta ventana.</p>
        </div>
    """)