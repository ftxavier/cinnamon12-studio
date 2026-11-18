/* Cinnamon12 start launcher - optional and experimental (Cinnamon 6.0 API).
 * Uses desktop applications installed locally. No external network calls.
 * Add via Cinnamon Settings > Applets, don't replace stock menu automatically.
 */
const Applet = imports.ui.applet;
const PopupMenu = imports.ui.popupMenu;
const St = imports.gi.St;
const Gio = imports.gi.Gio;
const Util = imports.misc.util;

class C12StartApplet extends Applet.IconApplet {
    constructor(metadata, orientation, panelHeight, instanceId) {
        super(orientation, panelHeight, instanceId);
        this.set_applet_icon_name('cinnamon12-start');
        this.set_applet_tooltip('Cinnamon12 | Início');
        this.menu = new Applet.AppletPopupMenu(this, orientation);
        this.menuManager = new PopupMenu.PopupMenuManager(this);
        this.menuManager.addMenu(this.menu);
        this._makeMenu();
    }
    _run(command) {
        try { Util.spawnCommandLineAsync(command); }
        catch (e) { global.logError(e); }
    }
    _addCommand(label, command, toMenu) {
        const item = new PopupMenu.PopupMenuItem(label);
        item.connect('activate', () => this._run(command));
        (toMenu || this.menu).addMenuItem(item);
    }
    _makeMenu() {
        const searchContainer = new PopupMenu.PopupBaseMenuItem({reactive: false});
        this._search = new St.Entry({style_class:'menu-search-entry', hint_text:'Pesquisar aplicativos…', can_focus:true});
        searchContainer.addActor(this._search, {expand: true});
        this.menu.addMenuItem(searchContainer);
        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());
        this._addCommand('Arquivos  ·  Nemo', 'nemo');
        this._addCommand('Terminal', 'x-terminal-emulator');
        this._addCommand('Configurações', 'cinnamon-settings');
        this._addCommand('Monitor do sistema', 'gnome-system-monitor');
        this.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());
        this._appsMenu = new PopupMenu.PopupSubMenuMenuItem('Todos os aplicativos');
        this.menu.addMenuItem(this._appsMenu);
        this._search.clutter_text.connect('text-changed', () => this._populateApps());
        this._populateApps();
    }
    _populateApps() {
        if (!this._appsMenu || !this._appsMenu.menu) return;
        this._appsMenu.menu.removeAll();
        const text = String(this._search.get_text()).toLocaleLowerCase().trim();
        const apps = Gio.AppInfo.get_all()
            .filter(a => a.should_show() && a.get_display_name())
            .sort((a,b) => a.get_display_name().localeCompare(b.get_display_name()));
        let count = 0;
        for (const app of apps) {
            if (text && !app.get_display_name().toLocaleLowerCase().includes(text)) continue;
            const item = new PopupMenu.PopupMenuItem(app.get_display_name());
            item.connect('activate', () => {
                try { app.launch([], null); }
                catch(e) { global.logError(e); }
            });
            this._appsMenu.menu.addMenuItem(item);
            if (++count >= 65) break;
        }
        if (text && count > 0) this._appsMenu.setSubmenuShown(true);
        if (count === 0) {
            const empty = new PopupMenu.PopupMenuItem('Nenhum aplicativo encontrado');
            empty.setSensitive(false);
            this._appsMenu.menu.addMenuItem(empty);
        }
    }
    on_applet_clicked() { this.menu.toggle(); }
    on_applet_removed_from_panel() {
        if (this.menuManager) this.menuManager.removeMenu(this.menu);
    }
}
function main(metadata, orientation, panelHeight, instanceId) {
    return new C12StartApplet(metadata, orientation, panelHeight, instanceId);
}
