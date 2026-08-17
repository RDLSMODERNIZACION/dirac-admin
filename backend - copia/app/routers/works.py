import calendar
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from psycopg import sql

from ..core.config import get_settings
from ..core.db import db_cursor
from ..core.security import require_api_key

router = APIRouter(prefix="/api/works", tags=["works"], dependencies=[Depends(require_api_key)])
settings = get_settings()
S = sql.Identifier(settings.db_schema)


def _month_start(d: date) -> date:
    return date(d.year, d.month, 1)


def _add_months(d: date, months: int) -> date:
    total = d.year * 12 + (d.month - 1) + months
    year = total // 12
    month = total % 12 + 1
    return date(year, month, 1)


def _due_date(year: int, month: int, billing_day: int) -> date:
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, min(billing_day, last_day))


@router.post("/{work_id}/generate-receivables")
def generate_receivables(work_id: str):
    """Generate missing monthly receivables for a monthly service contract.

    Idempotent: a deterministic document_number per work/period prevents duplicate
    installments when this endpoint is called more than once.
    """
    with db_cursor() as cur:
        cur.execute(
            sql.SQL("""
                SELECT id, code, client_id, name, type, status, start_date, end_date,
                       monthly_amount, billing_frequency, billing_day
                FROM {}.works
                WHERE id = %s
            """).format(S),
            [work_id],
        )
        work = cur.fetchone()

        if not work:
            raise HTTPException(status_code=404, detail="Obra/contrato no encontrado")
        if work["type"] != "servicio_mensual":
            raise HTTPException(status_code=400, detail="El contrato no es de tipo servicio_mensual")
        if work["billing_frequency"] != "mensual":
            raise HTTPException(status_code=400, detail="Por ahora el cronograma automático está habilitado para frecuencia mensual")
        if not work["start_date"] or not work["end_date"]:
            raise HTTPException(status_code=400, detail="El contrato necesita fecha de inicio y fecha de fin")
        if not work["monthly_amount"] or work["monthly_amount"] <= 0:
            raise HTTPException(status_code=400, detail="El contrato necesita un monto mensual mayor que cero")

        billing_day = int(work["billing_day"] or 10)
        if billing_day < 1 or billing_day > 31:
            raise HTTPException(status_code=400, detail="billing_day debe estar entre 1 y 31")

        start = work["start_date"]
        end = work["end_date"]
        cursor_month = _month_start(start)
        last_month = _month_start(end)
        created = []
        skipped = []

        while cursor_month <= last_month:
            due = _due_date(cursor_month.year, cursor_month.month, billing_day)
            # Never generate an installment outside the contractual interval.
            if due < start:
                cursor_month = _add_months(cursor_month, 1)
                continue
            if due > end:
                break

            period = f"{cursor_month.year:04d}-{cursor_month.month:02d}"
            document_number = f"AUTO-{work['code']}-{period}"

            cur.execute(
                sql.SQL("""
                    SELECT id, due_date, amount, status
                    FROM {}.receivables
                    WHERE work_id = %s AND document_number = %s
                    LIMIT 1
                """).format(S),
                [work_id, document_number],
            )
            existing = cur.fetchone()
            if existing:
                skipped.append({"period": period, "id": str(existing["id"]), "reason": "already_exists"})
            else:
                description = f"{work['name']} - {cursor_month.strftime('%m/%Y')}"
                cur.execute(
                    sql.SQL("""
                        INSERT INTO {}.receivables
                            (client_id, work_id, description, document_number, issue_date, due_date, amount, status, notes)
                        VALUES
                            (%s, %s, %s, %s, %s, %s, %s, 'pendiente', %s)
                        RETURNING id, due_date, amount, status, document_number
                    """).format(S),
                    [
                        work["client_id"], work_id, description, document_number,
                        max(start, cursor_month), due, work["monthly_amount"],
                        "Generado automáticamente desde contrato mensual",
                    ],
                )
                row = cur.fetchone()
                created.append({**row, "id": str(row["id"])})

            cursor_month = _add_months(cursor_month, 1)

    return {
        "work_id": work_id,
        "contract": work["name"],
        "billing_day": billing_day,
        "created_count": len(created),
        "skipped_count": len(skipped),
        "created": created,
        "skipped": skipped,
    }
