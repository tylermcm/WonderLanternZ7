"""Compiled portrait adapter through original Z7 image/rectangle dispatch.

SPDX-License-Identifier: MIT. Backend renderers and kernel event service are
supplied. Original message dispatch, image adapters, completion and compiled
transforms execute. No live graphics hook, LCD admission, pixels or device I/O.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import struct

from unicorn.arm_const import UC_ARM_REG_R0, UC_ARM_REG_R1, UC_ARM_REG_R2, UC_ARM_REG_R3, UC_ARM_REG_SP
from audit_splash_image import NativePNG, MEM, STOCK_SHA
from build_z7_module import build, HEADER
from build_z7_module_host import ROOT, ZIG

CODE, BOX = MEM+0x10000, MEM+0x20000
MESSAGE, PAYLOAD = 0xa1d75000, 0xa1d75100
BACKENDS={0x13:0x1042f066,0x16:0x1042f426,0x17:0x1042f5a8,0x19:0x104303e6,0x1a:0x1042f894}
WORDS={0x13:8,0x16:7,0x17:6,0x19:18,0x1a:24}


class PortraitFixture(NativePNG):
    def __init__(self,raw,packet,metadata):
        super().__init__(raw)
        self.u.mem_map(0xa1d75000,0x1000)
        image=bytearray(packet[HEADER:HEADER+metadata['image_bytes']])
        for off in metadata['relocations']:
            struct.pack_into('<I',image,off,struct.unpack_from('<I',image,off)[0]+CODE)
        self.u.mem_write(CODE,bytes(image))
        self.operation=CODE+metadata['symbols']['z7_portrait_draw_probe']
        self.deferred=(CODE+metadata['symbols']['z7_portrait_defer_completion'])&~1
        self.events=[];self.rendered=[]
    def hook(self,u,address,size,context):
        if address in BACKENDS.values():
            self.events.append('render')
            if address==BACKENDS[0x16]:
                registers=[u.reg_read(r) for r in (UC_ARM_REG_R0,UC_ARM_REG_R1,UC_ARM_REG_R2,UC_ARM_REG_R3)]
                data=struct.pack('<4I',*registers)+bytes(u.mem_read(u.reg_read(UC_ARM_REG_SP),12))
            else:
                length=88 if address==BACKENDS[0x1a] else 68 if address==BACKENDS[0x19] else 28
                data=bytes(u.mem_read(u.reg_read(UC_ARM_REG_R0),length))
            self.rendered.append((address,data));self.ret(0)
        elif address==self.deferred:
            self.events.append(('deferred',u.reg_read(UC_ARM_REG_R0),u.reg_read(UC_ARM_REG_R1)))
        elif address==0x1042eade:
            self.events.append(('ack',u.reg_read(UC_ARM_REG_R0),u.reg_read(UC_ARM_REG_R1)))
        elif address==0x10170be8:
            assert (u.reg_read(UC_ARM_REG_R0),u.reg_read(UC_ARM_REG_R1))==(0xa1d75e3c,1)
            self.events.append('event');self.ret(0)
        else:super().hook(u,address,size,context)


def reference_destination(box,orientation):
    x,y,w,h=box
    corners=[(x,y),(x+w,y),(x,y+h),(x+w,y+h)]
    corners=[(720-py,px) if orientation==1 else (py,480-px) for px,py in corners]
    xs,ys=zip(*corners)
    return min(xs),min(ys),max(xs)-min(xs),max(ys)-min(ys)


def normalized_payload(command,words):
    if command==0x16:return struct.pack('<7I',*words),bytes([1]*28)
    if command in (0x13,0x17):
        flags=(words[6],words[7]) if command==0x13 else (words[4],words[5])
        result=struct.pack('<6I2B2x',*words[:4],*(words[4:6] if command==0x13 else (0,0)),*(v&255 for v in flags))
        return result,bytes([1]*26+[0]*2)
    result=bytearray(88 if command==0x1a else 68)
    result[:60]=struct.pack('<15I',*words[:15])
    struct.pack_into('<H',result,60,words[15]&65535)
    result[64:66]=bytes((words[16]&255,words[17]&255))
    mask=bytearray([1]*len(result));mask[62:64]=bytes(2);mask[66:68]=bytes(2)
    if command==0x1a:result[68:88]=struct.pack('<5I',*words[19:24])
    return bytes(result),bytes(mask)


def audit(raw,packet,metadata):
    f=PortraitFixture(raw,packet,metadata);checks=[]
    def check(name,good):
        checks.append(dict(name=name,passed=bool(good)))
        if not good:raise AssertionError(name)
    cases=0
    for command,orientation,box in itertools.product(WORDS,(1,2),((0,0,480,720),(40,100,24,110),(479,719,1,1))):
        for mode,angle in (itertools.product((0,1),(0,90,180,270,360)) if command>=0x19 else ((0,0),)):
            source=[0x76540000+i for i in range(24)]
            source[0]=mode if command>=0x19 else 40
            source[15]=0xabcd0000|angle
            message=struct.pack('<7I',1,2,3,0x1042eadf,0x42010000+command,PAYLOAD,0xa5a5a5a5)
            original=struct.pack('<24I',*source)
            f.u.mem_write(MESSAGE,message);f.u.mem_write(PAYLOAD,original);f.u.mem_write(BOX,struct.pack('<4i',*box))
            f.events.clear();f.rendered.clear()
            returned=f.call(f.operation,MESSAGE,BOX,orientation)
            desired=source[:WORDS[command]];x,y,w,h=reference_destination(box,orientation)
            if command>=0x19:
                desired[0]=0;desired[6]=x|(y<<16);desired[7]=(x+w)|((y+h)<<16)
                desired[15]=(source[15]&0xffff0000)|((angle+(270 if orientation==1 else 90))%360)
            else:desired[:4]=[x,480-y-h,w,h]
            expected,mask=normalized_payload(command,desired)
            actual=f.rendered[0][1] if f.rendered else b''
            check(f'cmd{command:x}-orientation{orientation}-box{box}-mode{mode}-angle{angle}',
                  returned==1 and len(f.rendered)==1 and f.rendered[0][0]==BACKENDS[command] and len(actual)==len(expected) and
                  all(a==b for a,b,m in zip(actual,expected,mask) if m) and
                  bytes(f.u.mem_read(PAYLOAD,96))==original and bytes(f.u.mem_read(MESSAGE,28))==message[:24]+bytes(4) and
                  f.events==['render',('deferred',0x42010062,0),('ack',0x42010062,0),'event'])
            cases+=1
    # Invalid admission must not dispatch, acknowledge or mutate native input.
    for kind in ('message-null','message-unaligned','message-end','foreign-completion','unknown-command','fixed-image-1c',
                 'source-null','source-unaligned','source-end','landscape','inverted','unknown-orientation',
                 'box-null','box-outside','negative-box','angle-invalid','image-mode-invalid'):
        message=[1,2,3,0x1042eadf,0x4201001a,PAYLOAD,0xa5a5a5a5];source=[0]*24
        box=(1,1,20,30);orientation=1;mp=MESSAGE;bp=BOX
        if kind=='message-null':mp=0
        if kind=='message-unaligned':mp=MESSAGE+1
        if kind=='message-end':mp=0xaffffff0
        if kind=='foreign-completion':message[3]=0x1042eae7
        if kind=='unknown-command':message[4]=0xffffffff
        if kind=='fixed-image-1c':message[4]=0x4201001c
        if kind=='source-null':message[5]=0
        if kind=='source-unaligned':message[5]=PAYLOAD+1
        if kind=='source-end':message[5]=0xaffffff0
        if kind=='landscape':orientation=0
        if kind=='inverted':orientation=3
        if kind=='unknown-orientation':orientation=4
        if kind=='box-null':bp=0
        if kind=='box-outside':box=(479,719,2,2)
        if kind=='negative-box':box=(-1,0,1,1)
        if kind=='angle-invalid':source[15]=45
        if kind=='image-mode-invalid':source[0]=2
        original=struct.pack('<24I',*source);msg=struct.pack('<7I',*message)
        f.u.mem_write(MESSAGE,msg);f.u.mem_write(PAYLOAD,original);f.u.mem_write(BOX,struct.pack('<4i',*box))
        f.events.clear();f.rendered.clear()
        check(kind+'-no-dispatch-ack-or-input-mutation',f.call(f.operation,mp,bp,orientation)==0 and not f.events and not f.rendered and
              bytes(f.u.mem_read(MESSAGE,28))==msg and bytes(f.u.mem_read(PAYLOAD,96))==original)
    return dict(passed=True,checks=checks,draw_cases=cases,stock_main_sha256=STOCK_SHA,
                original_dispatch_image_adapters_completion_and_compiled_geometry_execute=True,
                backend_renderer_kernel_event_and_caller_lcd_admission_supplied=True,
                fixed_image_1c_text_reflow_navigation_hook_lifetime_and_pixels_proven=False,camera_card_access=False)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--stock-main',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private directory')
    raw=a.stock_main.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=STOCK_SHA:p.error('Exact original Z7 C3.80 MAIN required')
    packet,metadata=build(ROOT/'z7-native-modules/examples/portrait_draw_probe.c',zig=ZIG)
    again,other=build(ROOT/'z7-native-modules/examples/portrait_draw_probe.c',zig=ZIG)
    assert packet==again and metadata==other,'Probe not reproducible'
    result=audit(raw,packet,metadata)
    names=('tools/audit_z7_portrait_draw.py','tools/audit_splash_image.py','tools/build_z7_module.py',
           'z7-native-modules/sdk/module.h','z7-native-modules/sdk/module.ld','z7-native-modules/plugins/portrait_draw.h',
           'z7-native-modules/plugins/portrait_geometry.h','z7-native-modules/examples/portrait_draw_probe.c')
    result.update(probe_sha256=hashlib.sha256(packet).hexdigest(),reproducible_probe=True,
                  probe_bytes=len(packet),image_bytes=metadata['image_bytes'],bss_bytes=metadata['bss_bytes'],
                  relocation_count=len(metadata['relocations']),flat_probe_loader_admission_exercised=False,
                  source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    out.mkdir(parents=True);(out/'probe.BIN').write_bytes(packet)
    (out/'probe.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8',newline='\n')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(result['checks']),draw_cases=result['draw_cases'],probe_bytes=len(packet))))


if __name__=='__main__':main()
