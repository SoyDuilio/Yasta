# app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Creamos el motor de SQLAlchemy usando la URL de la base de datos
# desde nuestra configuración central (settings).
# El pool_pre_ping=True es una buena práctica para verificar las conexiones
# antes de entregarlas, evitando errores con conexiones que se han cerrado.
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)

# Creamos una fábrica de sesiones (SessionLocal) que usaremos para
# crear nuevas sesiones de base de datos para cada solicitud.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Esta es la función de dependencia que los endpoints usarán.
def get_db():
    """
    Dependency function that provides a database session for a single request.
    It ensures the session is properly closed after the request is finished.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()