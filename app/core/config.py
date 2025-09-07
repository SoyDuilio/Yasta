# app/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache
from typing import List, Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "YASTA Cloud API"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development" # Valor por defecto

    # --- Variables de Entorno (Pydantic las leerá del .env) ---
    DATABASE_URL: str
    SECRET_KEY: str
    DATA_ENCRYPTION_KEY: str
    
    OPENAI_API_KEY: str

    # <-- LA NUEVA LÍNEA, CON SU TIPO CORRECTO -->
    APIS_NET_PE_TOKEN: str 

    # --- Variables de Google OAuth ---
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_REDIRECT_URI: Optional[str] = None 

    # --- Configuración Fija ---
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:1111", "http://127.0.0.1:1111"] # Orígenes permitidos
    ACCESS_TOKEN_COOKIE_NAME: str = "yasta_access_token"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 días

    # Configuración para que Pydantic lea desde el archivo .env
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- NUEVA VARIABLE PARA EL PANEL DE LEADS ---
    LEADS_ACCESS_KEY: str = "aldo2025"

@lru_cache() # Cachea el resultado para no leer .env múltiples veces
def get_settings() -> Settings:
    return Settings()

settings = get_settings()