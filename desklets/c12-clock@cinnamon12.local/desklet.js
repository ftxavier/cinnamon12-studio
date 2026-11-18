/* Cinnamon12 | Local clock desklet. No network access. */
const Desklet=imports.ui.desklet;
const St=imports.gi.St;
const Mainloop=imports.mainloop;
class C12Clock extends Desklet.Desklet {
    constructor(metadata, deskletId) {
        super(metadata, deskletId);
        this._box=new St.BoxLayout({vertical:true, style_class:'c12-widget'});
        this._title=new St.Label({text:'HOJE',style_class:'c12-widget-title'});
        this._time=new St.Label({text:'--:--',style_class:'c12-widget-main'});
        this._date=new St.Label({text:'',style_class:'c12-widget-secondary'});
        this._box.add_child(this._title);
        this._box.add_child(this._time);
        this._box.add_child(this._date);
        this.setContent(this._box);
        this._update();
        this._timer=Mainloop.timeout_add_seconds(10,()=> { this._update(); return true; });
    }
    _update() {
        const date=new Date();
        this._time.set_text(date.toLocaleTimeString('pt-BR',{hour:'2-digit',minute:'2-digit'}));
        this._date.set_text(date.toLocaleDateString('pt-BR',{weekday:'long',day:'numeric',month:'long'}));
    }
    on_desklet_removed() { if (this._timer) {Mainloop.source_remove(this._timer);this._timer=0;} }
}
function main(metadata,deskletId) { return new C12Clock(metadata,deskletId); }
