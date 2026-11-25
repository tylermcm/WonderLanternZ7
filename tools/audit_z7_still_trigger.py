"""Provisional still-file shutter-sound trigger: policy and wiring audit (MIT).

Executes the original-Z7 host loader, the compiled module (WAV load, playback
install, still-file wrapper, trigger policy), Nikon's sound post, dispatcher and
completion, and the original property getter wrappers. Supplied boundaries are
those of audit_z7_shutter_sound_playback.py plus the native still-file consumer
(recorded with a marker result, not executed) and the Silent photography value.
Record layout follows STILL_FILE_TRACE.md. No camera; per-photo cardinality of
the event on hardware is NOT established here.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3
from audit_z7_shutter_sound_playback import SoundFixture,WAV_PATH,wav,DISPATCH,CONTEXT,STATE_ADDR
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output

SLOT,NATIVE,EVENT=0xa18d2750,0x104db211,0x041e0002
PACKET=0xa18d8000


def record(slot,group,number,kind):return (slot<<29)|(group<<19)|(number<<5)|kind


class TriggerFixture(SoundFixture):
    def __init__(self,*a,slot_value=NATIVE,silent=1,**kw):
        super().__init__(*a,**kw)
        try:self.u.mem_map(0xa18d0000,0x10000)
        except Exception:pass
        self.u.mem_write(SLOT,struct.pack('<I',slot_value))
        self.silent=silent;self.native_calls=[]
    def hook(self,u,address,size,context):
        if address==NATIVE-1:
            self.native_calls.append(tuple(self.r(x) for x in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)))
            self.ret(0x77);return
        if address==0x10070234:
            assert self.r(UC_ARM_REG_R0)==0x576
            u.mem_write(self.r(UC_ARM_REG_R1),struct.pack('<I',self.silent));self.ret(0);return
        super().hook(u,address,size,context)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('host','module','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text());raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256']
    m=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(packet).hexdigest()==m['module_sha256']
    checks=[]
    def check(name,ok):
        assert ok,name
        checks.append(name)
    good=wav(frames=480)
    def load(files=None,**kw):
        f=TriggerFixture(raw,h,packet,files={WAV_PATH:good} if files is None else files,**kw)
        f.loaded=f.call(h['symbols']['z7_module_load_once'],STATE)
        f.base=f.words()[12];f.s=m['symbols'];return f
    def sym(f,n):return f.base+f.s[n]
    def val(f,n):return f.read(sym(f,n))
    def notify(f,event,rec,flag=1):
        f.u.mem_write(PACKET,struct.pack('<3I',rec,flag,0))
        return f.call(f.read(SLOT),event,PACKET,0x22,0x33)
    def finish(f):
        f.call(DISPATCH,f.sends[-1][1]);f.call(f.read(CONTEXT+32),0x04180023,0);f.u.mem_write(STATE_ADDR,b'\0\0\0')

    # Policy through the compiled seam.
    f=load()
    op=lambda *x:f.call(sym(f,'z7_trigger_operation'),*x)
    check('key-ignores-kind-keeps-slot-group-number',op(2,record(1,100,1234,3))==op(2,record(1,100,1234,7))!=op(2,record(1,100,1235,3)) and
          op(2,record(2,100,1234,3))!=op(2,record(1,100,1234,3)))
    check('policy-plays-new-record',op(1,EVENT,record(1,100,1,3),1)==1)
    check('policy-dedupes-same-photo-other-kind',op(1,EVENT,record(1,100,1,7),1)==2)
    check('policy-not-silent',op(1,EVENT,record(1,100,2,3),0)==3)
    check('policy-not-silent-key-remembered',op(1,EVENT,record(1,100,2,3),1)==2)
    check('policy-ignores-other-events',op(1,0x04190001,record(1,100,3,3),1)==0)
    check('policy-zero-record',op(1,EVENT,7,1)==4)
    for n in range(10,19):op(1,EVENT,record(1,100,n,3),1)
    check('policy-forgets-after-8-newer-records',op(1,EVENT,record(1,100,1,3),1)==1)

    # Wiring through the installed wrapper and Nikon's sound service.
    f=load()
    check('module-loads-installs-and-wraps',f.loaded==8 and val(f,'z7_sound_installed')==1 and val(f,'z7_trigger_init_result')==1 and
          f.read(SLOT)==(sym(f,'z7_trigger_wrap')|1))
    r=notify(f,EVENT,record(1,100,1,3))
    check('native-handler-always-called-with-same-arguments',r==0x77 and f.native_calls==[(EVENT,PACKET,0x22,0x33)])
    check('new-photo-queues-one-sound',len(f.sends)==1 and val(f,'z7_trigger_queued')==1)
    finish(f)
    check('sound-programmed-and-finished',[c[0] for c in f.setter_calls]==['format','tones','data','dma-start'] and val(f,'z7_sound_playback')==0)
    notify(f,EVENT,record(1,100,1,7))
    check('jpeg-plus-nef-pair-sounds-once',len(f.sends)==1 and len(f.native_calls)==2)
    notify(f,EVENT,record(1,100,2,3));notify(f,EVENT,record(1,100,3,3))
    check('burst-frame-while-playing-skipped-not-queued',len(f.sends)==2 and val(f,'z7_trigger_busy')==1)
    notify(f,0x041e0001,record(1,100,9,3))
    check('other-still-file-events-pass-through-silently',len(f.sends)==2 and len(f.native_calls)==5)
    f.call(f.read(SLOT),EVENT,0,0x22,0x33);f.call(f.read(SLOT),EVENT,0x10000000,0x22,0x33)
    check('null-or-non-ram-packet-not-read',len(f.sends)==2 and f.native_calls[-1][1]==0x10000000)
    g=load(silent=0);notify(g,EVENT,record(1,1,1,3))
    check('mechanical-shutter-no-sound',not g.sends and len(g.native_calls)==1)
    g=load(files={})
    check('no-wav-leaves-slot-native',g.loaded==8 and g.read(SLOT)==NATIVE and val(g,'z7_trigger_init_result')==0)
    g=load(slot_value=0x12345679)
    check('foreign-slot-untouched',g.read(SLOT)==0x12345679 and val(g,'z7_trigger_init_result')==0)
    g=TriggerFixture(raw,h,packet,files={WAV_PATH:good},fingerprint_patch=0x104db210)
    check('firmware-mismatch-fails-init',g.call(h['symbols']['z7_module_load_once'],STATE)==7 and g.read(SLOT)==NATIVE)

    report=dict(passed=True,count=len(checks),checks=checks,module_sha256=m['module_sha256'],host_main_sha256=h['main_payload_sha256'],
                provisional=True,camera_access=False,per_photo_cardinality_established=False,scope=__doc__)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
