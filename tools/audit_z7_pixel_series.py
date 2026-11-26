"""Pixel-shift series dry run (step 3a): offline audit (MIT).

Simulated body-VR unit and D2 sender as audit_z7_vr_restore.py; photos are
delivered through the module's real still-file hook (slot 0xA18D2750, event
0x041E0002) exactly as the upside-down playback audit does. Checks that the
module holds Bayer position 0 after arming, steps through the four corners
{0,0},{21,0},{21,18},{0,18} (upstream's Z7II scale) only after each new photo,
ignores photos before arming and repeated records, re-sends a lost hold
(bounded), stops on a missing photo, always recentres and restores D2 once,
logs the four still keys, and never moves without a D2 snapshot.
No camera, no card, no sensor movement.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from audit_z7_vr_restore import D2Unit,R,SEL,FLAGS
from audit_z7_vr_move import CENTRE,F,LOG,SLOT,BUSY,MAGIC
from audit_z7_lcd_shutter_sound import WAV
from audit_z7_lcd_grid_persistence import NEW,v3record
from audit_z7_settings_files import PATHS
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output

SSLOT,STILL=0xa18d2750,0x041e0002
S=dict(SERIES_STARTED=1<<16,FRAME_TIMEOUT=1<<17,HOLD_LOST=1<<18,SERIES_COMPLETE=1<<19,POSITION_MISSED=1<<20,MOVED_LATE=1<<21)
CORNERS=[(0,0),(21,0),(21,18),(0,18)]
def pos(x,y):return bytes([0,x,0,y,0,16,16,0,0,2])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('host','module','output','clip'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text());raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    m=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256'] and hashlib.sha256(packet).hexdigest()==m['module_sha256']
    assert m['configuration'].get('pixel_series')
    clip=a.clip.read_bytes();symbols=m['symbols'];checks=[]
    def check(name,ok):
        assert ok,name
        checks.append(name)
    journal={NEW[0]:v3record((3,15,1,0,5,0,127,7,0,127,4),0)}
    def load(**kw):
        D2Unit.sound_files={WAV:clip}
        f=D2Unit(raw,h,packet,dict(journal),**kw);f.file_paths=PATHS+NEW
        f.u.mem_write(SLOT,bytes(4));f.u.mem_write(BUSY,bytes(4))
        assert f.call(h['symbols']['z7_module_load_once'],STATE)==8
        f.base=f.words()[12];f.setword(40,8);f.reply_addr=f.base+symbols['z7_vm_reply'];f.called_addr=f.base+symbols['z7_vm_d2_called']
        f.shots=0;return f
    def tick(f,n=1):
        for _ in range(n):f.call(h['symbols']['z7_module_worker_tick'])
    def photo(f,key=None):
        f.shots+=1;key=key or ((0x2000+f.shots)<<5)|1
        pk=0xa18d8400;f.u.mem_write(pk,struct.pack('<2I',key,1))
        r=f.call(f.read(SSLOT),STILL,pk,0,0);return r,key&0x7fffffe0
    def moves(f):return [r['payload'] for r in f.requests if r['opcode']==0xf1f1]
    def log(f):
        d=f.sound_files.get(LOG,b'')
        if len(d)<72:return None
        head=struct.unpack('<18I',d[:72]);ents=[]
        for i in range(head[2]):
            e=d[72+56*i:72+56*i+56];ents.append(dict(tick=struct.unpack('<I',e[:4])[0],phase=e[4],poll=e[5],status=struct.unpack('<H',e[6:8])[0],bytes=e[8:50]))
        return dict(version=head[1],entries=head[2],flags=head[3],d2=head[8],frames=head[12],resends=head[13],keys=list(head[14:18]),entry=ents,size=len(d),magic=head[0])

    # 1. Full series.
    f=load()
    check('still-hook-installed',f.read(SSLOT)!=0x104db211)
    r,_=photo(f);check('photo-before-arming-ignored-native-runs',r==0x602)
    tick(f)
    check('arms-then-holds-position-0',moves(f)==[pos(0,0)])
    keys=[]
    for i in range(1,4):
        _,k=photo(f);keys.append(k);tick(f)
        check(f'photo-{i}-steps-to-corner-{i}',moves(f)[-1]==pos(*CORNERS[i]) and len(moves(f))==i+1)
    check('no-restore-during-series',not f.d2_calls)
    _,k=photo(f);keys.append(k);tick(f)
    check('fourth-photo-centres',moves(f)==[pos(*c) for c in CORNERS]+[CENTRE])
    check('restore-once-with-snapshot',len(f.d2_calls)==1 and f.d2_calls[0]['selection']==bytes(SEL) and f.d2_calls[0]['flags']==FLAGS)
    tick(f,32);L=log(f)
    check('log-v3-layout',L and L['magic']==MAGIC and L['version']==3 and L['size']==72+128*56)
    check('four-keys-in-order',L['frames']==4 and L['keys']==keys)
    want=S['SERIES_STARTED']|S['SERIES_COMPLETE']
    check('flags-series-complete',L['flags']&want==want and L['flags']&R['RESTORED'] and L['flags']&F['CENTRE_FOLLOWED'] and
          not L['flags']&(S['FRAME_TIMEOUT']|S['HOLD_LOST']|S['POSITION_MISSED']|S['MOVED_LATE']))
    frames=[e for e in L['entry'] if e['phase']==7]
    check('frame-entries-logged',[e['poll'] for e in frames]==[1,2,3,4])
    n=len(f.requests);photo(f);tick(f,5);check('quiet-after-done',len(f.requests)==n and len(moves(f))==5)
    # 2. Same record twice counts once.
    g=load();tick(g);photo(g,key=(0x3000<<5)|1);photo(g,key=(0x3000<<5)|1);tick(g)
    check('repeated-record-counts-once',moves(g)==[pos(0,0),pos(21,0)])
    # 3. Missing photo: timeout, centre, restore.
    g=load();tick(g);photo(g);tick(g);tick(g,121)
    L=log(g);check('timeout-centres-and-restores',moves(g)[-1]==CENTRE and L['flags']&S['FRAME_TIMEOUT'] and len(g.d2_calls)==1 and L['frames']==1)
    # 4. Hold lost while waiting: re-send, bounded.
    g=load();tick(g);photo(g);tick(g)
    g.state=1;tick(g)
    check('lost-hold-resent',moves(g)[-1]==pos(21,0) and len(moves(g))==3)
    for _ in range(10):g.state=1;tick(g)
    L=log(g);check('resends-bounded',len(moves(g))==2+6 and L['resends']==6 and L['flags']&S['HOLD_LOST'])
    # 5. Two photos in one tick.
    g=load();tick(g);photo(g);photo(g);tick(g)
    L=log(g);check('two-photos-one-tick-flagged',L['flags']&S['MOVED_LATE'] and moves(g)[-1]==pos(21,18))
    # 6. No D2: never moves, photos ignored.
    g=load(d2=(0,0,0));tick(g,2);photo(g);tick(g,2)
    check('no-d2-never-moves',not moves(g) and not g.d2_calls)
    report=dict(passed=True,count=len(checks),checks=checks,module_sha256=m['module_sha256'],host_main_sha256=h['main_payload_sha256'],
                corners=CORNERS,camera_access=False,sensor_moved=False,scope=__doc__)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
