"""Compiled portrait touch geometry and original-Z7 navigation adapter.

SPDX-License-Identifier: MIT. Native mode dispatch, focus getter and item reads
execute. Native selector/rendering, admitted page/layout/output, item state and
touch calibration/events are supplied. No installed input hook, actual touch
registration, task/queue lifetime, native selection completion or camera proof.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import struct
from unicorn.arm_const import UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_SP,UC_ARM_REG_LR,UC_ARM_REG_PC
from audit_splash_image import NativePNG,STOCK_SHA,MEM,STACK,STOP
from build_z7_module import build,HEADER
from build_z7_module_host import ROOT,ZIG

CODE,POINT,EVENT,COPY=MEM+0x10000,MEM+0x20000,MEM+0x21000,MEM+0x22000
MODE,COUNT,INDEX,FOCUS,UI,ITEMS=0xa182df80,0xa2023318,0xa202331c,0xa182e2fc,0xa20235a8,0xa202373c
OFFSETS=(0x12,0x1a,0x28,0x2c,0x30,0x34)

class InputFixture(NativePNG):
    def __init__(self,raw,packet,metadata):
        super().__init__(raw);self.native_call_timeout_us=0;self.metadata=metadata
        self.u.mem_map(0xa2010000,0x20000)
        image=bytearray(packet[HEADER:HEADER+metadata['image_bytes']])
        for off in metadata['relocations']:struct.pack_into('<I',image,off,struct.unpack_from('<I',image,off)[0]+CODE)
        self.u.mem_write(CODE,bytes(image));self.u.mem_write(CODE+len(image),bytes(metadata['bss_bytes']))
        self.functions=struct.unpack('<34I',self.u.mem_read(0x11eca198,136))[1::2]
        self.stock=[];self.selected=[];self.queries=[];self.focus_calls=0;self.selector_prefix=False;self.selector_gate=0
    def read(self,p):return int.from_bytes(self.u.mem_read(p,4),'little')
    def word(self,p,v):self.u.mem_write(p,struct.pack('<I',v&0xffffffff))
    def entry(self,name):return CODE+self.metadata['symbols']['z7_portrait_'+name+'_probe']
    def setup(self,mode=0,current=0,disabled=0,count=12,imenu=0):
        self.u.mem_write(MODE,bytes([mode]));self.word(COUNT,count);self.word(INDEX,0x12345678)
        self.u.mem_write(0xa18298b8,bytes([imenu]));self.u.mem_write(UI,b'\0');self.word(FOCUS+4,current)
        for i in range(12):self.u.mem_write(ITEMS+8*i,struct.pack('<2I',bool(disabled&(1<<i)),0x9000+i))
        self.stock.clear();self.selected.clear();self.queries.clear();self.focus_calls=0
    def hook(self,u,address,size,context):
        if self.selector_prefix and address==0x103ddec2:u.emu_stop();return
        if self.selector_prefix and address in (0x1030119e,0x103dd4d0):self.ret(self.selector_gate if address==0x1030119e else 0);return
        if address in {v&~1 for v in getattr(self,'functions',())}:
            direction=u.reg_read(UC_ARM_REG_R0);self.stock.append((bytes(u.mem_read(MODE,1))[0],direction));self.ret(direction^0x5a5a0000);return
        if address==0x103dde4a and not self.selector_prefix:self.selected.append(u.reg_read(UC_ARM_REG_R0));self.ret(0);return
        if address==0x103dde3a:self.queries.append(u.reg_read(UC_ARM_REG_R1))
        if address==0x103dd558:self.focus_calls+=1
        super().hook(u,address,size,context)


def divide(n,d):return n//d if n>=0 else -((-n)//d)


def point_reference(point,page,orientation):
    x=divide(point[0]*720+512,1024);y=divide(point[1]*480+341,682)
    u,v=(479-y,x) if orientation==2 else (y,719-x)
    if not (0<=u<480 and 0<=v<720):return (-4,-4)
    sx=sy=-1
    inv=lambda pixel,scale:((pixel+1)*65536-1)//scale
    if page in (1,2):
        if 440<=v<659:
            cell=((v-440)//73)*4+u//120
            sx=(cell%6)*120+u%120;sy=280+(cell//6)*73+(v-440)%73
        elif 660<=v<715:sx=inv(u+211,57344);sy=inv(v-295,57344)
        elif page==2 and 283<=v<440:sx=inv(u,43691);sy=inv(v-254,43691)
    else:
        shift,scale=(235,65536) if page==3 else (394,43691)
        if shift<=v<shift+(480*scale//65536):sx=inv(u,43691);sy=inv(v-shift,scale)
    if not (0<=sx<720 and 0<=sy<480):return (-4,-4)
    return ((sx*1024+360)//720,(sy*682+240)//480)


def cycle(current,direction,orientation):
    # Enumerate the selected row/column in physical-button order, independently
    # from the C unsigned modular step arithmetic.
    x,y=current%4,current//4;sign=1 if orientation==2 else -1
    if direction in (0,1):
        step=sign if direction==0 else -sign
        return [y*4+((x+step*n)%4) for n in range(1,5)]
    step=sign if direction==2 else -sign
    return [((y+step*n)%3)*4+x for n in range(1,4)]


def audit(raw,packet,metadata):
    f=InputFixture(raw,packet,metadata);checks=[];nav_cases=point_cases=0
    def check(name,good):checks.append(dict(name=name,passed=bool(good)));assert good,name
    rows=struct.unpack('<34I',f.u.mem_read(0x11eca198,136))
    check('original-seventeen-row-initializer-matches-ram-ids-and-functions',rows[::2]==tuple(range(17)) and
          bytes(f.u.mem_read(MODE+4,136))==bytes(f.u.mem_read(0x11eca198,136)))
    for mode,direction in itertools.product(range(17),range(4)):
        f.setup(mode);result=f.call(0x104389b0,direction)
        check(f'original-native-dispatch-mode{mode}-direction{direction}',result==(direction^0x5a5a0000) and f.stock==[(mode,direction)])
    for current,direction,orientation in itertools.product(range(12),range(4),(1,2)):
        path=cycle(current,direction,orientation)
        for subset in range(1<<len(path)):
            disabled=sum(1<<v for i,v in enumerate(path) if subset&(1<<i))
            visited=[];target=current
            for v in path:
                target=v
                if v==current:break
                visited.append(v)
                if not disabled&(1<<v):break
            check(f'pure-nav{nav_cases}-all-cycle-disable-patterns',f.call(f.entry('input_target'),current,direction,orientation,disabled)==target)
            f.setup(current=current,disabled=disabled)
            check(f'native-nav{nav_cases}-original-focus-and-item-reads',f.call(f.entry('navigation'),direction,1,orientation)==0 and
                  f.selected==[target] and not f.stock and f.queries==visited and f.focus_calls==1 and f.read(INDEX)==target)
            nav_cases+=1
    for mode,orientation,direction in itertools.product(range(17),(1,2),range(4)):
        f.setup(mode);mapped=({1:(3,2,0,1),2:(2,3,1,0)}[orientation])[direction]
        check(f'settings-mode{mode}-orientation{orientation}-direction{direction}',f.call(f.entry('navigation'),direction,3,orientation)==(mapped^0x5a5a0000) and
              f.stock==[(mode,mapped)] and not f.selected and not f.queries)
    for mode,count,imenu,current,page,orientation,direction in (
        (0,12,0,0,1,0,0),(0,12,0,0,1,3,1),(0,12,0,0,1,1,4),(0,12,0,0,1,1,0xffffffff),
        (1,12,0,0,1,1,0),(0,11,0,0,1,1,0),(0,13,0,0,1,1,0),(0,12,3,0,1,1,0),
        (0,12,0,12,1,1,0),(0,12,0,0xffffffff,1,1,0),(0,12,0,0,0,1,0),
        (0,12,0,0,2,1,0),(0,12,0,0,4,1,0),(0,12,0,0,5,1,0)):
        f.setup(mode,current,count=count,imenu=imenu)
        check(f'delegate{len(checks)}',f.call(f.entry('navigation'),direction,page,orientation)==(direction^0x5a5a0000) and
              f.stock==[(mode,direction)] and not f.selected and f.read(INDEX)==0x12345678)
    for mode in (17,18,255):
        f.setup(mode);check(f'invalid-original-mode{mode}-no-table-read-or-selection',f.call(f.entry('navigation'),0,1,1)==0 and not f.stock and not f.selected)
    samples=set(itertools.product((-32768,-4,-1,0,1,681,682,1023,1024,32767),repeat=2))
    for orientation in (1,2):
        logical=set()
        for row,col,xoff,yoff in itertools.product(range(3),range(4),(0,1,59,119),(0,1,36,72)):
            logical.add((col*120+xoff,440+row*73+yoff))
        logical.update(itertools.product((0,1,120,241,242,479),(0,234,235,282,283,369,393,394,439,440,659,660,661,714,715,719)))
        raw=set(samples)
        for u,v in logical:
            x,y=(v,479-u) if orientation==2 else (719-v,u)
            raw.add(((x*1024+360)//720,(y*682+240)//480))
        for page,point in itertools.product(range(1,5),sorted(raw)):
            f.u.mem_write(POINT,struct.pack('<2h',*point))
            check(f'touch-point{point_cases}',f.call(f.entry('input_point'),POINT,page,orientation)==1 and
                  struct.unpack('<2h',f.u.mem_read(POINT,4))==point_reference(point,page,orientation))
            point_cases+=1
    for page,orientation,kind in itertools.product(range(1,5),(1,2),(*range(10),255)):
        event=bytearray(range(60));event[9]=kind
        for off,p in zip(OFFSETS,((0,0),(0,0),(700,200),(500,300),(-4,-4),(1000,600))):struct.pack_into('<2h',event,off,*p)
        f.u.mem_write(EVENT,bytes(event));f.u.mem_write(COPY-16,b'\xa5'*92)
        expected=bytearray(event);handled=kind in range(1,9)
        if handled:
            for i,off in enumerate(OFFSETS):
                p=struct.unpack_from('<2h',event,off)
                if not i or any(p):struct.pack_into('<2h',expected,off,*point_reference(p,page,orientation))
        check(f'event-page{page}-orientation{orientation}-kind{kind}',f.call(f.entry('input_event'),EVENT,COPY,page,orientation)==handled and
              bytes(f.u.mem_read(EVENT,60))==bytes(event) and bytes(f.u.mem_read(COPY,60))==(bytes(expected) if handled else b'\xa5'*60) and
              bytes(f.u.mem_read(COPY-16,16))==b'\xa5'*16 and bytes(f.u.mem_read(COPY+60,16))==b'\xa5'*16)
    for event,copy,page,orientation in ((0,COPY,1,1),(EVENT,0,1,1),(EVENT+1,COPY,1,1),(EVENT,EVENT,1,1),
        (EVENT,EVENT+4,1,1),(EVENT,EVENT-4,1,1),(0xfffffff0,COPY,1,1),(EVENT,COPY,0,1),(EVENT,COPY,1,3)):
        check(f'invalid-event{len(checks)}',f.call(f.entry('input_event'),event,copy,page,orientation)==0)
    for orientation,key in itertools.product((0,1,2,3),(0,1,2,3,4,5,6,0xffffffff)):
        mapped=({1:(4,5,3,2),2:(5,4,2,3)}[orientation][key-2] if orientation in (1,2) and 2<=key<=5 else key)
        check(f'external-key{key}-orientation{orientation}',f.call(f.entry('input_key'),key,orientation)==mapped)
    # Execute the native selector only to the concrete pre-render boundary;
    # its admission gate/old-widget cleanup are supplied, not a completed UI.
    f.selector_prefix=True
    for target in range(12):
        f.setup(current=0);f.word(FOCUS+0x54,0);f.word(FOCUS+0xc,0)
        f.u.reg_write(UC_ARM_REG_R0,target);f.u.reg_write(UC_ARM_REG_SP,STACK);f.u.reg_write(UC_ARM_REG_LR,STOP|1)
        f.u.emu_start(0x103dde4b,STOP,count=10000)
        check(f'original-selector-prefix-commits-focus{target}-before-render',f.u.reg_read(UC_ARM_REG_PC)==0x103ddec2 and
              f.read(FOCUS+4)==target and f.read(FOCUS+0xc)==target and f.queries==[target])
    f.setup(current=3);f.word(FOCUS+0x54,0);f.word(FOCUS+0xc,0);f.selector_gate=1
    f.u.reg_write(UC_ARM_REG_R0,7);f.u.reg_write(UC_ARM_REG_SP,STACK);f.u.reg_write(UC_ARM_REG_LR,STOP|1)
    f.u.emu_start(0x103dde4b,STOP,count=10000)
    check('original-selector-admission-rejection-keeps-focus',f.u.reg_read(UC_ARM_REG_PC)==STOP and f.read(FOCUS+4)==3 and
          f.read(FOCUS+0xc)==0 and not f.queries)
    return dict(passed=True,checks=checks,grid_navigation_cases=nav_cases,touch_point_cases=point_cases,
                original_selector_prefix_cases=12,original_selector_admission_rejection_executes=True,
                original_seventeen_mode_dispatch_focus_getter_and_item_readers_execute=True,
                compiled_grid_skip_wrap_direction_and_touch_copy_geometry_execute=True,
                native_selector_page_layout_output_items_and_pinned_touch_calibration_supplied=True,
                installed_input_hook_native_touch_registration_calibration_queue_lifetime_or_selection_completion_proven=False,camera_card_access=False)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stock-main',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private directory')
    raw=a.stock_main.read_bytes();assert hashlib.sha256(raw).hexdigest()==STOCK_SHA
    source=ROOT/'z7-native-modules/examples/portrait_input_probe.c';packet,metadata=build(source,zig=ZIG);again,other=build(source,zig=ZIG)
    assert packet==again and metadata==other
    result=audit(raw,packet,metadata)
    names=('tools/audit_z7_portrait_input.py','tools/audit_splash_image.py','tools/build_z7_module.py',
           'z7-native-modules/plugins/portrait_input.h','z7-native-modules/plugins/portrait_navigation.h',
           'z7-native-modules/examples/portrait_input_probe.c','z7-native-modules/sdk/module.h','z7-native-modules/sdk/module.ld')
    result.update(probe_sha256=hashlib.sha256(packet).hexdigest(),probe_bytes=len(packet),image_bytes=metadata['image_bytes'],bss_bytes=metadata['bss_bytes'],
                  relocations=len(metadata['relocations']),reproducible_probe=True,source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    out.mkdir(parents=True);(out/'probe.BIN').write_bytes(packet)
    (out/'probe.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8',newline='\n')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(result['checks']),grid_cases=result['grid_navigation_cases'],touch_cases=result['touch_point_cases'])))


if __name__=='__main__':main()
