'use client';
import { useCallback, useEffect, useMemo, useState } from 'react';
import { api } from '@/src/lib/api';
import { dateAR, money } from '@/src/lib/format';
import { Card, Empty, ErrorBox, Loading, SectionTitle, Status } from './ui';
import { ServiceDetail } from './ServiceDetail';

type Client = { id:string; name:string };
type Service = {
  id:string; code:string; client_id:string; name:string; description?:string|null;
  service_type:string; billing_frequency:string; billing_amount:number; contract_amount:number;
  billing_day?:number|null; start_date?:string|null; end_date?:string|null; duration_months?:number|null;
  status:string; is_contract:boolean; notes?:string|null;
};

type Form = {
  client_id:string; name:string; description:string; service_type:string; billing_amount:string;
  billing_day:string; start_date:string; duration_months:string; is_contract:boolean; notes:string;
};

const today=()=>new Date().toISOString().slice(0,10);
const emptyForm=():Form=>({client_id:'',name:'',description:'',service_type:'mensual',billing_amount:'',billing_day:'',start_date:today(),duration_months:'1',is_contract:true,notes:''});

export function ServiceManager(){
  const [rows,setRows]=useState<Service[]>([]); const [clients,setClients]=useState<Client[]>([]);
  const [loading,setLoading]=useState(true); const [error,setError]=useState(''); const [query,setQuery]=useState('');
  const [modal,setModal]=useState(false); const [editing,setEditing]=useState<Service|null>(null); const [selected,setSelected]=useState<string|null>(null); const [form,setForm]=useState<Form>(emptyForm()); const [saving,setSaving]=useState(false);

  const load=useCallback(async()=>{setLoading(true);setError('');try{const [s,c]=await Promise.all([api.list<Service>('services','?limit=500'),api.list<Client>('clients','?limit=500')]);setRows(s);setClients(c)}catch(e:any){setError(e.message||String(e))}finally{setLoading(false)}},[]);
  useEffect(()=>{void load()},[load]);
  const clientMap=useMemo(()=>Object.fromEntries(clients.map(c=>[c.id,c.name])),[clients]);
  const filtered=useMemo(()=>{const q=query.trim().toLowerCase();return !q?rows:rows.filter(r=>JSON.stringify(r).toLowerCase().includes(q))},[rows,query]);

  function openNew(){setEditing(null);setForm(emptyForm());setModal(true)}
  function openEdit(r:Service){setEditing(r);setForm({client_id:r.client_id||'',name:r.name||'',description:r.description||'',service_type:r.service_type||'mensual',billing_amount:String(r.billing_amount??''),billing_day:r.billing_day==null?'':String(r.billing_day),start_date:r.start_date?String(r.start_date).slice(0,10):today(),duration_months:r.duration_months==null?'1':String(r.duration_months),is_contract:Boolean(r.is_contract),notes:r.notes||''});setModal(true)}
  async function remove(r:Service){if(!confirm(`¿Eliminar el servicio ${r.name}?`))return;try{await api.remove('services',r.id);await load()}catch(e:any){alert(e.message)}}
  async function submit(e:React.FormEvent){e.preventDefault();setSaving(true);try{
    const payload:any={client_id:form.client_id,name:form.name.trim(),description:form.description.trim()||null,service_type:form.service_type,billing_amount:Number(form.billing_amount||0),billing_day:form.billing_day===''?null:Number(form.billing_day),start_date:form.start_date||null,is_contract:form.is_contract,notes:form.notes.trim()||null};
    if(form.service_type==='mensual') payload.duration_months=Number(form.duration_months||0);
    if(editing) await api.update('services',editing.id,payload); else await api.create('services',payload);
    setModal(false);setEditing(null);await load();
  }catch(e:any){alert(e?.message||'No se pudo guardar el servicio')}finally{setSaving(false)}}

  if(selected) return <ServiceDetail serviceId={selected} onBack={()=>{setSelected(null);void load();}}/>;

  return <div className="page-stack"><SectionTitle title="Servicios" subtitle="Servicios puntuales o recurrentes. Los mensualizados calculan automáticamente código, vencimiento contractual y valor total." action={<button className="primary-button" onClick={openNew}>+ Nuevo servicio</button>}/>
    {error?<ErrorBox message={error} onRetry={load}/>:loading?<Loading/>:<Card><div className="table-toolbar"><input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Buscar servicios…"/><span className="record-count">{filtered.length} registros</span></div>{filtered.length===0?<Empty text="Todavía no hay servicios."/>:<div className="table-wrap"><table><thead><tr><th>Código</th><th>Servicio</th><th>Cliente</th><th>Modalidad</th><th>Monto período</th><th>Duración</th><th>Valor total</th><th>Vigencia</th><th>Estado</th><th>Acciones</th></tr></thead><tbody>{filtered.map(r=><tr key={r.id} className="clickable-row" onClick={()=>setSelected(r.id)}><td><b>{r.code}</b></td><td>{r.name}</td><td>{clientMap[r.client_id]||'—'}</td><td>{r.service_type}</td><td><b>{money(r.billing_amount)}</b></td><td>{r.duration_months?`${r.duration_months} meses`:'—'}</td><td><b>{money(r.contract_amount)}</b></td><td>{r.start_date?`${dateAR(r.start_date)} → ${dateAR(r.end_date)}`:'—'}</td><td><Status tone={r.status==='activo'?'green':r.status==='cancelado'?'red':'blue'}>{r.status}</Status></td><td><div className="row-actions"><button className="mini-button" onClick={e=>{e.stopPropagation();openEdit(r)}}>Editar</button><button className="mini-button danger-text" onClick={e=>{e.stopPropagation();remove(r)}}>Eliminar</button></div></td></tr>)}</tbody></table></div>}</Card>}
    {modal&&<div className="modal-backdrop" onMouseDown={e=>{if(e.target===e.currentTarget)setModal(false)}}><div className="modal"><div className="modal-head"><div><span className="eyebrow">{editing?'EDITAR':'NUEVO'}</span><h2>{editing?'Editar servicio':'Nuevo servicio'}</h2></div><button className="close-button" onClick={()=>setModal(false)}>×</button></div><form onSubmit={submit}><div className="form-grid">
      <label className="field"><span>Cliente *</span><select required value={form.client_id} onChange={e=>setForm({...form,client_id:e.target.value})}><option value="">Seleccionar…</option>{clients.map(c=><option key={c.id} value={c.id}>{c.name}</option>)}</select></label>
      <label className="field"><span>Servicio *</span><input required value={form.name} onChange={e=>setForm({...form,name:e.target.value})}/></label>
      <label className="field full"><span>Descripción</span><textarea rows={3} value={form.description} onChange={e=>setForm({...form,description:e.target.value})}/></label>
      <label className="field"><span>Modalidad *</span><select value={form.service_type} onChange={e=>setForm({...form,service_type:e.target.value})}><option value="mensual">Mensual</option><option value="puntual">Puntual</option></select></label>
      <label className="field"><span>{form.service_type==='mensual'?'Monto mensual *':'Monto del servicio *'}</span><input type="number" min="0" step="0.01" required value={form.billing_amount} onChange={e=>setForm({...form,billing_amount:e.target.value})}/></label>
      <label className="field"><span>Fecha de inicio *</span><input type="date" required value={form.start_date} onChange={e=>setForm({...form,start_date:e.target.value})}/></label>
      {form.service_type==='mensual'&&<label className="field"><span>Duración (meses) *</span><input type="number" min="1" step="1" required value={form.duration_months} onChange={e=>setForm({...form,duration_months:e.target.value})}/></label>}
      {form.service_type==='mensual'&&<label className="field"><span>Día previsto de cobro</span><input type="number" min="1" max="31" step="1" value={form.billing_day} onChange={e=>setForm({...form,billing_day:e.target.value})}/></label>}
      <label className="field"><span>Tiene contrato</span><input type="checkbox" checked={form.is_contract} onChange={e=>setForm({...form,is_contract:e.target.checked})}/></label>
      {form.service_type==='mensual'&&<div className="field"><span>Valor total calculado</span><div style={{fontWeight:800,fontSize:'1.2rem',padding:'12px 0'}}>{money(Number(form.billing_amount||0)*Number(form.duration_months||0))}</div></div>}
      <label className="field full"><span>Notas</span><textarea rows={3} value={form.notes} onChange={e=>setForm({...form,notes:e.target.value})}/></label>
    </div><div className="modal-actions"><button type="button" className="ghost-button" onClick={()=>setModal(false)}>Cancelar</button><button type="submit" className="primary-button" disabled={saving}>{saving?'Guardando…':'Guardar'}</button></div></form></div></div>}
  </div>
}
