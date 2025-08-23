# app/core/security.py

from datetime import datetime, timedelta
from typing import Any, Union
from jose import jwt
from passlib.context import CryptContext
from cryptography.fernet import Fernet

from app.core.config import settings

# --- SECCIÓN 1: HASHING DE CONTRASEÑAS ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# --- SECCIÓN 2: TOKENS DE AUTENTICACIÓN (JWT) ---
ALGORITHM = "HS256"

def create_access_token(
    subject: Union[str, Any], expires_delta: timedelta = None
) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# --- SECCIÓN 3: ENCRIPTACIÓN DE DATOS SIMÉTRICA (PARA CLAVE SOL, ETC.) ---

# Creamos una instancia de Fernet usando la clave de nuestra configuración.
# Es importante que la clave esté en bytes, por eso usamos .encode()
try:
    fernet = Fernet(settings.DATA_ENCRYPTION_KEY.encode())
except Exception as e:
    # Si la clave no es válida, la aplicación no debe arrancar.
    raise ValueError(f"La DATA_ENCRYPTION_KEY no es válida: {e}")

def encrypt_data(data: str) -> str:
    """
    Encripta un string y devuelve el resultado como un string seguro para almacenar.
    """
    if not isinstance(data, str):
        raise TypeError("Solo se pueden encriptar datos de tipo string.")
        
    encrypted_data = fernet.encrypt(data.encode())
    return encrypted_data.decode()

def decrypt_data(encrypted_data: str) -> str:
    """
    Desencripta un string que fue previamente encriptado con encrypt_data.
    """
    if not isinstance(encrypted_data, str):
        raise TypeError("Solo se pueden desencriptar datos de tipo string.")

    try:
        decrypted_data = fernet.decrypt(encrypted_data.encode())
        return decrypted_data.decode()
    except Exception:
        # Si el token es inválido o ha sido manipulado, la desencriptación fallará.
        # En este caso, podríamos devolver un string vacío o lanzar una excepción específica.
        return "Error: No se pudo desencriptar el dato."