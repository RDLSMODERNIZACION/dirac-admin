from fastapi import APIRouter, Depends
from psycopg import sql

from ..core.config import get_settings
from ..core.db import db_cursor
from ..core.security import require_api_key

router = APIRouter(prefix="/api/reports", tags=["reports"], dependencies=[Depends(require_api_key)])
settings = get_settings()
S = sql.Identifier(settings.db_schema)


@router.get("/current-stock")
def current_stock():
    q = sql.SQL("""
      SELECT m.id, m.code, m.name, m.category, m.unit, m.minimum_stock, m.current_cost,
             COALESCE(SUM(CASE
               WHEN sm.movement_type IN ('ingreso','ajuste_positivo') THEN sm.quantity
               WHEN sm.movement_type IN ('egreso','ajuste_negativo') THEN -sm.quantity
               ELSE 0 END),0) AS current_stock,
             COALESCE(SUM(CASE
               WHEN sm.movement_type IN ('ingreso','ajuste_positivo') THEN sm.quantity
               WHEN sm.movement_type IN ('egreso','ajuste_negativo') THEN -sm.quantity
               ELSE 0 END),0) * m.current_cost AS stock_value
      FROM {}.materials m
      LEFT JOIN {}.stock_movements sm ON sm.material_id=m.id
      WHERE m.is_active=true
      GROUP BY m.id
      ORDER BY m.name
    """).format(S, S)
    with db_cursor() as cur:
        cur.execute(q)
        return cur.fetchall()


@router.get("/supplier-balances")
def supplier_balances():
    q = sql.SQL("""
      SELECT s.id, s.name, s.type,
             COALESCE(SUM(p.amount),0) AS generated,
             COALESCE(SUM(pm.paid),0) AS paid,
             COALESCE(SUM(p.amount),0) - COALESCE(SUM(pm.paid),0) AS balance
      FROM {}.suppliers s
      LEFT JOIN {}.payables p ON p.supplier_id=s.id AND p.status <> 'anulado'
      LEFT JOIN LATERAL (
        SELECT COALESCE(SUM(fm.amount),0) AS paid
        FROM {}.financial_movements fm
        WHERE fm.payable_id=p.id AND fm.type='egreso'
      ) pm ON true
      WHERE s.is_active=true
      GROUP BY s.id
      ORDER BY balance DESC, s.name
    """).format(S, S, S)
    with db_cursor() as cur:
        cur.execute(q)
        return cur.fetchall()


@router.get("/work-profitability")
def work_profitability():
    q = sql.SQL("""
      WITH material_cost AS (
        SELECT work_id, SUM(total_cost) AS amount
        FROM {}.stock_movements
        WHERE work_id IS NOT NULL AND movement_type IN ('egreso','ajuste_negativo')
        GROUP BY work_id
      ), contractor_cost AS (
        SELECT work_id, SUM(total_amount) AS amount
        FROM {}.supplier_services
        WHERE work_id IS NOT NULL AND status='aprobado'
        GROUP BY work_id
      ), work_cost AS (
        SELECT work_id, SUM(amount) AS amount
        FROM {}.work_costs
        WHERE work_id IS NOT NULL AND payment_status <> 'anulado'
        GROUP BY work_id
      ), direct_payables AS (
        SELECT work_id, SUM(amount) AS amount
        FROM {}.payables p
        WHERE p.work_id IS NOT NULL AND p.status <> 'anulado'
          AND p.purchase_id IS NULL AND p.supplier_service_id IS NULL
          AND NOT EXISTS (SELECT 1 FROM {}.work_costs wc WHERE wc.payable_id = p.id)
        GROUP BY p.work_id
      ), billed AS (
        SELECT work_id, SUM(amount) AS amount
        FROM {}.receivables
        WHERE work_id IS NOT NULL AND status <> 'anulado'
        GROUP BY work_id
      ), collected AS (
        SELECT work_id, SUM(amount) AS amount
        FROM {}.financial_movements
        WHERE work_id IS NOT NULL AND type='ingreso'
        GROUP BY work_id
      )
      SELECT w.id, w.code, w.name, w.status, w.contract_amount, w.estimated_cost, w.progress_percent,
             COALESCE(mc.amount,0) + COALESCE(cc.amount,0) + COALESCE(wc.amount,0) + COALESCE(dp.amount,0) AS real_cost,
             COALESCE(b.amount,0) AS billed,
             COALESCE(c.amount,0) AS collected,
             w.contract_amount - (COALESCE(mc.amount,0)+COALESCE(cc.amount,0)+COALESCE(wc.amount,0)+COALESCE(dp.amount,0)) AS projected_result,
             CASE WHEN w.contract_amount > 0 THEN
               (w.contract_amount - (COALESCE(mc.amount,0)+COALESCE(cc.amount,0)+COALESCE(wc.amount,0)+COALESCE(dp.amount,0))) / w.contract_amount
             ELSE 0 END AS margin_ratio
      FROM {}.works w
      LEFT JOIN material_cost mc ON mc.work_id=w.id
      LEFT JOIN contractor_cost cc ON cc.work_id=w.id
      LEFT JOIN work_cost wc ON wc.work_id=w.id
      LEFT JOIN direct_payables dp ON dp.work_id=w.id
      LEFT JOIN billed b ON b.work_id=w.id
      LEFT JOIN collected c ON c.work_id=w.id
      ORDER BY w.created_at DESC
    """).format(S, S, S, S, S, S, S, S)
    with db_cursor() as cur:
        cur.execute(q)
        return cur.fetchall()
