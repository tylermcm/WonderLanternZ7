"""Compare frozen working/failing SD modules and in-memory ablations (MIT).

No card access, deployable diagnostics or firmware images are produced. Native
filesystem/kernel/GUI inputs and exclusive-store failure results are supplied.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from capstone import Cs,CS_ARCH_ARM,CS_MODE_THUMB
import unicorn.arm_const as arm
from audit_z7_grid_restore_readonly import RestoreFixture,PATH
from audit_z7_worker_exclusive_progress import guard
from audit_splash_image import STACK,STOP,ARGUMENTS,SAVED
from build_z7_module import HEADER,seal
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output

WORKING='53334536d00ed18ea9d80d36dd736d6341fd1943da674f6e0fd513112f226195'
FAILED='0714fe8491b4e802406ed0867f0c5ecacc3ceb4c573feecceb742364b2c4bf95'


def code_for(packet,meta,name):
    start=meta['symbols'][name]&~1
    end=min([v&~1 for v in meta['symbols'].values() if (v&~1)>start]+[meta['image_bytes']])
    return list(Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(packet[HEADER+start:HEADER+end],start))


class Capture(RestoreFixture):
    def __init__(self,raw,host,packet,meta,seed):
        super().__init__(raw,host,packet,files={PATH:seed})
        self.meta=meta;self.host=host;self.body=0;self.targets={};self.registrations=[]
        self.fail_site=None;self.exclusive_attempts=0;self.worker_entries=0;self.callback=0;self.setter_calls=0
    def hook(self,u,pc,size,context):
        if pc==self.host['symbols']['z7_module_call']&~1:self.body=self.words()[19]
        if self.body and pc==self.body+self.meta['entry_offset']:
            api=u.reg_read(arm.UC_ARM_REG_R0)
            self.targets={int.from_bytes(u.mem_read(api+off,4),'little')&~1:name
                          for name,off in (('display',12),('grid_menu',16),('worker',40))}
        if pc in self.targets:
            name=self.targets[pc];offset=(u.reg_read(arm.UC_ARM_REG_LR)&~1)-2-self.body
            self.registrations.append(dict(name=name,module_call_offset=offset))
            if name=='worker':self.callback=u.reg_read(arm.UC_ARM_REG_R0)&~1
        if self.callback and pc==self.callback:self.worker_entries+=1
        if pc==0x104065b0:self.setter_calls+=1
        if self.fail_site and pc==self.fail_site['pc']:
            self.exclusive_attempts+=1;u.reg_write(self.fail_site['register'],1)
            u.reg_write(arm.UC_ARM_REG_PC,(pc+size)|1);return
        super().hook(u,pc,size,context)


def load(raw,host,packet,meta,seed):
    f=Capture(raw,host,packet,meta,seed)
    assert f.call(host['symbols']['z7_module_load_once'],STATE)==8
    f.base=f.words()[12];f.setword(40,8)
    return f


def invoke(f,address,limit=100000):
    for reg in ARGUMENTS:f.u.reg_write(reg,0)
    for i,reg in enumerate(SAVED):f.u.reg_write(reg,0x51510000+i)
    f.u.reg_write(arm.UC_ARM_REG_SP,STACK);f.u.reg_write(arm.UC_ARM_REG_LR,STOP|1)
    f.u.emu_start(address|1,STOP,timeout=3000000,count=limit)
    returned=f.u.reg_read(arm.UC_ARM_REG_PC)==STOP
    if returned:
        assert f.u.reg_read(arm.UC_ARM_REG_SP)==STACK
        assert all(f.u.reg_read(reg)==0x51510000+i for i,reg in enumerate(SAVED))
    return returned


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('host','working','failed','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text());raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256']=='7d7356e7775db90483ed9fe5598f401afb7fb8498a7b42bd71900db849d7f057'
    wm=json.loads((a.working/'module.json').read_text());fm=json.loads((a.failed/'module.json').read_text())
    wp=(a.working/'Z7APP.BIN').read_bytes();fp=(a.failed/'Z7APP.BIN').read_bytes();seed=(a.failed/'Z7GRID.DAT').read_bytes()
    assert hashlib.sha256(wp).hexdigest()==WORKING and hashlib.sha256(fp).hexdigest()==FAILED
    g=guard(raw,0x10020000,h['symbols'])
    original=load(raw,h,fp,fm,seed)
    call=next(x['module_call_offset'] for x in original.registrations if x['name']=='worker')
    ins=list(Cs(CS_ARCH_ARM,CS_MODE_THUMB).disasm(fp[HEADER+call:HEADER+call+2],call))
    assert len(ins)==1 and ins[0].mnemonic=='blx' and ins[0].size==2
    worker=fm['symbols']['restore_worker']&~1
    def changed(offset,data):
        assert offset>=0 and offset+len(data)<=fm['image_bytes']
        assert not any(offset<r+4 and r<offset+len(data) for r in fm['relocations'])
        b=bytearray(fp);b[HEADER+offset:HEADER+offset+len(data)]=data;b=seal(b)
        allowed=set(range(32,36))|set(range(HEADER+offset,HEADER+offset+len(data)))
        assert len(b)==len(fp) and all(x==y or i in allowed for i,(x,y) in enumerate(zip(fp,b)))
        return b
    # Ack registration without calling it; or retain it and return at callback entry.
    no_registration=changed(call,bytes.fromhex('0120'))
    no_body=changed(worker,bytes.fromhex('00207047'))
    results={}
    variants=[('working',wp,wm),('failed',fp,fm),('failed-without-registration',no_registration,fm),('failed-with-empty-worker',no_body,fm)]
    for name,packet,meta in variants:
        outcomes={}
        for fault in (False,True):
            f=load(raw,h,packet,meta,seed)
            initial_settings=[e for e in f.file_events if e[0] not in ('clean','invalidate')];assert not initial_settings
            f.call(h['symbols']['z7_display_before_paint']);f.call(h['symbols']['z7_display_after_paint'])
            assert f.labels==[('63%',299)]
            if fault:f.fail_site=dict(pc=g['store'],register=g['status_register'])
            returned=invoke(f,h['symbols']['z7_module_worker_tick'])
            settings=[e[0] for e in f.file_events if e[0] not in ('clean','invalidate')]
            registered=bool(f.words()[50])
            if fault and registered:
                assert not returned and f.worker_entries==0 and not settings and f.exclusive_attempts>10
            else:
                assert returned
                if name=='failed':assert settings==['open','read','close'] and f.worker_entries==1
                else:assert not settings
            if name=='failed-without-registration':assert not registered
            if name=='failed-with-empty-worker':assert registered
            outcomes['failed-exclusive-store' if fault else 'normal-exclusive-store']=dict(returned=returned,registered_worker=registered,worker_entries=f.worker_entries,settings_operations=settings,injected_attempts=f.exclusive_attempts,stopped_pc=hex(f.u.reg_read(arm.UC_ARM_REG_PC)),registration_sequence=f.registrations)
        results[name]=outcomes
        print(name,{k:v['returned'] for k,v in outcomes.items()},flush=True)
    # A second exclusive retry was added to each new menu-selection handler.
    selection={}
    for name,packet,meta in (('working',wp,wm),('failed',fp,fm)):
        f=load(raw,h,packet,meta,seed);code=code_for(packet,meta,'center')
        stores=[i for i in code if i.mnemonic=='strex']
        if stores:
            i=stores[0];register=getattr(arm,'UC_ARM_REG_'+i.op_str.split(',')[0].strip().upper())
            f.fail_site=dict(pc=f.base+i.address,register=register)
        returned=invoke(f,f.base+(meta['symbols']['center']&~1),limit=10000)
        assert returned==(name=='working')
        if name=='failed':assert f.setter_calls==0 and f.exclusive_attempts>10
        selection[name]=dict(exclusive_store_offsets=[i.address for i in stores],returned=returned,normal_on_off_setter_calls=f.setter_calls,injected_failures=f.exclusive_attempts)
    common=set(wm['source_inputs_sha256'])&set(fm['source_inputs_sha256'])
    shared={n:wm['source_inputs_sha256'][n]==fm['source_inputs_sha256'][n] for n in sorted(common)}
    report=dict(host_main_sha256=h['main_payload_sha256'],working_sha256=WORKING,failed_sha256=FAILED,
                footprints={name:{**{k:m[k] for k in ('file_bytes','image_bytes','bss_bytes','entry_offset','api_minimum_bytes')},'relocations':len(m['relocations'])} for name,m in (('working',wm),('failed',fm))},
                shared_source_hashes_equal=shared,worker_comparison=results,selection_atomic_comparison=selection,
                in_memory_changes=dict(no_registration=dict(image_offset=call,code_bytes_changed=2),empty_worker=dict(image_offset=worker,code_bytes_changed=4),header_changes='CRC only',file_size_bss_and_relocations_unchanged=True),
                source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                card_written=False,hardware_diagnostics_generated=False,firmware_image_generated=False,hardware_cause_established=False,
                limits=['Exclusive failure is injected; no target PC or physical monitor capture',
                        'Both same-size variants exist in memory only and were not tested on camera',
                        'UI/kernel/filesystem/telemetry/On-Off setter boundaries supplied',
                        'Menu-selection loop cannot explain a boot freeze unless that handler ran'])
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
