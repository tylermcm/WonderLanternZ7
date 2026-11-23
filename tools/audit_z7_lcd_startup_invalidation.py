"""Compare actual LCD initial invalidation with real visibility/page deltas (MIT).

Instruction fixture only: this does not reproduce physical first-frame scanout.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from unicorn import UC_HOOK_CODE
from audit_z7_display_persistence import PersistenceFixture
from audit_z7_settings_files import PATHS
from audit_z7_settings_storage import record
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('host','baseline','module','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text());raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256']
    checks=[];results=[]
    def check(name,good):
        assert good,name
        checks.append(name)
    cases=[('master-off',0,1,0,0,0,0),('unchanged-grid-on',1,1,0,0,1,1),
           ('initial-grid-hidden',1,0,0,0,1,1),('enable-horizon',1,1,0,1,1,1),
           ('leave-native-horizon',1,1,3,0,1,1)]
    for label,master,grid,native,horizon,old_count,new_count in cases:
        pair=[]
        for profile,directory in (('baseline',a.baseline),('candidate',a.module)):
            m=json.loads((directory/'module.json').read_text());packet=(directory/'Z7APP.BIN').read_bytes()
            assert hashlib.sha256(packet).hexdigest()==m['module_sha256']
            if profile=='candidate':assert m['configuration']['initial_grid_delta_only']
            settings=(2|master,15,grid|(horizon<<2),0,5,0,127,7,0,127)
            f=PersistenceFixture(raw,h,packet,{PATHS[0]:record(settings,0)})
            check(label+'-'+profile+'-load',f.call(h['symbols']['z7_module_load_once'],STATE)==8)
            base=f.words()[12];symbols=m['symbols'];f.setword(40,8)
            f.properties[0x2f15]=native;f.u.mem_write(0xa201d65a,bytes([native]))
            invalidations=[]
            def observe(u,address,size,context):invalidations.append(address)
            f.u.hook_add(UC_HOOK_CODE,observe,begin=0x10367c5a,end=0x10367c5a)
            io=list(f.file_events)
            descriptors=struct.unpack('<24I',f.u.mem_read(base+symbols['readout_descriptors'],96))
            def masks():return [bytes(f.u.mem_read(address+4+bank*12,4)) for address in descriptors for bank in range(2)]
            original_masks=masks()
            f.call(h['symbols']['z7_display_before_update'])
            first=len(invalidations);writes=list(f.property_writes)
            mask_changes=sum(x!=y for x,y in zip(original_masks,masks()))
            expected=old_count if profile=='baseline' else new_count
            check(label+'-'+profile+'-first-invalidation-count',first==expected)
            for _ in range(2):f.call(h['symbols']['z7_display_before_update'])
            check(label+'-'+profile+'-settled-update-no-extra-invalidation',len(invalidations)==first)
            reacquire=None
            if label=='unchanged-grid-on':
                check(profile+'-cold-information-mask-changes-still-require-redraw',mask_changes>0)
                # Separate controlled boundary: ownership starts again with the
                # native masks already matching the preset. Do not call this a
                # simulation of physical startup or of the visible flash.
                f.write(base+symbols['z7_base_active'],0)
                f.write(base+symbols['base_grid_valid'],0)
                f.call(h['symbols']['z7_display_before_update'])
                reacquire=len(invalidations)-first
                check(profile+'-matching-mask-grid-on-reacquisition',reacquire==int(profile=='baseline'))
            settled=len(invalidations)
            if master:
                # The live GUI adapter is independently checked by the LCD suite.
                # Here change one RAM component to isolate the native delta path.
                model=base+symbols['z7_menu_settings']
                f.call(base+symbols['z7_settings_component'],model,0,0,int(not grid))
                f.call(h['symbols']['z7_display_before_update'])
                check(label+'-'+profile+'-real-grid-toggle-invalidates',len(invalidations)==settled+1)
                check(label+'-'+profile+'-grid-toggle-does-not-write-page',f.property_writes==writes)
            check(label+'-'+profile+'-update-never-performs-file-io',f.file_events==io)
            pair.append(dict(profile=profile,initial_invalidations=first,initial_readout_mask_changes=mask_changes,matching_masks_reacquisition_invalidations=reacquire,page_writes=writes))
        check(label+'-native-page-writes-unchanged',pair[0]['page_writes']==pair[1]['page_writes'])
        results.append(dict(case=label,comparison=pair))
    candidate=json.loads((a.module/'module.json').read_text());baseline=json.loads((a.baseline/'module.json').read_text())
    report=dict(passed=True,module_sha256=candidate['module_sha256'],baseline_sha256=baseline['module_sha256'],host_sha256=h['main_payload_sha256'],checks=len(checks),check_names=checks,cases=results,
                cold_initial_redraw_removed=False,matching_masks_reacquisition_redraw_removed=True,
                owner_visible_startup_flash_reproduced=False,hardware_fix_confirmed=False,card_written=False,
                limits=['Supplied native GUI/property/filesystem context','Actual compiled before-update and native invalidation/page-setter instructions execute','No first-frame cached geometry, scanout or physical boot timing'])
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('check_names','cases')}))


if __name__=='__main__':main()
