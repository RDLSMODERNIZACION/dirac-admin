import React from 'react';

export const money = (n: number) => new Intl.NumberFormat('es-AR', { style: 'currency', currency: 'ARS', maximumFractionDigits: 0 }).format(n);
export const shortMoney = (n: number) => n >= 1_000_000 ? `$ ${(n/1_000_000).toFixed(1)} M` : money(n);

export function Card({ children, className = '' }: React.PropsWithChildren<{ className?: string }>) {
  return <div className={`card ${className}`}>{children}</div>;
}

export function Kpi({ label, value, note, tone = 'neutral' }: { label: string; value: string; note?: string; tone?: 'neutral'|'good'|'warn'|'bad' }) {
  return <Card className={`kpi ${tone}`}><span className="kpi-label">{label}</span><strong>{value}</strong>{note && <small>{note}</small>}</Card>;
}

export function Status({ children, tone }: React.PropsWithChildren<{ tone?: 'green'|'yellow'|'red'|'blue'|'gray' }>) {
  return <span className={`status ${tone || 'gray'}`}>{children}</span>;
}

export function Progress({ value, dangerAt = 85 }: { value: number; dangerAt?: number }) {
  const tone = value >= dangerAt ? 'danger' : value >= 65 ? 'warn' : 'ok';
  return <div className="progress-row"><div className="progress-track"><span className={tone} style={{width: `${Math.min(value,100)}%`}} /></div><b>{value}%</b></div>;
}

export function SectionTitle({ title, subtitle, action }: { title: string; subtitle?: string; action?: React.ReactNode }) {
  return <div className="section-title"><div><h2>{title}</h2>{subtitle && <p>{subtitle}</p>}</div>{action}</div>;
}
