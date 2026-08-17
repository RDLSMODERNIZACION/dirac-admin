# Dirac Administración API

Backend REST para el sistema de administración de Dirac. Trabaja sobre PostgreSQL/Supabase usando el schema `administracion`.

## Incluye

- CRUD genérico seguro (whitelist) para las 15 tablas iniciales.
- Crear, listar, buscar, editar y eliminar registros.
- Dashboard financiero macro.
- Proyección simple de caja.
- Stock actual calculado desde movimientos.
- Cuenta corriente resumida de proveedores.
- Rentabilidad por obra.
- Swagger/OpenAPI en `/docs`.
- CORS configurable.
- API key opcional.
- Archivos para Render y Docker.

## Tablas administradas

`clients`, `works`, `work_progress`, `suppliers`, `supplier_rates`, `supplier_services`, `materials`, `purchases`, `purchase_items`, `stock_movements`, `accounts`, `receivables`, `payables`, `financial_movements`, `fixed_costs`.

## 1. Configuración

Copiar `.env.example` a `.env`:

```powershell
Copy-Item .env.example .env
```

Completar especialmente:

```env
DATABASE_URL=postgresql://...
DB_SCHEMA=administracion
CORS_ORIGINS=http://localhost:3000
API_KEY=una-clave-segura
```

La contraseña de Supabase y la API key **nunca** deben ir al frontend ni subirse a Git.

## 2. Ejecutar localmente

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Abrir:

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

Si configuraste `API_KEY`, Swagger permite enviar el header manualmente desde cada request como `X-API-Key`.

## 3. CRUD

Todos los recursos siguen el mismo patrón.

### Listar

```http
GET /api/clients
GET /api/works?status=activo
GET /api/materials?q=cable
GET /api/payables?limit=100&offset=0
```

### Obtener uno

```http
GET /api/works/{uuid}
```

### Crear

```http
POST /api/clients
Content-Type: application/json
X-API-Key: ...

{
  "name": "Municipalidad",
  "tax_id": "...",
  "is_active": true
}
```

### Editar parcialmente

```http
PATCH /api/works/{uuid}
Content-Type: application/json

{
  "status": "activo",
  "progress_percent": 40
}
```

### Eliminar

```http
DELETE /api/works/{uuid}
```

Las foreign keys de PostgreSQL siguen protegiendo integridad referencial. Por ejemplo, no se podrá borrar un cliente si una obra lo referencia con `ON DELETE RESTRICT`.

## 4. Endpoints de gestión

```http
GET /api/dashboard/summary
GET /api/dashboard/cash-projection?days=90
GET /api/reports/current-stock
GET /api/reports/supplier-balances
GET /api/reports/work-profitability
GET /api/meta/tables
```

## 5. Conexión con el frontend

Ejemplo:

```ts
const API = process.env.NEXT_PUBLIC_ADMIN_API_URL!;

const response = await fetch(`${API}/api/works?status=activo`, {
  headers: {
    "X-API-Key": process.env.NEXT_PUBLIC_ADMIN_API_KEY ?? "",
  },
});

const works = await response.json();
```

### Importante para producción

No es recomendable exponer una API key administrativa persistente como `NEXT_PUBLIC_*`. Para producción, la siguiente etapa debería usar autenticación de usuarios (Supabase Auth/JWT) o llamadas server-side desde Next.js. La `API_KEY` incluida sirve para una primera integración controlada y pruebas.

## 6. Render

El repositorio incluye `render.yaml`. Variables mínimas:

- `DATABASE_URL`
- `DB_SCHEMA=administracion`
- `CORS_ORIGINS=https://tu-dominio.vercel.app`
- `API_KEY=...`

El endpoint de health check es `/health`.

## 7. Modelo de negocio

El backend diferencia deliberadamente:

- `receivables` / `payables`: compromisos pendientes.
- `financial_movements`: dinero realmente cobrado o pagado.
- `supplier_services`: horas/servicios generados por contratistas.
- `stock_movements`: entradas y consumos reales de material.

Esto permite calcular rentabilidad y caja por separado.
