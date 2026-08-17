FIX GANTT PRO - WINDOWS / ONEDRIVE

Este paquete corrige el error:
PermissionError: [WinError 32]

y también restaura:
front/src/components/Planning.tsx

NO usa shutil.copy2 sobre el mismo archivo.

ANTES DE APLICAR:
Desde la raíz de dirac-admin podés restaurar el archivo original con:

git restore front/src/components/Planning.tsx

Luego copiá este ZIP a la raíz y ejecutá:

.\APLICAR.ps1

Después:

cd front
npm run dev

Si funciona:
git add .
git commit -m "Mejorar cronograma Gantt"
git push
