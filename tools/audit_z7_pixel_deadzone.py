"""Pixel-shift y dead-zone run (step 3e): offline audit (MIT).

Same simulated stabiliser (camera-measured payload layout), release and
restore methods as audit_z7_pixel_calib.py. Checks that the twenty frames go
out in order - discarded first frame, references around y +18/+36/+54/-18/-36,
an x 20 control, and y 18 / -18 reached from 54 / -54 - each fired only while
held at (-4x,-4y,-4y) within +-216 counts, after a 2 s start settle (touching
the button then cancels) and a 500 ms settle per frame, one click each, then
centre and Nikon's D2 apply restore. No camera, no card, no exposure.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0
from audit_z7_pixel_probe import ProbeUnit,WORKED
from audit_z7_pixel_release import V
from audit_z7_vr_restore import R
from audit_z7_vr_move import CENTRE,LOG,SLOT,BUSY,DELAY
from audit_z7_lcd_shutter_sound import WAV
from audit_z7_lcd_grid_persistence import NEW,v3record
from audit_z7_settings_files import PATHS
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output

STEPS=[(0,0),(0,0),(0,18),(0,0),(0,36),(0,0),(0,54),(0,0),(0,-18),(0,0),(0,-36),(0,0),(20,0),(0,0),
       (0,54),(0,18),(0,0),(0,-54),(0,-18),(0,0)]
def payload(x,y):return bytes([0])+struct.pack('<2h',x,y)+bytes([16,16,0,0,2])


class DzUnit(ProbeUnit):
    def __init__(self,*a,touch_in_settle=False,**k):
        super().__init__(*a,**k);self.timeline=[];self.touch_in_settle=touch_in_settle
    def hook(self,u,address,size,context):
        if address==DELAY:
            ms=self.r(UC_ARM_REG_R0);self.timeline.append((ms,len(self.fires)))
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
    assert m['configuration'].get('pixel_deadzone')
    clip=a.clip.read_bytes();symbols=m['symbols'];checks=[]
    def check(name,ok):
        assert ok,name
        checks.append(name)
    journal={NEW[0]:v3record((3,15,1,0,5,0,127,7,0,127,4),0)}
    def load(**kw):
        DzUnit.sound_files={WAV:clip}
        f=DzUnit(raw,h,packet,dict(journal),works='m1',**kw);f.file_paths=PATHS+NEW
        f.u.mem_write(SLOT,bytes(4));f.u.mem_write(BUSY,bytes(4))
        assert f.call(h['symbols']['z7_module_load_once'],STATE)==8
        f.base=f.words()[12];f.setword(40,8);f.reply_addr=f.base+symbols['z7_vm_reply'];f.called_addr=f.base+symbols['z7_vm_d2_called']
        f.setup(f.base,symbols);return f
    f=load();f.call(h['symbols']['z7_module_worker_tick'])
    mv=[r['payload'] for r in f.requests if r['opcode']==0xf1f1]
    check('twenty-payloads-then-centre',mv==[payload(x,y) for x,y in STEPS]+[CENTRE])
    check('twenty-frames',len(f.fires)==20)
    check('each-fired-held-at-target',[(x['state'],x['target']) for x in f.fires]==[(0x40,[-4*x,-4*y,-4*y]) for x,y in STEPS])
    check('all-within-216',all(max(abs(t) for t in x['target'])<=216 for x in f.fires))
    before=[ms for ms,n in f.timeline if n==0]
    check('two-second-start-settle',sum(ms for ms in before if ms==100)>=2000+500)
    check('500ms-settle-before-each-frame',all(500 in [ms for ms,n in f.timeline if n==k] for k in range(20)))
    check('one-click-each',f.r_('z7_vr_clicks')==20)
    check('restore-apply-flags',[(c['selection'],c['flags']) for c in f.d2_calls]==[(bytes([2,0x11]),0x91)])
    for _ in range(32):f.call(h['symbols']['z7_module_worker_tick'])
    d=f.sound_files.get(LOG,b'');hd=struct.unpack_from('<18I',d)
    check('log-records-twenty-and-restore',hd[12]==20 and hd[3]&WORKED and hd[3]&R['RESTORED'])
    g=load(touch_in_settle=True);g.call(h['symbols']['z7_module_worker_tick'])
    for _ in range(32):g.call(h['symbols']['z7_module_worker_tick'])
    d=g.sound_files.get(LOG,b'');fl=struct.unpack_from('<I',d,12)[0]
    check('touch-during-start-settle-no-frames',not g.fires and fl&V['TOUCHED'] and not [r for r in g.requests if r['opcode']==0xf1f1])
    report=dict(passed=True,count=len(checks),checks=checks,module_sha256=m['module_sha256'],host_main_sha256=h['main_payload_sha256'],
                steps=STEPS,camera_access=False,exposures=0,scope=__doc__)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
