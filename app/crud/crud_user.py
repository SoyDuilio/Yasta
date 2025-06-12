# app/crud/crud_user.py
# Al principio de app/crud/crud_user.py
from sqlalchemy import text
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timezone

from app.core.security import get_password_hash, verify_password
from app.models import User, UserRole # Importación unificada

class CRUDUser:
    def get(self, db: Session, *, id: int) -> Optional[User]:
        return db.query(User).filter(User.id == id).first()

    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def create_user_authenticated(self, db: Session, *, email: str, password: str) -> User:
        hashed_password = get_password_hash(password)
        db_obj = User(
            email=email,
            hashed_password=hashed_password,
            role=UserRole.AUTHENTICATED,
            is_active=True
        )
        db.add(db_obj)
        # Dejamos que el endpoint haga el commit
        return db_obj

    def create_user_from_google(self, db: Session, *, email: str, full_name: str, picture_url: str) -> User:
        pseudo_random_string = f"{email}-{full_name}-{datetime.now(timezone.utc).isoformat()}" # Evitar usar SECRET_KEY aquí por seguridad
        hashed_password = get_password_hash(pseudo_random_string)
        db_obj = User(
            email=email,
            hashed_password=hashed_password,
            contact_name=full_name,
            profile_image_url=picture_url,
            role=UserRole.AUTHENTICATED,
            is_active=True
        )
        db.add(db_obj)
        # Dejamos que el endpoint haga el commit
        return db_obj
        
    def authenticate_user(self, db: Session, *, identifier: str, password: str) -> Optional[User]:
        user = self.get_by_email(db, email=identifier)
        if not user or not verify_password(password, user.hashed_password):
            return None
        return user

    """def update_user_role(self, db: Session, *, user: User, new_role: UserRole) -> User:
        user.role = new_role
        db.add(user)
        # Dejamos que el endpoint haga el commit
        return user"""
    
    # En app/crud/crud_user.py

    def update_user_role(self, db: Session, *, user: User, new_role: UserRole) -> User:
        """
        Actualiza el rol de un usuario usando SQL crudo para evitar problemas
        de casteo de tipo con el ENUM de PostgreSQL.
        """
        try:
            # 1. Obtenemos el valor del Enum como un string (ej: "client_freemium")
            role_value_str = new_role.value

            # 2. Creamos la consulta SQL cruda. 
            #    Usamos :role_value y :user_id para prevenir inyección SQL.
            #    Hacemos un CAST explícito a 'userrole' en la propia consulta.
            sql_query = text(
                """
                UPDATE users
                SET role = CAST(:role_value AS userrole)
                WHERE id = :user_id
                """
            )
            
            # 3. Ejecutamos la consulta con los parámetros
            db.execute(sql_query, {"role_value": role_value_str, "user_id": user.id})
            
            # 4. No necesitamos hacer commit aquí si el endpoint lo hace.
            #    Pero sí necesitamos actualizar nuestro objeto de Python.
            user.role = new_role
            
        except Exception as e:
            # Si algo sale mal, hacemos rollback para no dejar la sesión en un estado inconsistente.
            db.rollback()
            raise e # Relanzamos la excepción para que el endpoint la maneje.
            
        return user

# Instancia para exportar
crud_user = CRUDUser()