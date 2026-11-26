"""AF-area buttons in the LCD module: offline audit (MIT).

Same fixture as audit_z7_lcd_shutter_sound.py (the 277-check display suite runs
first, unchanged). Then, with the module's real menu handlers and the display
fixture's supplied property getter/setter (0x104065A4/0x104065B0) holding
AF-area 0x568, focus mode 0x567 and the f2 assignments 0x1048/0x104C/0x1050/
0x1054/0x1057 (Nikon's real getter mapping for these keys is checked by
audit_z7_af_area_apply.py and the f2 menu walks):
 - the root's last row reads "Extras" and opens Shutter volume / Shutter sound /
   AF-area buttons / Back; volume and sound still step as before;
 - AF-area buttons lists Fn1, Fn2, AF-ON, sub-selector centre and movie record,
   each stepping OFF, Pinpoint, Single, Dynamic, Wide S, Wide L, Auto;
 - Back returns Extras (focus on AF-area buttons) and then the root;
 - the choice is saved to A:\\Z7AFB.DAT only after a change, restored at power
   on, and a corrupt file means all OFF;
 - a press of an assigned button, in photo mode, sets the AF-area once (press
   edge, not hold); not in movie mode, not when Nikon's f2 assignment for that
   button is not None, not for a mode the current focus mode greys out;
 - nothing runs on a getter/setter firmware mismatch.
No camera, no card.
"""
import argparse,hashlib,json,struct,sys
import audit_z7_lcd_preset_persistence as preset_suite
from pathlib import Path
from audit_z7_lcd_shutter_sound import SoundAware,WAV
import audit_z7_lcd_shutter_sound as shutter
from audit_z7_lcd_grid_persistence import NEW,OBJECT,v3record
from audit_z7_settings_files import PATHS
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output

AFB='A:'+chr(92)+'Z7AFB.DAT'
SW={0:(0xa1f90aa4,0x4000),1:(0xa1f90acc,0x4000),2:(0xa1f90aa4,0x200000),3:(0xa1f90acc,0x8000),4:(0xa1f90ab8,0x2000)}
TEXT=['OFF','Pinpt','Single','Dynamic','Wide-S','Wide-L','Auto']
AREAS=[None,0,1,2,3,4,6]


def record(state):
    check=(0x42464137^(1<<8)^((state*0x9e3779b1)&0xffffffff)^0x5a5a5a5a)&0xffffffff
    return struct.pack('<4I',0x42464137,1,state,check)


class AfAware(SoundAware):
    def __init__(self,*a,**k):
        super().__init__(*a,**k)
        try:self.u.mem_map(0xa1f90000,0x10000)
        except Exception:pass
        self.properties.update({0x567:1,0x568:1})
    @property
    def sets(self):return [w for w in self.property_writes if w[0]==0x568]


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('host','module','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text());raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    m=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256'] and hashlib.sha256(packet).hexdigest()==m['module_sha256']
    assert m['configuration'].get('af_buttons')
    symbols=m['symbols'];checks=[]
    def check(name,ok):
        assert ok,name
        checks.append(name)
    suite_out=out.with_name(out.stem+'-preset-suite.json')
    preset_suite.PersistenceFixture=AfAware;AfAware.sound_files={}
    argv=sys.argv;sys.argv=['x','--host',str(a.host),'--module',str(a.module),'--output',str(suite_out)]
    try:preset_suite.main()
    finally:sys.argv=argv
    suite=json.loads(suite_out.read_text())
    check('display-preset-suite-passes-unchanged',suite['passed'] and suite['checks']>=270)
    journal={NEW[0]:v3record((3,15,1,0,5,0,127,7,0,127,4),0)}
    clip=shutter.wav([((i*37)%20000)-10000 for i in range(480)])
    def load(files=None,patch=None,**kw):
        AfAware.sound_files={WAV:clip,**(files or {})}
        f=AfAware(raw,h,packet,dict(journal),**kw);f.file_paths=PATHS+NEW
        if patch:f.u.mem_write(patch,bytes(4))
        assert f.call(h['symbols']['z7_module_load_once'],STATE)==8
        f.base=f.words()[12];f.setword(40,8);f.write(f.base+symbols['sm_lcd_rows_ready'],1);return f
    def word(f,n):return f.read(f.base+symbols[n])
    def labels(f):
        f.menu_labels.clear();f.call(f.base+symbols['sm_render'],OBJECT);return dict(f.menu_labels)
    def press(f,row):
        f.u.mem_write(OBJECT+22,struct.pack('<2H',row,0));f.call(f.base+symbols['sm_activate'])
    def back(f):f.call(f.base+symbols['sm_back_event'])
    def ticks(f,n=1):
        for _ in range(n):f.call(h['symbols']['z7_module_worker_tick'])
    def update(f):f.call(f.base+symbols['readouts_before'])
    def button(f,row,down):
        w,mask=SW[row];v=struct.unpack('<I',bytes(f.u.mem_read(w,4)))[0]
        f.u.mem_write(w,struct.pack('<I',(v|mask) if down else (v&~mask)))
    def tap(f,row):button(f,row,1);update(f);button(f,row,0);update(f)
    def area(f):return f.properties.get(0x568)

    f=load()
    check('loads-ready-all-off',word(f,'z7_ab_ready')==1 and word(f,'z7_ab_state')==0 and word(f,'z7_ab_loaded')==0)
    lab=labels(f);check('root-last-row-is-extras',lab.get(237)=='Extras' and lab.get(244)=='')
    press(f,6);lab=labels(f)
    check('extras-page',word(f,'z7_settings_view')==5 and lab.get(230)=='Extras' and
          [lab.get(231+i) for i in range(4)]==['Shutter volume','Shutter sound','AF-area buttons','Back'] and lab.get(238)=='5')
    press(f,0);check('extras-volume-still-steps',word(f,'z7_sl_level')==6)
    press(f,2);lab=labels(f)
    check('af-page',word(f,'z7_settings_view')==6 and lab.get(230)=='AF-area buttons' and
          [lab.get(231+i) for i in range(6)]==['Fn1 button','Fn2 button','AF-ON button','Sub-selector center','Movie-record button','Back'] and
          all(lab.get(238+i)=='OFF' for i in range(5)))
    for i in range(1,7):
        press(f,0);check(f'fn1-steps-to-{TEXT[i]}',labels(f).get(238)==TEXT[i] and word(f,'z7_ab_state')==i)
    press(f,0);check('fn1-wraps-to-off',labels(f).get(238)=='OFF' and word(f,'z7_ab_state')==0)
    for _ in range(5):press(f,0)                        # Fn1 -> Wide-area L
    for _ in range(4):press(f,4)                        # movie -> Wide-area S
    press(f,2)                                          # AF-ON -> Pinpoint
    st=5|(1<<6)|(4<<12)
    check('state-packs-three-bits-per-button',word(f,'z7_ab_state')==st)
    press(f,5);check('back-row-returns-extras',word(f,'z7_settings_view')==5)
    press(f,2);back(f);check('back-key-returns-extras',word(f,'z7_settings_view')==5)
    back(f);check('back-from-extras-to-root',word(f,'z7_settings_view')==0)
    check('nothing-saved-yet',AFB not in f.sound_files)
    ticks(f,5);check('saved-after-change',f.sound_files.get(AFB)==record(st))
    n=len([e for e in f.sound_events if e[0]=='create' and e[1]==AFB]);ticks(f,6)
    check('no-rewrite-without-change',len([e for e in f.sound_events if e[0]=='create' and e[1]==AFB])==n)
    # Runtime (AF-S, area single).
    tap(f,0);check('fn1-press-sets-wide-l',area(f)==4 and f.sets[-1]==(0x568,4))
    f.properties[0x568]=1;k=len(f.sets);button(f,0,1);update(f)
    f.properties[0x568]=1;update(f);update(f);button(f,0,0);update(f)
    check('hold-acts-once-per-press',len(f.sets)==k+1 and area(f)==1)
    k=len(f.sets);tap(f,0);check('already-selected-no-write',len(f.sets)==k+1 and area(f)==4)
    k=len(f.sets);tap(f,0);check('already-selected-skips-setter',len(f.sets)==k)
    tap(f,4);check('movie-press-sets-wide-s',area(f)==3)
    tap(f,2);check('af-on-pinpoint-in-af-s',area(f)==0)
    f.properties[0x567]=2;k=len(f.sets);tap(f,2)
    check('pinpoint-refused-in-af-c',area(f)==0 and len(f.sets)==k)
    f.properties[0x567]=1
    tap(f,1);check('unassigned-button-does-nothing',area(f)==0)
    f.properties[0x1048]=0x1f;k=len(f.sets);tap(f,0)
    check('native-f2-assignment-wins',len(f.sets)==k and area(f)==0)
    f.properties[0x1048]=0
    f.u.mem_write(0xa201d4d0+0x40,bytes([1]));k=len(f.sets);tap(f,0)
    check('movie-mode-does-nothing',len(f.sets)==k)
    f.u.mem_write(0xa201d4d0+0x40,bytes([0]));f.u.mem_write(0xa18237c6,bytes([1]));tap(f,0)
    check('menu-or-playback-does-nothing',len(f.sets)==k)
    f.u.mem_write(0xa18237c6,bytes([0]));tap(f,0);check('photo-again-acts',area(f)==4)
    # Reload.
    g=load({AFB:record(st)})
    check('reload-restores',word(g,'z7_ab_state')==st and word(g,'z7_ab_loaded')==1)
    press(g,6);press(g,2);lab=labels(g)
    check('reload-shows-choices',lab.get(238)=='Wide-L' and lab.get(240)=='Pinpt' and lab.get(242)=='Wide-S')
    tap(g,0);check('reload-acts',area(g)==4)
    bad=bytearray(record(st));bad[12]^=1
    g=load({AFB:bytes(bad)});check('corrupt-file-all-off',word(g,'z7_ab_state')==0 and word(g,'z7_ab_loaded')==2)
    g=load({AFB:record(7)});check('invalid-choice-all-off',word(g,'z7_ab_state')==0 and word(g,'z7_ab_loaded')==2)
    # Firmware mismatch: feature off, menu says so.
    g=load({AFB:record(st)},patch=0x104065a4)
    check('mismatch-feature-off',word(g,'z7_ab_ready')==0)
    press(g,6);press(g,2);check('mismatch-shows-dashes',labels(g).get(238)=='--')
    tap(g,0);check('mismatch-no-write',not g.sets)
    report=dict(passed=True,count=len(checks),checks=checks,display_suite_checks=suite['checks'],module_sha256=m['module_sha256'],host_main_sha256=h['main_payload_sha256'],
                camera_access=False,scope=__doc__)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
