# app/routers/payments.py
import json # Para parsear el string JSON que vendrá del formulario
from fastapi import APIRouter, Depends, Request, Form, UploadFile, File, HTTPException, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime
from typing import Optional

from pydantic import ValidationError

from app.db.session import get_db
from app.schemas.payment import PaymentManualCreate
from app.models.fee_payment import FeePayment, FeePaymentStatus
from app.models.user import User
from app.apis.deps import get_current_active_user

# Importa los modelos y schemas que vamos a usar
from app.models.yape_plin_transaction import YapePlinTransaction, ExtractionStatus
from app.models.declaration_request import DeclarationRequest
from app.schemas.payment import UnifiedPaymentCreate

from app.models.client_profile import ClientProfile
from app.models.user_client_access import UserClientAccess

import shutil
import uuid
import os
from fastapi import BackgroundTasks
from datetime import datetime

# --- AÑADE LAS IMPORTACIONES DE NUESTROS MÓDULOS ---
from app.services import voucher_processor



# --- NUEVAS IMPORTACIONES ---
# Importamos la función CRUD que acabamos de crear
from app.crud import crud_yape_plin_transaction
# Importamos el Enum para el proveedor (yape/plin)
from app.models.yape_plin_transaction import DigitalWalletProvider

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


# --- Endpoint Principal para el Nuevo Formulario Unificado ---
# =========================================================================
# === VERSIÓN DEFINITIVA Y ROBUSTA DEL ENDPOINT DE REGISTRO UNIFICADO ===
# =========================================================================
### INICIO DEL BLOQUE PARA REEMPLAZAR ###

@router.post("/payments/register-unified", summary="Registra un pago unificado con declaraciones")
async def register_unified_payment(
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Endpoint para el nuevo formulario de registro de pago.
    Procesa manualmente el form-data para máxima robustez, maneja tanto
    entradas manuales como subidas de vouchers para procesamiento con IA.
    """
    # --- 1. Parseo y Validación del Formulario ---
    try:
        form_data = await request.form()
        payment_data_json = form_data.get("payment_data_json")
        voucher_file = form_data.get("voucher_file")

        if not payment_data_json:
            raise HTTPException(status_code=400, detail="Faltan datos del formulario (payment_data_json).")

        payment_data = UnifiedPaymentCreate.parse_raw(payment_data_json)

    except ValidationError as e:
        print(f"!!! ERROR DE VALIDACIÓN Pydantic !!!\n{e.json()}")
        raise HTTPException(status_code=422, detail={"message": "Datos de formulario inválidos.", "errors": e.errors()})
    except Exception as e:
        print(f"!!! ERROR INESPERADO AL PARSEAR: {e} !!!")
        raise HTTPException(status_code=400, detail=f"Error al procesar formulario: {e}")

    # --- 2. Creación y Procesamiento de la Transacción ---
    new_payment_transaction = YapePlinTransaction(
        uploader_user_id=current_user.id,
        client_profile_id=payment_data.client_profile_id,
        processing_notes="Registro creado desde formulario unificado."
    )

    if payment_data.payment_method == "MANUAL":
        if not payment_data.manual_data:
            raise HTTPException(status_code=400, detail="Faltan datos para registro manual.")
        
        # Completar objeto para el flujo MANUAL
        new_payment_transaction.user_declared_amount = payment_data.manual_data.declared_amount
        new_payment_transaction.extracted_operation_number = payment_data.manual_data.operation_number
        new_payment_transaction.provider = payment_data.manual_data.provider
        if payment_data.manual_data.provider and payment_data.manual_data.provider.value == 'yape':
            new_payment_transaction.extracted_security_code = payment_data.manual_data.security_code
        new_payment_transaction.original_image_filename = "manual_entry"
        new_payment_transaction.image_storage_path = "N/A"
        new_payment_transaction.extraction_status = ExtractionStatus.MANUAL_VERIFICATION_REQUIRED
        db.add(new_payment_transaction)

    elif payment_data.payment_method == "VOUCHER":
        # Comprobación robusta para el archivo
        if not voucher_file or not hasattr(voucher_file, 'filename'):
            raise HTTPException(status_code=400, detail="No se ha adjuntado el archivo del voucher o el archivo es inválido.")

        # Generar un nombre de archivo único usando UUID
        unique_id = uuid.uuid4()
        file_extension = os.path.splitext(voucher_file.filename)[1]
        unique_filename = f"{unique_id}{file_extension}"
        upload_dir = "uploads/vouchers"
        os.makedirs(upload_dir, exist_ok=True)
        file_path = os.path.join(upload_dir, unique_filename)

        # Completar objeto para el flujo VOUCHER. AHORA es válido.
        new_payment_transaction.extraction_status = ExtractionStatus.PENDING
        new_payment_transaction.original_image_filename = voucher_file.filename
        new_payment_transaction.image_storage_path = file_path # <-- Asignamos la ruta ANTES de cualquier operación de DB
        
        # Guardar el archivo físicamente en el disco
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(voucher_file.file, buffer)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"No se pudo guardar el archivo: {e}")

        # AHORA que el objeto es válido, lo añadimos a la sesión
        db.add(new_payment_transaction)

        # Añadir la tarea de procesamiento IA al fondo
        # Tenemos que hacer flush para obtener el ID y pasárselo a la tarea
        db.flush()
        background_tasks.add_task(
            voucher_processor.process_voucher_image,
            new_payment_transaction.id,
            file_path
        )
    else:
        raise HTTPException(status_code=400, detail=f"Método de pago no reconocido: '{payment_data.payment_method}'.")

    # --- 3. Creación de las Solicitudes de Declaración Hijas ---
    db.flush() # Asegurar que el ID de la transacción está disponible

    for decl_request in payment_data.declarations:
        new_request = DeclarationRequest(
            yape_plin_transaction_id=new_payment_transaction.id,
            client_profile_id=payment_data.client_profile_id,
            tax_period=f"{decl_request.year}-{str(decl_request.month).zfill(2)}",
            declaration_type=decl_request.declaration_type
        )
        db.add(new_request)

    # --- 4. Commit Final y Respuesta de Éxito ---
    db.commit()

    return HTMLResponse(
        content="""
        <div id="unified-payment-form-container" 
             style="display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; padding: 1.5rem; min-height: 300px;">
            <div style="margin-bottom: 1rem;">
                <svg style="width: 4rem; height: 4rem; color: #4ade80;" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
            </div>
            <h3 style="font-size: 1.5rem; line-height: 2rem; font-weight: 700; color: #ffffff; margin-bottom: 0.5rem;">¡Registro Exitoso!</h3>
            <p style="color: #d1d5db; max-width: 24rem;">Hemos recibido tu pago y tus solicitudes. Nuestro equipo lo verificará a la brevedad.</p>
        </div>
        """,
        status_code=status.HTTP_200_OK,
        headers={"HX-Trigger": "paymentSuccess"}
    )

### FIN DEL BLOQUE PARA REEMPLAZAR ###

### FIN DEL BLOQUE PARA REEMPLAZAR ###

    # === FIN DEL NUEVO BLOQUE ===

# =================================================================================
# A partir de aquí, el resto del código es el mismo, ya que tenemos las variables
# `payment_data` y `voucher_file` listas para usar.
# =================================================================================




# --- Endpoint Auxiliar para HTMX (Añadir Fila) ---
@router.get("/payments/declaration-row", response_class=HTMLResponse)
def get_declaration_row(request: Request):
    """
    Devuelve el fragmento de HTML para una nueva fila de declaración.
    HTMX usará esto para añadir filas dinámicamente.
    """
    # En el futuro, podríamos pasar los tipos de declaración desde aquí.
    # Por ahora, los hardcodeamos en la plantilla.
    # context = {"request": request, "declaration_types": [e.value for e in DeclarationType]}
    
    # Asumimos que tendrás una plantilla para la fila.
    # Crearemos esta plantilla en el siguiente paso.
    return templates.get_template("payments/partials/_declaration_request_row.html").render({"request": request})




@router.get("/payments/new", response_class=HTMLResponse)
async def get_new_payment_form(request: Request,
    # Añadimos la dependencia para asegurar que solo usuarios logueados pueden pedir el formulario
    current_user: User = Depends(get_current_active_user)):
    return templates.TemplateResponse("payments/partials/_payment_form.html", {"request": request})

@router.post("/payments/manual-entry", response_class=HTMLResponse)
async def process_manual_payment(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    monto_pagado: Decimal = Form(...),
    numero_operacion: str = Form(...),
    origen_app: str = Form(...),
    codigo_seguridad: Optional[str] = Form(None)
):
    """
    Procesa el registro manual de un pago Yape/Plin enviado por el cliente.

    Esta función NO crea un FeePayment. En su lugar, crea un YapePlinTransaction
    con el estado 'MANUAL_VERIFICATION_REQUIRED', que entra en el flujo de
    verificación del equipo de Yasta.
    """
    
    # 1. Validar y convertir el 'origen_app' del formulario al tipo Enum.
    #    Si el valor no es 'yape' o 'plin', FastAPI devolverá un error 422 automáticamente.
    provider_enum = DigitalWalletProvider(origen_app)
    
    # 2. Llamar a nuestra nueva función CRUD para crear el registro en la BD.
    crud_yape_plin_transaction.create_manual_transaction(
        db=db,
        uploader_user=current_user,
        provider=provider_enum,
        amount=monto_pagado,
        operation_number=numero_operacion,
        security_code=codigo_seguridad
    )
    
    # 3. Devolver la respuesta de éxito al usuario. Esta parte no cambia.
    return templates.TemplateResponse("payments/partials/_payment_success.html", {"request": request})



# --- RUTA DEFINITIVA PARA EL NUEVO FORMULARIO ---
# ===================================================================
# === NUEVO ENDPOINT PARA CARGAR EL FORMULARIO UNIFICADO EN EL MODAL ===
# ===================================================================
@router.get("/payments/get-unified-form", response_class=HTMLResponse)
async def get_unified_payment_form(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Obtiene los perfiles de cliente asociados al usuario y renderiza
    el formulario de pago unificado para ser cargado en el modal del dashboard.
    """
    # Lógica para obtener los perfiles de cliente (la misma que en tu ruta de prueba)
    client_profiles = (
        db.query(ClientProfile)
        .join(UserClientAccess)
        .filter(UserClientAccess.user_id == current_user.id)
        .all()
    )
    
    context = {
        "request": request,
        "client_profiles": client_profiles
    }
    
    # Renderizamos ÚNICAMENTE el parcial del formulario. HTMX lo inyectará en el modal.
    return templates.get_template("payments/partials/_unified_payment_form.html").render(context)


# --- RUTA DE PRUEBA TEMPORAL ---
@router.get("/payments/test-new-form", response_class=HTMLResponse)
async def test_new_payment_form(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    client_profiles = db.query(ClientProfile).join(UserClientAccess).filter(UserClientAccess.user_id == current_user.id).all()
    
    context = {
        "request": request,
        "client_profiles": client_profiles
    }
    
    # --- LA LÍNEA MODIFICADA ---
    # Ahora renderizamos la página completa que incluye el layout.
    return templates.get_template("payments/test_page.html").render(context)


# --- AL PESIONAR  "REGISTRAR  PAGO" ---
# ... (al final de las rutas existentes)
@router.get("/get-payment-instructions", response_class=HTMLResponse, name="get_payment_instructions")
async def get_payment_instructions(request: Request):
    """Devuelve el parcial con las instrucciones y QR para pagar."""
    return templates.get_template("payments/partials/_payment_instructions.html").render({"request": request})
