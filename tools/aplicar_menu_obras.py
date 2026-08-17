from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
p = ROOT / 'front/src/components/WorksBoard.tsx'
t = p.read_text(encoding='utf-8')

old = " const [selected,setSelected]=useState<string|null>(null);\n"
new = ''' const [selected,setSelected]=useState<string|null>(null);
 const [menuOpen,setMenuOpen]=useState<string|null>(null);
 const [editing,setEditing]=useState<any|null>(null);
 const [editForm,setEditForm]=useState<any>({});
 const [savingEdit,setSavingEdit]=useState(false);
'''
if old not in t: raise SystemExit('ERROR: estado selected no encontrado')
t = t.replace(old,new,1)

needle = " if(selected)return <WorkDetail workId={selected} onBack={()=>{setSelected(null);void load()}}/>;"
insert = ''' const openEdit=(r:any)=>{
   setMenuOpen(null);
   setEditing(r);
   setEditForm({
     name:r.name||'',
     start_date:r.start_date?String(r.start_date).slice(0,10):'',
     end_date:r.end_date?String(r.end_date).slice(0,10):'',
     contract_amount:String(r.contract_amount??''),
   });
 };

 const saveEdit=async(e:any)=>{
   e.preventDefault();
   if(!editing)return;
   setSavingEdit(true);
   try{
     await api.update('works',editing.id,{
       name:String(editForm.name||'').trim(),
       start_date:editForm.start_date||null,
       end_date:editForm.end_date||null,
       contract_amount:Number(editForm.contract_amount||0),
     });
     setEditing(null);
     await load();
   }catch(err:any){alert(err?.message||String(err))}
   finally{setSavingEdit(false)}
 };

 const removeWork=async(r:any)=>{
   setMenuOpen(null);
   if(!confirm(`¿Eliminar la obra "${r.name}"?`))return;
   try{
     await api.remove('works',r.id);
     await load();
   }catch(err:any){alert(err?.message||String(err))}
 };

 if(selected)return <WorkDetail workId={selected} onBack={()=>{setSelected(null);void load()}}/>;'''
if needle not in t: raise SystemExit('ERROR: if selected no encontrado')
t = t.replace(needle,insert,1)

old = '<th>Riesgo</th><th>Acciones</th>'
new = '<th>Riesgo</th><th className="work-menu-head"></th>'
if old not in t: raise SystemExit('ERROR: encabezado Acciones no encontrado')
t = t.replace(old,new,1)

old = "          return <tr key={r.id} className={r.is_finished?'finished-row':''}>"
new = "          return <tr key={r.id} className={`${r.is_finished?'finished-row':''} clickable-row`} onClick={()=>setSelected(r.id)}>"
if old not in t: raise SystemExit('ERROR: fila no encontrada')
t = t.replace(old,new,1)

old = '<td><button className="mini-button" onClick={()=>setSelected(r.id)}>Ver detalle</button></td>'
new = '''<td className="work-menu-cell" onClick={e=>e.stopPropagation()}>
              <div className="work-row-menu">
                <button className="work-row-menu-button" aria-label="Opciones" onClick={()=>setMenuOpen(menuOpen===r.id?null:r.id)}>⋯</button>
                {menuOpen===r.id&&<div className="work-row-menu-popover">
                  <button onClick={()=>{setMenuOpen(null);openEdit(r)}}>Editar</button>
                  <button className="danger-text" onClick={()=>removeWork(r)}>Eliminar</button>
                </div>}
              </div>
            </td>'''
if old not in t: raise SystemExit('ERROR: botón Ver detalle no encontrado')
t = t.replace(old,new,1)

modal = '''
   {editing&&<div className="modal-backdrop" onMouseDown={e=>{if(e.target===e.currentTarget)setEditing(null)}}>
     <div className="modal">
       <div className="modal-head"><div><span className="eyebrow">EDITAR OBRA</span><h2>{editing.name}</h2></div><button className="close-button" onClick={()=>setEditing(null)}>×</button></div>
       <form onSubmit={saveEdit}>
         <div className="form-grid">
           <label className="field full"><span>Nombre</span><input required value={editForm.name||''} onChange={e=>setEditForm({...editForm,name:e.target.value})}/></label>
           <label className="field"><span>Inicio</span><input type="date" value={editForm.start_date||''} onChange={e=>setEditForm({...editForm,start_date:e.target.value})}/></label>
           <label className="field"><span>Fin estimado</span><input type="date" value={editForm.end_date||''} onChange={e=>setEditForm({...editForm,end_date:e.target.value})}/></label>
           <label className="field"><span>Valor contrato IVA incluido</span><input type="number" min="0" step="0.01" value={editForm.contract_amount||''} onChange={e=>setEditForm({...editForm,contract_amount:e.target.value})}/></label>
         </div>
         <div className="modal-actions"><button type="button" className="ghost-button" onClick={()=>setEditing(null)}>Cancelar</button><button className="primary-button" disabled={savingEdit}>{savingEdit?'Guardando…':'Guardar cambios'}</button></div>
       </form>
     </div>
   </div>}
'''

marker = '\n </div>\n}'
pos = t.rfind(marker)
if pos == -1: raise SystemExit('ERROR: cierre final no encontrado')
t = t[:pos] + modal + t[pos:]
p.write_text(t,encoding='utf-8')

p = ROOT / 'front/app/globals.css'
css = p.read_text(encoding='utf-8')
extra = '''
/* Obras: menú sutil de tres puntos */
.work-menu-head{width:42px;min-width:42px}
.work-menu-cell{width:42px;min-width:42px;padding-left:4px!important;padding-right:4px!important;overflow:visible!important}
.work-row-menu{position:relative;display:flex;justify-content:flex-end}
.work-row-menu-button{width:32px;height:32px;border:0;background:transparent;border-radius:8px;font-size:22px;line-height:1;color:#718096;cursor:pointer}
.work-row-menu-button:hover{background:#f1f5f9;color:#1e293b}
.work-row-menu-popover{position:absolute;right:0;top:34px;z-index:100;min-width:130px;background:#fff;border:1px solid #e2e8f0;border-radius:10px;box-shadow:0 12px 30px rgba(15,23,42,.14);padding:5px}
.work-row-menu-popover button{display:block;width:100%;border:0;background:transparent;text-align:left;padding:9px 11px;border-radius:7px;font-size:13px;font-weight:700;cursor:pointer}
.work-row-menu-popover button:hover{background:#f8fafc}
.works-board-table .clickable-row{cursor:pointer}
'''
if '/* Obras: menú sutil de tres puntos */' not in css:
    css = css.rstrip() + '\n\n' + extra + '\n'
p.write_text(css,encoding='utf-8')
print('OK: menú ⋯ agregado a Obras.')