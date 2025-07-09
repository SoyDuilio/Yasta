# app/crud/crud_yape_plin_transaction.py

from sqlalchemy.orm import Session
from decimal import Decimal
from typing import Optional

from datetime import datetime

from app.models import User, YapePlinTransaction
from app.models.yape_plin_transaction import YapePlinTransaction, ExtractionStatus, DigitalWalletProvider

def update_transaction_status(db: Session, transaction_id: int, new_status: ExtractionStatus, notes: str = None):
    """Actualiza el estado y las notas de una transacción."""
    db_transaction = db.query(YapePlinTransaction).filter(YapePlinTransaction.id == transaction_id).first()
    if db_transaction:
        db_transaction.extraction_status = new_status
        if notes:
            db_transaction.processing_notes = notes
        db.commit()
    return db_transaction

def update_transaction_from_ai(db: Session, transaction_id: int, ai_data: dict, new_status: ExtractionStatus):
    """Actualiza una transacción con los datos extraídos por la IA."""
    db_transaction = db.query(YapePlinTransaction).filter(YapePlinTransaction.id == transaction_id).first()
    if not db_transaction:
        return None

    # Asigna los valores extraídos a las columnas correspondientes del modelo
    db_transaction.extracted_amount = ai_data.get('monto')
    db_transaction.extracted_currency = ai_data.get('moneda')
    db_transaction.extracted_operation_number = ai_data.get('numero_operacion')
    db_transaction.extracted_recipient_name = ai_data.get('nombre_destinatario')
    db_transaction.extracted_sender_name = ai_data.get('nombre_remitente')

    # Convierte fecha y hora de string a objetos de Python si vienen
    fecha_str = ai_data.get('fecha')
    if fecha_str:
        try:
            db_transaction.extracted_transaction_date = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            print(f"Formato de fecha inválido: {fecha_str}")

    hora_str = ai_data.get('hora')
    if hora_str:
        try:
            db_transaction.extracted_transaction_time = datetime.strptime(hora_str, '%H:%M:%S').time()
        except (ValueError, TypeError):
            print(f"Formato de hora inválido: {hora_str}")

    db_transaction.extraction_status = new_status
    db_transaction.processing_notes = "Datos extraídos automáticamente por IA."

    db.commit()
    return db_transaction

# NO SÉ SI SE ESTÁN USANDO ESTOS CRUDS, PERO LOS DEJARÉ POR SI ACASO
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