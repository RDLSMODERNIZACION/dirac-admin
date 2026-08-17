from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# finance_payables.py
p = ROOT / 'backend/app/routers/finance_payables.py'
t = p.read_text(encoding='utf-8')

old = """class PayableCreate(BaseModel):
    supplier_id: UUID
    work_id: UUID | None = None
    work_item_id: UUID | None = None
    description: str
    document_number: str | None = None
    issue_date: str | None = None
    due_date: str | None = None
    amount: Decimal
    category: str = \"otros\"
    notes: str | None = None
"""
new = """class PayableCreate(BaseModel):
    supplier_id: UUID
    work_id: UUID | None = None
    work_item_id: UUID | None = None
    description: str
    document_number: str | None = None
    issue_date: str | None = None
    due_date: str | None = None
    amount: Decimal
    category: str = \"otros\"
    quantity: Decimal = Decimal(\"1\")
    unit: str | None = None
    unit_price: Decimal | None = None
    notes: str | None = None
"""
if old in t:
    t = t.replace(old, new, 1)

needle = '''    cur.execute(sql.SQL("""
        ALTER TABLE {}.payables
        ADD COLUMN IF NOT EXISTS work_item_id uuid NULL
    """).format(S))
'''
addition = '''    cur.execute(sql.SQL("""
        ALTER TABLE {}.payables
        ADD COLUMN IF NOT EXISTS work_item_id uuid NULL
    """).format(S))

    cur.execute(sql.SQL("""
        ALTER TABLE {}.work_costs
        ADD COLUMN IF NOT EXISTS work_item_id uuid NULL
    """).format(S))
'''
if needle in t and 'ALTER TABLE {}.work_costs' not in t:
    t = t.replace(needle, addition, 1)

old = '''        cur.execute(sql.SQL("""
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
        return cur.fetchone()
'''
new = '''        cur.execute(sql.SQL("""
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
            quantity = body.quantity if body.quantity and body.quantity > 0 else Decimal(\"1\")
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
'''
if old not in t:
    raise SystemExit('ERROR: bloque create_payable no encontrado')
t = t.replace(old, new, 1)

needle = '''        cur.execute(
            sql.SQL("UPDATE {}.payables SET status=%s WHERE id=%s").format(S),
            [status,payable_id],
        )

        return {
'''
replacement = '''        cur.execute(
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
'''
if needle not in t:
    raise SystemExit('ERROR: actualización payable no encontrada')
t = t.replace(needle, replacement, 1)
p.write_text(t, encoding='utf-8')

# work_detail.py
p = ROOT / 'backend/app/routers/work_detail.py'
t = p.read_text(encoding='utf-8')
old = '''        costs = _rows(cur, """
            SELECT wc.*, s.name AS supplier_name
            FROM {}.work_costs wc
            LEFT JOIN {}.suppliers s ON s.id=wc.supplier_id
            WHERE wc.work_id=%s ORDER BY wc.cost_date DESC, wc.created_at DESC
        """, [work_id])
'''
new = '''        cur.execute(sql.SQL("""
            ALTER TABLE {}.work_costs
            ADD COLUMN IF NOT EXISTS work_item_id uuid NULL
        """).format(S))

        costs = _rows(cur, """
            SELECT wc.*, s.name AS supplier_name,
                   wi.description AS work_item_description,
                   wi.code AS work_item_code
            FROM {}.work_costs wc
            LEFT JOIN {}.suppliers s ON s.id=wc.supplier_id
            LEFT JOIN {}.work_items wi ON wi.id=wc.work_item_id
            WHERE wc.work_id=%s ORDER BY wc.cost_date DESC, wc.created_at DESC
        """, [work_id])
'''
if old not in t:
    raise SystemExit('ERROR: consulta costs no encontrada')
t = t.replace(old, new, 1)
p.write_text(t, encoding='utf-8')

# FinancePayables.tsx
p = ROOT / 'front/src/components/FinancePayables.tsx'
t = p.read_text(encoding='utf-8')
needle = '''    amount:total,
    category:f.category||'otros',
    notes:detail,
'''
replacement = '''    amount:total,
    category:f.category||'otros',
    quantity:Number(f.quantity||1),
    unit:String(f.unit||'').trim()||null,
    unit_price:Number(f.unit_price||0),
    notes:detail,
'''
if needle not in t:
    raise SystemExit('ERROR: payload frontend no encontrado')
t = t.replace(needle, replacement, 1)
p.write_text(t, encoding='utf-8')

print('OK: sincronización Por pagar -> Costos de Obra aplicada.')