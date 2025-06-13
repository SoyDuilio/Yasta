# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import List, Optional
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "RUCFACIL API"
    API_V1_STR: str = "/api/v1"

    DATA_ENCRYPTION_KEY: str = os.getenv("DATA_ENCRYPTION_KEY", "")
    
    # Database settings
    # Ejemplo para PostgreSQL asíncrono (si usas asyncpg)
        # Ejemplo para PostgreSQL síncrono (si usas psycopg2)
    BACKEND_CORS_ORIGINS: List[str] = [] # Default a lista vacía si no se define en .env
    DATABASE_URL: str = os.getenv("DATA_BASE_URL", "")
    

    ACCESS_TOKEN_COOKIE_NAME: str = "rucfacil_access_token" # Nombre de la cookie para el token

    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: Optional[str] = None 


    # JWT Settings
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 días

    # Configuración para leer desde .env
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache() # Cachea el resultado para no leer .env múltiples veces
def get_settings() -> Settings:
    return Settings()

settings = get_settings()