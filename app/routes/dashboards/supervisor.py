# app/routes/dashboards/supervisor.py
from fastapi import APIRouter, Depends, Request, HTTPException, Form, Query, status
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session, joinedload
from datetime import datetime, date, timezone
from typing import Optional

from app.crud import crud_user

from app.db.session import get_db
from app.core.templating import templates
from app.apis.deps import require_login_for_pages
from app.routes.pages import user_flow_guardian

from app.models.user import User, UserRole
from app.models.service_contract import ServiceContract, ServiceContractStatus
from app.models.client_profile import ClientProfile
from app.models.declaration_request import DeclarationRequest, DeclarationRequestStatus
from app.models.user_client_access import UserClientAccess
from app.models.service_type import ServiceType
from app.models.sunat_schedule import SunatSchedule, ContributorGroup

router = APIRouter(dependencies=[Depends(require_login_for_pages), Depends(user_flow_guardian)])

# --- Rutas de Vistas ---
@router.get("/", response_class=HTMLResponse, name="supervisor_dashboard_page")
async def serve_supervisor_dashboard_shell(
    request: Request,
    # 1. Añadimos la dependencia para obtener el usuario logueado
    current_user: User = Depends(require_login_for_pages) 
):
    initial_load_url = request.url_for('supervisor_validate_view')
    
    # 2. Añadimos 'current_user' al contexto que pasamos a la plantilla
    return templates.TemplateResponse("dashboard_supervisor.html", {
        "request": request,
        "initial_load_url": initial_load_url,
        "current_user": current_user 
    })

# --- ¡VISTA DE VALIDACIÓN ENRIQUECIDA! ---
@router.get("/validate-view", response_class=HTMLResponse, name="supervisor_validate_view")
async def get_validation_view(request: Request, db: Session = Depends(get_db)):
    pending_requests_query = db.query(DeclarationRequest).options(joinedload(DeclarationRequest.client_profile).joinedload(ClientProfile.user_accesses).joinedload(UserClientAccess.user)).filter(DeclarationRequest.status == DeclarationRequestStatus.PENDING_VALIDATION).order_by(DeclarationRequest.created_at.asc()).all()
    
    tax_periods_needed = {req.tax_period for req in pending_requests_query}
    schedules = db.query(SunatSchedule).filter(SunatSchedule.tax_period.in_(tax_periods_needed)).all()
    due_dates_map = {(s.tax_period, s.last_ruc_digit): s.due_date for s in schedules if s.contributor_group == ContributorGroup.GENERAL}

    requests_with_data = []
    for req in pending_requests_query:
        req.client_role = "N/A"
        for access in req.client_profile.user_accesses:
            if access.relationship_type.value == "TITULAR":
                req.client_role = access.user.role.value
                break
        
        last_digit = req.client_profile.ruc[-1]
        due_date = due_dates_map.get((req.tax_period, last_digit))
        
        # --- ¡CORRECCIÓN CLAVE! ---
        # La clave del diccionario ahora es 'request', para que coincida con la plantilla.
        requests_with_data.append({"request": req, "due_date": due_date})
        
    return templates.TemplateResponse("dashboards/supervisor/_validation_view.html", {
        "request": request,
        "pending_requests_data": requests_with_data,
        "today": date.today()
    })

# --- ¡NUEVO ENDPOINT PARA EL MODAL DE VALIDACIÓN! ---
@router.get("/confirm-validation", response_class=HTMLResponse, name="supervisor_confirm_validation")
async def get_confirm_validation_modal(request: Request, request_id: int = Query(...), db: Session = Depends(get_db)):
    req_data = db.query(DeclarationRequest).options(joinedload(DeclarationRequest.client_profile)).filter(DeclarationRequest.id == request_id).first()
    if not req_data: raise HTTPException(status_code=404, detail="Solicitud no encontrada.")
    client_role = "N/A"
    db.refresh(req_data.client_profile, ['user_accesses'])
    for access in req_data.client_profile.user_accesses:
        if access.relationship_type.value == "TITULAR": client_role = access.user.role.value; break
    return templates.TemplateResponse("dashboards/supervisor/_validation_confirmation_modal.html", {"request": request, "req": req_data, "client_role": client_role})


@router.get("/assignment-view", response_class=HTMLResponse, name="supervisor_assignment_view")
async def get_assignment_view(request: Request, db: Session = Depends(get_db)):
    pending_assignments_query = db.query(ServiceContract, ClientProfile).join(DeclarationRequest, ServiceContract.id == DeclarationRequest.service_contract_id).join(ClientProfile, DeclarationRequest.client_profile_id == ClientProfile.id).filter(ServiceContract.status == ServiceContractStatus.PENDING_STAFF_ASSIGNMENT).order_by(ServiceContract.requested_at.asc()).all()
    tax_periods_needed = {c.tax_period for c, p in pending_assignments_query}
    schedules = db.query(SunatSchedule).filter(SunatSchedule.tax_period.in_(tax_periods_needed)).all()
    due_dates_map = {(s.tax_period, s.last_ruc_digit): s.due_date for s in schedules if s.contributor_group == ContributorGroup.GENERAL}
    assignments_with_due_date = []
    for contract, profile in pending_assignments_query:
        last_digit = profile.ruc[-1]; due_date = due_dates_map.get((contract.tax_period, last_digit))
        assignments_with_due_date.append({"contract": contract, "profile": profile, "due_date": due_date})
    accountants = db.query(User).filter(User.role == UserRole.STAFF_COLLABORATOR).order_by(User.contact_name).all()
    return templates.TemplateResponse("dashboards/supervisor/_assignment_view.html", {"request": request, "pending_assignments": assignments_with_due_date, "accountants": accountants, "today": date.today()})

# En app/routes/dashboards/supervisor.py

@router.get("/confirm-assignment", response_class=HTMLResponse, name="supervisor_confirm_assignment")
async def get_confirm_assignment_modal(request: Request, db: Session = Depends(get_db), contract_id: int = Query(...), staff_id: int = Query(...)):
    contract = db.query(ServiceContract).filter_by(id=contract_id).first()
    accountant = db.query(User).filter_by(id=staff_id).first()
    profile = db.query(ClientProfile).join(DeclarationRequest, ClientProfile.id == DeclarationRequest.client_profile_id).filter(DeclarationRequest.service_contract_id == contract_id).first()
    if not contract or not accountant or not profile:
        raise HTTPException(status_code=404, detail="No se pudieron encontrar los datos para la confirmación.")
    return templates.TemplateResponse("dashboards/supervisor/_confirmation_modal.html", {"request": request, "contract": contract, "accountant": accountant, "profile": profile})

# --- Rutas de Acciones ---
@router.post("/validate-request/{request_id}", response_class=HTMLResponse, name="supervisor_validate_request")
async def validate_request_and_create_contract(request: Request, request_id: int, db: Session = Depends(get_db)):
    req_to_validate = db.query(DeclarationRequest).options(joinedload(DeclarationRequest.client_profile).joinedload(ClientProfile.user_accesses)).filter(DeclarationRequest.id == request_id).first()
    if not req_to_validate or req_to_validate.status != DeclarationRequestStatus.PENDING_VALIDATION: raise HTTPException(status_code=404, detail="Solicitud no encontrada o ya validada.")
    client_user_id = None
    for access in req_to_validate.client_profile.user_accesses:
        if access.relationship_type.value == "TITULAR": client_user_id = access.user_id; break
    if not client_user_id: raise HTTPException(status_code=500, detail="No se encontró un usuario titular.")
    service_type = db.query(ServiceType).filter(ServiceType.name == "Declaración Mensual General").first()
    if not service_type: raise HTTPException(status_code=500, detail="El tipo de servicio 'Declaración Mensual General' no existe.")
    new_contract = ServiceContract(client_id=client_user_id, service_type_id=service_type.id, status=ServiceContractStatus.PENDING_STAFF_ASSIGNMENT, tax_period=req_to_validate.tax_period, requested_at=req_to_validate.created_at)
    db.add(new_contract); db.flush()
    req_to_validate.status = DeclarationRequestStatus.VALIDATED; req_to_validate.service_contract_id = new_contract.id
    db.commit()
    card_html = f"""<div class="task-card" id="request-card-{request_id}"><div class="p-4 text-center font-semibold text-green-300">¡Validado! La tarea ahora está en la cola de asignación.</div></div><script>setTimeout(() => {{ const card = document.querySelector('#request-card-{request_id}'); if (card) {{ card.style.transition = 'opacity 0.5s ease-out'; card.style.opacity = '0'; setTimeout(() => card.remove(), 500); }} }}, 2500);</script>"""
    modal_html = """<div id="modal-container" hx-swap-oob="true"></div>"""
    return HTMLResponse(content=card_html + modal_html)

@router.post("/assign-contract", response_class=HTMLResponse, name="supervisor_assign_contract")
async def assign_contract_to_accountant(request: Request, db: Session = Depends(get_db), contract_id: int = Form(...), staff_id: int = Form(...)):
    contract = db.query(ServiceContract).filter_by(id=contract_id, status=ServiceContractStatus.PENDING_STAFF_ASSIGNMENT).first()
    if not contract: raise HTTPException(status_code=404, detail="Contrato no encontrado o ya no está pendiente.")
    accountant = db.query(User).filter_by(id=staff_id, role=UserRole.STAFF_COLLABORATOR).first()
    if not accountant: raise HTTPException(status_code=404, detail="Contador no encontrado.")
    contract.assigned_staff_id = staff_id; contract.status = ServiceContractStatus.ASSIGNED_TO_STAFF; contract.assigned_at = datetime.now(timezone.utc)
    db.commit()

    # --- ¡RESPUESTA AJUSTADA AL NUEVO TARGET! ---
    # Reemplaza la tarjeta completa con el mensaje de éxito.
    card_html = f"""
    <div class="task-card" id="task-card-{contract.id}">
        <div class="p-4 text-center font-semibold text-blue-300">
            Asignado a {accountant.contact_name}.
        </div>
    </div>
    <script>
        setTimeout(() => {{ 
            const card = document.querySelector('#task-card-{contract.id}');
            if (card) {{
                card.style.transition = 'opacity 0.5s ease-out';
                card.style.opacity = '0';
                setTimeout(() => card.remove(), 500);
            }}
        }}, 2500);
    </script>
    """

    modal_html = """<div id="modal-container" hx-swap-oob="true"></div>"""

    return HTMLResponse(content=card_html + modal_html)

# --- ¡NUEVO ENDPOINT PARA EL MODAL DE ALERTA GENÉRICO! ---
@router.get("/alert-modal", response_class=HTMLResponse, name="get_alert_modal")
async def get_alert_modal(request: Request, message: str = Query("Ocurrió un error.")):
    """Genera un modal de alerta simple con un mensaje personalizado."""
    return templates.TemplateResponse("partials/_alert_modal.html", {"request": request, "message": message, "title": "Atención"})



# RUTA PARA MOSTRAR LA VISTA DE GESTIÓN DE PERSONAL
@router.get("/manage-staff-view", response_class=HTMLResponse, name="supervisor_manage_staff_view")
async def get_manage_staff_view(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Muestra la vista para gestionar al personal (ver lista y formulario de creación).
    """
    # Consultamos solo a los usuarios que son parte del staff operativo
    staff_members = db.query(User).filter(
        User.role.in_([
            UserRole.STAFF_COLLABORATOR,
            UserRole.STAFF_MANAGER
        ])
    ).order_by(User.contact_name).all()
    
    # --- INICIO DE LA CORRECIÓN ---
    # Definimos la lista de roles que un supervisor puede crear.
    # Por ahora, solo puede crear contadores.
    creatable_roles = [UserRole.STAFF_COLLABORATOR]
    # --- FIN DE LA CORRECIÓN ---
    
    context = {
        "request": request,
        "staff_members": staff_members,
        "creatable_roles": creatable_roles # <-- Ahora pasamos la lista a la plantilla
    }
    
    return templates.TemplateResponse("dashboards/supervisor/_manage_staff_view.html", context)

# RUTA PARA PROCESAR LA CREACIÓN DE UN NUEVO MIEMBRO
# app/routes/dashboards/supervisor.py

@router.post("/create-staff", response_class=HTMLResponse, name="supervisor_create_staff")
async def create_staff_member(
    request: Request,
    db: Session = Depends(get_db),
    full_name: str = Form(...),
    dni: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    role: UserRole = Form(...)
):
    """
    Recibe los datos del formulario de nuevo personal, lo crea en la BD
    y devuelve la lista de staff actualizada para que HTMX la reemplace.
    """
    # 1. Validación
    if crud_user.get_by_email(db, email=email):
        return HTMLResponse("<div class='p-4 text-red-400 font-bold'>Error: El correo electrónico ya está en uso.</div>", status_code=400)
    
    # 2. Creación del usuario en la sesión de la BD
    crud_user.create_staff_user(
        db=db, 
        full_name=full_name, 
        dni=dni, 
        email=email, 
        password=password, 
        role=role
    )
    
    # 3. ¡CRÍTICO! Guardar los cambios en la base de datos
    db.commit()

    # 4. Preparar y devolver el fragmento HTML actualizado para HTMX
    staff_members = db.query(User).filter(
        User.role.in_([UserRole.STAFF_COLLABORATOR, UserRole.STAFF_MANAGER])
    ).order_by(User.contact_name).all()
    
    creatable_roles = [UserRole.STAFF_COLLABORATOR]
    
    context = {
        "request": request,
        "staff_members": staff_members,
        "creatable_roles": creatable_roles
    }
    
    # La plantilla _manage_staff_view.html es la que contiene tanto el formulario
    # como la lista, por lo que al devolverla, refrescamos todo el componente.
    return templates.TemplateResponse("dashboards/supervisor/_manage_staff_view.html", context)