"""Compiled original-Z7 dial/settings/external-page draw placement.

SPDX-License-Identifier: MIT. Actual dispatch/normalizers/completion execute;
backend renderer/events and page/orientation admission supplied. External app
bindings, footer/text/input/transitions and pixels unproved.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from audit_z7_portrait_draw import PortraitFixture,CODE,BOX,MESSAGE,PAYLOAD,BACKENDS,WORDS,reference_destination
from audit_z7_portrait_grid_message import packpoint
from audit_splash_image import STOCK_SHA
from build_z7_module import build
from build_z7_module_host import ROOT,ZIG

def scaled(box,page):
    x,y,w,h=box;left=x*43691//65536;right=(x+w)*43691//65536
    top=y if page==3 else y*43691//65536;bottom=y+h if page==3 else (y+h)*43691//65536
    return left,top+{2:254,3:235,4:394}[page],max(1,right-left),max(1,bottom-top)

def strip19_reference(dest,sw,sh,angle):
    x,y,w,h=dest
    if angle in (90,270):
        nw=max(1,(w*sw+sh//2)//sh);nh=max(1,(h*sh+sw//2)//sw);half=(nw+nh)//2
        x,y=(x+nh-half,y+h-half) if angle==90 else (x+w-half,y+nw-half)
        w,h=nw,nh
    return x,y,w,h

def audit(raw,packet,metadata):
    meta=dict(metadata,symbols=dict(metadata['symbols']));meta['symbols']['z7_portrait_draw_probe']=metadata['symbols']['z7_portrait_page_message_probe']
    f=PortraitFixture(raw,packet,meta);f.native_call_timeout_us=0;checks=[];draws=0
    scale=CODE+metadata['symbols']['z7_portrait_page_scale_probe']
    def check(name,good):checks.append(dict(name=name,passed=bool(good)));assert good,name
    def run(name,command,page,orientation,box,mode=0,angle=0,clear=0,expected=None):
        nonlocal draws
        x,y,w,h=box;s=[0]*WORDS[command]
        if command in (0x13,0x16,0x17):s[:4]=[x,480-y-h,w,h]
        else:
            s[0]=mode;s[4]=0;s[5]=packpoint(w,h);s[6]=packpoint(x,y);s[7]=packpoint(x+(17 if mode else w),y+(19 if mode else h))
            if command==0x1c:s[6:10]=[x<<16,y<<16,(x+(17 if mode else w))<<16,(y+(19 if mode else h))<<16]
            else:s[15]=angle;s[9]=clear
        data=struct.pack('<%dI'%len(s),*(v&0xffffffff for v in s));f.u.mem_write(PAYLOAD,data)
        msg=struct.pack('<7I',1,2,3,0x1042eadf,0x42010000+command,PAYLOAD,123);f.u.mem_write(MESSAGE,msg)
        f.events.clear();f.rendered.clear();got=f.call(f.operation,MESSAGE,page,orientation)
        if expected is None:
            check(name,got==0 and not f.rendered and not f.events and bytes(f.u.mem_read(MESSAGE,28))==msg and bytes(f.u.mem_read(PAYLOAD,len(data)))==data);return
        check(name+'-handled',got==1 and len(f.rendered)==1)
        backend,out=f.rendered[0]
        if command>=0x19:
            start,end=struct.unpack_from('<2I',out,24);x,y=start&65535,start>>16;actual=(x,y,(end&65535)-x,(end>>16)-y)
            check(name+'-angle',struct.unpack_from('<H',out,60)[0]==((90 if orientation==2 else 270)+angle)%360)
        else:
            x,y,w,h=struct.unpack_from('<4i',out);actual=(x,480-y-h,w,h)
        physical=reference_destination(expected,orientation)
        if page==2 and command==0x19:physical=strip19_reference(physical,box[2],box[3],((90 if orientation==2 else 270)+angle)%360)
        if page==2 and command>=0x19:check(name+'-strip-clearing-disabled',struct.unpack_from('<I',out,36)[0]==0)
        check(name,actual==physical and backend==BACKENDS[0x1a if command==0x1c else command] and
              f.events==['render',('deferred',0x42010062,0),('ack',0x42010062,0),'event'] and
              bytes(f.u.mem_read(MESSAGE,24))==msg[:24] and int.from_bytes(f.u.mem_read(MESSAGE+24,4),'little')==0 and bytes(f.u.mem_read(PAYLOAD,len(data)))==data)
        draws+=1
    boxes=((1,44,2,1),(0,44,720,236),(199,100,201,111),(719,279,1,1))
    for page in (2,3,4):
        for box in boxes:
            f.u.mem_write(BOX,struct.pack('<4i',*box));f.u.mem_write(BOX+32,b'\x6b'*16)
            got=f.call(scale,BOX,page,BOX+32)
            check(f'floor-edge-scale{page}-{box}',got==1 and struct.unpack('<4i',bytes(f.u.mem_read(BOX+32,16)))==scaled(box,page))
            for orientation in (1,2):
                for command in WORDS:
                    for mode in ((0,1) if command>=0x19 else (0,)):
                        expected=scaled(box,page)
                        run(f'draw-{page}-{box}-{orientation}-{command}-{mode}',command,page,orientation,box,mode,expected=expected)
    for page in (2,4):
        for command in (0x19,0x1a):
            for angle in (90,180,270,360):
                expected=scaled((199,100,201,111),page)
                run(f'pre-rotated-{page}-{command}-{angle}',command,page,2,(199,100,201,111),angle=angle,expected=expected)
    for angle in (1,90,180,270,361):run(f'settings-pre-rotated-reject{angle}',0x1a,3,1,(199,100,201,111),angle=angle)
    for command in (0x19,0x1a):
        run(f'dial-image-clear-disabled{command}',command,2,1,(199,100,201,111),clear=1,expected=scaled((199,100,201,111),2))
    for page in (2,3,4):
        for command in WORDS:run(f'full-screen-pass-{page}-{command}',command,page,1,(0,0,720,480))
    for page in (0,5,0xffffffff):run(f'unknown-page{page}',0x17,page,1,(199,100,201,111))
    for orientation in (0,3,4,0xffffffff):run(f'nonportrait{orientation}',0x17,3,orientation,(199,100,201,111))
    for page in (2,3,4):
        for box in ((-1,44,2,1),(0,0,721,1),(0,0,1,481),(0,0,0,1),(0,0,1,-1),(0x7fffffff,0,1,1)):
            f.u.mem_write(BOX,struct.pack('<4i',*box));f.u.mem_write(BOX+32,b'\x6b'*16)
            check(f'invalid-scale-{page}-{box}',f.call(scale,BOX,page,BOX+32)==0 and bytes(f.u.mem_read(BOX+32,16))==b'\x6b'*16)
    # DIAL's top grid border and tile area follow the existing grid pipeline.
    run('dial-top-grid-edge',0x17,2,1,(0,278,120,2),expected=(0,440,120,2))
    run('dial-grid-tile',0x17,2,2,(10,290,100,53),expected=(10,450,100,53))
    return dict(passed=True,checks=checks,native_draws=draws,original_dispatch_normalization_completion_and_page_scaling_execute=True,
                backend_renderer_kernel_events_and_page_orientation_admission_supplied=True,
                external_app_binding_footer_text_input_transition_or_pixels_proven=False,camera_card_access=False)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--stock-main',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();out=a.output.resolve()
    if not out.is_relative_to(ROOT/'.private') or out.exists():p.error('Choose a new private directory')
    raw=a.stock_main.read_bytes();assert hashlib.sha256(raw).hexdigest()==STOCK_SHA
    packet,metadata=build(ROOT/'z7-native-modules/examples/portrait_page_message_probe.c',zig=ZIG)
    again,other=build(ROOT/'z7-native-modules/examples/portrait_page_message_probe.c',zig=ZIG);assert packet==again and metadata==other
    result=audit(raw,packet,metadata)
    names=('tools/audit_z7_portrait_page_message.py','tools/audit_z7_portrait_draw.py','tools/audit_z7_portrait_grid_message.py','tools/audit_splash_image.py','tools/build_z7_module.py',
           'z7-native-modules/sdk/module.h','z7-native-modules/sdk/module.ld','z7-native-modules/plugins/portrait_page_message.h',
           'z7-native-modules/plugins/portrait_grid_message.h','z7-native-modules/plugins/portrait_grid.h','z7-native-modules/plugins/portrait_geometry.h',
           'z7-native-modules/plugins/portrait_draw.h','z7-native-modules/examples/portrait_page_message_probe.c')
    result.update(probe_sha256=hashlib.sha256(packet).hexdigest(),reproducible_probe=True,probe_bytes=len(packet),source_sha256={n:hashlib.sha256((ROOT/n).read_bytes()).hexdigest() for n in names})
    out.mkdir(parents=True);(out/'probe.BIN').write_bytes(packet)
    (out/'probe.json').write_text(json.dumps(metadata,indent=2)+'\n',encoding='utf-8',newline='\n')
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps(dict(passed=True,checks=len(result['checks']),native_draws=result['native_draws'],probe_bytes=len(packet))))

if __name__=='__main__':main()
