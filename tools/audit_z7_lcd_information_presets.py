"""Saved native Information display and compact-menu compatibility audit (MIT).

Compiled menu, codec, worker and native file wrappers execute. Incoming GUI,
files and selected rendering boundaries are supplied; no physical persistence.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from audit_z7_display_persistence import PersistenceFixture
from audit_z7_lcd_grid_persistence import NEW,OBJECT,v3record
from audit_z7_settings_files import PATHS
from audit_z7_settings_storage import record
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('host','module','rollback','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text())
    m=json.loads((a.module/'module.json').read_text())
    raw=(a.host/'module-host.emulator.main.bin').read_bytes();packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256']
    assert hashlib.sha256(packet).hexdigest()==m['module_sha256'] and m['configuration']['information_page']
    s=m['symbols'];expected=[0,15,1,0,5,0,127,7,0,127,4];checks=[];generation=0
    legacy={PATHS[0]:record(expected[:10],3)}
    def check(name,good):
        assert good,name
        checks.append(name)
    def model(f):return list(struct.unpack('<11I',f.u.mem_read(f.base+s['z7_menu_settings'],44)))
    def load(files):
        f=PersistenceFixture(raw,h,packet,files);f.file_paths=PATHS+NEW
        check('load-'+str(len(checks)),f.call(h['symbols']['z7_module_load_once'],STATE)==8)
        f.base=f.words()[12];f.setword(40,8);f.write(f.base+s['sm_lcd_rows_ready'],1)
        check('exact-cold-model-'+str(len(checks)),model(f)==expected)
        return f
    def action(f,row,name):
        events=list(f.file_events);f.u.mem_write(OBJECT+22,struct.pack('<2H',row,0))
        f.call(f.base+s['sm_activate'])
        check(name+'-model',model(f)==expected)
        check(name+'-no-gui-file-io',f.file_events==events)
    def save(f,name):
        nonlocal generation
        previous=dict(f.files);labels=list(f.menu_labels)
        for _ in range(4):f.call(h['symbols']['z7_module_worker_tick'])
        generation+=1;slot=generation%2
        check(name+'-exact-v3-record',f.files[NEW[slot]]==v3record(expected,generation))
        check(name+'-previous-journal-preserved',f.files[NEW[1-slot]]==previous[NEW[1-slot]])
        check(name+'-legacy-preserved',all(f.files[n]==data for n,data in legacy.items()))
        check(name+'-worker-no-rendering',f.menu_labels==labels)
    f=load({**legacy,NEW[0]:v3record(expected,0)})
    action(f,99,'invalid-root-row')
    expected[1]=31;action(f,5,'information-enable')
    check('seven-root-rows',f.read(f.base+s['sm_meta']+20)==0x00070007)
    check('correct-information-and-battery-labels',[dict(f.menu_labels)[236+i] for i in range(2)]==['Information display','Battery percentage'])
    expected[0]=2;action(f,6,'battery-enable-independent');save(f,'information-and-battery');f=load(f.files)
    for preset in range(4):
        action(f,preset+1,'preset-open-'+str(preset))
        expected[1]&=~(1<<preset);action(f,0,'disable-preset-'+str(preset))
        f.call(f.base+s['sm_back_event'])
    check('native-information-can-be-only-page',expected[1]==16)
    action(f,5,'last-page-disable-is-rejected');save(f,'information-only');f=load(f.files)
    rollback_files=dict(f.files);rollback_expected=list(expected)
    action(f,1,'standard-open');expected[1]=17;action(f,0,'standard-enable')
    f.call(f.base+s['sm_back_event']);expected[1]=1;action(f,5,'information-disable')
    check('information-disable-preserves-battery-and-grid',model(f)==expected and expected[0]==2 and expected[10]==4)
    save(f,'information-disabled');f=load(f.files)
    oldmeta=json.loads((a.rollback/'module.json').read_text());oldpacket=(a.rollback/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(oldpacket).hexdigest()==oldmeta['module_sha256']
    old=PersistenceFixture(raw,h,oldpacket,rollback_files);old.file_paths=PATHS+NEW
    check('rollback-loads-information-only-record',old.call(h['symbols']['z7_module_load_once'],STATE)==8)
    restored=list(struct.unpack('<11I',old.u.mem_read(old.words()[12]+oldmeta['symbols']['z7_menu_settings'],44)))
    rollback_expected[1]=1
    check('rollback-restores-standard-with-other-preferences-intact',restored==rollback_expected)
    check('rollback-loader-does-not-write-settings',old.files==rollback_files and not any(e[0] in ('create','write') for e in old.file_events))
    r=dict(passed=True,count=len(checks),checks=checks,module_sha256=m['module_sha256'],
        rollback_sha256=oldmeta['module_sha256'],alternating_saves=generation,wire_version=3,
        camera_access=False,physical_persistence=False,actual_pixels=False,scope=__doc__)
    out.write_text(json.dumps(r,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(checks),saves=generation)))


if __name__=='__main__':main()
