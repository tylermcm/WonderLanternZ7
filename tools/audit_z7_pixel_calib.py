"""Pixel-shift calibration run (step 3d): offline audit (MIT).

Same simulated stabiliser, release and restore methods as
audit_z7_pixel_probe.py, with the payload layout measured on the camera
(x/y little-endian int16 at bytes 1-2/3-4). Checks that the nine calibration
frames go out in order - reference, x+80, reference, x-80, y+72, reference,
y-72, (40,36), reference - each fired only while held at (-4x,-4y,-4y)
within +-400 counts, one click each, then centre and Nikon's D2 apply restore
(flags sel[1]|0x80), which ends the hold. No camera, no card, no exposure.
"""
import argparse,hashlib,json,struct
from pathlib import Path
from audit_z7_pixel_probe import ProbeUnit,WORKED
from audit_z7_vr_restore import R
from audit_z7_vr_move import CENTRE,LOG,SLOT,BUSY
from audit_z7_lcd_shutter_sound import WAV
from audit_z7_lcd_grid_persistence import NEW,v3record
from audit_z7_settings_files import PATHS
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output

STEPS=[(0,0),(80,0),(0,0),(-80,0),(0,72),(0,0),(0,-72),(40,36),(0,0)]
def payload(x,y):return bytes([0])+struct.pack('<2h',x,y)+bytes([16,16,0,0,2])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('host','module','output','clip'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text());raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    m=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256'] and hashlib.sha256(packet).hexdigest()==m['module_sha256']
    assert m['configuration'].get('pixel_calib')
    clip=a.clip.read_bytes();symbols=m['symbols'];checks=[]
    def check(name,ok):
        assert ok,name
        checks.append(name)
    journal={NEW[0]:v3record((3,15,1,0,5,0,127,7,0,127,4),0)}
    ProbeUnit.sound_files={WAV:clip}
    f=ProbeUnit(raw,h,packet,dict(journal),works='m1');f.file_paths=PATHS+NEW
    f.u.mem_write(SLOT,bytes(4));f.u.mem_write(BUSY,bytes(4))
    assert f.call(h['symbols']['z7_module_load_once'],STATE)==8
    f.base=f.words()[12];f.setword(40,8);f.reply_addr=f.base+symbols['z7_vm_reply'];f.called_addr=f.base+symbols['z7_vm_d2_called']
    f.setup(f.base,symbols)
    f.call(h['symbols']['z7_module_worker_tick'])
    mv=[r['payload'] for r in f.requests if r['opcode']==0xf1f1]
    check('nine-payloads-then-centre',mv==[payload(x,y) for x,y in STEPS]+[CENTRE])
    check('nine-frames',len(f.fires)==9)
    check('each-fired-held-at-target',[(x['state'],x['target']) for x in f.fires]==[(0x40,[-4*x,-4*y,-4*y]) for x,y in STEPS])
    check('all-within-320',all(max(abs(t) for t in x['target'])<=320 for x in f.fires))
    check('one-click-each',f.r_('z7_vr_clicks')==9)
    check('restore-apply-flags-once',[(c['selection'],c['flags']) for c in f.d2_calls]==[(bytes([2,0x11]),0x91)] and not f.posts and not f.applies)
    for _ in range(32):f.call(h['symbols']['z7_module_worker_tick'])
    d=f.sound_files.get(LOG,b'');hd=struct.unpack_from('<18I',d)
    check('log-records-nine-and-restore',hd[12]==9 and hd[3]&WORKED and hd[3]&R['RESTORED'] and hd[9]&0xff==1 and len(d)==72+192*56)
    report=dict(passed=True,count=len(checks),checks=checks,module_sha256=m['module_sha256'],host_main_sha256=h['main_payload_sha256'],
                steps=STEPS,camera_access=False,exposures=0,scope=__doc__)
    out.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
