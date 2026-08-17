from calendar import monthrange
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from psycopg import sql

from ..core.config import get_settings
from ..core.db import db_cursor
from ..core.security import require_api_key

router = APIRouter(prefix="/api/debts", tags=["debts"], dependencies=[Depends(require_api_key)])
settings = get_settings()
S = sql.Identifier(settings.db_schema)

def money(v):
    return Decimal(str(v or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def add_months(d: date, months: int):
    idx = d.year*12 + (d.month-1) + months
    y, m = idx//12, idx%12+1
    return date(y,m,min(d.day,monthrange(y,m)[1]))

class DebtCreate(BaseModel):
    creditor: str
    debt_type: str
    description: str | None = None
    original_amount: Decimal
    start_date: date = date.today()
    first_due_date: date | None = None
    total_installments: int | None = None
    installment_amount: Decimal | None = None
    minimum_payment: Decimal | None = None
    notes: str | None = None
    register_inflow: bool = False
    account_id: UUID | None = None

@router.get("")
def list_debts():
    with db_cursor() as cur:
        cur.execute(sql.SQL("""
          SELECT d.*,
                 COALESCE(p.paid_amount,0) AS paid_amount,
                 GREATEST(0,d.original_amount-COALESCE(p.paid_amount,0)) AS balance,
                 ni.next_due_date, ni.next_amount
          FROM {}.debts d
          LEFT JOIN LATERAL (SELECT COALESCE(SUM(amount),0) paid_amount FROM {}.debt_payments dp WHERE dp.debt_id=d.id) p ON true
          LEFT JOIN LATERAL (
            SELECT due_date next_due_date, GREATEST(0,amount-paid_amount) next_amount
            FROM {}.debt_installments di
            WHERE di.debt_id=d.id AND di.status IN ('pendiente','parcial')
            ORDER BY due_date, installment_number LIMIT 1
          ) ni ON true
          ORDER BY CASE WHEN d.status='activa' THEN 0 ELSE 1 END, ni.next_due_date NULLS LAST, d.created_at DESC
        """).format(S,S,S))
        return cur.fetchall()

@router.get("/summary")
def summary():
    with db_cursor() as cur:
        cur.execute(sql.SQL("""
          SELECT
            COALESCE(SUM(GREATEST(0,d.original_amount-COALESCE(p.paid,0))) FILTER (WHERE d.status='activa'),0) total_balance,
            COALESCE(SUM(GREATEST(0,d.original_amount-COALESCE(p.paid,0))) FILTER (WHERE d.status='activa' AND d.debt_type='tarjeta_credito'),0) credit_cards,
            COALESCE(SUM(GREATEST(0,d.original_amount-COALESCE(p.paid,0))) FILTER (WHERE d.status='activa' AND d.debt_type='deuda_socio'),0) partners,
            COALESCE(SUM(GREATEST(0,d.original_amount-COALESCE(p.paid,0))) FILTER (WHERE d.status='activa' AND d.debt_type='prestamo'),0) loans
          FROM {}.debts d
          LEFT JOIN LATERAL (SELECT COALESCE(SUM(amount),0) paid FROM {}.debt_payments dp WHERE dp.debt_id=d.id) p ON true
        """).format(S,S))
        row=cur.fetchone()
        cur.execute(sql.SQL("""SELECT COALESCE(SUM(GREATEST(0,amount-paid_amount)),0) next_30_days FROM {}.debt_installments
                               WHERE status IN ('pendiente','parcial') AND due_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '30 days'""").format(S))
        row['next_30_days']=cur.fetchone()['next_30_days']
        return row

@router.post("")
def create_debt(body: DebtCreate):
    if body.original_amount <= 0: raise HTTPException(400,"El monto original debe ser mayor a cero")
    if body.register_inflow and not body.account_id: raise HTTPException(400,"Seleccioná la cuenta donde ingresó el dinero")
    n=body.total_installments or 1
    if n<1: raise HTTPException(400,"La cantidad de cuotas debe ser al menos 1")
    first=body.first_due_date or body.start_date
    installment=money(body.installment_amount or (body.original_amount/n))
    with db_cursor() as cur:
        cur.execute(sql.SQL("""INSERT INTO {}.debts
          (creditor,debt_type,description,original_amount,start_date,first_due_date,total_installments,installment_amount,minimum_payment,status,notes,origin_account_id)
          VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,'activa',%s,%s) RETURNING *""").format(S),
          [body.creditor.strip(),body.debt_type,body.description,money(body.original_amount),body.start_date,first,n,installment,
           money(body.minimum_payment) if body.minimum_payment is not None else None,body.notes,body.account_id if body.register_inflow else None])
        debt=cur.fetchone(); remaining=money(body.original_amount)
        for i in range(1,n+1):
            amount=installment if i<n else remaining
            amount=min(remaining,amount)
            cur.execute(sql.SQL("INSERT INTO {}.debt_installments (debt_id,installment_number,due_date,amount,status) VALUES (%s,%s,%s,%s,'pendiente')").format(S),
                        [debt['id'],i,add_months(first,i-1),amount])
            remaining=max(Decimal('0'),remaining-amount)
        if body.register_inflow:
            cur.execute(sql.SQL("""INSERT INTO {}.financial_movements
              (account_id,type,category,description,amount,movement_date,notes)
              VALUES (%s,'ingreso','financiamiento',%s,%s,%s,%s) RETURNING id""").format(S),
              [body.account_id,f"Financiamiento recibido - {body.creditor}",money(body.original_amount),body.start_date,body.notes])
            mid=cur.fetchone()['id']
            cur.execute(sql.SQL("UPDATE {}.debts SET origin_financial_movement_id=%s WHERE id=%s").format(S),[mid,debt['id']])
        return debt


class DebtUpdate(BaseModel):
    creditor: str
    debt_type: str
    description: str | None = None
    original_amount: Decimal
    start_date: date
    first_due_date: date | None = None
    total_installments: int | None = None
    installment_amount: Decimal | None = None
    minimum_payment: Decimal | None = None
    notes: str | None = None

@router.patch("/{debt_id}")
def update_debt(debt_id: UUID, body: DebtUpdate):
    if body.original_amount <= 0:
        raise HTTPException(400, "El monto original debe ser mayor a cero")

    n = body.total_installments or 1
    if n < 1:
        raise HTTPException(400, "La cantidad de cuotas debe ser al menos 1")

    first = body.first_due_date or body.start_date
    installment = money(body.installment_amount or (body.original_amount / n))

    with db_cursor() as cur:
        cur.execute(
            sql.SQL("""
                SELECT d.*,
                       COALESCE((SELECT SUM(amount) FROM {}.debt_payments dp WHERE dp.debt_id=d.id),0) AS paid
                FROM {}.debts d
                WHERE d.id=%s
                FOR UPDATE
            """).format(S, S),
            [debt_id],
        )
        debt = cur.fetchone()
        if not debt:
            raise HTTPException(404, "Deuda no encontrada")

        paid = money(debt["paid"])
        if body.original_amount < paid:
            raise HTTPException(400, f"El monto original no puede ser menor que lo ya pagado ({paid})")

        schedule_changed = (
            money(body.original_amount) != money(debt["original_amount"])
            or body.start_date != debt["start_date"]
            or first != debt.get("first_due_date")
            or n != int(debt.get("total_installments") or 1)
            or installment != money(debt.get("installment_amount"))
        )

        if paid > 0 and schedule_changed:
            raise HTTPException(
                400,
                "Esta deuda ya tiene pagos. Podés editar acreedor, tipo, descripción y notas, "
                "pero no monto, fechas ni cuotas."
            )

        cur.execute(
            sql.SQL("""
                UPDATE {}.debts
                SET creditor=%s,
                    debt_type=%s,
                    description=%s,
                    original_amount=%s,
                    start_date=%s,
                    first_due_date=%s,
                    total_installments=%s,
                    installment_amount=%s,
                    minimum_payment=%s,
                    notes=%s,
                    updated_at=now()
                WHERE id=%s
                RETURNING *
            """).format(S),
            [
                body.creditor.strip(),
                body.debt_type,
                body.description,
                money(body.original_amount),
                body.start_date,
                first,
                n,
                installment,
                money(body.minimum_payment) if body.minimum_payment is not None else None,
                body.notes,
                debt_id,
            ],
        )
        updated = cur.fetchone()

        if paid <= 0 and schedule_changed:
            cur.execute(sql.SQL("DELETE FROM {}.debt_installments WHERE debt_id=%s").format(S), [debt_id])
            remaining = money(body.original_amount)
            for i in range(1, n + 1):
                amount = installment if i < n else remaining
                amount = min(remaining, amount)
                cur.execute(
                    sql.SQL("""
                        INSERT INTO {}.debt_installments
                        (debt_id,installment_number,due_date,amount,status)
                        VALUES (%s,%s,%s,%s,'pendiente')
                    """).format(S),
                    [debt_id, i, add_months(first, i - 1), amount],
                )
                remaining = max(Decimal("0"), remaining - amount)

        return updated

class DebtPaymentCreate(BaseModel):
    account_id: UUID
    amount: Decimal
    payment_date: date = date.today()
    notes: str | None = None

@router.post("/{debt_id}/payments")
def pay_debt(debt_id: UUID, body: DebtPaymentCreate):
    if body.amount<=0: raise HTTPException(400,"El monto debe ser mayor a cero")
    with db_cursor() as cur:
        cur.execute(sql.SQL("""SELECT d.*,COALESCE((SELECT SUM(amount) FROM {}.debt_payments dp WHERE dp.debt_id=d.id),0) paid
                               FROM {}.debts d WHERE d.id=%s FOR UPDATE""").format(S,S),[debt_id])
        debt=cur.fetchone()
        if not debt: raise HTTPException(404,"Deuda no encontrada")
        balance=max(Decimal('0'),money(debt['original_amount'])-money(debt['paid']))
        if body.amount>balance: raise HTTPException(400,f"El pago supera el saldo pendiente ({balance})")
        cur.execute(sql.SQL("""INSERT INTO {}.financial_movements
          (account_id,type,category,description,amount,movement_date,notes)
          VALUES (%s,'egreso','pago_deuda',%s,%s,%s,%s) RETURNING *""").format(S),
          [body.account_id,f"Pago deuda - {debt['creditor']}",money(body.amount),body.payment_date,body.notes])
        movement=cur.fetchone()
        cur.execute(sql.SQL("""INSERT INTO {}.debt_payments (debt_id,account_id,payment_date,amount,financial_movement_id,notes)
                               VALUES (%s,%s,%s,%s,%s,%s) RETURNING *""").format(S),
                    [debt_id,body.account_id,body.payment_date,money(body.amount),movement['id'],body.notes])
        payment=cur.fetchone(); left=money(body.amount)
        cur.execute(sql.SQL("SELECT * FROM {}.debt_installments WHERE debt_id=%s AND status IN ('pendiente','parcial') ORDER BY due_date,installment_number FOR UPDATE").format(S),[debt_id])
        for inst in cur.fetchall():
            if left<=0: break
            pending=max(Decimal('0'),money(inst['amount'])-money(inst['paid_amount']))
            applied=min(left,pending); new_paid=money(inst['paid_amount'])+applied
            status='pagado' if new_paid>=money(inst['amount']) else 'parcial'
            cur.execute(sql.SQL("UPDATE {}.debt_installments SET paid_amount=%s,status=%s WHERE id=%s").format(S),[new_paid,status,inst['id']])
            left-=applied
        new_balance=max(Decimal('0'),balance-money(body.amount))
        if new_balance<=0:
            cur.execute(sql.SQL("UPDATE {}.debts SET status='cancelada',updated_at=now() WHERE id=%s").format(S),[debt_id])
        return {'payment':payment,'movement':movement,'balance':new_balance}

@router.delete("/{debt_id}")
def delete_debt(debt_id: UUID):
    with db_cursor() as cur:
        cur.execute(sql.SQL("SELECT * FROM {}.debts WHERE id=%s FOR UPDATE").format(S),[debt_id]); debt=cur.fetchone()
        if not debt: raise HTTPException(404,"Deuda no encontrada")
        cur.execute(sql.SQL("SELECT COUNT(*) n FROM {}.debt_payments WHERE debt_id=%s").format(S),[debt_id])
        if cur.fetchone()['n']: raise HTTPException(400,"No se puede eliminar una deuda que ya tiene pagos")
        if debt.get('origin_financial_movement_id'):
            cur.execute(sql.SQL("DELETE FROM {}.financial_movements WHERE id=%s").format(S),[debt['origin_financial_movement_id']])
        cur.execute(sql.SQL("DELETE FROM {}.debts WHERE id=%s").format(S),[debt_id])
    return {'ok':True}
