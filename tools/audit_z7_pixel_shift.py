"""First real Z7 pixel-shift series (Z7_PIXEL_SHIFT_V1): offline audit (MIT).

Same simulated stabiliser (camera-measured payload layout), D2 sender and
release as audit_z7_pixel_release.py. Checks that, after arming and the
button being free, the module waits 2 s (and aborts if the button is touched
then), fires four frames at the calibrated Bayer corners (x 20, y 18 steps:
targets (0,0,0), (-80,0,0), (-80,-72,-72), (0,-72,-72)), waits 500 ms on each
confirmed position and re-checks it before releasing (a lost hold stops the
series without a release), clicks once per frame, then recentres and restores
with Nikon's apply flags sel[1]|0x80. No camera, no card, no exposure.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0
from audit_z7_pixel_release import ReleaseUnit,V
from audit_z7_pixel_series import S
from audit_z7_vr_restore import R
from audit_z7_vr_move import CENTRE,LOG,SLOT,BUSY,DELAY
from audit_z7_lcd_shutter_sound import WAV
from audit_z7_lcd_grid_persistence import NEW,v3record
from audit_z7_settings_files import PATHS
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output

CORNERS=[(0,0),(20,0),(20,18),(0,18)]
def pos(x,y):return bytes([0,x,0,y,0,16,16,0,0,2])


class ShiftUnit(ReleaseUnit):
    def __init__(self,*a,lose_hold_frame=None,touch_in_settle=False,**k):
        super().__init__(*a,**k);self.lose_hold_frame=lose_hold_frame;self.touch_in_settle=touch_in_settle;self.timeline=[]
    def hook(self,u,address,size,context):
        if address==DELAY:
            ms=self.r(UC_ARM_REG_R0);self.timeline.append(('sleep',ms,len(self.fires)))
            if ms==500 and self.lose_hold_frame is not None and len(self.fires)==self.lose_hold_frame:
                self.state=1                           # Nikon took the sensor back during the settle
            if self.touch_in_settle and ms==100 and getattr(self,'long_delays',0)>=8 and not self.fires:
                u.mem_write(0xa1f90aa4,struct.pack('<I',0x40000000))
        super().hook(u,address,size,context)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('host','module','output','clip'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text());raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    m=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256'] and hashlib.sha256(packet).hexdigest()==m['module_sha256']
    assert m['configuration'].get('pixel_shift')
    clip=a.clip.read_bytes();symbols=m['symbols'];checks=[]
    def check(name,ok):
        assert ok,name
        checks.append(name)
    journal={NEW[0]:v3record((3,15,1,0,5,0,127,7,0,127,4),0)}
    def load(**kw):
        ShiftUnit.sound_files={WAV:clip}
        f=ShiftUnit(raw,h,packet,dict(journal),**kw);f.file_paths=PATHS+NEW
        f.u.mem_write(SLOT,bytes(4));f.u.mem_write(BUSY,bytes(4))
        assert f.call(h['symbols']['z7_module_load_once'],STATE)==8
        f.base=f.words()[12];f.setword(40,8);f.reply_addr=f.base+symbols['z7_vm_reply'];f.called_addr=f.base+symbols['z7_vm_d2_called']
        f.setup(f.base,symbols);return f
    def tick(f,n=1):
        for _ in range(n):f.call(h['symbols']['z7_module_worker_tick'])
    def moves(f):return [r['payload'] for r in f.requests if r['opcode']==0xf1f1]
    def flags(f):
        d=f.sound_files.get(LOG,b'');return struct.unpack_from('<I',d,12)[0] if len(d)>=16 else None

    f=load();tick(f)
    check('four-fires',len(f.fires)==4)
    check('calibrated-corners-then-centre',moves(f)==[pos(*c) for c in CORNERS]+[CENTRE])
    check('fired-held-at-calibrated-targets',[(x['state'],x['target']) for x in f.fires]==[(0x40,[-4*cx,-4*cy,-4*cy]) for cx,cy in CORNERS])
    before=[ms for kind,ms,n in f.timeline if n==0]
    check('two-second-settle-before-first-frame',sum(ms for ms in before if ms==100)>=2000+500)
    per=[[ms for kind,ms,n in f.timeline if n==k] for k in range(4)]
    check('500ms-settle-before-each-release',all(500 in x for x in per))
    check('one-click-per-frame',f.r_('z7_vr_clicks')==4)
    check('restore-with-apply-flags',[(c['selection'],c['flags']) for c in f.d2_calls]==[(bytes([2,0x11]),0x91)])
    tick(f,32);fl=flags(f)
    check('flags-complete-and-restored',fl&S['SERIES_COMPLETE'] and fl&R['RESTORED'] and fl&V['FIRED'] and not fl&(V['REFUSED']|V['FRAME_FAILED']|V['TOUCHED']))
    g=load(lose_hold_frame=2);tick(g);tick(g,32)
    check('lost-hold-in-settle-no-release',len(g.fires)==2 and flags(g)&S['HOLD_LOST'] and moves(g)[-1]==CENTRE and len(g.d2_calls)==1)
    g=load(touch_in_settle=True);tick(g);tick(g,32)
    check('touch-during-start-settle-no-release',not g.fires and flags(g)&V['TOUCHED'])
    report=dict(passed=True,count=len(checks),checks=checks,module_sha256=m['module_sha256'],host_main_sha256=h['main_payload_sha256'],
                corners=CORNERS,camera_access=False,exposures=0,scope=__doc__)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
