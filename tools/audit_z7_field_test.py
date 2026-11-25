"""Shutter-sound field-test module audit: chime preview + trigger probe (MIT).

Executes the original-Z7 host loader and worker tick, the compiled field-test
module, Nikon's sound post, dispatcher and completion, the property getter
wrappers and the native file create/write/close wrappers. Supplied boundaries are
the union of audit_z7_shutter_sound_playback.py and audit_z7_trigger_probe.py.
No camera, no card, no capture pipeline.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from audit_z7_shutter_sound_playback import SoundFixture,WAV_PATH,wav,DISPATCH,CONTEXT,STATE_ADDR,SLOT as SOUND_SLOT
from audit_z7_trigger_probe import ProbeFixture,SLOTS,NATIVE,LOG,PACKET
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output
from read_z7_trigger_log import parse
from analyze_z7_field_test import analyze
from audit_z7_exif_orientation import SLOT as EXIF_SLOT,DESCRIPTOR


class FieldFixture(ProbeFixture,SoundFixture):
    def __init__(self,raw,host,packet,files=None,silent=0,slot_values=NATIVE,log_faults=None,**sound):
        SoundFixture.__init__(self,raw,host,packet,files=files,**sound)
        self.probe_setup(slot_values,silent,log_faults,None)
        self.u.mem_write(EXIF_SLOT,struct.pack('<4I',*DESCRIPTOR))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('host','module','output'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--clip',type=Path,required=True,help='Exact SHUTTER1.WAV intended for the card')
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text());raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256']
    m=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(packet).hexdigest()==m['module_sha256'] and m['kind']=='original-Z7-shutter-sound-field-test'
    clip=a.clip.read_bytes()
    checks=[]
    def check(name,ok):
        assert ok,name
        checks.append(name)
    def load(files=None,**kw):
        f=FieldFixture(raw,h,packet,files={WAV_PATH:clip} if files is None else files,**kw)
        f.loaded=f.call(h['symbols']['z7_module_load_once'],STATE);f.setword(40,f.loaded)
        f.base=f.words()[12];f.s=m['symbols'];return f
    def sym(f,n):return f.base+f.s[n]
    def val(f,n):return f.read(sym(f,n))
    def tick(f,n=1):
        for _ in range(n):f.call(h['symbols']['z7_module_worker_tick'])
    def log(f):return parse(f.log_files[LOG])

    f=load()
    check('module-loads',f.loaded==8)
    check('sound-intercept-installed',val(f,'z7_sound_installed')==1 and f.read(SOUND_SLOT)==(sym(f,'z7_sound_start')|1))
    check('three-trigger-wrappers-installed',all(f.read(s)&1 and f.read(s)!=n for s,n in zip(SLOTS,NATIVE)) and val(f,'z7_trig_init_result')==7)
    check('only-shutter1-read-and-nothing-written-at-load',[e[0] for e in f.file_events]==['open','read','close'] and not f.log_events)
    tick(f,3)
    first=log(f)
    check('first-log-carries-sound-state',first['sound']==dict(preview='not yet',installed=True,wav_loaded=True,starts=0,rejects=0,finished=0,native_passthrough=0,exif_orientation_installed=True))
    tick(f,4)
    check('no-preview-before-tick-8',not f.sends)
    tick(f)
    check('preview-queued-on-tick-8',len(f.sends)==1 and val(f,'z7_sound_boot_queued')==1)
    f.call(DISPATCH,f.sends[0][1])
    check('preview-programs-native-setters',[c[0] for c in f.setter_calls]==['format','tones','data','dma-start'])
    f.call(f.read(CONTEXT+32),0x04180023,0);f.u.mem_write(STATE_ADDR,b'\0\0\0')
    # A native beep passes through the intercept and is counted.
    nj=0xa2970000;f.u.mem_write(nj,bytes(16));nm=0xa2970100;f.u.mem_write(nm,struct.pack('<7I',0,0,0,0,0x0418001e,nj,nm))
    f.call(DISPATCH,nm)
    # A still-file notification is logged and passed to Nikon, with no sound.
    f.u.mem_write(PACKET,struct.pack('<2I',(1<<29)|(5<<19)|(77<<5)|3,1))
    r=f.call(f.read(SLOTS[2]),0x041e0002,PACKET,0,0)
    check('trigger-event-passed-through-without-sound',r==0x602 and len(f.sends)==1 and f.native_calls[-1][:2]==(2,0x041e0002))
    # Counters publish after each tick's write, so they reach the card on the next
    # write window (ticks 9 and 12 here).
    tick(f,4);later=log(f)
    check('log-shows-preview-started-and-finished',later['sound']==dict(preview='queued',installed=True,wav_loaded=True,starts=1,rejects=0,finished=1,native_passthrough=1,exif_orientation_installed=True))
    check('log-shows-trigger-event',later['counts']['still-file-0xA18D2750']=={'0x041E0002':1})
    tick(f,30)
    check('preview-never-repeats',len(f.sends)==1)
    # Upside-down EXIF orientation: pose 3 writes 3, other poses use Nikon's writer; every pose is logged.
    check('exif-getter-installed',f.read(EXIF_SLOT)==(sym(f,'z7_exif_get')|1))
    table=f.call(f.read(EXIF_SLOT));writer=struct.unpack('<I',bytes(f.u.mem_read(table+16*9+12,4)))[0]
    capture,meta,entry=0xa18d7000,0xa18d8200,0xa18d8300
    values=[]
    for pose in (0,3,2):
        f.u.mem_write(capture+0x24fd,bytes([pose]));f.u.mem_write(meta,struct.pack('<3I',0,capture,0));f.u.mem_write(entry,bytes(12))
        f.call(writer,entry,meta,0);values.append(struct.unpack('<6H',bytes(f.u.mem_read(entry,12)))[4])
    check('exif-orientation-values',values==[1,3,6])
    tick(f,3)
    poses=[int(e['event'],16)&0xffff for e in log(f)['ring'] if e['slot']=='exif-orientation-pose']
    check('exif-poses-logged',poses==[0,3,2])
    g=load({})
    tick(g,11)
    check('no-wav-probe-still-logs',g.read(SOUND_SLOT)==0x1006bc47 and all(g.read(s)&1 for s in SLOTS) and
          log(g)['sound']['preview']=='no clip installed' and not g.sends)
    g=load();g.u.mem_write(STATE_ADDR,b'\1');tick(g,11)
    check('busy-service-preview-refused-and-logged',not g.sends and log(g)['sound']['preview']=='refused (service busy)')
    g=load(speaker=0);tick(g,8);g.call(DISPATCH,g.sends[0][1]);tick(g,4)
    check('speaker-reject-visible-in-log',log(g)['sound']['rejects']==1 and log(g)['sound']['starts']==0)
    for patch in (0x1006b7dc,0x1014708c):
        g=FieldFixture(raw,h,packet,files={WAV_PATH:clip});g.u.mem_write(patch,bytes(4))
        r=g.call(h['symbols']['z7_module_load_once'],STATE)
        check(f'firmware-mismatch-{patch:x}-touches-nothing',r==7 and g.read(SOUND_SLOT)==0x1006bc47 and
              all(g.read(s)==n for s,n in zip(SLOTS,NATIVE)) and not g.file_events and not g.log_events)

    # After-session analyzer on logs written by the compiled module.
    def session(speaker=1,upside_pose=3):
        g=load(speaker=speaker);tick(g,8)
        g.call(DISPATCH,g.sends[0][1])
        if speaker:g.call(g.read(CONTEXT+32),0x04180023,0)
        g.u.mem_write(STATE_ADDR,bytes(3))
        table=g.call(g.read(EXIF_SLOT));writer=struct.unpack('<I',bytes(g.u.mem_read(table+16*9+12,4)))[0]
        for n in range(6):
            for _ in range(3):g.call(g.read(SLOTS[1]),0x04190001,0,0,0)  # live-view noise
            if n==5:continue
            pose=upside_pose if n==4 else 0
            g.u.mem_write(0xa18d7000+0x24fd,bytes([pose]));g.u.mem_write(0xa18d8200,struct.pack('<3I',0,0xa18d7000,0))
            g.call(writer,0xa18d8300,0xa18d8200,0)
            for kind in (3,7):
                g.u.mem_write(PACKET,struct.pack('<2I',(1<<29)|(9<<19)|((60+n)<<5)|kind,1));g.call(g.read(SLOTS[2]),0x041e0002,PACKET,0,0)
        tick(g,4);return analyze(g.log_files[LOG],5)
    r=session()
    check('analyzer-full-session',r['chime'].startswith('played to the end') and r['trigger'].startswith('0x041E0002 on still-file') and
          r['exif'].startswith('camera reports pose 3') and r['exif_poses']==[0,0,0,0,3])
    r=session(speaker=0,upside_pose=0)
    check('analyzer-rejected-chime-and-no-pose-3',r['chime'].startswith('queued but rejected') and r['exif'].startswith('no pose 3 seen'))

    report=dict(passed=True,count=len(checks),checks=checks,module_sha256=m['module_sha256'],host_main_sha256=h['main_payload_sha256'],
                clip_sha256=hashlib.sha256(clip).hexdigest(),camera_access=False,scope=__doc__)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
