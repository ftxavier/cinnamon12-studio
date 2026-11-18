#!/usr/bin/env python3
"""Compile GTK3 and Cinnamon shell themes using literal supported CSS colors."""
import json, shutil, io
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1]
D=json.loads((ROOT/'design'/'tokens.json').read_text())

CINNAMON='''/* Cinnamon12 Studio | @VARIANT@ | Shell CSS targeting Cinnamon 6.0.x.\n   St (Cinnamon) != browser CSS. No backdrop-filter or CSS custom props. */

stage { color: @PANEL_TEXT@; font-family: "Ubuntu", "Noto Sans", sans-serif; font-size: 10pt; }
#panel, .panel-top, .panel-bottom, .panel-left, .panel-right {
  background-color: @PANEL@;
  color: @PANEL_TEXT@;
  border: 1px solid rgba(157,204,252,0.26);
  border-radius: 8px;
  box-shadow: 0 3px 16px @SHADOW@;
}
#panelLeft, #panelCenter, #panelRight { background-color: transparent; }
.panel-button, .panel-status-button, .panel-launcher, .panel-top .applet-box,
.panel-bottom .applet-box {
 color: @PANEL_TEXT@;
 border-radius: 5px;
 padding: 1px 7px;
}
.panel-button:hover, .panel-status-button:hover, .panel-top .applet-box:hover,
.panel-bottom .applet-box:hover { background-color: rgba(194,224,255,0.15); }
.panel-button:active, .panel-button:checked, .panel-status-button:active {
 background-color: rgba(25,155,255,0.29); color: #ffffff;
}
.grouped-window-list-item-box, .window-list-item-box {
 border-radius: 5px; padding: 2px 7px; color: @PANEL_TEXT@;
}
.grouped-window-list-item-box:hover, .window-list-item-box:hover { background-color: rgba(185,215,255,0.15); }
.grouped-window-list-item-box:active, .window-list-item-box:active,
.grouped-window-list-item-box:checked { background-color: rgba(49,150,243,0.30); }
.window-list-item-demands-attention { background-color: #ca5e63; }

/* Popups and menus */
.popup-menu-content, .menu, .switcher-list, .workspace-osd {
 color: @TEXT@; background-color: @POPUP@;
 border: 1px solid @LINE@; border-radius: 8px;
 box-shadow: 0 9px 25px @SHADOW@; padding: 8px;
}
.popup-menu-item { color: @TEXT@; border-radius: 5px; padding: 7px 12px; }
.popup-menu-item:active, .popup-menu-item:checked,
.popup-menu-item:hover { background-color: @ACCENT_SOFT@; color: @TEXT@; }
.popup-menu-item:insensitive { color: @MUTED@; }
.popup-separator-menu-item { height: 1px; background-color: @LINE@; margin: 6px 3px; }
.popup-menu-arrow { color: @MUTED@; }
.popup-menu-ornament { color: @ACCENT@; }
.popup-slider-menu-item { color: @ACCENT@; }
.popup-inactive-menu-item { color: @MUTED@; }

/* Original Cinnamon application menu */
.menu-background { background-color: @POPUP@; border: 1px solid @LINE@; border-radius: 8px; }
.menu-search-entry, .search-entry {
 background-color: @ENTRY@; color: @TEXT@;
 border: 1px solid @LINE@; border-radius: 6px; padding: 7px 11px;
 selection-background-color: @ACCENT@; selected-color: #ffffff;
}
.menu-search-entry:focus, .search-entry:focus { border: 2px solid @ACCENT@; }
.menu-category-button { color: @TEXT@; border-radius: 5px; padding: 6px 10px; }
.menu-category-button:hover, .menu-category-button-selected { background-color: @ACCENT_SOFT@; }
.menu-application-button, .menu-favorites-button { padding: 6px; border-radius: 6px; color: @TEXT@; }
.menu-application-button:hover, .menu-application-button-selected,
.menu-favorites-button:hover { background-color: @ACCENT_SOFT@; }
.menu-favorites-box, .menu-categories-box { border-radius: 5px; }
.menu-application-button-label { color: @TEXT@; }
.menu-selected-app-box { background-color: @SELECTED@; border-radius: 5px; }
.menu-selected-app-title, .menu-selected-app-description { color: @TEXT@; }
.menu-button { border-radius: 6px; }

/* Calendar and date popover */
.calendar { padding: 6px; color: @TEXT@; }
.calendar-month-label { font-weight: bold; color: @TEXT@; }
.calendar-day-base { border-radius: 5px; text-align: center; padding: 5px; }
.calendar-day-base:hover { background-color: @ACCENT_SOFT@; }
.calendar-day-base:active, .calendar-today { background-color: @ACCENT@; color: #ffffff; border-radius: 5px; }
.calendar-other-month-day { color: @MUTED@; }
.calendar-week-number { color: @MUTED@; }
.calendar-today { font-weight: bold; }
.datemenu-date-label, .datemenu-time-label { color: @TEXT@; }

/* Notifications and OSD */
.notification, .notification-body, .notification-applet-padding {
 color: @TEXT@; background-color: @POPUP@;
 border-color: @LINE@; border-radius: 7px;
}
.notification-button { color: @TEXT@; border-radius: 5px; }
.notification-button:hover { background-color: @ACCENT_SOFT@; }
.osd-window { border-radius: 8px; padding: 14px; color: @TEXT@;
 background-color: @POPUP@; border: 1px solid @LINE@; }
.osd-window .level { color: @ACCENT@; }
.tooltip { color: @TEXT@; background-color: @POPUP@; border: 1px solid @LINE@;
 border-radius: 5px; padding: 6px 9px; }
.modal-dialog, .end-session-dialog, .run-dialog {
 color: @TEXT@; background-color: @POPUP@; border: 1px solid @LINE@; border-radius: 8px;
}
.modal-dialog-button, .modal-dialog-button-box StButton { color: @TEXT@;
 background-color: @CARD@; border: 1px solid @LINE@; border-radius: 5px; padding: 8px 14px; }
.modal-dialog-button:hover { background-color: @ACCENT_SOFT@; }
.modal-dialog-button:focus { border: 2px solid @ACCENT@; }

/* Sliders, entry, scrollbars, switchers */
.slider { -slider-height: 5px; -slider-background-color: @LINE@;
 -slider-active-background-color: @ACCENT@; -slider-border-color: transparent;
 -slider-active-border-color: transparent; -slider-handle-radius: 7px;
 -slider-handle-color: @CYAN@; }
StScrollBar StBin#trough { background-color: rgba(75,112,151,.13); border-radius: 5px; }
StScrollBar StButton#vhandle, StScrollBar StButton#hhandle {
 background-color: rgba(88,155,209,.54); border-radius: 5px; }
StScrollBar StButton#vhandle:hover, StScrollBar StButton#hhandle:hover { background-color: @ACCENT@; }
.switcher-list .item-box { border-radius: 6px; padding: 9px; }
.switcher-list .item-box:selected { background-color: @ACCENT_SOFT@; }

/* Desklets and additional Cinnamon12 components */
.desklet, .desklet-header, .desklet-decoration { color: @PANEL_TEXT@; }
.desklet-with-borders, .desklet-with-borders-and-header {
 background-color: @WIDGET@; border: 1px solid rgba(172,211,250,.28); border-radius: 8px; }
.c12-widget { background-color: @WIDGET@; color: @PANEL_TEXT@;
 border: 1px solid rgba(164,209,250,.30); border-radius: 7px;
 padding: 13px 17px; }
.c12-widget-title { color: #e2f5ff; font-size: 11pt; font-weight: bold; }
.c12-widget-main { color: #ffffff; font-size: 24pt; font-weight: bold; }
.c12-widget-secondary { color: #bad9f7; font-size: 9pt; }
.c12-widget-divider { background-color: rgba(190,225,255,.22); height: 1px; }
.c12-popover { color: @TEXT@; background-color: @POPUP@; border: 1px solid @LINE@;
 border-radius: 8px; padding: 10px; }
.c12-action { color: @TEXT@; background-color: @CARD@; border: 1px solid @LINE@;
 border-radius: 6px; padding: 7px 10px; }
.c12-action:hover { background-color: @ACCENT_SOFT@; }
'''

GTK='''/* Cinnamon12 Studio | @VARIANT@ | GTK 3.x (and optional GTK 4.x) theme.
   Target: Nemo, GTK3 tools. GTK4/libadwaita apps may ignore the theme. */
@define-color theme_bg_color @WINDOW@;
@define-color theme_fg_color @TEXT@;
@define-color theme_base_color @ENTRY@;
@define-color theme_text_color @TEXT@;
@define-color theme_selected_bg_color @ACCENT@;
@define-color theme_selected_fg_color #ffffff;
@define-color borders @LINE@;
@define-color insensitive_fg_color @MUTED@;
@define-color insensitive_bg_color @SIDE@;
@define-color theme_unfocused_bg_color @WINDOW@;
@define-color theme_unfocused_fg_color @MUTED@;
@define-color view_bg_color @CARD@;
@define-color view_fg_color @TEXT@;
@define-color accent_bg_color @ACCENT@;
@define-color accent_fg_color #ffffff;

* { -GtkWidget-link-color: @ACCENT@; }
window, dialog, messagedialog, GtkWindow, .background {
 background-color: @WINDOW@; color: @TEXT@;
}
window:backdrop { color: @MUTED@; }
headerbar, .titlebar, decoration {
 background-image: none;
 background-color: @HEADER@;
 color: @TEXT@;
 border-color: @LINE@;
 border-radius: 7px 7px 0 0;
}
headerbar, .titlebar { min-height: 28px; padding: 5px 8px; border-bottom: 1px solid @LINE@; }
headerbar:backdrop, .titlebar:backdrop { background-color: @WINDOW@; color: @MUTED@; }
window decoration { box-shadow: 0 7px 25px @SHADOW_GTK@; }
.titlebar .title { font-weight: 600; }

button, modelbutton, .button, spinbutton button {
 background-image: none; background-color: @CARD@; color: @TEXT@;
 border: 1px solid @LINE@; border-radius: 6px;
 padding: 5px 10px; min-height: 17px;
}
button:hover, modelbutton:hover, .button:hover { background-image: none; background-color: @ACCENT_SOFT@; }
button:active, button:checked, modelbutton:checked, .suggested-action {
 background-image: none; background-color: @ACCENT@; color: #ffffff; border-color: @ACCENT@;
}
button:focus, entry:focus, textview:focus, spinbutton:focus {
 outline-style: solid; outline-color: @ACCENT@; outline-width: 1px; outline-offset: -2px;
}
button:disabled { color: @MUTED@; opacity: .62; }
button.flat, button.flat:hover { border-color: transparent; background-color: transparent; }
button.flat:hover { background-color: @ACCENT_SOFT@; }
.titlebutton { border-radius: 5px; min-width: 18px; min-height: 18px; }
.titlebutton.close:hover { background-color: #e05a75; color: white; }

entry, searchentry, spinbutton, combobox box.linked entry, .entry {
 background-image: none; background-color: @ENTRY@; color: @TEXT@;
 border: 1px solid @LINE@; border-radius: 6px; padding: 6px 8px;
 caret-color: @ACCENT@;
}
entry:focus, searchentry:focus, spinbutton:focus { border-color: @ACCENT@; }
entry selection, textview text selection { background-color: @ACCENT@; color: white; }
entry:disabled, textview:disabled { color: @MUTED@; background-color: @SIDE@; }

.view, iconview, treeview, textview, textview text, viewport, scrolledwindow,
list, listbox, flowbox, gridview {
 background-color: @CARD@; color: @TEXT@;
}
textview text { background-color: @ENTRY@; }
row { padding: 3px 5px; border-radius: 4px; }
row:hover, treeview.view:hover, iconview:hover { background-color: @ACCENT_SOFT@; }
row:selected, treeview.view:selected, iconview:selected, .view:selected {
 background-color: @SELECTED@; color: @TEXT@;
}
row:selected:focus { box-shadow: inset 0 0 0 1px @ACCENT@; }

/* Nemo's location sidebar, panes and path widgets */
.sidebar, .nemo-window .sidebar, .source-list, placessidebar, placessidebar viewport {
 background-color: @SIDE@; color: @TEXT@;
}
.sidebar row, placessidebar row { border-radius: 5px; padding: 5px 7px; }
.sidebar row:hover, placessidebar row:hover { background-color: @ACCENT_SOFT@; }
.sidebar row:selected, placessidebar row:selected { background-color: @SELECTED@; color: @TEXT@; }
.path-bar button { border-radius: 4px; }
.nemo-window .view:selected, .nemo-window iconview:selected { background-color: @SELECTED@; }

/* Menus, popovers, notifications */
menu, .menu, popover, popover.background, .context-menu, menuitem {
 background-color: @WINDOW@; color: @TEXT@;
 border-color: @LINE@; border-radius: 5px;
}
popover, menu { border: 1px solid @LINE@; box-shadow: 0 8px 22px @SHADOW_GTK@; }
menuitem { padding: 5px 11px; }
menuitem:hover, modelbutton:hover { background-color: @ACCENT_SOFT@; }
separator { background-color: @LINE@; min-height: 1px; min-width: 1px; }
notebook > header { background-color: @SIDE@; border-color: @LINE@; }
notebook > header tab { background-color: transparent; color: @MUTED@;
 border-radius: 5px 5px 0 0; padding: 7px 12px; }
notebook > header tab:hover { background-color: @ACCENT_SOFT@; }
notebook > header tab:checked { background-color: @CARD@; color: @ACCENT@; border-bottom: 2px solid @ACCENT@; }

/* Progress, scrollbars, switches */
progressbar trough, scale trough, levelbar trough {
 background-color: @SIDE@; border-radius: 6px; min-height: 5px;
}
progressbar progress, scale highlight, levelbar block.filled {
 background-color: @ACCENT@; border-radius: 6px;
}
scale slider { background-color: @ACCENT@; border: 2px solid @CARD@;
 border-radius: 50%; min-width: 13px; min-height: 13px; }
scrollbar { background-color: transparent; }
scrollbar slider { background-color: @LINE@; border-radius: 6px; min-width: 6px; min-height: 6px; }
scrollbar slider:hover { background-color: @ACCENT@; }
switch { background-color: @SIDE@; border: 1px solid @LINE@; border-radius: 20px; }
switch:checked { background-color: @ACCENT@; }
switch slider { background-color: @CARD@; border-radius: 50%; border: 1px solid @LINE@; }
checkbutton check, radiobutton radio { background-color: @ENTRY@; border: 1px solid @LINE@; }
checkbutton check:checked, radiobutton radio:checked { background-color: @ACCENT@; color: white; }

infobar, banner, .app-notification { background-color: @ACCENT_SOFT@; color: @TEXT@; }
statusbar { color: @MUTED@; background-color: @SIDE@; }
frame > border { border: 1px solid @LINE@; border-radius: 6px; }
.linked button { border-radius: 0; }
.linked button:first-child { border-radius: 5px 0 0 5px; }
.linked button:last-child { border-radius: 0 5px 5px 0; }
'''

ROOT_THEMES=ROOT/'themes'
for variant, vals in [('light',D['light']),('dark',D['dark'])]:
 name='Cinnamon12-'+variant.capitalize()
 p=ROOT_THEMES/name
 vals2={k.upper():v for k,v in vals.items()}
 vals2['VARIANT']=variant
 vals2['SELECTED']=vals['accent_soft']
 def compile(s):
  for k,v in vals2.items():s=s.replace('@'+k+'@',str(v))
  return s
 for layer,css in [('cinnamon',CINNAMON),('gtk-3.0',GTK),('gtk-4.0',GTK)]:
  loc=p/layer;loc.mkdir(parents=True,exist_ok=True)
  (loc/('cinnamon.css' if layer=='cinnamon' else 'gtk.css')).write_text(compile(css))
 (p/'index.theme').write_text(f'''[Desktop Entry]\nType=X-GNOME-Metatheme\nName={name}\nComment=Cinnamon12 Studio native theme ({variant}), small radius and blue accents\nGtkTheme={name}\nIconTheme=Cinnamon12-Icons\nCursorTheme=Yaru\n''')
 wallpaper='c12-arctic' if variant=='light' else 'c12-midnight'
 src=Image.open(ROOT/'assets'/'wallpapers'/f'{wallpaper}-1920x1080.jpg').resize((420,236))
 d=ImageDraw.Draw(src)
 d.rounded_rectangle((13,195,405,228),radius=7,fill='#12345b')
 for i in range(6):
  x=152+29*i
  d.rounded_rectangle((x,200,x+21,221),radius=4,fill=['#38bafd','#538dfe','#786afc','#3daac3','#f8a65b','#8dceff'][i])
 for layer in ('cinnamon','gtk-3.0'):
  src.save(p/layer/'thumbnail.png')
 print(name)
