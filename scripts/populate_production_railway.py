# scripts/populate_production.py
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from getpass import getpass # Para ocultar la URL al pegarla

# --- Configuración para que el script encuentre los módulos de la app ---
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Ahora podemos importar desde 'app'
from app.models.buen_contribuyente import BuenContribuyente
from app.db.base import Base # Necesario para que SQLAlchemy conozca la tabla

def populate_production_data():
    """
    Lee un archivo de texto con la lista de Buenos Contribuyentes y
    los inserta en la base de datos de PRODUCCIÓN especificada por el usuario.
    """
    print("\n" + "="*60)
    print("      SCRIPT DE CARGA DE DATOS A LA BASE DE DATOS DE PRODUCCIÓN")
    print("="*60)
    print("\n*** ADVERTENCIA: Este script modificará la base de datos en VIVO en Railway. ***\n")
    
    # Pedir la URL de conexión de forma segura
    print("Por favor, pega la 'Postgres Connection URL' de tu base de datos en Railway.")
    print("(La entrada estará oculta por seguridad)")
    database_url = getpass("URL de Conexión: ")

    if not database_url or not database_url.startswith("postgresql://"):
        print("\nError: URL de base de datos no válida. Abortando.")
        return

    print("\nConectando a la base de datos de PRODUCCIÓN...")
    
    try:
        engine = create_engine(database_url)
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        db = SessionLocal()
        print("¡Conexión exitosa!")
    except Exception as e:
        print(f"\nError al conectar a la base de datos: {e}")
        return

    # Ruta al archivo de datos
    data_file_path = os.path.join(os.path.dirname(__file__), 'buc_list.txt')
    if not os.path.exists(data_file_path):
        print(f"Error: El archivo de datos 'buc_list.txt' no se encontró en la carpeta 'scripts'.")
        db.close()
        return

    print(f"Leyendo datos de {data_file_path}...")
    
    try:
        with open(data_file_path, 'r', encoding='latin-1') as f:
            next(f, None)  # Omitir el encabezado
            
            lines_processed = 0
            bucs_to_add = []
            
            existing_rucs = {r[0] for r in db.query(BuenContribuyente.ruc).all()}
            print(f"Se encontraron {len(existing_rucs)} RUCs existentes en la base de datos de producción.")
            
            total_lines = sum(1 for line in f)
            f.seek(0) # Volver al inicio del archivo
            next(f, None)
            
            print(f"Se procesarán aproximadamente {total_lines} líneas.")

            for i, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue

                parts = line.split('|')
                if len(parts) < 4:
                    continue

                ruc, razon_social, fecha_str, resolucion = parts[0], parts[1], parts[2], parts[3]
                razon_social = razon_social.strip().strip('"')

                if ruc in existing_rucs:
                    continue

                try:
                    fecha_incorporacion = datetime.strptime(fecha_str.strip(), '%d/%m/%Y').date()
                except ValueError:
                    continue

                new_buc = BuenContribuyente(
                    ruc=ruc.strip(),
                    razon_social=razon_social.strip(),
                    fecha_incorporacion=fecha_incorporacion,
                    numero_resolucion=resolucion.strip().strip('|'),
                    observaciones="Cargado desde script masivo a producción."
                )
                bucs_to_add.append(new_buc)
                existing_rucs.add(ruc)

                if len(bucs_to_add) >= 1000:
                    db.bulk_save_objects(bucs_to_add)
                    db.commit()
                    print(f"  > Lote de {len(bucs_to_add)} registros insertado. ({i+1}/{total_lines})")
                    bucs_to_add = []

            if bucs_to_add:
                db.bulk_save_objects(bucs_to_add)
                db.commit()
                print(f"  > Lote final de {len(bucs_to_add)} registros insertado.")
                
            lines_processed = len(existing_rucs) - len({r[0] for r in db.query(BuenContribuyente.ruc).all()})

            print("\n--- ¡PROCESO COMPLETADO! ---")
            
    except Exception as e:
        print(f"\nOcurrió un error durante la inserción: {e}")
        db.rollback()
    finally:
        db.close()
        print("Conexión a la base de datos de producción cerrada.")

if __name__ == "__main__":
    populate_production_data()