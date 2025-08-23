# app/routes/dashboards/supervisor.py
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from datetime import datetime, date
from typing import List

from app.db.session import get_db
from app.core.templating import templates
from app.apis.deps import get_current_user_from_cookie, require_login_for_pages
from app.routes.pages import user_flow_guardian # Importamos el guardián

# Importamos todos los modelos y enums necesarios
from app.models.user import User, UserRole
from app.models.service_contract import ServiceContract, ServiceContractStatus
from app.models.client_profile import ClientProfile
from app.models.user_client_access import UserClientAccess
from app.models.sunat_schedule import SunatSchedule, ContributorGroup

router = APIRouter(
    dependencies=[
        Depends(require_login_for_pages),
        Depends(user_flow_guardian)
    ]
)

@router.get("/", response_class=HTMLResponse, name="supervisor_dashboard_page")
async def serve_supervisor_dashboard_page(
    request: Request,
    current_user: User = Depends(get_current_user_from_cookie),
    db: Session = Depends(get_db)
):
    """
    Renderiza el dashboard del supervisor con la lista de declaraciones pendientes de asignar.
    """
    # 1. ¡CONSULTA CORREGIDA!
    # Hacemos el JOIN a través de la ruta correcta: ServiceContract -> User -> UserClientAccess -> ClientProfile
    pending_contracts_query = (
        db.query(ServiceContract, ClientProfile)
        .join(User, ServiceContract.client_id == User.id)
        .join(UserClientAccess, User.id == UserClientAccess.user_id)
        .join(ClientProfile, UserClientAccess.client_profile_id == ClientProfile.id)
        .filter(ServiceContract.status == ServiceContractStatus.PENDING_STAFF_ASSIGNMENT)
        .order_by(ServiceContract.requested_at.asc())
        .all()
    )

    # 2. Obtenemos los periodos y RUCs para buscar las fechas de vencimiento eficientemente.
    tax_periods = {c.tax_period for c, p in pending_contracts_query}
    due_date_schedules = {}
    if tax_periods:
        schedules = db.query(SunatSchedule).filter(SunatSchedule.tax_period.in_(tax_periods)).all()
        for s in schedules:
            key = (s.tax_period, s.last_ruc_digit, s.contributor_group.value) # Usamos .value para el group
            due_date_schedules[key] = s.due_date

    # 3. Enriquecemos los resultados con la fecha de vencimiento
    assignments_with_due_date = []
    for contract, profile in pending_contracts_query:
        last_digit = profile.ruc[-1]
        # Por ahora, asumimos que todos son del grupo 'general'.
        # En el futuro, se podría añadir una columna a ClientProfile para "Buen Contribuyente".
        group_key = ContributorGroup.GENERAL.value
        
        due_date = due_date_schedules.get((contract.tax_period, last_digit, group_key))
        
        assignments_with_due_date.append({
            "contract": contract,
            "profile": profile,
            "due_date": due_date
        })

    # 4. Query para obtener la lista de contadores (staff collaborators)
    accountants = db.query(User).filter(User.role == UserRole.STAFF_COLLABORATOR).order_by(User.contact_name).all()

    today_date = date.today()

    context = {
        "request": request,
        "current_user": current_user,
        "pending_assignments": assignments_with_due_date,
        "accountants": accountants,
        "today": today_date
    }
    return templates.TemplateResponse("dashboard_supervisor.html", context)


@router.post("/assign-contract", response_class=HTMLResponse, name="assign_contract_to_staff")
async def assign_contract_to_staff(
    request: Request,
    contract_id: int = Form(...),
    staff_id: int = Form(...),
    db: Session = Depends(get_db)
):
    staff_user = db.query(User).filter(User.id == staff_id, User.role == UserRole.STAFF_COLLABORATOR).first()
    if not staff_user:
        raise HTTPException(status_code=400, detail="Contador no válido o no encontrado.")

    contract = db.query(ServiceContract).filter(ServiceContract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contrato no encontrado")
    
    if contract.status != ServiceContractStatus.PENDING_STAFF_ASSIGNMENT:
        raise HTTPException(status_code=409, detail="Este contrato ya no está pendiente de asignación.")

    contract.assigned_staff_id = staff_id
    contract.status = ServiceContractStatus.ASSIGNED_TO_STAFF
    contract.assigned_at = datetime.utcnow()
    db.commit()

    return HTMLResponse(f"""
    <tr id="contract-row-{contract.id}" class="bg-green-900/50 text-center">
        <td colspan="8" class="p-4 font-semibold text-green-300">
            Asignado a {staff_user.contact_name} correctamente.
        </td>
    </tr>
    <script>
        setTimeout(() => {{
            const row = document.getElementById('contract-row-{contract.id}');
            if (row) {{
                row.style.transition = 'opacity 0.5s ease-out';
                row.style.opacity = '0';
                setTimeout(() => row.remove(), 500);
            }}
        }}, 2500);
    </script>
    """)