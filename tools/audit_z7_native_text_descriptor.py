"""Original text descriptors/options/font context through portrait interception.

SPDX-License-Identifier: MIT. Native font context/provider constructors, option
construction/text copying, descriptor34/37/38, glyph layout and destruction run.
Font face/cache data, shaping, allocators and GPU/emission boundaries are supplied.
No Nikon font-file loading, inline symbols, real GPU pixels or camera proof.
"""
import argparse
import gc
import hashlib
import itertools
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_SP
from audit_splash_image import NativePNG, STOCK_SHA
from audit_z7_native_glyph import NativeGlyphFixture, FONT, FONT_TABLE, STRING, GLYPH_SINK, POINTS
from audit_z7_portrait_text import MEM, MESSAGE, PAYLOAD, DESCRIPTOR, CONTEXT, TABLE, TRANSFORM, RENDER, UNIT, reference
from build_z7_module import build
from build_z7_module_host import ROOT, ZIG

PARAMS,INPUT_TEXT,RANGE,START=MEM+0x80000,MEM+0x80010,MEM+0x80100,MEM+0x80120
ALLOCATOR,REALLOC,GLYPH_BOUNDS=MEM+0x90000,MEM+0x90f00,MEM+0x70900
IDENTITY=(UNIT,0,0,0,UNIT,0,1)


class DescriptorFixture(NativeGlyphFixture):
    def __init__(self,*args):
        super().__init__(*args);self.u.mem_map(0xa1d76000,0x1000)
        self.gpu={0x1104:0x2001};self.gpu_calls=[];self.full_context=False
        self.descriptors=[];self.renders=[];self.bitmap_matrices=[];self.ctor_results=[]
    def prepare_descriptor(self,command,transform,text,alignment):
        super().prepare(command,IDENTITY,transform,text)
        # Discard the parent fixture's supplied context before constructing the
        # operational context with the original constructor and providers.
        self.call(0x10477b9c,CONTEXT);assert not self.live
        self.u.mem_write(ALLOCATOR,struct.pack('<12I',0x1016fe39,0x1016fe4b,REALLOC|1,*([0]*9)))
        self.full_context=True;created=self.call(0x10476904,ALLOCATOR,0);self.full_context=False
        assert created==CONTEXT
        for getter in (0x1044c00c,0x1044f33e,0x1044e17c,0x10477b98):
            self.ctor_results.append(self.call(0x10476aca,CONTEXT,self.call(getter)))
        self.word(CONTEXT+0xb0,FONT);self.word(CONTEXT+0xac,0xffffffff);self.word(CONTEXT+0xc0,FONT)
        self.word(FONT_TABLE+0x1c,GLYPH_BOUNDS|1)
        self.options=self.call(0x104774ac,CONTEXT);assert self.options
        for mode,values in ((0,(UNIT,UNIT)),(1,(200*UNIT,24*UNIT))):
            self.u.mem_write(PARAMS,struct.pack('<2I',*values));assert self.call(0x1047762a,self.options,mode,PARAMS)==0
        self.u.mem_write(INPUT_TEXT,struct.pack('<3I',STRING,len(text),0))
        assert self.call(0x10477526,self.options,INPUT_TEXT)==0
        self.word(self.options+0x24,alignment);self.word(self.options+0x28,alignment)
        self.u.mem_write(DESCRIPTOR,bytes(0xc8))
        self.word(DESCRIPTOR,0x50090000);self.word(DESCRIPTOR+0x94,CONTEXT);self.word(DESCRIPTOR+0x98,self.options)
        self.word(DESCRIPTOR+0x28,0xffffffff)
        self.u.mem_write(DESCRIPTOR+8,struct.pack('<2H',20,20));self.u.mem_write(DESCRIPTOR+0xe,bytes((100,100)))
        self.word(DESCRIPTOR+0x1c,STRING);self.word(DESCRIPTOR+0x24,len(text)*2);self.word(DESCRIPTOR+0x6c,STRING)
        self.u.mem_write(DESCRIPTOR+0x5e,struct.pack('<6H',40,100,240,124,200,24))
        self.word(0xa1d75eac,1);self.word(0xa1d75eac+8,FONT);self.word(0xa1d75eac+12,0);self.word(0xa1d75eac+16,0x50090000)
        self.word(PAYLOAD+4,0);self.word(PAYLOAD+8,0)
        if command==0x38:
            self.word(PAYLOAD+4,RANGE);self.u.mem_write(RANGE,struct.pack('<3I',START,len(text),0));self.word(START,0)
        self.initial_options=bytes(self.u.mem_read(self.options,0x78))
        self.initial_provider=self.read(CONTEXT+0x45b4)
        self.descriptors.clear();self.renders.clear();self.bitmap_matrices.clear();self.gpu_calls.clear()
    def hook(self,u,address,size,context):
        if address==0x1016fe38 and u.reg_read(UC_ARM_REG_R0)==0x4604 and self.full_context:
            self.attempts+=1;self.live[CONTEXT]=0x4604;self.allocations.append(0x4604)
            u.mem_write(CONTEXT,bytes(0x4604));self.ret(CONTEXT);return
        if address==REALLOC:raise AssertionError('Unexpected realloc outside admitted fixture capacity')
        if address in (0x104baa5e,0x104bb130,0x104bb248):
            assert u.reg_read(UC_ARM_REG_R0)==DESCRIPTOR
            self.descriptors.append(address);self.events.append('native-descriptor')
            return NativePNG.hook(self,u,address,size,context)
        if address==RENDER:
            origin=u.reg_read(UC_ARM_REG_R2);metrics=u.reg_read(UC_ARM_REG_R3)
            bounds=self.read(u.reg_read(UC_ARM_REG_SP))
            self.renders.append(dict(matrix=self.matrix(),origin=struct.unpack('<2i',u.mem_read(origin,8)) if origin else None,
                                     metrics=bool(metrics),bounds=bool(bounds)))
        if address==GLYPH_BOUNDS:
            u.mem_write(u.reg_read(UC_ARM_REG_R2),struct.pack('<4i',0,UNIT,UNIT,0));self.ret(0);return
        if address==0x104aa7fe:
            self.bitmap_matrices.append(self.matrix());self.events.append('bitmap-emitter');self.ret(0);return
        if address in (0x1045004e,0x1045006a,0x10450a7c,0x10450a96):
            self.gpu_calls.append(address);self.ret(1 if address==0x10450a7c else 0);return
        if address==0x104501c4:
            self.ret(self.gpu.get(u.reg_read(UC_ARM_REG_R0),0));return
        if address==0x1045014e:
            self.gpu[u.reg_read(UC_ARM_REG_R0)]=u.reg_read(UC_ARM_REG_R1);self.ret(0);return
        super().hook(u,address,size,context)
        if address==0x1047aa90:
            run=u.reg_read(UC_ARM_REG_R1)
            for i in range(self.read(run+12)):self.word(self.read(run+0x34)+i*4,UNIT//16)
        if address==GLYPH_SINK:u.mem_write(POINTS,struct.pack('<6i',0,0,UNIT//16,0,0,UNIT//16))
    def destroy(self):
        assert self.call(0x10477502,self.options)==0
        assert self.call(0x10476a70,CONTEXT)==0


def audit(raw,packet,metadata):
    checks=[];cases=0
    def check(name,good):
        checks.append(dict(name=name,passed=bool(good)))
        if not good:raise AssertionError(name)
    for command,orientation,text,scale,alignment in itertools.product((0x34,0x37,0x38),(1,2),('A','ABC'),(UNIT,3*UNIT//4),(0,2)):
        transform=(orientation,scale,scale,0,0)
        original=DescriptorFixture(raw,packet,metadata);original.prepare_descriptor(command,transform,text,alignment)
        initial=original.initial_options
        check(f'case{cases}-native-context-and-option-construction',original.ctor_results==[0]*4 and original.initial_provider==TABLE and
              original.read(original.options)==CONTEXT and original.read(original.options+0x64)==1 and original.read(original.options+0x6c)==1 and
              bytes(original.u.mem_read(original.read(original.options+0x54),len(text)*2))==text.encode('utf-16le'))
        original.baseline=True;original.call(0x10372390,MESSAGE)
        baseline=original.renders[:];metrics=bytes(original.u.mem_read(DESCRIPTOR+0xa8,0x20))
        emission_count=len(original.bitmap_matrices) if command==0x34 else len(original.outlines)
        check(f'case{cases}-original-descriptor-glyph-emission',original.descriptors==[{0x34:0x104baa5e,0x37:0x104bb130,0x38:0x104bb248}[command]] and
              emission_count==len(text) and any(not r['metrics'] and not r['bounds'] for r in baseline))
        original.destroy();check(f'case{cases}-native-baseline-destruction-releases-all-buffers',not original.live)
        del original;gc.collect()
        rotated=DescriptorFixture(raw,packet,metadata);rotated.prepare_descriptor(command,transform,text,alignment)
        message_before=bytes(rotated.u.mem_read(MESSAGE,28));payload_before=bytes(rotated.u.mem_read(PAYLOAD,12))
        returned=rotated.call(rotated.entry,MESSAGE,TRANSFORM)
        expected=[]
        for entry in baseline:
            copy=dict(entry)
            if entry['origin'] is not None and not entry['metrics'] and not entry['bounds']:
                copy['matrix']=reference(entry['matrix'],transform)
            expected.append(copy)
        if rotated.renders!=expected:print(json.dumps(dict(case=cases,command=command,baseline=baseline,actual=rotated.renders,expected=expected)),flush=True)
        emission_count=len(rotated.bitmap_matrices) if command==0x34 else len(rotated.outlines)
        check(f'case{cases}-native-descriptor-query-and-draw-provider-integration',returned==1 and rotated.renders==expected and emission_count==len(text) and
              bytes(rotated.u.mem_read(DESCRIPTOR+0xa8,0x20))==metrics and rotated.matrix()==IDENTITY and rotated.read(CONTEXT+0x45b4)==TABLE and
              bytes(rotated.u.mem_read(PAYLOAD,12))==payload_before and bytes(rotated.u.mem_read(MESSAGE,28))==message_before[:24]+bytes(4) and
              rotated.events[-3:]==[('defer',0x42010063,0),('ack',0x42010063,0),'event'] and rotated.gpu[0x1104]==0x2001)
        rotated.destroy();check(f'case{cases}-native-portrait-destruction-releases-all-buffers',not rotated.live)
        del rotated;gc.collect();cases+=1
    return dict(passed=True,checks=checks,paired_native_descriptor_cases=cases,
                original_context_providers_options_text_copy_descriptors_glyph_layout_and_destruction_execute=True,
                font_face_cache_metrics_shaping_allocator_gpu_and_final_emission_supplied=True,
                native_font_file_loading_inline_symbols_gpu_pixels_or_live_task_lifetime_proven=False,camera_card_access=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stock-main',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private directory')
    raw=a.stock_main.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=STOCK_SHA:p.error('Exact original Z7 C3.80 MAIN required')
    source=ROOT/'z7-native-modules/examples/portrait_text_probe.c';packet,metadata=build(source,zig=ZIG);again,other=build(source,zig=ZIG)
    assert packet==again and metadata==other,'Probe not reproducible'
    result=audit(raw,packet,metadata)
    names=('tools/audit_z7_native_text_descriptor.py','tools/audit_z7_native_glyph.py','tools/audit_z7_portrait_text.py','tools/audit_splash_image.py',
           'tools/build_z7_module.py','z7-native-modules/sdk/module.h','z7-native-modules/sdk/module.ld','z7-native-modules/plugins/portrait_text.h',
           'z7-native-modules/examples/portrait_text_probe.c')
    result.update(probe_sha256=hashlib.sha256(packet).hexdigest(),reproducible_probe=True,
                  source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    out.mkdir(parents=True);(out/'probe.BIN').write_bytes(packet)
    (out/'probe.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8',newline='\n')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(result['checks']),paired_cases=result['paired_native_descriptor_cases'])))


if __name__=='__main__':main()
