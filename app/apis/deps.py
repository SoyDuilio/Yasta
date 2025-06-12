# app/apis/deps.py
from fastapi import Request, Depends, HTTPException, status
from typing import Optional
from sqlalchemy.orm import Session
from jose import jwt, JWTError

from app.core import security
from app.core.config import settings
from app.db.session import get_db 
# Importamos desde el paquete 'crud', que gracias a __init__.py, nos da acceso a todo.
#from app.crud import crud_user
from app.crud import crud_user
from app.models import User, UserRole
#from app.models.user import User, UserRole

# --- DEPENDENCIA BASE (Sin cambios) ---
def get_current_user_from_cookie(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    token = request.cookies.get(settings.ACCESS_TOKEN_COOKIE_NAME)
    if not token:
        return None
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        user_id_str = payload.get("sub") # Lo nombramos _str para ser claros
        if user_id_str is None:
            return None
        
        # Movemos la consulta DENTRO del try. Si user_id_str no es un número,
        # lanzará un ValueError que será capturado por el except.
        user = crud_user.get(db, id=int(user_id_str))
        return user

    except (JWTError, ValueError): # Capturamos ambos tipos de error
        # Si el token es inválido o el user_id no es un entero, devolvemos None.
        return None

# --- DEPENDENCIA DE PROTECCIÓN BÁSICA PARA PÁGINAS WEB (Sin cambios) ---
async def require_login_for_pages(
    request: Request,
    current_user: Optional[User] = Depends(get_current_user_from_cookie)
) -> User:
    """Exige login para ver una página, si no, redirige a la home."""
    if not current_user:
        # Apunta al modal de login en la home page.
        login_url = str(request.url_for("home_page")) + "#auth-login"
        raise HTTPException(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            detail="Not authenticated",
            headers={"Location": login_url},
        )
    return current_user

# --- DEPENDENCIAS PARA APIs (Corregidas y funcionales) ---
def get_current_active_user(
    current_user: User = Depends(get_current_user_from_cookie)
) -> User:
    """Dependencia para APIs que requiere un usuario logueado y activo."""
    if not current_user or not current_user.is_active:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
    return current_user

def get_current_active_client(current_user: User = Depends(get_current_active_user)) -> User:
    # Comparamos si el rol está en el grupo de roles de cliente
    client_roles = {UserRole.CLIENT_FREEMIUM, UserRole.CLIENT_PAID}
    if current_user.role not in client_roles: # <-- LÍNEA CORREGIDA
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")
    return current_user

def get_current_active_staff(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Dependencia para APIs que requiere un usuario con rol de staff."""
    staff_roles = {UserRole.STAFF_COLLABORATOR, UserRole.STAFF_MANAGER, UserRole.STAFF_CEO, UserRole.ADMIN}
    if current_user.role not in staff_roles:
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")
    return current_user