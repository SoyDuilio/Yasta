# app/routes/dashboards/staff.py
from fastapi import APIRouter, Depends, Request, HTTPException, Form, Response, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, date, timezone
from typing import Optional

from app.db.session import get_db
from app.core.templating import templates
from app.apis.deps import require_login_for_pages
from app.routes.pages import user_flow_guardian

from app.models.user import User, UserRole
from app.models.service_contract import ServiceContract, ServiceContractStatus
from app.models.client_profile import ClientProfile
from app.models.declaration_request import DeclarationRequest
from app.models.sunat_schedule import SunatSchedule, ContributorGroup
from app.models.credential_access_audit import CredentialAccessAudit
from app.core.security import decrypt_data
from app.models.sunat_credential import SunatCredential

router = APIRouter(dependencies=[Depends(require_login_for_pages), Depends(user_flow_guardian)])

# --- FUNCIÓN AUXILIAR REUTILIZABLE ---
def _get_task_data_for_template(db: Session, contract_id: int):
    """Función interna para obtener todos los datos de una tarea en el formato que espera la plantilla."""
    task_data = (
        db.query(ServiceContract, ClientProfile, DeclarationRequest)
        .join(DeclarationRequest, ServiceContract.id == DeclarationRequest.service_contract_id)
        .join(ClientProfile, DeclarationRequest.client_profile_id == ClientProfile.id)
        .filter(ServiceContract.id == contract_id)
        .first()
    )
    if not task_data: return None
    
    contract, profile, declaration_req = task_data
    schedule = db.query(SunatSchedule).filter_by(tax_period=contract.tax_period, last_ruc_digit=profile.ruc[-1]).first()
    due_date = schedule.due_date if schedule else None
    
    return { "contract": contract, "profile": profile, "declaration_request": declaration_req, "due_date": due_date }

# --- VISTAS DEL DASHBOARD ---
@router.get("/", response_class=HTMLResponse, name="staff_dashboard_page")
async def serve_staff_dashboard_shell(request: Request):
    initial_load_url = request.url_for('staff_tasks_view')
    return templates.TemplateResponse("dashboard_staff.html", {
        "request": request,
        "initial_load_url": initial_load_url
    })

STATUS_DISPLAY_MAP = {
    ServiceContractStatus.IN_PROGRESS: "En Proceso",
    ServiceContractStatus.PENDING_CLIENT_ACTION: "Acción Cliente",
    ServiceContractStatus.COMPLETED_PAID: "Completada",
    ServiceContractStatus.FAILED_MISSING_INFO: "Info Faltante"
}

@router.get("/tasks-view", response_class=HTMLResponse, name="staff_tasks_view")
async def get_staff_tasks_view(request: Request, current_user: User = Depends(require_login_for_pages), db: Session = Depends(get_db)):
    active_statuses = [ServiceContractStatus.ASSIGNED_TO_STAFF, ServiceContractStatus.IN_PROGRESS, ServiceContractStatus.PENDING_CLIENT_ACTION, ServiceContractStatus.FAILED_MISSING_INFO]
    assigned_tasks_query = db.query(ServiceContract).filter(ServiceContract.assigned_staff_id == current_user.id, ServiceContract.status.in_(active_statuses)).order_by(ServiceContract.assigned_at.desc()).all()
    
    tasks_with_data = [_get_task_data_for_template(db, contract.id) for contract in assigned_tasks_query if _get_task_data_for_template(db, contract.id) is not None]
    
    available_statuses = [ServiceContractStatus.IN_PROGRESS, ServiceContractStatus.PENDING_CLIENT_ACTION, ServiceContractStatus.COMPLETED_PAID, ServiceContractStatus.FAILED_MISSING_INFO]

    available_statuses = [
        ServiceContractStatus.IN_PROGRESS,
        ServiceContractStatus.PENDING_CLIENT_ACTION,
        ServiceContractStatus.COMPLETED_PAID,
        ServiceContractStatus.FAILED_MISSING_INFO
    ]

    return templates.TemplateResponse("dashboards/staff/_staff_tasks_view.html", {
        "request": request,
        "assigned_tasks": tasks_with_data,
        "today": date.today(),
        "available_statuses": available_statuses,
        "status_map": STATUS_DISPLAY_MAP # <-- Pasamos el mapa de traducción
    })

@router.get("/confirm-update-status", response_class=HTMLResponse, name="staff_confirm_update_status")
async def get_confirm_update_modal(
    request: Request,
    contract_id: int = Query(...),
    new_status: ServiceContractStatus = Query(...) # Recibimos el new_status
):
    return templates.TemplateResponse("dashboards/staff/_update_confirmation_modal.html", {
        "request": request,
        "contract_id": contract_id,
        "new_status": new_status, # Lo pasamos a la plantilla
        "new_status_display": new_status.name.replace('_', ' ').title()
    })

# --- ¡FUNCIÓN DE ACTUALIZACIÓN CORREGIDA Y COMPLETA! ---
@router.post("/update-task-status", response_class=HTMLResponse, name="staff_update_task_status")
async def update_task_status(
    request: Request, current_user: User = Depends(require_login_for_pages), db: Session = Depends(get_db),
    contract_id: int = Form(...), new_status: ServiceContractStatus = Form(...)
):
    contract = db.query(ServiceContract).filter_by(id=contract_id, assigned_staff_id=current_user.id).first()
    if not contract: raise HTTPException(status_code=404, detail="Tarea no encontrada.")
    
    contract.status = new_status
    if new_status == ServiceContractStatus.COMPLETED_PAID:
        contract.completed_at = datetime.now(timezone.utc)
    db.commit()

    # Usamos la función auxiliar para obtener los datos frescos y completos de la tarea
    updated_task = _get_task_data_for_template(db, contract_id)
    if not updated_task: 
        return HTMLResponse("<div class='text-red-500 p-4'>Error al recargar la tarea.</div>")

    # Obtenemos la lista de estados disponibles de nuevo para la plantilla
    available_statuses = [
        ServiceContractStatus.IN_PROGRESS, ServiceContractStatus.PENDING_CLIENT_ACTION,
        ServiceContractStatus.COMPLETED_PAID, ServiceContractStatus.FAILED_MISSING_INFO
    ]
    
    # Renderizamos la tarjeta actualizada
    card_html = templates.get_template("dashboards/staff/partials/_staff_task_card.html").render({
        "request": request,
        "task": updated_task,
        "today": date.today(),
        "available_statuses": available_statuses,
        "status_map": STATUS_DISPLAY_MAP # <-- Pasamos el mapa de traducción
    })

    # Y enviamos la instrucción para cerrar el modal
    modal_html = """<div id="modal-container" hx-swap-oob="true"></div>"""
    
    return HTMLResponse(content=card_html + modal_html)


@router.post("/copy-sol-password/{contract_id}", response_class=HTMLResponse, name="staff_copy_sol_password")
async def copy_sol_password(
    response: Response, request: Request, contract_id: int, current_user: User = Depends(require_login_for_pages), db: Session = Depends(get_db)
):
    profile = (db.query(ClientProfile).join(DeclarationRequest, ClientProfile.id == DeclarationRequest.client_profile_id).filter(DeclarationRequest.service_contract_id == contract_id).options(joinedload(ClientProfile.sunat_credential)).first())
    if not profile or not profile.sunat_credential:
        audit = CredentialAccessAudit(accessing_user_id=current_user.id, service_contract_id=contract_id, action_performed="VIEW_SOL_PASSWORD", access_successful=False, failure_reason_if_any="Credencial no encontrada.")
        db.add(audit); db.commit()
        return HTMLResponse("<script>alert('Error: No se encontraron las credenciales para este cliente.');</script>")

    credential = profile.sunat_credential
    try:
        decrypted_password = decrypt_data(credential.encrypted_sol_password)
    except Exception as e:
        audit = CredentialAccessAudit(credential_id=credential.id, accessing_user_id=current_user.id, service_contract_id=contract_id, action_performed="VIEW_SOL_PASSWORD", access_successful=False, failure_reason_if_any=f"Error de desencriptación: {e}")
        db.add(audit); db.commit()
        return HTMLResponse("<script>alert('Error: No se pudo desencriptar la clave.');</script>")
    
    audit = CredentialAccessAudit(credential_id=credential.id, accessing_user_id=current_user.id, service_contract_id=contract_id, action_performed="VIEW_SOL_PASSWORD", access_successful=True)
    db.add(audit); db.commit()
    
    success_count = (db.query(CredentialAccessAudit).filter_by(service_contract_id=contract_id, access_successful=True, action_performed="VIEW_SOL_PASSWORD").count())
    
    updated_button_html = templates.get_template("dashboards/staff/partials/_sol_button_updated.html").render({"request": request, "contract_id": contract_id, "request_count": success_count})
    
    import json
    event_data = {"password": decrypted_password, "message": "¡Clave SOL copiada!"}
    response.headers["HX-Trigger"] = json.dumps({"copyToClipboardAndNotify": event_data})
    
    return HTMLResponse(content=updated_button_html)