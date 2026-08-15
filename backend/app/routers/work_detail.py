from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from psycopg import sql

from ..core.config import get_settings
from ..core.db import db_cursor
from ..core.security import require_api_key

router = APIRouter(prefix="/api/works", tags=["work-detail"], dependencies=[Depends(require_api_key)])
settings = get_settings()
S = sql.Identifier(settings.db_schema)


def _rows(cur, query: str, params):
    cur.execute(sql.SQL(query).format(*([S] * query.count("{}"))), params)
    return cur.fetchall()


@router.get("/{work_id}/detail")
def work_detail(work_id: UUID):
    with db_cursor() as cur:
        cur.execute(sql.SQL("""
            SELECT w.*, c.name AS client_name
            FROM {}.works w
            JOIN {}.clients c ON c.id = w.client_id
            WHERE w.id = %s
        """).format(S, S), [work_id])
        work = cur.fetchone()
        if not work:
            raise HTTPException(404, "Obra no encontrada")

        items = _rows(cur, """
            SELECT wi.*,
                   (wi.budget_amount * wi.progress_percent / 100.0) AS executed_amount,
                   COALESCE(b.billed_amount,0) AS billed_amount,
                   GREATEST(0, (wi.budget_amount * wi.progress_percent / 100.0) - COALESCE(b.billed_amount,0)) AS available_to_invoice
            FROM {}.work_items wi
            LEFT JOIN (
                SELECT ii.work_item_id, SUM(ii.amount) AS billed_amount
                FROM {}.work_invoice_items ii
                JOIN {}.work_invoices inv ON inv.id=ii.work_invoice_id
                WHERE inv.work_id=%s AND inv.status <> 'anulada'
                GROUP BY ii.work_item_id
            ) b ON b.work_item_id=wi.id
            WHERE wi.work_id=%s
            ORDER BY wi.code NULLS LAST, wi.created_at
        """, [work_id, work_id])
        budget = _rows(cur, "SELECT * FROM {}.work_budget_items WHERE work_id=%s ORDER BY category, created_at", [work_id])
        costs = _rows(cur, """
            SELECT wc.*, s.name AS supplier_name
            FROM {}.work_costs wc
            LEFT JOIN {}.suppliers s ON s.id=wc.supplier_id
            WHERE wc.work_id=%s ORDER BY wc.cost_date DESC, wc.created_at DESC
        """, [work_id])
        certs = _rows(cur, "SELECT * FROM {}.work_certificates WHERE work_id=%s ORDER BY period_to DESC NULLS LAST, created_at DESC", [work_id])
        docs = _rows(cur, "SELECT * FROM {}.work_documents WHERE work_id=%s ORDER BY document_date DESC, created_at DESC", [work_id])
        recv = _rows(cur, "SELECT * FROM {}.receivables WHERE work_id=%s ORDER BY due_date DESC NULLS LAST, created_at DESC", [work_id])
        invoices = _rows(cur, """
            SELECT inv.*, r.status AS receivable_status,
                   COALESCE(
                     jsonb_agg(
                       jsonb_build_object(
                         'id', ii.id,
                         'work_item_id', ii.work_item_id,
                         'amount', ii.amount,
                         'progress_percent_snapshot', ii.progress_percent_snapshot,
                         'executed_amount_snapshot', ii.executed_amount_snapshot,
                         'item_code', wi.code,
                         'item_description', wi.description
                       ) ORDER BY wi.code
                     ) FILTER (WHERE ii.id IS NOT NULL),
                     '[]'::jsonb
                   ) AS items
            FROM {}.work_invoices inv
            LEFT JOIN {}.receivables r ON r.id=inv.receivable_id
            LEFT JOIN {}.work_invoice_items ii ON ii.work_invoice_id=inv.id
            LEFT JOIN {}.work_items wi ON wi.id=ii.work_item_id
            WHERE inv.work_id=%s
            GROUP BY inv.id, r.status
            ORDER BY inv.issue_date DESC, inv.created_at DESC
        """, [work_id])
        pay = _rows(cur, """
            SELECT p.*, s.name AS supplier_name
            FROM {}.payables p
            LEFT JOIN {}.suppliers s ON s.id=p.supplier_id
            WHERE p.work_id=%s ORDER BY p.due_date DESC NULLS LAST, p.created_at DESC
        """, [work_id])

        real_cost = sum((Decimal(str(x.get("amount") or 0)) for x in costs if x.get("payment_status") != "anulado"), Decimal("0"))
        invoiced = sum((Decimal(str(x.get("total_amount") or 0)) for x in invoices if x.get("status") != "anulada"), Decimal("0"))
        executed_amount = sum((Decimal(str(x.get("executed_amount") or 0)) for x in items if x.get("status") != "cancelado"), Decimal("0"))
        available_to_invoice = sum((Decimal(str(x.get("available_to_invoice") or 0)) for x in items if x.get("status") != "cancelado"), Decimal("0"))
        collected = Decimal("0")
        cur.execute(sql.SQL("""
            SELECT COALESCE(SUM(amount),0) AS total
            FROM {}.financial_movements
            WHERE work_id=%s AND type='ingreso'
        """).format(S), [work_id])
        collected = Decimal(str(cur.fetchone()["total"] or 0))
        paid = Decimal("0")
        cur.execute(sql.SQL("""
            SELECT COALESCE(SUM(amount),0) AS total
            FROM {}.financial_movements
            WHERE work_id=%s AND type='egreso'
        """).format(S), [work_id])
        paid = Decimal(str(cur.fetchone()["total"] or 0))
        contract = Decimal(str(work.get("contract_amount") or 0))

    return {
        "work": work,
        "metrics": {
            "real_cost": real_cost,
            "projected_result": contract - real_cost,
            "executed_amount": executed_amount,
            "invoiced": invoiced,
            "available_to_invoice": available_to_invoice,
            "collected": collected,
            "pending_collection": max(Decimal("0"), invoiced - collected),
            "paid": paid,
        },
        "items": items,
        "budget_items": budget,
        "costs": costs,
        "certificates": certs,
        "documents": docs,
        "receivables": recv,
        "invoices": invoices,
        "payables": pay,
    }


class CostCreate(BaseModel):
    supplier_id: UUID | None = None
    cost_date: date = date.today()
    category: str = "otros"
    concept: str
    quantity: Decimal = Decimal("1")
    unit: str | None = None
    unit_price: Decimal
    payment_status: str = "pendiente"
    due_date: date | None = None
    invoice_number: str | None = None
    notes: str | None = None


@router.post("/{work_id}/costs")
def create_work_cost(work_id: UUID, body: CostCreate):
    with db_cursor() as cur:
        cur.execute(sql.SQL("SELECT id FROM {}.works WHERE id=%s").format(S), [work_id])
        if not cur.fetchone():
            raise HTTPException(404, "Obra no encontrada")
        cur.execute(sql.SQL("""
            INSERT INTO {}.work_costs
            (work_id,supplier_id,cost_date,category,concept,quantity,unit,unit_price,payment_status,due_date,invoice_number,notes)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            RETURNING *
        """).format(S), [work_id, body.supplier_id, body.cost_date, body.category, body.concept, body.quantity, body.unit,
                           body.unit_price, body.payment_status, body.due_date, body.invoice_number, body.notes])
        cost = cur.fetchone()

        # A cost assigned to a supplier creates an obligation, but not a cash movement.
        if body.supplier_id and body.payment_status != "anulado":
            cur.execute(sql.SQL("""
                INSERT INTO {}.payables
                (supplier_id,work_id,description,document_number,issue_date,due_date,amount,category,status,notes)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                RETURNING id
            """).format(S), [body.supplier_id, work_id, body.concept, body.invoice_number, body.cost_date, body.due_date,
                               cost["amount"], body.category, "pagado" if body.payment_status=="pagado" else "pendiente", body.notes])
            payable_id = cur.fetchone()["id"]
            cur.execute(sql.SQL("UPDATE {}.work_costs SET payable_id=%s WHERE id=%s").format(S), [payable_id, cost["id"]])
            cost["payable_id"] = payable_id
    return cost


class PayCost(BaseModel):
    account_id: UUID
    payment_date: date = date.today()
    amount: Decimal | None = None
    notes: str | None = None


@router.post("/{work_id}/costs/{cost_id}/pay")
def pay_work_cost(work_id: UUID, cost_id: UUID, body: PayCost):
    with db_cursor() as cur:
        cur.execute(sql.SQL("SELECT * FROM {}.work_costs WHERE id=%s AND work_id=%s").format(S), [cost_id, work_id])
        cost = cur.fetchone()
        if not cost:
            raise HTTPException(404, "Costo no encontrado")
        if cost["payment_status"] == "pagado":
            raise HTTPException(400, "El costo ya figura pagado")
        amount = body.amount or cost["amount"]
        cur.execute(sql.SQL("""
            INSERT INTO {}.financial_movements
            (account_id,work_id,supplier_id,payable_id,type,category,description,amount,movement_date,notes)
            VALUES (%s,%s,%s,%s,'egreso',%s,%s,%s,%s,%s)
            RETURNING *
        """).format(S), [body.account_id, work_id, cost["supplier_id"], cost["payable_id"], cost["category"], cost["concept"], amount, body.payment_date, body.notes])
        movement = cur.fetchone()
        cur.execute(sql.SQL("UPDATE {}.work_costs SET payment_status='pagado', paid_at=%s WHERE id=%s").format(S), [body.payment_date, cost_id])
        if cost["payable_id"]:
            cur.execute(sql.SQL("UPDATE {}.payables SET status='pagado' WHERE id=%s").format(S), [cost["payable_id"]])
    return movement


class InvoiceItemCreate(BaseModel):
    work_item_id: UUID
    amount: Decimal


class InvoiceCreate(BaseModel):
    description: str | None = None
    document_number: str | None = None
    issue_date: date = date.today()
    due_date: date | None = None
    notes: str | None = None
    items: list[InvoiceItemCreate]


@router.post("/{work_id}/invoices")
def create_client_invoice(work_id: UUID, body: InvoiceCreate):
    if not body.items:
        raise HTTPException(400, "Seleccioná al menos un ítem para facturar")

    with db_cursor() as cur:
        cur.execute(sql.SQL("""
            SELECT client_id, requires_certificate, certificate_received
            FROM {}.works WHERE id=%s
        """).format(S), [work_id])
        work = cur.fetchone()
        if not work:
            raise HTTPException(404, "Obra no encontrada")
        if work.get("requires_certificate") and not work.get("certificate_received"):
            raise HTTPException(400, "Esta obra requiere certificado y todavía no figura recibido")

        ids = [x.work_item_id for x in body.items]
        if len(set(ids)) != len(ids):
            raise HTTPException(400, "No se puede repetir un ítem dentro de la misma factura")

        validated = []
        total = Decimal("0")
        for req in body.items:
            if req.amount <= 0:
                raise HTTPException(400, "Los montos a facturar deben ser mayores que cero")
            cur.execute(sql.SQL("""
                SELECT wi.*,
                       (wi.budget_amount * wi.progress_percent / 100.0) AS executed_amount,
                       COALESCE((
                         SELECT SUM(ii.amount)
                         FROM {}.work_invoice_items ii
                         JOIN {}.work_invoices inv ON inv.id=ii.work_invoice_id
                         WHERE ii.work_item_id=wi.id AND inv.status <> 'anulada'
                       ),0) AS billed_amount
                FROM {}.work_items wi
                WHERE wi.id=%s AND wi.work_id=%s
                FOR UPDATE
            """).format(S, S, S), [req.work_item_id, work_id])
            item = cur.fetchone()
            if not item:
                raise HTTPException(400, f"Ítem {req.work_item_id} no pertenece a esta obra")
            if item.get("status") == "cancelado":
                raise HTTPException(400, f"El ítem {item.get('code') or item['id']} está cancelado")

            executed = Decimal(str(item.get("executed_amount") or 0))
            billed = Decimal(str(item.get("billed_amount") or 0))
            available = max(Decimal("0"), executed - billed)
            if req.amount > available:
                raise HTTPException(
                    400,
                    f"{item.get('code') or item['description']}: disponible {available}, solicitado {req.amount}"
                )
            validated.append((item, req.amount, executed))
            total += req.amount

        cur.execute(sql.SQL("""
            INSERT INTO {}.work_invoices
              (work_id,client_id,invoice_number,description,issue_date,due_date,total_amount,status,notes)
            VALUES (%s,%s,%s,%s,%s,%s,%s,'emitida',%s)
            RETURNING *
        """).format(S), [work_id, work["client_id"], body.document_number or None,
                           body.description, body.issue_date, body.due_date, total, body.notes])
        invoice = cur.fetchone()

        for item, amount, executed in validated:
            cur.execute(sql.SQL("""
                INSERT INTO {}.work_invoice_items
                  (work_invoice_id,work_item_id,amount,progress_percent_snapshot,executed_amount_snapshot)
                VALUES (%s,%s,%s,%s,%s)
            """).format(S), [invoice["id"], item["id"], amount,
                               item.get("progress_percent") or 0, executed])

        description = body.description or f"Factura de obra {body.document_number or ''}".strip()
        cur.execute(sql.SQL("""
            INSERT INTO {}.receivables
              (client_id,work_id,description,document_number,issue_date,due_date,amount,status,notes)
            VALUES (%s,%s,%s,%s,%s,%s,%s,'pendiente',%s)
            RETURNING id
        """).format(S), [work["client_id"], work_id, description, body.document_number,
                           body.issue_date, body.due_date, total, body.notes])
        receivable_id = cur.fetchone()["id"]
        cur.execute(sql.SQL("UPDATE {}.work_invoices SET receivable_id=%s WHERE id=%s").format(S),
                    [receivable_id, invoice["id"]])
        invoice["receivable_id"] = receivable_id
        invoice["total_amount"] = total
        return invoice


@router.delete("/{work_id}/invoices/{invoice_id}")
def delete_client_invoice(work_id: UUID, invoice_id: UUID):
    """Permite corregir una factura solo mientras su cuenta por cobrar no tenga cobros."""
    with db_cursor() as cur:
        cur.execute(sql.SQL("SELECT * FROM {}.work_invoices WHERE id=%s AND work_id=%s").format(S),
                    [invoice_id, work_id])
        invoice = cur.fetchone()
        if not invoice:
            raise HTTPException(404, "Factura no encontrada")
        if invoice.get("receivable_id"):
            cur.execute(sql.SQL("""
                SELECT COALESCE(SUM(amount),0) AS total
                FROM {}.financial_movements
                WHERE receivable_id=%s AND type='ingreso'
            """).format(S), [invoice["receivable_id"]])
            if Decimal(str(cur.fetchone()["total"] or 0)) > 0:
                raise HTTPException(400, "No se puede eliminar una factura que ya tiene cobros registrados")
        receivable_id = invoice.get("receivable_id")
        cur.execute(sql.SQL("DELETE FROM {}.work_invoices WHERE id=%s").format(S), [invoice_id])
        if receivable_id:
            cur.execute(sql.SQL("DELETE FROM {}.receivables WHERE id=%s").format(S), [receivable_id])
    return {"ok": True}
