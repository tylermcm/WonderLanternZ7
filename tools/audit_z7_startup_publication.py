"""Trace exact module startup stores and stack use; not a hardware boot model.

SPDX-License-Identifier: MIT. Uses existing supplied kernel/filesystem/UI fixture
boundaries. Does not create a module, write a card or establish freeze causation.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path

from unicorn import UC_HOOK_MEM_WRITE, UC_HOOK_BLOCK, UcError
from unicorn.arm_const import UC_ARM_REG_PC, UC_ARM_REG_SP
from audit_z7_display_persistence import PersistenceFixture
from audit_splash_image import STACK
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output

MENU, DISPATCH = 0xa1833548, 0xa182ed34


def trace(raw, host, packet, module):
    if hashlib.sha256(raw).hexdigest() != host['main_payload_sha256']:
        raise ValueError('Host fingerprint mismatch')
    if hashlib.sha256(packet).hexdigest() != module['module_sha256']:
        raise ValueError('Module fingerprint mismatch')
    descriptor = struct.unpack_from('<4I',raw,0x11f9a92c-0x10020000)
    if descriptor != (1,28,8192,0):
        raise ValueError('Unexpected native task descriptor')
    writes, calls = [], []
    minimum_sp = STACK
    entered = False
    module_minimum_sp = STACK
    body = 0
    symbols = module.get('symbols', {})
    watched = {value & ~1: name for name, value in symbols.items()
               if name in ('z7_main', 'persistence_prepare', 'persistence_worker')}

    def code(u, pc):
        nonlocal entered, body
        if pc == host['symbols']['z7_module_call'] & ~1:
            body = f.words()[19]
        if body and pc == body + module['entry_offset']:
            entered = True
        if body and entered:
            if pc - body in watched:
                calls.append(watched[pc - body])

    def block(u,pc,size,context):
        nonlocal minimum_sp,module_minimum_sp
        sp=u.reg_read(UC_ARM_REG_SP)
        minimum_sp=min(minimum_sp,sp)
        if body and entered:module_minimum_sp=min(module_minimum_sp,sp)

    def write(u, access, address, size, value, context):
        if MENU <= address < MENU + 44 or address == DISPATCH or address == STATE + 92:
            writes.append(dict(address=hex(address), bytes=size, value=hex(value),
                               pc=hex(u.reg_read(UC_ARM_REG_PC)),
                               display_ready_before=f.words()[23]))

    class TracedFixture(PersistenceFixture):
        def hook(self,u,address,size,context):
            code(u,address)
            super().hook(u,address,size,context)

    f = TracedFixture(raw,host,packet)
    f.u.hook_add(UC_HOOK_BLOCK,block)
    f.u.hook_add(UC_HOOK_MEM_WRITE, write, begin=MENU, end=MENU+43)
    f.u.hook_add(UC_HOOK_MEM_WRITE, write, begin=DISPATCH, end=DISPATCH+3)
    f.u.hook_add(UC_HOOK_MEM_WRITE, write, begin=STATE+92, end=STATE+95)
    try:
        status = f.call(host['symbols']['z7_module_load_once'], STATE)
    except UcError as exc:
        raise RuntimeError('Trace failed at PC=%08x SP=%08x' %
                           (f.u.reg_read(UC_ARM_REG_PC),f.u.reg_read(UC_ARM_REG_SP))) from exc
    assert status == 8 and entered
    publication = [w for w in writes if int(w['address'], 16) in (MENU, DISPATCH)]
    ready = [i for i, w in enumerate(writes)
             if int(w['address'], 16) == STATE + 92 and w['value'] == '0x1']
    if module.get('display_registration_expected', True):
        assert len(publication) == 2 and len(ready) == 1
        assert all(w['display_ready_before'] == 0 for w in publication)
        assert all(i < ready[0] for i,w in enumerate(writes) if w in publication)
    else:
        assert not publication and not ready
    return dict(native_load_status=status, entry_observed=True,
                traced_stores=writes, module_functions_entered=calls,
                block_sampled_load_call_stack_depth_bytes=STACK-minimum_sp,
                stack_depth_while_module_loading_bytes=STACK-module_minimum_sp,
                settings_file_events=[e for e in f.file_events if e[0] not in ('clean','invalidate')],
                native_menu_published_before_host_ready=bool(publication),
                native_descriptor_stack_bytes=descriptor[2],
                limits=['Single task with supplied kernel/filesystem/UI boundaries',
                        'Stack sampled at basic-block entries; excludes supplied services/task wrapper and is a lower bound',
                        'Native runtime RAM and active application are fixture inputs',
                        'Publication order is observed; preemption or freeze causation is not established'])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--host',type=Path,required=True)
    p.add_argument('--module',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    host=json.loads((a.host/'module-host.emulator.json').read_text(encoding='utf-8'))
    raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    original=json.loads((a.module/'module.json').read_text(encoding='utf-8'))
    from build_z7_noinit_diagnostic import disable_entry
    from build_z7_no_settings_io_diagnostic import suppress_settings_io
    packet=(a.module/'Z7APP.BIN').read_bytes()
    noinit,_=disable_entry(packet,original['module_sha256'])
    nofiles,_,_=suppress_settings_io(packet,original['module_sha256'],original['symbols'])
    result={}
    for name,data in (('full',packet),('noinit',noinit),('no_settings_io',nofiles)):
        meta=dict(original,module_sha256=hashlib.sha256(data).hexdigest(),display_registration_expected=name!='noinit')
        result[name]=dict(module_sha256=meta['module_sha256'],**trace(raw,host,data,meta))
        print(name, result[name]['block_sampled_load_call_stack_depth_bytes'], 'bytes sampled stack; publication before ready:',result[name]['native_menu_published_before_host_ready'],flush=True)
    result.update(host_main_sha256=host['main_payload_sha256'],emulator_only=True,
                  hardware_cause_established=False,card_written=False,firmware_generated=False,
                  audit_source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    out.mkdir(parents=True,exist_ok=False)
    (out/'audit.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')


if __name__=='__main__':main()
