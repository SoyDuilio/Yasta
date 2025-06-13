# create_tables.py
from sqlalchemy import create_engine
from app.db.base import Base
import app.models
import os

DATABASE_URL = "postgresql://postgres:isfYzwpgcwPelenerBmZvJULfexfqRRW@shuttle.proxy.rlwy.net:37514/railway"
print("Conectando a:", DATABASE_URL)

engine = create_engine(DATABASE_URL)

def create_all():
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas exitosamente.")

if __name__ == "__main__":
    create_all()
