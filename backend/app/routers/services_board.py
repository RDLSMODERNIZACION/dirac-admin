from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends
from psycopg import sql

from ..core.config import get_settings
from ..core.db import db_cursor
from ..core.security import require_api_key

router = APIRouter(prefix="/api/services-board", tags=["services-board"], dependencies=[Depends(require_api_key)])
settings = get_settings()
S = sql.Identifier(settings.db_schema)


def D(v) -> Decimal:
    return Decimal(str(v or 0))


@router.get("")
def services_board():
    today = date.today()

    with db_cursor() as cur:
        cur.execute(sql.SQL("""
        SELECT
          s.id,
          s.name,
          s.status,
          s.service_type,
          s.billing_frequency,
          s.billing_amount,
          s.contract_amount,
          s.start_date,
          s.end_date,
          s.duration_months,
          s.billing_day,
          c.name AS client_name,

          COALESCE(periods.total_periods,0) AS total_periods,
          COALESCE(periods.billed_periods,0) AS billed_periods,
          COALESCE(periods.pending_periods,0) AS pending_periods,
          COALESCE(periods.due_pending_periods,0) AS due_pending_periods,
          COALESCE(periods.future_pending_periods,0) AS future_pending_periods,
          periods.next_period_number,
          periods.next_period_start,
          periods.next_due_date,

          COALESCE(fin.invoiced_total,0) AS invoiced_total,
          COALESCE(fin.collected_total,0) AS collected_total,
          COALESCE(fin.pending_collection,0) AS pending_collection,
          COALESCE(fin.overdue_amount,0) AS overdue_amount

        FROM {}.services s
        LEFT JOIN {}.clients c ON c.id=s.client_id

        LEFT JOIN LATERAL (
          SELECT
            COUNT(*) AS total_periods,
            COUNT(*) FILTER (WHERE sp.receivable_id IS NOT NULL) AS billed_periods,
            COUNT(*) FILTER (WHERE sp.receivable_id IS NULL) AS pending_periods,
            COUNT(*) FILTER (
              WHERE sp.receivable_id IS NULL
                AND sp.due_date <= CURRENT_DATE
            ) AS due_pending_periods,
            COUNT(*) FILTER (
              WHERE sp.receivable_id IS NULL
                AND sp.due_date > CURRENT_DATE
            ) AS future_pending_periods,
            MIN(sp.period_number) FILTER (WHERE sp.receivable_id IS NULL) AS next_period_number,
            MIN(sp.period_start) FILTER (WHERE sp.receivable_id IS NULL) AS next_period_start,
            MIN(sp.due_date) FILTER (WHERE sp.receivable_id IS NULL) AS next_due_date
          FROM {}.service_periods sp
          WHERE sp.service_id=s.id
        ) periods ON true

        LEFT JOIN LATERAL (
          SELECT
            COALESCE(SUM(r.amount),0) AS invoiced_total,
            COALESCE(SUM(COALESCE(p.paid,0)),0) AS collected_total,
            COALESCE(SUM(GREATEST(0,r.amount-COALESCE(p.paid,0))),0) AS pending_collection,
            COALESCE(SUM(
              CASE WHEN r.due_date < CURRENT_DATE
                THEN GREATEST(0,r.amount-COALESCE(p.paid,0))
                ELSE 0 END
            ),0) AS overdue_amount
          FROM {}.receivables r
          LEFT JOIN LATERAL (
            SELECT COALESCE(SUM(fm.amount),0) AS paid
            FROM {}.financial_movements fm
            WHERE fm.receivable_id=r.id AND fm.type='ingreso'
          ) p ON true
          WHERE r.service_id=s.id
            AND r.status <> 'anulado'
        ) fin ON true

        ORDER BY
          CASE WHEN s.status='activo' THEN 0 ELSE 1 END,
          s.end_date NULLS LAST,
          s.created_at DESC
        """).format(S,S,S,S,S))
        rows = cur.fetchall()

    result = []
    active_count = 0
    recurring_monthly = Decimal("0")
    pending_total = Decimal("0")
    high_count = 0

    for r in rows:
        end_date = r.get("end_date")
        start_date = r.get("start_date")
        status = str(r.get("status") or "").lower()

        days_to_end = (end_date - today).days if end_date else None
        pending_collection = D(r.get("pending_collection"))
        invoiced = D(r.get("invoiced_total"))
        overdue = D(r.get("overdue_amount"))
        pending_periods = int(r.get("pending_periods") or 0)
        due_pending_periods = int(r.get("due_pending_periods") or 0)
        future_pending_periods = int(r.get("future_pending_periods") or 0)
        total_periods = int(r.get("total_periods") or 0)
        billed_periods = int(r.get("billed_periods") or 0)

        if status == "cancelado":
            effective_status = "cancelado"
        elif end_date and end_date < today:
            if pending_periods <= 0 and pending_collection <= 0:
                effective_status = "finalizado"
            else:
                effective_status = "pendiente_cierre"
        else:
            effective_status = "activo"

        score = 0
        reasons = []

        if effective_status == "activo" and days_to_end is not None:
            if days_to_end < 0:
                score += 3
                reasons.append("vigencia vencida")
            elif days_to_end <= 14:
                score += 2
                reasons.append("finaliza pronto")
            elif days_to_end <= 30:
                score += 1

        if overdue > 0:
            score += 3
            reasons.append("facturas vencidas")
        elif invoiced > 0 and pending_collection / invoiced >= Decimal("0.50"):
            score += 2
            reasons.append("alta cobranza pendiente")
        elif invoiced > 0 and pending_collection / invoiced >= Decimal("0.25"):
            score += 1

        if due_pending_periods >= 2:
            score += 2
            reasons.append("períodos vencidos sin facturar")
        elif due_pending_periods == 1:
            score += 2
            reasons.append("período vencido sin facturar")

        if effective_status == "pendiente_cierre":
            score += 3
            if due_pending_periods > 0:
                reasons.append("vigencia terminada con períodos sin facturar")
            if pending_collection > 0:
                reasons.append("vigencia terminada con saldo pendiente")

        if effective_status == "cancelado":
            risk = "bajo"
        elif score >= 5:
            risk = "alto"
        elif score >= 2:
            risk = "medio"
        else:
            risk = "bajo"

        billing_progress = (Decimal(billed_periods) / Decimal(total_periods) * 100) if total_periods else Decimal("0")

        if effective_status == "activo":
            active_count += 1
            if str(r.get("service_type") or "").lower() == "mensual":
                recurring_monthly += D(r.get("billing_amount"))

        if effective_status in ("activo", "pendiente_cierre"):
            pending_total += pending_collection
            if risk == "alto":
                high_count += 1

        result.append({
            **r,
            "effective_status": effective_status,
            "days_to_end": days_to_end,
            "billing_progress_percent": billing_progress,
            "risk_level": risk,
            "risk_reasons": reasons,
        })

    return {
        "summary": {
            "active_services": active_count,
            "total_services": len(rows),
            "monthly_recurring": recurring_monthly,
            "pending_collection": pending_total,
            "high_risk_services": high_count,
        },
        "services": result,
    }

@router.delete("/{service_id}")
def delete_service_from_board(service_id: str):
    """
    Elimina un servicio cargado por error si todavía no tiene movimientos de caja.
    Limpia períodos, cuentas por cobrar sin cobros y documentos asociados.
    """
    with db_cursor() as cur:
        cur.execute(sql.SQL("SELECT * FROM {}.services WHERE id=%s FOR UPDATE").format(S), [service_id])
        service = cur.fetchone()
        if not service:
            from fastapi import HTTPException
            raise HTTPException(404, "Servicio no encontrado")

        # Si hubo cualquier movimiento de caja ligado al servicio, no permitir borrado.
        cur.execute(sql.SQL("""
            SELECT COALESCE(SUM(amount),0) AS total
            FROM {}.financial_movements
            WHERE service_id=%s
        """).format(S), [service_id])
        cash_total = D(cur.fetchone()["total"])
        if cash_total > 0:
            from fastapi import HTTPException
            raise HTTPException(
                400,
                "No se puede eliminar este servicio porque ya tiene cobros o movimientos de caja registrados."
            )

        # Verificación adicional por cuentas por cobrar vinculadas.
        cur.execute(sql.SQL("""
            SELECT COALESCE(SUM(fm.amount),0) AS paid
            FROM {}.financial_movements fm
            JOIN {}.receivables r ON r.id=fm.receivable_id
            WHERE r.service_id=%s AND fm.type='ingreso'
        """).format(S, S), [service_id])
        paid = D(cur.fetchone()["paid"])
        if paid > 0:
            from fastapi import HTTPException
            raise HTTPException(
                400,
                "No se puede eliminar este servicio porque ya tiene cobros registrados."
            )

        # Desvincular períodos de sus cuentas por cobrar.
        cur.execute(sql.SQL("""
            UPDATE {}.service_periods
            SET receivable_id=NULL
            WHERE service_id=%s
        """).format(S), [service_id])

        # Documentos: se eliminan los registros de BD.
        # Los archivos físicos del storage pueden quedar para limpieza administrativa posterior.
        cur.execute(sql.SQL("""
            DELETE FROM {}.service_documents
            WHERE service_id=%s
        """).format(S), [service_id])

        # Eliminar cuentas por cobrar sin movimientos.
        cur.execute(sql.SQL("""
            DELETE FROM {}.receivables
            WHERE service_id=%s
        """).format(S), [service_id])

        # Eliminar períodos.
        cur.execute(sql.SQL("""
            DELETE FROM {}.service_periods
            WHERE service_id=%s
        """).format(S), [service_id])

        # Finalmente el servicio.
        cur.execute(sql.SQL("""
            DELETE FROM {}.services
            WHERE id=%s
        """).format(S), [service_id])

    return {"ok": True}

