# app/routes/leads.py
from fastapi import APIRouter, Depends, Request, Header, Query, HTTPException, status, Response
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import Annotated, Optional

import json

from app.core.config import settings
from app.core.templating import templates
from app.db.session import get_db
from app.models.landing_lead import LandingLead
from app.core.security import decrypt_data

# --- DEPENDENCIA DE SEGURIDAD A PRUEBA DE BALAS ---
async def verify_access_key(
    key: Optional[str] = Query(None), 
    x_access_key: Optional[str] = Header(None, alias="X-Access-Key") # Usamos alias para el header
):
    # La clave secreta de nuestra configuración
    secret = settings.LEADS_ACCESS_KEY
    
    # Comprueba si la clave viene en la URL O en el header
    if (key and key == secret) or (x_access_key and x_access_key == secret):
        return # Permite el acceso

    # Si no se encuentra en ninguno de los dos, deniega el acceso
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, 
        detail="Clave de acceso inválida o no proporcionada."
    )

router = APIRouter(prefix="/leads", tags=["Gestión de Leads"], dependencies=[Depends(verify_access_key)])

# --- ENDPOINT PRINCIPAL: Muestra el panel ---
@router.get("", response_class=HTMLResponse, name="leads_panel")
async def serve_leads_panel(request: Request, db: Session = Depends(get_db)):
    
    contacts_to_attend = db.query(LandingLead).filter(LandingLead.status == "forgot_sol_key").order_by(LandingLead.created_at.desc()).all()
    
    registrations_to_activate = db.query(LandingLead).filter(LandingLead.status == "credentials_submitted").order_by(LandingLead.created_at.desc()).all()

    return templates.TemplateResponse("leads/leads_panel.html", {
        "request": request,
        "contacts_to_attend": contacts_to_attend,
        "registrations_to_activate": registrations_to_activate,
        "access_key": settings.LEADS_ACCESS_KEY # Pasamos la clave al script
    })

# --- ENDPOINTS DE ACCIONES (HTMX) ---
# En app/routes/leads.py

@router.post("/update-status/{lead_id}/{new_status}", response_class=HTMLResponse, name="update_lead_status")
async def update_lead_status(
    request: Request, # <-- AÑADIMOS EL PARÁMETRO request
    lead_id: int, 
    new_status: str, 
    db: Session = Depends(get_db)
):
    lead = db.query(LandingLead).filter(LandingLead.id == lead_id).first()
    if lead:
        lead.status = new_status
        db.commit()
        # AÑADIMOS "request": request al contexto
        return templates.TemplateResponse("leads/partials/_lead_row_updated.html", {
            "request": request, 
            "lead": lead
        })
    return HTMLResponse("Lead no encontrado.", status_code=404)


# Reemplaza tu endpoint en app/routes/leads.py con esta versión con debug:

# Alternativa: usando JSONResponse en lugar de Response
from fastapi.responses import JSONResponse

# Reemplaza tu endpoint con esta versión final y limpia:

from fastapi.responses import JSONResponse

@router.post("/get-sol-key/{lead_id}", name="get_decrypted_sol_key")
async def get_sol_key(
    lead_id: int, 
    db: Session = Depends(get_db)
):
    """
    Busca un lead por su ID, desencripta su Clave SOL, y la envía
    al frontend a través de un header HX-Trigger para que sea copiada
    al portapapeles, sin exponerla en el cuerpo de la respuesta.
    """
    lead = db.query(LandingLead).filter(LandingLead.id == lead_id).first()

    if lead and lead.encrypted_sol_pass:
        try:
            # Desencripta la contraseña
            decrypted_pass = decrypt_data(lead.encrypted_sol_pass)
            
            # Prepara el payload del evento para HTMX
            event_data = {"password": decrypted_pass}
            json_payload = json.dumps({"copytoclipboard": event_data})
            
            # Crear respuesta con header personalizado
            return JSONResponse(
                content={"status": "success"}, 
                status_code=200,
                headers={"HX-Trigger": json_payload}
            )

        except Exception as e:
            print(f"--- ERROR al desencriptar clave para lead ID {lead_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No se pudo procesar la clave."
            )
            
    # Si no se encuentra el lead o no tiene clave
    raise HTTPException(status_code=404, detail="Lead o clave no encontrada.")