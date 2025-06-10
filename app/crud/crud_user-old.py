# app/crud/crud_user.py
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timezone

from app.core.security import get_password_hash, verify_password
from app.core.config import settings
#from app.models.user import User, UserRole
from app.models.client_profile import ClientProfile, ClientType
#from app.models.user_client_access import UserClientAccess, RelationshipType
from app.models.sunat_credential import SunatCredential

# --- CLASE CRUD PARA MANEJAR USUARIOS (LOGINS, ROLES) ---
class CRUDUser:
    def get(self, db: Session, *, id: int) -> Optional[User]:
        return db.query(User).filter(User.id == id).first()

    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def create_user_authenticated(self, db: Session, *, email: str, password: str) -> User:
        hashed_password = get_password_hash(password)
        db_obj = User(
            email=email, 
            hashed_password=hashed_password, 
            role=UserRole.AUTHENTICATED,
            is_active=True
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def create_user_from_google(self, db: Session, *, email: str, full_name: str, picture_url: str) -> User:
        """Crea un usuario básico desde Google con el rol 'AUTHENTICATED'."""
        pseudo_random_string = f"{email}-{settings.SECRET_KEY}-{datetime.now(timezone.utc).isoformat()}"
        hashed_password = get_password_hash(pseudo_random_string)
        db_obj = User(
            email=email,
            hashed_password=hashed_password,
            contact_name=full_name,
            profile_image_url=picture_url,
            role=UserRole.AUTHENTICATED,
            is_active=True
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj
        
    def authenticate_user(self, db: Session, *, identifier: str, password: str) -> Optional[User]:
        user = self.get_by_email(db, email=identifier)
        if not user or not verify_password(password, user.hashed_password):
            return None
        return user

    def update_user_role(self, db: Session, *, user: User, new_role: UserRole) -> User:
        user.role = new_role
        user.updated_at = datetime.now(timezone.utc)
        db.add(user)
        #db.commit()
        #db.refresh(user)
        return user

# --- CLASE CRUD PARA MANEJAR PERFILES DE CLIENTE (RUCs) Y SUS ACCESOS ---
class CRUDClientProfile:
    def get_by_ruc(self, db: Session, *, ruc: str) -> Optional[ClientProfile]:
        return db.query(ClientProfile).filter(ClientProfile.ruc == ruc).first()

    def create_or_get_profile(self, db: Session, *, ruc: str, business_name: str) -> ClientProfile:
        """Busca un perfil por RUC. Si no existe, lo crea."""
        profile = self.get_by_ruc(db, ruc=ruc)
        if profile:
            return profile
        
        client_type = ClientType.JURIDICA if ruc.startswith("20") else ClientType.NATURAL
        new_profile = ClientProfile(
            ruc=ruc,
            business_name=business_name,
            client_type=client_type
        )
        db.add(new_profile)
        db.commit()
        db.refresh(new_profile)
        return new_profile

    def link_user_to_profile(
        self, db: Session, *, user: User, profile: ClientProfile, relationship: RelationshipType
    ) -> UserClientAccess:
        """Crea el enlace entre un usuario y un perfil de cliente."""
        access_link = UserClientAccess(
            user_id=user.id,
            client_profile_id=profile.id,
            relationship_type=relationship
        )
        db.add(access_link)
        db.commit()
        db.refresh(access_link)
        return access_link

    def has_any_access(self, db: Session, *, user_id: int) -> bool:
        """Verifica si un usuario tiene acceso a al menos un perfil de cliente."""
        return db.query(UserClientAccess).filter(UserClientAccess.user_id == user_id).first() is not None

# --- CLASE CRUD PARA MANEJAR CREDENCIALES SUNAT ---
class CRUDSunatCredential:
    def has_credentials(self, db: Session, *, client_profile_id: int) -> bool:
        """Verifica si un ClientProfile ya tiene credenciales guardadas."""
        return db.query(SunatCredential).filter(SunatCredential.owner_client_profile_id == client_profile_id).first() is not None
        
    def create_credentials(self, db: Session, *, client_profile_id: int, sol_user: str, sol_pass: str) -> SunatCredential:
        encrypted_pass = sol_pass # Placeholder para la encriptación
        db_obj = SunatCredential(
            owner_client_profile_id=client_profile_id,
            sol_username=sol_user,
            encrypted_sol_password=encrypted_pass
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

# Creamos instancias para importarlas fácilmente en otros lugares
crud_user = CRUDUser()
crud_client_profile = CRUDClientProfile()
crud_sunat_credential = CRUDSunatCredential()