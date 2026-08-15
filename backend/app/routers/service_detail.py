from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from psycopg import sql

from ..core.config import get_settings
from ..core.db import db_cursor
from ..core.security import require_api_key

router = APIRouter(prefix="/api/services", tags=["service-detail"], dependencies=[Depends(require_api_key)])
settings = get_settings()
S = sql.Identifier(settings.db_schema)


def _money(v) -> Decimal:
    return Decimal(str(v or 0))


@router.get("/{service_id}/detail")
def service_detail(service_id: UUID):
    with db_cursor() as cur:
        cur.execute(sql.SQL("""
            SELECT s.*, c.name AS client_name
            FROM {}.services s
            LEFT JOIN {}.clients c ON c.id=s.client_id
            WHERE s.id=%s
        """).format(S, S), [service_id])
        service = cur.fetchone()
        if not service:
            raise HTTPException(404, "Servicio no encontrado")

        cur.execute(sql.SQL("""
            SELECT sp.*,
                   r.document_number,
                   r.issue_date,
                   r.status AS receivable_status,
                   r.description AS invoice_description,
                   COALESCE((
                       SELECT SUM(fm.amount)
                       FROM {}.financial_movements fm
                       WHERE fm.receivable_id=r.id AND fm.type='ingreso'
                   ),0) AS paid_amount
            FROM {}.service_periods sp
            LEFT JOIN {}.receivables r ON r.id=sp.receivable_id
            WHERE sp.service_id=%s
            ORDER BY sp.period_number
        """).format(S, S, S), [service_id])
        periods = cur.fetchall()

        cur.execute(sql.SQL("""
            SELECT * FROM {}.service_documents
            WHERE service_id=%s
            ORDER BY created_at DESC
        """).format(S), [service_id])
        documents = cur.fetchall()

        invoiced = sum((_money(p["amount"]) for p in periods if p.get("receivable_id")), Decimal("0"))
        collected = sum((_money(p.get("paid_amount")) for p in periods), Decimal("0"))
        contract = _money(service.get("contract_amount"))

    return {
        "service": service,
        "metrics": {
            "contract_amount": contract,
            "invoiced": invoiced,
            "collected": collected,
            "pending_collection": max(Decimal("0"), invoiced - collected),
            "pending_invoice": max(Decimal("0"), contract - invoiced),
        },
        "periods": periods,
        "documents": documents,
    }


class PeriodInvoiceCreate(BaseModel):
    document_number: str
    issue_date: date = date.today()
    due_date: date | None = None
    notes: str | None = None


@router.post("/{service_id}/periods/{period_id}/invoice")
def invoice_period(service_id: UUID, period_id: UUID, body: PeriodInvoiceCreate):
    with db_cursor() as cur:
        cur.execute(sql.SQL("""
            SELECT sp.*, s.client_id, s.name AS service_name
            FROM {}.service_periods sp
            JOIN {}.services s ON s.id=sp.service_id
            WHERE sp.id=%s AND sp.service_id=%s
            FOR UPDATE
        """).format(S, S), [period_id, service_id])
        period = cur.fetchone()
        if not period:
            raise HTTPException(404, "Período no encontrado")
        if period.get("receivable_id"):
            raise HTTPException(400, "Este período ya fue facturado")

        description = f"{period['service_name']} - período {period['period_number']} ({period['period_start']} a {period['period_end']})"
        due = body.due_date or period.get("due_date")
        cur.execute(sql.SQL("""
            INSERT INTO {}.receivables
              (client_id,service_id,description,document_number,issue_date,due_date,amount,status,notes)
            VALUES (%s,%s,%s,%s,%s,%s,%s,'pendiente',%s)
            RETURNING *
        """).format(S), [period["client_id"], service_id, description, body.document_number,
                          body.issue_date, due, period["amount"], body.notes])
        receivable = cur.fetchone()
        cur.execute(sql.SQL("UPDATE {}.service_periods SET receivable_id=%s WHERE id=%s").format(S),
                    [receivable["id"], period_id])
        return receivable


class ServicePaymentCreate(BaseModel):
    account_id: UUID
    amount: Decimal
    payment_date: date = date.today()
    notes: str | None = None


@router.post("/{service_id}/receivables/{receivable_id}/payments")
def register_payment(service_id: UUID, receivable_id: UUID, body: ServicePaymentCreate):
    if body.amount <= 0:
        raise HTTPException(400, "El monto debe ser mayor a cero")

    with db_cursor() as cur:
        cur.execute(sql.SQL("""
            SELECT r.*, s.client_id, s.name AS service_name
            FROM {}.receivables r
            JOIN {}.services s ON s.id=r.service_id
            WHERE r.id=%s AND r.service_id=%s
            FOR UPDATE
        """).format(S, S), [receivable_id, service_id])
        r = cur.fetchone()
        if not r:
            raise HTTPException(404, "Cuenta por cobrar no encontrada")
        if r["status"] == "anulado":
            raise HTTPException(400, "La cuenta por cobrar está anulada")

        cur.execute(sql.SQL("""
            SELECT COALESCE(SUM(amount),0) AS paid
            FROM {}.financial_movements
            WHERE receivable_id=%s AND type='ingreso'
        """).format(S), [receivable_id])
        already = _money(cur.fetchone()["paid"])
        total = _money(r["amount"])
        pending = max(Decimal("0"), total - already)
        if body.amount > pending:
            raise HTTPException(400, f"El cobro supera el saldo pendiente ({pending})")

        cur.execute(sql.SQL("""
            INSERT INTO {}.financial_movements
              (account_id,service_id,client_id,receivable_id,type,category,description,amount,movement_date,notes)
            VALUES (%s,%s,%s,%s,'ingreso','cobro_servicio',%s,%s,%s,%s)
            RETURNING *
        """).format(S), [body.account_id, service_id, r["client_id"], receivable_id,
                          f"Cobro {r.get('document_number') or r['description']}", body.amount,
                          body.payment_date, body.notes])
        movement = cur.fetchone()

        new_paid = already + body.amount
        new_status = "cobrado" if new_paid >= total else "parcial"
        cur.execute(sql.SQL("UPDATE {}.receivables SET status=%s WHERE id=%s").format(S),
                    [new_status, receivable_id])
        return {"movement": movement, "paid_total": new_paid, "pending": max(Decimal("0"), total-new_paid), "status": new_status}
