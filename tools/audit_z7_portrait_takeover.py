"""Native original Z7 MENU/playback constructors and observed state guard.

SPDX-License-Identifier: MIT. Native config/object getters, constructors, generic
state setter/getter and compiled guard execute. Kernel task/event creation is
supplied; no task runs and pending requests, boot, scheduling or pixels are unproved.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2
from audit_splash_image import NativePNG,MEM,STOCK_SHA
from build_z7_module import build,HEADER
from build_z7_module_host import ROOT,ZIG
CODE=MEM+0x10000
MENU,PLAY=0xa182ecb8,0xa183dd90

class TakeoverFixture(NativePNG):
    def __init__(self,raw,packet,metadata):
        super().__init__(raw);self.native_call_timeout_us=0
        self.u.mem_map(0xa1ff0000,0x10000)
        self.creates=[];self.events=[];self.getters=0;self.mutation=None
        image=bytearray(packet[HEADER:HEADER+metadata['image_bytes']])
        for off in metadata['relocations']:
            struct.pack_into('<I',image,off,struct.unpack_from('<I',image,off)[0]+CODE)
        self.u.mem_write(CODE,bytes(image));self.operation=CODE+metadata['symbols']['z7_portrait_takeover_probe']
    def hook(self,u,address,size,context):
        if address in (0x1017074a,0x10170b5c):
            args=tuple(u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2))
            (self.creates if address==0x1017074a else self.events).append(args);self.ret(0);return
        if address==0x10465020:self.getters+=1
        if address==0x10465024 and self.getters==2 and self.mutation:
            p,data=self.mutation;u.mem_write(p,data)
        super().hook(u,address,size,context)
    def setup(self,a=4,b=4):
        self.u.mem_write(MENU+0x74,bytes([a]));self.u.mem_write(PLAY+0x74,bytes([b]));self.getters=0;self.mutation=None
    def word(self,p):return int.from_bytes(self.u.mem_read(p,4),'little')

def audit(raw,packet,metadata):
    f=TakeoverFixture(raw,packet,metadata);checks=[]
    def check(name,good):
        checks.append(dict(name=name,passed=bool(good)));assert good,name
    config=f.call(0x10053a50);f.call(0x101f2474,config)
    for index,name,base,getter,ctor in ((7,b'APPMENU',MENU,0x1048b0e4,0x1048b0e8),(8,b'APPPLAY',PLAY,0x105006e4,0x105006e8)):
        p=f.call(0x101f247a,0x10000+index)
        check(name.decode()+'-native-config-name',bytes(f.u.mem_read(p+16,12)).split(b'\0')[0]==name)
        check(name.decode()+'-native-object-getter',f.call(getter)==base)
        f.creates.clear();f.events.clear();f.call(ctor)
        check(name.decode()+'-native-constructor-kernel-boundaries',f.creates==[(base,0x1020ba0f,p)] and len(f.events)==1 and f.events[0][0]==base+0x20)
        for state in range(256):
            f.u.mem_write(base+0x94,bytes.fromhex('78563412efcdab89'))
            f.call(0x10465026,base,state)
            check(name.decode()+f'-native-setter-getter{state}',f.call(0x10465020,base)==state and
                  bytes(f.u.mem_read(base+0x94,8))==(bytes(8) if state==0 else bytes.fromhex('78563412efcdab89')))
    for task in (MENU,PLAY):
        for state in range(256):
            f.setup(state if task==MENU else 4,state if task==PLAY else 4)
            before=(bytes(f.u.mem_read(MENU,0x9c)),bytes(f.u.mem_read(PLAY,0x9c)))
            expected=int(state not in (0,4));got=f.call(f.operation)
            check(f'observed-task{task}-state{state}',got==expected and f.getters==2 and before==(bytes(f.u.mem_read(MENU,0x9c)),bytes(f.u.mem_read(PLAY,0x9c))))
    for a in (0,4):
        for b in (0,4):
            f.setup(a,b);check(f'inactive-combination{a}-{b}',f.call(f.operation)==0)
    for base in (MENU,PLAY):
        for off in (0x38,0x3c):
            p=base+off;saved=f.word(p);f.setup();f.u.mem_write(p,bytes(4))
            check(f'foreign-native-callback{p}',f.call(f.operation)==1 and f.getters==0);f.u.mem_write(p,struct.pack('<I',saved))
    for base in (MENU,PLAY):
        for off,data in ((0x74,b'\1'),(0x38,bytes(4)),(0x3c,bytes(4))):
            p=base+off;saved=bytes(f.u.mem_read(p,len(data)));f.setup();f.mutation=(p,data)
            check(f'changed-across-native-state-query{p}',f.call(f.operation)==1 and f.getters==2);f.u.mem_write(p,saved)
    return dict(passed=True,checks=checks,original_config_names_object_getters_constructors_and_state_accessors_execute=True,
                kernel_task_event_creation_and_state_race_inputs_supplied=True,task_bodies_pending_request_fence_scheduling_or_pixels_proven=False,camera_card_access=False)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-main',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private directory')
    raw=a.stock_main.read_bytes();assert hashlib.sha256(raw).hexdigest()==STOCK_SHA
    packet,metadata=build(ROOT/'z7-native-modules/examples/portrait_takeover_probe.c',zig=ZIG)
    again,other=build(ROOT/'z7-native-modules/examples/portrait_takeover_probe.c',zig=ZIG);assert packet==again and metadata==other
    result=audit(raw,packet,metadata)
    names=('tools/audit_z7_portrait_takeover.py','tools/audit_splash_image.py','tools/build_z7_module.py',
           'z7-native-modules/sdk/module.h','z7-native-modules/sdk/module.ld',
           'z7-native-modules/plugins/portrait_takeover.h','z7-native-modules/examples/portrait_takeover_probe.c')
    result.update(probe_sha256=hashlib.sha256(packet).hexdigest(),reproducible_probe=True,probe_bytes=len(packet),
                  source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    out.mkdir(parents=True);(out/'probe.BIN').write_bytes(packet)
    (out/'probe.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8',newline='\n')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(result['checks']),probe_bytes=len(packet))))

if __name__=='__main__':main()
