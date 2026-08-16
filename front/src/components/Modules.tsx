'use client';
import { useEffect, useState } from 'react';
import { api } from '@/src/lib/api';
import { specs } from '@/src/lib/resources';
import { pct, shortMoney } from '@/src/lib/format';
import { ResourceManager } from './ResourceManager';
import { Card, ErrorBox, Kpi, Loading, SectionTitle, Status } from './ui';
import { WorkDetail } from './WorkDetail';

export const Clients=()=> <ResourceManager spec={specs.clients} subtitle="Cartera de clientes y datos de contacto."/>;

export function Accounts(){
  const [tab,setTab]=useState<'balances'|'manage'>('balances');
  return <div className="page-stack"><SectionTitle title="Cuentas" subtitle="Saldos líquidos por banco, caja, billetera o cuenta en moneda extranjera."/><Tabs tabs={[["balances","Saldos"],["manage","Administrar"]]} value={tab} set={setTab}/>{tab==='balances'?<AccountBalances/>:<ResourceManager hideTitle spec={specs.accounts}/>}</div>
}

export const Services=()=> <ResourceManager spec={specs.services} subtitle="Servicios puntuales o recurrentes. Los contratos mensualizados se administran acá, no como obras."/>;

function AccountBalances(){
  const [rows,setRows]=useState<any[]|null>(null);
  const [movements,setMovements]=useState<any[]|null>(null);
  const [error,setError]=useState('');
  const now=new Date();
  const [month,setMonth]=useState(`${now.getFullYear()}-${String(now.getMonth()+1).padStart(2,'0')}`);

  const load=async()=>{
    try{
      const [balances,movs]=await Promise.all([
        api.get<any[]>('/api/reports/account-balances'),
        api.list<any>('financial_movements','?limit=500')
      ]);
      setRows(balances);
      setMovements(movs);
      setError('');
    }catch(e:any){setError(e.message)}
  };
  useEffect(()=>{ void load(); },[]);
  if(error)return <ErrorBox message={error} onRetry={load}/>;
  if(!rows||!movements)return <Loading/>;

  const fullMoney=(value:any,currency='ARS')=>{
    const amount=Number(value||0);
    return currency==='USD'
      ? `USD ${amount.toLocaleString('es-AR',{minimumFractionDigits:0,maximumFractionDigits:2})}`
      : `$ ${amount.toLocaleString('es-AR',{minimumFractionDigits:0,maximumFractionDigits:2})}`;
  };
  const accountMap=Object.fromEntries(rows.map((x:any)=>[x.id,x]));
  const monthRows=movements
    .filter((x:any)=>String(x.movement_date||'').slice(0,7)===month)
    .sort((a:any,b:any)=>String(b.movement_date||'').localeCompare(String(a.movement_date||'')));
  const monthIncome=monthRows.filter((x:any)=>String(x.type).toLowerCase()==='ingreso').reduce((a:number,x:any)=>a+Number(x.amount||0),0);
  const monthExpense=monthRows.filter((x:any)=>String(x.type).toLowerCase()==='egreso').reduce((a:number,x:any)=>a+Number(x.amount||0),0);
  const monthNet=monthIncome-monthExpense;
  const monthLabel=(()=>{
    const [y,m]=month.split('-').map(Number);
    const label=new Intl.DateTimeFormat('es-AR',{month:'long',year:'numeric'}).format(new Date(y,m-1,1));
    return label.charAt(0).toUpperCase()+label.slice(1);
  })();

  const undoMovement=async(x:any)=>{
    const type=String(x.type||'').toLowerCase();
    const action=type==='ingreso'?'cobro / ingreso':type==='egreso'?'pago / egreso':'movimiento';
    const ok=confirm(
      `¿Eliminar este ${action} de ${fullMoney(x.amount,accountMap[x.account_id]?.currency||'ARS')}?\n\n`+
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

  return <>
    <Card>
      <div className="table-wrap">
        <table>
          <thead><tr><th>Cuenta</th><th>Tipo</th><th>Moneda</th><th>Saldo líquido</th></tr></thead>
          <tbody>{rows.map((x:any)=><tr key={x.id}><td><b>{x.name}</b></td><td>{x.type}</td><td>{x.currency}</td><td><b>{fullMoney(x.balance,x.currency)}</b></td></tr>)}</tbody>
        </table>
      </div>
    </Card>

    <Card>
      <div style={{display:'flex',justifyContent:'space-between',gap:16,alignItems:'end',flexWrap:'wrap',marginBottom:18}}>
        <div>
          <div style={{fontSize:12,fontWeight:800,letterSpacing:'.08em',textTransform:'uppercase',color:'#6b7890'}}>Movimientos del mes</div>
          <h3 style={{margin:'5px 0 0'}}>{monthLabel}</h3>
        </div>
        <label style={{display:'grid',gap:6,fontWeight:700,fontSize:13}}>
          Mes
          <input type="month" value={month} onChange={e=>setMonth(e.target.value)} />
        </label>
      </div>

      <div className="kpi-grid three" style={{marginBottom:18}}>
        <Kpi label="Ingresos del mes" value={fullMoney(monthIncome)} tone="good"/>
        <Kpi label="Egresos del mes" value={fullMoney(monthExpense)} tone={monthExpense>0?'warn':undefined}/>
        <Kpi label="Neto del mes" value={fullMoney(monthNet)} tone={monthNet>=0?'good':'bad'}/>
      </div>

      {monthRows.length===0?<div className="empty-state">No hay movimientos registrados en {monthLabel}.</div>:
      <div className="table-wrap">
        <table>
          <thead><tr><th>Fecha</th><th>Cuenta</th><th>Tipo</th><th>Concepto</th><th>Monto</th><th>Acciones</th></tr></thead>
          <tbody>{monthRows.map((x:any)=>{
            const acc=accountMap[x.account_id];
            const type=String(x.type||'').toLowerCase();
            return <tr key={x.id}>
              <td>{x.movement_date?new Date(`${String(x.movement_date).slice(0,10)}T12:00:00`).toLocaleDateString('es-AR'):'—'}</td>
              <td><b>{acc?.name||'—'}</b></td>
              <td><Status tone={type==='ingreso'?'green':type==='egreso'?'red':'yellow'}>{x.type||'—'}</Status></td>
              <td>{x.description||x.category||'—'}</td>
              <td><b>{type==='egreso'?'- ':type==='ingreso'?'+ ':''}{fullMoney(x.amount,acc?.currency||'ARS')}</b></td>
              <td><button className="mini-button danger-text" onClick={()=>undoMovement(x)}>Eliminar</button></td>
            </tr>
          })}</tbody>
        </table>
      </div>}
    </Card>
  </>
}

export function Works({embedded=false}:{embedded?:boolean}={}){
  const [selected,setSelected]=useState<string|null>(null);
  if(selected) return <WorkDetail workId={selected} onBack={()=>setSelected(null)}/>;

  const sortWorks=(rows:any[])=>{
    const isFinished=(status:any)=>{
      const s=String(status||'').toLowerCase();
      return ['finalizada','finalizado','completada','completado','cerrada','cerrado','terminada','terminado'].some(x=>s.includes(x));
    };
    const endTime=(row:any)=>row.end_date?new Date(`${String(row.end_date).slice(0,10)}T12:00:00`).getTime():Number.POSITIVE_INFINITY;
    return rows.sort((a,b)=>{
      const aFinished=isFinished(a.status);
      const bFinished=isFinished(b.status);
      if(aFinished!==bFinished) return aFinished?1:-1;
      if(!aFinished&&!bFinished) return endTime(a)-endTime(b);
      return endTime(b)-endTime(a);
    });
  };

  return <div className="page-stack">{!embedded&&<SectionTitle title="Obras" subtitle="Trabajos con ítems, ejecución, costos y facturación."/>}<ResourceManager hideTitle spec={specs.works} sortRows={sortWorks} onRowClick={(r:any)=>setSelected(r.id)}/></div>
}

export function Suppliers(){const [tab,setTab]=useState<'suppliers'|'supplier_rates'|'supplier_services'>('suppliers');return <div className="page-stack"><SectionTitle title="Proveedores y contratistas" subtitle="Cuenta base, tarifas y horas/servicios acumulados."/><Tabs tabs={[['suppliers','Proveedores'],['supplier_rates','Tarifas'],['supplier_services','Horas y servicios']]} value={tab} set={setTab}/><ResourceManager hideTitle spec={specs[tab]}/></div>}
export function Stock(){const [tab,setTab]=useState<'summary'|'materials'|'stock_movements'>('summary');return <div className="page-stack"><SectionTitle title="Stock de materiales" subtitle="Existencias calculadas desde entradas, salidas y ajustes."/><Tabs tabs={[['summary','Stock actual'],['materials','Materiales'],['stock_movements','Movimientos']]} value={tab} set={setTab}/>{tab==='summary'?<StockSummary/>:<ResourceManager hideTitle spec={specs[tab]}/>}</div>}
export function Purchases(){const [tab,setTab]=useState<'purchases'|'purchase_items'>('purchases');return <div className="page-stack"><SectionTitle title="Compras" subtitle="Compras a proveedores y detalle de materiales/servicios."/><Tabs tabs={[['purchases','Compras'],['purchase_items','Ítems']]} value={tab} set={setTab}/><ResourceManager hideTitle spec={specs[tab]}/></div>}
export function Finance(){const [tab,setTab]=useState<'summary'|'receivables'|'payables'|'financial_movements'|'fixed_costs'>('summary');return <div className="page-stack"><SectionTitle title="Finanzas" subtitle="Caja, cobros, pagos, vencimientos y costos fijos."/><Tabs tabs={[['summary','Resumen'],['receivables','Por cobrar'],['payables','Por pagar'],['financial_movements','Caja'],['fixed_costs','Costos fijos']]} value={tab} set={setTab}/>{tab==='summary'?<FinanceSummary/>:<ResourceManager hideTitle spec={specs[tab]}/>}</div>}

function Tabs({tabs,value,set}:{tabs:any[];value:string;set:(v:any)=>void}){return <div className="tabs standalone">{tabs.map(([id,label])=><button key={id} className={value===id?'active':''} onClick={()=>set(id)}>{label}</button>)}</div>}

function StockSummary(){const [rows,setRows]=useState<any[]|null>(null);const [error,setError]=useState('');const load=()=>api.get<any[]>('/api/reports/current-stock').then(setRows).catch(e=>setError(e.message));useEffect(()=>{ void load(); },[]);if(error)return <ErrorBox message={error} onRetry={load}/>;if(!rows)return <Loading/>;const total=rows.reduce((a,x)=>a+Number(x.stock_value||0),0);const low=rows.filter(x=>Number(x.current_stock)<Number(x.minimum_stock));return <><div className="kpi-grid three"><Kpi label="Valor de stock" value={shortMoney(total)}/><Kpi label="Materiales" value={String(rows.length)}/><Kpi label="Stock bajo" value={String(low.length)} tone={low.length?'warn':'good'}/></div><Card><div className="table-wrap"><table><thead><tr><th>Material</th><th>Categoría</th><th>Stock</th><th>Mínimo</th><th>Costo actual</th><th>Valor</th><th>Estado</th></tr></thead><tbody>{rows.map(x=><tr key={x.id}><td><b>{x.name}</b><span className="cell-sub">{x.code||'—'}</span></td><td>{x.category||'—'}</td><td>{x.current_stock} {x.unit}</td><td>{x.minimum_stock} {x.unit}</td><td>{shortMoney(x.current_cost)}</td><td><b>{shortMoney(x.stock_value)}</b></td><td><Status tone={Number(x.current_stock)<Number(x.minimum_stock)?'red':'green'}>{Number(x.current_stock)<Number(x.minimum_stock)?'Reponer':'OK'}</Status></td></tr>)}</tbody></table></div></Card></>}

function FinanceSummary(){const [d,setD]=useState<any>(null);const [error,setError]=useState('');const load=async()=>{try{const [s,p]=await Promise.all([api.get<any>('/api/dashboard/summary'),api.get<any[]>('/api/dashboard/cash-projection?days=90')]);setD({s,p})}catch(e:any){setError(e.message)}};useEffect(()=>{load()},[]);if(error)return <ErrorBox message={error} onRetry={load}/>;if(!d)return <Loading/>;const s=d.s;const points=[0,30,60,90].map(days=>{const dt=new Date();dt.setDate(dt.getDate()+days);const row=d.p.find((x:any)=>String(x.day).slice(0,10)===dt.toISOString().slice(0,10));return {label:days===0?'Hoy':`${days}d`,v:Number(row?.projected_cash??s.cash_balance)}});const max=Math.max(1,...points.map(x=>Math.abs(x.v)));return <><div className="kpi-grid four"><Kpi label="Caja" value={shortMoney(s.cash_balance)}/><Kpi label="Por cobrar" value={shortMoney(s.receivables)} note={`${shortMoney(s.overdue_receivables)} vencido`}/><Kpi label="Por pagar" value={shortMoney(s.payables)} note={`${shortMoney(s.overdue_payables)} vencido`}/><Kpi label="Posición neta" value={shortMoney(s.net_position)} tone={Number(s.net_position)>=0?'good':'bad'}/></div><div className="two-col wide-left"><Card><SectionTitle title="Proyección 90 días"/><div className="cash-chart large">{points.map(x=><div className="bar-wrap" key={x.label}><div className="bar-value">{shortMoney(x.v)}</div><div className="bar-shell"><div className="bar" style={{height:`${Math.max(20,Math.abs(x.v)/max*190)}px`}}/></div><span>{x.label}</span></div>)}</div></Card><Card><SectionTitle title="Compromisos"/><div className="health-list"><div><span>Cobros vencidos</span><strong>{shortMoney(s.overdue_receivables)}</strong><Status tone={Number(s.overdue_receivables)>0?'red':'green'}>{Number(s.overdue_receivables)>0?'Atención':'OK'}</Status></div><div><span>Pagos vencidos</span><strong>{shortMoney(s.overdue_payables)}</strong><Status tone={Number(s.overdue_payables)>0?'red':'green'}>{Number(s.overdue_payables)>0?'Atención':'OK'}</Status></div><div><span>Costos fijos mensuales</span><strong>{shortMoney(s.monthly_fixed_costs)}</strong></div></div></Card></div></>}

export function Reports(){const [d,setD]=useState<any>(null);const [error,setError]=useState('');const load=async()=>{try{const [s,w,sp,stock,clients,recv]=await Promise.all([api.get<any>('/api/dashboard/summary'),api.get<any[]>('/api/reports/work-profitability'),api.get<any[]>('/api/reports/supplier-balances'),api.get<any[]>('/api/reports/current-stock'),api.list<any>('clients','?limit=500'),api.list<any>('receivables','?limit=500')]);setD({s,w,sp,stock,clients,recv})}catch(e:any){setError(e.message)}};useEffect(()=>{load()},[]);if(error)return <ErrorBox message={error} onRetry={load}/>;if(!d)return <Loading/>;const byClient:Record<string,number>={};d.recv.filter((r:any)=>r.status!=='anulado').forEach((r:any)=>byClient[r.client_id]=(byClient[r.client_id]||0)+Number(r.amount));const total=Object.values(byClient).reduce((a,b)=>a+b,0);const clientMap=Object.fromEntries(d.clients.map((c:any)=>[c.id,c.name]));const concentration=Object.entries(byClient).sort((a,b)=>b[1]-a[1]);return <div className="page-stack"><SectionTitle title="Reportes y ratios" subtitle="Indicadores calculados desde la base real."/><div className="kpi-grid four"><Kpi label="Posición neta" value={shortMoney(d.s.net_position)} tone={Number(d.s.net_position)>=0?'good':'bad'}/><Kpi label="Costos fijos / mes" value={shortMoney(d.s.monthly_fixed_costs)}/><Kpi label="Obras activas" value={String(d.s.active_works)}/><Kpi label="Stock valorizado" value={shortMoney(d.stock.reduce((a:number,x:any)=>a+Number(x.stock_value||0),0))}/></div><div className="two-col"><Card><SectionTitle title="Rentabilidad por obra"/>{d.w.length===0?<div className="empty-state">Sin obras para analizar.</div>:<div className="health-list">{d.w.map((w:any)=><div key={w.id}><span>{w.code} · {w.name}</span><strong>{pct(w.margin_ratio)}</strong><Status tone={Number(w.margin_ratio)>=.3?'green':Number(w.margin_ratio)>=.15?'yellow':'red'}>{shortMoney(w.projected_result)}</Status></div>)}</div>}</Card><Card><SectionTitle title="Concentración por cliente"/>{concentration.length===0?<div className="empty-state">Todavía no hay cuentas por cobrar.</div>:<div className="client-share">{concentration.map(([id,val])=>{const share=total?val/total*100:0;return <div key={id}><div className="share-head"><span>{clientMap[id]||id}</span><b>{share.toFixed(1)}%</b></div><div className="share-track"><i style={{width:`${share}%`}}/></div><small>{shortMoney(val)}</small></div>})}</div>}</Card></div><Card><SectionTitle title="Saldos de proveedores"/><div className="table-wrap"><table><thead><tr><th>Proveedor</th><th>Tipo</th><th>Generado</th><th>Pagado</th><th>Saldo</th></tr></thead><tbody>{d.sp.map((x:any)=><tr key={x.id}><td><b>{x.name}</b></td><td>{x.type}</td><td>{shortMoney(x.generated)}</td><td>{shortMoney(x.paid)}</td><td><b>{shortMoney(x.balance)}</b></td></tr>)}</tbody></table></div></Card></div>}
