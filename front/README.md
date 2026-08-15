# Dirac Administración — Front conectado a Render

Frontend Next.js sin datos mock. Consume directamente el backend FastAPI desplegado en Render y, a través de él, el schema `administracion` de Supabase.

## Backend por defecto

`https://dirac-admin.onrender.com`

Se puede cambiar con:

```env
NEXT_PUBLIC_API_URL=https://dirac-admin.onrender.com
NEXT_PUBLIC_API_KEY=
```

## Ejecutar local

```powershell
npm install
Copy-Item .env.example .env.local
npm run dev
```

Abrir `http://localhost:3000`.

## Vercel

- Root Directory: `front` si este proyecto vive dentro del monorepo.
- Framework Preset: Next.js.
- Variable: `NEXT_PUBLIC_API_URL=https://dirac-admin.onrender.com`.

El backend de Render debe incluir la URL de Vercel dentro de `CORS_ORIGINS`, por ejemplo:

`http://localhost:3000,https://tu-app.vercel.app`

## Funciones conectadas

- Dashboard y proyección de caja.
- Clientes CRUD.
- Obras CRUD y avances de obra.
- Proveedores/contratistas CRUD.
- Tarifas y servicios/horas CRUD.
- Materiales y movimientos de stock CRUD.
- Stock actual calculado por backend.
- Compras e ítems CRUD.
- Cuentas, cuentas por cobrar, cuentas por pagar, movimientos financieros y costos fijos CRUD.
- Reportes de rentabilidad de obra, saldos de proveedores y concentración por cliente.

No existe `mock.ts`; si la base está vacía, la interfaz muestra estados vacíos reales.
