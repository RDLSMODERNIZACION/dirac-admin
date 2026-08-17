CRONOGRAMA LEGIBLE

Cambios:
- cada semana tiene ancho fijo de 128 px
- el cronograma ya no se comprime; usa scroll horizontal
- obras 100% ejecutadas no aparecen
- jerarquía visual clara:
  OBRA
    Plazo de obra
      Tareas
- conserva arrastre, dependencias y reprogramación

Aplicar:
.\APLICAR.ps1

Luego:
git diff
git status
git add .
git commit -m "Mejorar lectura del cronograma"
git push

Solo requiere Vercel.
