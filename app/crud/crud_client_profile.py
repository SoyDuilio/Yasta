# app/crud/crud_client_profile.py
from sqlalchemy.orm import Session
from typing import Optional

from app.models import User, ClientProfile, ClientType, UserClientAccess, RelationshipType # Importación unificada

class CRUDClientProfile:
    def get_by_ruc(self, db: Session, *, ruc: str) -> Optional[ClientProfile]:
        return db.query(ClientProfile).filter(ClientProfile.ruc == ruc).first()

    def create_or_get_profile(self, db: Session, *, ruc: str, business_name: str) -> ClientProfile:
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
        # Dejamos que el endpoint haga el commit
        return new_profile

    def link_user_to_profile(
        self, db: Session, *, user: User, profile: ClientProfile, relationship: RelationshipType
    ) -> UserClientAccess:
        """
        Vincula un usuario a un perfil de cliente.
        Si el vínculo ya existe, lo devuelve. Si no, lo crea.
        Esto hace que la operación sea idempotente.
        """
        # 1. Buscar si el vínculo ya existe
        existing_access = db.query(UserClientAccess).filter_by(
            user_id=user.id,
            client_profile_id=profile.id
        ).first()
        
        # 2. Si ya existe, lo devolvemos y no hacemos nada más.
        if existing_access:
            # Opcional: podrías decidir actualizar el 'relationship_type' si ha cambiado.
            # existing_access.relationship_type = relationship
            # db.add(existing_access)
            return existing_access
            
        # 3. Si no existe, creamos el nuevo vínculo.
        new_access_link = UserClientAccess(
            user_id=user.id,
            client_profile_id=profile.id,
            relationship_type=relationship
        )
        db.add(new_access_link)
        
        return new_access_link

    def has_any_access(self, db: Session, *, user_id: int) -> bool:
        return db.query(UserClientAccess).filter(UserClientAccess.user_id == user_id).first() is not None

# Instancia para exportar
crud_client_profile = CRUDClientProfile()