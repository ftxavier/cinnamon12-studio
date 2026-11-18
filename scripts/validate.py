#!/usr/bin/env python3
"""Static validation of packaged resources without running Cinnamon."""
from pathlib import Path
from PIL import Image
import json, xml.etree.ElementTree as ET
R=Path(__file__).resolve().parents[1]
errors=[]
def assert_ok(cond,msg):
 if not cond:errors.append(msg)
for v in ('Light','Dark'):
 p=R/'themes'/('Cinnamon12-'+v)
 assert_ok((p/'cinnamon'/'cinnamon.css').is_file(),f'missing Cinnamon CSS {v}')
 assert_ok((p/'gtk-3.0'/'gtk.css').is_file(),f'missing GTK3 {v}')
 for path in [p/'cinnamon'/'cinnamon.css',p/'gtk-3.0'/'gtk.css']:
  text=path.read_text();assert_ok('@VARIANT@' not in text, f'unresolved token in {path}')
icons=R/'icons'/'Cinnamon12-Icons'
assert_ok((icons/'index.theme').is_file(),'missing index.theme')
manifest=json.loads((R/'design'/'assets-manifest.json').read_text())
count=0
for c in ['apps','places','devices','mimetypes','actions','status']:
 for src in (icons/'scalable'/c).glob('*.svg'):
  count+=1
  try: ET.parse(src)
  except Exception as ex:errors.append(f'malformed SVG {src}: {ex}')
  for size in ([16,24,32,48] if c=='status' else [16,24,32,48,64,128]):
   f=icons/f'{size}x{size}'/c/(src.stem+'.png')
   if not f.is_file():errors.append('missing '+str(f));continue
   try:
    with Image.open(f) as im:assert_ok(im.size==(size,size),'bad icon size '+str(f))
   except Exception as ex:errors.append('bad PNG '+str(f)+' '+str(ex))
assert_ok(count==manifest['icon_count'],f'icon count {count} differs from manifest {manifest["icon_count"]}')
for name in ['c12-arctic','c12-aurora','c12-midnight']:
 for w,h in ((1920,1080),(2560,1440),(3840,2160)):
  f=R/'assets'/'wallpapers'/f'{name}-{w}x{h}.jpg'
  assert_ok(f.is_file(),str(f)+' missing')
  if f.is_file():
   with Image.open(f) as im:assert_ok(im.size==(w,h),str(f)+' wrong resolution')
for obj in (R/'applets').glob('*/metadata.json'):
 try:json.loads(obj.read_text())
 except Exception as ex:errors.append('invalid JSON '+str(obj)+str(ex))
for obj in (R/'desklets').glob('*/metadata.json'):
 try:json.loads(obj.read_text())
 except Exception as ex:errors.append('invalid JSON '+str(obj)+str(ex))
# WCAG AA contrast (4.5:1) for text pairs of both variants; derived values live in
# generate-themes.py (EXTRA), the base palette in design/tokens.json.
import importlib.util, re
_spec=importlib.util.spec_from_file_location('c12gen', R/'scripts'/'generate-themes.py')
_gen=importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_gen)
def _rgb(c, under=(1,1,1)):
 if c.startswith('#'): return tuple(int(c[i:i+2],16)/255 for i in (1,3,5))
 r,g,b,a=[float(x) for x in re.findall(r'[\d.]+',c)]
 return tuple(a*v/255+(1-a)*u for v,u in zip((r,g,b),under))
def _lum(c):
 f=lambda v: v/12.92 if v<=0.03928 else ((v+0.055)/1.055)**2.4
 r,g,b=map(f,c); return .2126*r+.7152*g+.0722*b
def _ratio(a,b):
 a,b=_lum(a),_lum(b); return (max(a,b)+.05)/(min(a,b)+.05)
contrast_checks=0
for v in ('light','dark'):
 p=_gen.palette(v); popup=_rgb(p['popup'],(0.05,0.07,0.1))
 for fg,bg in [('text','window'),('muted','window'),('text','card'),('muted','card'),('text','selected'),
               ('on_accent','accent_fill'),('accent_fg','window'),('accent_fg','popup'),('muted','popup'),('panel_text','panel')]:
  bgc=popup if bg=='popup' else _rgb(p[bg],(0.05,0.07,0.1))
  r=_ratio(_rgb(p[fg]),bgc); contrast_checks+=1
  assert_ok(r>=4.5,f'contrast {v}: {fg} on {bg} = {r:.2f} (< 4.5)')
print('Validated icons:',count,'wallpapers:',3,'themes:',2,'optional applets:',len(list((R/'applets').iterdir())),'desklets:',len(list((R/'desklets').iterdir())),'contrast pairs:',contrast_checks)
if errors:
 print('\n'.join(errors[:100]));raise SystemExit(1)
print('Static validation passed. Cinnamon runtime compatibility must still be tested.')
