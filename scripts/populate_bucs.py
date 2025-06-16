# scripts/populate_bucs.py
import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# --- Configuración para que el script encuentre los módulos de la app ---
# Añade el directorio raíz del proyecto al path de Python
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

# Ahora podemos importar desde 'app'
from app.models.buen_contribuyente import BuenContribuyente
from app.db.base import Base # Necesario para que SQLAlchemy conozca la tabla

def populate_data():
    """
    Lee un archivo de texto con la lista de Buenos Contribuyentes y
    los inserta en la base deatos.
    """
    print("--- Iniciando script de población de Buenos Contribuyentes ---")
    
    # Cargar variables de entorno desde el archivo .env
    env_path = os.path.join(project_root, '.env')
    if not os.path.exists(env_path):
        print(f"Error: Archivo .env no encontrado en {project_root}")
        return
    load_dotenv(dotenv_path=env_path)

    # Obtener la URL de la base de datos de las variables de entorno
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("Error: La variable de entorno DATABASE_URL no está configurada.")
        return
        
    print(f"Conectando a la base de datos...")
    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    # Ruta al archivo de datos
    data_file_path = os.path.join(os.path.dirname(__file__), 'buc_list.txt')
    if not os.path.exists(data_file_path):
        print(f"Error: El archivo de datos 'buc_list.txt' no se encontró en la carpeta 'scripts'.")
        db.close()
        return

    print(f"Leyendo datos de {data_file_path}...")
    
    try:
        # --- LA LÍNEA MODIFICADA ESTÁ AQUÍ ---
        # Cambiamos encoding='utf-8' por encoding='latin-1' o 'cp1252'
        # 'latin-1' es un buen candidato que rara vez falla.
        with open(data_file_path, 'r', encoding='latin-1') as f:
            lines_processed = 0
            bucs_to_add = []
            
            # Obtener todos los RUCs existentes para evitar duplicados
            existing_rucs = {r[0] for r in db.query(BuenContribuyente.ruc).all()}
            print(f"Se encontraron {len(existing_rucs)} RUCs existentes en la base de datos.")

            for line in f:
                line = line.strip()
                if not line:
                    continue

                parts = line.split('|')
                if len(parts) < 4:
                    print(f"Advertencia: Línea malformada, se omite: {line}")
                    continue

                ruc, razon_social, fecha_str, resolucion = parts[0], parts[1], parts[2], parts[3]

                # Omitir si el RUC ya existe
                if ruc in existing_rucs:
                    continue

                try:
                    # Formato de fecha esperado: 'DD/MM/YYYY'
                    fecha_incorporacion = datetime.strptime(fecha_str, '%d/%m/%Y').date()
                except ValueError:
                    print(f"Advertencia: Formato de fecha inválido para RUC {ruc}, se omite: {fecha_str}")
                    continue

                new_buc = BuenContribuyente(
                    ruc=ruc,
                    razon_social=razon_social.strip(),
                    fecha_incorporacion=fecha_incorporacion,
                    numero_resolucion=resolucion.strip(),
                    observaciones="Cargado desde script masivo."
                )
                bucs_to_add.append(new_buc)
                existing_rucs.add(ruc) # Añadir al set para evitar duplicados en el mismo lote
                lines_processed += 1

                # Para bases de datos grandes, hacer commit en lotes
                if len(bucs_to_add) >= 1000:
                    db.bulk_save_objects(bucs_to_add)
                    db.commit()
                    print(f"Lote de {len(bucs_to_add)} registros insertado.")
                    bucs_to_add = []

            # Insertar el último lote si queda algo
            if bucs_to_add:
                db.bulk_save_objects(bucs_to_add)
                db.commit()
                print(f"Lote final de {len(bucs_to_add)} registros insertado.")

            print(f"\n--- Proceso completado ---")
            print(f"Líneas procesadas del archivo: {lines_processed}")
    except Exception as e:
        print(f"Ocurrió un error: {e}")
        db.rollback()
    finally:
        db.close()
        print("Conexión a la base de datos cerrada.")

if __name__ == "__main__":
    populate_data()