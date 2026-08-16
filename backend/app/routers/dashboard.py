from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal
import json
import os
from urllib.parse import quote
from urllib.request import Request, urlopen
from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from psycopg import sql

from ..core.config import get_settings
from ..core.db import db_cursor
from ..core.security import require_api_key

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"], dependencies=[Depends(require_api_key)])
settings = get_settings()
S = sql.Identifier(settings.db_schema)

FREQUENCY_MONTHS = {
    "mensual": 1,
    "bimestral": 2,
    "trimestral": 3,
    "semestral": 6,
    "anual": 12,
}


def _month_start(d: date) -> date:
    return date(d.year, d.month, 1)


def _add_months(d: date, months: int) -> date:
    idx = d.year * 12 + (d.month - 1) + months
    return date(idx // 12, idx % 12 + 1, 1)


def _months_between(a: date, b: date) -> int:
    return (b.year - a.year) * 12 + (b.month - a.month)


def _due_date(period_start: date, due_day: int | None) -> date:
    day = max(1, min(int(due_day or 1), monthrange(period_start.year, period_start.month)[1]))
    return date(period_start.year, period_start.month, day)


def _is_occurrence(start_date: date, period_start: date, frequency: str) -> bool:
    anchor = _month_start(start_date)
    diff = _months_between(anchor, period_start)
    step = FREQUENCY_MONTHS.get(frequency, 1)
    return diff >= 0 and diff % step == 0


def _fixed_occurrences(cost: dict, from_month: date, to_month: date):
    start_date = cost.get("start_date") or (cost.get("created_at").date() if cost.get("created_at") else date.today())
    start_date = start_date if isinstance(start_date, date) else date.fromisoformat(str(start_date)[:10])
    current = max(_month_start(start_date), from_month)
    while current <= to_month:
        if _is_occurrence(start_date, current, cost.get("frequency") or "mensual"):
            yield current, _due_date(current, cost.get("due_day"))
        current = _add_months(current, 1)


def _storage_config():
    base = (os.getenv("SUPABASE_URL") or "").rstrip("/")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or ""
    bucket = os.getenv("SUPABASE_DOCUMENT_BUCKET") or "administracion-documents"
    if not base or not key:
        raise HTTPException(500, "Faltan SUPABASE_URL o SUPABASE_SERVICE_ROLE_KEY en Render")
    return base, key, bucket


def _storage_upload(path: str, content: bytes, content_type: str):
    base, key, bucket = _storage_config()
    url = f"{base}/storage/v1/object/{quote(bucket, safe='')}/{quote(path, safe='/')}"
    req = Request(url, data=content, method="POST", headers={
        "Authorization": f"Bearer {key}",
        "apikey": key,
        "Content-Type": content_type or "application/octet-stream",
        "x-upsert": "true",
    })
    try:
        with urlopen(req, timeout=30) as r:
            r.read()
    except Exception as exc:
        raise HTTPException(502, f"No se pudo subir el comprobante a Storage: {exc}")


def _storage_signed_url(path: str, expires: int = 3600) -> str:
    base, key, bucket = _storage_config()
    url = f"{base}/storage/v1/object/sign/{quote(bucket, safe='')}/{quote(path, safe='/')}"
    req = Request(url, data=json.dumps({"expiresIn": expires}).encode(), method="POST", headers={
        "Authorization": f"Bearer {key}",
        "apikey": key,
        "Content-Type": "application/json",
    })
    try:
        with urlopen(req, timeout=20) as r:
            body = json.loads(r.read().decode())
    except Exception as exc:
        raise HTTPException(502, f"No se pudo generar el enlace del comprobante: {exc}")
    signed = body.get("signedURL") or body.get("signedUrl")
    if not signed:
        raise HTTPException(502, "Storage no devolvió una URL firmada")
    return signed if signed.startswith("http") else f"{base}/storage/v1{signed}"


@router.get("/summary")
def summary():
    q = sql.SQL("""
    WITH
    cash AS (
      SELECT COALESCE(SUM(a.initial_balance),0)
           + COALESCE(SUM(CASE WHEN fm.type='ingreso' THEN fm.amount WHEN fm.type='egreso' THEN -fm.amount ELSE 0 END),0) AS balance
      FROM {}.accounts a
      LEFT JOIN {}.financial_movements fm ON fm.account_id = a.id
      WHERE a.is_active = true
    ),
    recv AS (
      SELECT COALESCE(SUM(GREATEST(0, r.amount-COALESCE(x.paid,0))),0) AS total,
             COALESCE(SUM(CASE WHEN r.due_date < CURRENT_DATE AND r.status IN ('pendiente','parcial') THEN GREATEST(0,r.amount-COALESCE(x.paid,0)) ELSE 0 END),0) AS overdue
      FROM {}.receivables r
      LEFT JOIN LATERAL (
        SELECT COALESCE(SUM(fm.amount),0) AS paid FROM {}.financial_movements fm
        WHERE fm.receivable_id=r.id AND fm.type='ingreso'
      ) x ON true
      WHERE r.status IN ('pendiente','parcial')
    ),
    pay AS (
      SELECT COALESCE(SUM(GREATEST(0, p.amount-COALESCE(x.paid,0))),0) AS total,
             COALESCE(SUM(CASE WHEN p.due_date < CURRENT_DATE AND p.status IN ('pendiente','parcial') THEN GREATEST(0,p.amount-COALESCE(x.paid,0)) ELSE 0 END),0) AS overdue
      FROM {}.payables p
      LEFT JOIN LATERAL (
        SELECT COALESCE(SUM(fm.amount),0) AS paid FROM {}.financial_movements fm
        WHERE fm.payable_id=p.id AND fm.type='egreso'
      ) x ON true
      WHERE p.status IN ('pendiente','parcial')
    ),
    works AS (
      SELECT COUNT(*) FILTER (WHERE status='activo') AS active_works,
             COALESCE(SUM(contract_amount) FILTER (WHERE status <> 'cancelado'),0) AS contracted,
             COALESCE(SUM(monthly_amount) FILTER (
               WHERE status='activo' AND type='servicio_mensual' AND billing_frequency='mensual'
                 AND (start_date IS NULL OR start_date<=CURRENT_DATE)
                 AND (end_date IS NULL OR end_date>=CURRENT_DATE)
             ),0) AS legacy_monthly_revenue
      FROM {}.works
    ),
    services AS (
      SELECT COUNT(*) FILTER (WHERE status='activo' AND (start_date IS NULL OR start_date<=CURRENT_DATE) AND (end_date IS NULL OR end_date>=CURRENT_DATE)) AS active_services,
             COALESCE(SUM(contract_amount) FILTER (WHERE status <> 'cancelado'),0) AS service_contract_value,
             COALESCE(SUM(billing_amount) FILTER (
               WHERE status='activo' AND billing_frequency='mensual'
                 AND (start_date IS NULL OR start_date<=CURRENT_DATE)
                 AND (end_date IS NULL OR end_date>=CURRENT_DATE)
             ),0) AS monthly_revenue
      FROM {}.services
    ),
    fixed AS (
      SELECT COALESCE(SUM(amount) FILTER (WHERE is_active=true AND frequency='mensual'),0) AS monthly_fixed
      FROM {}.fixed_costs
    )
    SELECT cash.balance AS cash_balance, recv.total AS receivables, pay.total AS payables,
           recv.overdue AS overdue_receivables, pay.overdue AS overdue_payables,
           works.active_works, works.contracted AS total_contracted,
           works.legacy_monthly_revenue + services.monthly_revenue AS monthly_recurring_revenue,
           services.active_services, services.service_contract_value,
           fixed.monthly_fixed AS monthly_fixed_costs,
           cash.balance + recv.total - pay.total AS net_position
    FROM cash, recv, pay, works, services, fixed
    """).format(S, S, S, S, S, S, S, S, S)
    with db_cursor() as cur:
        cur.execute(q)
        return cur.fetchone()


@router.get("/fixed-cost-schedule")
def fixed_cost_schedule(months: int = 6):
    if months < 1 or months > 36:
        raise HTTPException(400, "months debe estar entre 1 y 36")
    today = date.today()
    first = _month_start(today)
    last = _add_months(first, months - 1)
    with db_cursor() as cur:
        cur.execute(sql.SQL("SELECT * FROM {}.fixed_costs WHERE is_active=true ORDER BY name").format(S))
        costs = cur.fetchall()
        cur.execute(sql.SQL("""
          SELECT fcp.*, a.name AS account_name
          FROM {}.fixed_cost_payments fcp
          LEFT JOIN {}.accounts a ON a.id=fcp.account_id
          WHERE fcp.period_start >= %s AND fcp.period_start <= %s
        """).format(S, S), [first, last])
        payments = cur.fetchall()
    pmap = {(str(p["fixed_cost_id"]), p["period_start"]): p for p in payments}
    rows = []
    for cost in costs:
        for period_start, due in _fixed_occurrences(cost, first, last):
            payment = pmap.get((str(cost["id"]), period_start))
            if payment:
                state = "pagado"
            elif due < today:
                state = "vencido"
            elif due <= today + timedelta(days=7):
                state = "vence_pronto"
            else:
                state = "pendiente"
            rows.append({
                "fixed_cost_id": cost["id"],
                "period_start": period_start,
                "due_date": due,
                "name": cost["name"],
                "category": cost.get("category"),
                "frequency": cost.get("frequency"),
                "expected_amount": cost["amount"],
                "supplier_id": cost.get("supplier_id"),
                "status": state,
                "payment": payment,
            })
    rows.sort(key=lambda x: (x["due_date"], x["name"]))
    return rows


class FixedCostPaymentCreate(BaseModel):
    period_start: date
    account_id: UUID
    amount: Decimal
    payment_date: date = date.today()
    notes: str | None = None


@router.post("/fixed-costs/{fixed_cost_id}/pay")
def pay_fixed_cost(fixed_cost_id: UUID, body: FixedCostPaymentCreate):
    if body.amount <= 0:
        raise HTTPException(400, "El monto pagado debe ser mayor a cero")
    period_start = _month_start(body.period_start)
    with db_cursor() as cur:
        cur.execute(sql.SQL("SELECT * FROM {}.fixed_costs WHERE id=%s FOR UPDATE").format(S), [fixed_cost_id])
        cost = cur.fetchone()
        if not cost:
            raise HTTPException(404, "Costo fijo no encontrado")
        start_date = cost.get("start_date") or date.today()
        if not _is_occurrence(start_date, period_start, cost.get("frequency") or "mensual"):
            raise HTTPException(400, "Ese período no corresponde a la frecuencia del costo fijo")
        cur.execute(sql.SQL("SELECT id FROM {}.accounts WHERE id=%s AND is_active=true").format(S), [body.account_id])
        if not cur.fetchone():
            raise HTTPException(400, "Cuenta inexistente o inactiva")
        cur.execute(sql.SQL("SELECT * FROM {}.fixed_cost_payments WHERE fixed_cost_id=%s AND period_start=%s").format(S), [fixed_cost_id, period_start])
        if cur.fetchone():
            raise HTTPException(409, "Ese período ya fue pagado")
        due = _due_date(period_start, cost.get("due_day"))
        description = f"Costo fijo {cost['name']} - {period_start.strftime('%m/%Y')}"
        cur.execute(sql.SQL("""
          INSERT INTO {}.financial_movements
            (account_id,supplier_id,type,category,description,amount,movement_date,notes)
          VALUES (%s,%s,'egreso','costo_fijo',%s,%s,%s,%s)
          RETURNING *
        """).format(S), [body.account_id, cost.get("supplier_id"), description, body.amount, body.payment_date, body.notes])
        movement = cur.fetchone()
        cur.execute(sql.SQL("""
          INSERT INTO {}.fixed_cost_payments
            (fixed_cost_id,period_start,due_date,expected_amount,actual_amount,payment_date,account_id,financial_movement_id,notes)
          VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
          RETURNING *
        """).format(S), [fixed_cost_id, period_start, due, cost["amount"], body.amount, body.payment_date, body.account_id, movement["id"], body.notes])
        payment = cur.fetchone()
    return {"payment": payment, "movement": movement}


@router.post("/fixed-cost-payments/{payment_id}/receipt")
async def upload_fixed_cost_receipt(payment_id: UUID, file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(400, "Archivo inválido")
    content = await file.read()
    if not content:
        raise HTTPException(400, "El archivo está vacío")
    safe_name = file.filename.replace("/", "_").replace("\\", "_")
    path = f"fixed-costs/{payment_id}/{safe_name}"
    _storage_upload(path, content, file.content_type or "application/octet-stream")
    with db_cursor() as cur:
        cur.execute(sql.SQL("UPDATE {}.fixed_cost_payments SET receipt_path=%s, receipt_name=%s WHERE id=%s RETURNING *").format(S), [path, safe_name, payment_id])
        row = cur.fetchone()
    if not row:
        raise HTTPException(404, "Pago de costo fijo no encontrado")
    return row


@router.get("/fixed-cost-payments/{payment_id}/receipt-url")
def fixed_cost_receipt_url(payment_id: UUID):
    with db_cursor() as cur:
        cur.execute(sql.SQL("SELECT receipt_path FROM {}.fixed_cost_payments WHERE id=%s").format(S), [payment_id])
        row = cur.fetchone()
    if not row or not row.get("receipt_path"):
        raise HTTPException(404, "Este pago no tiene comprobante")
    return {"url": _storage_signed_url(row["receipt_path"])}


@router.get("/cash-projection")
def cash_projection(days: int = 90):
    if days < 1 or days > 3650:
        raise HTTPException(400, "days must be between 1 and 3650")
    today = date.today()
    end = today + timedelta(days=days)
    daily: dict[date, dict[str, Decimal]] = {
        today + timedelta(days=i): {"in": Decimal("0"), "out": Decimal("0"), "fixed": Decimal("0")}
        for i in range(days + 1)
    }
    with db_cursor() as cur:
        cur.execute(sql.SQL("""
          SELECT COALESCE(SUM(a.initial_balance),0)
               + COALESCE(SUM(CASE WHEN fm.type='ingreso' THEN fm.amount WHEN fm.type='egreso' THEN -fm.amount ELSE 0 END),0) AS current_cash
          FROM {}.accounts a
          LEFT JOIN {}.financial_movements fm ON fm.account_id=a.id
          WHERE a.is_active=true
        """).format(S, S))
        cash = Decimal(str(cur.fetchone()["current_cash"] or 0))

        cur.execute(sql.SQL("""
          SELECT r.id,r.due_date,GREATEST(0,r.amount-COALESCE(x.paid,0)) AS remaining
          FROM {}.receivables r
          LEFT JOIN LATERAL (SELECT COALESCE(SUM(amount),0) paid FROM {}.financial_movements fm WHERE fm.receivable_id=r.id AND fm.type='ingreso') x ON true
          WHERE r.status IN ('pendiente','parcial')
        """).format(S, S))
        receivables = cur.fetchall()
        cur.execute(sql.SQL("""
          SELECT p.id,p.due_date,GREATEST(0,p.amount-COALESCE(x.paid,0)) AS remaining
          FROM {}.payables p
          LEFT JOIN LATERAL (SELECT COALESCE(SUM(amount),0) paid FROM {}.financial_movements fm WHERE fm.payable_id=p.id AND fm.type='egreso') x ON true
          WHERE p.status IN ('pendiente','parcial')
        """).format(S, S))
        payables = cur.fetchall()
        cur.execute(sql.SQL("SELECT * FROM {}.fixed_costs WHERE is_active=true").format(S))
        costs = cur.fetchall()
        from_month = min((_month_start(c.get("start_date") or today) for c in costs), default=_month_start(today))
        to_month = _month_start(end)
        cur.execute(sql.SQL("SELECT fixed_cost_id,period_start FROM {}.fixed_cost_payments WHERE period_start >= %s AND period_start <= %s").format(S), [from_month, to_month])
        paid_keys = {(str(x["fixed_cost_id"]), x["period_start"]) for x in cur.fetchall()}

    for r in receivables:
        amount = Decimal(str(r.get("remaining") or 0))
        if amount <= 0: continue
        d = r.get("due_date") or today
        d = max(today, d)
        if d <= end: daily[d]["in"] += amount
    for p in payables:
        amount = Decimal(str(p.get("remaining") or 0))
        if amount <= 0: continue
        d = p.get("due_date") or today
        d = max(today, d)
        if d <= end: daily[d]["out"] += amount
    for cost in costs:
        start_month = _month_start(cost.get("start_date") or today)
        for period_start, due in _fixed_occurrences(cost, start_month, to_month):
            if (str(cost["id"]), period_start) in paid_keys:
                continue
            target = max(today, due)
            if target <= end:
                amount = Decimal(str(cost.get("amount") or 0))
                daily[target]["out"] += amount
                daily[target]["fixed"] += amount

    running = cash
    result = []
    for d in sorted(daily):
        values = daily[d]
        running += values["in"] - values["out"]
        result.append({
            "day": d,
            "expected_in": values["in"],
            "expected_out": values["out"],
            "fixed_cost_out": values["fixed"],
            "projected_cash": running,
        })
    return result
