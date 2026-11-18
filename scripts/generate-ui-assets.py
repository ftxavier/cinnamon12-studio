#!/usr/bin/env python3
"""Export optional decorative UI SVG/PNG templates; the real controls are native Cinnamon CSS."""
from pathlib import Path
import cairosvg
R=Path(__file__).resolve().parents[1]
O=R/'assets'/'ui';O.mkdir(exist_ok=True)
COMMON='''<defs>
 <linearGradient id="blue" x2="1" y2="1"><stop stop-color="#60ddff"/><stop offset="1" stop-color="#0579e2"/></linearGradient>
 <linearGradient id="purple" x2="1" y2="1"><stop stop-color="#a3a4ff"/><stop offset="1" stop-color="#6255db"/></linearGradient>
 <linearGradient id="glass" x2="0" y2="1"><stop stop-color="#f9fdff" stop-opacity=".97"/><stop offset="1" stop-color="#c8e4ff" stop-opacity=".95"/></linearGradient>
 <linearGradient id="night" x2="0" y2="1"><stop stop-color="#213d67"/><stop offset="1" stop-color="#071c38"/></linearGradient>
 </defs>'''
def svg(w,h,body):return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">{COMMON}{body}</svg>'
items={
 'brand-mark':(128,128,'''
   <rect x="5" y="5" width="118" height="118" rx="22" fill="url(#blue)"/>
   <g fill="#f6fcff"><rect x="23" y="23" width="35" height="35" rx="6"/><rect x="70" y="23" width="35" height="35" rx="6"/><rect x="23" y="70" width="35" height="35" rx="6"/><rect x="70" y="70" width="35" height="35" rx="6"/></g>
  '''),
 'brand-mark-outline':(128,128,'''
   <rect x="5" y="5" width="118" height="118" rx="22" fill="#102f57" stroke="#7bcbff" stroke-width="2"/>
   <g fill="none" stroke="#e6faff" stroke-width="5"><rect x="23" y="23" width="35" height="35" rx="5"/><rect x="70" y="23" width="35" height="35" rx="5"/><rect x="23" y="70" width="35" height="35" rx="5"/><rect x="70" y="70" width="35" height="35" rx="5"/></g>'''),
 'panel-light':(900,75,'''
   <rect x="6" y="9" width="888" height="58" rx="8" fill="#0e2e55" stroke="#8ac9ff" stroke-opacity=".50" stroke-width="1.5"/>
   <rect x="340" y="19" width="39" height="39" rx="6" fill="url(#blue)"/>
   <g fill="#fff"><rect x="350" y="29" width="8" height="8" rx="1"/><rect x="361" y="29" width="8" height="8" rx="1"/><rect x="350" y="40" width="8" height="8" rx="1"/><rect x="361" y="40" width="8" height="8" rx="1"/></g>
   <rect x="390" y="20" width="37" height="37" rx="6" fill="#315c8c"/>
   <path d="M399 39h20l4 9h-28z" fill="#7fd7ff"/>
   <rect x="436" y="20" width="37" height="37" rx="6" fill="#315c8c"/>
   <path d="m446 29 9 9-9 9" fill="none" stroke="#fff" stroke-width="3"/>
   <g fill="#aad5ff"><circle cx="822" cy="39" r="4"/><circle cx="839" cy="39" r="4"/><circle cx="856" cy="39" r="4"/></g>
  '''),
 'control-tile-on':(250,105,'''
   <rect x="3" y="3" width="244" height="99" rx="7" fill="url(#blue)"/>
   <rect x="20" y="23" width="50" height="50" rx="7" fill="#fff" opacity=".17"/>
   <g transform="translate(26 30)" fill="none" stroke="#fff" stroke-linecap="round" stroke-width="5"><path d="M2 17Q20 1 38 17M9 26q11-9 22 0"/><circle cx="20" cy="35" r="3" fill="#fff"/></g>
  '''),
 'control-tile-off':(250,105,'''
   <rect x="3" y="3" width="244" height="99" rx="7" fill="#dae7f5" stroke="#a3c7e7"/>
   <rect x="20" y="23" width="50" height="50" rx="7" fill="#fff"/>
   <g transform="translate(28 31)" stroke="#6b88ac" stroke-width="4" fill="none"><circle cx="18" cy="17" r="15"/><path d="M6 6 30 30"/></g>'''),
 'widget-weather-shell':(380,180,'''
   <rect x="3" y="3" width="374" height="174" rx="7" fill="url(#night)" stroke="#72b9fc" stroke-opacity=".6"/>
   <circle cx="84" cy="71" r="27" fill="#ffc45b"/>
   <path d="M66 111q-16-27 8-37 11-7 23-1 12-23 38-16 22 5 27 28 25-3 32 18 5 18-14 29H76z" fill="url(#glass)"/>
   <path d="M229 64h115M229 93h90M229 122h105" stroke="#c2e3ff" stroke-width="5" stroke-linecap="round" stroke-opacity=".7"/>
  '''),
 'widget-performance-shell':(380,180,'''
   <rect x="3" y="3" width="374" height="174" rx="7" fill="url(#night)" stroke="#72b9fc" stroke-opacity=".6"/>
   <path d="M21 83h48l16-22 21 37 25-26 22 18 17-37 23 32 28-10 20-28 27 34 28-12 26 14" fill="none" stroke="#25caff" stroke-width="5" stroke-linecap="round"/>
   <rect x="23" y="130" width="334" height="9" rx="4" fill="#4d6d92"/>
   <rect x="23" y="130" width="151" height="9" rx="4" fill="#31c7fb"/>
   <rect x="23" y="149" width="334" height="9" rx="4" fill="#4d6d92"/>
   <rect x="23" y="149" width="230" height="9" rx="4" fill="#9c91f5"/>
  '''),
 'widget-calendar-shell':(380,275,'''
   <rect x="3" y="3" width="374" height="269" rx="7" fill="url(#night)" stroke="#72b9fc" stroke-opacity=".6"/>
   <path d="M22 62h336" stroke="#b4ddff" opacity=".3"/>
   <g fill="#96c8f3">'''+''.join(f'<rect x="{33+col*46}" y="{83+row*35}" width="29" height="25" rx="4" opacity="{.50 if (row+col)%3 else .72}"/>' for row in range(4) for col in range(7))+'''</g>
   <rect x="125" y="153" width="29" height="25" rx="4" fill="url(#blue)"/>
  '''),
 'login-avatar-placeholder':(144,144,'''
   <circle cx="72" cy="72" r="69" fill="url(#blue)"/>
   <circle cx="72" cy="53" r="25" fill="#e8f7ff"/>
   <path d="M19 126c5-35 24-49 53-49s48 14 53 49" fill="#e8f7ff"/>
  '''),
 'search-field':(610,68,'''
   <rect x="3" y="3" width="604" height="62" rx="7" fill="#f4faff" stroke="#a0c9eb"/>
   <circle cx="42" cy="34" r="13" fill="none" stroke="#548cc4" stroke-width="4"/>
   <path d="m52 44 10 10" stroke="#548cc4" stroke-width="4" stroke-linecap="round"/>
   <path d="M88 34h225" stroke="#9fb9d6" stroke-width="7" stroke-linecap="round" opacity=".30"/>
  '''),
 'menu-card-surface':(580,500,'''
   <rect x="5" y="5" width="570" height="490" rx="9" fill="url(#glass)" stroke="#98bfe8"/>
   <rect x="23" y="22" width="534" height="53" rx="7" fill="#fff" opacity=".67"/>
   <rect x="23" y="93" width="150" height="380" rx="6" fill="#d9eaff"/>
   <g fill="#7bbaff" opacity=".8">'''+''.join(f'<rect x="38" y="{116+i*48}" width="119" height="29" rx="5"/>' for i in range(7))+'''</g>
   <g fill="url(#blue)">'''+''.join(f'<rect x="{210+col*104}" y="{123+row*112}" width="66" height="66" rx="10"/>' for row in range(3) for col in range(3))+'''</g>
  '''),
}
for n,(w,h,b) in items.items():
 x=svg(w,h,b)
 (O/f'{n}.svg').write_text(x,encoding='utf8')
 for scale in [1,2]:
  cairosvg.svg2png(bytestring=x.encode(),write_to=str(O/f'{n}@{scale}x.png'),output_width=w*scale,output_height=h*scale)
print('Created',len(items),'original UI element SVGs, with 1x/2x PNG')
