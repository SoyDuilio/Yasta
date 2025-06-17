import os
import sys
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# --- Configuración de Colores para la Terminal ---
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# --- Cargar Variables de Entorno ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
dotenv_path = os.path.join(project_root, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)
else:
    print(f"{bcolors.FAIL}Error: Archivo .env no encontrado en la raíz del proyecto ('{project_root}').{bcolors.ENDC}")
    sys.exit(1)

DATABASE_URL = os.getenv("DATABASE_URL")
print("===>", DATABASE_URL)
if not DATABASE_URL:
    print(f"{bcolors.FAIL}Error: La variable de entorno DATABASE_URL no está definida.{bcolors.ENDC}")
    sys.exit(1)

# --- Lista de Tablas a Verificar ---
TABLES_TO_CHECK = [
    "attached_documents", "buen_contribuyentes", "client_profiles", "communications",
    "company_tax_declarations", "company_transactions", "credential_access_audits",
    "fee_payments", "monthly_client_summaries", "monthly_declarations",
    "payroll_receipts", "service_contracts", "service_tariffs", "service_types",
    "sunat_credentials", "sunat_schedules", "user_client_accesses", "users",
    "yape_plin_transactions"
]

def check_and_fix_defaults():
    try:
        engine = create_engine(DATABASE_URL)
        with engine.connect() as connection:
            print(f"{bcolors.OKBLUE}Conectado exitosamente a la base de datos.{bcolors.ENDC}")
            print(f"{bcolors.HEADER}{bcolors.BOLD}--- FASE 1: VERIFICACIÓN DE DEFAULTS ---{bcolors.ENDC}")

            tables_to_fix = []

            for table_name in TABLES_TO_CHECK:
                print(f"\n{bcolors.OKCYAN}Verificando tabla: '{table_name}'...{bcolors.ENDC}")
                
                table_exists_query = text("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :table_name);")
                table_exists = connection.execute(table_exists_query, {'table_name': table_name}).scalar_one()

                if not table_exists:
                    print(f"  {bcolors.WARNING}↳ Advertencia: La tabla '{table_name}' no existe en la base de datos. Saltando...{bcolors.ENDC}")
                    continue

                query = text("SELECT column_name, column_default FROM information_schema.columns WHERE table_name = :table_name AND column_name IN ('created_at', 'updated_at');")
                results = connection.execute(query, {'table_name': table_name}).fetchall()
                
                if not results:
                    print(f"  {bcolors.WARNING}↳ Advertencia: Columnas 'created_at'/'updated_at' no encontradas en '{table_name}'.{bcolors.ENDC}")
                    continue

                needs_fix = False
                for row in results:
                    column_name, column_default = row
                    if column_default is None or 'now()' not in str(column_default):
                        needs_fix = True
                        print(f"  {bcolors.FAIL}↳ {column_name}: NECESITA CORRECCIÓN (Default actual: {column_default}){bcolors.ENDC}")
                    else:
                        print(f"  {bcolors.OKGREEN}↳ {column_name}: OK (Default: {column_default}){bcolors.ENDC}")
                
                if needs_fix:
                    tables_to_fix.append(table_name)
            
            if not tables_to_fix:
                print(f"\n{bcolors.OKGREEN}{bcolors.BOLD}¡Todo en orden! Todas las tablas ya tienen los defaults correctos.{bcolors.ENDC}")
                return

            print(f"\n{bcolors.HEADER}{bcolors.BOLD}--- FASE 2: EJECUCIÓN DE CORRECCIONES ---{bcolors.ENDC}")
            print(f"{bcolors.WARNING}Se han encontrado {len(tables_to_fix)} tablas que necesitan corrección.")
            
            confirm = input(f"{bcolors.BOLD}¿Deseas aplicar los cambios (ALTER TABLE ... SET DEFAULT now()) a estas tablas? (s/n): {bcolors.ENDC}").lower()

            if confirm == 's':
                print("\nIniciando correcciones...")
                # --- SECCIÓN CORREGIDA ---
                # Usamos la transacción implícita del 'with' y la manejamos con try/except
                try:
                    for table_name in tables_to_fix:
                        print(f"  {bcolors.OKCYAN}Corrigiendo tabla '{table_name}'...{bcolors.ENDC}")
                        # Usamos f-strings de forma segura porque table_name viene de nuestra lista interna, no de input de usuario
                        connection.execute(text(f'ALTER TABLE "{table_name}" ALTER COLUMN created_at SET DEFAULT now();'))
                        connection.execute(text(f'ALTER TABLE "{table_name}" ALTER COLUMN updated_at SET DEFAULT now();'))
                    
                    connection.commit() # Si todo sale bien, guardamos los cambios.
                    print(f"\n{bcolors.OKGREEN}{bcolors.BOLD}¡Éxito! Todos los cambios han sido aplicados y guardados en la base de datos.{bcolors.ENDC}")
                except Exception as e:
                    print(f"{bcolors.FAIL}\nError durante la aplicación de cambios. Realizando rollback...{bcolors.ENDC}")
                    print(f"{bcolors.FAIL}Detalle del error: {e}{bcolors.ENDC}")
                    connection.rollback() # Si algo falla, revertimos todo.
                # --- FIN DE LA SECCIÓN CORREGIDA ---
            else:
                print("\nOperación cancelada por el usuario. No se realizaron cambios en la base de datos.")
                # Es buena práctica hacer rollback si se cancela también
                connection.rollback()

    except Exception as e:
        print(f"\n{bcolors.FAIL}Error fatal al intentar conectar o ejecutar el script: {e}{bcolors.ENDC}")
        sys.exit(1)

if __name__ == "__main__":
    check_and_fix_defaults()