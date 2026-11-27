"""Pixel-shift geometry probe (step 3c): offline audit (MIT).

Same simulated stabiliser, D2 sender and release as audit_z7_pixel_release.py.
The simulated unit decodes the payload as measured on the camera: x and y
little-endian int16 at bytes 1-2 and 3-4, targets (-4x, -4y, -4y), clamped
at +-8180 counts. Also supplied: Nikon's BodyVr event post
0x1017088C and VR-mode apply 0x101C69D8, recorded, each optionally ending the
hold. Checks that the module fires one frame per variant, in order, only
while that variant is held within +-400 counts; skips and recentres an
out-of-range variant without firing; sends exactly the seven variant payloads
and then the centre; and tries the three restore methods in order (D2 with
the apply flags sel[1]|0x80, BodyVr event bit 4 to task 0xA23826D0, Nikon's
apply), stopping at the first that ends the hold. Nothing is sent on a
restore-binding mismatch. No camera, no card, no exposure.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1
from audit_z7_pixel_release import ReleaseUnit,V
from audit_z7_vr_restore import R
from audit_z7_vr_move import CENTRE,LOG,SLOT,BUSY
from audit_z7_lcd_shutter_sound import WAV
from audit_z7_lcd_grid_persistence import NEW,v3record
from audit_z7_settings_files import PATHS
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output

POST,APPLY,TASK=0x1017088c,0x101c69d8,0xa23826d0
VARIANTS=[bytes(v) for v in ([0,0,0,0,0,16,16,0,0,2],[0,19,0,0,0,16,16,0,0,2],[0,0,0,18,0,16,16,0,0,2],[0,0,0,0,18,16,16,0,0,2],
                              [0,0,0,18,0,24,8,0,0,2],[0,0,0xff,0xee,0,16,16,0,0,2],[0xff,0xed,0,0,0,16,16,0,0,2])]
TARGETS=[[0,0,0],[-76,0,0],[0,-72,-72],[0,-72,-72]]   # fired V0, V1, V2, V4; V3, V5, V6 out of range, as on the camera
SKIPPED,WORKED=1<<28,1<<29


class ProbeUnit(ReleaseUnit):
    def __init__(self,*a,works=None,**k):
        super().__init__(*a,**k);self.works=works;self.posts=[];self.applies=[]
    def hook(self,u,address,size,context):
        if address==0x101c63f8:
            fl=self.r(UC_ARM_REG_R1)
            if self.works!='m1' or not fl&0x80:
                self.d2_calls.append(dict(selection=bytes(u.mem_read(self.r(UC_ARM_REG_R0),2)),flags=fl,state=self.state))
                self.ret(1);return                      # accepted, hold stays
        if address==POST:
            self.posts.append((self.r(UC_ARM_REG_R0),self.r(UC_ARM_REG_R1)))
            if self.works=='m2':self.state=1;self.target=[0,0,0]
            self.ret(0);return
        if address==APPLY:
            self.applies.append((bytes(u.mem_read(self.r(UC_ARM_REG_R0),2)),self.r(UC_ARM_REG_R1)))
            if self.works=='m3':self.state=1;self.target=[0,0,0]
            self.ret(1);return
        super().hook(u,address,size,context)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('host','module','output','clip'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text());raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    m=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256'] and hashlib.sha256(packet).hexdigest()==m['module_sha256']
    assert m['configuration'].get('pixel_probe')
    clip=a.clip.read_bytes();symbols=m['symbols'];checks=[]
    def check(name,ok):
        assert ok,name
        checks.append(name)
    journal={NEW[0]:v3record((3,15,1,0,5,0,127,7,0,127,4),0)}
    def load(patch=None,**kw):
        ProbeUnit.sound_files={WAV:clip}
        f=ProbeUnit(raw,h,packet,dict(journal),**kw);f.file_paths=PATHS+NEW
        f.u.mem_write(SLOT,bytes(4));f.u.mem_write(BUSY,bytes(4))
        if patch:f.u.mem_write(patch,bytes(4))
        assert f.call(h['symbols']['z7_module_load_once'],STATE)==8
        f.base=f.words()[12];f.setword(40,8);f.reply_addr=f.base+symbols['z7_vm_reply'];f.called_addr=f.base+symbols['z7_vm_d2_called']
        f.setup(f.base,symbols);return f
    def tick(f,n=1):
        for _ in range(n):f.call(h['symbols']['z7_module_worker_tick'])
    def moves(f):return [r['payload'] for r in f.requests if r['opcode']==0xf1f1]
    def head(f):
        d=f.sound_files.get(LOG,b'');return struct.unpack_from('<18I',d) if len(d)>=72 else None

    f=load(works='m1');tick(f)
    check('four-frames-three-skipped',len(f.fires)==4)
    mv=moves(f)
    check('variant-payloads-skips-recentred',mv==VARIANTS[:4]+[CENTRE,VARIANTS[4],VARIANTS[5],CENTRE,VARIANTS[6],CENTRE,CENTRE])
    check('each-fire-while-variant-held',[(x['state'],x['target']) for x in f.fires]==[(0x40,t) for t in TARGETS])
    check('one-click-per-frame',f.r_('z7_vr_clicks')==4)
    check('restore-method-1-apply-flags',[(c['selection'],c['flags']) for c in f.d2_calls]==[(bytes([2,0x11]),0x91)] and not f.posts and not f.applies)
    tick(f,32);hd=head(f)
    check('log-192-entries-layout',len(f.sound_files[LOG])==72+192*56 and hd[1]==3)
    check('restore-1-recorded',hd[3]&WORKED and hd[3]&R['RESTORED'] and hd[9]&0xff==1 and hd[12]==4 and hd[3]&SKIPPED)
    g=load(works='m2');tick(g)
    check('method-1-fails-then-event-bit4-works',[c['flags'] for c in g.d2_calls]==[0x11|0x80] and g.posts==[(TASK,0x10)] and not g.applies)
    tick(g,32);check('restore-2-recorded',head(g)[9]&0xff==2)
    g=load(works='m3');tick(g)
    check('then-nikon-apply-works',len(g.d2_calls)==1 and g.posts==[(TASK,0x10)] and g.applies and g.applies[0][0]==bytes([2,0x11]))
    tick(g,32);check('restore-3-recorded',head(g)[9]&0xff==3)
    g=load(works=None);tick(g);tick(g,32);hd=head(g)
    check('no-method-works-all-tried-reported',len(g.d2_calls)==1 and len(g.posts)==1 and len(g.applies)==1 and not hd[3]&WORKED)
    check('never-fired-out-of-range',all(max(abs(t) for t in x['target'])<=400 for x in f.fires))
    g=load(works='m1',codes=[0,0,0xd]);tick(g)
    check('refusal-stops-then-centre-restore',len(g.fires)==3 and moves(g)[-1]==CENTRE and len(g.d2_calls)==1)
    g=load(works='m1',patch=APPLY);tick(g,3)
    check('probe-binding-mismatch-nothing',not g.fires and not moves(g))
    report=dict(passed=True,count=len(checks),checks=checks,module_sha256=m['module_sha256'],host_main_sha256=h['main_payload_sha256'],
                variants=[v.hex() for v in VARIANTS],camera_access=False,exposures=0,scope=__doc__)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
