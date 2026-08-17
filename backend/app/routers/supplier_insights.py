from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from psycopg import sql

from ..core.config import get_settings
from ..core.db import db_cursor
from ..core.security import require_api_key

router = APIRouter(prefix="/api/supplier-insights", tags=["supplier-insights"], dependencies=[Depends(require_api_key)])
settings = get_settings()
S = sql.Identifier(settings.db_schema)
GROUPS = {"flota_vehicular", "marketing", "contratistas"}


def ensure_schema(cur):
    cur.execute(sql.SQL("ALTER TABLE {}.suppliers ADD COLUMN IF NOT EXISTS supplier_group text").format(S))
    cur.execute(sql.SQL("""
        UPDATE {}.suppliers
        SET supplier_group = CASE
            WHEN LOWER(name) LIKE ANY(ARRAY['%facebook%','%meta%','%instagram%','%marketing%','%publicidad%','%imprenta%','%diseño%','%freeda%']) THEN 'marketing'
            WHEN LOWER(name) LIKE ANY(ARRAY['%seguro%','%microtrack%','%nippon%','%taller%','%combustible%','%lubricentro%','%neumatic%','%repuesto%','%vehicul%','%camion%','%tracker%','%gps%']) THEN 'flota_vehicular'
            ELSE 'contratistas'
        END
        WHERE supplier_group IS NULL OR supplier_group=''
    """).format(S))
    cur.execute(sql.SQL("""
        CREATE TABLE IF NOT EXISTS {}.supplier_documents (
            id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
            supplier_id uuid NOT NULL REFERENCES {}.suppliers(id) ON DELETE CASCADE,
            document_type text NOT NULL DEFAULT 'otro',
            title text NOT NULL,
            document_date date NULL,
            url text NULL,
            notes text NULL,
            created_at timestamptz NOT NULL DEFAULT now()
        )
    """).format(S, S))


class SupplierPayload(BaseModel):
    name: str
    supplier_group: str = "contratistas"
    tax_id: str | None = None
    type: str = "proveedor"
    contact_name: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    notes: str | None = None
    is_active: bool = True
    is_fixed_cost: bool = False
    fixed_cost_amount: float | None = None
    fixed_cost_frequency: str = "mensual"
    fixed_cost_due_day: int | None = None


class DocumentPayload(BaseModel):
    document_type: str = "otro"
    title: str
    document_date: date | None = None
    url: str | None = None
    notes: str | None = None


def validate_supplier(body: SupplierPayload):
    if not body.name.strip():
        raise HTTPException(400, "El proveedor necesita un nombre")
    if body.supplier_group not in GROUPS:
        raise HTTPException(400, "Grupo de proveedor inválido")


def sync_fixed_cost(cur, supplier_id: UUID, body: SupplierPayload):
    cur.execute(sql.SQL("""
        SELECT id FROM {}.fixed_costs
        WHERE supplier_id=%s
        ORDER BY is_active DESC, created_at DESC
        LIMIT 1
    """).format(S), [supplier_id])
    existing = cur.fetchone()

    if body.is_fixed_cost:
        amount = float(body.fixed_cost_amount or 0)
        if amount <= 0:
            raise HTTPException(400, "Ingresá el monto del costo fijo")
        due_day = int(body.fixed_cost_due_day or 1)
        if not 1 <= due_day <= 31:
            raise HTTPException(400, "El día de vencimiento debe estar entre 1 y 31")
        vals = [body.name.strip(), body.supplier_group, amount, body.fixed_cost_frequency or "mensual", due_day, supplier_id, body.notes]
        if existing:
            cur.execute(sql.SQL("""
                UPDATE {}.fixed_costs
                SET name=%s,category=%s,amount=%s,frequency=%s,due_day=%s,supplier_id=%s,is_active=true,notes=%s
                WHERE id=%s
            """).format(S), vals + [existing["id"]])
        else:
            cur.execute(sql.SQL("""
                INSERT INTO {}.fixed_costs
                (name,category,amount,frequency,due_day,supplier_id,is_active,notes)
                VALUES (%s,%s,%s,%s,%s,%s,true,%s)
            """).format(S), vals)
    elif existing:
        cur.execute(sql.SQL("UPDATE {}.fixed_costs SET is_active=false WHERE id=%s").format(S), [existing["id"]])


def load_suppliers(cur):
    cur.execute(sql.SQL("""
        WITH payable_calc AS (
            SELECT p.id,p.supplier_id,p.amount,p.due_date,p.status,
                   COALESCE(SUM(fm.amount) FILTER (WHERE fm.type='egreso'),0) AS paid,
                   MAX(fm.movement_date) FILTER (WHERE fm.type='egreso') AS last_payment_date
            FROM {}.payables p
            LEFT JOIN {}.financial_movements fm ON fm.payable_id=p.id
            WHERE p.supplier_id IS NOT NULL AND LOWER(COALESCE(p.status,'')) <> 'anulado'
            GROUP BY p.id,p.supplier_id,p.amount,p.due_date,p.status
        ),
        fin AS (
            SELECT supplier_id,
                   COALESCE(SUM(amount),0) AS generated,
                   COALESCE(SUM(LEAST(paid,amount)),0) AS paid_total,
                   COALESCE(SUM(GREATEST(amount-paid,0)),0) AS pending,
                   COALESCE(SUM(CASE WHEN due_date<CURRENT_DATE THEN GREATEST(amount-paid,0) ELSE 0 END),0) AS overdue,
                   MAX(last_payment_date) AS last_payment_date,
                   MAX(CASE WHEN due_date<CURRENT_DATE AND amount-paid>0 THEN CURRENT_DATE-due_date ELSE 0 END) AS max_overdue_days
            FROM payable_calc GROUP BY supplier_id
        ),
        this_month AS (
            SELECT p.supplier_id,COALESCE(SUM(fm.amount),0) AS paid_this_month
            FROM {}.financial_movements fm
            JOIN {}.payables p ON p.id=fm.payable_id
            WHERE fm.type='egreso'
              AND date_trunc('month',fm.movement_date::timestamp)=date_trunc('month',CURRENT_DATE::timestamp)
            GROUP BY p.supplier_id
        ),
        fixed AS (
            SELECT DISTINCT ON (supplier_id)
                   supplier_id,id AS fixed_cost_id,amount AS fixed_cost_amount,
                   frequency AS fixed_cost_frequency,due_day AS fixed_cost_due_day,is_active AS fixed_cost_active
            FROM {}.fixed_costs
            WHERE supplier_id IS NOT NULL
            ORDER BY supplier_id,is_active DESC,created_at DESC
        )
        SELECT s.id,s.name,s.tax_id,s.type,s.contact_name,s.email,s.phone,s.address,s.notes,s.is_active,s.supplier_group,
               COALESCE(f.generated,0) AS generated,COALESCE(f.paid_total,0) AS paid_total,
               COALESCE(f.pending,0) AS pending,COALESCE(f.overdue,0) AS overdue,
               COALESCE(f.max_overdue_days,0) AS max_overdue_days,f.last_payment_date,
               COALESCE(tm.paid_this_month,0) AS paid_this_month,
               fx.fixed_cost_id,COALESCE(fx.fixed_cost_active,false) AS is_fixed_cost,
               COALESCE(fx.fixed_cost_amount,0) AS fixed_cost_amount,
               COALESCE(fx.fixed_cost_frequency,'mensual') AS fixed_cost_frequency,
               fx.fixed_cost_due_day
        FROM {}.suppliers s
        LEFT JOIN fin f ON f.supplier_id=s.id
        LEFT JOIN this_month tm ON tm.supplier_id=s.id
        LEFT JOIN fixed fx ON fx.supplier_id=s.id
        ORDER BY CASE s.supplier_group WHEN 'flota_vehicular' THEN 1 WHEN 'marketing' THEN 2 ELSE 3 END,s.name
    """).format(S,S,S,S,S,S))
    rows = cur.fetchall()
    for r in rows:
        overdue,pending,max_days=float(r["overdue"] or 0),float(r["pending"] or 0),int(r["max_overdue_days"] or 0)
        if overdue > 0:
            r["risk_level"],r["risk_reason"]="alto",(f"{max_days} días de atraso" if max_days else "saldo vencido")
        elif pending > 0:
            r["risk_level"],r["risk_reason"]="medio","saldo pendiente"
        else:
            r["risk_level"],r["risk_reason"]="bajo","sin deuda pendiente"
    return rows


@router.get("")
def supplier_insights():
    with db_cursor() as cur:
        ensure_schema(cur)
        rows=load_suppliers(cur)
    return {"summary":{
        "active":sum(1 for r in rows if r["is_active"] is not False),
        "flota_vehicular":sum(1 for r in rows if r["supplier_group"]=="flota_vehicular" and r["is_active"] is not False),
        "marketing":sum(1 for r in rows if r["supplier_group"]=="marketing" and r["is_active"] is not False),
        "contratistas":sum(1 for r in rows if r["supplier_group"]=="contratistas" and r["is_active"] is not False),
        "pending":sum(float(r["pending"] or 0) for r in rows),
        "overdue":sum(float(r["overdue"] or 0) for r in rows),
        "paid_this_month":sum(float(r["paid_this_month"] or 0) for r in rows),
        "fixed_cost_suppliers":sum(1 for r in rows if r["is_fixed_cost"] and r["is_active"] is not False),
        "fixed_cost_monthly":sum(float(r["fixed_cost_amount"] or 0) for r in rows if r["is_fixed_cost"] and r["is_active"] is not False and str(r["fixed_cost_frequency"]).lower()=="mensual"),
    },"suppliers":rows}


@router.get("/{supplier_id}")
def supplier_detail(supplier_id: UUID):
    with db_cursor() as cur:
        ensure_schema(cur)
        supplier=next((r for r in load_suppliers(cur) if r["id"]==supplier_id),None)
        if not supplier: raise HTTPException(404,"Proveedor no encontrado")
        cur.execute(sql.SQL("""
            SELECT p.id,p.description,p.document_number,p.issue_date,p.due_date,p.amount,p.status,
                   COALESCE(SUM(fm.amount) FILTER (WHERE fm.type='egreso'),0) AS paid,
                   GREATEST(p.amount-COALESCE(SUM(fm.amount) FILTER (WHERE fm.type='egreso'),0),0) AS pending
            FROM {}.payables p LEFT JOIN {}.financial_movements fm ON fm.payable_id=p.id
            WHERE p.supplier_id=%s AND LOWER(COALESCE(p.status,''))<>'anulado'
            GROUP BY p.id ORDER BY p.due_date DESC NULLS LAST
        """).format(S,S),[supplier_id]); payables=cur.fetchall()
        cur.execute(sql.SQL("""
            SELECT fm.id,fm.movement_date,fm.amount,fm.description,fm.category,p.document_number,p.description AS payable_description
            FROM {}.financial_movements fm JOIN {}.payables p ON p.id=fm.payable_id
            WHERE p.supplier_id=%s AND fm.type='egreso' ORDER BY fm.movement_date DESC NULLS LAST
        """).format(S,S),[supplier_id]); payments=cur.fetchall()
        cur.execute(sql.SQL("""
            SELECT id,document_type,title,document_date,url,notes,created_at FROM {}.supplier_documents
            WHERE supplier_id=%s ORDER BY document_date DESC NULLS LAST,created_at DESC
        """).format(S),[supplier_id]); documents=cur.fetchall()
    return {"supplier":supplier,"payables":payables,"payments":payments,"documents":documents}


@router.post("")
def create_supplier(body: SupplierPayload):
    validate_supplier(body)
    with db_cursor() as cur:
        ensure_schema(cur)
        cur.execute(sql.SQL("""
            INSERT INTO {}.suppliers (name,supplier_group,tax_id,type,contact_name,email,phone,address,notes,is_active)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING *
        """).format(S),[body.name.strip(),body.supplier_group,body.tax_id,body.type,body.contact_name,body.email,body.phone,body.address,body.notes,body.is_active])
        row=cur.fetchone(); sync_fixed_cost(cur,row["id"],body); return row


@router.patch("/{supplier_id}")
def update_supplier(supplier_id: UUID, body: SupplierPayload):
    validate_supplier(body)
    with db_cursor() as cur:
        ensure_schema(cur)
        cur.execute(sql.SQL("""
            UPDATE {}.suppliers SET name=%s,supplier_group=%s,tax_id=%s,type=%s,contact_name=%s,email=%s,phone=%s,address=%s,notes=%s,is_active=%s
            WHERE id=%s RETURNING *
        """).format(S),[body.name.strip(),body.supplier_group,body.tax_id,body.type,body.contact_name,body.email,body.phone,body.address,body.notes,body.is_active,supplier_id])
        row=cur.fetchone()
        if not row: raise HTTPException(404,"Proveedor no encontrado")
        sync_fixed_cost(cur,supplier_id,body); return row


@router.delete("/{supplier_id}")
def delete_supplier(supplier_id: UUID):
    with db_cursor() as cur:
        ensure_schema(cur)
        cur.execute(sql.SQL("""
            SELECT EXISTS(SELECT 1 FROM {}.payables WHERE supplier_id=%s) AS has_payables,
                   EXISTS(SELECT 1 FROM {}.purchases WHERE supplier_id=%s) AS has_purchases,
                   EXISTS(SELECT 1 FROM {}.supplier_services WHERE supplier_id=%s) AS has_services,
                   EXISTS(SELECT 1 FROM {}.fixed_costs WHERE supplier_id=%s) AS has_fixed_costs
        """).format(S,S,S,S),[supplier_id,supplier_id,supplier_id,supplier_id])
        if any(cur.fetchone().values()):
            raise HTTPException(400,"No se puede eliminar porque tiene movimientos asociados. Podés marcarlo como inactivo.")
        cur.execute(sql.SQL("DELETE FROM {}.suppliers WHERE id=%s RETURNING id").format(S),[supplier_id])
        if not cur.fetchone(): raise HTTPException(404,"Proveedor no encontrado")
    return {"ok":True}


@router.post("/{supplier_id}/documents")
def add_document(supplier_id: UUID, body: DocumentPayload):
    if not body.title.strip(): raise HTTPException(400,"El documento necesita un título")
    with db_cursor() as cur:
        ensure_schema(cur)
        cur.execute(sql.SQL("SELECT id FROM {}.suppliers WHERE id=%s").format(S),[supplier_id])
        if not cur.fetchone(): raise HTTPException(404,"Proveedor no encontrado")
        cur.execute(sql.SQL("""
            INSERT INTO {}.supplier_documents (supplier_id,document_type,title,document_date,url,notes)
            VALUES (%s,%s,%s,%s,%s,%s) RETURNING *
        """).format(S),[supplier_id,body.document_type,body.title.strip(),body.document_date,body.url,body.notes])
        return cur.fetchone()


@router.delete("/documents/{document_id}")
def delete_document(document_id: UUID):
    with db_cursor() as cur:
        ensure_schema(cur)
        cur.execute(sql.SQL("DELETE FROM {}.supplier_documents WHERE id=%s RETURNING id").format(S),[document_id])
        if not cur.fetchone(): raise HTTPException(404,"Documento no encontrado")
    return {"ok":True}
