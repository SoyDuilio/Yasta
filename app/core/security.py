# app/core/security.py
from datetime import datetime, timedelta, timezone
from typing import Any, Union, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from cryptography.fernet import Fernet
from app.core.config import settings

# Configuración de Passlib para hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = settings.ALGORITHM
SECRET_KEY = settings.SECRET_KEY
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

def create_access_token(
    subject: Union[str, Any], expires_delta: Optional[timedelta] = None
) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception: # Captura cualquier error de passlib (ej: hash malformado)
        return False

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def decode_token(token: str) -> Optional[dict]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError: # Si el token es inválido, expirado, etc.
        return None
    

# --- LÓGICA DE ENCRIPTACIÓN PARA DATOS SENSIBLES (CLAVE SOL) ---

# La clave de encriptación se deriva de tu SECRET_KEY para consistencia.
# ¡IMPORTANTE! Si cambias tu SECRET_KEY, los datos encriptados anteriormente no podrán ser leídos.
# Se debe asegurar que settings.SECRET_KEY sea una clave de 32 bytes codificada en URL-safe base64.
# Fernet.generate_key() puede generar una. Puedes guardar esta clave en una variable de entorno separada
# llamada por ejemplo `DATA_ENCRYPTION_KEY`. Por ahora, usaremos la SECRET_KEY.
# Por seguridad, es mejor que DATA_ENCRYPTION_KEY sea diferente a SECRET_KEY.
# Vamos a asumir que la tienes en tu .env o config.py

if not settings.DATA_ENCRYPTION_KEY:
    raise ValueError("DATA_ENCRYPTION_KEY no está configurada en los settings. No se puede continuar.")

# Convertir la clave a bytes, ya que Fernet trabaja con bytes
encryption_key_bytes = settings.DATA_ENCRYPTION_KEY.encode('utf-8')
fernet_cipher = Fernet(encryption_key_bytes)

def encrypt_data(data: str) -> str:
    """Encripta un string y devuelve un string (codificado)."""
    if not data:
        return ""
    data_bytes = data.encode('utf-8')
    encrypted_bytes = fernet_cipher.encrypt(data_bytes)
    return encrypted_bytes.decode('utf-8')

def decrypt_data(encrypted_data: str) -> Optional[str]:
    """Desencripta un string y devuelve el string original o None si falla."""
    if not encrypted_data:
        return None
    try:
        encrypted_bytes = encrypted_data.encode('utf-8')
        decrypted_bytes = fernet_cipher.decrypt(encrypted_bytes)
        return decrypted_bytes.decode('utf-8')
    except Exception:
        # Esto puede pasar si el token es inválido, ha sido manipulado, o la clave cambió.
        return None