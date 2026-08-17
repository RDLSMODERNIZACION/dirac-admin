'use client';

import { useEffect, useState } from 'react';
import { api } from '@/src/lib/api';

const today=()=>new Date().toISOString().slice(0,10);

export function NewWorkModal({close,done}:{close:()=>void;done:()=>Promise<void>|void}){
 const [clients,setClients]=useState<any[]>([]);
 const [saving,setSaving]=useState(false);
 const [form,setForm]=useState<any>({client_id:'',name:'',description:'',start_date:today(),end_date:'',contract_amount:'',notes:''});
 useEffect(()=>{api.list<any>('clients','?limit=500').then(setClients).catch(e=>alert(e.message))},[]);
 const submit=async(e:any)=>{
  e.preventDefault();setSaving(true);
  try{
   await api.create('works',{client_id:form.client_id,name:String(form.name||'').trim(),description:String(form.description||'').trim()||null,start_date:form.start_date||null,end_date:form.end_date||null,contract_amount:Number(form.contract_amount||0),status:'activo',execution_status:'pendiente',type:'obra',notes:String(form.notes||'').trim()||null});
   await done();
  }catch(e:any){alert(e.message||String(e))}finally{setSaving(false)}
 };
 return <div className="modal-backdrop" onMouseDown={e=>{if(e.target===e.currentTarget)close()}}><div className="modal"><div className="modal-head"><div><span className="eyebrow">NUEVA</span><h2>Nueva obra</h2></div><button className="close-button" onClick={close}>×</button></div><form onSubmit={submit}><div className="form-grid">
 <label className="field"><span>Cliente *</span><select required value={form.client_id} onChange={e=>setForm({...form,client_id:e.target.value})}><option value="">Seleccionar…</option>{clients.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></label>
 <label className="field"><span>Nombre *</span><input required value={form.name} onChange={e=>setForm({...form,name:e.target.value})}/></label>
 <label className="field full"><span>Descripción</span><textarea rows={3} value={form.description} onChange={e=>setForm({...form,description:e.target.value})}/></label>
 <label className="field"><span>Inicio</span><input type="date" value={form.start_date} onChange={e=>setForm({...form,start_date:e.target.value})}/></label>
 <label className="field"><span>Fin estimado</span><input type="date" value={form.end_date} onChange={e=>setForm({...form,end_date:e.target.value})}/></label>
 <label className="field"><span>Valor contrato (IVA incluido) *</span><input type="number" min="0" step="0.01" required value={form.contract_amount} onChange={e=>setForm({...form,contract_amount:e.target.value})}/></label>
 <label className="field full"><span>Notas</span><textarea rows={3} value={form.notes} onChange={e=>setForm({...form,notes:e.target.value})}/></label>
 </div><div className="modal-actions"><button type="button" className="ghost-button" onClick={close}>Cancelar</button><button className="primary-button" disabled={saving}>{saving?'Guardando…':'Crear obra'}</button></div></form></div></div>
}

export function NewServiceModal({close,done}:{close:()=>void;done:()=>Promise<void>|void}){
 const [clients,setClients]=useState<any[]>([]);
 const [saving,setSaving]=useState(false);
 const [form,setForm]=useState<any>({client_id:'',name:'',description:'',service_type:'mensual',billing_amount:'',start_date:today(),duration_months:'1',billing_day:'',notes:''});
 useEffect(()=>{api.list<any>('clients','?limit=500').then(setClients).catch(e=>alert(e.message))},[]);
 const submit=async(e:any)=>{
  e.preventDefault();setSaving(true);
  try{
   const payload:any={client_id:form.client_id,name:String(form.name||'').trim(),description:String(form.description||'').trim()||null,service_type:form.service_type,billing_amount:Number(form.billing_amount||0),start_date:form.start_date||null,billing_day:form.billing_day===''?null:Number(form.billing_day),status:'activo',is_contract:true,notes:String(form.notes||'').trim()||null};
   if(form.service_type==='mensual')payload.duration_months=Number(form.duration_months||1);
   await api.create('services',payload);await done();
  }catch(e:any){alert(e.message||String(e))}finally{setSaving(false)}
 };
 return <div className="modal-backdrop" onMouseDown={e=>{if(e.target===e.currentTarget)close()}}><div className="modal"><div className="modal-head"><div><span className="eyebrow">NUEVO</span><h2>Nuevo servicio</h2></div><button className="close-button" onClick={close}>×</button></div><form onSubmit={submit}><div className="form-grid">
 <label className="field"><span>Cliente *</span><select required value={form.client_id} onChange={e=>setForm({...form,client_id:e.target.value})}><option value="">Seleccionar…</option>{clients.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></label>
 <label className="field"><span>Servicio *</span><input required value={form.name} onChange={e=>setForm({...form,name:e.target.value})}/></label>
 <label className="field full"><span>Descripción</span><textarea rows={3} value={form.description} onChange={e=>setForm({...form,description:e.target.value})}/></label>
 <label className="field"><span>Modalidad</span><select value={form.service_type} onChange={e=>setForm({...form,service_type:e.target.value})}><option value="mensual">Mensual</option><option value="puntual">Puntual</option></select></label>
 <label className="field"><span>{form.service_type==='mensual'?'Monto mensual *':'Monto del servicio *'}</span><input type="number" min="0" step="0.01" required value={form.billing_amount} onChange={e=>setForm({...form,billing_amount:e.target.value})}/></label>
 <label className="field"><span>Inicio *</span><input type="date" required value={form.start_date} onChange={e=>setForm({...form,start_date:e.target.value})}/></label>
 {form.service_type==='mensual'&&<label className="field"><span>Duración (meses) *</span><input type="number" min="1" step="1" required value={form.duration_months} onChange={e=>setForm({...form,duration_months:e.target.value})}/></label>}
 {form.service_type==='mensual'&&<label className="field"><span>Día de facturación</span><input type="number" min="1" max="31" value={form.billing_day} onChange={e=>setForm({...form,billing_day:e.target.value})}/></label>}
 <label className="field full"><span>Notas</span><textarea rows={3} value={form.notes} onChange={e=>setForm({...form,notes:e.target.value})}/></label>
 </div><div className="modal-actions"><button type="button" className="ghost-button" onClick={close}>Cancelar</button><button className="primary-button" disabled={saving}>{saving?'Guardando…':'Crear servicio'}</button></div></form></div></div>
}
