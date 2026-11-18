/* Cinnamon12 | Calendar desklet - Cinnamon 6.0.x
 * Month view from the system clock and locale. No events, no network.
 */
const Desklet = imports.ui.desklet;
const Settings = imports.ui.settings;
const St = imports.gi.St;
const Clutter = imports.gi.Clutter;
const GLib = imports.gi.GLib;
const Cinnamon = imports.gi.Cinnamon;
const Mainloop = imports.mainloop;
const Gettext = imports.gettext;

const UUID = 'c12-calendar@cinnamon12.local';

function _(s) {
    const t = Gettext.dgettext(UUID, s);
    return t !== s ? t : Gettext.dgettext('cinnamon', s);
}

class C12Calendar extends Desklet.Desklet {
    constructor(metadata, deskletId) {
        super(metadata, deskletId);
        Gettext.bindtextdomain(UUID, metadata.path + '/locale');
        this.settings = new Settings.DeskletSettings(this, UUID, deskletId);
        this.settings.bind('week-start', 'weekStartSetting', () => this._render());
        this.settings.bind('show-week-numbers', 'showWeekNumbers', () => this._render());

        const now = GLib.DateTime.new_now_local();
        this._year = now.get_year();
        this._month = now.get_month();

        this._box = new St.BoxLayout({ vertical: true, style_class: 'c12-widget c12-calendar' });
        const header = new St.BoxLayout({ style_class: 'c12-calendar-header' });
        this._prev = this._navButton('go-previous-symbolic', _('Previous month'), -1);
        this._title = new St.Button({ style_class: 'c12-calendar-title', x_expand: true, can_focus: true });
        this._titleLabel = new St.Label({ x_align: Clutter.ActorAlign.CENTER });
        this._title.set_child(this._titleLabel);
        this._title.accessible_name = _('Today');
        this._title.connect('clicked', () => this._goToday());
        this._next = this._navButton('go-next-symbolic', _('Next month'), 1);
        header.add_child(this._prev);
        header.add_child(this._title);
        header.add_child(this._next);
        this._box.add_child(header);

        this._grid = new St.BoxLayout({ vertical: true, style_class: 'c12-calendar-grid' });
        this._box.add_child(this._grid);
        this.setContent(this._box);

        this._render();
        this._scheduleMidnight();
    }

    _navButton(icon, label, delta) {
        const b = new St.Button({ style_class: 'c12-calendar-nav', can_focus: true });
        b.set_child(new St.Icon({ icon_name: icon, icon_size: 14 }));
        b.accessible_name = label;
        b.connect('clicked', () => {
            this._month += delta;
            if (this._month < 1) { this._month = 12; this._year--; }
            if (this._month > 12) { this._month = 1; this._year++; }
            this._render();
        });
        return b;
    }

    _goToday() {
        const now = GLib.DateTime.new_now_local();
        this._year = now.get_year();
        this._month = now.get_month();
        this._render();
    }

    _weekStart() {
        if (this.weekStartSetting === 'sunday') return 0;
        if (this.weekStartSetting === 'monday') return 1;
        return Cinnamon.util_get_week_start(); // locale / Cinnamon setting
    }

    _render() {
        const today = GLib.DateTime.new_now_local();
        const first = GLib.DateTime.new_local(this._year, this._month, 1, 0, 0, 0);
        let title = first.format('%B %Y');
        this._titleLabel.set_text(title.charAt(0).toUpperCase() + title.slice(1));
        this._grid.destroy_all_children();

        const ws = this._weekStart();
        // weekday headings: 2023-01-01 was a Sunday
        const head = new St.BoxLayout({ style_class: 'c12-calendar-row' });
        if (this.showWeekNumbers) head.add_child(new St.Label({ text: '', style_class: 'c12-calendar-weeknum' }));
        for (let i = 0; i < 7; i++) {
            const d = GLib.DateTime.new_local(2023, 1, 1 + ((ws + i) % 7), 0, 0, 0);
            let name = d.format('%a').replace('.', '');
            head.add_child(new St.Label({ text: name.charAt(0).toUpperCase() + name.slice(1, 3), style_class: 'c12-calendar-dayname' }));
        }
        this._grid.add_child(head);

        // first cell = the week-start day on or before the 1st
        const dow = first.get_day_of_week() % 7; // 0 = Sunday
        let cursor = first.add_days(-((dow - ws + 7) % 7));
        for (let week = 0; week < 6; week++) {
            const row = new St.BoxLayout({ style_class: 'c12-calendar-row' });
            if (this.showWeekNumbers)
                row.add_child(new St.Label({ text: String(cursor.add_days(3).get_week_of_year()), style_class: 'c12-calendar-weeknum' }));
            for (let i = 0; i < 7; i++) {
                const classes = ['c12-calendar-day'];
                if (cursor.get_month() !== this._month) classes.push('c12-calendar-other');
                const dw = cursor.get_day_of_week() % 7;
                if (dw === 0 || dw === 6) classes.push('c12-calendar-weekend');
                if (cursor.get_year() === today.get_year() && cursor.get_day_of_year() === today.get_day_of_year())
                    classes.push('c12-calendar-today');
                row.add_child(new St.Label({ text: String(cursor.get_day_of_month()), style_class: classes.join(' ') }));
                cursor = cursor.add_days(1);
            }
            this._grid.add_child(row);
        }
    }

    _scheduleMidnight() {
        const now = GLib.DateTime.new_now_local();
        const secs = (24 * 3600) - (now.get_hour() * 3600 + now.get_minute() * 60 + now.get_second()) + 2;
        this._timer = Mainloop.timeout_add_seconds(secs, () => {
            this._goToday();
            this._scheduleMidnight();
            return false;
        });
    }

    on_desklet_removed() {
        if (this._timer) Mainloop.source_remove(this._timer);
        this._timer = 0;
        this.settings.finalize();
    }
}

function main(metadata, deskletId) {
    return new C12Calendar(metadata, deskletId);
}
