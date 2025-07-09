# app/crud/crud_declaration_request.py
from sqlalchemy.orm import joinedload

from sqlalchemy.orm import Session
from sqlalchemy import func, case

from app.models.declaration_request import DeclarationRequest
from app.models.yape_plin_transaction import YapePlinTransaction
from app.models.service_contract import ServiceContract
from app.models.monthly_declaration import MonthlyDeclaration
from app.models.sunat_schedule import SunatSchedule
from app.models.client_profile import ClientProfile

def get_declarations_for_dashboard(db: Session, client_profile_id: int, year: int):
    """
    Realiza una consulta compleja para obtener todos los datos necesarios
    para la tabla del dashboard de un cliente en un año específico.
    """
    # Subconsulta para obtener el último dígito del RUC del perfil de cliente.
    # Esto es necesario para unir con el cronograma de SUNAT.
    ruc_last_digit = func.substr(ClientProfile.ruc, -1, 1).label("ruc_last_digit")

    query = (
        db.query(
            DeclarationRequest.id,
            DeclarationRequest.tax_period,
            DeclarationRequest.status.label("request_status"),
            YapePlinTransaction.created_at.label("request_date"),
            ServiceContract.status.label("contract_status"),
            MonthlyDeclaration.sunat_presentation_date.label("filed_at"),
            SunatSchedule.due_date
        )
        .join(YapePlinTransaction, YapePlinTransaction.id == DeclarationRequest.yape_plin_transaction_id)
        .join(ClientProfile, ClientProfile.id == DeclarationRequest.client_profile_id)
        .outerjoin(ServiceContract, ServiceContract.id == DeclarationRequest.service_contract_id)
        .outerjoin(MonthlyDeclaration, MonthlyDeclaration.service_contract_id == ServiceContract.id)
        .outerjoin(
            SunatSchedule,
            (SunatSchedule.tax_period == DeclarationRequest.tax_period) &
            (SunatSchedule.last_ruc_digit == func.substr(ClientProfile.ruc, -1, 1))
        )
        .filter(DeclarationRequest.client_profile_id == client_profile_id)
        .filter(DeclarationRequest.tax_period.like(f"{year}-%"))
    )

    return query.all()

# === INICIO DE LA CORRECCIÓN ===

def get_details_for_modal(db: Session, *, request_id: int) -> DeclarationRequest | None:
    """
    Obtiene una solicitud de declaración con sus relaciones clave precargadas.
    No usa 'self' porque es una función a nivel de módulo.
    """
    return (
        db.query(DeclarationRequest)  # Cambiado de self.model a DeclarationRequest
        .options(
            joinedload(DeclarationRequest.client_profile),   # Cambiado de self.model.client_profile
            joinedload(DeclarationRequest.service_contract)  # Cambiado de self.model.service_contract
        )
        .filter(DeclarationRequest.id == request_id) # Cambiado de self.model.id
        .first()
    )

# === FIN DE LA CORRECCIÓN ===