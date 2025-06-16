# app/apis/v1/endpoints/utils.py
import requests
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.apis.deps import get_db
from app.core.config import settings # <-- Importamos el objeto settings
from app.crud import crud_buen_contribuyente
# from app.crud import crud_sunat_schedule # (Descomentar cuando exista)

# --- Configuración del Cliente de API Externa ---
class ApisNetPe:
    def __init__(self, token: Optional[str] = None):
        self._api_token = token
        self._api_url = "https://api.apis.net.pe"

    def _get(self, path: str, params: dict):
        if not self._api_token:
            logging.error("API Token for apis.net.pe is not configured.")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="External API service is not configured."
            )
            
        url = f"{self._api_url}{path}"
        headers = {
            "Authorization": f"Bearer {self._api_token}",
            "Referer": "https://yasta.cloud" # Buena práctica
        }

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status() # Lanza una excepción para códigos 4xx/5xx
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            logging.warning(f"HTTP error occurred: {http_err} - URL: {url}")
            # Intenta devolver el detalle del error de la API si es posible
            detail = "Error consulting external service."
            try:
                detail = http_err.response.json().get("message", detail)
            except:
                pass
            raise HTTPException(status_code=http_err.response.status_code, detail=detail)
        except requests.exceptions.RequestException as req_err:
            logging.error(f"Request error occurred: {req_err}")
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Could not connect to external service.")

# Instancia del cliente de API, leyendo el token desde la configuración central
api_client = ApisNetPe(token=settings.APIS_NET_PE_TOKEN)

router = APIRouter(prefix="/utils", tags=["Utilities"])

@router.get("/sunat-info/{ruc}", summary="Get RUC information from external API")
async def get_sunat_info(ruc: str):
    """
    Validates a RUC and retrieves company data from an external provider.
    """
    if not (ruc.isdigit() and len(ruc) == 11 and (ruc.startswith('10') or ruc.startswith('20'))):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid RUC format."
        )

    company_data = api_client.get_company(ruc=ruc)

    if not company_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="RUC not found or external service failed."
        )
        
    return {
        "razonSocial": company_data.get("razonSocial"),
        "direccion": company_data.get("direccion"),
        "estado": company_data.get("estado"),
        "condicion": company_data.get("condicion"),
    }

@router.get("/next-freemium-periods/{ruc}", summary="Get the next 2 tax periods for a RUC")
async def get_next_freemium_periods(ruc: str, db: Session = Depends(get_db)):
    """
    Calculates the next two tax periods to be declared for a given RUC,
    considering if they are a "Buen Contribuyente".
    """
    if not (ruc.isdigit() and len(ruc) == 11):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid RUC format.")

    is_buc = crud_buen_contribuyente.is_buc(db, ruc=ruc)
    
    today = datetime.now().date()
    
    # Lógica de placeholder mejorada para calcular periodos
    current_month = today.month
    current_year = today.year

    # El periodo a declarar es siempre el mes anterior.
    # Ej: En Junio se declara Mayo.
    first_period_month = (current_month - 2 + 12) % 12 + 1
    first_period_year = current_year if current_month > 1 else current_year - 1

    # El segundo periodo es el siguiente al primero.
    second_period_month = (first_period_month % 12) + 1
    second_period_year = first_period_year if first_period_month < 12 else first_period_year + 1

    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

    return {
        "is_buc": is_buc,
        "periods": [
            {
                "name": f"Declaración IGV-Renta ({meses[first_period_month-1]} {first_period_year})",
                "due_text": "Gratis con tu prueba"
            },
            {
                "name": f"Declaración IGV-Renta ({meses[second_period_month-1]} {second_period_year})",
                "due_text": "Gratis con tu prueba"
            }
        ]
    }