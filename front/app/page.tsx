'use client';

import { useMemo, useState } from 'react';
import { mock } from '@/src/data/mock';
import { Sidebar } from '@/src/components/Sidebar';
import { Dashboard } from '@/src/components/Dashboard';
import { Works } from '@/src/components/Works';
import { Suppliers } from '@/src/components/Suppliers';
import { Stock } from '@/src/components/Stock';
import { Purchases } from '@/src/components/Purchases';
import { Finance } from '@/src/components/Finance';
import { Reports } from '@/src/components/Reports';

export type Section = 'dashboard' | 'works' | 'suppliers' | 'stock' | 'purchases' | 'finance' | 'reports';

export default function HomePage() {
  const [section, setSection] = useState<Section>('dashboard');
  const [selectedWork, setSelectedWork] = useState<string | null>(null);
  const [selectedSupplier, setSelectedSupplier] = useState<string | null>(null);

  const content = useMemo(() => {
    switch (section) {
      case 'works':
        return <Works works={mock.works} selectedId={selectedWork} onSelect={setSelectedWork} />;
      case 'suppliers':
        return <Suppliers suppliers={mock.suppliers} movements={mock.supplierMovements} selectedId={selectedSupplier} onSelect={setSelectedSupplier} />;
      case 'stock':
        return <Stock materials={mock.materials} movements={mock.stockMovements} />;
      case 'purchases':
        return <Purchases purchases={mock.purchases} />;
      case 'finance':
        return <Finance finance={mock.finance} movements={mock.financeMovements} />;
      case 'reports':
        return <Reports works={mock.works} clients={mock.clients} finance={mock.finance} />;
      default:
        return <Dashboard data={mock} onNavigate={(s) => setSection(s)} />;
    }
  }, [section, selectedWork, selectedSupplier]);

  return (
    <div className="app-shell">
      <Sidebar section={section} onChange={setSection} />
      <main className="main-area">
        <header className="topbar">
          <div>
            <div className="eyebrow">DIRAC · GESTIÓN INTEGRAL</div>
            <h1>{labelForSection(section)}</h1>
          </div>
          <div className="topbar-actions">
            <button className="ghost-button">15 AGO 2026</button>
            <button className="primary-button">+ Nuevo</button>
          </div>
        </header>
        {content}
      </main>
    </div>
  );
}

function labelForSection(section: Section) {
  const labels: Record<Section, string> = {
    dashboard: 'Resumen ejecutivo',
    works: 'Obras y contratos',
    suppliers: 'Proveedores y contratistas',
    stock: 'Stock de materiales',
    purchases: 'Compras',
    finance: 'Finanzas',
    reports: 'Reportes y ratios'
  };
  return labels[section];
}
