"""Original glyph layout/contour transforms around compiled portrait text.

SPDX-License-Identifier: MIT. Original font-provider buffer initialization,
renderer, glyph selection, affine contour transformation and destruction execute.
Descriptor processing, font metrics/shaping/outlines, allocation and final contour
emission are supplied. No native font-file shaping, GPU pixels or camera proof.
"""
import argparse
import gc
import hashlib
import itertools
import json
from pathlib import Path
import struct

from unicorn import UcError, UC_ERR_WRITE_UNMAPPED
from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_PC
from audit_splash_image import NativePNG, STOCK_SHA
from audit_z7_portrait_text import TextFixture, CODE, TRANSFORM, STUB, CONTROL, OPTIONS, CONTEXT, TABLE, RENDER, MESSAGE, DESCRIPTOR, UNIT, MEM
from build_z7_module import build
from build_z7_module_host import ROOT, ZIG

FONT,FONT_TABLE,METRIC_SINK,STRING,SELECT_SINK,PROVIDER,GLYPH_SINK,GLYPH,POINTS=(
    0xa1870000,*(MEM+x for x in (0x70000,0x70100,0x70200,0x70300,0x70400,0x70500,0x70600,0x70700)))


class NativeGlyphFixture(TextFixture):
    def prepare(self,command,matrix,transform,text,fail_allocation=0):
        self.u.mem_write(CONTEXT,bytes(0x4604));self.u.mem_write(FONT,bytes(0x100))
        super().reset(command,matrix,transform)
        self.word(CONTEXT,0x1016fe39);self.word(CONTEXT+4,0x1016fe4b)
        self.word(CONTEXT+0x45d8,0);self.glyph_cursor=0xa1880000
        self.fail_allocation=fail_allocation
        self.initialized=self.call(0x10477c30,CONTEXT)
        self.outlines=[];self.glyph_ids=[];self.shaped=[];self.native_entries=0;self.native_stage_counts={}
        self.pre_round=[];self.post_round=[]
        self.metric_error=0
        if self.initialized:return
        self.word(CONTEXT+0xb0,FONT);self.word(CONTEXT+0xac,0xffffffff)
        self.word(CONTEXT+0x50,UNIT);self.word(CONTEXT+0x60,UNIT);self.word(CONTEXT+0xe0,1)
        self.word(FONT+4,CONTEXT);self.word(FONT+8,FONT_TABLE);self.word(FONT+0x28,PROVIDER)
        self.u.mem_write(FONT_TABLE,bytes(0x50))
        self.word(FONT_TABLE+0x14,SELECT_SINK|1);self.word(FONT_TABLE+0x18,METRIC_SINK|1);self.word(FONT_TABLE+0x2c,GLYPH_SINK|1)
        self.word(PROVIDER+4,1)
        self.u.mem_write(OPTIONS,bytes(0x80));self.word(OPTIONS+4,UNIT);self.word(OPTIONS+8,UNIT)
        self.word(OPTIONS+12,200*UNIT);self.word(OPTIONS+16,20*UNIT)
        self.u.mem_write(STRING,text.encode('utf-16le'))
        self.word(OPTIONS+0x54,STRING);self.word(OPTIONS+0x58,len(text.encode('utf-16le'))//2);self.word(OPTIONS+0x74,CONTEXT)
        self.baseline=False
    def hook(self,u,address,size,context):
        if address==0x1016fe38:
            self.attempts+=1
            if self.attempts==self.fail_allocation:self.ret(0);return
            length=u.reg_read(UC_ARM_REG_R0);result=self.glyph_cursor
            assert 0<length<=0x10000 and result+length<0xa1900000
            self.glyph_cursor+=(length+7)&~7;self.live[result]=length;self.allocations.append(length)
            self.ret(result);return
        if address in (0x10539eb0,0x10539ed0):
            matrix=struct.unpack('<7i',u.mem_read(CONTEXT+0x34,28))
            (self.pre_round if address==0x10539eb0 else self.post_round).append((matrix[2],matrix[5]))
        if address in (0x10476e28,0x10476846,0x104a9416):
            if hasattr(self,'native_stage_counts'):self.native_stage_counts[address]=self.native_stage_counts.get(address,0)+1
        if address in (0x104baa5e,0x104bb130,0x104bb248):
            assert u.reg_read(UC_ARM_REG_R0)==DESCRIPTOR
            assert (u.reg_read(UC_ARM_REG_R1),u.reg_read(UC_ARM_REG_R2))==(
                (0x12340000,0x56780000) if self.command==0x38 else (0,0x12340000))
            table=self.read(CONTEXT+0x45b4);contents=bytes(u.mem_read(table,32))
            assert contents[:28]==self.original_table[:28]
            assert int.from_bytes(contents[28:32],'little')==(RENDER|1 if self.baseline else self.callback)
            self.events.append('descriptor');u.reg_write(UC_ARM_REG_PC,STUB|1)
        elif address==RENDER:
            self.native_entries+=1;self.events.append('native-renderer')
            NativePNG.hook(self,u,address,size,context)
        elif address==METRIC_SINK:
            assert u.reg_read(UC_ARM_REG_R0)==FONT
            u.mem_write(u.reg_read(UC_ARM_REG_R1),struct.pack('<4i',UNIT,UNIT,-UNIT,UNIT))
            self.ret(self.metric_error)
        elif address==SELECT_SINK:
            assert u.reg_read(UC_ARM_REG_R0)==FONT;self.ret(0)
        elif address==0x1047aa90:
            run=u.reg_read(UC_ARM_REG_R1);n=self.read(run+12);start=self.read(run+8)
            codes=[int.from_bytes(u.mem_read(self.read(run)+(start+i)*2,2),'little') for i in range(n)]
            self.shaped.extend(codes)
            for i,code in enumerate(codes):
                self.word(self.read(run+0x2c)+i*4,code);self.word(self.read(run+0x30)+i*4,start+i)
                self.word(self.read(run+0x34)+i*4,UNIT);u.mem_write(self.read(run+0x38)+i*8,bytes(8))
                u.mem_write(self.read(run+0x3c)+i*2,bytes(2))
            self.word(run+0x28,n);self.ret(1)
        elif address==GLYPH_SINK:
            assert u.reg_read(UC_ARM_REG_R0)==FONT
            self.glyph_ids.append(u.reg_read(UC_ARM_REG_R1))
            for reg in (UC_ARM_REG_R2,UC_ARM_REG_R3):self.word(u.reg_read(reg),0)
            u.mem_write(GLYPH,struct.pack('<HHI',0,3,POINTS));u.mem_write(POINTS,struct.pack('<6i',0,0,UNIT,0,0,UNIT))
            self.word(FONT+0x18,GLYPH);self.ret(0)
        elif address==0x10478ad2:
            assert u.reg_read(UC_ARM_REG_R0)==CONTEXT
            self.outlines.append(struct.unpack('<6i',u.mem_read(POINTS,24)));self.events.append('outline');self.ret(0)
        else:super().hook(u,address,size,context)
    def decoded(self,count):
        state=self.read(CONTEXT+0x45d8)
        return list(struct.unpack('<'+'I'*count,self.u.mem_read(self.read(state+0x178),count*4)))


def transformed_outline(points,transform):
    orientation,sx,sy,dx,dy=transform;result=[]
    for x,y in zip(points[::2],points[1::2]):
        px=x*sx//UNIT+dx;py=(480*UNIT-y)*sy//UNIT+dy
        result.extend((py,px) if orientation==2 else (720*UNIT-py,480*UNIT-px))
    return tuple(result)


def ceiling_point(point):return tuple((v+UNIT-1)//UNIT*UNIT for v in point)


def audit(raw,packet,metadata):
    checks=[];cases=0
    def check(name,good):
        checks.append(dict(name=name,passed=bool(good)))
        if not good:raise AssertionError(name)
    for command,orientation,text,params in itertools.product((0x34,0x37,0x38),(1,2),('A','ABC'),
            ((UNIT,UNIT,0,0),(3*UNIT//4,3*UNIT//4,20*UNIT,-10*UNIT),(UNIT,UNIT//2,0,0))):
        matrix=(UNIT,0,40*UNIT,0,UNIT,100*UNIT,0);transform=(orientation,*params)
        # Native glyph layout rounds its baseline after scaling. Compare with
        # the same native scaled layout, then rotate its emitted contours;
        # post-scaling an already emitted unscaled contour is not equivalent.
        sx,sy,dx,dy=params
        baseline_matrix=(sx,0,40*sx+dx,0,sy,480*UNIT-480*sy+100*sy-dy,0)
        original=NativeGlyphFixture(raw,packet,metadata);original.prepare(command,baseline_matrix,transform,text);original.baseline=True
        check(f'baseline{cases}-native-provider-initializes-owned-buffers',original.initialized==0 and len(original.live)==5)
        original.call(0x10372390,MESSAGE)
        baseline=original.outlines[:]
        pre_round=original.pre_round[:]
        if len(baseline)!=len(text) or original.shaped!=list(map(ord,text)) or original.glyph_ids!=list(map(ord,text)):
            print(json.dumps(dict(case=cases,text=text,outlines=baseline,shaped=original.shaped,glyph_ids=original.glyph_ids,
                                  native_return=original.read(CONTROL+12),stages=original.native_stage_counts)),flush=True)
        check(f'baseline{cases}-native-renderer-contours-and-utf16-decoding',
              original.read(CONTROL+12)==0 and len(baseline)==len(text) and original.shaped==list(map(ord,text)) and
              original.decoded(len(text))==list(map(ord,text)) and
              len(pre_round)==len(text) and original.post_round==list(map(ceiling_point,pre_round)) and
              original.glyph_ids==list(map(ord,text)) and original.native_entries==1 and original.native_stage_counts.get(0x104a9416)==len(text))
        original.call(0x10477b9c,CONTEXT)
        check(f'baseline{cases}-native-provider-destroys-all-owned-buffers',not original.live and original.read(CONTEXT+0x45d8)==0)
        del original;gc.collect()
        rotated=NativeGlyphFixture(raw,packet,metadata);rotated.prepare(command,matrix,transform,text)
        returned=rotated.call(rotated.entry,MESSAGE,TRANSFORM)
        rotation=(orientation,UNIT,UNIT,0,0)
        projected_pre=[transformed_outline(p,rotation) for p in pre_round]
        expected=[]
        for points,origin in zip(baseline,pre_round):
            # Stock10539EB0..CE ceilings translation AFTER rotation. Reflecting
            # a ceiled origin differs by one pixel at fractional positions.
            # Apply that exact native phase, never a comparison tolerance.
            target=ceiling_point(transformed_outline(origin,rotation))
            projected_rounded=transformed_outline(ceiling_point(origin),rotation)
            dx,dy=(a-b for a,b in zip(target,projected_rounded))
            projected=transformed_outline(points,rotation)
            expected.append(tuple(v+(dx if i%2==0 else dy) for i,v in enumerate(projected)))
        if rotated.outlines!=expected:
            print(json.dumps(dict(case=cases,baseline=baseline,actual=rotated.outlines,expected=expected)),flush=True)
        check(f'portrait{cases}-cmd{command:x}-orientation{orientation}-text{text}-params{params}-native-contours',
              returned==1 and rotated.read(CONTROL+12)==0 and rotated.outlines==expected and rotated.native_entries==1 and
              rotated.shaped==list(map(ord,text)) and rotated.glyph_ids==list(map(ord,text)) and rotated.matrix()==matrix and
              rotated.decoded(len(text))==list(map(ord,text)) and
              rotated.pre_round==projected_pre and rotated.post_round==list(map(ceiling_point,projected_pre)) and
              rotated.read(CONTEXT+0x45b4)==TABLE and rotated.events[-3:]==[('defer',0x42010063,0),('ack',0x42010063,0),'event'])
        rotated.call(0x10477b9c,CONTEXT)
        check(f'portrait{cases}-native-provider-destroys-all-owned-buffers',not rotated.live and rotated.read(CONTEXT+0x45d8)==0)
        del rotated;gc.collect();cases+=1
    allocator_faults=[]
    for fail in range(1,6):
        f=NativeGlyphFixture(raw,packet,metadata)
        fault=None
        try:f.prepare(0x34,(UNIT,0,40*UNIT,0,UNIT,100*UNIT,0),(1,UNIT,UNIT,0,0),'A',fail_allocation=fail)
        except UcError as error:
            fault=dict(allocation=fail,unicorn_error=error.errno,pc=f.u.reg_read(UC_ARM_REG_PC),retained_allocations=len(f.live))
        if fail==1:
            check('native-provider-first-allocation-null-returns-error-without-publication',
                  fault is None and f.initialized==1 and not f.live and f.read(CONTEXT+0x45d8)==0)
        else:
            # This is a counterexample, not successful native OOM recovery.
            # Native buffer helpers zero the supplied NULL before checking it.
            check(f'native-null-allocation{fail}-documented-null-write-counterexample',
                  fault==dict(allocation=fail,unicorn_error=UC_ERR_WRITE_UNMAPPED,pc=0x104a9c4a,retained_allocations=fail-1) and
                  f.read(CONTEXT+0x45d8)!=0)
            allocator_faults.append(fault)
        message_before=bytes(f.u.mem_read(MESSAGE,28));state_before=f.read(CONTEXT+0x45d8);live_before=dict(f.live)
        check(f'separate-admission-call-rejects-native-partial-state-after-null-allocation{fail}',
              f.call(f.entry,MESSAGE,TRANSFORM)==0 and not f.events and bytes(f.u.mem_read(MESSAGE,28))==message_before and
              f.read(CONTEXT+0x45d8)==state_before and f.live==live_before)
        del f;gc.collect()
    f=NativeGlyphFixture(raw,packet,metadata)
    matrix=(UNIT,0,40*UNIT,0,UNIT,100*UNIT,0)
    f.prepare(0x34,matrix,(2,UNIT,UNIT,0,0),'A');f.metric_error=2
    check('native-font-metric-error-restores-provider-and-matrix-before-stock-ack',
          f.call(f.entry,MESSAGE,TRANSFORM)==1 and f.read(CONTROL+12)==2 and not f.outlines and
          f.read(CONTEXT+0x45b4)==TABLE and f.matrix()==matrix and f.events[-1]=='event')
    f.call(0x10477b9c,CONTEXT);check('metric-error-provider-destruction-frees-all-owned-buffers',not f.live)
    return dict(passed=True,checks=checks,paired_native_glyph_cases=cases,
                status='PROGRESS; exact native contours checked; supplied NULL allocator policy exposes native faults',
                native_null_allocator_policy_observed_unsafe=True,native_allocator_failure_contract_proven=False,
                allocator_fault_counterexamples=allocator_faults,stock_post_rotation_translation_ceiling_checked=True,
                separate_partial_state_admission_checks=5,native_fault_recovery_demonstrated=False,
                original_provider_allocation_initialization_renderer_glyph_selection_contour_transform_and_destruction_execute=True,
                descriptor_font_metrics_shaping_outlines_allocator_and_final_emission_supplied=True,
                native_font_file_shaping_gpu_pixels_live_font_task_lifetime_or_installation_proven=False,camera_card_access=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stock-main',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private directory')
    raw=a.stock_main.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=STOCK_SHA:p.error('Exact original Z7 C3.80 MAIN required')
    source=ROOT/'z7-native-modules/examples/portrait_text_probe.c';packet,metadata=build(source,zig=ZIG);again,other=build(source,zig=ZIG)
    assert packet==again and metadata==other,'Probe not reproducible'
    result=audit(raw,packet,metadata)
    names=('tools/audit_z7_native_glyph.py','tools/audit_z7_portrait_text.py','tools/audit_splash_image.py','tools/build_z7_module.py',
           'z7-native-modules/sdk/module.h','z7-native-modules/sdk/module.ld','z7-native-modules/plugins/portrait_text.h','z7-native-modules/examples/portrait_text_probe.c')
    result.update(probe_sha256=hashlib.sha256(packet).hexdigest(),reproducible_probe=True,
                  source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    out.mkdir(parents=True);(out/'probe.BIN').write_bytes(packet)
    (out/'probe.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8',newline='\n')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(result['checks']),paired_cases=result['paired_native_glyph_cases'])))


if __name__=='__main__':main()
