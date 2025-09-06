# app/apis/v1/endpoints/auth.py
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from app.apis import deps
from app.core import security
from app.core.config import settings
from app.models.user import User, UserRole

# Importamos desde el paquete 'crud', que gracias a __init__.py, nos da acceso a todo.
from app.crud import crud_user, crud_client_profile

from authlib.integrations.starlette_client import OAuth
oauth = OAuth()

# --- Configuración de OAuth ---
if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
    CONF_URL = 'https://accounts.google.com/.well-known/openid-configuration'
    oauth.register(name='google', server_metadata_url=CONF_URL, client_id=settings.GOOGLE_CLIENT_ID, client_secret=settings.GOOGLE_CLIENT_SECRET, client_kwargs={'scope': 'openid email profile'})
else:
    print("ADVERTENCIA DE CONFIGURACIÓN: Credenciales de Google OAuth incompletas.")

router = APIRouter(tags=["Authentication"])

# --- Helper para setear cookie ---
def _set_auth_cookie_and_redirect(response: RedirectResponse, user_id: int, request: Request) -> RedirectResponse:
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(subject=str(user_id), expires_delta=access_token_expires)
    is_secure_connection = request.url.scheme == "https"
    response.set_cookie(key=settings.ACCESS_TOKEN_COOKIE_NAME, value=access_token, httponly=True, max_age=int(access_token_expires.total_seconds()), samesite="Lax", secure=is_secure_connection, path="/")
    return response

# --- FUNCIÓN HELPER PARA REDIRECCIÓN POST-AUTH (CORREGIDA) ---
def get_post_auth_redirect_url(request: Request, user: User, db: Session) -> str:
    """
    Decide a dónde redirigir al usuario después de una autenticación exitosa,
    basándose en su rol específico.
    """
    
    # --- INICIO DE LA CORRECIÓN ---

    # REGLA 1: Rol de Contador -> A su dashboard de tareas.
    if user.role == UserRole.STAFF_COLLABORATOR:
        return str(request.url_for("staff_dashboard_page"))

    # REGLA 2: Roles de Gestión (Supervisor, CEO, Admin) -> A la consola de operaciones.
    elif user.role in [UserRole.STAFF_MANAGER, UserRole.STAFF_CEO, UserRole.ADMIN]:
        return str(request.url_for("supervisor_dashboard_page"))

    # --- FIN DE LA CORRECIÓN ---

    # REGLA 3: Roles de Cliente (con plan) -> Siempre al dashboard de cliente.
    elif user.role in [UserRole.CLIENT_FREEMIUM, UserRole.CLIENT_PAID]:
        return str(request.url_for("client_dashboard_page"))

    # REGLA 4: Rol de usuario recién autenticado -> Su destino es el onboarding.
    elif user.role == UserRole.AUTHENTICATED:
        # La lógica de onboarding no cambia y es correcta.
        user_has_completed_onboarding = crud_client_profile.has_any_access(db=db, user_id=user.id)
        if user_has_completed_onboarding:
            return str(request.url_for("client_dashboard_page"))
        else:
            return str(request.url_for("onboarding_start_page"))
            
    # REGLA 5 (POR DEFECTO): Si hay algún otro rol no contemplado, ir a la home.
    return str(request.url_for("home_page"))

# --- RUTAS DE AUTENTICACIÓN ---

@router.post("/login/token", name="login_for_access_token", summary="Login tradicional y seteo de cookie")
async def login_for_access_token_and_set_cookie(request: Request, db: Session = Depends(deps.get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = crud_user.authenticate_user(db, identifier=form_data.username, password=form_data.password)
    if not user or not user.is_active:
        error_redirect_url = str(request.url_for("home_page")) + "#auth-login-error"
        return RedirectResponse(url=error_redirect_url, status_code=status.HTTP_303_SEE_OTHER)

    final_redirect_url = get_post_auth_redirect_url(request, user, db)
    response = RedirectResponse(url=final_redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    return _set_auth_cookie_and_redirect(response, user.id, request)

@router.post("/register/email", name="register_via_email", summary="Registro con Email (Paso 1: Autenticación)")
async def register_via_email(request: Request, db: Session = Depends(deps.get_db), email: str = Form(...), password: str = Form(..., min_length=8)):
    user = crud_user.get_by_email(db, email=email)
    if user:
        error_redirect_url = str(request.url_for("home_page")) + "#auth-register-error-email"
        return RedirectResponse(url=error_redirect_url, status_code=status.HTTP_303_SEE_OTHER)

    user = crud_user.create_user_authenticated(db=db, email=email, password=password)

    db.flush()
    db.refresh(user)
    
    final_redirect_url = get_post_auth_redirect_url(request, user, db) # Lo mandará a onboarding
    response = RedirectResponse(url=final_redirect_url, status_code=status.HTTP_303_SEE_OTHER)
    return _set_auth_cookie_and_redirect(response, user.id, request)

@router.get("/login/google", name="auth_login_google")
async def login_via_google(request: Request):
    if not (settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET):
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Google OAuth no configurado.")
    return await oauth.google.authorize_redirect(request, str(request.url_for('auth_google_callback')))

@router.get("/google/callback", name="auth_google_callback")
async def auth_google_callback(request: Request, db: Session = Depends(deps.get_db)):
    logging.info("--- [1] ENTRANDO EN CALLBACK DE GOOGLE ---") # <-- NUEVA LÍNEA
    try:
        # 1. AUTENTICACIÓN CON GOOGLE
        try:
            logging.info("--- [2] INTENTANDO OBTENER TOKEN DE ACCESO DE GOOGLE ---") # <-- NUEVA LÍNEA
            token_data = await oauth.google.authorize_access_token(request)
            logging.info("--- [3] TOKEN DE ACCESO OBTENIDO EXITOSAMENTE ---") # <-- NUEVA LÍNEA
        except Exception as e:
            logging.error(f"--- ERROR AL OBTENER TOKEN DE GOOGLE: {e} ---", exc_info=True)
            # Si Google falla, no podemos continuar.
            raise e  # Relanzamos para que el bloque exterior lo capture

        user_info_google = token_data.get('userinfo')
        if not user_info_google or not user_info_google.get('email'):
            raise ValueError("La información del usuario de Google es incompleta.")
        
        logging.info(f"--- [4] PROCESANDO USUARIO: {user_info_google.get('email')} ---") # <-- NUEVA LÍNEA

        email_google = user_info_google.get('email')
        
        # 2. BUSCAR O CREAR USUARIO EN NUESTRA BD
        user = crud_user.get_by_email(db, email=email_google)

        if not user:
            # El usuario es nuevo, lo creamos y lo guardamos INMEDIATAMENTE.
            user = crud_user.create_user_from_google(
                db=db,
                email=email_google,
                full_name=user_info_google.get('name', ''),
                picture_url=user_info_google.get('picture', '')
            )
            try:
                db.commit()
                db.refresh(user)
            except Exception as db_error:
                logging.error(f"--- ERROR GENERAL NO MANEJADO EN GOOGLE CALLBACK: {e} ---", exc_info=True)
                db.rollback()
                # Este es un error crítico del servidor, lo relanzamos.
                raise db_error

        # 3. VERIFICACIONES DE ESTADO DEL USUARIO
        if not user.is_active:
            # Si el usuario existe pero está inactivo, lo redirigimos con un error específico.
            error_url = str(request.url_for("home_page")) + "#auth-inactive-error"
            return RedirectResponse(url=error_url)
            
        # 4. CREAR SESIÓN (COOKIE) Y REDIRIGIR
        # Si llegamos aquí, tenemos un usuario válido y activo.
        
        final_redirect_url = get_post_auth_redirect_url(request, user, db)
        response = RedirectResponse(url=final_redirect_url, status_code=status.HTTP_303_SEE_OTHER)
        
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(subject=str(user.id), expires_delta=access_token_expires)
        
        is_secure_connection = request.url.scheme == "https"
        response.set_cookie(
            key=settings.ACCESS_TOKEN_COOKIE_NAME, 
            value=access_token, 
            httponly=True, 
            max_age=int(access_token_expires.total_seconds()), 
            samesite="Lax",
            secure=is_secure_connection, 
            path="/"
        )
        
        return response

    except Exception as e:
        # Bloque de captura general para cualquier error no manejado en los pasos anteriores.
        print(f"--- ERROR GENERAL NO MANEJADO EN GOOGLE CALLBACK: {e} ---")
        error_redirect_url = str(request.url_for("home_page")) + "#auth-general-error"
        return RedirectResponse(url=error_redirect_url)