"""Trace registration and resident-loop progress on exact A/B controls (MIT).

No camera access. The task loop starts after the audited module load; native
delay is a supplied boundary, not a scheduler or timing simulation.
"""
import argparse
import hashlib
import json
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
from unicorn import UC_HOOK_MEM_WRITE
import unicorn.arm_const as arm
from compare_z7_working_restore import Capture
from audit_z7_worker_exclusive_progress import guard
from audit_splash_image import STACK,STOP
from build_z7_module_host import STATE,ROOT
from prepare_flash_review import require_private_output


class Trace(Capture):
    def __init__(self,*args):
        self.registration_active=False;self.registration_return=0
        self.registration_pcs=[];self.registration_writes=[];self.registration_returned=False
        self.loop_active=False;self.delays=0
        super().__init__(*args)
        def write(u,access,address,size,value,context):
            if self.registration_active:self.registration_writes.append(dict(address=hex(address),bytes=size,value=hex(value)))
        self.u.hook_add(UC_HOOK_MEM_WRITE,write,begin=STATE,end=STATE+255)
    def hook(self,u,pc,size,context):
        if self.targets.get(pc)=='worker':
            self.registration_active=True;self.registration_return=u.reg_read(arm.UC_ARM_REG_LR)&~1
        if self.registration_active and pc==self.registration_return:
            self.registration_active=False;self.registration_returned=True
            assert u.reg_read(arm.UC_ARM_REG_R0)==1
        if self.registration_active:self.registration_pcs.append(pc)
        if self.loop_active and pc==0x1017081e:
            assert u.reg_read(arm.UC_ARM_REG_R0)==1000
            self.delays+=1
            if self.delays==4:u.emu_stop()
            else:self.ret(0)
            return
        super().hook(u,pc,size,context)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=require_private_output(a.output)
    folder=ROOT/'.private/builds/20261121-lcd-core-host-01'
    host=json.loads((folder/'module-host.emulator.json').read_text());raw=(folder/'module-host.emulator.main.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==host['main_payload_sha256']=='7d7356e7775db90483ed9fe5598f401afb7fb8498a7b42bd71900db849d7f057'
    cs=Cs(CS_ARCH_ARM,CS_MODE_THUMB);g=guard(raw,0x10020000,host['symbols'])
    # Exact installed resident loop: delay(1000), worker_tick(), branch to delay.
    start=0x11fa6032
    loop=list(cs.disasm(raw[start-0x10020000:start-0x10020000+12],start))
    assert [(i.mnemonic,i.op_str) for i in loop]==[('mov.w','r0, #0x3e8'),('blx','r5'),('bl','#0x11fa57d4'),('b','#0x11fa6032')]
    results={}
    for name,fault,bounded in [('A',False,False),('B',False,False),('A',True,False),('B',True,False),('B',True,True)]:
        d=ROOT/'.private/builds/20261122-worker-registration-pair-01'/('disabled' if name=='A' else 'enabled')
        packet=(d/'Z7APP.BIN').read_bytes();meta=json.loads((d/'module.json').read_text())
        assert hashlib.sha256(packet).hexdigest()==meta['module_sha256']
        f=Trace(raw,host,packet,meta,b'');assert f.call(host['symbols']['z7_module_load_once'],STATE)==8
        f.base=f.words()[12];f.setword(40,8)
        regcode=[]
        for pc in f.registration_pcs:
            i=next(cs.disasm(bytes(f.u.mem_read(pc,4)),pc,count=1));regcode.append(dict(pc=hex(pc),instruction=i.mnemonic+' '+i.op_str))
        if name=='B':
            assert f.registration_returned
            assert not any(x['instruction'].startswith(('ldrex','strex','bl ','blx ')) for x in regcode)
            statewrites=[w for w in f.registration_writes if STATE<=int(w['address'],16)<STATE+256]
            assert statewrites==[dict(address=hex(STATE+196),bytes=4,value=hex(f.base+meta['symbols']['worker_pair_noop'])),dict(address=hex(STATE+200),bytes=4,value='0x1')]
        else:assert not f.registration_pcs and not f.registration_writes
        if bounded:
            # Branch on failed STREX to the existing return instead of retry.
            branch=0x11fa585e;exitpc=0x11fa581a
            old=next(cs.disasm(bytes(f.u.mem_read(branch,2)),branch));assert old.mnemonic=='bne' and old.op_str=='#0x11fa5852'
            delta=(exitpc-(branch+4))//2;patch=(0xd100|(delta&255)).to_bytes(2,'little')
            f.u.mem_write(branch,patch)
            assert next(cs.disasm(patch,branch)).op_str==hex(exitpc).replace('0x','#0x')
        if fault:f.fail_site=dict(pc=g['store'],register=g['status_register'])
        f.loop_active=True;f.u.reg_write(arm.UC_ARM_REG_SP,STACK);f.u.reg_write(arm.UC_ARM_REG_LR,STOP|1)
        f.u.reg_write(arm.UC_ARM_REG_R5,0x1017081f)
        f.u.emu_start(start|1,STOP,timeout=3000000,count=4096)
        spins=name=='B' and fault and not bounded
        assert f.delays==(1 if spins else 4)
        assert f.worker_entries==(3 if name=='B' and not fault else 0)
        assert f.words()[51]==0
        assert not [e for e in f.file_events if e[0] not in ('clean','invalidate')]
        key=f'{name}-'+('failed-exclusive' if fault else 'healthy')+('-bounded-in-memory' if bounded else '')
        results[key]=dict(delay_boundary_calls=f.delays,worker_entries=f.worker_entries,injected_store_failures=f.exclusive_attempts,
                          stopped_pc=hex(f.u.reg_read(arm.UC_ARM_REG_PC)),registration_returned=f.registration_returned,
                          registration_state_writes=[w for w in f.registration_writes if STATE<=int(w['address'],16)<STATE+256],
                          registration_trace=regcode)
        print(key,'delays',f.delays,'callbacks',f.worker_entries,'failed stores',f.exclusive_attempts,flush=True)
    report=dict(passed=True,host_main_sha256=host['main_payload_sha256'],results=results,guard_address='0xa97000cc',
                hardware_observation='Owner A pass; B freeze; camera normal with card removed',
                physical_failure_pc_established=False,card_written=False,firmware_image_generated=False,
                limits=['Exact binaries with supplied filesystem, memory and native services',
                        'Starts resident loop after load; does not emulate physical scheduler',
                        'Exclusive-store failures injected, not observed on camera',
                        'Two-byte bounded branch exists only in emulator memory'])
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
