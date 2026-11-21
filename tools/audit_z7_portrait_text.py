"""Compiled text-provider interception with original Z7 dispatch/completion.

SPDX-License-Identifier: MIT. Descriptor processing, glyph rendering, font
context and kernel event are supplied. Matrix transforms/provider publication,
cleanup and acknowledgement execute; no live hook, page reflow or pixels.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_SP, UC_ARM_REG_PC
from audit_splash_image import NativePNG, MEM, STOCK_SHA
from build_z7_module import build, HEADER
from build_z7_module_host import ROOT, ZIG
from z30_extensions.assembly import assemble, constant

CODE, TRANSFORM, STUB, CONTROL = (MEM+x for x in (0x10000,0x20000,0x40000,0x40200))
OPTIONS, ORIGIN, METRICS, BOUNDS = (MEM+x for x in (0x50000,0x51000,0x51100,0x51200))
MESSAGE,PAYLOAD,DESCRIPTOR,CONTEXT=0xa1d75000,0xa1d75100,0xa1d75200,0xa1850000
TABLE,RENDER,COMPLETE=0x11b6e120,0x10539574,0x104ba382
UNIT=65536


class TextFixture(NativePNG):
    def __init__(self,raw,packet,metadata):
        super().__init__(raw);self.native_call_timeout_us=0
        self.u.mem_map(0xa1d75000,0x1000)
        data=bytearray(packet[HEADER:HEADER+metadata['image_bytes']])
        for off in metadata['relocations']:
            struct.pack_into('<I',data,off,struct.unpack_from('<I',data,off)[0]+CODE)
        self.u.mem_write(CODE,bytes(data));self.u.mem_write(CODE+len(data),bytes(metadata['bss_bytes']))
        self.entry=CODE+metadata['symbols']['z7_portrait_text_probe']
        self.defer=(CODE+metadata['symbols']['z7_portrait_text_defer'])&~1
        self.callback=CODE+metadata['symbols']['z7_portrait_text_render']
        self.state=CODE+metadata['symbols']['z7_portrait_text_state']
        stub='push {r4,r5,r6,lr}; sub sp,#8; mov r4,r0; ldr r0,[r4,#0x94];'
        stub+=constant('r1',OPTIONS)+constant('r5',CONTROL)
        stub+='ldr r2,[r5]; ldr r3,[r5,#4]; ldr r6,[r5,#8]; str r6,[sp]; movw r5,#0x45b4; ldr r5,[r0,r5]; ldr r5,[r5,#0x1c]; blx r5;'
        stub+=constant('r5',CONTROL)+'str r0,[r5,#12]; add sp,#8; pop {r4,r5,r6,pc};'
        self.u.mem_write(STUB,assemble(stub,STUB,160))
        self.calls=[];self.events=[];self.result=0;self.replace_provider=False
        self.original_table=bytes(self.u.mem_read(TABLE,32))
    def word(self,p,v):self.u.mem_write(p,struct.pack('<I',v&0xffffffff))
    def read(self,p):return int.from_bytes(self.u.mem_read(p,4),'little')
    def matrix(self):return struct.unpack('<7I',self.u.mem_read(CONTEXT+0x34,28))
    def reset(self,command,matrix,transform,origin=ORIGIN,metrics=0,bounds=0):
        self.command=command;self.before_matrix=tuple(v&0xffffffff for v in matrix)
        self.word(0xa180ad98,CONTEXT);self.word(DESCRIPTOR+0x94,CONTEXT);self.word(CONTEXT+0x45b4,TABLE)
        self.word(CONTEXT+0x45d8,0xa1860000)
        self.u.mem_write(0xa1860000,bytes(0x1bc))
        for field,buffer in zip((0x1ac,0x18c,0x19c,0x178),(0xa1861000,0xa1862000,0xa1863000,0xa1864000)):
            self.word(0xa1860000+field,buffer)
        self.u.mem_write(CONTEXT+0x34,struct.pack('<7I',*(v&0xffffffff for v in matrix)))
        self.u.mem_write(TRANSFORM,struct.pack('<I4i',*transform))
        self.u.mem_write(MESSAGE,struct.pack('<7I',1,2,3,COMPLETE|1,0x42010000+command,PAYLOAD,0xaaaaaaaa))
        self.u.mem_write(PAYLOAD,struct.pack('<3I',DESCRIPTOR,0x12340000,0x56780000))
        self.u.mem_write(CONTROL,struct.pack('<4I',origin,metrics,bounds,0xa5a5a5a5))
        self.calls.clear();self.events.clear();self.replace_provider=False;self.result=0
    def hook(self,u,address,size,context):
        if address in (0x104baa5e,0x104bb130,0x104bb248):
            assert u.reg_read(UC_ARM_REG_R0)==DESCRIPTOR
            assert (u.reg_read(UC_ARM_REG_R1),u.reg_read(UC_ARM_REG_R2))==(
                (0x12340000,0x56780000) if self.command==0x38 else (0,0x12340000))
            table=self.read(CONTEXT+0x45b4)
            contents=bytes(u.mem_read(table,32))
            assert contents[:28]==self.original_table[:28] and struct.unpack_from('<I',contents,28)[0]==self.callback
            self.events.append('descriptor');u.reg_write(UC_ARM_REG_PC,STUB|1)
        elif address==RENDER:
            args=tuple(u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3))
            bounds=self.read(u.reg_read(UC_ARM_REG_SP))
            self.calls.append((args+(bounds,),self.matrix()))
            self.events.append('glyph')
            if self.replace_provider:self.word(CONTEXT+0x45b4,0xa1804000)
            self.ret(self.result)
        elif address==self.defer:
            self.events.append(('defer',u.reg_read(UC_ARM_REG_R0),u.reg_read(UC_ARM_REG_R1)))
        elif address==COMPLETE:
            assert self.read(self.state)==0 and self.read(self.state+4)==0
            assert self.matrix()==self.before_matrix
            assert self.read(CONTEXT+0x45b4)==(0xa1804000 if self.replace_provider else TABLE)
            self.events.append(('ack',u.reg_read(UC_ARM_REG_R0),u.reg_read(UC_ARM_REG_R1)))
        elif address==0x10170be8:
            assert (u.reg_read(UC_ARM_REG_R0),u.reg_read(UC_ARM_REG_R1))==(0xa1d75e48,2)
            self.events.append('event');self.ret(0)
        else:super().hook(u,address,size,context)


def signed(v):return (v+2**31)%2**32-2**31


def reference(matrix,transform):
    # Compose native->portrait scale/translation with portrait->LCD rotation.
    # Rows are mathematical 16.16 transforms, independent of C field writes.
    orientation,sx,sy,dx,dy=transform
    a,b,c,d,e,f,unused=(signed(v) for v in matrix)
    if not 0<a<=2*UNIT or not 0<e<=2*UNIT or b or d:return tuple(v&0xffffffff for v in matrix)
    portrait=[[a*sx//UNIT,0,c*sx//UNIT+dx],[0,-(e*sy//UNIT),480*sy-f*sy//UNIT+dy]]
    if orientation==2:rows=[portrait[1],portrait[0]]
    else:rows=[[-v for v in portrait[1]],[-v for v in portrait[0]]];rows[0][2]+=720*UNIT;rows[1][2]+=480*UNIT
    if not 0<a*sx//UNIT<=2*UNIT or not 0<e*sy//UNIT<=2*UNIT or any(not -2**31<=rows[i][2]<2**31 for i in (0,1)):
        return tuple(v&0xffffffff for v in matrix)
    return tuple(v&0xffffffff for row in rows for v in row)+(0,)


def audit(raw,packet,metadata):
    f=TextFixture(raw,packet,metadata);checks=[]
    def check(name,good):
        checks.append(dict(name=name,passed=bool(good)))
        if not good:raise AssertionError(name)
    f.word(0xa180ad98,CONTEXT)
    check('original-font-context-getter-returns-bound-slot',f.call(0x104ba37c)==CONTEXT)
    base=(UNIT,0,40*UNIT,0,UNIT,100*UNIT,0x12345678)
    matrices=(base,(UNIT//2,0,-10*UNIT,0,UNIT*2,20*UNIT,7),
              (0,0,0,0,UNIT,0,0),(UNIT,1,0,0,UNIT,0,0),(UNIT,0,0,1,UNIT,0,0),
              (2*UNIT+1,0,0,0,UNIT,0,0),(UNIT,0,2**31-1,0,UNIT,-2**31,3),(1,0,0,0,1,0,0),(-1,0,0,0,UNIT,0,0))
    cases=0
    for command,orientation,params,matrix in itertools.product((0x34,0x37,0x38),(1,2),
            ((UNIT,UNIT,0,0),(UNIT*3//4,UNIT*3//4,20*UNIT,-10*UNIT),(UNIT*3//2,UNIT,-5*UNIT,20*UNIT),
             (2*UNIT,UNIT//2,-720*UNIT,720*UNIT)),matrices):
        transform=(orientation,*params);f.reset(command,matrix,transform)
        msg=bytes(f.u.mem_read(MESSAGE,28));payload=bytes(f.u.mem_read(PAYLOAD,12))
        f.result=(0,1,0xdeadbeef)[cases%3]
        returned=f.call(f.entry,MESSAGE,TRANSFORM)
        check(f'command{command:x}-orientation{orientation}-params{params}-matrix{matrix}',
              returned==1 and f.calls==[((CONTEXT,OPTIONS,ORIGIN,0,0),reference(matrix,transform))] and
              f.matrix()==tuple(v&0xffffffff for v in matrix) and f.read(CONTEXT+0x45b4)==TABLE and
              bytes(f.u.mem_read(PAYLOAD,12))==payload and bytes(f.u.mem_read(MESSAGE,28))==msg[:24]+bytes(4) and
              f.read(CONTROL+12)==f.result and f.events==['descriptor','glyph',('defer',0x42010063,0),('ack',0x42010063,0),'event'])
        cases+=1
    for origin,metrics,bounds in itertools.product((0,ORIGIN),(0,METRICS),(0,BOUNDS)):
        if origin and not metrics and not bounds:continue
        f.reset(0x34,base,(1,UNIT,UNIT,0,0),origin,metrics,bounds)
        check(f'query-or-null-origin-{origin}-{metrics}-{bounds}-unchanged-matrix',
              f.call(f.entry,MESSAGE,TRANSFORM)==1 and f.calls==[((CONTEXT,OPTIONS,origin,metrics,bounds),base)] and f.matrix()==base)
    f.reset(0x34,base,(2,UNIT,UNIT,0,0));f.replace_provider=True
    check('foreign-provider-replacement-not-overwritten-after-render',
          f.call(f.entry,MESSAGE,TRANSFORM)==1 and f.read(CONTEXT+0x45b4)==0xa1804000 and f.matrix()==base and f.events[-1]=='event')
    for kind in ('orientation0','orientation3','scale0','scale-large','translation-large','foreign-completion','unknown-command',
                 'payload-null','payload-end','descriptor-null','descriptor-context','context-null','context-end','foreign-provider','busy',
                 'message-null','message-unaligned','transform-null','glyph-state-null','glyph-state-end',
                 'glyph-buffer-1ac','glyph-buffer-18c','glyph-buffer-19c','glyph-buffer-178'):
        t=[1,UNIT,UNIT,0,0];f.reset(0x34,base,t);mp=MESSAGE;tp=TRANSFORM
        if kind=='orientation0':t[0]=0
        if kind=='orientation3':t[0]=3
        if kind=='scale0':t[1]=0
        if kind=='scale-large':t[2]=2*UNIT+1
        if kind=='translation-large':t[3]=720*UNIT+1
        f.u.mem_write(TRANSFORM,struct.pack('<I4i',*t))
        if kind=='foreign-completion':f.word(MESSAGE+12,0x1042eadf)
        if kind=='unknown-command':f.word(MESSAGE+16,0x42010035)
        if kind=='payload-null':f.word(MESSAGE+20,0)
        if kind=='payload-end':f.word(MESSAGE+20,0xaffffffc)
        if kind=='descriptor-null':f.word(PAYLOAD,0)
        if kind=='descriptor-context':f.word(DESCRIPTOR+0x94,CONTEXT+4)
        if kind=='context-null':f.word(0xa180ad98,0)
        if kind=='context-end':f.word(0xa180ad98,0xaffffffc)
        if kind=='foreign-provider':f.word(CONTEXT+0x45b4,0xa1804000)
        if kind=='busy':f.word(f.state,1)
        if kind=='message-null':mp=0
        if kind=='message-unaligned':mp=MESSAGE+1
        if kind=='transform-null':tp=0
        if kind=='glyph-state-null':f.word(CONTEXT+0x45d8,0)
        if kind=='glyph-state-end':f.word(CONTEXT+0x45d8,0xaffffffc)
        if kind.startswith('glyph-buffer-'):f.word(0xa1860000+int(kind.rsplit('-',1)[1],16),0)
        msg=bytes(f.u.mem_read(MESSAGE,28));payload=bytes(f.u.mem_read(PAYLOAD,12));provider=f.read(CONTEXT+0x45b4)
        check(kind+'-rejected-without-publication-or-ack',f.call(f.entry,mp,tp)==0 and not f.events and not f.calls and
              bytes(f.u.mem_read(MESSAGE,28))==msg and bytes(f.u.mem_read(PAYLOAD,12))==payload and f.read(CONTEXT+0x45b4)==provider and f.matrix()==base)
        check(kind+'-does-not-clear-another-owner-busy-state',f.read(f.state)==int(kind=='busy'))
        f.word(f.state,0)
    return dict(passed=True,checks=checks,text_draw_cases=cases,
                native_message_dispatch_text_completion_and_kernel_wrapper_execute=True,
                compiled_provider_interception_matrix_math_and_cleanup_execute=True,
                descriptor_processing_glyph_renderer_context_and_kernel_event_supplied=True,
                page_reflow_inline_bitmap_symbols_live_font_state_or_pixels_proven=False,
                camera_card_access=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stock-main',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private directory')
    raw=a.stock_main.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=STOCK_SHA:p.error('Exact original Z7 C3.80 MAIN required')
    source=ROOT/'z7-native-modules/examples/portrait_text_probe.c';packet,metadata=build(source,zig=ZIG);again,other=build(source,zig=ZIG)
    assert packet==again and metadata==other,'Probe not reproducible'
    result=audit(raw,packet,metadata)
    names=('tools/audit_z7_portrait_text.py','tools/audit_splash_image.py','tools/build_z7_module.py','z7-native-modules/sdk/module.h',
           'z7-native-modules/sdk/module.ld','z7-native-modules/plugins/portrait_text.h','z7-native-modules/examples/portrait_text_probe.c')
    result.update(probe_sha256=hashlib.sha256(packet).hexdigest(),reproducible_probe=True,probe_bytes=len(packet),image_bytes=metadata['image_bytes'],
                  bss_bytes=metadata['bss_bytes'],relocations=len(metadata['relocations']),flat_probe_loader_admission_exercised=False,
                  source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    out.mkdir(parents=True);(out/'probe.BIN').write_bytes(packet)
    (out/'probe.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8',newline='\n')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(result['checks']),text_draw_cases=result['text_draw_cases'],probe_bytes=len(packet))))


if __name__=='__main__':main()
