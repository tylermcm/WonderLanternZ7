"""Interrupt the actual GUI revision publisher and run its reader (MIT)."""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from unicorn import UC_HOOK_CODE,UC_HOOK_MEM_WRITE
import unicorn.arm_const as arm
from audit_z7_display_persistence import PersistenceFixture
from audit_splash_image import STACK,STOP,ARGUMENTS,SAVED
from build_z7_module import ROOT
from build_z7_module_host import STATE
from prepare_flash_review import require_private_output


def enter(f,address,stack):
    for reg in ARGUMENTS:f.u.reg_write(reg,0)
    guards={reg:0x52520000+i for i,reg in enumerate(SAVED)}
    for reg,value in guards.items():f.u.reg_write(reg,value)
    f.u.reg_write(arm.UC_ARM_REG_SP,stack);f.u.reg_write(arm.UC_ARM_REG_LR,STOP|1)
    f.u.emu_start(address|1,STOP,timeout=3000000,count=1000000)
    return guards


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('host','module','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text());raw=(a.host/'module-host.emulator.main.bin').read_bytes()
    m=json.loads((a.module/'module.json').read_text());packet=(a.module/'Z7APP.BIN').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==h['main_payload_sha256']
    assert hashlib.sha256(packet).hexdigest()==m['module_sha256']
    f=PersistenceFixture(raw,h,packet);assert f.call(h['symbols']['z7_module_load_once'],STATE)==8
    f.base=f.words()[12];f.setword(40,8);symbols=m['symbols']
    revision=f.base+symbols['z7_settings_revision'];model=f.base+symbols['z7_menu_settings']
    def word(address):return int.from_bytes(f.u.mem_read(address,4),'little')
    before_model=bytes(f.u.mem_read(model,64));before_events=list(f.file_events)
    state=dict(phase='writer',pause_next=False,paused=False);events=[]
    def write(u,access,address,size,value,context):
        if address==revision or model<=address<model+64:
            events.append(dict(phase=state['phase'],address=address,bytes=size,value=value))
        if state['phase']=='writer' and address==revision and value&1:
            state['pause_next']=True
    def code(u,pc,size,context):
        if state['phase']=='writer' and state['pause_next']:
            state['pause_next']=False;state['paused']=True;u.emu_stop()
    mw=f.u.hook_add(UC_HOOK_MEM_WRITE,write,begin=f.base+m['image_bytes'],end=f.base+m['image_bytes']+m['bss_bytes']-1)
    ch=f.u.hook_add(UC_HOOK_CODE,code)
    f.u.mem_write(0xa1833548+22,struct.pack('<2H',0,0))
    guards=enter(f,f.base+symbols['sm_activate'],STACK)
    assert state['paused'] and f.u.reg_read(arm.UC_ARM_REG_PC)!=STOP
    assert word(revision)==1 and bytes(f.u.mem_read(model,64))==before_model
    writer=f.u.context_save();writer_pc=f.u.reg_read(arm.UC_ARM_REG_PC)
    state['phase']='reader'
    for _ in range(4):
        worker_guards=enter(f,h['symbols']['z7_module_worker_tick'],STACK-0x10000)
        assert f.u.reg_read(arm.UC_ARM_REG_PC)==STOP and f.u.reg_read(arm.UC_ARM_REG_SP)==STACK-0x10000
        assert all(f.u.reg_read(reg)==value for reg,value in worker_guards.items())
        assert f.words()[51]==0 and word(revision)==1 and f.file_events==before_events
    assert not [e for e in events if e['phase']=='reader']
    f.u.context_restore(writer);state['phase']='writer-resume'
    f.u.emu_start(writer_pc|1,STOP,timeout=3000000,count=1000000)
    assert f.u.reg_read(arm.UC_ARM_REG_PC)==STOP and f.u.reg_read(arm.UC_ARM_REG_SP)==STACK
    assert all(f.u.reg_read(reg)==value for reg,value in guards.items())
    assert word(revision)==2 and word(model)==1 and f.file_events==before_events
    revisions=[e['value'] for e in events if e['address']==revision]
    assert revisions==[1,2] and events[0]['address']==events[-1]['address']==revision
    state['phase']='saving'
    for _ in range(4):f.call(h['symbols']['z7_module_worker_tick'])
    assert word(f.base+symbols['z7_persistence_saved_revision'])==2
    assert word(f.base+symbols['z7_persistence_saves'])==1
    f.u.hook_del(mw);f.u.hook_del(ch)
    report=dict(passed=True,module_sha256=m['module_sha256'],host_main_sha256=h['main_payload_sha256'],
                actual_writer_paused_after_odd_store=True,reader_calls_while_writer_paused=4,
                readers_returned_without_io=True,reader_stack_separate=True,writer_resumed_with_abi_preserved=True,
                revision_store_sequence=revisions,payload_stores_between_revision_stores=True,completed_revision_saved=True,
                card_written=False,hardware_tested=False,
                limits=['Explicit emulator interleaving is not a physical memory-order/scheduler proof',
                        'Single GUI writer or loader before publication remains a requirement',
                        'Native filesystem services and storage durability supplied/unverified'])
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report))


if __name__=='__main__':main()
