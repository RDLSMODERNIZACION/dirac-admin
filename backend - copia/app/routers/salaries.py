from calendar import monthrange
from datetime import date
from decimal import Decimal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from psycopg import sql

from ..core.config import get_settings
from ..core.db import db_cursor
from ..core.security import require_api_key

router = APIRouter(prefix="/api/salaries", tags=["salaries"], dependencies=[Depends(require_api_key)])
settings = get_settings()
S = sql.Identifier(settings.db_schema)


def _money(v) -> Decimal:
    return Decimal(str(v or 0))


def _month_start(d: date) -> date:
    return date(d.year, d.month, 1)


def _add_months(d: date, months: int) -> date:
    idx = d.year * 12 + d.month - 1 + months
    return date(idx // 12, idx % 12 + 1, 1)


def _due_date(month: date, due_day: int) -> date:
    return date(month.year, month.month, min(max(1, int(due_day or 5)), monthrange(month.year, month.month)[1]))


def _ensure_periods(cur, from_month: date, to_month: date):
    last_day = date(to_month.year, to_month.month, monthrange(to_month.year, to_month.month)[1])
    cur.execute(sql.SQL("""
      SELECT * FROM {}.salary_employees
      WHERE start_date <= %s AND (end_date IS NULL OR end_date >= %s)
      ORDER BY name
    """).format(S), [last_day, from_month])
    employees = cur.fetchall()
    for e in employees:
        current = max(from_month, _month_start(e["start_date"]))
        last = to_month if not e.get("end_date") else min(to_month, _month_start(e["end_date"]))
        while current <= last:
            cur.execute(sql.SQL("""
              INSERT INTO {}.salary_periods(employee_id,period_month,due_date,base_amount,adjustments)
              VALUES (%s,%s,%s,%s,0)
              ON CONFLICT (employee_id,period_month) DO NOTHING
            """).format(S), [e["id"], current, _due_date(current, e["due_day"]), e["monthly_salary"]])
            current = _add_months(current, 1)


class EmployeeCreate(BaseModel):
    name: str
    role: str | None = None
    monthly_salary: Decimal
    due_day: int = 5
    start_date: date = date.today()
    end_date: date | None = None
    notes: str | None = None


@router.get("/employees")
def list_employees():
    with db_cursor() as cur:
        cur.execute(sql.SQL("SELECT * FROM {}.salary_employees ORDER BY is_active DESC,name").format(S))
        return cur.fetchall()


@router.post("/employees")
def create_employee(body: EmployeeCreate):
    if not body.name.strip():
        raise HTTPException(400, "Ingresá el nombre")
    if body.monthly_salary < 0:
        raise HTTPException(400, "El sueldo no puede ser negativo")
    with db_cursor() as cur:
        cur.execute(sql.SQL("""
          INSERT INTO {}.salary_employees(name,role,monthly_salary,due_day,start_date,end_date,is_active,notes)
          VALUES (%s,%s,%s,%s,%s,%s,true,%s) RETURNING *
        """).format(S), [body.name.strip(), body.role, body.monthly_salary, body.due_day, body.start_date, body.end_date, body.notes])
        return cur.fetchone()


@router.get("/periods")
def list_periods(months_back: int = 12, months_forward: int = 12):
    today = date.today()
    from_month = _add_months(_month_start(today), -months_back)
    to_month = _add_months(_month_start(today), months_forward)
    with db_cursor() as cur:
        _ensure_periods(cur, from_month, to_month)
        cur.execute(sql.SQL("""
          SELECT sp.*,e.name employee_name,e.role employee_role,
                 COALESCE(p.paid_amount,0) paid_amount,
                 GREATEST(0,(sp.base_amount+sp.adjustments)-COALESCE(p.paid_amount,0)) balance
          FROM {}.salary_periods sp
          JOIN {}.salary_employees e ON e.id=sp.employee_id
          LEFT JOIN LATERAL (
            SELECT COALESCE(SUM(amount),0) paid_amount FROM {}.salary_payments sap WHERE sap.salary_period_id=sp.id
          ) p ON true
          WHERE sp.period_month BETWEEN %s AND %s
          ORDER BY sp.period_month DESC,e.name
        """).format(S,S,S), [from_month,to_month])
        rows=cur.fetchall()
    for r in rows:
        total=_money(r["base_amount"])+_money(r["adjustments"]); paid=_money(r["paid_amount"])
        r["status"]="pagado" if paid>=total and total>0 else "parcial" if paid>0 else "vencido" if r["due_date"]<today else "pendiente"
    return rows


class SalaryAdjustment(BaseModel):
    adjustments: Decimal
    notes: str | None = None


@router.patch("/periods/{period_id}")
def adjust_period(period_id: UUID, body: SalaryAdjustment):
    with db_cursor() as cur:
        cur.execute(sql.SQL("UPDATE {}.salary_periods SET adjustments=%s,notes=%s WHERE id=%s RETURNING *").format(S), [body.adjustments,body.notes,period_id])
        row=cur.fetchone()
        if not row: raise HTTPException(404,"Período salarial no encontrado")
        return row


class SalaryPayment(BaseModel):
    account_id: UUID
    amount: Decimal
    payment_date: date = date.today()
    notes: str | None = None


@router.post("/periods/{period_id}/payments")
def pay_salary(period_id: UUID, body: SalaryPayment):
    if body.amount<=0: raise HTTPException(400,"El monto debe ser mayor a cero")
    with db_cursor() as cur:
        cur.execute(sql.SQL("""
          SELECT sp.*,e.name employee_name FROM {}.salary_periods sp
          JOIN {}.salary_employees e ON e.id=sp.employee_id WHERE sp.id=%s FOR UPDATE
        """).format(S,S), [period_id])
        period=cur.fetchone()
        if not period: raise HTTPException(404,"Período salarial no encontrado")
        cur.execute(sql.SQL("SELECT COALESCE(SUM(amount),0) paid FROM {}.salary_payments WHERE salary_period_id=%s").format(S), [period_id])
        already=_money(cur.fetchone()["paid"]); total=_money(period["base_amount"])+_money(period["adjustments"]); pending=max(Decimal("0"),total-already)
        if body.amount>pending: raise HTTPException(400,f"El pago supera el saldo pendiente ({pending})")
        description=f"Sueldo {period['employee_name']} - {period['period_month'].strftime('%m/%Y')}"
        cur.execute(sql.SQL("""
          INSERT INTO {}.financial_movements(account_id,type,category,description,amount,movement_date,notes)
          VALUES (%s,'egreso','sueldo',%s,%s,%s,%s) RETURNING *
        """).format(S), [body.account_id,description,body.amount,body.payment_date,body.notes])
        movement=cur.fetchone()
        cur.execute(sql.SQL("""
          INSERT INTO {}.salary_payments(salary_period_id,account_id,payment_date,amount,financial_movement_id,notes)
          VALUES (%s,%s,%s,%s,%s,%s) RETURNING *
        """).format(S), [period_id,body.account_id,body.payment_date,body.amount,movement["id"],body.notes])
        payment=cur.fetchone()
        return {"payment":payment,"movement":movement,"pending":max(Decimal("0"),pending-body.amount)}


@router.get("/summary")
def salary_summary():
    today=date.today(); month=_month_start(today)
    with db_cursor() as cur:
        _ensure_periods(cur,month,month)
        cur.execute(sql.SQL("""
          SELECT COALESCE(SUM(sp.base_amount+sp.adjustments),0) month_total,
                 COALESCE(SUM(COALESCE(p.paid,0)),0) month_paid,
                 COALESCE(SUM(GREATEST(0,(sp.base_amount+sp.adjustments)-COALESCE(p.paid,0))),0) month_pending
          FROM {}.salary_periods sp
          LEFT JOIN LATERAL (SELECT COALESCE(SUM(amount),0) paid FROM {}.salary_payments sap WHERE sap.salary_period_id=sp.id) p ON true
          WHERE sp.period_month=%s
        """).format(S,S), [month])
        current=cur.fetchone()
        cur.execute(sql.SQL("""
          SELECT COALESCE(SUM(GREATEST(0,(sp.base_amount+sp.adjustments)-COALESCE(p.paid,0))),0) overdue
          FROM {}.salary_periods sp
          LEFT JOIN LATERAL (SELECT COALESCE(SUM(amount),0) paid FROM {}.salary_payments sap WHERE sap.salary_period_id=sp.id) p ON true
          WHERE sp.due_date<CURRENT_DATE AND GREATEST(0,(sp.base_amount+sp.adjustments)-COALESCE(p.paid,0))>0
        """).format(S,S))
        current["overdue"]=cur.fetchone()["overdue"]
        return current
