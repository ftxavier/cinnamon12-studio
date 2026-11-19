/* Cinnamon12 | Search - panel search for Cinnamon 6.0.x, Windows style.
 *
 * In the panel: a search field you type into (results pop up on the first character),
 * a search icon or nothing (keyboard shortcut only; both open a popup with its own
 * field). It searches, all locally:
 *   apps and settings -> Cinnamon.AppSystem + CMenu tree (same apps as the menu);
 *                        entries with the "Settings" category are listed as settings
 *   files and folders -> name index of the home folder, built by indexer.py in a
 *                        separate low-priority process and queried with grep, so the
 *                        shell never walks the disk nor holds the index in memory
 *   empty query       -> recent files (GTK history)
 * No network access, no shell strings built from user input (argv only).
 */
const Applet = imports.ui.applet;
const PopupMenu = imports.ui.popupMenu;
const Main = imports.ui.main;
const Settings = imports.ui.settings;
const DocInfo = imports.misc.docInfo;
const AppFavorites = imports.ui.appFavorites;
const Util = imports.misc.util;
const St = imports.gi.St;
const Clutter = imports.gi.Clutter;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const Cinnamon = imports.gi.Cinnamon;
const CMenu = imports.gi.CMenu;
const Gettext = imports.gettext;
const Mainloop = imports.mainloop;
const ByteArray = imports.byteArray;

const UUID = 'c12-search@cinnamon12.local';
const MAX_APPS = 8;
const MAX_SETTINGS = 5;
const GREP_LIMIT = 400;          // raw index lines read per query, ranked afterwards
const INDEX_MAX_ENTRIES = 400000;
const INDEX_MAX_AGE = 10 * 60;   // seconds; re-index on open when older
const MENU_WIDTH = 860;
const MENU_HEIGHT = 560;

function _(str) {
    const own = Gettext.dgettext(UUID, str);
    if (own !== str) return own;
    return Gettext.dgettext('cinnamon', str);
}

// Must match norm() in indexer.py: NFKD, drop combining marks, lower case.
function normalize(s) {
    return (s || '').normalize('NFKD').replace(/\p{M}/gu, '').toLowerCase();
}

function pcreEscape(s) {
    return s.replace(/[\\^$.*+?()[\]{}|\/-]/g, '\\$&');
}

function tildePath(p) {
    const home = GLib.get_home_dir();
    return p && (p === home || p.startsWith(home + '/')) ? '~' + p.slice(home.length) : p;
}

/* Opens above the applet, 10 px off the panel like the Start menu, aligned with the
 * applet's start edge on horizontal panels and kept inside the monitor. */
class C12SearchMenu extends Applet.AppletPopupMenu {
    _calculatePosition() {
        let [x, y] = super._calculatePosition();
        const GAP = 10;
        switch (this._orientation) {
            case St.Side.BOTTOM: y -= GAP; break;
            case St.Side.TOP: y += GAP; break;
            case St.Side.LEFT: x += GAP; break;
            case St.Side.RIGHT: x -= GAP; break;
        }
        const horizontal = this._orientation === St.Side.TOP || this._orientation === St.Side.BOTTOM;
        if (!horizontal) return [x, y];
        const src = Cinnamon.util_get_transformed_allocation(this.sourceActor);
        const [, , natWidth] = this.actor.get_preferred_size();
        const monitor = Main.layoutManager.findMonitorForActor(this.sourceActor);
        const rtl = Clutter.get_default_text_direction() === Clutter.TextDirection.RTL;
        x = rtl ? src.x2 - natWidth : src.x1;
        x = Math.max(monitor.x, Math.min(x, monitor.x + monitor.width - natWidth));
        return [Math.round(x), y];
    }
}

class C12SearchApplet extends Applet.IconApplet {
    constructor(metadata, orientation, panelHeight, instanceId) {
        super(orientation, panelHeight, instanceId);
        this.metadata = metadata;
        this.instanceId = instanceId;
        this._orientation = orientation;
        Gettext.bindtextdomain(UUID, metadata.path + '/locale');

        this._signals = [];
        this._apps = [];        // [{app, name, search, isSetting}]
        this._results = [];     // [{actor, activate, reveal}]
        this._selected = -1;
        this._searchTimer = 0;
        this._refreshTimer = 0;
        this._startupTimer = 0;
        this._grepCancel = null;
        this._indexProc = null;
        this._indexStale = false;
        this._lastQuery = null;
        this._indexPath = GLib.build_filenamev([GLib.get_user_cache_dir(), 'cinnamon12', 'search-index.tsv']);

        this.settings = new Settings.AppletSettings(this, UUID, instanceId);
        this.settings.bind('display-mode', 'displayMode', () => this._applyDisplayMode());
        this.settings.bind('entry-width', 'entryWidth', () => this._applyDisplayMode());
        this.settings.bind('search-files', 'searchFiles', () => { this._indexStale = true; this._redoSearch(); });
        this.settings.bind('excluded-folders', 'excludedFolders', () => { this._indexStale = true; });
        this.settings.bind('max-files', 'maxFiles', () => this._redoSearch());
        this.settings.bind('hotkey', 'hotkey', () => this._updateKeybinding());

        this.set_applet_icon_symbolic_name('edit-find-symbolic');
        this.set_applet_tooltip(_('Search'));
        this._buildPanelEntry();

        this.menuManager = new PopupMenu.PopupMenuManager(this);
        this.menu = new C12SearchMenu(this, orientation);
        this.menuManager.addMenu(this.menu);
        this.menu.actor.add_style_class_name('c12-search-menu');
        this._buildUi();

        this._appSys = Cinnamon.AppSystem.get_default();
        this._recentManager = DocInfo.getDocManager();
        this._connect(this._appSys, 'installed-changed', () => this._queueRefresh());
        this._connect(this.menu, 'open-state-changed', (m, open) => this._onOpenStateChanged(open));
        this._connect(global.settings, 'changed::panel-edit-mode', () => this._applyDisplayMode());

        this._applyDisplayMode();
        this._updateKeybinding();
        this._loadApps();
        // first index shortly after login, off the startup path
        this._startupTimer = Mainloop.timeout_add_seconds(30, () => {
            this._startupTimer = 0;
            this._ensureIndex();
            return false;
        });
    }

    _connect(obj, signal, cb) {
        this._signals.push([obj, obj.connect(signal, cb)]);
    }

    // ------------------------------------------------------------------ panel
    /* The panel field is a real entry: clicking it (or the shortcut) takes the keyboard
     * with a modal grab of its own, because the panel never has X keyboard focus; the
     * results popup opens on the first typed character and closes when the text is
     * cleared, keeping the field focused. Escape or a click elsewhere gives the
     * keyboard back. The popup menu manager treats the applet (and so this field) as
     * part of the open menu, so typing and clicking here keep the popup open. */
    _buildPanelEntry() {
        this._entry = new St.Entry({ style_class: 'c12-search-panel-entry', can_focus: true,
            hint_text: _('Search'), y_align: Clutter.ActorAlign.CENTER });
        this._entry.set_primary_icon(new St.Icon({ icon_name: 'edit-find-symbolic', style_class: 'c12-search-panel-icon' }));
        this._entry.clutter_text.connect('text-changed', () => this._onPanelTextChanged());
        this._entry.clutter_text.connect('key-press-event', (a, e) => this._onSearchKey(e));
        // ClutterText handles the press itself (and takes key focus without any grab),
        // so hook its signal: user handlers run before the class handler.
        this._entry.clutter_text.connect('button-press-event', () => { this._beginTyping(); return Clutter.EVENT_PROPAGATE; });
        // any other way the field gets key focus (Tab, a11y) must also take the keyboard
        this._entry.clutter_text.connect('key-focus-in', () => { if (!this._typing && !this._ending) this._beginTyping(); });
        this.actor.add_child(this._entry);
        this._typing = false;
        this._ending = false;
        this._captureId = 0;
    }

    _beginTyping() {
        if (this._typing) return;
        this._typing = true;  // set first: pushModal moves key focus and re-enters here
        if (!Main.pushModal(this._entry)) {
            this._typing = false;
            global.logError(UUID + ': could not grab the keyboard for the search field');
            global.stage.set_key_focus(null);
            return;
        }
        this._captureId = global.stage.connect('captured-event', (a, e) => this._onTypingCapture(e));
        global.stage.set_key_focus(this._entry.clutter_text);
        this._ensureIndex();
    }

    _endTyping() {
        if (!this._typing) return;
        this._typing = false;
        // popModal (ours and the menu's) restores the focus saved at grab time, which
        // may be this field: don't let that start a new grab.
        this._ending = true;
        if (this._captureId) global.stage.disconnect(this._captureId);
        this._captureId = 0;
        if (this.menu.isOpen) { this._closingForEmpty = false; this.menu.close(); }
        Main.popModal(this._entry);
        const focus = global.stage.get_key_focus();
        if (focus && this._entry.contains(focus)) global.stage.set_key_focus(null);
        this._lastQuery = null;
        this._entry.set_text('');
        this._ending = false;
    }

    // While the field holds the keyboard without the popup: a click elsewhere ends it.
    _onTypingCapture(event) {
        if (!this._typing || this.menu.isOpen) return Clutter.EVENT_PROPAGATE;
        if (event.type() !== Clutter.EventType.BUTTON_PRESS) return Clutter.EVENT_PROPAGATE;
        const src = event.get_source();
        if (src && this.actor.contains(src)) return Clutter.EVENT_PROPAGATE;
        this._endTyping();
        return Clutter.EVENT_PROPAGATE;
    }

    _onPanelTextChanged() {
        if (!this._typing) return;
        const q = this._entry.get_text().trim();
        if (q && !this.menu.isOpen) {
            this.menu.open(false);
        } else if (!q && this.menu.isOpen) {
            this._closingForEmpty = true;
            this.menu.close();
        }
        this._onSearchChanged();
    }

    _queryEntry() {
        return this._mode === 'entry' ? this._entry : this.searchEntry;
    }

    _applyDisplayMode() {
        const horizontal = this._orientation === St.Side.TOP || this._orientation === St.Side.BOTTOM;
        const editing = global.settings.get_boolean('panel-edit-mode');
        let mode = this.displayMode;
        if (mode === 'entry' && !horizontal) mode = 'icon';
        if (mode === 'hidden' && editing) mode = 'icon';
        if (mode !== this._mode && this._typing) this._endTyping();
        this._mode = mode;
        if (this.searchEntry) this.searchEntry.visible = mode !== 'entry';
        this.actor.remove_style_class_name('c12-search-applet-entry');
        this.actor.remove_style_class_name('c12-search-applet-hidden');
        this._entry.visible = mode === 'entry';
        this._applet_icon_box.visible = mode === 'icon';
        // Hidden keeps a zero-width actor in place, so the popup still opens next to
        // where the applet sits (e.g. right after the Start button).
        this.actor.reactive = mode !== 'hidden';
        if (mode === 'entry') {
            this.actor.add_style_class_name('c12-search-applet-entry');
            this._entry.set_style(`width: ${this.entryWidth}px;`);
        } else if (mode === 'hidden') {
            this.actor.add_style_class_name('c12-search-applet-hidden');
        }
    }

    on_orientation_changed(orientation) {
        this._orientation = orientation;
        this.menu.setOrientation(orientation);
        this._applyDisplayMode();
    }

    // ------------------------------------------------------------------ popup UI
    _buildUi() {
        const section = new PopupMenu.PopupMenuSection();
        this.menu.addMenuItem(section);
        this.mainBox = new St.BoxLayout({ vertical: true, style_class: 'c12-search' });
        section.actor.add_actor(this.mainBox);

        this.searchEntry = new St.Entry({
            style_class: 'c12-launcher-search', can_focus: true, x_expand: true,
            hint_text: _('Search apps, settings and files'),
        });
        this.searchEntry.set_primary_icon(new St.Icon({
            icon_name: 'edit-find-symbolic', style_class: 'c12-launcher-search-icon' }));
        this.searchEntry.clutter_text.connect('text-changed', () => this._onSearchChanged());
        this.searchEntry.clutter_text.connect('key-press-event', (a, e) => this._onSearchKey(e));
        this.mainBox.add_child(this.searchEntry);

        const body = new St.BoxLayout({ vertical: false, style_class: 'c12-search-body', x_expand: true, y_expand: true });
        this.mainBox.add_child(body);
        this.resultsScroll = new St.ScrollView({ style_class: 'c12-search-results', x_expand: true, y_expand: true });
        this.resultsScroll.set_policy(St.PolicyType.NEVER, St.PolicyType.AUTOMATIC);
        this.resultsBox = new St.BoxLayout({ vertical: true, x_expand: true, style_class: 'c12-search-results-box' });
        this.resultsScroll.add_actor(this.resultsBox);
        body.add_child(this.resultsScroll);
        // detail pane: what the selected result is and what can be done with it
        this.detailScroll = new St.ScrollView({ style_class: 'c12-search-detail', y_expand: true });
        this.detailScroll.set_policy(St.PolicyType.NEVER, St.PolicyType.AUTOMATIC);
        this.detailBox = new St.BoxLayout({ vertical: true, x_expand: true });
        this.detailScroll.add_actor(this.detailBox);
        body.add_child(this.detailScroll);
        this.searchEntry.visible = this._mode !== 'entry';
        this._applySize();
    }

    _applySize() {
        const monitor = Main.layoutManager.primaryMonitor;
        const w = monitor ? Math.min(MENU_WIDTH, Math.floor(monitor.width * 0.9)) : MENU_WIDTH;
        const h = monitor ? Math.min(MENU_HEIGHT, Math.floor(monitor.height * 0.75)) : MENU_HEIGHT;
        this.mainBox.set_style(`width: ${w}px; height: ${h}px;`);
    }

    // ------------------------------------------------------------------ apps
    _loadApps() {
        const root = this._appSys.get_tree().get_root_directory();
        const apps = new Set();
        this._walk(root, apps);
        this._apps = Array.from(apps).map(app => {
            const info = app.get_app_info();
            const parts = [app.get_name(), info ? info.get_generic_name() : '', info ? info.get_description() : '',
                           info ? (info.get_keywords() || []).join(' ') : '', info ? info.get_executable() : ''];
            const cats = info && info.get_categories ? (info.get_categories() || '') : '';
            const exec = info && info.get_executable() ? GLib.path_get_basename(info.get_executable()) : '';
            const name = normalize(app.get_name());
            return { app, name, words: name.split(/[\s\-_.]+/), exec: normalize(exec),
                     search: normalize(parts.join(' ')), isSetting: cats.split(';').includes('Settings') };
        });
    }

    _walk(dir, apps) {
        const iter = dir.iter();
        let t;
        while ((t = iter.next()) !== CMenu.TreeItemType.INVALID) {
            if (t === CMenu.TreeItemType.ENTRY) {
                const app = this._appSys.lookup_app(iter.get_entry().get_desktop_file_id());
                if (app && !app.get_nodisplay()) apps.add(app);
            } else if (t === CMenu.TreeItemType.DIRECTORY) {
                const sub = iter.get_directory();
                if (!sub.get_is_nodisplay()) this._walk(sub, apps);
            }
        }
    }

    _queueRefresh() {
        if (this._refreshTimer) return;
        this._refreshTimer = Mainloop.timeout_add(500, () => {
            this._refreshTimer = 0;
            this._loadApps();
            return false;
        });
    }

    _matchApps(q) {
        const words = q.split(/\s+/);
        const scored = [];
        for (const a of this._apps) {
            if (!words.every(w => a.search.includes(w))) continue;
            let score = 0;
            // "code" finds Visual Studio Code (a word of the name, and its executable)
            if (a.name.startsWith(q)) score += 100;
            else if (a.exec && a.exec.startsWith(q)) score += 95;
            else if (a.words.some(w => w.startsWith(q))) score += 90;
            else if (a.name.includes(q)) score += 50;
            else if (words.every(w => a.name.includes(w))) score += 30;
            scored.push([score, Object.assign({ score }, a)]);
        }
        scored.sort((x, y) => y[0] - x[0] || x[1].app.get_name().localeCompare(y[1].app.get_name()));
        return scored.map(s => s[1]);
    }

    // ------------------------------------------------------------------ file index
    _indexAge() {
        try {
            const info = Gio.File.new_for_path(this._indexPath).query_info('time::modified', Gio.FileQueryInfoFlags.NONE, null);
            return GLib.get_real_time() / 1e6 - info.get_attribute_uint64('time::modified');
        } catch (e) {
            return -1;  // no index yet
        }
    }

    _ensureIndex() {
        if (!this.searchFiles || this._indexProc) return;
        const age = this._indexAge();
        if (age >= 0 && age < INDEX_MAX_AGE && !this._indexStale) return;
        const python = GLib.find_program_in_path('python3');
        if (!python) return;
        this._indexStale = false;
        const argv = [python, this.metadata.path + '/indexer.py', this._indexPath,
                      String(INDEX_MAX_ENTRIES), this.excludedFolders || ''];
        try {
            const proc = Gio.Subprocess.new(argv, Gio.SubprocessFlags.STDOUT_SILENCE | Gio.SubprocessFlags.STDERR_PIPE);
            this._indexProc = proc;
            proc.wait_check_async(null, (p, res) => {
                try { p.wait_check_finish(res); }
                catch (e) { global.logError(UUID + ': indexer failed: ' + e.message); }
                if (this._indexProc !== p) return;
                this._indexProc = null;
                // first index finished while the user is typing: show file results now
                if (this.menu.isOpen) this._redoSearch();
            });
        } catch (e) {
            this._indexProc = null;
            global.logError(UUID + ': ' + e);
        }
    }

    _searchFilesAsync(q, done) {
        if (this._grepCancel) this._grepCancel.cancel();
        this._grepCancel = null;
        if (!this.searchFiles) return done(null);
        if (this._indexAge() < 0) return done(this._indexProc ? 'indexing' : null);
        const grep = GLib.find_program_in_path('grep');
        if (!grep) return done(null);
        const words = q.split(/\s+/).filter(w => w);
        // every word must appear in the normalized name (first column)
        const pattern = '^' + words.map(w => `(?=[^\\t]*${pcreEscape(w)})`).join('');
        const cancel = new Gio.Cancellable();
        this._grepCancel = cancel;
        try {
            const proc = Gio.Subprocess.new([grep, '-a', '-P', '-m', String(GREP_LIMIT), '--', pattern, this._indexPath],
                Gio.SubprocessFlags.STDOUT_PIPE | Gio.SubprocessFlags.STDERR_SILENCE);
            proc.communicate_async(null, cancel, (p, res) => {
                if (cancel.is_cancelled()) return;
                let out = '';
                try {
                    const [, stdout] = p.communicate_finish(res);
                    if (stdout) out = ByteArray.toString(ByteArray.fromGBytes(stdout));
                } catch (e) {
                    if (!cancel.is_cancelled()) global.logError(UUID + ': ' + e);
                    return;
                }
                if (this._grepCancel === cancel) this._grepCancel = null;
                done(this._rankFiles(q, out));
            });
        } catch (e) {
            global.logError(UUID + ': ' + e);
            done(null);
        }
    }

    _rankFiles(q, out) {
        const words = q.split(/\s+/).filter(w => w);
        const items = [];
        for (const line of out.split('\n')) {
            const parts = line.split('\t');
            if (parts.length < 3) continue;
            const [name, kind] = parts;
            const path = parts.slice(2).join('\t');
            let score = 0;
            if (name === q) score += 300;
            else if (name.startsWith(q)) score += 200;
            else if (name.includes(q)) score += 100;
            else if (words.length && name.startsWith(words[0])) score += 60;
            if (kind === 'd') score += 5;
            score -= path.split('/').length;  // shallower first
            items.push({ score, name, isDir: kind === 'd', path });
        }
        items.sort((a, b) => b.score - a.score || a.path.localeCompare(b.path));
        return items.slice(0, this.maxFiles);
    }

    // ------------------------------------------------------------------ results
    /* A result is {kind: 'app'|'setting'|'file'|'folder', title, subtitle, app?, path?,
     * uri?}. Rows only highlight on hover; the detail pane follows the selection, which
     * moves with the arrow keys or the row's chevron, so sweeping the pointer towards
     * the pane does not change it. Clicking a row opens it, as in Windows. */
    _clearResults() {
        const focus = global.stage.get_key_focus();
        if (focus && (this.resultsBox.contains(focus) || this.detailBox.contains(focus)))
            global.stage.set_key_focus(this._queryEntry().clutter_text);
        this.resultsBox.destroy_all_children();
        this.detailBox.destroy_all_children();
        this._results = [];
        this._selected = -1;
        this.resultsScroll.get_vscroll_bar().get_adjustment().set_value(0);
    }

    _sectionTitle(text) {
        this.resultsBox.add_child(new St.Label({ text, style_class: 'c12-launcher-section-title c12-search-section' }));
    }

    _note(text) {
        this.resultsBox.add_child(new St.Label({ text, style_class: 'c12-launcher-empty' }));
    }

    _kindLabel(item) {
        return { app: _('Application'), setting: _('Settings'), file: _('File'), folder: _('Folder') }[item.kind];
    }

    _itemIcon(item, size) {
        if (item.app) return item.app.create_icon_texture(size);
        if (item.gicon) return new St.Icon({ gicon: item.gicon, icon_size: size });
        if (item.kind === 'folder') return new St.Icon({ icon_name: 'folder', icon_size: size });
        const [type] = Gio.content_type_guess(item.path || item.uri, null);
        return new St.Icon({ gicon: Gio.content_type_get_icon(type), icon_size: size });
    }

    _addResult(item, big = false) {
        const b = new St.Button({ style_class: 'c12-launcher-row c12-search-row' + (big ? ' c12-search-best' : ''),
                                  can_focus: false, x_fill: true, x_expand: true });
        const box = new St.BoxLayout({ vertical: false, style_class: 'c12-launcher-row-box' });
        box.add_child(this._itemIcon(item, big ? 32 : 24));
        const text = new St.BoxLayout({ vertical: true, y_align: Clutter.ActorAlign.CENTER, x_expand: true });
        const t = new St.Label({ text: item.title, style_class: 'c12-launcher-row-title' });
        t.clutter_text.ellipsize = 3;  // Pango.EllipsizeMode.END
        text.add_child(t);
        const sub = big ? this._kindLabel(item) : item.subtitle;
        if (sub) {
            const s = new St.Label({ text: sub, style_class: 'c12-launcher-row-subtitle' });
            s.clutter_text.ellipsize = 1;  // START: keep the end of long paths
            text.add_child(s);
        }
        box.add_child(text);
        const index = this._results.length;
        const more = new St.Button({ style_class: 'c12-search-chevron', can_focus: false, y_align: Clutter.ActorAlign.CENTER });
        more.set_child(new St.Icon({ icon_name: 'go-next-symbolic', icon_size: 16 }));
        more.accessible_name = _('More options');
        more.connect('clicked', () => this._select(index, false));
        box.add_child(more);
        b.set_child(box);
        b.connect('clicked', () => this._activate(item));
        this.resultsBox.add_child(b);
        this._results.push({ actor: b, item });
    }

    _select(index, scroll = true) {
        if (!this._results.length) { this._selected = -1; return; }
        index = Math.max(0, Math.min(index, this._results.length - 1));
        if (this._selected >= 0 && this._results[this._selected])
            this._results[this._selected].actor.remove_style_pseudo_class('checked');
        this._selected = index;
        const actor = this._results[index].actor;
        actor.add_style_pseudo_class('checked');
        if (scroll) this._scrollTo(actor);
        this._showDetail(this._results[index].item);
    }

    _scrollTo(actor) {
        const adj = this.resultsScroll.get_vscroll_bar().get_adjustment();
        const [, y] = actor.get_transformed_position();
        const [, boxY] = this.resultsScroll.get_transformed_position();
        const h = this.resultsScroll.height;
        const rel = y - boxY;
        if (rel < 0) adj.set_value(adj.get_value() + rel - 8);
        else if (rel + actor.height > h) adj.set_value(adj.get_value() + rel + actor.height - h + 8);
    }

    // ------------------------------------------------------------------ detail pane
    _showDetail(item) {
        const focus = global.stage.get_key_focus();
        if (focus && this.detailBox.contains(focus)) global.stage.set_key_focus(this._queryEntry().clutter_text);
        this.detailBox.destroy_all_children();
        const head = new St.BoxLayout({ vertical: true, style_class: 'c12-search-detail-head' });
        const icon = this._itemIcon(item, 64);
        icon.x_align = Clutter.ActorAlign.CENTER;
        head.add_child(icon);
        const title = new St.Label({ text: item.title, style_class: 'c12-search-detail-title', x_align: Clutter.ActorAlign.CENTER });
        title.clutter_text.line_wrap = true;
        title.clutter_text.ellipsize = 0;
        head.add_child(title);
        head.add_child(new St.Label({ text: this._kindLabel(item), style_class: 'c12-search-detail-kind', x_align: Clutter.ActorAlign.CENTER }));
        this.detailBox.add_child(head);

        this._detailSeparator();
        for (const [iconName, label, action] of this._actionsFor(item)) this._detailAction(iconName, label, action);

        if (item.app) this._detailRecents(item.app);
        else if (item.path) this._detailInfo(item);
    }

    _detailSeparator() {
        this.detailBox.add_child(new St.Widget({ style_class: 'c12-search-detail-separator', x_expand: true }));
    }

    _detailTitle(text) {
        this.detailBox.add_child(new St.Label({ text, style_class: 'c12-search-detail-section' }));
    }

    _detailAction(iconName, label, action) {
        const b = new St.Button({ style_class: 'c12-search-action', can_focus: true, x_fill: true, x_expand: true });
        const box = new St.BoxLayout({ vertical: false, style_class: 'c12-search-action-box' });
        const icon = typeof iconName === 'string' ? new St.Icon({ icon_name: iconName, icon_size: 16 })
                                                  : new St.Icon({ gicon: iconName, icon_size: 16 });
        icon.y_align = Clutter.ActorAlign.CENTER;
        box.add_child(icon);
        const l = new St.Label({ text: label, y_align: Clutter.ActorAlign.CENTER, x_expand: true });
        l.clutter_text.ellipsize = 3;
        box.add_child(l);
        b.set_child(box);
        b.connect('clicked', () => action());
        this.detailBox.add_child(b);
        return b;
    }

    _actionsFor(item) {
        const acts = [];
        if (item.app) {
            const app = item.app, info = app.get_app_info(), id = app.get_id();
            acts.push(['window-new-symbolic', _('Open'), () => this._launch(app)]);
            for (const a of (info && info.list_actions ? info.list_actions() : []).slice(0, 4))
                acts.push(['system-run-symbolic', info.get_action_name(a), () => this._launchAction(app, a)]);
            if (info && info.get_filename())
                acts.push(['folder-open-symbolic', _('Open file location'), () => this._reveal(Gio.File.new_for_path(info.get_filename()).get_uri())]);
            const wl = this._windowList();
            if (wl) {
                const pinned = wl.pinnedFavorites._favorites.some(f => f.id === id);
                acts.push(['view-pin-symbolic', pinned ? _('Unpin from taskbar') : _('Pin to taskbar'), () => this._toggleTaskbarPin(app, pinned)]);
            }
            const favs = AppFavorites.getAppFavorites();
            const fav = favs.isFavorite(id);
            acts.push([fav ? 'starred-symbolic' : 'non-starred-symbolic', fav ? _('Unpin from Start') : _('Pin to Start'),
                () => { if (fav) favs.removeFavorite(id); else favs.addFavorite(id); this._showDetail(item); }]);
            if (GLib.file_test('/usr/bin/cinnamon-remove-application', GLib.FileTest.EXISTS) && info && info.get_filename())
                acts.push(['edit-delete-symbolic', _('Uninstall'), () => { this._close(); this._spawn(['/usr/bin/cinnamon-remove-application', info.get_filename()]); }]);
            return acts;
        }
        const file = item.uri ? Gio.File.new_for_uri(item.uri) : Gio.File.new_for_path(item.path);
        const uri = file.get_uri();
        const type = item.kind === 'folder' ? 'inode/directory' : Gio.content_type_guess(file.get_basename(), null)[0];
        const def = Gio.AppInfo.get_default_for_type(type, !file.get_path());
        acts.push(['document-open-symbolic', def ? _('Open with %s').format(def.get_display_name()) : _('Open'), () => this._openUri(uri)]);
        const others = Gio.AppInfo.get_recommended_for_type(type)
            .filter(a => a.should_show() && (!def || !a.equal(def))).slice(0, 3);
        for (const a of others)
            acts.push([a.get_icon() || 'application-x-executable-symbolic', _('Open with %s').format(a.get_display_name()),
                () => this._openWith(a, file)]);
        if (item.kind === 'folder' && file.get_path())
            acts.push(['utilities-terminal-symbolic', _('Open in Terminal'), () => this._openTerminal(file.get_path())]);
        acts.push(['folder-open-symbolic', _('Open file location'), () => this._reveal(uri)]);
        acts.push(['edit-copy-symbolic', _('Copy path'), () => {
            St.Clipboard.get_default().set_text(St.ClipboardType.CLIPBOARD, file.get_path() || uri);
            this._close();
        }]);
        return acts;
    }

    // files the app can open, from the GTK recent list
    _detailRecents(app) {
        const info = app.get_app_info();
        const types = info && info.get_supported_types ? (info.get_supported_types() || []) : [];
        if (!types.length) return;
        const recents = (this._recentManager._infosByTimestamp || [])
            .filter(r => !r.name.startsWith('.') && types.some(t => Gio.content_type_is_a(r.mimeType, t))).slice(0, 5);
        if (!recents.length) return;
        this._detailSeparator();
        this._detailTitle(_('Recent'));
        for (const r of recents)
            this._detailAction(r.gicon, r.name, () => this._openWith(info, Gio.File.new_for_uri(r.uri)));
    }

    _detailInfo(item) {
        let info;
        try {
            info = Gio.File.new_for_path(item.path).query_info('standard::content-type,standard::size,time::modified',
                Gio.FileQueryInfoFlags.NONE, null);
        } catch (e) { return; }
        this._detailSeparator();
        const rows = [[_('Location'), tildePath(GLib.path_get_dirname(item.path))]];
        if (item.kind === 'file') {
            rows.push([_('Type'), Gio.content_type_get_description(info.get_content_type())]);
            rows.push([_('Size'), GLib.format_size(info.get_size())]);
        }
        const dt = info.get_modification_date_time();
        if (dt) rows.push([_('Modified'), dt.to_local().format('%x %H:%M')]);
        for (const [k, v] of rows) {
            const box = new St.BoxLayout({ vertical: true, style_class: 'c12-search-info' });
            box.add_child(new St.Label({ text: k, style_class: 'c12-search-info-key' }));
            const l = new St.Label({ text: v, style_class: 'c12-search-info-value' });
            l.clutter_text.ellipsize = 1;
            box.add_child(l);
            this.detailBox.add_child(box);
        }
    }

    // ------------------------------------------------------------------ search
    _showEmpty() {
        this._clearResults();
        const recents = (this._recentManager._infosByTimestamp || []).filter(i => !i.name.startsWith('.')).slice(0, 6);
        if (recents.length) {
            this._sectionTitle(_('Recent Files'));
            for (const info of recents) {
                let parent = '', path = null;
                try {
                    const f = Gio.File.new_for_uri(info.uri);
                    path = f.get_path();
                    const p = f.get_parent();
                    parent = p ? tildePath(p.get_path() || p.get_uri()) : '';
                } catch (e) { /* non-local uri */ }
                this._addResult({ kind: 'file', title: info.name, subtitle: parent, uri: info.uri, path, gicon: info.gicon });
            }
        }
        this._note(this.searchFiles
            ? _('Type to search apps, settings and files in your home folder.')
            : _('Type to search apps and settings.'));
        this._select(0);
    }

    _appItem(a) {
        const info = a.app.get_app_info();
        const desc = info ? (info.get_description() || info.get_generic_name() || '') : '';
        return { kind: a.isSetting ? 'setting' : 'app', title: a.app.get_name(), subtitle: desc, app: a.app, score: a.score };
    }

    _doSearch() {
        const q = normalize(this._queryEntry().get_text().trim());
        if (!q) { if (this._grepCancel) this._grepCancel.cancel(); this._showEmpty(); return; }
        const matches = this._matchApps(q).map(a => this._appItem(a));
        this._ensureIndex();
        // Wait for the files (a grep of a few ms) before drawing, so the best match and
        // the sections don't jump around; apps alone are shown if the index is missing.
        this._searchFilesAsync(q, files => {
            if (normalize(this._queryEntry().get_text().trim()) !== q) return;
            this._render(q, matches, files);
        });
    }

    _render(q, matches, files) {
        this._clearResults();
        const indexing = files === 'indexing';
        const fileItems = Array.isArray(files) ? files.map(f => ({
            kind: f.isDir ? 'folder' : 'file', title: GLib.path_get_basename(f.path),
            subtitle: tildePath(GLib.path_get_dirname(f.path)), path: f.path, score: f.score,
            uri: Gio.File.new_for_path(f.path).get_uri() })) : [];
        // best match: an app whose name (or a word of it, or its command) starts with the
        // query wins, then a file/folder
        // named like it, then whatever ranks first
        let best = matches.find(m => m.score >= 90) || fileItems.find(f => f.score >= 100)
                   || matches[0] || fileItems[0] || null;
        const rest = list => list.filter(x => x !== best);
        if (best) { this._sectionTitle(_('Best match')); this._addResult(best, true); }
        const groups = [
            [_('Applications'), rest(matches.filter(m => m.kind === 'app')).slice(0, MAX_APPS)],
            [_('Settings'), rest(matches.filter(m => m.kind === 'setting')).slice(0, MAX_SETTINGS)],
            [_('Files'), rest(fileItems.filter(f => f.kind === 'file'))],
            [_('Folders'), rest(fileItems.filter(f => f.kind === 'folder'))],
        ];
        for (const [title, list] of groups) {
            if (!list.length) continue;
            this._sectionTitle(title);
            list.forEach(item => this._addResult(item));
        }
        if (indexing) { this._sectionTitle(_('Files and folders')); this._note(_('Indexing your home folder…')); }
        if (!this._results.length && !indexing) this._note(_('No results found'));
        this._select(0);
        if (this._pendingEnter) { const go = this._pendingEnter; this._pendingEnter = null; go(); }
    }

    _redoSearch() {
        if (!this.menu || !this.menu.isOpen) return;
        this._doSearch();
    }

    _onSearchChanged() {
        // StEntry emits text-changed when it swaps the hint text on focus changes.
        const q = this._queryEntry().get_text().trim();
        if (q === this._lastQuery) return;
        this._lastQuery = q;
        if (this._searchTimer) Mainloop.source_remove(this._searchTimer);
        this._searchTimer = Mainloop.timeout_add(120, () => {
            this._searchTimer = 0;
            this._doSearch();
            return false;
        });
    }

    _onSearchKey(event) {
        const sym = event.get_key_symbol();
        if (sym === Clutter.KEY_Escape && this._typing) { this._endTyping(); return Clutter.EVENT_STOP; }
        if (sym === Clutter.KEY_Down) { this._select(this._selected + 1); return Clutter.EVENT_STOP; }
        if (sym === Clutter.KEY_Up) { this._select(this._selected - 1); return Clutter.EVENT_STOP; }
        if (sym === Clutter.KEY_Page_Down) { this._select(this._selected + 5); return Clutter.EVENT_STOP; }
        if (sym === Clutter.KEY_Page_Up) { this._select(this._selected - 5); return Clutter.EVENT_STOP; }
        if (sym === Clutter.KEY_Return || sym === Clutter.KEY_KP_Enter) {
            const go = () => {
                const r = this._results[this._selected];
                if (!r) return;
                const ctrl = (event.get_state() & Clutter.ModifierType.CONTROL_MASK) !== 0;
                if (ctrl && !r.item.app) this._reveal(r.item.uri);
                else this._activate(r.item);
            };
            if (this._searchTimer) {  // Enter before the debounce: search, then open
                Mainloop.source_remove(this._searchTimer);
                this._searchTimer = 0;
                this._pendingEnter = go;
                this._doSearch();
            } else go();
            return Clutter.EVENT_STOP;
        }
        return Clutter.EVENT_PROPAGATE;
    }

    // ------------------------------------------------------------------ actions
    _close() {
        if (this._typing) this._endTyping();
        else this.menu.close();
    }

    _activate(item) {
        if (item.app) this._launch(item.app);
        else this._openUri(item.uri);
    }

    _launch(app) {
        this._close();
        try { app.open_new_window(-1); } catch (e) { global.logError(UUID + ': ' + e); }
    }

    _launchAction(app, action) {
        this._close();
        try { app.get_app_info().launch_action(action, global.create_app_launch_context()); }
        catch (e) { global.logError(UUID + ': ' + e); }
    }

    _openWith(appInfo, file) {
        this._close();
        try { appInfo.launch([file], global.create_app_launch_context()); }
        catch (e) { global.logError(UUID + ': ' + e); }
    }

    _openTerminal(path) {
        this._close();
        const s = new Gio.Settings({ schema_id: 'org.cinnamon.desktop.default-applications.terminal' });
        const term = GLib.find_program_in_path(s.get_string('exec') || '') || GLib.find_program_in_path('x-terminal-emulator');
        if (!term) return;
        try {
            const launcher = new Gio.SubprocessLauncher({ flags: Gio.SubprocessFlags.NONE });
            launcher.set_cwd(path);
            launcher.spawnv([term]);
        } catch (e) { global.logError(UUID + ': ' + e); }
    }

    _windowList() {
        try {
            const list = imports.ui.appletManager.getRunningInstancesForUuid('grouped-window-list@cinnamon.org');
            const wl = list && list[0];
            return wl && wl.pinnedFavorites && Array.isArray(wl.pinnedFavorites._favorites) ? wl : null;
        } catch (e) { return null; }
    }

    _toggleTaskbarPin(app, pinned) {
        const wl = this._windowList();
        if (!wl) return;
        try {
            if (pinned) wl.pinnedFavorites.removeFavorite(app.get_id());
            else wl.pinnedFavorites.addFavorite({ appId: app.get_id(), pos: -1 });
        } catch (e) { global.logError(UUID + ': ' + e); }
        const r = this._results[this._selected];
        if (r) this._showDetail(r.item);
    }

    _spawn(argv) {
        try { Util.spawn(argv); } catch (e) { global.logError(UUID + ': ' + e); }
    }

    _openUri(uri) {
        this._close();
        try { Gio.AppInfo.launch_default_for_uri(uri, global.create_app_launch_context()); }
        catch (e) { global.logError(UUID + ': ' + e); }
    }

    // Open the containing folder with the item selected (FileManager1, which Nemo
    // implements); fall back to opening the parent folder.
    _reveal(uri) {
        this._close();
        const fallback = () => {
            const parent = Gio.File.new_for_uri(uri).get_parent();
            if (!parent) return;
            try { Gio.AppInfo.launch_default_for_uri(parent.get_uri(), global.create_app_launch_context()); }
            catch (e) { global.logError(UUID + ': ' + e); }
        };
        Gio.DBus.session.call('org.freedesktop.FileManager1', '/org/freedesktop/FileManager1',
            'org.freedesktop.FileManager1', 'ShowItems', new GLib.Variant('(ass)', [[uri], '']),
            null, Gio.DBusCallFlags.NONE, 3000, null, (conn, res) => {
                try { conn.call_finish(res); } catch (e) { fallback(); }
            });
    }

    _onOpenStateChanged(open) {
        if (this._mode === 'entry') {
            if (open) {
                this._applySize();
                this._doSearch();
            } else if (this._closingForEmpty) {
                // text cleared: popup gone, field keeps the keyboard
                this._closingForEmpty = false;
                if (this._typing) global.stage.set_key_focus(this._entry.clutter_text);
            } else {
                this._endTyping();  // launched something, clicked outside, ...
            }
            return;
        }
        if (!open) return;
        this._applySize();
        this._lastQuery = '';
        this.searchEntry.set_text('');
        this._showEmpty();
        global.stage.set_key_focus(this.searchEntry);
        this._ensureIndex();
    }

    _updateKeybinding() {
        Main.keybindingManager.removeHotKey('c12-search-' + this.instanceId);
        if (this.hotkey) {
            Main.keybindingManager.addHotKey('c12-search-' + this.instanceId, this.hotkey, () => {
                if (Main.overview.visible || Main.expo.visible) return;
                if (this._mode === 'entry') { if (this._typing) this._endTyping(); else this._beginTyping(); }
                else this.menu.toggle_with_options(false);
            });
        }
    }

    on_applet_clicked() {
        if (this._mode === 'entry') this._beginTyping();
        else this.menu.toggle();
    }

    on_applet_removed_from_panel() {
        this._endTyping();
        Main.keybindingManager.removeHotKey('c12-search-' + this.instanceId);
        for (const id of [this._searchTimer, this._refreshTimer, this._startupTimer])
            if (id) Mainloop.source_remove(id);
        this._searchTimer = this._refreshTimer = this._startupTimer = 0;
        if (this._grepCancel) this._grepCancel.cancel();
        this._indexProc = null;  // let a running indexer finish on its own
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
    return new C12SearchApplet(metadata, orientation, panelHeight, instanceId);
}
