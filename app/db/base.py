# app/db/base.py
from sqlalchemy import Column, Integer, DateTime, func
from sqlalchemy.ext.declarative import as_declarative, declared_attr
from datetime import datetime

# Esta es la nueva clase Base declarativa.
# SQLAlchemy usará esta ÚNICA Base para descubrir todos nuestros modelos.
@as_declarative()
class Base:
    """
    Base class for all SQLAlchemy models in the application.
    It provides a default __tablename__ generation and an 'id' primary key column.
    """
    id = Column(Integer, primary_key=True, index=True)
    __name__: str

    # Genera __tablename__ automáticamente a partir del nombre de la clase
    # Ejemplo: ServiceContract -> service_contracts
    @declared_attr
    def __tablename__(cls) -> str:
        # Importación local para evitar bucles
        import re
        # Convierte CamelCase a snake_case y lo pluraliza añadiendo 's'
        name_snake_case = re.sub(r'(?<!^)(?=[A-Z])', '_', cls.__name__).lower()
        # Maneja casos simples de pluralización (ej. 'y' -> 'ies'), puede mejorarse si es necesario
        if name_snake_case.endswith('y'):
            return name_snake_case[:-1] + 'ies'
        elif name_snake_case.endswith('s'):
            return name_snake_case + 'es'
        else:
            return name_snake_case + 's'

    # --- CAMPOS COMUNES PARA TODAS LAS TABLAS ---
    # Estos campos se añadirán a todas las tablas que hereden de Base.
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)