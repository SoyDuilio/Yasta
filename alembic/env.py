# alembic/env.py
from logging.config import fileConfig

from sqlalchemy import engine_from_config # Original, se puede comentar si no se usa directamente
from sqlalchemy import pool
from sqlalchemy import create_engine # Necesario para crear el engine con settings

from alembic import context

# --- INICIO DE MODIFICACIONES ESPECÍFICAS DEL PROYECTO ---
import os
import sys
from dotenv import load_dotenv # Para cargar .env si es necesario aquí (aunque FastAPI ya lo hace)

# Cargar variables de entorno del archivo .env si existe
# Esto es útil si ejecutas alembic directamente y quieres que .env se cargue.
# FastAPI/Uvicorn usualmente cargan .env al iniciar la app.
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) # Raíz del proyecto (RUCFACIL)
load_dotenv(os.path.join(BASE_DIR, '.env'))

# Añadir el directorio raíz del proyecto al PYTHONPATH
# para que Alembic pueda encontrar tus módulos de la aplicación.
# Si env.py está en RUCFACIL/alembic/env.py, esto debería ser correcto:
sys.path.insert(0, BASE_DIR) # Añade RUCFACIL/ al sys.path

# Importar la Base de SQLAlchemy y todos los modelos para que target_metadata los conozca.
from app.db.base import Base  # Tu clase Base de SQLAlchemy
from app.models import user         # Importar todos los módulos de modelos
from app.models import sunat_credential
from app.models.client_profile import ClientProfile
from app.models.user_client_access import UserClientAccess
from app.models import service_type
from app.models import service_contract
from app.models import monthly_declaration
from app.models import payroll_receipt
from app.models import fee_payment
from app.models import yape_plin_transaction
from app.models import attached_document
from app.models import communication
from app.models import credential_access_audit
from app.models import monthly_client_summary
from app.models import company_transaction
from app.models import company_tax_declaration
from app.models.landing_lead import LandingLead
# Asegúrate de que cada archivo de modelo (ej: app/models/user.py) exista
# y que cada modelo (ej: class User(Base):) esté definido en su respectivo archivo.

# Importar las settings de la aplicación para obtener DATABASE_URL
from app.core.config import settings

# Asignar los metadatos de tus modelos a target_metadata
target_metadata = Base.metadata
# --- FIN DE MODIFICACIONES ESPECÍFICAS DEL PROYECTO ---

# Esto carga la configuración de logging de alembic.ini
# si no se ha configurado ya.
config = context.config # type: ignore

# Interpretar el archivo de configuración para el logging de Python.
# Esta línea asume que tienes una sección de logging en tu alembic.ini.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata # Esto ya lo hicimos arriba con nuestra Base

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here поздно.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Usar DATABASE_URL de las settings de la aplicación
    url = settings.DATABASE_URL
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Crear un engine usando DATABASE_URL de las settings de la aplicación
    # No usar engine_from_config directamente si ya tienes tu URL en settings
    connectable = create_engine(settings.DATABASE_URL)

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()