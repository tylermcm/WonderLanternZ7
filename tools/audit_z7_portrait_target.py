"""Read-only original Z7 logical2 LCD target admission with native getter.

SPDX-License-Identifier: MIT. Registry and output state are supplied; original
10414756 executes. No renderer, task exclusion, lifetime, full boot or pixels.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from audit_splash_image import NativePNG, MEM, STOCK_SHA
from build_z7_module import build, HEADER
from build_z7_module_host import ROOT, ZIG

CODE,TABLE=MEM+0x10000,0xa1d75000
REG,OUTPUT=0xa180ad84,0xa1821394

class TargetFixture(NativePNG):
    def __init__(self,raw,packet,metadata):
        super().__init__(raw)
        self.native_call_timeout_us=0
        self.u.mem_map(TABLE,0x1000)
        image=bytearray(packet[HEADER:HEADER+metadata['image_bytes']])
        for off in metadata['relocations']:
            struct.pack_into('<I',image,off,struct.unpack_from('<I',image,off)[0]+CODE)
        self.u.mem_write(CODE,bytes(image))
        self.operation=CODE+metadata['symbols']['z7_portrait_target_probe']
        self.getters=0;self.mutation=None
    def write(self,p,v):self.u.mem_write(p,struct.pack('<I',v))
    def setup(self,selected=12,index=2,outputs=1):
        self.u.mem_write(REG,struct.pack('<3I',selected,TABLE,0))
        self.write(OUTPUT,outputs)
        records=bytearray(660)
        for i in range(33):records[i*20+4]=255
        struct.pack_into('<IBxHHHII',records,index*20,0xb0000000,selected,720,480,0,0,0)
        self.u.mem_write(TABLE,bytes(records))
        self.getters=0;self.mutation=None
    def hook(self,u,address,size,context):
        if address==0x10414756:self.getters+=1
        if address==0x1041477a and self.mutation:
            p,data=self.mutation;u.mem_write(p,data)
        super().hook(u,address,size,context)

def audit(raw,packet,metadata):
    f=TargetFixture(raw,packet,metadata);checks=[]
    def check(name,expected,calls):
        before=(bytes(f.u.mem_read(REG,12)),bytes(f.u.mem_read(OUTPUT,4)),bytes(f.u.mem_read(TABLE,660)))
        result=f.call(f.operation)
        after=(bytes(f.u.mem_read(REG,12)),bytes(f.u.mem_read(OUTPUT,4)),bytes(f.u.mem_read(TABLE,660)))
        good=result==expected and f.getters==calls and (f.mutation is not None or before==after)
        checks.append(dict(name=name,passed=good))
        assert good,(name,result,f.getters)
    for selected in (0,1,2,12,32,254):
        f.setup(selected);check(f'hardware-id{selected}-maps-to-logical2',1,1)
    for outputs in (0,2,3,4,5,6,7,0xffffffff):
        f.setup(outputs=outputs);check(f'non-exclusive-lcd-output{outputs}',0,0)
    f.setup(outputs=0x80000001);check('unrelated-output-bits-preserved',1,1)
    for index in (0,1,3,5,32):
        f.setup(index=index);check(f'other-logical-target{index}',0,0)
    for table in (0,1,0xa1800001,0xaffffd70,0xb0000000,0xfffffffc):
        f.setup();f.write(REG+4,table);check(f'invalid-table{table}',0,0)
    for offset,value in ((0,0),(4,0x02d000ff),(4,0x0280000c),(8,479),(8,481)):
        f.setup();f.write(TABLE+40+offset,value);check(f'invalid-descriptor{offset}-{value}',0,0)
    f.setup(255);check('inactive-id255',0,0)
    for index in (0,1,3,32):
        f.setup();f.u.mem_write(TABLE+index*20+4,b'\x0c');check(f'duplicate-hardware-id{index}',0,0)
    for offset in range(0,20,4):
        f.setup();f.mutation=(TABLE+40+offset,struct.pack('<I',0x12345678));check(f'descriptor-changed-across-native-query{offset}',0,1)
    for p,value in ((REG,13),(REG+4,TABLE+4),(OUTPUT,2)):
        f.setup();f.mutation=(p,struct.pack('<I',value));check(f'registry-or-output-changed-across-query{p}',0,1)
    match=CODE+metadata['symbols']['z7_portrait_target_match_probe']
    for logical in (0,1,2,3,32):
        f.setup(index=logical);before=bytes(f.u.mem_read(TABLE,660))
        good=f.call(match,logical)==1 and f.getters==1 and bytes(f.u.mem_read(TABLE,660))==before
        checks.append(dict(name=f'generic-native-logical-match{logical}',passed=good));assert good
        f.getters=0;good=f.call(match,(logical+1)%33)==0 and not f.getters
        checks.append(dict(name=f'generic-wrong-logical-match{logical}',passed=good));assert good
    for logical in (33,0xffffffff):
        f.getters=0;good=f.call(match,logical)==0 and not f.getters
        checks.append(dict(name=f'generic-out-of-range{logical}',passed=good));assert good
    return dict(passed=True,checks=checks,original_target_getter_executes=True,registry_and_output_state_supplied=True,
                task_exclusion_allocation_lifetime_aba_page_policy_or_pixels_proven=False,camera_card_access=False)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-main',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private directory')
    raw=a.stock_main.read_bytes();assert hashlib.sha256(raw).hexdigest()==STOCK_SHA
    packet,metadata=build(ROOT/'z7-native-modules/examples/portrait_target_probe.c',zig=ZIG)
    again,other=build(ROOT/'z7-native-modules/examples/portrait_target_probe.c',zig=ZIG)
    assert packet==again and metadata==other
    result=audit(raw,packet,metadata)
    names=('tools/audit_z7_portrait_target.py','tools/audit_splash_image.py','tools/build_z7_module.py',
           'z7-native-modules/sdk/module.h','z7-native-modules/sdk/module.ld',
           'z7-native-modules/plugins/portrait_target.h','z7-native-modules/examples/portrait_target_probe.c')
    result.update(probe_sha256=hashlib.sha256(packet).hexdigest(),reproducible_probe=True,probe_bytes=len(packet),
                  source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    out.mkdir(parents=True);(out/'probe.BIN').write_bytes(packet)
    (out/'probe.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8',newline='\n')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(result['checks']),probe_bytes=len(packet))))

if __name__=='__main__':main()
