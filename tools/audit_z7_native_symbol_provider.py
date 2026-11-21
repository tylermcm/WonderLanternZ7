"""Original Z7 inline-symbol provider registration, measurement and draw ABI.

SPDX-License-Identifier: MIT. Context/options constructors, provider registration,
symbol callbacks, bitmap metadata reader and destruction execute. Synthetic PNG
resource callbacks, font metrics/shaping, allocation and final draw are supplied.
No portrait symbol interception, native asset inventory or task/pixel proof.
"""
import argparse
import gc
import hashlib
import json
from pathlib import Path
import struct
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2
from audit_z7_native_text_descriptor import DescriptorFixture
from audit_z7_portrait_text import MEM,DESCRIPTOR,CONTEXT,UNIT
from audit_splash_image import STOCK_SHA,synthetic_png
from build_z7_module import build
from build_z7_module_host import ROOT,ZIG

GETTER,OVERRIDE,ASSET,OUTPUT,GLYPH,MATRIX=(MEM+x for x in (0xc0000,0xc0100,0xc1000,0xc2000,0xc3000,0xc3100))

class SymbolFixture(DescriptorFixture):
    def __init__(self,*args):
        super().__init__(*args);self.resource_calls=[];self.symbol_draws=[];self.metadata_entries=0
        self.asset=synthetic_png(32,24,4)
    def prepare_symbol(self):
        self.prepare_descriptor(0x37,(1,UNIT,UNIT,0,0),'A',0)
        self.word(0xa180ada0,GETTER|1);self.word(0xa180ada4,OVERRIDE|1);self.u.mem_write(ASSET,self.asset)
        assert self.call(0x104bbaa2,DESCRIPTOR,CONTEXT)==1
        self.resource_calls.clear();self.symbol_draws.clear();self.metadata_entries=0
    def hook(self,u,address,size,context):
        if address in (GETTER,OVERRIDE):
            self.resource_calls.append((address==OVERRIDE,u.reg_read(UC_ARM_REG_R0)))
            self.word(u.reg_read(UC_ARM_REG_R1),len(self.asset));self.word(u.reg_read(UC_ARM_REG_R2),ASSET);self.ret(0);return
        if address==0x104310b4:self.metadata_entries+=1
        if address==0x10431738:
            self.symbol_draws.append((u.reg_read(UC_ARM_REG_R0),u.reg_read(UC_ARM_REG_R1),
                                      struct.unpack('<12I',u.mem_read(u.reg_read(UC_ARM_REG_R2),48))))
            self.ret(1);return
        super().hook(u,address,size,context)


def audit(raw,packet,metadata):
    checks=[];cases=0
    def check(name,good):checks.append(dict(name=name,passed=bool(good)));assert good,name
    for code in (0xe300,0xe700,0xe701,0xe702,0xefff):
        for flag in (0,1,2):
            f=SymbolFixture(raw,packet,metadata);f.prepare_symbol()
            state=f.read(CONTEXT+0x45d8);provider=f.read(state+0xb8)
            expected=(0xe300,0xefff,0x104bb461,0x104bb605,DESCRIPTOR)
            check(f'case{cases}-original-registration-clones-exact-provider',f.read(state+0xb4)==1 and
                  struct.unpack('<5I',f.u.mem_read(provider,20))==expected)
            count=len(f.live);check(f'case{cases}-replacement-registration-frees-old-copy',f.call(0x104bbaa2,DESCRIPTOR,CONTEXT)==1 and len(f.live)==count)
            if 0xe700<=code<=0xe702:
                index=code-0xe700;f.u.mem_write(DESCRIPTOR+0x7e+8*index,bytes([flag]));f.word(DESCRIPTOR+0x80+8*index,0x12340000+index)
            override=flag==1 and 0xe700<=code<=0xe702
            resource=(override,0x12340000+code-0xe700 if override else code)
            result=f.call(0x104bb460,code,OUTPUT,DESCRIPTOR)
            measured=struct.unpack('<4i',f.u.mem_read(OUTPUT,16))
            check(f'case{cases}-native-measure-resource-routing-and-png-dimensions',result==0 and f.resource_calls==[resource] and
                  f.metadata_entries==1 and f.read(DESCRIPTOR+0x74)==32 and f.read(DESCRIPTOR+0x78)==24 and
                  measured==(0,UNIT,104857,0))
            f.u.mem_write(GLYPH,struct.pack('<3I',1,code,MATRIX));f.u.mem_write(MATRIX,struct.pack('<7i',UNIT,0,100*UNIT,0,UNIT,200*UNIT,1))
            result=f.call(0x104bb604,GLYPH,0,0,DESCRIPTOR)
            check(f'case{cases}-native-draw-resource-routing-and-stock-abi',result==0 and f.resource_calls==[resource,resource] and
                  f.symbol_draws==[(100,(-209)&0xffffffff,(ASSET,len(f.asset),0xffffffff,0,0,0,0,0,0,0,0,1))])
            f.word(GLYPH,0);f.resource_calls.clear();f.symbol_draws.clear()
            check(f'case{cases}-draw-disabled-makes-no-resource-or-render-call',f.call(0x104bb604,GLYPH,0,0,DESCRIPTOR)==0 and
                  not f.resource_calls and not f.symbol_draws)
            f.destroy();check(f'case{cases}-native-destruction-releases-all-buffers',not f.live)
            del f;gc.collect();cases+=1
    return dict(passed=True,checks=checks,native_symbol_cases=cases,
                original_symbol_registration_measure_draw_override_routing_and_destruction_execute=True,
                native_png_metadata_reader_executes=True,
                synthetic_resource_callbacks_font_metrics_allocator_and_final_draw_supplied=True,
                portrait_symbol_rotation_native_assets_mutex_task_lifetime_or_pixels_proven=False,camera_card_access=False,
                native_entries=dict(register='104BBAA2',measure='104BB461',draw='104BB605',resource='104BBAE5',override='104BBAEB'))


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stock-main',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private directory')
    raw=a.stock_main.read_bytes();assert hashlib.sha256(raw).hexdigest()==STOCK_SHA
    source=ROOT/'z7-native-modules/examples/portrait_text_probe.c'
    packet,metadata=build(source,zig=ZIG);again,other=build(source,zig=ZIG);assert packet==again and metadata==other
    result=audit(raw,packet,metadata)
    names=('tools/audit_z7_native_symbol_provider.py','tools/audit_z7_native_text_descriptor.py','tools/audit_z7_native_glyph.py',
           'tools/audit_z7_portrait_text.py','tools/audit_splash_image.py','tools/build_z7_module.py','z7-native-modules/examples/portrait_text_probe.c',
           'z7-native-modules/plugins/portrait_text.h','z7-native-modules/sdk/module.h','z7-native-modules/sdk/module.ld')
    result.update(probe_sha256=hashlib.sha256(packet).hexdigest(),reproducible_probe=True,
                  source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    out.mkdir(parents=True);(out/'probe.BIN').write_bytes(packet)
    (out/'probe.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8',newline='\n')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(result['checks']),native_cases=result['native_symbol_cases'])))


if __name__=='__main__':main()
