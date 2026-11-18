/* Cinnamon12 | Quick Settings - Cinnamon 6.0.x
 *
 * Every control reflects and changes REAL state, and is hidden when its backend is
 * missing (no decorative toggles):
 *   Wi-Fi          NetworkManager (libnm: WirelessEnabled, active connection)
 *   Bluetooth      BlueZ org.bluez.Adapter1.Powered (system bus)
 *   Dark mode      switches Cinnamon12-Light <-> Cinnamon12-Dark (shell + GTK) and
 *                  org.x.apps.portal color-scheme; only when a Cinnamon12 theme is active
 *   Night light    org.cinnamon.settings-daemon.plugins.color night-light-enabled (6.2+)
 *   Do not disturb org.cinnamon.desktop.notifications display-notifications
 *   Power mode     power-profiles-daemon (net.hadess / org.freedesktop.UPower.PowerProfiles)
 *   Volume         Cvc mixer default sink (same library as the sound applet)
 *   Brightness     org.cinnamon.SettingsDaemon.Power.Screen
 *   Airplane mode  turns Wi-Fi/WWAN (NetworkManager) and Bluetooth (BlueZ) off and
 *                  restores their previous state; there is no rfkill daemon in Cinnamon 6.0
 * Signals/D-Bus notifications are used instead of polling. Nothing is logged about
 * networks (no SSIDs in logs).
 */
const Applet = imports.ui.applet;
const PopupMenu = imports.ui.popupMenu;
const Main = imports.ui.main;
const Slider = imports.ui.slider;
const Util = imports.misc.util;
const St = imports.gi.St;
const Clutter = imports.gi.Clutter;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const Cinnamon = imports.gi.Cinnamon;
const Gettext = imports.gettext;
const Mainloop = imports.mainloop;

const UUID = 'c12-quicksettings@cinnamon12.local';

function _(str) {
    const own = Gettext.dgettext(UUID, str);
    if (own !== str) return own;
    return Gettext.dgettext('cinnamon', str);
}

function settingsHas(schemaId, key) {
    const src = Gio.SettingsSchemaSource.get_default();
    const schema = src.lookup(schemaId, true);
    return !!(schema && schema.has_key(key));
}

function findProgram(...names) {
    for (const n of names) if (GLib.find_program_in_path(n)) return n;
    return null;
}

/* Popup that opens aligned with the right edge of the button (like the reference). */
class C12QSMenu extends Applet.AppletPopupMenu {
    _calculatePosition() {
        let [x, y] = super._calculatePosition();
        if (this._orientation !== St.Side.TOP && this._orientation !== St.Side.BOTTOM) return [x, y];
        const src = Cinnamon.util_get_transformed_allocation(this.sourceActor);
        const [, , natWidth] = this.actor.get_preferred_size();
        const monitor = Main.layoutManager.findMonitorForActor(this.sourceActor);
        const rtl = Clutter.get_default_text_direction() === Clutter.TextDirection.RTL;
        x = rtl ? src.x1 : src.x2 - natWidth;
        x = Math.max(monitor.x, Math.min(x, monitor.x + monitor.width - natWidth));
        return [Math.round(x), y];
    }
}

/* A two-column tile: main area toggles, optional arrow opens the related settings. */
class Tile {
    constructor(iconName, title, onToggle, onDetails) {
        this.actor = new St.BoxLayout({ style_class: 'c12-qs-tile', x_expand: true, reactive: false });
        this.main = new St.Button({ style_class: 'c12-qs-tile-main', can_focus: true, x_expand: true, x_fill: true, toggle_mode: false });
        const box = new St.BoxLayout({ vertical: true, style_class: 'c12-qs-tile-box', x_expand: true, x_align: Clutter.ActorAlign.FILL });
        this.icon = new St.Icon({ icon_name: iconName, icon_size: 18, style_class: 'c12-qs-tile-icon', x_align: Clutter.ActorAlign.START });
        this.title = new St.Label({ text: title, style_class: 'c12-qs-tile-title', x_align: Clutter.ActorAlign.START });
        this.subtitle = new St.Label({ text: '', style_class: 'c12-qs-tile-subtitle', x_align: Clutter.ActorAlign.START });
        this.title.clutter_text.ellipsize = 3;
        this.subtitle.clutter_text.ellipsize = 3;
        box.add_child(this.icon);
        box.add_child(this.title);
        box.add_child(this.subtitle);
        this.main.set_child(box);
        this.main.accessible_name = title;
        this.main.connect('clicked', () => onToggle());
        this.actor.add_child(this.main);
        if (onDetails) {
            this.arrow = new St.Button({ style_class: 'c12-qs-tile-arrow', can_focus: true, y_expand: true });
            this.arrow.set_child(new St.Icon({ icon_name: 'go-next-symbolic', icon_size: 14 }));
            this.arrow.accessible_name = title + ' – ' + _('Settings');
            this.arrow.connect('clicked', () => onDetails());
            this.actor.add_child(this.arrow);
        }
    }

    set(active, subtitle, iconName) {
        if (active) this.actor.add_style_pseudo_class('checked');
        else this.actor.remove_style_pseudo_class('checked');
        this.main.checked = !!active;
        if (subtitle !== undefined) this.subtitle.set_text(subtitle);
        if (iconName) this.icon.icon_name = iconName;
    }

    setSensitive(sensitive) {
        this.main.reactive = sensitive;
        if (sensitive) this.actor.remove_style_pseudo_class('insensitive');
        else this.actor.add_style_pseudo_class('insensitive');
    }
}

class C12QuickSettings extends Applet.IconApplet {
    constructor(metadata, orientation, panelHeight, instanceId) {
        super(orientation, panelHeight, instanceId);
        Gettext.bindtextdomain(UUID, metadata.path + '/locale');
        this._signals = [];       // [object, id]
        this._dbusSubs = [];      // [connection, id]
        this._timers = [];
        this._tiles = {};

        this.set_applet_icon_symbolic_name('cinnamon12-toggles');
        this.set_applet_tooltip(_('Quick settings'));

        this.menuManager = new PopupMenu.PopupMenuManager(this);
        this.menu = new C12QSMenu(this, orientation);
        this.menuManager.addMenu(this.menu);
        this.menu.actor.add_style_class_name('c12-qs-menu');
        this._connect(this.menu, 'open-state-changed', (m, open) => { if (open) this._refreshAll(); });

        this._buildUi();
        this._initNetwork();
        this._initBluetooth();
        this._initGSettingsToggles();
        this._initPowerProfiles();
        this._initVolume();
        this._initBrightness();
        this._updateClock();
    }

    _connect(obj, signal, cb) { this._signals.push([obj, obj.connect(signal, cb)]); }

    _spawn(argv) {
        this.menu.close();
        try { Util.spawn(argv); } catch (e) { global.logError(UUID + ': ' + e); }
    }

    // ------------------------------------------------------------------ layout
    _buildUi() {
        const section = new PopupMenu.PopupMenuSection();
        this.menu.addMenuItem(section);
        this.box = new St.BoxLayout({ vertical: true, style_class: 'c12-qs' });
        section.actor.add_actor(this.box);

        // header: date, time, settings
        const header = new St.BoxLayout({ style_class: 'c12-qs-header' });
        this.dateLabel = new St.Label({ style_class: 'c12-qs-date', y_align: Clutter.ActorAlign.CENTER });
        this.timeLabel = new St.Label({ style_class: 'c12-qs-time', y_align: Clutter.ActorAlign.CENTER });
        header.add_child(this.dateLabel);
        header.add_child(new St.Widget({ x_expand: true }));
        header.add_child(this.timeLabel);
        header.add_child(this._roundButton('emblem-system-symbolic', _('System Settings'), () => this._spawn(['cinnamon-settings'])));
        this.box.add_child(header);

        // tiles grid (2 columns, rows created as tiles become available)
        this.grid = new St.BoxLayout({ vertical: true, style_class: 'c12-qs-grid' });
        this.box.add_child(this.grid);

        // sliders
        this.sliders = new St.BoxLayout({ vertical: true, style_class: 'c12-qs-sliders' });
        this.box.add_child(this.sliders);

        // bottom actions
        this.actions = new St.BoxLayout({ style_class: 'c12-qs-actions' });
        this.box.add_child(this.actions);
        this.actions.add_child(this._roundButton('video-display-symbolic', _('Display'), () => this._spawn(['cinnamon-settings', 'display'])));
        this.airplaneButton = this._roundButton('airplane-mode-symbolic', _('Airplane mode'), () => this._toggleAirplane());
        this.actions.add_child(this.airplaneButton);
        const shot = findProgram('gnome-screenshot', 'flameshot', 'xfce4-screenshooter');
        if (shot) {
            const argv = shot === 'flameshot' ? ['flameshot', 'gui'] : shot === 'gnome-screenshot' ? ['gnome-screenshot', '--interactive'] : [shot];
            this.actions.add_child(this._roundButton('applets-screenshooter-symbolic', _('Screenshot'), () => this._spawn(argv)));
        }
        this.actions.add_child(this._roundButton('preferences-system-symbolic', _('All settings'), () => this._spawn(['cinnamon-settings'])));
    }

    _roundButton(icon, label, action) {
        const b = new St.Button({ style_class: 'c12-qs-action', can_focus: true });
        b.set_child(new St.Icon({ icon_name: icon, icon_size: 16, style_class: 'c12-qs-action-icon' }));
        b.accessible_name = label;
        b.connect('clicked', action);
        b.connect('notify::hover', () => this.set_applet_tooltip(b.hover ? label : _('Quick settings')));
        return b;
    }

    _addTile(key, tile) {
        this._tiles[key] = tile;
        // keep a stable order regardless of async init order
        const order = ['wifi', 'bluetooth', 'night', 'dark', 'dnd', 'power'];
        const present = order.filter(k => this._tiles[k]);
        for (const row of this.grid.get_children()) {
            for (const c of row.get_children()) row.remove_child(c);
            row.destroy();
        }
        let row = null;
        present.forEach((k, i) => {
            if (i % 2 === 0) {
                row = new St.BoxLayout({ style_class: 'c12-qs-row' });
                this.grid.add_child(row);
            }
            row.add_child(this._tiles[k].actor);
        });
        if (present.length % 2 === 1) row.add_child(new St.Widget({ x_expand: true, style_class: 'c12-qs-tile-spacer' }));
    }

    _addSlider(iconName, label, onChange, onIconClick) {
        const row = new St.BoxLayout({ style_class: 'c12-qs-slider-row' });
        const iconBtn = new St.Button({ style_class: 'c12-qs-slider-icon', can_focus: !!onIconClick, reactive: !!onIconClick });
        const icon = new St.Icon({ icon_name: iconName, icon_size: 16 });
        iconBtn.set_child(icon);
        iconBtn.accessible_name = label;
        if (onIconClick) iconBtn.connect('clicked', onIconClick);
        const slider = new Slider.Slider(0);
        slider.actor.x_expand = true;
        slider.actor.add_style_class_name('c12-qs-slider');
        slider.actor.can_focus = true;
        slider.actor.accessible_name = label;
        const value = new St.Label({ style_class: 'c12-qs-slider-value', y_align: Clutter.ActorAlign.CENTER });
        slider.connect('value-changed', (s, v) => { value.set_text(Math.round(v * 100) + '%'); onChange(v); });
        row.add_child(iconBtn);
        row.add_child(slider.actor);
        row.add_child(value);
        this.sliders.add_child(row);
        return { row, slider, icon, value };
    }

    _updateClock() {
        const now = GLib.DateTime.new_now_local();
        const iface = new Gio.Settings({ schema_id: 'org.cinnamon.desktop.interface' });
        this.dateLabel.set_text(now.format('%a, %e %b %Y').replace(/\s+/g, ' '));
        this.timeLabel.set_text(now.format(iface.get_boolean('clock-use-24h') ? '%H:%M' : '%l:%M %p').trim());
    }

    _refreshAll() {
        this._updateClock();
        if (!this._clockTimer) {
            this._clockTimer = Mainloop.timeout_add_seconds(15, () => {
                if (!this.menu.isOpen) { this._clockTimer = 0; return false; }
                this._updateClock();
                return true;
            });
        }
        if (this._brightness) this._readBrightness();
        this._updateAirplane();
    }

    // ------------------------------------------------------------------ Wi-Fi (NetworkManager)
    _initNetwork() {
        let NM;
        try { NM = imports.gi.NM; } catch (e) { return; }
        this.NM = NM;
        NM.Client.new_async(null, (obj, res) => {
            try { this._nm = NM.Client.new_finish(res); } catch (e) { return; }
            const hasWifi = () => this._nm.get_devices().some(d => d.get_device_type() === NM.DeviceType.WIFI);
            if (!hasWifi()) return;
            const tile = new Tile('network-wireless-signal-excellent-symbolic', _('Wi-Fi'),
                () => this._setNm('WirelessEnabled', !this._nm.wireless_enabled),
                () => this._spawn(['cinnamon-settings', 'network']));
            this._addTile('wifi', tile);
            for (const sig of ['notify::wireless-enabled', 'notify::active-connections', 'notify::primary-connection', 'notify::wireless-hardware-enabled'])
                this._connect(this._nm, sig, () => this._updateWifi());
            this._updateWifi();
        });
    }

    _setNm(prop, value) {
        this._nm.dbus_set_property(this.NM.DBUS_PATH, this.NM.DBUS_INTERFACE, prop,
            new GLib.Variant('b', value), -1, null, (c, r) => {
                try { c.dbus_set_property_finish(r); } catch (e) { global.logError(UUID + ': ' + prop + ': ' + e.message); }
            });
    }

    _updateWifi() {
        const tile = this._tiles.wifi;
        if (!tile) return;
        if (!this._nm.wireless_hardware_enabled) {
            tile.set(false, _('Blocked by hardware switch'), 'network-wireless-offline-symbolic');
            tile.setSensitive(false);
            return;
        }
        tile.setSensitive(true);
        if (!this._nm.wireless_enabled) {
            tile.set(false, _('Off'), 'network-wireless-offline-symbolic');
        } else {
            const ac = this._nm.get_active_connections().find(c => c.get_connection_type() === '802-11-wireless');
            if (ac) tile.set(true, ac.get_id(), 'network-wireless-signal-excellent-symbolic');
            else tile.set(true, _('Not connected'), 'network-wireless-signal-none-symbolic');
        }
        this._updateAirplane();
    }

    // ------------------------------------------------------------------ Bluetooth (BlueZ)
    _initBluetooth() {
        Gio.bus_get(Gio.BusType.SYSTEM, null, (o, res) => {
            try { this._sys = Gio.bus_get_finish(res); } catch (e) { return; }
            this._findAdapter();
            // adapter added/removed
            this._dbusSubs.push([this._sys, this._sys.signal_subscribe('org.bluez', 'org.freedesktop.DBus.ObjectManager',
                null, '/', null, Gio.DBusSignalFlags.NONE, () => this._findAdapter())]);
            this._dbusSubs.push([this._sys, this._sys.signal_subscribe('org.bluez', 'org.freedesktop.DBus.Properties',
                'PropertiesChanged', null, 'org.bluez.Adapter1', Gio.DBusSignalFlags.NONE, () => this._readBtPowered())]);
        });
    }

    _findAdapter() {
        this._sys.call('org.bluez', '/', 'org.freedesktop.DBus.ObjectManager', 'GetManagedObjects', null, null,
            Gio.DBusCallFlags.NONE, -1, null, (c, res) => {
                let objects;
                try { objects = c.call_finish(res).deep_unpack()[0]; } catch (e) { objects = {}; }
                this._btPath = Object.keys(objects).find(p => 'org.bluez.Adapter1' in objects[p]) || null;
                if (!this._btPath) {
                    if (this._tiles.bluetooth) this._tiles.bluetooth.setSensitive(false);
                    this._btPowered = false;
                    return;
                }
                if (!this._tiles.bluetooth) {
                    const manager = findProgram('blueman-manager', 'blueberry');
                    const tile = new Tile('bluetooth-active-symbolic', _('Bluetooth'),
                        () => this._setBtPowered(!this._btPowered),
                        () => this._spawn(manager ? [manager] : ['cinnamon-settings', 'bluetooth']));
                    this._addTile('bluetooth', tile);
                }
                this._tiles.bluetooth.setSensitive(true);
                this._readBtPowered();
            });
    }

    _readBtPowered() {
        if (!this._btPath) return;
        this._sys.call('org.bluez', this._btPath, 'org.freedesktop.DBus.Properties', 'Get',
            new GLib.Variant('(ss)', ['org.bluez.Adapter1', 'Powered']), null, Gio.DBusCallFlags.NONE, -1, null, (c, res) => {
                try { this._btPowered = c.call_finish(res).deep_unpack()[0].deep_unpack(); } catch (e) { return; }
                this._tiles.bluetooth.set(this._btPowered, this._btPowered ? _('On') : _('Off'),
                    this._btPowered ? 'bluetooth-active-symbolic' : 'bluetooth-disabled-symbolic');
                this._updateAirplane();
            });
    }

    _setBtPowered(on, cb) {
        if (!this._btPath) { if (cb) cb(); return; }
        this._sys.call('org.bluez', this._btPath, 'org.freedesktop.DBus.Properties', 'Set',
            new GLib.Variant('(ssv)', ['org.bluez.Adapter1', 'Powered', new GLib.Variant('b', on)]), null,
            Gio.DBusCallFlags.NONE, -1, null, (c, res) => {
                try { c.call_finish(res); }
                catch (e) {
                    // typically org.bluez.Error.Blocked (rfkill soft block)
                    if (this._tiles.bluetooth) this._tiles.bluetooth.set(false, _('Blocked'), 'bluetooth-disabled-symbolic');
                    global.logError(UUID + ': bluetooth: ' + e.message);
                }
                if (cb) cb();
            });
    }

    // ------------------------------------------------------------------ Airplane mode
    _hasRadios() { return !!(this._tiles.wifi || this._btPath); }

    _isAirplane() {
        if (!this._hasRadios()) return false;
        const wifiOff = !this._nm || !this._nm.wireless_enabled;
        const btOff = !this._btPath || !this._btPowered;
        return wifiOff && btOff;
    }

    _updateAirplane() {
        if (!this.airplaneButton) return;
        this.airplaneButton.visible = this._hasRadios();
        if (this._isAirplane()) this.airplaneButton.add_style_pseudo_class('checked');
        else this.airplaneButton.remove_style_pseudo_class('checked');
    }

    _toggleAirplane() {
        if (this._isAirplane()) {
            const prev = this._radioMemory || { wifi: true, wwan: true, bt: true };
            if (this._nm) { this._setNm('WirelessEnabled', prev.wifi); this._setNm('WwanEnabled', prev.wwan); }
            if (prev.bt) this._setBtPowered(true);
            this._radioMemory = null;
        } else {
            this._radioMemory = {
                wifi: this._nm ? this._nm.wireless_enabled || false : false,
                wwan: this._nm ? this._nm.wwan_enabled || false : false,
                bt: !!this._btPowered,
            };
            if (this._nm) { this._setNm('WirelessEnabled', false); this._setNm('WwanEnabled', false); }
            this._setBtPowered(false);
        }
    }

    // ------------------------------------------------------------------ GSettings-backed toggles
    _initGSettingsToggles() {
        // Night light: only where Cinnamon itself implements it (6.2+).
        if (settingsHas('org.cinnamon.settings-daemon.plugins.color', 'night-light-enabled')) {
            this._colorSettings = new Gio.Settings({ schema_id: 'org.cinnamon.settings-daemon.plugins.color' });
            const tile = new Tile('cinnamon12-night-light-symbolic', _('Night Light'),
                () => this._colorSettings.set_boolean('night-light-enabled', !this._colorSettings.get_boolean('night-light-enabled')), null);
            this._addTile('night', tile);
            const upd = () => {
                const on = this._colorSettings.get_boolean('night-light-enabled');
                tile.set(on, on ? _('On') : _('Off'));
            };
            this._connect(this._colorSettings, 'changed::night-light-enabled', upd);
            upd();
        }

        // Dark mode: switches between the two Cinnamon12 variants only.
        this._themeSettings = new Gio.Settings({ schema_id: 'org.cinnamon.theme' });
        this._ifaceSettings = new Gio.Settings({ schema_id: 'org.cinnamon.desktop.interface' });
        this._portal = settingsHas('org.x.apps.portal', 'color-scheme') ? new Gio.Settings({ schema_id: 'org.x.apps.portal' }) : null;
        const dark = new Tile('weather-clear-night-symbolic', _('Dark Mode'), () => this._toggleDark(),
            () => this._spawn(['cinnamon-settings', 'themes']));
        this._addTile('dark', dark);
        const updDark = () => {
            const name = this._themeSettings.get_string('name');
            const ours = name.startsWith('Cinnamon12-');
            dark.setSensitive(ours);
            if (!ours) dark.set(false, _('Cinnamon12 theme only'));
            else dark.set(name === 'Cinnamon12-Dark', name === 'Cinnamon12-Dark' ? _('On') : _('Off'));
        };
        this._connect(this._themeSettings, 'changed::name', updDark);
        updDark();

        // Do not disturb
        this._notifSettings = new Gio.Settings({ schema_id: 'org.cinnamon.desktop.notifications' });
        const dnd = new Tile('notifications-disabled-symbolic', _('Do Not Disturb'),
            () => this._notifSettings.set_boolean('display-notifications', !this._notifSettings.get_boolean('display-notifications')),
            () => this._spawn(['cinnamon-settings', 'notifications']));
        this._addTile('dnd', dnd);
        const updDnd = () => {
            const on = !this._notifSettings.get_boolean('display-notifications');
            dnd.set(on, on ? _('On') : _('Off'), on ? 'notifications-disabled-symbolic' : 'notifications-symbolic');
        };
        this._connect(this._notifSettings, 'changed::display-notifications', updDnd);
        updDnd();
    }

    _toggleDark() {
        const name = this._themeSettings.get_string('name');
        if (!name.startsWith('Cinnamon12-')) return;
        const toDark = name !== 'Cinnamon12-Dark';
        const target = toDark ? 'Cinnamon12-Dark' : 'Cinnamon12-Light';
        // Close first: reloading the shell stylesheet while the popup is open leaves
        // the menu in a stale "open" state.
        this.menu.close();
        Mainloop.timeout_add(180, () => {
            // GTK first, then shell, so both layers switch together.
            if (this._ifaceSettings.get_string('gtk-theme').startsWith('Cinnamon12-'))
                this._ifaceSettings.set_string('gtk-theme', target);
            this._themeSettings.set_string('name', target);
            if (this._portal) this._portal.set_string('color-scheme', toDark ? 'prefer-dark' : 'default');
            return false;
        });
    }

    // ------------------------------------------------------------------ Power profiles
    _initPowerProfiles() {
        Gio.bus_get(Gio.BusType.SYSTEM, null, (o, res) => {
            let bus;
            try { bus = Gio.bus_get_finish(res); } catch (e) { return; }
            const candidates = [['org.freedesktop.UPower.PowerProfiles', '/org/freedesktop/UPower/PowerProfiles'],
                                ['net.hadess.PowerProfiles', '/net/hadess/PowerProfiles']];
            const tryNext = (i) => {
                if (i >= candidates.length) return;
                const [name, path] = candidates[i];
                Gio.DBusProxy.new(bus, Gio.DBusProxyFlags.DO_NOT_AUTO_START, null, name, path, name, null, (p, r) => {
                    let proxy;
                    try { proxy = Gio.DBusProxy.new_finish(r); } catch (e) { return tryNext(i + 1); }
                    if (!proxy.get_name_owner()) return tryNext(i + 1);
                    this._ppd = proxy;
                    const tile = new Tile('power-profile-balanced-symbolic', _('Power Mode'), () => this._cycleProfile(),
                        () => this._spawn(['cinnamon-settings', 'power']));
                    this._addTile('power', tile);
                    this._connect(proxy, 'g-properties-changed', () => this._updateProfile());
                    this._updateProfile();
                });
            };
            tryNext(0);
        });
    }

    _profiles() {
        const v = this._ppd.get_cached_property('Profiles');
        const list = v ? v.deep_unpack().map(d => d.Profile.deep_unpack()) : [];
        const order = ['power-saver', 'balanced', 'performance'];
        return order.filter(p => list.includes(p));
    }

    _updateProfile() {
        const v = this._ppd.get_cached_property('ActiveProfile');
        const active = v ? v.deep_unpack() : 'balanced';
        const names = { 'power-saver': _('Power Saver'), 'balanced': _('Balanced'), 'performance': _('Performance') };
        this._tiles.power.set(active !== 'balanced', names[active] || active, 'power-profile-' + active + '-symbolic');
    }

    _cycleProfile() {
        const list = this._profiles();
        if (!list.length) return;
        const cur = this._ppd.get_cached_property('ActiveProfile').deep_unpack();
        const next = list[(list.indexOf(cur) + 1) % list.length];
        this._ppd.call('org.freedesktop.DBus.Properties.Set',
            new GLib.Variant('(ssv)', [this._ppd.g_interface_name, 'ActiveProfile', new GLib.Variant('s', next)]),
            Gio.DBusCallFlags.NONE, -1, null, (p, r) => {
                try { p.call_finish(r); } catch (e) { global.logError(UUID + ': power profile: ' + e.message); }
            });
    }

    // ------------------------------------------------------------------ Volume (Cvc)
    _initVolume() {
        let Cvc;
        try { Cvc = imports.gi.Cvc; } catch (e) { return; }
        this.Cvc = Cvc;
        this._mixer = new Cvc.MixerControl({ name: 'Cinnamon12 Quick Settings' });
        this._volume = this._addSlider('audio-volume-high-symbolic', _('Volume'), v => this._setVolume(v),
            () => { if (this._sink) this._sink.change_is_muted(!this._sink.is_muted); });
        this._volume.row.hide();
        this._connect(this._mixer, 'state-changed', () => this._onMixerState());
        this._connect(this._mixer, 'default-sink-changed', () => this._onMixerState());
        this._mixer.open();
    }

    _onMixerState() {
        if (this._mixer.get_state() !== this.Cvc.MixerControlState.READY) { this._volume.row.hide(); return; }
        const sink = this._mixer.get_default_sink();
        if (this._sinkSignals) for (const id of this._sinkSignals) this._sink.disconnect(id);
        this._sink = sink;
        this._sinkSignals = [];
        if (!sink) { this._volume.row.hide(); return; }
        this._sinkSignals.push(sink.connect('notify::volume', () => this._readVolume()));
        this._sinkSignals.push(sink.connect('notify::is-muted', () => this._readVolume()));
        this._volume.row.show();
        this._readVolume();
    }

    _readVolume() {
        if (!this._sink) return;
        const norm = this._mixer.get_vol_max_norm();
        const v = Math.min(1, this._sink.volume / norm);
        this._settingVolume = true;
        this._volume.slider.setValue(this._sink.is_muted ? 0 : v);
        this._settingVolume = false;
        this._volume.value.set_text(this._sink.is_muted ? _('Muted') : Math.round(v * 100) + '%');
        const icon = this._sink.is_muted || v === 0 ? 'audio-volume-muted-symbolic'
            : v < 0.33 ? 'audio-volume-low-symbolic' : v < 0.66 ? 'audio-volume-medium-symbolic' : 'audio-volume-high-symbolic';
        this._volume.icon.icon_name = icon;
    }

    _setVolume(v) {
        if (this._settingVolume || !this._sink) return;
        if (this._sink.is_muted && v > 0) this._sink.change_is_muted(false);
        this._sink.volume = Math.round(v * this._mixer.get_vol_max_norm());
        this._sink.push_volume();
    }

    // ------------------------------------------------------------------ Brightness (csd-power)
    _initBrightness() {
        this._session = Gio.DBus.session;
        const call = (method, params, cb) => this._session.call('org.cinnamon.SettingsDaemon.Power',
            '/org/cinnamon/SettingsDaemon/Power', 'org.cinnamon.SettingsDaemon.Power.Screen', method, params, null,
            Gio.DBusCallFlags.NO_AUTO_START, -1, null, (c, r) => {
                let out = null;
                try { out = c.call_finish(r).deep_unpack(); } catch (e) { out = null; }
                cb(out);
            });
        this._brightnessCall = call;
        call('GetPercentage', null, out => {
            if (!out) return; // no backlight (e.g. desktop monitor): keep the slider hidden
            this._brightness = this._addSlider('display-brightness-symbolic', _('Brightness'), v => this._setBrightness(v), null);
            // keep volume first, brightness second
            if (this._volume) this.sliders.set_child_below_sibling(this._volume.row, this._brightness.row);
            this._applyBrightness(out[0]);
            this._dbusSubs.push([this._session, this._session.signal_subscribe('org.cinnamon.SettingsDaemon.Power',
                'org.cinnamon.SettingsDaemon.Power.Screen', 'Changed', '/org/cinnamon/SettingsDaemon/Power', null,
                Gio.DBusSignalFlags.NONE, () => { if (!this._brightnessBusy) this._readBrightness(); })]);
        });
    }

    _readBrightness() {
        this._brightnessCall('GetPercentage', null, out => { if (out) this._applyBrightness(out[0]); });
    }

    _applyBrightness(pct) {
        this._settingBrightness = true;
        this._brightness.slider.setValue(pct / 100);
        this._settingBrightness = false;
        this._brightness.value.set_text(pct + '%');
    }

    _setBrightness(v) {
        if (this._settingBrightness) return;
        const pct = Math.max(1, Math.min(100, Math.round(v * 100)));
        this._brightnessBusy = true;
        this._brightnessCall('SetPercentage', new GLib.Variant('(u)', [pct]), () => { this._brightnessBusy = false; });
    }

    // ------------------------------------------------------------------ applet lifecycle
    on_applet_clicked() {
        this.menu.toggle();
    }

    on_applet_removed_from_panel() {
        if (this._clockTimer) Mainloop.source_remove(this._clockTimer);
        this._clockTimer = 0;
        for (const [obj, id] of this._signals) { try { obj.disconnect(id); } catch (e) { /* gone */ } }
        if (this._sinkSignals && this._sink) for (const id of this._sinkSignals) this._sink.disconnect(id);
        for (const [conn, id] of this._dbusSubs) { try { conn.signal_unsubscribe(id); } catch (e) { /* gone */ } }
        this._signals = []; this._dbusSubs = [];
        if (this._mixer) this._mixer.close();
        this.menuManager.removeMenu(this.menu);
        this.menu.destroy();
    }
}

function main(metadata, orientation, panelHeight, instanceId) {
    return new C12QuickSettings(metadata, orientation, panelHeight, instanceId);
}
