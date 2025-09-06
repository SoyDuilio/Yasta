# app/routes/capture.py
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.core.templating import templates
from app.db.session import get_db
from app.models.landing_lead import LandingLead
from app.core.security import encrypt_data

router = APIRouter(prefix="/gratis", tags=["Captura de Leads"])

# --- ENDPOINT PRINCIPAL: Sirve la página con la pregunta inicial ---
@router.get("", response_class=HTMLResponse, name="capture_page")
async def serve_capture_page(request: Request):
    return templates.TemplateResponse("capture/capture_page.html", {"request": request})

# --- ENDPOINTS PARA CARGAR LOS FORMULARIOS PARCIALES VÍA HTMX ---
@router.get("/get-full-form", response_class=HTMLResponse, name="get_capture_full_form")
async def get_capture_full_form(request: Request):
    return templates.TemplateResponse("capture/partials/_capture_form_full.html", {"request": request})

@router.get("/get-contact-form", response_class=HTMLResponse, name="get_capture_contact_form")
async def get_capture_contact_form(request: Request):
    return templates.TemplateResponse("capture/partials/_capture_form_contact.html", {"request": request})

# --- ENDPOINTS PARA PROCESAR LOS DATOS DE LOS FORMULARIOS ---
@router.post("/capturar-lead", name="capture_full_lead")
async def capture_full_lead(
    request: Request, db: Session = Depends(get_db),
    ruc: str = Form(...),
    business_name: str = Form(...),
    sol_user: str = Form(...),
    sol_pass: str = Form(...)
):
    encrypted_pass = encrypt_data(sol_pass)
    new_lead = LandingLead(
        ruc=ruc, sol_user=sol_user, encrypted_sol_pass=encrypted_pass,
        contact_name=business_name, source_landing="presencial", status="credentials_submitted"
    )
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)
    # Devuelve el paso de pedir WhatsApp
    return templates.TemplateResponse("capture/partials/_whatsapp_step.html", {"request": request, "lead": new_lead})

@router.post("/capturar-contacto", name="capture_contact_only")
async def capture_contact_only(
    request: Request, db: Session = Depends(get_db),
    ruc: str = Form(None),
    contact_name: str = Form(...),
    whatsapp_number: str = Form(...)
):
    new_lead = LandingLead(
        ruc=ruc, contact_name=contact_name, whatsapp_number=whatsapp_number,
        source_landing="presencial", status="forgot_sol_key"
    )
    db.add(new_lead)
    db.commit()
    db.refresh(new_lead)
    # Devuelve el agradecimiento y los enlaces a los demos
    return templates.TemplateResponse("capture/partials/_thank_you_plan_b.html", {"request": request})

# --- NUEVO ENDPOINT PARA GUARDAR WHATSAPP ---
@router.post("/guardar-whatsapp", name="capture_save_whatsapp")
async def save_whatsapp(
    request: Request, db: Session = Depends(get_db),
    lead_id: int = Form(...),
    whatsapp_number: str = Form(...)
):
    lead = db.query(LandingLead).filter(LandingLead.id == lead_id).first()
    if lead:
        lead.whatsapp_number = whatsapp_number
        db.commit()
    # Devuelve el paso final
    return templates.TemplateResponse("capture/partials/_thank_you_final.html", {
        "request": request,
        "yasta_whatsapp_number": "51999888777" # Configura tu número aquí
    })