"""Exercise exact LCD preference-journal fault/restart paths offline (MIT).

Native file/UI services are supplied. No physical write durability is implied.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from audit_z7_display_persistence import PersistenceFixture
from audit_z7_lcd_release import DEFAULTS, OBJECT
from audit_z7_settings_files import PATHS, ERROR
from audit_z7_settings_storage import record
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('host','module','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text())
    raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    m=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256']
    assert hashlib.sha256(packet).hexdigest()==m['module_sha256']
    assert m['kind'] in ('original-Z7-LCD-persistence-checkpoint','original-Z7-LCD-startup-grid-checkpoint')
    symbols=m['symbols'];checks=[]
    def check(name,good):
        assert good,name
        checks.append(name)
    def word(f,n):return f.read(f.base+symbols[n])
    def model(f):return struct.unpack('<10I',f.u.mem_read(f.base+symbols['z7_menu_settings'],40))
    def load(files=None,faults=None):
        f=PersistenceFixture(raw,h,packet,files,faults)
        status=f.call(h['symbols']['z7_module_load_once'],STATE)
        f.base=f.words()[12];f.setword(40,status)
        check('resident-load-'+str(len(checks)),status==8 and f.words()[50]==1)
        f.write(f.base+symbols['sm_lcd_rows_ready'],1)
        check('startup-never-writes-'+str(len(checks)),not any(e[0] in ('create','write') for e in f.file_events))
        return f
    def action(f,row):
        before=list(f.file_events)
        f.u.mem_write(OBJECT+22,struct.pack('<2H',row,0));f.call(f.base+symbols['sm_activate'])
        check('gui-action-no-file-io-'+str(len(checks)),f.file_events==before)
    def tick(f,n):
        labels=list(f.menu_labels)
        for _ in range(n):f.call(h['symbols']['z7_module_worker_tick'])
        check('worker-never-renders-native-labels-'+str(len(checks)),f.menu_labels==labels)
    def title(f,text):
        f.call(f.base+symbols['sm_render'],OBJECT)
        check('status-'+text+'-'+str(len(checks)),[s for slot,s in f.menu_labels if slot==230][-1]=='Display: '+text)

    f=load();check('missing-slots-defaults',model(f)==DEFAULTS)
    title(f,'Defaults');before=list(f.file_events);tick(f,12)
    check('idle-defaults-do-not-create-journals',f.file_events==before and not f.files)
    action(f,0);title(f,'Unsaved');before=list(f.file_events);tick(f,3)
    check('debounce-first-three-observations-no-io',f.file_events==before)
    tick(f,1);first=model(f);title(f,'Saved')
    check('first-save-slot-zero-exact-v1',f.files=={PATHS[0]:record(first,0)})
    action(f,5);tick(f,4);second=model(f)
    check('battery-save-alternates-and-keeps-prior',f.files=={PATHS[0]:record(first,0),PATHS[1]:record(second,1)})
    restart=load(f.files)
    check('restart-restores-both-toggles',model(restart)==second and word(restart,'z7_battery_enabled')==1)
    check('grid-layout-deliberately-starts-thirds',word(restart,'checkpoint_grid_value')==2)
    before=list(restart.file_events);tick(restart,12)
    check('clean-restart-does-not-write',restart.file_events==before)

    original={PATHS[0]:record(DEFAULTS,2)}
    for fault in ('open','read','close'):
        bad=load(original,{fault:ERROR});title(bad,'Restart to save')
        check(fault+'-startup-blocks-saving',not word(bad,'z7_persistence_ready'))
        action(bad,0);before=list(bad.file_events);tick(bad,12)
        check(fault+'-startup-never-overwrites-unread-original',bad.file_events==before and bad.files==original)

    f=load(original);action(f,0);f.faults['create']=ERROR;tick(f,4);title(f,'Save retry')
    check('create-failure-preserves-prior-and-dirty',f.files==original and word(f,'z7_persistence_saved_revision')==0)
    del f.faults['create'];before=list(f.file_events);tick(f,5)
    check('retry-backoff-five-ticks',f.file_events==before)
    tick(f,1);title(f,'Saved')
    check('retry-writes-other-slot',f.files[PATHS[0]]==original[PATHS[0]] and f.files[PATHS[1]]==record(model(f),3))

    f=load(original);action(f,0);f.write_prefix=37;tick(f,4)
    check('short-write-keeps-good-slot-and-dirty',f.files[PATHS[0]]==original[PATHS[0]] and len(f.files[PATHS[1]])==37 and not word(f,'z7_persistence_saved_revision'))
    restart=load(f.files)
    check('restart-after-torn-write-uses-good-prior',model(restart)==DEFAULTS)

    f=load(original);action(f,0);f.faults['close']=ERROR;tick(f,4);title(f,'Restart to save')
    before=list(f.file_events);tick(f,12)
    check('uncertain-close-latches-and-stops-further-io',f.file_events==before and word(f,'z7_settings_revision')!=word(f,'z7_persistence_saved_revision'))
    report=dict(passed=True,module_sha256=m['module_sha256'],host_sha256=h['main_payload_sha256'],checks=len(checks),check_names=checks,
                journal_version=1,grid_layout_persisted=False,camera_access=False,card_written=False,hardware_tested=False,
                limits=['Native filesystem and UI services supplied','No physical durability, shutdown flush, menu lifecycle or recovery proof'])
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='check_names'}))


if __name__=='__main__':main()
