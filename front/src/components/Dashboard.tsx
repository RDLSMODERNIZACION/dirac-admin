'use client';

import { useEffect, useState } from 'react';
import { api } from '@/src/lib/api';
import { ErrorBox, Loading, Status } from './ui';

const money = (value: any) => `$ ${Math.round(Number(value || 0)).toLocaleString('es-AR')}`;

function monthName(value: string) {
  const d = new Date(`${String(value).slice(0, 10)}T12:00:00`);
  const text = new Intl.DateTimeFormat('es-AR', { month: 'long', year: 'numeric' }).format(d);
  return text.charAt(0).toUpperCase() + text.slice(1);
}

function monthShort(value: string) {
  const d = new Date(`${String(value).slice(0, 10)}T12:00:00`);
  const m = new Intl.DateTimeFormat('es-AR', { month: 'short' }).format(d).replace('.', '');
  return `${m.charAt(0).toUpperCase() + m.slice(1)} ${String(d.getFullYear()).slice(2)}`;
}

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
    <strong>{value}</strong><span className="exec-metric-note">{note}</span>
  </div>;
}

function CompactMetric({label,value,note,icon}:{label:string,value:string,note:string,icon:any}){
  return <div className="exec-compact"><span className="exec-compact-icon"><Icon name={icon}/></span><div><span>{label}</span><strong>{value}</strong><small>{note}</small></div></div>;
}

function MonthlyCashChart({months}:{months:any[]}){
  if (!months.length) return null;
  const points=months.map(m=>({label:monthShort(m.month_start),value:Number(m.closing_cash||0)}));
  const width=860,height=250,padX=36,padTop=26,padBottom=42;
  const values=points.map(p=>p.value);
  let min=Math.min(...values),max=Math.max(...values);
  if(min===max){min-=1;max+=1;}
  const spread=Math.max(1,max-min);
  const x=(i:number)=>padX+i*((width-padX*2)/Math.max(1,points.length-1));
  const y=(v:number)=>padTop+(max-v)/spread*(height-padTop-padBottom);
  const coords=points.map((p,i)=>[x(i),y(p.value)] as [number,number]);
  const line=coords.map((c,i)=>`${i?'L':'M'} ${c[0]} ${c[1]}`).join(' ');
  const area=`${line} L ${coords[coords.length-1][0]} ${height-padBottom} L ${coords[0][0]} ${height-padBottom} Z`;
  return <div className="monthly-chart-wrap">
    <svg className="exec-chart monthly-chart" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none" role="img" aria-label="Caja proyectada por mes">
      <defs><linearGradient id="monthlyCashArea" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#3476da" stopOpacity=".20"/><stop offset="100%" stopColor="#3476da" stopOpacity=".02"/></linearGradient></defs>
      {[0,1,2,3].map(i=><line key={i} x1={padX} x2={width-padX} y1={padTop+i*(height-padTop-padBottom)/3} y2={padTop+i*(height-padTop-padBottom)/3} className="exec-gridline"/>)}
      <path d={area} fill="url(#monthlyCashArea)"/><path d={line} className="exec-chart-line"/>
      {coords.map((c,i)=><g key={points[i].label}><circle cx={c[0]} cy={c[1]} r="5" className="exec-chart-point"/><text x={c[0]} y={height-13} textAnchor="middle" className="exec-chart-label">{points[i].label}</text></g>)}
    </svg>
    <div className="monthly-chart-values">{points.map(p=><div key={p.label}><span>{p.label}</span><strong>{money(p.value)}</strong></div>)}</div>
  </div>;
}

export function Dashboard({onNavigate}:{onNavigate:(s:any)=>void}){
  const [data,setData]=useState<any>(null); const [error,setError]=useState('');
  const load=async()=>{setError('');try{const [summary,flow,stock,suppliers]=await Promise.all([
    api.get<any>('/api/dashboard/summary'),
    api.get<any>('/api/dashboard/monthly-flow?months=6'),
    api.get<any[]>('/api/reports/current-stock'),
    api.get<any[]>('/api/reports/supplier-balances')
  ]);setData({summary,flow,stock,suppliers});}catch(e:any){setError(e.message);}};
  useEffect(()=>{void load();},[]);
  if(error) return <ErrorBox message={error} onRetry={load}/>; if(!data) return <Loading/>;

  const s=data.summary, months=data.flow.months||[], current=months[0]||{};
  const lowStock=data.stock.filter((x:any)=>Number(x.current_stock)<Number(x.minimum_stock));
  const supplierDebt=data.suppliers.filter((x:any)=>Number(x.balance)>0);
  const alertCount=(Number(s.overdue_receivables)>0?1:0)+(Number(s.overdue_payables)>0?1:0)+lowStock.length+supplierDebt.length;
  const currentMonth=monthName(current.month_start || new Date().toISOString().slice(0,10));
  const last=months[months.length-1]||current;

  return <div className="executive-dashboard monthly-dashboard">
    <div className="exec-overview-head month-overview-head">
      <div><span className="exec-eyebrow">POSICIÓN ACTUAL</span><h2>{currentMonth}</h2><p>Situación financiera actual y proyección de caja de los próximos seis meses.</p></div>
      <div className={`exec-health ${alertCount?'has-alerts':'healthy'}`}><span className="exec-health-dot"/><div><strong>{alertCount?`${alertCount} puntos a revisar`:'Sin alertas críticas'}</strong><small>{alertCount?'Hay vencimientos o saldos para controlar':'La operación no presenta alertas prioritarias'}</small></div></div>
    </div>

    <section className="exec-metrics-grid">
      <MetricCard label="Caja disponible hoy" value={money(s.cash_balance)} note="Saldo líquido consolidado" tone="green" icon="wallet"/>
      <MetricCard label="Por cobrar" value={money(s.receivables)} note={`${money(s.overdue_receivables)} vencidos`} tone={Number(s.overdue_receivables)>0?'amber':'blue'} icon="in"/>
      <MetricCard label="Por pagar" value={money(s.payables)} note={`${money(s.overdue_payables)} vencidos`} tone={Number(s.overdue_payables)>0?'red':'slate'} icon="out"/>
      <MetricCard label="Posición neta" value={money(s.net_position)} note="Caja + por cobrar − por pagar" tone={Number(s.net_position)>=0?'green':'red'} icon="net"/>
    </section>

    <section className="exec-panel monthly-flow-panel">
      <div className="exec-panel-head monthly-flow-head"><div><span className="exec-eyebrow">FLUJO DE CAJA PROYECTADO</span><h3>{currentMonth} → {monthName(last.month_start || current.month_start)}</h3><p>Cobros y pagos previstos, incluyendo los costos fijos activos todavía no pagados.</p></div><div className={`exec-delta ${Number(last.closing_cash)>=Number(s.cash_balance)?'positive':'negative'}`}><small>Caja proyectada al final</small><strong>{money(last.closing_cash)}</strong></div></div>

      <div className="current-month-strip">
        <div><span>Caja hoy</span><strong>{money(s.cash_balance)}</strong></div>
        <div className="positive"><span>Cobros previstos · {currentMonth}</span><strong>+ {money(current.expected_in)}</strong></div>
        <div className="negative"><span>Otros pagos · {currentMonth}</span><strong>− {money(current.other_payments)}</strong></div>
        <div className="negative"><span>Costos fijos · {currentMonth}</span><strong>− {money(current.fixed_cost_out)}</strong></div>
        <div className={Number(current.closing_cash)>=0?'positive':'negative'}><span>Caja fin de mes</span><strong>{money(current.closing_cash)}</strong></div>
      </div>

      <MonthlyCashChart months={months}/>

      <div className="monthly-flow-table-wrap"><table className="monthly-flow-table"><thead><tr><th>Mes</th><th>Caja inicial</th><th>Cobros previstos</th><th>Otros pagos</th><th>Costos fijos</th><th>Caja final</th></tr></thead><tbody>{months.map((m:any)=><tr key={m.month_start} className={m.is_current_month?'current-row':''}><td><strong>{monthName(m.month_start)}</strong>{m.is_current_month&&<span className="current-month-badge">Mes actual</span>}</td><td>{money(m.opening_cash)}</td><td className="amount-in">+ {money(m.expected_in)}</td><td className="amount-out">− {money(m.other_payments)}</td><td className="amount-out">− {money(m.fixed_cost_out)}</td><td className={Number(m.closing_cash)>=0?'closing-positive':'closing-negative'}><strong>{money(m.closing_cash)}</strong></td></tr>)}</tbody></table></div>
      <div className="flow-footer"><span>Mínimo de caja proyectado en el período: <strong>{money(data.flow.minimum_projected_cash)}</strong></span><button className="exec-secondary-button" onClick={()=>onNavigate('finance')}><Icon name="chart"/>Ver detalle financiero</button></div>
    </section>

    <section className="exec-business-card"><div className="exec-section-title"><div><span className="exec-eyebrow">ACTIVIDAD ACTUAL</span><h3>Negocio y estructura</h3></div><button className="exec-link" onClick={()=>onNavigate('jobs')}>Ver trabajos <span>→</span></button></div><div className="exec-compact-grid">
      <CompactMetric label="Ingresos recurrentes / mes" value={money(s.monthly_recurring_revenue||0)} note="Servicios vigentes" icon="repeat"/>
      <CompactMetric label="Valor contratado" value={money(s.total_contracted)} note="Obras y contratos registrados" icon="contract"/>
      <CompactMetric label="Costos fijos / mes" value={money(s.monthly_fixed_costs)} note="Estructura recurrente" icon="fixed"/>
      <CompactMetric label="Obras activas" value={String(s.active_works)} note="Trabajos en ejecución" icon="work"/>
    </div></section>

    <section className="exec-panel exec-alert-panel full-alert-panel"><div className="exec-panel-head"><div><span className="exec-eyebrow">CONTROL</span><h3>Atención requerida</h3><p>Solo situaciones que necesitan una acción o revisión.</p></div><span className={`exec-alert-count ${alertCount?'active':''}`}>{alertCount}</span></div><div className="exec-alert-list alert-grid">
      {Number(s.overdue_receivables)>0&&<div className="exec-alert-item critical"><span className="exec-alert-icon"><Icon name="alert"/></span><div><b>Cobros vencidos</b><small>Créditos fuera de término.</small></div><strong>{money(s.overdue_receivables)}</strong></div>}
      {Number(s.overdue_payables)>0&&<div className="exec-alert-item critical"><span className="exec-alert-icon"><Icon name="alert"/></span><div><b>Pagos vencidos</b><small>Obligaciones fuera de término.</small></div><strong>{money(s.overdue_payables)}</strong></div>}
      {lowStock.slice(0,2).map((x:any)=><div className="exec-alert-item warning" key={x.id}><span className="exec-alert-icon"><Icon name="alert"/></span><div><b>Stock bajo · {x.name}</b><small>{x.current_stock} {x.unit} disponibles · mínimo {x.minimum_stock}</small></div></div>)}
      {supplierDebt.slice(0,2).map((x:any)=><div className="exec-alert-item info" key={x.id}><span className="exec-alert-icon"><Icon name="out"/></span><div><b>Saldo proveedor · {x.name}</b><small>Cuenta corriente pendiente.</small></div><strong>{money(x.balance)}</strong></div>)}
      {!alertCount&&<div className="exec-empty-state wide-empty"><span className="exec-empty-check">✓</span><strong>Sin alertas críticas</strong><p>Vencimientos, stock y proveedores se encuentran dentro de parámetros normales.</p><Status tone="green">Todo en orden</Status></div>}
    </div></section>
  </div>;
}
