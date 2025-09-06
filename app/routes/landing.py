# app/routes/landing.py
from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.templating import templates
from app.db.session import get_db

from app.schemas.landing_lead import LandingLeadCreate
from app.crud import crud_landing_lead

# --- Modelos Pydantic para la validación de datos ---
class ClickEvent(BaseModel):
    event_name: str

class ForgotSOLEntry(BaseModel):
    ruc: str = Field(..., max_length=11)
    contact_name: str
    whatsapp_number: str = Field(..., max_length=9)

class WhatsAppEntry(BaseModel):
    # Asumimos que pasaremos el ID del usuario recién creado
    user_id: int 
    whatsapp_number: str = Field(..., max_length=9)

# Creamos un nuevo router para todas las rutas de la landing
router = APIRouter(tags=["Landing Page lanza"]) # <--- CAMBIO 1: Prefijo

# --- Modelos para la captura de datos ---
class ClickEvent(BaseModel):
    event_name: str

# --- RUTAS PARA SERVIR LAS 3 VERSIONES DE LA LANDING ---

@router.get("/formal", response_class=HTMLResponse, name="landing_formal") # <--- CAMBIO 2: Nueva ruta
async def serve_landing_formal(request: Request):
    """Sirve el diseño Formal y Confiable."""
    return templates.TemplateResponse("landing/landing_formal.html", {
        "request": request,
        "body_class": "theme-formal"
    })

@router.get("/sencilla", response_class=HTMLResponse, name="landing_sencilla") # <--- CAMBIO 3: Nueva ruta
async def serve_landing_sencilla(request: Request):
    """Sirve el diseño Sencillo y Festivo."""
    return templates.TemplateResponse("landing/landing_sencilla.html", {
        "request": request,
        "body_class": "theme-sencilla"
    })

@router.get("/moderna", response_class=HTMLResponse, name="landing_moderna") # <--- CAMBIO 4: Nueva ruta
async def serve_landing_moderna(request: Request):
    """Sirve el diseño Moderno y Tecnológico."""
    return templates.TemplateResponse("landing/landing_moderna.html", {
        "request": request,
        "body_class": "theme-moderna"
    })


# --- RUTAS PARA LA FUNCIONALIDAD (HTMX y JS) ---

@router.get("/get-registration-form", response_class=HTMLResponse, name="get_registration_form")
async def get_registration_form(request: Request):
    """Devuelve el parcial HTML del formulario para cargarlo en el modal."""
    return templates.TemplateResponse("landing/partials/_registration_form.html", {"request": request})


# --- ¡NUEVOS ENDPOINTS PARA EL FLUJO COMPLETO! ---

@router.post("/save-progress", name="save_onboarding_progress")
async def save_progress(form_data: ForgotSOLEntry, db: Session = Depends(get_db)):
    """Endpoint para el 'Plan B': El usuario no recuerda su Clave SOL."""
    print(f"--- LEAD 'OLVIDÉ MI CLAVE' CAPTURADO ---")
    print(f"RUC: {form_data.ruc}")
    print(f"Nombre: {form_data.contact_name}")
    print(f"WhatsApp: {form_data.whatsapp_number}")
    # AQUÍ VA TU LÓGICA PARA GUARDAR ESTE LEAD EN LA BASE DE DATOS
    # Ejemplo: crud_onboarding_lead.create(...)
    
    # Devolvemos la vista de agradecimiento
    return templates.TemplateResponse("landing/partials/_thank_you_plan_b.html", {"request": {}})

@router.post("/save-whatsapp", name="save_whatsapp_number")
async def save_whatsapp(form_data: WhatsAppEntry, db: Session = Depends(get_db)):
    """Guarda el número de WhatsApp después del registro exitoso."""
    print(f"--- GUARDANDO WHATSAPP PARA USUARIO {form_data.user_id} ---")
    print(f"WhatsApp: {form_data.whatsapp_number}")
    # AQUÍ VA TU LÓGICA PARA ACTUALIZAR AL USUARIO CON SU NÚMERO DE WHATSAPP
    # Ejemplo: user = crud_user.get(db, id=form_data.user_id); user.phone_number = form_data.whatsapp_number; db.commit()

    # Devolvemos la sección final con el enlace a WhatsApp
    return templates.TemplateResponse("landing/partials/_whatsapp_final_step.html", {
        "request": {},
        # Debes configurar tu número de WhatsApp aquí
        "yasta_whatsapp_number": "51999888777" 
    })


# --- INICIO: NUEVOS ENDPOINTS PARA MODALES DE CONTENIDO ---

@router.get("/get-what-is", response_class=HTMLResponse, name="get_what_is_content")
async def get_what_is_content(request: Request):
    """Devuelve el contenido para el modal '¿Qué es YASTA?'."""
    return templates.TemplateResponse("landing/partials/_what_is_content.html", {"request": request})

@router.get("/get-benefits", response_class=HTMLResponse, name="get_benefits_content")
async def get_benefits_content(request: Request):
    """Devuelve el contenido para el modal 'Beneficios'."""
    return templates.TemplateResponse("landing/partials/_benefits_content.html", {"request": request})

# --- FIN: NUEVOS ENDPOINTS ---


@router.post("/track-click", name="track_click")
async def track_click(event: ClickEvent):
    """Endpoint para hacer seguimiento de los clics en botones."""
    print(f"EVENTO DE TRACKING RECIBIDO: '{event.event_name}'")
    return {"status": "ok"}



# --- ¡NUEVO ENDPOINT PÚBLICO PARA CAPTURAR LEADS! ---
@router.post("/capture-lead", name="capture_landing_lead")
async def capture_lead(
    request: Request,
    db: Session = Depends(get_db),
    # Usamos Form(...) para recibir datos de un formulario HTML
    ruc: str = Form(...),
    sol_user: str = Form(...),
    sol_pass: str = Form(...),
    sol_pass_confirm: str = Form(...),
    business_name: str = Form(...), # Aunque no lo guardemos, el form lo envía
    source_landing: str = Form(...) # Campo oculto para saber de dónde vino
):
    """Endpoint público que recibe los datos del formulario y los guarda como un lead."""
    
    if sol_pass != sol_pass_confirm:
        # Manejo de error si las claves no coinciden
        return HTMLResponse("Error: Las claves SOL no coinciden.", status_code=400)

    lead_data = LandingLeadCreate(
        ruc=ruc,
        sol_user=sol_user,
        sol_pass=sol_pass,
        contact_name=business_name, # Usamos la razón social como nombre de contacto inicial
        source_landing=source_landing
    )
    
    lead = crud_landing_lead.create(db=db, obj_in=lead_data)
    
    # Devolvemos la primera parte de la página de agradecimiento
    return templates.TemplateResponse("landing/partials/_thank_you.html", {
        "request": request,
        "lead": lead # Pasamos el lead para poder usar su ID/RUC
    })
