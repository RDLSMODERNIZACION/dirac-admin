from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends
from psycopg import sql

from ..core.config import get_settings
from ..core.db import db_cursor
from ..core.security import require_api_key

router = APIRouter(prefix="/api/works-board", tags=["works-board"], dependencies=[Depends(require_api_key)])
settings = get_settings()
S = sql.Identifier(settings.db_schema)


def D(v) -> Decimal:
    return Decimal(str(v or 0))


@router.get("")
def works_board():
    with db_cursor() as cur:
        cur.execute(sql.SQL("""
        SELECT
          w.id,
          w.name,
          w.status,
          w.start_date,
          w.end_date,
          w.contract_amount,
          c.name AS client_name,

          COALESCE(items.executed_amount,0) AS executed_amount,
          COALESCE(items.net_billed,0) AS net_billed,
          COALESCE(inv.invoiced_total,0) AS invoiced_total,
          COALESCE(cash.collected,0) AS collected,
          COALESCE(costs.real_cost,0) AS real_cost,
          COALESCE(overdue.overdue_amount,0) AS overdue_amount

        FROM {}.works w
        JOIN {}.clients c ON c.id=w.client_id

        LEFT JOIN LATERAL (
          SELECT
            COALESCE(SUM(
              CASE WHEN wi.status <> 'cancelado'
                THEN wi.budget_amount * wi.progress_percent / 100.0
                ELSE 0 END
            ),0) AS executed_amount,
            COALESCE(SUM(
              CASE WHEN wi.status <> 'cancelado'
                THEN COALESCE(b.billed_amount,0)
                ELSE 0 END
            ),0) AS net_billed
          FROM {}.work_items wi
          LEFT JOIN LATERAL (
            SELECT COALESCE(SUM(ii.amount),0) AS billed_amount
            FROM {}.work_invoice_items ii
            JOIN {}.work_invoices x ON x.id=ii.work_invoice_id
            WHERE ii.work_item_id=wi.id AND x.status <> 'anulada'
          ) b ON true
          WHERE wi.work_id=w.id
        ) items ON true

        LEFT JOIN LATERAL (
          SELECT COALESCE(SUM(total_amount),0) AS invoiced_total
          FROM {}.work_invoices x
          WHERE x.work_id=w.id AND x.status <> 'anulada'
        ) inv ON true

        LEFT JOIN LATERAL (
          SELECT COALESCE(SUM(amount),0) AS collected
          FROM {}.financial_movements fm
          WHERE fm.work_id=w.id AND fm.type='ingreso'
        ) cash ON true

        LEFT JOIN LATERAL (
          SELECT COALESCE(SUM(amount),0) AS real_cost
          FROM {}.work_costs wc
          WHERE wc.work_id=w.id AND wc.payment_status <> 'anulado'
        ) costs ON true

        LEFT JOIN LATERAL (
          SELECT COALESCE(SUM(
            GREATEST(0,r.amount-COALESCE(p.paid,0))
          ),0) AS overdue_amount
          FROM {}.receivables r
          LEFT JOIN LATERAL (
            SELECT COALESCE(SUM(amount),0) AS paid
            FROM {}.financial_movements fm2
            WHERE fm2.receivable_id=r.id AND fm2.type='ingreso'
          ) p ON true
          WHERE r.work_id=w.id
            AND r.status IN ('pendiente','parcial')
            AND r.due_date < CURRENT_DATE
        ) overdue ON true

        WHERE COALESCE(w.type,'obra') <> 'servicio_mensual'
        ORDER BY
          CASE WHEN w.status IN ('finalizado','finalizada','completado','completada','cerrado','cerrada') THEN 1 ELSE 0 END,
          w.end_date NULLS LAST,
          w.created_at DESC
        """).format(S,S,S,S,S,S,S,S,S,S,S))
        rows = cur.fetchall()

    today = date.today()
    result = []
    active_count = 0
    executed_total = Decimal("0")
    pending_total = Decimal("0")
    high_count = 0

    for r in rows:
        contract = D(r.get("contract_amount"))
        executed = D(r.get("executed_amount"))
        net_billed = D(r.get("net_billed"))
        invoiced = D(r.get("invoiced_total"))
        collected = D(r.get("collected"))
        real_cost = D(r.get("real_cost"))
        overdue = D(r.get("overdue_amount"))

        pending_collection = max(Decimal("0"), invoiced - collected)
        executed_unbilled = max(Decimal("0"), executed - net_billed)
        advanced_invoicing = max(Decimal("0"), net_billed - executed)
        progress = (executed / contract * 100) if contract > 0 else Decimal("0")

        status_text = str(r.get("status") or "").lower()
        finished = any(x in status_text for x in ("finaliz","complet","cerrad","terminad"))
        days_to_end = None
        if r.get("end_date"):
            days_to_end = (r["end_date"] - today).days

        # Riesgo simple de gestión.
        score = 0
        reasons = []

        if not finished and days_to_end is not None:
            if days_to_end < 0:
                score += 3
                reasons.append("plazo vencido")
            elif days_to_end <= 14:
                score += 2
                reasons.append("fin próximo")
            elif days_to_end <= 30:
                score += 1

        if overdue > 0:
            score += 3
            reasons.append("cobros vencidos")
        elif invoiced > 0 and pending_collection / invoiced >= Decimal("0.50"):
            score += 2
            reasons.append("alta cobranza pendiente")
        elif invoiced > 0 and pending_collection / invoiced >= Decimal("0.25"):
            score += 1

        if contract > 0 and executed_unbilled / contract >= Decimal("0.20"):
            score += 2
            reasons.append("mucho ejecutado sin facturar")
        elif contract > 0 and executed_unbilled / contract >= Decimal("0.10"):
            score += 1

        if contract > 0 and real_cost / contract >= Decimal("0.85"):
            score += 3
            reasons.append("costo alto vs contrato")
        elif contract > 0 and real_cost / contract >= Decimal("0.65"):
            score += 1

        if finished and pending_collection <= 0:
            risk = "bajo"
        elif score >= 5:
            risk = "alto"
        elif score >= 2:
            risk = "medio"
        else:
            risk = "bajo"

        if not finished:
            active_count += 1
            executed_total += executed
            pending_total += pending_collection
            if risk == "alto":
                high_count += 1

        result.append({
            **r,
            "progress_percent": progress,
            "pending_collection": pending_collection,
            "executed_unbilled": executed_unbilled,
            "advanced_invoicing": advanced_invoicing,
            "days_to_end": days_to_end,
            "risk_level": risk,
            "risk_reasons": reasons,
            "is_finished": finished,
        })

    return {
        "summary": {
            "active_works": active_count,
            "total_works": len(rows),
            "executed_total": executed_total,
            "pending_collection": pending_total,
            "high_risk_works": high_count,
        },
        "works": result,
    }
