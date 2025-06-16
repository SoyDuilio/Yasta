# app/models/buen_contribuyente.py
from sqlalchemy import Column, String, Date, Text
from sqlalchemy.orm import declarative_base

# Usamos una Base separada para este modelo de datos de referencia,
# o podemos integrarlo a la Base principal. Para mantener la modularidad,
# si este dato es muy estático, una base separada puede ser limpia.
# Sin embargo, para simplicidad con Alembic, lo integramos con la Base existente.
from app.db.base import Base

class BuenContribuyente(Base):
    __tablename__ = "buen_contribuyentes"

    # Sobreescribimos el 'id' de la clase Base para que el RUC sea la PK.
    id = None 
    ruc = Column(String(11), primary_key=True, index=True)
    
    razon_social = Column(String(255), nullable=False)
    fecha_incorporacion = Column(Date, nullable=False)
    numero_resolucion = Column(String(100), nullable=True)
    observaciones = Column(Text, nullable=True)

    def __repr__(self):
        return f"<BuenContribuyente(ruc='{self.ruc}', razon_social='{self.razon_social}')>"