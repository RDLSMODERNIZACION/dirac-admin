'use client';

import { useEffect, useMemo, useState } from 'react';
import { api } from '@/src/lib/api';
import { money, shortMoney } from '@/src/lib/format';
import { Card, Empty, ErrorBox, Kpi, Loading, SectionTitle, Status } from './ui';
import { ResourceManager } from './ResourceManager';
import { specs } from '@/src/lib/resources';

type Row = {
  fixed_cost_id:string;
  period_start:string;
  due_date:string;
  name:string;
  category?:string|null;
  frequency:string;
  expected_amount:number;
  status:'pendiente'|'vence_pronto'|'vencido'|'pagado';
  payment?:any;
};

type Account={id:string;name:string;currency:string;is_active:boolean};

function todayIso(){ return new Date().toISOString().slice(0,10); }
function periodLabel(v:string){
  const d=new Date(`${String(v).slice(0,10)}T12:00:00`);
  return new Intl.DateTimeFormat('es-AR',{month:'long',year:'numeric'}).format(d);
}
function dateLabel(v:string){
  if(!v)return '—';
  const d=new Date(`${String(v).slice(0,10)}T12:00:00`);
  return new Intl.DateTimeFormat('es-AR').format(d);
}

export function FixedCostsPanel(){
  const [sub,setSub]=useState<'schedule'|'config'>('schedule');
  return <div className="page-stack">
    <div className="tabs standalone">
      <button className={sub==='schedule'?'active':''} onClick={()=>setSub('schedule')}>Vencimientos y pagos</button>
      <button className={sub==='config'?'active':''} onClick={()=>setSub('config')}>Configuración</button>
    </div>
    {sub==='schedule'?<Schedule/>:<ResourceManager hideTitle spec={specs.fixed_costs}/>} 
  </div>;
}

function Schedule(){
  const [rows,setRows]=useState<Row[]|null>(null);
  const [accounts,setAccounts]=useState<Account[]>([]);
  const [error,setError]=useState('');
  const [selected,setSelected]=useState<Row|null>(null);
  const [amount,setAmount]=useState('');
  const [accountId,setAccountId]=useState('');
  const [paymentDate,setPaymentDate]=useState(todayIso());
  const [notes,setNotes]=useState('');
  const [receipt,setReceipt]=useState<File|null>(null);
  const [saving,setSaving]=useState(false);

  async function load(){
    setError('');
    try{
      const [schedule,acc]=await Promise.all([
        api.get<Row[]>('/api/dashboard/fixed-cost-schedule?months=6'),
        api.list<Account>('accounts','?limit=500'),
      ]);
      setRows(schedule);
      setAccounts(acc.filter(x=>x.is_active));
    }catch(e:any){setError(e?.message||String(e));}
  }
  useEffect(()=>{void load();},[]);

  const pending=useMemo(()=>rows?.filter(x=>x.status!=='pagado')||[],[rows]);
  const overdue=useMemo(()=>pending.filter(x=>x.status==='vencido'),[pending]);
  const next30=useMemo(()=>{
    const limit=new Date();limit.setDate(limit.getDate()+30);
    return pending.filter(x=>new Date(`${x.due_date}T12:00:00`)<=limit).reduce((a,x)=>a+Number(x.expected_amount||0),0);
  },[pending]);

  function openPay(r:Row){
    setSelected(r);setAmount(String(r.expected_amount||0));setPaymentDate(todayIso());setNotes('');setReceipt(null);
    const ars=accounts.find(a=>a.currency==='ARS')||accounts[0];setAccountId(ars?.id||'');
  }

  async function pay(){
    if(!selected||!accountId||Number(amount)<=0)return;
    setSaving(true);setError('');
    try{
      const result=await api.post<any>(`/api/dashboard/fixed-costs/${selected.fixed_cost_id}/pay`,{
        period_start:String(selected.period_start).slice(0,10),
        account_id:accountId,
        amount:Number(amount),
        payment_date:paymentDate,
        notes:notes||null,
      });
      if(receipt&&result?.payment?.id){
        const form=new FormData();form.append('file',receipt);
        await api.upload(`/api/dashboard/fixed-cost-payments/${result.payment.id}/receipt`,form);
      }
      setSelected(null);await load();
    }catch(e:any){setError(e?.message||String(e));}
    finally{setSaving(false);}
  }

  async function openReceipt(paymentId:string){
    try{const r=await api.get<{url:string}>(`/api/dashboard/fixed-cost-payments/${paymentId}/receipt-url`);window.open(r.url,'_blank','noopener,noreferrer');}
    catch(e:any){setError(e?.message||String(e));}
  }

  if(error&&!rows)return <ErrorBox message={error} onRetry={load}/>;
  if(!rows)return <Loading/>;
  return <>
    {error&&<ErrorBox message={error} onRetry={load}/>} 
    <div className="kpi-grid three">
      <Kpi label="Próximos 30 días" value={shortMoney(next30)} note="Costos fijos aún no pagados" tone={next30>0?'warn':'good'}/>
      <Kpi label="Vencidos" value={String(overdue.length)} note={shortMoney(overdue.reduce((a,x)=>a+Number(x.expected_amount||0),0))} tone={overdue.length?'bad':'good'}/>
      <Kpi label="Períodos pendientes" value={String(pending.length)} note="Próximos 6 meses"/>
    </div>
    <Card>
      <SectionTitle title="Vencimientos de costos fijos" subtitle="Se proyectan automáticamente. La caja real cambia recién cuando registrás el pago."/>
      {rows.length===0?<Empty text="No hay costos fijos activos."/>:<div className="table-wrap"><table>
        <thead><tr><th>Período</th><th>Concepto</th><th>Vence</th><th>Esperado</th><th>Estado</th><th>Pago real</th><th>Cuenta</th><th>Acciones</th></tr></thead>
        <tbody>{rows.map((r,i)=><tr key={`${r.fixed_cost_id}-${r.period_start}-${i}`}>
          <td>{periodLabel(r.period_start)}</td>
          <td><b>{r.name}</b><span className="cell-sub">{r.category||r.frequency}</span></td>
          <td>{dateLabel(r.due_date)}</td>
          <td><b>{money(r.expected_amount)}</b></td>
          <td><Status tone={r.status==='pagado'?'green':r.status==='vencido'?'red':r.status==='vence_pronto'?'yellow':'blue'}>{r.status.replace('_',' ')}</Status></td>
          <td>{r.payment?money(r.payment.actual_amount):'—'}</td>
          <td>{r.payment?.account_name||'—'}</td>
          <td><div className="row-actions">
            {r.status!=='pagado'&&<button className="mini-button" onClick={()=>openPay(r)}>Pagar</button>}
            {r.payment?.receipt_path&&<button className="mini-button" onClick={()=>openReceipt(r.payment.id)}>Comprobante</button>}
          </div></td>
        </tr>)}</tbody>
      </table></div>}
    </Card>

    {selected&&<div className="modal-backdrop"><div className="modal">
      <div className="modal-head"><div><span className="eyebrow">REGISTRAR PAGO</span><h2>{selected.name}</h2><p>{periodLabel(selected.period_start)} · esperado {money(selected.expected_amount)}</p></div><button className="close-button" onClick={()=>setSelected(null)}>×</button></div>
      <div className="form-grid">
        <label className="field"><span>Cuenta *</span><select value={accountId} onChange={e=>setAccountId(e.target.value)}><option value="">Seleccionar...</option>{accounts.map(a=><option key={a.id} value={a.id}>{a.name} · {a.currency}</option>)}</select></label>
        <label className="field"><span>Monto real *</span><input type="number" step="0.01" value={amount} onChange={e=>setAmount(e.target.value)}/></label>
        <label className="field"><span>Fecha de pago *</span><input type="date" value={paymentDate} onChange={e=>setPaymentDate(e.target.value)}/></label>
        <label className="field"><span>Comprobante</span><input type="file" accept="application/pdf,image/*" onChange={e=>setReceipt(e.target.files?.[0]||null)}/></label>
        <label className="field full"><span>Notas</span><textarea rows={3} value={notes} onChange={e=>setNotes(e.target.value)}/></label>
      </div>
      <div className="modal-actions"><button className="ghost-button" onClick={()=>setSelected(null)}>Cancelar</button><button className="primary-button" disabled={saving||!accountId||Number(amount)<=0} onClick={pay}>{saving?'Guardando...':'Registrar pago'}</button></div>
    </div></div>}
  </>;
}
