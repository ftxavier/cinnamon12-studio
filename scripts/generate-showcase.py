#!/usr/bin/env python3
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps,ImageFilter
R=Path(__file__).resolve().parents[1];P=R/'assets'/'previews'
W,H=1550,1080
bg=Image.new('RGB',(W,H),'#091c38'); d=ImageDraw.Draw(bg)
font='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
def f(s,bold=False):
 p='/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else font
 return ImageFont.truetype(p,s)
d.text((47,28),'CINNAMON12',font=f(49,True),fill='#e9faff')
d.text((48,90),'STUDIO  |  Ubuntu 24.04  ·  Cinnamon 6.0.4',font=f(21),fill='#95c6ed')
colors=['arctic','aurora','midnight']
for i,name in enumerate(colors):
 x=48+i*501; y=156
 im=Image.open(R/'assets'/'wallpapers'/f'c12-{name}-1920x1080.jpg')
 im=ImageOps.fit(im,(464,262));bg.paste(im,(x,y));d.rectangle((x,y,x+464,y+262),outline='#83bbe3',width=2)
 d.text((x+9,y+269),name.upper(),font=f(19,True),fill='#d3ebff')
# icon lineup
positions=[('apps','cinnamon12-start'),('apps','system-file-manager'),('apps','utilities-terminal'),('apps','preferences-system'),('apps','accessories-calculator'),('apps','multimedia-video-player'),('places','folder-music'),('places','folder-pictures'),('places','folder-videos'),('apps','utilities-system-monitor'),('apps','system-software-update'),('apps','preferences-desktop-wallpaper'),('places','folder-publicshare'),('places','folder-code'),('places','folder-download'),('apps','multimedia-audio-player'),('apps','system-lock-screen'),('apps','help-browser')]
d.text((48,470),'ICONES DO SISTEMA',font=f(24,True),fill='#e9faff')
for i,(c,n) in enumerate(positions):
 x=50+(i%9)*167;y=515+(i//9)*126
 d.rounded_rectangle((x,y,x+150,y+114),radius=7,fill='#173960',outline='#2b5e8c')
 ico=Image.open(R/'icons'/'Cinnamon12-Icons'/'128x128'/c/(n+'.png')).convert('RGBA').resize((81,81),Image.Resampling.LANCZOS)
 bg.paste(ico,(x+34,y+8),ico)
 d.text((x+10,y+91),n.replace('folder-','')[:18],font=f(11),fill='#b5d9f5')
d.text((48,804),'COMPONENTES DE INTERFACE',font=f(24,True),fill='#e9faff')
ui=['panel-light','control-tile-on','control-tile-off','widget-weather-shell','widget-performance-shell']
coords=[(47,859,500,43),(555,859,220,88),(787,859,220,88),(1019,827,220,105),(1251,827,220,105)]
for name,(x,y,w,h) in zip(ui,coords):
 img=Image.open(R/'assets'/'ui'/f'{name}@1x.png').convert('RGBA')
 img.thumbnail((w,h),Image.Resampling.LANCZOS)
 bg.paste(img,(x,y),img)
d.line((48,1000,1502,1000),fill='#2a5e91',width=1)
d.text((48,1017),'202 ICONES SVG  +  PNG  |  3 WALLPAPERS  |  LIGHT / DARK  |  THEME + ASSETS + DEB',font=f(19),fill='#8ecfff')
bg.save(P/'vitrine-cinnamon12.jpg',quality=93,subsampling=0,optimize=True)
print(P/'vitrine-cinnamon12.jpg')
