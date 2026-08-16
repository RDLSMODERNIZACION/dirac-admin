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
export function Finance(){const [tab,setTab]=useState<'summary'|'receivables'|'payables'|'debts'|'financial_movements'|'fixed_costs'>('summary');return <div className="page-stack"><SectionTitle title="Finanzas" subtitle="Caja, cobros, pagos, deudas, vencimientos y costos fijos."/><Tabs tabs={[['summary','Resumen'],['receivables','Por cobrar'],['payables','Por pagar'],['debts','Deudas'],['financial_movements','Caja'],['fixed_costs','Costos fijos']]} value={tab} set={setTab}/>{tab==='summary'?<FinanceSummary/>:tab==='debts'?<DebtManager/>:<ResourceManager hideTitle spec={specs[tab]}/>}</div>}

function DebtManager(){
 const [rows,setRows]=useState<any[]|null>(null),[summary,setSummary]=useState<any|null>(null),[accounts,setAccounts]=useState<any[]>([]),[error,setError]=useState(''),[open,setOpen]=useState(false),[pay,setPay]=useState<any|null>(null);
 const fm=(v:any)=>`$ ${Number(v||0).toLocaleString('es-AR',{maximumFractionDigits:2})}`; const fd=(v:any)=>v?new Date(`${String(v).slice(0,10)}T12:00:00`).toLocaleDateString('es-AR'):'—';
 const labels:any={tarjeta_credito:'Tarjeta de crédito',prestamo:'Préstamo',deuda_socio:'Deuda con socio',cheque_emitido:'Cheque emitido',cuota_vehiculo:'Cuota vehículo / maquinaria',impuesto_financiado:'Impuesto financiado',otra:'Otra deuda'};
 const load=async()=>{try{const [d,s,a]=await Promise.all([api.get<any[]>('/api/debts'),api.get<any>('/api/debts/summary'),api.list<any>('accounts','?limit=500')]);setRows(d);setSummary(s);setAccounts(a.filter((x:any)=>x.is_active!==false));setError('')}catch(e:any){setError(e.message||String(e))}}; useEffect(()=>{void load()},[]);
 if(error)return <ErrorBox message={error} onRetry={load}/>; if(!rows||!summary)return <Loading/>;
 const remove=async(r:any)=>{if(!confirm(`¿Eliminar la deuda con ${r.creditor}?`))return;try{await fetch(`${(process.env.NEXT_PUBLIC_API_URL||'https://dirac-admin.onrender.com').replace(/\/$/,'')}/api/debts/${r.id}`,{method:'DELETE',headers:process.env.NEXT_PUBLIC_API_KEY?{'X-API-Key':process.env.NEXT_PUBLIC_API_KEY}:{}}).then(async x=>{if(!x.ok){const b=await x.json().catch(()=>({}));throw new Error(b.detail||`Error ${x.status}`)}});await load()}catch(e:any){alert(e.message)}};
 return <><div className="kpi-grid four"><Kpi label="Deuda total" value={fm(summary.total_balance)}/><Kpi label="Próximos 30 días" value={fm(summary.next_30_days)} tone={Number(summary.next_30_days)>0?'warn':undefined}/><Kpi label="Tarjetas" value={fm(summary.credit_cards)}/><Kpi label="Deuda con socios" value={fm(summary.partners)}/></div><Card><SectionTitle title="Deudas y financiamiento" subtitle="Tarjetas, préstamos, socios, cheques, cuotas e impuestos financiados." action={<button className="primary-button" onClick={()=>setOpen(true)}>+ Nueva deuda</button>}/>{rows.length===0?<div className="empty-state">Todavía no hay deudas registradas.</div>:<div className="table-wrap"><table><thead><tr><th>Acreedor</th><th>Tipo</th><th>Monto original</th><th>Pagado</th><th>Saldo</th><th>Próximo vencimiento</th><th>Estado</th><th>Acciones</th></tr></thead><tbody>{rows.map((r:any)=><tr key={r.id}><td><b>{r.creditor}</b><div className="muted-line">{r.description||''}</div></td><td>{labels[r.debt_type]||r.debt_type}</td><td>{fm(r.original_amount)}</td><td>{fm(r.paid_amount)}</td><td><b>{fm(r.balance)}</b></td><td>{fd(r.next_due_date)}<div className="muted-line">{r.next_amount!=null?fm(r.next_amount):''}</div></td><td><Status tone={r.status==='cancelada'?'green':'yellow'}>{r.status}</Status></td><td><div className="row-actions">{r.status==='activa'&&Number(r.balance)>0&&<button className="mini-button" onClick={()=>setPay(r)}>Pagar</button>}<button className="mini-button danger-text" onClick={()=>remove(r)}>Eliminar</button></div></td></tr>)}</tbody></table></div>}</Card>{open&&<DebtCreateModal accounts={accounts} close={()=>setOpen(false)} done={async()=>{setOpen(false);await load()}}/>}{pay&&<DebtPayModal debt={pay} accounts={accounts} close={()=>setPay(null)} done={async()=>{setPay(null);await load()}}/>}</>
}
function DebtCreateModal({accounts,close,done}:any){const today=new Date().toISOString().slice(0,10);const [f,setF]=useState<any>({creditor:'',debt_type:'tarjeta_credito',description:'',original_amount:'',start_date:today,first_due_date:'',total_installments:1,installment_amount:'',minimum_payment:'',notes:'',register_inflow:false,account_id:''}),[saving,setSaving]=useState(false);const submit=async()=>{if(!f.creditor.trim()||Number(f.original_amount)<=0){alert('Completá acreedor y monto');return}if(f.register_inflow&&!f.account_id){alert('Seleccioná la cuenta donde ingresó el dinero');return}setSaving(true);try{await api.post('/api/debts',{...f,original_amount:Number(f.original_amount),total_installments:Number(f.total_installments||1),installment_amount:f.installment_amount?Number(f.installment_amount):null,minimum_payment:f.minimum_payment?Number(f.minimum_payment):null,first_due_date:f.first_due_date||null,account_id:f.account_id||null});await done()}catch(e:any){alert(e.message)}finally{setSaving(false)}};return <div className="modal-backdrop"><div className="modal"><div className="modal-head"><div><span className="eyebrow">DEUDA</span><h2>Nueva deuda</h2></div><button className="close-button" onClick={close}>×</button></div><div className="form-grid"><label className="field"><span>Acreedor *</span><input value={f.creditor} onChange={e=>setF({...f,creditor:e.target.value})}/></label><label className="field"><span>Tipo *</span><select value={f.debt_type} onChange={e=>setF({...f,debt_type:e.target.value})}><option value="tarjeta_credito">Tarjeta de crédito</option><option value="prestamo">Préstamo</option><option value="deuda_socio">Deuda con socio</option><option value="cheque_emitido">Cheque emitido</option><option value="cuota_vehiculo">Cuota vehículo / maquinaria</option><option value="impuesto_financiado">Impuesto financiado</option><option value="otra">Otra deuda</option></select></label><label className="field full"><span>Descripción</span><input value={f.description} onChange={e=>setF({...f,description:e.target.value})}/></label><label className="field"><span>Monto original *</span><input type="number" step="0.01" value={f.original_amount} onChange={e=>setF({...f,original_amount:e.target.value})}/></label><label className="field"><span>Fecha de inicio</span><input type="date" value={f.start_date} onChange={e=>setF({...f,start_date:e.target.value})}/></label><label className="field"><span>Primer vencimiento</span><input type="date" value={f.first_due_date} onChange={e=>setF({...f,first_due_date:e.target.value})}/></label><label className="field"><span>Cantidad de cuotas</span><input type="number" min="1" value={f.total_installments} onChange={e=>setF({...f,total_installments:e.target.value})}/></label><label className="field"><span>Monto por cuota</span><input type="number" step="0.01" value={f.installment_amount} onChange={e=>setF({...f,installment_amount:e.target.value})} placeholder="Automático si queda vacío"/></label>{f.debt_type==='tarjeta_credito'&&<label className="field"><span>Pago mínimo</span><input type="number" step="0.01" value={f.minimum_payment} onChange={e=>setF({...f,minimum_payment:e.target.value})}/></label>}<label className="field full"><span>Notas</span><textarea rows={2} value={f.notes} onChange={e=>setF({...f,notes:e.target.value})}/></label><label className="field full" style={{display:'flex',alignItems:'center',gap:10}}><input type="checkbox" checked={!!f.register_inflow} onChange={e=>setF({...f,register_inflow:e.target.checked})}/><span>Este dinero ingresó a la empresa y quiero registrarlo en caja</span></label>{f.register_inflow&&<label className="field full"><span>Cuenta donde ingresó *</span><select value={f.account_id} onChange={e=>setF({...f,account_id:e.target.value})}><option value="">Seleccionar…</option>{accounts.map((a:any)=><option key={a.id} value={a.id}>{a.name} · {a.currency}</option>)}</select></label>}</div><div className="modal-actions"><button className="ghost-button" onClick={close}>Cancelar</button><button className="primary-button" disabled={saving} onClick={submit}>{saving?'Guardando…':'Crear deuda'}</button></div></div></div>}
function DebtPayModal({debt,accounts,close,done}:any){const [f,setF]=useState<any>({account_id:accounts[0]?.id||'',amount:String(debt.next_amount||debt.balance||''),payment_date:new Date().toISOString().slice(0,10),notes:''}),[saving,setSaving]=useState(false);const submit=async()=>{if(!f.account_id||Number(f.amount)<=0){alert('Seleccioná cuenta y monto');return}setSaving(true);try{await api.post(`/api/debts/${debt.id}/payments`,{...f,amount:Number(f.amount)});await done()}catch(e:any){alert(e.message)}finally{setSaving(false)}};return <div className="modal-backdrop"><div className="modal"><div className="modal-head"><div><span className="eyebrow">PAGO DE DEUDA</span><h2>{debt.creditor}</h2></div><button className="close-button" onClick={close}>×</button></div><p className="modal-note">Saldo pendiente: <b>$ {Number(debt.balance||0).toLocaleString('es-AR')}</b>. El pago generará un egreso real de caja.</p><div className="form-grid"><label className="field"><span>Cuenta *</span><select value={f.account_id} onChange={e=>setF({...f,account_id:e.target.value})}><option value="">Seleccionar…</option>{accounts.map((a:any)=><option key={a.id} value={a.id}>{a.name} · {a.currency}</option>)}</select></label><label className="field"><span>Monto *</span><input type="number" min="0.01" max={Number(debt.balance||0)} step="0.01" value={f.amount} onChange={e=>setF({...f,amount:e.target.value})}/></label><label className="field"><span>Fecha</span><input type="date" value={f.payment_date} onChange={e=>setF({...f,payment_date:e.target.value})}/></label><label className="field"><span>Notas</span><input value={f.notes} onChange={e=>setF({...f,notes:e.target.value})}/></label></div><div className="modal-actions"><button className="ghost-button" onClick={close}>Cancelar</button><button className="primary-button" disabled={saving} onClick={submit}>{saving?'Pagando…':'Registrar pago'}</button></div></div></div>}

function Tabs({tabs,value,set}:{tabs:any[];value:string;set:(v:any)=>void}){return <div className="tabs standalone">{tabs.map(([id,label])=><button key={id} className={value===id?'active':''} onClick={()=>set(id)}>{label}</button>)}</div>}

function StockSummary(){const [rows,setRows]=useState<any[]|null>(null);const [error,setError]=useState('');const load=()=>api.get<any[]>('/api/reports/current-stock').then(setRows).catch(e=>setError(e.message));useEffect(()=>{ void load(); },[]);if(error)return <ErrorBox message={error} onRetry={load}/>;if(!rows)return <Loading/>;const total=rows.reduce((a,x)=>a+Number(x.stock_value||0),0);const low=rows.filter(x=>Number(x.current_stock)<Number(x.minimum_stock));return <><div className="kpi-grid three"><Kpi label="Valor de stock" value={shortMoney(total)}/><Kpi label="Materiales" value={String(rows.length)}/><Kpi label="Stock bajo" value={String(low.length)} tone={low.length?'warn':'good'}/></div><Card><div className="table-wrap"><table><thead><tr><th>Material</th><th>Categoría</th><th>Stock</th><th>Mínimo</th><th>Costo actual</th><th>Valor</th><th>Estado</th></tr></thead><tbody>{rows.map(x=><tr key={x.id}><td><b>{x.name}</b><span className="cell-sub">{x.code||'—'}</span></td><td>{x.category||'—'}</td><td>{x.current_stock} {x.unit}</td><td>{x.minimum_stock} {x.unit}</td><td>{shortMoney(x.current_cost)}</td><td><b>{shortMoney(x.stock_value)}</b></td><td><Status tone={Number(x.current_stock)<Number(x.minimum_stock)?'red':'green'}>{Number(x.current_stock)<Number(x.minimum_stock)?'Reponer':'OK'}</Status></td></tr>)}</tbody></table></div></Card></>}

function FinanceSummary(){const [d,setD]=useState<any>(null);const [error,setError]=useState('');const load=async()=>{try{const [s,p]=await Promise.all([api.get<any>('/api/dashboard/summary'),api.get<any[]>('/api/dashboard/cash-projection?days=90')]);setD({s,p})}catch(e:any){setError(e.message)}};useEffect(()=>{load()},[]);if(error)return <ErrorBox message={error} onRetry={load}/>;if(!d)return <Loading/>;const s=d.s;const points=[0,30,60,90].map(days=>{const dt=new Date();dt.setDate(dt.getDate()+days);const row=d.p.find((x:any)=>String(x.day).slice(0,10)===dt.toISOString().slice(0,10));return {label:days===0?'Hoy':`${days}d`,v:Number(row?.projected_cash??s.cash_balance)}});const max=Math.max(1,...points.map(x=>Math.abs(x.v)));return <><div className="kpi-grid four"><Kpi label="Caja" value={shortMoney(s.cash_balance)}/><Kpi label="Por cobrar" value={shortMoney(s.receivables)} note={`${shortMoney(s.overdue_receivables)} vencido`}/><Kpi label="Por pagar" value={shortMoney(s.payables)} note={`${shortMoney(s.overdue_payables)} vencido`}/><Kpi label="Posición neta" value={shortMoney(s.net_position)} tone={Number(s.net_position)>=0?'good':'bad'}/></div><div className="two-col wide-left"><Card><SectionTitle title="Proyección 90 días"/><div className="cash-chart large">{points.map(x=><div className="bar-wrap" key={x.label}><div className="bar-value">{shortMoney(x.v)}</div><div className="bar-shell"><div className="bar" style={{height:`${Math.max(20,Math.abs(x.v)/max*190)}px`}}/></div><span>{x.label}</span></div>)}</div></Card><Card><SectionTitle title="Compromisos"/><div className="health-list"><div><span>Cobros vencidos</span><strong>{shortMoney(s.overdue_receivables)}</strong><Status tone={Number(s.overdue_receivables)>0?'red':'green'}>{Number(s.overdue_receivables)>0?'Atención':'OK'}</Status></div><div><span>Pagos vencidos</span><strong>{shortMoney(s.overdue_payables)}</strong><Status tone={Number(s.overdue_payables)>0?'red':'green'}>{Number(s.overdue_payables)>0?'Atención':'OK'}</Status></div><div><span>Costos fijos mensuales</span><strong>{shortMoney(s.monthly_fixed_costs)}</strong></div></div></Card></div></>}

export function Reports(){const [d,setD]=useState<any>(null);const [error,setError]=useState('');const load=async()=>{try{const [s,w,sp,stock,clients,recv]=await Promise.all([api.get<any>('/api/dashboard/summary'),api.get<any[]>('/api/reports/work-profitability'),api.get<any[]>('/api/reports/supplier-balances'),api.get<any[]>('/api/reports/current-stock'),api.list<any>('clients','?limit=500'),api.list<any>('receivables','?limit=500')]);setD({s,w,sp,stock,clients,recv})}catch(e:any){setError(e.message)}};useEffect(()=>{load()},[]);if(error)return <ErrorBox message={error} onRetry={load}/>;if(!d)return <Loading/>;const byClient:Record<string,number>={};d.recv.filter((r:any)=>r.status!=='anulado').forEach((r:any)=>byClient[r.client_id]=(byClient[r.client_id]||0)+Number(r.amount));const total=Object.values(byClient).reduce((a,b)=>a+b,0);const clientMap=Object.fromEntries(d.clients.map((c:any)=>[c.id,c.name]));const concentration=Object.entries(byClient).sort((a,b)=>b[1]-a[1]);return <div className="page-stack"><SectionTitle title="Reportes y ratios" subtitle="Indicadores calculados desde la base real."/><div className="kpi-grid four"><Kpi label="Posición neta" value={shortMoney(d.s.net_position)} tone={Number(d.s.net_position)>=0?'good':'bad'}/><Kpi label="Costos fijos / mes" value={shortMoney(d.s.monthly_fixed_costs)}/><Kpi label="Obras activas" value={String(d.s.active_works)}/><Kpi label="Stock valorizado" value={shortMoney(d.stock.reduce((a:number,x:any)=>a+Number(x.stock_value||0),0))}/></div><div className="two-col"><Card><SectionTitle title="Rentabilidad por obra"/>{d.w.length===0?<div className="empty-state">Sin obras para analizar.</div>:<div className="health-list">{d.w.map((w:any)=><div key={w.id}><span>{w.code} · {w.name}</span><strong>{pct(w.margin_ratio)}</strong><Status tone={Number(w.margin_ratio)>=.3?'green':Number(w.margin_ratio)>=.15?'yellow':'red'}>{shortMoney(w.projected_result)}</Status></div>)}</div>}</Card><Card><SectionTitle title="Concentración por cliente"/>{concentration.length===0?<div className="empty-state">Todavía no hay cuentas por cobrar.</div>:<div className="client-share">{concentration.map(([id,val])=>{const share=total?val/total*100:0;return <div key={id}><div className="share-head"><span>{clientMap[id]||id}</span><b>{share.toFixed(1)}%</b></div><div className="share-track"><i style={{width:`${share}%`}}/></div><small>{shortMoney(val)}</small></div>})}</div>}</Card></div><Card><SectionTitle title="Saldos de proveedores"/><div className="table-wrap"><table><thead><tr><th>Proveedor</th><th>Tipo</th><th>Generado</th><th>Pagado</th><th>Saldo</th></tr></thead><tbody>{d.sp.map((x:any)=><tr key={x.id}><td><b>{x.name}</b></td><td>{x.type}</td><td>{shortMoney(x.generated)}</td><td>{shortMoney(x.paid)}</td><td><b>{shortMoney(x.balance)}</b></td></tr>)}</tbody></table></div></Card></div>}
