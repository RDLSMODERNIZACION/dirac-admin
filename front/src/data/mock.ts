export const mock = {
  finance: {
    cash: 92500000,
    receivable: 28600000,
    payable: 17450000,
    overdueReceivable: 4500000,
    overduePayable: 1200000,
    fixedCosts: 6200000,
    monthlyRevenue: 24800000,
    monthlyResult: 8100000,
    projectedCash: [92500000, 86400000, 79500000, 70200000, 88500000],
    labels: ['Hoy', '30d', '60d', '90d', '180d'],
    debt: 18500000,
    stockValue: 13800000,
  },
  clients: [
    { name: 'Municipalidad RDLS', share: 54, revenue: 13400000 },
    { name: 'AICO', share: 18, revenue: 4500000 },
    { name: 'Tanckoating', share: 12, revenue: 3000000 },
    { name: 'Otros', share: 16, revenue: 3900000 },
  ],
  works: [
    { id: 'OB-026', client: 'Municipalidad RDLS', name: 'Telemetría plantas de agua', type: 'Servicio mensual', status: 'Activo', progress: 72, budgetConsumed: 61, contract: 36000000, estimatedCost: 14500000, actualCost: 12800000, billed: 24000000, collected: 19500000, start: '01/01/2026', end: '31/12/2026', manager: 'Víctor Pavez' },
    { id: 'OB-031', client: 'Municipalidad RDLS', name: 'Automatización cargaderos de agua', type: 'Proyecto', status: 'Activo', progress: 48, budgetConsumed: 57, contract: 18500000, estimatedCost: 7900000, actualCost: 4500000, billed: 8000000, collected: 4000000, start: '15/06/2026', end: '30/09/2026', manager: 'Víctor Pavez' },
    { id: 'OB-034', client: 'AICO', name: 'Certificación SIP', type: 'Servicio', status: 'Activo', progress: 85, budgetConsumed: 52, contract: 6800000, estimatedCost: 2100000, actualCost: 1100000, billed: 5000000, collected: 5000000, start: '20/07/2026', end: '25/08/2026', manager: 'Equipo técnico' },
    { id: 'OB-029', client: 'Municipalidad RDLS', name: 'Mantenimiento banco capacitores', type: 'Mantenimiento', status: 'Finalizado', progress: 100, budgetConsumed: 88, contract: 8200000, estimatedCost: 3100000, actualCost: 2720000, billed: 8200000, collected: 8200000, start: '01/07/2026', end: '30/07/2026', manager: 'Equipo técnico' },
  ],
  suppliers: [
    { id: 'PR-001', name: 'Neuquén Máquinas SRL', kind: 'Contratista', service: 'Retroexcavadora / camión', balance: 2080000, overdue: 720000, monthWorked: 2580000, lastPayment: '08/08/2026', status: 'Activo' },
    { id: 'PR-002', name: 'Electro Sur', kind: 'Proveedor', service: 'Material eléctrico', balance: 3400000, overdue: 0, monthWorked: 4150000, lastPayment: '12/08/2026', status: 'Activo' },
    { id: 'PR-003', name: 'Servicios Patagonia', kind: 'Contratista', service: 'Mano de obra especializada', balance: 1350000, overdue: 480000, monthWorked: 1900000, lastPayment: '02/08/2026', status: 'Activo' },
  ],
  supplierMovements: [
    { supplier: 'PR-001', date: '05/08/2026', work: 'OB-031', concept: 'Retroexcavadora', qty: 8, unit: 'horas', price: 120000, amount: 960000, approved: true, paid: 0 },
    { supplier: 'PR-001', date: '06/08/2026', work: 'OB-031', concept: 'Retroexcavadora', qty: 6, unit: 'horas', price: 120000, amount: 720000, approved: true, paid: 500000 },
    { supplier: 'PR-001', date: '08/08/2026', work: 'OB-026', concept: 'Camión volcador', qty: 10, unit: 'horas', price: 90000, amount: 900000, approved: false, paid: 0 },
    { supplier: 'PR-003', date: '11/08/2026', work: 'OB-034', concept: 'Técnico instrumentista', qty: 16, unit: 'horas', price: 30000, amount: 480000, approved: true, paid: 0 },
  ],
  materials: [
    { sku: 'CAB-4X10', name: 'Cable Sintenax 4x10 mm²', category: 'Cables', unit: 'm', stock: 85, min: 30, avgCost: 12500 },
    { sku: 'TUB-40', name: 'Caño tubing 40x40x2', category: 'Estructuras', unit: 'm', stock: 18, min: 24, avgCost: 18500 },
    { sku: 'TERM-25', name: 'Térmica tetrapolar 25 A', category: 'Protecciones', unit: 'u', stock: 12, min: 6, avgCost: 42000 },
    { sku: 'CONT-32', name: 'Contactor 32 A', category: 'Automatización', unit: 'u', stock: 4, min: 5, avgCost: 89000 },
    { sku: 'UTP-CAT6', name: 'Cable UTP Cat6 exterior', category: 'Comunicaciones', unit: 'm', stock: 340, min: 100, avgCost: 980 },
  ],
  stockMovements: [
    { date: '14/08/2026', type: 'Egreso', item: 'Cable Sintenax 4x10 mm²', qty: 25, unit: 'm', work: 'OB-031', responsible: 'Depósito' },
    { date: '13/08/2026', type: 'Ingreso', item: 'Térmica tetrapolar 25 A', qty: 10, unit: 'u', work: '-', responsible: 'Compra OC-118' },
    { date: '12/08/2026', type: 'Egreso', item: 'Contactor 32 A', qty: 2, unit: 'u', work: 'OB-029', responsible: 'Equipo técnico' },
  ],
  purchases: [
    { id: 'OC-118', supplier: 'Electro Sur', work: 'OB-031', date: '12/08/2026', due: '11/09/2026', amount: 1850000, status: 'Recibida', payment: 'Pendiente' },
    { id: 'OC-119', supplier: 'Neuquén Máquinas SRL', work: 'OB-031', date: '14/08/2026', due: '21/08/2026', amount: 1680000, status: 'Aprobada', payment: 'Pendiente' },
    { id: 'OC-115', supplier: 'Electro Sur', work: 'OB-029', date: '28/07/2026', due: '12/08/2026', amount: 920000, status: 'Recibida', payment: 'Pagada' },
  ],
  financeMovements: [
    { date: '10/08/2026', type: 'Cobro', entity: 'Municipalidad RDLS', concept: 'Certificado telemetría julio', work: 'OB-026', expected: '10/08/2026', real: '', amount: 4500000, status: 'Vencido' },
    { date: '12/08/2026', type: 'Pago', entity: 'Electro Sur', concept: 'Materiales OC-115', work: 'OB-029', expected: '12/08/2026', real: '12/08/2026', amount: 920000, status: 'Pagado' },
    { date: '20/08/2026', type: 'Pago', entity: 'Seguro', concept: 'Seguro vehículos', work: '-', expected: '20/08/2026', real: '', amount: 650000, status: 'Próximo' },
    { date: '25/08/2026', type: 'Cobro', entity: 'AICO', concept: 'Saldo certificación', work: 'OB-034', expected: '25/08/2026', real: '', amount: 1800000, status: 'Pendiente' },
  ]
};
