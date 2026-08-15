'use client';
import { useState } from 'react';
import { Sidebar } from '@/src/components/Sidebar';
import { Dashboard } from '@/src/components/Dashboard';
import { Clients, Finance, Purchases, Reports, Stock, Suppliers, Works } from '@/src/components/Modules';
import { API_URL } from '@/src/lib/api';

export type Section='dashboard'|'works'|'clients'|'suppliers'|'stock'|'purchases'|'finance'|'reports';
export default function HomePage(){const [section,setSection]=useState<Section>('dashboard');return <div className="app-shell"><Sidebar section={section} onChange={setSection}/><main className="main-area"><header className="topbar"><div><div className="eyebrow">DIRAC · GESTIÓN INTEGRAL</div><h1>{labels[section]}</h1></div><div className="topbar-actions"><span className="api-pill">● API Render</span><button className="ghost-button" title={API_URL}>Conectado</button></div></header>{section==='dashboard'&&<Dashboard onNavigate={setSection}/>} {section==='works'&&<Works/>}{section==='clients'&&<Clients/>}{section==='suppliers'&&<Suppliers/>}{section==='stock'&&<Stock/>}{section==='purchases'&&<Purchases/>}{section==='finance'&&<Finance/>}{section==='reports'&&<Reports/>}</main></div>}
const labels:Record<Section,string>={dashboard:'Resumen ejecutivo',works:'Obras y contratos',clients:'Clientes',suppliers:'Proveedores y contratistas',stock:'Stock de materiales',purchases:'Compras',finance:'Finanzas',reports:'Reportes y ratios'};
