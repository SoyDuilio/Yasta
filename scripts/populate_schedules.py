# scripts/populate_schedules.py
import os
import sys
from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

from app.models.sunat_schedule import SunatSchedule, ContributorGroup
from app.db.base import Base

# Datos transcritos del cronograma 2025
cronograma_2025 = [
    {"periodo": "Ene-25", "mes_periodo": 1, "mes_vencimiento": 2, "dias": [17, 18, 19, 19, 20, 20, 21, 21, 24, 24], "buc": 25},
    {"periodo": "Feb-25", "mes_periodo": 2, "mes_vencimiento": 3, "dias": [17, 18, 19, 19, 20, 20, 21, 21, 24, 24], "buc": 25},
    {"periodo": "Mar-25", "mes_periodo": 3, "mes_vencimiento": 4, "dias": [15, 16, 21, 21, 22, 22, 23, 23, 24, 24], "buc": 25},
    {"periodo": "Abr-25", "mes_periodo": 4, "mes_vencimiento": 5, "dias": [16, 19, 20, 20, 21, 21, 22, 22, 23, 23], "buc": 26},
    {"periodo": "May-25", "mes_periodo": 5, "mes_vencimiento": 6, "dias": [16, 17, 18, 18, 19, 19, 20, 20, 23, 23], "buc": 24},
    {"periodo": "Jun-25", "mes_periodo": 6, "mes_vencimiento": 7, "dias": [15, 16, 17, 17, 18, 18, 21, 21, 22, 22], "buc": 24},
    {"periodo": "Jul-25", "mes_periodo": 7, "mes_vencimiento": 8, "dias": [18, 19, 20, 20, 21, 21, 22, 22, 25, 25], "buc": 26},
    {"periodo": "Ago-25", "mes_periodo": 8, "mes_vencimiento": 9, "dias": [15, 16, 17, 17, 18, 18, 19, 19, 22, 22], "buc": 23},
    {"periodo": "Set-25", "mes_periodo": 9, "mes_vencimiento": 10, "dias": [16, 17, 20, 20, 21, 21, 22, 22, 23, 23], "buc": 24},
    {"periodo": "Oct-25", "mes_periodo": 10, "mes_vencimiento": 11, "dias": [17, 18, 19, 19, 20, 20, 21, 21, 24, 24], "buc": 25},
    {"periodo": "Nov-25", "mes_periodo": 11, "mes_vencimiento": 12, "dias": [17, 18, 19, 19, 22, 22, 23, 23, 24, 24], "buc": 26},
    {"periodo": "Dic-25", "mes_periodo": 12, "mes_vencimiento": 1, "dias": [16, 19, 20, 20, 21, 21, 22, 22, 23, 23], "buc": 26},
]

def populate_schedules():
    print("--- Iniciando script de población de Calendario SUNAT 2025 ---")
    load_dotenv(dotenv_path=os.path.join(project_root, '.env'))
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("Error: DATABASE_URL no encontrada. Asegúrate de que tu .env esté configurado.")
        return

    engine = create_engine(database_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Borrar datos existentes para 2025 para evitar duplicados
        year_to_process = 2025
        print(f"Borrando registros existentes para el año {year_to_process}...")
        deleted_count = db.query(SunatSchedule).filter(SunatSchedule.tax_period.like(f"{year_to_process}-%")).delete(synchronize_session=False)
        db.commit()
        print(f"{deleted_count} registros eliminados.")

        schedules_to_add = []
        print("Generando nuevos registros del cronograma...")
        for data_mes in cronograma_2025:
            tax_period = f"{year_to_process}-{data_mes['mes_periodo']:02d}"
            
            # Determinar el año del vencimiento (si es Dic-25, vence en Ene-26)
            year_vencimiento = year_to_process if data_mes['mes_vencimiento'] >= data_mes['mes_periodo'] else year_to_process + 1

            # Contribuyentes Generales
            for i, dia in enumerate(data_mes['dias']):
                schedule = SunatSchedule(
                    tax_period=tax_period,
                    last_ruc_digit=str(i),
                    due_date=date(year_vencimiento, data_mes['mes_vencimiento'], dia),
                    contributor_group=ContributorGroup.GENERAL,
                    created_by_user_id=1, # Asumimos que el usuario admin/sistema tiene id=1
                )
                schedules_to_add.append(schedule)

            # Buenos Contribuyentes (aplica a todos los dígitos)
            for i in range(10):
                schedule = SunatSchedule(
                    tax_period=tax_period,
                    last_ruc_digit=str(i),
                    due_date=date(year_vencimiento, data_mes['mes_vencimiento'], data_mes['buc']),
                    contributor_group=ContributorGroup.BUEN_CONTRIBUYENTE,
                    created_by_user_id=1,
                )
                schedules_to_add.append(schedule)
        
        print(f"Insertando {len(schedules_to_add)} nuevos registros en la base de datos...")
        db.bulk_save_objects(schedules_to_add)
        db.commit()
        print("¡Inserción completada exitosamente!")

    except Exception as e:
        print(f"Ocurrió un error: {e}")
        db.rollback()
    finally:
        db.close()
        print("Conexión a la base de datos cerrada.")

if __name__ == "__main__":
    populate_schedules()