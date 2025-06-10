# app/schemas/user_schema.py
from pydantic import BaseModel, EmailStr, Field # Field reemplaza a constr aquí
from typing import Optional, List, Annotated # Importar Annotated
from datetime import datetime, timezone # Importar timezone
from app.models.user import UserRole # Importa el Enum del modelo
from fastapi import Form as FastAPIForm # Para el método as_form

from typing import Union

# --- Type Aliases con Annotated y Field para validaciones ---
# Para RUC (cliente o personal)
RucStr = Annotated[str, Field(min_length=11, max_length=11, pattern=r"^(10|20)\d{9}$")]
# Para DNI del personal
DniStr = Annotated[str, Field(min_length=8, max_length=15)] # Ajustar max_length si es necesario
# Para números de teléfono
PhoneNumberStr = Annotated[str, Field(min_length=9, max_length=20)]
# Para contraseñas
PasswordStr = Annotated[str, Field(min_length=8)]
# Para nombres/razón social
NameStr = Annotated[str, Field(min_length=2, max_length=255)]
# Para URLs de imagen
ImageUrlStr = Annotated[str, Field(max_length=512)]


# --- Base Schemas ---
class UserBase(BaseModel):
    email: EmailStr
    phone_number: Optional[PhoneNumberStr] = None
    profile_image_url: Optional[ImageUrlStr] = None

class ClientUserBase(UserBase):
    # role: UserRole = Field(UserRole.CLIENT_FREEMIUM, description="Role must be a client type") # Literal no es necesario si hay default
    role: UserRole = UserRole.CLIENT_FREEMIUM
    client_ruc: RucStr
    business_name: NameStr
    contact_name: Optional[NameStr] = None

class StaffUserBase(UserBase):
    # role: UserRole = Field(UserRole.STAFF_COLLABORATOR, description="Role must be a staff type")
    role: UserRole = UserRole.STAFF_COLLABORATOR
    staff_dni: DniStr
    staff_full_name: NameStr
    staff_ruc_personal: Optional[RucStr] = None # RUC 10 para persona natural

# --- Creation Schemas ---
class UserCreateBase(UserBase):
    password: PasswordStr

class ClientUserCreate(ClientUserBase, UserCreateBase):
    terms_accepted: bool = Field(..., description="Client must accept terms and conditions")

class StaffUserCreate(StaffUserBase, UserCreateBase):
    pass

class ClientUserCreate(ClientUserBase, UserCreateBase):
    terms_accepted: bool = Field(..., description="Client must accept terms and conditions")

    @classmethod
    def as_form(
        cls,
        email: EmailStr = FastAPIForm(...),
        password: str = FastAPIForm(..., min_length=8), # Añadir validación aquí también
        # role no se envía desde el form, se toma de ClientUserBase
        client_ruc: RucStr = FastAPIForm(...), # Usa tu type alias para validación
        business_name: Annotated[str, Field(min_length=2, max_length=255)] = FastAPIForm(...),
        contact_name: Optional[Annotated[str, Field(max_length=255)]] = FastAPIForm(None),
        phone_number: Optional[Annotated[str, Field(min_length=9, max_length=20)]] = FastAPIForm(None),
        profile_image_url: Optional[Annotated[str, Field(max_length=512)]] = FastAPIForm(None), # Probablemente no desde este form
        terms_accepted: bool = FastAPIForm(...) # FastAPI convierte "true"/"on" a bool si el tipo es bool
    ):
        # El rol se toma del default en ClientUserBase (CLIENT_FREEMIUM)
        return cls(
            email=email, password=password,
            client_ruc=client_ruc, business_name=business_name,
            contact_name=contact_name, phone_number=phone_number,
            profile_image_url=profile_image_url, # Se pasará como None si no se envía
            terms_accepted=terms_accepted
            # role se setea por ClientUserBase
        )


# --- Update Schemas ---
class UserUpdateBase(BaseModel):
    email: Optional[EmailStr] = None
    phone_number: Optional[PhoneNumberStr] = None
    password: Optional[PasswordStr] = None
    profile_image_url: Optional[ImageUrlStr] = None
    is_active: Optional[bool] = None

class ClientUserUpdate(UserUpdateBase):
    client_ruc: Optional[RucStr] = None
    business_name: Optional[NameStr] = None
    contact_name: Optional[NameStr] = None
    terms_accepted: Optional[bool] = None
    role: Optional[UserRole] = None # Admin might change client type (freemium/paid)

class StaffUserUpdate(UserUpdateBase):
    staff_dni: Optional[DniStr] = None
    staff_full_name: Optional[NameStr] = None
    staff_ruc_personal: Optional[RucStr] = None
    role: Optional[UserRole] = None # Admin might change staff role

# --- Response Schemas (Output) ---
class UserInDBBase(UserBase):
    id: int
    role: UserRole
    is_active: bool
    created_at: datetime # Asume que el modelo tiene timezone-aware UTC datetime
    updated_at: datetime # Asume que el modelo tiene timezone-aware UTC datetime
    last_platform_login_at: Optional[datetime] = None

    class Config:
        orm_mode = True
        # Si necesitas que los datetimes se serialicen con offset UTC (ej: +00:00)
        # json_encoders = {
        #     datetime: lambda dt: dt.isoformat()
        # }

class ClientUserResponse(ClientUserBase, UserInDBBase):
    terms_accepted_at: Optional[datetime] = None

class StaffUserResponse(StaffUserBase, UserInDBBase):
    pass

class UserGeneralResponse(UserInDBBase):
    client_ruc: Optional[RucStr] = None
    business_name: Optional[NameStr] = None
    contact_name: Optional[NameStr] = None
    terms_accepted_at: Optional[datetime] = None
    staff_dni: Optional[DniStr] = None
    staff_full_name: Optional[NameStr] = None
    staff_ruc_personal: Optional[RucStr] = None

    class Config:
        # orm_mode = True # Para Pydantic V1
        from_attributes = True # Para Pydantic V2

class UserLoginSchema(BaseModel):
    identifier: str
    password: str

# Para el token JWT
class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserGeneralResponse # Devolver información del usuario junto con el token

class TokenPayload(BaseModel):
    sub: str # Puede ser email, o un ID de usuario numérico como string
    # exp: Optional[datetime] = None # Pydantic puede manejar esto si lo necesitas


# Definir UserUpdate como una unión de los tipos específicos de actualización
UserUpdate = Union[ClientUserUpdate, StaffUserUpdate, UserUpdateBase] # UserUpdateBase si quieres permitir actualizar solo campos comunes