# app/apis/v1/endpoints/onboarding.py
from fastapi import APIRouter, Request, Depends, Form, status, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from typing import Optional

# Importamos las dependencias necesarias de deps.py
from app.apis.deps import get_db, get_current_active_user
from app.core.templating import templates
from app.models import User, UserRole, RelationshipType
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
    # Usamos get_current_active_user para asegurarnos de que el usuario está logueado y activo
    current_user: User = Depends(get_current_active_user),
    
    # --- Datos recibidos del formulario de onboarding.html ---
    client_ruc: str = Form(..., pattern=r"^(10|20)\d{9}$", description="RUC de 11 dígitos del cliente."),
    business_name: str = Form(..., min_length=3, description="Razón Social o nombre del contribuyente."),
    sol_username: str = Form(..., min_length=3, description="Usuario SOL de SUNAT."),
    sol_password: str = Form(..., min_length=3, description="Clave SOL de SUNAT."),
    
    # Campos opcionales para la persona de contacto
    contact_dni: Optional[str] = Form(None),
    contact_name: Optional[str] = Form(None),
    contact_phone: Optional[str] = Form(None),
    contact_role: Optional[str] = Form(None) # Cargo del contacto en la empresa
):
    """
    Procesa los datos del formulario de onboarding, crea las entidades necesarias
    en la base de datos y actualiza el estado del usuario.
    """
    # --- PASO 1: Buscar o crear el Perfil de Cliente (ClientProfile) ---
    # Esto asegura que no tengamos RUCs duplicados.
    profile = crud_client_profile.create_or_get_profile(
        db=db,
        ruc=client_ruc,
        business_name=business_name
    )

    # --- PASO 2: Determinar la relación y enlazar al Usuario con el Perfil ---
    # Lógica simple por ahora. Si se proporciona un `contact_role`, lo usamos, si no, lo inferimos.
    if contact_role:
        # Aquí podrías tener una lógica para mapear el string a tu Enum
        # Por ahora, asumimos que es un asistente si se especifica un rol.
        relationship = RelationshipType.ASISTENTE
    else:
        # Si no se especifica rol, lo inferimos del RUC
        relationship = RelationshipType.TITULAR if client_ruc.startswith("10") else RelationshipType.REPRESENTANTE_LEGAL
        
    crud_client_profile.link_user_to_profile(
        db=db,
        user=current_user,
        profile=profile,
        relationship=relationship
    )

    # --- PASO 3: Guardar las credenciales SOL para ese Perfil de Cliente ---
    # Verificamos si ya existen credenciales para este perfil para no duplicarlas.
    if not crud_sunat_credential.has_credentials(db=db, client_profile_id=profile.id):
        crud_sunat_credential.create_credentials(
            db=db,
            client_profile_id=profile.id,
            sol_user=sol_username,
            sol_pass=sol_password # Recordar implementar encriptación aquí
        )

    # --- PASO 4: Actualizar el Usuario ---
    # Actualizamos el rol del usuario para que salga del estado "authenticated".
    crud_user.update_user_role(
        db=db,
        user=current_user,
        new_role=UserRole.CLIENT_FREEMIUM # O el rol que corresponda
    )
    
    # (Opcional) Actualizamos el DNI y teléfono del usuario si los proporcionó
    if contact_dni:
        current_user.staff_dni = contact_dni # O un nuevo campo 'contact_dni'
    if contact_phone:
        current_user.phone_number = contact_phone
    
    db.add(current_user)
    db.commit()


    # --- PASO 5: Redirigir al dashboard del cliente ---
    # Como el usuario ya es un cliente completo, esta redirección funcionará.
    return RedirectResponse(url=request.url_for("client_dashboard_page"), status_code=status.HTTP_303_SEE_OTHER)