"""Movie/photo LCD battery admission and transition audit (MIT).

Compiled module, native getter and object helpers execute. GUI/icon/movie flags,
telemetry input, files and selected drawing services are supplied. This does not
prove the physical movie HUD layout, recording scheduler or framebuffer pixels.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from audit_z7_display_persistence import PersistenceFixture
from audit_z7_battery_percent import ICON, CONTROL
from audit_z7_lcd_grid_persistence import NEW
from audit_z7_settings_files import PATHS
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('host','module','baseline','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text())
    raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256']
    checks=[]
    def check(name,good):
        assert good,name
        checks.append(name)
    def load(directory):
        m=json.loads((directory/'module.json').read_text());packet=(directory/'Z7APP.BIN').read_bytes()
        assert hashlib.sha256(packet).hexdigest()==m['module_sha256']
        f=PersistenceFixture(raw,h,packet)
        f.file_paths=PATHS+NEW
        check(directory.name+'-loads',f.call(h['symbols']['z7_module_load_once'],STATE)==8)
        f.base=f.words()[12];f.setword(40,8);s=m['symbols']
        # Battery percentage is root row 5, or row 6 once Information display
        # occupies row 5 in the --information-page profile.
        battery_row=6 if m['configuration'].get('information_page') else 5
        f.u.mem_write(0xa1833548+22,struct.pack('<2H',0,battery_row))
        f.call(f.base+s['sm_activate'])
        check(directory.name+'-global-switch-enables-battery',f.read(f.base+s['z7_battery_enabled'])==1)
        return f,m,s
    def frame(f):
        f.call(h['symbols']['z7_display_before_paint'])
        f.call(h['symbols']['z7_display_after_paint'])
    old,oldmeta,olds=load(a.baseline)
    old.u.mem_write(0xa201d510,b'\1');frame(old)
    check('baseline-still-excludes-movie',not old.getter_calls and not old.read(old.base+olds['z7_battery_object']))
    f,m,s=load(a.module)
    assert m['configuration']['movie_battery'] and m['configuration']['histogram_presets']
    def word(name):return f.read(f.base+s['z7_battery_'+name])
    def paint():
        f.paint_calls.clear()
        f.call(f.base+s['painter'],word('object'),0,0,0)
        return [p[0] for p in f.paint_calls]
    f.u.mem_write(0xa201d510,b'\1');frame(f)
    obj=word('object')
    check('movie-lcd-matching-icon-admits-percentage',obj and f.labels==[('63%',299)] and f.getter_calls==1)
    check('movie-painter-composes-native-battery-silhouette',paint()==[0x10433912]*5+[0x10384968])
    count=f.getter_calls
    for _ in range(15):frame(f)
    check('movie-sampling-retains-fifteen-frame-throttle',f.getter_calls==count)
    frame(f);check('movie-sixteenth-frame-samples',f.getter_calls==count+1)
    for mode in (0,1,0,1):
        f.u.mem_write(0xa201d510,bytes([mode]));frame(f)
        check('photo-movie-transition-reuses-object-'+str(len(checks)),word('object')==obj and len(f.list_calls)==1)
        check('photo-movie-transition-keeps-painter-'+str(len(checks)),paint()==[0x10433912]*5+[0x10384968])
    def exclusion(name,address,data):
        previous=bytes(f.u.mem_read(address,len(data)));f.u.mem_write(address,data)
        count=f.getter_calls;labels=list(f.labels);frame(f)
        check(name+'-does-not-sample-or-rewrite-label',f.getter_calls==count and f.labels==labels)
        calls=paint()
        check(name+'-retires-percentage',f.read(obj+0x28)==0 and not any(
            address==0x10384968 and int.from_bytes(blob[:4],'little')==0x7a40 for address,blob in f.paint_calls))
        f.u.mem_write(address,previous);frame(f)
        check(name+'-returns-with-same-owned-object',word('object')==obj and f.read(obj+0x28)==1 and len(f.list_calls)==1)
    for name,address,data in (
        ('evf',0xa18237c6,b'\2'),('unknown-output',0xa18237c6,b'\xff'),
        ('unknown-mode',0xa201d510,b'\2'),('bar-fallback',0xa18b4de8,struct.pack('<I',1)),
        ('hidden-native-icon',ICON+40,bytes(4)),('adapter',ICON+8,struct.pack('<I',0x112a)),
        ('alternate-layout',ICON+16,struct.pack('<I',658|(396<<16))),
        ('foreign-painter',ICON+76,struct.pack('<I',0x100202b5)),
        ('menu',0xa2c41008,struct.pack('<I',1))):exclusion(name,address,data)
    battery_row=6 if m['configuration'].get('information_page') else 5
    f.u.mem_write(0xa1833548+22,struct.pack('<2H',0,battery_row));f.call(f.base+s['sm_activate'])
    check('same-global-switch-disables-movie-overlay',word('enabled')==0)
    count=f.getter_calls;frame(f);paint()
    for _ in range(32):frame(f)
    check('disabled-movie-does-no-telemetry-work',f.getter_calls==count and f.read(obj+0x28)==0)
    check('gui-transitions-never-write-settings-files',not any(e[0] in ('create','write') for e in f.file_events))
    result=dict(passed=True,count=len(checks),checks=checks,module_sha256=m['module_sha256'],
        baseline_sha256=oldmeta['module_sha256'],host_main_sha256=h['main_payload_sha256'],
        camera_access=False,actual_pixels_verified=False,physical_movie_layout_verified=False,
        recording_scheduler_verified=False,scope=__doc__)
    out.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks))))


if __name__=='__main__':main()
