"""Build/check a private single-task worker guard without exclusives (MIT).

Only a host code blob is saved. Full firmware exists solely as an in-memory
fixture with updated C symbols; old out-of-blob display bridges are NOT rebuilt.
This is not an installable host, complete integration test or flash assessment.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
from unicorn import UC_HOOK_MEM_WRITE
from audit_z7_worker import audit as worker_audit,WorkerFixture
from build_z7_module_host import ROOT,STATE,compile_host
from prepare_flash_review import require_private_output


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output);assert not out.exists()
    source=ROOT/'z7-native-modules/host/z7_380.c';text=source.read_text(encoding='utf-8')
    uses=[]
    for folder in ('host','sdk','plugins','examples'):
        for file in (ROOT/'z7-native-modules'/folder).rglob('*'):
            if file.suffix in ('.c','.h'):
                for line,value in enumerate(file.read_text(encoding='utf-8').splitlines(),1):
                    if re.search(r'\bz7_module_worker_tick\b',value):uses.append(dict(file=file.relative_to(ROOT).as_posix(),line=line,text=value.strip()))
    assert len(uses)==2 and all(x['file']=='z7-native-modules/host/z7_380.c' for x in uses)
    assert uses[0]['text']=='static __attribute__((noinline)) void z7_module_worker_tick(void)'
    assert uses[1]['text']=='z7_module_worker_tick();'
    assert text.index(uses[1]['text'])>text.index('void z7_module_worker(struct z7_host_state *s)')
    olddir=ROOT/'.private/builds/20261121-lcd-core-host-01'
    old=json.loads((olddir/'module-host.emulator.json').read_text());raw=(olddir/'module-host.emulator.main.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==old['main_payload_sha256']=='7d7356e7775db90483ed9fe5598f401afb7fb8498a7b42bd71900db849d7f057'
    base=int(old['host_address'],16);details={};code,symbols=compile_host(base,symbol_details=details)
    again,others=compile_host(base);assert code==again and symbols==others
    tick=details['z7_module_worker_tick'];assert tick['binding']==0 and tick['type']==2 and tick['bytes']>0
    start=tick['address']&~1
    ins=list(Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(code[start-base:start-base+tick['bytes']],start))
    assert sum(i.size for i in ins)==tick['bytes']
    assert not any(i.mnemonic.startswith(('ldrex','strex','clrex')) for i in ins)
    assert len(code)<=old['host_bytes']
    image=bytearray(raw);offset=base-0x10020000;image[offset:offset+old['host_bytes']]=code+bytes(old['host_bytes']-len(code));image=bytes(image)
    host=dict(old,symbols=symbols,host_bytes=len(code),main_payload_sha256=hashlib.sha256(image).hexdigest())
    modules=ROOT/'.private/builds/20261120-worker-diagnostics-01/probes'
    suite=worker_audit(image,host,(ROOT/'.private/builds/20261021-laptop-01/stock-main.bin').read_bytes(),modules,ROOT/'.private/builds/20261120-display-host-08')
    packet=(modules/'worker-success.BIN').read_bytes();module=json.loads((modules/'worker-success.json').read_text())
    runs={}
    for case in ('normal','recursive','already-running','no-worker'):
        f=WorkerFixture(image,host,packet);f.module_symbols=module['symbols']
        assert f.call(symbols['z7_module_load_once'],STATE)==8;f.setword(40,8)
        if case=='recursive':f.configure('z7_worker_dispatch',symbols['z7_module_worker_tick']);f.configure('z7_worker_recurse',1)
        if case=='already-running':f.setword(204,1)
        if case=='no-worker':f.setword(200,0)
        writes=[]
        def write(u,access,address,size,value,context):writes.append([address,size,value])
        token=f.u.hook_add(UC_HOOK_MEM_WRITE,write,begin=STATE+204,end=STATE+207)
        f.call(symbols['z7_module_worker_tick']);f.u.hook_del(token)
        active=case in ('normal','recursive')
        assert f.calls()==int(active)
        assert writes==([[STATE+204,4,1],[STATE+204,4,0]] if active else [])
        assert f.words()[51]==int(case=='already-running')
        runs[case]=dict(callback_calls=f.calls(),guard_writes=writes,final_guard=f.words()[51])
    report=dict(passed=True,host_blob_sha256=hashlib.sha256(code).hexdigest(),host_blob_bytes=len(code),
                installed_host_blob_bytes=old['host_bytes'],reproducible=True,guard_symbol=tick,
                compiled_guard=[dict(address=hex(i.address),instruction=i.mnemonic+' '+i.op_str) for i in ins],
                exclusive_instructions_in_worker_guard=0,production_symbol_references=uses,
                worker_suite_checks=len(suite['checks']),worker_suite=suite,guard_runs=runs,
                source_inputs_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in
                    ('z7-native-modules/host/z7_380.c','z7-native-modules/host/z7_380.h','z7-native-modules/sdk/worker.h','tools/build_z7_module_host.py','tools/audit_z7_worker_task_guard.py')},
                card_written=False,firmware_image_written=False,hardware_fix_confirmed=False,
                limits=['Task-owned recursion flag is not mutual exclusion for concurrent tasks',
                        'Private C linkage and one audited production caller; arbitrary raw-address calls are outside contract',
                        'Native kernel/heap/filesystem/delay boundaries supplied',
                        'Compiled blob overlaid in memory; old native display bridges not rebuilt or validated',
                        'No installation/recovery clearance, camera test or full firmware build'])
    out.mkdir(parents=True)
    (out/'host-code.bin').write_bytes(code)
    (out/'symbols.json').write_text(json.dumps(dict(base=base,symbols=symbols,sha256=report['host_blob_sha256'],details=details),indent=2)+'\n',encoding='utf-8',newline='\n')
    (out/'audit.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,blob_bytes=len(code),sha256=report['host_blob_sha256'],worker_checks=report['worker_suite_checks'],guard_cases=len(runs))))


if __name__=='__main__':main()
