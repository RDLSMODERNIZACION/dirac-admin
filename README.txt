TAREAS PUNTUALES -> HITOS

Cuando una tarea normal tiene:
Inicio = Fin

el modal muestra:
"Actividad puntual de un día"
y ofrece:
"Convertir en hito"

Al convertir:
- Tipo pasa a Hito puntual
- Fin queda igual a Inicio
- En el cronograma se muestra como rombo ◆

Si realmente querés una tarea normal de un día, podés ignorar la sugerencia.

Aplicar:
.\APLICAR.ps1

Luego:
git diff
git status
git add .
git commit -m "Sugerir hitos para tareas puntuales"
git push

Solo requiere Vercel.
