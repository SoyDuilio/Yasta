# app/db/seed_data.py
from faker import Faker
from app.db.database import SessionLocal, engine
from app.models import User, UserRole # Importación unificada
from app.core.security import get_password_hash # Necesitas esta función

fake = Faker('es_PE') # Para datos peruanos

def seed_users(db, num_users=10):
    for _ in range(num_users):
        user = User(
            email=fake.unique.email(),
            hashed_password=get_password_hash("password123"), # Usa una contraseña por defecto
            ruc=fake.numerify(text="20#########"), # Para clientes
            business_name=fake.company(),
            role=UserRole.CLIENT_FREEMIUM,
            is_active=True,
            terms_accepted=True
        )
        db.add(user)
    db.commit()
    print(f"Seeded {num_users} users.")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_users(db, 20)
        # Llama a otras funciones seed_... para otras tablas
    finally:
        db.close()