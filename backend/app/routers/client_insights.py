from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from psycopg import sql

from ..core.config import get_settings
from ..core.db import db_cursor
from ..core.security import require_api_key

router = APIRouter(
    prefix="/api/client-insights",
    tags=["client-insights"],
    dependencies=[Depends(require_api_key)],
)

settings = get_settings()
S = sql.Identifier(settings.db_schema)


def _client_rows(cur):
    cur.execute(sql.SQL("""
        WITH recv AS (
            SELECT
                r.id,
                r.client_id,
                r.amount,
                r.issue_date,
                r.due_date,
                r.status,
                COALESCE(SUM(fm.amount) FILTER (WHERE fm.type='ingreso'),0) AS paid,
                MAX(fm.movement_date) FILTER (WHERE fm.type='ingreso') AS last_payment_date
            FROM {}.receivables r
            LEFT JOIN {}.financial_movements fm ON fm.receivable_id=r.id
            WHERE COALESCE(r.status,'') <> 'anulado'
            GROUP BY r.id,r.client_id,r.amount,r.issue_date,r.due_date,r.status
        ),
        financial AS (
            SELECT
                client_id,
                COALESCE(SUM(amount),0) AS invoiced,
                COALESCE(SUM(LEAST(paid,amount)),0) AS collected,
                COALESCE(SUM(GREATEST(amount-paid,0)),0) AS pending,
                COALESCE(SUM(
                    CASE WHEN due_date < CURRENT_DATE
                         THEN GREATEST(amount-paid,0)
                         ELSE 0 END
                ),0) AS overdue,
                MAX(CASE
                    WHEN due_date < CURRENT_DATE AND amount-paid>0
                    THEN CURRENT_DATE-due_date
                    ELSE 0 END
                ) AS max_overdue_days,
                MAX(issue_date) AS last_invoice_date,
                MAX(last_payment_date) AS last_payment_date,
                AVG(
                    CASE
                        WHEN last_payment_date IS NOT NULL AND issue_date IS NOT NULL
                        THEN last_payment_date-issue_date
                        ELSE NULL
                    END
                ) AS avg_collection_days
            FROM recv
            GROUP BY client_id
        ),
        works AS (
            SELECT
                client_id,
                COUNT(*) FILTER (
                    WHERE LOWER(COALESCE(status,'')) NOT IN
                    ('finalizado','finalizada','completado','completada','cancelado','cancelada','cerrado','cerrada')
                ) AS active_works,
                MAX(COALESCE(end_date,start_date)) AS last_work_date
            FROM {}.works
            GROUP BY client_id
        ),
        services AS (
            SELECT
                client_id,
                COUNT(*) FILTER (
                    WHERE LOWER(COALESCE(status,'')) IN ('activo','pendiente_cierre')
                ) AS active_services,
                MAX(COALESCE(end_date,start_date)) AS last_service_date
            FROM {}.services
            GROUP BY client_id
        )
        SELECT
            c.id,c.name,c.tax_id,c.contact_name,c.email,c.phone,c.address,c.notes,c.is_active,
            COALESCE(f.invoiced,0) AS invoiced,
            COALESCE(f.collected,0) AS collected,
            COALESCE(f.pending,0) AS pending,
            COALESCE(f.overdue,0) AS overdue,
            COALESCE(f.max_overdue_days,0) AS max_overdue_days,
            COALESCE(f.avg_collection_days,0) AS avg_collection_days,
            COALESCE(w.active_works,0) AS active_works,
            COALESCE(sv.active_services,0) AS active_services,
            GREATEST(
                f.last_invoice_date,
                f.last_payment_date,
                w.last_work_date,
                sv.last_service_date
            ) AS last_activity
        FROM {}.clients c
        LEFT JOIN financial f ON f.client_id=c.id
        LEFT JOIN works w ON w.client_id=c.id
        LEFT JOIN services sv ON sv.client_id=c.id
        ORDER BY COALESCE(f.invoiced,0) DESC,c.name
    """).format(S,S,S,S,S))
    rows = cur.fetchall()

    total_invoiced = sum(float(r["invoiced"] or 0) for r in rows) or 0
    for r in rows:
        invoiced = float(r["invoiced"] or 0)
        pending = float(r["pending"] or 0)
        overdue = float(r["overdue"] or 0)
        max_days = int(r["max_overdue_days"] or 0)
        share = (invoiced / total_invoiced * 100) if total_invoiced else 0

        score = 0
        reasons = []
        if overdue > 0:
            score += 2
            reasons.append("saldo vencido")
        if max_days >= 30:
            score += 1
            reasons.append(f"{max_days} días de atraso")
        if invoiced > 0 and overdue / invoiced >= .20:
            score += 1
            reasons.append("vencido relevante")
        if share >= 50:
            score += 2
            reasons.append("alta concentración")
        elif share >= 30:
            score += 1
            reasons.append("concentración")
        if pending > 0 and float(r["collected"] or 0) == 0:
            score += 1
            reasons.append("sin cobros")

        r["share_percent"] = round(share, 2)
        r["risk_level"] = "alto" if score >= 3 else ("medio" if score >= 1 else "bajo")
        r["risk_reasons"] = reasons
    return rows


@router.get("")
def insights():
    with db_cursor() as cur:
        rows = _client_rows(cur)

    active = sum(1 for r in rows if r["is_active"] is not False)
    invoiced = sum(float(r["invoiced"] or 0) for r in rows)
    collected = sum(float(r["collected"] or 0) for r in rows)
    pending = sum(float(r["pending"] or 0) for r in rows)
    overdue = sum(float(r["overdue"] or 0) for r in rows)

    billed_clients = [r for r in rows if float(r["invoiced"] or 0) > 0]
    avg_ticket = invoiced / len(billed_clients) if billed_clients else 0

    ordered = sorted(rows, key=lambda r: float(r["invoiced"] or 0), reverse=True)
    top3 = sum(float(r["invoiced"] or 0) for r in ordered[:3])
    concentration_top3 = (top3 / invoiced * 100) if invoiced else 0

    collection_days = [
        float(r["avg_collection_days"] or 0)
        for r in rows
        if float(r["avg_collection_days"] or 0) > 0
    ]
    avg_collection_days = sum(collection_days) / len(collection_days) if collection_days else 0

    return {
        "summary": {
            "active_clients": active,
            "total_clients": len(rows),
            "invoiced": invoiced,
            "collected": collected,
            "pending": pending,
            "overdue": overdue,
            "avg_ticket": avg_ticket,
            "top3_concentration": concentration_top3,
            "avg_collection_days": avg_collection_days,
            "high_risk_clients": sum(1 for r in rows if r["risk_level"] == "alto"),
        },
        "clients": rows,
    }


@router.get("/{client_id}")
def client_detail(client_id: UUID):
    with db_cursor() as cur:
        rows = _client_rows(cur)
        client = next((r for r in rows if r["id"] == client_id), None)
        if not client:
            raise HTTPException(404, "Cliente no encontrado")

        cur.execute(sql.SQL("""
            SELECT id,name,start_date,end_date,status,contract_amount
            FROM {}.works
            WHERE client_id=%s
            ORDER BY start_date DESC NULLS LAST
        """).format(S), [client_id])
        works = cur.fetchall()

        cur.execute(sql.SQL("""
            SELECT id,name,start_date,end_date,status,billing_amount,contract_amount
            FROM {}.services
            WHERE client_id=%s
            ORDER BY start_date DESC NULLS LAST
        """).format(S), [client_id])
        services = cur.fetchall()

        cur.execute(sql.SQL("""
            SELECT
                r.id,r.description,r.document_number,r.issue_date,r.due_date,r.amount,r.status,
                COALESCE(SUM(fm.amount) FILTER (WHERE fm.type='ingreso'),0) AS paid,
                GREATEST(r.amount-COALESCE(SUM(fm.amount) FILTER (WHERE fm.type='ingreso'),0),0) AS pending
            FROM {}.receivables r
            LEFT JOIN {}.financial_movements fm ON fm.receivable_id=r.id
            WHERE r.client_id=%s AND COALESCE(r.status,'')<>'anulado'
            GROUP BY r.id
            ORDER BY r.issue_date DESC NULLS LAST
        """).format(S,S), [client_id])
        receivables = cur.fetchall()

        cur.execute(sql.SQL("""
            SELECT fm.id,fm.movement_date,fm.amount,fm.description,fm.category,r.document_number
            FROM {}.financial_movements fm
            JOIN {}.receivables r ON r.id=fm.receivable_id
            WHERE r.client_id=%s AND fm.type='ingreso'
            ORDER BY fm.movement_date DESC NULLS LAST
        """).format(S,S), [client_id])
        payments = cur.fetchall()

    return {
        "client": client,
        "works": works,
        "services": services,
        "receivables": receivables,
        "payments": payments,
    }
