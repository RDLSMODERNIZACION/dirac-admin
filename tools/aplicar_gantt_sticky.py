from pathlib import Path

p=Path.cwd()/'front/app/globals.css'
css=p.read_text(encoding='utf-8')

block='''

/* GANTT - COLUMNA OBRA/TAREA FIJA */
.gantt-pro-shell{position:relative}
.gantt-left-head{
  position:sticky;
  left:0;
  z-index:40;
  background:#fff;
  box-shadow:8px 0 14px -14px rgba(15,34,55,.45);
}
.gantt-work-main-info{
  position:sticky;
  left:0;
  z-index:32;
  background:#eaf2fc;
  box-shadow:8px 0 14px -14px rgba(15,34,55,.45);
}
.gantt-row-info{
  position:sticky;
  left:0;
  z-index:30;
  background:#fff;
  box-shadow:8px 0 14px -14px rgba(15,34,55,.35);
}
.gantt-row-pro.selected .gantt-row-info{background:#f4f8ff}
'''

if '/* GANTT - COLUMNA OBRA/TAREA FIJA */' not in css:
    css += block

p.write_text(css,encoding='utf-8')
print('OK: columna Obra / tarea fijada durante el scroll horizontal.')
