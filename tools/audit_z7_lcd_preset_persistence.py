"""Exercise every LCD preset edit/reset with v3 grid-preserving saves (MIT).

Actual compiled menu, native DISP admission and file wrappers execute with
supplied GUI/property/filesystem boundaries. No camera or pixels are tested.
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
    h=json.loads((a.host/'module-host.emulator.json').read_text());raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    m=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256']
    assert hashlib.sha256(packet).hexdigest()==m['module_sha256']
    assert m['configuration']['grid_layout_persistence']
    symbols=m['symbols'];checks=[];defaults=(3,15,1,0,5,0,127,7,0,127,4)
    legacy={PATHS[0]:record(defaults[:10],5)}
    files={**legacy,NEW[0]:v3record(defaults,0)};generation=0
    expected=list(defaults)
    def check(name,good):
        assert good,name
        checks.append(name)
    def word(f,name):return f.read(f.base+symbols[name])
    def model(f):return struct.unpack('<11I',f.u.mem_read(f.base+symbols['z7_menu_settings'],44))
    def load(saved):
        f=PersistenceFixture(raw,h,packet,saved);f.file_paths=PATHS+NEW
        check('load-'+str(len(checks)),f.call(h['symbols']['z7_module_load_once'],STATE)==8)
        f.base=f.words()[12];f.setword(40,8);f.write(f.base+symbols['sm_lcd_rows_ready'],1)
        check('restore-exact-complete-model-'+str(len(checks)),model(f)==tuple(expected) and word(f,'checkpoint_grid_value')==4)
        check('load-read-only-new-journal-'+str(len(checks)),not any(e[0] in ('create','write') or (e[0]=='open' and e[1] in PATHS) for e in f.file_events))
        return f
    def action(f,row,name):
        before=list(f.file_events)
        f.u.mem_write(OBJECT+22,struct.pack('<2H',row,0));f.call(f.base+symbols['sm_activate'])
        check(name+'-no-gui-file-io',f.file_events==before)
        check(name+'-expected-model-grid-intact',model(f)==tuple(expected) and word(f,'checkpoint_grid_value')==4)
    def back(f,name):
        before=list(f.file_events);f.call(f.base+symbols['sm_back_event'])
        check(name+'-navigation-only',f.file_events==before and model(f)==tuple(expected))
    def save(f,name):
        nonlocal generation
        before=dict(f.files);labels=list(f.menu_labels)
        for _ in range(4):f.call(h['symbols']['z7_module_worker_tick'])
        generation+=1;slot=generation%2
        check(name+'-exact-v3-record',f.files[NEW[slot]]==v3record(expected,generation))
        check(name+'-prior-slot-preserved',f.files[NEW[1-slot]]==before[NEW[1-slot]])
        check(name+'-legacy-unchanged',all(f.files[n]==data for n,data in legacy.items()))
        check(name+'-worker-no-paint',f.menu_labels==labels)
        check(name+'-new-path-writes-only',all(e[1] in NEW for e in f.file_events if e[0] in ('create','write')))
        check(name+'-complete-revision-acknowledged',word(f,'z7_settings_revision')==word(f,'z7_persistence_saved_revision'))
    f=load(files)
    for preset in range(4):
        label=('Standard','Minimal','Composition','Exposure')[preset]
        action(f,preset+1,label+'-open')
        check(label+'-correct-view',word(f,'z7_settings_view')==1 and word(f,'z7_settings_preset')==preset)
        expected[1]^=1<<preset;action(f,0,label+'-page-disabled')
        expected[2+preset]^=1;action(f,2,label+'-grid')
        expected[2+preset]^=4;action(f,3,label+'-horizon')
        action(f,1,label+'-information-open')
        for bit in range(6):
            expected[6+preset]^=1<<bit;action(f,bit,label+'-information-'+str(bit))
        action(f,6,label+'-more-open')
        for row,bit in ((0,6),(1,7)):
            expected[6+preset]^=1<<bit;action(f,row,label+'-information-'+str(bit))
        action(f,2,label+'-more-back');back(f,label+'-information-back');back(f,label+'-preset-back')
        save(f,label+'-save-edits');f=load(f.files)
        # Exercise real DISP admission after reload, including the disabled page.
        f.call(h['symbols']['z7_display_before_update'])
        current=word(f,'z7_readout_preset')
        check(label+'-active-page-enabled',bool(expected[1]&(1<<current)))
        for press in range(4):
            current=next((current+step)%4 for step in range(1,5) if expected[1]&(1<<((current+step)%4)))
            f.call(0x1030da56,0x29)
            check(label+'-disp-skips-disabled-'+str(press),word(f,'z7_readout_preset')==current)
            f.call(h['symbols']['z7_display_before_update'])
        action(f,preset+1,label+'-reopen')
        expected[1]^=1<<preset;action(f,0,label+'-page-reenabled')
        back(f,label+'-root');save(f,label+'-save-reenabled')
    for preset in range(4):
        action(f,preset+1,'reset-open-'+str(preset))
        expected[2+preset]=defaults[2+preset];expected[6+preset]=defaults[6+preset]
        action(f,4,'reset-'+str(preset));back(f,'reset-back-'+str(preset))
    check('all-resets-preserve-page-flags-battery-and-grid',tuple(expected)==defaults)
    save(f,'all-resets');f=load(f.files)
    expected[0]^=1;action(f,0,'custom-pages-off');save(f,'custom-pages-off');f=load(f.files)
    check('custom-pages-off-grid-restores',not (model(f)[0]&1) and word(f,'checkpoint_grid_value')==4)
    report=dict(passed=True,module_sha256=m['module_sha256'],host_sha256=h['main_payload_sha256'],checks=len(checks),check_names=checks,
                presets=4,information_bits_per_preset=8,saves=generation,all_presets_cold_reloaded=True,grid_shape_preserved=True,legacy_journals_unchanged=True,
                native_disp_skip_checks=16,camera_access=False,card_written=False,
                limits=['Supplied native GUI/property/filesystem boundaries','No physical menu pixels, lens telemetry, capture/shutdown/output lifecycle or durability proof'])
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k!='check_names'}))


if __name__=='__main__':main()
