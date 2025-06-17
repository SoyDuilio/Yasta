# app/apis/v1/endpoints/onboarding.py
from fastapi import APIRouter, Request, Depends, Form, status, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional

# Importamos las dependencias necesarias de deps.py
from app.apis.deps import get_db, get_current_active_user
from app.core.templating import templates
from app.core.security import encrypt_data
from app.models import User, UserRole, RelationshipType, SOLValidationStatus
#from app.models.user import User, UserRole
#from app.models.user_client_access import RelationshipType

# --- ¡IMPORTANTE! Importamos las nuevas instancias CRUD ---
# Importa todo desde el paquete 'crud'
from app.crud import crud_user, crud_client_profile, crud_sunat_credential

# El router de API para el proceso de onboarding
router = APIRouter(prefix="/onboarding", tags=["Onboarding"])

@router.post("/finalize", name="onboarding_finalize")
async def finalize_onboarding(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    
    # Estos nombres deben coincidir con el atributo 'name' de tus inputs en el HTML
    client_ruc: str = Form(..., alias="client_ruc"),
    business_name: str = Form(..., alias="business_name"),
    sol_username: str = Form(..., alias="sol_username"),
    sol_password: str = Form(..., alias="sol_password"),
    contact_phone: Optional[str] = Form(None, alias="contact_phone")
):
    # <<< REEMPLAZA EL CONTENIDO DE LA FUNCIÓN CON ESTO >>>

    # 1. Crear o encontrar el perfil de cliente
    profile = crud_client_profile.create_or_get_profile(
        db=db, 
        ruc=client_ruc,
        business_name=business_name
    )
    
    # 2. Vincular usuario a perfil
    relationship = RelationshipType.TITULAR if client_ruc.startswith("10") else RelationshipType.REPRESENTANTE_LEGAL
    crud_client_profile.link_user_to_profile(db=db, user=current_user, profile=profile, relationship=relationship)

    # 3. Encriptar y guardar las credenciales SOL
    encrypted_pass = encrypt_data(sol_password)
    
    if not crud_sunat_credential.has_credentials(db=db, client_profile_id=profile.id):
        crud_sunat_credential.create_credentials(
            db=db,
            client_profile_id=profile.id,
            sol_user=sol_username,       # Usando la variable del formulario
            sol_pass=encrypted_pass      # Usando la variable del formulario
        )

    # 4. Actualizar el usuario con el estado correcto
    current_user.role = UserRole.CLIENT_FREEMIUM
    current_user.sol_validation_status = SOLValidationStatus.PENDING # CORREGIDO
    if contact_phone:
        current_user.phone_number = contact_phone
    
    db.add(current_user)
    db.commit()

    return RedirectResponse(url=request.url_for("client_dashboard_page"), status_code=status.HTTP_303_SEE_OTHER)