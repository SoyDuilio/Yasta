# app/crud/crud_buen_contribuyente.py
from sqlalchemy.orm import Session
from app.models.buen_contribuyente import BuenContribuyente

class CRUDBuenContribuyente:
    def is_buc(self, db: Session, *, ruc: str) -> bool:
        """
        Verifica de forma eficiente si un RUC pertenece a un Buen Contribuyente.
        """
        # .first() es más eficiente que .all() si solo necesitamos saber si existe.
        return db.query(BuenContribuyente).filter(BuenContribuyente.ruc == ruc).first() is not None

crud_buen_contribuyente = CRUDBuenContribuyente()