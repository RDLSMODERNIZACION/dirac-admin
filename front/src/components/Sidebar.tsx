'use client';
import type { Section } from '@/app/page';
const items:{id:Section;label:string;icon:string}[]=[
 {id:'dashboard',label:'Inicio',icon:'⌂'},
 {id:'accounts',label:'Cuentas',icon:'▰'},
 {id:'jobs',label:'Trabajos',icon:'▣'},
 {id:'planning',label:'Planificación',icon:'◷'},
 {id:'clients',label:'Clientes',icon:'◉'},
 {id:'suppliers',label:'Proveedores',icon:'◫'},
 {id:'stock',label:'Stock',icon:'▦'},
 {id:'finance',label:'Finanzas',icon:'$'},
 {id:'reports',label:'Reportes',icon:'▥'}
];
export function Sidebar({section,onChange}:{section:Section;onChange:(s:Section)=>void}){return <aside className="sidebar"><div className="brand"><div className="brand-mark">D</div><div><strong>DIRAC</strong><span>Gestión integral</span></div></div><nav>{items.map(i=><button key={i.id} className={`nav-item ${section===i.id?'active':''}`} onClick={()=>onChange(i.id)}><span className="nav-icon">{i.icon}</span>{i.label}</button>)}</nav><div className="sidebar-footer"><div className="avatar">DP</div><div><strong>Administración</strong><span>Datos en vivo</span></div></div></aside>}
