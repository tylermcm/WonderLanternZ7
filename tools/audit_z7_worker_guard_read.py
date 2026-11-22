"""Audit manual ordinary-read guard control and visible result labels (MIT)."""
import argparse
import hashlib
import json
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
from unicorn import UC_HOOK_MEM_WRITE,UC_HOOK_MEM_READ
import unicorn.arm_const as arm
from compare_z7_working_restore import Capture,code_for,invoke
from audit_z7_battery_percent import audit as battery
from build_z7_module import ROOT
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--module',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    d=ROOT/'.private/builds/20261121-lcd-core-host-01'
    host=json.loads((d/'module-host.emulator.json').read_text());raw=(d/'module-host.emulator.main.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==host['main_payload_sha256']=='7d7356e7775db90483ed9fe5598f401afb7fb8498a7b42bd71900db849d7f057'
    packet=(a.module/'Z7APP.BIN').read_bytes();m=json.loads((a.module/'module.json').read_text())
    assert hashlib.sha256(packet).hexdigest()==m['module_sha256'] and m['kind']=='original-Z7-worker-guard-read'
    code=code_for(packet,m,'guard_read_once')
    assert sum(i.mnemonic=='ldr' for i in code)==1
    for name in ('guard_read_once','set_grid','center'):
        assert not any(i.mnemonic.startswith(('ldrex','strex','clrex')) for i in code_for(packet,m,name))
    assert not any(i.mnemonic in ('bl','blx') for i in code)
    results={}
    for case in ('healthy','guard-busy','worker-registered','wrong-host-signature'):
        f=Capture(raw,host,packet,m,b'')
        if case=='wrong-host-signature':f.u.mem_write(0x11fa5852,b'\x00')
        assert f.call(host['symbols']['z7_module_load_once'],STATE)==8
        f.base=f.words()[12];f.setword(40,8)
        reads=[]
        def read(u,access,address,size,value,context):reads.append((address,size))
        readtoken=f.u.hook_add(UC_HOOK_MEM_READ,read,begin=STATE+204,end=STATE+207)
        def word(name):return int.from_bytes(f.u.mem_read(f.base+m['symbols'][name],4),'little')
        def menu():
            f.menu_active=True;f.grid_labels.clear();f.marks.clear()
            f.u.mem_write(0xa1836f8c+36,(0xa2901000).to_bytes(4,'little'))
            f.call(f.base+m['symbols']['grid_enter'],0xa1836f8c);f.menu_active=False
            assert len(f.grid_labels)==6
            return f.grid_labels[3][1]
        assert f.words()[49:52]==(0,0,0) and word('guard_probe_attempts')==0
        f.call(host['symbols']['z7_display_before_paint']);f.call(host['symbols']['z7_display_after_paint'])
        assert f.labels==[('63%',299)]
        for _ in range(8):assert invoke(f,host['symbols']['z7_module_worker_tick'])
        assert word('guard_probe_attempts')==0 and reads==[]
        assert menu()==('Center [RD host]' if case=='wrong-host-signature' else 'Center [RD run]')
        for choice in ('fourths','thirds','golden','dense'):assert invoke(f,f.base+m['symbols'][choice])
        assert word('guard_probe_attempts')==0
        if case=='guard-busy':f.setword(204,1)
        if case=='worker-registered':f.setword(200,1)
        before=bytes(f.u.mem_read(STATE+196,12));writes=[]
        def written(u,access,address,size,value,context):writes.append((address,size,value))
        token=f.u.hook_add(UC_HOOK_MEM_WRITE,written,begin=STATE+196,end=STATE+207)
        assert invoke(f,f.base+m['symbols']['center'],limit=4096)
        f.u.hook_del(token)
        expected={'healthy':'Center [RD OK]',
                  'guard-busy':'Center [RD busy]','worker-registered':'Center [RD busy]',
                  'wrong-host-signature':'Center [RD host]'}[case]
        assert menu()==expected and bytes(f.u.mem_read(STATE+196,12))==before
        attempts=word('guard_probe_attempts');assert attempts==int(case in ('healthy','guard-busy'))
        assert f.exclusive_attempts==0 and len(reads)==attempts
        assert writes==[]
        for _ in range(3):assert invoke(f,f.base+m['symbols']['center'])
        assert word('guard_probe_attempts')==attempts and menu()==expected and len(reads)==attempts
        f.u.hook_del(readtoken)
        assert not [e for e in f.file_events if e[0] not in ('clean','invalidate')]
        results[case]=dict(label=expected,probe_attempts=attempts,injected_store_failures=f.exclusive_attempts,
                           host_word_contents_preserved=True,guard_writes=writes,ordinary_guard_reads=len(reads),no_worker_registered_by_module=True)
        print(case,expected,'attempts',attempts,flush=True)
    policy=battery(raw,host,packet,m)
    r=dict(passed=True,module_sha256=m['module_sha256'],file_bytes=len(packet),host_main_sha256=host['main_payload_sha256'],
           cases=results,battery_checks=len(policy['checks']),probe_exclusive_instruction_count=0,
           no_retry_branch=True,card_written=False,hardware_tested=False,
           limits=['Native UI, telemetry, memory and filesystem services supplied',
                   'No exclusive access is attempted; physical attributes/exceptions unobserved',
                   'Plain read does not establish exclusive support or worker-task behavior',
                   'No fault recovery handler; unrelated address/menu faults could still stall the camera'])
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(r,indent=2)+'\n')
    print('battery checks',len(policy['checks']))


if __name__=='__main__':main()
