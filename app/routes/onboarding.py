# app/routes/pages.py
router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

import json # Para parsear el string JSON que vendrá del formulario
from fastapi import APIRouter, Depends, Request, Form, UploadFile, File, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app.apis.deps import get_current_active_user

@router.get("/onboarding/get-register-form", response_class=HTMLResponse, name="onboarding_get_form")
async def get_register_ruc_form(request: Request):
    """Devuelve el parcial del formulario para registrar un RUC."""
    return templates.get_template("onboarding/partials/_register_ruc_form.html").render({"request": request})

@router.post("/onboarding/finalize-htmx", response_class=HTMLResponse, name="onboarding_finalize_htmx")
async def onboarding_finalize_htmx(request: Request):
    """Procesa el envío del formulario de RUC desde HTMX y devuelve un mensaje."""
    # TODO: Añadir la lógica real de guardado de datos del RUC aquí
    return HTMLResponse("""
        <div class="text-center p-8">
            <h3 class="font-bold text-lg text-green-300">¡Solicitud Recibida!</h3>
            <p class="text-gray-300">Verificaremos los datos de tu nuevo RUC y te notificaremos. Puedes cerrar esta ventana.</p>
        </div>
    """)