/* Cinnamon12 | Simple CPU + memory display from Linux /proc.
 * Average CPU delta from two samples, not an instant GHz or process metric.
 */
const Desklet=imports.ui.desklet;
const St=imports.gi.St;
const GLib=imports.gi.GLib;
const ByteArray=imports.byteArray;
const Mainloop=imports.mainloop;
class C12Performance extends Desklet.Desklet {
    constructor(metadata,deskletId) {
        super(metadata,deskletId);
        this._last=null;
        this._box=new St.BoxLayout({vertical:true,style_class:'c12-widget'});
        this._title=new St.Label({text:'DESEMPENHO',style_class:'c12-widget-title'});
        this._cpu=new St.Label({text:'CPU  •  analisando…',style_class:'c12-widget-secondary'});
        this._ram=new St.Label({text:'RAM  •  analisando…',style_class:'c12-widget-secondary'});
        this._box.add_child(this._title);
        this._box.add_child(this._cpu);
        this._box.add_child(this._ram);
        this.setContent(this._box);
        this._update();
        this._timer=Mainloop.timeout_add_seconds(3,()=> {this._update();return true;});
    }
    _read(file) {
        const [ok,content]=GLib.file_get_contents(file);
        if (!ok) return '';
        return ByteArray.toString(content);
    }
    _update() {
        try {
            const cpu=this._read('/proc/stat').split('\n')[0].trim().split(/\s+/).slice(1).map(Number);
            const idle=cpu[3]+(cpu[4]||0);
            const total=cpu.reduce((a,b)=>a+b,0);
            if(this._last && total > this._last.total) {
                const deltaTotal=total-this._last.total;
                const deltaIdle=idle-this._last.idle;
                const pct=Math.max(0,Math.min(100,(1-deltaIdle/deltaTotal)*100));
                this._cpu.set_text('CPU  •  '+pct.toFixed(0)+' %');
            }
            this._last={idle,total};
            const mem=this._read('/proc/meminfo');
            const val=(key)=>{const m=mem.match(new RegExp('^'+key+':\\s*(\\d+)','m'));return m?Number(m[1]):0;};
            const all=val('MemTotal'), available=val('MemAvailable');
            if(all) this._ram.set_text('RAM  •  '+((all-available)*100/all).toFixed(0)+' %');
        } catch(e) {this._cpu.set_text('Métricas indisponíveis');global.logError(e);}
    }
    on_desklet_removed() {if(this._timer){Mainloop.source_remove(this._timer);this._timer=0;}}
}
function main(metadata,deskletId){return new C12Performance(metadata,deskletId);}
