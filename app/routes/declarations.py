# app/routes/declarations.py

import calendar
from datetime import datetime
from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.models.sunat_schedule import SunatSchedule
from app.models.monthly_declaration import MonthlyDeclaration
from app.models.user_client_access import UserClientAccess 

# === CAMBIO 1: Añadir dependencias necesarias ===
from app.apis.deps import get_current_active_user
from app.crud import crud_declaration_request
from app.db.session import get_db
from app.models.user import User
from app.models.user_client_access import UserClientAccess

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# Diccionario para mapear meses y estados a clases CSS (SIN CAMBIOS)
MONTH_NAMES = {1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril", 5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto", 9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"}
STATUS_STYLES = {
    "completed": "badge-green",
    "completed_paid": "badge-green",
    "in_progress": "badge-blue",
    "assigned_to_staff": "badge-blue",
    "pending_assignment": "badge-yellow",
    "requested_by_client": "badge-yellow",
    "failed": "badge-red",
    "failed_sunat_error": "badge-red",
    "cancelled": "badge-gray",
    "default": "badge-gray",
    "not_requested": "status-not-requested"
}

@router.get("/table", response_class=HTMLResponse)
async def get_declarations_table(
    request: Request,
    client_profile_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    # TODO: Añadir validación de seguridad para asegurar que el current_user
    # tiene acceso a este client_profile_id.

    year = datetime.now().year
    db_results = crud_declaration_request.get_declarations_for_dashboard(db, client_profile_id, year)
    declarations_map = {res.tax_period: res for res in db_results}
    
    display_items = []
    for month in range(1, 13):
        period = f"{year}-{str(month).zfill(2)}"
        if period in declarations_map:
            item_data = declarations_map[period]
            raw_status = item_data.contract_status.value if item_data.contract_status else item_data.request_status.value
            display_items.append({
                "id": item_data.id,
                "is_placeholder": False,
                "period_display": f"{MONTH_NAMES[month]} - {year}",
                "request_date": item_data.request_date.strftime("%d/%m/%Y") if item_data.request_date else "N/A",
                "due_date": item_data.due_date.strftime("%d/%m/%Y") if item_data.due_date else "N/A",
                "filed_at": item_data.filed_at.strftime("%d/%m/%Y %H:%M") if item_data.filed_at else "-",
                "status_text": raw_status.replace("_", " ").title(),
                "status_class": STATUS_STYLES.get(raw_status, STATUS_STYLES["default"])
            })
        else:
            display_items.append({
                "is_placeholder": True,
                "period_display": f"{MONTH_NAMES[month]} - {year}",
                "status_text": "Servicio de Declaración no Solicitado",
                "status_class": STATUS_STYLES["not_requested"]
            })
            
    display_items.reverse()
    context = {"request": request, "items": display_items}
    return templates.get_template("declarations/partials/_declarations_table.html").render(context)


# === CAMBIO 2: Lógica completa para el modal de detalles ===
@router.get("/details/{declaration_id}", response_class=HTMLResponse)
async def get_declaration_details(
    request: Request, 
    declaration_id: int, 
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user) # Dependencia de seguridad
):
    # 1. Obtener los datos de la DB.
    # Usaremos una función del CRUD que debería traer el objeto con sus relaciones
    # precargadas (como client_profile) para evitar consultas adicionales.
    # Si no tienes get_details, un get simple también funciona, pero es menos eficiente.
    # 1. Obtener los datos de la DB (Esta parte no cambia)
    declaration_data = crud_declaration_request.get_details_for_modal(db=db, request_id=declaration_id)
    
    if not declaration_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Declaración no encontrada")

    # === INICIO DE LA CORRECIÓN DE LA VALIDACIÓN ===

    # 2. Validación de Seguridad (¡CRÍTICO!) - Nueva Lógica
    # En lugar de buscar un user_id en client_profile, consultamos la tabla de acceso.
    
    client_profile_id_to_check = declaration_data.client_profile_id

    access_record = db.query(UserClientAccess).filter(
        UserClientAccess.user_id == current_user.id,
        UserClientAccess.client_profile_id == declaration_data.client_profile_id
    ).first()

    # Si no se encuentra un registro de acceso, el usuario no tiene permiso.
    if not access_record:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="No tienes permiso para ver esta declaración."
        )
    # === FIN DE LA CORRECIÓN DE LA VALIDACIÓN ===

    # === INICIO DE LA LÓGICA PARA DATOS REALES ===

    # 1. Obtener la fecha de vencimiento de SUNAT
    # === INICIO DE LA CORRECCIÓN ===

    # 1. Obtener la fecha de vencimiento de SUNAT (Método compatible con SQLAlchemy 1.x)
    due_date_result = db.query(SunatSchedule.due_date).filter(
        SunatSchedule.tax_period == declaration_data.tax_period,
        SunatSchedule.last_ruc_digit == declaration_data.client_profile.ruc[-1]
    ).first() # Usamos .first() que devuelve una tupla (o None)

    # Si .first() encontró un resultado, será una tupla como (datetime.date(...),).
    # Accedemos al primer elemento. Si no, es None.
    due_date_obj = due_date_result[0] if due_date_result else None
    
    due_date_str = due_date_obj.strftime("%d/%m/%Y") if due_date_obj else "No calculado"

    # === FIN DE LA CORRECCIÓN ===

    # 2. Obtener los montos de la declaración final (si existe)
    amount_declared_str = "Pendiente"
    amount_paid_sunat_str = "Pendiente"
    
    if declaration_data.service_contract and declaration_data.service_contract.monthly_declaration:
        monthly_decl = declaration_data.service_contract.monthly_declaration
        # Asumiendo que tu modelo MonthlyDeclaration tiene estos campos. ¡Ajústalos si se llaman diferente!
        total_income = monthly_decl.total_income or 0.0
        tax_to_pay = (monthly_decl.igv_payable or 0.0) + (monthly_decl.income_tax_payable or 0.0)
        
        amount_declared_str = f"S/ {total_income:,.2f}"
        amount_paid_sunat_str = f"S/ {tax_to_pay:,.2f}"

    # === FIN DE LA LÓGICA PARA DATOS REALES ===

    # Formatear el resto de los datos (sin cambios)
    year, month = map(int, declaration_data.tax_period.split('-'))
    period_display = f"{MONTH_NAMES[month]} - {year}"
    raw_status = (declaration_data.service_contract.status.value if declaration_data.service_contract else declaration_data.status.value)
    status_info = {
        "text": raw_status.replace("_", " ").title(),
        "class": STATUS_STYLES.get(raw_status, STATUS_STYLES["default"])
    }

    # Construir el contexto final con los datos reales
    details_context = {
        "id": declaration_data.id,
        "period_display": period_display,
        "ruc": declaration_data.client_profile.ruc,
        "razon_social": declaration_data.client_profile.business_name,
        "request_date": declaration_data.created_at.strftime("%d/%m/%Y %H:%M"),
        "status_info": status_info,
        "accountant_name": "Aún no asignado", # Placeholder, puedes obtenerlo del service_contract.staff_id
        "filed_at": (declaration_data.service_contract.monthly_declaration.sunat_presentation_date.strftime("%d/%m/%Y") 
                     if (declaration_data.service_contract and declaration_data.service_contract.monthly_declaration and declaration_data.service_contract.monthly_declaration.sunat_presentation_date)
                     else "No presentado"),
        # --- USANDO LOS NUEVOS VALORES DINÁMICOS ---
        "due_date": due_date_str,
        "amount_declared": amount_declared_str,
        "amount_paid_sunat": amount_paid_sunat_str,
    }

    context = { "request": request, "declaration": details_context }
    return templates.get_template("declarations/partials/_declaration_details_modal.html").render(context)