"""Read-only post-GUI restore and fault/preemption audit (MIT).

Real compiled module/file wrappers; kernel/filesystem dispatcher, battery/GUI
inputs, menu rendering and the normal On/Off UI setter are supplied boundaries.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_PC,UC_ARM_REG_SP,UC_ARM_REG_LR
from audit_z7_settings_files import FilesFixture,ERROR
from audit_z7_battery_thirds_checkpoint import CheckpointFixture
from audit_splash_image import MEM,STACK,STOP,ARGUMENTS,SAVED
from build_z7_module_host import STATE
from grid_restore_record import encode
from prepare_flash_review import require_private_output

PATH='A:\\Z7GRID.DAT'
PAGE=0xa1836f8c


class RestoreFixture(FilesFixture,CheckpointFixture):
    file_paths=(PATH,)
    def __init__(self,raw,host,packet,files=None,faults=None):
        super().__init__(raw,host,packet)
        self.files=dict(files or {});self.faults=dict(faults or {})
        self.handles={};self.next_fd=0;self.write_prefix=80
        self.file_events=[];self.file_cache_lines=[];self.cache_operations=[]
        self.files_enabled=self.allow_module_loader=True
        self.menu_active=False;self.grid_labels=[];self.marks=[]
        self.pause_read=False;self.paused=False
    def hook(self,u,pc,size,context):
        if pc==0x1027beae and self.pause_read:
            p=u.reg_read(UC_ARM_REG_R0)
            if bytes(u.mem_read(p+0x9c,1))==b'\x08':
                self.pause_read=False;self.paused=True;u.emu_stop();return
        if pc==0x104065b0:
            assert u.reg_read(UC_ARM_REG_R0)==0x102d and u.reg_read(UC_ARM_REG_R1) in (0,1)
            u.mem_write(0xa24f182c,struct.pack('<I',u.reg_read(UC_ARM_REG_R1)));self.ret(1);return
        if self.menu_active:
            if pc==0x103fbb5c:
                self.grid_labels.append((u.reg_read(UC_ARM_REG_R1),self.cstring(u.reg_read(UC_ARM_REG_R0))))
                self.ret(0);return
            if pc==0x103fcf0e:self.ret(MEM+0x20000+u.reg_read(UC_ARM_REG_R2)*64);return
            if pc in (0x103fb344,0x10402bc2):self.ret(0);return
            if pc==0x10404cd8:
                self.marks.append((u.reg_read(UC_ARM_REG_R1),u.reg_read(UC_ARM_REG_R2)));self.ret(0);return
            if pc==0x10405f00:self.ret(0);return
        super().hook(u,pc,size,context)


def audit(raw,host,packet,module):
    assert hashlib.sha256(raw).hexdigest()==host['main_payload_sha256']
    assert hashlib.sha256(packet).hexdigest()==module['module_sha256']
    assert 'z7_settings_files_write' not in module['symbols']
    checks=[];symbols=module['symbols']
    def check(name,good):
        assert good,name
        checks.append(name)
    def word(f,name):return int.from_bytes(f.u.mem_read(f.base+symbols[name],4),'little')
    def events(f):return [e for e in f.file_events if e[0] not in ('clean','invalidate')]
    def load(files=None,faults=None):
        f=RestoreFixture(raw,host,packet,files,faults)
        status=f.call(host['symbols']['z7_module_load_once'],STATE);f.base=f.words()[12];f.setword(40,status)
        check('load-'+str(len(checks)),status==8 and f.words()[50]==1 and not events(f) and not f.labels and not f.getter_calls)
        return f
    def tick(f):return f.call(host['symbols']['z7_module_worker_tick'])
    def gui(f):
        f.call(host['symbols']['z7_display_before_paint']);f.call(host['symbols']['z7_display_after_paint'])
    def menu(f):
        f.menu_active=True;f.grid_labels.clear();f.marks.clear()
        f.u.mem_write(PAGE+36,struct.pack('<I',MEM+0x10000))
        f.call(f.base+symbols['grid_enter'],PAGE);f.menu_active=False
    def stable(f,label):
        previous=list(f.file_events);files=dict(f.files)
        for _ in range(8):tick(f)
        check(label+'-no-retry-create-or-write',f.file_events==previous and f.files==files and all(e[0] in ('open','read','close') for e in events(f)))
    f=load({PATH:encode(5)})
    for _ in range(3):tick(f)
    check('worker-waits-for-eligible-gui',not events(f) and word(f,'restore_state')==0)
    gui(f);labels=list(f.labels);tick(f)
    check('single-post-gui-read-no-ui-write',word(f,'restore_state')==2 and f.labels==labels and [e[0] for e in events(f)]==['open','read','close'] and not f.handles)
    check('worker-does-not-apply-gui-layout',word(f,'checkpoint_grid_value')==2)
    before=list(f.file_events);menu(f)
    check('menu-applies-seed-and-marks-loaded-row',word(f,'checkpoint_grid_value')==5 and word(f,'restore_state')==3 and (43,'6x6 [SD]') in f.grid_labels and f.file_events==before)
    stable(f,'success')
    # Execute the compiled decoder against independent Python-generated records.
    buffer,output=MEM+0x80000,MEM+0x80100
    for choice in range(1,6):
        f.u.mem_write(buffer,encode(choice));f.u.mem_write(output,struct.pack('<I',99))
        check('compiled-codec-choice-'+str(choice),f.call(f.base+symbols['checkpoint_grid_record_decode'],buffer,80,output)==1 and int.from_bytes(f.u.mem_read(output,4),'little')==choice)
    for offset in (0,4,8,12,16,20,79):
        corrupt=bytearray(encode(5));corrupt[offset]^=1;f.u.mem_write(buffer,bytes(corrupt));f.u.mem_write(output,struct.pack('<I',99))
        check('compiled-codec-rejects-'+str(offset),f.call(f.base+symbols['checkpoint_grid_record_decode'],buffer,80,output)==0 and int.from_bytes(f.u.mem_read(output,4),'little')==99)
    for name,files,faults,state in [('missing',{},None,4),('short',{PATH:encode(5)[:-1]},None,5),('long',{PATH:encode(5)+b'x'},None,5),('corrupt',{PATH:bytes(80)},None,5),('open-error',{PATH:encode(5)},{'open':ERROR},5),('read-error',{PATH:encode(5)},{'read':ERROR},5),('close-error',{PATH:encode(5)},{'close':ERROR},5)]:
        case=load(files,faults);gui(case);tick(case);menu(case)
        check(name+'-fails-closed-default-retained',word(case,'restore_state')==state and word(case,'checkpoint_grid_value')==2 and len(case.live)==1 and case.words()[23]==1)
        check(name+'-menu-status-marker',(44,'Off [SD miss]' if state==4 else 'Off [SD error]') in case.grid_labels)
        if name=='close-error':check('uncertain-close-resident-handle-preserved',len(case.handles)==1 and int.from_bytes(case.u.mem_read(case.base+symbols['restore_files']+4,4),'little')!=0xffffffff)
        stable(case,name)
    # An actual compiled menu choice preempts a paused file read on another stack.
    concurrent=load({PATH:encode(5)});gui(concurrent);concurrent.pause_read=True
    try:tick(concurrent)
    except ValueError:assert concurrent.paused
    else:raise AssertionError('Read did not pause')
    saved=concurrent.u.context_save();pc=concurrent.u.reg_read(UC_ARM_REG_PC);prior=list(concurrent.file_events)
    for reg in ARGUMENTS:concurrent.u.reg_write(reg,0)
    guards={reg:0x52520000+i for i,reg in enumerate(SAVED)}
    for reg,value in guards.items():concurrent.u.reg_write(reg,value)
    concurrent.u.reg_write(UC_ARM_REG_SP,STACK-0x10000);concurrent.u.reg_write(UC_ARM_REG_LR,STOP|1)
    concurrent.u.emu_start((concurrent.base+symbols['center'])|1,STOP,timeout=30000000,count=10000000)
    check('gui-selection-during-read-no-file-io',concurrent.u.reg_read(UC_ARM_REG_PC)==STOP and concurrent.u.reg_read(UC_ARM_REG_SP)==STACK-0x10000 and all(concurrent.u.reg_read(reg)==v for reg,v in guards.items()) and prior==concurrent.file_events and word(concurrent,'checkpoint_grid_value')==4)
    concurrent.u.context_restore(saved);concurrent.u.emu_start(pc|1,STOP,timeout=30000000,count=10000000)
    check('read-resumes-and-retains-module',concurrent.u.reg_read(UC_ARM_REG_PC)==STOP and concurrent.u.reg_read(UC_ARM_REG_SP)==STACK and
          all(concurrent.u.reg_read(reg)==0x51510000+i for i,reg in enumerate(SAVED)) and concurrent.words()[51]==0 and len(concurrent.live)==1)
    menu(concurrent)
    check('late-restore-never-overrides-user-choice',word(concurrent,'restore_state')==6 and word(concurrent,'checkpoint_grid_value')==4 and (44,'Off [SD skip]') in concurrent.grid_labels)
    stable(concurrent,'concurrent')
    return dict(passed=True,checks=checks,module_sha256=module['module_sha256'],host_main_sha256=host['main_payload_sha256'],owned_path=PATH,read_only=True,camera_access=False,card_written=False,scheduler_verified=False,limits=['Kernel/filesystem dispatcher, incoming GUI/telemetry and rendering supplied','Menu On/Off service supplied; no physical UI or card readiness proof','Read starts only after eligible GUI callback; this is not a native card-ready query','No camera-side save implementation or physical recovery proof'])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('host','module','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();out=require_private_output(a.output)
    h=json.loads((a.host/'module-host.emulator.json').read_text());m=json.loads((a.module/'module.json').read_text())
    r=audit((a.host/'module-host.emulator.main.bin').read_bytes(),h,(a.module/'Z7APP.BIN').read_bytes(),m)
    r['source_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest();out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x',encoding='utf-8',newline='\n') as f:f.write(json.dumps(r,indent=2)+'\n')
    print(json.dumps(dict(passed=True,checks=len(r['checks']))))


if __name__=='__main__':main()
