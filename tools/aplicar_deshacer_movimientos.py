from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

main_path = ROOT / "backend/app/main.py"
main = main_path.read_text(encoding="utf-8")

imp = "from .routers.financial_movements import router as financial_movements_router\n"
anchor_imp = "from .routers.service_documents import router as service_documents_router\n"
if imp not in main:
    if anchor_imp not in main:
        raise SystemExit("ERROR: no encontré el punto de importación en backend/app/main.py")
    main = main.replace(anchor_imp, anchor_imp + imp)

inc = "app.include_router(financial_movements_router)\n"
anchor_inc = "app.include_router(service_documents_router)\n"
if inc not in main:
    if anchor_inc not in main:
        raise SystemExit("ERROR: no encontré el punto de routers en backend/app/main.py")
    main = main.replace(anchor_inc, anchor_inc + inc)

main_path.write_text(main, encoding="utf-8")

modules_path = ROOT / "front/src/components/Modules.tsx"
text = modules_path.read_text(encoding="utf-8")

needle = """  const monthLabel=(()=>{
    const [y,m]=month.split('-').map(Number);
    const label=new Intl.DateTimeFormat('es-AR',{month:'long',year:'numeric'}).format(new Date(y,m-1,1));
    return label.charAt(0).toUpperCase()+label.slice(1);
  })();

  return <>"""

replacement = """  const monthLabel=(()=>{
    const [y,m]=month.split('-').map(Number);
    const label=new Intl.DateTimeFormat('es-AR',{month:'long',year:'numeric'}).format(new Date(y,m-1,1));
    return label.charAt(0).toUpperCase()+label.slice(1);
  })();

  const undoMovement=async(x:any)=>{
    const type=String(x.type||'').toLowerCase();
    const action=type==='ingreso'?'cobro / ingreso':type==='egreso'?'pago / egreso':'movimiento';
    const ok=confirm(
      `¿Eliminar este ${action} de ${fullMoney(x.amount,accountMap[x.account_id]?.currency||'ARS')}?\\n\\n`+
      `El saldo de la cuenta volverá automáticamente al valor anterior. `+
      `Si está vinculado a una factura, también se recalculará su saldo pendiente.`
    );
    if(!ok)return;
    try{
      await api.post(`/api/financial-movements/${x.id}/undo`,{});
      await load();
    }catch(e:any){
      alert(e.message||String(e));
    }
  };

  return <>"""

if "const undoMovement=async(x:any)=>" not in text:
    if needle not in text:
        raise SystemExit("ERROR: no encontré el bloque monthLabel en Modules.tsx")
    text = text.replace(needle, replacement)

old_head = "<thead><tr><th>Fecha</th><th>Cuenta</th><th>Tipo</th><th>Concepto</th><th>Monto</th></tr></thead>"
new_head = "<thead><tr><th>Fecha</th><th>Cuenta</th><th>Tipo</th><th>Concepto</th><th>Monto</th><th>Acciones</th></tr></thead>"
if old_head in text:
    text = text.replace(old_head, new_head)

old_cell = """              <td><b>{type==='egreso'?'- ':type==='ingreso'?'+ ':''}{fullMoney(x.amount,acc?.currency||'ARS')}</b></td>
            </tr>"""
new_cell = """              <td><b>{type==='egreso'?'- ':type==='ingreso'?'+ ':''}{fullMoney(x.amount,acc?.currency||'ARS')}</b></td>
              <td><button className="mini-button danger-text" onClick={()=>undoMovement(x)}>Eliminar</button></td>
            </tr>"""
if "onClick={()=>undoMovement(x)}" not in text:
    if old_cell not in text:
        raise SystemExit("ERROR: no encontré la fila de movimientos en Modules.tsx")
    text = text.replace(old_cell, new_cell)

modules_path.write_text(text, encoding="utf-8")
print("OK: actualización aplicada.")
