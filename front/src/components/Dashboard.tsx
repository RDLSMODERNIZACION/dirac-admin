import type { Section } from '@/app/page';
import { Card, Kpi, Progress, SectionTitle, Status, shortMoney } from './ui';

export function Dashboard({ data, onNavigate }: { data: any; onNavigate: (s: Section) => void }) {
  const f = data.finance;
  const net = f.cash + f.receivable - f.payable;
  const coverage = f.cash / f.fixedCosts;
  return <div className="page-stack">
    <div className="kpi-grid four">
      <Kpi label="Caja disponible" value={shortMoney(f.cash)} note="Disponibilidad actual" tone="good" />
      <Kpi label="Por cobrar" value={shortMoney(f.receivable)} note={`${shortMoney(f.overdueReceivable)} vencidos`} tone={f.overdueReceivable ? 'warn' : 'good'} />
      <Kpi label="Por pagar" value={shortMoney(f.payable)} note={`${shortMoney(f.overduePayable)} vencidos`} tone={f.overduePayable ? 'warn' : 'neutral'} />
      <Kpi label="Posición neta" value={shortMoney(net)} note="Caja + créditos − obligaciones" tone="good" />
    </div>

    <div className="two-col wide-left">
      <Card>
        <SectionTitle title="Caja proyectada" subtitle="Cobros y pagos previstos" action={<button className="link-button" onClick={() => onNavigate('finance')}>Ver finanzas →</button>} />
        <div className="cash-chart">
          {f.projectedCash.map((v:number, i:number) => {
            const max = Math.max(...f.projectedCash);
            return <div className="bar-wrap" key={f.labels[i]}><div className="bar-value">{shortMoney(v)}</div><div className="bar-shell"><div className="bar" style={{height: `${Math.max(18,(v/max)*150)}px`}} /></div><span>{f.labels[i]}</span></div>
          })}
        </div>
      </Card>
      <Card>
        <SectionTitle title="Salud económica" subtitle="Indicadores principales" />
        <div className="health-list">
          <div><span>Resultado mensual</span><strong>{shortMoney(f.monthlyResult)}</strong><Status tone="green">Positivo</Status></div>
          <div><span>Costos fijos</span><strong>{shortMoney(f.fixedCosts)}</strong><Status tone="blue">Mensual</Status></div>
          <div><span>Cobertura de caja</span><strong>{coverage.toFixed(1)} meses</strong><Status tone="green">Sólida</Status></div>
          <div><span>Deuda financiera</span><strong>{shortMoney(f.debt)}</strong><Status tone="yellow">Controlar</Status></div>
        </div>
      </Card>
    </div>

    <div className="two-col">
      <Card>
        <SectionTitle title="Obras activas" subtitle="Avance físico vs. presupuesto consumido" action={<button className="link-button" onClick={() => onNavigate('works')}>Ver todas →</button>} />
        <div className="list-stack">
          {data.works.filter((w:any)=>w.status==='Activo').slice(0,3).map((w:any)=><div className="work-mini" key={w.id}>
            <div className="work-mini-head"><div><b>{w.id}</b><span>{w.name}</span></div><Status tone="blue">{w.client}</Status></div>
            <div className="dual-progress"><span>Avance</span><Progress value={w.progress}/><span>Presupuesto</span><Progress value={w.budgetConsumed}/></div>
          </div>)}
        </div>
      </Card>
      <Card>
        <SectionTitle title="Alertas" subtitle="Lo que requiere atención" />
        <div className="alerts">
          <div className="alert red"><b>Cobro vencido</b><span>Municipalidad · $ 4,5 M · 5 días</span></div>
          <div className="alert yellow"><b>Stock bajo</b><span>Caño tubing 40x40x2 · 18 m</span></div>
          <div className="alert yellow"><b>Proveedor con deuda vencida</b><span>Neuquén Máquinas · $ 720.000</span></div>
          <div className="alert blue"><b>Pago próximo</b><span>Seguro vehículos · $ 650.000 · 20/08</span></div>
        </div>
      </Card>
    </div>

    <div className="kpi-grid four">
      <Kpi label="Facturación del mes" value={shortMoney(f.monthlyRevenue)} />
      <Kpi label="Resultado del mes" value={shortMoney(f.monthlyResult)} tone="good" />
      <Kpi label="Valor de stock" value={shortMoney(f.stockValue)} />
      <Kpi label="Obras activas" value={String(data.works.filter((w:any)=>w.status==='Activo').length)} />
    </div>
  </div>
}
