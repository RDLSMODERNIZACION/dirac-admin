PROVEEDORES EJECUTIVO AGRUPADO

Se eliminan las pestañas:
- Tarifas
- Horas y servicios

Agrupamiento:
- Flota vehicular
- Marketing
- Contratistas

Pantalla principal:
- KPI compactos estilo tabla
- Filtros por grupo
- Buscador
- Proveedores agrupados
- Pendiente
- Vencido
- Último pago
- Estado
- Riesgo

Click en proveedor:
abre panel lateral con:
- Resumen
- Cuentas por pagar
- Pagos
- Documentación

Desde el lateral:
- Editar
- Eliminar

Documentación:
permite registrar tipo, título, fecha, URL y notas.

Migración automática:
- Facebook / Freeda / términos de publicidad -> Marketing
- Seguro / Microtrack / Nippon / términos de vehículo -> Flota vehicular
- resto -> Contratistas
Luego podés corregir el grupo desde Editar.

No requiere SQL manual.
El backend agrega supplier_group y supplier_documents automáticamente.

Aplicar:
.\APLICAR.ps1

Luego:
git diff
git status
git add .
git commit -m "Reorganizar proveedores por grupos"
git push

Requiere Render + Vercel.
