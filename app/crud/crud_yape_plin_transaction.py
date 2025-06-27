# app/crud/crud_yape_plin_transaction.py

from sqlalchemy.orm import Session
from decimal import Decimal
from typing import Optional

from app.models import User, YapePlinTransaction
from app.models.yape_plin_transaction import DigitalWalletProvider, ExtractionStatus

def create_manual_transaction(
    db: Session, 
    *, 
    uploader_user: User, 
    provider: DigitalWalletProvider, 
    amount: Decimal, 
    operation_number: str, 
    security_code: Optional[str]
) -> YapePlinTransaction:
    """
    Crea un registro de transacción Yape/Plin a partir de una entrada manual del usuario.
    
    Este registro se crea con un estado que indica que requiere verificación manual
    por parte del equipo de Yasta.
    """
    
    # Creamos la instancia del modelo con los datos proporcionados
    db_obj = YapePlinTransaction(
        uploader_user_id=uploader_user.id,
        provider=provider,
        user_declared_amount=amount,
        
        # Guardamos el número de operación y el código de seguridad en los campos 'extracted'
        # ya que son los datos que tenemos. Es consistente para un uso futuro.
        extracted_operation_number=operation_number,
        extracted_security_code=security_code,
        
        # Como no hay imagen, usamos placeholders para indicar que fue una entrada manual.
        original_image_filename="manual_entry",
        image_storage_path="N/A",
        
        # El estado inicial es clave para el proceso de back-office.
        extraction_status=ExtractionStatus.MANUAL_VERIFICATION_REQUIRED,

        processing_notes="Registro creado manualmente por el cliente."
    )
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    
    return db_obj