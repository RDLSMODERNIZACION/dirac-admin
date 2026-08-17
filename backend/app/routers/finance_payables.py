from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from psycopg import sql

from ..core.config import get_settings
from ..core.db import db_cursor
from ..core.security import require_api_key

router = APIRouter(
    prefix="/api/finance-payables",
    tags=["finance-payables"],
    dependencies=[Depends(require_api_key)],
)

settings = get_settings()
S = sql.Identifier(settings.db_schema)


def D(v):
    return Decimal(str(v or 0))


def ensure_schema(cur):
    cur.execute(sql.SQL("""
        ALTER TABLE {}.payables
        ADD COLUMN IF NOT EXISTS work_item_id uuid NULL
    """).format(S))

    cur.execute(sql.SQL("""
        ALTER TABLE {}.work_costs
        ADD COLUMN IF NOT EXISTS work_item_id uuid NULL
    """).format(S))

    # FK opcional. Si ya existe no hacemos nada.
    cur.execute(sql.SQL("""
        DO $$
        BEGIN
          IF NOT EXISTS (
            SELECT 1
            FROM pg_constraint
            WHERE conname='payables_work_item_id_fkey'
          ) THEN
            ALTER TABLE {}.payables
            ADD CONSTRAINT payables_work_item_id_fkey
            FOREIGN KEY (work_item_id)
            REFERENCES {}.work_items(id)
            ON DELETE SET NULL;
          END IF;
        END $$;
    """).format(S, S))


class PayableCreate(BaseModel):
    supplier_id: UUID
    work_id: UUID | None = None
    work_item_id: UUID | None = None
    description: str
    document_number: str | None = None
    issue_date: str | None = None
    due_date: str | None = None
    amount: Decimal
    category: str = "otros"
    quantity: Decimal = Decimal("1")
    unit: str | None = None
    unit_price: Decimal | None = None
    notes: str | None = None


class PaymentPayload(BaseModel):
    account_id: UUID
    amount: Decimal
    payment_date: str
    notes: str | None = None


def _paid_amount(cur, payable_id):
    cur.execute(sql.SQL("""
        SELECT COALESCE(SUM(amount),0) AS paid
        FROM {}.financial_movements
        WHERE payable_id=%s AND type='egreso'
    """).format(S), [payable_id])
    return D(cur.fetchone()["paid"])


@router.get("")
def list_payables():
    with db_cursor() as cur:
        ensure_schema(cur)
        cur.execute(sql.SQL("""
            SELECT
                p.*,
                s.name AS supplier_name,
                w.name AS work_name,
                wi.description AS work_item_description,
                COALESCE((
                    SELECT SUM(fm.amount)
                    FROM {}.financial_movements fm
                    WHERE fm.payable_id=p.id AND fm.type='egreso'
                ),0) AS paid_amount
            FROM {}.payables p
            LEFT JOIN {}.suppliers s ON s.id=p.supplier_id
            LEFT JOIN {}.works w ON w.id=p.work_id
            LEFT JOIN {}.work_items wi ON wi.id=p.work_item_id
            WHERE LOWER(COALESCE(p.status,'')) <> 'anulado'
            ORDER BY
                CASE WHEN LOWER(COALESCE(p.status,''))='pagado' THEN 1 ELSE 0 END,
                p.due_date NULLS LAST,
                p.issue_date DESC NULLS LAST
        """).format(S,S,S,S,S))
        rows=cur.fetchall()

        for r in rows:
            total=D(r["amount"])
            paid=D(r["paid_amount"])
            r["pending_amount"]=max(D(0), total-paid)
            if paid >= total and total > 0:
                r["effective_status"]="pagado"
            elif paid > 0:
                r["effective_status"]="parcial"
            else:
                r["effective_status"]="pendiente"
        return rows


@router.post("")
def create_payable(body: PayableCreate):
    if not body.description.strip():
        raise HTTPException(400, "Ingresá el concepto")
    if body.amount <= 0:
        raise HTTPException(400, "El monto debe ser mayor a cero")

    with db_cursor() as cur:
        ensure_schema(cur)

        cur.execute(sql.SQL("SELECT id FROM {}.suppliers WHERE id=%s").format(S), [body.supplier_id])
        if not cur.fetchone():
            raise HTTPException(404, "Proveedor no encontrado")

        if body.work_id:
            cur.execute(sql.SQL("SELECT id FROM {}.works WHERE id=%s").format(S), [body.work_id])
            if not cur.fetchone():
                raise HTTPException(404, "Obra no encontrada")

        if body.work_item_id:
            if not body.work_id:
                raise HTTPException(400, "Para asignar un ítem primero seleccioná una obra")
            cur.execute(sql.SQL("""
                SELECT id
                FROM {}.work_items
                WHERE id=%s AND work_id=%s
            """).format(S), [body.work_item_id, body.work_id])
            if not cur.fetchone():
                raise HTTPException(400, "El ítem seleccionado no pertenece a esa obra")

        cur.execute(sql.SQL("""
            INSERT INTO {}.payables
            (
              supplier_id,work_id,work_item_id,description,document_number,
              issue_date,due_date,amount,category,status,notes
            )
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'pendiente',%s)
            RETURNING *
        """).format(S), [
            body.supplier_id,body.work_id,body.work_item_id,body.description.strip(),
            body.document_number,body.issue_date,body.due_date,body.amount,
            body.category,body.notes
        ])
        payable = cur.fetchone()

        if body.work_id:
            unit_price = body.unit_price if body.unit_price is not None else body.amount
            quantity = body.quantity if body.quantity and body.quantity > 0 else Decimal("1")
            cur.execute(sql.SQL("""
                INSERT INTO {}.work_costs
                (
                  work_id,work_item_id,supplier_id,cost_date,category,concept,
                  quantity,unit,unit_price,payment_status,due_date,
                  invoice_number,payable_id,notes
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'pendiente',%s,%s,%s,%s)
                RETURNING id
            """).format(S), [
                body.work_id,body.work_item_id,body.supplier_id,body.issue_date,
                body.category,body.description.strip(),quantity,body.unit,unit_price,
                body.due_date,body.document_number,payable['id'],body.notes
            ])

        return payable


@router.post("/{payable_id}/payments")
def pay_payable(payable_id: UUID, body: PaymentPayload):
    if body.amount <= 0:
        raise HTTPException(400, "El monto debe ser mayor a cero")

    with db_cursor() as cur:
        ensure_schema(cur)

        cur.execute(
            sql.SQL("SELECT * FROM {}.payables WHERE id=%s FOR UPDATE").format(S),
            [payable_id],
        )
        payable=cur.fetchone()
        if not payable:
            raise HTTPException(404, "Cuenta por pagar no encontrada")

        cur.execute(
            sql.SQL("SELECT * FROM {}.accounts WHERE id=%s AND is_active IS NOT FALSE").format(S),
            [body.account_id],
        )
        account=cur.fetchone()
        if not account:
            raise HTTPException(404, "Cuenta no encontrada o inactiva")

        total=D(payable["amount"])
        already=_paid_amount(cur,payable_id)
        pending=max(D(0),total-already)

        if pending <= 0:
            raise HTTPException(400, "Esta cuenta por pagar ya está pagada")
        if body.amount > pending:
            raise HTTPException(400, f"El pago supera el saldo pendiente ({pending})")

        cur.execute(sql.SQL("""
            INSERT INTO {}.financial_movements
            (
              account_id,work_id,supplier_id,payable_id,type,category,
              description,amount,movement_date,notes
            )
            VALUES (%s,%s,%s,%s,'egreso','pago_proveedor',%s,%s,%s,%s)
            RETURNING *
        """).format(S), [
            body.account_id,
            payable.get("work_id"),
            payable.get("supplier_id"),
            payable_id,
            f"Pago - {payable.get('description') or 'cuenta por pagar'}",
            body.amount,
            body.payment_date,
            body.notes,
        ])
        movement=cur.fetchone()

        new_paid=already+D(body.amount)
        status="pagado" if new_paid >= total else "parcial"
        cur.execute(
            sql.SQL("UPDATE {}.payables SET status=%s WHERE id=%s").format(S),
            [status,payable_id],
        )

        cur.execute(
            sql.SQL("""
                UPDATE {}.work_costs
                SET payment_status=%s,
                    paid_at=CASE WHEN %s='pagado' THEN %s::date ELSE paid_at END
                WHERE payable_id=%s
            """).format(S),
            [status,status,body.payment_date,payable_id],
        )

        return {
            "ok":True,
            "movement":movement,
            "payable_id":str(payable_id),
            "work_id":str(payable["work_id"]) if payable.get("work_id") else None,
            "status":status,
            "paid_amount":new_paid,
            "pending_amount":max(D(0),total-new_paid),
        }
