"""Exercise saved histogram/horizon controls in the integrated LCD module (MIT).

Compiled GUI/codec/worker instructions; supplied file and rendering boundaries.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from audit_z7_display_persistence import PersistenceFixture
from audit_z7_lcd_grid_persistence import NEW, OBJECT, v3record
from audit_z7_settings_files import PATHS
from audit_z7_settings_storage import record
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('host','module','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text())
    m=json.loads((a.module/'module.json').read_text())
    raw=(a.host/'module-host.emulator.main.bin').read_bytes();packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256']
    assert hashlib.sha256(packet).hexdigest()==m['module_sha256'] and m['configuration']['histogram_presets']
    symbols=m['symbols'];expected=[3,15,1,0,5,0,127,7,0,127,4]
    legacy={PATHS[0]:record(expected[:10],5)}
    files={**legacy,NEW[0]:v3record(expected,0)};generation=0;checks=[]
    def check(name,good):
        assert good,name
        checks.append(name)
    def model(f):return list(struct.unpack('<11I',f.u.mem_read(f.base+symbols['z7_menu_settings'],44)))
    def load(saved):
        f=PersistenceFixture(raw,h,packet,saved);f.file_paths=PATHS+NEW
        check('resident-load-'+str(len(checks)),f.call(h['symbols']['z7_module_load_once'],STATE)==8)
        f.base=f.words()[12];f.setword(40,8);f.write(f.base+symbols['sm_lcd_rows_ready'],1)
        check('cold-restores-all-fields-'+str(len(checks)),model(f)==expected)
        check('loader-does-not-rewrite-settings-'+str(len(checks)),not any(e[0] in ('create','write') for e in f.file_events))
        return f
    def action(f,row,name):
        before=list(f.file_events);f.u.mem_write(OBJECT+22,struct.pack('<2H',row,0))
        f.call(f.base+symbols['sm_activate'])
        check(name+'-no-gui-file-io',f.file_events==before)
        check(name+'-model-grid-and-other-presets-intact',model(f)==expected)
    def save(f,name):
        nonlocal generation
        before=dict(f.files);labels=list(f.menu_labels)
        for _ in range(4):f.call(h['symbols']['z7_module_worker_tick'])
        generation+=1;slot=generation%2
        check(name+'-exact-v3-histogram-record',f.files[NEW[slot]]==v3record(expected,generation))
        check(name+'-previous-slot-preserved',f.files[NEW[1-slot]]==before[NEW[1-slot]])
        check(name+'-legacy-record-untouched',all(f.files[n]==data for n,data in legacy.items()))
        check(name+'-worker-never-renders',f.menu_labels==labels)
        check(name+'-writes-owned-new-journals-only',all(e[1] in NEW for e in f.file_events if e[0] in ('create','write')))
    f=load(files)
    for preset in range(4):
        name=('Standard','Minimal','Composition','Exposure')[preset]
        action(f,preset+1,name+'-open')
        check(name+'-six-native-controls',f.read(f.base+symbols['sm_meta']+20)==0x00070006)
        check(name+'-correct-row-order',[dict(f.menu_labels)[231+i] for i in range(6)]==
              ['Page enabled','Shooting information','Framing grid','Histogram','Virtual horizon','Reset preset'])
        expected[2+preset]^=2;action(f,3,name+'-histogram-on')
        check(name+'-histogram-status-on',dict(f.menu_labels)[241]=='ON')
        expected[2+preset]^=4;action(f,4,name+'-independent-horizon')
        save(f,name);f=load(f.files)
    action(f,1,'Standard-reopen');expected[2]^=2;action(f,3,'Standard-histogram-off')
    check('off-retains-horizon-and-other-three-histograms',not expected[2]&2 and all(v&2 for v in expected[3:6]))
    save(f,'histogram-off');f=load(f.files)
    rollback_expected=list(expected)
    action(f,3,'Composition-reopen')
    expected[4]=5;expected[8]=0;action(f,5,'Composition-reset')
    check('reset-returns-grid-horizon-default-without-changing-other-presets',model(f)==expected and expected[4]==5)
    before=model(f);action(f,6,'out-of-range-preset-row');check('invalid-row-ignored',model(f)==before)
    # A rollback must disable unsupported histogram bits before GUI readiness.
    old_dir=Path('.private/review/20261122-lcd-grid-persistence-01/candidate')
    old_meta=json.loads((old_dir/'module.json').read_text())
    old_packet=(old_dir/'Z7APP.BIN').read_bytes()
    check('exact-hardware-tested-rollback',hashlib.sha256(old_packet).hexdigest()==
          'f848e62de232776a27fef9f481452d590901ff5fb95de2c564fe6e46611cc00e')
    old=PersistenceFixture(raw,h,old_packet,f.files);old.file_paths=PATHS+NEW
    check('rollback-loads-histogram-record',old.call(h['symbols']['z7_module_load_once'],STATE)==8)
    restored=list(struct.unpack('<11I',old.u.mem_read(old.words()[12]+old_meta['symbols']['z7_menu_settings'],44)))
    check('rollback-removes-only-unsupported-histogram-components',
          restored==[v&~2 if 2<=i<6 else v for i,v in enumerate(rollback_expected)])
    check('rollback-loader-preserves-file-bytes',old.files==f.files and not any(e[0] in ('create','write') for e in old.file_events))
    r=dict(passed=True,count=len(checks),checks=checks,module_sha256=m['module_sha256'],host_main_sha256=h['main_payload_sha256'],
        histogram_presets=4,alternating_saves=generation,wire_version=3,grid_shape_preserved=True,legacy_files_unchanged=True,
        no_gui_file_io=True,camera_access=False,actual_histogram_pixels=False,physical_statistics_verified=False)
    out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks),presets=4,saves=generation)))


if __name__=='__main__':main()
