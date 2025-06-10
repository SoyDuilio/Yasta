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
        user_id = payload.get("sub")
        if user_id is None:
            return None
    except JWTError:
        return None
    
    user = crud_user.get(db, id=int(user_id))
    return user

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

def get_current_active_client(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Dependencia para APIs que requiere un usuario con rol de cliente."""
    if not current_user.role.value.startswith("client_"):
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")
    return current_user

def get_current_active_staff(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """Dependencia para APIs que requiere un usuario con rol de staff."""
    if not (current_user.role.value.startswith("staff_") or current_user.role == UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="The user doesn't have enough privileges")
    return current_user