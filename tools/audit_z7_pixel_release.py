"""Module-fired pixel-shift series (step 3b): offline audit (MIT).

Simulated body-VR unit and D2 sender as audit_z7_pixel_series.py, plus Nikon's
release API 0x101ECFB0 (request, callback): the fixture records each call, the
request bytes, the callback and the VR state at that moment, returns a chosen
code, and completes the frame by updating the module's completion and photo
counters the way the callback and the still-file hook do (both are executed
for real separately below). Checks that, after arming, the module waits until
the shutter button is free, fires exactly once per Bayer corner and only while
the commanded position is held, uses the PTP/upstream request {0,1,0,0, 0,0,1,1}
with its own callback, stops on a refusal, a failed or missing completion, a
busy completion slot or a touched shutter button, always recentres and
restores D2, and sends nothing on a release-binding mismatch.
No camera, no card, no sensor movement, no exposure.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1
from audit_z7_vr_restore import D2Unit,R
from audit_z7_vr_move import CENTRE,F,LOG,SLOT,BUSY,DELAY
from audit_z7_pixel_series import S,CORNERS,pos
from audit_z7_lcd_shutter_sound import WAV
from audit_z7_lcd_grid_persistence import NEW,v3record
from audit_z7_settings_files import PATHS
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output

RELEASE,RSLOT,SW0,DONE=0x101ecfb0,0xa238ba48+0x38*4,0xa1f90aa4,0x04100034
V=dict(FIRED=1<<22,REFUSED=1<<23,FRAME_FAILED=1<<24,TOUCHED=1<<25,NOT_FREED=1<<26,SLOT_BUSY=1<<27)
REQUEST=bytes([0,1,0,0])+struct.pack('<4I',0,0,1,1)


class ReleaseUnit(D2Unit):
    def __init__(self,*a,codes=None,complete='ok',hold_button=False,touch_after=None,slot_busy=False,**k):
        super().__init__(*a,**k);self.fires=[];self.codes=list(codes or []);self.complete=complete
        self.hold_button=hold_button;self.touch_after=touch_after;self.slot_busy=slot_busy;self.pending_frame=None;self.sym={}
        for base in (0xa2380000,0xa1f90000):
            try:self.u.mem_map(base,0x10000)
            except Exception:pass
    def setup(self,base,symbols):
        self.sym={n:base+symbols[n] for n in ('z7_vr_done','z7_vs_photos','z7_vr_last_event','z7_vr_arg0','z7_vr_arg1','z7_vr_events')}
        self.u.mem_write(SW0,struct.pack('<I',0x80000000 if self.hold_button else 0))
        self.u.mem_write(RSLOT,struct.pack('<I',0x10001 if self.slot_busy else 0))
    def w(self,n,v):self.u.mem_write(self.sym[n],struct.pack('<I',v))
    def r_(self,n):return struct.unpack('<I',bytes(self.u.mem_read(self.sym[n],4)))[0]
    def hook(self,u,address,size,context):
        if address==RELEASE:
            req=bytes(u.mem_read(self.r(UC_ARM_REG_R0),0x14));cb=self.r(UC_ARM_REG_R1)
            self.fires.append(dict(request=req,callback=cb,state=self.state,target=list(self.target),
                                   button=struct.unpack('<I',bytes(u.mem_read(SW0,4)))[0]))
            code=self.codes.pop(0) if self.codes else 0
            if not code:self.pending_frame=len(self.fires)
            if self.touch_after is not None and len(self.fires)>=self.touch_after:u.mem_write(SW0,struct.pack('<I',0x40000000))
            self.ret(code);return
        if address==DELAY and self.pending_frame and self.complete!='none':
            self.pending_frame=None
            self.w('z7_vr_last_event',DONE);self.w('z7_vr_events',self.r_('z7_vr_events')+1)
            if self.complete=='fail':self.w('z7_vr_arg0',7);self.w('z7_vr_done',2)
            else:
                self.w('z7_vr_arg0',0);self.w('z7_vr_done',1);self.w('z7_vs_photos',self.r_('z7_vs_photos')+1)
                self.state=0x40                     # exposure over; the hold stays
        super().hook(u,address,size,context)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('host','module','output','clip'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text());raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    m=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256'] and hashlib.sha256(packet).hexdigest()==m['module_sha256']
    assert m['configuration'].get('pixel_release')
    clip=a.clip.read_bytes();symbols=m['symbols'];checks=[]
    def check(name,ok):
        assert ok,name
        checks.append(name)
    journal={NEW[0]:v3record((3,15,1,0,5,0,127,7,0,127,4),0)}
    def load(patch=None,**kw):
        ReleaseUnit.sound_files={WAV:clip}
        f=ReleaseUnit(raw,h,packet,dict(journal),**kw);f.file_paths=PATHS+NEW
        f.u.mem_write(SLOT,bytes(4));f.u.mem_write(BUSY,bytes(4))
        if patch:f.u.mem_write(patch,bytes(4))
        assert f.call(h['symbols']['z7_module_load_once'],STATE)==8
        f.base=f.words()[12];f.setword(40,8);f.reply_addr=f.base+symbols['z7_vm_reply'];f.called_addr=f.base+symbols['z7_vm_d2_called']
        f.setup(f.base,symbols);return f
    def tick(f,n=1):
        for _ in range(n):f.call(h['symbols']['z7_module_worker_tick'])
    def moves(f):return [r['payload'] for r in f.requests if r['opcode']==0xf1f1]
    def flags(f):
        d=f.sound_files.get(LOG,b'');return struct.unpack_from('<I',d,12)[0] if len(d)>=16 else None

    # 1. Full module-fired series.
    f=load();tick(f)
    check('four-fires',len(f.fires)==4)
    check('request-is-ptp-upstream-shape',all(x['request']==REQUEST for x in f.fires))
    check('callback-is-module-function',all(x['callback']==f.base+symbols['z7_vr_callback']|1 or x['callback']==(f.base+symbols['z7_vr_callback'])|1 for x in f.fires))
    check('each-fire-while-position-held',[ (x['state'],x['target']) for x in f.fires]==[(0x40,[-4*cx,-4*cy,-4*cy]) for cx,cy in CORNERS])
    check('never-fired-with-button-touched',all(x['button']==0 for x in f.fires))
    check('positions-then-centre',moves(f)==[pos(*c) for c in CORNERS]+[CENTRE])
    check('restore-once',len(f.d2_calls)==1)
    tick(f,32);fl=flags(f)
    check('flags-complete',fl&V['FIRED'] and fl&S['SERIES_COMPLETE'] and fl&R['RESTORED'] and fl&F['CENTRE_FOLLOWED'] and
          not fl&(V['REFUSED']|V['FRAME_FAILED']|V['TOUCHED']|V['NOT_FREED']|V['SLOT_BUSY']))
    n=len(f.fires);tick(f,5);check('quiet-after-done',len(f.fires)==n)
    # 2. Shutter button held: never fires, recentres.
    g=load(hold_button=True);tick(g);tick(g,32)
    check('held-button-no-fire',not g.fires and flags(g)&V['NOT_FREED'] and moves(g)==[] and len(g.d2_calls)==0)
    # 3. Touched mid-series.
    g=load(touch_after=1);tick(g);tick(g,32)
    check('touched-stops-after-frame',len(g.fires)==1 and flags(g)&V['TOUCHED'] and moves(g)[-1]==CENTRE and len(g.d2_calls)==1)
    # 4. Refused.
    g=load(codes=[0,0xd]);tick(g);tick(g,32)
    check('refusal-stops',len(g.fires)==2 and flags(g)&V['REFUSED'] and moves(g)[-1]==CENTRE and len(g.d2_calls)==1)
    # 5. Failed completion.
    g=load(complete='fail');tick(g);tick(g,32)
    check('failed-completion-stops',len(g.fires)==1 and flags(g)&V['FRAME_FAILED'] and moves(g)[-1]==CENTRE)
    # 6. No completion: bounded wait.
    g=load(complete='none');tick(g)
    check('missing-completion-bounded',len(g.fires)==1 and sum(d for d in g.delays if d==50)<=300*50 and moves(g)[-1]==CENTRE)
    tick(g,32);check('missing-completion-flag',flags(g)&V['FRAME_FAILED'])
    # 7. Completion slot busy.
    g=load(slot_busy=True);tick(g);tick(g,32)
    check('busy-slot-no-fire',not g.fires and flags(g)&V['SLOT_BUSY'] and moves(g)[-1]==CENTRE)
    # 8. Release binding mismatch: nothing at all.
    g=load(patch=RELEASE);tick(g,3)
    check('release-mismatch-nothing',not g.fires and not g.requests)
    # 9. The callback itself.
    g=load(hold_button=True);arg=0xa2970500
    cb=g.base+symbols['z7_vr_callback']
    g.u.mem_write(arg,struct.pack('<2I',0,0x1234));g.call(cb,DONE,arg,0,0)
    check('callback-success',g.r_('z7_vr_done')==1 and g.r_('z7_vr_arg1')==0x1234 and g.r_('z7_vr_events')==1)
    g.u.mem_write(arg,struct.pack('<2I',5,0));g.call(cb,DONE,arg,0,0)
    check('callback-failure',g.r_('z7_vr_done')==2 and g.r_('z7_vr_arg0')==5)
    g.w('z7_vr_done',0);g.call(cb,0x04100038,0x13,0,0)
    check('callback-other-event-bad-pointer',g.r_('z7_vr_done')==0 and g.r_('z7_vr_arg0')==0xffffffff and g.r_('z7_vr_last_event')==0x04100038)
    report=dict(passed=True,count=len(checks),checks=checks,module_sha256=m['module_sha256'],host_main_sha256=h['main_payload_sha256'],
                request=REQUEST.hex(),camera_access=False,exposures=0,scope=__doc__)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
