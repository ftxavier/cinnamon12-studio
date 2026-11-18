/* Cinnamon12 quick LINKS (not fake toggle switches).
 * Never changes network, bluetooth or brightness state.
 * All actions open real system settings or external tools.
 */
const Applet = imports.ui.applet;
const PopupMenu = imports.ui.popupMenu;
const Util = imports.misc.util;
class C12QuickLinks extends Applet.IconApplet {
    constructor(metadata, orientation, panelHeight, instanceId) {
        super(orientation,panelHeight,instanceId);
        this.set_applet_icon_name('cinnamon12-control-center');
        this.set_applet_tooltip('Cinnamon12 | Configurações rápidas');
        this.menu = new Applet.AppletPopupMenu(this,orientation);
        this.manager = new PopupMenu.PopupMenuManager(this);
        this.manager.addMenu(this.menu);
        const links = [
            ['Rede e Wi-Fi', 'cinnamon-settings network'],
            ['Bluetooth', 'cinnamon-settings bluetooth'],
            ['Som e microfone', 'cinnamon-settings sound'],
            ['Monitores e resolução', 'cinnamon-settings display'],
            ['Energia e bateria', 'cinnamon-settings power'],
            ['Aparência e temas', 'cinnamon-settings themes'],
            ['Todos os ajustes', 'cinnamon-settings']
        ];
        for (const [name,command] of links) {
            const item = new PopupMenu.PopupMenuItem(name);
            item.connect('activate',() => {
                try { Util.spawnCommandLineAsync(command); }
                catch (e) { global.logError(e); }
            });
            this.menu.addMenuItem(item);
        }
    }
    on_applet_clicked() { this.menu.toggle(); }
    on_applet_removed_from_panel() { if(this.manager) this.manager.removeMenu(this.menu); }
}
function main(metadata, orientation, panelHeight, instanceId) {
    return new C12QuickLinks(metadata,orientation,panelHeight,instanceId);
}
