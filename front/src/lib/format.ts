export const money = (v: any) => new Intl.NumberFormat('es-AR', { style:'currency', currency:'ARS', maximumFractionDigits:0 }).format(Number(v || 0));
export const shortMoney = (v: any) => {
  const n = Number(v || 0);
  if (Math.abs(n) >= 1_000_000) return `$ ${(n/1_000_000).toLocaleString('es-AR',{maximumFractionDigits:1})} M`;
  if (Math.abs(n) >= 1_000) return `$ ${(n/1_000).toLocaleString('es-AR',{maximumFractionDigits:0})} mil`;
  return money(n);
};
export const pct = (v:any) => `${(Number(v || 0) * 100).toFixed(1)}%`;
export const dateAR = (v:any) => v ? new Date(`${String(v).slice(0,10)}T12:00:00`).toLocaleDateString('es-AR') : '—';
