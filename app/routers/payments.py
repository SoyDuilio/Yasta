# app/routers/payments.py
from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from decimal import Decimal
from datetime import datetime
from typing import Optional

from app.db.session import get_db
from app.schemas.payment import PaymentManualCreate
from app.models.fee_payment import FeePayment, FeePaymentStatus
from app.models.user import User
from app.apis.deps import get_current_active_user

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/payments/new", response_class=HTMLResponse)
async def get_new_payment_form(request: Request):
    return templates.TemplateResponse("payments/new_payment.html", {"request": request})

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
    payment_data = PaymentManualCreate(
        monto_pagado=monto_pagado,
        numero_operacion=numero_operacion,
        origen_app=origen_app,
        codigo_seguridad=codigo_seguridad
    )
    
    # Por ahora, el codigo_seguridad se valida pero no se guarda en FeePayment
    # ya que no tiene un campo para ello. Lo podríamos asociar a YapePlinTransaction
    # en un futuro si es necesario.
    new_fee_payment = FeePayment(
        paying_user_id=current_user.id,
        amount_paid=payment_data.monto_pagado,
        currency="PEN",
        payment_method_used=payment_data.origen_app,
        payment_reference=payment_data.numero_operacion,
        payment_date=datetime.now(tz=None),
        status=FeePaymentStatus.PENDING_VERIFICATION
    )
    
    db.add(new_fee_payment)
    db.commit()
    db.refresh(new_fee_payment)
    
    return templates.TemplateResponse("payments/partials/success_message.html", {"request": request})