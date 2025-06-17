# app/apis/v1/endpoints/utils.py
import requests
import logging
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.apis.deps import get_db
from app.core.config import settings
from app.crud import crud_sunat_schedule

# --- Definición COMPLETA y CORRECTA de la Clase ---
# Incluye todos los métodos que tenías originalmente.
class ApisNetPe:
    def __init__(self, token: Optional[str] = None):
        self._api_token = token
        self._api_url = "https://api.apis.net.pe"

    def _get(self, path: str, params: dict) -> Optional[dict]:
        if not self._api_token:
            logging.error("API Token for apis.net.pe is not configured.")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="External API service is not configured."
            )
            
        url = f"{self._api_url}{path}"
        headers = {
            "Authorization": f"Bearer {self._api_token}",
            "Referer": "https://yasta.cloud"
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            logging.warning(f"HTTP error occurred: {http_err} - URL: {url}")
            detail = "Error consulting external service."
            try:
                detail = http_err.response.json().get("message", detail)
            except:
                pass
            raise HTTPException(status_code=http_err.response.status_code, detail=detail)
        except requests.exceptions.RequestException as req_err:
            logging.error(f"Request error occurred: {req_err}")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Could not connect to external service.")

    def get_person(self, dni: str) -> Optional[dict]:
        """Consulta un DNI en la API."""
        return self._get("/v2/reniec/dni", {"numero": dni})
        
    def get_company(self, ruc: str) -> Optional[dict]:
        """Consulta un RUC en la API."""
        return self._get("/v2/sunat/ruc", {"numero": ruc})

    def get_exchange_rate(self, date_str: str) -> Optional[dict]:
        """Consulta el tipo de cambio para una fecha específica."""
        return self._get("/v2/sunat/tipo-cambio", {"fecha": date_str})

    def get_exchange_rate_today(self) -> Optional[dict]:
        """Consulta el tipo de cambio de hoy."""
        return self._get("/v2/sunat/tipo-cambio", {})

    def get_exchange_rate_for_month(self, month: int, year: int) -> List[dict]:
        """Consulta el tipo de cambio para un mes y año."""
        return self._get("/v2/sunat/tipo-cambio", {"month": month, "year": year})


# --- Instancia del cliente y el router ---
api_client = ApisNetPe(token=settings.APIS_NET_PE_TOKEN)
router = APIRouter(prefix="/utils", tags=["Utilities"])


# --- Endpoints de la API ---

@router.get("/sunat-info/{ruc}", summary="Get RUC information from external API")
async def get_sunat_info(ruc: str):
    # <<< COMIENZA A REEMPLAZAR DESDE AQUÍ >>>
    if not (ruc.isdigit() and len(ruc) == 11 and (ruc.startswith('10') or ruc.startswith('20'))):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid RUC format.")
    
    company_data = api_client.get_company(ruc=ruc)
    
    if not company_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RUC not found or external service failed.")
    
    nombre_o_razon_social = company_data.get("nombre") or company_data.get("razonSocial")
    
    # --- LA CORRECCIÓN CLAVE ESTÁ AQUÍ ---
    # Obtenemos la dirección. Si no viene, es None.
    direccion = company_data.get("direccion")
    
    # Verificamos si la dirección es "falsa" (None, "", "-"). Si lo es, usamos nuestro texto.
    if not direccion or direccion.strip() == "-":
        direccion_final = "Dirección no disponible"
    else:
        direccion_final = direccion

    return {
        "razonSocial": nombre_o_razon_social,
        "direccion": direccion_final,
    }
    # <<< TERMINA DE REEMPLAZAR HASTA AQUÍ >>>

@router.get("/next-freemium-periods/{ruc}", summary="Get the next 2 tax periods for a RUC")
async def get_next_freemium_periods(ruc: str, db: Session = Depends(get_db)):
    """
    Calcula los próximos dos periodos tributarios a declarar para un RUC,
    usando la tabla de cronogramas y la fecha actual.
    """
    if not (ruc.isdigit() and len(ruc) == 11):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid RUC format.")

    # Usamos la fecha que me diste para la simulación
    today = date(2025, 6, 16)
    
    # Obtenemos los próximos periodos desde la base de datos
    due_schedules = crud_sunat_schedule.get_next_due_periods(db=db, ruc=ruc, from_date=today, count=2)
    
    if not due_schedules:
        return {"periods": [{"name": "No se encontraron próximos vencimientos.", "due_text": "Contacta a soporte."}]}
    
    meses_es = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    
    # Formateamos la respuesta para el frontend
    periods_for_frontend = []
    for schedule in due_schedules:
        try:
            period_year, period_month = map(int, schedule.tax_period.split('-'))
            month_name = meses_es[period_month - 1]
            days_until_due = (schedule.due_date - today).days
            
            if days_until_due < 0:
                due_text = "Vencido"
            elif days_until_due == 0:
                due_text = "Vence Hoy"
            elif days_until_due == 1:
                due_text = "Vence Mañana"
            else:
                due_text = f"Vence en {days_until_due} días"

            periods_for_frontend.append({
                "name": f"Declaración IGV-Renta ({month_name} {period_year})",
                "due_text": due_text
            })
        except (ValueError, IndexError):
            continue

    return {"periods": periods_for_frontend}