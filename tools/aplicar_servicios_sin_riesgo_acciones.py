from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
p = ROOT / "front/src/components/ServicesBoard.tsx"
t = p.read_text(encoding="utf-8")

old_head = '''          <th>Períodos</th><th>Facturado</th><th>Cobrado</th><th>Pendiente</th><th>Próximo período</th><th>Riesgo</th><th>Acciones</th>'''
new_head = '''          <th>Períodos</th><th>Facturado</th><th>Cobrado</th><th>Pendiente</th><th>Próximo período</th>'''
if old_head not in t:
    raise SystemExit("ERROR: no encontré encabezados Riesgo/Acciones en ServicesBoard.tsx")
t = t.replace(old_head, new_head, 1)

old_row = '''          return <tr key={r.id} className={r.effective_status!=='activo'?'finished-row':''}>'''
new_row = '''          return <tr key={r.id} className={`${r.effective_status!=='activo'?'finished-row':''} clickable-row`} onClick={()=>setSelected(r.id)}>'''
if old_row not in t:
    raise SystemExit("ERROR: no encontré la fila de servicios")
t = t.replace(old_row, new_row, 1)

old_tail = '''            <td><Risk level={r.risk_level} reasons={r.risk_reasons}/></td>
            <td><button className="mini-button" onClick={()=>setSelected(r.id)}>Ver detalle</button></td>'''
if old_tail not in t:
    raise SystemExit("ERROR: no encontré celdas Riesgo/Acciones")
t = t.replace(old_tail, '', 1)

p.write_text(t, encoding="utf-8")

p = ROOT / "front/app/globals.css"
css = p.read_text(encoding="utf-8")

extra = """
/* Servicios: tabla compacta sin Riesgo ni Acciones */
.services-board-table td:first-child{min-width:220px}
.services-board-table td:nth-child(2){min-width:180px}
.services-board-table td:nth-child(3){min-width:135px}
.services-board-table td:nth-child(4){min-width:120px}
.services-board-table td:nth-child(5){min-width:125px}
.services-board-table td:nth-child(6),
.services-board-table td:nth-child(7),
.services-board-table td:nth-child(8){min-width:115px}
.services-board-table td:nth-child(9){min-width:125px}
"""

if "/* Servicios: tabla compacta sin Riesgo ni Acciones */" not in css:
    css = css.rstrip() + "\n\n" + extra + "\n"
    p.write_text(css, encoding="utf-8")

print("OK: Servicios sin columnas Riesgo ni Acciones; fila completa abre el detalle.")
