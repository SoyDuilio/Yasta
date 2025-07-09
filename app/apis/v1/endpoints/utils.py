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

# --- Definición COMPLETA y CORRECTA de la Clase con DEPUREACIÓN ---
class ApisNetPe:
    def __init__(self, token: Optional[str] = None):
        # 1. Limpiamos el token para eliminar espacios en blanco accidentales
        self._api_token = token.strip() if token else None
        self._api_url = "https://api.apis.net.pe"
        
        # Sabemos que este log no se muestra al inicio, pero lo dejamos por si la config de logging cambia
        if self._api_token:
            logging.info(f"ApisNetPe Client configured with a token.")
        else:
            logging.error("CRITICAL: ApisNetPe Client is configured WITHOUT a token!")

    def _get(self, path: str, params: dict) -> Optional[dict]:
        if not self._api_token:
            # Este error sí se registrará porque ocurre durante una petición
            logging.error("API Token for apis.net.pe is missing in the request context.")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="External API service is not configured."
            )
            
        url = f"{self._api_url}{path}"
        headers = {
            # 2. Usamos el token ya limpio y quitamos el header 'Referer'
            "Authorization": f"Bearer {self._api_token}",
            #"Accept": "application/json"
        }

        # 3. Añadimos prints de depuración que SÍ se mostrarán en la consola por cada llamada
        print("\n--- [YASTA DEBUG] Making API Call to apis.net.pe ---")
        print(f"URL: {url}")
        print(f"PARAMS: {params}")
        # ¡IMPORTANTE! Revisa esta línea en tu consola para ver si el token tiene espacios o caracteres raros.
        print(f"HEADERS: Authorization: |{headers['Authorization']}|")
        print("------------------------------------------------------\n")

        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()  # Esto lanzará una excepción para errores HTTP (4xx o 5xx)
            return response.json()
        
        except requests.exceptions.HTTPError as http_err:
            # Este bloque se ejecutará si recibimos un 401, 404, 500, etc.
            logging.warning(f"HTTP error occurred from apis.net.pe: {http_err}")
            
            # Depuración adicional para ver la respuesta exacta del error
            print("\n--- [YASTA DEBUG] HTTP Error Response ---")
            print(f"Status Code: {http_err.response.status_code}")
            print(f"Response Body: {http_err.response.text}") # Esto nos dirá si la API da algún mensaje
            print("-----------------------------------------\n")

            detail = "Error consulting external service."
            try:
                # Intentamos extraer un mensaje de error más claro del JSON de respuesta
                error_response = http_err.response.json()
                detail = error_response.get("message", detail)
            except requests.exceptions.JSONDecodeError:
                # Si la respuesta no es JSON, usamos el texto plano
                detail = http_err.response.text if http_err.response.text else detail

            raise HTTPException(status_code=http_err.response.status_code, detail=detail)
        
        except requests.exceptions.RequestException as req_err:
            # Este bloque se ejecutará para errores de red (no se pudo conectar, timeout, etc.)
            logging.error(f"Network error connecting to apis.net.pe: {req_err}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
                detail="Could not connect to external service."
            )

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
        # Nota: La API parece no tener este endpoint documentado, verificar si es correcto.
        # Asumiendo que es un endpoint hipotético o no documentado.
        return self._get("/v2/sunat/tipo-cambio", {"month": month, "year": year})


# --- Instancia del cliente y el router ---
api_client = ApisNetPe(token=settings.APIS_NET_PE_TOKEN)
router = APIRouter(prefix="/utils", tags=["Utilities"])


# --- Endpoints de la API (Sin cambios, usan la lógica de arriba) ---

### INICIO DEL BLOQUE PARA REEMPLAZAR ###

@router.get("/sunat-info/{ruc}", summary="Get RUC information from external API")
async def get_sunat_info(ruc: str):

    # --- Print de depuración inicial ---
    print("\n" + "="*50)
    print(f"===> [API RUC] Endpoint /sunat-info/{ruc} ha sido llamado.")
    print(f"===> [API RUC] RUC recibido: {ruc}")
    print("="*50 + "\n")

    # --- 1. Validación del formato del RUC ---
    if not (ruc.isdigit() and len(ruc) == 11 and (ruc.startswith('10') or ruc.startswith('20'))):
        print(f"!!! [API RUC] Error: Formato de RUC inválido. RUC: '{ruc}'")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid RUC format.")
    
    print("===> [API RUC] Formato de RUC es válido.")

    try:
        # --- 2. Llamada al cliente de la API externa ---
        # La clase ApisNetPe ya tiene sus propios prints de depuración, así que veremos los detalles de la llamada.
        print("===> [API RUC] Intentando llamar a api_client.get_company(ruc=ruc)...")
        company_data = api_client.get_company(ruc=ruc)
        print(f"===> [API RUC] Datos recibidos de api_client: {company_data}")
        
        # --- 3. Validación de la respuesta de la API externa ---
        if not company_data:
            print("!!! [API RUC] Error: No se recibieron datos de la API externa (respuesta vacía).")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="RUC not found or external service failed.")
        
        print("===> [API RUC] La respuesta de la API externa no está vacía.")
        
        # --- 4. Procesamiento de los datos recibidos ---
        nombre_o_razon_social = company_data.get("nombre") or company_data.get("razonSocial")
        direccion = company_data.get("direccion")
        
        print(f"===> [API RUC] Nombre extraído: '{nombre_o_razon_social}'")
        print(f"===> [API RUC] Dirección extraída: '{direccion}'")

        if not direccion or direccion.strip() == "-":
            direccion_final = "Dirección no disponible"
        else:
            direccion_final = direccion
        
        print(f"===> [API RUC] Dirección final a devolver: '{direccion_final}'")
        
        response_data = {
            "razonSocial": nombre_o_razon_social,
            "direccion": direccion_final,
        }

        print(f"===> [API RUC] Devolviendo respuesta exitosa al frontend: {response_data}")
        return response_data

    except HTTPException as http_exc:
        # Si la excepción ya es una HTTPException (lanzada desde el cliente de la API),
        # simplemente la registramos y la volvemos a lanzar.
        print(f"!!! [API RUC] Se capturó una HTTPException: Status={http_exc.status_code}, Detail='{http_exc.detail}'")
        raise http_exc
        
    except Exception as e:
        # Para cualquier otra excepción inesperada durante el proceso.
        print(f"!!! [API RUC] EXCEPCIÓN INESPERADA en get_sunat_info: {type(e).__name__} - {e}")
        raise HTTPException(status_code=500, detail="Ocurrió un error interno al procesar la solicitud.")

### FIN DEL BLOQUE PARA REEMPLAZAR ###

@router.get("/next-freemium-periods/{ruc}", summary="Get the next 2 tax periods for a RUC")
async def get_next_freemium_periods(ruc: str, db: Session = Depends(get_db)):
    if not (ruc.isdigit() and len(ruc) == 11):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid RUC format.")

    today = date.today() # Usar la fecha real, a menos que estés en una simulación específica
    
    due_schedules = crud_sunat_schedule.get_next_due_periods(db=db, ruc=ruc, from_date=today, count=2)
    
    if not due_schedules:
        return {"periods": [{"name": "No se encontraron próximos vencimientos.", "due_text": "Contacta a soporte."}]}
    
    meses_es = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    
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