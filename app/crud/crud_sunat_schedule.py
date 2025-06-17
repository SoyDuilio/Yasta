# app/crud/crud_sunat_schedule.py
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from app.models.sunat_schedule import SunatSchedule, ContributorGroup
from .crud_buen_contribuyente import crud_buen_contribuyente

class CRUDSunatSchedule:
    def get_next_due_periods(
        self, 
        db: Session, 
        *, 
        ruc: str, 
        from_date: date, 
        count: int = 2
    ) -> List[SunatSchedule]:
        """
        Obtiene los próximos 'count' periodos tributarios a vencer para un RUC específico
        a partir de una fecha dada, considerando si es Buen Contribuyente.
        """
        is_buc = crud_buen_contribuyente.is_buc(db, ruc=ruc)
        last_digit = ruc[-1]
        
        group_to_query = ContributorGroup.BUEN_CONTRIBUYENTE if is_buc else ContributorGroup.GENERAL

        # La consulta busca registros que cumplan todas las condiciones:
        # - El grupo de contribuyente sea el correcto.
        # - El último dígito del RUC coincida.
        # - La fecha de vencimiento sea igual o posterior a la fecha de hoy.
        # Se ordena por fecha de vencimiento y se toman los primeros 'count' resultados.
        due_schedules = (
            db.query(SunatSchedule)
            .filter(
                SunatSchedule.contributor_group == group_to_query,
                SunatSchedule.last_ruc_digit == last_digit,
                SunatSchedule.due_date >= from_date,
            )
            .order_by(SunatSchedule.due_date.asc())
            .limit(count)
            .all()
        )
        return due_schedules

crud_sunat_schedule = CRUDSunatSchedule()