from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# ============================================================
# BACKEND: services_board.py
# ============================================================
p = ROOT / "backend/app/routers/services_board.py"
t = p.read_text(encoding="utf-8")

# 1) El query distingue períodos pendientes totales de períodos YA FACTURABLES.
old = """            COUNT(*) FILTER (WHERE sp.receivable_id IS NULL) AS pending_periods,
            MIN(sp.period_number) FILTER (WHERE sp.receivable_id IS NULL) AS next_period_number,
            MIN(sp.period_start) FILTER (WHERE sp.receivable_id IS NULL) AS next_period_start,
            MIN(sp.due_date) FILTER (WHERE sp.receivable_id IS NULL) AS next_due_date"""
new = """            COUNT(*) FILTER (WHERE sp.receivable_id IS NULL) AS pending_periods,
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
            MIN(sp.due_date) FILTER (WHERE sp.receivable_id IS NULL) AS next_due_date"""
if old not in t:
    raise SystemExit("ERROR: no encontré el bloque de períodos en services_board.py")
t = t.replace(old, new, 1)

# 2) Exponer los nuevos contadores en el SELECT principal.
old = """          COALESCE(periods.pending_periods,0) AS pending_periods,
          periods.next_period_number,"""
new = """          COALESCE(periods.pending_periods,0) AS pending_periods,
          COALESCE(periods.due_pending_periods,0) AS due_pending_periods,
          COALESCE(periods.future_pending_periods,0) AS future_pending_periods,
          periods.next_period_number,"""
if old not in t:
    raise SystemExit("ERROR: no encontré pending_periods en SELECT")
t = t.replace(old, new, 1)

# 3) Variables Python.
old = """        pending_periods = int(r.get("pending_periods") or 0)
        total_periods = int(r.get("total_periods") or 0)
        billed_periods = int(r.get("billed_periods") or 0)"""
new = """        pending_periods = int(r.get("pending_periods") or 0)
        due_pending_periods = int(r.get("due_pending_periods") or 0)
        future_pending_periods = int(r.get("future_pending_periods") or 0)
        total_periods = int(r.get("total_periods") or 0)
        billed_periods = int(r.get("billed_periods") or 0)"""
if old not in t:
    raise SystemExit("ERROR: no encontré variables de períodos")
t = t.replace(old, new, 1)

# 4) El riesgo solo considera períodos cuya fecha de facturación ya llegó.
old = """        if pending_periods >= 2:
            score += 2
            reasons.append("períodos sin facturar")
        elif pending_periods == 1:
            next_due = r.get("next_due_date")
            if next_due and next_due <= today:
                score += 2
                reasons.append("período vencido sin facturar")
            else:
                score += 1"""
new = """        if due_pending_periods >= 2:
            score += 2
            reasons.append("períodos vencidos sin facturar")
        elif due_pending_periods == 1:
            score += 2
            reasons.append("período vencido sin facturar")"""
if old not in t:
    raise SystemExit("ERROR: no encontré lógica de riesgo por períodos")
t = t.replace(old, new, 1)

# 5) En pendiente de cierre, no llamar "sin facturar" a un período futuro.
old = """        if effective_status == "pendiente_cierre":
            score += 3
            if pending_periods > 0:
                reasons.append("vigencia terminada con períodos sin facturar")
            if pending_collection > 0:
                reasons.append("vigencia terminada con saldo pendiente")"""
new = """        if effective_status == "pendiente_cierre":
            if due_pending_periods > 0 or pending_collection > 0:
                score += 3
            if due_pending_periods > 0:
                reasons.append("vigencia terminada con períodos vencidos sin facturar")
            elif future_pending_periods > 0:
                reasons.append("pendiente de fecha de facturación")
            if pending_collection > 0:
                reasons.append("vigencia terminada con saldo pendiente")"""
if old in t:
    t = t.replace(old, new, 1)

p.write_text(t, encoding="utf-8")


# ============================================================
# FRONTEND: ServicesBoard.tsx
# ============================================================
p = ROOT / "front/src/components/ServicesBoard.tsx"
t = p.read_text(encoding="utf-8")

# 1) Sacar Próximo período del encabezado.
old = """          <th>Períodos</th><th>Facturado</th><th>Cobrado</th><th>Pendiente</th><th>Próximo período</th>"""
new = """          <th>Períodos</th><th>Facturado</th><th>Cobrado</th><th>Pendiente</th>"""
if old not in t:
    raise SystemExit("ERROR: no encontré la columna Próximo período")
t = t.replace(old, new, 1)

# 2) La advertencia bajo el servicio solo aparece si el período ya está vencido/facturable.
old = """              {Number(r.pending_periods)>0&&<small className="work-row-note">{r.pending_periods} período{Number(r.pending_periods)===1?'':'s'} sin facturar</small>}"""
new = """              {Number(r.due_pending_periods)>0&&<small className="work-row-note">{r.due_pending_periods} período{Number(r.due_pending_periods)===1?'':'s'} sin facturar</small>}"""
if old not in t:
    raise SystemExit("ERROR: no encontré aviso de períodos sin facturar")
t = t.replace(old, new, 1)

# 3) Sacar la celda Próximo período.
old = """            <td>{r.next_period_number?<><b>Mes {r.next_period_number}</b><small>{dateAR(r.next_period_start)}</small></>:<span>—</span>}</td>"""
if old not in t:
    raise SystemExit("ERROR: no encontré celda Próximo período")
t = t.replace(old, "", 1)

p.write_text(t, encoding="utf-8")


# ============================================================
# CSS: ahora la tabla tiene 8 columnas y puede respirar más.
# ============================================================
p = ROOT / "front/app/globals.css"
css = p.read_text(encoding="utf-8")

extra = """
/* Servicios: sin próximo período y facturación a mes vencido */
.services-board-table td:first-child{min-width:230px}
.services-board-table td:nth-child(2){min-width:185px}
.services-board-table td:nth-child(3){min-width:140px}
.services-board-table td:nth-child(4){min-width:125px}
.services-board-table td:nth-child(5){min-width:130px}
.services-board-table td:nth-child(6),
.services-board-table td:nth-child(7),
.services-board-table td:nth-child(8){min-width:120px}
"""

if "/* Servicios: sin próximo período y facturación a mes vencido */" not in css:
    css = css.rstrip() + "\n\n" + extra + "\n"
    p.write_text(css, encoding="utf-8")

print("OK: Próximo período eliminado y 'sin facturar' solo se marca al llegar la fecha de facturación.")
