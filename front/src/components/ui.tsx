'use client';
import React from 'react';
import { money, shortMoney } from '@/src/lib/format';

export function Card({children,className=''}:{children:React.ReactNode;className?:string}){return <div className={`card ${className}`}>{children}</div>}
export function SectionTitle({title,subtitle,action}:{title:string;subtitle?:string;action?:React.ReactNode}){return <div className="section-title"><div><h2>{title}</h2>{subtitle&&<p>{subtitle}</p>}</div>{action}</div>}
export function Status({children,tone='gray'}:{children:React.ReactNode;tone?:'green'|'yellow'|'red'|'blue'|'gray'}){return <span className={`status ${tone}`}>{children}</span>}
export function Kpi({label,value,note,tone='neutral'}:{label:string;value:string;note?:string;tone?:'good'|'warn'|'bad'|'neutral'}){return <Card className={`kpi ${tone}`}><span className="kpi-label">{label}</span><strong>{value}</strong>{note&&<small>{note}</small>}</Card>}
export function Progress({value}:{value:any}){const n=Math.max(0,Math.min(100,Number(value||0)));return <div className="progress-row"><div className="progress-track"><span className={n>90?'danger':n>70?'warn':'ok'} style={{width:`${n}%`}}/></div><b>{n.toFixed(0)}%</b></div>}
export function Empty({text='No hay registros todavía.'}:{text?:string}){return <div className="empty-state">{text}</div>}
export function Loading(){return <div className="empty-state">Cargando datos reales…</div>}
export function ErrorBox({message,onRetry}:{message:string;onRetry?:()=>void}){return <div className="alert red"><b>No se pudo cargar</b><span>{message}</span>{onRetry&&<button className="link-button" onClick={onRetry}>Reintentar</button>}</div>}
export { money, shortMoney };
