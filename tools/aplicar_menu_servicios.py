from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

# ============================================================
# BACKEND
# ============================================================
p=ROOT/"backend/app/routers/services_board.py"
t=p.read_text(encoding="utf-8")
marker='@router.delete("/{service_id}")'
if marker not in t:
    t=t.rstrip()+'\n\n@router.delete("/{service_id}")\ndef delete_service_from_board(service_id: str):\n    """\n    Elimina un servicio cargado por error si todavía no tiene movimientos de caja.\n    Limpia períodos, cuentas por cobrar sin cobros y documentos asociados.\n    """\n    with db_cursor() as cur:\n        cur.execute(sql.SQL("SELECT * FROM {}.services WHERE id=%s FOR UPDATE").format(S), [service_id])\n        service = cur.fetchone()\n        if not service:\n            from fastapi import HTTPException\n            raise HTTPException(404, "Servicio no encontrado")\n\n        # Si hubo cualquier movimiento de caja ligado al servicio, no permitir borrado.\n        cur.execute(sql.SQL("""\n            SELECT COALESCE(SUM(amount),0) AS total\n            FROM {}.financial_movements\n            WHERE service_id=%s\n        """).format(S), [service_id])\n        cash_total = D(cur.fetchone()["total"])\n        if cash_total > 0:\n            from fastapi import HTTPException\n            raise HTTPException(\n                400,\n                "No se puede eliminar este servicio porque ya tiene cobros o movimientos de caja registrados."\n            )\n\n        # Verificación adicional por cuentas por cobrar vinculadas.\n        cur.execute(sql.SQL("""\n            SELECT COALESCE(SUM(fm.amount),0) AS paid\n            FROM {}.financial_movements fm\n            JOIN {}.receivables r ON r.id=fm.receivable_id\n            WHERE r.service_id=%s AND fm.type=\'ingreso\'\n        """).format(S, S), [service_id])\n        paid = D(cur.fetchone()["paid"])\n        if paid > 0:\n            from fastapi import HTTPException\n            raise HTTPException(\n                400,\n                "No se puede eliminar este servicio porque ya tiene cobros registrados."\n            )\n\n        # Desvincular períodos de sus cuentas por cobrar.\n        cur.execute(sql.SQL("""\n            UPDATE {}.service_periods\n            SET receivable_id=NULL\n            WHERE service_id=%s\n        """).format(S), [service_id])\n\n        # Documentos: se eliminan los registros de BD.\n        # Los archivos físicos del storage pueden quedar para limpieza administrativa posterior.\n        cur.execute(sql.SQL("""\n            DELETE FROM {}.service_documents\n            WHERE service_id=%s\n        """).format(S), [service_id])\n\n        # Eliminar cuentas por cobrar sin movimientos.\n        cur.execute(sql.SQL("""\n            DELETE FROM {}.receivables\n            WHERE service_id=%s\n        """).format(S), [service_id])\n\n        # Eliminar períodos.\n        cur.execute(sql.SQL("""\n            DELETE FROM {}.service_periods\n            WHERE service_id=%s\n        """).format(S), [service_id])\n\n        # Finalmente el servicio.\n        cur.execute(sql.SQL("""\n            DELETE FROM {}.services\n            WHERE id=%s\n        """).format(S), [service_id])\n\n    return {"ok": True}\n'+"\n"
p.write_text(t,encoding="utf-8")

# ============================================================
# FRONTEND
# ============================================================
p=ROOT/"front/src/components/ServicesBoard.tsx"
t=p.read_text(encoding="utf-8")

# Estado del menú
old=""" const [savingEdit,setSavingEdit]=useState(false);
"""
new=""" const [savingEdit,setSavingEdit]=useState(false);
 const [menuOpen,setMenuOpen]=useState<string|null>(null);
"""
if old not in t:
    raise SystemExit("ERROR: no encontré estado savingEdit")
t=t.replace(old,new,1)

# Agregar función eliminar
needle=""" const saveEdit=async(e:any)=>{
"""
idx=t.find(needle)
if idx==-1:
    raise SystemExit("ERROR: no encontré saveEdit")

# Insertamos función antes de saveEdit
delete_fn=""" const removeService=async(r:any)=>{
   setMenuOpen(null);
   const ok=confirm(`¿Eliminar el servicio "${r.name}"? Esta acción eliminará sus períodos y facturas pendientes si todavía no tiene cobros.`);
   if(!ok)return;
   try{
     await api.remove('services-board',r.id);
     await load();
   }catch(err:any){
     alert(err?.message||String(err));
   }
 };

"""
t=t[:idx]+delete_fn+t[idx:]

# Sacar botón Editar del nombre
old="""              <div style={{display:'flex',alignItems:'center',gap:8,flexWrap:'wrap'}}>
                <b>{r.name}</b>
                <button className="mini-button" onClick={e=>{e.stopPropagation();openEdit(r)}}>Editar</button>
              </div>
"""
new="""              <div style={{display:'flex',alignItems:'center',gap:8,flexWrap:'wrap'}}>
                <b>{r.name}</b>
              </div>
"""
if old not in t:
    raise SystemExit("ERROR: no encontré botón Editar en nombre")
t=t.replace(old,new,1)

# Agregar encabezado vacío
old="""          <th>Períodos</th><th>Facturado</th><th>Cobrado</th><th>Pendiente</th>
"""
new="""          <th>Períodos</th><th>Facturado</th><th>Cobrado</th><th>Pendiente</th><th className="service-menu-head"></th>
"""
if old not in t:
    raise SystemExit("ERROR: no encontré encabezado final")
t=t.replace(old,new,1)

# Agregar menú al final de cada fila
old="""            <td className={Number(r.pending_collection)>0?'pending-money':''}><b>{moneyFull(r.pending_collection)}</b></td>


          </tr>
"""
new="""            <td className={Number(r.pending_collection)>0?'pending-money':''}><b>{moneyFull(r.pending_collection)}</b></td>
            <td className="service-menu-cell" onClick={e=>e.stopPropagation()}>
              <div className="service-row-menu">
                <button
                  className="service-row-menu-button"
                  aria-label="Opciones"
                  onClick={()=>setMenuOpen(menuOpen===r.id?null:r.id)}
                >⋯</button>
                {menuOpen===r.id&&<div className="service-row-menu-popover">
                  <button onClick={()=>{setMenuOpen(null);openEdit(r)}}>Editar</button>
                  <button className="danger-text" onClick={()=>removeService(r)}>Eliminar</button>
                </div>}
              </div>
            </td>
          </tr>
"""
if old not in t:
    raise SystemExit("ERROR: no encontré final de fila")
t=t.replace(old,new,1)

p.write_text(t,encoding="utf-8")

# CSS
p=ROOT/"front/app/globals.css"
css=p.read_text(encoding="utf-8")
extra="""
/* Servicios: menú sutil de tres puntos */
.service-menu-head{width:42px;min-width:42px}
.service-menu-cell{width:42px;min-width:42px;padding-left:4px!important;padding-right:4px!important;overflow:visible!important}
.service-row-menu{position:relative;display:flex;justify-content:flex-end}
.service-row-menu-button{
  width:32px;height:32px;border:0;background:transparent;border-radius:8px;
  font-size:22px;line-height:1;color:#718096;cursor:pointer;
}
.service-row-menu-button:hover{background:#f1f5f9;color:#1e293b}
.service-row-menu-popover{
  position:absolute;right:0;top:34px;z-index:50;min-width:125px;
  background:white;border:1px solid #e2e8f0;border-radius:10px;
  box-shadow:0 12px 30px rgba(15,23,42,.14);padding:5px;
}
.service-row-menu-popover button{
  display:block;width:100%;text-align:left;border:0;background:transparent;
  padding:9px 11px;border-radius:7px;cursor:pointer;font-size:13px;font-weight:700;
}
.service-row-menu-popover button:hover{background:#f8fafc}
"""
if "/* Servicios: menú sutil de tres puntos */" not in css:
    css=css.rstrip()+"\n\n"+extra+"\n"
p.write_text(css,encoding="utf-8")

print("OK: menú ⋯ con Editar/Eliminar agregado a Servicios.")
