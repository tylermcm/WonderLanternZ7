"""Execute v3 LCD grid preferences with independent records and cold reloads (MIT).

Native file/UI services are supplied; physical durability is not established.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from audit_z7_display_persistence import PersistenceFixture
from audit_z7_settings_files import PATHS, ERROR
from audit_z7_settings_storage import record, seal
from audit_splash_image import MEM
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output

NEW=('A:\\Z7DSP0.DAT','A:\\Z7DSP1.DAT')
DEFAULT=(3,15,1,0,5,0,127,7,0,127,2)
OBJECT=0xa1833548


def v3record(model,generation):
    payload=seal(struct.pack('<16I',0x3143375a,3,0x03800007,0,*model[:10],model[10],0))
    return seal(struct.pack('<4I',0x314a375a,1,generation,0)+payload)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('host','module','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text());raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    m=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256']
    assert hashlib.sha256(packet).hexdigest()==m['module_sha256']
    assert m['configuration']['grid_layout_persistence']
    symbols=m['symbols'];checks=[];legacy={PATHS[0]:record(DEFAULT[:10],5)}
    def check(name,good):
        assert good,name
        checks.append(name)
    def word(f,n):return f.read(f.base+symbols[n])
    def model(f):return struct.unpack('<11I',f.u.mem_read(f.base+symbols['z7_menu_settings'],44))
    def load(files=None,faults=None):
        f=PersistenceFixture(raw,h,packet,legacy if files is None else files,faults)
        f.file_paths=PATHS+NEW
        status=f.call(h['symbols']['z7_module_load_once'],STATE)
        f.base=f.words()[12];f.setword(40,status)
        check('resident-load-'+str(len(checks)),status==8 and f.words()[50]==1)
        f.write(f.base+symbols['sm_lcd_rows_ready'],1)
        check('startup-no-write-'+str(len(checks)),not any(e[0] in ('create','write') for e in f.file_events))
        check('legacy-selector-cleared-'+str(len(checks)),word(f,'lcd_grid_legacy_paths')==0)
        return f
    def tick(f,n=4):
        labels=list(f.menu_labels)
        for _ in range(n):f.call(h['symbols']['z7_module_worker_tick'])
        check('worker-never-renders-'+str(len(checks)),f.menu_labels==labels)
        check('worker-writes-new-owned-slots-only-'+str(len(checks)),all(e[1] in NEW for e in f.file_events if e[0] in ('create','write')))
    def choose(f,name,value):
        before=list(f.file_events);f.call(f.base+symbols[name])
        check(name+'-gui-no-io-'+str(len(checks)),f.file_events==before)
        check(name+'-model-and-ram-'+str(len(checks)),model(f)[10]==value and word(f,'checkpoint_grid_value')==value)
        check(name+'-native-boolean-only-'+str(len(checks)),f.property_writes[-1]==(0x102d,1))
    def originals(f):return all(f.files.get(path)==data for path,data in legacy.items())

    f=load();check('v1-fallback-preserves-all-preferences',model(f)==DEFAULT)
    for version,shape,reserved in ((3,0,0),(3,6,0),(3,0xffffffff,0),(3,2,1),(2,2,0),(4,2,0)):
        data=seal(struct.pack('<16I',0x3143375a,version,0x03800007,0,*DEFAULT[:10],shape,reserved))
        f.u.mem_write(MEM+0x10000,data);f.u.mem_write(MEM+0x11000,b'\xa5'*44)
        good=f.call(f.base+symbols['z7_settings_decode'],MEM+0x10000,64,MEM+0x11000)
        check('codec-rejects-with-output-intact-'+str((version,shape,reserved)),good==0 and bytes(f.u.mem_read(MEM+0x11000,44))==b'\xa5'*44)
    before=list(f.file_events);tick(f,8)
    check('v1-load-never-automigrates-or-creates-new-slots',f.files==legacy and f.file_events==before)
    for generation,(name,value) in enumerate((('fourths',1),('thirds',2),('golden',3),('center',4),('dense',5))):
        prior=dict(f.files);choose(f,name,value);tick(f)
        current=model(f);slot=generation%2
        check(name+'-exact-v3-new-slot',f.files[NEW[slot]]==v3record(current,generation))
        check(name+'-old-v1-never-written',originals(f))
        if generation:check(name+'-other-new-slot-preserved',f.files[NEW[1-slot]]==prior[NEW[1-slot]])
        restarted=load(f.files)
        check(name+'-fresh-load-restores-shape-and-preferences',model(restarted)==current and word(restarted,'checkpoint_grid_value')==value)
        check(name+'-new-slots-preferred-without-opening-legacy',not any(e[0]=='open' and e[1] in PATHS for e in restarted.file_events))
    # An ordinary menu edit must retain the appended field in its coherent snapshot.
    f.u.mem_write(OBJECT+22,struct.pack('<2H',5,0));before=list(f.file_events)
    f.call(f.base+symbols['sm_activate'])
    check('battery-toggle-no-io-retains-grid',f.file_events==before and model(f)[0]==1 and model(f)[10]==5)
    tick(f);check('battery-toggle-saves-v3-with-grid-retained',f.files[NEW[1]]==v3record(model(f),5) and originals(f))
    f.call(f.base+symbols['sm_render'],OBJECT)
    check('compact-root-menu-retained',[dict(f.menu_labels)[231+i] for i in range(6)]==['Custom pages','Standard','Minimal','Composition','Exposure','Battery percentage'])

    for name,data in (('corrupt',b'x'*80),('unknown-version',seal(struct.pack('<4I',0x314a375a,1,0,0)+seal(struct.pack('<16I',0x3143375a,4,0x03800007,0,*DEFAULT[:10],2,0))))):
        files={**legacy,NEW[0]:data};bad=load(files)
        check(name+'-new-slot-blocks-default-or-legacy-overwrite',not word(bad,'z7_persistence_ready') and not any(e[0]=='open' and e[1] in PATHS for e in bad.file_events))
        choose(bad,'center',4);before=list(bad.file_events);tick(bad,8)
        check(name+'-blocked-worker-leaves-all-files',bad.file_events==before and bad.files==files)
    bad=load(faults={'open':ERROR});check('read-errors-block-saving',not word(bad,'z7_persistence_ready'))
    before=list(bad.file_events);choose(bad,'dense',5);tick(bad,8)
    check('read-errors-never-create-new-or-change-legacy',bad.files==legacy and bad.file_events==before)

    f=load();choose(f,'center',4);f.faults['create']=ERROR;tick(f)
    check('create-failure-preserves-legacy-and-dirty',f.files==legacy and not word(f,'z7_persistence_saved_revision'))
    del f.faults['create'];before=list(f.file_events);tick(f,5)
    check('create-retry-backs-off',f.file_events==before)
    tick(f,1);check('create-retry-writes-only-new-slot',f.files[NEW[0]]==v3record(model(f),0) and originals(f))
    f=load();choose(f,'dense',5);f.write_prefix=37;tick(f)
    check('short-write-not-acknowledged-legacy-preserved',len(f.files[NEW[0]])==37 and originals(f) and not word(f,'z7_persistence_saved_revision'))
    restarted=load(f.files);check('short-new-record-blocks-silent-legacy-fallback',not word(restarted,'z7_persistence_ready') and originals(restarted))
    f=load();choose(f,'center',4);f.faults['close']=ERROR;tick(f)
    before=list(f.file_events);tick(f,8)
    check('uncertain-close-latches-without-more-io',f.file_events==before and originals(f) and not word(f,'z7_persistence_saved_revision'))
    check('all-writes-target-new-owned-slots',all(e[1] in NEW for e in f.file_events if e[0] in ('create','write')))
    report=dict(passed=True,module_sha256=m['module_sha256'],host_sha256=h['main_payload_sha256'],checks=len(checks),check_names=checks,
                payload_version=3,journal_version=1,legacy_slots_read_only=True,new_paths=list(NEW),all_five_shapes_saved_and_cold_reloaded=True,
                camera_access=False,card_written=False,hardware_tested=False,
                limits=['Supplied file/GUI/native-property services','No physical shutdown, durability, scanout or camera recovery proof'])
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='check_names'}))


if __name__=='__main__':main()
