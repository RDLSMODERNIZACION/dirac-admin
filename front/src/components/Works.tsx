import { Card, Progress, SectionTitle, Status, money, shortMoney } from './ui';

export function Works({ works, selectedId, onSelect }: any) {
  const selected = works.find((w:any)=>w.id===selectedId);
  if (selected) return <WorkDetail work={selected} onBack={()=>onSelect(null)} />;
  return <div className="page-stack">
    <SectionTitle title="Obras y contratos" subtitle="Cada costo, compra, material y cobro puede asociarse a una obra." action={<button className="primary-button">+ Nueva obra</button>} />
    <Card><div className="table-toolbar"><input placeholder="Buscar obra, cliente o código…"/><select><option>Todos los estados</option><option>Activos</option><option>Finalizados</option></select></div>
      <div className="table-wrap"><table><thead><tr><th>Obra</th><th>Cliente</th><th>Estado</th><th>Avance</th><th>Contrato</th><th>Costo real</th><th>Margen</th><th>Cobrado</th></tr></thead><tbody>
      {works.map((w:any)=><tr key={w.id} onClick={()=>onSelect(w.id)} className="clickable"><td><b>{w.id}</b><span className="cell-sub">{w.name}</span></td><td>{w.client}</td><td><Status tone={w.status==='Activo'?'blue':'green'}>{w.status}</Status></td><td><Progress value={w.progress}/></td><td>{shortMoney(w.contract)}</td><td>{shortMoney(w.actualCost)}</td><td>{Math.round(((w.contract-w.actualCost)/w.contract)*100)}%</td><td>{shortMoney(w.collected)}</td></tr>)}
      </tbody></table></div>
    </Card>
  </div>
}

function WorkDetail({ work:w, onBack }:any){
  const margin=w.contract-w.actualCost;
  return <div className="page-stack">
    <button className="link-button" onClick={onBack}>← Volver a obras</button>
    <div className="detail-head"><div><span className="eyebrow">{w.id}</span><h2>{w.name}</h2><p>{w.client} · Responsable: {w.manager}</p></div><Status tone={w.status==='Activo'?'blue':'green'}>{w.status}</Status></div>
    <div className="kpi-grid four"><KpiLike label="Monto contratado" value={shortMoney(w.contract)}/><KpiLike label="Costo real" value={shortMoney(w.actualCost)}/><KpiLike label="Margen actual" value={shortMoney(margin)}/><KpiLike label="Cobrado" value={shortMoney(w.collected)}/></div>
    <div className="two-col">
      <Card><SectionTitle title="Ejecución" subtitle={`${w.start} → ${w.end}`} /><div className="metric-block"><label>Avance físico</label><Progress value={w.progress}/></div><div className="metric-block"><label>Presupuesto consumido</label><Progress value={w.budgetConsumed}/></div><div className="comparison"><div><span>Presupuestado</span><b>{money(w.estimatedCost)}</b></div><div><span>Real</span><b>{money(w.actualCost)}</b></div></div></Card>
      <Card><SectionTitle title="Facturación y cobros"/><div className="health-list"><div><span>Facturado</span><strong>{money(w.billed)}</strong></div><div><span>Cobrado</span><strong>{money(w.collected)}</strong></div><div><span>Pendiente de cobro</span><strong>{money(w.billed-w.collected)}</strong></div><div><span>Saldo por facturar</span><strong>{money(w.contract-w.billed)}</strong></div></div></Card>
    </div>
    <Card><div className="tabs"><button className="active">Resumen</button><button>Finanzas</button><button>Materiales</button><button>Compras</button><button>Avance</button><button>Documentos</button></div><div className="empty-state">Esta maqueta deja preparadas las secciones para conectar los datos reales de la obra.</div></Card>
  </div>
}
function KpiLike({label,value}:{label:string,value:string}){return <Card className="kpi"><span className="kpi-label">{label}</span><strong>{value}</strong></Card>}
