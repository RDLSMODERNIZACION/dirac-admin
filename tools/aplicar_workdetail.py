from pathlib import Path
import re

path = Path('front/src/components/WorkDetail.tsx')
if not path.exists():
    raise SystemExit('No encontré front/src/components/WorkDetail.tsx. Ejecutá este script desde la raíz del repositorio.')

text = path.read_text(encoding='utf-8')

new_documents = r'''function Documents({workId,rows,reload}:{workId:string;rows:any[];reload:()=>void}){
 const [open,setOpen]=useState(false); const [edit,setEdit]=useState<any>(null); const [busy,setBusy]=useState<string>('');
 const docs=rows;
 const upload=async(fd:FormData)=>{await api.upload('/api/work-documents/upload',fd);setOpen(false);reload()};
 const view=async(id:string)=>{const r=await api.get<any>(`/api/work-documents/${id}/signed-url`);if(r.url)window.open(r.url,'_blank')};
 const request=async(path:string,init:RequestInit)=>{const headers=new Headers(init.headers||{});const key=process.env.NEXT_PUBLIC_API_KEY||'';if(key)headers.set('X-API-Key',key);const base=(process.env.NEXT_PUBLIC_API_URL||'https://dirac-admin.onrender.com').replace(/\/$/,'');const res=await fetch(`${base}${path}`,{...init,headers});if(!res.ok){const b=await res.json().catch(()=>({}));throw new Error(typeof b.detail==='string'?b.detail:`Error ${res.status}`)}return res.status===204?null:res.json().catch(()=>null)};
 const saveEdit=async(fd:FormData)=>{if(!edit)return;setBusy(edit.id);try{await request(`/api/work-documents/${edit.id}`,{method:'PATCH',body:fd});setEdit(null);reload()}finally{setBusy('')}};
 const remove=async(r:any)=>{if(!confirm(`¿Eliminar el documento “${r.title}”? El PDF también se borrará de Supabase Storage.`))return;setBusy(r.id);try{await request(`/api/work-documents/${r.id}`,{method:'DELETE'});reload()}catch(e:any){alert(e.message)}finally{setBusy('')}};
 return <Card><SectionTitle title="Documentación de obra" subtitle="Acá quedan contrato, presupuesto, certificados, remitos, planos, memorias, facturas de proveedor y demás documentación técnica." action={<button className="primary-button" onClick={()=>setOpen(true)}>+ Subir PDF</button>}/>{docs.length===0?<Empty text="Todavía no hay documentación cargada."/>:<div className="document-grid">{docs.map((r:any)=><div className="document-card" key={r.id}><span className="doc-type">{r.document_type.replaceAll('_',' ')}</span><b>{r.title}</b><small>{r.file_name}</small><small>{dateAR(r.document_date)}</small><div style={{display:'flex',gap:8,flexWrap:'wrap',marginTop:4}}><button className="mini-button" onClick={()=>view(r.id)}>Ver PDF</button><button className="mini-button" disabled={busy===r.id} onClick={()=>setEdit(r)}>Editar</button><button className="mini-button danger-text" disabled={busy===r.id} onClick={()=>remove(r)}>{busy===r.id?'Procesando…':'Eliminar'}</button></div></div>)}</div>}{open&&<UploadModal workId={workId} onClose={()=>setOpen(false)} onSave={upload}/>} {edit&&<DocumentEditModal document={edit} onClose={()=>setEdit(null)} onSave={saveEdit}/>}</Card>
}
'''

pattern = re.compile(r'function Documents\(\{workId,rows,reload\}.*?\n\}\n\n\nfunction Contract', re.S)
match = pattern.search(text)
if not match:
    # tolerar dos saltos en lugar de tres
    pattern = re.compile(r'function Documents\(\{workId,rows,reload\}.*?\n\}\n\nfunction Contract', re.S)
    match = pattern.search(text)
if not match:
    raise SystemExit('No pude ubicar la función Documents. No se modificó nada.')
text = text[:match.start()] + new_documents + '\n\nfunction Contract' + text[match.end():]

modal = r'''
function DocumentEditModal({document,onClose,onSave}:{document:any;onClose:()=>void;onSave:(fd:FormData)=>Promise<void>}){
 const [type,setType]=useState(document.document_type||'otro'); const [title,setTitle]=useState(document.title||''); const [description,setDescription]=useState(document.description||''); const [file,setFile]=useState<File|null>(null); const [saving,setSaving]=useState(false);
 const types=['contrato','presupuesto','certificacion','factura_proveedor','remito','plano','memoria_tecnica','acta','otro']; const linked=!!document.related_type;
 const submit=async(e:any)=>{e.preventDefault();const fd=new FormData();fd.append('document_type',type);fd.append('title',title);fd.append('description',description);if(file)fd.append('file',file);setSaving(true);try{await onSave(fd)}catch(x:any){alert(x.message)}finally{setSaving(false)}};
 return <div className="modal-backdrop"><div className="modal"><div className="modal-head"><div><h2>Editar documento</h2><p>{linked?'Documento vinculado: el tipo se mantiene para no romper su relación con facturación/cobros.':'Podés cambiar los datos o reemplazar el PDF.'}</p></div><button className="close-button" onClick={onClose}>×</button></div><form onSubmit={submit}><div className="form-grid"><label className="field"><span>Tipo</span><select disabled={linked} value={type} onChange={e=>setType(e.target.value)}>{linked&&!types.includes(type)&&<option value={type}>{type}</option>}{types.map(x=><option key={x} value={x}>{x.replaceAll('_',' ')}</option>)}</select></label><label className="field"><span>Título</span><input required value={title} onChange={e=>setTitle(e.target.value)}/></label><label className="field full"><span>Descripción</span><input value={description} onChange={e=>setDescription(e.target.value)}/></label><label className="field full"><span>Reemplazar PDF (opcional)</span><input type="file" accept="application/pdf,.pdf" onChange={e=>setFile(e.target.files?.[0]||null)}/><small>Si no elegís un archivo, se conserva el PDF actual.</small></label></div><div className="modal-actions"><button type="button" className="ghost-button" onClick={onClose}>Cancelar</button><button className="primary-button" disabled={saving}>{saving?'Guardando…':'Guardar cambios'}</button></div></form></div></div>
}
'''

anchor = '\nfunction RelatedUploadModal('
if 'function DocumentEditModal(' not in text:
    idx = text.find(anchor)
    if idx < 0:
        raise SystemExit('No pude ubicar RelatedUploadModal para insertar el editor. No se guardó el archivo.')
    text = text[:idx] + '\n' + modal + text[idx:]

path.write_text(text, encoding='utf-8')
print('OK: WorkDetail.tsx actualizado sin reemplazar el resto de la ficha de obra.')
