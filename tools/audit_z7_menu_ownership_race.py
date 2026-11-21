"""Inject a competing owner after prepare, before native menu publication.

SPDX-License-Identifier: MIT. Synthetic task-interleaving regression using
compiled ARM code and supplied kernel/filesystem/UI boundaries. Not a physical
freeze reproduction or proof that native startup actually changes these words.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from audit_z7_display_persistence import PersistenceFixture
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output

PAGE, SLOT = 0xa1833548, 0xa182ed34
CONFLICTS = {'dispatcher': (SLOT, 0x1040525f), 'page': (PAGE, 0x12340002)}


def exercise(raw, host, packet, module, conflict):
    if hashlib.sha256(raw).hexdigest() != host['main_payload_sha256']:
        raise ValueError('Host fingerprint mismatch')
    if hashlib.sha256(packet).hexdigest() != module['module_sha256']:
        raise ValueError('Module fingerprint mismatch')

    class RaceFixture(PersistenceFixture):
        injected = False
        snapshot_at_injection = None

        def hook(self,u,pc,size,context):
            body=self.words()[19] if pc == host['symbols']['z7_module_call'] & ~1 else 0
            if body:self.entry_body=body
            if (conflict and not self.injected and
                    pc == getattr(self,'entry_body',0)+(module['symbols']['persistence_prepare'] & ~1)):
                address,value=CONFLICTS[conflict]
                u.mem_write(address,struct.pack('<I',value))
                self.injected=True
                self.snapshot_at_injection=(bytes(u.mem_read(PAGE,44)),bytes(u.mem_read(SLOT,4)))
            super().hook(u,pc,size,context)

    f=RaceFixture(raw,host,packet)
    status=f.call(host['symbols']['z7_module_load_once'],STATE)
    if conflict:
        assert f.injected
        untouched=f.snapshot_at_injection==(bytes(f.u.mem_read(PAGE,44)),bytes(f.u.mem_read(SLOT,4)))
        address,value=CONFLICTS[conflict]
        conflict_preserved=int.from_bytes(f.u.mem_read(address,4),'little')==value
    else:untouched=conflict_preserved=None
    return dict(status=status,injected=bool(f.injected),conflict_preserved=conflict_preserved,
                complete_native_menu_snapshot_preserved=untouched,
                display_ready=f.words()[23],resident_allocations=len(f.live),
                native_page_header=hex(int.from_bytes(f.u.mem_read(PAGE,4),'little')),
                native_dispatcher=hex(int.from_bytes(f.u.mem_read(SLOT,4),'little')))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--host',type=Path,required=True)
    p.add_argument('--module',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--expect',choices=('overwrites','rejects'),required=True)
    a=p.parse_args();out=require_private_output(a.output)
    host=json.loads((a.host/'module-host.emulator.json').read_text(encoding='utf-8'))
    module=json.loads((a.module/'module.json').read_text(encoding='utf-8'))
    raw=(a.host/'module-host.emulator.main.bin').read_bytes();packet=(a.module/'Z7APP.BIN').read_bytes()
    results={}
    for conflict in (None,'dispatcher','page'):
        result=exercise(raw,host,packet,module,conflict)
        if conflict:
            if a.expect=='rejects':
                assert result['status']==7 and result['complete_native_menu_snapshot_preserved']
                assert not result['display_ready'] and not result['resident_allocations']
            else:
                assert result['status']==8 and not result['conflict_preserved']
        else:assert result['status']==8 and result['display_ready']==1
        results[conflict or 'normal']=result
        print(conflict or 'normal',json.dumps(result),flush=True)
    report=dict(results=results,expected=a.expect,module_sha256=module['module_sha256'],
                host_main_sha256=host['main_payload_sha256'],synthetic_interleaving=True,
                hardware_cause_established=False,card_written=False,
                limits=['Conflict is an explicit synthetic owner mutation after prepare',
                        'No actual kernel scheduling, task locks or physical startup modeled',
                        'No claim that native firmware performs the injected change',
                        'No protection against changes inside the final publication window is tested'])
    out.mkdir(parents=True,exist_ok=False)
    (out/'audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
