'use client';

import { useEffect, useMemo, useState } from 'react';
import { api } from '@/src/lib/api';
import { shortMoney } from '@/src/lib/format';
import { ErrorBox, Loading, Status } from './ui';

function Icon({name}:{name:'wallet'|'in'|'out'|'net'|'repeat'|'contract'|'fixed'|'work'|'alert'|'chart'}){
  const paths:any={
    wallet:<><path d="M3 7.5h15.5a2.5 2.5 0 0 1 2.5 2.5v8a2.5 2.5 0 0 1-2.5 2.5h-15A2.5 2.5 0 0 1 1 18V6a3 3 0 0 1 3-3h13"/><path d="M16 12h5v5h-5a2.5 2.5 0 0 1 0-5Z"/></>,
    in:<><path d="M12 3v14"/><path d="m7 12 5 5 5-5"/><path d="M4 21h16"/></>,
    out:<><path d="M12 21V7"/><path d="m7 12 5-5 5 5"/><path d="M4 3h16"/></>,
    net:<><circle cx="12" cy="12" r="9"/><path d="M8 12h8"/><path d="M12 8v8"/></>,
    repeat:<><path d="m17 2 4 4-4 4"/><path d="M3 11V9a3 3 0 0 1 3-3h15"/><path d="m7 22-4-4 4-4"/><path d="M21 13v2a3 3 0 0 1-3 3H3"/></>,
    contract:<><path d="M6 2h9l4 4v16H6z"/><path d="M15 2v5h5"/><path d="M9 12h6M9 16h6"/></>,
    fixed:<><path d="M12 2v20M17 6.5c0-1.4-2.2-2.5-5-2.5S7 5.1 7 6.5 9.2 9 12 9s5 1.1 5 2.5S14.8 14 12 14s-5 1.1-5 2.5S9.2 19 12 19s5-1.1 5-2.5"/></>,
    work:<><path d="M4 7h16v13H4z"/><path d="M8 7V4h8v3M9 12h6"/></>,
    alert:<><path d="M12 3 2.5 20h19z"/><path d="M12 9v5M12 17h.01"/></>,
    chart:<><path d="M3 20h18"/><path d="m5 16 4-5 4 3 6-8"/></>
  };
  return <svg className="exec-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>;
}

function MetricCard({label,value,note,tone='blue',icon}:{label:string,value:string,note:string,tone?:'blue'|'green'|'amber'|'red'|'slate',icon:any}){
  return <div className={`exec-metric tone-${tone}`}>
    <div className="exec-metric-top"><span className="exec-metric-icon"><Icon name={icon}/></span><span className="exec-metric-label">{label}</span></div>
    <strong>{value}</strong>
    <span className="exec-metric-note">{note}</span>
  </div>;
}

function CompactMetric({label,value,note,icon}:{label:string,value:string,note:string,icon:any}){
  return <div className="exec-compact">
    <span className="exec-compact-icon"><Icon name={icon}/></span>
    <div><span>{label}</span><strong>{value}</strong><small>{note}</small></div>
  </div>;
}

function CashLineChart({points}:{points:{label:string,value:number}[]}){
  const width=760, height=240, padX=26, padTop=25, padBottom=36;
  const values=points.map(p=>p.value);
  const min=Math.min(...values), max=Math.max(...values);
  const spread=Math.max(1,max-min);
  const x=(i:number)=>padX + i*((width-padX*2)/(points.length-1));
  const y=(v:number)=>padTop + (max-v)/spread*(height-padTop-padBottom);
  const coords=points.map((p,i)=>[x(i),y(p.value)] as [number,number]);
  const line=coords.map((c,i)=>`${i?'L':'M'} ${c[0]} ${c[1]}`).join(' ');
  const area=`${line} L ${coords[coords.length-1][0]} ${height-padBottom} L ${coords[0][0]} ${height-padBottom} Z`;
  return <div className="exec-chart-wrap">
    <svg className="exec-chart" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" role="img" aria-label="Caja proyectada">
      <defs>
        <linearGradient id="cashArea" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="currentColor" stopOpacity=".22"/><stop offset="100%" stopColor="currentColor" stopOpacity=".02"/></linearGradient>
      </defs>
      {[0,1,2,3].map(i=><line key={i} x1={padX} x2={width-padX} y1={padTop+i*(height-padTop-padBottom)/3} y2={padTop+i*(height-padTop-padBottom)/3} className="exec-gridline"/>)}
      <path d={area} className="exec-chart-area"/>
      <path d={line} className="exec-chart-line"/>
      {coords.map((c,i)=><g key={i}><circle cx={c[0]} cy={c[1]} r="5" className="exec-chart-point"/><text x={c[0]} y={height-11} textAnchor="middle" className="exec-chart-label">{points[i].label}</text></g>)}
    </svg>
    <div className="exec-chart-values">{points.map(p=><div key={p.label}><span>{p.label}</span><strong>{shortMoney(p.value)}</strong></div>)}</div>
  </div>;
}

export function Dashboard({onNavigate}:{onNavigate:(s:any)=>void}){
  const [data,setData]=useState<any>(null);
  const [error,setError]=useState('');
  const load=async()=>{setError('');try{const [summary,projection,works,stock,suppliers]=await Promise.all([
    api.get<any>('/api/dashboard/summary'),api.get<any[]>('/api/dashboard/cash-projection?days=180'),api.get<any[]>('/api/reports/work-profitability'),api.get<any[]>('/api/reports/current-stock'),api.get<any[]>('/api/reports/supplier-balances')
  ]);setData({summary,projection,works,stock,suppliers});}catch(e:any){setError(e.message);}};
  useEffect(()=>{void load();},[]);
  if(error) return <ErrorBox message={error} onRetry={load}/>;
  if(!data) return <Loading/>;

  const s=data.summary;
  const lowStock=data.stock.filter((x:any)=>Number(x.current_stock)<Number(x.minimum_stock));
  const supplierDebt=data.suppliers.filter((x:any)=>Number(x.balance)>0);
  const projPoints=[0,30,60,90,180].map(d=>{const target=new Date();target.setDate(target.getDate()+d);const iso=target.toISOString().slice(0,10);let row=data.projection.find((x:any)=>String(x.day).slice(0,10)===iso);if(!row&&d===0) row={projected_cash:s.cash_balance};return {label:d===0?'Hoy':`${d}d`,value:Number(row?.projected_cash??s.cash_balance)};});
  const delta180=projPoints[4].value-projPoints[0].value;
  const alertCount=(Number(s.overdue_receivables)>0?1:0)+(Number(s.overdue_payables)>0?1:0)+lowStock.length+supplierDebt.length;

  return <div className="executive-dashboard">
    <div className="exec-overview-head">
      <div><span className="exec-eyebrow">VISIÓN EJECUTIVA</span><h2>Estado general de la empresa</h2><p>Liquidez, compromisos y actividad operativa en una sola vista.</p></div>
      <div className={`exec-health ${alertCount?'has-alerts':'healthy'}`}><span className="exec-health-dot"/><div><strong>{alertCount?`${alertCount} puntos a revisar`:'Operación saludable'}</strong><small>{alertCount?'Hay alertas o saldos pendientes':'Sin alertas críticas registradas'}</small></div></div>
    </div>

    <section className="exec-metrics-grid">
      <MetricCard label="Caja disponible" value={shortMoney(s.cash_balance)} note="Liquidez consolidada" tone="green" icon="wallet"/>
      <MetricCard label="Por cobrar" value={shortMoney(s.receivables)} note={`${shortMoney(s.overdue_receivables)} vencidos`} tone={Number(s.overdue_receivables)>0?'amber':'blue'} icon="in"/>
      <MetricCard label="Por pagar" value={shortMoney(s.payables)} note={`${shortMoney(s.overdue_payables)} vencidos`} tone={Number(s.overdue_payables)>0?'red':'slate'} icon="out"/>
      <MetricCard label="Posición neta" value={shortMoney(s.net_position)} note="Caja + créditos − obligaciones" tone={Number(s.net_position)>=0?'green':'red'} icon="net"/>
    </section>

    <section className="exec-business-card">
      <div className="exec-section-title"><div><span className="exec-eyebrow">NEGOCIO ACTIVO</span><h3>Actividad y estructura</h3></div><button className="exec-link" onClick={()=>onNavigate('jobs')}>Ver trabajos <span>→</span></button></div>
      <div className="exec-compact-grid">
        <CompactMetric label="Recurrente / mes" value={shortMoney(s.monthly_recurring_revenue||0)} note="Servicios vigentes" icon="repeat"/>
        <CompactMetric label="Valor contratado" value={shortMoney(s.total_contracted)} note="Cartera registrada" icon="contract"/>
        <CompactMetric label="Costos fijos / mes" value={shortMoney(s.monthly_fixed_costs)} note="Estructura mensual" icon="fixed"/>
        <CompactMetric label="Obras activas" value={String(s.active_works)} note="En ejecución" icon="work"/>
      </div>
    </section>

    <section className="exec-main-grid">
      <div className="exec-panel exec-cash-panel">
        <div className="exec-panel-head"><div><span className="exec-eyebrow">PROYECCIÓN</span><h3>Caja proyectada</h3><p>Saldo estimado según cobros y pagos previstos.</p></div><div className={`exec-delta ${delta180>=0?'positive':'negative'}`}><small>Variación a 180 días</small><strong>{delta180>=0?'+':''}{shortMoney(delta180)}</strong></div></div>
        <CashLineChart points={projPoints}/>
        <button className="exec-secondary-button" onClick={()=>onNavigate('finance')}><Icon name="chart"/>Ver detalle financiero</button>
      </div>

      <div className="exec-panel exec-alert-panel">
        <div className="exec-panel-head"><div><span className="exec-eyebrow">CONTROL</span><h3>Atención requerida</h3><p>Situaciones que merecen revisión.</p></div><span className={`exec-alert-count ${alertCount?'active':''}`}>{alertCount}</span></div>
        <div className="exec-alert-list">
          {Number(s.overdue_receivables)>0&&<div className="exec-alert-item critical"><span className="exec-alert-icon"><Icon name="alert"/></span><div><b>Cobros vencidos</b><small>Hay créditos fuera de término.</small></div><strong>{shortMoney(s.overdue_receivables)}</strong></div>}
          {Number(s.overdue_payables)>0&&<div className="exec-alert-item critical"><span className="exec-alert-icon"><Icon name="alert"/></span><div><b>Pagos vencidos</b><small>Obligaciones fuera de término.</small></div><strong>{shortMoney(s.overdue_payables)}</strong></div>}
          {lowStock.slice(0,2).map((x:any)=><div className="exec-alert-item warning" key={x.id}><span className="exec-alert-icon"><Icon name="alert"/></span><div><b>Stock bajo · {x.name}</b><small>{x.current_stock} {x.unit} disponibles · mínimo {x.minimum_stock}</small></div></div>)}
          {supplierDebt.slice(0,2).map((x:any)=><div className="exec-alert-item info" key={x.id}><span className="exec-alert-icon"><Icon name="out"/></span><div><b>Saldo proveedor · {x.name}</b><small>Cuenta corriente pendiente</small></div><strong>{shortMoney(x.balance)}</strong></div>)}
          {!alertCount&&<div className="exec-empty-state"><span className="exec-empty-check">✓</span><strong>Sin alertas críticas</strong><p>Vencimientos, stock y proveedores se encuentran dentro de parámetros normales.</p><Status tone="green">Todo en orden</Status></div>}
        </div>
      </div>
    </section>
  </div>;
}
