# app/crud/crud_sunat_credential.py
from sqlalchemy.orm import Session

from app.models import SunatCredential # Importación unificada

class CRUDSunatCredential:
    def has_credentials(self, db: Session, *, client_profile_id: int) -> bool:
        return db.query(SunatCredential).filter(SunatCredential.owner_client_profile_id == client_profile_id).first() is not None
        
    def create_credentials(self, db: Session, *, client_profile_id: int, sol_user: str, sol_pass: str) -> SunatCredential:
        encrypted_pass = sol_pass # Placeholder para la encriptación
        db_obj = SunatCredential(
            owner_client_profile_id=client_profile_id,
            sol_username=sol_user,
            encrypted_sol_password=encrypted_pass
        )
        db.add(db_obj)
        # Dejamos que el endpoint haga el commit
        return db_obj

# Instancia para exportar
crud_sunat_credential = CRUDSunatCredential()