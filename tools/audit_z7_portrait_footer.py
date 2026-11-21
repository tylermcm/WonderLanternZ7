"""Compiled original-Z7 hint footer geometry and native image rendering.

SPDX-License-Identifier: MIT. Raw messages, native normalization, image19/1A CPU
math and completion execute. GPU services, rectangle renderer and admitted pages
are supplied. No footer band ownership, transition latch, text/input or pixels.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from audit_z7_portrait_native_image import NativeImageFixture
from audit_z7_portrait_draw import CODE,BOX,MESSAGE,PAYLOAD,WORDS,reference_destination
from audit_z7_portrait_page_message import strip19_reference
from audit_splash_image import STOCK_SHA
from build_z7_module import build
from build_z7_module_host import ROOT,ZIG

def footer_reference(box,command):
    x,y,w,h=box;full=x==0 and w==720 and command in (0x13,0x17)
    if x<242 and not full:
        if command!=0x17 or x+w<=242:return None
        w-=242-x;x=242
    left=x*7//8;right=(x+w)*7//8;top=y*7//8;bottom=(y+h)*7//8
    result=(0 if full else left-211,top+295,480 if full else max(1,right-left),max(1,bottom-top))
    a,b,c,d=result
    return result if a>=0 and b>=660 and a+c<=480 and b+d<=720 else None

def audit(raw,packet,metadata):
    f=NativeImageFixture(raw,packet,metadata);checks=[];native_images=0;draws=0
    geometry=CODE+metadata['symbols']['z7_portrait_footer_box_probe']
    def check(name,good):checks.append(dict(name=name,passed=bool(good)));assert good,name
    def call_message(name,command,page,orientation,box,angle=0,mode=0):
        nonlocal native_images,draws
        f.rendered.clear()
        if command>=0x19:
            # mode1 derives the extent from source dimensions; mode0 exercises
            # a different source aspect and signed compensated coordinates.
            sw,sh=(box[2],box[3]) if mode else (160,80)
            msg,data,stock=f.prepare(command,angle,mode,clear=1,sw=sw,sh=sh,box=box)
        else:
            x,y,w,h=box;s=[0]*WORDS[command];s[:4]=[x,480-y-h,w,h]
            data=struct.pack('<%dI'%len(s),*(v&0xffffffff for v in s));f.u.mem_write(PAYLOAD,data)
            msg=struct.pack('<7I',1,2,3,0x1042eadf,0x42010000+command,PAYLOAD,123);f.u.mem_write(MESSAGE,msg)
            f.events.clear();f.api.clear();f.native_payloads.clear();stock=box
        logical=footer_reference(stock,command)
        got=f.call(f.operation,MESSAGE,page,orientation)
        if command<0x19 and stock[0]>720:
            check(name+'-rectangle-source-range-reject',got==0 and not f.events and not f.rendered and bytes(f.u.mem_read(MESSAGE,28))==msg and bytes(f.u.mem_read(PAYLOAD,len(data)))==data)
            return
        consumed=logical is None or command>=0x19 and angle not in (0,90,180,270,360)
        if consumed:
            check(name,got==1 and not f.api and not f.rendered and not f.native_payloads and f.events==[('ack',0x42010062,0),'event'])
        else:
            physical=reference_destination(logical,orientation)
            if command>=0x19:
                if command==0x19:physical=strip19_reference(physical,sw,sh,((90 if orientation==2 else 270)+angle)%360)
                _,out=f.native_payloads[0];x,y,x2,y2=struct.unpack_from('<4h',out,24);actual=(x,y,x2-x,y2-y)
                check(name+'-native-image-clear-disabled',not any(a==0x1045081e for a,_ in f.api) and struct.unpack_from('<I',out,36)[0]==0)
                check(name+'-native-image-draw-once',len(f.native_payloads)==1 and sum(a in (0x10450c86,0x10451338) for a,_ in f.api)==1)
                native_images+=1
            else:
                _,out=f.rendered[0];x,y,w,h=struct.unpack_from('<4i',out);actual=(x,480-y-h,w,h)
                check(name+'-rectangle-once',len(f.rendered)==1)
            check(name,got==1 and actual==physical and f.events==['render',('deferred',0x42010062,0),('ack',0x42010062,0),'event'])
            draws+=1
        check(name+'-producer-payload-preserved',bytes(f.u.mem_read(PAYLOAD,len(data)))==data and bytes(f.u.mem_read(MESSAGE,24))==msg[:24] and int.from_bytes(f.u.mem_read(MESSAGE+24,4),'little')==0)
    boxes=((0,418,720,10),(200,418,100,10),(242,418,80,10),(300,430,80,24),(722,480,2,4),(243,427,1,1))
    for command in WORDS:
        for box in boxes:
            f.u.mem_write(BOX,struct.pack('<4i',*box));f.u.mem_write(BOX+32,b'\x6b'*16)
            expected=footer_reference(box,command);got=f.call(geometry,BOX,command,BOX+32)
            check(f'geometry-{command}-{box}',got==int(expected is not None) and bytes(f.u.mem_read(BOX+32,16))==(struct.pack('<4i',*expected) if expected else b'\x6b'*16))
    for box in ((0,417,1,10),(242,418,1,8),(242,480,1,5),(-1,430,1,1),(0x7fffffff,430,1,1)):
        f.u.mem_write(BOX,struct.pack('<4i',*box));f.u.mem_write(BOX+32,b'\x6b'*16)
        check('outside-hint-geometry'+str(box),f.call(geometry,BOX,0x17,BOX+32)==0 and bytes(f.u.mem_read(BOX+32,16))==b'\x6b'*16)
    for page in (1,2):
        for orientation in (1,2):
            for command in (0x13,0x16,0x17):
                for box in boxes:call_message(f'footer-rect-{page}-{orientation}-{command}-{box}',command,page,orientation,box)
            for command in (0x19,0x1a,0x1c):
                for mode in (0,1):
                    for angle in ((0,) if command==0x1c else (0,90,180,270,360)):
                        for box in ((242,418,80,10),(300,430,80,24),(722,480,2,4),(243,427,1,1)):
                            call_message(f'footer-image-{page}-{orientation}-{command}-{mode}-{angle}-{box}',command,page,orientation,box,angle,mode)
            call_message(f'left-image-consumed-{page}-{orientation}',0x19,page,orientation,(200,430,80,24))
            call_message(f'bad-footer-angle-{page}-{orientation}',0x1a,page,orientation,(300,430,80,24),angle=1)
    return dict(passed=True,checks=checks,native_image_cases=native_images,draws=draws,
                original_image_math_clear_dispatch_and_completion_execute=True,
                gpu_services_rectangle_renderer_and_page_admission_supplied=True,
                footer_band_ownership_transition_latch_text_input_or_pixels_proven=False,camera_card_access=False)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stock-main',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private directory')
    raw=a.stock_main.read_bytes();assert hashlib.sha256(raw).hexdigest()==STOCK_SHA
    packet,metadata=build(ROOT/'z7-native-modules/examples/portrait_footer_probe.c',zig=ZIG)
    again,other=build(ROOT/'z7-native-modules/examples/portrait_footer_probe.c',zig=ZIG);assert packet==again and metadata==other
    result=audit(raw,packet,metadata)
    names=('tools/audit_z7_portrait_footer.py','tools/audit_z7_portrait_native_image.py','tools/audit_z7_portrait_page_message.py','tools/audit_z7_portrait_draw.py','tools/audit_z7_portrait_grid_message.py','tools/audit_splash_image.py','tools/build_z7_module.py',
           'z7-native-modules/sdk/module.h','z7-native-modules/sdk/module.ld','z7-native-modules/plugins/portrait_page_message.h','z7-native-modules/plugins/portrait_grid_message.h',
           'z7-native-modules/plugins/portrait_grid.h','z7-native-modules/plugins/portrait_footer.h','z7-native-modules/plugins/portrait_geometry.h','z7-native-modules/plugins/portrait_draw.h','z7-native-modules/examples/portrait_footer_probe.c')
    result.update(probe_sha256=hashlib.sha256(packet).hexdigest(),reproducible_probe=True,probe_bytes=len(packet),source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    out.mkdir(parents=True);(out/'probe.BIN').write_bytes(packet)
    (out/'probe.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8',newline='\n')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(result['checks']),native_image_cases=result['native_image_cases'],probe_bytes=len(packet))))

if __name__=='__main__':main()
