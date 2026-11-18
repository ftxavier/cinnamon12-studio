/* Cinnamon12 | Weather desklet - Cinnamon 6.0.x
 *
 * Privacy / network policy:
 *  - OFF by default. Nothing is requested until the user types a city AND enables
 *    "Allow network access" in the desklet settings.
 *  - Provider: Open-Meteo (https://open-meteo.com), free, no API key, no account.
 *    The city name is sent to the Open-Meteo geocoding API once; afterwards only the
 *    resulting coordinates are sent to the forecast API. No automatic geolocation.
 *  - Results are cached in $XDG_CACHE_HOME/cinnamon12/weather-<id>.json and refreshed
 *    at most every N minutes (minimum 30). Offline/failed requests show the cached
 *    data (marked as such) or "unavailable".
 */
const Desklet = imports.ui.desklet;
const Settings = imports.ui.settings;
const St = imports.gi.St;
const Clutter = imports.gi.Clutter;
const Gio = imports.gi.Gio;
const GLib = imports.gi.GLib;
const Soup = imports.gi.Soup;
const Mainloop = imports.mainloop;
const Gettext = imports.gettext;

const UUID = 'c12-weather@cinnamon12.local';
const MIN_REFRESH_MIN = 30;

function _(s) {
    const t = Gettext.dgettext(UUID, s);
    return t !== s ? t : Gettext.dgettext('cinnamon', s);
}

// WMO weather interpretation codes -> [description, freedesktop icon (day), (night)]
const WMO = {
    0: ['Clear sky', 'weather-clear', 'weather-clear-night'],
    1: ['Mainly clear', 'weather-few-clouds', 'weather-few-clouds-night'],
    2: ['Partly cloudy', 'weather-few-clouds', 'weather-few-clouds-night'],
    3: ['Overcast', 'weather-overcast', 'weather-overcast'],
    45: ['Fog', 'weather-fog', 'weather-fog'], 48: ['Fog', 'weather-fog', 'weather-fog'],
    51: ['Drizzle', 'weather-showers-scattered', 'weather-showers-scattered'],
    53: ['Drizzle', 'weather-showers-scattered', 'weather-showers-scattered'],
    55: ['Drizzle', 'weather-showers-scattered', 'weather-showers-scattered'],
    56: ['Freezing drizzle', 'weather-showers-scattered', 'weather-showers-scattered'],
    57: ['Freezing drizzle', 'weather-showers-scattered', 'weather-showers-scattered'],
    61: ['Light rain', 'weather-showers-scattered', 'weather-showers-scattered'],
    63: ['Rain', 'weather-showers', 'weather-showers'], 65: ['Heavy rain', 'weather-showers', 'weather-showers'],
    66: ['Freezing rain', 'weather-showers', 'weather-showers'], 67: ['Freezing rain', 'weather-showers', 'weather-showers'],
    71: ['Light snow', 'weather-snow', 'weather-snow'], 73: ['Snow', 'weather-snow', 'weather-snow'],
    75: ['Heavy snow', 'weather-snow', 'weather-snow'], 77: ['Snow grains', 'weather-snow', 'weather-snow'],
    80: ['Rain showers', 'weather-showers', 'weather-showers'], 81: ['Rain showers', 'weather-showers', 'weather-showers'],
    82: ['Violent rain showers', 'weather-showers', 'weather-showers'],
    85: ['Snow showers', 'weather-snow', 'weather-snow'], 86: ['Snow showers', 'weather-snow', 'weather-snow'],
    95: ['Thunderstorm', 'weather-storm', 'weather-storm'],
    96: ['Thunderstorm with hail', 'weather-storm', 'weather-storm'],
    99: ['Thunderstorm with hail', 'weather-storm', 'weather-storm'],
};

function wmo(code, isDay) {
    const e = WMO[code] || ['Unknown', 'weather-severe-alert', 'weather-severe-alert'];
    return { text: _(e[0]), icon: isDay === false ? e[2] : e[1] };
}

class C12Weather extends Desklet.Desklet {
    constructor(metadata, deskletId) {
        super(metadata, deskletId);
        Gettext.bindtextdomain(UUID, metadata.path + '/locale');
        this._id = deskletId;
        this.settings = new Settings.DeskletSettings(this, UUID, deskletId);
        this.settings.bind('allow-network', 'allowNetwork', () => this._onConfigChanged());
        this.settings.bind('city', 'city', () => this._onConfigChanged(true));
        this.settings.bind('units', 'units', () => this._onConfigChanged());
        this.settings.bind('refresh-minutes', 'refreshMinutes', () => this._schedule());

        const cacheDir = GLib.build_filenamev([GLib.get_user_cache_dir(), 'cinnamon12']);
        GLib.mkdir_with_parents(cacheDir, 0o700);
        this._cacheFile = GLib.build_filenamev([cacheDir, `weather-${deskletId}.json`]);

        this._buildUi();
        this._cache = this._loadCache();
        this._render();
        this._onConfigChanged();
    }

    // ------------------------------------------------------------------ UI
    _buildUi() {
        this._box = new St.BoxLayout({ vertical: true, style_class: 'c12-widget c12-weather' });
        const top = new St.BoxLayout({ style_class: 'c12-weather-top' });
        top.add_child(new St.Icon({ icon_name: 'mark-location-symbolic', icon_size: 14, style_class: 'c12-weather-pin' }));
        this._place = new St.Label({ style_class: 'c12-weather-place', y_align: Clutter.ActorAlign.CENTER, x_expand: true });
        top.add_child(this._place);
        this._box.add_child(top);

        const now = new St.BoxLayout({ style_class: 'c12-weather-now' });
        this._icon = new St.Icon({ icon_name: 'weather-few-clouds', icon_size: 48, style_class: 'c12-weather-icon' });
        const text = new St.BoxLayout({ vertical: true, y_align: Clutter.ActorAlign.CENTER, x_expand: true });
        this._temp = new St.Label({ style_class: 'c12-widget-main' });
        this._desc = new St.Label({ style_class: 'c12-widget-secondary' });
        text.add_child(this._temp);
        text.add_child(this._desc);
        this._range = new St.Label({ style_class: 'c12-weather-range', y_align: Clutter.ActorAlign.CENTER });
        now.add_child(this._icon);
        now.add_child(text);
        now.add_child(this._range);
        this._box.add_child(now);

        this._forecast = new St.BoxLayout({ style_class: 'c12-weather-forecast' });
        this._box.add_child(this._forecast);
        this._footer = new St.Label({ style_class: 'c12-weather-footer' });
        this._footer.clutter_text.line_wrap = true;
        this._footer.clutter_text.ellipsize = 0;
        this._box.add_child(this._footer);
        this.setContent(this._box);
    }

    _render(note) {
        this._forecast.destroy_all_children();
        if (!this.allowNetwork || !this.city || !this.city.trim()) {
            this._place.set_text(_('Weather'));
            this._icon.icon_name = 'weather-few-clouds-symbolic';
            this._temp.set_text('—');
            this._desc.set_text(_('Disabled'));
            this._range.set_text('');
            this._footer.set_text(_('Choose a city and allow network access in this desklet\'s settings (data: Open-Meteo).'));
            return;
        }
        const c = this._cache;
        if (!c || !c.current || c.key !== this._cacheKey()) {
            this._place.set_text(this.city);
            this._temp.set_text('—');
            this._desc.set_text(note || _('Loading…'));
            this._range.set_text('');
            this._footer.set_text('Open-Meteo');
            return;
        }
        const unit = this.units === 'fahrenheit' ? '°F' : '°C';
        const cur = wmo(c.current.weather_code, c.current.is_day === 1);
        this._place.set_text(c.place);
        this._icon.icon_name = cur.icon;
        this._temp.set_text(Math.round(c.current.temperature_2m) + ' ' + unit);
        this._desc.set_text(cur.text);
        const d = c.daily;
        this._range.set_text('↑ ' + Math.round(d.temperature_2m_max[0]) + '°\n↓ ' + Math.round(d.temperature_2m_min[0]) + '°');
        for (let i = 1; i < Math.min(6, d.time.length); i++) {
            const day = new St.BoxLayout({ vertical: true, style_class: 'c12-weather-day', x_expand: true });
            const [y, m, dd] = d.time[i].split('-').map(Number);
            let name = GLib.DateTime.new_local(y, m, dd, 12, 0, 0).format('%a').replace('.', '');
            day.add_child(new St.Label({ text: name.charAt(0).toUpperCase() + name.slice(1, 3), style_class: 'c12-weather-day-name', x_align: Clutter.ActorAlign.CENTER }));
            day.add_child(new St.Icon({ icon_name: wmo(d.weather_code[i], true).icon, icon_size: 22, x_align: Clutter.ActorAlign.CENTER }));
            day.add_child(new St.Label({ text: Math.round(d.temperature_2m_max[i]) + '°', style_class: 'c12-weather-day-temp', x_align: Clutter.ActorAlign.CENTER }));
            this._forecast.add_child(day);
        }
        const when = GLib.DateTime.new_from_unix_local(c.fetched).format('%H:%M');
        this._footer.set_text((note ? note + ' · ' : '') + _('Updated') + ' ' + when + ' · Open-Meteo');
    }

    // ------------------------------------------------------------------ data
    _cacheKey() { return (this.city || '').trim().toLowerCase() + '|' + this.units; }

    _loadCache() {
        try {
            const [ok, bytes] = GLib.file_get_contents(this._cacheFile);
            return ok ? JSON.parse(new TextDecoder().decode(bytes)) : null;
        } catch (e) { return null; }
    }

    _saveCache() {
        try { GLib.file_set_contents(this._cacheFile, JSON.stringify(this._cache)); } catch (e) { /* ignore */ }
    }

    _onConfigChanged(cityChanged) {
        if (cityChanged && this._cache && this._cache.key !== this._cacheKey()) this._cache = null;
        this._render();
        this._schedule();
    }

    _schedule() {
        if (this._timer) { Mainloop.source_remove(this._timer); this._timer = 0; }
        if (!this.allowNetwork || !this.city || !this.city.trim()) return;
        const every = Math.max(MIN_REFRESH_MIN, this.refreshMinutes || 60) * 60;
        const age = this._cache && this._cache.key === this._cacheKey() ? GLib.get_real_time() / 1e6 - this._cache.fetched : Infinity;
        const first = age >= every ? 1 : Math.ceil(every - age);
        this._timer = Mainloop.timeout_add_seconds(first, () => {
            this._timer = 0;
            this._refresh();
            return false;
        });
    }

    _session() {
        if (!this._soup) {
            this._soup = new Soup.Session({ timeout: 15, user_agent: 'Cinnamon12-Weather/0.4 (Cinnamon desklet)' });
        }
        return this._soup;
    }

    _getJson(url, cb) {
        const msg = Soup.Message.new('GET', url);
        this._session().send_and_read_async(msg, GLib.PRIORITY_DEFAULT, null, (s, res) => {
            try {
                const bytes = s.send_and_read_finish(res);
                if (msg.get_status() !== 200) throw new Error('HTTP ' + msg.get_status());
                cb(null, JSON.parse(new TextDecoder().decode(bytes.get_data())));
            } catch (e) { cb(e, null); }
        });
    }

    _refresh() {
        const key = this._cacheKey();
        const done = (note) => { this._render(note); this._schedule(); };
        const fetchForecast = (geo) => {
            const temp = this.units === 'fahrenheit' ? '&temperature_unit=fahrenheit' : '';
            const url = `https://api.open-meteo.com/v1/forecast?latitude=${geo.lat}&longitude=${geo.lon}` +
                '&current=temperature_2m,weather_code,is_day&daily=weather_code,temperature_2m_max,temperature_2m_min' +
                `&timezone=auto&forecast_days=6${temp}`;
            this._getJson(url, (err, data) => {
                if (err || !data.current) { done(_('Offline – showing last data')); return; }
                this._cache = { key, place: geo.place, lat: geo.lat, lon: geo.lon,
                    fetched: Math.floor(GLib.get_real_time() / 1e6), current: data.current, daily: data.daily };
                this._saveCache();
                done();
            });
        };
        if (this._cache && this._cache.key === key && this._cache.lat !== undefined) {
            fetchForecast({ lat: this._cache.lat, lon: this._cache.lon, place: this._cache.place });
            return;
        }
        const lang = (GLib.get_language_names()[0] || 'en').split(/[_.@]/)[0];
        const url = 'https://geocoding-api.open-meteo.com/v1/search?count=1&format=json&language=' + encodeURIComponent(lang) +
            '&name=' + encodeURIComponent(this.city.trim());
        this._getJson(url, (err, data) => {
            if (err) { done(_('Weather unavailable')); return; }
            const r = data.results && data.results[0];
            if (!r) { done(_('City not found')); return; }
            const place = [r.name, r.admin1 && r.admin1 !== r.name ? r.admin1 : null, r.country_code].filter(Boolean).join(', ');
            fetchForecast({ lat: r.latitude, lon: r.longitude, place });
        });
    }

    on_desklet_removed() {
        if (this._timer) Mainloop.source_remove(this._timer);
        this._timer = 0;
        if (this._soup) this._soup.abort();
        this.settings.finalize();
    }
}

function main(metadata, deskletId) {
    return new C12Weather(metadata, deskletId);
}
