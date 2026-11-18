#!/usr/bin/env python3
"""Prepare image-generated original wallpaper series for common displays."""
from pathlib import Path
from PIL import Image,ImageOps,ImageFilter,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets'/'wallpapers'
# Masters live in the repo (assets/wallpapers/<name>-original.png). To replace a design,
# overwrite its master (or pass NAME=PATH arguments) and run this script again.
import sys
IMAGES={n:OUT/f'{n}-original.png' for n in ('c12-arctic','c12-aurora','c12-midnight')}
for arg in sys.argv[1:]:
 n,_,path=arg.partition('=')
 if n in IMAGES and path:IMAGES[n]=Path(path)
for name,p in IMAGES.items():
 if not p.exists():continue
 im=Image.open(p).convert('RGB')
 if p.resolve()!=(OUT/f'{name}-original.png').resolve():(OUT/f'{name}-original.png').write_bytes(p.read_bytes())
 for W,H in [(1920,1080),(2560,1440),(3840,2160)]:
  a=ImageOps.fit(im,(W,H),method=Image.Resampling.LANCZOS,centering=(.5,.5))
  if W>2000:a=a.filter(ImageFilter.UnsharpMask(radius=1.1,percent=85,threshold=3))
  a.save(OUT/f'{name}-{W}x{H}.jpg',quality=92,subsampling=0,optimize=True)
  print(name,W,H)
# wallpaper contact preview
small=[]
for name in IMAGES:
 img=Image.open(OUT/f'{name}-1920x1080.jpg');small.append(img.resize((832,468),Image.Resampling.LANCZOS))
prev=Image.new('RGB',(1760,1135),'#0f213a');d=ImageDraw.Draw(prev)
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
ft=ImageFont.truetype(font,24) if Path(font).exists() else ImageFont.load_default()
d.text((35,22),'CINNAMON 12  /  WALLPAPERS ORIGINAIS',font=ft,fill='#e6f4ff')
for i,img in enumerate(small):
 x=33+(i%2)*866;y=83+(i//2)*515
 prev.paste(img,(x,y));d.text((x,y+476),list(IMAGES)[i].upper(),font=ft,fill='#cfe8ff')
prev.save(ROOT/'assets'/'previews'/'catalogo-wallpapers.jpg',quality=90)
