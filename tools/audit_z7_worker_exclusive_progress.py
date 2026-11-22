"""Inject failed store-exclusive results at the worker guard (MIT).

Exact installed host plus instruction-only worker module. Injection supplies a
STREX failure result and skips its store; it does not model a physical MMU,
exclusive monitor, scheduler or the camera freeze. No deployable image emitted.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
import unicorn.arm_const as arm
from audit_z7_module_host import HostFixture
from audit_splash_image import STACK,STOP,ARGUMENTS,SAVED
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output


def guard(code,base,symbols):
    entry=symbols['z7_module_worker_tick']&~1
    instructions=list(Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(code[entry-base:entry-base+256],entry))
    load=next(i for i in instructions if i.mnemonic=='ldrex')
    store=next(i for i in instructions if i.mnemonic=='strex')
    clear=next(i for i in instructions if i.address>load.address and i.mnemonic=='clrex')
    retries=[i for i in instructions if i.mnemonic=='bne' and i.op_str==hex(load.address).replace('0x','#0x')]
    status=store.op_str.split(',')[0].strip()
    return dict(entry=entry,load=load.address,store=store.address,store_bytes=store.size,
                status_register=getattr(arm,'UC_ARM_REG_'+status.upper()),
                retry_branch=retries[0].address if retries else None,clear=clear.address)


def exercise(raw,host,packet,module,analysis,patch=None,case='healthy'):
    class Fixture(HostFixture):
        active=False
        remaining=0
        exclusive_store_attempts=0
        injected=0
        def hook(self,u,pc,size,context):
            if self.active and pc==analysis['store']:
                self.exclusive_store_attempts+=1
                if self.remaining is None or self.remaining>0:
                    if self.remaining is not None:self.remaining-=1
                    self.injected+=1
                    u.reg_write(analysis['status_register'],1)
                    u.reg_write(arm.UC_ARM_REG_PC,(pc+size)|1)
                    return
            super().hook(u,pc,size,context)
    f=Fixture(raw,host,packet)
    assert f.call(host['symbols']['z7_module_load_once'],STATE)==8
    f.setword(40,8);body=f.words()[12]
    if patch:
        address,data=patch;f.u.mem_write(address,data)
    f.active=True
    f.remaining=None if case=='permanent-failure' else 2 if case=='transient-failure' else 0
    if case=='busy':f.setword(204,1)
    if case=='no-worker':f.setword(200,0)
    if case=='recursive':
        f.u.mem_write(body+module['symbols']['z7_worker_dispatch'],struct.pack('<I',analysis['entry']|1))
        f.u.mem_write(body+module['symbols']['z7_worker_recurse'],struct.pack('<I',1))
    runs=[]
    for _ in range(3 if case=='transient-failure' else 1):
        for reg in ARGUMENTS:f.u.reg_write(reg,0)
        for i,reg in enumerate(SAVED):f.u.reg_write(reg,0x51510000+i)
        f.u.reg_write(arm.UC_ARM_REG_SP,STACK);f.u.reg_write(arm.UC_ARM_REG_LR,STOP|1)
        f.u.emu_start(analysis['entry']|1,STOP,timeout=1000000,count=4096)
        returned=f.u.reg_read(arm.UC_ARM_REG_PC)==STOP
        if returned:
            assert f.u.reg_read(arm.UC_ARM_REG_SP)==STACK
            assert all(f.u.reg_read(reg)==0x51510000+i for i,reg in enumerate(SAVED))
        else:
            assert analysis['load']<=f.u.reg_read(arm.UC_ARM_REG_PC)<=analysis['store']+8
        calls=int.from_bytes(f.u.mem_read(body+module['symbols']['z7_worker_calls'],4),'little')
        runs.append(dict(returned=returned,pc=hex(f.u.reg_read(arm.UC_ARM_REG_PC)),callback_calls=calls,
                         store_attempts=f.exclusive_store_attempts,injected_failures=f.injected,worker_running=f.words()[51]))
        if not returned:break
    return runs


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('host','module','output'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--compiled-host',type=Path)
    p.add_argument('--compiled-symbols',type=Path)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text());m=json.loads((a.module/'module.json').read_text())
    raw=(a.host/'module-host.emulator.main.bin').read_bytes();packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256']
    assert hashlib.sha256(packet).hexdigest()==m['module_sha256']
    base=int(h['host_address'],16);original=guard(raw,0x10020000,h['symbols'])
    assert original['retry_branch'] is not None
    branch=original['retry_branch'];delta=(original['clear']-(branch+4))//2
    assert -128<=delta<=127
    branch_bytes=struct.pack('<H',0xd100|(delta&255))
    modes=[('installed',original,None),('in-memory-single-attempt',original,(branch,branch_bytes))]
    if bool(a.compiled_host)!=bool(a.compiled_symbols):raise ValueError('Provide both compiled host inputs')
    if a.compiled_host:
        compiled=a.compiled_host.read_bytes();meta=json.loads(a.compiled_symbols.read_text())
        assert meta['base']==base and meta['sha256']==hashlib.sha256(compiled).hexdigest()
        analysis=guard(compiled,base,meta['symbols']);assert analysis['retry_branch'] is None
        modes.append(('compiled-weak-cas',analysis,(base,compiled)))
    results={}
    for name,analysis,patch in modes:
        outcomes={}
        for case in ('healthy','busy','no-worker','recursive','transient-failure','permanent-failure'):
            runs=exercise(raw,h,packet,m,analysis,patch,case)
            if case=='permanent-failure' and name=='installed':
                assert not runs[-1]['returned'] and runs[-1]['callback_calls']==0 and runs[-1]['store_attempts']>10
            else:
                assert all(r['returned'] for r in runs)
                if case in ('healthy','recursive'):assert runs[-1]['callback_calls']==1
                if case in ('busy','no-worker','permanent-failure'):assert runs[-1]['callback_calls']==0
                if case in ('busy','no-worker'):assert runs[-1]['store_attempts']==0
                if case=='permanent-failure':assert runs[-1]['store_attempts']==1
                if case=='transient-failure':assert runs[-1]['callback_calls']==(3 if name=='installed' else 1)
            outcomes[case]=runs
        results[name]=outcomes
        print(name,'permanent failure:',json.dumps(outcomes['permanent-failure'][-1]),flush=True)
    report=dict(passed=True,host_main_sha256=h['main_payload_sha256'],probe_module_sha256=m['module_sha256'],
                installed_guard={k:v for k,v in original.items() if k!='status_register'},results=results,
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                simulation='STREX failure status supplied; failed store skipped; instruction cap4096',
                hardware_cause_established=False,physical_memory_attributes_verified=False,
                card_written=False,firmware_image_generated=False,
                limits=['No evidence yet that physical STREX fails at this address',
                        'A simulated busy loop is not a reproduction of whole-camera input freeze',
                        'Compiled blob tested after fixture load, not complete rebuilt firmware boot'])
    if a.compiled_host:
        report['compiled_host_blob_sha256']=meta['sha256']
        report['compiled_guard']={k:v for k,v in analysis.items() if k!='status_register'}
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
