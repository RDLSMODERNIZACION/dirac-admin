from fastapi import APIRouter, Depends, HTTPException
from psycopg import sql

from ..core.config import get_settings
from ..core.db import db_cursor
from ..core.security import require_api_key

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"], dependencies=[Depends(require_api_key)])
settings = get_settings()
S = sql.Identifier(settings.db_schema)


@router.get("/summary")
def summary():
    # Macro snapshot. Partial payments are derived from financial_movements links.
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
      SELECT COALESCE(SUM(r.amount),0) AS total,
             COALESCE(SUM(CASE WHEN r.due_date < CURRENT_DATE AND r.status IN ('pendiente','parcial') THEN r.amount ELSE 0 END),0) AS overdue
      FROM {}.receivables r
      WHERE r.status IN ('pendiente','parcial')
    ),
    pay AS (
      SELECT COALESCE(SUM(p.amount),0) AS total,
             COALESCE(SUM(CASE WHEN p.due_date < CURRENT_DATE AND p.status IN ('pendiente','parcial') THEN p.amount ELSE 0 END),0) AS overdue
      FROM {}.payables p
      WHERE p.status IN ('pendiente','parcial')
    ),
    works AS (
      SELECT COUNT(*) FILTER (WHERE status='activo') AS active_works,
             COALESCE(SUM(contract_amount) FILTER (WHERE status <> 'cancelado'),0) AS contracted
      FROM {}.works
    ),
    fixed AS (
      SELECT COALESCE(SUM(amount) FILTER (WHERE is_active=true AND frequency='mensual'),0) AS monthly_fixed
      FROM {}.fixed_costs
    )
    SELECT cash.balance AS cash_balance,
           recv.total AS receivables,
           pay.total AS payables,
           recv.overdue AS overdue_receivables,
           pay.overdue AS overdue_payables,
           works.active_works,
           works.contracted AS total_contracted,
           fixed.monthly_fixed AS monthly_fixed_costs,
           cash.balance + recv.total - pay.total AS net_position
    FROM cash, recv, pay, works, fixed
    """).format(S, S, S, S, S, S)
    with db_cursor() as cur:
        cur.execute(q)
        return cur.fetchone()


@router.get("/cash-projection")
def cash_projection(days: int = 90):
    if days < 1 or days > 3650:
        raise HTTPException(status_code=400, detail="days must be between 1 and 3650")
    q = sql.SQL("""
      WITH cash AS (
        SELECT COALESCE(SUM(a.initial_balance),0)
             + COALESCE(SUM(CASE WHEN fm.type='ingreso' THEN fm.amount WHEN fm.type='egreso' THEN -fm.amount ELSE 0 END),0) AS current_cash
        FROM {}.accounts a
        LEFT JOIN {}.financial_movements fm ON fm.account_id=a.id
        WHERE a.is_active=true
      ), daily AS (
        SELECT d::date AS day,
          COALESCE((SELECT SUM(amount) FROM {}.receivables r WHERE r.due_date=d::date AND r.status IN ('pendiente','parcial')),0) AS expected_in,
          COALESCE((SELECT SUM(amount) FROM {}.payables p WHERE p.due_date=d::date AND p.status IN ('pendiente','parcial')),0) AS expected_out
        FROM generate_series(CURRENT_DATE, CURRENT_DATE + (%s || ' days')::interval, interval '1 day') d
      )
      SELECT day, expected_in, expected_out,
             (SELECT current_cash FROM cash)
             + SUM(expected_in - expected_out) OVER (ORDER BY day) AS projected_cash
      FROM daily
      ORDER BY day
    """).format(S, S, S, S)
    with db_cursor() as cur:
        cur.execute(q, [days])
        return cur.fetchall()
