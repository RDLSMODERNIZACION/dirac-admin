# Dirac Gestión — Front hardcodeado

Prototipo navegable en **Next.js + TypeScript** para validar la arquitectura de una app de gestión integral antes de construir backend.

## Módulos incluidos

- Dashboard ejecutivo
- Obras y contratos
- Ficha de obra con avance físico / consumo presupuestario / facturación / cobros
- Proveedores y contratistas
- Cuenta corriente de contratistas con horas, tarifas, validación y pagos
- Stock y movimientos por obra
- Compras
- Finanzas: caja, cuentas por cobrar/pagar, vencimientos y proyección
- Reportes y ratios económicos

## Importante

Todo está hardcodeado en `src/data/mock.ts`. Los botones de alta son visuales; no persisten datos todavía.

## Ejecutar

```bash
npm install
npm run dev
```

Abrir `http://localhost:3000`.

## Próximo paso recomendado

Antes de backend, validar nombres de módulos, campos de cada entidad y flujos principales. Luego reemplazar `mock.ts` por servicios/API y persistencia.
