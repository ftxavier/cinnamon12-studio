#!/usr/bin/env python3
"""Create original Cinnamon12 vector icons and freedesktop icon-themes.
Runtime on development host: Python3, CairoSVG, Pillow. Prebuilt assets ship in ZIP/DEB.
All vector paths here are original minimalist geometric drawings, not rebranded third-party marks.
"""
import json, os, shutil, io
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import cairosvg

ROOT=Path(__file__).resolve().parents[1]
ICONS=ROOT/'icons'/'Cinnamon12-Icons'
DEST=ROOT/'assets'/'previews'
COLORS={
 'blue':('#64DDFF','#0085EF'), 'indigo':('#8198FF','#3B51CD'),
 'purple':('#B59BFF','#7250DF'), 'teal':('#67E5DB','#0AA6B3'),
 'green':('#75E6A6','#1DAD77'), 'orange':('#FFC975','#F38945'),
 'pink':('#FF9EC7','#E65B9C'), 'grey':('#BED2E9','#6689AD'),
 'navy':('#5CA6F4','#204E9C'), 'red':('#FF8D9A','#D54B70')}

# Icon symbols use 64x64 viewBox. Simple outlined universal shapes, designed for this pack.
PATHS={
 'grid':'<rect x="10" y="10" width="18" height="18" rx="3"/><rect x="36" y="10" width="18" height="18" rx="3"/><rect x="10" y="36" width="18" height="18" rx="3"/><rect x="36" y="36" width="18" height="18" rx="3"/>',
 'home':'<path d="M7 30 32 9 57 30 M14 28v25h36V28 M26 53V38h12v15"/>',
 'monitor':'<rect x="7" y="11" width="50" height="37" rx="4"/><path d="M26 48v7m12-7v7M19 55h26"/>',
 'document':'<path d="M17 7h22l11 12v38H17z M39 7v13h11 M24 32h18 M24 40h18 M24 48h12"/>',
 'download':'<path d="M32 7v34m-13-12 13 13 13-13 M11 47v10h42V47"/>',
 'music':'<path d="M23 46V16l28-7v30 M23 20l28-7 M23 46c0 9-18 12-18 3 0-8 18-11 18-3z M51 39c0 9-18 12-18 3 0-8 18-11 18-3z"/>',
 'picture':'<rect x="7" y="10" width="50" height="44" rx="5"/><circle cx="22" cy="24" r="5"/><path d="m11 49 15-15 10 9 9-12 8 11"/>',
 'video':'<rect x="7" y="11" width="50" height="42" rx="6"/><path d="m27 23 16 9-16 9z"/>',
 'person':'<circle cx="32" cy="21" r="11"/><path d="M11 56c2-17 13-23 21-23s19 6 21 23"/>',
 'people':'<circle cx="24" cy="22" r="8"/><circle cx="45" cy="25" r="7"/><path d="M5 52c1-14 9-20 19-20 12 0 20 7 20 20 M41 35c8 1 15 6 17 17"/>',
 'code':'<path d="m22 16-15 16 15 16 M42 16l15 16-15 16 M38 9 26 55"/>',
 'terminal':'<rect x="6" y="9" width="52" height="46" rx="5"/><path d="m15 23 11 9-11 9 M33 42h14"/>',
 'gear':'<path d="M25 7h14l2 8 7 4 8-3 7 13-7 5v8l7 5-7 12-8-3-7 4-2 8H25l-2-8-7-4-8 3-7-12 7-5v-8l-7-5 7-13 8 3 7-4z" transform="translate(4 1) scale(.88)"/><circle cx="32" cy="33" r="10"/>',
 'search':'<circle cx="26" cy="26" r="18"/><path d="m40 40 18 18"/>',
 'calculator':'<rect x="11" y="5" width="42" height="54" rx="5"/><rect x="17" y="12" width="30" height="13" rx="2"/><path d="M20 33h5m9 0h5m-19 8h5m9 0h5m-19 9h5m9 0h5"/>',
 'folder':'<path d="M6 18v-5c0-3 2-5 5-5h16l8 8h18c3 0 5 2 5 5v4H6z M6 25h52v27c0 3-2 5-5 5H11c-3 0-5-2-5-5z"/>',
 'calendar':'<rect x="8" y="13" width="48" height="43" rx="5"/><path d="M8 26h48 M21 7v13 M43 7v13 M20 36h6m10 0h6m-22 10h6m10 0h6"/>',
 'clock':'<circle cx="32" cy="32" r="25"/><path d="M32 17v16l12 8"/>',
 'mail':'<rect x="6" y="14" width="52" height="37" rx="5"/><path d="m7 18 25 20 25-20"/>',
 'wifi':'<path d="M5 24q27-25 54 0 M13 33q19-17 38 0 M22 42q10-9 20 0"/><circle cx="32" cy="51" r="3" fill="currentColor" stroke="none"/>',
 'bluetooth':'<path d="M32 5v54l17-15-34-25m0 26L49 20 32 5"/>',
 'volume':'<path d="M7 24h11l13-11v38L18 40H7z M40 24q10 8 0 16 M47 17q18 15 0 30"/>',
 'mic':'<rect x="24" y="7" width="16" height="34" rx="8"/><path d="M16 30c0 22 32 22 32 0 M32 47v10m-13 0h26"/>',
 'camera':'<path d="M6 18h12l5-7h18l5 7h12v35H6z"/><circle cx="32" cy="35" r="12"/>',
 'trash':'<path d="M12 17h40 M23 17V9h18v8 M16 20l3 36h26l3-36 M26 27v20m12-20v20"/>',
 'star':'<path d="m32 6 8 17 18 3-13 13 3 19-16-9-16 9 3-19L6 26l18-3z"/>',
 'lock':'<rect x="12" y="27" width="40" height="31" rx="5"/><path d="M20 27v-8a12 12 0 0 1 24 0v8 M32 40v8"/>',
 'shield':'<path d="M32 5 55 14v19c0 13-9 22-23 27C18 55 9 46 9 33V14z M22 32l8 8 15-17"/>',
 'power':'<path d="M32 5v28 M17 14a23 23 0 1 0 30 0"/>',
 'battery':'<rect x="5" y="18" width="49" height="29" rx="5"/><path d="M56 27h3v11h-3 M11 24h30v17H11z"/>',
 'sun':'<circle cx="32" cy="32" r="11"/><path d="M32 4v9M32 51v9M4 32h9m38 0h9M12 12l7 7m26 26 7 7m0-40-7 7M19 45l-7 7"/>',
 'moon':'<path d="M48 47a25 25 0 0 1-31-31A25 25 0 1 0 48 47z"/>',
 'airplane':'<path d="M8 27h21L26 8q1-6 6-6t6 6l-3 19h21l5 9-26 5-3 18-8-1 1-17-24-5z"/>',
 'bell':'<path d="M14 44h36l-6-9V22c0-18-24-18-24 0v13z M26 51c1 9 11 9 12 0"/>',
 'refresh':'<path d="M52 23A22 22 0 0 0 13 20L7 28 M7 11v17h17 M12 41a22 22 0 0 0 39 3l6-8 M57 53V36H40"/>',
 'check':'<path d="M8 33 25 50 56 15"/>',
 'close':'<path d="M12 12 52 52 M52 12 12 52"/>',
 'plus':'<path d="M32 7v50 M7 32h50"/>',
 'minus':'<path d="M7 32h50"/>',
 'arrow-left':'<path d="m31 10-22 22 22 22 M10 32h46"/>',
 'arrow-right':'<path d="m33 10 22 22-22 22 M54 32H8"/>',
 'arrow-down':'<path d="m10 29 22 22 22-22 M32 50V8"/>',
 'arrow-up':'<path d="m10 35 22-22 22 22 M32 14v42"/>',
 'menu':'<path d="M8 16h48M8 32h48M8 48h48"/>',
 'list':'<path d="M22 14h36M22 32h36M22 50h36"/><circle cx="10" cy="14" r="3"/><circle cx="10" cy="32" r="3"/><circle cx="10" cy="50" r="3"/>',
 'settings-sliders':'<path d="M6 16h52M6 32h52M6 48h52"/><circle cx="22" cy="16" r="6" fill="currentColor"/><circle cx="43" cy="32" r="6" fill="currentColor"/><circle cx="25" cy="48" r="6" fill="currentColor"/>',
 'edit':'<path d="m11 43 32-32 11 11-32 32-14 3z M37 17l11 11"/>',
 'copy':'<rect x="18" y="18" width="38" height="39" rx="4"/><path d="M43 18V8H8v39h10"/>',
 'save':'<path d="M9 7h39l8 9v41H9z M19 7v16h26V7 M18 57V36h28v21"/>',
 'open':'<path d="M7 25V10h20l8 9h22v35H7z M7 26h50l-8 28H7"/>',
 'share':'<circle cx="11" cy="32" r="7"/><circle cx="51" cy="12" r="7"/><circle cx="51" cy="52" r="7"/><path d="m17 28 27-13 M17 36l27 13"/>',
 'printer':'<path d="M16 8h32v16H16z M11 27h42a5 5 0 0 1 5 5v17H6V32a5 5 0 0 1 5-5z M17 42h30v17H17z"/>',
 'archive':'<rect x="12" y="9" width="40" height="49" rx="4"/><path d="M12 22h40M26 9v30m6-26v7m-6 10h9v9h-9"/>',
 'disk':'<rect x="9" y="10" width="46" height="45" rx="6"/><circle cx="32" cy="30" r="13"/><circle cx="32" cy="30" r="3"/><path d="M15 48h11"/>',
 'cloud':'<path d="M18 49h31a13 13 0 0 0 1-26c-6-19-31-19-37 0A13 13 0 0 0 18 49z"/>',
 'link':'<path d="M24 41 16 49a12 12 0 0 1-17-17l12-12a12 12 0 0 1 17 0 M40 23l8-8a12 12 0 0 1 17 17L53 44a12 12 0 0 1-17 0 M22 42 43 21" transform="translate(3 0) scale(.9 1)"/>',
 'chart':'<path d="M9 8v48h50 M19 44V30m12 14V18m12 26V26m12 18V12"/>',
 'tune':'<path d="M9 16h46m-46 16h46m-46 16h46"/><circle cx="25" cy="16" r="6"/><circle cx="44" cy="32" r="6"/><circle cx="28" cy="48" r="6"/>',
 'globe':'<circle cx="32" cy="32" r="25"/><path d="M7 32h50M32 7v50 M15 16c17 12 17 20 0 32M49 16c-17 12-17 20 0 32"/>',
 'book':'<path d="M32 12q-11-8-25-3v43q14-5 25 3 11-8 25-3V9q-14-5-25 3z M32 12v43"/>',
 'play':'<path d="m19 9 37 23-37 23z"/>',
 'pause':'<path d="M16 10v44m30-44v44"/>',
 'stop':'<rect x="14" y="14" width="36" height="36" rx="4"/>',
 'info':'<circle cx="32" cy="32" r="25"/><path d="M32 28v20 M32 16v3"/>',
 'warning':'<path d="M32 7 60 55H4z M32 23v15 M32 45v2"/>',
 'heart':'<path d="M32 56 9 33C-1 15 21 1 32 17 43 1 65 15 55 33z"/>',
 'wifi-off':'<path d="M5 24q27-25 54 0 M13 33q19-17 38 0 M22 42q10-9 20 0 M6 6l52 52"/>',
 'volume-off':'<path d="M7 24h11l13-11v38L18 40H7z M42 22l16 21m0-21L42 43"/>',
 'fullscreen':'<path d="M25 8H8v17 M39 8h17v17 M8 39v17h17 M56 39v17H39"/>',
 'logout':'<path d="M34 7H12v50h22 M28 32h30m-13-13 13 13-13 13"/>',
 'key':'<circle cx="20" cy="22" r="13"/><path d="m29 31 25 25 M40 42l7-7m0 14 7-7"/>',
 'lightning':'<path d="M35 3 11 36h20l-3 25 25-35H33z"/>',
 'ethernet':'<rect x="15" y="5" width="34" height="28" rx="3"/><path d="M21 17h22M32 33v9M10 42h44v14H10z M19 42v6m9-6v6m9-6v6m9-6v6"/>',
 'clipboard':'<rect x="12" y="12" width="40" height="47" rx="5"/><path d="M24 12V7h16v5 M21 28h21M21 38h21M21 48h14"/>',
 'eye':'<path d="M4 32q28-35 56 0-28 35-56 0z"/><circle cx="32" cy="32" r="10"/>',
 'keyboard':'<rect x="5" y="16" width="54" height="34" rx="4"/><path d="M12 24h4m7 0h4m7 0h4m7 0h4M12 33h4m7 0h4m7 0h4m7 0h4M17 42h30"/>',
 'workspace':'<rect x="8" y="9" width="48" height="46" rx="5"/><path d="M32 9v46 M8 32h48"/>',
 'user-switch':'<circle cx="20" cy="19" r="9"/><path d="M4 48c1-14 8-19 16-19 9 0 16 5 17 19 M43 20h17m-6-6 6 6-6 6M43 43h17m-6-6 6 6-6 6"/>',
}

# Each row: freedesktop icon name, glyph, unique color family.
APP_ICONS={
 'cinnamon12-start':('grid','blue'), 'cinnamon12-control-center':('settings-sliders','navy'),
 'system-file-manager':('folder','blue'), 'nemo':('folder','blue'),
 'utilities-terminal':('terminal','navy'), 'org.gnome.Terminal':('terminal','navy'),
 'preferences-system':('gear','indigo'), 'cinnamon-settings':('gear','indigo'),
 'preferences-desktop':('monitor','blue'), 'preferences-desktop-wallpaper':('picture','blue'),
 'preferences-desktop-theme':('tune','indigo'), 'preferences-system-network':('wifi','teal'),
 'preferences-system-bluetooth':('bluetooth','blue'), 'preferences-system-sound':('volume','indigo'),
 'preferences-system-power':('power','green'), 'preferences-system-privacy':('shield','teal'),
 'accessories-calculator':('calculator','indigo'), 'org.gnome.Calculator':('calculator','indigo'),
 'accessories-text-editor':('document','teal'), 'text-editor':('document','teal'),
 'internet-web-browser':('globe','blue'), 'web-browser':('globe','blue'),
 'system-software-install':('download','blue'), 'software-center':('download','blue'),
 'system-software-update':('refresh','teal'), 'software-update-available':('refresh','teal'),
 'utilities-system-monitor':('chart','green'), 'gnome-system-monitor':('chart','green'),
 'org.gnome.Calendar':('calendar','purple'), 'x-office-calendar':('calendar','purple'),
 'multimedia-video-player':('video','purple'), 'video-player':('video','purple'),
 'multimedia-audio-player':('music','pink'), 'audio-player':('music','pink'),
 'multimedia-volume-control':('volume','blue'), 'org.gnome.Eog':('picture','purple'),
 'image-viewer':('picture','purple'), 'org.gnome.FileRoller':('archive','orange'),
 'file-roller':('archive','orange'), 'help-browser':('book','green'),
 'utilities-system-info':('info','blue'), 'system-log-out':('logout','orange'),
 'system-lock-screen':('lock','indigo'), 'system-shutdown':('power','red'),
 'camera-photo':('camera','pink'), 'document-print':('printer','blue'),
 'org.gnome.Screenshot':('camera','blue'), 'utilities-disk-utility':('disk','grey'),
 'seahorse':('key','purple'), 'gnome-disks':('disk','grey'),
 'preferences-desktop-keyboard':('keyboard','indigo'),
 'network-workgroup':('people','teal'), 'application-x-executable':('code','navy'),
}
PLACE_ICONS={
 'folder':('folder','blue'),'folder-home':('home','blue'),
 'user-home':('home','blue'),'user-desktop':('monitor','teal'),
 'folder-documents':('document','blue'),'folder-download':('download','blue'),
 'folder-music':('music','purple'),'folder-pictures':('picture','blue'),
 'folder-videos':('video','indigo'),'folder-publicshare':('people','teal'),
 'folder-templates':('document','purple'),'folder-favorites':('star','orange'),
 'folder-recent':('clock','grey'),'folder-network':('globe','teal'),
 'folder-cloud':('cloud','blue'), 'folder-remote':('link','blue'),
 'folder-sync':('refresh','teal'),'folder-code':('code','indigo'),
 'folder-projects':('grid','purple'),'folder-backup':('shield','green'),
 'folder-open':('open','blue'),'user-trash':('trash','grey'),
 'user-trash-full':('trash','red'), 'computer':('monitor','blue'),
 'network-server':('disk','teal'), 'start-here':('grid','blue')}
DEVICE_ICONS={
 'computer':('monitor','blue'), 'computer-laptop':('monitor','blue'),
 'drive-harddisk':('disk','grey'),'drive-removable-media':('disk','teal'),
 'media-flash':('disk','teal'), 'media-optical':('disk','purple'),
 'printer':('printer','blue'), 'audio-card':('volume','indigo'),
 'input-keyboard':('keyboard','navy'), 'camera-web':('camera','purple'),
 'network-wired':('ethernet','teal'), 'network-wireless':('wifi','teal'),
 'battery':('battery','green'),
}
MIME_ICONS={
 'text-x-generic':('document','blue'), 'text-plain':('document','blue'),
 'text-x-script':('code','indigo'),'text-html':('code','orange'),
 'application-json':('code','teal'),'application-pdf':('document','red'),
 'application-zip':('archive','orange'), 'package-x-generic':('archive','grey'),
 'image-x-generic':('picture','purple'), 'video-x-generic':('video','purple'),
 'audio-x-generic':('music','pink'), 'application-x-executable':('code','navy'),
 'x-office-document':('document','blue'), 'x-office-spreadsheet':('chart','green'),
 'x-office-presentation':('monitor','orange')}
ACTIONS={
 'edit-find':'search','edit-copy':'copy','edit-paste':'clipboard',
 'document-open':'open','document-save':'save','document-print':'printer',
 'document-new':'plus','document-properties':'info','document-revert':'refresh',
 'view-refresh':'refresh','view-fullscreen':'fullscreen','view-list':'list',
 'view-grid':'grid','view-details':'list','view-preview':'eye',
 'list-add':'plus','list-remove':'minus','go-home':'home',
 'go-next':'arrow-right','go-previous':'arrow-left','go-up':'arrow-up',
 'go-down':'arrow-down','go-back':'arrow-left','go-forward':'arrow-right',
 'window-close':'close','dialog-close':'close','dialog-ok':'check',
 'dialog-cancel':'close','edit-delete':'trash','folder-new':'folder',
 'system-search':'search','system-run':'play','system-lock-screen':'lock',
 'system-shutdown':'power','system-reboot':'refresh','application-exit':'logout',
 'media-playback-start':'play','media-playback-stop':'stop','media-playback-pause':'pause',
 'mail-send':'mail','emblem-favorite':'star','emblem-default':'check',
 'emblem-important':'warning','emblem-symbolic-link':'link',
 'help-about':'info','help-contents':'book','configure':'gear',
 'insert-link':'link','mark-location':'star','share':'share',
 'network-connect':'ethernet','network-disconnect':'wifi-off',
}
STATUS={
 'network-wireless-signal-excellent-symbolic':'wifi',
 'network-wireless-signal-good-symbolic':'wifi',
 'network-wireless-signal-ok-symbolic':'wifi',
 'network-wireless-signal-weak-symbolic':'wifi',
 'network-wireless-signal-none-symbolic':'wifi-off',
 'network-wireless-offline-symbolic':'wifi-off',
 'network-wired-symbolic':'ethernet',
 'bluetooth-active-symbolic':'bluetooth','bluetooth-disabled-symbolic':'bluetooth',
 'audio-volume-high-symbolic':'volume','audio-volume-medium-symbolic':'volume',
 'audio-volume-low-symbolic':'volume','audio-volume-muted-symbolic':'volume-off',
 'microphone-sensitivity-high-symbolic':'mic','microphone-sensitivity-muted-symbolic':'mic',
 'battery-full-symbolic':'battery','battery-good-symbolic':'battery',
 'battery-medium-symbolic':'battery','battery-low-symbolic':'battery',
 'battery-caution-symbolic':'battery','battery-empty-symbolic':'battery',
 'battery-full-charging-symbolic':'lightning',
 'display-brightness-symbolic':'sun', 'weather-clear-symbolic':'sun',
 'weather-clear-night-symbolic':'moon', 'weather-few-clouds-symbolic':'cloud',
 'airplane-mode-symbolic':'airplane', 'notifications-symbolic':'bell',
 'notifications-disabled-symbolic':'bell',
 'system-search-symbolic':'search', 'system-lock-screen-symbolic':'lock',
 'system-shutdown-symbolic':'power','system-reboot-symbolic':'refresh',
 'system-log-out-symbolic':'logout', 'security-high-symbolic':'shield',
 'emblem-ok-symbolic':'check','dialog-warning-symbolic':'warning',
 'dialog-information-symbolic':'info',
 'cinnamon12-menu-symbolic':'grid','cinnamon12-toggles-symbolic':'settings-sliders',
 'cinnamon12-night-light-symbolic':'moon', 'cinnamon12-performance-symbolic':'chart',
 'cinnamon12-calendar-symbolic':'calendar',
}

SIZES=[16,24,32,48,64,128]

def icon_svg(name, glyph, pal, tile=True, folder=False):
 c1,c2=COLORS[pal]
 defs=f'''<defs>
 <linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient>
 <linearGradient id="shine" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".26"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>
 <filter id="shadow" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="2"/></filter>
 </defs>'''
 if folder:
  # Physical folder geometry with a bevel, subtle holographic gradient, and an embedded emblem.
  return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96">{defs}
  <path d="M10 27V20q0-5 5-5h24l10 9h29q7 0 7 7v7H10Z" fill="{c2}" stroke="#13487D" stroke-opacity=".18" stroke-width="2"/>
  <path d="M10 31h75v45q0 7-7 7H17q-7 0-7-7z" fill="url(#g)"/>
  <path d="M10 33h75v8H10z" fill="#fff" opacity=".24"/>
  <path d="M11 60q30-17 73-4v17q0 8-7 8H17q-6 0-6-7z" fill="{c2}" opacity=".23"/>
  <path d="M10 34h75v40q0 8-8 8H18q-8 0-8-8z" fill="none" stroke="#fff" stroke-opacity=".28" stroke-width="1.4"/>
  <g transform="translate(47 54) scale(.32) translate(-32 -32)" fill="none" stroke="#fff" stroke-opacity=".90" stroke-width="5.7" stroke-linecap="round" stroke-linejoin="round">{PATHS[glyph]}</g>
  </svg>'''
 if tile:
  return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96">{defs}
   <rect x="8" y="10" width="80" height="80" rx="17" fill="#071d3b" opacity=".13"/>
   <rect x="7" y="6" width="82" height="82" rx="16" fill="url(#g)"/>
   <rect x="8" y="7" width="80" height="47" rx="15" fill="url(#shine)"/>
   <path d="M12 75Q49 87 83 66" stroke="#fff" stroke-opacity=".21" fill="none" stroke-width="2"/>
   <g transform="translate(48 47) scale(.86) translate(-32 -32)" stroke="white" stroke-width="4.3" fill="none" stroke-linecap="round" stroke-linejoin="round">{PATHS[glyph]}</g></svg>'''
 return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 96 96">{defs}<g transform="translate(16 16)" stroke="{c2}" stroke-width="5" fill="none" stroke-linecap="round" stroke-linejoin="round">{PATHS[glyph]}</g></svg>'''

def glyph_svg(glyph):
 return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" width="64" height="64"><g fill="none" stroke="#bebebe" stroke-width="4.4" stroke-linecap="round" stroke-linejoin="round">{PATHS[glyph]}</g></svg>'''

def save_icon(category,name,glyph,pal='blue',folder=False,symbolic=False):
 data = glyph_svg(glyph) if symbolic else icon_svg(name,glyph,pal,folder=folder)
 p=ICONS/'scalable'/category/f'{name}.svg'
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(data,encoding='utf8')
 # PNGs are generated for high compatibility; scalable originals remain editable.
 for size in ([16,24,32,48,64,128] if not symbolic else [16,24,32,48]):
  out=ICONS/f'{size}x{size}'/category/f'{name}.png'
  out.parent.mkdir(parents=True,exist_ok=True)
  png=cairosvg.svg2png(bytestring=data.encode(),output_width=size,output_height=size)
  out.write_bytes(png)

for name,(glyph,color) in APP_ICONS.items():save_icon('apps',name,glyph,color)
for name,(glyph,color) in PLACE_ICONS.items():save_icon('places',name,glyph,color,folder=name.startswith('folder') and name not in ('folder-home',))
for name,(glyph,color) in DEVICE_ICONS.items():save_icon('devices',name,glyph,color)
for name,(glyph,color) in MIME_ICONS.items():save_icon('mimetypes',name,glyph,color)
for name,glyph in ACTIONS.items():save_icon('actions',name,glyph,symbolic=False)
for name,glyph in STATUS.items():save_icon('status',name,glyph,symbolic=True)

sections=[]
for s in SIZES:
 for c in ('apps','places','devices','mimetypes','actions','status'):
  sections.append(f'{s}x{s}/{c}')
for c in ('apps','places','devices','mimetypes','actions','status'):sections.append(f'scalable/{c}')

index='[Icon Theme]\nName=Cinnamon12 Icons\nComment=Original icons for Cinnamon12 Concept\nInherits=Yaru,Adwaita,hicolor\nDirectories='+','.join(sections)+'\n\n'
for s in SIZES:
 for c in ('apps','places','devices','mimetypes','actions','status'):
  index+=f'[{s}x{s}/{c}]\nSize={s}\nType=Fixed\nContext={"Applications" if c=="apps" else ("MimeTypes" if c=="mimetypes" else c.title())}\n\n'
for c in ('apps','places','devices','mimetypes','actions','status'):
 index+=f'[scalable/{c}]\nSize=64\nMinSize=8\nMaxSize=512\nType=Scalable\nContext={"Applications" if c=="apps" else ("MimeTypes" if c=="mimetypes" else c.title())}\n\n'
(ICONS/'index.theme').write_text(index)

# Design preview contact sheet with title, icon names, and categories.
FONT=None
for font in ['/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf']:
 if Path(font).exists(): FONT=font; break
f=lambda sz: ImageFont.truetype(FONT,sz) if FONT else ImageFont.load_default()
items=[]
for category,dct in [('apps',APP_ICONS),('places',PLACE_ICONS),('devices',DEVICE_ICONS),('mimetypes',MIME_ICONS),('actions',ACTIONS),('status',STATUS)]:
 for name in dct:items.append((category,name))
C=9; CELL_W=156; CELL_H=120; ROWS=(len(items)+C-1)//C
im=Image.new('RGB',(C*CELL_W+56,ROWS*CELL_H+108),'#dceafb'); d=ImageDraw.Draw(im)
d.rounded_rectangle((16,15,im.width-16,88),radius=14,fill='#14325d')
d.text((40,28),'CINNAMON 12  |  BIBLIOTECA DE ICONES',font=f(23),fill='white')
d.text((40,60),f'{len(items)} nomes • SVG + PNG • Ubuntu 24.04 / Cinnamon 6.0.4',font=f(14),fill='#b3d6ff')
for i,(cat,n) in enumerate(items):
 x=28+(i%C)*CELL_W;y=102+(i//C)*CELL_H
 d.rounded_rectangle((x,y,x+CELL_W-10,y+CELL_H-10),radius=8,fill='#f5f9ff',outline='#c6d8ec')
 src=ICONS/'64x64'/cat/(n+'.png')
 if not src.exists():src=ICONS/'48x48'/cat/(n+'.png')
 icon=Image.open(src).convert('RGBA').resize((60,60),Image.Resampling.LANCZOS)
 im.paste(icon,(x+43,y+7),icon)
 text=n[:19]
 box=d.textbbox((0,0),text,font=f(10))
 tx=x+(CELL_W-10-(box[2]-box[0]))/2
 d.text((tx,y+73),text,font=f(10),fill='#29456b')
 d.text((x+12,y+91),cat.upper(),font=f(9),fill='#8098b8')
DEST.mkdir(parents=True,exist_ok=True)
im.save(DEST/'catalogo-icones.jpg',quality=90,optimize=True)
manifest={'icon_count':len(items),'count_by_category': {k:len(v) for k,v in [('apps',APP_ICONS),('places',PLACE_ICONS),('devices',DEVICE_ICONS),('mimetypes',MIME_ICONS),('actions',ACTIONS),('status',STATUS)]},'png_sizes':[16,24,32,48,64,128], 'format':['SVG','PNG'],'original_design':True}
(ROOT/'design'/'assets-manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(manifest,ensure_ascii=False))
