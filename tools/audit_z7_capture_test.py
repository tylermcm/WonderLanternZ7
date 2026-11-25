"""Shutter sound on every photo: capture-trigger camera-test module audit (MIT).

Executes the original-Z7 host loader and worker tick, the compiled
capture-test module, Nikon's sound post, dispatcher and completion, the
property getter wrapper and the native file create/write/close wrappers (the
field-test fixture). Fires capture-controller events as measured on the camera
in field-test session 2 and checks: a sound is queued on 0x0419000B only in
Silent photography, Nikon's handler always runs with the same arguments and
result, a busy service is counted not retried, a burst sounds each frame once
the previous click finished, and the log header carries the counters.
No camera, no card.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from audit_z7_field_test import FieldFixture
from audit_z7_shutter_sound_playback import WAV_PATH,DISPATCH,CONTEXT,STATE_ADDR,SLOT as SOUND_SLOT
from audit_z7_trigger_probe import SLOTS,NATIVE,LOG
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output
from read_z7_trigger_log import parse

EXPOSURE=0x0419000b


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('host','module','output'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--clip',type=Path,required=True,help='Exact SHUTTER1.WAV intended for the card')
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text());raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256']
    m=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(packet).hexdigest()==m['module_sha256'] and m['kind']=='original-Z7-shutter-sound-capture-test'
    clip=a.clip.read_bytes()
    checks=[]
    def check(name,ok):
        assert ok,name
        checks.append(name)
    def load(files=None,**kw):
        f=FieldFixture(raw,h,packet,files={WAV_PATH:clip} if files is None else files,**kw)
        f.loaded=f.call(h['symbols']['z7_module_load_once'],STATE);f.setword(40,f.loaded)
        f.base=f.words()[12];f.s=m['symbols'];return f
    def val(f,n):return f.read(f.base+f.s[n])
    def tick(f,n=1):
        for _ in range(n):f.call(h['symbols']['z7_module_worker_tick'])
    def fire(f,event,slot=0):return f.call(f.read(SLOTS[slot]),event,0,0x22,0x33)
    def finish(f):
        f.call(DISPATCH,f.sends[-1][1]);f.call(f.read(CONTEXT+32),0x04180023,0);f.u.mem_write(STATE_ADDR,bytes(3))

    f=load(silent=1)
    check('module-loads',f.loaded==8)
    check('sound-intercept-installed',val(f,'z7_sound_installed')==1 and f.read(SOUND_SLOT)==((f.base+f.s['z7_sound_start'])|1))
    check('three-probe-wrappers-installed',val(f,'z7_capture_init_result')==7 and all(f.read(s)&1 and f.read(s)!=n for s,n in zip(SLOTS,NATIVE)))
    check('only-shutter1-read-at-load',[e[0] for e in f.file_events]==['open','read','close'] and not f.log_events)
    check('no-sound-at-boot',(tick(f,8) or True) and not f.sends)
    r=fire(f,EXPOSURE)
    check('exposure-in-silent-queues-one-sound',len(f.sends)==1 and val(f,'z7_capture_queued')==1)
    check('native-controller-handler-still-runs',r==0x600 and f.native_calls[-1]==(0,EXPOSURE,0,0x22,0x33))
    for ev in (0x04190008,0x0419000c,0x0419000d,0x0419000e,0x04190007):fire(f,ev)
    for ev in (0x04190003,0x04190005,0x0419000b):fire(f,ev,1)
    check('other-events-and-other-callbacks-silent',len(f.sends)==1)
    fire(f,EXPOSURE)
    check('busy-service-counted-not-retried',len(f.sends)==1 and val(f,'z7_capture_busy')==1)
    finish(f)
    check('click-programs-native-setters',[c[0] for c in f.setter_calls]==['format','tones','data','dma-start'])
    for frame in range(4):
        fire(f,EXPOSURE);finish(f)
    check('burst-sounds-each-frame-after-finish',len(f.sends)==5 and val(f,'z7_capture_queued')==5 and val(f,'z7_sound_finished')==5)
    tick(f,6);log=parse(f.log_files[LOG])
    check('log-v2-with-trigger-counters',log['version']==2 and log['extra']['trigger_seen']==6 and log['extra']['trigger_silent']==6 and
          log['extra']['trigger_queued']==5 and log['extra']['trigger_busy']==1)
    check('log-sound-state',log['sound']['preview'].startswith('none') and log['sound']['finished']==5 and log['sound']['installed'])
    check('log-keeps-exposure-events',sum(1 for e in log['ring'] if e['event']=='0x0419000B' and e['slot'].startswith('capture-controller'))==6)

    g=load(silent=0)
    fire(g,EXPOSURE);fire(g,EXPOSURE)
    check('mechanical-shutter-no-sound',not g.sends and val(g,'z7_capture_queued')==0)
    tick(g,3)
    check('mechanical-shutter-counted',parse(g.log_files[LOG])['extra']['trigger_seen']==2 and parse(g.log_files[LOG])['extra']['trigger_silent']==0)

    g=load(files={},silent=1)
    r=fire(g,EXPOSURE)
    check('no-wav-stays-silent-and-logs',not g.sends and g.read(SOUND_SLOT)==0x1006bc47 and r==0x600 and all(g.read(s)&1 for s in SLOTS))
    for patch in (0x1006b7dc,0x101426a8):
        g=FieldFixture(raw,h,packet,files={WAV_PATH:clip},silent=1)
        g.u.mem_write(patch,b'\0\0\0\0')
        res=g.call(h['symbols']['z7_module_load_once'],STATE)
        check(f'firmware-mismatch-{patch:x}-touches-nothing',res==7 and g.read(SOUND_SLOT)==0x1006bc47 and
              all(g.read(s)==n for s,n in zip(SLOTS,NATIVE)) and not g.file_events and not g.log_events)

    report=dict(passed=True,count=len(checks),checks=checks,module_sha256=m['module_sha256'],host_main_sha256=h['main_payload_sha256'],
                clip_sha256=hashlib.sha256(clip).hexdigest(),trigger='0x0419000B on 0xA18D1BD8, Silent photography only',
                camera_access=False,scope=__doc__)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
