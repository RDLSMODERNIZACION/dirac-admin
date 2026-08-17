PLANIFICACION PRO + DEPENDENCIAS

Incluye:
- Gantt profesional.
- Click en barra = selecciona tarea y abre panel lateral.
- Editar / Eliminar / Duplicar / Completar.
- Tareas normales e Hitos puntuales.
- Antecesoras múltiples.
- Sucesoras automáticas.
- Relación Fin -> Inicio.
- Prevención de ciclos de dependencias.
- Arrastrar barra horizontalmente para mover la tarea por días.
- Opción "Reprogramar sucesoras al mover".
- Vista Calendario.
- Vista Tareas.
- Filtro por responsable y estado.
- Dependencias visibles en panel y en la fila del Gantt.

BASE DE DATOS
No requiere SQL manual.
El backend crea automáticamente:
administracion.planning_task_dependencies
y agrega planning_tasks.task_type si hace falta.

IMPORTANTE
La reprogramación automática desplaza las sucesoras la misma cantidad de días.
No modifica duración de las tareas sucesoras.

APLICAR
Desde la raíz del repo:

.\APLICAR.ps1

Luego desplegar Render y Vercel.

Recomendado:
git diff
git status
git add .
git commit -m "Planificacion pro con dependencias"
git push
