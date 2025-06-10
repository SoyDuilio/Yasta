# app/db/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings # Importa tus settings

# Para SQLAlchemy síncrono
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True # Verifica conexiones antes de usarlas
)

# Para SQLAlchemy asíncrono (si decidieras usarlo más adelante con asyncpg)
# from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
# async_engine = create_async_engine(settings.DATABASE_URL, echo=True) # echo=True para debug
# AsyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=async_engine, class_=AsyncSession)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Función para obtener una sesión de DB (dependencia para FastAPI)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()