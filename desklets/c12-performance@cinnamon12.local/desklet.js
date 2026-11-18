/* Cinnamon12 | System monitor desklet - Cinnamon 6.0.x
 * CPU, memory, disk and network from local Linux sources only:
 *   /proc/stat, /proc/meminfo, /proc/net/dev and the filesystem info of a mount point.
 * Rates are computed between two samples; the interval is configurable (1-5 s).
 */
const Desklet = imports.ui.desklet;
const Settings = imports.ui.settings;
const St = imports.gi.St;
const Clutter = imports.gi.Clutter;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const Mainloop = imports.mainloop;
const Gettext = imports.gettext;

const UUID = 'c12-performance@cinnamon12.local';
const HISTORY = 40;

function _(s) {
    const t = Gettext.dgettext(UUID, s);
    return t !== s ? t : Gettext.dgettext('cinnamon', s);
}

function readText(path) {
    try {
        const [ok, bytes] = GLib.file_get_contents(path);
        return ok ? new TextDecoder().decode(bytes) : '';
    } catch (e) { return ''; }
}

function formatRate(bytesPerSec) {
    const units = ['B/s', 'KB/s', 'MB/s', 'GB/s'];
    let v = bytesPerSec, i = 0;
    while (v >= 1000 && i < units.length - 1) { v /= 1024; i++; }
    return (v >= 100 || i === 0 ? Math.round(v) : v.toFixed(1)) + ' ' + units[i];
}

/* Small sparkline drawn with cairo. Colors come from the theme node (color property). */
class Sparkline {
    constructor(styleClass) {
        this.values = [];
        this.actor = new St.DrawingArea({ style_class: 'c12-sysmon-graph ' + styleClass, y_align: Clutter.ActorAlign.CENTER });
        this.actor.connect('repaint', area => this._paint(area));
    }

    push(v) {
        this.values.push(Math.max(0, Math.min(1, v)));
        if (this.values.length > HISTORY) this.values.shift();
        this.actor.queue_repaint();
    }

    _paint(area) {
        const cr = area.get_context();
        const [w, h] = area.get_surface_size();
        const c = area.get_theme_node().get_foreground_color();
        const n = this.values.length;
        if (n > 1) {
            const step = w / (HISTORY - 1);
            const x0 = w - (n - 1) * step;
            const y = v => h - 1 - v * (h - 2);
            cr.moveTo(x0, h);
            this.values.forEach((v, i) => cr.lineTo(x0 + i * step, y(v)));
            cr.lineTo(w, h);
            cr.closePath();
            cr.setSourceRGBA(c.red / 255, c.green / 255, c.blue / 255, 0.22);
            cr.fill();
            this.values.forEach((v, i) => i === 0 ? cr.moveTo(x0, y(v)) : cr.lineTo(x0 + i * step, y(v)));
            cr.setSourceRGBA(c.red / 255, c.green / 255, c.blue / 255, 1);
            cr.setLineWidth(1.6);
            cr.stroke();
        }
        cr.$dispose();
    }
}

class C12SystemMonitor extends Desklet.Desklet {
    constructor(metadata, deskletId) {
        super(metadata, deskletId);
        Gettext.bindtextdomain(UUID, metadata.path + '/locale');
        this.settings = new Settings.DeskletSettings(this, UUID, deskletId);
        this.settings.bind('interval', 'interval', () => this._restart());
        this.settings.bind('mount-point', 'mountPoint', () => this._update());
        this.settings.bind('show-network', 'showNetwork', () => { this._netRow.visible = this.showNetwork; });

        this._prevCpu = null;
        this._prevNet = null;

        this._box = new St.BoxLayout({ vertical: true, style_class: 'c12-widget c12-sysmon' });
        const header = new St.BoxLayout({ style_class: 'c12-sysmon-header' });
        header.add_child(new St.Icon({ icon_name: 'utilities-system-monitor', icon_size: 18, style_class: 'c12-sysmon-header-icon' }));
        header.add_child(new St.Label({ text: _('System Monitor'), style_class: 'c12-widget-title', y_align: Clutter.ActorAlign.CENTER }));
        this._box.add_child(header);

        this._cpu = this._metric(_('CPU'), 'c12-sysmon-cpu', true);
        this._ram = this._metric(_('RAM'), 'c12-sysmon-ram', true);
        this._disk = this._metric(_('Disk'), 'c12-sysmon-disk', false);

        this._netRow = new St.BoxLayout({ style_class: 'c12-sysmon-net' });
        this._netRow.add_child(new St.Label({ text: _('Network'), style_class: 'c12-sysmon-label', x_expand: true }));
        this._down = new St.Label({ text: '↓ —', style_class: 'c12-sysmon-rate' });
        this._up = new St.Label({ text: '↑ —', style_class: 'c12-sysmon-rate' });
        this._netRow.add_child(this._down);
        this._netRow.add_child(this._up);
        this._box.add_child(this._netRow);
        this._netRow.visible = this.showNetwork;

        this.setContent(this._box);
        this._update();
        this._restart();
    }

    _metric(name, cls, withGraph) {
        const wrap = new St.BoxLayout({ vertical: true, style_class: 'c12-sysmon-metric ' + cls });
        const top = new St.BoxLayout({ style_class: 'c12-sysmon-top' });
        const label = new St.Label({ text: name, style_class: 'c12-sysmon-label', y_align: Clutter.ActorAlign.CENTER });
        const value = new St.Label({ text: '—', style_class: 'c12-sysmon-value', y_align: Clutter.ActorAlign.CENTER, x_expand: true });
        top.add_child(label);
        top.add_child(value);
        let graph = null;
        if (withGraph) { graph = new Sparkline(cls); top.add_child(graph.actor); }
        wrap.add_child(top);
        const track = new St.Widget({ style_class: 'c12-sysmon-bar', x_expand: true });
        const fill = new St.Widget({ style_class: 'c12-sysmon-bar-fill ' + cls });
        track.add_child(fill);
        track.connect('notify::width', () => { if (m.ratio !== undefined) fill.set_width(Math.round(m.ratio * track.width)); });
        wrap.add_child(track);
        this._box.add_child(wrap);
        const m = { value, graph, track, fill, label };
        return m;
    }

    _set(m, ratio, text) {
        m.value.set_text(text);
        m.value.accessible_name = m.label.get_text() + ' ' + text;
        m.ratio = Math.max(0, Math.min(1, ratio));
        if (m.track.get_stage()) m.fill.set_width(Math.round(m.ratio * m.track.width));
        if (m.graph) m.graph.push(ratio);
    }

    _restart() {
        if (this._timer) Mainloop.source_remove(this._timer);
        const secs = Math.max(1, Math.min(5, this.interval || 2));
        this._timer = Mainloop.timeout_add_seconds(secs, () => { this._update(); return true; });
    }

    _update() {
        // CPU
        const line = readText('/proc/stat').split('\n')[0] || '';
        const f = line.trim().split(/\s+/).slice(1).map(Number);
        if (f.length >= 4) {
            const idle = f[3] + (f[4] || 0);
            const total = f.reduce((a, b) => a + b, 0);
            if (this._prevCpu && total > this._prevCpu.total) {
                const r = 1 - (idle - this._prevCpu.idle) / (total - this._prevCpu.total);
                this._set(this._cpu, r, Math.round(r * 100) + '%');
            }
            this._prevCpu = { idle, total };
        }
        // RAM
        const mem = readText('/proc/meminfo');
        const kv = k => { const m = mem.match(new RegExp('^' + k + ':\\s*(\\d+)', 'm')); return m ? Number(m[1]) : 0; };
        const memTotal = kv('MemTotal'), memAvail = kv('MemAvailable');
        if (memTotal) {
            const r = (memTotal - memAvail) / memTotal;
            this._set(this._ram, r, Math.round(r * 100) + '%');
        }
        // Disk
        try {
            const info = Gio.File.new_for_path(this.mountPoint || '/').query_filesystem_info('filesystem::size,filesystem::free', null);
            const size = info.get_attribute_uint64('filesystem::size');
            const free = info.get_attribute_uint64('filesystem::free');
            if (size) {
                const r = (size - free) / size;
                this._set(this._disk, r, Math.round(r * 100) + '%  (' + (this.mountPoint || '/') + ')');
            }
        } catch (e) { this._disk.value.set_text(_('Unavailable')); }
        // Network (all interfaces except loopback)
        if (this.showNetwork) {
            let rx = 0, tx = 0;
            for (const l of readText('/proc/net/dev').split('\n').slice(2)) {
                const m = l.match(/^\s*([^:]+):\s*(.*)$/);
                if (!m || m[1] === 'lo') continue;
                const c = m[2].trim().split(/\s+/).map(Number);
                rx += c[0] || 0; tx += c[8] || 0;
            }
            const now = GLib.get_monotonic_time() / 1e6;
            if (this._prevNet) {
                const dt = Math.max(0.5, now - this._prevNet.t);
                this._down.set_text('↓ ' + formatRate(Math.max(0, rx - this._prevNet.rx) / dt));
                this._up.set_text('↑ ' + formatRate(Math.max(0, tx - this._prevNet.tx) / dt));
            }
            this._prevNet = { rx, tx, t: now };
        }
    }

    on_desklet_removed() {
        if (this._timer) Mainloop.source_remove(this._timer);
        this._timer = 0;
        this.settings.finalize();
    }
}

function main(metadata, deskletId) {
    return new C12SystemMonitor(metadata, deskletId);
}
