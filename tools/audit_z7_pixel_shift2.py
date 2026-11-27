"""Pixel-shift series v2 (Z7_PIXEL_SHIFT_V2): offline audit (MIT).

Same fixture as audit_z7_pixel_shift.py. Checks the two changes from the
dead-zone run (615cf144): a 7 s start settle after the button is free
(touching it then cancels), and every frame approached from 36 y-steps above
its target - payloads (x, y+36) then (x, y) for each calibrated corner -
with each release only while the target itself is held, plus the 0.5 s
settle and re-check, one click per frame, recentre and the D2 apply restore.
No camera, no card, no exposure.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from audit_z7_pixel_shift import ShiftUnit,pos,CORNERS
from audit_z7_pixel_release import V
from audit_z7_pixel_series import S
from audit_z7_vr_restore import R
from audit_z7_vr_move import CENTRE,LOG,SLOT,BUSY
from audit_z7_lcd_shutter_sound import WAV
from audit_z7_lcd_grid_persistence import NEW,v3record
from audit_z7_settings_files import PATHS
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('host','module','output','clip'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text());raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    m=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256'] and hashlib.sha256(packet).hexdigest()==m['module_sha256']
    assert m['configuration'].get('pixel_shift2')
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
    want=[]
    for cx,cy in CORNERS:want+=[pos(cx,cy+36),pos(cx,cy)]
    check('approach-from-above-then-target-each-corner',moves(f)==want+[CENTRE])
    check('four-fires',len(f.fires)==4)
    check('fired-only-at-target-not-approach',[(x['state'],x['target']) for x in f.fires]==[(0x40,[-4*cx,-4*cy,-4*cy]) for cx,cy in CORNERS])
    before=[ms for kind,ms,n in f.timeline if n==0]
    check('seven-second-start-settle',sum(ms for ms in before if ms==100)>=7000)
    per=[[ms for kind,ms,n in f.timeline if n==k] for k in range(4)]
    check('500ms-settle-before-each-release',all(500 in x for x in per))
    check('one-click-per-frame',f.r_('z7_vr_clicks')==4)
    check('restore-with-apply-flags',[(c['selection'],c['flags']) for c in f.d2_calls]==[(bytes([2,0x11]),0x91)])
    check('max-target-216',all(abs(t)<=216 for r in f.requests if r['opcode']==0xf1f1 for t in [-4*v for v in struct.unpack('<2h',r['payload'][1:5])]))
    tick(f,32);fl=flags(f)
    check('flags-complete-and-restored',fl&S['SERIES_COMPLETE'] and fl&R['RESTORED'] and not fl&(V['REFUSED']|V['FRAME_FAILED']|V['TOUCHED']))
    g=load(touch_in_settle=True);tick(g);tick(g,32)
    check('touch-during-start-settle-no-moves',not g.fires and flags(g)&V['TOUCHED'] and not moves(g))
    g=load(lose_hold_frame=1);tick(g);tick(g,32)
    check('lost-hold-in-settle-no-release',len(g.fires)==1 and flags(g)&S['HOLD_LOST'] and moves(g)[-1]==CENTRE)
    report=dict(passed=True,count=len(checks),checks=checks,module_sha256=m['module_sha256'],host_main_sha256=h['main_payload_sha256'],
                corners=CORNERS,approach_y=36,camera_access=False,exposures=0,scope=__doc__)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
