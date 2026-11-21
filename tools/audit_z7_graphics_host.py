"""Loaded API84 graphics callback staging, resident bridge and stock fallback.

SPDX-License-Identifier: MIT. Loader/registration/bridge and original graphics
dispatcher/completion run. Filesystem/kernel/allocator and rectangle rendering
are supplied. No full boot, real graphics task scheduling, pixels or camera I/O.
"""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1
from audit_z7_module_host import HostFixture
from build_z7_module import build
from build_z7_module_host import ROOT, STATE, CURSOR, ZIG

SLOT,MESSAGE,PAYLOAD=0xa1d75d60,0xa1d75000,0xa1d75100
STOCK=0x10372391


class GraphicsHostFixture(HostFixture):
    def __init__(self,raw,report,packet,metadata):
        super().__init__(raw,report,packet)
        self.metadata=metadata;self.native_call_timeout_us=0
        self.u.mem_map(0xa1d75000,0x1000)
        if report.get('graphics_queue_hooks'):
            self.setword(376,0xa5a5a5a5);self.setword(380,0xa5a5a5a5)
        self.draws=[];self.acks=[];self.flags=[];self.write(SLOT,STOCK)
    def write(self,p,v):self.u.mem_write(p,struct.pack('<I',v))
    def read(self,p):return int.from_bytes(self.u.mem_read(p,4),'little')
    def var(self,name):return self.words()[12]+self.metadata['symbols']['z7_graphics_probe_'+name]
    def hook(self,u,address,size,context):
        if address==0x1042f5a8:
            self.draws.append(bytes(u.mem_read(u.reg_read(UC_ARM_REG_R0),28)));self.ret(0)
        elif address==0x1042eade:
            self.acks.append((u.reg_read(UC_ARM_REG_R0),u.reg_read(UC_ARM_REG_R1)))
        elif address==0x10170be8:
            self.flags.append((u.reg_read(UC_ARM_REG_R0),u.reg_read(UC_ARM_REG_R1)));self.ret(0)
        else:super().hook(u,address,size,context)
    def load(self):
        result=self.call(self.report['symbols']['z7_module_load_once'],STATE)
        self.setword(40,result)
        if result==8:self.write(self.var('bridge'),self.report['symbols']['z7_graphics_dispatch_bridge'])
        return result
    def tick(self):self.call(self.report['symbols']['z7_module_worker_tick'])
    def dispatch(self,mode=0):
        self.write(self.var('mode'),mode);self.draws.clear();self.acks.clear();self.flags.clear()
        self.u.mem_write(MESSAGE,struct.pack('<7I',1,2,3,0x1042eadf,0x42010017,PAYLOAD,0xa5a5a5a5))
        self.u.mem_write(PAYLOAD,struct.pack('<6I',110,194,110,24,1,2))
        before=self.read(self.var('calls'))
        self.call(self.report['symbols']['z7_graphics_dispatch_bridge'],MESSAGE)
        return self.read(self.var('calls'))-before


def audit(raw,host,packet,metadata,failed_packet,failed_metadata,old_raw,old_host):
    checks=[]
    def check(name,good):
        checks.append(dict(name=name,passed=bool(good)))
        if not good:raise AssertionError(name)
    def fixture(data=packet,meta=metadata):return GraphicsHostFixture(raw,host,data,meta)
    f=fixture();f.write(SLOT,0)
    check('loaded-api84-module-stages-without-writing-native-slot',f.load()==8 and f.read(f.var('api_size'))==84 and
          f.read(f.var('registered'))==1 and f.read(STATE+364)==1 and f.read(SLOT)==0 and f.read(STATE+92)==1)
    f.tick();check('worker-waits-for-native-task-registration',f.read(SLOT)==0 and f.read(STATE+368)==0)
    f.write(SLOT,STOCK);f.tick()
    bridge=host['symbols']['z7_graphics_dispatch_bridge']
    check('worker-cas-installs-resident-bridge-without-module-worker-registration',f.read(SLOT)==bridge and f.read(STATE+368)==1 and f.read(STATE+196)==0 and f.read(STATE+200)==0)
    for mode in range(5):
        calls=f.dispatch(mode)
        result=0x2468 if mode==1 else 0
        check(f'mode{mode}-compiled-callback-stock-or-owned-completion-exactly-once',
              calls==1 and len(f.draws)==int(mode!=1) and f.acks==[(0x42010062,result)] and
              f.flags==[(0xa1d75e3c,1)] and f.read(MESSAGE+24)==result and f.read(STATE+372)==0)
        if mode==4:check('registration-rejected-after-module-commit',f.read(f.var('late_registration'))==0)
    for offset,value in ((92,0),(368,0),(372,1),(360,0),(360,f.words()[12]+metadata['image_bytes']+1),(376,0),(380,0)):
        saved=f.read(STATE+offset);f.setword(offset,value)
        check(f'fallback-state{offset}-value{value}-does-not-call-module',f.dispatch()==0 and len(f.draws)==1 and f.acks==[(0x42010062,0)])
        f.setword(offset,saved)
    f.write(SLOT,0x12345679)
    check('prefetched-old-bridge-forwards-stock-after-foreign-slot-replacement',f.dispatch()==0 and len(f.draws)==1 and f.read(SLOT)==0x12345679)
    f.tick();check('worker-marks-foreign-ownership-without-overwriting-slot',f.read(STATE+368)==2 and f.read(SLOT)==0x12345679)
    f.write(SLOT,STOCK);f.tick();check('conflict-is-sticky-no-automatic-reinstallation',f.read(SLOT)==STOCK and f.read(STATE+368)==2)
    del f;gc.collect()
    for slot in (0x12345679,bridge):
        f=fixture();f.write(SLOT,slot);check(f'foreign-initial-slot{slot}-module-load',f.load()==8)
        f.tick();check(f'foreign-initial-slot{slot}-never-adopted',f.read(SLOT)==slot and f.read(STATE+368)==2)
        del f;gc.collect()
    f=fixture(failed_packet,failed_metadata)
    check('failed-init-clears-staged-graphics-callback-and-retains-no-module',f.load()==7 and not f.live and not any(f.read(STATE+off) for off in (48,52,360,364,368,372)))
    f.tick();check('failed-init-never-publishes-native-graphics-slot',f.read(SLOT)==STOCK and f.read(STATE+92)==0)
    del f;gc.collect()
    f=GraphicsHostFixture(old_raw,old_host,packet,metadata)
    result=f.call(old_host['symbols']['z7_module_load_once'],STATE)
    check('api84-probe-rejects-api80-before-registration-publication',result==7 and not f.live and f.read(STATE+48)==0 and f.read(SLOT)==STOCK)
    del f;gc.collect()
    f=fixture();f.u.mem_write(STATE,b'\x6b'*384)
    check('cold-workspace-hook-preserves-original-return',f.call(0x101e3d94)==STATE)
    check('cold-reserves384-clears-full-state-and-initializes-new-guards',f.read(CURSOR)==STATE+384 and
          [f.read(STATE+off) for off in (360,364,368,372)]==[0]*4 and
          [f.read(STATE+off) for off in (376,380)]==[0xa5a5a5a5]*2)
    check('cold-preserves-native-continuation-registers-and-flags',f.heap_observation==
          dict(r0=STATE,r1=CURSOR,r2=0x22334455,r3=0x66778899,flags=0xf8000000))
    return dict(passed=True,checks=checks,api_bytes=84,state_bytes=384,
                original_loader_sdk_callback_graphics_dispatch_completion_and_cold_workspace_execute=True,
                filesystem_kernel_allocator_rectangle_renderer_and_task_registration_order_supplied=True,
                resident_no_hot_unload=True,full_boot_real_task_caller_closure_lcd_admission_or_pixels_proven=False,camera_card_access=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('host','report','old-host','old-report','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private directory')
    host=json.loads(a.report.read_text(encoding='utf-8'));old=json.loads(a.old_report.read_text(encoding='utf-8'))
    raw=a.host.read_bytes();old_raw=a.old_host.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==host['main_payload_sha256'] and host.get('api_bytes')==84
    assert hashlib.sha256(old_raw).hexdigest()==old['main_payload_sha256'] and old.get('api_bytes')==80
    packet,metadata=build(ROOT/'z7-native-modules/examples/graphics_queue_probe.c',zig=ZIG)
    again,repeated=build(ROOT/'z7-native-modules/examples/graphics_queue_probe.c',zig=ZIG)
    assert packet==again and metadata==repeated
    failed,failed_meta=build(ROOT/'z7-native-modules/examples/graphics_queue_fail_probe.c',zig=ZIG)
    result=audit(raw,host,packet,metadata,failed,failed_meta,old_raw,old)
    names=('tools/audit_z7_graphics_host.py','tools/audit_z7_module_host.py','tools/audit_splash_image.py','tools/build_z7_module.py',
           'tools/build_z7_module_host.py','z7-native-modules/examples/graphics_queue_probe.c','z7-native-modules/examples/graphics_queue_fail_probe.c')
    result.update(host_sha256=host['main_payload_sha256'],probe_sha256=hashlib.sha256(packet).hexdigest(),reproducible_probe=True,
                  source_sha256={**host['source_files'],**{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names}})
    out.mkdir(parents=True);(out/'probe.BIN').write_bytes(packet);(out/'failed-probe.BIN').write_bytes(failed)
    for name,data in (('probe.json',metadata),('result.json',result)):
        (out/name).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(result['checks']),probe_bytes=len(packet))))


if __name__=='__main__':main()
