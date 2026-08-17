MODULO PLANIFICACION - DIRAC

Agrega en Sidebar:
- Planificación

Vista general:
- Tareas
- Cronograma tipo Gantt
- Pendientes
- En ejecución
- Vencidas
- Próximos 7 días

Cada tarea:
- Obra obligatoria
- Ítem de obra opcional
- Título
- Descripción
- Responsable
- Inicio / Fin
- Prioridad
- Estado
- Avance %
- Notas

Dentro de cada Obra:
- nueva pestaña "Cronograma"
- muestra las mismas tareas filtradas por esa obra
- permite crear tareas directamente para esa obra

La tabla planning_tasks se crea automáticamente desde el backend.
No requiere SQL manual.

Aplicar:
1. Copiar backend/, front/, tools/, PLANNING_CSS.txt y APLICAR.ps1 a la raíz.
2. Ejecutar:
   .\APLICAR.ps1
3. Revisar:
   git diff
   git status
4. Subir:
   git add .
   git commit -m "Agregar modulo de planificacion y cronograma"
   git push

Requiere deploy de Render y Vercel.
