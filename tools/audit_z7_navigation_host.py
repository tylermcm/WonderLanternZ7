"""Loaded API88 resident navigation bridge, publication and stock fallback.

SPDX-License-Identifier: MIT. Loader, API registration, patched central dispatch,
resident guards and cold initialization execute. Filesystem/kernel/allocator and
native mode callbacks are supplied. No complete boot, UI task/selector lifetime,
touch handling, pixels, camera/card access or installation clearance.
"""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import struct
from unicorn.arm_const import UC_ARM_REG_R0
from audit_z7_module_host import HostFixture
from audit_splash_image import MEM
from build_z7_module import build
from build_z7_module_host import ROOT,STATE,CURSOR,ZIG

MODE,SLOTS,FOREIGN=0xa182df80,0xa182df88,MEM+0x70000

class NavigationHostFixture(HostFixture):
    def __init__(self,raw,report,packet,metadata):
        super().__init__(raw,report,packet);self.metadata=metadata;self.native_call_timeout_us=0
        self.functions=struct.unpack('<34I',self.u.mem_read(0x11eca198,136))[1::2]
        self.stock=[];self.foreign=[];self.loaded_base=0
    def read(self,p):return int.from_bytes(self.u.mem_read(p,4),'little')
    def write(self,p,v):self.u.mem_write(p,struct.pack('<I',v&0xffffffff))
    def var(self,name):return (self.loaded_base or self.words()[12])+self.metadata['symbols']['z7_navigation_probe_'+name]
    def hook(self,u,address,size,context):
        if address in {v&~1 for v in getattr(self,'functions',())}:
            d=u.reg_read(UC_ARM_REG_R0);self.stock.append((address,d));self.ret(d^0x5a5a0000);return
        if address==FOREIGN:
            d=u.reg_read(UC_ARM_REG_R0);self.foreign.append(d);self.ret(d^0x9a9a0000);return
        super().hook(u,address,size,context)
    def load(self):
        result=self.call(self.report['symbols']['z7_module_load_once'],STATE);self.setword(40,result)
        if result==8:self.loaded_base=self.words()[12]
        return result
    def dispatch(self,probe_mode=0,native_mode=0,direction=0):
        self.write(self.var('mode'),probe_mode);self.u.mem_write(MODE,bytes([native_mode]));self.stock.clear();self.foreign.clear()
        before=self.read(self.var('calls'));result=self.call(0x104389b1,direction)
        return result,self.read(self.var('calls'))-before


def audit(raw,host,packet,metadata,failed,failed_meta,old_raw,old_host):
    checks=[]
    def check(name,good):checks.append(dict(name=name,passed=bool(good)));assert good,name
    f=NavigationHostFixture(raw,host,packet,metadata)
    original=bytes(f.u.mem_read(MODE+4,136))
    for mode in range(17):
        f.u.mem_write(MODE,bytes([mode]));f.stock.clear()
        check(f'before-load-central-dispatch-mode{mode}-stock',f.call(0x104389b1,2)==(2^0x5a5a0000) and f.stock==[(f.functions[mode]&~1,2)])
    check('init-only-api88-registration-publishes-after-commit-without-slot-writes',f.load()==8 and
          f.read(f.var('api_size'))==88 and f.read(f.var('registered'))==1 and f.read(f.var('duplicate'))==0 and
          f.read(STATE+388)==1 and f.read(STATE+92)==1 and bytes(f.u.mem_read(MODE+4,136))==original)
    for mode in range(17):
        for d in (0,1,2,3,4,0xffffffff):
            result,calls=f.dispatch(native_mode=mode,direction=d)
            check(f'loaded-stock-mode{mode}-direction{d}',result==(d^0x5a5a0000) and calls==1 and
                  f.stock==[(f.functions[mode]&~1,d)] and not f.foreign and f.read(STATE+392)==0)
    for probe_mode in (1,2,3,4):
        result,calls=f.dispatch(probe_mode,direction=3)
        check(f'callback-mode{probe_mode}-handled-invalid-recursive-or-late',calls==1 and result==
              ((0x24680000|3) if probe_mode==1 else (3^0x5a5a0000)) and len(f.stock)==int(probe_mode!=1) and f.read(STATE+392)==0)
        if probe_mode==4:check('late-registration-is-rejected',f.read(f.var('late'))==0)
    for offset,value in ((32,0),(40,7),(48,0),(52,0),(76,1),(92,0),(384,0),(384,f.words()[12]+metadata['image_bytes']+1),
                         (388,0),(392,1),(396,0),(400,0)):
        saved=f.read(STATE+offset);f.setword(offset,value)
        result,calls=f.dispatch(1,direction=2)
        check(f'invalid-host-field{offset}-delegates-once',result==(2^0x5a5a0000) and calls==0 and len(f.stock)==1)
        f.setword(offset,saved)
    f.write(SLOTS,FOREIGN|1)
    result,calls=f.dispatch(1,direction=1)
    check('foreign-native-slot-bypasses-module-and-is-preserved',result==(1^0x9a9a0000) and calls==0 and f.foreign==[1] and not f.stock and f.read(SLOTS)==FOREIGN|1)
    f.write(SLOTS,f.functions[0]);f.write(f.var('foreign'),FOREIGN|1)
    result,calls=f.dispatch(5,direction=2)
    check('stock-fallback-refreshes-foreign-slot-after-callback-delegates',result==(2^0x9a9a0000) and calls==1 and f.foreign==[2] and not f.stock)
    for pointer in (0,FOREIGN,0x104389b1,host['symbols']['z7_navigation_bridge']):
        f.write(SLOTS,pointer);result,calls=f.dispatch(1)
        check(f'null-even-or-recursive-slot{pointer}-rejected',result==0 and calls==0 and not f.stock and not f.foreign)
    f.write(SLOTS,f.functions[0])
    for mode in (17,18,255):
        result,calls=f.dispatch(1,native_mode=mode)
        check(f'invalid-native-mode{mode}-no-table-callback',result==0 and calls==0 and not f.stock)
    del f;gc.collect()
    f=NavigationHostFixture(raw,host,failed,failed_meta)
    check('failed-init-clears-navigation-before-free',f.load()==7 and not f.live and not any(f.read(STATE+o) for o in (48,52,92,384,388,392)))
    f.u.mem_write(MODE,b'\0');check('failed-init-central-entry-remains-stock',f.call(0x104389b1,2)==(2^0x5a5a0000) and len(f.stock)==1)
    f=NavigationHostFixture(old_raw,old_host,packet,metadata)
    check('api84-rejects-navigation-module-before-publication',f.load()==7 and not f.live and f.read(STATE+48)==0)
    f=NavigationHostFixture(raw,host,packet,metadata);f.u.mem_write(STATE,b'\x6b'*404)
    check('cold-entry-preserves-original-return',f.call(0x101e3d94)==STATE)
    check('cold-reserves448-and-initializes404-byte-state',f.read(CURSOR)==STATE+448 and
          [f.read(STATE+o) for o in (384,388,392)]==[0]*3 and [f.read(STATE+o) for o in (396,400)]==[0xa5a5a5a5]*2)
    check('cold-preserves-continuation-registers-and-flags',f.heap_observation==dict(r0=STATE,r1=CURSOR,r2=0x22334455,r3=0x66778899,flags=0xf8000000))
    return dict(passed=True,checks=checks,api_bytes=88,state_bytes=404,reserved_bytes=448,
                actual_loader_sdk_central_navigation_bridge_native_table_and_cold_execute=True,
                filesystem_kernel_allocator_and_native_navigation_callbacks_supplied=True,
                real_ui_task_page_admission_selection_touch_boot_or_pixels_proven=False,camera_card_access=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('host','report','old-host','old-report','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private directory')
    host=json.loads(a.report.read_text());old=json.loads(a.old_report.read_text());raw=a.host.read_bytes();old_raw=a.old_host.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==host['main_payload_sha256'] and host['api_bytes']==88
    assert hashlib.sha256(old_raw).hexdigest()==old['main_payload_sha256'] and old['api_bytes']==84
    packet,metadata=build(ROOT/'z7-native-modules/examples/navigation_host_probe.c',zig=ZIG)
    again,other=build(ROOT/'z7-native-modules/examples/navigation_host_probe.c',zig=ZIG);assert packet==again and metadata==other
    failed,failed_meta=build(ROOT/'z7-native-modules/examples/navigation_host_fail_probe.c',zig=ZIG)
    result=audit(raw,host,packet,metadata,failed,failed_meta,old_raw,old)
    names=('tools/audit_z7_navigation_host.py','tools/audit_z7_module_host.py','tools/audit_splash_image.py','tools/build_z7_module.py','tools/build_z7_module_host.py',
           'z7-native-modules/examples/navigation_host_probe.c','z7-native-modules/examples/navigation_host_fail_probe.c')
    result.update(host_sha256=host['main_payload_sha256'],probe_sha256=hashlib.sha256(packet).hexdigest(),probe_bytes=len(packet),
                  reproducible_probe=True,source_sha256={**host['source_files'],**{n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names}})
    out.mkdir(parents=True);(out/'probe.BIN').write_bytes(packet);(out/'failed-probe.BIN').write_bytes(failed)
    (out/'probe.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8',newline='\n')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(result['checks']),probe_bytes=len(packet))))


if __name__=='__main__':main()
