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
import { ServicesBoard } from './ServicesBoard';

type Tab = 'admin' | 'works' | 'services';
type Client = { id:string; name:string };
type Work = { id:string; name:string; client_id:string; status:string; contract_amount:number; type?:string; end_date?:string|null };
type Service = { id:string; name:string; client_id:string; status:string; contract_amount:number; service_type?:string; end_date?:string|null };

type Unified = {
  id:string;
  kind:'obra'|'servicio';
  name:string;
  client_id:string;
  status:string;
  value:number;
  subtype:string;
  end_date?:string|null;
};

function AdminCheck({row}:{row:any}){
 if(!row?.completed)return <span className="admin-check pending">Pendiente</span>;
 const d=row.completed_date?new Date(`${String(row.completed_date).slice(0,10)}T12:00:00`).toLocaleDateString('es-AR'):'';
 return <span className="admin-check done">OK<small>{d}</small></span>;
}

export function Jobs(){
  const [tab,setTab]=useState<Tab>('admin');
  const [works,setWorks]=useState<Work[]>([]);
  const [services,setServices]=useState<Service[]>([]);
  const [clients,setClients]=useState<Client[]>([]);
  const [loading,setLoading]=useState(true);
  const [error,setError]=useState('');
  const [query,setQuery]=useState('');
  const [adminRows,setAdminRows]=useState<any[]>([]);
  const [selected,setSelected]=useState<{kind:'obra'|'servicio';id:string}|null>(null);

  async function load(){
    setLoading(true); setError('');
    try{
      const [w,s,c,admin]=await Promise.all([
        api.list<Work>('works','?limit=500'),
        api.list<Service>('services','?limit=500'),
        api.list<Client>('clients','?limit=500'),
        api.get<any>('/api/works-board'),
      ]);
      setWorks(w); setServices(s); setClients(c); setAdminRows(admin.works||[]);
    }catch(e:any){ setError(e?.message||String(e)); }
    finally{ setLoading(false); }
  }

  useEffect(()=>{ void load(); },[]);

  const clientMap=useMemo(()=>Object.fromEntries(clients.map(c=>[c.id,c.name])),[clients]);
  const rows=useMemo<Unified[]>(()=>[
    ...works.map(w=>({id:w.id,kind:'obra' as const,name:w.name,client_id:w.client_id,status:w.status,value:Number(w.contract_amount||0),subtype:w.type||'obra',end_date:w.end_date||null})),
    ...services.map(s=>({id:s.id,kind:'servicio' as const,name:s.name,client_id:s.client_id,status:s.status,value:Number(s.contract_amount||0),subtype:s.service_type||'servicio',end_date:s.end_date||null})),
  ],[works,services]);

  const filteredAdmin=useMemo(()=>{
    const q=query.trim().toLowerCase();
    return [...adminRows]
      .filter((r:any)=>!q||`${r.name} ${r.client_name||''}`.toLowerCase().includes(q))
      .sort((a:any,b:any)=>{
        const ad=a.end_date?new Date(`${String(a.end_date).slice(0,10)}T12:00:00`).getTime():Number.MAX_SAFE_INTEGER;
        const bd=b.end_date?new Date(`${String(b.end_date).slice(0,10)}T12:00:00`).getTime():Number.MAX_SAFE_INTEGER;
        return ad-bd;
      });
  },[adminRows,query]);


  if(selected?.kind==='obra') return <WorkDetail workId={selected.id} onBack={()=>{setSelected(null);void load();}}/>;
  if(selected?.kind==='servicio') return <ServiceDetail serviceId={selected.id} onBack={()=>{setSelected(null);void load();}}/>;

  return <div className="page-stack">
    <SectionTitle title="Trabajos" subtitle="Obras y servicios de la empresa en un solo lugar."/>
    <div className="tabs standalone">
      <button className={tab==='admin'?'active':''} onClick={()=>{setTab('admin');void load()}}>Administración</button>
      <button className={tab==='works'?'active':''} onClick={()=>setTab('works')}>Obras</button>
      <button className={tab==='services'?'active':''} onClick={()=>setTab('services')}>Servicios</button>
    </div>

    {tab==='works'&&<WorksBoard/>}
    {tab==='services'&&<ServicesBoard/>}
    {tab==='admin'&&(
      error?<ErrorBox message={error} onRetry={load}/>:loading?<Loading/>:<Card>
        <div className="table-toolbar">
          <input value={query} onChange={e=>setQuery(e.target.value)} placeholder="Buscar obra o cliente…"/>
          <span className="record-count">{filteredAdmin.length} obras</span>
        </div>
        {filteredAdmin.length===0?<Empty text="Todavía no hay obras."/>:<div className="table-wrap"><table className="admin-works-table">
          <thead><tr><th>Obra</th><th>Cliente</th><th>Fecha fin</th><th>Presupuesto</th><th>Contrato</th><th>Certificación</th><th>Factura</th><th>Cobro</th><th>Avance adm.</th></tr></thead>
          <tbody>{filteredAdmin.map((r:any)=>{
            const checklist=r.checklist||{};
            const defs=[['presupuesto','Presupuesto'],['contrato','Contrato'],['certificacion','Certificación'],['factura','Factura'],['cobro','Cobro']] as [string,string][];
            const done=defs.filter(([k])=>!!checklist[k]?.completed).length;
            const progress=Math.round(done/defs.length*100);
            return <tr key={r.id} className="clickable-row" onClick={()=>setSelected({kind:'obra',id:r.id})}>
              <td><b>{r.name}</b></td>
              <td>{r.client_name||'—'}</td>
              <td>{r.end_date?new Date(`${String(r.end_date).slice(0,10)}T12:00:00`).toLocaleDateString('es-AR'):'—'}</td>
              {defs.map(([k])=><td key={k}><AdminCheck row={checklist[k]}/></td>)}
              <td><div className="admin-progress-cell"><b>{progress}%</b><span><i style={{width:`${progress}%`}}/></span></div></td>
            </tr>
          })}</tbody>
        </table></div>}
      </Card>
    )}
  </div>;
}
