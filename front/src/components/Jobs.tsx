'use client';

import { useEffect, useMemo, useState } from 'react';
import { api } from '@/src/lib/api';
import { money } from '@/src/lib/format';
import { Card, Empty, ErrorBox, Loading, SectionTitle, Status } from './ui';
import { Works } from './Modules';
import { ServiceManager } from './ServiceManager';
import { WorkDetail } from './WorkDetail';
import { WorksBoard } from './WorksBoard';
import { ServiceDetail } from './ServiceDetail';

type Tab = 'all' | 'works' | 'services';
type Client = { id:string; name:string };
type Work = { id:string; name:string; client_id:string; status:string; contract_amount:number; type?:string };
type Service = { id:string; name:string; client_id:string; status:string; contract_amount:number; service_type?:string };

type Unified = {
  id:string;
  kind:'obra'|'servicio';
  name:string;
  client_id:string;
  status:string;
  value:number;
  subtype:string;
};

export function Jobs(){
  const [tab,setTab]=useState<Tab>('all');
  const [works,setWorks]=useState<Work[]>([]);
  const [services,setServices]=useState<Service[]>([]);
  const [clients,setClients]=useState<Client[]>([]);
  const [loading,setLoading]=useState(true);
  const [error,setError]=useState('');
  const [query,setQuery]=useState('');
  const [selected,setSelected]=useState<{kind:'obra'|'servicio';id:string}|null>(null);

  async function load(){
    setLoading(true); setError('');
    try{
      const [w,s,c]=await Promise.all([
        api.list<Work>('works','?limit=500'),
        api.list<Service>('services','?limit=500'),
        api.list<Client>('clients','?limit=500'),
      ]);
      setWorks(w); setServices(s); setClients(c);
    }catch(e:any){ setError(e?.message||String(e)); }
    finally{ setLoading(false); }
  }

  useEffect(()=>{ void load(); },[]);

  const clientMap=useMemo(()=>Object.fromEntries(clients.map(c=>[c.id,c.name])),[clients]);
  const rows=useMemo<Unified[]>(()=>[
    ...works.map(w=>({id:w.id,kind:'obra' as const,name:w.name,client_id:w.client_id,status:w.status,value:Number(w.contract_amount||0),subtype:w.type||'obra'})),
    ...services.map(s=>({id:s.id,kind:'servicio' as const,name:s.name,client_id:s.client_id,status:s.status,value:Number(s.contract_amount||0),subtype:s.service_type||'servicio'})),
  ],[works,services]);

  const filtered=useMemo(()=>{
    const q=query.trim().toLowerCase();
    return !q?rows:rows.filter(r=>`${r.name} ${clientMap[r.client_id]||''} ${r.kind} ${r.status}`.toLowerCase().includes(q));
  },[rows,query,clientMap]);

  if(selected?.kind==='obra') return <WorkDetail workId={selected.id} onBack={()=>{setSelected(null);void load();}}/>;
  if(selected?.kind==='servicio') return <ServiceDetail serviceId={selected.id} onBack={()=>{setSelected(null);void load();}}/>;

  return <div className="page-stack">
    <SectionTitle title="Trabajos" subtitle="Obras y servicios de la empresa en un solo lugar."/>
    <div className="tabs standalone">
      <button className={tab==='all'?'active':''} onClick={()=>setTab('all')}>Todos</button>
      <button className={tab==='works'?'active':''} onClick={()=>setTab('works')}>Obras</button>
      <button className={tab==='services'?'active':''} onClick={()=>setTab('services')}>Servicios</button>
    </div>

    {tab==='works'&&<WorksBoard/>}
    {tab==='services'&&<ServiceManager embedded/>}
    {tab==='all'&&(
      error?<ErrorBox message={error} onRetry={load}/>:loading?<Loading/>:<Card>
        <div className="table-toolbar">
          <input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Buscar trabajos…"/>
          <span className="record-count">{filtered.length} registros</span>
        </div>
        {filtered.length===0?<Empty text="Todavía no hay trabajos."/>:<div className="table-wrap"><table>
          <thead><tr><th>Trabajo</th><th>Cliente</th><th>Tipo</th><th>Modalidad</th><th>Estado</th><th>Valor</th></tr></thead>
          <tbody>{filtered.map(r=><tr key={`${r.kind}-${r.id}`} className="clickable-row" onClick={()=>setSelected({kind:r.kind,id:r.id})}>
            <td><b>{r.name}</b></td>
            <td>{clientMap[r.client_id]||'—'}</td>
            <td><Status tone={r.kind==='obra'?'blue':'green'}>{r.kind==='obra'?'Obra':'Servicio'}</Status></td>
            <td>{r.subtype}</td>
            <td><Status tone={r.status==='activo'?'green':r.status==='cancelado'?'red':'blue'}>{r.status}</Status></td>
            <td><b>{money(r.value)}</b></td>
          </tr>)}</tbody>
        </table></div>}
      </Card>
    )}
  </div>;
}
