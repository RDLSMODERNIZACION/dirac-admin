from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from psycopg import sql

from ..core.config import get_settings
from ..core.db import db_cursor
from ..core.security import require_api_key

router = APIRouter(
    prefix="/api/financial-movements",
    tags=["financial-movements"],
    dependencies=[Depends(require_api_key)],
)

settings = get_settings()
S = sql.Identifier(settings.db_schema)


def _money(value) -> Decimal:
    return Decimal(str(value or 0))


@router.post("/{movement_id}/undo")
def undo_financial_movement(movement_id: UUID):
    with db_cursor() as cur:
        cur.execute(
            sql.SQL("SELECT * FROM {}.financial_movements WHERE id=%s FOR UPDATE").format(S),
            [movement_id],
        )
        movement = cur.fetchone()
        if not movement:
            raise HTTPException(404, "Movimiento no encontrado")

        receivable_id = movement.get("receivable_id")
        payable_id = movement.get("payable_id")

        cur.execute(
            sql.SQL("DELETE FROM {}.financial_movements WHERE id=%s").format(S),
            [movement_id],
        )

        receivable_status = None
        if receivable_id:
            cur.execute(
                sql.SQL("SELECT amount FROM {}.receivables WHERE id=%s FOR UPDATE").format(S),
                [receivable_id],
            )
            receivable = cur.fetchone()
            if receivable:
                total = _money(receivable.get("amount"))
                cur.execute(
                    sql.SQL("""
                        SELECT COALESCE(SUM(amount),0) AS paid
                        FROM {}.financial_movements
                        WHERE receivable_id=%s AND type='ingreso'
                    """).format(S),
                    [receivable_id],
                )
                paid = _money(cur.fetchone().get("paid"))
                receivable_status = "pendiente" if paid <= 0 else ("cobrado" if paid >= total else "parcial")
                cur.execute(
                    sql.SQL("UPDATE {}.receivables SET status=%s WHERE id=%s").format(S),
                    [receivable_status, receivable_id],
                )

        payable_status = None
        if payable_id:
            cur.execute(
                sql.SQL("SELECT amount FROM {}.payables WHERE id=%s FOR UPDATE").format(S),
                [payable_id],
            )
            payable = cur.fetchone()
            if payable:
                total = _money(payable.get("amount"))
                cur.execute(
                    sql.SQL("""
                        SELECT COALESCE(SUM(amount),0) AS paid
                        FROM {}.financial_movements
                        WHERE payable_id=%s AND type='egreso'
                    """).format(S),
                    [payable_id],
                )
                paid = _money(cur.fetchone().get("paid"))
                payable_status = "pagado" if paid >= total and total > 0 else "pendiente"
                cur.execute(
                    sql.SQL("UPDATE {}.payables SET status=%s WHERE id=%s").format(S),
                    [payable_status, payable_id],
                )

        return {
            "ok": True,
            "movement_id": str(movement_id),
            "amount": movement.get("amount"),
            "receivable_status": receivable_status,
            "payable_status": payable_status,
        }
