"""Original Z7 app registry/getters and i-menu variant routing prefix.

SPDX-License-Identifier: MIT. App registration prefix, native state getters and
variant routing branch execute, with observed native task state guards. State/race
inputs supplied. No pending-request fence, reflow, input mapping, full boot or pixels.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from unicorn.arm_const import UC_ARM_REG_R4, UC_ARM_REG_SP, UC_ARM_REG_LR, UC_ARM_REG_PC
from audit_splash_image import MEM, STOCK_SHA, STACK, STOP
from audit_z7_information_native import InformationFixture
from build_z7_module import build, HEADER
from build_z7_module_host import ROOT,ZIG
CODE=MEM+0x10000
APP,ROOTS,STATE=0xa1829af4,0xa20207bc,0xa18298b8

class PageFixture(InformationFixture):
    def __init__(self,raw,packet,metadata):
        super().__init__(raw);self.native_call_timeout_us=0
        self.getters=[];self.mutation=None;self.route_stop=False
        self.prefix(0x1030cf74,0x1030d00a,MEM+0x60001)
        image=bytearray(packet[HEADER:HEADER+metadata['image_bytes']])
        for off in metadata['relocations']:
            struct.pack_into('<I',image,off,struct.unpack_from('<I',image,off)[0]+CODE)
        self.u.mem_write(CODE,bytes(image));self.operation=CODE+metadata['symbols']['z7_portrait_page_probe']
    def hook(self,u,address,size,context):
        if self.route_stop and address in (0x10386b20,0x10386b38):u.emu_stop();return
        if address in (0x10385b6a,0x10385b72):self.getters.append(address)
        if address==0x10385b78 and self.mutation:
            p,data=self.mutation;u.mem_write(p,data)
        super().hook(u,address,size,context)
    def setup(self,mode,variant,app=3):
        self.u.mem_write(APP,bytes([app]));self.u.mem_write(STATE,bytes([mode,variant]));self.getters=[];self.mutation=None
    def route(self,variant):
        self.u.mem_write(STATE+1,bytes([variant]));self.route_stop=True
        self.u.reg_write(UC_ARM_REG_R4,STATE);self.u.reg_write(UC_ARM_REG_SP,STACK);self.u.reg_write(UC_ARM_REG_LR,STOP|1)
        self.u.emu_start(0x10386b19,STOP,count=100)
        self.route_stop=False;return self.u.reg_read(UC_ARM_REG_PC)

def audit(raw,packet,metadata):
    f=PageFixture(raw,packet,metadata);checks=[]
    def check(name,good):
        checks.append(dict(name=name,passed=bool(good)));assert good,name
    check('original-registration-prefix-binds-app3-imenu-not-app4-or5',
          [int.from_bytes(f.u.mem_read(ROOTS+i*4,4),'little') for i in (3,4,5)]==[0xa1829970,0xa1829b1c,0xa1829b40])
    for variant in range(256):
        check(f'original-variant-branch{variant}',f.route(variant)==(0x10386b38 if variant in (0,0x29) else 0x10386b20))
    cases=[(mode,v) for mode in range(4) for v in range(256)]
    cases += [(mode,v) for mode in range(4,256) for v in (0,0x29,0x31,255)]
    for mode,variant in cases:
        f.setup(mode,variant)
        before=bytes(f.u.mem_read(STATE,2))
        got=f.call(f.operation)
        expected=1 if mode==3 or mode==0 and variant in (0,0x29) else 2 if mode==2 and variant in (0,0x29) else 3 if mode<=2 else 0
        check(f'native-mode{mode}-variant{variant}',got==expected and f.getters==[0x10385b6a,0x10385b72] and bytes(f.u.mem_read(STATE,2))==before)
    for app in range(256):
        if app==3:continue
        f.setup(3,0,app);check(f'other-app{app}',f.call(f.operation)==0 and not f.getters)
    for root in (0,0xa1829b1c,0xa1829971,0xffffffff):
        f.u.mem_write(ROOTS+12,struct.pack('<I',root));f.setup(3,0)
        check(f'foreign-imenu-root{root}',f.call(f.operation)==0 and not f.getters)
    f.u.mem_write(ROOTS+12,struct.pack('<I',0xa1829970))
    for p,data in ((APP,b'\0'),(ROOTS+12,bytes(4)),(STATE,b'\2'),(STATE+1,b'\x29')):
        f.setup(3,0);f.mutation=(p,data)
        check(f'observed-change-across-query{p}',f.call(f.operation)==0 and f.getters==[0x10385b6a,0x10385b72])
        f.u.mem_write(ROOTS+12,struct.pack('<I',0xa1829970))
    for task in (0xa182ecb8,0xa183dd90):
        for mode in range(256):
            f.setup(3,0);f.u.mem_write(task+0x74,bytes([mode]))
            got=f.call(f.operation)
            check(f'task{task}-state{mode}-gates-imenu',got==int(mode in (0,4)) and
                  f.getters==([0x10385b6a,0x10385b72] if mode in (0,4) else []))
        f.u.mem_write(task+0x74,b'\4')
        for off,data in ((0x74,b'\1'),(0x38,bytes(4)),(0x3c,bytes(4))):
            p=task+off;saved=bytes(f.u.mem_read(p,len(data)));f.setup(3,0);f.mutation=(p,data)
            check(f'task-change-during-page-query{p}',f.call(f.operation)==0 and f.getters==[0x10385b6a,0x10385b72])
            f.u.mem_write(p,saved)
    return dict(passed=True,checks=checks,classification_cases=len(cases),original_app_registration_state_getters_and_variant_branch_execute=True,
                app_state_and_race_inputs_supplied=True,observed_task_takeover_guard_integrated=True,
                pending_request_fence_page_admission_reflow_input_mapping_or_pixels_proven=False,camera_card_access=False)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-main',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private directory')
    raw=a.stock_main.read_bytes();assert hashlib.sha256(raw).hexdigest()==STOCK_SHA
    packet,metadata=build(ROOT/'z7-native-modules/examples/portrait_page_probe.c',zig=ZIG)
    again,other=build(ROOT/'z7-native-modules/examples/portrait_page_probe.c',zig=ZIG);assert packet==again and metadata==other
    result=audit(raw,packet,metadata)
    names=('tools/audit_z7_portrait_page.py','tools/audit_z7_information_native.py','tools/audit_splash_image.py',
           'tools/build_z7_module.py','z7-native-modules/sdk/module.h','z7-native-modules/sdk/module.ld',
           'z7-native-modules/plugins/portrait_page.h','z7-native-modules/plugins/portrait_takeover.h',
           'z7-native-modules/examples/portrait_page_probe.c')
    result.update(probe_sha256=hashlib.sha256(packet).hexdigest(),reproducible_probe=True,probe_bytes=len(packet),
                  source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    out.mkdir(parents=True);(out/'probe.BIN').write_bytes(packet)
    (out/'probe.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8',newline='\n')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(result['checks']),probe_bytes=len(packet))))

if __name__=='__main__':main()
