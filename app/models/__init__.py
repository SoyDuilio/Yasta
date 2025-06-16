# app/models/__init__.py

# El propósito de este archivo es importar todos los modelos en un solo lugar.
# De esta manera, Alembic y SQLAlchemy pueden descubrir todas las tablas
# y sus relaciones simplemente importando 'from app.models import *'.
# El orden aquí es crucial para evitar errores de dependencia.

# 1. Modelos Base o de los que dependen muchos otros.
from .user import User, UserRole, SOLValidationStatus
from .client_profile import ClientProfile, ClientType

# 2. Tabla de Asociación que une a los de arriba.
from .user_client_access import UserClientAccess, RelationshipType

# 3. Modelos que dependen de User o ClientProfile.
from .sunat_credential import SunatCredential

# 4. Modelos del core de negocio (Servicios).
from .service_type import ServiceType
from .service_contract import ServiceContract, ServiceContractStatus

# 5. Modelos específicos de cada tipo de servicio.
from .monthly_declaration import MonthlyDeclaration, DeclarationType, SunatPaymentStatus
from .payroll_receipt import PayrollReceipt, PaymentMethodRxh

# 6. Modelos de soporte (Pagos, Documentos, Comunicaciones).
from .fee_payment import FeePayment, PaymentMethodPlatform, FeePaymentStatus
from .yape_plin_transaction import YapePlinTransaction, DigitalWalletProvider, ExtractionStatus
from .attached_document import AttachedDocument, DocumentType
from .communication import Communication, CommunicationChannel, CommunicationStatus

# 7. Modelos de Auditoría y Reportes.
from .credential_access_audit import CredentialAccessAudit
from .monthly_client_summary import MonthlyClientSummary

# 8. Modelos de Contabilidad Interna de la Empresa.
from .company_transaction import CompanyTransaction, TransactionType
from .company_tax_declaration import CompanyTaxDeclaration, TaxDeclarationTypeCompany

# 9. Modelos de Configuración y Reglas de Negocio
from .sunat_schedule import SunatSchedule, ContributorGroup
from .buen_contribuyente import BuenContribuyente # <-- NUEVO MODELO AÑADIDO
from .service_tariff import ServiceTariff