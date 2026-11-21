# SPDX-License-Identifier: MIT
"""Offline SD-only comparison: retain UI init, skip settings prepare/worker.

Not a repair or firmware image. The host still reads this module and ordinary
camera I/O is unchanged. Existing component licenses/notices remain applicable.
No card deployment or hardware trial is authorized by generating this file.
"""
import argparse
import hashlib
import json
from pathlib import Path

from build_z7_noinit_diagnostic import disable_entry, RETURN_ZERO
from build_z7_module import HEADER, seal
from prepare_flash_review import require_private_output

FUNCTIONS = ('persistence_prepare','persistence_worker')


def suppress_settings_io(packet, expected_sha256, symbols):
    packet=bytes(packet)
    _,layout=disable_entry(packet,expected_sha256)  # Canonical source validation.
    ranges=[]
    for name in FUNCTIONS:
        value=symbols.get(name)
        if not isinstance(value,int) or not value & 1:
            raise ValueError('Missing Thumb function: '+name)
        offset=value & ~1
        if offset+4>layout['image_bytes'] or offset<0:
            raise ValueError('Function outside image')
        if offset<layout['entry_offset']+4 and layout['entry_offset']<offset+4:
            raise ValueError('Patch overlaps module entry')
        if any(offset<r+4 and r<offset+4 for r in layout['relocations']):
            raise ValueError('Patch overlaps relocation')
        if any(offset<previous+4 and previous<offset+4 for _,previous in ranges):
            raise ValueError('Function patches overlap')
        ranges.append((name,offset))
    modified=bytearray(packet); allowed=set(range(32,36))
    for _,offset in ranges:
        modified[HEADER+offset:HEADER+offset+4]=RETURN_ZERO
        allowed.update(range(HEADER+offset,HEADER+offset+4))
    modified=seal(modified)
    assert len(modified)==len(packet)
    assert all(a==b or i in allowed for i,(a,b) in enumerate(zip(packet,modified)))
    return modified,layout,dict(ranges)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('module','build','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();output=require_private_output(a.output)
    source=json.loads((a.module/'module.json').read_text())
    if source['kind']!='original-Z7-LCD-first-release-candidate':
        raise ValueError('Requires quarantined original LCD module')
    packet,layout,patches=suppress_settings_io((a.module/'Z7APP.BIN').read_bytes(),source['module_sha256'],source['symbols'])
    for name in ('entry_offset','image_bytes','bss_bytes','relocations','file_bytes'):
        if layout[name]!=source[name]:raise ValueError('Source metadata mismatch')
    from audit_z7_display_persistence import PersistenceFixture
    from build_z7_module_host import STATE
    from unicorn import UC_HOOK_CODE
    raw=(a.build/'module-host.emulator.main.bin').read_bytes()
    host=json.loads((a.build/'module-host.emulator.json').read_text())
    if hashlib.sha256(raw).hexdigest()!=host['main_payload_sha256']:raise ValueError('Exact host required')
    f=PersistenceFixture(raw,host,packet)
    status=f.call(host['symbols']['z7_module_load_once'],STATE)
    assert status==8
    f.setword(40,status)
    base=f.words()[12]
    assert f.words()[22:24]==(1,1) and f.words()[50]==1
    # The fixture also records the loader's cache maintenance here. Actual
    # settings opens/reads/writes/closes have different event names.
    assert all(e[0] in ('clean','invalidate') for e in f.file_events), 'Settings filesystem was accessed'
    assert not f.handles and not f.files
    loader_cache_events=list(f.file_events)
    assert bytes(f.u.mem_read(base+source['symbols']['z7_persistence_files'],4))==bytes(4)
    assert int.from_bytes(f.u.mem_read(0xa182ed34,4),'little')==base+source['symbols']['sm_menu_dispatch']
    worker=base+patches['persistence_worker'];seen=[]
    f.u.hook_add(UC_HOOK_CODE,lambda u,pc,size,ctx:seen.append(pc),begin=worker,end=worker+3)
    f.call(host['symbols']['z7_module_worker_tick'])
    assert seen==[worker,worker+2] and f.file_events==loader_cache_events
    report=dict(kind='original-Z7-settings-io-disabled-diagnostic',**layout,
                source_module_sha256=source['module_sha256'],module_sha256=hashlib.sha256(packet).hexdigest(),
                host_main_sha256=host['main_payload_sha256'],patches=patches,
                native_load_status=status,display_registration=True,worker_registration=True,
                patched_worker_two_instructions_observed=True,settings_filesystem_events=0,
                menu_dispatch_publication_verified=True,same_layout=True,emulator_only=True,
                do_not_stage=True,hardware_trial_authorized=False,firmware_image=False,repair_claimed=False,
                limits=['Loader file I/O remains; only module settings preparation/worker are suppressed',
                        'UI/menu callbacks remain active and could still cause a freeze',
                        'Kernel/filesystem/render boundaries supplied; no hardware acceptance proof',
                        'Normal controls alone do not prove module loaded; visible Display settings entry is needed'],
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    output.mkdir(parents=True)
    (output/'Z7APP.BIN').write_bytes(packet)
    (output/'diagnostic.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({k:report[k] for k in ('kind','module_sha256','native_load_status','settings_filesystem_events','do_not_stage')}))


if __name__=='__main__':main()
