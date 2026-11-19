#!/usr/bin/env python3
"""Cinnamon12 Studio | compile Cinnamon shell, GTK3 and GTK4 themes from design/tokens.json.

Architecture (v0.3):
  * Cinnamon shell: @import the stock cinnamon.css that ships with the *installed*
    Cinnamon (/usr/share/cinnamon/theme/cinnamon.css) and override colors/geometry.
    This keeps every selector of whatever Cinnamon version is installed styled.
  * GTK3: @import the Adwaita theme compiled into libgtk-3 (gtk-contained*.css) and
    override. Muffin 6.x draws server-side title bars with this same GTK3 CSS
    (headerbar.titlebar.default-decoration), so no metacity-1 theme is needed.
  * GTK4: @import the GTK4 Default theme from libgtk-4 and override named colors.
    libadwaita apps ignore it by design.

Only literal values are emitted (St has no CSS variables).  Run:
    python3 scripts/generate-themes.py
"""
import json
from pathlib import Path
from string import Template
import re

ROOT = Path(__file__).resolve().parents[1]
TOK = json.loads((ROOT / 'design' / 'tokens.json').read_text())

STOCK_CINNAMON_CSS = '/usr/share/cinnamon/theme/cinnamon.css'

# --------------------------------------------------------------------------------------
# Extra derived values per variant (kept here so tokens.json stays the human palette).
EXTRA = {
    'light': {
        'popup_solid': '#ebf6ff', 'popup_border': '#b6d0eb', 'hover_bg': '#d6ecff',
        'item_active': '#c1e4ff', 'subtle_bg': 'rgba(7,143,232,0.08)',
        'entry_border': '#b6d0eb', 'osd_bg': 'rgba(235,246,255,0.96)',
        'dialog_bg': 'rgba(237,245,255,0.98)', 'danger': '#d9516a', 'success': '#28b89a',
        'warning': '#f3b34d', 'gtk_base': 'Adwaita/gtk-contained.css',
        'gtk4_base': 'Default/Default-light.css', 'titlebar': '#c4e0fd', 'titlebar_hi': '#cde9fd',
        'titlebar_backdrop': '#dcebfd', 'titlebar_edge': 'rgba(255,255,255,0.55)',
        'toolbar': '#d8e8fb', 'toolbar_line': '#c2d6ef',
        'crumb_bg': '#e9f2fe', 'crumb_hover': '#dcebfd', 'crumb_border': '#c8dcf3', 'crumb_hi': 'rgba(255,255,255,0.70)',
        # Nemo surfaces (file manager reference images)
        'fm_view': '#f5faff', 'fm_side': '#d9eafa', 'fm_status': '#edf5ff', 'fm_line': '#b6d0eb',
        'fm_sel': '#0571c4', 'fm_sel_fg': '#ffffff', 'fm_hover': '#d6ecff',
        'fm_tile': '#c1e4ff', 'fm_tile_ring': '#078fe8', 'fm_checked': '#c1e4ff', 'fm_checked_ring': '#078fe8', 'scroll': 'rgba(82,110,144,0.45)',
        'tooltip_bg': 'rgba(22,46,77,0.95)', 'tooltip_fg': '#f2f8ff',
        # WCAG AA: accent as text on light surfaces (4.7:1 over the 97% popup) and as a fill under white text (5.0:1).
        'accent_fg': '#056bbb', 'accent_fill': '#0571c4', 'on_accent': '#ffffff',
        'on_accent_muted': 'rgba(255,255,255,0.85)', 'on_accent_line': 'rgba(255,255,255,0.30)',
    },
    'dark': {
        'popup_solid': '#17283c', 'popup_border': '#2d4766', 'hover_bg': '#21405f',
        'item_active': '#254d71', 'subtle_bg': 'rgba(43,170,255,0.10)',
        'entry_border': '#355474', 'osd_bg': 'rgba(23,40,60,0.96)',
        'dialog_bg': 'rgba(23,40,62,0.98)', 'danger': '#f17189', 'success': '#42d5ad',
        'warning': '#f6c262', 'gtk_base': 'Adwaita/gtk-contained-dark.css',
        'gtk4_base': 'Default/Default-dark.css', 'titlebar': '#112b52', 'titlebar_hi': '#173d70',
        'titlebar_backdrop': '#11233b', 'titlebar_edge': 'rgba(120,170,230,0.28)',
        'toolbar': '#121f33', 'toolbar_line': '#2a3b58',
        'crumb_bg': '#1a2d49', 'crumb_hover': '#22395b', 'crumb_border': '#2a4068', 'crumb_hi': 'rgba(255,255,255,0.04)',
        # Nemo surfaces: deeper navy than the generic dark card; white text on the sidebar
        # selection needs a deeper blue than the bright accent (4.9:1)
        'fm_view': '#122039', 'fm_side': '#0f1b2b', 'fm_status': '#141d2f', 'fm_line': '#24364f',
        'fm_sel': '#0b6fd6', 'fm_sel_fg': '#ffffff', 'fm_hover': '#2b3c57',
        'fm_tile': '#0d3060', 'fm_tile_ring': '#1a8fe0', 'fm_checked': '#1f4374', 'fm_checked_ring': '#2f73c4', 'scroll': 'rgba(164,191,220,0.40)',
        'tooltip_bg': 'rgba(9,20,39,0.96)', 'tooltip_fg': '#eef6ff',
        # Bright accent keeps the look; text on it is dark navy (6.5:1) instead of white (2.5:1).
        'accent_fg': '#2baaff', 'accent_fill': '#2baaff', 'on_accent': '#06203d',
        'on_accent_muted': 'rgba(6,32,61,0.80)', 'on_accent_line': 'rgba(6,32,61,0.30)',
    },
}
# The panel and the widgets are dark navy in both variants (reference image).
PANEL = {
    'panel_hover': 'rgba(194,224,255,0.14)', 'panel_active': 'rgba(43,170,255,0.28)',
    'panel_border': 'rgba(157,204,252,0.22)', 'panel_indicator': '#36ccf6',
}


def palette(variant):
    p = dict(TOK[variant])
    p.update(EXTRA[variant])
    p.update(PANEL)
    p.update({'r_' + k: str(v) for k, v in TOK['radii'].items()})
    p['variant'] = variant
    p['chevron'] = 'assets/pathbar-chevron-%s.svg' % variant
    p['stock'] = STOCK_CINNAMON_CSS
    return p


# ======================================================================================
# Cinnamon shell (St)
CINNAMON = Template(r'''/* Cinnamon12 Studio | $variant | Cinnamon shell theme.
 * Generated by scripts/generate-themes.py from design/tokens.json - do not edit by hand.
 * Base: the stylesheet of the Cinnamon version installed on this system, so every
 * stock selector stays styled; only the Cinnamon12 overrides follow. */
@import url("$stock");

/* ---------- Panel (dark navy in both variants) ---------- */
#panel {
  background-color: $panel;
  background-gradient-direction: none;
  color: $panel_text;
  border: none;
}
/* Full-width panel, edge to edge like the Windows taskbar: solid translucent navy with
 * a hairline on the side facing the desktop. Hover/active pills are border-images
 * inset 4 px from the bar edges. */
.panel-bottom, .panel-top, .panel-left, .panel-right {
  background-color: $panel; background-gradient-direction: none; border: none; border-image: none; }
.panel-bottom { border-top: 1px solid $panel_border; }
.panel-top { border-bottom: 1px solid $panel_border; }
.panel-left { border-right: 1px solid $panel_border; }
.panel-right { border-left: 1px solid $panel_border; }
.panel-bottom, .panel-top { padding: 0 0 0 6px; }
.panel-bottom:rtl, .panel-top:rtl { padding: 0 6px 0 0; }
.panel-left, .panel-right { padding: 6px 0 0 0; }
#panel:highlight, .applet-box:highlight, .spacer-box:highlight { background-color: rgba(43,170,255,0.35); }
.panel-dummy { background-color: rgba(43,170,255,0.18); }
.panel-dummy:entered { background-color: rgba(43,170,255,0.40); }
.panelLeft:dnd, .panelCenter:dnd, .panelRight:dnd {
  background-gradient-direction: none; background-color: rgba(43,170,255,0.12); }

.applet-box { color: $panel_text; text-shadow: none; border-radius: 5px; }
.applet-box:hover, .applet-box:checked { color: #ffffff; }
/* Applet pills: symmetric padding keeps the icon centered and the pill square-ish:
 * 20 px status icon + 12 = 32 x 32 at the ends; 28 px start icon + 12 = 40 x 40 in the
 * center, like the window list. */
.panel-bottom .applet-box, .panel-top .applet-box { padding: 0 6px; }
.panel-left .applet-box, .panel-right .applet-box { padding: 6px 0; }
.panel-bottom .applet-box:hover, .panel-bottom .applet-box:checked,
.panel-top .applet-box:hover, .panel-top .applet-box:checked { border-image: url("assets/pill-h-hover-sm.svg") 20 10; }
.panel-left .applet-box:hover, .panel-left .applet-box:checked,
.panel-right .applet-box:hover, .panel-right .applet-box:checked { border-image: url("assets/pill-v-hover-sm.svg") 10 20; }
.panel-bottom .panelCenter .applet-box, .panel-top .panelCenter .applet-box { padding: 0 6px; }
.panel-bottom .panelCenter .applet-box:hover, .panel-bottom .panelCenter .applet-box:checked,
.panel-top .panelCenter .applet-box:hover, .panel-top .panelCenter .applet-box:checked { border-image: url("assets/pill-h-hover.svg") 20 10; }
.applet-box:checked > .applet-label, .applet-box:hover > .applet-label { color: #ffffff; text-shadow: none; }
.applet-box:checked .applet-icon, .applet-box:hover .applet-icon { color: #ffffff; icon-shadow: none; }
.applet-label, .applet-icon { color: $panel_text; }
.panel-button, .panel-status-button { color: $panel_text; }
.panel-button:hover, .panel-status-button:hover { color: #ffffff; text-shadow: none; }
.applet-separator-line { background: rgba(237,246,255,0.25); }
/* "show desktop": a 14 px strip in the corner, Windows style. The panel has no end
 * padding on that side, so the strip reaches the screen edge (throw the pointer into
 * the corner); it is a bit lighter than the bar and lights up more on hover.
 * Assumes the applet is the last one, as in the stock layout and our panel profile. */
.applet-cornerbar { background: transparent; width: 0; height: 0; }
.panel-bottom .applet-cornerbar-box, .panel-top .applet-cornerbar-box {
  padding: 0; margin-left: 8px; width: 14px; border-image: url("assets/cap-h.svg") 0; }
.panel-bottom .applet-cornerbar-box:hover, .panel-top .applet-cornerbar-box:hover { border-image: url("assets/cap-h-hover.svg") 0; }
.panel-left .applet-cornerbar-box, .panel-right .applet-cornerbar-box {
  padding: 0; margin-top: 8px; height: 14px; border-image: url("assets/cap-v.svg") 0; }
.panel-left .applet-cornerbar-box:hover, .panel-right .applet-cornerbar-box:hover { border-image: url("assets/cap-v-hover.svg") 0; }

/* window lists (grouped and classic): pills drawn as border-images inset to the bar */
.grouped-window-list-item-box, .window-list-item-box {
  color: $panel_text;
  background-gradient-direction: none; background-color: transparent;
  box-shadow: none; border-radius: 8px;
}
.panel-bottom .grouped-window-list-item-box, .panel-top .grouped-window-list-item-box,
.panel-bottom .window-list-item-box, .panel-top .window-list-item-box { margin: 0 2px; }
/* the stock applet zeroes the horizontal padding inline; min-width makes the pill square
 * (40 x 40: 48 px panel minus a 4 px inset on each side) */
.panel-bottom .grouped-window-list-item-box, .panel-top .grouped-window-list-item-box { min-width: 40px; }
.panel-left .grouped-window-list-item-box, .panel-right .grouped-window-list-item-box { min-height: 40px; }
.panel-left .grouped-window-list-item-box, .panel-right .grouped-window-list-item-box,
.panel-left .window-list-item-box, .panel-right .window-list-item-box { margin: 2px 0; }
.grouped-window-list-item-box:hover, .window-list-item-box:hover,
.grouped-window-list-item-box:active, .window-list-item-box:active { background-color: transparent; box-shadow: none; }
.panel-bottom .grouped-window-list-item-box:hover, .panel-top .grouped-window-list-item-box:hover,
.panel-bottom .window-list-item-box:hover, .panel-top .window-list-item-box:hover { border-image: url("assets/pill-h-hover.svg") 20 10; }
.panel-left .grouped-window-list-item-box:hover, .panel-right .grouped-window-list-item-box:hover,
.panel-left .window-list-item-box:hover, .panel-right .window-list-item-box:hover { border-image: url("assets/pill-v-hover.svg") 10 20; }
.panel-bottom .grouped-window-list-item-box:active, .panel-top .grouped-window-list-item-box:active,
.panel-bottom .window-list-item-box:active, .panel-top .window-list-item-box:active { border-image: url("assets/pill-h-running.svg") 20 10; }
.panel-left .grouped-window-list-item-box:active, .panel-right .grouped-window-list-item-box:active,
.panel-left .window-list-item-box:active, .panel-right .window-list-item-box:active { border-image: url("assets/pill-v-running.svg") 10 20; }
.grouped-window-list-item-box:checked, .grouped-window-list-item-box:focus,
.grouped-window-list-item-box:active:hover, .grouped-window-list-item-box:focus:hover,
.grouped-window-list-item-box:active:focus:hover,
.window-list-item-box:checked, .window-list-item-box:focus {
  background-gradient-direction: none; background-color: transparent; box-shadow: none; }
.panel-bottom .grouped-window-list-item-box:checked, .panel-bottom .grouped-window-list-item-box:focus,
.panel-bottom .grouped-window-list-item-box:active:hover, .panel-bottom .grouped-window-list-item-box:focus:hover,
.panel-bottom .window-list-item-box:checked, .panel-bottom .window-list-item-box:focus,
.panel-top .grouped-window-list-item-box:checked, .panel-top .grouped-window-list-item-box:focus,
.panel-top .grouped-window-list-item-box:active:hover, .panel-top .grouped-window-list-item-box:focus:hover,
.panel-top .window-list-item-box:checked, .panel-top .window-list-item-box:focus { border-image: url("assets/pill-h-focus.svg") 20 10; }
.panel-left .grouped-window-list-item-box:checked, .panel-left .grouped-window-list-item-box:focus,
.panel-left .grouped-window-list-item-box:active:hover, .panel-left .grouped-window-list-item-box:focus:hover,
.panel-right .grouped-window-list-item-box:checked, .panel-right .grouped-window-list-item-box:focus,
.panel-right .grouped-window-list-item-box:active:hover, .panel-right .grouped-window-list-item-box:focus:hover { border-image: url("assets/pill-v-focus.svg") 10 20; }
.grouped-window-list-item-demands-attention, .window-list-item-demands-attention {
  background-gradient-direction: none; background-color: transparent; }
.panel-bottom .grouped-window-list-item-demands-attention, .panel-top .grouped-window-list-item-demands-attention,
.panel-bottom .window-list-item-demands-attention, .panel-top .window-list-item-demands-attention { border-image: url("assets/pill-h-attention.svg") 20 10; }
.panel-left .grouped-window-list-item-demands-attention, .panel-right .grouped-window-list-item-demands-attention { border-image: url("assets/pill-v-attention.svg") 10 20; }
.grouped-window-list-item-box .progress, .window-list-item-box .progress {
  background-gradient-direction: none; background-color: rgba(54,204,246,0.55); box-shadow: none; }
.grouped-window-list-badge { background-color: $accent; border-radius: 6px; }
.grouped-window-list-number-label { color: #ffffff; text-shadow: none; }

.grouped-window-list-thumbnail-menu .item-box, .window-list-preview {
  background: $popup; border: 1px solid $popup_border; color: $text;
  text-shadow: none; border-radius: ${r_menu}px; }
.grouped-window-list-thumbnail-menu .item-box:outlined { border: 1px solid $accent; }
.grouped-window-list-thumbnail-menu .item-box:selected { background: $item_active; }
.grouped-window-list-thumbnail-menu .separator { background: $popup_border; }
.grouped-window-list-thumbnail-alert { background: rgba(241,113,137,0.30); }

.workspace-button { color: $panel_text; border-color: rgba(237,246,255,0.35); border-radius: 4px; }
.workspace-button:outlined { background: $accent_fill; color: $on_accent; box-shadow: none; }
.workspace-graph .workspace { border: 1px solid rgba(237,246,255,0.25);
  background-gradient-direction: none; background-color: rgba(255,255,255,0.06); border-radius: 3px; }
.workspace-graph .workspace:active { border: 1px solid $cyan;
  background-gradient-direction: none; background-color: rgba(43,170,255,0.25); }

/* ---------- Popup menus ---------- */
.popup-menu-boxpointer {
  -arrow-border-radius: ${r_menu}px;
  -arrow-background-color: $popup;
  -arrow-border-width: 1px;
  -arrow-border-color: $popup_border;
  -arrow-base: 0; -arrow-rise: 0;
}
.menu {
  background-color: $popup;
  border: 1px solid $popup_border;
  border-radius: ${r_menu}px;
  color: $text;
  box-shadow: 0 6px 18px $shadow;
}
.popup-menu { color: $text; }
.popup-menu-content { padding: 6px 0; }
.popup-menu-item { color: $text; border-radius: 5px; margin: 0 6px; padding: .45em 1.2em; }
.popup-menu-item:active { background-color: $item_active; color: $text; }
.popup-menu-item:checked { background-color: $subtle_bg; }
.popup-menu-item:insensitive, .popup-inactive-menu-item { color: $muted; }
.popup-submenu-menu-item:open { background-color: $subtle_bg; }
.popup-sub-menu { background-gradient-direction: none; background-color: $subtle_bg; border-radius: 6px; }
.popup-sub-menu StScrollBar StBin#vhandle { background-color: $scroll; }
.popup-combo-menu { background-color: $popup_solid; color: $text; border: 1px solid $popup_border; border-radius: 6px; }
.popup-separator-menu-item, .separator {
  -gradient-height: 1px; -gradient-start: $popup_border; -gradient-end: $popup_border; }
.popup-menu-ornament, .popup-menu-arrow { color: $muted; }
.popup-menu-icon { color: $text; }

.slider, .popup-slider-menu-item {
  -slider-height: 4px;
  -slider-background-color: $line;
  -slider-border-color: transparent;
  -slider-active-background-color: $accent;
  -slider-active-border-color: transparent;
  -slider-border-width: 0px;
  -slider-handle-radius: 7px;
  -slider-handle-border-width: 2px;
  -slider-handle-border-color: $popup_solid;
  color: $accent_fg;
}

.toggle-switch-us, .toggle-switch-intl { background-image: url("assets/toggle-off.svg"); }
.toggle-switch-us:checked, .toggle-switch-intl:checked { background-image: url("assets/toggle-on.svg"); }
.check-box StBin, .check-box:focus StBin { background-image: url("assets/checkbox-off.svg"); }
.check-box:checked StBin, .check-box:focus:checked StBin { background-image: url("assets/checkbox-on.svg"); }
.radiobutton StBin, .radiobutton:focus StBin { background-image: url("assets/radio-off.svg"); }
.radiobutton:checked StBin, .radiobutton:focus:checked StBin { background-image: url("assets/radio-on.svg"); }

/* Slim overlay-style scrollbars (base theme uses 16 px). */
StScrollView StScrollBar { min-width: 8px; min-height: 8px; padding: 1px; }
StScrollBar StBin#trough { background-color: transparent; border: none; }
StScrollBar StButton#vhandle, StScrollBar StButton#hhandle {
  background-image: none; background-color: $scroll; border: none; border-radius: 4px; }
StScrollBar StButton#vhandle:hover, StScrollBar StButton#hhandle:hover { background-color: $accent; }

/* ---------- Stock application menu (menu@cinnamon.org) ---------- */
.menu-favorites-box {
  border: 1px solid $popup_border; border-radius: ${r_card}px;
  background-gradient-direction: none; background-color: $subtle_bg; }
.menu-favorites-button:hover, .menu-application-button-selected, .menu-category-button-selected {
  color: $text; background-gradient-direction: none; background-color: $item_active;
  box-shadow: none; border-radius: 5px; }
.menu-application-button, .menu-category-button { color: $text; border-radius: 5px; }
.menu-category-button:hover { background-color: $hover_bg; }
.menu-category-button-greyed { color: $muted; }
.menu-selected-app-title, .menu-selected-app-description { color: $text; }
#menu-search-entry {
  color: $text; caret-color: $accent; selected-color: $on_accent; selection-background-color: $accent_fill;
  border: 1px solid $entry_border; border-radius: 6px;
  background-gradient-direction: none; background-color: $entry; padding: 6px 8px; }
#menu-search-entry:hover { border: 1px solid $accent; background-gradient-direction: none; background-color: $entry; }
#menu-search-entry:focus { border: 2px solid $accent; background-gradient-direction: none;
  background-color: $entry; color: $text; font-weight: normal; padding: 5px 7px; }
.menu-search-entry-icon { color: $muted; }

/* ---------- Calendar applet ---------- */
.calendar-events-main-box {
  border: 1px solid $popup_border; border-radius: ${r_card}px;
  background-gradient-direction: none; background-color: $subtle_bg; }
.calendar-events-main-box .separator { -gradient-start: $popup_border; -gradient-end: $popup_border; }
.calendar-events-no-events-icon, .calendar-events-no-events-label, .calendar-events-date-label,
.calendar-event-countdown, .calendar-event-summary, .calendar-today-day-label,
.calendar-today-date-label, .calendar-month-label, .calendar-day-heading,
.calendar-not-today, .calendar-week-number { color: $text; }
.calendar-day-heading, .calendar-week-number { color: $muted; }
.calendar-event-time-past { color: $muted; }
.calendar-event-countdown:soon { color: $accent_fg; }
.calendar-event-countdown:imminent { color: $warning; }
.calendar-event-countdown:current, .calendar-event-time-present:all-day { color: $success; }
.calendar-events-no-events-button:hover, .calendar-event-button:hover,
.calendar-today-home-button-enabled:hover {
  background-gradient-direction: none; background-color: $hover_bg; box-shadow: none; border-radius: 5px; }
.calendar-change-month-back, .calendar-change-month-forward { border-radius: 4px; }
.calendar-change-month-back { background-image: url("assets/arrow-left.svg"); }
.calendar-change-month-forward { background-image: url("assets/arrow-right.svg"); }
.calendar-change-month-back:rtl { background-image: url("assets/arrow-right.svg"); }
.calendar-change-month-forward:rtl { background-image: url("assets/arrow-left.svg"); }
.calendar-change-month-back:hover, .calendar-change-month-forward:hover { background-color: $hover_bg; }
.calendar-change-month-back:active, .calendar-change-month-forward:active { background-color: $item_active; }
.calendar-day:ltr, .calendar-day:rtl { border: none; }
.calendar-day-base { border-radius: 5px; }
.calendar-day-base:hover { color: $text; background-color: $hover_bg; }
.calendar-day-base:active { background-color: $item_active; }
.calendar-nonwork-day { background-color: transparent; color: $muted; }
.calendar-other-month-day { color: $muted; background-color: transparent; opacity: 0.55; }
.calendar-today {
  background-gradient-direction: none; background-color: $accent_fill; color: $on_accent;
  font-weight: bold; border-radius: 5px; }
.calendar-today:selected, .calendar-not-today:selected { color: $accent_fg; }
.calendar-today:selected { color: $on_accent; }

/* ---------- Sound applet / media player ---------- */
.sound-player StButton { color: $muted; border-radius: 5px; }
.sound-player StButton:hover, .sound-player StButton:active { color: $accent_fg; background-color: $hover_bg; }
.sound-player .slider { -slider-background-color: $line; -slider-active-background-color: $accent; }
.sound-player-overlay { background-color: $popup_solid; color: $text; border-top: 1px solid $popup_border; }
.sound-player-overlay StButton, .notification-button, .notification-icon-button, .modal-dialog-button {
  color: $text; border: 1px solid $entry_border; border-radius: 6px;
  background-gradient-direction: none; background-color: $card; }
.sound-player-overlay StButton:hover, .notification-button:hover, .notification-icon-button:hover,
.modal-dialog-button:hover { background-gradient-direction: none; background-color: $hover_bg; }
.notification-button:focus, .notification-icon-button:focus, .modal-dialog-button:focus { border: 2px solid $accent; }
.notification-button:active, .notification-icon-button:active, .modal-dialog-button:active,
.modal-dialog-button:pressed { background-gradient-direction: none; background-color: $item_active; }
.modal-dialog-button:disabled { color: $muted; }

/* ---------- Notifications ---------- */
#notification {
  border: 1px solid $popup_border; border-radius: ${r_card}px;
  background-gradient-direction: none; background-color: $popup; color: $text;
  box-shadow: 0 6px 18px $shadow; }
#notification.multi-line-notification, .notification-with-image { color: $text; }
#notification StEntry, #notification StEntry:focus {
  color: $text; selected-color: $on_accent; selection-background-color: $accent_fill; caret-color: $accent;
  border: 1px solid $entry_border; border-radius: 6px;
  background-gradient-direction: none; background-color: $entry; box-shadow: none; }
#notification StEntry:focus { border: 1px solid $accent; }

/* ---------- Tooltips ---------- */
#Tooltip, .tooltip {
  border: 1px solid rgba(157,204,252,0.25); border-radius: 5px;
  background-gradient-direction: none; background-color: $tooltip_bg; color: $tooltip_fg;
  padding: 4px 10px; }

/* ---------- Alt-Tab / switchers / OSD / dialogs ---------- */
.switcher-list {
  background: $popup; border: 1px solid $popup_border; border-radius: ${r_menu}px;
  color: $text; text-shadow: none; box-shadow: 0 8px 24px $shadow; }
.switcher-list .item-box { border-radius: 6px; }
.switcher-list .item-box:outlined { border: 2px solid $accent; }
.switcher-list .item-box:selected { background: $item_active; }
.switcher-list .separator { background: $popup_border; }
.thumbnail-scroll-gradient-left, .thumbnail-scroll-gradient-right { background-gradient-direction: none; }
.switcher-arrow { color: $muted; }
.switcher-arrow:highlighted { color: $accent_fg; }
.switcher-preview-backdrop { background-color: rgba(9,20,39,0.55); }

.osd-window, .info-osd {
  background: $osd_bg; border: 1px solid $popup_border; border-radius: ${r_menu}px; color: $text; }
.osd-window .level { background-color: $line; }
.osd-window .level-bar { background-color: $accent; }
.workspace-osd { color: #ffffff; text-shadow: 0 1px 6px rgba(0,0,0,0.6); }

.modal-dialog {
  border-radius: ${r_menu}px; background-color: $dialog_bg; border: 1px solid $popup_border;
  color: $text; box-shadow: 0 10px 30px $shadow; }
.run-dialog-label, .run-dialog-description { color: $text; }
.run-dialog-description.error { color: $danger; }
.run-dialog-entry { color: $text; selection-background-color: $accent_fill; selected-color: $on_accent; }
.lightbox { background-color: rgba(9,20,39,0.45); }

/* ---------- Expo / overview / tiling ---------- */
.expo-background { background-gradient-direction: vertical; background-gradient-start: #0b1f3a; background-gradient-end: #12345b; }
.expo-workspace-thumbnail-frame { background-color: rgba(9,20,39,0.6); border-radius: 6px; }
.expo-workspace-thumbnail-frame#active { background-color: rgba(43,170,255,0.35); border-radius: 6px; }
.expo-workspaces-name-entry {
  color: #eef6ff; border: 1px solid rgba(157,204,252,0.35); border-radius: 5px;
  background-gradient-direction: none; background-color: rgba(9,20,39,0.7); }
.expo-workspaces-name-entry#selected, .expo-workspaces-name-entry:focus {
  background-gradient-direction: none; background-color: #ffffff; color: #162e4d; }
.window-caption { background: rgba(9,20,39,0.85); border: 1px solid rgba(157,204,252,0.35); color: #eef6ff; border-radius: 5px; }
.window-border { border: 3px $accent; box-shadow: 0 0 0 1px $cyan inset; border-radius: 6px; }
.workspace-thumbnails-background { background-color: rgba(9,20,39,0.6); border-radius: 6px 0 0 6px; }
.tile-preview, .tile-hud { background-color: rgba(43,170,255,0.20); border: 2px solid rgba(43,170,255,0.65); border-radius: 6px; }
.tile-preview.snap, .tile-hud.snap { background-color: rgba(54,204,246,0.28); border: 2px solid $cyan; }

/* ---------- On-screen keyboard ---------- */
#keyboard { background-color: rgba(13,39,76,0.95); }
.keyboard-key {
  background-gradient-direction: none; background-color: rgba(255,255,255,0.10);
  border: 1px solid rgba(157,204,252,0.30); border-radius: 6px; color: #eef6ff; }
.keyboard-key:hover, .keyboard-key:checked { background: rgba(43,170,255,0.35); border: 1px solid $cyan; }
.keyboard-key:active { background: $accent; }

/* ---------- Desklets ---------- */
.desklet { color: #eef6ff; }
.desklet-with-borders, .desklet-with-borders-and-header, .desklet-header {
  border: 1px solid rgba(164,209,250,0.28); background-color: $widget; color: #eef6ff; }
.desklet-with-borders { border-radius: ${r_card}px; }
.desklet-with-borders-and-header { border-radius: 0 0 ${r_card}px ${r_card}px; border-top: 0; }
.desklet-header { border-radius: ${r_card}px ${r_card}px 0 0; border-bottom: 0; }
.desklet:highlight, .desklet:highlight-with-borders, .desklet:highlight-with-borders-and-header {
  background-color: rgba(43,170,255,0.35); }
.desklet-drag-placeholder { border: 2px solid $cyan; background-color: rgba(54,204,246,0.25); border-radius: ${r_card}px; }

/* ---------- Cinnamon12 xlets (applets/desklets of this project) ---------- */
.c12-widget {
  background-color: $widget; color: #eef6ff;
  border: 1px solid rgba(164,209,250,0.28); border-radius: ${r_card}px; padding: 12px 16px; }
.c12-widget-title { color: #dff3ff; font-size: 10pt; font-weight: bold; }
.c12-widget-main { color: #ffffff; font-size: 22pt; font-weight: bold; }
.c12-widget-secondary { color: #b9d6f2; font-size: 9pt; }
.c12-widget-divider { background-color: rgba(190,225,255,0.20); height: 1px; }
.c12-popover { color: $text; background-color: $popup; border: 1px solid $popup_border; border-radius: ${r_menu}px; padding: 10px; }
.c12-action { color: $text; background-color: $card; border: 1px solid $entry_border; border-radius: 6px; padding: 7px 10px; }
.c12-action:hover { background-color: $hover_bg; }

/* Cinnamon12 desklets (dark cards in both variants) */
.c12-calendar, .c12-sysmon, .c12-weather { width: 252px; }
.c12-calendar { spacing: 6px; }
.c12-calendar-header { spacing: 4px; }
.c12-calendar-title { color: #ffffff; font-weight: bold; border-radius: 5px; padding: 4px; }
.c12-calendar-title:hover { background-color: rgba(255,255,255,0.10); }
.c12-calendar-nav { color: #cfe6ff; padding: 4px 6px; border-radius: 5px; }
.c12-calendar-nav:hover, .c12-calendar-nav:focus { background-color: rgba(255,255,255,0.12); }
.c12-calendar-grid, .c12-calendar-row { spacing: 2px; }
.c12-calendar-dayname { width: 30px; text-align: center; color: #9fc3e6; font-size: 8.5pt; padding-bottom: 2px; }
.c12-calendar-day { width: 30px; padding: 4px 0; text-align: center; border-radius: 5px; color: #eef6ff; font-size: 9.5pt; }
.c12-calendar-weekend { color: #b9d6f2; }
.c12-calendar-other { color: rgba(185,214,242,0.38); }
.c12-calendar-today { background-color: $accent_fill; color: $on_accent; font-weight: bold; }
.c12-calendar-weeknum { width: 22px; text-align: center; color: rgba(185,214,242,0.5); font-size: 8pt; padding: 4px 0; }
.c12-sysmon { spacing: 10px; }
.c12-sysmon-header, .c12-weather-top { spacing: 8px; }
.c12-sysmon-header-icon, .c12-weather-pin { color: #9fc3e6; }
.c12-sysmon-metric { spacing: 4px; }
.c12-sysmon-top { spacing: 8px; }
.c12-sysmon-label { width: 44px; color: #dff3ff; font-weight: bold; }
.c12-sysmon-value { color: #eef6ff; }
.c12-sysmon-graph { width: 92px; height: 22px; color: #36ccf6; }
.c12-sysmon-ram .c12-sysmon-graph { color: #9a8cff; }
.c12-sysmon-ram .c12-sysmon-bar-fill { background-color: #9a8cff; }
.c12-sysmon-bar { height: 4px; background-color: rgba(255,255,255,0.12); border-radius: 2px; }
.c12-sysmon-bar-fill { height: 4px; border-radius: 2px; background-color: #36ccf6; }
.c12-sysmon-disk .c12-sysmon-bar-fill { background-color: #42d5ad; }
.c12-sysmon-net { spacing: 10px; }
.c12-sysmon-rate { color: #b9d6f2; font-size: 9pt; }
.c12-weather { spacing: 8px; }
.c12-weather-place { color: #dff3ff; font-weight: bold; }
.c12-weather-now { spacing: 12px; }
.c12-weather-range { color: #b9d6f2; font-size: 9pt; }
.c12-weather-forecast { spacing: 4px; padding-top: 8px; border-top: 1px solid rgba(190,225,255,0.18); }
.c12-weather-day { spacing: 3px; }
.c12-weather-day-name { color: #9fc3e6; font-size: 8.5pt; }
.c12-weather-day-temp { color: #eef6ff; font-size: 9pt; }
.c12-weather-footer { color: rgba(185,214,242,0.65); font-size: 7.5pt; }

/* Cinnamon12 Start (c12-start@cinnamon12.local) */
.c12-launcher-menu .popup-menu-content { padding: 0; }
.c12-launcher { padding: 14px 14px 0 14px; spacing: 12px; color: $text; }
.c12-launcher-search {
  color: $text; caret-color: $accent; selected-color: $on_accent; selection-background-color: $accent_fill;
  background-color: $entry; border: 1px solid $entry_border; border-radius: 6px; padding: 8px 10px; }
.c12-launcher-search:focus { border: 1px solid $accent; box-shadow: inset 0 0 0 1px $accent; }
.c12-launcher-search StLabel.hint-text { color: $muted; }
.c12-launcher-search-icon { icon-size: 16px; color: $muted; padding-right: 6px; }
.c12-launcher-body { spacing: 12px; }
.c12-launcher-categories { width: 196px; padding-right: 10px; border-right: 1px solid $popup_border; }
.c12-launcher-category { color: $text; border-radius: 5px; padding: 6px 10px; margin-bottom: 1px; }
.c12-launcher-category-box { spacing: 10px; }
.c12-launcher-category:hover, .c12-launcher-category:focus { background-color: $hover_bg; }
.c12-launcher-category:checked { background-color: $accent_fill; color: $on_accent; }
.c12-launcher-content { padding-right: 4px; }
.c12-launcher-section-title { font-weight: bold; color: $text; padding: 2px 4px 8px 4px; }
.c12-launcher-grid-row { spacing: 4px; padding-bottom: 6px; }
.c12-launcher-tile { width: 82px; padding: 8px 2px 6px 2px; border-radius: 6px; color: $text; }
.c12-launcher-tile:hover, .c12-launcher-tile:focus { background-color: $hover_bg; }
.c12-launcher-tile-box { spacing: 6px; }
.c12-launcher-tile-label { font-size: 9pt; text-align: center; max-width: 78px; }
.c12-launcher-row { border-radius: 6px; padding: 6px 8px; color: $text; }
.c12-launcher-row:hover, .c12-launcher-row:focus { background-color: $hover_bg; }
.c12-launcher-row-box { spacing: 12px; }
.c12-launcher-row-title { color: $text; }
.c12-launcher-row-subtitle { color: $muted; font-size: 8.5pt; }
.c12-launcher-empty { color: $muted; padding: 8px 4px; }
.c12-launcher-footer {
  border-top: 1px solid $popup_border; padding: 10px 0 12px 0; spacing: 4px; }
.c12-launcher-user { border-radius: 6px; padding: 4px 10px 4px 4px; color: $text; }
.c12-launcher-user:hover, .c12-launcher-user:focus { background-color: $hover_bg; }
.c12-launcher-user-box { spacing: 10px; }
.c12-launcher-avatar { border-radius: 14px; color: $accent_fg; }
.c12-launcher-session { border-radius: 6px; padding: 8px; color: $text; }
.c12-launcher-session:hover, .c12-launcher-session:focus { background-color: $hover_bg; color: $accent_fg; }
.c12-launcher-session-icon { color: $text; }

/* Cinnamon12 Quick Settings (c12-quicksettings@cinnamon12.local) */
.c12-qs-menu .popup-menu-content { padding: 0; }
.c12-qs { width: 340px; padding: 14px; spacing: 12px; color: $text; }
.c12-qs-header { spacing: 8px; padding: 0 2px; }
.c12-qs-date { color: $text; font-weight: bold; }
.c12-qs-time { color: $text; font-weight: bold; padding-right: 4px; }
.c12-qs-grid { spacing: 8px; }
.c12-qs-row { spacing: 8px; }
.c12-qs-tile, .c12-qs-tile-spacer { width: 162px; }
.c12-qs-tile { border-radius: 6px; background-color: $card; border: 1px solid $entry_border; }
.c12-qs-tile:checked { background-color: $accent_fill; border: 1px solid $accent_fill; }
.c12-qs-tile:insensitive { opacity: 0.55; }
.c12-qs-tile-main { padding: 10px 10px 9px 12px; border-radius: 6px; color: $text; }
.c12-qs-tile-main:hover, .c12-qs-tile-main:focus { background-color: $hover_bg; }
.c12-qs-tile:checked .c12-qs-tile-main { color: $on_accent; }
.c12-qs-tile:checked .c12-qs-tile-main:hover, .c12-qs-tile:checked .c12-qs-tile-main:focus { background-color: rgba(255,255,255,0.14); }
.c12-qs-tile-box { spacing: 3px; }
.c12-qs-tile-icon { color: $accent_fg; }
.c12-qs-tile:checked .c12-qs-tile-icon { color: $on_accent; }
.c12-qs-tile-title { font-weight: bold; }
.c12-qs-tile-subtitle { font-size: 8.5pt; color: $muted; }
.c12-qs-tile:checked .c12-qs-tile-subtitle { color: $on_accent_muted; }
.c12-qs-tile-arrow { padding: 0 8px; border-radius: 0 6px 6px 0; color: $muted; border-left: 1px solid $entry_border; }
.c12-qs-tile:checked .c12-qs-tile-arrow { color: $on_accent; border-left: 1px solid $on_accent_line; }
.c12-qs-tile-arrow:hover, .c12-qs-tile-arrow:focus { background-color: $hover_bg; }
.c12-qs-tile:checked .c12-qs-tile-arrow:hover { background-color: rgba(255,255,255,0.14); }
.c12-qs-sliders { spacing: 6px; padding: 2px 0; }
.c12-qs-slider-row { spacing: 8px; }
.c12-qs-slider-icon { padding: 6px; border-radius: 6px; color: $text; }
.c12-qs-slider-icon:hover, .c12-qs-slider-icon:focus { background-color: $hover_bg; color: $accent_fg; }
.c12-qs-slider { height: 20px; -slider-height: 4px; -slider-background-color: $line;
  -slider-active-background-color: $accent; -slider-border-width: 0; -slider-handle-radius: 8px; }
.c12-qs-slider-value { width: 44px; text-align: right; color: $muted; font-size: 9pt; }
.c12-qs-actions { spacing: 8px; padding-top: 8px; border-top: 1px solid $popup_border; }
.c12-qs-action { padding: 9px 14px; border-radius: 6px; color: $text; background-color: $card; border: 1px solid $entry_border; }
.c12-qs-action:hover, .c12-qs-action:focus { background-color: $hover_bg; }
.c12-qs-action:checked { background-color: $accent_fill; border: 1px solid $accent_fill; color: $on_accent; }
.c12-qs-action-icon { color: $text; }
.c12-qs-action:checked .c12-qs-action-icon { color: $on_accent; }
.c12-launcher-session:hover .c12-launcher-session-icon, .c12-launcher-session:focus .c12-launcher-session-icon { color: $accent_fg; }

.cinnamon-link { color: $accent_fg; }
.cinnamon-link:hover { color: $hover; }
''')

# ======================================================================================
# GTK3 (also styles Muffin server-side title bars)
GTK3 = Template(r'''/* Cinnamon12 Studio | $variant | GTK 3 theme.
 * Generated by scripts/generate-themes.py from design/tokens.json - do not edit by hand.
 * Base: Adwaita compiled into libgtk-3; Cinnamon12 overrides follow.
 * Muffin (Cinnamon 6) draws server-side title bars with this CSS too. */
@import url("resource:///org/gtk/libgtk/theme/$gtk_base");

@define-color theme_bg_color $window;
@define-color theme_fg_color $text;
@define-color theme_base_color $card;
@define-color theme_text_color $text;
@define-color theme_selected_bg_color $accent_fill;
@define-color theme_selected_fg_color $on_accent;
@define-color insensitive_bg_color $side;
@define-color insensitive_fg_color $muted;
@define-color insensitive_base_color $side;
@define-color theme_unfocused_bg_color $window;
@define-color theme_unfocused_fg_color $text;
@define-color theme_unfocused_base_color $card;
@define-color theme_unfocused_text_color $text;
@define-color theme_unfocused_selected_bg_color $accent_fill;
@define-color theme_unfocused_selected_fg_color $on_accent;
@define-color borders $line;
@define-color unfocused_borders $line;
@define-color warning_color $warning;
@define-color error_color $danger;
@define-color success_color $success;
@define-color accent_color $accent;
@define-color accent_bg_color $accent_fill;
@define-color accent_fg_color $on_accent;
@define-color window_bg_color $window;
@define-color window_fg_color $text;
@define-color view_bg_color $card;
@define-color view_fg_color $text;
@define-color headerbar_bg_color $titlebar;
@define-color headerbar_fg_color $text;
@define-color sidebar_bg_color $side;
@define-color card_bg_color $card;
@define-color popover_bg_color $popup_solid;
@define-color wm_title $text;
@define-color wm_unfocused_title $muted;
@define-color wm_bg $titlebar;
@define-color wm_bg_unfocused $titlebar_backdrop;

*:link, link, button.link:link { color: $accent_fg; }
*:visited, link:visited { color: $hover; }

/* ---------- windows & surfaces ---------- */
window.background, .background, dialog, messagedialog.background { background-color: $window; color: $text; }
.view, iconview, treeview.view, textview text, list, listview, flowbox, viewport.frame, .content-view {
  background-color: $card; color: $text; }
.view:selected, iconview:selected, treeview.view:selected, .view text selection, textview text selection,
flowboxchild:selected, row:selected, label selection, entry selection {
  background-color: $accent_fill; color: $on_accent; }
.view:hover, treeview.view:hover { background-color: $hover_bg; }
.nemo-window .view:selected, .nemo-window iconview:selected,
.nemo-window .view:selected:focus, .nemo-window iconview:selected:focus {
  background-color: $item_active; color: $text; border-radius: 5px; }
.nemo-window .view:hover, .nemo-window iconview:hover { background-color: $subtle_bg; }
.nemo-window .nemo-window-pane widget.entry { border-radius: 6px; }
/* icon view: Nemo's canvas paints only the label box; selected = light tile with an accent
 * ring (the canvas has no hover background, Nemo just brightens the icon) */
.nemo-window .nemo-canvas-item:selected, .nemo-window .nemo-canvas-item:selected:focus {
  background-color: $fm_tile; color: $text; border-radius: 8px; box-shadow: inset 0 0 0 1px $fm_tile_ring; }
.nemo-window toolbar button:checked, .nemo-window .primary-toolbar button:checked {
  background-color: $fm_checked; color: $text; border: 1px solid $fm_checked_ring; }
treeview.view header button { background-image: none; background-color: $card; color: $muted;
  border-color: $line; box-shadow: none; }
treeview.view header button:hover { background-color: $hover_bg; color: $text; }
separator { background-color: $line; }
frame > border, .frame { border-color: $line; border-radius: 6px; }
scrolledwindow undershoot, scrolledwindow overshoot { background-image: none; background: none; }

/* ---------- title bars: CSD headerbars and Muffin server-side decorations ---------- */
headerbar, .titlebar:not(headerbar), headerbar.titlebar.default-decoration,
window.ssd headerbar.titlebar, .titlebar {
  background-image: linear-gradient(to right, $titlebar, $titlebar_hi); background-color: $titlebar; color: $text;
  border-color: $line; box-shadow: inset 0 -1px $titlebar_edge; text-shadow: none; }
headerbar:backdrop, .titlebar:backdrop, headerbar.titlebar.default-decoration:backdrop {
  background-image: none; background-color: $titlebar_backdrop; color: $muted; box-shadow: inset 0 -1px $titlebar_edge; }
headerbar.titlebar.default-decoration { min-height: 30px; padding: 4px 8px; }
.titlebar:not(headerbar), headerbar.titlebar, window:not(.tiled):not(.maximized):not(.fullscreen) headerbar.titlebar,
window.csd > .titlebar:not(headerbar) { border-radius: ${r_window}px ${r_window}px 0 0; }
window.maximized headerbar.titlebar, window.tiled headerbar.titlebar, window.fullscreen headerbar.titlebar { border-radius: 0; }
headerbar .title, .titlebar .title { font-weight: bold; color: $text; }
headerbar .title:backdrop, .titlebar .title:backdrop { color: $muted; }
headerbar .subtitle { color: $muted; }
window.csd, window.csd.background { border-radius: ${r_window}px; }
decoration { border-radius: ${r_window}px ${r_window}px 0 0; box-shadow: 0 4px 16px $shadow_gtk, 0 0 0 1px rgba(10,40,80,0.18); }
decoration:backdrop { box-shadow: 0 2px 8px $shadow_gtk, 0 0 0 1px rgba(10,40,80,0.14); }
window.ssd decoration { border-radius: ${r_window}px ${r_window}px 0 0; box-shadow: 0 0 0 1px rgba(10,40,80,0.20); }
window.maximized decoration, window.tiled decoration { border-radius: 0; }

button.titlebutton {
  background-image: none; background-color: transparent; border: none; box-shadow: none;
  color: $text; border-radius: 4px; min-width: 22px; min-height: 22px; padding: 2px 8px; margin: 0 1px; }
button.titlebutton:hover { background-color: $hover_bg; }
button.titlebutton:active { background-color: $item_active; }
button.titlebutton.close:hover { background-color: $danger; color: #ffffff; }
button.titlebutton.close:active { background-color: shade($danger, 0.85); color: #ffffff; }
button.titlebutton:backdrop { color: $muted; }

/* ---------- buttons ---------- */
button {
  background-image: none; background-color: $card; color: $text;
  border: 1px solid $line; border-radius: ${r_button}px; box-shadow: none; text-shadow: none; -gtk-icon-shadow: none; }
button:hover { background-image: none; background-color: $hover_bg; border-color: $line; }
button:active, button:checked { background-image: none; background-color: $item_active; color: $text; border-color: $accent; }
button:disabled { background-image: none; background-color: $side; color: $muted; border-color: $line; }
button:backdrop { background-image: none; background-color: $card; color: $muted; border-color: $line; }
button:backdrop:checked { background-color: $item_active; color: $text; }
button.flat, button.flat:backdrop, button.image-button.flat, .toolbar button, headerbar button.flat, .path-bar button.flat {
  background-color: transparent; border-color: transparent; }
button.flat:hover, headerbar button.flat:hover, .toolbar button:hover { background-color: $hover_bg; border-color: transparent; }
button.flat:checked, button.flat:active { background-color: $item_active; border-color: transparent; }
button.suggested-action, button.default:not(.flat) {
  background-image: none; background-color: $accent_fill; color: $on_accent; border-color: $accent; }
button.suggested-action:hover { background-color: $hover; border-color: $hover; }
button.suggested-action:disabled { background-color: $side; color: $muted; border-color: $line; }
button.destructive-action { background-image: none; background-color: $danger; color: #ffffff; border-color: $danger; }
button.destructive-action:hover { background-color: shade($danger, 0.9); }
button:focus { outline-color: alpha($accent, 0.6); outline-width: 1px; outline-offset: -3px; }
.linked > button { border-radius: 0; }
.linked > button:first-child { border-top-left-radius: ${r_button}px; border-bottom-left-radius: ${r_button}px; }
.linked > button:last-child { border-top-right-radius: ${r_button}px; border-bottom-right-radius: ${r_button}px; }
.linked > button:only-child { border-radius: ${r_button}px; }

/* ---------- entries / combos / spin ---------- */
entry, spinbutton:not(.vertical), .entry {
  background-image: none; background-color: $entry; color: $text; caret-color: $accent;
  border: 1px solid $entry_border; border-radius: ${r_button}px; box-shadow: none; }
entry:focus, spinbutton:focus:not(.vertical) { border-color: $accent; box-shadow: inset 0 0 0 1px $accent; }
entry:disabled { background-color: $side; color: $muted; }
entry:backdrop { background-color: $entry; border-color: $entry_border; }
entry image { color: $muted; }
entry progress { border-color: $accent; }
combobox button.combo, combobox box.linked > button.combo { background-color: $card; }

/* ---------- sidebars (Nemo places, settings) ---------- */
.sidebar, placessidebar, placessidebar list, .nemo-places-sidebar, .nemo-places-sidebar treeview.view,
.nemo-window .sidebar, .nemo-window .sidebar .view, stacksidebar list {
  background-color: $side; color: $text; border-color: $line; }
.nemo-window .sidebar .view:selected, .nemo-places-sidebar treeview.view:selected,
placessidebar row:selected, stacksidebar row:selected, .sidebar row:selected {
  background-color: $accent_fill; color: $on_accent; border-radius: 5px; }
.nemo-window .sidebar .view:hover, placessidebar row:hover, .sidebar row:hover { background-color: $hover_bg; }
placessidebar row:selected:backdrop { background-color: $item_active; color: $text; }
.nemo-window .sidebar .view:selected:backdrop { background-color: $accent_fill; color: $on_accent; }
/* Nemo places sidebar is a GtkTreeView: the selection can't be rounded (it is painted
 * per column), so it stays a full-width band and rows get more air */
.nemo-places-sidebar { padding: 6px 0; }
.nemo-window .sidebar .view, .nemo-places-sidebar treeview.view { padding-top: 5px; padding-bottom: 5px; }
placessidebar row { border-radius: 5px; margin: 1px 4px; }
/* GtkTreeView paints the selection per cell (expander, icon, name, eject), so a radius
 * there draws a chain of separate bubbles: keep tree rows square. GtkListBox rows
 * (placessidebar row) and icon view items stay rounded. */
.nemo-window treeview.view:selected, .nemo-window .sidebar .view:selected,
.nemo-window .sidebar .view:selected:backdrop, .nemo-places-sidebar treeview.view:selected,
treeview.view:selected { border-radius: 0; }
/* hover rules come later than :selected and would paint the light hover background
 * under the selection's white text; a hovered selected row stays selected */
.view:selected:hover, treeview.view:selected:hover, row:selected:hover,
.nemo-window .sidebar .view:selected:hover, .nemo-places-sidebar treeview.view:selected:hover,
placessidebar row:selected:hover, .sidebar row:selected:hover { background-color: $accent_fill; color: $on_accent; }
.nemo-window .view:selected:hover, .nemo-window iconview:selected:hover,
.nemo-window treeview.view:selected:hover { background-color: $item_active; color: $text; }
.nemo-window .sidebar .view:selected:hover { background-color: $accent_fill; color: $on_accent; }
.nemo-window toolbar, .nemo-window .primary-toolbar, .primary-toolbar {
  background-image: none; background-color: $toolbar; border-color: $toolbar_line; box-shadow: inset 0 -1px $toolbar_line; }
.nemo-window statusbar, statusbar { background-color: $window; color: $muted; border-top: 1px solid $line; }
/* Nemo surfaces and selection colours (reference images, light and dark) */
.nemo-window .view, .nemo-window iconview, .nemo-window treeview.view, .nemo-window .nemo-canvas-item,
.nemo-window treeview.view header button { background-color: $fm_view; }
.nemo-window .sidebar, .nemo-window .sidebar .view, .nemo-places-sidebar, .nemo-places-sidebar treeview.view {
  background-color: $fm_side; }
.nemo-window statusbar { background-color: $fm_status; border-top: 1px solid $fm_line; }
/* the bottom bar's sidebar buttons and zoom slider sit on the window background */
window.nemo-window.background, .nemo-window statusbar ~ * { background-color: $fm_status; }
.nemo-window paned > separator { background-color: $fm_line; }
.nemo-window .sidebar .view:hover, .nemo-places-sidebar treeview.view:hover { background-color: $fm_hover; }
.nemo-window .sidebar .view:selected, .nemo-places-sidebar treeview.view:selected,
.nemo-window .sidebar .view:selected:hover, .nemo-places-sidebar treeview.view:selected:hover,
.nemo-window .sidebar .view:selected:backdrop { background-color: $fm_sel; color: $fm_sel_fg; }
.nemo-window .nemo-inactive-pane .view, .nemo-window .nemo-inactive-pane iconview { background-color: $window; }
.path-bar button { border-radius: 5px; }
.path-bar button:checked { background-color: $item_active; border-color: transparent; font-weight: bold; }
/* Nemo breadcrumb: the path bar container draws nothing, so its buttons form one rounded
 * box (sliders are the first/last children) and each folder gets a trailing chevron */
.nemo-window .path-bar button, .nemo-window .path-bar button:hover, .nemo-window .path-bar button:checked,
.nemo-window .path-bar button:backdrop, .nemo-window .path-bar button:backdrop:checked, .nemo-window .path-bar button:disabled {
  background-color: $crumb_bg; color: $text; border: 1px solid $crumb_border; border-left-width: 0; border-right-width: 0;
  border-radius: 0; box-shadow: inset 0 1px $crumb_hi; min-height: 30px; text-shadow: none;
  background-image: url("$chevron"); background-repeat: no-repeat; background-position: right center;
  padding: 0 22px 0 8px; }
.nemo-window .path-bar button:hover { background-color: $crumb_hover; }
.nemo-window .path-bar button:checked { font-weight: bold; }
.nemo-window .path-bar button:first-child, .nemo-window .path-bar button:last-child {
  background-image: none; padding: 0 4px; color: $muted; }
.nemo-window .path-bar button:first-child { border-left-width: 1px; border-radius: ${r_button}px 0 0 ${r_button}px; }
.nemo-window .path-bar button:last-child { border-right-width: 1px; border-radius: 0 ${r_button}px ${r_button}px 0; }

/* ---------- menus / popovers / tooltips ---------- */
menu, .menu, .context-menu, popover.menu, popover, popover.background {
  background-color: $popup_solid; color: $text; border: 1px solid $popup_border; border-radius: ${r_menu}px; }
menu, .menu, .context-menu { padding: 4px 0; }
menu menuitem, .menu menuitem, .context-menu menuitem { color: $text; padding: 5px 12px; border-radius: 0; }
menu menuitem:hover, .menu menuitem:hover, .context-menu menuitem:hover, modelbutton.flat:hover, popover modelbutton:hover {
  background-color: $accent_fill; color: $on_accent; }
menu menuitem:disabled, .menu menuitem:disabled { color: $muted; }
menu separator, popover separator { background-color: $line; }
menubar { background-color: $window; box-shadow: inset 0 -1px $line; }
menubar > menuitem:hover { background-color: $hover_bg; color: $text; box-shadow: inset 0 -2px $accent; }
tooltip, tooltip.background, .tooltip {
  background-color: $tooltip_bg; color: $tooltip_fg; border-radius: 5px; border: none; box-shadow: none; }
tooltip * { color: $tooltip_fg; }

/* ---------- notebooks ---------- */
notebook > header { background-color: $side; border-color: $line; }
notebook > header tab { color: $muted; border-radius: 5px 5px 0 0; }
notebook > header tab:hover { background-color: $hover_bg; color: $text; box-shadow: none; }
notebook > header tab:checked { color: $text; background-color: $card; box-shadow: inset 0 -2px $accent; }
notebook > header.top > tabs > tab:checked { box-shadow: inset 0 -2px $accent; }
notebook > stack:not(:only-child) { background-color: $card; }

/* ---------- check / radio / switch ---------- */
check, radio { background-image: none; background-color: $entry; border: 1px solid $entry_border; color: #ffffff; }
check { border-radius: 4px; }
check:hover, radio:hover { border-color: $accent; }
check:checked, check:indeterminate, radio:checked, radio:indeterminate {
  background-image: none; background-color: $accent_fill; border-color: $accent; color: $on_accent; }
check:disabled, radio:disabled { background-color: $side; border-color: $line; }
menu menuitem check, menu menuitem radio, .menu menuitem check, .menu menuitem radio { border-color: $entry_border; }
switch { background-image: none; background-color: $line; border: 1px solid $line; border-radius: 14px; }
switch:checked { background-color: $accent; border-color: $accent; }
switch slider { background-image: none; background-color: #ffffff; border: 1px solid $line; border-radius: 50%; box-shadow: none; }
switch:checked slider { border-color: $accent; }
switch:disabled { background-color: $side; }

/* ---------- scales / progress / level ---------- */
scale trough, progressbar trough, levelbar trough { background-image: none; background-color: $line; border: none; border-radius: 4px; }
scale highlight, progressbar progress, levelbar block.filled { background-image: none; background-color: $accent; border: none; border-radius: 4px; }
scale slider { background-image: none; background-color: #ffffff; border: 2px solid $accent; border-radius: 50%; box-shadow: none; }
scale slider:hover { background-color: $hover_bg; }
levelbar block.low { background-color: $warning; }
levelbar block.full, levelbar block.high { background-color: $success; }

/* ---------- scrollbars ---------- */
scrollbar { background-color: transparent; border-color: transparent; }
scrollbar slider { background-color: $scroll; border-radius: 6px; min-width: 6px; min-height: 6px; border: 2px solid transparent; }
scrollbar slider:hover { background-color: alpha($accent, 0.75); }
scrollbar slider:active { background-color: $accent; }
scrollbar.overlay-indicator:not(.dragging):not(.hovering) slider { background-color: $scroll; }

/* ---------- info bars / misc ---------- */
infobar.info > revealer > box, infobar.question > revealer > box { background-color: $item_active; color: $text; }
infobar.warning > revealer > box { background-color: alpha($warning, 0.25); color: $text; }
infobar.error > revealer > box { background-color: alpha($danger, 0.25); color: $text; }
.app-notification { background-color: $tooltip_bg; color: $tooltip_fg; border-radius: 0 0 6px 6px; }
calendar { color: $text; border-color: $line; }
calendar:selected { background-color: $accent_fill; color: $on_accent; border-radius: 4px; }
calendar.header { background-color: $side; border-color: $line; }
toolbar, .inline-toolbar { background-color: $window; }
.dim-label, label.separator { color: $muted; opacity: 1; }
.cinnamon-settings-window .sidebar, .cs-category-view { background-color: $side; }
''')

# ======================================================================================
# GTK4 (non-libadwaita GTK4 apps only)
GTK4 = Template(r'''/* Cinnamon12 Studio | $variant | GTK 4 theme (non-libadwaita apps only).
 * Generated by scripts/generate-themes.py - do not edit by hand.
 * libadwaita applications ignore user themes by design. */
@import url("resource:///org/gtk/libgtk/theme/$gtk4_base");

@define-color accent_color $accent;
@define-color accent_bg_color $accent_fill;
@define-color accent_fg_color $on_accent;
@define-color window_bg_color $window;
@define-color window_fg_color $text;
@define-color view_bg_color $card;
@define-color view_fg_color $text;
@define-color headerbar_bg_color $titlebar;
@define-color headerbar_fg_color $text;
@define-color headerbar_backdrop_color $titlebar_backdrop;
@define-color sidebar_bg_color $side;
@define-color sidebar_fg_color $text;
@define-color card_bg_color $card;
@define-color card_fg_color $text;
@define-color popover_bg_color $popup_solid;
@define-color popover_fg_color $text;
@define-color dialog_bg_color $window;
@define-color dialog_fg_color $text;
@define-color theme_bg_color $window;
@define-color theme_fg_color $text;
@define-color theme_base_color $card;
@define-color theme_text_color $text;
@define-color theme_selected_bg_color $accent_fill;
@define-color theme_selected_fg_color $on_accent;
@define-color borders $line;
@define-color warning_color $warning;
@define-color error_color $danger;
@define-color success_color $success;

window, .background { background-color: $window; color: $text; }
headerbar { background-image: none; background-color: $titlebar; color: $text; box-shadow: inset 0 -1px $line; }
headerbar:backdrop { background-color: $titlebar_backdrop; }
window.csd { border-radius: ${r_window}px; }
button { border-radius: ${r_button}px; }
button.suggested-action { background-color: $accent_fill; color: $on_accent; }
entry { border-radius: ${r_button}px; }
entry:focus-within { outline-color: alpha($accent, 0.6); }
popover > contents { background-color: $popup_solid; color: $text; border-radius: ${r_menu}px; }
.view:selected, row:selected { background-color: alpha($accent, 0.25); }
switch:checked, scale highlight, progressbar progress { background-color: $accent; }
.sidebar, .navigation-sidebar { background-color: $side; }
''')


# ======================================================================================
# Small recolored shell assets (originals drawn here, replacing the stock grey ones)
def svg_assets(p):
    acc, line, entry, text, muted = p['accent_fill'], p['line'], p['entry'], p['text'], p['muted']
    on = p['on_accent']
    border = p['entry_border']
    m = re.match(r'rgba\((\d+),(\d+),(\d+),([\d.]+)\)', p['panel'].replace(' ', ''))
    pfill, pop = '#%02x%02x%02x' % tuple(int(v) for v in m.groups()[:3]), m.group(4)
    def svg(body):
        return f'<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">{body}</svg>'
    # Pills: 4 px inset on the cross axis. (fill, opacity, indicator?)
    states = {'hover': ('#c2e0ff', 0.14, False), 'running': ('#c2e0ff', 0.08, False),
              'focus': ('#2baaff', 0.28, True), 'attention': ('#f17189', 0.55, False)}
    panels = {}
    # "Show desktop" strip: hairline separator at rest, whole strip lit on hover.
    def cap(w, h, body):
        return f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">{body}</svg>'
    # Solid strip over the whole click area, a little lighter than the bar; stronger on hover.
    strip = '<rect width="{w}" height="{h}" fill="#c2e0ff" fill-opacity="{o}"/>'
    panels['cap-h.svg'] = cap(14, 48, strip.format(w=14, h=48, o=0.10))
    panels['cap-h-hover.svg'] = cap(14, 48, strip.format(w=14, h=48, o=0.22))
    panels['cap-v.svg'] = cap(48, 14, strip.format(w=48, h=14, o=0.10))
    panels['cap-v-hover.svg'] = cap(48, 14, strip.format(w=48, h=14, o=0.22))
    for name, (col, op, ind) in states.items():
        line_h = '<rect x="16" y="56" width="32" height="3" rx="1.5" fill="#36ccf6"/>' if ind else ''
        line_v = '<rect x="56" y="16" width="3" height="32" rx="1.5" fill="#36ccf6"/>' if ind else ''
        panels[f'pill-h-{name}.svg'] = svg(f'<rect x="0" y="4" width="64" height="56" rx="8" fill="{col}" fill-opacity="{op}"/>{line_h}')
        panels[f'pill-v-{name}.svg'] = svg(f'<rect x="4" y="0" width="56" height="64" rx="8" fill="{col}" fill-opacity="{op}"/>{line_v}')
    # smaller pills (32 px: 8 px inset) for applets at the ends of the bar
    panels['pill-h-hover-sm.svg'] = svg('<rect x="0" y="8" width="64" height="48" rx="7" fill="#c2e0ff" fill-opacity="0.14"/>')
    panels['pill-v-hover-sm.svg'] = svg('<rect x="8" y="0" width="48" height="64" rx="7" fill="#c2e0ff" fill-opacity="0.14"/>')
    return {
        **panels,
        'toggle-on.svg': f'''<svg xmlns="http://www.w3.org/2000/svg" width="64" height="22" viewBox="0 0 64 22">
<rect x="14" y="2" width="36" height="18" rx="9" fill="{acc}"/><circle cx="41" cy="11" r="6.5" fill="{on}"/></svg>''',
        'toggle-off.svg': f'''<svg xmlns="http://www.w3.org/2000/svg" width="64" height="22" viewBox="0 0 64 22">
<rect x="14.5" y="2.5" width="35" height="17" rx="8.5" fill="{entry}" stroke="{muted}" stroke-width="1"/><circle cx="23" cy="11" r="5.5" fill="{muted}"/></svg>''',
        'checkbox-on.svg': f'''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
<rect x="1" y="1" width="14" height="14" rx="3.5" fill="{acc}"/><path d="M4.5 8.2l2.3 2.3 4.7-5" fill="none" stroke="{on}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>''',
        'checkbox-off.svg': f'''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
<rect x="1.5" y="1.5" width="13" height="13" rx="3" fill="{entry}" stroke="{border}" stroke-width="1"/></svg>''',
        'radio-on.svg': f'''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
<circle cx="8" cy="8" r="7" fill="{acc}"/><circle cx="8" cy="8" r="3" fill="{on}"/></svg>''',
        'radio-off.svg': f'''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
<circle cx="8" cy="8" r="6.5" fill="{entry}" stroke="{border}" stroke-width="1"/></svg>''',
        'arrow-left.svg': f'''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
<path d="M10 3.5L5.5 8l4.5 4.5" fill="none" stroke="{text}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>''',
        'arrow-right.svg': f'''<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">
<path d="M6 3.5L10.5 8 6 12.5" fill="none" stroke="{text}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg>''',
    }


def thumbnail(variant, out_paths):
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return
    wallpaper = 'c12-arctic' if variant == 'light' else 'c12-midnight'
    src = ROOT / 'assets' / 'wallpapers' / f'{wallpaper}-1920x1080.jpg'
    if not src.exists():
        return
    im = Image.open(src).resize((420, 236))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((13, 195, 405, 228), radius=7, fill='#12345b')
    for i in range(6):
        x = 152 + 29 * i
        d.rounded_rectangle((x, 200, x + 21, 221), radius=4,
                            fill=['#38bafd', '#538dfe', '#786afc', '#3daac3', '#f8a65b', '#8dceff'][i])
    for o in out_paths:
        o.parent.mkdir(parents=True, exist_ok=True)
        im.save(o)


def main():
    for variant in ('light', 'dark'):
        p = palette(variant)
        name = 'Cinnamon12-' + variant.capitalize()
        base = ROOT / 'themes' / name
        (base / 'cinnamon' / 'assets').mkdir(parents=True, exist_ok=True)
        (base / 'gtk-3.0' / 'assets').mkdir(parents=True, exist_ok=True)
        for v in ('light', 'dark'):
            (base / 'gtk-3.0' / 'assets' / ('pathbar-chevron-%s.svg' % v)).write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 16 16">'
                '<path d="M6 3.5 10.5 8 6 12.5" fill="none" stroke="%s" stroke-width="1.6" '
                'stroke-linecap="round" stroke-linejoin="round"/></svg>\n' % palette(v)['text'])
        (base / 'gtk-4.0').mkdir(parents=True, exist_ok=True)
        (base / 'cinnamon' / 'cinnamon.css').write_text(CINNAMON.substitute(p))
        for fname, svg in svg_assets(p).items():
            (base / 'cinnamon' / 'assets' / fname).write_text(svg + '\n')
        (base / 'gtk-3.0' / 'gtk.css').write_text(GTK3.substitute(p))
        (base / 'gtk-3.0' / 'gtk-dark.css').write_text(
            GTK3.substitute(palette('dark')) if variant == 'light' else GTK3.substitute(p))
        (base / 'gtk-4.0' / 'gtk.css').write_text(GTK4.substitute(p))
        (base / 'gtk-4.0' / 'gtk-dark.css').write_text(GTK4.substitute(palette('dark')))
        (base / 'index.theme').write_text(
            '[Desktop Entry]\nType=X-GNOME-Metatheme\nName=%s\n'
            'Comment=Cinnamon12 Studio theme (%s): blue accents, small radius\nEncoding=UTF-8\n\n'
            '[X-GNOME-Metatheme]\nGtkTheme=%s\nIconTheme=Cinnamon12-Icons\nCursorTheme=Yaru\n'
            % (name, variant, name))
        thumbs = [base / 'cinnamon' / 'thumbnail.png', base / 'gtk-3.0' / 'thumbnail.png']
        if not all(t.exists() for t in thumbs):
            thumbnail(variant, thumbs)
        print('generated', name)


if __name__ == '__main__':
    main()
