# app/crud/crud_landing_lead.py
from sqlalchemy.orm import Session
from app.models.landing_lead import LandingLead
from app.schemas.landing_lead import LandingLeadCreate # Crearemos este schema
from app.core.security import encrypt_data

class CRUDLandingLead:
    def create(self, db: Session, *, obj_in: LandingLeadCreate) -> LandingLead:
        encrypted_password = encrypt_data(obj_in.sol_pass)
        db_obj = LandingLead(
            ruc=obj_in.ruc,
            sol_user=obj_in.sol_user,
            encrypted_sol_pass=encrypted_password,
            whatsapp_number=obj_in.whatsapp_number,
            contact_name=obj_in.contact_name,
            source_landing=obj_in.source_landing
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

crud_landing_lead = CRUDLandingLead()