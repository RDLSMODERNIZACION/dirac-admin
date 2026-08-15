import type { Section } from '@/app/page';

const items: { key: Section; label: string; icon: string }[] = [
  { key: 'dashboard', label: 'Inicio', icon: '▦' },
  { key: 'works', label: 'Obras', icon: '◫' },
  { key: 'suppliers', label: 'Proveedores', icon: '⌂' },
  { key: 'stock', label: 'Stock', icon: '◈' },
  { key: 'purchases', label: 'Compras', icon: '▣' },
  { key: 'finance', label: 'Finanzas', icon: '$' },
  { key: 'reports', label: 'Reportes', icon: '↗' },
];

export function Sidebar({ section, onChange }: { section: Section; onChange: (s: Section) => void }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="brand-mark">D</div>
        <div><strong>DIRAC</strong><span>Gestión</span></div>
      </div>
      <nav>
        {items.map((item) => (
          <button key={item.key} onClick={() => onChange(item.key)} className={section === item.key ? 'nav-item active' : 'nav-item'}>
            <span className="nav-icon">{item.icon}</span>{item.label}
          </button>
        ))}
      </nav>
      <div className="sidebar-footer">
        <div className="avatar">VP</div>
        <div><strong>Víctor Pavez</strong><span>Administrador</span></div>
      </div>
    </aside>
  );
}
