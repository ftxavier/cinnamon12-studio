/* Cinnamon12 | Start - application launcher for Cinnamon 6.0.x
 *
 * Layout (reference image): search on top, categories on the left, pinned grid +
 * recent files on the right, user + session buttons at the bottom.
 * Data sources are all local and real:
 *   apps/categories  -> Cinnamon.AppSystem + CMenu tree (same as menu@cinnamon.org)
 *   pinned           -> Cinnamon favorites (org.cinnamon favorite-apps)
 *   recent           -> GTK recent files (misc/docInfo), can be hidden in settings
 *   user             -> AccountsService
 *   session actions  -> cinnamon-screensaver / cinnamon-session (own confirmations)
 * No network access, no shell strings built from user input.
 */
const Applet = imports.ui.applet;
const PopupMenu = imports.ui.popupMenu;
const Main = imports.ui.main;
const Settings = imports.ui.settings;
const AppFavorites = imports.ui.appFavorites;
const DocInfo = imports.misc.docInfo;
const GnomeSession = imports.misc.gnomeSession;
const Util = imports.misc.util;
const St = imports.gi.St;
const Clutter = imports.gi.Clutter;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const Cinnamon = imports.gi.Cinnamon;
const CMenu = imports.gi.CMenu;
const Gettext = imports.gettext;
const Gtk = imports.gi.Gtk;
const Mainloop = imports.mainloop;

const UUID = 'c12-start@cinnamon12.local';
const HOME_CATEGORY = '__home__';
const ALL_CATEGORY = '__all__';
const PLACES_CATEGORY = '__places__';
const MAX_RESULTS = 60;

function _(str) {
    const own = Gettext.dgettext(UUID, str);
    if (own !== str) return own;
    return Gettext.dgettext('cinnamon', str);
}

function normalize(s) {
    return (s || '').normalize('NFKD').replace(/\p{M}/gu, '').toLowerCase();
}

class C12StartApplet extends Applet.IconApplet {
    constructor(metadata, orientation, panelHeight, instanceId) {
        super(orientation, panelHeight, instanceId);
        this.metadata = metadata;
        this.instanceId = instanceId;
        Gettext.bindtextdomain(UUID, metadata.path + '/locale');

        this._signals = [];
        this._apps = [];          // [{app, categories:[menu_id], search}]
        this._categories = [];    // CMenu.TreeDirectory
        this._category = HOME_CATEGORY;
        this._searchTimer = 0;
        this._refreshTimer = 0;

        this.settings = new Settings.AppletSettings(this, UUID, instanceId);
        this.settings.bind('show-recent', 'showRecent', () => this._rebuildRight());
        this.settings.bind('menu-width', 'menuWidth', () => this._applySize());
        this.settings.bind('menu-height', 'menuHeight', () => this._applySize());
        this.settings.bind('grid-columns', 'gridColumns', () => this._rebuildRight());
        this.settings.bind('overlay-key', 'overlayKey', () => this._updateKeybinding());

        const iconFile = Gio.File.new_for_path(metadata.path + '/icon.svg');
        if (iconFile.query_exists(null)) this.set_applet_icon_path(iconFile.get_path());
        else this.set_applet_icon_name('cinnamon12-start');
        this.set_applet_tooltip(_('Start'));

        this.menuManager = new PopupMenu.PopupMenuManager(this);
        this.menu = new Applet.AppletPopupMenu(this, orientation);
        this.menuManager.addMenu(this.menu);
        this.menu.actor.add_style_class_name('c12-launcher-menu');
        this._buildUi();

        this._session = new GnomeSession.SessionManager();
        this._recentManager = DocInfo.getDocManager();
        this._appSys = Cinnamon.AppSystem.get_default();

        this._connect(this._appSys, 'installed-changed', () => this._queueRefresh());
        this._connect(AppFavorites.getAppFavorites(), 'changed', () => this._queueRefresh());
        this._connect(this._recentManager, 'changed', () => this._queueRefresh());
        this._connect(this.menu, 'open-state-changed', (m, open) => this._onOpenStateChanged(open));

        this._updateKeybinding();
        this._loadApps();
        this._showCategory(HOME_CATEGORY);
    }

    _connect(obj, signal, cb) {
        this._signals.push([obj, obj.connect(signal, cb)]);
    }

    // ------------------------------------------------------------------ UI
    _buildUi() {
        const section = new PopupMenu.PopupMenuSection();
        this.menu.addMenuItem(section);

        this.mainBox = new St.BoxLayout({ vertical: true, style_class: 'c12-launcher' });
        section.actor.add_actor(this.mainBox);

        // search
        this.searchEntry = new St.Entry({
            style_class: 'c12-launcher-search', can_focus: true, x_expand: true,
            hint_text: _('Search for apps, settings and files…'),
        });
        this.searchEntry.set_primary_icon(new St.Icon({
            icon_name: 'edit-find-symbolic', style_class: 'c12-launcher-search-icon' }));
        this.searchEntry.clutter_text.connect('text-changed', () => this._onSearchChanged());
        this.searchEntry.clutter_text.connect('key-press-event', (a, e) => this._onSearchKey(e));
        this.mainBox.add_child(this.searchEntry);

        // body: categories | content
        const body = new St.BoxLayout({ vertical: false, style_class: 'c12-launcher-body', y_expand: true });
        this.mainBox.add_child(body);

        this.categoryScroll = new St.ScrollView({ style_class: 'c12-launcher-categories', y_expand: true });
        this.categoryScroll.set_policy(St.PolicyType.NEVER, St.PolicyType.AUTOMATIC);
        this.categoryBox = new St.BoxLayout({ vertical: true });
        this.categoryScroll.add_actor(this.categoryBox);
        body.add_child(this.categoryScroll);

        this.contentScroll = new St.ScrollView({ style_class: 'c12-launcher-content', x_expand: true, y_expand: true });
        this.contentScroll.set_policy(St.PolicyType.NEVER, St.PolicyType.AUTOMATIC);
        this.contentBox = new St.BoxLayout({ vertical: true, x_expand: true });
        this.contentScroll.add_actor(this.contentBox);
        body.add_child(this.contentScroll);

        // footer
        const footer = new St.BoxLayout({ vertical: false, style_class: 'c12-launcher-footer' });
        this.mainBox.add_child(footer);
        this.userButton = new St.Button({ style_class: 'c12-launcher-user', can_focus: true });
        const userBox = new St.BoxLayout({ vertical: false, style_class: 'c12-launcher-user-box' });
        this.userIcon = new St.Icon({ icon_name: 'avatar-default-symbolic', icon_size: 28, style_class: 'c12-launcher-avatar' });
        this.userLabel = new St.Label({ text: GLib.get_user_name(), y_align: Clutter.ActorAlign.CENTER });
        userBox.add_child(this.userIcon);
        userBox.add_child(this.userLabel);
        this.userButton.set_child(userBox);
        this.userButton.connect('clicked', () => this._spawn(['cinnamon-settings', 'user']));
        footer.add_child(this.userButton);
        footer.add_child(new St.Widget({ x_expand: true }));
        footer.add_child(this._sessionButton('system-lock-screen-symbolic', _('Lock screen'), () => this._lock()));
        footer.add_child(this._sessionButton('system-log-out-symbolic', _('Logout'), () => this._session.LogoutRemote(0)));
        footer.add_child(this._sessionButton('system-reboot-symbolic', _('Restart'), () => this._spawn(['cinnamon-session-quit', '--reboot'])));
        footer.add_child(this._sessionButton('system-shutdown-symbolic', _('Shut down'), () => this._session.ShutdownRemote()));
        this._loadUser();

        // arrow-key navigation between focusable buttons
        this.mainBox.connect('key-press-event', (a, e) => this._onNavKey(e));
        this._applySize();
    }

    _sessionButton(icon, label, action) {
        const b = new St.Button({ style_class: 'c12-launcher-session', can_focus: true, reactive: true });
        b.set_child(new St.Icon({ icon_name: icon, icon_size: 18, style_class: 'c12-launcher-session-icon' }));
        b.accessible_name = label;
        b.connect('clicked', () => { this.menu.close(); action(); });
        this._tooltipFor(b, label);
        return b;
    }

    _tooltipFor(actor, text) {
        // Lightweight: show the label in the footer user label area on hover.
        actor.connect('notify::hover', () => {
            this.userLabel.set_text(actor.hover ? text : this._userName());
        });
    }

    _applySize() {
        const monitor = Main.layoutManager.primaryMonitor;
        const maxH = monitor ? Math.floor(monitor.height * 0.8) : this.menuHeight;
        const maxW = monitor ? Math.floor(monitor.width * 0.9) : this.menuWidth;
        this.mainBox.set_style(`width: ${Math.min(this.menuWidth, maxW)}px; height: ${Math.min(this.menuHeight, maxH)}px;`);
    }

    // ------------------------------------------------------------------ data
    _loadApps() {
        const tree = this._appSys.get_tree();
        const root = tree.get_root_directory();
        const iter = root.iter();
        const apps = new Map();
        const dirs = [];
        let t;
        while ((t = iter.next()) !== CMenu.TreeItemType.INVALID) {
            if (t === CMenu.TreeItemType.DIRECTORY) {
                const dir = iter.get_directory();
                if (dir.get_is_nodisplay()) continue;
                if (this._loadDirectory(dir, dir, apps)) dirs.push(dir);
            }
        }
        const prefLast = ['administration', 'preferences'];
        dirs.sort((a, b) => {
            const pa = prefLast.indexOf(a.get_menu_id().toLowerCase()), pb = prefLast.indexOf(b.get_menu_id().toLowerCase());
            if ((pa < 0) !== (pb < 0)) return pa < 0 ? -1 : 1;
            return a.get_name().localeCompare(b.get_name());
        });
        this._categories = dirs;
        this._apps = Array.from(apps.entries()).map(([app, cats]) => {
            const info = app.get_app_info();
            const parts = [app.get_name(), info ? info.get_generic_name() : '', info ? info.get_description() : '',
                           info ? (info.get_keywords() || []).join(' ') : '', info ? info.get_executable() : ''];
            return { app, categories: cats, name: normalize(app.get_name()), search: normalize(parts.join(' ')) };
        }).sort((a, b) => a.app.get_name().localeCompare(b.app.get_name()));
        this._buildCategories();
    }

    _loadDirectory(dir, topDir, apps) {
        const iter = dir.iter();
        let has = false, t;
        while ((t = iter.next()) !== CMenu.TreeItemType.INVALID) {
            if (t === CMenu.TreeItemType.ENTRY) {
                const app = this._appSys.lookup_app(iter.get_entry().get_desktop_file_id());
                if (!app || app.get_nodisplay()) continue;
                has = true;
                if (apps.has(app)) apps.get(app).push(topDir.get_menu_id());
                else apps.set(app, [topDir.get_menu_id()]);
            } else if (t === CMenu.TreeItemType.DIRECTORY) {
                if (this._loadDirectory(iter.get_directory(), topDir, apps)) has = true;
            }
        }
        return has;
    }

    _queueRefresh() {
        if (this._refreshTimer) return;
        this._refreshTimer = Mainloop.timeout_add(500, () => {
            this._refreshTimer = 0;
            this._loadApps();
            this._showCategory(this._category);
            return false;
        });
    }

    // ------------------------------------------------------------------ categories
    _buildCategories() {
        this.categoryBox.destroy_all_children();
        this._categoryButtons = {};
        this._addCategory(HOME_CATEGORY, _('Home'), 'go-home-symbolic', null);
        this._addCategory(ALL_CATEGORY, _('All Applications'), 'view-app-grid-symbolic', null);
        for (const dir of this._categories) {
            this._addCategory(dir.get_menu_id(), dir.get_name(), null, dir.get_icon());
        }
        this._addCategory(PLACES_CATEGORY, _('Places'), 'folder-symbolic', null);
    }

    _addCategory(id, label, iconName, gicon) {
        const b = new St.Button({ style_class: 'c12-launcher-category', can_focus: true, x_fill: true, x_expand: true });
        const box = new St.BoxLayout({ vertical: false, style_class: 'c12-launcher-category-box' });
        const icon = gicon ? new St.Icon({ gicon, icon_size: 16 }) : new St.Icon({ icon_name: iconName, icon_size: 16 });
        box.add_child(icon);
        box.add_child(new St.Label({ text: label, y_align: Clutter.ActorAlign.CENTER }));
        b.set_child(box);
        b.connect('clicked', () => this._showCategory(id));
        this.categoryBox.add_child(b);
        this._categoryButtons[id] = b;
    }

    _showCategory(id) {
        this._category = id;
        for (const [cid, b] of Object.entries(this._categoryButtons || {})) {
            if (cid === id) b.add_style_pseudo_class('checked');
            else b.remove_style_pseudo_class('checked');
        }
        if (this.searchEntry.get_text()) return;
        this._rebuildRight();
    }

    _clearContent() {
        // Never destroy the actor holding key focus: the menu manager would close the menu.
        const focus = global.stage.get_key_focus();
        if (focus && this.contentBox.contains(focus)) global.stage.set_key_focus(this.searchEntry);
        this.contentBox.destroy_all_children();
    }

    _rebuildRight() {
        if (!this.contentBox) return;
        this._clearContent();
        const vadj = this.contentScroll.get_vscroll_bar().get_adjustment();
        vadj.set_value(0);
        const id = this._category;
        if (id === HOME_CATEGORY) return this._buildHome();
        if (id === PLACES_CATEGORY) return this._buildPlaces();
        const list = id === ALL_CATEGORY ? this._apps : this._apps.filter(a => a.categories.includes(id));
        this._buildAppList(list.map(a => a.app));
    }

    _sectionTitle(text) {
        this.contentBox.add_child(new St.Label({ text, style_class: 'c12-launcher-section-title' }));
    }

    _buildHome() {
        this._sectionTitle(_('Pinned'));
        const favs = AppFavorites.getAppFavorites().getFavorites();
        if (favs.length === 0) {
            this.contentBox.add_child(new St.Label({ text: _('Right-click an app to pin it here.'), style_class: 'c12-launcher-empty' }));
        } else {
            this._buildGrid(favs);
        }
        if (!this.showRecent) return;
        const recents = (this._recentManager._infosByTimestamp || []).filter(i => !i.name.startsWith('.')).slice(0, 5);
        if (recents.length === 0) return;
        this._sectionTitle(_('Recent Files'));
        for (const info of recents) {
            const row = this._row(info.createIcon(24), info.name, this._location(info), () => this._openUri(info.uri));
            this.contentBox.add_child(row);
        }
    }

    _location(info) {
        try {
            const file = Gio.File.new_for_uri(info.uri);
            const parent = file.get_parent();
            if (!parent) return '';
            const p = parent.get_path() || parent.get_uri();
            const home = GLib.get_home_dir();
            return p && p.startsWith(home) ? '~' + p.slice(home.length) : p;
        } catch (e) { return ''; }
    }

    _buildGrid(apps) {
        const cols = Math.max(3, Math.min(8, this.gridColumns));
        let row = null;
        apps.forEach((app, i) => {
            if (i % cols === 0) {
                row = new St.BoxLayout({ vertical: false, style_class: 'c12-launcher-grid-row' });
                this.contentBox.add_child(row);
            }
            row.add_child(this._tile(app));
        });
    }

    _tile(app) {
        const b = new St.Button({ style_class: 'c12-launcher-tile', can_focus: true });
        const box = new St.BoxLayout({ vertical: true, style_class: 'c12-launcher-tile-box' });
        const icon = app.create_icon_texture(32);
        icon.x_align = Clutter.ActorAlign.CENTER;
        box.add_child(icon);
        const label = new St.Label({ text: app.get_name(), style_class: 'c12-launcher-tile-label', x_align: Clutter.ActorAlign.CENTER });
        label.clutter_text.ellipsize = 3; // Pango.EllipsizeMode.END
        box.add_child(label);
        b.set_child(box);
        b._c12App = app;
        b.connect('clicked', () => this._launch(app));
        b.connect('button-release-event', (a, e) => this._onAppButtonRelease(app, e));
        return b;
    }

    _buildAppList(apps) {
        if (apps.length === 0) {
            this.contentBox.add_child(new St.Label({ text: _('No items found'), style_class: 'c12-launcher-empty' }));
            return;
        }
        for (const app of apps) {
            const info = app.get_app_info();
            const desc = info ? (info.get_description() || info.get_generic_name() || '') : '';
            const row = this._row(app.create_icon_texture(24), app.get_name(), desc, () => this._launch(app));
            row._c12App = app;
            row.connect('button-release-event', (a, e) => this._onAppButtonRelease(app, e));
            this.contentBox.add_child(row);
        }
    }

    _row(icon, title, subtitle, onActivate) {
        const b = new St.Button({ style_class: 'c12-launcher-row', can_focus: true, x_fill: true, x_expand: true });
        const box = new St.BoxLayout({ vertical: false, style_class: 'c12-launcher-row-box' });
        box.add_child(icon);
        const text = new St.BoxLayout({ vertical: true, y_align: Clutter.ActorAlign.CENTER, x_expand: true });
        const t = new St.Label({ text: title, style_class: 'c12-launcher-row-title' });
        t.clutter_text.ellipsize = 3;
        text.add_child(t);
        if (subtitle) {
            const s = new St.Label({ text: subtitle, style_class: 'c12-launcher-row-subtitle' });
            s.clutter_text.ellipsize = 3;
            text.add_child(s);
        }
        box.add_child(text);
        b.set_child(box);
        b.connect('clicked', onActivate);
        return b;
    }

    _buildPlaces() {
        const dirs = [
            [GLib.get_home_dir(), _('Home'), 'user-home'],
            [GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DESKTOP), null, 'user-desktop'],
            [GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOCUMENTS), null, 'folder-documents'],
            [GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_DOWNLOAD), null, 'folder-download'],
            [GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_MUSIC), null, 'folder-music'],
            [GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_PICTURES), null, 'folder-pictures'],
            [GLib.get_user_special_dir(GLib.UserDirectory.DIRECTORY_VIDEOS), null, 'folder-videos'],
        ];
        const seen = new Set();
        for (const [path, name, iconName] of dirs) {
            if (!path || seen.has(path) || !GLib.file_test(path, GLib.FileTest.IS_DIR)) continue;
            seen.add(path);
            const file = Gio.File.new_for_path(path);
            const label = name || file.get_basename();
            this.contentBox.add_child(this._row(new St.Icon({ icon_name: iconName, icon_size: 24 }), label, path,
                () => this._openUri(file.get_uri())));
        }
        this.contentBox.add_child(this._row(new St.Icon({ icon_name: 'user-trash', icon_size: 24 }), _('Trash'), '',
            () => this._openUri('trash:///')));
        this.contentBox.add_child(this._row(new St.Icon({ icon_name: 'drive-harddisk', icon_size: 24 }), _('File System'), '/',
            () => this._openUri('file:///')));
    }

    // ------------------------------------------------------------------ search
    _onSearchChanged() {
        // Cinnamon's StEntry emits text-changed when it swaps the hint text in/out on
        // focus changes; only react to real query changes.
        const q = this.searchEntry.get_text().trim();
        if (q === this._lastQuery) return;
        this._lastQuery = q;
        if (this._searchTimer) Mainloop.source_remove(this._searchTimer);
        this._searchTimer = Mainloop.timeout_add(120, () => {
            this._searchTimer = 0;
            this._doSearch();
            return false;
        });
    }

    _doSearch() {
        const q = normalize(this.searchEntry.get_text().trim());
        if (!q) { this._firstResult = null; this._rebuildRight(); return; }
        const words = q.split(/\s+/);
        const scored = [];
        for (const a of this._apps) {
            if (!words.every(w => a.search.includes(w))) continue;
            let score = 0;
            if (a.name.startsWith(q)) score += 100;
            else if (a.name.includes(q)) score += 50;
            else if (words.every(w => a.name.includes(w))) score += 30;
            scored.push([score, a.app]);
        }
        scored.sort((x, y) => y[0] - x[0] || x[1].get_name().localeCompare(y[1].get_name()));
        this._clearContent();
        this._sectionTitle(_('Applications'));
        this._buildAppList(scored.slice(0, MAX_RESULTS).map(s => s[1]));
        this._firstResult = scored.length ? scored[0][1] : null;
    }

    _onSearchKey(event) {
        const sym = event.get_key_symbol();
        if (sym === Clutter.KEY_Return || sym === Clutter.KEY_KP_Enter) {
            if (this.searchEntry.get_text().trim() && this._firstResult) this._launch(this._firstResult);
            return Clutter.EVENT_STOP;
        }
        if (sym === Clutter.KEY_Down) {
            this.contentBox.navigate_focus(null, Gtk.DirectionType.TAB_FORWARD, false);
            return Clutter.EVENT_STOP;
        }
        return Clutter.EVENT_PROPAGATE;
    }

    _onNavKey(event) {
        const sym = event.get_key_symbol();
        const map = {};
        map[Clutter.KEY_Up] = Gtk.DirectionType.UP;
        map[Clutter.KEY_Down] = Gtk.DirectionType.DOWN;
        map[Clutter.KEY_Left] = Gtk.DirectionType.LEFT;
        map[Clutter.KEY_Right] = Gtk.DirectionType.RIGHT;
        if (!(sym in map)) return Clutter.EVENT_PROPAGATE;
        const focus = global.stage.get_key_focus();
        if (focus === this.searchEntry.clutter_text) return Clutter.EVENT_PROPAGATE;
        this.mainBox.navigate_focus(focus, map[sym], false);
        const now = global.stage.get_key_focus();
        if (now && this.contentBox.contains(now)) this._scrollTo(now);
        return Clutter.EVENT_STOP;
    }

    _scrollTo(actor) {
        const adj = this.contentScroll.get_vscroll_bar().get_adjustment();
        const [, y] = actor.get_transformed_position();
        const [, boxY] = this.contentScroll.get_transformed_position();
        const h = this.contentScroll.height;
        const rel = y - boxY;
        if (rel < 0) adj.set_value(adj.get_value() + rel - 8);
        else if (rel + actor.height > h) adj.set_value(adj.get_value() + rel + actor.height - h + 8);
    }

    // ------------------------------------------------------------------ actions
    _onAppButtonRelease(app, event) {
        if (event.get_button() !== 3) return Clutter.EVENT_PROPAGATE;
        const favs = AppFavorites.getAppFavorites();
        if (favs.isFavorite(app.get_id())) favs.removeFavorite(app.get_id());
        else favs.addFavorite(app.get_id());
        return Clutter.EVENT_STOP;
    }

    _launch(app) {
        this.menu.close();
        try { app.open_new_window(-1); } catch (e) { global.logError(UUID + ': ' + e); }
    }

    _openUri(uri) {
        this.menu.close();
        try { Gio.AppInfo.launch_default_for_uri(uri, global.create_app_launch_context()); }
        catch (e) { global.logError(UUID + ': ' + e); }
    }

    _spawn(argv) {
        try { Util.spawn(argv); } catch (e) { global.logError(UUID + ': ' + e); }
    }

    _lock() {
        const ss = new Gio.Settings({ schema_id: 'org.cinnamon.desktop.screensaver' });
        if (GLib.find_program_in_path('cinnamon-screensaver-command')) {
            if (ss.get_boolean('ask-for-away-message')) this._spawn(['cinnamon-screensaver-lock-dialog']);
            else this._spawn(['cinnamon-screensaver-command', '--lock']);
        }
    }

    _userName() {
        if (this._user && this._user.is_loaded) {
            const real = this._user.get_real_name();
            if (real) return real;
        }
        return GLib.get_user_name();
    }

    _loadUser() {
        try {
            const AccountsService = imports.gi.AccountsService;
            this._user = AccountsService.UserManager.get_default().get_user(GLib.get_user_name());
            const update = () => {
                this.userLabel.set_text(this._userName());
                const f = this._user.get_icon_file();
                if (f && GLib.file_test(f, GLib.FileTest.EXISTS))
                    this.userIcon.gicon = new Gio.FileIcon({ file: Gio.File.new_for_path(f) });
            };
            this._connect(this._user, 'notify::is-loaded', update);
            this._connect(this._user, 'changed', update);
            if (this._user.is_loaded) update();
        } catch (e) {
            this.userLabel.set_text(GLib.get_user_name());
        }
    }

    _onOpenStateChanged(open) {
        if (open) {
            this._lastQuery = '';
            this.searchEntry.set_text('');
            this._showCategory(HOME_CATEGORY);
            global.stage.set_key_focus(this.searchEntry);
        }
    }

    _updateKeybinding() {
        Main.keybindingManager.removeHotKey('c12-start-' + this.instanceId);
        if (this.overlayKey) {
            Main.keybindingManager.addHotKey('c12-start-' + this.instanceId, this.overlayKey, () => {
                if (!Main.overview.visible && !Main.expo.visible) this.menu.toggle_with_options(false);
            });
        }
    }

    on_applet_clicked() {
        this.menu.toggle();
    }

    on_applet_removed_from_panel() {
        Main.keybindingManager.removeHotKey('c12-start-' + this.instanceId);
        if (this._searchTimer) Mainloop.source_remove(this._searchTimer);
        if (this._refreshTimer) Mainloop.source_remove(this._refreshTimer);
        this._searchTimer = this._refreshTimer = 0;
        for (const [obj, id] of this._signals) {
            try { obj.disconnect(id); } catch (e) { /* already gone */ }
        }
        this._signals = [];
        this.settings.finalize();
        this.menuManager.removeMenu(this.menu);
        this.menu.destroy();
    }
}

function main(metadata, orientation, panelHeight, instanceId) {
    return new C12StartApplet(metadata, orientation, panelHeight, instanceId);
}
