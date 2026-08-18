'use client';

import { FormEvent, useEffect, useState } from 'react';
import { Sidebar } from '@/src/components/Sidebar';
import { Dashboard } from '@/src/components/Dashboard';
import { Accounts, Clients, Finance, Reports, Services, Stock, Suppliers, Works } from '@/src/components/Modules';
import { Jobs } from '@/src/components/Jobs';
import { Planning } from '@/src/components/Planning';
import { api, clearAuthToken, getAuthToken, setAuthToken } from '@/src/lib/api';

export type Section='dashboard'|'accounts'|'jobs'|'planning'|'services'|'works'|'clients'|'suppliers'|'stock'|'finance'|'reports';

export default function HomePage(){
 const [section,setSection]=useState<Section>('dashboard');
 const [authChecking,setAuthChecking]=useState(true);
 const [user,setUser]=useState('');
 const [loginError,setLoginError]=useState('');
 const [loginLoading,setLoginLoading]=useState(false);

 useEffect(()=>{
  const check=async()=>{
   if(!getAuthToken()){setAuthChecking(false);return}
   try{
    const me=await api.get<{username:string}>('/api/auth/me');
    setUser(me.username);
   }catch{
    clearAuthToken();
   }finally{
    setAuthChecking(false);
   }
  };
  void check();

  const requireLogin=()=>{setUser('');setAuthChecking(false)};
  window.addEventListener('dirac-auth-required',requireLogin);
  return()=>window.removeEventListener('dirac-auth-required',requireLogin);
 },[]);

 const doLogin=async(username:string,password:string)=>{
  setLoginLoading(true);setLoginError('');
  try{
   const result=await api.post<{token:string;username:string}>('/api/auth/login',{username,password});
   setAuthToken(result.token);
   setUser(result.username);
  }catch(e:any){
   setLoginError(e?.message||'No se pudo iniciar sesión');
  }finally{
   setLoginLoading(false);
  }
 };

 const logout=async()=>{
  try{await api.post('/api/auth/logout',{})}catch{}
  clearAuthToken();
  setUser('');
  setSection('dashboard');
 };

 if(authChecking)return <div className="login-screen"><div className="login-card"><div className="login-brand">DIRAC</div><p>Verificando sesión…</p></div></div>;
 if(!user)return <LoginForm loading={loginLoading} error={loginError} onLogin={doLogin}/>;

 return <div className="app-shell">
  <Sidebar section={section} onChange={setSection}/>
  <main className="main-area">
   <header className="topbar">
    <div><div className="eyebrow">DIRAC · GESTIÓN INTEGRAL</div><h1>{labels[section]}</h1></div>
    <div className="topbar-actions">
     <span className="api-pill">● API Render</span>
     <span className="user-pill">{user}</span>
     <button className="ghost-button" onClick={logout}>Cerrar sesión</button>
    </div>
   </header>
   {section==='dashboard'&&<Dashboard onNavigate={setSection}/>}
   {section==='accounts'&&<Accounts/>}
   {section==='jobs'&&<Jobs/>}
   {section==='planning'&&<Planning/>}
   {section==='services'&&<Services/>}
   {section==='works'&&<Works/>}
   {section==='clients'&&<Clients/>}
   {section==='suppliers'&&<Suppliers/>}
   {section==='stock'&&<Stock/>}
   {section==='finance'&&<Finance/>}
   {section==='reports'&&<Reports/>}
  </main>
 </div>
}

function LoginForm({loading,error,onLogin}:{loading:boolean;error:string;onLogin:(u:string,p:string)=>Promise<void>}){
 const [username,setUsername]=useState('');
 const [password,setPassword]=useState('');

 const submit=(e:FormEvent)=>{
  e.preventDefault();
  if(!username.trim()||!password)return;
  void onLogin(username,password);
 };

 return <div className="login-screen">
  <form className="login-card" onSubmit={submit}>
   <div className="login-brand">DIRAC</div>
   <div className="login-eyebrow">GESTIÓN INTEGRAL</div>
   <h1>Iniciar sesión</h1>
   <p>Acceso administrativo</p>
   <label className="login-field"><span>Usuario</span><input autoFocus autoComplete="username" value={username} onChange={e=>setUsername(e.target.value)} placeholder="Usuario"/></label>
   <label className="login-field"><span>Contraseña</span><input type="password" autoComplete="current-password" value={password} onChange={e=>setPassword(e.target.value)} placeholder="Contraseña"/></label>
   {error&&<div className="login-error">{error}</div>}
   <button className="primary-button login-submit" type="submit" disabled={loading||!username.trim()||!password}>{loading?'Ingresando…':'Ingresar'}</button>
  </form>
 </div>
}

const labels:Record<Section,string>={dashboard:'Resumen ejecutivo',accounts:'Cuentas y liquidez',jobs:'Trabajos',planning:'Planificación',services:'Servicios',works:'Obras',clients:'Clientes',suppliers:'Proveedores y contratistas',stock:'Stock de materiales',finance:'Finanzas',reports:'Reportes y ratios'};
