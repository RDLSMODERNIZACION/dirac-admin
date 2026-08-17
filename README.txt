CLIENTES - VISTA LIMPIA

Se eliminan de la pantalla principal:
- 8 KPI superiores
- Facturación por cliente
- Cartera de cobranza

Se conserva:
- Título Clientes
- + Nuevo cliente
- Buscador
- Ordenar por
- Tabla ejecutiva
- Riesgo
- Click en fila para ficha del cliente
- Menú ⋯ Editar / Eliminar

No requiere backend ni SQL.
Solo requiere deploy de Vercel.

Aplicar:
.\APLICAR.ps1

Luego:
git diff
git add .
git commit -m "Simplificar vista de clientes"
git push
