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
                   GREATEST(0, wi.budget_amount - COALESCE(b.billed_amount,0)) AS available_to_invoice
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
        cur.execute(sql.SQL("""
            ALTER TABLE {}.work_costs
            ADD COLUMN IF NOT EXISTS work_item_id uuid NULL
        """).format(S))

        costs = _rows(cur, """
            SELECT wc.*, s.name AS supplier_name,
                   wi.description AS work_item_description,
                   wi.code AS work_item_code
            FROM {}.work_costs wc
            LEFT JOIN {}.suppliers s ON s.id=wc.supplier_id
            LEFT JOIN {}.work_items wi ON wi.id=wc.work_item_id
            WHERE wc.work_id=%s ORDER BY wc.cost_date DESC, wc.created_at DESC
        """, [work_id])
        certs = _rows(cur, "SELECT * FROM {}.work_certificates WHERE work_id=%s ORDER BY period_to DESC NULLS LAST, created_at DESC", [work_id])
        docs = _rows(cur, "SELECT * FROM {}.work_documents WHERE work_id=%s ORDER BY document_date DESC, created_at DESC", [work_id])
        checklist = _rows(cur, "SELECT * FROM {}.work_checklist WHERE work_id=%s ORDER BY created_at", [work_id])
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

        # Agrega el detalle de cobros reales a cada factura de obra.
        for inv in invoices:
            receivable_id = inv.get("receivable_id")
            payments = []
            if receivable_id:
                payments = _rows(cur, """
                    SELECT fm.*, a.name AS account_name, a.currency AS account_currency
                    FROM {}.financial_movements fm
                    LEFT JOIN {}.accounts a ON a.id=fm.account_id
                    WHERE fm.receivable_id=%s AND fm.type='ingreso'
                    ORDER BY fm.movement_date DESC, fm.created_at DESC
                """, [receivable_id])
            paid_amount = sum((Decimal(str(x.get("amount") or 0)) for x in payments), Decimal("0"))
            total_amount = Decimal(str(inv.get("total_amount") or 0))
            inv["payments"] = payments
            inv["paid_amount"] = paid_amount
            inv["pending_amount"] = max(Decimal("0"), total_amount - paid_amount)

        pay = _rows(cur, """
            SELECT p.*, s.name AS supplier_name
            FROM {}.payables p
            LEFT JOIN {}.suppliers s ON s.id=p.supplier_id
            WHERE p.work_id=%s ORDER BY p.due_date DESC NULLS LAST, p.created_at DESC
        """, [work_id])

        real_cost = sum((Decimal(str(x.get("amount") or 0)) for x in costs if x.get("payment_status") != "anulado"), Decimal("0"))
        invoiced = sum((Decimal(str(x.get("total_amount") or 0)) for x in invoices if x.get("status") != "anulada"), Decimal("0"))
        executed_amount = sum((Decimal(str(x.get("executed_amount") or 0)) for x in items if x.get("status") != "cancelado"), Decimal("0"))
        net_billed = invoiced
        advanced_invoicing = max(Decimal("0"), invoiced - executed_amount)
        executed_unbilled = max(Decimal("0"), executed_amount - invoiced)
        available_to_invoice = Decimal("0")
        collected = Decimal("0")
        cur.execute(sql.SQL("""
            SELECT COALESCE(SUM(amount),0) AS total
            FROM {}.financial_movements
            WHERE work_id=%s AND type='ingreso'
        """).format(S), [work_id])
        collected = Decimal(str(cur.fetchone()["total"] or 0))
        collected_ahead_execution = max(Decimal("0"), collected - executed_amount)
        paid = Decimal("0")
        cur.execute(sql.SQL("""
            SELECT COALESCE(SUM(amount),0) AS total
            FROM {}.financial_movements
            WHERE work_id=%s AND type='egreso'
        """).format(S), [work_id])
        paid = Decimal(str(cur.fetchone()["total"] or 0))
        contract = Decimal(str(work.get("contract_amount") or 0))
        available_to_invoice = max(Decimal("0"), contract - invoiced)

    return {
        "work": work,
        "metrics": {
            "real_cost": real_cost,
            "projected_result": contract - real_cost,
            "executed_amount": executed_amount,
            "invoiced": invoiced,
            "available_to_invoice": available_to_invoice,
            "net_billed": net_billed,
            "advanced_invoicing": advanced_invoicing,
            "executed_unbilled": executed_unbilled,
            "collected": collected,
            "collected_ahead_execution": collected_ahead_execution,
            "pending_collection": max(Decimal("0"), invoiced - collected),
            "paid": paid,
        },
        "items": items,
        "budget_items": budget,
        "costs": costs,
        "certificates": certs,
        "documents": docs,
        "checklist": checklist,
        "receivables": recv,
        "invoices": invoices,
        "payables": pay,
    }


CHECKLIST_TYPES = {
    "presupuesto": "Presupuesto presentado",
    "nota": "Nota presentada",
    "memoria_descriptiva": "Memoria descriptiva",
    "contrato": "Contrato",
    "certificacion": "Certificación",
    "factura": "Factura",
    "cobro": "Cobro",
}


class WorkChecklistUpdate(BaseModel):
    completed: bool = True
    completed_date: date | None = None
    notes: str | None = None


@router.put("/{work_id}/checklist/{item_type}")
def update_work_checklist(work_id: UUID, item_type: str, body: WorkChecklistUpdate):
    if item_type not in CHECKLIST_TYPES:
        raise HTTPException(400, "Tipo de checklist inválido")

    completed_date = body.completed_date
    if body.completed and completed_date is None:
        completed_date = date.today()
    if not body.completed:
        completed_date = None

    with db_cursor() as cur:
        cur.execute(sql.SQL("SELECT id FROM {}.works WHERE id=%s").format(S), [work_id])
        if not cur.fetchone():
            raise HTTPException(404, "Obra no encontrada")

        cur.execute(sql.SQL("""
            INSERT INTO {}.work_checklist
              (work_id,item_type,completed,completed_date,notes)
            VALUES (%s,%s,%s,%s,%s)
            ON CONFLICT (work_id,item_type)
            DO UPDATE SET
              completed=EXCLUDED.completed,
              completed_date=EXCLUDED.completed_date,
              notes=EXCLUDED.notes,
              updated_at=now()
            RETURNING *
        """).format(S), [work_id, item_type, body.completed, completed_date, body.notes])
        return cur.fetchone()


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
    vat_rate: Decimal = Decimal("21")
    amount: Decimal
    items: list[InvoiceItemCreate] = []


@router.post("/{work_id}/invoices")
def create_client_invoice(work_id: UUID, body: InvoiceCreate):
    if body.amount <= 0:
        raise HTTPException(400, "El monto de la factura debe ser mayor a cero")
    if body.vat_rate < 0 or body.vat_rate > 100:
        raise HTTPException(400, "La alícuota de IVA no es válida")

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

        invoice_total = body.amount.quantize(Decimal("0.01"))
        divisor = Decimal("1") + (body.vat_rate / Decimal("100"))
        net_amount = (
            (invoice_total / divisor).quantize(Decimal("0.01"))
            if divisor > 0
            else invoice_total
        )
        vat_amount = invoice_total - net_amount

        cur.execute(sql.SQL("""
            INSERT INTO {}.work_invoices
              (work_id,client_id,invoice_number,description,issue_date,due_date,total_amount,status,notes)
            VALUES (%s,%s,%s,%s,%s,%s,%s,'emitida',%s)
            RETURNING *
        """).format(S), [
            work_id,
            work["client_id"],
            body.document_number or None,
            body.description,
            body.issue_date,
            body.due_date,
            invoice_total,
            body.notes,
        ])
        invoice = cur.fetchone()

        description = body.description or f"Factura de obra {body.document_number or ''}".strip()
        cur.execute(sql.SQL("""
            INSERT INTO {}.receivables
              (client_id,work_id,description,document_number,issue_date,due_date,amount,status,notes)
            VALUES (%s,%s,%s,%s,%s,%s,%s,'pendiente',%s)
            RETURNING id
        """).format(S), [
            work["client_id"],
            work_id,
            description,
            body.document_number,
            body.issue_date,
            body.due_date,
            invoice_total,
            body.notes,
        ])
        receivable_id = cur.fetchone()["id"]
        cur.execute(
            sql.SQL("UPDATE {}.work_invoices SET receivable_id=%s WHERE id=%s").format(S),
            [receivable_id, invoice["id"]],
        )

        invoice["receivable_id"] = receivable_id
        invoice["net_amount"] = net_amount
        invoice["vat_rate"] = body.vat_rate
        invoice["vat_amount"] = vat_amount
        invoice["total_amount"] = invoice_total
        return invoice


class WorkInvoiceUpdate(BaseModel):
    document_number: str | None = None
    description: str | None = None
    issue_date: date | None = None
    due_date: date | None = None
    notes: str | None = None
    amount: Decimal | None = None
    vat_rate: Decimal | None = None


@router.patch("/{work_id}/invoices/{invoice_id}")
def update_client_invoice(work_id: UUID, invoice_id: UUID, body: WorkInvoiceUpdate):
    with db_cursor() as cur:
        cur.execute(sql.SQL("""
            SELECT * FROM {}.work_invoices
            WHERE id=%s AND work_id=%s
            FOR UPDATE
        """).format(S), [invoice_id, work_id])
        invoice = cur.fetchone()
        if not invoice:
            raise HTTPException(404, "Factura no encontrada")

        new_amount = Decimal(str(body.amount)) if body.amount is not None else Decimal(str(invoice.get("total_amount") or 0))
        if new_amount <= 0:
            raise HTTPException(400, "El monto de la factura debe ser mayor a cero")

        receivable_id = invoice.get("receivable_id")
        paid = Decimal("0")
        if receivable_id:
            cur.execute(sql.SQL("""
                SELECT COALESCE(SUM(amount),0) AS paid
                FROM {}.financial_movements
                WHERE receivable_id=%s AND type='ingreso'
            """).format(S), [receivable_id])
            paid = Decimal(str(cur.fetchone()["paid"] or 0))
            if new_amount < paid:
                raise HTTPException(400, f"El monto no puede ser menor a lo ya cobrado ({paid})")

        document_number = body.document_number if body.document_number is not None else invoice.get("invoice_number")
        description = body.description if body.description is not None else invoice.get("description")
        issue_date = body.issue_date or invoice.get("issue_date")
        due_date = body.due_date
        notes = body.notes if body.notes is not None else invoice.get("notes")

        cur.execute(sql.SQL("""
            UPDATE {}.work_invoices
            SET invoice_number=%s,
                description=%s,
                issue_date=%s,
                due_date=%s,
                total_amount=%s,
                notes=%s
            WHERE id=%s
            RETURNING *
        """).format(S), [
            document_number or None,
            description,
            issue_date,
            due_date,
            new_amount,
            notes,
            invoice_id,
        ])
        updated = cur.fetchone()

        if receivable_id:
            receivable_description = description or f"Factura de obra {document_number or ''}".strip()
            new_status = "cobrado" if paid >= new_amount else ("parcial" if paid > 0 else "pendiente")
            cur.execute(sql.SQL("""
                UPDATE {}.receivables
                SET document_number=%s,
                    description=%s,
                    issue_date=%s,
                    due_date=%s,
                    amount=%s,
                    status=%s,
                    notes=%s
                WHERE id=%s AND work_id=%s
            """).format(S), [
                document_number or None,
                receivable_description,
                issue_date,
                due_date,
                new_amount,
                new_status,
                notes,
                receivable_id,
                work_id,
            ])

        return updated


class WorkPaymentCreate(BaseModel):
    account_id: UUID
    amount: Decimal
    payment_date: date = date.today()
    notes: str | None = None


@router.post("/{work_id}/receivables/{receivable_id}/payments")
def register_work_payment(work_id: UUID, receivable_id: UUID, body: WorkPaymentCreate):
    """Registra un cobro parcial o total de una factura de obra y lo imputa a una cuenta."""
    if body.amount <= 0:
        raise HTTPException(400, "El monto debe ser mayor a cero")

    with db_cursor() as cur:
        cur.execute(sql.SQL("""
            SELECT r.*, w.client_id, w.name AS work_name
            FROM {}.receivables r
            JOIN {}.works w ON w.id=r.work_id
            WHERE r.id=%s AND r.work_id=%s
            FOR UPDATE
        """).format(S, S), [receivable_id, work_id])
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
        already = Decimal(str(cur.fetchone()["paid"] or 0))
        total = Decimal(str(r["amount"] or 0))
        pending = max(Decimal("0"), total - already)
        if body.amount > pending:
            raise HTTPException(400, f"El cobro supera el saldo pendiente ({pending})")

        cur.execute(sql.SQL("""
            INSERT INTO {}.financial_movements
              (account_id,work_id,client_id,receivable_id,type,category,description,amount,movement_date,notes)
            VALUES (%s,%s,%s,%s,'ingreso','cobro_obra',%s,%s,%s,%s)
            RETURNING *
        """).format(S), [
            body.account_id, work_id, r["client_id"], receivable_id,
            f"Cobro {r.get('document_number') or r['description']}",
            body.amount, body.payment_date, body.notes
        ])
        movement = cur.fetchone()

        new_paid = already + body.amount
        new_status = "cobrado" if new_paid >= total else "parcial"
        cur.execute(sql.SQL("UPDATE {}.receivables SET status=%s WHERE id=%s").format(S),
                    [new_status, receivable_id])

    return {
        "movement": movement,
        "paid_total": new_paid,
        "pending": max(Decimal("0"), total - new_paid),
        "status": new_status,
    }


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
