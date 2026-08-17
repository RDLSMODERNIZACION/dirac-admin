from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
p = ROOT / 'front/src/components/ServicesBoard.tsx'
t = p.read_text(encoding='utf-8')
old = "          const progress=Math.max(0,Math.min(100,Number(r.billing_progress_percent||0)));\n"
if old in t: t = t.replace(old, '', 1)
old = '''            <td><div className="works-progress"><div><b>{r.billed_periods}/{r.total_periods}</b><span><i style={{width:`${progress}%`}}/></span></div></div></td>'''
new = '''            <td className="service-period-count"><b>{r.billed_periods}/{r.total_periods}</b></td>'''
if old not in t: raise SystemExit('ERROR: no encontré la barra de períodos en ServicesBoard.tsx')
t = t.replace(old, new, 1)
p.write_text(t, encoding='utf-8')
p = ROOT / 'front/app/globals.css'
css = p.read_text(encoding='utf-8')
extra = '''
/* Servicios: tabla compacta sin barra visual de períodos */
.services-board-table{width:100%;table-layout:auto}
.services-board-table th,.services-board-table td{padding-left:8px!important;padding-right:8px!important}
.services-board-table td:first-child{min-width:185px!important}
.services-board-table td:nth-child(2){min-width:155px!important}
.services-board-table td:nth-child(3){min-width:120px!important}
.services-board-table td:nth-child(4){min-width:105px!important}
.services-board-table td:nth-child(5){min-width:68px!important;width:68px!important}
.services-board-table td:nth-child(6),.services-board-table td:nth-child(7),.services-board-table td:nth-child(8){min-width:100px!important}
.services-board-table td:nth-child(9){min-width:42px!important;width:42px!important}
.service-period-count{white-space:nowrap;text-align:left}
@media(min-width:1000px){.works-board-table-wrap{overflow-x:visible!important}}
'''
if '/* Servicios: tabla compacta sin barra visual de períodos */' not in css: css = css.rstrip() + '\n\n' + extra + '\n'
p.write_text(css, encoding='utf-8')
print('OK: barra azul de períodos eliminada y tabla compactada.')